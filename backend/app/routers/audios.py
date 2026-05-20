import os
import secrets
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_admin_user, get_current_user, get_current_concurso, require_active_subscription
from ..db import get_db
from ..models import MaterialAudio, StudyDay, StudyMaterial, User, Week, Phase, Concurso
from ..schemas import MaterialAudioOut, PodcastTokenOut

router = APIRouter(tags=["audios"])


def _public_base_url() -> str:
    return os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")


def _audio_url_for(audio: MaterialAudio, token: Optional[str]) -> Optional[str]:
    if audio.status != "done" or not token:
        return None
    base = _public_base_url()
    path = f"/api/podcast/{token}/audio/{audio.id}.mp3"
    return f"{base}{path}" if base else path


def _to_out(audio: MaterialAudio, token: Optional[str]) -> MaterialAudioOut:
    return MaterialAudioOut(
        id=audio.id,
        status=audio.status,
        arquivo_url=_audio_url_for(audio, token),
        duracao_seg=audio.duracao_seg,
        tamanho_bytes=audio.tamanho_bytes,
        gerado_em=audio.gerado_em,
        concluido_em=audio.concluido_em,
        error_msg=audio.error_msg,
        tentativas=audio.tentativas,
    )


async def _get_audio_for_day(db: AsyncSession, day_id: int, concurso_id: int) -> Optional[MaterialAudio]:
    stmt = (
        select(MaterialAudio)
        .join(StudyMaterial, MaterialAudio.study_material_id == StudyMaterial.id)
        .join(StudyDay, StudyMaterial.study_day_id == StudyDay.id)
        .join(Week, StudyDay.week_id == Week.id)
        .join(Phase, Week.phase_id == Phase.id)
        .where(StudyMaterial.study_day_id == day_id, Phase.concurso_id == concurso_id)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


@router.get("/api/days/{day_id}/audio", response_model=Optional[MaterialAudioOut])
async def get_audio(
    day_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    concurso: Concurso = Depends(get_current_concurso),
):
    audio = await _get_audio_for_day(db, day_id, concurso.id)
    if not audio:
        return None
    return _to_out(audio, current_user.podcast_token)


@router.post("/api/days/{day_id}/audio/generate", response_model=MaterialAudioOut, status_code=202)
async def trigger_audio(
    day_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
    _: User = Depends(require_active_subscription),
    concurso: Concurso = Depends(get_current_concurso),
):
    owns = await db.execute(
        select(StudyDay.id)
        .join(Week, StudyDay.week_id == Week.id)
        .join(Phase, Week.phase_id == Phase.id)
        .where(StudyDay.id == day_id, Phase.concurso_id == concurso.id)
    )
    if not owns.scalar_one_or_none():
        raise HTTPException(404, "Dia não encontrado")
    day = await db.get(StudyDay, day_id)
    if not day:
        raise HTTPException(404, "Dia não encontrado")

    material = (
        await db.execute(
            select(StudyMaterial).where(StudyMaterial.study_day_id == day_id)
        )
    ).scalar_one_or_none()
    if not material:
        raise HTTPException(400, "Material ainda não foi gerado")
    if material.status != "done":
        raise HTTPException(400, "Material precisa estar concluído antes de gerar áudio")

    audio = (
        await db.execute(
            select(MaterialAudio).where(MaterialAudio.study_material_id == material.id)
        )
    ).scalar_one_or_none()

    if audio and audio.status in ("pendente", "gerando"):
        raise HTTPException(409, f"Áudio já está {audio.status}")

    if audio:
        audio.status = "pendente"
        audio.error_msg = None
        audio.arquivo_path = None
        audio.duracao_seg = None
        audio.tamanho_bytes = None
        audio.notebooklm_id = None
        audio.gerado_em = datetime.utcnow()
        audio.concluido_em = None
    else:
        audio = MaterialAudio(
            study_material_id=material.id,
            status="pendente",
        )
        db.add(audio)

    await db.commit()
    await db.refresh(audio)
    return _to_out(audio, current_user.podcast_token)


@router.post("/api/podcast/regenerate-token", response_model=PodcastTokenOut)
async def regenerate_podcast_token(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.podcast_token = secrets.token_urlsafe(32)
    await db.commit()
    base = _public_base_url()
    feed_path = f"/api/podcast/{current_user.podcast_token}/feed.xml"
    return PodcastTokenOut(
        token=current_user.podcast_token,
        feed_url=f"{base}{feed_path}" if base else feed_path,
    )


@router.get("/api/podcast/me", response_model=PodcastTokenOut)
async def my_podcast_feed(
    current_user: User = Depends(get_current_user),
):
    if not current_user.podcast_token:
        raise HTTPException(404, "Token ainda não gerado")
    base = _public_base_url()
    feed_path = f"/api/podcast/{current_user.podcast_token}/feed.xml"
    return PodcastTokenOut(
        token=current_user.podcast_token,
        feed_url=f"{base}{feed_path}" if base else feed_path,
    )
