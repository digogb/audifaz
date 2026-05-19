from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel
from datetime import date
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user, get_admin_user
from ..db import get_db
from ..models import Concurso, UserConcurso, User
from ..schemas import ConcursoOut
from ..services.plan_importer import import_plan, parse_plan, detect_format

router = APIRouter(prefix="/api", tags=["concursos"])


class ConcursoCreate(BaseModel):
    slug: str
    nome: str
    banca: str
    orgao: str
    cargo: str
    data_prova: Optional[date] = None
    descricao: Optional[str] = None
    edital_url: Optional[str] = None
    prompt_extra: Optional[str] = None
    publico: bool = False


@router.get("/concursos", response_model=List[ConcursoOut])
async def list_my_concursos(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Concurso)
        .join(UserConcurso, UserConcurso.concurso_id == Concurso.id)
        .where(UserConcurso.user_id == current_user.id, UserConcurso.ativo == True)
        .order_by(Concurso.nome)
    )
    concursos = result.scalars().all()
    return [
        ConcursoOut(
            id=c.id, slug=c.slug, nome=c.nome, banca=c.banca, orgao=c.orgao,
            cargo=c.cargo, data_prova=c.data_prova, descricao=c.descricao,
            edital_url=c.edital_url, ativo=c.ativo,
            atual=(c.id == current_user.concurso_atual_id),
        )
        for c in concursos
    ]


@router.get("/concursos/disponiveis", response_model=List[ConcursoOut])
async def list_public_concursos(db: AsyncSession = Depends(get_db)):
    """Catálogo público (sem auth) para landing/signup."""
    result = await db.execute(
        select(Concurso).where(Concurso.publico == True, Concurso.ativo == True).order_by(Concurso.nome)
    )
    concursos = result.scalars().all()
    return [ConcursoOut.model_validate(c) for c in concursos]


@router.post("/admin/concursos", response_model=ConcursoOut, status_code=201)
async def admin_create_concurso(
    body: ConcursoCreate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    exists = await db.execute(select(Concurso).where(Concurso.slug == body.slug))
    if exists.scalar_one_or_none():
        raise HTTPException(409, f"Já existe concurso com slug '{body.slug}'")

    concurso = Concurso(**body.model_dump(), ativo=True)
    db.add(concurso)
    await db.flush()
    db.add(UserConcurso(user_id=admin.id, concurso_id=concurso.id, ativo=True))
    await db.commit()
    await db.refresh(concurso)
    return ConcursoOut(
        id=concurso.id, slug=concurso.slug, nome=concurso.nome, banca=concurso.banca,
        orgao=concurso.orgao, cargo=concurso.cargo, data_prova=concurso.data_prova,
        descricao=concurso.descricao, edital_url=concurso.edital_url, ativo=concurso.ativo,
        atual=False,
    )


@router.post("/admin/concursos/{concurso_id}/preview-plano")
async def admin_preview_plano(
    concurso_id: int,
    file: UploadFile = File(...),
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Faz parse do arquivo sem persistir; útil para mostrar contagens antes de importar."""
    concurso = await db.get(Concurso, concurso_id)
    if not concurso:
        raise HTTPException(404, "Concurso não encontrado")
    content = (await file.read()).decode("utf-8", errors="replace")
    fmt = detect_format(content)
    if fmt == "unknown":
        raise HTTPException(400, "Formato de plano não reconhecido (SEFAZ ou TJCE)")
    plan = parse_plan(content)
    return {
        "formato": fmt,
        "fases": len(plan.phases),
        "semanas": len(plan.weeks),
        "dias": plan.total_days,
        "topicos": plan.total_topics,
        "primeira_semana": (
            {
                "numero": plan.weeks[0].numero,
                "tema": plan.weeks[0].tema,
                "inicio": plan.weeks[0].data_inicio.isoformat(),
                "fim": plan.weeks[0].data_fim.isoformat(),
            }
            if plan.weeks else None
        ),
    }


@router.post("/admin/concursos/{concurso_id}/importar-plano")
async def admin_import_plano(
    concurso_id: int,
    file: UploadFile = File(...),
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Apaga Phases/Weeks/StudyDays/Topics do concurso e importa do .md."""
    concurso = await db.get(Concurso, concurso_id)
    if not concurso:
        raise HTTPException(404, "Concurso não encontrado")
    content = (await file.read()).decode("utf-8", errors="replace")
    try:
        counts = await import_plan(db, concurso_id, content)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return {"concurso_id": concurso_id, **counts}


@router.put("/me/concurso-atual/{concurso_id}", response_model=ConcursoOut)
async def set_concurso_atual(
    concurso_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    link = await db.execute(
        select(UserConcurso).where(
            UserConcurso.user_id == current_user.id,
            UserConcurso.concurso_id == concurso_id,
            UserConcurso.ativo == True,
        )
    )
    if not link.scalar_one_or_none():
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuário não tem acesso a este concurso")

    concurso = await db.get(Concurso, concurso_id)
    if not concurso or not concurso.ativo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Concurso inexistente ou inativo")

    current_user.concurso_atual_id = concurso_id
    await db.commit()
    await db.refresh(current_user)

    return ConcursoOut(
        id=concurso.id, slug=concurso.slug, nome=concurso.nome, banca=concurso.banca,
        orgao=concurso.orgao, cargo=concurso.cargo, data_prova=concurso.data_prova,
        descricao=concurso.descricao, edital_url=concurso.edital_url, ativo=concurso.ativo,
        atual=True,
    )
