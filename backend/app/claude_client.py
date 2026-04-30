import json
from anthropic import AsyncAnthropic

_client = AsyncAnthropic()

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
    return round(input_cost + output_cost + cache_write_cost + cache_read_cost, 6)


def _calc_cache_ratio(usage: dict) -> float:
    total_input = (
        usage.get("input_tokens", 0)
        + usage.get("cache_creation_input_tokens", 0)
        + usage.get("cache_read_input_tokens", 0)
    )
    if total_input == 0:
        return 0.0
    return round(usage.get("cache_read_input_tokens", 0) / total_input, 3)


async def generate_material_stream(topics: list[str], model: str = "claude-sonnet-4-6"):
    """Async generator yielding SSE-ready dicts for study material generation."""
    topics_text = "\n".join(f"- {t}" for t in topics)

    user_message = f"""Gere o material de estudo para os tópicos do dia:

{topics_text}

Estruture em exatamente 4 seções com esses cabeçalhos:

## 1. Resumo Executivo
O que a FCC cobra deste tópico, pontos críticos para a prova, frequência nas provas SEFAZ TI anteriores. Seja específico sobre o que costuma cair.

## 2. Conteúdo Aprofundado
Conceitos completos com a estrutura exata que a FCC cobra literalmente. Para frameworks (COBIT, ITIL) inclua domínios, práticas, objetivos com seus códigos. Para normas ISO inclua cláusulas e controles. Para padrões GoF/microsserviços inclua quando usar cada um. Contextualize com aplicação fiscal/tributária quando relevante.

## 3. Macetes e Mnemônicos
Técnicas de memorização para estruturas complexas. Analogias com desenvolvimento de software (ex: ITIL SLA ≈ contrato de API). Siglas e sequências que ajudem a lembrar.

## 4. Pegadinhas FCC
As alternativas incorretas mais comuns que a banca usa. Confusões típicas de conceito (ex: COBIT vs ITIL, RPO vs RTO). Casos onde quem "sabe o assunto" erra por não conhecer a letra exata do framework. Inclua exemplos de alternativas falsas convincentes.

Após as 4 seções, use a ferramenta `registrar_questoes` para gerar exatamente 15 questões estilo FCC com:
- Enunciado-cenário realista (contexto de Auditor Fiscal da SEFAZ)
- 5 alternativas plausíveis (alternativas erradas devem ser tentadoras, não óbvias)
- Gabarito correto
- Comentário explicando o raciocínio e por que cada alternativa errada está errada"""

    system_blocks = [
        {"type": "text", "text": _SYSTEM_PROFILE, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": _FCC_METHODOLOGY, "cache_control": {"type": "ephemeral"}},
    ]

    params: dict = {
        "model": model,
        "max_tokens": 10000,
        "system": system_blocks,
        "tools": [_TOOL],
        "tool_choice": {"type": "auto"},
        "messages": [{"role": "user", "content": user_message}],
    }

    if model == "claude-opus-4-7":
        params["thinking"] = {"type": "adaptive"}
        params["output_config"] = {"effort": "high"}
    else:
        params["output_config"] = {"effort": "medium"}

    in_tool_use = False
    tool_input_buffer = ""

    async with _client.messages.stream(**params) as stream:
        async for event in stream:
            if event.type == "content_block_start":
                if event.content_block.type == "tool_use":
                    in_tool_use = True
                    tool_input_buffer = ""

            elif event.type == "content_block_delta":
                if event.delta.type == "text_delta":
                    yield {"type": "content", "chunk": event.delta.text}
                elif event.delta.type == "input_json_delta" and in_tool_use:
                    tool_input_buffer += event.delta.partial_json

            elif event.type == "content_block_stop":
                if in_tool_use and tool_input_buffer:
                    try:
                        questions = json.loads(tool_input_buffer).get("questoes", [])
                        yield {"type": "questions", "data": questions}
                    except (json.JSONDecodeError, AttributeError):
                        yield {"type": "questions", "data": []}
                    in_tool_use = False
                    tool_input_buffer = ""

        final = stream.get_final_message()
        usage = final.usage
        usage_dict = {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0) or 0,
            "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
        }
        yield {
            "type": "done",
            "usage": usage_dict,
            "custo_usd": _calc_cost(model, usage_dict),
            "cache_hit_ratio": _calc_cache_ratio(usage_dict),
        }
