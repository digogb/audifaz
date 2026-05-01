from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import Topic, StudyDay, User
from ..auth import get_current_user

router = APIRouter(prefix="/api/topics", tags=["topics"])


@router.put("/{topic_id}/toggle")
async def toggle_topic(topic_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(404)
    topic.concluido = not topic.concluido

    # Auto-update day status based on topics
    day = await db.get(StudyDay, topic.study_day_id)
    if day:
        from sqlalchemy import select
        result = await db.execute(select(Topic).where(Topic.study_day_id == day.id))
        topics = result.scalars().all()
        done = sum(1 for t in topics if t.concluido)
        total = len(topics)
        if done == 0:
            day.status = "pendente"
        elif done == total:
            day.status = "concluido"
        else:
            day.status = "em_andamento"

    await db.commit()
    return {"concluido": topic.concluido}
