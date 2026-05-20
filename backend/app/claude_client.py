import asyncio
import json
import math
from dataclasses import dataclass
from datetime import date
from typing import Optional

from anthropic import AsyncAnthropic

_client = AsyncAnthropic()


@dataclass
class ConcursoContext:
    """Contexto do concurso usado para personalizar o prompt do Claude."""
    nome: str
    banca: str
    orgao: str
    cargo: str
    data_prova: Optional[date] = None
    prompt_extra: Optional[str] = None


def _fmt_examples_block(banca: str, questoes: list[dict]) -> str:
    """Bloco de questões reais da banca, ancorando estilo e gabarito."""
    if not questoes:
        return ""
    lines = [
        f"**Questões reais de provas anteriores da banca {banca} — use para calibrar estilo, conteúdo e gabaritos:**\n"
    ]
    for i, q in enumerate(questoes[:12], 1):
        fonte = q.get("fonte", "")
        ano = q.get("ano", "")
        disciplina = q.get("disciplina", "")
        lines.append(f"**Q{i}** ({fonte} {ano} — {disciplina})")
        lines.append(q.get("enunciado", ""))
        for alt, txt in (q.get("alternativas") or {}).items():
            lines.append(f"{alt}) {txt}")
        gab = (q.get("gabarito") or "").strip()
        if gab:
            lines.append(f"Gabarito: {gab}")
        lines.append("")
    return "\n".join(lines)


def _fmt_concurso_profile(c: ConcursoContext) -> str:
    """Bloco específico do concurso atual. Pequeno, mas o que muda entre concursos."""
    data_str = c.data_prova.isoformat() if c.data_prova else "a definir"
    extra = f"\n\n{c.prompt_extra.strip()}" if c.prompt_extra else ""
    return f"""**Perfil do candidato e do concurso atual:**
- Candidato: desenvolvedor sênior com experiência em TI
- Concurso: {c.nome}
- Órgão: {c.orgao}
- Cargo: {c.cargo}
- Banca: {c.banca}
- Data da prova: {data_str}

**Abordagem:**
- Candidato é dev sênior: contextualize conceitos com experiência prática quando útil.
- Foco em acertar questões da banca {c.banca}, não em aprendizado acadêmico geral.
- Seja denso e direto — ele não precisa de explicações básicas de TI, mas precisa das literalidades dos frameworks e normas.
- Para provas discursivas: estrutura {c.banca} — contexto (3 linhas) → fundamentação técnica citando norma/framework (8 linhas) → proposta/conclusão (4 linhas).{extra}"""


_FCC_METHODOLOGY = """**Como a FCC elabora questões de TI (inteligência de banca):**

1. **Enunciado-cenário:** "Um Analista de TI..." — identifique qual conceito está sendo testado
2. **Literalidade de frameworks:** COBIT e ITIL cobram nomes exatos de domínios, processos, práticas e objetivos (ex: "Qual domínio do COBIT 2019 contém APO12?")
3. **ISO 27001/27002:** Cobra os 93 controles por categoria (organizacional, pessoas, físico, tecnológico), diferença entre requisitos (27001) e guia (27002), processo ISO 27005
4. **Engenharia de Software:** GoF (qual padrão resolve qual problema), microsserviços (CQRS vs Saga vs Circuit Breaker), testes (qual tipo em cada situação)
5. **Dados:** Definições exatas DW vs Data Mart vs Data Lake vs Lakehouse, esquemas estrela/floco, SQL com window functions em contexto profissional
6. **PMBOK 7ª ed:** 12 princípios e 8 domínios de desempenho — NÃO as áreas de conhecimento do PMBOK 5/6
7. **Armadilhas clássicas FCC:**
   - Troca COBIT por ITIL e vice-versa (ex: atribui prática ITIL a domínio COBIT)
   - Mistura versões: COBIT 5 vs COBIT 2019, ITIL v3 vs ITIL v4
   - Troca ISO 27001 (requisitos/certificação) com ISO 27002 (controles/guia)
   - Confunde OAuth 2.0 (autorização) com OIDC (autenticação)
   - Troca RPO (quanto dado pode perder) com RTO (quanto tempo pode ficar fora)
   - Alternativas que descrevem corretamente um padrão mas com nome errado"""

