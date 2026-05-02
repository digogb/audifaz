from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import StudyDay, Topic, Week, Phase, User, UserTopicProgress, UserDayProgress
from ..schemas import StudyDayOut, StudyDayWithPhase
from ..auth import get_current_user

router = APIRouter(prefix="/api/days", tags=["days"])

TZ = ZoneInfo("America/Fortaleza")


def _today():
    return datetime.now(TZ).date()


async def _apply_user_progress(db: AsyncSession, day: StudyDay, user_id: int) -> dict:
    """Build a day dict with status/notas/topics resolved for the given user."""
    topic_ids = [t.id for t in day.topics]

    # Load user topic progress
    topic_progress = {}
    if topic_ids:
        result = await db.execute(
            select(UserTopicProgress).where(
                UserTopicProgress.user_id == user_id,
                UserTopicProgress.topic_id.in_(topic_ids),
            )
        )
        for p in result.scalars().all():
            topic_progress[p.topic_id] = p

    # Load user day progress
    day_prog_result = await db.execute(
        select(UserDayProgress).where(
            UserDayProgress.user_id == user_id,
            UserDayProgress.study_day_id == day.id,
        )
    )
    day_prog = day_prog_result.scalar_one_or_none()

    topics_out = []
    for t in sorted(day.topics, key=lambda x: x.ordem):
        prog = topic_progress.get(t.id)
        topics_out.append({
            "id": t.id,
            "descricao": t.descricao,
            "ordem": t.ordem,
            "concluido": prog.concluido if prog else False,
            "observacao": prog.observacao if prog else None,
        })

    return {
        "id": day.id,
        "data": day.data,
        "tipo": day.tipo,
        "status": day_prog.status if day_prog else "pendente",
        "notas": day_prog.notas if day_prog else None,
        "topics": topics_out,
    }


async def _load_day_raw(db: AsyncSession, day_id: int) -> StudyDay:
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


async def _build_response(db: AsyncSession, day: StudyDay, user_id: int) -> StudyDayWithPhase:
    day_dict = await _apply_user_progress(db, day, user_id)
    if day.week:
        day_dict["week"] = {
            "id": day.week.id,
            "numero": day.week.numero,
            "tema": day.week.tema,
            "data_inicio": day.week.data_inicio,
            "data_fim": day.week.data_fim,
        }
    out = StudyDayWithPhase.model_validate(day_dict)
    if day.week and day.week.phase:
        from ..schemas import PhaseOut
        out.phase = PhaseOut.model_validate(day.week.phase)
    return out


@router.get("/today", response_model=StudyDayWithPhase)
async def get_today(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
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
    return await _build_response(db, day, current_user.id)


@router.get("/{day_id}", response_model=StudyDayWithPhase)
async def get_day(day_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    day = await _load_day_raw(db, day_id)
    return await _build_response(db, day, current_user.id)


@router.get("/by-date/{date_str}", response_model=StudyDayWithPhase)
async def get_day_by_date(date_str: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from datetime import date as date_type
    try:
        target = date_type.fromisoformat(date_str)
    except ValueError:
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
        raise HTTPException(404, "Dia não encontrado")
    return await _build_response(db, day, current_user.id)


@router.put("/{day_id}/status")
async def update_status(day_id: int, body: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    day = await db.get(StudyDay, day_id)
    if not day:
        raise HTTPException(404)
    status = body.get("status")
    if status not in ("pendente", "em_andamento", "concluido"):
        raise HTTPException(400, "Status inválido")

    result = await db.execute(
        select(UserDayProgress).where(
            UserDayProgress.user_id == current_user.id,
            UserDayProgress.study_day_id == day_id,
        )
    )
    prog = result.scalar_one_or_none()
    if prog:
        prog.status = status
    else:
        db.add(UserDayProgress(user_id=current_user.id, study_day_id=day_id, status=status))
    await db.commit()
    return {"ok": True}


@router.put("/{day_id}/notes")
async def update_notes(day_id: int, body: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    day = await db.get(StudyDay, day_id)
    if not day:
        raise HTTPException(404)

    result = await db.execute(
        select(UserDayProgress).where(
            UserDayProgress.user_id == current_user.id,
            UserDayProgress.study_day_id == day_id,
        )
    )
    prog = result.scalar_one_or_none()
    if prog:
        prog.notas = body.get("notas", "")
    else:
        db.add(UserDayProgress(user_id=current_user.id, study_day_id=day_id, status="pendente", notas=body.get("notas", "")))
    await db.commit()
    return {"ok": True}


@router.get("/{day_id}/week-context")
async def week_context(day_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    day = await _load_day_raw(db, day_id)
    if not day.week:
        return {}

    week_days_result = await db.execute(
        select(StudyDay)
        .where(StudyDay.week_id == day.week_id)
        .order_by(StudyDay.data)
    )
    week_days = week_days_result.scalars().all()
    week_day_ids = [d.id for d in week_days]

    # Load all user day progress for this week at once
    prog_result = await db.execute(
        select(UserDayProgress).where(
            UserDayProgress.user_id == current_user.id,
            UserDayProgress.study_day_id.in_(week_day_ids),
        )
    )
    prog_by_day = {p.study_day_id: p for p in prog_result.scalars().all()}

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
                "status": prog_by_day[d.id].status if d.id in prog_by_day else "pendente",
                "is_today": d.id == day_id,
            }
            for d in week_days
        ],
    }
