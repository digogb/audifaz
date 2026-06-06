"""Regenera o material+questões de um StudyDay específico.

Deleta o material existente (que pode ter ficado com 0 questões) e roda a
geração de novo. Idempotente o suficiente para uso pontual.

Uso (dentro do container app):
    python /tmp/regen_day.py <day_id>
"""
import asyncio
import sys

from sqlalchemy import select, delete

from app.db import AsyncSessionLocal
from app.models import StudyMaterial, GeneratedQuestion
from app.routers.materials import generate_for_day


async def main(day_id: int):
    async with AsyncSessionLocal() as db:
        mat = (await db.execute(
            select(StudyMaterial).where(StudyMaterial.study_day_id == day_id)
        )).scalar_one_or_none()
        if mat:
            await db.execute(
                delete(GeneratedQuestion).where(GeneratedQuestion.study_material_id == mat.id)
            )
            await db.delete(mat)
            await db.commit()
            print(f"[regen] material {mat.id} antigo deletado")
        else:
            print("[regen] nenhum material existente")

    print(f"[regen] gerando para day {day_id}...")
    await generate_for_day(day_id)

    async with AsyncSessionLocal() as db:
        mat = (await db.execute(
            select(StudyMaterial).where(StudyMaterial.study_day_id == day_id)
        )).scalar_one_or_none()
        if not mat:
            print("[regen] ERRO: nenhum material após geração")
            sys.exit(1)
        nq = (await db.execute(
            select(GeneratedQuestion).where(GeneratedQuestion.study_material_id == mat.id)
        )).scalars().all()
        print(f"[regen] novo material {mat.id} status={mat.status} "
              f"validacao={mat.validacao_status} questoes={len(nq)} "
              f"conteudo_chars={len(mat.conteudo_md or '')}")
        if len(nq) == 0:
            print("[regen] ATENÇÃO: ainda 0 questões — investigar tool_choice/stop_reason")
            sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1])))
