from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import ErrorEntry, User, Concurso
from ..schemas import ErrorEntryOut, ErrorEntryCreate
from ..auth import get_current_user, get_current_concurso
from typing import Optional

router = APIRouter(prefix="/api/errors", tags=["errors"])

TZ = ZoneInfo("America/Fortaleza")


@router.get("", response_model=list[ErrorEntryOut])
async def list_errors(
    disciplina: Optional[str] = None,
    banca: Optional[str] = None,
    revisado: Optional[bool] = None,
    dias: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    concurso: Concurso = Depends(get_current_concurso),
):
    q = (
        select(ErrorEntry)
        .where(ErrorEntry.user_id == current_user.id, ErrorEntry.concurso_id == concurso.id)
        .order_by(ErrorEntry.data.desc())
    )

    if disciplina:
        q = q.where(ErrorEntry.disciplina == disciplina)
    if banca:
        q = q.where(ErrorEntry.banca == banca)
    if revisado is True:
        q = q.where(ErrorEntry.revisado_em.isnot(None))
    elif revisado is False:
        q = q.where(ErrorEntry.revisado_em.is_(None))
    if dias:
        from datetime import timedelta
        cutoff = datetime.now(TZ).date() - timedelta(days=dias)
        q = q.where(ErrorEntry.data >= cutoff)

    result = await db.execute(q)
    return result.scalars().all()


@router.get("/stale-count")
async def stale_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    concurso: Concurso = Depends(get_current_concurso),
):
    from datetime import timedelta
    cutoff = datetime.now(TZ) - timedelta(days=7)
    result = await db.execute(
        select(ErrorEntry)
        .where(ErrorEntry.user_id == current_user.id)
        .where(ErrorEntry.concurso_id == concurso.id)
        .where(ErrorEntry.revisado_em.is_(None))
        .where(ErrorEntry.data <= cutoff.date())
    )
    return {"count": len(result.scalars().all())}


@router.post("", response_model=ErrorEntryOut)
async def create_error(
    body: ErrorEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    concurso: Concurso = Depends(get_current_concurso),
):
    error = ErrorEntry(**body.model_dump(), user_id=current_user.id, concurso_id=concurso.id)
    db.add(error)
    await db.commit()
    await db.refresh(error)
    return error


@router.put("/{error_id}/review")
async def mark_reviewed(error_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    error = await db.get(ErrorEntry, error_id)
    if not error or error.user_id != current_user.id:
        raise HTTPException(404)
    error.revisado_em = datetime.utcnow()
    await db.commit()
    return {"ok": True}


@router.delete("/{error_id}")
async def delete_error(error_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    error = await db.get(ErrorEntry, error_id)
    if not error or error.user_id != current_user.id:
        raise HTTPException(404)
    await db.delete(error)
    await db.commit()
    return {"ok": True}


@router.get("/disciplines")
async def list_disciplines(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    concurso: Concurso = Depends(get_current_concurso),
):
    result = await db.execute(
        select(ErrorEntry.disciplina)
        .where(ErrorEntry.user_id == current_user.id, ErrorEntry.concurso_id == concurso.id)
        .distinct()
    )
    return sorted(r[0] for r in result.all())
