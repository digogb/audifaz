"""Importa questões REAIS de provas anteriores (PDF oficial) para `banca_examples`.

As bancas publicam o PDF oficial da prova + o gabarito oficial após cada concurso
— documentos públicos. Este script extrai o texto com pdfplumber, usa o Claude
(chave já paga pelo app) para transcrever fielmente as questões em estrutura, junta
com o gabarito oficial e grava em `BancaExample`. Esses exemplos ancoram a geração
diária (few-shot por banca), calibrando estilo, conteúdo e gabarito.

NÃO faz scraping: você baixa os PDFs oficiais manualmente e aponta o caminho aqui.

Uso (dentro do container app, ou local com venv do backend):
    python scripts/import_banca_pdf.py PROVA.pdf \\
        --gabarito GABARITO.pdf \\
        --banca FCC --fonte "SEFAZ-BA" --ano 2019 \\
        [--disciplinas "Tecnologia da Informação,Direito Tributário"] \\
        [--model claude-sonnet-4-6] [--dry-run]

  --gabarito  pode ser um PDF, um .txt, ou um mapeamento inline tipo "1-A,2-C,3-E".
              Se omitido, o Claude tenta inferir o gabarito do próprio texto da prova
              (menos confiável — prefira sempre passar o gabarito oficial).
  --disciplinas  filtro opcional: só grava questões cuja disciplina contenha um dos
                 termos (case-insensitive). Útil para pegar só TI/Direito.
  --dry-run   extrai e mostra o que gravaria, sem tocar no banco.

O `fonte` é gravado SEM o ano (ano vai na coluna própria), seguindo o padrão
existente (ex.: fonte="SEFAZ-BA", ano=2019).
"""

import argparse
import asyncio
import json
import os
import sys

from sqlalchemy import select

from app.db import AsyncSessionLocal
from app.models import BancaExample

try:
    import pdfplumber
except ImportError:
    print("ERRO: pdfplumber não instalado. Rode: pip install pdfplumber", file=sys.stderr)
    sys.exit(1)

from anthropic import AsyncAnthropic

_client = AsyncAnthropic()

_EXTRACT_TOOL = {
    "name": "registrar_questoes_reais",
    "description": "Registra as questões REAIS extraídas do PDF da prova, transcritas fielmente.",
    "input_schema": {
        "type": "object",
        "properties": {
            "questoes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "numero": {"type": "integer", "description": "Número da questão na prova"},
                        "disciplina": {
                            "type": "string",
                            "description": "Disciplina/assunto específico, ex.: 'Governança de TI (COBIT)', "
                            "'Engenharia de Software / Requisitos', 'Direito Tributário'",
                        },
                        "enunciado": {"type": "string", "description": "Enunciado transcrito LITERALMENTE, com acentuação completa"},
                        "alternativas": {
                            "type": "object",
                            "description": "Mapa A..E → texto literal da alternativa",
                            "additionalProperties": {"type": "string"},
                        },
                        "gabarito": {"type": "string", "enum": ["A", "B", "C", "D", "E"]},
                    },
                    "required": ["numero", "disciplina", "enunciado", "alternativas", "gabarito"],
                },
            }
        },
        "required": ["questoes"],
    },
}

_SYSTEM = """Você extrai questões REAIS de provas de concurso público a partir do texto bruto de um PDF oficial.

REGRAS INVIOLÁVEIS:
- NÃO invente, complete ou "melhore" nada. Transcreva enunciado e alternativas EXATAMENTE como no texto.
- Mantenha a acentuação completa em português (afeta uso posterior em TTS e fidelidade).
- Inclua APENAS questões de múltipla escolha com alternativas A a E.
- Use o GABARITO OFICIAL fornecido para preencher o campo `gabarito`, casando pelo número da questão.
- Se o gabarito de uma questão não constar no material fornecido, OMITA essa questão (não chute).
- Ignore instruções de prova, cabeçalhos, textos de apoio sem pergunta, e questões discursivas.
- Classifique `disciplina` de forma específica (framework/assunto), não genérica."""


def _extract_pdf_pages(path: str) -> list[str]:
    """Texto de cada página (só as não-vazias), preservando a ordem."""
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            if txt.strip():
                pages.append(txt)
    return pages


def _extract_pdf_text(path: str) -> str:
    return "\n\n".join(_extract_pdf_pages(path))


