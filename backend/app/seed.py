"""Seed inicial do concurso default (SEFAZ-CE) na primeira inicialização.

Delega o parsing para services.plan_importer.
"""
from datetime import date
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Phase, Concurso
from .services.plan_importer import import_plan


def _locate_plano() -> Path | None:
    """Procura plano.md em dev (audifaz/plano.md) ou container (/app/plano.md)."""
    candidates = [
        Path(__file__).parent.parent.parent / "plano.md",
        Path("/app/plano.md"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


async def seed_if_needed(db: AsyncSession):
    # Já tem fase? Não faz nada.
    if (await db.execute(select(Phase))).scalars().first():
        return

    plano_path = _locate_plano()
    if not plano_path:
        return  # sem plano.md no disco, nada a fazer (admin importa via endpoint)

    # Garante concurso default (migrate normalmente já cria)
    concurso = (await db.execute(
        select(Concurso).where(Concurso.slug == "sefaz-ce-2026")
    )).scalar_one_or_none()
    if not concurso:
        concurso = Concurso(
            slug="sefaz-ce-2026",
            nome="SEFAZ-CE 2026 — Auditor Fiscal TI",
            banca="FCC",
            orgao="SEFAZ-CE",
            cargo="B02 Auditor-Fiscal TI",
            data_prova=date(2026, 8, 1),
            descricao="Concurso para Auditor Fiscal de TI da Secretaria da Fazenda do Ceará",
            ativo=True,
            publico=True,
        )
        db.add(concurso)
        await db.flush()

    content = plano_path.read_text(encoding="utf-8")
    await import_plan(db, concurso.id, content)
