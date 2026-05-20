from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional, List


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    token: str
    username: str


class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    descricao: str
    ordem: int
    concluido: bool
    observacao: Optional[str] = None


class WeekOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    numero: int
    tema: str
    data_inicio: date
    data_fim: date


class PhaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    numero: int
    nome: str


class StudyDayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    data: date
    tipo: str
    status: str = "pendente"
    notas: Optional[str] = None
    topics: List[TopicOut] = []
    week: Optional[WeekOut] = None


class StudyDayWithPhase(StudyDayOut):
    phase: Optional[PhaseOut] = None


class QuestionAttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    alternativa_escolhida: str
    acertou: bool
    respondido_em: datetime
    observacao: Optional[str] = None


class GeneratedQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    enunciado: str
    alternativas: dict
    gabarito: str
    comentario: str
    disciplina: str
    dificuldade: str
    ordem: int
    attempt: Optional[QuestionAttemptOut] = None


class StudyMaterialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    gerado_em: datetime
    modelo: str
    conteudo_md: str
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    custo_usd: Optional[float] = None
    cache_hit_ratio: Optional[float] = None
    validation_flags: Optional[list] = None
    status: str = "done"
    error_msg: Optional[str] = None
    # Cross-provider validation pipeline
    tentativas_geracao: int = 1
    validador_provider: Optional[str] = None
    validador_modelo: Optional[str] = None
    validacao_status: str = "pendente"  # pendente|ok|warning|alerta
    regenerado_em: Optional[datetime] = None
    questions: List[GeneratedQuestionOut] = []


class ErrorEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    origem: str
    question_id: Optional[int] = None
    data: date
    disciplina: str
    subtopico: Optional[str] = None
    banca: Optional[str] = None
    enunciado: str
    gabarito: str
    sua_resposta: Optional[str] = None
    justificativa: Optional[str] = None
    revisado_em: Optional[datetime] = None


class ErrorEntryCreate(BaseModel):
    data: date
    disciplina: str
    subtopico: Optional[str] = None
    banca: Optional[str] = None
    enunciado: str
    gabarito: str
    sua_resposta: Optional[str] = None
    justificativa: Optional[str] = None


class MockExamResultIn(BaseModel):
    disciplina: str
    acertos: int
    total: int


class MockExamResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    disciplina: str
    acertos: int
    total: int


class MockExamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    data: date
    tipo: str
    observacoes: Optional[str] = None
    results: List[MockExamResultOut] = []


class MockExamCreate(BaseModel):
    data: date
    tipo: str
    observacoes: Optional[str] = None
    results: List[MockExamResultIn] = []


class AttemptCreate(BaseModel):
    alternativa_escolhida: str
    observacao: Optional[str] = None


class ProgressDay(BaseModel):
    data: date
    status: str
    tipo: str
    topics_total: int
    topics_done: int


class PhaseProgress(BaseModel):
    numero: int
    nome: str
    total_days: int
    done_days: int
    pct: float


class MaterialAudioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    arquivo_url: Optional[str] = None
    duracao_seg: Optional[int] = None
    tamanho_bytes: Optional[int] = None
    gerado_em: datetime
    concluido_em: Optional[datetime] = None
    error_msg: Optional[str] = None
    tentativas: int = 0


class PodcastTokenOut(BaseModel):
    token: str
    feed_url: str


class ConcursoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    nome: str
    banca: str
    orgao: str
    cargo: str
    data_prova: Optional[date] = None
    descricao: Optional[str] = None
    edital_url: Optional[str] = None
    theme_slug: str = "audifaz"
    brand: str = "audifaz"
    requer_assinatura: bool = False
    preco_cents: Optional[int] = None
    ativo: bool
    atual: bool = False