def _load_gabarito(arg: str | None) -> str:
    """Retorna o texto do gabarito a partir de um PDF, .txt ou mapeamento inline."""
    if not arg:
        return ""
    if os.path.isfile(arg):
        if arg.lower().endswith(".pdf"):
            return _extract_pdf_text(arg)
        with open(arg, encoding="utf-8") as f:
            return f.read()
    # tratado como mapeamento inline ("1-A,2-C,...")
    return arg


# Lote de páginas por chamada. Provas FCC têm ~2-4 questões/página; 8 páginas
# (~15-25 questões) cabem com folga na resposta sem risco de truncamento.
PAGES_PER_CHUNK = 8
# Sobreposição de 1 página entre lotes: evita perder questão partida na fronteira.
CHUNK_OVERLAP = 1


async def _extract_chunk(prova_text: str, gabarito_text: str, model: str) -> list[dict]:
    gab_block = (
        f"\n\n=== GABARITO OFICIAL (prova inteira; case pelo número) ===\n{gabarito_text}\n"
        if gabarito_text.strip()
        else "\n\n(Gabarito oficial não fornecido — só inclua questão se o gabarito for inequívoco no próprio texto.)"
    )
    user_msg = (
        "Extraia as questões de múltipla escolha do TRECHO de prova abaixo e registre via a ferramenta. "
        "O trecho pode começar/terminar no meio de uma questão; ignore qualquer questão incompleta.\n"
        f"=== TRECHO DA PROVA ===\n{prova_text}{gab_block}"
    )
    # Streaming é obrigatório com max_tokens alto (o SDK recusa non-streaming
    # quando a geração pode passar de 10 min) e evita o truncamento silencioso
    # que o teto antigo de 16k causava em provas grandes.
    async with _client.messages.stream(
        model=model,
        max_tokens=32000,
        system=_SYSTEM,
        tools=[_EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "registrar_questoes_reais"},
        messages=[{"role": "user", "content": user_msg}],
    ) as stream:
        resp = await stream.get_final_message()
    if resp.stop_reason == "max_tokens":
        raise RuntimeError(
            "Resposta truncada (max_tokens) mesmo com chunking — reduza PAGES_PER_CHUNK."
        )
    for block in resp.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "registrar_questoes_reais":
            return block.input.get("questoes", [])
    return []


async def _extract_questions(pages: list[str], gabarito_text: str, model: str) -> list[dict]:
    """Extrai a prova em lotes de páginas (com streaming) e mescla por número.

    Chunkar evita o truncamento que ocorria ao pedir ~80 questões numa única
    resposta. Dedup por `numero` mantendo a transcrição mais completa (maior
    enunciado), o que naturalmente descarta as questões partidas na fronteira.
    """
    step = max(1, PAGES_PER_CHUNK - CHUNK_OVERLAP)
    by_num: dict[int, dict] = {}
    sem_num: list[dict] = []
    n_chunks = (max(0, len(pages) - CHUNK_OVERLAP) + step - 1) // step or 1
    for ci, start in enumerate(range(0, len(pages), step), 1):
        chunk_text = "\n\n".join(pages[start:start + PAGES_PER_CHUNK])
        if not chunk_text.strip():
            continue
        print(f"  · lote {ci}/{n_chunks} (páginas {start + 1}-{min(start + PAGES_PER_CHUNK, len(pages))}) ...")
        for q in await _extract_chunk(chunk_text, gabarito_text, model):
            if not isinstance(q, dict):
                continue  # o modelo às vezes emite item malformado (string) no array
            num = q.get("numero")
            enun = (q.get("enunciado") or "").strip()
            if not isinstance(num, int):
                sem_num.append(q)
                continue
            prev = by_num.get(num)
            if prev is None or len(enun) > len((prev.get("enunciado") or "")):
                by_num[num] = q
        if start + PAGES_PER_CHUNK >= len(pages):
            break
    return [by_num[n] for n in sorted(by_num)] + sem_num


def _matches_filter(disciplina: str, termos: list[str]) -> bool:
    if not termos:
        return True
    d = (disciplina or "").lower()
    return any(t.strip().lower() in d for t in termos if t.strip())


