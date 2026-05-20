from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import claude_client
from ..auth import get_admin_user, get_current_user, get_current_concurso
from ..claude_client import ConcursoContext, _calc_cost
from ..db import AsyncSessionLocal, get_db
from ..models import Concurso, Redacao, RedacaoTema, User

router = APIRouter(prefix="/api", tags=["redacoes"])


# ----- schemas -----

class TemaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    titulo: str
    enunciado_md: str
    textos_apoio_md: Optional[str] = None
    ordem: int


class TemaIn(BaseModel):
    titulo: str
    enunciado_md: str
    textos_apoio_md: Optional[str] = None
    ordem: int = 0


class RedacaoSubmit(BaseModel):
    tema_id: int
    texto: str


class SugestaoOut(BaseModel):
    trecho: str
    problema: str
    sugestao: str
    categoria: str


class RedacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tema_id: Optional[int]
    tema_titulo_snapshot: str
    texto: str
    num_linhas: int
    status: str
    nota_recorte: Optional[float] = None
    nota_interpretacao: Optional[float] = None
    nota_progressao: Optional[float] = None
    nota_vocabular: Optional[float] = None
    nota_coesao: Optional[float] = None
    nota_morfo: Optional[float] = None
    nota_total: Optional[float] = None
    feedback_geral: Optional[str] = None
    sugestoes: Optional[List[SugestaoOut]] = None
    zerou_motivo: Optional[str] = None
    error_msg: Optional[str] = None
    criado_em: datetime
    corrigido_em: Optional[datetime] = None


class RedacaoListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tema_titulo_snapshot: str
    status: str
    nota_total: Optional[float] = None
    num_linhas: int
    criado_em: datetime
    corrigido_em: Optional[datetime] = None


# ----- helpers -----

def _to_ctx(c: Concurso) -> ConcursoContext:
    return ConcursoContext(
        nome=c.nome, banca=c.banca, orgao=c.orgao, cargo=c.cargo,
        data_prova=c.data_prova, prompt_extra=c.prompt_extra,
    )


def _count_content_lines(texto: str) -> int:
    return sum(1 for ln in texto.split("\n") if ln.strip())


async def _correct_in_background(redacao_id: int):
    try:
        async with AsyncSessionLocal() as db:
            r = await db.get(Redacao, redacao_id)
            if not r:
                return
            r.status = "corrigindo"
            await db.commit()

            tema = await db.get(RedacaoTema, r.tema_id) if r.tema_id else None
            concurso = await db.get(Concurso, r.concurso_id)
            if not concurso:
                r.status = "erro"
                r.error_msg = "concurso não encontrado"
                await db.commit()
                return
            ctx = _to_ctx(concurso)
            enunciado = tema.enunciado_md if tema else r.tema_titulo_snapshot
            apoio = tema.textos_apoio_md if tema else None
            texto = r.texto
            titulo = r.tema_titulo_snapshot

        # chamada Claude fora da transação
        correcao, usage = await claude_client.correct_redacao(
            texto, titulo, enunciado, apoio, ctx,
        )

        async with AsyncSessionLocal() as db:
            r = await db.get(Redacao, redacao_id)
            if not r:
                return
            r.nota_recorte = float(correcao.get("nota_recorte") or 0)
            r.nota_interpretacao = float(correcao.get("nota_interpretacao") or 0)
            r.nota_progressao = float(correcao.get("nota_progressao") or 0)
            r.nota_vocabular = float(correcao.get("nota_vocabular") or 0)
            r.nota_coesao = float(correcao.get("nota_coesao") or 0)
            r.nota_morfo = float(correcao.get("nota_morfo") or 0)
            r.nota_total = round(
                r.nota_recorte + r.nota_interpretacao + r.nota_progressao
                + r.nota_vocabular + r.nota_coesao + r.nota_morfo,
                2,
            )
            r.feedback_geral = correcao.get("feedback_geral")
            r.sugestoes = correcao.get("sugestoes") or []
            r.zerou_motivo = correcao.get("zerou_motivo")
            r.tokens_in = usage.get("input_tokens")
            r.tokens_out = usage.get("output_tokens")
            r.custo_usd = _calc_cost("claude-sonnet-4-6", usage)
            r.status = "done"
            r.corrigido_em = datetime.utcnow()
            await db.commit()
    except Exception as exc:
        try:
            async with AsyncSessionLocal() as db:
                r = await db.get(Redacao, redacao_id)
                if r:
                    r.status = "erro"
                    r.error_msg = str(exc)[:500]
                    await db.commit()
        except Exception:
            pass


