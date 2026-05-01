import { useState, useEffect, useRef, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { format, parseISO, addDays, subDays } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  Sparkles, CheckSquare, Square, ChevronDown, ChevronUp,
  RefreshCw, ChevronLeft, ChevronRight,
} from 'lucide-react'
import * as api from '../api'
import { useAuth } from '../contexts/AuthContext'

const glass = {
  background: 'rgba(255,255,255,0.05)',
  border: '0.5px solid rgba(255,255,255,0.10)',
  backdropFilter: 'blur(12px)',
  WebkitBackdropFilter: 'blur(12px)',
}

const TYPE_LABELS = {
  util:    { label: 'Dia útil', cls: 'text-white/60' },
  sabado:  { label: 'Sábado',  cls: 'text-text-blue' },
  domingo: { label: 'Domingo', cls: 'text-text-blue' },
  feriado: { label: 'Feriado', cls: 'text-accent-orange' },
  prova:   { label: 'PROVA',  cls: 'text-accent-orange font-bold' },
}

const STATUS_LABELS = {
  pendente:     'text-white/50',
  em_andamento: 'text-accent-orange',
  concluido:    'text-text-blue',
}

function Pill({ children, cls = '' }) {
  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full text-[11px] font-medium uppercase tracking-wider ${cls}`}
      style={{ background: 'rgba(255,255,255,0.07)', border: '0.5px solid rgba(255,255,255,0.12)' }}
    >
      {children}
    </span>
  )
}

function GlassCard({ children, className = '', style: extraStyle = {} }) {
  return (
    <div
      className={`rounded-container ${className}`}
      style={{ ...glass, ...extraStyle }}
    >
      {children}
    </div>
  )
}

function SectionLabel({ children }) {
  return <p className="text-[11px] font-medium text-white/40 uppercase tracking-widest mb-3">{children}</p>
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
    <GlassCard className="p-5 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <p className="text-[14px] text-white/85 leading-relaxed flex-1">{q.enunciado}</p>
        <Pill cls={
          q.dificuldade === 'facil' ? 'text-text-blue' :
          q.dificuldade === 'dificil' ? 'text-accent-orange' :
          'text-white/60'
        }>
          {q.dificuldade}
        </Pill>
      </div>

      <div className="space-y-1.5">
        {Object.entries(q.alternativas).map(([key, text]) => {
          let cls = 'text-white/75 hover:bg-white/5 cursor-pointer'
          let style = { background: 'rgba(255,255,255,0.03)', border: '0.5px solid rgba(255,255,255,0.10)' }
          if (revealed) {
            if (key === correct) {
              cls = 'text-text-blue'
              style = { background: 'rgba(45,114,217,0.15)', border: '0.5px solid rgba(91,158,244,0.45)' }
            } else if (key === selected) {
              cls = 'text-accent-orange'
              style = { background: 'rgba(212,132,90,0.12)', border: '0.5px solid rgba(212,132,90,0.45)' }
            } else {
              cls = 'text-white/35 cursor-default'
              style = { background: 'rgba(255,255,255,0.02)', border: '0.5px solid rgba(255,255,255,0.06)' }
            }
          } else if (selected === key) {
            cls = 'text-text-blue'
            style = { background: 'rgba(45,114,217,0.10)', border: '0.5px solid rgba(91,158,244,0.35)' }
          }
          return (
            <button
              key={key}
              onClick={() => handleAnswer(key)}
              disabled={revealed || loading}
              className={`w-full text-left px-3.5 py-2.5 rounded-btn text-[13px] transition-all ${cls}`}
              style={style}
            >
              <span className="font-mono font-semibold mr-2 text-white/50">{key}.</span>
              {text}
            </button>
          )
        })}
      </div>

      {revealed && (
        <div>
          <button
            onClick={() => setShowComment(!showComment)}
            className={`text-[12px] flex items-center gap-1 font-medium ${acertou ? 'text-text-blue' : 'text-accent-orange'}`}
          >
            {showComment ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            {acertou ? '✓ Correto' : `✗ Gabarito: ${correct}`} — ver comentário
          </button>
          {showComment && (
            <div
              className="mt-3 text-[12px] text-white/65 leading-relaxed rounded-btn p-3"
              style={{ background: 'rgba(255,255,255,0.03)', border: '0.5px solid rgba(255,255,255,0.08)' }}
            >
              {q.comentario}
            </div>
          )}
        </div>
      )}
    </GlassCard>
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
  const [model, setModel] = useState('claude-sonnet-4-6')
  const [error, setError] = useState(null)
  const [notes, setNotes] = useState('')
  const notesTimer = useRef(null)

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
      setError(e.response?.data?.detail || e.message || 'Erro ao gerar material')
    } finally {
      setGenerating(false)
    }
  }

  if (error && !day) return <p className="text-accent-orange text-sm">{error}</p>
  if (!day) return <p className="text-white/40 text-sm animate-pulse">Carregando...</p>

  const dateLabel = format(parseISO(day.data), "EEEE, d 'de' MMMM", { locale: ptBR })
  const yearLabel = format(parseISO(day.data), 'yyyy')
  const typeInfo = TYPE_LABELS[day.tipo] || TYPE_LABELS.util
  const isToday = !dateParam || dateParam === format(new Date(), 'yyyy-MM-dd')

  const correctCount = questions.filter(q => q.attempt?.acertou).length
  const wrongCount = questions.filter(q => q.attempt && !q.attempt.acertou).length
  const pendingCount = questions.filter(q => !q.attempt).length

  return (
    <div className="space-y-6">

      {/* Hero header */}
      <div className="space-y-3">
        {(day.phase || week?.week) && (
          <div className="flex items-center gap-2 text-[11px] uppercase tracking-widest">
            {day.phase && <span className="text-text-blue font-semibold">FASE {day.phase.numero}</span>}
            {day.phase && <span className="text-white/30">·</span>}
            {day.phase && <span className="text-white/55">{day.phase.nome}</span>}
            {week?.week && <span className="text-white/30">·</span>}
            {week?.week && <span className="text-white/55">SEM {week.week.numero}</span>}
          </div>
        )}

        <div className="flex items-end justify-between gap-4 flex-wrap">
          <div className="space-y-1">
            <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white capitalize leading-none">
              {dateLabel}
            </h1>
            <p className="text-[12px] text-white/40 font-mono">{yearLabel}</p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={goPrev}
              className="p-2 rounded-btn text-white/60 hover:text-white hover:bg-white/5 transition-all"
              style={{ border: '0.5px solid rgba(255,255,255,0.10)' }}
            >
              <ChevronLeft size={15} strokeWidth={1.75} />
            </button>
            {!isToday && (
              <button
                onClick={() => navigate(null)}
                className="text-[12px] px-3 py-2 rounded-btn text-text-blue hover:bg-text-blue/10 transition-all font-medium"
                style={{ border: '0.5px solid rgba(91,158,244,0.30)' }}
              >
                Hoje
              </button>
            )}
            <button
              onClick={goNext}
              className="p-2 rounded-btn text-white/60 hover:text-white hover:bg-white/5 transition-all"
              style={{ border: '0.5px solid rgba(255,255,255,0.10)' }}
            >
              <ChevronRight size={15} strokeWidth={1.75} />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Pill cls={typeInfo.cls}>{typeInfo.label}</Pill>
          <Pill cls={STATUS_LABELS[day.status]}>{day.status.replace('_', ' ')}</Pill>
        </div>
      </div>

      {/* Week mini-calendar */}
      {week?.days && (
        <div className="grid grid-cols-7 gap-2">
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
                className={`flex flex-col items-center justify-center py-3 rounded-card transition-all ${
                  isCurrent ? 'bg-accent-blue text-white' : 'text-white/60 hover:text-white hover:bg-white/5'
                }`}
                style={!isCurrent ? { background: 'rgba(255,255,255,0.03)', border: '0.5px solid rgba(255,255,255,0.08)' } : {}}
              >
                <span className="text-[10px] uppercase font-medium opacity-70">{dayLabel}</span>
                <span className="text-base font-bold mt-0.5">{dayN}</span>
                {!isCurrent && d.status === 'concluido' && (
                  <span className="w-1 h-1 rounded-full bg-text-blue mt-1" />
                )}
                {!isCurrent && d.status === 'em_andamento' && (
                  <span className="w-1 h-1 rounded-full bg-accent-orange mt-1" />
                )}
              </button>
            )
          })}
        </div>
      )}

      {/* Topics + Notes */}
      <div className="grid md:grid-cols-3 gap-4">
        <GlassCard className="p-5 md:col-span-2">
          <SectionLabel>Tópicos do dia</SectionLabel>
          <div className="space-y-3">
            {day.topics.map(topic => (
              <button
                key={topic.id}
                onClick={() => handleToggle(topic.id)}
                className="w-full flex items-start gap-3 text-left group"
              >
                {topic.concluido ? (
                  <CheckSquare size={16} strokeWidth={1.75} className="text-text-blue shrink-0 mt-0.5" />
                ) : (
                  <Square size={16} strokeWidth={1.75} className="text-white/30 group-hover:text-text-blue shrink-0 mt-0.5 transition-colors" />
                )}
                <span className={`text-[14px] leading-relaxed transition-colors ${
                  topic.concluido ? 'line-through text-white/35' : 'text-white/85 group-hover:text-white'
                }`}>
                  {topic.descricao}
                </span>
              </button>
            ))}
          </div>
        </GlassCard>

        <GlassCard className="p-5">
          <SectionLabel>Anotações</SectionLabel>
          <textarea
            value={notes}
            onChange={handleNotesChange}
            placeholder="Dúvidas, dificuldades..."
            rows={5}
            className="w-full bg-transparent text-[13px] text-white/85 placeholder-white/30 focus:outline-none resize-none"
          />
        </GlassCard>
      </div>

      {/* Generate Material */}
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <h2 className="text-lg font-bold text-white tracking-tight">Material de Estudo</h2>
          {isAdmin && (
            <div className="flex items-center gap-2">
              <select
                value={model}
                onChange={e => setModel(e.target.value)}
                disabled={generating}
                className="rounded-btn text-[12px] text-white/80 px-3 py-2 focus:outline-none focus:border-accent-blue"
                style={{ background: 'rgba(255,255,255,0.04)', border: '0.5px solid rgba(255,255,255,0.12)' }}
              >
                <option value="claude-sonnet-4-6" className="bg-bg-base">Sonnet 4.6</option>
                <option value="claude-opus-4-7" className="bg-bg-base">Opus 4.7</option>
              </select>
              <button
                onClick={handleGenerate}
                disabled={generating}
                className="flex items-center gap-2 px-4 py-2 rounded-btn bg-accent-blue hover:bg-accent-blue/90 disabled:opacity-50 disabled:cursor-not-allowed text-white text-[13px] font-semibold transition-colors"
              >
                {generating ? <RefreshCw size={13} strokeWidth={2} className="animate-spin" /> : <Sparkles size={13} strokeWidth={2} />}
                {material && !generating ? 'Regenerar' : 'Gerar'}
              </button>
            </div>
          )}
        </div>

        {!isAdmin && !material && !generating && (
          <p className="text-[13px] text-white/50">Material ainda não disponível para este dia.</p>
        )}

        {error && (
          <div className="rounded-btn px-4 py-3" style={{ background: 'rgba(212,132,90,0.10)', border: '0.5px solid rgba(212,132,90,0.35)' }}>
            <p className="text-accent-orange text-[13px]">{error}</p>
          </div>
        )}

        {generating && (
          <GlassCard className="px-5 py-4">
            <div className="flex items-center gap-3">
              <RefreshCw size={16} className="animate-spin text-accent-orange" />
              <div>
                <p className="text-[13px] font-medium text-white">Gerando material...</p>
                <p className="text-[11px] text-white/40 font-mono">~ 60s</p>
              </div>
            </div>
          </GlassCard>
        )}

        {material && !generating && (
          <>
            {material.custo_usd && (
              <div className="flex items-center gap-4 text-[11px] text-white/40 font-mono">
                <span>{material.tokens_in?.toLocaleString()} in</span>
                <span>{material.tokens_out?.toLocaleString()} out</span>
                <span>${material.custo_usd?.toFixed(4)}</span>
                <span>cache {Math.round((material.cache_hit_ratio || 0) * 100)}%</span>
              </div>
            )}

            <GlassCard className="p-7">
              <div className="prose-study">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{material.conteudo_md}</ReactMarkdown>
              </div>
            </GlassCard>

            {questions.length > 0 && (
              <div className="space-y-4 pt-4">
                <div className="flex items-center justify-between flex-wrap gap-3">
                  <h3 className="text-base font-bold text-white">Questões FCC <span className="text-white/40 font-normal">({questions.length})</span></h3>
                  <div className="flex items-center gap-3 text-[11px] font-mono">
                    <span className="text-text-blue">{correctCount} OK</span>
                    <span className="text-accent-orange">{wrongCount} ERR</span>
                    <span className="text-white/40">{pendingCount} —</span>
                  </div>
                </div>

                {(correctCount + wrongCount) > 0 && (
                  <div className="w-full rounded-full h-1 overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                    <div className="h-full flex">
                      <div className="bg-text-blue transition-all" style={{ width: `${(correctCount / questions.length) * 100}%` }} />
                      <div className="bg-accent-orange transition-all" style={{ width: `${(wrongCount / questions.length) * 100}%` }} />
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