_ACCURACY_CLAUSE = """**Princípios de precisão (CRÍTICO):**

Quando você não tem certeza absoluta sobre:
- Códigos exatos de processos (ex: APO12, BAI06, DSS04, MEA02)
- Identificadores de controles ISO 27001:2022 (ex: A.5.7, A.8.23)
- Versões de framework (COBIT 5 vs 2019, ITIL v3 vs v4, ISO 27001:2013 vs 2022, PMBOK 6 vs 7)
- Quantidades exatas (ex: "93 controles", "47 práticas", "8 domínios", "12 princípios")
- Nomes literais de domínios, práticas, objetivos

**USE a ferramenta `web_search` para confirmar antes de afirmar.** Imprecisão é pior que omissão — o candidato perde questão por confiar em código errado tanto quanto por não saber. Se mesmo após buscar você fica em dúvida, escreva "[consultar fonte oficial]" em vez de inventar.

**Fontes preferidas para busca:**
- ISACA oficial (cobit) e Axelos/PeopleCert (itil) para frameworks
- iso.org para normas (controles e cláusulas)
- pmi.org para PMBOK 7
- gov.br e sites oficiais para legislação
- nist.gov para SP 800-* e cybersecurity
- cnj.jus.br para resoluções/portarias do CNJ
- planalto.gov.br para leis federais

**Política de citação:** quando você usar um fato vindo de uma busca, cite brevemente "(fonte: <domínio>)" no comentário da questão ou ao final da seção. Não cite ao usar conhecimento geral consolidado.

**Importante:** faça as buscas primeiro, depois produza o conteúdo final completo. Não intercale narração de busca com o conteúdo entregue ao usuário."""

_BASE_SYSTEM = """Você é um assistente de estudos especializado em concursos públicos brasileiros."""

def _build_tool(bloco_slugs: list[str]) -> dict:
    schema_props = {
        "enunciado": {"type": "string", "description": "Enunciado completo com contexto profissional realista"},
        "alternativas": {
            "type": "object",
            "properties": {
                "A": {"type": "string"}, "B": {"type": "string"}, "C": {"type": "string"},
                "D": {"type": "string"}, "E": {"type": "string"},
            },
            "required": ["A", "B", "C", "D", "E"],
        },
        "gabarito": {"type": "string", "enum": ["A", "B", "C", "D", "E"]},
        "comentario": {"type": "string", "description": "Explica o gabarito e por que cada alternativa errada está errada"},
        "disciplina": {"type": "string"},
        "dificuldade": {"type": "string", "enum": ["facil", "medio", "dificil"]},
    }
    required = ["enunciado", "alternativas", "gabarito", "comentario", "disciplina", "dificuldade"]
    if bloco_slugs:
        schema_props["bloco_slug"] = {
            "type": "string",
            "enum": bloco_slugs,
            "description": "Slug do bloco temático ao qual a questão pertence (use 'outros' se nenhum se aplicar).",
        }
        required.append("bloco_slug")
    return {
        "name": "registrar_questoes",
        "description": "Registra as questões de múltipla escolha geradas para o dia de estudo, no estilo da banca com cenário realista.",
        "input_schema": {
            "type": "object",
            "properties": {
                "questoes": {
                    "type": "array",
                    "description": "Lista de questões estilo da banca",
                    "items": {"type": "object", "properties": schema_props, "required": required},
                },
            },
            "required": ["questoes"],
        },
    }

_VALIDATION_TOOL = {
    "name": "registrar_flags",
    "description": "Registra inconsistências ou afirmações potencialmente incorretas encontradas no material.",
    "input_schema": {
        "type": "object",
        "properties": {
            "flags": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "tipo": {"type": "string", "enum": ["conteudo", "questao"]},
                        "referencia": {"type": "string"},
                        "descricao": {"type": "string"},
                        "severidade": {"type": "string", "enum": ["alta", "media", "baixa"]}
                    },
                    "required": ["tipo", "referencia", "descricao", "severidade"]
                }
            }
        },
        "required": ["flags"]
    }
}

_VALIDATION_SYSTEM = """Você é um auditor de precisão técnica para materiais de concurso público focado em frameworks de TI.

Sinalize APENAS afirmações com risco real de erro. Seja criterioso — prefira falsos negativos a falsos positivos.

Priorize verificar:
- Nomes exatos de domínios/práticas/objetivos COBIT 2019 e ITIL 4
- Versões confundidas: COBIT 5 vs 2019, ITIL v3 vs v4, PMBOK 6ª vs 7ª, ISO 27001:2013 vs 2022
- Quantidade de controles ISO 27001:2022 (são 93, divididos em 4 categorias)
- Gabarito de questão que contradiz o próprio comentário explicativo
- Códigos de objetivos COBIT (ex: APO, BAI, DSS, MEA) atribuídos ao domínio errado

NÃO sinalize: conceitos gerais corretos, simplificações pedagógicas razoáveis, estilo ou formatação."""

