import asyncio
import json
import math
from pathlib import Path
from anthropic import AsyncAnthropic

_client = AsyncAnthropic()

_EXAMPLES_PATH = Path(__file__).parent / "fcc_examples.json"


def _load_fcc_examples() -> list[dict]:
    if not _EXAMPLES_PATH.exists():
        return []
    try:
        data = json.loads(_EXAMPLES_PATH.read_text(encoding="utf-8"))
        return [q for q in data.get("questoes", []) if q.get("enunciado")]
    except Exception:
        return []


def _fmt_examples_block(questoes: list[dict]) -> str:
    lines = ["**Questões reais das provas de referência FCC — use para calibrar estilo, conteúdo e gabaritos:**\n"]
    for i, q in enumerate(questoes[:12], 1):
        prova = q.get("prova", "")
        ano = q.get("ano", "")
        disciplina = q.get("disciplina", "")
        lines.append(f"**Q{i}** ({prova} {ano} — {disciplina})")
        lines.append(q.get("enunciado", ""))
        for alt, txt in q.get("alternativas", {}).items():
            lines.append(f"{alt}) {txt}")
        gab = q.get("gabarito", "").strip()
        if gab:
            lines.append(f"Gabarito: {gab}")
        lines.append("")
    return "\n".join(lines)

_SYSTEM_PROFILE = """Você é um assistente de estudos especializado em concursos públicos brasileiros, com foco na banca FCC (Fundação Carlos Chagas).

**Perfil do candidato:**
- Desenvolvedor Sênior com 23 anos de experiência em TI
- Concurso: Auditor Fiscal de TI — SEFAZ-CE 2026 (cargo B02)
- Banca: FCC (Fundação Carlos Chagas)
- Provas: Objetiva Gerais 01/08/2026 | Objetiva Específicos + Discursiva 02/08/2026
- Referências: SEFAZ-BA 2019 (FCC TI), SEFAZ-SP 2026 (FCC TI), SEFAZ-PI 2025 (FCC TI)

**Abordagem:**
- Candidato é dev sênior: contextualize conceitos com experiência prática quando útil
- Foco em acertar questões FCC, não em aprendizado acadêmico geral
- Seja denso e direto — ele não precisa de explicações básicas de TI, mas precisa das literalidades dos frameworks e normas
- Para provas discursivas: estrutura FCC — contexto (3 linhas) → fundamentação técnica citando norma/framework (8 linhas) → proposta/conclusão (4 linhas)"""

_FCC_METHODOLOGY = """**Como a FCC elabora questões de TI (inteligência de banca):**

1. **Enunciado-cenário:** "Um Auditor Fiscal da área de TI..." — identifique qual conceito está sendo testado
2. **Literalidade de frameworks:** COBIT e ITIL cobram nomes exatos de domínios, processos, práticas e objetivos (ex: "Qual domínio do COBIT 2019 contém APO12?")
3. **ISO 27001/27002:** Cobra os 93 controles por categoria (organizacional, pessoas, físico, tecnológico), diferença entre requisitos (27001) e guia (27002), processo ISO 27005
4. **Engenharia de Software:** GoF (qual padrão resolve qual problema), microsserviços (CQRS vs Saga vs Circuit Breaker), testes (qual tipo em cada situação)
5. **Dados:** Definições exatas DW vs Data Mart vs Data Lake vs Lakehouse, esquemas estrela/floco, SQL com window functions em contexto de auditoria fiscal
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
- gov.br e sites de SEFAZ para legislação tributária e fiscal
- nist.gov para SP 800-* e cybersecurity

**Política de citação:** quando você usar um fato vindo de uma busca, cite brevemente "(fonte: <domínio>)" no comentário da questão ou ao final da seção. Não cite ao usar conhecimento geral consolidado.

**Importante:** faça as buscas primeiro, depois produza o conteúdo final completo. Não intercale narração de busca com o conteúdo entregue ao usuário."""

