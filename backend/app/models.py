from sqlalchemy import String, Integer, Boolean, Date, DateTime, Float, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase
from datetime import datetime, date
from typing import Optional, List


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    podcast_token: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True, index=True)
    concurso_atual_id: Mapped[Optional[int]] = mapped_column(ForeignKey("concursos.id"), nullable=True)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False)


class Concurso(Base):
    __tablename__ = "concursos"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    nome: Mapped[str] = mapped_column(String(200))
    banca: Mapped[str] = mapped_column(String(50))
    orgao: Mapped[str] = mapped_column(String(120))
    cargo: Mapped[str] = mapped_column(String(120))
    data_prova: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    descricao: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    edital_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    prompt_extra: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    theme_slug: Mapped[str] = mapped_column(String(40), default="audifaz")
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    publico: Mapped[bool] = mapped_column(Boolean, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    phases: Mapped[List["Phase"]] = relationship(back_populates="concurso", order_by="Phase.numero")


class UserConcurso(Base):
    __tablename__ = "user_concursos"
    __table_args__ = (UniqueConstraint("user_id", "concurso_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    concurso_id: Mapped[int] = mapped_column(ForeignKey("concursos.id"), index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Phase(Base):
    __tablename__ = "phases"
    id: Mapped[int] = mapped_column(primary_key=True)
    concurso_id: Mapped[int] = mapped_column(ForeignKey("concursos.id"), index=True)
    numero: Mapped[int]
    nome: Mapped[str] = mapped_column(String(200))
    concurso: Mapped["Concurso"] = relationship(back_populates="phases")
    weeks: Mapped[List["Week"]] = relationship(back_populates="phase", order_by="Week.numero")


class Bloco(Base):
    """Bloco temático (Governança, Segurança, Direito etc.) com peso e meta."""
    __tablename__ = "blocos"
    __table_args__ = (UniqueConstraint("concurso_id", "slug"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    concurso_id: Mapped[int] = mapped_column(ForeignKey("concursos.id"), index=True)
    slug: Mapped[str] = mapped_column(String(60))
    nome: Mapped[str] = mapped_column(String(120))
    peso: Mapped[float] = mapped_column(Float, default=1.0)
    prioridade: Mapped[str] = mapped_column(String(10), default="media")  # alta|media|baixa
    alocacao_pct: Mapped[float] = mapped_column(Float, default=0.0)
    meta_acerto_pct: Mapped[float] = mapped_column(Float, default=70.0)
    ordem: Mapped[int] = mapped_column(default=0)
    keywords: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # csv para heurística


class Week(Base):
    __tablename__ = "weeks"
    id: Mapped[int] = mapped_column(primary_key=True)
    phase_id: Mapped[int] = mapped_column(ForeignKey("phases.id"))
    numero: Mapped[int]
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fim: Mapped[date] = mapped_column(Date)
    tema: Mapped[str] = mapped_column(String(300))
    phase: Mapped["Phase"] = relationship(back_populates="weeks")
    days: Mapped[List["StudyDay"]] = relationship(back_populates="week", order_by="StudyDay.data")


class StudyDay(Base):
    __tablename__ = "study_days"
    id: Mapped[int] = mapped_column(primary_key=True)
    week_id: Mapped[int] = mapped_column(ForeignKey("weeks.id"))
    data: Mapped[date] = mapped_column(Date, index=True)
    tipo: Mapped[str] = mapped_column(String(20), default="util")  # util|sabado|domingo|feriado|prova
    status: Mapped[str] = mapped_column(String(20), default="pendente")  # pendente|em_andamento|concluido
    notas: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    week: Mapped["Week"] = relationship(back_populates="days")
    topics: Mapped[List["Topic"]] = relationship(back_populates="study_day", order_by="Topic.ordem")
    material: Mapped[Optional["StudyMaterial"]] = relationship(back_populates="study_day", uselist=False)


class Topic(Base):
    __tablename__ = "topics"
    id: Mapped[int] = mapped_column(primary_key=True)
    study_day_id: Mapped[int] = mapped_column(ForeignKey("study_days.id"))
    descricao: Mapped[str] = mapped_column(String(1000))
    ordem: Mapped[int] = mapped_column(default=0)
    concluido: Mapped[bool] = mapped_column(Boolean, default=False)
    observacao: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bloco_id: Mapped[Optional[int]] = mapped_column(ForeignKey("blocos.id"), nullable=True, index=True)
    study_day: Mapped["StudyDay"] = relationship(back_populates="topics")


class StudyMaterial(Base):
    __tablename__ = "study_materials"
    id: Mapped[int] = mapped_column(primary_key=True)
    study_day_id: Mapped[int] = mapped_column(ForeignKey("study_days.id"), unique=True)
    gerado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modelo: Mapped[str] = mapped_column(String(50))
    conteudo_md: Mapped[str] = mapped_column(String)
    tokens_in: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    custo_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cache_hit_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    validation_flags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="done")
    error_msg: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    study_day: Mapped["StudyDay"] = relationship(back_populates="material")
    questions: Mapped[List["GeneratedQuestion"]] = relationship(
        back_populates="material", order_by="GeneratedQuestion.ordem"
    )


class GeneratedQuestion(Base):
    __tablename__ = "generated_questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    study_material_id: Mapped[int] = mapped_column(ForeignKey("study_materials.id"))
    enunciado: Mapped[str] = mapped_column(String)
    alternativas: Mapped[dict] = mapped_column(JSON)  # {"A": "...", "B": "...", ...}
    gabarito: Mapped[str] = mapped_column(String(1))
    comentario: Mapped[str] = mapped_column(String)
    disciplina: Mapped[str] = mapped_column(String(100))
    dificuldade: Mapped[str] = mapped_column(String(20), default="medio")
    ordem: Mapped[int] = mapped_column(default=0)
    bloco_id: Mapped[Optional[int]] = mapped_column(ForeignKey("blocos.id"), nullable=True, index=True)
    material: Mapped["StudyMaterial"] = relationship(back_populates="questions")


class UserTopicProgress(Base):
    __tablename__ = "user_topic_progress"
    __table_args__ = (UniqueConstraint("user_id", "topic_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    concluido: Mapped[bool] = mapped_column(Boolean, default=False)
    observacao: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class UserDayProgress(Base):
    __tablename__ = "user_day_progress"
    __table_args__ = (UniqueConstraint("user_id", "study_day_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    study_day_id: Mapped[int] = mapped_column(ForeignKey("study_days.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="pendente")
    notas: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)


class QuestionAttempt(Base):
    __tablename__ = "question_attempts"
    __table_args__ = (UniqueConstraint("question_id", "user_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("generated_questions.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    alternativa_escolhida: Mapped[str] = mapped_column(String(1))
    acertou: Mapped[bool] = mapped_column(Boolean)
    respondido_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    observacao: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class ErrorEntry(Base):
    __tablename__ = "error_entries"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    concurso_id: Mapped[Optional[int]] = mapped_column(ForeignKey("concursos.id"), nullable=True, index=True)
    origem: Mapped[str] = mapped_column(String(10), default="manual")  # gerada|manual
    question_id: Mapped[Optional[int]] = mapped_column(ForeignKey("generated_questions.id"), nullable=True)
    data: Mapped[date] = mapped_column(Date, index=True)
    disciplina: Mapped[str] = mapped_column(String(100), index=True)
    subtopico: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    banca: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    enunciado: Mapped[str] = mapped_column(String)
    gabarito: Mapped[str] = mapped_column(String(1))
    sua_resposta: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)
    justificativa: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    revisado_em: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class MockExam(Base):
    __tablename__ = "mock_exams"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    concurso_id: Mapped[Optional[int]] = mapped_column(ForeignKey("concursos.id"), nullable=True, index=True)
    data: Mapped[date] = mapped_column(Date)
    tipo: Mapped[str] = mapped_column(String(30))  # ti_especifico|conhec_gerais|discursiva|completo
    observacoes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    results: Mapped[List["MockExamResult"]] = relationship(back_populates="exam")


class MockExamResult(Base):
    __tablename__ = "mock_exam_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    mock_exam_id: Mapped[int] = mapped_column(ForeignKey("mock_exams.id"))
    disciplina: Mapped[str] = mapped_column(String(100))
    acertos: Mapped[int]
    total: Mapped[int]
    bloco_id: Mapped[Optional[int]] = mapped_column(ForeignKey("blocos.id"), nullable=True, index=True)
    exam: Mapped["MockExam"] = relationship(back_populates="results")


class BancaExample(Base):
    """Questão real de prova anterior, usada para calibrar estilo da banca."""
    __tablename__ = "banca_examples"
    id: Mapped[int] = mapped_column(primary_key=True)
    banca: Mapped[str] = mapped_column(String(50), index=True)
    fonte: Mapped[str] = mapped_column(String(120))  # ex: "SEFAZ-BA 2019"
    ano: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    disciplina: Mapped[str] = mapped_column(String(100))
    enunciado: Mapped[str] = mapped_column(String)
    alternativas: Mapped[dict] = mapped_column(JSON)
    gabarito: Mapped[str] = mapped_column(String(1))
    comentario: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MaterialAudio(Base):
    __tablename__ = "material_audios"
    id: Mapped[int] = mapped_column(primary_key=True)
    study_material_id: Mapped[int] = mapped_column(ForeignKey("study_materials.id"), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pendente")  # pendente|gerando|done|erro
    arquivo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duracao_seg: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tamanho_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notebooklm_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    instrucoes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    gerado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    concluido_em: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_msg: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tentativas: Mapped[int] = mapped_column(Integer, default=0)
    material: Mapped["StudyMaterial"] = relationship()
