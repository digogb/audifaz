"""Modelos mínimos pro worker — apenas o necessário pra ler material + concurso.

Mantemos schemas paralelos pra não criar dependência circular com o backend.
Se mudar o modelo no backend, atualize aqui também.
"""
import os
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


DATABASE_URL = os.environ.get(
    "DATABASE_URL", "sqlite+aiosqlite:////data/audifaz.db"
)

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Concurso(Base):
    __tablename__ = "concursos"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80))
    nome: Mapped[str] = mapped_column(String(200))
    banca: Mapped[str] = mapped_column(String(50))
    orgao: Mapped[str] = mapped_column(String(120))
    cargo: Mapped[str] = mapped_column(String(120))
    data_prova: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    prompt_extra: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class Phase(Base):
    __tablename__ = "phases"
    id: Mapped[int] = mapped_column(primary_key=True)
    concurso_id: Mapped[int] = mapped_column(ForeignKey("concursos.id"))


class Week(Base):
    __tablename__ = "weeks"
    id: Mapped[int] = mapped_column(primary_key=True)
    phase_id: Mapped[int] = mapped_column(ForeignKey("phases.id"))


class StudyDay(Base):
    __tablename__ = "study_days"
    id: Mapped[int] = mapped_column(primary_key=True)
    week_id: Mapped[int] = mapped_column(ForeignKey("weeks.id"))


class StudyMaterial(Base):
    __tablename__ = "study_materials"
    id: Mapped[int] = mapped_column(primary_key=True)
    study_day_id: Mapped[int] = mapped_column(ForeignKey("study_days.id"))
    conteudo_md: Mapped[str] = mapped_column(String)


class MaterialAudio(Base):
    __tablename__ = "material_audios"
    id: Mapped[int] = mapped_column(primary_key=True)
    study_material_id: Mapped[int] = mapped_column(ForeignKey("study_materials.id"))
    status: Mapped[str] = mapped_column(String(20))
    arquivo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duracao_seg: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tamanho_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notebooklm_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    instrucoes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    gerado_em: Mapped[datetime] = mapped_column(DateTime)
    concluido_em: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_msg: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tentativas: Mapped[int] = mapped_column(Integer)
    material: Mapped["StudyMaterial"] = relationship()


async def get_concurso_for_material(db: AsyncSession, material_id: int) -> Optional[Concurso]:
    """Resolve o Concurso responsável por um StudyMaterial via Day → Week → Phase."""
    from sqlalchemy import select
    result = await db.execute(
        select(Concurso)
        .join(Phase, Phase.concurso_id == Concurso.id)
        .join(Week, Week.phase_id == Phase.id)
        .join(StudyDay, StudyDay.week_id == Week.id)
        .join(StudyMaterial, StudyMaterial.study_day_id == StudyDay.id)
        .where(StudyMaterial.id == material_id)
    )
    return result.scalar_one_or_none()
