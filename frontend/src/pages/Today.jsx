import { useState, useEffect, useRef, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { format, parseISO, addDays, subDays } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  Sparkles, CheckSquare, Square, ChevronDown, ChevronUp,
  RefreshCw, CheckCircle2, ChevronLeft, ChevronRight,
} from 'lucide-react'
import * as api from '../api'

const TYPE_LABELS = {
  util: { label: 'Dia útil', cls: 'bg-slate-700 text-slate-300' },
  sabado: { label: 'Sábado', cls: 'bg-blue-900 text-blue-300' },
  domingo: { label: 'Domingo', cls: 'bg-purple-900 text-purple-300' },
  feriado: { label: 'Feriado', cls: 'bg-amber-900 text-amber-300' },
  prova: { label: '🎯 PROVA', cls: 'bg-rose-900 text-rose-300 font-bold' },
}

const STATUS_LABELS = {
  pendente: 'bg-slate-700 text-slate-400',
  em_andamento: 'bg-amber-900 text-amber-300',
  concluido: 'bg-emerald-900 text-emerald-300',
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

  return (
    <div className={`rounded-lg border p-4 space-y-3 ${revealed ? (acertou ? 'border-emerald-700/50' : 'border-rose-700/50') : 'border-slate-800'}`}>
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm text-slate-200 leading-relaxed flex-1">{q.enunciado}</p>
        <span className="text-xs text-slate-500 shrink-0">{q.dificuldade}</span>
      </div>

      <div className="space-y-1.5">
        {Object.entries(q.alternativas).map(([key, text]) => {
          let cls = 'border-slate-700 text-slate-300 hover:bg-slate-800 cursor-pointer'
          if (revealed) {
            if (key === correct) cls = 'border-emerald-600 bg-emerald-900/30 text-emerald-200'
            else if (key === selected) cls = 'border-rose-600 bg-rose-900/30 text-rose-300'
            else cls = 'border-slate-800 text-slate-500 cursor-default'
          } else if (selected === key) {
            cls = 'border-indigo-500 bg-indigo-900/20 text-indigo-200'
          }
          return (
            <button
              key={key}
              onClick={() => handleAnswer(key)}
              disabled={revealed || loading}
              className={`w-full text-left px-3 py-2 rounded border text-sm transition-colors ${cls}`}
            >
              <span className="font-mono font-semibold mr-2">{key}.</span>
              {text}
            </button>
          )
        })}
      </div>

      {revealed && (
        <div>
          <button
            onClick={() => setShowComment(!showComment)}
            className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1"
          >
            {showComment ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            {acertou ? '✓ Correto' : `✗ Gabarito: ${correct}`} — ver comentário
          </button>
          {showComment && (
            <p className="mt-2 text-xs text-slate-400 leading-relaxed bg-slate-800/50 rounded p-3">
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
    } catch (e) {
      setError('Erro ao carregar dia de estudo')
    }
  }, [])

  useEffect(() => {
    loadDay(dateParam)
  }, [dateParam, loadDay])

  function navigate(dateStr) {
    if (dateStr) {
      setSearchParams({ data: dateStr })
    } else {
      setSearchParams({})
    }
  }

  function goPrev() {
    if (!day) return
    const prev = subDays(parseISO(day.data), 1)
    navigate(format(prev, 'yyyy-MM-dd'))
  }

  function goNext() {
    if (!day) return
    const next = addDays(parseISO(day.data), 1)
    const today = format(new Date(), 'yyyy-MM-dd')
    if (format(next, 'yyyy-MM-dd') === today) {
      navigate(null)
    } else {
      navigate(format(next, 'yyyy-MM-dd'))
    }
  }

  async function handleToggle(topicId) {
    const res = await api.toggleTopic(topicId)
    setDay(prev => ({
      ...prev,
      topics: prev.topics.map(t =>
        t.id === topicId ? { ...t, concluido: res.data.concluido } : t
      ),
    }))
    const updated = await api.getDay(day.id)
    setDay(updated.data)
  }

  function handleNotesChange(e) {
    const val = e.target.value
    setNotes(val)
    clearTimeout(notesTimer.current)
    notesTimer.current = setTimeout(() => {
      api.updateDayNotes(day.id, val)
    }, 800)
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

  if (error && !day) {
    return <div className="text-rose-400 text-sm">{error}</div>
  }

  if (!day) {
    return <div className="text-slate-500 text-sm animate-pulse">Carregando...</div>
  }

  const dateLabel = format(parseISO(day.data), "EEEE, d 'de' MMMM 'de' yyyy", { locale: ptBR })
  const typeInfo = TYPE_LABELS[day.tipo] || TYPE_LABELS.util
  const isToday = !dateParam || dateParam === format(new Date(), 'yyyy-MM-dd')

  return (
    <div className="space-y-6">
      {/* Header with navigation */}
      <div className="space-y-1">
        {day.phase && (
          <p className="text-xs text-slate-500 uppercase tracking-wider">
            Fase {day.phase.numero} · {day.phase.nome}
          </p>
        )}
        {week?.week && (
          <p className="text-xs text-slate-500">
            Semana {week.week.numero} · {week.week.tema}
          </p>
        )}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-1">
            <button
              onClick={goPrev}
              className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
              title="Dia anterior"
            >
              <ChevronLeft size={18} />
            </button>
            <button
              onClick={goNext}
              className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
              title="Próximo dia"
            >
              <ChevronRight size={18} />
            </button>
          </div>
          <h1 className="text-xl font-semibold text-slate-100 capitalize flex-1">{dateLabel}</h1>
          {!isToday && (
            <button
              onClick={() => navigate(null)}
              className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              Ir para hoje
            </button>
          )}
          <span className={`text-xs px-2 py-0.5 rounded-full ${typeInfo.cls}`}>{typeInfo.label}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_LABELS[day.status]}`}>
            {day.status}
          </span>
        </div>
      </div>

      {/* Week mini-calendar — clickable */}
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
              className={`flex-1 rounded py-1 text-center text-xs transition-colors ${
                d.data === day.data
                  ? 'bg-indigo-600 text-white font-bold'
                  : d.status === 'concluido'
                  ? 'bg-emerald-900/50 text-emerald-400 hover:bg-emerald-900'
                  : d.status === 'em_andamento'
                  ? 'bg-amber-900/50 text-amber-400 hover:bg-amber-900'
                  : 'bg-slate-800 text-slate-500 hover:bg-slate-700'
              }`}
            >
              {format(parseISO(d.data), 'EEE', { locale: ptBR }).slice(0, 3)}
            </button>
          ))}
        </div>
      )}

      {/* Topics */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-4 space-y-3">
        <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider">Tópicos do dia</h2>
        {day.topics.map(topic => (
          <button
            key={topic.id}
            onClick={() => handleToggle(topic.id)}
            className="w-full flex items-start gap-3 text-left group"
          >
            {topic.concluido ? (
              <CheckSquare size={18} className="text-emerald-400 shrink-0 mt-0.5" />
            ) : (
              <Square size={18} className="text-slate-600 group-hover:text-slate-400 shrink-0 mt-0.5" />
            )}
            <span className={`text-sm leading-relaxed ${topic.concluido ? 'line-through text-slate-500' : 'text-slate-200'}`}>
              {topic.descricao}
            </span>
          </button>
        ))}
      </div>

      {/* Notes */}
      <div>
        <label className="block text-xs text-slate-500 mb-1.5 uppercase tracking-wider">Anotações do dia</label>
        <textarea
          value={notes}
          onChange={handleNotesChange}
          placeholder="Dificuldades, dúvidas, observações..."
          rows={3}
          className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-600 resize-none"
        />
      </div>

      {/* Generate Material */}
      <div className="border-t border-slate-800 pt-6 space-y-4">
        <div className="flex items-center gap-3 flex-wrap">
          <h2 className="text-sm font-semibold text-slate-300 flex-1">Material de Estudo</h2>
          <div className="flex items-center gap-2">
            <select
              value={model}
              onChange={e => setModel(e.target.value)}
              disabled={generating}
              className="bg-slate-800 border border-slate-700 rounded-md text-xs text-slate-300 px-2 py-1.5 focus:outline-none focus:border-indigo-600"
            >
              <option value="claude-sonnet-4-6">Sonnet 4.6</option>
              <option value="claude-opus-4-7">Opus 4.7 (melhor)</option>
            </select>
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition-colors"
            >
              {generating ? (
                <RefreshCw size={14} className="animate-spin" />
              ) : (
                <Sparkles size={14} />
              )}
              {material && !generating ? 'Regenerar' : 'Gerar Material'}
            </button>
          </div>
        </div>

        {error && <p className="text-rose-400 text-sm">{error}</p>}

        {generating && (
          <div className="flex items-center gap-2 text-xs text-amber-500">
            <RefreshCw size={11} className="animate-spin" />
            Gerando material... isso pode levar até 1 minuto
          </div>
        )}

        {material && !generating && (
          <>
            {material.custo_usd && (
              <p className="text-xs text-slate-600">
                {material.tokens_in?.toLocaleString()} tokens entrada ·{' '}
                {material.tokens_out?.toLocaleString()} saída ·{' '}
                ${material.custo_usd?.toFixed(4)} ·{' '}
                cache {Math.round((material.cache_hit_ratio || 0) * 100)}%
              </p>
            )}

            <div className="bg-slate-900 rounded-xl border border-slate-800 p-5">
              <div className="prose-study">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{material.conteudo_md}</ReactMarkdown>
              </div>
            </div>

            {questions.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-medium text-slate-300">Questões FCC ({questions.length})</h3>
                  <span className="text-xs text-slate-600">
                    {questions.filter(q => q.attempt?.acertou).length} corretas ·{' '}
                    {questions.filter(q => q.attempt && !q.attempt.acertou).length} erradas ·{' '}
                    {questions.filter(q => !q.attempt).length} não respondidas
                  </span>
                </div>
                {questions.map(q => (
                  <QuestionCard key={q.id} q={q} />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
