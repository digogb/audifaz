"""Endpoints de billing: checkout Pix via Mercado Pago + webhook.

Para uso pelo aluno após o trial expirar (ou a qualquer momento).
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user
from ..db import get_db
from ..models import Concurso, Subscription, User
from ..services import mercadopago

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/billing", tags=["billing"])


class CheckoutOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    payment_id: str
    status: str
    qr_code: Optional[str] = None
    qr_code_base64: Optional[str] = None
    ticket_url: Optional[str] = None
    valor_cents: int


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    concurso_id: int
    status: str
    tipo: str
    valor_cents: Optional[int]
    trial_ate: Optional[datetime]
    paid_at: Optional[datetime]
    expira_em: Optional[datetime]
    payment_provider: Optional[str]


@router.get("/me", response_model=list[SubscriptionOut])
async def list_my_subscriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )).scalars().all()
    return rows


@router.post("/checkout/{concurso_id}", response_model=CheckoutOut)
async def create_checkout(
    concurso_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cria payment Pix no MP. Reusa o mesmo payment_external_id se já houver um aberto."""
    concurso = await db.get(Concurso, concurso_id)
    if not concurso or not concurso.requer_assinatura:
        raise HTTPException(404, "Concurso não exige assinatura")
    if not concurso.preco_cents or concurso.preco_cents <= 0:
        raise HTTPException(400, "Concurso sem preço configurado")

    sub = (await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.concurso_id == concurso_id,
        )
    )).scalar_one_or_none()
    if sub and sub.status == "ativa":
        raise HTTPException(409, "Assinatura já está ativa")
    if not sub:
        sub = Subscription(
            user_id=current_user.id, concurso_id=concurso_id,
            status="trial", tipo="single",
            valor_cents=concurso.preco_cents,
            criado_em=datetime.utcnow(),
        )
        db.add(sub)
        await db.flush()

    # E-mail do usuário: como não armazenamos email ainda, usamos placeholder estável
    # baseado no username; o MP precisa de algo válido em formato.
    payer_email = f"{current_user.username}@anajud.local"
    try:
        payment = await mercadopago.create_pix_payment(
            amount_cents=concurso.preco_cents,
            description=f"AnaJud — {concurso.nome}",
            payer_email=payer_email,
            subscription_id=sub.id,
        )
    except mercadopago.MercadoPagoError as exc:
        raise HTTPException(502, f"Falha ao criar pagamento: {exc}")

    sub.payment_provider = "mercado_pago"
    sub.payment_external_id = str(payment["id"])
    await db.commit()

    return CheckoutOut(
        payment_id=str(payment["id"]),
        status=payment["status"],
        qr_code=payment.get("qr_code"),
        qr_code_base64=payment.get("qr_code_base64"),
        ticket_url=payment.get("ticket_url"),
        valor_cents=concurso.preco_cents,
    )


@router.post("/mp/webhook", status_code=200)
async def mp_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Recebe notificações do Mercado Pago. Consulta payment, ativa Subscription se approved."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    payment_id = None
    if isinstance(body, dict):
        data = body.get("data") or {}
        payment_id = data.get("id") or body.get("id")
    payment_id = payment_id or request.query_params.get("data.id") or request.query_params.get("id")
    if not payment_id:
        logger.warning("webhook MP sem id: body=%s qp=%s", body, dict(request.query_params))
        return {"ok": True}  # ack mesmo assim para não receber retry

    try:
        payment = await mercadopago.fetch_payment(str(payment_id))
    except mercadopago.MercadoPagoError as exc:
        logger.error("falha ao buscar payment %s: %s", payment_id, exc)
        return {"ok": False}

    ext_ref = payment.get("external_reference") or ""
    if not ext_ref.startswith("sub-"):
        return {"ok": True}
    try:
        sub_id = int(ext_ref.split("-", 1)[1])
    except ValueError:
        return {"ok": True}

    sub = await db.get(Subscription, sub_id)
    if not sub:
        return {"ok": True}

    if payment.get("status") == "approved":
        now = datetime.utcnow()
        sub.status = "ativa"
        sub.paid_at = now
        # Expira após data_prova + 30 dias se existir; senão 1 ano
        concurso = await db.get(Concurso, sub.concurso_id)
        if concurso and concurso.data_prova:
            sub.expira_em = datetime.combine(concurso.data_prova, datetime.min.time()) + timedelta(days=30)
        else:
            sub.expira_em = now + timedelta(days=365)
        sub.payment_external_id = str(payment_id)
        sub.payment_provider = "mercado_pago"
        await db.commit()
        logger.info("subscription %s ativada via MP payment %s", sub_id, payment_id)
    elif payment.get("status") in ("rejected", "cancelled"):
        logger.info("payment %s para sub %s status=%s", payment_id, sub_id, payment.get("status"))
        # Não muda status local; trial ainda pode estar valendo
    return {"ok": True}
