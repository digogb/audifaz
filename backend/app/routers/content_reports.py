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

@router.get("/admin/content-reports", response_model=List[ReportOut])
async def admin_list_reports(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    q = select(ContentReport).order_by(ContentReport.criado_em.desc()).limit(200)
    if status:
        q = q.where(ContentReport.status == status)
    rows = (await db.execute(q)).scalars().all()
    return rows


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
