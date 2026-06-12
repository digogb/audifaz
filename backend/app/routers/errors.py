from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import ErrorEntry, GeneratedQuestion, User, Concurso
from ..schemas import ErrorEntryOut, ErrorEntryCreate, ErrorAnswerIn
from ..auth import get_current_user, get_current_concurso
from typing import Optional

router = APIRouter(prefix="/api/errors", tags=["errors"])

TZ = ZoneInfo("America/Fortaleza")


def _clean_alternativas(alts) -> Optional[dict]:
    """Só A–E (a geração às vezes injeta chaves espúrias como 'comentario')."""
    if not isinstance(alts, dict):
        return None
    clean = {k.upper(): v for k, v in alts.items() if k.upper() in ("A", "B", "C", "D", "E")}
    return clean or None


def _to_out(e: ErrorEntry, alternativas: Optional[dict]) -> ErrorEntryOut:
    out = ErrorEntryOut.model_validate(e)
    out.alternativas = alternativas
    # Erro re-respondível ainda não revisado: gabarito e comentário ficam fora
    # do payload até a nova tentativa (revisão = responder de novo, não ler).
    if alternativas and not e.revisado_em:
        out.gabarito = None
        out.justificativa = None
    return out


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
    entries = result.scalars().all()

    # Alternativas das questões geradas vinculadas, em lote
    qids = [e.question_id for e in entries if e.question_id]
    alts_by_qid: dict[int, dict] = {}
    if qids:
        rows = await db.execute(
            select(GeneratedQuestion.id, GeneratedQuestion.alternativas)
            .where(GeneratedQuestion.id.in_(qids))
        )
        for qid, alts in rows.all():
            clean = _clean_alternativas(alts)
            if clean:
                alts_by_qid[qid] = clean

    return [_to_out(e, alts_by_qid.get(e.question_id)) for e in entries]


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


@router.put("/{error_id}/answer")
async def answer_error(
    error_id: int,
    body: ErrorAnswerIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revisão ativa: re-responder a questão do erro. Acertou → revisado;
    errou → continua pendente (volta para a fila de revisão)."""
    alternativa = (body.alternativa or "").strip().upper()
    if alternativa not in ("A", "B", "C", "D", "E"):
        raise HTTPException(400, "Alternativa inválida")
    error = await db.get(ErrorEntry, error_id)
    if not error or error.user_id != current_user.id:
        raise HTTPException(404)
    if not error.question_id:
        raise HTTPException(400, "Erro manual não tem alternativas para responder")

    acertou = alternativa == error.gabarito
    if acertou:
        error.revisado_em = datetime.utcnow()
        await db.commit()
    return {
        "acertou": acertou,
        "gabarito": error.gabarito,
        "comentario": error.justificativa,
    }


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
