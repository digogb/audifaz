from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import MockExam, MockExamResult
from ..schemas import MockExamOut, MockExamCreate

router = APIRouter(prefix="/api/mocks", tags=["mocks"])


@router.get("", response_model=list[MockExamOut])
async def list_mocks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MockExam)
        .options(selectinload(MockExam.results))
        .order_by(MockExam.data.desc())
    )
    return result.scalars().all()


@router.post("", response_model=MockExamOut)
async def create_mock(body: MockExamCreate, db: AsyncSession = Depends(get_db)):
    mock = MockExam(data=body.data, tipo=body.tipo, observacoes=body.observacoes)
    db.add(mock)
    await db.flush()

    for r in body.results:
        result = MockExamResult(
            mock_exam_id=mock.id,
            disciplina=r.disciplina,
            acertos=r.acertos,
            total=r.total,
        )
        db.add(result)

    await db.commit()
    await db.refresh(mock)

    result = await db.execute(
        select(MockExam)
        .options(selectinload(MockExam.results))
        .where(MockExam.id == mock.id)
    )
    return result.scalar_one()


@router.delete("/{mock_id}")
async def delete_mock(mock_id: int, db: AsyncSession = Depends(get_db)):
    mock = await db.get(MockExam, mock_id)
    if not mock:
        raise HTTPException(404)
    await db.delete(mock)
    await db.commit()
    return {"ok": True}
