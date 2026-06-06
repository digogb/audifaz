import os
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db, AsyncSessionLocal
from ..models import StudyDay, StudyMaterial, GeneratedQuestion, QuestionAttempt, ErrorEntry, User, MaterialAudio, Week, Phase, Concurso, BancaExample, Bloco, Topic
from ..schemas import StudyMaterialOut, AttemptCreate
from .. import claude_client
from ..claude_client import _calc_cost, _calc_cache_ratio, ConcursoContext
from ..auth import get_current_user, get_admin_user, get_current_concurso, require_active_subscription
from ..config import audio_enabled

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


def _clean_alternativas(alts) -> dict:
    """Mantém apenas as chaves A–E. A geração às vezes injeta chaves espúrias
    (ex.: 'comentario' com o gabarito embutido, ou um 'F'), que vazariam para o
    cliente já que o dict de alternativas sempre é renderizado."""
    if not isinstance(alts, dict):
        return {}
    return {k.upper(): v for k, v in alts.items() if k.upper() in ("A", "B", "C", "D", "E")}


def _parse_gabarito(raw) -> str:
    """Normaliza o gabarito retornado pelo Claude.

    dict.get("gabarito", "A") retorna None quando a chave existe mas o valor é
    null — o default só é usado quando a chave está ausente. Este helper
    garante que o gabarito é sempre uma letra válida (A–E), usando "A" como
    fallback seguro quando o modelo viola o schema."""
    if not raw:
        return "A"
    g = str(raw).strip().upper()[:1]
    return g if g in ("A", "B", "C", "D", "E") else "A"


def _salvage_comentario(comentario, alts) -> str:
    """Se o comentário veio vazio mas o modelo o embutiu em alternativas['comentario'],
    recupera-o antes de _clean_alternativas descartar a chave (senão perderíamos a
    explicação — foi exatamente o que aconteceu com questões antigas)."""
    if (comentario or "").strip():
        return comentario
    if isinstance(alts, dict):
        emb = alts.get("comentario") or alts.get("Comentario")
        if emb and emb.strip():
            return emb.strip()
    return comentario or ""


def _rotate(rows: list, n: int, seed: int | None) -> list:
    """Janela contígua determinística de `n` itens começando em `seed % len`.

    Mesma seed (= data do dia) → mesmo conjunto, o que mantém o cache do prompt
    estável no burst do cron; seeds diferentes → janelas diferentes, exercitando
    todo o acervo ao longo do plano.
    """
    if not rows:
        return []
    if seed is None or len(rows) <= n:
        return rows[:n]
    start = seed % len(rows)
    return [rows[(start + i) % len(rows)] for i in range(n)]


async def _focus_terms_for_day(db: AsyncSession, day_id: int) -> list[str]:
    """Termos (keywords + nome dos blocos do dia) p/ priorizar exemplos on-topic.

    Usa Bloco.keywords (CSV curado "para heurística") dos blocos referenciados
    pelos tópicos do dia. Vazio em dias sem disciplina única (redação, revisão).
    """
    bloco_ids = {
        b for (b,) in (await db.execute(
            select(Topic.bloco_id).where(
                Topic.study_day_id == day_id, Topic.bloco_id.isnot(None)
            )
        )).all()
    }
    if not bloco_ids:
        return []
    rows = (await db.execute(
        select(Bloco.nome, Bloco.keywords).where(Bloco.id.in_(bloco_ids))
    )).all()
    terms: list[str] = []
    for nome, kw in rows:
        terms += [k.strip().lower() for k in (kw or "").split(",") if k.strip()]
        if nome:
            terms.append(nome.lower())
    return list(dict.fromkeys(terms))  # dedup preservando ordem


