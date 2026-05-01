from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db, AsyncSessionLocal
from ..models import StudyDay, StudyMaterial, GeneratedQuestion, QuestionAttempt, ErrorEntry, User
from ..schemas import StudyMaterialOut, AttemptCreate
from .. import claude_client
from ..claude_client import _calc_cost, _calc_cache_ratio
from ..auth import get_current_user

router = APIRouter(prefix="/api/days", tags=["materials"])


@router.get("/{day_id}/material", response_model=StudyMaterialOut)
async def get_material(
    day_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(StudyMaterial)
        .options(selectinload(StudyMaterial.questions))
        .where(StudyMaterial.study_day_id == day_id)
    )
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(404, "Material não gerado ainda")

    question_ids = [q.id for q in material.questions]
    attempts_by_question = {}
    if question_ids:
        attempts_result = await db.execute(
            select(QuestionAttempt).where(
                QuestionAttempt.question_id.in_(question_ids),
                QuestionAttempt.user_id == current_user.id,
            )
        )
        for att in attempts_result.scalars().all():
            attempts_by_question[att.question_id] = att

    questions_out = []
    for q in sorted(material.questions, key=lambda x: x.ordem):
        att = attempts_by_question.get(q.id)
        att_out = None
        if att:
            att_out = {
                "id": att.id,
                "alternativa_escolhida": att.alternativa_escolhida,
                "acertou": att.acertou,
                "respondido_em": att.respondido_em,
                "observacao": att.observacao,
            }
        questions_out.append({
            "id": q.id,
            "enunciado": q.enunciado,
            "alternativas": q.alternativas,
            "gabarito": q.gabarito,
            "comentario": q.comentario,
            "disciplina": q.disciplina,
            "dificuldade": q.dificuldade,
            "ordem": q.ordem,
            "attempt": att_out,
        })

    return {
        "id": material.id,
        "gerado_em": material.gerado_em,
        "modelo": material.modelo,
        "conteudo_md": material.conteudo_md,
        "tokens_in": material.tokens_in,
        "tokens_out": material.tokens_out,
        "custo_usd": material.custo_usd,
        "cache_hit_ratio": material.cache_hit_ratio,
        "questions": questions_out,
    }


@router.post("/{day_id}/material/generate", response_model=StudyMaterialOut)
async def generate_material(
    day_id: int,
    model: str = Query("claude-sonnet-4-6"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if model not in ("claude-sonnet-4-6", "claude-opus-4-7"):
        raise HTTPException(400, "Modelo inválido")

    result = await db.execute(
        select(StudyDay)
        .options(selectinload(StudyDay.topics))
        .where(StudyDay.id == day_id)
    )
    day = result.scalar_one_or_none()
    if not day:
        raise HTTPException(404, "Dia não encontrado")

    topics = [t.descricao for t in day.topics]
    if not topics:
        raise HTTPException(400, "Nenhum tópico encontrado")

    content_md, questions_data, usage_dict = await claude_client.generate_material(topics, model)

    # Replace existing material
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
        tokens_in=usage_dict.get("input_tokens"),
        tokens_out=usage_dict.get("output_tokens"),
        custo_usd=_calc_cost(model, usage_dict),
        cache_hit_ratio=_calc_cache_ratio(usage_dict),
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

    # Return full material with empty attempts for current user
    questions_out = []
    for gq in sorted(
        await _reload_questions(db, material.id), key=lambda x: x.ordem
    ):
        questions_out.append({
            "id": gq.id,
            "enunciado": gq.enunciado,
            "alternativas": gq.alternativas,
            "gabarito": gq.gabarito,
            "comentario": gq.comentario,
            "disciplina": gq.disciplina,
            "dificuldade": gq.dificuldade,
            "ordem": gq.ordem,
            "attempt": None,
        })

    return {
        "id": material.id,
        "gerado_em": material.gerado_em,
        "modelo": material.modelo,
        "conteudo_md": material.conteudo_md,
        "tokens_in": material.tokens_in,
        "tokens_out": material.tokens_out,
        "custo_usd": material.custo_usd,
        "cache_hit_ratio": material.cache_hit_ratio,
        "questions": questions_out,
    }


async def _reload_questions(db: AsyncSession, material_id: int) -> list:
    result = await db.execute(
        select(GeneratedQuestion).where(GeneratedQuestion.study_material_id == material_id)
    )
    return result.scalars().all()


async def generate_for_day(day_id: int, model: str = "claude-sonnet-4-6"):
    """Used by cron job to generate material for a day without auth."""
    async with AsyncSessionLocal() as db:
        # Skip if material already exists
        existing = await db.execute(
            select(StudyMaterial).where(StudyMaterial.study_day_id == day_id)
        )
        if existing.scalar_one_or_none():
            return

        result = await db.execute(
            select(StudyDay)
            .options(selectinload(StudyDay.topics))
            .where(StudyDay.id == day_id)
        )
        day = result.scalar_one_or_none()
        if not day or not day.topics:
            return

        topics = [t.descricao for t in day.topics]

    content_md, questions_data, usage_dict = await claude_client.generate_material(topics, model)

    async with AsyncSessionLocal() as db:
        material = StudyMaterial(
            study_day_id=day_id,
            modelo=model,
            conteudo_md=content_md,
            tokens_in=usage_dict.get("input_tokens"),
            tokens_out=usage_dict.get("output_tokens"),
            custo_usd=_calc_cost(model, usage_dict),
            cache_hit_ratio=_calc_cache_ratio(usage_dict),
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


@router.post("/questions/{question_id}/attempt")
async def record_attempt(
    question_id: int,
    body: AttemptCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    question = await db.get(GeneratedQuestion, question_id)
    if not question:
        raise HTTPException(404)

    acertou = body.alternativa_escolhida.upper() == question.gabarito.upper()

    existing = await db.execute(
        select(QuestionAttempt).where(
            QuestionAttempt.question_id == question_id,
            QuestionAttempt.user_id == current_user.id,
        )
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
            user_id=current_user.id,
            alternativa_escolhida=body.alternativa_escolhida.upper(),
            acertou=acertou,
            observacao=body.observacao,
        )
        db.add(attempt)

    if not acertou:
        from datetime import date
        from zoneinfo import ZoneInfo
        today = datetime.now(ZoneInfo("America/Fortaleza")).date()

        existing_error = await db.execute(
            select(ErrorEntry).where(
                ErrorEntry.question_id == question_id,
                ErrorEntry.user_id == current_user.id,
            )
        )
        if not existing_error.scalar_one_or_none():
            error = ErrorEntry(
                origem="gerada",
                user_id=current_user.id,
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
