"""Cliente fino para Mercado Pago Pix.

Doc: https://www.mercadopago.com.br/developers/pt/reference/payments/_payments/post

Em sandbox usa a mesma API; só muda o access token (TEST-...).
"""
import logging
import os
import secrets
from typing import Any

import httpx

logger = logging.getLogger(__name__)

MP_BASE = "https://api.mercadopago.com"
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN", "")
MP_WEBHOOK_SECRET = os.environ.get("MP_WEBHOOK_SECRET", "")  # opcional, usado se MP enviar 'x-signature'
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")


class MercadoPagoError(RuntimeError):
    """Erro retornado pela API do MP."""


def _check_configured() -> None:
    if not MP_ACCESS_TOKEN:
        raise MercadoPagoError("MP_ACCESS_TOKEN não configurado")


async def create_pix_payment(
    *,
    amount_cents: int,
    description: str,
    payer_email: str,
    subscription_id: int,
) -> dict[str, Any]:
    """Cria pagamento Pix no MP. Retorna o objeto do payment (com qr_code, ticket_url etc)."""
    _check_configured()
    amount = round(amount_cents / 100.0, 2)
    notification_url = f"{PUBLIC_BASE_URL}/api/billing/mp/webhook" if PUBLIC_BASE_URL else None
    body = {
        "transaction_amount": amount,
        "description": description,
        "payment_method_id": "pix",
        "payer": {"email": payer_email},
        "external_reference": f"sub-{subscription_id}",
        "metadata": {"subscription_id": subscription_id},
    }
    if notification_url:
        body["notification_url"] = notification_url

    headers = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
        "X-Idempotency-Key": secrets.token_hex(16),
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(f"{MP_BASE}/v1/payments", json=body, headers=headers)
    if resp.status_code >= 400:
        logger.error("mp create_pix falhou: %s %s", resp.status_code, resp.text[:400])
        raise MercadoPagoError(f"MP {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    poi = (data.get("point_of_interaction") or {}).get("transaction_data") or {}
    return {
        "id": data["id"],
        "status": data["status"],
        "qr_code": poi.get("qr_code"),
        "qr_code_base64": poi.get("qr_code_base64"),
        "ticket_url": poi.get("ticket_url"),
        "raw": data,
    }


async def fetch_payment(payment_id: str) -> dict[str, Any]:
    """Consulta o status de um pagamento já criado (usado pelo webhook handler)."""
    _check_configured()
    headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{MP_BASE}/v1/payments/{payment_id}", headers=headers)
    if resp.status_code >= 400:
        raise MercadoPagoError(f"MP {resp.status_code}: {resp.text[:200]}")
    return resp.json()
