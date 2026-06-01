import { useState, useEffect, useRef, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { format, parseISO, addDays, subDays } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  Sparkles, CheckSquare, Square, ChevronDown, ChevronUp,
  RefreshCw, ChevronLeft, ChevronRight, ShieldAlert, ShieldCheck,
  Flag, X, Send,
} from 'lucide-react'
import * as api from '../api'
import { useAuth } from '../contexts/AuthContext'
import AudioStatus from '../components/AudioStatus'

const MODEL_LABELS = {
  'claude-sonnet-4-6': 'Sonnet 4.6',
  'claude-opus-4-7': 'Opus 4.7',
  'claude-opus-4-8': 'Opus 4.8',
}

const TYPE_LABELS = {
  util:    { label: 'Dia útil', cls: 'text-muted' },
  sabado:  { label: 'Sábado',  cls: 'text-accent-text' },
  domingo: { label: 'Domingo', cls: 'text-accent-text' },
  feriado: { label: 'Feriado', cls: 'text-danger' },
  prova:   { label: 'PROVA',   cls: 'text-danger font-bold' },
}

const STATUS_LABELS = {
  pendente:     'text-subtle',
  em_andamento: 'text-danger',
  concluido:    'text-accent-text',
}

function Pill({ children, cls = '' }) {
  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full text-[11px] font-medium uppercase tracking-wider surface-card ${cls}`}
    >
      {children}
    </span>
  )
}

function Card({ children, className = '' }) {
  return <div className={`surface-card ${className}`}>{children}</div>
}

function SectionLabel({ children }) {
  return <p className="text-[11px] font-medium text-subtle uppercase tracking-widest mb-3">{children}</p>
}

const SEVERITY_LABEL = { alta: 'Alta', media: 'Média', baixa: 'Baixa' }
const SEVERITY_CLS = { alta: 'text-danger', media: 'text-secondary', baixa: 'text-subtle' }

const STATUS_META = {
  ok: {
    bg: 'bg-accent-soft',
    border: 'border-accent-soft',
    text: 'text-accent-text',
    icon: ShieldCheck,
    label: 'Validado por auditor cross-provider — sem inconsistências detectadas',
    severity: 'success',
  },
  warning: {
    bg: 'bg-accent-soft',
    border: 'border-accent-soft',
    text: 'text-secondary',
    icon: ShieldAlert,
    label: 'Possíveis imprecisões de severidade média/baixa — revise antes de fixar',
    severity: 'warning',
  },
  alerta: {
    bg: null,
    border: null,
    text: 'text-danger',
    icon: ShieldAlert,
    label: 'Material regenerado e ainda apresenta inconsistências graves — confirme em fonte oficial',
    severity: 'error',
  },
}

function ValidationBanner({ material }) {
  const [open, setOpen] = useState(false)
  if (!material) return null
  const flags = material.validation_flags
  const status = material.validacao_status || (flags?.length ? 'warning' : 'ok')
  const meta = STATUS_META[status] || STATUS_META.warning
  const Icon = meta.icon
  const altas = (flags || []).filter(f => f.severidade === 'alta').length
  const isError = status === 'alerta'

  const wrapperStyle = isError
    ? { background: 'color-mix(in srgb, var(--color-danger) 12%, transparent)', border: '1px solid color-mix(in srgb, var(--color-danger) 45%, transparent)' }
    : status === 'warning'
      ? { background: 'color-mix(in srgb, var(--color-secondary) 10%, transparent)', border: '0.5px solid color-mix(in srgb, var(--color-secondary) 35%, transparent)' }
      : null

  return (
    <div className={`rounded-btn overflow-hidden ${!wrapperStyle ? 'bg-accent-soft' : ''}`} style={wrapperStyle || {}}>
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between gap-2 px-4 py-2.5 text-left"
      >
        <div className={`flex items-center gap-2 text-[12px] font-medium ${meta.text}`}>
          <Icon size={13} strokeWidth={2} />
          <span>{meta.label}</span>
          {altas > 0 && <span className="text-[11px] text-subtle">({altas} alta{altas > 1 ? 's' : ''})</span>}
          {material.tentativas_geracao > 1 && (
            <span className="text-[10px] font-mono uppercase tracking-wider text-subtle ml-1">
              regenerado {material.tentativas_geracao}×
            </span>
          )}
        </div>
        {flags && flags.length > 0 && (open
          ? <ChevronUp size={12} className="text-subtle" />
          : <ChevronDown size={12} className="text-subtle" />)}
      </button>
      {open && flags && flags.length > 0 && (
        <div className="px-4 pb-3 space-y-2 border-t" style={{ borderColor: 'color-mix(in srgb, var(--color-text) 10%, transparent)' }}>
          {flags.map((f, i) => (
            <div key={i} className="pt-2">
              <div className="flex items-center gap-2 text-[11px] font-mono text-subtle mb-0.5">
                <span>{f.referencia}</span>
                <span>·</span>
                <span className={SEVERITY_CLS[f.severidade]}>{SEVERITY_LABEL[f.severidade]}</span>
              </div>
              <p className="text-[12px] text-muted leading-relaxed">{f.descricao}</p>
            </div>
          ))}
        </div>
      )}
      {material.validador_provider && (
        <div className="px-4 pb-2 text-[10px] font-mono text-subtle">
          auditor: {material.validador_provider}/{material.validador_modelo}
        </div>
      )}
    </div>
  )
}


function ReportButton({ target_type, question_id, material_id, redacao_id, label = 'Reportar erro' }) {
  const [open, setOpen] = useState(false)
  const [categoria, setCategoria] = useState('conteudo')
  const [descricao, setDescricao] = useState('')
  const [busy, setBusy] = useState(false)
  const [sent, setSent] = useState(false)
  const [err, setErr] = useState(null)

  async function submit() {
    setBusy(true); setErr(null)
    try {
      await api.reportContent({ target_type, question_id, material_id, redacao_id, categoria, descricao })
      setSent(true)
      setTimeout(() => { setOpen(false); setSent(false); setDescricao('') }, 1800)
    } catch (e) {
      setErr(e.response?.data?.detail || 'Falha ao enviar')
    } finally {
      setBusy(false)
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-1 text-[11px] text-subtle hover:text-danger transition-colors"
      >
        <Flag size={11} strokeWidth={2} /> {label}
      </button>
    )
  }

  return (
    <div className="mt-3 surface-input rounded-btn p-3 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <span className="text-[11px] font-medium uppercase tracking-widest text-subtle">Reportar problema</span>
        <button onClick={() => setOpen(false)} className="text-subtle hover:text-primary"><X size={13} /></button>
      </div>
      <select
        value={categoria}
        onChange={e => setCategoria(e.target.value)}
        className="surface-input w-full rounded-btn px-2 py-1.5 text-[12px] text-primary focus:outline-none focus:border-accent"
      >
        <option value="conteudo">Conteúdo incorreto</option>
        <option value="questao">Questão com erro</option>
        <option value="gabarito">Gabarito errado</option>
        <option value="redacao">Correção de redação imprecisa</option>
        <option value="outro">Outro</option>
      </select>
      <textarea
        value={descricao}
        onChange={e => setDescricao(e.target.value)}
        rows={3}
        minLength={10}
        placeholder="Descreva o problema com pelo menos 10 caracteres. Inclua a versão correta segundo fonte oficial, se souber."
        className="surface-input w-full rounded-btn px-3 py-2 text-[12px] text-primary placeholder:text-subtle focus:outline-none focus:border-accent"
      />
      <div className="flex items-center justify-between gap-2">
        <button
          onClick={submit}
          disabled={busy || descricao.trim().length < 10}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-btn bg-accent hover:bg-accent-hover disabled:opacity-50 text-[12px] font-semibold"
          style={{ color: 'var(--color-bg)' }}
        >
          {busy ? <RefreshCw size={11} className="animate-spin" /> : <Send size={11} />}
          {sent ? 'Enviado!' : 'Enviar'}
        </button>
        {err && <span className="text-[11px] text-danger">{err}</span>}
      </div>
    </div>
  )
}

function QuestionCard({ q }) {
  const [selected, setSelected] = useState(q.attempt?.alternativa_escolhida || null)
  const [revealed, setRevealed] = useState(!!q.attempt)
  const [loading, setLoading] = useState(false)
  const [showComment, setShowComment] = useState(false)

  const handleAnswer = async (alt) => {
    if (revealed) return
    setSelected(alt)
    setLoading(true)
    try {
      await api.recordAttempt(q.id, alt)
      setRevealed(true)
    } finally {
      setLoading(false)
    }
  }

  const correct = q.gabarito
  const acertou = revealed && selected === correct

  return (
    <Card className="p-4 sm:p-5 space-y-3">
      <div className="flex items-start justify-between gap-2 sm:gap-3">
        <p className="text-[13px] sm:text-[14px] text-primary leading-relaxed flex-1">{q.enunciado}</p>
        <Pill cls={
          q.dificuldade === 'facil' ? 'text-accent-text' :
          q.dificuldade === 'dificil' ? 'text-danger' :
          'text-muted'
        }>
          {q.dificuldade}
        </Pill>
      </div>

      <div className="space-y-1.5">
        {Object.entries(q.alternativas).map(([key, text]) => {
          let cls = 'text-muted hover:bg-accent-soft cursor-pointer surface-input'
          if (revealed) {
            if (key === correct) cls = 'text-accent-text bg-accent-soft'
            else if (key === selected) cls = 'text-danger'
            else cls = 'text-subtle cursor-default surface-input'
          } else if (selected === key) {
            cls = 'text-accent-text bg-accent-soft'
          }
          return (
            <button
              key={key}
              onClick={() => handleAnswer(key)}
              disabled={revealed || loading}
              className={`w-full text-left px-3.5 py-2.5 rounded-btn text-[13px] transition-all ${cls}`}
            >
              <span className="font-mono font-semibold mr-2 text-subtle">{key}.</span>
              {text}
            </button>
          )
        })}
      </div>

      {revealed && (
        <div>
          <button
            onClick={() => setShowComment(!showComment)}
            className={`text-[12px] flex items-center gap-1 font-medium ${acertou ? 'text-accent-text' : 'text-danger'}`}
          >
            {showComment ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            {acertou ? '✓ Correto' : `✗ Gabarito: ${correct}`} — ver comentário
          </button>
          {showComment && (
            <div className="mt-3 text-[12px] text-muted leading-relaxed surface-input rounded-btn p-3">
              {q.comentario}
            </div>
          )}
        </div>
      )}
      <div className="pt-1 flex justify-end">
        <ReportButton target_type="question" question_id={q.id} label="Reportar erro nesta questão" />
      </div>
    </Card>
  )
}

export default function Today() {
  const { isAdmin } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const [day, setDay] = useState(null)
  const [week, setWeek] = useState(null)
  const [material, setMaterial] = useState(null)
  const [questions, setQuestions] = useState([])
  const [generating, setGenerating] = useState(false)
  const [model, setModel] = useState('claude-opus-4-8')
  const [error, setError] = useState(null)
  const [notes, setNotes] = useState('')
  const notesTimer = useRef(null)
  const pollTimer = useRef(null)

  const dateParam = searchParams.get('data')

  const loadDay = useCallback(async (dateStr) => {
    setError(null)
    setDay(null); setWeek(null); setMaterial(null); setQuestions([])
    try {
      const dayRes = dateStr ? await api.getDayByDate(dateStr) : await api.getToday()
      setDay(dayRes.data)
      setNotes(dayRes.data.notas || '')
      const [weekRes, matRes] = await Promise.allSettled([
        api.getWeekContext(dayRes.data.id),
        api.getMaterial(dayRes.data.id),
      ])
      if (weekRes.status === 'fulfilled') setWeek(weekRes.value.data)
      if (matRes.status === 'fulfilled') {
        setMaterial(matRes.value.data)
        setQuestions(matRes.value.data.questions || [])
      }
    } catch {
      setError('Erro ao carregar dia de estudo')
    }
  }, [])

  useEffect(() => { loadDay(dateParam) }, [dateParam, loadDay])

  useEffect(() => {
    if (material?.status !== 'generating') {
      clearInterval(pollTimer.current)
      return
    }
    pollTimer.current = setInterval(async () => {
      try {
        const res = await api.getMaterial(day.id)
        if (res.data.status !== 'generating') {
          setMaterial(res.data)
          setQuestions(res.data.questions || [])
          clearInterval(pollTimer.current)
        }
      } catch { /* ignore transient errors */ }
    }, 4000)
    return () => clearInterval(pollTimer.current)
  }, [material?.status, day?.id])

  function navigate(dateStr) {
    if (dateStr) setSearchParams({ data: dateStr })
    else setSearchParams({})
  }
  function goPrev() { if (day) navigate(format(subDays(parseISO(day.data), 1), 'yyyy-MM-dd')) }
  function goNext() {
    if (!day) return
    const next = addDays(parseISO(day.data), 1)
    const today = format(new Date(), 'yyyy-MM-dd')
    if (format(next, 'yyyy-MM-dd') === today) navigate(null)
    else navigate(format(next, 'yyyy-MM-dd'))
  }

  async function handleToggle(topicId) {
    const res = await api.toggleTopic(topicId)
    setDay(prev => ({
      ...prev,
      topics: prev.topics.map(t => t.id === topicId ? { ...t, concluido: res.data.concluido } : t),
    }))
    const updated = await api.getDay(day.id)
    setDay(updated.data)
  }

  function handleNotesChange(e) {
    const val = e.target.value
    setNotes(val)
    clearTimeout(notesTimer.current)
    notesTimer.current = setTimeout(() => api.updateDayNotes(day.id, val), 800)
  }

  async function handleGenerate() {
    setGenerating(true)
    setError(null); setMaterial(null); setQuestions([])
    try {
      const res = await api.generateMaterial(day.id, model)
      setMaterial(res.data)
      setQuestions(res.data.questions || [])
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Erro ao iniciar geração')
    } finally {
      setGenerating(false)
    }
  }

  if (error && !day) return <p className="text-danger text-sm">{error}</p>
  if (!day) return <p className="text-subtle text-sm animate-pulse">Carregando...</p>

  const dateLabel = format(parseISO(day.data), "EEEE, d 'de' MMMM", { locale: ptBR })
  const yearLabel = format(parseISO(day.data), 'yyyy')
  const typeInfo = TYPE_LABELS[day.tipo] || TYPE_LABELS.util
  const isToday = !dateParam || dateParam === format(new Date(), 'yyyy-MM-dd')

  const correctCount = questions.filter(q => q.attempt?.acertou).length
  const wrongCount = questions.filter(q => q.attempt && !q.attempt.acertou).length
  const pendingCount = questions.filter(q => !q.attempt).length

  return (
    <div className="space-y-5 sm:space-y-6">

      <div className="space-y-3">
        {(day.phase || week?.week) && (
          <div className="flex items-center gap-2 text-[10px] sm:text-[11px] uppercase tracking-widest flex-wrap">
            {day.phase && <span className="text-accent-text font-semibold">FASE {day.phase.numero}</span>}
            {day.phase && <span className="text-subtle">·</span>}
            {day.phase && <span className="text-muted truncate max-w-[60vw]">{day.phase.nome}</span>}
            {week?.week && <span className="text-subtle">·</span>}
            {week?.week && <span className="text-muted">SEM {week.week.numero}</span>}
          </div>
        )}

        <div className="flex items-end justify-between gap-3 flex-wrap">
          <div className="space-y-1 min-w-0 flex-1">
            <h1 className="font-heading text-2xl sm:text-3xl md:text-4xl font-extrabold tracking-tight text-primary capitalize leading-tight">
              {dateLabel}
            </h1>
            <p className="text-[12px] text-subtle font-mono">{yearLabel}</p>
          </div>

          <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
            <button onClick={goPrev} className="surface-input p-2 rounded-btn text-muted hover:text-primary hover:bg-accent-soft transition-all">
              <ChevronLeft size={15} strokeWidth={1.75} />
            </button>
            {!isToday && (
              <button
                onClick={() => navigate(null)}
                className="surface-input text-[12px] px-2.5 sm:px-3 py-2 rounded-btn text-accent-text hover:bg-accent-soft transition-all font-medium"
              >
                Hoje
              </button>
            )}
            <button onClick={goNext} className="surface-input p-2 rounded-btn text-muted hover:text-primary hover:bg-accent-soft transition-all">
              <ChevronRight size={15} strokeWidth={1.75} />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Pill cls={typeInfo.cls}>{typeInfo.label}</Pill>
          <Pill cls={STATUS_LABELS[day.status]}>{day.status.replace('_', ' ')}</Pill>
        </div>
      </div>

      {week?.days && (
        <div className="grid grid-cols-7 gap-1 sm:gap-2">
          {week.days.map(d => {
            const isCurrent = d.data === day.data
            const dayN = format(parseISO(d.data), 'd')
            const dayLabel = format(parseISO(d.data), 'EEE', { locale: ptBR }).slice(0, 3)
            return (
              <button
                key={d.id}
                onClick={() => {
                  const today = format(new Date(), 'yyyy-MM-dd')
                  if (d.data === today) navigate(null)
                  else navigate(d.data)
                }}
                className={`flex flex-col items-center justify-center py-2 sm:py-3 rounded-card transition-all ${
                  isCurrent
                    ? 'bg-accent text-bg'
                    : 'surface-input text-muted hover:text-primary hover:bg-accent-soft'
                }`}
                style={isCurrent ? { color: 'var(--color-bg)' } : {}}
              >
                <span className="text-[9px] sm:text-[10px] uppercase font-medium opacity-70">{dayLabel}</span>
                <span className="text-sm sm:text-base font-bold mt-0.5">{dayN}</span>
                {!isCurrent && d.status === 'concluido' && (
                  <span className="w-1 h-1 rounded-full bg-accent-text mt-1" />
                )}
                {!isCurrent && d.status === 'em_andamento' && (
                  <span className="w-1 h-1 rounded-full bg-danger mt-1" />
                )}
              </button>
            )
          })}
        </div>
      )}

      <div className="grid md:grid-cols-3 gap-4">
        <Card className="p-4 sm:p-5 md:col-span-2">
          <SectionLabel>Tópicos do dia</SectionLabel>
          <div className="space-y-3">
            {day.topics.map(topic => (
              <button key={topic.id} onClick={() => handleToggle(topic.id)} className="w-full flex items-start gap-3 text-left group">
                {topic.concluido ? (
                  <CheckSquare size={16} strokeWidth={1.75} className="text-accent-text shrink-0 mt-0.5" />
                ) : (
                  <Square size={16} strokeWidth={1.75} className="text-subtle group-hover:text-accent-text shrink-0 mt-0.5 transition-colors" />
                )}
                <span className={`text-[14px] leading-relaxed transition-colors ${
                  topic.concluido ? 'line-through text-subtle' : 'text-primary group-hover:text-accent-text'
                }`}>
                  {topic.descricao}
                </span>
              </button>
            ))}
          </div>
        </Card>

        <Card className="p-4 sm:p-5">
          <SectionLabel>Anotações</SectionLabel>
          <textarea
            value={notes}
            onChange={handleNotesChange}
            placeholder="Dúvidas, dificuldades..."
            rows={4}
            className="w-full bg-transparent text-[13px] text-primary placeholder:text-subtle focus:outline-none resize-none"
          />
        </Card>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <h2 className="font-heading text-base sm:text-lg font-bold text-primary tracking-tight">Material de Estudo</h2>
          {isAdmin && (
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <select
                value={model}
                onChange={e => setModel(e.target.value)}
                disabled={generating}
                className="surface-input flex-1 sm:flex-none rounded-btn text-[12px] text-primary px-3 py-2 focus:outline-none focus:border-accent"
              >
                <option value="claude-opus-4-8">Opus 4.8</option>
                <option value="claude-opus-4-7">Opus 4.7</option>
                <option value="claude-sonnet-4-6">Sonnet 4.6</option>
              </select>
              <button
                onClick={handleGenerate}
                disabled={generating || material?.status === 'generating'}
                className="flex items-center gap-2 px-4 py-2 rounded-btn bg-accent hover:bg-accent-hover disabled:opacity-50 text-[13px] font-semibold transition-colors"
                style={{ color: 'var(--color-bg)' }}
              >
                {generating ? <RefreshCw size={13} strokeWidth={2} className="animate-spin" /> : <Sparkles size={13} strokeWidth={2} />}
                {material?.status === 'done' && !generating ? 'Regenerar' : 'Gerar'}
              </button>
            </div>
          )}
        </div>

        {!isAdmin && !material && !generating && (
          <p className="text-[13px] text-muted">Material ainda não disponível para este dia.</p>
        )}

        {error && (
          <div className="rounded-btn px-4 py-3" style={{ background: 'color-mix(in srgb, var(--color-danger) 10%, transparent)', border: '0.5px solid color-mix(in srgb, var(--color-danger) 35%, transparent)' }}>
            <p className="text-danger text-[13px]">{error}</p>
          </div>
        )}

        {(generating || material?.status === 'generating') && (
          <Card className="px-5 py-4">
            <div className="flex items-center gap-3">
              <RefreshCw size={16} className="animate-spin text-danger" />
              <div>
                <p className="text-[13px] font-medium text-primary">Gerando material...</p>
                <p className="text-[11px] text-subtle font-mono">~ 60–90s · pode fechar o app</p>
              </div>
            </div>
          </Card>
        )}

        {material?.status === 'error' && (
          <div className="rounded-btn px-4 py-3" style={{ background: 'color-mix(in srgb, var(--color-danger) 10%, transparent)', border: '0.5px solid color-mix(in srgb, var(--color-danger) 35%, transparent)' }}>
            <p className="text-danger text-[13px]">Erro na geração: {material.error_msg || 'falha desconhecida'}</p>
          </div>
        )}

        {material && material.status === 'done' && !generating && (
          <>
            <AudioStatus dayId={day.id} materialReady={true} />

            {material.custo_usd && (
              <div className="flex items-center gap-3 sm:gap-4 text-[11px] text-subtle font-mono flex-wrap">
                <span className="text-muted">{MODEL_LABELS[material.modelo] || material.modelo}</span>
                <span>·</span>
                <span>{material.tokens_in?.toLocaleString()} in</span>
                <span>{material.tokens_out?.toLocaleString()} out</span>
                <span>${material.custo_usd?.toFixed(4)}</span>
                <span>cache {Math.round((material.cache_hit_ratio || 0) * 100)}%</span>
              </div>
            )}

            <ValidationBanner material={material} />

            <Card className="p-4 sm:p-6 md:p-7">
              <div className="prose-study">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{material.conteudo_md}</ReactMarkdown>
              </div>
              <div className="pt-3 mt-3 flex justify-end" style={{ borderTop: 'var(--surface-border)' }}>
                <ReportButton target_type="material" material_id={material.id} label="Reportar erro no material" />
              </div>
            </Card>

            {questions.length > 0 && (
              <div className="space-y-4 pt-4">
                <div className="flex items-center justify-between flex-wrap gap-3">
                  <h3 className="font-heading text-base font-bold text-primary">Questões FCC <span className="text-subtle font-normal">({questions.length})</span></h3>
                  <div className="flex items-center gap-3 text-[11px] font-mono">
                    <span className="text-accent-text">{correctCount} OK</span>
                    <span className="text-danger">{wrongCount} ERR</span>
                    <span className="text-subtle">{pendingCount} —</span>
                  </div>
                </div>

                {(correctCount + wrongCount) > 0 && (
                  <div className="w-full rounded-full h-1 overflow-hidden bg-accent-soft">
                    <div className="h-full flex">
                      <div className="bg-accent transition-all" style={{ width: `${(correctCount / questions.length) * 100}%` }} />
                      <div className="bg-danger transition-all" style={{ width: `${(wrongCount / questions.length) * 100}%` }} />
                    </div>
                  </div>
                )}

                {questions.map(q => <QuestionCard key={q.id} q={q} />)}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
