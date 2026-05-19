import os
import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .db import get_db
from .models import User, Concurso, UserConcurso

SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production-please")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "").strip()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

bearer = HTTPBearer()


def is_admin(user: User) -> bool:
    return bool(ADMIN_USERNAME) and user.username == ADMIN_USERNAME


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(user_id: int, username: str) -> str:
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": str(user_id), "username": username, "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")
    return user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not is_admin(current_user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Apenas o admin pode executar esta ação")
    return current_user


async def get_current_concurso(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Concurso:
    """Retorna o concurso ativo do usuário. Se concurso_atual_id estiver vazio,
    cai no primeiro UserConcurso ativo e persiste o valor."""
    if current_user.concurso_atual_id:
        concurso = await db.get(Concurso, current_user.concurso_atual_id)
        if concurso and concurso.ativo:
            return concurso

    result = await db.execute(
        select(Concurso)
        .join(UserConcurso, UserConcurso.concurso_id == Concurso.id)
        .where(UserConcurso.user_id == current_user.id, UserConcurso.ativo == True, Concurso.ativo == True)
        .order_by(UserConcurso.criado_em)
        .limit(1)
    )
    concurso = result.scalar_one_or_none()
    if not concurso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário não está vinculado a nenhum concurso ativo",
        )

    current_user.concurso_atual_id = concurso.id
    await db.commit()
    return concurso