# ----- temas -----

@router.get("/redacao/temas", response_model=List[TemaOut])
async def list_temas(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    concurso: Concurso = Depends(get_current_concurso),
):
    rows = (await db.execute(
        select(RedacaoTema)
        .where(RedacaoTema.concurso_id == concurso.id, RedacaoTema.ativo == True)
        .order_by(RedacaoTema.ordem, RedacaoTema.id)
    )).scalars().all()
    return rows


@router.post("/admin/redacao/temas", response_model=TemaOut, status_code=201)
async def admin_create_tema(
    body: TemaIn,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    concurso: Concurso = Depends(get_current_concurso),
):
    tema = RedacaoTema(concurso_id=concurso.id, ativo=True, **body.model_dump())
    db.add(tema)
    await db.commit()
    await db.refresh(tema)
    return tema


@router.delete("/admin/redacao/temas/{tema_id}", status_code=204)
async def admin_delete_tema(
    tema_id: int,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
    concurso: Concurso = Depends(get_current_concurso),
):
    tema = await db.get(RedacaoTema, tema_id)
    if not tema or tema.concurso_id != concurso.id:
        raise HTTPException(404)
    await db.delete(tema)
    await db.commit()


# ----- redação -----

@router.get("/redacao", response_model=List[RedacaoListItem])
async def list_minhas_redacoes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    concurso: Concurso = Depends(get_current_concurso),
):
    rows = (await db.execute(
        select(Redacao)
        .where(Redacao.user_id == current_user.id, Redacao.concurso_id == concurso.id)
        .order_by(Redacao.criado_em.desc())
    )).scalars().all()
    return rows


@router.get("/redacao/{redacao_id}", response_model=RedacaoOut)
async def get_redacao(
    redacao_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    concurso: Concurso = Depends(get_current_concurso),
):
    r = await db.get(Redacao, redacao_id)
    if not r or r.user_id != current_user.id or r.concurso_id != concurso.id:
        raise HTTPException(404)
    return r


@router.post("/redacao", response_model=RedacaoOut, status_code=202)
async def submit_redacao(
    body: RedacaoSubmit,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    concurso: Concurso = Depends(get_current_concurso),
):
    tema = await db.get(RedacaoTema, body.tema_id)
    if not tema or tema.concurso_id != concurso.id:
        raise HTTPException(404, "Tema não encontrado neste concurso")

    texto = (body.texto or "").strip()
    if not texto:
        raise HTTPException(400, "Texto vazio")
    num_linhas = _count_content_lines(texto)

    # Não bloqueia textos curtos — a banca zera, e o feedback explica
    r = Redacao(
        user_id=current_user.id,
        concurso_id=concurso.id,
        tema_id=tema.id,
        tema_titulo_snapshot=tema.titulo,
        texto=texto,
        num_linhas=num_linhas,
        status="pendente",
    )
    db.add(r)
    await db.commit()
    await db.refresh(r)

    background_tasks.add_task(_correct_in_background, r.id)
    return r


@router.delete("/redacao/{redacao_id}", status_code=204)
async def delete_redacao(
    redacao_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    concurso: Concurso = Depends(get_current_concurso),
):
    r = await db.get(Redacao, redacao_id)
    if not r or r.user_id != current_user.id or r.concurso_id != concurso.id:
        raise HTTPException(404)
    await db.delete(r)
    await db.commit()