_PRICES = {
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0, "cache_write": 3.75, "cache_read": 0.30},
    "claude-opus-4-7": {"input": 5.0, "output": 25.0, "cache_write": 6.25, "cache_read": 0.50},
}


def _calc_cost(model: str, usage: dict) -> float:
    p = _PRICES.get(model, _PRICES["claude-sonnet-4-6"])
    input_cost = usage.get("input_tokens", 0) * p["input"] / 1_000_000
    output_cost = usage.get("output_tokens", 0) * p["output"] / 1_000_000
    cache_write_cost = usage.get("cache_creation_input_tokens", 0) * p["cache_write"] / 1_000_000
    cache_read_cost = usage.get("cache_read_input_tokens", 0) * p["cache_read"] / 1_000_000
    web_search_cost = usage.get("web_search_requests", 0) * 0.01
    return round(input_cost + output_cost + cache_write_cost + cache_read_cost + web_search_cost, 6)


def _calc_cache_ratio(usage: dict) -> float:
    total_input = (
        usage.get("input_tokens", 0)
        + usage.get("cache_creation_input_tokens", 0)
        + usage.get("cache_read_input_tokens", 0)
    )
    if total_input == 0:
        return 0.0
    return round(usage.get("cache_read_input_tokens", 0) / total_input, 3)


def _build_params(
    topic: str,
    questions_count: int,
    model: str,
    concurso: ConcursoContext,
    examples: list[dict],
    bloco_slugs: list[str] | None = None,
) -> dict:
    user_message = f"""Gere o material de estudo focado **exclusivamente neste tópico**:

**Tópico:** {topic}

Estruture em exatamente 4 seções com esses cabeçalhos:

## 1. Resumo Executivo
O que a banca {concurso.banca} cobra deste tópico, pontos críticos para a prova, frequência em provas anteriores. Seja específico sobre o que costuma cair.

## 2. Conteúdo Aprofundado
Conceitos completos com a estrutura exata que a banca cobra literalmente. Para frameworks (COBIT, ITIL) inclua domínios, práticas, objetivos com seus códigos. Para normas ISO inclua cláusulas e controles. Para padrões GoF/microsserviços inclua quando usar cada um. Contextualize com aplicação prática do cargo "{concurso.cargo}" quando relevante.

## 3. Macetes e Mnemônicos
Técnicas de memorização para estruturas complexas. Analogias com desenvolvimento de software (ex: ITIL SLA ≈ contrato de API). Siglas e sequências que ajudem a lembrar.

## 4. Pegadinhas {concurso.banca}
As alternativas incorretas mais comuns que a banca usa. Confusões típicas de conceito (ex: COBIT vs ITIL, RPO vs RTO). Casos onde quem "sabe o assunto" erra por não conhecer a letra exata do framework. Inclua exemplos de alternativas falsas convincentes.

**Densidade e precisão antes de extensão.** Cada seção no máximo 600 palavras; conteúdo total ≤ 2500 palavras. **Use `web_search` sempre que precisar confirmar códigos, versões, números ou nomes literais antes de afirmar.**

Após as 4 seções, use a ferramenta `registrar_questoes` para gerar exatamente {questions_count} questões estilo {concurso.banca} com:
- Enunciado-cenário realista (contexto profissional de "{concurso.cargo}" no(a) {concurso.orgao})
- 5 alternativas plausíveis (erradas devem ser tentadoras, não óbvias)
- Gabarito correto
- Comentário explicando o raciocínio e por que cada alternativa errada está errada
- O comentário deve ser AUTOCONSISTENTE com o gabarito declarado"""

    # Ordem dos blocos do system: do mais estável (cacheável entre concursos) para o mais variável
    system_blocks = [
        {"type": "text", "text": _BASE_SYSTEM, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": _FCC_METHODOLOGY, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": _ACCURACY_CLAUSE, "cache_control": {"type": "ephemeral"}},
    ]
    examples_block = _fmt_examples_block(concurso.banca, examples)
    if examples_block:
        system_blocks.append({
            "type": "text",
            "text": examples_block,
            "cache_control": {"type": "ephemeral"},
        })
    system_blocks.append({
        "type": "text",
        "text": _fmt_concurso_profile(concurso),
        "cache_control": {"type": "ephemeral"},
    })

    tools = [
        _build_tool(bloco_slugs or []),
        {"type": "web_search_20250305", "name": "web_search", "max_uses": 5},
    ]

    thinking_budget = 6000 if model == "claude-opus-4-7" else 4000

    return {
        "model": model,
        "max_tokens": 16000,
        "system": system_blocks,
        "tools": tools,
        "tool_choice": {"type": "auto"},
        "messages": [{"role": "user", "content": user_message}],
        "thinking": {"type": "enabled", "budget_tokens": thinking_budget},
    }


