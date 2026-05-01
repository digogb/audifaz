from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import StudyDay, Topic, Week, Phase, User
from ..schemas import StudyDayOut, StudyDayWithPhase
from ..auth import get_current_user

router = APIRouter(prefix="/api/days", tags=["days"])

TZ = ZoneInfo("America/Fortaleza")


def _today():
    return datetime.now(TZ).date()


async def _load_day(db: AsyncSession, day_id: int) -> StudyDay:
    result = await db.execute(
        select(StudyDay)
        .options(
            selectinload(StudyDay.topics),
            selectinload(StudyDay.week).selectinload(Week.phase),
        )
        .where(StudyDay.id == day_id)
    )
    day = result.scalar_one_or_none()
    if not day:
        raise HTTPException(404, "Dia não encontrado")
    return day


@router.get("/today", response_model=StudyDayWithPhase)
async def get_today(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    today = _today()
    result = await db.execute(
        select(StudyDay)
        .options(
            selectinload(StudyDay.topics),
            selectinload(StudyDay.week).selectinload(Week.phase),
        )
        .where(StudyDay.data == today)
    )
    day = result.scalar_one_or_none()
    if not day:
        # Return nearest future day
        result = await db.execute(
            select(StudyDay)
            .options(
                selectinload(StudyDay.topics),
                selectinload(StudyDay.week).selectinload(Week.phase),
            )
            .where(StudyDay.data >= today)
            .order_by(StudyDay.data)
            .limit(1)
        )
        day = result.scalar_one_or_none()
    if not day:
        raise HTTPException(404, "Nenhum dia de estudo encontrado")

    out = StudyDayWithPhase.model_validate(day)
    if day.week and day.week.phase:
        from ..schemas import PhaseOut
        out.phase = PhaseOut.model_validate(day.week.phase)
    return out


@router.get("/{day_id}", response_model=StudyDayWithPhase)
async def get_day(day_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    day = await _load_day(db, day_id)
    out = StudyDayWithPhase.model_validate(day)
    if day.week and day.week.phase:
        from ..schemas import PhaseOut
        out.phase = PhaseOut.model_validate(day.week.phase)
    return out


@router.get("/by-date/{date_str}", response_model=StudyDayWithPhase)
async def get_day_by_date(date_str: str, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    from datetime import date as date_type
    try:
        target = date_type.fromisoformat(date_str)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(400, "Data inválida, use YYYY-MM-DD")
    result = await db.execute(
        select(StudyDay)
        .options(
            selectinload(StudyDay.topics),
            selectinload(StudyDay.week).selectinload(Week.phase),
        )
        .where(StudyDay.data == target)
    )
    day = result.scalar_one_or_none()
    if not day:
        from fastapi import HTTPException
        raise HTTPException(404, "Dia não encontrado")
    out = StudyDayWithPhase.model_validate(day)
    if day.week and day.week.phase:
        from ..schemas import PhaseOut
        out.phase = PhaseOut.model_validate(day.week.phase)
    return out


@router.put("/{day_id}/status")
async def update_status(day_id: int, body: dict, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    day = await db.get(StudyDay, day_id)
    if not day:
        raise HTTPException(404)
    status = body.get("status")
    if status not in ("pendente", "em_andamento", "concluido"):
        raise HTTPException(400, "Status inválido")
    day.status = status
    await db.commit()
    return {"ok": True}


@router.put("/{day_id}/notes")
async def update_notes(day_id: int, body: dict, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    day = await db.get(StudyDay, day_id)
    if not day:
        raise HTTPException(404)
    day.notas = body.get("notas", "")
    await db.commit()
    return {"ok": True}


@router.get("/{day_id}/week-context")
async def week_context(day_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    day = await _load_day(db, day_id)
    if not day.week:
        return {}
    week_days_result = await db.execute(
        select(StudyDay)
        .options(selectinload(StudyDay.topics))
        .where(StudyDay.week_id == day.week_id)
        .order_by(StudyDay.data)
    )
    week_days = week_days_result.scalars().all()
    return {
        "week": {
            "numero": day.week.numero,
            "tema": day.week.tema,
            "data_inicio": day.week.data_inicio.isoformat(),
            "data_fim": day.week.data_fim.isoformat(),
        },
        "days": [
            {
                "id": d.id,
                "data": d.data.isoformat(),
                "tipo": d.tipo,
                "status": d.status,
                "is_today": d.id == day_id,
            }
            for d in week_days
        ],
    }
