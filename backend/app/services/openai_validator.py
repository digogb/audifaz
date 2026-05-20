"""Cross-provider validator: usa OpenAI GPT para auditar material gerado pelo Claude.

Por que cross-provider: Claude validando Claude tem viés alto (mesmo treino, mesmas
ambiguidades). Um modelo de outro provider (OpenAI) tem priors diferentes, pega
erros que Claude deixou passar — especialmente em domínio normativo (códigos exatos
de leis, números de processos, versões de framework).

A validação roda DEPOIS da geração, com tool/function calling forçado pra garantir
formato estruturado. Custo típico: ~$0.003 por validação (GPT-5-mini).
"""
import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_VALIDATOR_MODEL = os.environ.get("OPENAI_VALIDATOR_MODEL", "gpt-5-mini")


_SYSTEM = """Você é um auditor de precisão técnica para materiais de concurso público focado em frameworks de TI e direito administrativo brasileiro.

Você recebe material gerado por uma OUTRA IA e tem a tarefa de detectar erros factuais com risco real de fazer o candidato perder questão na prova.

Priorize sinalizar:
- Nomes/códigos errados de domínios/práticas/objetivos COBIT 2019 e ITIL 4 (ex: APO12 atribuído ao domínio errado)
- Versões confundidas: COBIT 5 vs 2019, ITIL v3 vs v4, PMBOK 6 vs 7, ISO 27001:2013 vs 2022
- Quantidade incorreta de controles ISO 27001:2022 (são 93, em 4 categorias — não 114 da versão 2013)
- Gabarito de questão que contradiz o próprio comentário explicativo
- Números de leis, datas, alíquotas, prazos trocados (LGPD 13.709/2018; Lei 14.133/2021; Reforma Tributária EC 132/2023; etc.)
- Nomes de resoluções/portarias do CNJ atribuídos errado (335/2020 PDPJ; 396/2021 ENSEC-PJ; 522/2023 MoReq-Jus)
- Confusões clássicas: OAuth 2.0 vs OIDC; RPO vs RTO; DW vs Data Lake; SOA vs microsserviços

Severidade:
- alta: erro que faz o candidato marcar alternativa errada em prova
- media: imprecisão que não muda o gabarito mas confunde estudo (ex: definição imprecisa)
- baixa: simplificação pedagógica aceitável ou ambiguidade textual

NÃO sinalize: conceitos gerais corretos, estilo, formatação, omissão pedagógica razoável."""


_TOOL = {
    "type": "function",
    "function": {
        "name": "registrar_flags",
        "description": "Registra erros factuais encontrados no material auditado.",
        "parameters": {
            "type": "object",
            "properties": {
                "flags": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "tipo": {"type": "string", "enum": ["conteudo", "questao"]},
                            "referencia": {"type": "string", "description": "ex: 'Seção 2', 'Questão 5'"},
                            "descricao": {"type": "string", "description": "O que está incorreto e qual é a versão correta segundo fonte oficial"},
                            "severidade": {"type": "string", "enum": ["alta", "media", "baixa"]},
                        },
                        "required": ["tipo", "referencia", "descricao", "severidade"],
                    },
                }
            },
            "required": ["flags"],
        },
    },
}


async def validate_with_openai(content_md: str, questions_data: list) -> list[dict]:
    """Cross-provider validation. Retorna lista de flags. [] se sem problemas ou erro."""
    if not OPENAI_API_KEY:
        logger.info("OPENAI_API_KEY não configurada; cross-validation desabilitada")
        return []

    try:
        from openai import AsyncOpenAI, APIError
    except ImportError:
        logger.warning("openai sdk não instalado; cross-validation desabilitada")
        return []

    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    questions_json = json.dumps(questions_data[:8], ensure_ascii=False, indent=2)
    user_msg = (
        "Analise o material abaixo gerado por outra IA. "
        "Chame `registrar_flags` com todas as inconsistências factuais relevantes "
        "(ou com flags: [] se não encontrar problemas com risco real).\n\n"
        f"--- CONTEÚDO ---\n{content_md[:12000]}\n\n"
        f"--- QUESTÕES (amostra) ---\n{questions_json[:6000]}"
    )

    # Modelos GPT-5 e o-series usam max_completion_tokens; modelos antigos usam max_tokens.
    # Tentamos o novo primeiro e caímos pro antigo se o servidor recusar.
    base_kwargs = dict(
        model=OPENAI_VALIDATOR_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        tools=[_TOOL],
        tool_choice={"type": "function", "function": {"name": "registrar_flags"}},
    )
    try:
        try:
            resp = await client.chat.completions.create(
                **base_kwargs, max_completion_tokens=1500,
            )
        except APIError as exc:
            # Modelos antigos (gpt-4o, gpt-4-turbo etc.) rejeitam max_completion_tokens
            if "max_completion_tokens" in str(exc):
                resp = await client.chat.completions.create(
                    **base_kwargs, max_tokens=1500,
                )
            else:
                raise
    except APIError as exc:
        logger.error("OpenAI validation falhou: %s", exc)
        return []
    except Exception as exc:
        logger.exception("OpenAI validation erro inesperado: %s", exc)
        return []

    msg = resp.choices[0].message if resp.choices else None
    if not msg or not msg.tool_calls:
        return []
    try:
        args = json.loads(msg.tool_calls[0].function.arguments)
        flags = args.get("flags", [])
        if not isinstance(flags, list):
            return []
        return flags
    except (json.JSONDecodeError, KeyError, AttributeError, IndexError):
        return []