async def _load_examples(
    db: AsyncSession,
    banca: str,
    limit: int = 12,
    seed: int | None = None,
    focus_terms: list[str] | None = None,
) -> list[dict]:
    rows = (await db.execute(
        select(BancaExample)
        .where(BancaExample.banca == banca, BancaExample.ativo == True)
        .order_by(BancaExample.id)
    )).scalars().all()

    if focus_terms:
        # Prioriza exemplos cuja disciplina casa com os termos do dia; completa
        # com o restante (rotacionado) para sempre devolver `limit`. A rotação
        # roda dentro de cada subconjunto, preservando variedade entre datas.
        ft = [t for t in focus_terms if t]
        on, on_ids = [], set()
        for r in rows:
            d = (r.disciplina or "").lower()
            if any(t in d for t in ft):
                on.append(r)
                on_ids.add(r.id)
        off = [r for r in rows if r.id not in on_ids]
        picked = _rotate(on, limit, seed)
        if len(picked) < limit:
            picked += _rotate(off, limit - len(picked), seed)
    else:
        picked = _rotate(rows, limit, seed)

    return [
        {
            "fonte": r.fonte,
            "ano": r.ano,
            "disciplina": r.disciplina,
            "enunciado": r.enunciado,
            "alternativas": r.alternativas,
            "gabarito": r.gabarito,
        }
        for r in picked
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
        q_out = {
            "id": q.id,
            "enunciado": q.enunciado,
            "alternativas": q.alternativas,
            "disciplina": q.disciplina,
            "dificuldade": q.dificuldade,
            "ordem": q.ordem,
            "attempt": att_out,
        }
        # Gabarito e comentário só são expostos depois que o usuário respondeu —
        # senão vazam no payload (DevTools) antes da tentativa.
        if att:
            q_out["gabarito"] = q.gabarito
            q_out["comentario"] = q.comentario
        questions_out.append(q_out)

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
    """Cria/reseta MaterialAudio('pendente') pro worker pegar.

    No-op quando o áudio está desabilitado (prod não roda o audio-worker):
    evita acumular registros 'pendente' que nunca seriam processados.
    """
    if not audio_enabled():
        return
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
            mat = await db_pre.get(StudyMaterial, material_id)
            day = await db_pre.get(StudyDay, mat.study_day_id) if mat else None
            seed = day.data.toordinal() if day else None
            focus = await _focus_terms_for_day(db_pre, day.id) if day else None
            examples = await _load_examples(db_pre, concurso.banca, seed=seed, focus_terms=focus)
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
            # Sem questões = geração quebrada → 'error' (fica visível e regerável).
            material.status = "done" if questions_data else "error"
            material.error_msg = None if questions_data else "geração retornou 0 questões"

            for i, q in enumerate(questions_data):
                slug = q.get("bloco_slug")
                db.add(GeneratedQuestion(
                    study_material_id=material_id,
                    enunciado=q.get("enunciado", ""),
                    alternativas=_clean_alternativas(q.get("alternativas", {})),
                    gabarito=_parse_gabarito(q.get("gabarito")),
                    comentario=_salvage_comentario(q.get("comentario", ""), q.get("alternativas", {})),
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
        # Reaproveita material só se estiver íntegro (done + com questões).
        # Materiais quebrados (status=error ou 0 questões — ex.: o modelo não
        # chamou registrar_questoes) são descartados e regerados: assim o cron
        # se auto-corrige na próxima execução em vez de pular o dia para sempre.
        existing = (await db.execute(
            select(StudyMaterial).where(StudyMaterial.study_day_id == day_id)
        )).scalar_one_or_none()
        if existing:
            nq = await db.scalar(
                select(func.count(GeneratedQuestion.id)).where(
                    GeneratedQuestion.study_material_id == existing.id
                )
            )
            if existing.status == "done" and nq > 0:
                return
            await db.execute(
                delete(GeneratedQuestion).where(
                    GeneratedQuestion.study_material_id == existing.id
                )
            )
            await db.delete(existing)
            await db.commit()

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
        focus = await _focus_terms_for_day(db, day.id)
        examples = await _load_examples(db, concurso.banca, seed=day.data.toordinal(), focus_terms=focus)
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

    # Sem questões = geração quebrada. Persiste como 'error' (não 'done') para
    # ficar visível e para o cron regenerar na próxima execução — em vez de
    # aceitar silenciosamente um dia sem questões.
    final_status = "done" if questions_data else "error"
    final_error = None if questions_data else "geração retornou 0 questões"

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
            status=final_status,
            error_msg=final_error,
        )
        db.add(material)
        await db.flush()

        for i, q in enumerate(questions_data):
            slug = q.get("bloco_slug")
            gq = GeneratedQuestion(
                study_material_id=material.id,
                enunciado=q.get("enunciado", ""),
                alternativas=_clean_alternativas(q.get("alternativas", {})),
                gabarito=_parse_gabarito(q.get("gabarito")),
                comentario=_salvage_comentario(q.get("comentario", ""), q.get("alternativas", {})),
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

    if not question.gabarito:
        raise HTTPException(422, detail="Questão com gabarito inválido; por favor reporte o erro.")

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
    return {"acertou": acertou, "gabarito": question.gabarito, "comentario": question.comentario}
