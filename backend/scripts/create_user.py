"""Cria (ou reusa) um usuário e o vincula a UM concurso existente, pelo slug.

Idempotente e seguro:
  - NUNCA cria/edita concursos. Apenas resolve o concurso pelo slug.
  - Se o usuário já existe: não recria. Com --reset-senha, reseta só a senha.
  - Cria UserConcurso (ativo) + define concurso_atual_id.
  - Cria Subscription: se o concurso requer assinatura → trial; senão → ativa (R$0).
  - Toca SOMENTE o usuário alvo; nenhum outro usuário/concurso é alterado.

Uso (dentro do container app):
    python scripts/create_user.py --username valdyrsf --senha 'XXXX' \
        --concurso-slug sefaz-ce-2026 [--email a@b.com] [--reset-senha]
"""

import argparse
import asyncio
import secrets
from datetime import datetime, timedelta

from sqlalchemy import select

from app.db import AsyncSessionLocal
from app.models import Concurso, User, UserConcurso, Subscription
from app.auth import hash_password

TERMOS_VERSAO_ATUAL = "2026-05-20"
TRIAL_DAYS = 7


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--username", required=True)
    ap.add_argument("--senha", required=True)
    ap.add_argument("--concurso-slug", required=True)
    ap.add_argument("--email", default=None)
    ap.add_argument("--reset-senha", action="store_true")
    args = ap.parse_args()

    now = datetime.utcnow()

    async with AsyncSessionLocal() as db:
        concurso = (
            await db.execute(select(Concurso).where(Concurso.slug == args.concurso_slug))
        ).scalar_one_or_none()
        if not concurso:
            raise SystemExit(f"ERRO: concurso slug={args.concurso_slug!r} não existe")
        if not concurso.ativo:
            raise SystemExit(f"ERRO: concurso {args.concurso_slug!r} está inativo")

        user = (
            await db.execute(select(User).where(User.username == args.username))
        ).scalar_one_or_none()

        if user:
            print(f"Usuário {args.username!r} JÁ EXISTE (id={user.id}).")
            if args.reset_senha:
                user.password_hash = hash_password(args.senha)
                print("  → senha resetada.")
        else:
            user = User(
                username=args.username,
                email=(args.email.strip().lower() if args.email else None),
                password_hash=hash_password(args.senha),
                podcast_token=secrets.token_hex(16),
                termos_aceitos_versao=TERMOS_VERSAO_ATUAL,
                termos_aceitos_em=now,
                created_at=now,
                is_internal=False,
            )
            db.add(user)
            await db.flush()
            print(f"Usuário {args.username!r} CRIADO (id={user.id}).")

        # Vínculo concurso (idempotente)
        link = (
            await db.execute(
                select(UserConcurso).where(
                    UserConcurso.user_id == user.id,
                    UserConcurso.concurso_id == concurso.id,
                )
            )
        ).scalar_one_or_none()
        if link:
            if not link.ativo:
                link.ativo = True
                print(f"  → vínculo com {concurso.slug} reativado.")
            else:
                print(f"  → já vinculado a {concurso.slug}.")
        else:
            db.add(UserConcurso(user_id=user.id, concurso_id=concurso.id, ativo=True, criado_em=now))
            print(f"  → vinculado a {concurso.slug}.")

        user.concurso_atual_id = concurso.id

        # Assinatura (idempotente)
        sub = (
            await db.execute(
                select(Subscription).where(
                    Subscription.user_id == user.id,
                    Subscription.concurso_id == concurso.id,
                )
            )
        ).scalar_one_or_none()
        if not sub:
            if concurso.requer_assinatura:
                db.add(Subscription(
                    user_id=user.id, concurso_id=concurso.id,
                    status="trial", tipo="single", valor_cents=concurso.preco_cents,
                    criado_em=now, trial_ate=now + timedelta(days=TRIAL_DAYS),
                ))
                print(f"  → assinatura TRIAL ({TRIAL_DAYS}d) criada.")
            else:
                db.add(Subscription(
                    user_id=user.id, concurso_id=concurso.id,
                    status="ativa", tipo="single", valor_cents=0,
                    criado_em=now, paid_at=now,
                ))
                print("  → assinatura ATIVA (R$0, concurso sem paywall) criada.")
        else:
            print(f"  → assinatura já existe (status={sub.status}).")

        await db.commit()
        print("OK: commit concluído.")


if __name__ == "__main__":
    asyncio.run(main())
