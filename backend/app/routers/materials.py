import os
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db, AsyncSessionLocal
from ..models import StudyDay, StudyMaterial, GeneratedQuestion, QuestionAttempt, ErrorEntry, User, MaterialAudio, Week, Phase, Concurso, BancaExample, Bloco
from ..schemas import StudyMaterialOut, AttemptCreate
from .. import claude_client
from ..claude_client import _calc_cost, _calc_cache_ratio, ConcursoContext
from ..auth import get_current_user, get_admin_user, get_current_concurso, require_active_subscription

# Modelo usado na geração diária (cron). Configurável via env; default Opus 4.8.
GENERATION_MODEL = os.environ.get("GENERATION_MODEL", "claude-opus-4-8")

router = APIRouter(prefix="/api/days", tags=["materials"])


async def _ensure_day_in_concurso(db: AsyncSession, day_id: int, concurso_id: int) -> None:
    """Raises 404 if day doesn't belong to the given concurso."""
    result = await db.execute(
        select(StudyDay.id)
        .join(Week, StudyDay.week_id == Week.id)
        .join(Phase, Week.phase_id == Phase.id)
        .where(StudyDay.id == day_id, Phase.concurso_id == concurso_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(404, "Dia não encontrado")


def _to_ctx(c: Concurso) -> ConcursoContext:
    return ConcursoContext(
        nome=c.nome, banca=c.banca, orgao=c.orgao, cargo=c.cargo,
        data_prova=c.data_prova, prompt_extra=c.prompt_extra,
    )


async def _load_examples(db: AsyncSession, banca: str, limit: int = 12) -> list[dict]:
    rows = (await db.execute(
        select(BancaExample)
        .where(BancaExample.banca == banca, BancaExample.ativo == True)
        .order_by(BancaExample.id)
        .limit(limit)
    )).scalars().all()
    return [
        {
            "fonte": r.fonte,
            "ano": r.ano,
            "disciplina": r.disciplina,
            "enunciado": r.enunciado,
            "alternativas": r.alternativas,
            "gabarito": r.gabarito,
        }
        for r in rows
    ]


async def _concurso_for_day(db: AsyncSession, day_id: int) -> Concurso | None:
    """Resolve o Concurso responsável por um StudyDay (via Phase)."""
    return (await db.execute(
        select(Concurso)
        .join(Phase, Phase.concurso_id == Concurso.id)
        .join(Week, Week.phase_id == Phase.id)
        .join(StudyDay, StudyDay.week_id == Week.id)
        .where(StudyDay.id == day_id)
    )).scalar_one_or_none()


async def _load_blocos(db: AsyncSession, concurso_id: int) -> dict[str, int]:
    """Retorna {slug: bloco_id} para passar como enum ao Claude."""
    rows = (await db.execute(
        select(Bloco.slug, Bloco.id).where(Bloco.concurso_id == concurso_id).order_by(Bloco.ordem)
    )).all()
    return {slug: bid for slug, bid in rows}


@router.get("/{day_id}/material", response_model=StudyMaterialOut)
async def get_material(
    day_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    concurso: Concurso = Depends(get_current_concurso),
):
    await _ensure_day_in_concurso(db, day_id, concurso.id)
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
        "validation_flags": material.validation_flags,
        "status": material.status or "done",
        "error_msg": material.error_msg,
        "questions": questions_out,
    }


async def _enqueue_audio(db, material_id: int):
    """Cria/reseta MaterialAudio('pendente') pro worker pegar."""
    existing = await db.execute(
        select(MaterialAudio).where(MaterialAudio.study_material_id == material_id)
    )
    audio = existing.scalar_one_or_none()
    if audio:
        if audio.status in ("pendente", "gerando"):
            return
        audio.status = "pendente"
        audio.error_msg = None
        audio.arquivo_path = None
        audio.duracao_seg = None
        audio.tamanho_bytes = None
        audio.notebooklm_id = None
        audio.gerado_em = datetime.utcnow()
        audio.concluido_em = None
    else:
        db.add(MaterialAudio(study_material_id=material_id, status="pendente"))


async def _run_generation_bg(material_id: int, topics: list[str], model: str, concurso_id: int):
    """Pipeline com cross-provider validation e retry single-shot.

    1. Sonnet gera material + questões.
    2. Validador (OpenAI ou Claude fallback) audita.
    3. Se houver flag de severidade ALTA, regenera 1x com instrução focada
       nos flags ("a 1ª tentativa errou X; corrija isso").
    4. Re-valida. Publica.
    5. Status final: ok | warning | alerta (warning persistente → Sentry).
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        async with AsyncSessionLocal() as db_pre:
            concurso = await db_pre.get(Concurso, concurso_id)
            if not concurso:
                raise RuntimeError(f"concurso {concurso_id} sumiu")
            examples = await _load_examples(db_pre, concurso.banca)
            bloco_map = await _load_blocos(db_pre, concurso_id)
            ctx = _to_ctx(concurso)

        # --- 1ª tentativa ---
        content_md, questions_data, usage_dict = await claude_client.generate_material(
            topics, ctx, examples, model, bloco_slugs=list(bloco_map.keys()),
        )
        flags, val_info = await claude_client.validate_material(content_md, questions_data)
        tentativas = 1
        regenerado_em = None

        # --- retry se há flag alta ---
        if claude_client.has_high_severity(flags):
            logger.info("material %s: flag alta detectada, regenerando 1x", material_id)
            retry_feedback = claude_client.format_flags_for_retry(flags)
            # Anexa o feedback ao primeiro tópico — o gerador é per-topic, então
            # injeta como sufixo do prompt do usuário via instrução adicional
            topics_with_feedback = [f"{topics[0]}\n\n{retry_feedback}", *topics[1:]] if topics else topics
            content_md2, questions_data2, usage_dict2 = await claude_client.generate_material(
                topics_with_feedback, ctx, examples, model, bloco_slugs=list(bloco_map.keys()),
            )
            flags2, _ = await claude_client.validate_material(content_md2, questions_data2)
            tentativas = 2
            regenerado_em = datetime.utcnow()
            # Sobrescreve com a segunda versão
            content_md, questions_data, flags = content_md2, questions_data2, flags2
            # Soma usage
            for k in usage_dict:
                usage_dict[k] = (usage_dict.get(k) or 0) + (usage_dict2.get(k) or 0)

        # --- classifica status final ---
        if not flags:
            validacao_status = "ok"
        elif claude_client.has_high_severity(flags):
            validacao_status = "alerta"  # persistiu mesmo após retry
            # Alerta admin via Sentry (se configurado)
            try:
                import sentry_sdk
                sentry_sdk.capture_message(
                    f"material {material_id}: flag alta persistiu após retry",
                    level="warning",
                )
            except Exception:
                pass
        else:
            validacao_status = "warning"  # só média/baixa

        async with AsyncSessionLocal() as db:
            material = await db.get(StudyMaterial, material_id)
            if not material:
                return
            material.conteudo_md = content_md
            material.tokens_in = usage_dict.get("input_tokens")
            material.tokens_out = usage_dict.get("output_tokens")
            material.custo_usd = _calc_cost(model, usage_dict)
            material.cache_hit_ratio = _calc_cache_ratio(usage_dict)
            material.validation_flags = flags
            material.tentativas_geracao = tentativas
            material.validador_provider = val_info.get("provider")
            material.validador_modelo = val_info.get("model")
            material.validacao_status = validacao_status
            material.regenerado_em = regenerado_em
            material.status = "done"
            material.error_msg = None

            for i, q in enumerate(questions_data):
                slug = q.get("bloco_slug")
                db.add(GeneratedQuestion(
                    study_material_id=material_id,
                    enunciado=q.get("enunciado", ""),
                    alternativas=q.get("alternativas", {}),
                    gabarito=q.get("gabarito", "A"),
                    comentario=q.get("comentario", ""),
                    disciplina=q.get("disciplina", ""),
                    dificuldade=q.get("dificuldade", "medio"),
                    ordem=i,
                    bloco_id=bloco_map.get(slug) if slug else None,
                ))
            await _enqueue_audio(db, material_id)
            await db.commit()
    except Exception as exc:
        try:
            async with AsyncSessionLocal() as db:
                material = await db.get(StudyMaterial, material_id)
                if material:
                    material.status = "error"
                    material.error_msg = str(exc)[:500]
                    await db.commit()
        except Exception:
            pass


@router.post("/{day_id}/material/generate", response_model=StudyMaterialOut, status_code=202)
async def generate_material(
    day_id: int,
    background_tasks: BackgroundTasks,
    model: str = Query("claude-sonnet-4-6"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
    __: User = Depends(require_active_subscription),
    concurso: Concurso = Depends(get_current_concurso),
):
    if model not in ("claude-sonnet-4-6", "claude-opus-4-7", "claude-opus-4-8"):
        raise HTTPException(400, "Modelo inválido")

    await _ensure_day_in_concurso(db, day_id, concurso.id)
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

    # Delete any existing material
    existing = await db.execute(
        select(StudyMaterial).where(StudyMaterial.study_day_id == day_id)
    )
    existing_material = existing.scalar_one_or_none()
    if existing_material:
        if existing_material.status == "generating":
            return {
                "id": existing_material.id,
                "gerado_em": existing_material.gerado_em,
                "modelo": existing_material.modelo,
                "conteudo_md": "",
                "status": "generating",
                "error_msg": None,
                "tokens_in": None, "tokens_out": None,
                "custo_usd": None, "cache_hit_ratio": None,
                "validation_flags": None,
                "questions": [],
            }
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
        conteudo_md="",
        status="generating",
    )
    db.add(material)
    await db.flush()
    material_id = material.id

    snapshot = {
        "id": material.id,
        "gerado_em": material.gerado_em,
        "modelo": material.modelo,
        "conteudo_md": "",
        "status": "generating",
        "error_msg": None,
        "tokens_in": None, "tokens_out": None,
        "custo_usd": None, "cache_hit_ratio": None,
        "validation_flags": None,
        "questions": [],
    }

    await db.commit()
    background_tasks.add_task(_run_generation_bg, material_id, topics, model, concurso.id)
    return snapshot


async def generate_for_day(day_id: int, model: str | None = None):
    """Used by cron job to generate material for a day without auth."""
    model = model or GENERATION_MODEL
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
        concurso = await _concurso_for_day(db, day_id)
        if not concurso:
            return
        examples = await _load_examples(db, concurso.banca)
        bloco_map = await _load_blocos(db, concurso.id)
        ctx = _to_ctx(concurso)

    # Mesma lógica de retry do _run_generation_bg
    content_md, questions_data, usage_dict = await claude_client.generate_material(
        topics, ctx, examples, model, bloco_slugs=list(bloco_map.keys()),
    )
    flags, val_info = await claude_client.validate_material(content_md, questions_data)
    tentativas = 1
    regenerado_em = None

    if claude_client.has_high_severity(flags):
        retry_feedback = claude_client.format_flags_for_retry(flags)
        topics_retry = [f"{topics[0]}\n\n{retry_feedback}", *topics[1:]] if topics else topics
        content_md2, questions_data2, usage_dict2 = await claude_client.generate_material(
            topics_retry, ctx, examples, model, bloco_slugs=list(bloco_map.keys()),
        )
        flags2, _ = await claude_client.validate_material(content_md2, questions_data2)
        content_md, questions_data, flags = content_md2, questions_data2, flags2
        tentativas = 2
        regenerado_em = datetime.utcnow()
        for k in usage_dict:
            usage_dict[k] = (usage_dict.get(k) or 0) + (usage_dict2.get(k) or 0)

    if not flags:
        validacao_status = "ok"
    elif claude_client.has_high_severity(flags):
        validacao_status = "alerta"
    else:
        validacao_status = "warning"

    async with AsyncSessionLocal() as db:
        material = StudyMaterial(
            study_day_id=day_id,
            modelo=model,
            conteudo_md=content_md,
            tokens_in=usage_dict.get("input_tokens"),
            tokens_out=usage_dict.get("output_tokens"),
            custo_usd=_calc_cost(model, usage_dict),
            cache_hit_ratio=_calc_cache_ratio(usage_dict),
            validation_flags=flags,
            tentativas_geracao=tentativas,
            validador_provider=val_info.get("provider"),
            validador_modelo=val_info.get("model"),
            validacao_status=validacao_status,
            regenerado_em=regenerado_em,
            status="done",
        )
        db.add(material)
        await db.flush()

        for i, q in enumerate(questions_data):
            slug = q.get("bloco_slug")
            gq = GeneratedQuestion(
                study_material_id=material.id,
                enunciado=q.get("enunciado", ""),
                alternativas=q.get("alternativas", {}),
                gabarito=q.get("gabarito", "A"),
                comentario=q.get("comentario", ""),
                disciplina=q.get("disciplina", ""),
                dificuldade=q.get("dificuldade", "medio"),
                ordem=i,
                bloco_id=bloco_map.get(slug) if slug else None,
            )
            db.add(gq)

        await _enqueue_audio(db, material.id)
        await db.commit()


@router.post("/questions/{question_id}/attempt")
async def record_attempt(
    question_id: int,
    body: AttemptCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    concurso: Concurso = Depends(get_current_concurso),
):
    # Verifica que a questão pertence a um dia do concurso atual
    owns = await db.execute(
        select(GeneratedQuestion.id)
        .join(StudyMaterial, GeneratedQuestion.study_material_id == StudyMaterial.id)
        .join(StudyDay, StudyMaterial.study_day_id == StudyDay.id)
        .join(Week, StudyDay.week_id == Week.id)
        .join(Phase, Week.phase_id == Phase.id)
        .where(GeneratedQuestion.id == question_id, Phase.concurso_id == concurso.id)
    )
    if not owns.scalar_one_or_none():
        raise HTTPException(404)

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
                concurso_id=concurso.id,
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