_TOOL = {
    "name": "registrar_questoes",
    "description": "Registra as 15 questões de múltipla escolha geradas para o dia de estudo, no estilo FCC com cenário realista.",
    "input_schema": {
        "type": "object",
        "properties": {
            "questoes": {
                "type": "array",
                "description": "Lista com exatamente 15 questões estilo FCC",
                "items": {
                    "type": "object",
                    "properties": {
                        "enunciado": {
                            "type": "string",
                            "description": "Enunciado completo com contexto (ex: 'Um Auditor Fiscal de TI da SEFAZ-CE precisa...')"
                        },
                        "alternativas": {
                            "type": "object",
                            "properties": {
                                "A": {"type": "string"},
                                "B": {"type": "string"},
                                "C": {"type": "string"},
                                "D": {"type": "string"},
                                "E": {"type": "string"}
                            },
                            "required": ["A", "B", "C", "D", "E"]
                        },
                        "gabarito": {
                            "type": "string",
                            "enum": ["A", "B", "C", "D", "E"]
                        },
                        "comentario": {
                            "type": "string",
                            "description": "Explica o gabarito e por que cada alternativa errada está errada"
                        },
                        "disciplina": {"type": "string"},
                        "dificuldade": {
                            "type": "string",
                            "enum": ["facil", "medio", "dificil"]
                        }
                    },
                    "required": ["enunciado", "alternativas", "gabarito", "comentario", "disciplina", "dificuldade"]
                }
            }
        },
        "required": ["questoes"]
    }
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
                        "referencia": {"type": "string", "description": "ex: 'Seção 2', 'Questão 5'"},
                        "descricao": {"type": "string", "description": "O que está potencialmente errado e por quê"},
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
- Nomes exatos de domínios/práticas/objetivos COBIT 2019 e ITIL 4 (atribuição ao framework errado é armadilha clássica)
- Versões confundidas: COBIT 5 vs 2019, ITIL v3 vs v4, PMBOK 6ª vs 7ª, ISO 27001:2013 vs 2022
- Quantidade de controles ISO 27001:2022 (são 93, divididos em 4 categorias — não 114 da versão 2013)
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
    # Web search server tool: $10 / 1k requests
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


def _build_params(topic: str, questions_count: int, model: str) -> dict:
    user_message = f"""Gere o material de estudo focado **exclusivamente neste tópico**:

**Tópico:** {topic}

Estruture em exatamente 4 seções com esses cabeçalhos:

## 1. Resumo Executivo
O que a FCC cobra deste tópico, pontos críticos para a prova, frequência nas provas SEFAZ TI anteriores. Seja específico sobre o que costuma cair.

## 2. Conteúdo Aprofundado
Conceitos completos com a estrutura exata que a FCC cobra literalmente. Para frameworks (COBIT, ITIL) inclua domínios, práticas, objetivos com seus códigos. Para normas ISO inclua cláusulas e controles. Para padrões GoF/microsserviços inclua quando usar cada um. Contextualize com aplicação fiscal/tributária quando relevante.

## 3. Macetes e Mnemônicos
Técnicas de memorização para estruturas complexas. Analogias com desenvolvimento de software (ex: ITIL SLA ≈ contrato de API). Siglas e sequências que ajudem a lembrar.

## 4. Pegadinhas FCC
As alternativas incorretas mais comuns que a banca usa. Confusões típicas de conceito (ex: COBIT vs ITIL, RPO vs RTO). Casos onde quem "sabe o assunto" erra por não conhecer a letra exata do framework. Inclua exemplos de alternativas falsas convincentes.

**Densidade e precisão antes de extensão.** Cada seção no máximo 600 palavras; conteúdo total ≤ 2500 palavras. **Use `web_search` sempre que precisar confirmar códigos, versões, números ou nomes literais antes de afirmar.**

Após as 4 seções, use a ferramenta `registrar_questoes` para gerar exatamente {questions_count} questões estilo FCC com:
- Enunciado-cenário realista (contexto de Auditor Fiscal da SEFAZ)
- 5 alternativas plausíveis (erradas devem ser tentadoras, não óbvias)
- Gabarito correto
- Comentário explicando o raciocínio e por que cada alternativa errada está errada
- O comentário deve ser AUTOCONSISTENTE com o gabarito declarado"""

    system_blocks = [
        {"type": "text", "text": _SYSTEM_PROFILE, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": _FCC_METHODOLOGY, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": _ACCURACY_CLAUSE, "cache_control": {"type": "ephemeral"}},
    ]

    examples = _load_fcc_examples()
    if examples:
        system_blocks.append({
            "type": "text",
            "text": _fmt_examples_block(examples),
            "cache_control": {"type": "ephemeral"},
        })

    tools = [
        _TOOL,
        {"type": "web_search_20250305", "name": "web_search", "max_uses": 5},
    ]

    thinking_budget = 6000 if model == "claude-opus-4-7" else 4000

    params: dict = {
        "model": model,
        "max_tokens": 16000,
        "system": system_blocks,
        "tools": tools,
        "tool_choice": {"type": "auto"},
        "messages": [{"role": "user", "content": user_message}],
        "thinking": {"type": "enabled", "budget_tokens": thinking_budget},
    }

    return params


async def _generate_for_topic(topic: str, questions_count: int, model: str) -> tuple[str, list, dict]:
    """Generate material for a single topic. Returns (content_md, questions, usage)."""
    params = _build_params(topic, questions_count, model)
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


async def generate_material(topics: list[str], model: str = "claude-sonnet-4-6") -> tuple[str, list, dict]:
    """Generate material per-topic in parallel. Aggregates content, questions and usage."""
    if not topics:
        return "", [], {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "web_search_requests": 0}

    n = len(topics)
    questions_per_topic = max(5, min(15, math.ceil(15 / n)))

    results = await asyncio.gather(
        *[_generate_for_topic(topic, questions_per_topic, model) for topic in topics]
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


async def validate_material(content_md: str, questions_data: list) -> list[dict]:
    """Second-pass validation. Returns list of flags (empty = no issues found)."""
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


