from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import StudyDay, Topic, Phase, Week, MockExam, MockExamResult, User, UserTopicProgress, UserDayProgress, Concurso
from ..schemas import ProgressDay, PhaseProgress
from ..auth import get_current_user, get_current_concurso

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("")
async def get_progress(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    concurso: Concurso = Depends(get_current_concurso),
):
    days_result = await db.execute(
        select(StudyDay)
        .join(Week, StudyDay.week_id == Week.id)
        .join(Phase, Week.phase_id == Phase.id)
        .options(selectinload(StudyDay.topics))
        .where(Phase.concurso_id == concurso.id)
        .order_by(StudyDay.data)
    )
    days = days_result.scalars().all()

    all_day_ids = [d.id for d in days]
    all_topic_ids = [t.id for d in days for t in d.topics]

    # Load all user progress in two queries
    topic_prog_result = await db.execute(
        select(UserTopicProgress).where(
            UserTopicProgress.user_id == current_user.id,
            UserTopicProgress.topic_id.in_(all_topic_ids),
        )
    )
    done_topic_ids = {p.topic_id for p in topic_prog_result.scalars().all() if p.concluido}

    day_prog_result = await db.execute(
        select(UserDayProgress).where(
            UserDayProgress.user_id == current_user.id,
            UserDayProgress.study_day_id.in_(all_day_ids),
        )
    )
    day_status = {p.study_day_id: p.status for p in day_prog_result.scalars().all()}

    progress_days = [
        {
            "data": d.data.isoformat(),
            "status": day_status.get(d.id, "pendente"),
            "tipo": d.tipo,
            "topics_total": len(d.topics),
            "topics_done": sum(1 for t in d.topics if t.id in done_topic_ids),
        }
        for d in days
    ]

    phases_result = await db.execute(
        select(Phase)
        .options(selectinload(Phase.weeks).selectinload(Week.days))
        .where(Phase.concurso_id == concurso.id)
        .order_by(Phase.numero)
    )
    phases = phases_result.scalars().all()

    phase_progress = []
    for p in phases:
        all_phase_days = [d for w in p.weeks for d in w.days]
        done = sum(1 for d in all_phase_days if day_status.get(d.id) == "concluido")
        total = len(all_phase_days)
        phase_progress.append({
            "numero": p.numero,
            "nome": p.nome,
            "total_days": total,
            "done_days": done,
            "pct": round(done / total * 100, 1) if total > 0 else 0.0,
        })

    mocks_result = await db.execute(
        select(MockExam)
        .options(selectinload(MockExam.results))
        .where(MockExam.user_id == current_user.id, MockExam.concurso_id == concurso.id)
        .order_by(MockExam.data)
    )
    mocks = mocks_result.scalars().all()
    mock_series = []
    for m in mocks:
        total_acertos = sum(r.acertos for r in m.results)
        total_questoes = sum(r.total for r in m.results)
        pct = round(total_acertos / total_questoes * 100, 1) if total_questoes > 0 else 0
        mock_series.append({
            "data": m.data.isoformat(),
            "tipo": m.tipo,
            "pct": pct,
            "por_disciplina": [
                {
                    "disciplina": r.disciplina,
                    "pct": round(r.acertos / r.total * 100, 1) if r.total > 0 else 0,
                }
                for r in m.results
            ],
        })

    return {
        "days": progress_days,
        "phases": phase_progress,
        "mocks": mock_series,
    }
