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


def _extract_pdf_text(path: str) -> str:
    parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            if txt.strip():
                parts.append(txt)
    return "\n\n".join(parts)


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


async def _extract_questions(prova_text: str, gabarito_text: str, model: str) -> list[dict]:
    gab_block = (
        f"\n\n=== GABARITO OFICIAL ===\n{gabarito_text}\n"
        if gabarito_text.strip()
        else "\n\n(Gabarito oficial não fornecido — só inclua questão se o gabarito for inequívoco no próprio texto.)"
    )
    user_msg = (
        "Extraia as questões de múltipla escolha da prova abaixo e registre via a ferramenta.\n"
        f"=== TEXTO DA PROVA ===\n{prova_text}{gab_block}"
    )
    resp = await _client.messages.create(
        model=model,
        max_tokens=16000,
        system=_SYSTEM,
        tools=[_EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "registrar_questoes_reais"},
        messages=[{"role": "user", "content": user_msg}],
    )
    for block in resp.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "registrar_questoes_reais":
            return block.input.get("questoes", [])
    return []


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
    prova_text = _extract_pdf_text(args.prova)
    if not prova_text.strip():
        print("ERRO: PDF da prova sem texto extraível (provavelmente escaneado/imagem). "
              "pdfplumber não faz OCR.", file=sys.stderr)
        sys.exit(1)
    gabarito_text = _load_gabarito(args.gabarito)
    if not gabarito_text.strip():
        print("AVISO: sem gabarito oficial — o Claude só incluirá questões com gabarito inequívoco.")

    print(f"→ Extraindo questões com {args.model} ...")
    questoes = await _extract_questions(prova_text, gabarito_text, args.model)
    print(f"  {len(questoes)} questões retornadas pelo modelo.")

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
