"""Cliente da Google Cloud Text-to-Speech — sintetiza um turn → mp3 bytes."""
import asyncio
import base64
import logging
import os

import httpx

logger = logging.getLogger(__name__)

GCP_TTS_API_KEY = os.environ.get("GCP_TTS_API_KEY", "")
GCP_TTS_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"

VOICE_ANA = os.environ.get("VOICE_ANA", "pt-BR-Chirp3-HD-Kore")
VOICE_LUCAS = os.environ.get("VOICE_LUCAS", "pt-BR-Chirp3-HD-Charon")

RETRY_STATUS = {408, 429, 500, 502, 503, 504}


class TTSError(RuntimeError):
    """Erro propagado pela API GCP TTS."""


def voice_for(speaker: str) -> str:
    if speaker == "Ana":
        return VOICE_ANA
    if speaker == "Lucas":
        return VOICE_LUCAS
    raise TTSError(f"speaker desconhecido: {speaker!r}")


async def synthesize(
    text: str,
    voice: str,
    client: httpx.AsyncClient,
    max_retries: int = 4,
) -> bytes:
    """Sintetiza um turn e retorna mp3 bytes."""
    if not GCP_TTS_API_KEY:
        raise TTSError("GCP_TTS_API_KEY não configurado")

    payload = {
        "input": {"text": text},
        "voice": {"languageCode": "pt-BR", "name": voice},
        "audioConfig": {"audioEncoding": "MP3"},
    }

    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = await client.post(
                GCP_TTS_URL,
                params={"key": GCP_TTS_API_KEY},
                json=payload,
                timeout=30.0,
            )
        except httpx.RequestError as err:
            last_err = err
            wait = 2 * attempt
            logger.warning("TTS request erro tentativa %d: %s (retry em %ss)", attempt, err, wait)
            await asyncio.sleep(wait)
            continue

        if resp.status_code == 200:
            data = resp.json()
            audio_b64 = data.get("audioContent")
            if not audio_b64:
                raise TTSError(f"resposta 200 sem audioContent: {data}")
            return base64.b64decode(audio_b64)

        body = resp.text[:300]
        last_err = TTSError(f"HTTP {resp.status_code}: {body}")
        if resp.status_code in RETRY_STATUS and attempt < max_retries:
            wait = 2 * attempt
            logger.warning("TTS %s tentativa %d (retry em %ss): %s", resp.status_code, attempt, wait, body)
            await asyncio.sleep(wait)
            continue
        raise last_err

    raise TTSError(f"falha após {max_retries} tentativas: {last_err}")


async def synthesize_turns(
    turns: list[dict],
    on_progress=None,
) -> list[bytes]:
    """Sintetiza todos os turnos sequencialmente. Retorna lista de mp3 bytes na mesma ordem."""
    async with httpx.AsyncClient() as client:
        result: list[bytes] = []
        for idx, turn in enumerate(turns):
            voice = voice_for(turn["speaker"])
            audio = await synthesize(turn["text"], voice, client)
            result.append(audio)
            if on_progress:
                on_progress(idx + 1, len(turns), len(audio))
        return result
