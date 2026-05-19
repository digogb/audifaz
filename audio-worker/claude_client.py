"""Cliente do Claude — gera transcript estruturado Ana/Lucas a partir de markdown."""
import logging
import os
from typing import Optional

from anthropic import AsyncAnthropic, APIError

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
MAX_TOKENS = int(os.environ.get("CLAUDE_MAX_TOKENS", "8000"))

SYSTEM_PROMPT = """Você é um roteirista de podcast educativo em português brasileiro. Recebe material de estudo e produz um diálogo NATURAL entre dois locutores: **Ana** (feminina) e **Lucas** (masculino). O diálogo será lido por TTS — então o roteiro precisa SOAR como conversa real, não como leitura de texto.

# Regras de conteúdo (absolutas)

1. NÃO resuma. O material já é um resumo — sua tarefa é expandi-lo em diálogo didático.
2. Cubra TODOS os tópicos da fonte, na ordem em que aparecem, sem omitir nenhum subitem.
3. Cada conceito da fonte deve virar pelo menos uma troca de fala.
4. Alterne falas entre Ana e Lucas — nunca duas falas seguidas do mesmo locutor.
5. Português brasileiro conversacional, com acentuação completa e correta. Nunca omita acentos.
6. Sem introdução longa nem despedida longa — vá direto ao conteúdo.

# Regras de ritmo e naturalidade (críticas — TTS amplifica problemas)

Como o áudio é sintético, frases compridas e tom uniforme ficam ROBÓTICAS. Para soar natural:

7. **Turnos curtos**: cada fala idealmente entre 1 e 3 frases. Máximo absoluto ~200 caracteres por turno.
8. **Frases curtas**: máximo ~25 palavras por frase. Quebre frases longas com pontos, não com vírgulas.
9. **Variação de tamanho**: misture turnos longos (3 frases) com turnos curtíssimos de reação ("Exato.", "Isso mesmo.", "Olha, boa pergunta.", "Espera, deixa eu ver se entendi.", "Hm, faz sentido.").
10. **Marcadores conversacionais frequentes**: use naturalmente "olha", "veja bem", "então", "ou seja", "tipo assim", "sabe", "certo", "exato", "isso", "boa", "deixa eu...", "espera aí". Use COM PARCIMÔNIA — não vire tique.
11. **Reações genuínas**: quando Lucas fala algo importante, Ana reage ANTES de continuar ("Hm, interessante.", "Ah, essa é boa.", "Espera, deixa eu repetir isso."). E vice-versa.
12. **Perguntas retóricas**: a cada ~3 turnos, um deles puxa o próximo conceito com pergunta ("E qual a diferença disso pro próximo?", "Mas por que isso cai tanto?", "Então e o caso de...?").
13. **Pontuação para prosódia**: use vírgulas para respiração curta, pontos para pausa, reticências... para suspense ou pensamento, exclamações com moderação. Travessões podem ajudar em apostos.
14. **Siglas técnicas**: ao mencionar uma sigla pela primeira vez, soletre-a ("COBIT — cê-ó-bê-i-tê") OU escreva expandido com a sigla depois ("Control Objectives for Information Technologies — o COBIT"). Códigos como "APO12" leia como "A-P-O doze" se mencionado.

# Contexto do ouvinte

Está estudando para o concurso de **Auditor Fiscal de TI da SEFAZ-CE 2026 (banca FCC)**. O material pode cobrir:
- TI: frameworks (COBIT, ITIL, ISO 27001/27002/27005), engenharia de software (GoF, microsserviços, DevOps, DevSecOps), dados (NoSQL, ETL/ELT, Kafka, Data Lake/Warehouse/Mesh), cloud (AWS/Azure/GCP, Kubernetes), segurança (criptografia, PKI, OAuth/OIDC, OWASP), infraestrutura (redes, virtualização, storage), IA/ML/MLOps
- Direito Tributário (CTN, LC 87/123/116, Reforma Tributária IBS/CBS), Constitucional, Administrativo (Lei 14.133, 8.429, 12.527), Civil, Penal, Financeiro (LRF, Lei 4.320), LGPD
- Contabilidade Geral e Pública (MCASP, NBC TSP, NBC TA), Auditoria
- Economia (micro/macro), Matemática Financeira, Estatística, Análise Combinatória, Raciocínio Lógico
- Língua Portuguesa, Redação Oficial
- Legislação Estadual CE (ICMS, ITCD, IPVA, FECOP)

Adapte o tom: técnico em TI, normativo em direito/contabilidade, prático em matemática/português.

# Pegadinhas FCC

Destaque pegadinhas típicas quando identificar uma no material:
- Troca de versões de framework (COBIT 5 vs 2019, ITIL v3 vs v4)
- Datas/números de leis trocados, alíquotas, prazos, exceções
- Palavras absolutas ("sempre", "nunca") versus relativas ("pode", "deve")
- Conceitos parecidos confundidos (OAuth vs OIDC, RPO vs RTO, DW vs Data Lake, ICMS vs ISS)
- Listas com pegadinha (modalidades de extinção do crédito tributário, controles ISO 27002, princípios LIMPE)

Use SEMPRE a ferramenta `submit_transcript` para entregar o diálogo final."""


