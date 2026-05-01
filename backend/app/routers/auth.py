from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import User
from ..schemas import LoginRequest, TokenOut
from ..auth import hash_password, verify_password, create_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Credenciais inválidas")
    return TokenOut(token=create_token(user.id, user.username), username=user.username)


@router.post("/register", response_model=TokenOut)
async def register(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalar_one_or_none():
        raise HTTPException(400, "Usuário já existe")
    user = User(username=body.username, password_hash=hash_password(body.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return TokenOut(token=create_token(user.id, user.username), username=user.username)


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username}
