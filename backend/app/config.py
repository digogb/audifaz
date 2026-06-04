import os


def audio_enabled() -> bool:
    """Feature flag do podcast/áudio.

    Default FALSE: produção não deploya o `audio-worker`, então registros de
    áudio nunca saem de 'pendente' e a UI ficaria presa em "Gerando podcast...".
    Em dev (com worker rodando) setar AUDIO_ENABLED=true — ver
    docker-compose.override.yml.
    """
    return os.environ.get("AUDIO_ENABLED", "").strip().lower() in ("1", "true", "yes")
