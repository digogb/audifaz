from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel
from datetime import date
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user, get_admin_user, get_current_brand
from ..db import get_db
from ..models import Concurso, UserConcurso, User, BancaExample
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


class BancaExampleIn(BaseModel):
    banca: str
    fonte: str
    ano: Optional[int] = None
    disciplina: str
    enunciado: str
    alternativas: dict
    gabarito: str
    comentario: Optional[str] = None


class BancaExampleOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    banca: str
    fonte: str
    ano: Optional[int] = None
    disciplina: str
    enunciado: str
    alternativas: dict
    gabarito: str
    comentario: Optional[str] = None
    ativo: bool


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
            edital_url=c.edital_url, theme_slug=c.theme_slug, ativo=c.ativo,
            atual=(c.id == current_user.concurso_atual_id),
        )
        for c in concursos
    ]


@router.get("/concursos/disponiveis", response_model=List[ConcursoOut])
async def list_public_concursos(
    db: AsyncSession = Depends(get_db),
    brand: str = Depends(get_current_brand),
):
    """Catálogo público (sem auth) para landing/signup, filtrado pela brand do host."""
    result = await db.execute(
        select(Concurso)
        .where(
            Concurso.publico == True,
            Concurso.ativo == True,
            Concurso.brand == brand,
        )
        .order_by(Concurso.nome)
    )
    concursos = result.scalars().all()
    return [ConcursoOut.model_validate(c) for c in concursos]


@router.get("/brand")
async def current_brand(brand: str = Depends(get_current_brand)):
    """Expõe a brand inferida pelo Host (público, útil pro frontend antes do login)."""
    return {"brand": brand}


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
        descricao=concurso.descricao, edital_url=concurso.edital_url,
        theme_slug=concurso.theme_slug, ativo=concurso.ativo,
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


@router.get("/admin/banca-examples", response_model=List[BancaExampleOut])
async def admin_list_examples(
    banca: Optional[str] = None,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(BancaExample).order_by(BancaExample.banca, BancaExample.id)
    if banca:
        q = q.where(BancaExample.banca == banca)
    rows = (await db.execute(q)).scalars().all()
    return rows


@router.post("/admin/banca-examples", response_model=BancaExampleOut, status_code=201)
async def admin_create_example(
    body: BancaExampleIn,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    ex = BancaExample(**body.model_dump(), ativo=True)
    db.add(ex)
    await db.commit()
    await db.refresh(ex)
    return ex


@router.delete("/admin/banca-examples/{example_id}", status_code=204)
async def admin_delete_example(
    example_id: int,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    ex = await db.get(BancaExample, example_id)
    if not ex:
        raise HTTPException(404)
    await db.delete(ex)
    await db.commit()


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
        descricao=concurso.descricao, edital_url=concurso.edital_url,
        theme_slug=concurso.theme_slug, ativo=concurso.ativo,
        atual=True,
    )