TRANSCRIPT_TOOL = {
    "name": "submit_transcript",
    "description": "Entrega o transcript final do podcast como lista de turnos alternados entre Ana e Lucas.",
    "input_schema": {
        "type": "object",
        "properties": {
            "turns": {
                "type": "array",
                "description": "Lista ordenada de falas. Deve alternar entre Ana e Lucas, começando por qualquer um.",
                "items": {
                    "type": "object",
                    "properties": {
                        "speaker": {
                            "type": "string",
                            "enum": ["Ana", "Lucas"],
                            "description": "Nome do locutor.",
                        },
                        "text": {
                            "type": "string",
                            "description": "Fala em português brasileiro, acentuação completa, conversacional.",
                            "minLength": 1,
                        },
                    },
                    "required": ["speaker", "text"],
                },
                "minItems": 4,
            }
        },
        "required": ["turns"],
    },
}


class TranscriptError(RuntimeError):
    """Erro ao gerar transcript via Claude."""


def _suggest_turn_count(content_chars: int) -> int:
    """Range de turnos sugerido pelo tamanho do material.

    Turnos curtos (1-3 frases cada) soam mais naturais no TTS. Por isso o
    divisor é baixo: queremos MAIS turnos, cada um mais curto, em vez de
    poucos turnos longos.
    """
    return max(20, min(60, content_chars // 300))


def _validate_turns(turns: list[dict]) -> list[dict]:
    if not turns:
        raise TranscriptError("transcript vazio")
    cleaned: list[dict] = []
    for i, turn in enumerate(turns):
        speaker = turn.get("speaker")
        text = (turn.get("text") or "").strip()
        if speaker not in ("Ana", "Lucas"):
            raise TranscriptError(f"turn {i}: speaker inválido {speaker!r}")
        if not text:
            raise TranscriptError(f"turn {i}: texto vazio")
        cleaned.append({"speaker": speaker, "text": text})
    return cleaned


async def generate_transcript(
    content_md: str,
    instrucoes: Optional[str] = None,
) -> list[dict]:
    """Chama Claude e retorna lista [{speaker, text}, ...] validada."""
    if not ANTHROPIC_API_KEY:
        raise TranscriptError("ANTHROPIC_API_KEY não configurado")

    target_turns = _suggest_turn_count(len(content_md))
    user_msg = (
        f"[Material do dia]\n{content_md}\n\n"
        f"[Instruções específicas]\n{instrucoes or 'Nenhuma instrução adicional.'}\n\n"
        f"Gere o diálogo com aproximadamente {target_turns} turnos curtos "
        "(cada turno = 1 a 3 frases, máx ~200 chars). É melhor MUITOS turnos "
        "curtos do que poucos longos — turnos longos soam robóticos no TTS. "
        "Varie tamanhos: misture turnos de 1 frase com turnos de 2-3 frases, "
        "e turnos de reação curta ('Exato.', 'Hm, interessante.') entre eles. "
        "Use a ferramenta `submit_transcript`."
    )

    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    try:
        resp = await client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=[TRANSCRIPT_TOOL],
            tool_choice={"type": "tool", "name": "submit_transcript"},
            messages=[{"role": "user", "content": user_msg}],
        )
    except APIError as err:
        raise TranscriptError(f"Anthropic API erro: {err}") from err

    for block in resp.content:
        if block.type == "tool_use" and block.name == "submit_transcript":
            turns = block.input.get("turns") if isinstance(block.input, dict) else None
            if not isinstance(turns, list):
                raise TranscriptError(f"tool_use sem turns válidos: {block.input!r}")
            validated = _validate_turns(turns)
            logger.info(
                "transcript gerado: %d turnos (input=%d tokens, output=%d tokens)",
                len(validated),
                resp.usage.input_tokens,
                resp.usage.output_tokens,
            )
            return validated

    raise TranscriptError(f"resposta sem tool_use submit_transcript: {resp.stop_reason}")