async def _generate_for_topic(
    topic: str,
    questions_count: int,
    model: str,
    concurso: ConcursoContext,
    examples: list[dict],
    bloco_slugs: list[str] | None = None,
) -> tuple[str, list, dict]:
    """Generate material for a single topic. Returns (content_md, questions, usage)."""
    params = _build_params(topic, questions_count, model, concurso, examples, bloco_slugs)
    response = await _client.messages.create(**params)

    content_md = ""
    questions_data = []

    for block in response.content:
        if block.type == "text":
            content_md += block.text
        elif block.type == "tool_use" and block.name == "registrar_questoes":
            try:
                questions_data = block.input.get("questoes", [])
            except Exception:
                questions_data = []

    usage = response.usage
    web_searches = 0
    server_tool_use = getattr(usage, "server_tool_use", None)
    if server_tool_use:
        web_searches = getattr(server_tool_use, "web_search_requests", 0) or 0

    usage_dict = {
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0) or 0,
        "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
        "web_search_requests": web_searches,
    }

    return content_md, questions_data, usage_dict


async def generate_material(
    topics: list[str],
    concurso: ConcursoContext,
    examples: list[dict],
    model: str = "claude-sonnet-4-6",
    bloco_slugs: list[str] | None = None,
) -> tuple[str, list, dict]:
    """Generate material per-topic in parallel."""
    if not topics:
        return "", [], {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "web_search_requests": 0}

    n = len(topics)
    questions_per_topic = max(5, min(15, math.ceil(15 / n)))

    results = await asyncio.gather(
        *[_generate_for_topic(t, questions_per_topic, model, concurso, examples, bloco_slugs) for t in topics]
    )

    full_md_parts: list[str] = []
    all_questions: list[dict] = []
    total_usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "web_search_requests": 0,
    }

    for topic, (md, questions, usage) in zip(topics, results):
        if n > 1:
            full_md_parts.append(f"# {topic}\n\n{md.strip()}")
        else:
            full_md_parts.append(md.strip())
        all_questions.extend(questions)
        for k in total_usage:
            total_usage[k] += usage.get(k, 0)

    full_md = "\n\n---\n\n".join(full_md_parts)
    return full_md, all_questions, total_usage


# ---- Correção de redação (rubrica FCC) ----

_REDACAO_RUBRICA = """**Rubrica FCC para correção de redação dissertativo-argumentativa (total = 10,0):**

TEMA (7,0 pontos):
- Recorte temático (0,0 – 2,0): clareza do recorte, alinhamento com o enunciado, não tangenciar
- Interpretação crítica dos textos de apoio (0,0 – 2,0): diálogo crítico com os textos, não apenas paráfrase
- Progressão textual (0,0 – 3,0): estrutura argumentativa, encadeamento entre parágrafos, conclusão articulada

NORMA-PADRÃO (3,0 pontos):
- Propriedade vocabular (0,0 – 0,8): adequação léxica, registro formal, evitar repetições
- Coesão (0,0 – 1,6): uso de conectivos, referenciação anafórica/catafórica, articulação intra e inter-parágrafos
- Morfossintaxe (0,0 – 0,6): concordância (verbal e nominal), regência, pontuação, ortografia, crase

**Critérios de zerar (informe em `zerou_motivo` e retorne todas as notas = 0):**
- Fuga total ao tema
- Texto com 7 linhas ou menos
- Texto em outra língua
- Cópia integral de texto pronto ou de algum dos textos de apoio
- Identificação do candidato (nome, assinatura) — improvável aqui, mas observe
- Modalidade diferente da dissertativo-argumentativa (narração, poesia)

**Princípios de avaliação:**
- Seja criterioso. Notas máximas só para texto realmente bom no critério.
- Use 0,1 como unidade mínima. Notas como 1,7 ou 2,3 são válidas.
- O candidato é dev sênior estudando para concurso público; pode soar técnico em alguns trechos. Não penalize tecnicalidade se houver clareza.
- Em `sugestoes`, aponte 3 a 7 problemas pontuais com a linha aproximada do texto e como melhorar."""


