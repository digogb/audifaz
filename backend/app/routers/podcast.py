import os
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import MaterialAudio, StudyDay, StudyMaterial, User, Week, Phase, Concurso

router = APIRouter(prefix="/api/podcast", tags=["podcast"])

MAX_EPISODES = 100


def _public_base_url() -> str:
    return os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")


def _render_rss(rows, base_url: str, token: str, username: str) -> str:
    items_xml = []
    for audio, data_dia in rows:
        title = f"AudiFaz — {data_dia.strftime('%d/%m/%Y')}"
        when = audio.concluido_em or audio.gerado_em
        pub = format_datetime(when)
        mp3_url = f"{base_url}/api/podcast/{token}/audio/{audio.id}.mp3"
        size = audio.tamanho_bytes or 0
        duracao = audio.duracao_seg or 0
        items_xml.append(
            f"""    <item>
      <title>{escape(title)}</title>
      <description>Podcast de estudo — Auditor TI SEFAZ-CE 2026</description>
      <pubDate>{pub}</pubDate>
      <guid isPermaLink="false">audifaz-{audio.id}</guid>
      <enclosure url="{escape(mp3_url, {'"': '&quot;'})}" length="{size}" type="audio/mpeg"/>
      <itunes:duration>{duracao}</itunes:duration>
      <itunes:explicit>false</itunes:explicit>
    </item>"""
        )

    feed_link = f"{base_url}/api/podcast/{token}/feed.xml"
    title_channel = f"AudiFaz — {escape(username)}"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{title_channel}</title>
    <link>{base_url or feed_link}</link>
    <atom:link href="{escape(feed_link, {'"': '&quot;'})}" rel="self" type="application/rss+xml"/>
    <description>Podcasts diários de estudo — Auditor Fiscal TI SEFAZ-CE 2026 (banca FCC)</description>
    <language>pt-BR</language>
    <itunes:author>AudiFaz</itunes:author>
    <itunes:explicit>false</itunes:explicit>
    <itunes:category text="Education"/>
    <itunes:summary>Resumos diários do plano de estudos no formato podcast.</itunes:summary>
{chr(10).join(items_xml)}
  </channel>
</rss>
"""


@router.get("/{token}/feed.xml")
async def rss_feed(token: str, db: AsyncSession = Depends(get_db)):
    user = (
        await db.execute(select(User).where(User.podcast_token == token))
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(404)

    if not user.concurso_atual_id:
        raise HTTPException(404, "Usuário sem concurso ativo")

    stmt = (
        select(MaterialAudio, StudyDay.data)
        .join(StudyMaterial, MaterialAudio.study_material_id == StudyMaterial.id)
        .join(StudyDay, StudyMaterial.study_day_id == StudyDay.id)
        .join(Week, StudyDay.week_id == Week.id)
        .join(Phase, Week.phase_id == Phase.id)
        .where(MaterialAudio.status == "done", Phase.concurso_id == user.concurso_atual_id)
        .order_by(StudyDay.data.desc())
        .limit(MAX_EPISODES)
    )
    rows = (await db.execute(stmt)).all()

    base = _public_base_url()
    xml = _render_rss(rows, base, token, user.username)
    return Response(
        content=xml,
        media_type="application/rss+xml; charset=utf-8",
        headers={"Cache-Control": "private, max-age=300"},
    )


@router.get("/{token}/audio/{audio_id}.mp3")
async def serve_audio(
    token: str,
    audio_id: int,
    db: AsyncSession = Depends(get_db),
):
    user = (
        await db.execute(select(User).where(User.podcast_token == token))
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(404)

    # Confirma que o áudio pertence ao concurso atual do usuário (defesa contra
    # adivinhação de IDs entre concursos)
    if user.concurso_atual_id:
        owns = await db.execute(
            select(MaterialAudio.id)
            .join(StudyMaterial, MaterialAudio.study_material_id == StudyMaterial.id)
            .join(StudyDay, StudyMaterial.study_day_id == StudyDay.id)
            .join(Week, StudyDay.week_id == Week.id)
            .join(Phase, Week.phase_id == Phase.id)
            .where(MaterialAudio.id == audio_id, Phase.concurso_id == user.concurso_atual_id)
        )
        if not owns.scalar_one_or_none():
            raise HTTPException(404)

    audio = await db.get(MaterialAudio, audio_id)
    if not audio or audio.status != "done" or not audio.arquivo_path:
        raise HTTPException(404)

    path = Path(audio.arquivo_path)
    if not path.exists():
        raise HTTPException(404, "Arquivo de áudio não encontrado no disco")

    return FileResponse(
        str(path),
        media_type="audio/mpeg",
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "private, max-age=86400",
        },
    )
