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

const TYPE_LABELS = {
  util:    { label: 'Dia útil',  cls: 'bg-gray-100 text-text-muted' },
  sabado:  { label: 'Sábado',   cls: 'bg-blue-50 text-blue-600' },
  domingo: { label: 'Domingo',  cls: 'bg-purple-50 text-purple-600' },
  feriado: { label: 'Feriado',  cls: 'bg-amber-50 text-tangerine' },
  prova:   { label: '🎯 PROVA', cls: 'bg-red-50 text-coral font-bold' },
}

const STATUS_LABELS = {
  pendente:     'bg-gray-100 text-text-muted',
  em_andamento: 'bg-amber-50 text-tangerine',
  concluido:    'bg-green-50 text-sage',
}

function Badge({ children, cls }) {
  return <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${cls}`}>{children}</span>
}

function Card({ children, accent, className = '' }) {
  return (
    <div
      className={`bg-white rounded-card shadow-card border-l-4 ${accent ?? 'border-l-surface-border'} ${className}`}
    >
      {children}
    </div>
  )
}

function SectionLabel({ children }) {
  return (
    <p className="text-xs font-semibold text-text-muted uppercase tracking-widest mb-3">{children}</p>
  )
}

function QuestionCard({ q, onAttempt }) {
  const [selected, setSelected] = useState(q.attempt?.alternativa_escolhida || null)
  const [revealed, setRevealed] = useState(!!q.attempt)
  const [loading, setLoading] = useState(false)
  const [showComment, setShowComment] = useState(false)

  const handleAnswer = async (alt) => {
    if (revealed) return
    setSelected(alt)
    setLoading(true)
    try {
      const res = await api.recordAttempt(q.id, alt)
      setRevealed(true)
      onAttempt?.(q.id, res.data.acertou)
    } finally {
      setLoading(false)
    }
  }

  const correct = q.gabarito
  const acertou = revealed && selected === correct

  const cardBorder = revealed
    ? acertou ? 'border-l-sage' : 'border-l-coral'
    : 'border-l-surface-border'

  return (
    <div className={`bg-white rounded-card shadow-card border-l-4 ${cardBorder} p-4 space-y-3`}>
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm text-text-main leading-relaxed flex-1">{q.enunciado}</p>
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ${
          q.dificuldade === 'facil' ? 'bg-green-50 text-sage' :
          q.dificuldade === 'dificil' ? 'bg-red-50 text-coral' :
          'bg-amber-50 text-tangerine'
        }`}>{q.dificuldade}</span>
      </div>

      <div className="space-y-1.5">
        {Object.entries(q.alternativas).map(([key, text]) => {
          let cls = 'border-surface-border text-text-main hover:bg-surface-bg hover:border-brand/30 cursor-pointer'
          if (revealed) {
            if (key === correct) cls = 'border-sage bg-green-50 text-sage'
            else if (key === selected) cls = 'border-coral bg-red-50 text-coral'
            else cls = 'border-surface-border text-text-faint cursor-default'
          } else if (selected === key) {
            cls = 'border-brand bg-brand-light text-brand'
          }
          return (
            <button
              key={key}
              onClick={() => handleAnswer(key)}
              disabled={revealed || loading}
              className={`w-full text-left px-3 py-2 rounded-xl border text-sm transition-all ${cls}`}
            >
              <span className="font-mono font-bold mr-2">{key}.</span>
              {text}
            </button>
          )
        })}
      </div>

      {revealed && (
        <div>
          <button
            onClick={() => setShowComment(!showComment)}
            className={`text-xs flex items-center gap-1 font-medium ${acertou ? 'text-sage' : 'text-coral'}`}
          >
            {showComment ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            {acertou ? '✓ Correto' : `✗ Gabarito: ${correct}`} — ver comentário
          </button>
          {showComment && (
            <p className="mt-2 text-xs text-text-muted leading-relaxed bg-surface-bg rounded-xl p-3 border border-surface-border">
              {q.comentario}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export default function Today() {
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
    setDay(null)
    setWeek(null)
    setMaterial(null)
    setQuestions([])
    try {
      const dayRes = dateStr
        ? await api.getDayByDate(dateStr)
        : await api.getToday()
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

  function goPrev() {
    if (!day) return
    navigate(format(subDays(parseISO(day.data), 1), 'yyyy-MM-dd'))
  }

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
    setError(null)
    setMaterial(null)
    setQuestions([])
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

  if (error && !day) return <p className="text-coral text-sm">{error}</p>
  if (!day) return <p className="text-text-faint text-sm animate-pulse">Carregando...</p>

  const dateLabel = format(parseISO(day.data), "EEEE, d 'de' MMMM 'de' yyyy", { locale: ptBR })
  const typeInfo = TYPE_LABELS[day.tipo] || TYPE_LABELS.util
  const isToday = !dateParam || dateParam === format(new Date(), 'yyyy-MM-dd')

  const correctCount = questions.filter(q => q.attempt?.acertou).length
  const wrongCount = questions.filter(q => q.attempt && !q.attempt.acertou).length
  const pendingCount = questions.filter(q => !q.attempt).length

  return (
    <div className="space-y-5">

      {/* Date header */}
      <div className="space-y-2">
        {(day.phase || week?.week) && (
          <div className="flex items-center gap-2">
            {day.phase && (
              <span className="text-xs font-semibold text-text-faint uppercase tracking-widest">
                Fase {day.phase.numero} · {day.phase.nome}
              </span>
            )}
            {week?.week && (
              <>
                <span className="text-text-faint text-xs">·</span>
                <span className="text-xs text-text-faint">
                  Sem {week.week.numero} · {week.week.tema}
                </span>
              </>
            )}
          </div>
        )}
        <div className="flex items-center gap-2 flex-wrap">
          <button onClick={goPrev} className="p-1 rounded-lg hover:bg-surface-bg text-text-muted hover:text-text-main transition-colors">
            <ChevronLeft size={18} />
          </button>
          <button onClick={goNext} className="p-1 rounded-lg hover:bg-surface-bg text-text-muted hover:text-text-main transition-colors">
            <ChevronRight size={18} />
          </button>
          <h1 className="text-xl font-bold text-text-main capitalize flex-1">{dateLabel}</h1>
          {!isToday && (
            <button onClick={() => navigate(null)} className="text-xs text-brand hover:text-brand-dark font-medium transition-colors">
              Ir para hoje
            </button>
          )}
          <Badge cls={typeInfo.cls}>{typeInfo.label}</Badge>
          <Badge cls={STATUS_LABELS[day.status]}>{day.status}</Badge>
        </div>
      </div>

      {/* Week mini-calendar */}
      {week?.days && (
        <div className="flex gap-1.5">
          {week.days.map(d => (
            <button
              key={d.id}
              onClick={() => {
                const today = format(new Date(), 'yyyy-MM-dd')
                if (d.data === today) navigate(null)
                else navigate(d.data)
              }}
              className={`flex-1 rounded-xl py-1.5 text-center text-xs font-medium transition-all ${
                d.data === day.data
                  ? 'bg-brand text-white shadow-sm'
                  : d.status === 'concluido'
                  ? 'bg-green-50 text-sage hover:bg-green-100'
                  : d.status === 'em_andamento'
                  ? 'bg-amber-50 text-tangerine hover:bg-amber-100'
                  : 'bg-white text-text-faint hover:bg-surface-bg border border-surface-border'
              }`}
            >
              {format(parseISO(d.data), 'EEE', { locale: ptBR }).slice(0, 3)}
            </button>
          ))}
        </div>
      )}

      {/* Topics */}
      <Card accent="border-l-brand" className="p-5">
        <SectionLabel>Tópicos do dia</SectionLabel>
        <div className="space-y-2.5">
          {day.topics.map(topic => (
            <button
              key={topic.id}
              onClick={() => handleToggle(topic.id)}
              className="w-full flex items-start gap-3 text-left group"
            >
              {topic.concluido ? (
                <CheckSquare size={17} className="text-sage shrink-0 mt-0.5" />
              ) : (
                <Square size={17} className="text-text-faint group-hover:text-brand shrink-0 mt-0.5 transition-colors" />
              )}
              <span className={`text-sm leading-relaxed transition-colors ${
                topic.concluido ? 'line-through text-text-faint' : 'text-text-main group-hover:text-brand'
              }`}>
                {topic.descricao}
              </span>
            </button>
          ))}
        </div>
      </Card>

      {/* Notes */}
      <div>
        <label className="block text-xs text-text-muted mb-1.5 font-semibold uppercase tracking-widest">Anotações do dia</label>
        <textarea
          value={notes}
          onChange={handleNotesChange}
          placeholder="Dificuldades, dúvidas, observações..."
          rows={3}
          className="w-full bg-white border border-surface-border rounded-card px-4 py-3 text-sm text-text-main placeholder-text-faint focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/10 resize-none shadow-card transition-all"
        />
      </div>

      {/* Generate Material */}
      <div className="space-y-4">
        <div className="flex items-center gap-3 flex-wrap">
          <h2 className="text-base font-bold text-text-main flex-1">Material de Estudo</h2>
          <div className="flex items-center gap-2">
            <select
              value={model}
              onChange={e => setModel(e.target.value)}
              disabled={generating}
              className="bg-white border border-surface-border rounded-xl text-xs text-text-main px-3 py-2 focus:outline-none focus:border-brand shadow-sm"
            >
              <option value="claude-sonnet-4-6">Sonnet 4.6</option>
              <option value="claude-opus-4-7">Opus 4.7 (melhor)</option>
            </select>
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-brand hover:bg-brand-dark disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold transition-colors shadow-sm"
            >
              {generating ? <RefreshCw size={14} className="animate-spin" /> : <Sparkles size={14} />}
              {material && !generating ? 'Regenerar' : 'Gerar Material'}
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3">
            <p className="text-coral text-sm">{error}</p>
          </div>
        )}

        {generating && (
          <Card accent="border-l-tangerine" className="px-5 py-4">
            <div className="flex items-center gap-3">
              <RefreshCw size={16} className="animate-spin text-tangerine" />
              <div>
                <p className="text-sm font-medium text-text-main">Gerando material...</p>
                <p className="text-xs text-text-muted">Isso pode levar até 1 minuto</p>
              </div>
            </div>
          </Card>
        )}

        {material && !generating && (
          <>
            {material.custo_usd && (
              <p className="text-xs text-text-faint">
                {material.tokens_in?.toLocaleString()} entrada · {material.tokens_out?.toLocaleString()} saída ·{' '}
                ${material.custo_usd?.toFixed(4)} · cache {Math.round((material.cache_hit_ratio || 0) * 100)}%
              </p>
            )}

            <Card accent="border-l-brand" className="p-6">
              <div className="prose-study">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{material.conteudo_md}</ReactMarkdown>
              </div>
            </Card>

            {questions.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-text-main">Questões FCC ({questions.length})</h3>
                  <div className="flex items-center gap-3 text-xs font-medium">
                    <span className="text-sage">{correctCount} corretas</span>
                    <span className="text-coral">{wrongCount} erradas</span>
                    <span className="text-text-faint">{pendingCount} pendentes</span>
                  </div>
                </div>

                {/* Score bar */}
                {questions.length > 0 && (correctCount + wrongCount) > 0 && (
                  <div className="w-full bg-surface-bg rounded-full h-1.5 overflow-hidden">
                    <div className="h-full flex">
                      <div className="bg-sage transition-all" style={{ width: `${(correctCount / questions.length) * 100}%` }} />
                      <div className="bg-coral transition-all" style={{ width: `${(wrongCount / questions.length) * 100}%` }} />
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
