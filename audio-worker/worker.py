"""Worker assíncrono: polla MaterialAudio('pendente') no SQLite, gera mp3 e atualiza status.

Fluxo:
  1. Claim pendente (status='gerando', tentativas+1)
  2. Claude gera transcript estruturado [{speaker, text}, ...]
  3. GCP TTS sintetiza cada turn como mp3
  4. ffmpeg concatena tudo em /data/audios/{audio_id}.mp3
  5. Marca done com duração/tamanho
"""
import asyncio
import logging
import os
import shutil
import signal
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from claude_client import generate_transcript
from db import MaterialAudio, SessionLocal
from tts_client import synthesize_turns

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("audio-worker")

POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "30"))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))
AUDIOS_DIR = Path(os.environ.get("AUDIOS_DIR", "/data/audios"))

_shutdown = asyncio.Event()


def _request_shutdown(*_):
    logger.info("shutdown signal received")
    _shutdown.set()


async def _claim_pending() -> int | None:
    async with SessionLocal() as db:
        stmt = (
            select(MaterialAudio)
            .where(
                MaterialAudio.status == "pendente",
                MaterialAudio.tentativas < MAX_RETRIES,
            )
            .order_by(MaterialAudio.gerado_em)
            .limit(1)
        )
        audio = (await db.execute(stmt)).scalar_one_or_none()
        if not audio:
            return None
        audio.status = "gerando"
        audio.tentativas = (audio.tentativas or 0) + 1
        await db.commit()
        return audio.id


async def _probe_duration(path: Path) -> int | None:
    proc = await asyncio.create_subprocess_exec(
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    stdout, _ = await proc.communicate()
    if proc.returncode != 0:
        return None
    try:
        return int(float(stdout.decode().strip()))
    except (ValueError, AttributeError):
        return None


async def _assemble_mp3(
    turns_audio: list[bytes],
    audio_id: int,
) -> tuple[str, int | None, int]:
    """Concatena mp3s via ffmpeg em /data/audios/{audio_id}.mp3."""
    AUDIOS_DIR.mkdir(parents=True, exist_ok=True)
    work_dir = AUDIOS_DIR / f"_tmp_{audio_id}"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir()

    try:
        parts: list[Path] = []
        for i, audio in enumerate(turns_audio):
            p = work_dir / f"{i:03d}.mp3"
            p.write_bytes(audio)
            parts.append(p)

        list_file = work_dir / "concat.txt"
        list_file.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))

        final_path = AUDIOS_DIR / f"{audio_id}.mp3"
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(final_path),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            err_text = stderr.decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"ffmpeg falhou (rc={proc.returncode}): {err_text}")

        duration = await _probe_duration(final_path)
        size = final_path.stat().st_size
        return str(final_path), duration, size
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


async def _process(audio_id: int):
    async with SessionLocal() as db:
        audio = (
            await db.execute(
                select(MaterialAudio)
                .options(selectinload(MaterialAudio.material))
                .where(MaterialAudio.id == audio_id)
            )
        ).scalar_one()
        content_md = audio.material.conteudo_md
        instrucoes = audio.instrucoes
        material_id = audio.material.id
        concurso = await get_concurso_for_material(db, material_id)
        ctx = ConcursoContext(
            nome=concurso.nome,
            banca=concurso.banca,
            orgao=concurso.orgao,
            cargo=concurso.cargo,
            data_prova=concurso.data_prova,
            prompt_extra=concurso.prompt_extra,
        ) if concurso else None

    logger.info(
        "processing audio id=%s material=%s concurso=%s (%d chars)",
        audio_id, material_id, (concurso.slug if concurso else "?"), len(content_md),
    )

    try:
        transcript = await generate_transcript(content_md, instrucoes, concurso=ctx)
        logger.info("audio id=%s transcript: %d turnos", audio_id, len(transcript))

        def _log_progress(done: int, total: int, size: int):
            logger.info(
                "audio id=%s tts %d/%d (%d KB)",
                audio_id, done, total, size // 1024,
            )

        turns_audio = await synthesize_turns(transcript, on_progress=_log_progress)
        path, duration, size = await _assemble_mp3(turns_audio, audio_id)
        logger.info(
            "audio id=%s pronto: %s (%d bytes, %ss)",
            audio_id, path, size, duration,
        )
    except Exception as exc:
        logger.exception("falha ao gerar áudio id=%s", audio_id)
        async with SessionLocal() as db:
            row = await db.get(MaterialAudio, audio_id)
            if row:
                row.status = "erro" if row.tentativas >= MAX_RETRIES else "pendente"
                row.error_msg = str(exc)[:500]
                await db.commit()
        return

    async with SessionLocal() as db:
        row = await db.get(MaterialAudio, audio_id)
        row.status = "done"
        row.arquivo_path = path
        row.duracao_seg = duration
        row.tamanho_bytes = size
        row.notebooklm_id = None
        row.concluido_em = datetime.utcnow()
        row.error_msg = None
        await db.commit()


async def main():
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _request_shutdown)

    logger.info(
        "worker iniciado — poll a cada %ss, max_retries=%s, audios_dir=%s",
        POLL_INTERVAL, MAX_RETRIES, AUDIOS_DIR,
    )

    while not _shutdown.is_set():
        try:
            audio_id = await _claim_pending()
            if audio_id:
                await _process(audio_id)
                continue
        except Exception:
            logger.exception("erro no tick do worker")

        try:
            await asyncio.wait_for(_shutdown.wait(), timeout=POLL_INTERVAL)
        except asyncio.TimeoutError:
            pass

    logger.info("worker encerrado")


if __name__ == "__main__":
    asyncio.run(main())
