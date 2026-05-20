"""Reporte de erro pelo aluno em qualquer conteúdo gerado."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_admin_user, get_current_user, get_current_concurso
from ..db import get_db
from ..models import (
    Concurso, ContentReport, GeneratedQuestion, Redacao, StudyMaterial, User,
)

router = APIRouter(prefix="/api", tags=["content_reports"])

VALID_CATEGORIAS = ("conteudo", "questao", "gabarito", "redacao", "outro")
VALID_TARGETS = ("question", "material", "redacao")


class ReportIn(BaseModel):
    target_type: str
    question_id: Optional[int] = None
    material_id: Optional[int] = None
    redacao_id: Optional[int] = None
    categoria: str = "outro"
    descricao: str


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    target_type: str
    question_id: Optional[int] = None
    material_id: Optional[int] = None
    redacao_id: Optional[int] = None
    categoria: str
    descricao: str
    status: str
    nota_admin: Optional[str] = None
    criado_em: datetime
    resolvido_em: Optional[datetime] = None


class AdminReportOut(ReportOut):
    """Visão admin enriquecida: inclui username do autor e contexto do alvo."""
    user_id: int
    username: Optional[str] = None
    concurso_id: Optional[int] = None
    # Trecho curto do alvo (enunciado da questão, primeiras linhas do material, tema da redação)
    target_preview: Optional[str] = None


class ReportResolve(BaseModel):
    status: str  # revisado|aceito|recusado
    nota_admin: Optional[str] = None


@router.post("/content-reports", response_model=ReportOut, status_code=201)
async def create_report(
    body: ReportIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    concurso: Concurso = Depends(get_current_concurso),
):
    if body.target_type not in VALID_TARGETS:
        raise HTTPException(400, "target_type inválido")
    if body.categoria not in VALID_CATEGORIAS:
        raise HTTPException(400, "categoria inválida")
    desc = (body.descricao or "").strip()
    if len(desc) < 10:
        raise HTTPException(400, "Descreva o problema com pelo menos 10 caracteres")

    # Valida que o alvo existe e pertence ao concurso atual
    if body.target_type == "question":
        if not body.question_id:
            raise HTTPException(400, "question_id obrigatório")
        if not await db.get(GeneratedQuestion, body.question_id):
            raise HTTPException(404, "Questão não encontrada")
    elif body.target_type == "material":
        if not body.material_id:
            raise HTTPException(400, "material_id obrigatório")
        if not await db.get(StudyMaterial, body.material_id):
            raise HTTPException(404, "Material não encontrado")
    elif body.target_type == "redacao":
        if not body.redacao_id:
            raise HTTPException(400, "redacao_id obrigatório")
        r = await db.get(Redacao, body.redacao_id)
        if not r or r.user_id != current_user.id:
            raise HTTPException(404, "Redação não encontrada")

    report = ContentReport(
        user_id=current_user.id,
        concurso_id=concurso.id,
        target_type=body.target_type,
        question_id=body.question_id,
        material_id=body.material_id,
        redacao_id=body.redacao_id,
        categoria=body.categoria,
        descricao=desc[:2000],
        status="aberto",
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@router.get("/content-reports/me", response_model=List[ReportOut])
async def list_my_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (await db.execute(
        select(ContentReport)
        .where(ContentReport.user_id == current_user.id)
        .order_by(ContentReport.criado_em.desc())
    )).scalars().all()
    return rows


# --- Admin ---

@router.get("/admin/content-reports", response_model=List[AdminReportOut])
async def admin_list_reports(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    q = select(ContentReport).order_by(ContentReport.criado_em.desc()).limit(200)
    if status:
        q = q.where(ContentReport.status == status)
    rows = (await db.execute(q)).scalars().all()

    # Enriquece com username + preview do alvo
    user_ids = {r.user_id for r in rows}
    users_map: dict[int, str] = {}
    if user_ids:
        users = (await db.execute(
            select(User.id, User.username).where(User.id.in_(user_ids))
        )).all()
        users_map = {uid: uname for uid, uname in users}

    q_ids = {r.question_id for r in rows if r.question_id}
    m_ids = {r.material_id for r in rows if r.material_id}
    r_ids = {r.redacao_id for r in rows if r.redacao_id}

    q_preview: dict[int, str] = {}
    if q_ids:
        rows_q = (await db.execute(
            select(GeneratedQuestion.id, GeneratedQuestion.enunciado).where(GeneratedQuestion.id.in_(q_ids))
        )).all()
        q_preview = {qid: (enu or "")[:200] for qid, enu in rows_q}
    m_preview: dict[int, str] = {}
    if m_ids:
        rows_m = (await db.execute(
            select(StudyMaterial.id, StudyMaterial.conteudo_md).where(StudyMaterial.id.in_(m_ids))
        )).all()
        m_preview = {mid: (md or "")[:200] for mid, md in rows_m}
    r_preview: dict[int, str] = {}
    if r_ids:
        rows_r = (await db.execute(
            select(Redacao.id, Redacao.tema_titulo_snapshot).where(Redacao.id.in_(r_ids))
        )).all()
        r_preview = {rid: (tema or "")[:200] for rid, tema in rows_r}

    def _preview(r: ContentReport) -> Optional[str]:
        if r.question_id and r.question_id in q_preview:
            return q_preview[r.question_id]
        if r.material_id and r.material_id in m_preview:
            return m_preview[r.material_id]
        if r.redacao_id and r.redacao_id in r_preview:
            return r_preview[r.redacao_id]
        return None

    return [
        AdminReportOut(
            id=r.id, target_type=r.target_type,
            question_id=r.question_id, material_id=r.material_id, redacao_id=r.redacao_id,
            categoria=r.categoria, descricao=r.descricao,
            status=r.status, nota_admin=r.nota_admin,
            criado_em=r.criado_em, resolvido_em=r.resolvido_em,
            user_id=r.user_id, username=users_map.get(r.user_id),
            concurso_id=r.concurso_id,
            target_preview=_preview(r),
        )
        for r in rows
    ]


@router.get("/admin/content-reports/count")
async def admin_count_reports(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    """Quantidade de reports abertos (badge no nav)."""
    from sqlalchemy import func
    n = (await db.execute(
        select(func.count(ContentReport.id)).where(ContentReport.status == "aberto")
    )).scalar() or 0
    return {"abertos": int(n)}


@router.put("/admin/content-reports/{report_id}/resolve", response_model=ReportOut)
async def admin_resolve_report(
    report_id: int,
    body: ReportResolve,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    if body.status not in ("revisado", "aceito", "recusado"):
        raise HTTPException(400, "status inválido")
    r = await db.get(ContentReport, report_id)
    if not r:
        raise HTTPException(404)
    r.status = body.status
    r.nota_admin = body.nota_admin
    r.resolvido_em = datetime.utcnow()
    await db.commit()
    await db.refresh(r)
    return r