def _build_redacao_tool() -> dict:
    return {
        "name": "registrar_correcao",
        "description": "Registra a correção da redação segundo a rubrica FCC.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nota_recorte": {"type": "number", "minimum": 0, "maximum": 2.0},
                "nota_interpretacao": {"type": "number", "minimum": 0, "maximum": 2.0},
                "nota_progressao": {"type": "number", "minimum": 0, "maximum": 3.0},
                "nota_vocabular": {"type": "number", "minimum": 0, "maximum": 0.8},
                "nota_coesao": {"type": "number", "minimum": 0, "maximum": 1.6},
                "nota_morfo": {"type": "number", "minimum": 0, "maximum": 0.6},
                "feedback_geral": {
                    "type": "string",
                    "description": "Parecer geral curto (4 a 8 linhas) destacando pontos fortes e o que mais limita a nota.",
                },
                "sugestoes": {
                    "type": "array",
                    "description": "3 a 7 problemas pontuais ordenados por relevância.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "trecho": {
                                "type": "string",
                                "description": "Fragmento literal do texto do aluno (até 120 chars) que ilustra o problema.",
                            },
                            "problema": {
                                "type": "string",
                                "description": "Descrição curta do problema (max 200 chars).",
                            },
                            "sugestao": {
                                "type": "string",
                                "description": "Como melhorar (max 250 chars). Reescreva o trecho quando útil.",
                            },
                            "categoria": {
                                "type": "string",
                                "enum": ["tema", "estrutura", "vocabular", "coesao", "morfo"],
                            },
                        },
                        "required": ["trecho", "problema", "sugestao", "categoria"],
                    },
                },
                "zerou_motivo": {
                    "type": "string",
                    "description": "Preencher SOMENTE quando o texto se enquadra em algum critério de zerar. Caso contrário, omitir.",
                },
            },
            "required": [
                "nota_recorte", "nota_interpretacao", "nota_progressao",
                "nota_vocabular", "nota_coesao", "nota_morfo",
                "feedback_geral", "sugestoes",
            ],
        },
    }


async def correct_redacao(
    texto: str,
    tema_titulo: str,
    enunciado: str,
    textos_apoio: str | None,
    concurso: ConcursoContext,
    model: str = "claude-sonnet-4-6",
) -> tuple[dict, dict]:
    """Corrige a redação. Retorna (correcao_dict, usage_dict)."""
    linhas = texto.split("\n")
    num_linhas = sum(1 for ln in linhas if ln.strip())

    apoio_block = f"\n\n**Textos de apoio:**\n{textos_apoio}" if textos_apoio else ""
    perfil = _fmt_concurso_profile(concurso)
    user_msg = f"""{perfil}

---

**Tema da redação:** {tema_titulo}

**Enunciado:**
{enunciado}{apoio_block}

---

**Texto submetido pelo aluno ({num_linhas} linhas com conteúdo):**

\"\"\"
{texto}
\"\"\"

Avalie segundo a rubrica FCC e chame a ferramenta `registrar_correcao`."""

    system_blocks = [
        {"type": "text", "text": _BASE_SYSTEM, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": _REDACAO_RUBRICA, "cache_control": {"type": "ephemeral"}},
    ]

    response = await _client.messages.create(
        model=model,
        max_tokens=3500,
        system=system_blocks,
        tools=[_build_redacao_tool()],
        tool_choice={"type": "tool", "name": "registrar_correcao"},
        messages=[{"role": "user", "content": user_msg}],
    )

    correcao: dict = {}
    for block in response.content:
        if block.type == "tool_use" and block.name == "registrar_correcao":
            correcao = dict(block.input)
            break
    if not correcao:
        raise RuntimeError(f"Claude não retornou correcao (stop={response.stop_reason})")

    usage = response.usage
    usage_dict = {
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0) or 0,
        "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
        "web_search_requests": 0,
    }
    return correcao, usage_dict


async def validate_material(content_md: str, questions_data: list) -> list[dict]:
    """Second-pass validation. Returns list of flags (empty = no issues)."""
    questions_json = json.dumps(questions_data[:8], ensure_ascii=False, indent=2)
    user_msg = (
        "Analise o material abaixo. Chame `registrar_flags` com todas as inconsistências encontradas "
        "(ou com `flags: []` se não encontrar problemas).\n\n"
        f"--- CONTEÚDO ---\n{content_md[:12000]}\n\n"
        f"--- QUESTÕES (amostra) ---\n{questions_json[:6000]}"
    )
    try:
        response = await _client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=_VALIDATION_SYSTEM,
            tools=[_VALIDATION_TOOL],
            tool_choice={"type": "tool", "name": "registrar_flags"},
            messages=[{"role": "user", "content": user_msg}],
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == "registrar_flags":
                return block.input.get("flags", [])
    except Exception:
        pass
    return []
