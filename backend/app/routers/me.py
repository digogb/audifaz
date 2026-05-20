"""LGPD: exportar e excluir dados do próprio usuário."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user
from ..db import get_db
from ..models import (
    User, UserConcurso, UserDayProgress, UserTopicProgress,
    QuestionAttempt, ErrorEntry, MockExam, MockExamResult,
    Redacao, Subscription,
)

router = APIRouter(prefix="/api/me", tags=["me"])


@router.get("/export")
async def export_my_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """LGPD art. 18, II. Retorna JSON com tudo do usuário."""
    def serialize(rows, fields):
        return [{f: getattr(r, f) for f in fields} for r in rows]

    subs = (await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )).scalars().all()
    uconcursos = (await db.execute(
        select(UserConcurso).where(UserConcurso.user_id == current_user.id)
    )).scalars().all()
    udays = (await db.execute(
        select(UserDayProgress).where(UserDayProgress.user_id == current_user.id)
    )).scalars().all()
    utopics = (await db.execute(
        select(UserTopicProgress).where(UserTopicProgress.user_id == current_user.id)
    )).scalars().all()
    attempts = (await db.execute(
        select(QuestionAttempt).where(QuestionAttempt.user_id == current_user.id)
    )).scalars().all()
    errors = (await db.execute(
        select(ErrorEntry).where(ErrorEntry.user_id == current_user.id)
    )).scalars().all()
    mocks = (await db.execute(
        select(MockExam).where(MockExam.user_id == current_user.id)
    )).scalars().all()
    mock_results = (await db.execute(
        select(MockExamResult).where(MockExamResult.mock_exam_id.in_([m.id for m in mocks] or [-1]))
    )).scalars().all() if mocks else []
    redacoes = (await db.execute(
        select(Redacao).where(Redacao.user_id == current_user.id)
    )).scalars().all()

    return {
        "exported_at": datetime.utcnow().isoformat(),
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "termos_aceitos_versao": current_user.termos_aceitos_versao,
            "termos_aceitos_em": current_user.termos_aceitos_em.isoformat() if current_user.termos_aceitos_em else None,
        },
        "subscriptions": serialize(subs, [
            "id", "concurso_id", "status", "tipo", "valor_cents",
            "criado_em", "trial_ate", "paid_at", "expira_em",
            "payment_provider", "payment_external_id",
        ]),
        "user_concursos": serialize(uconcursos, ["concurso_id", "ativo", "criado_em"]),
        "day_progress": serialize(udays, ["study_day_id", "status", "notas"]),
        "topic_progress": serialize(utopics, ["topic_id", "concluido", "observacao"]),
        "question_attempts": serialize(attempts, [
            "question_id", "alternativa_escolhida", "acertou", "respondido_em", "observacao",
        ]),
        "error_entries": serialize(errors, [
            "id", "concurso_id", "origem", "data", "disciplina", "subtopico",
            "banca", "enunciado", "gabarito", "sua_resposta", "justificativa",
            "revisado_em",
        ]),
        "mock_exams": serialize(mocks, [
            "id", "concurso_id", "data", "tipo", "observacoes",
        ]),
        "mock_results": serialize(mock_results, ["mock_exam_id", "disciplina", "acertos", "total"]),
        "redacoes": serialize(redacoes, [
            "id", "concurso_id", "tema_titulo_snapshot", "texto", "num_linhas",
            "status", "nota_total", "feedback_geral", "criado_em", "corrigido_em",
        ]),
    }


@router.delete("", status_code=204)
async def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """LGPD art. 18, VI. Exclui o usuário e todas as referências.

    Admins internos não podem se auto-excluir por aqui (impede acidente).
    """
    if current_user.is_internal:
        raise HTTPException(403, "Conta interna não pode ser excluída pela API; remova manualmente no DB")

    uid = current_user.id
    # Ordem topológica: filhos primeiro, depois pai
    mock_ids = [m.id for m in (await db.execute(
        select(MockExam).where(MockExam.user_id == uid)
    )).scalars().all()]
    if mock_ids:
        await db.execute(delete(MockExamResult).where(MockExamResult.mock_exam_id.in_(mock_ids)))
    await db.execute(delete(MockExam).where(MockExam.user_id == uid))
    await db.execute(delete(Redacao).where(Redacao.user_id == uid))
    await db.execute(delete(QuestionAttempt).where(QuestionAttempt.user_id == uid))
    await db.execute(delete(ErrorEntry).where(ErrorEntry.user_id == uid))
    await db.execute(delete(UserDayProgress).where(UserDayProgress.user_id == uid))
    await db.execute(delete(UserTopicProgress).where(UserTopicProgress.user_id == uid))
    await db.execute(delete(Subscription).where(Subscription.user_id == uid))
    await db.execute(delete(UserConcurso).where(UserConcurso.user_id == uid))
    await db.execute(delete(User).where(User.id == uid))
    await db.commit()
