import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db, AsyncSessionLocal
from ..models import StudyDay, StudyMaterial, GeneratedQuestion, QuestionAttempt, ErrorEntry
from ..schemas import StudyMaterialOut, AttemptCreate, GeneratedQuestionOut
from .. import claude_client

router = APIRouter(prefix="/api/days", tags=["materials"])


@router.get("/{day_id}/material", response_model=StudyMaterialOut)
async def get_material(day_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StudyMaterial)
        .options(
            selectinload(StudyMaterial.questions).selectinload(GeneratedQuestion.attempt)
        )
        .where(StudyMaterial.study_day_id == day_id)
    )
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(404, "Material não gerado ainda")
    return material


@router.post("/{day_id}/material/generate")
async def generate_material(
    day_id: int,
    model: str = Query("claude-sonnet-4-6"),
):
    if model not in ("claude-sonnet-4-6", "claude-opus-4-7"):
        raise HTTPException(400, "Modelo inválido")

    return StreamingResponse(
        _stream(day_id, model),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _stream(day_id: int, model: str):
    async with AsyncSessionLocal() as db:
        # Load day + topics
        result = await db.execute(
            select(StudyDay)
            .options(selectinload(StudyDay.topics))
            .where(StudyDay.id == day_id)
        )
        day = result.scalar_one_or_none()
        if not day:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Dia não encontrado'})}\n\n"
            yield "data: [DONE]\n\n"
            return

        topics = [t.descricao for t in day.topics]
        if not topics:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Nenhum tópico encontrado'})}\n\n"
            yield "data: [DONE]\n\n"
            return

        full_content = []
        questions_data = []
        usage_data = {}

        try:
            async for event in claude_client.generate_material_stream(topics, model):
                if event["type"] == "content":
                    full_content.append(event["chunk"])
                elif event["type"] == "questions":
                    questions_data = event["data"]
                elif event["type"] == "done":
                    usage_data = event

                yield f"data: {json.dumps(event)}\n\n"

            # Save to DB
            content_md = "".join(full_content)

            # Delete existing material
            existing = await db.execute(
                select(StudyMaterial).where(StudyMaterial.study_day_id == day_id)
            )
            existing_material = existing.scalar_one_or_none()
            if existing_material:
                await db.execute(
                    delete(GeneratedQuestion).where(
                        GeneratedQuestion.study_material_id == existing_material.id
                    )
                )
                await db.delete(existing_material)
                await db.flush()

            material = StudyMaterial(
                study_day_id=day_id,
                modelo=model,
                conteudo_md=content_md,
                tokens_in=usage_data.get("usage", {}).get("input_tokens"),
                tokens_out=usage_data.get("usage", {}).get("output_tokens"),
                custo_usd=usage_data.get("custo_usd"),
                cache_hit_ratio=usage_data.get("cache_hit_ratio"),
            )
            db.add(material)
            await db.flush()

            for i, q in enumerate(questions_data):
                gq = GeneratedQuestion(
                    study_material_id=material.id,
                    enunciado=q.get("enunciado", ""),
                    alternativas=q.get("alternativas", {}),
                    gabarito=q.get("gabarito", "A"),
                    comentario=q.get("comentario", ""),
                    disciplina=q.get("disciplina", ""),
                    dificuldade=q.get("dificuldade", "medio"),
                    ordem=i,
                )
                db.add(gq)

            await db.commit()

        except Exception as e:
            await db.rollback()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        yield "data: [DONE]\n\n"


@router.post("/questions/{question_id}/attempt")
async def record_attempt(
    question_id: int,
    body: AttemptCreate,
    db: AsyncSession = Depends(get_db),
):
    question = await db.get(GeneratedQuestion, question_id)
    if not question:
        raise HTTPException(404)

    acertou = body.alternativa_escolhida.upper() == question.gabarito.upper()

    # Update existing or create new attempt
    existing = await db.execute(
        select(QuestionAttempt).where(QuestionAttempt.question_id == question_id)
    )
    attempt = existing.scalar_one_or_none()
    if attempt:
        attempt.alternativa_escolhida = body.alternativa_escolhida.upper()
        attempt.acertou = acertou
        attempt.respondido_em = datetime.utcnow()
        attempt.observacao = body.observacao
    else:
        attempt = QuestionAttempt(
            question_id=question_id,
            alternativa_escolhida=body.alternativa_escolhida.upper(),
            acertou=acertou,
            observacao=body.observacao,
        )
        db.add(attempt)

    # Auto-create error entry if wrong
    if not acertou:
        from datetime import date, timezone
        from zoneinfo import ZoneInfo
        today = datetime.now(ZoneInfo("America/Fortaleza")).date()

        # Check if error already exists for this question
        existing_error = await db.execute(
            select(ErrorEntry).where(ErrorEntry.question_id == question_id)
        )
        if not existing_error.scalar_one_or_none():
            error = ErrorEntry(
                origem="gerada",
                question_id=question_id,
                data=today,
                disciplina=question.disciplina,
                enunciado=question.enunciado,
                gabarito=question.gabarito,
                sua_resposta=body.alternativa_escolhida.upper(),
                justificativa=question.comentario,
            )
            db.add(error)

    await db.commit()
    return {"acertou": acertou, "gabarito": question.gabarito}