async def main():
    ap = argparse.ArgumentParser(description="Importa questões reais de prova (PDF) para banca_examples")
    ap.add_argument("prova", help="Caminho do PDF da prova")
    ap.add_argument("--gabarito", help="PDF/.txt/mapeamento inline do gabarito oficial")
    ap.add_argument("--banca", required=True, help='ex.: "FCC"')
    ap.add_argument("--fonte", required=True, help='ex.: "SEFAZ-BA" (sem o ano)')
    ap.add_argument("--ano", type=int, help="ex.: 2019")
    ap.add_argument("--disciplinas", help="filtro CSV opcional (substring, case-insensitive)")
    ap.add_argument("--model", default="claude-sonnet-4-6", help="modelo de extração")
    ap.add_argument("--dry-run", action="store_true", help="não grava, só mostra")
    args = ap.parse_args()

    if not os.path.isfile(args.prova):
        print(f"ERRO: prova não encontrada: {args.prova}", file=sys.stderr)
        sys.exit(1)

    termos = [t for t in (args.disciplinas or "").split(",") if t.strip()]

    print(f"→ Extraindo texto de {args.prova} ...")
    pages = _extract_pdf_pages(args.prova)
    if not any(p.strip() for p in pages):
        print("ERRO: PDF da prova sem texto extraível (provavelmente escaneado/imagem). "
              "pdfplumber não faz OCR.", file=sys.stderr)
        sys.exit(1)
    print(f"  {len(pages)} páginas com texto.")
    gabarito_text = _load_gabarito(args.gabarito)
    if not gabarito_text.strip():
        print("AVISO: sem gabarito oficial — o Claude só incluirá questões com gabarito inequívoco.")

    print(f"→ Extraindo questões com {args.model} (em lotes) ...")
    questoes = await _extract_questions(pages, gabarito_text, args.model)
    print(f"  {len(questoes)} questões retornadas pelo modelo.")

    # relatório de cobertura: expõe questões perdidas (ex.: o modelo às vezes
    # emite itens malformados em questões com textos de apoio longos e elas são
    # descartadas). Sem isso a perda seria silenciosa.
    nums = sorted(q["numero"] for q in questoes if isinstance(q.get("numero"), int))
    if nums:
        faltando = [n for n in range(nums[0], nums[-1] + 1) if n not in set(nums)]
        if faltando:
            print(f"  ⚠️  cobertura {nums[0]}–{nums[-1]}: faltam {len(faltando)} questões: {faltando}")
        else:
            print(f"  cobertura completa: questões {nums[0]}–{nums[-1]}.")

    # filtro de disciplina
    questoes = [q for q in questoes if _matches_filter(q.get("disciplina", ""), termos)]
    if termos:
        print(f"  {len(questoes)} após filtro de disciplina {termos}.")

    async with AsyncSessionLocal() as db:
        # idempotência: enunciados já existentes para a mesma fonte
        existing = (await db.execute(
            select(BancaExample.enunciado).where(
                BancaExample.banca == args.banca, BancaExample.fonte == args.fonte
            )
        )).scalars().all()
        seen = {(e or "").strip()[:120] for e in existing}

        novas, dups = 0, 0
        for q in questoes:
            enun = (q.get("enunciado") or "").strip()
            alts = q.get("alternativas") or {}
            gab = (q.get("gabarito") or "").strip().upper()
            if not enun or not alts or gab not in {"A", "B", "C", "D", "E"}:
                continue
            key = enun[:120]
            if key in seen:
                dups += 1
                continue
            seen.add(key)
            novas += 1
            disc = q.get("disciplina", "")
            print(f"  + Q{q.get('numero','?')} [{gab}] {disc} — {enun[:70]}...")
            if not args.dry_run:
                db.add(BancaExample(
                    banca=args.banca,
                    fonte=args.fonte,
                    ano=args.ano,
                    disciplina=disc,
                    enunciado=enun,
                    alternativas=alts,
                    gabarito=gab,
                    comentario=None,  # questão real: não fabricamos comentário
                    ativo=True,
                ))

        if args.dry_run:
            print(f"\n[DRY-RUN] {novas} novas / {dups} duplicadas — nada gravado.")
        else:
            await db.commit()
            print(f"\n✓ Gravadas {novas} novas questões ({dups} duplicadas ignoradas) em banca_examples.")


if __name__ == "__main__":
    asyncio.run(main())
