from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import StudyDay, Topic, Phase, Week, MockExam, MockExamResult, User
from ..schemas import ProgressDay, PhaseProgress
from ..auth import get_current_user

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("")
async def get_progress(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    days_result = await db.execute(
        select(StudyDay).options(selectinload(StudyDay.topics)).order_by(StudyDay.data)
    )
    days = days_result.scalars().all()

    progress_days = [
        {
            "data": d.data.isoformat(),
            "status": d.status,
            "tipo": d.tipo,
            "topics_total": len(d.topics),
            "topics_done": sum(1 for t in d.topics if t.concluido),
        }
        for d in days
    ]

    phases_result = await db.execute(
        select(Phase).options(
            selectinload(Phase.weeks).selectinload(Week.days)
        ).order_by(Phase.numero)
    )
    phases = phases_result.scalars().all()

    phase_progress = []
    for p in phases:
        all_days = [d for w in p.weeks for d in w.days]
        done = sum(1 for d in all_days if d.status == "concluido")
        total = len(all_days)
        phase_progress.append({
            "numero": p.numero,
            "nome": p.nome,
            "total_days": total,
            "done_days": done,
            "pct": round(done / total * 100, 1) if total > 0 else 0.0,
        })

    # Mock exam evolution filtered by user
    mocks_result = await db.execute(
        select(MockExam)
        .options(selectinload(MockExam.results))
        .where(MockExam.user_id == current_user.id)
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
