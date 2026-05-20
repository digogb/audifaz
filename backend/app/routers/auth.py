from datetime import datetime, timedelta
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import User, Concurso, UserConcurso, Subscription
from ..schemas import LoginRequest, TokenOut
from ..auth import (
    hash_password, verify_password, create_token, get_current_user,
    get_admin_user, get_current_brand, is_admin,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

import re

TRIAL_DAYS = 7
TERMOS_VERSAO_ATUAL = "2026-05-19"

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SignupRequest(BaseModel):
    username: str
    email: str
    password: str
    aceita_termos: bool = False
    concurso_slug: str | None = None


@router.post("/login", response_model=TokenOut)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Credenciais inválidas")
    return TokenOut(token=create_token(user.id, user.username), username=user.username)


@router.post("/register", response_model=TokenOut)
async def register(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalar_one_or_none():
        raise HTTPException(400, "Usuário já existe")
    user = User(username=body.username, password_hash=hash_password(body.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return TokenOut(token=create_token(user.id, user.username), username=user.username)


@router.post("/signup", response_model=TokenOut, status_code=201)
async def signup(
    body: SignupRequest,
    db: AsyncSession = Depends(get_db),
    brand: str = Depends(get_current_brand),
):
    """Signup público. Cria User + UserConcurso + Subscription(trial 7 dias).
    O concurso é resolvido pelo slug ou (na ausência) pelo 1º público da brand do host."""
    username = body.username.strip()
    email = body.email.strip().lower()
    if len(username) < 3 or len(body.password) < 6:
        raise HTTPException(400, "Usuário ou senha muito curtos")
    if not _EMAIL_RE.match(email):
        raise HTTPException(400, "E-mail inválido")
    if not body.aceita_termos:
        raise HTTPException(400, "Aceite dos termos é obrigatório")
    if (await db.execute(select(User).where(User.username == username))).scalar_one_or_none():
        raise HTTPException(409, "Usuário já existe")
    if (await db.execute(select(User).where(User.email == email))).scalar_one_or_none():
        raise HTTPException(409, "E-mail já cadastrado")

    # Resolve concurso por brand do host (+ slug se fornecido)
    q = select(Concurso).where(
        Concurso.brand == brand, Concurso.ativo == True, Concurso.publico == True,
    )
    if body.concurso_slug:
        q = q.where(Concurso.slug == body.concurso_slug)
    q = q.order_by(Concurso.id)
    concurso = (await db.execute(q)).scalars().first()
    if not concurso:
        raise HTTPException(400, "Nenhum concurso público disponível para esta brand")

    now = datetime.utcnow()

    user = User(
        username=username, email=email,
        password_hash=hash_password(body.password),
        termos_aceitos_versao=TERMOS_VERSAO_ATUAL,
        termos_aceitos_em=now,
    )
    db.add(user)
    await db.flush()
    db.add(UserConcurso(user_id=user.id, concurso_id=concurso.id, ativo=True))
    user.concurso_atual_id = concurso.id

    # Cria assinatura: se o concurso requer, entra em trial; senão, ativa direto
    if concurso.requer_assinatura:
        sub = Subscription(
            user_id=user.id, concurso_id=concurso.id,
            status="trial", tipo="single",
            valor_cents=concurso.preco_cents,
            criado_em=now, trial_ate=now + timedelta(days=TRIAL_DAYS),
        )
    else:
        sub = Subscription(
            user_id=user.id, concurso_id=concurso.id,
            status="ativa", tipo="single",
            valor_cents=0, criado_em=now, paid_at=now,
        )
    db.add(sub)
    await db.commit()
    await db.refresh(user)
    return TokenOut(token=create_token(user.id, user.username), username=user.username)


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "is_admin": is_admin(current_user),
        "is_internal": current_user.is_internal,
    }
