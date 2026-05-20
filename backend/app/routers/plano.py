"""Visão estrutural do plano de estudos: fases > semanas > dias > tópicos.

Retorna SOMENTE o esqueleto (descrições dos tópicos), sem material aprofundado,
questões ou áudio. O valor protegido continua no fluxo do dia.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..auth import get_current_user, get_current_concurso
from ..db import get_db
from ..models import (
    Bloco, Concurso, Phase, StudyDay, Topic,
    User, UserDayProgress, UserTopicProgress, Week,
)

router = APIRouter(prefix="/api", tags=["plano"])


class TopicNode(BaseModel):
    id: int
    descricao: str
    ordem: int
    concluido: bool = False
    bloco_slug: Optional[str] = None


class DiaNode(BaseModel):
    id: int
    data: str
    tipo: str
    status: str = "pendente"
    topics_total: int
    topics_done: int
    topicos: List[TopicNode] = []


class SemanaNode(BaseModel):
    numero: int
    tema: str
    data_inicio: str
    data_fim: str
    dias: List[DiaNode] = []


class FaseNode(BaseModel):
    numero: int
    nome: str
    total_days: int
    done_days: int
    pct: float
    semanas: List[SemanaNode] = []


class PlanoOut(BaseModel):
    concurso: dict
    fases: List[FaseNode] = []


@router.get("/plano", response_model=PlanoOut)
async def get_plano(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    concurso: Concurso = Depends(get_current_concurso),
):
    # Carrega árvore completa do concurso atual
    phases = (await db.execute(
        select(Phase)
        .options(selectinload(Phase.weeks).selectinload(Week.days).selectinload(StudyDay.topics))
        .where(Phase.concurso_id == concurso.id)
        .order_by(Phase.numero)
    )).scalars().all()

    # Carrega progresso individual (status do dia e tópicos concluídos) numa só query
    all_day_ids = [d.id for p in phases for w in p.weeks for d in w.days]
    all_topic_ids = [t.id for p in phases for w in p.weeks for d in w.days for t in d.topics]

    day_status_map: dict[int, str] = {}
    if all_day_ids:
        rows = (await db.execute(
            select(UserDayProgress).where(
                UserDayProgress.user_id == current_user.id,
                UserDayProgress.study_day_id.in_(all_day_ids),
            )
        )).scalars().all()
        day_status_map = {r.study_day_id: r.status for r in rows}

    topic_done_set: set[int] = set()
    if all_topic_ids:
        rows = (await db.execute(
            select(UserTopicProgress).where(
                UserTopicProgress.user_id == current_user.id,
                UserTopicProgress.topic_id.in_(all_topic_ids),
            )
        )).scalars().all()
        topic_done_set = {r.topic_id for r in rows if r.concluido}

    # Mapeia slug do bloco
    bloco_rows = (await db.execute(
        select(Bloco.id, Bloco.slug).where(Bloco.concurso_id == concurso.id)
    )).all()
    bloco_slug_map = {bid: slug for bid, slug in bloco_rows}

    fases_out: List[FaseNode] = []
    for p in phases:
        total_days = 0
        done_days = 0
        semanas_out: List[SemanaNode] = []
        for w in sorted(p.weeks, key=lambda x: x.numero):
            dias_out: List[DiaNode] = []
            for d in sorted(w.days, key=lambda x: x.data):
                topics = sorted(d.topics, key=lambda x: x.ordem)
                topics_done = sum(1 for t in topics if t.id in topic_done_set)
                dias_out.append(DiaNode(
                    id=d.id,
                    data=d.data.isoformat(),
                    tipo=d.tipo,
                    status=day_status_map.get(d.id, "pendente"),
                    topics_total=len(topics),
                    topics_done=topics_done,
                    topicos=[
                        TopicNode(
                            id=t.id, descricao=t.descricao, ordem=t.ordem,
                            concluido=t.id in topic_done_set,
                            bloco_slug=bloco_slug_map.get(t.bloco_id) if t.bloco_id else None,
                        )
                        for t in topics
                    ],
                ))
                total_days += 1
                if day_status_map.get(d.id) == "concluido":
                    done_days += 1
            semanas_out.append(SemanaNode(
                numero=w.numero, tema=w.tema,
                data_inicio=w.data_inicio.isoformat(),
                data_fim=w.data_fim.isoformat(),
                dias=dias_out,
            ))
        fases_out.append(FaseNode(
            numero=p.numero, nome=p.nome,
            total_days=total_days, done_days=done_days,
            pct=round(done_days / total_days * 100, 1) if total_days else 0.0,
            semanas=semanas_out,
        ))

    return PlanoOut(
        concurso={
            "nome": concurso.nome,
            "slug": concurso.slug,
            "data_prova": concurso.data_prova.isoformat() if concurso.data_prova else None,
        },
        fases=fases_out,
    )
