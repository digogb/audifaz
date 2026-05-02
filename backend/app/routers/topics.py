from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import Topic, UserTopicProgress, UserDayProgress, User
from ..auth import get_current_user

router = APIRouter(prefix="/api/topics", tags=["topics"])


async def _recalc_day_status(db: AsyncSession, study_day_id: int, user_id: int):
    result = await db.execute(select(Topic).where(Topic.study_day_id == study_day_id))
    topics = result.scalars().all()
    if not topics:
        return

    topic_ids = [t.id for t in topics]
    prog_result = await db.execute(
        select(UserTopicProgress).where(
            UserTopicProgress.user_id == user_id,
            UserTopicProgress.topic_id.in_(topic_ids),
        )
    )
    done_ids = {p.topic_id for p in prog_result.scalars().all() if p.concluido}
    done = len(done_ids)
    total = len(topics)

    if done == 0:
        new_status = "pendente"
    elif done == total:
        new_status = "concluido"
    else:
        new_status = "em_andamento"

    day_prog_result = await db.execute(
        select(UserDayProgress).where(
            UserDayProgress.user_id == user_id,
            UserDayProgress.study_day_id == study_day_id,
        )
    )
    day_prog = day_prog_result.scalar_one_or_none()
    if day_prog:
        day_prog.status = new_status
    else:
        db.add(UserDayProgress(user_id=user_id, study_day_id=study_day_id, status=new_status))


@router.put("/{topic_id}/toggle")
async def toggle_topic(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(404)

    result = await db.execute(
        select(UserTopicProgress).where(
            UserTopicProgress.user_id == current_user.id,
            UserTopicProgress.topic_id == topic_id,
        )
    )
    prog = result.scalar_one_or_none()
    if prog:
        prog.concluido = not prog.concluido
    else:
        prog = UserTopicProgress(user_id=current_user.id, topic_id=topic_id, concluido=True)
        db.add(prog)

    await db.flush()
    await _recalc_day_status(db, topic.study_day_id, current_user.id)
    await db.commit()
    return {"concluido": prog.concluido}
