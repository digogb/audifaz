from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_admin_user, get_current_user, get_current_concurso
from ..db import get_db
from ..models import (
    Bloco, Concurso, GeneratedQuestion, MockExam, MockExamResult, Phase,
    QuestionAttempt, StudyDay, StudyMaterial, Topic, User, Week,
)

router = APIRouter(prefix="/api", tags=["blocos"])


class BlocoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    nome: str
    peso: float
    prioridade: str
    alocacao_pct: float
    meta_acerto_pct: float
    ordem: int
    keywords: Optional[str] = None


class BlocoIn(BaseModel):
    slug: str
    nome: str
    peso: float = 1.0
    prioridade: str = "media"
    alocacao_pct: float = 0.0
    meta_acerto_pct: float = 70.0
    ordem: int = 0
    keywords: Optional[str] = None


class BlocoUpdate(BaseModel):
    nome: Optional[str] = None
    peso: Optional[float] = None
    prioridade: Optional[str] = None
    alocacao_pct: Optional[float] = None
    meta_acerto_pct: Optional[float] = None
    ordem: Optional[int] = None
    keywords: Optional[str] = None


class BlocoMetric(BaseModel):
    bloco_id: int
    slug: str
    nome: str
    peso: float
    prioridade: str
    meta_acerto_pct: float
    total_attempts: int
    acertos: int
    pct_acerto: float
    gap_meta: float  # diferença para a meta (negativo = atrasado)
    status: str  # ok | alerta | critico


@router.get("/blocos", response_model=List[BlocoOut])
async def list_blocos(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    concurso: Concurso = Depends(get_current_concurso),
):
    rows = (await db.execute(
        select(Bloco).where(Bloco.concurso_id == concurso.id).order_by(Bloco.ordem, Bloco.nome)
    )).scalars().all()
    return rows


@router.post("/admin/blocos", response_model=BlocoOut, status_code=201)
async def admin_create_bloco(
    body: BlocoIn,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    concurso: Concurso = Depends(get_current_concurso),
):
    bloco = Bloco(concurso_id=concurso.id, **body.model_dump())
    db.add(bloco)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(409, f"Slug '{body.slug}' já existe neste concurso")
    await db.refresh(bloco)
    return bloco


@router.put("/admin/blocos/{bloco_id}", response_model=BlocoOut)
async def admin_update_bloco(
    bloco_id: int,
    body: BlocoUpdate,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    concurso: Concurso = Depends(get_current_concurso),
):
    bloco = await db.get(Bloco, bloco_id)
    if not bloco or bloco.concurso_id != concurso.id:
        raise HTTPException(404)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(bloco, k, v)
    await db.commit()
    await db.refresh(bloco)
    return bloco


@router.delete("/admin/blocos/{bloco_id}", status_code=204)
async def admin_delete_bloco(
    bloco_id: int,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    concurso: Concurso = Depends(get_current_concurso),
):
    bloco = await db.get(Bloco, bloco_id)
    if not bloco or bloco.concurso_id != concurso.id:
        raise HTTPException(404)
    await db.delete(bloco)
    await db.commit()


@router.put("/admin/topics/{topic_id}/bloco/{bloco_id}", status_code=204)
async def admin_set_topic_bloco(
    topic_id: int,
    bloco_id: int,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    concurso: Concurso = Depends(get_current_concurso),
):
    bloco = await db.get(Bloco, bloco_id)
    if not bloco or bloco.concurso_id != concurso.id:
        raise HTTPException(404, "Bloco inválido")
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(404, "Tópico não encontrado")
    topic.bloco_id = bloco_id
    await db.commit()


@router.put("/admin/questions/{question_id}/bloco/{bloco_id}", status_code=204)
async def admin_set_question_bloco(
    question_id: int,
    bloco_id: int,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    concurso: Concurso = Depends(get_current_concurso),
):
    bloco = await db.get(Bloco, bloco_id)
    if not bloco or bloco.concurso_id != concurso.id:
        raise HTTPException(404, "Bloco inválido")
    q = await db.get(GeneratedQuestion, question_id)
    if not q:
        raise HTTPException(404, "Questão não encontrada")
    q.bloco_id = bloco_id
    await db.commit()


def _classify_status(pct: float, meta: float, total: int) -> str:
    if total == 0:
        return "sem_dados"
    if pct >= meta:
        return "ok"
    if pct >= meta - 15:
        return "alerta"
    return "critico"


@router.get("/metricas/blocos", response_model=List[BlocoMetric])
async def metricas_blocos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    concurso: Concurso = Depends(get_current_concurso),
):
    """Agrega QuestionAttempts (gerados pelo Claude) + MockExamResults
    do usuário no concurso atual, por bloco."""
    blocos = (await db.execute(
        select(Bloco).where(Bloco.concurso_id == concurso.id).order_by(Bloco.ordem)
    )).scalars().all()

    # Soma de tentativas de questões geradas, por bloco
    attempts_q = (
        select(
            GeneratedQuestion.bloco_id.label("bid"),
            func.count(QuestionAttempt.id).label("total"),
            func.sum(case((QuestionAttempt.acertou.is_(True), 1), else_=0)).label("acertos"),
        )
        .join(GeneratedQuestion, GeneratedQuestion.id == QuestionAttempt.question_id)
        .join(StudyMaterial, StudyMaterial.id == GeneratedQuestion.study_material_id)
        .join(StudyDay, StudyDay.id == StudyMaterial.study_day_id)
        .join(Week, Week.id == StudyDay.week_id)
        .join(Phase, Phase.id == Week.phase_id)
        .where(
            QuestionAttempt.user_id == current_user.id,
            Phase.concurso_id == concurso.id,
        )
        .group_by(GeneratedQuestion.bloco_id)
    )
    attempts_by_bloco: dict[Optional[int], tuple[int, int]] = {}
    for bid, total, acertos in (await db.execute(attempts_q)).all():
        attempts_by_bloco[bid] = (int(total or 0), int(acertos or 0))

    # MockExamResults agregados por bloco (cada result tem acertos/total)
    mock_q = (
        select(
            MockExamResult.bloco_id.label("bid"),
            func.sum(MockExamResult.total).label("total"),
            func.sum(MockExamResult.acertos).label("acertos"),
        )
        .join(MockExam, MockExam.id == MockExamResult.mock_exam_id)
        .where(
            MockExam.user_id == current_user.id,
            MockExam.concurso_id == concurso.id,
        )
        .group_by(MockExamResult.bloco_id)
    )
    for bid, total, acertos in (await db.execute(mock_q)).all():
        prev = attempts_by_bloco.get(bid, (0, 0))
        attempts_by_bloco[bid] = (prev[0] + int(total or 0), prev[1] + int(acertos or 0))

    out: List[BlocoMetric] = []
    for b in blocos:
        total, acertos = attempts_by_bloco.get(b.id, (0, 0))
        pct = round((acertos / total) * 100, 1) if total > 0 else 0.0
        out.append(BlocoMetric(
            bloco_id=b.id, slug=b.slug, nome=b.nome,
            peso=b.peso, prioridade=b.prioridade,
            meta_acerto_pct=b.meta_acerto_pct,
            total_attempts=total, acertos=acertos,
            pct_acerto=pct, gap_meta=round(pct - b.meta_acerto_pct, 1),
            status=_classify_status(pct, b.meta_acerto_pct, total),
        ))
    return out
