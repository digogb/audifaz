"""Smoke test do pipeline completo: Claude -> TTS -> ffmpeg.

Lê 1 StudyMaterial real do banco audifaz.db, gera o transcript via Claude,
sintetiza via GCP TTS e concatena com ffmpeg. Não escreve no banco.

Uso:
    export ANTHROPIC_API_KEY=...
    export GCP_TTS_API_KEY=...
    python audio-worker/scripts/test_pipeline.py [material_id]   # default 3

Saída: /tmp/audio_pipeline_test/preview.mp3
"""

import asyncio
import logging
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claude_client import generate_transcript  # noqa: E402
from tts_client import synthesize_turns  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("smoke")

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "audifaz.db"
OUT_DIR = Path("/tmp/audio_pipeline_test")


def load_material(material_id: int) -> str:
    con = sqlite3.connect(str(DB_PATH))
    try:
        row = con.execute(
            "SELECT conteudo_md FROM study_materials WHERE id=?", (material_id,)
        ).fetchone()
    finally:
        con.close()
    if not row:
        raise SystemExit(f"material_id={material_id} não encontrado em {DB_PATH}")
    return row[0]


async def assemble(parts: list[bytes]) -> Path:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    paths: list[Path] = []
    for i, audio in enumerate(parts):
        p = OUT_DIR / f"{i:03d}.mp3"
        p.write_bytes(audio)
        paths.append(p)

    list_file = OUT_DIR / "concat.txt"
    list_file.write_text("".join(f"file '{p.resolve()}'\n" for p in paths))

    final = OUT_DIR / "preview.mp3"
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file), "-c", "copy", str(final),
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise SystemExit(f"ffmpeg falhou: {stderr.decode(errors='replace')[:400]}")
    return final


async def main():
    material_id = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    content_md = load_material(material_id)
    logger.info("material_id=%s carregado (%d chars)", material_id, len(content_md))

    logger.info("chamando Claude...")
    transcript = await generate_transcript(content_md)
    logger.info("transcript: %d turnos", len(transcript))
    total_chars = sum(len(t["text"]) for t in transcript)
    logger.info("total chars TTS: %d (~%.1f%% do free tier mensal)",
                total_chars, total_chars / 10_000)

    def progress(done, total, size):
        logger.info("tts %d/%d (%d KB)", done, total, size // 1024)

    logger.info("sintetizando...")
    parts = await synthesize_turns(transcript, on_progress=progress)

    logger.info("concatenando...")
    final = await assemble(parts)

    size_kb = final.stat().st_size / 1024
    logger.info("Pronto: %s (%.1f KB)", final, size_kb)


if __name__ == "__main__":
    asyncio.run(main())
