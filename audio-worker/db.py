"""Modelos mínimos pro worker — só MaterialAudio e StudyMaterial (read).

Mantemos schemas paralelos pra não criar dependência circular com o backend.
Se mudar o modelo no backend, atualize aqui também.
"""
import os
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


DATABASE_URL = os.environ.get(
    "DATABASE_URL", "sqlite+aiosqlite:////data/audifaz.db"
)

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class StudyMaterial(Base):
    __tablename__ = "study_materials"
    id: Mapped[int] = mapped_column(primary_key=True)
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
