import { useState, useEffect } from 'react'
import { format, parseISO } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { AlertTriangle, CheckCircle, Trash2, ChevronDown, ChevronUp, Plus, X, RotateCcw } from 'lucide-react'
import * as api from '../api'

function ErrorCard({ error, onReview, onDelete, onAnswered }) {
  const [expanded, setExpanded] = useState(false)
  const [answering, setAnswering] = useState(false)
  const [selected, setSelected] = useState(null)
  const [revealed, setRevealed] = useState(false)
  const [loading, setLoading] = useState(false)
  const [answerErr, setAnswerErr] = useState(null)
  // gabarito/comentário só chegam do backend após a nova tentativa
  // (ou já vêm no payload quando o erro está revisado / é manual)
  const [gabarito, setGabarito] = useState(error.gabarito ?? null)
  const [comentario, setComentario] = useState(error.justificativa ?? null)
  const [acertou, setAcertou] = useState(null)

  const reviewed = !!error.revisado_em
  const reanswerable = !!error.alternativas

  const handleAnswer = async (alt) => {
    if (revealed || loading) return
    setSelected(alt)
    setLoading(true)
    setAnswerErr(null)
    try {
      const res = await api.answerError(error.id, alt)
      setGabarito(res.data.gabarito ?? null)
      setComentario(res.data.comentario ?? null)
      setAcertou(res.data.acertou)
      setRevealed(true)
      onAnswered(error.id, res.data)
    } catch (e) {
      setSelected(null)
      setAnswerErr(e.response?.data?.detail || 'Erro ao registrar resposta. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={`surface-card p-4 space-y-3 transition-opacity ${reviewed && !revealed ? 'opacity-50' : ''}`}>
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <span className="text-[11px] font-bold text-accent-text uppercase tracking-wider">{error.disciplina}</span>
            {error.subtopico && <span className="text-[11px] text-muted">{error.subtopico}</span>}
            {error.banca && (
              <span className="text-[10px] px-2 py-0.5 rounded-full text-accent-text font-medium uppercase tracking-wider bg-accent-soft border border-accent/30">
                {error.banca}
              </span>
            )}
            <span className="text-[11px] text-subtle font-mono">{format(parseISO(error.data), 'dd/MM/yy', { locale: ptBR })}</span>
            {reviewed && <span className="text-[11px] text-accent-text font-medium">✓ revisado</span>}
            {error.sua_resposta && (
              <span className="text-[11px] text-danger font-mono">
                {gabarito ? `${error.sua_resposta} → ${gabarito}` : `marcou ${error.sua_resposta}`}
              </span>
            )}
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-[14px] text-primary/90 text-left hover:text-primary transition-colors leading-relaxed"
          >
            {error.enunciado.length > 150 && !expanded && !answering
              ? error.enunciado.slice(0, 150) + '...'
              : error.enunciado}
          </button>
        </div>
        <div className="flex gap-1 shrink-0">
          {!reviewed && !reanswerable && (
            <button
              onClick={() => onReview(error.id)}
              className="p-1.5 rounded-btn text-subtle hover:text-accent-text hover:bg-accent-soft transition-colors"
              title="Marcar como revisado"
            >
              <CheckCircle size={14} strokeWidth={1.75} />
            </button>
          )}
          <button
            onClick={() => onDelete(error.id)}
            className="p-1.5 rounded-btn text-subtle hover:text-danger hover:bg-danger/10 transition-colors"
            title="Deletar"
          >
            <Trash2 size={14} strokeWidth={1.75} />
          </button>
        </div>
      </div>

      {/* Revisão ativa: responder a questão de novo (só sai da fila acertando) */}
      {reanswerable && !reviewed && !answering && (
        <button
          onClick={() => { setAnswering(true); setExpanded(true) }}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-btn bg-accent hover:bg-accent-hover text-white text-[12px] font-semibold transition-colors"
        >
          <RotateCcw size={12} strokeWidth={2} /> Responder de novo
        </button>
      )}

      {reanswerable && (answering || (reviewed && expanded)) && (
        <div className="space-y-1.5">
          {['A', 'B', 'C', 'D', 'E'].filter(k => k in error.alternativas).map((key) => {
            const done = revealed || reviewed
            let cls = 'text-muted hover:bg-accent-soft cursor-pointer surface-input'
            if (done) {
              if (key === gabarito) cls = 'text-accent-text bg-accent-soft'
              else if (key === selected) cls = 'text-danger surface-input'
              else cls = 'text-subtle cursor-default surface-input'
            } else if (selected === key) {
              cls = 'text-accent-text bg-accent-soft'
            }
            return (
              <button
                key={key}
                onClick={() => handleAnswer(key)}
                disabled={done || loading || reviewed}
                className={`w-full text-left px-3.5 py-2.5 rounded-btn text-[13px] transition-all ${cls}`}
              >
                <span className="font-mono font-semibold mr-2 text-subtle">{key}.</span>
                {error.alternativas[key]}
              </button>
            )
          })}
          {answerErr && <p className="text-[12px] text-danger">{answerErr}</p>}
          {revealed && (
            <p className={`text-[12px] font-medium pt-1 ${acertou ? 'text-success' : 'text-danger'}`}>
              {acertou
                ? '✓ Correto — erro marcado como revisado'
                : `✗ Gabarito: ${gabarito} — a questão continua na fila de revisão`}
            </p>
          )}
        </div>
      )}

      {expanded && comentario && (revealed || reviewed || !reanswerable) && (
        <div className="surface-input rounded-btn p-3 text-[12px] text-muted leading-relaxed">
          <span className="font-semibold text-accent-text">Comentário · </span>
          {comentario}
        </div>
      )}

      {(error.enunciado.length > 150 || (reanswerable && reviewed)) && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-[11px] text-subtle hover:text-accent-text flex items-center gap-1 transition-colors"
        >
          {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          {expanded ? 'Mostrar menos' : 'Mostrar mais'}
        </button>
      )}
    </div>
  )
}

const inputCls = 'w-full rounded-btn px-3 py-2 text-[13px] text-primary placeholder-subtle surface-input focus:outline-none focus:border-accent transition-colors'

function ManualErrorModal({ onClose, onSave }) {
  const [form, setForm] = useState({
    data: new Date().toISOString().split('T')[0],
    disciplina: '', subtopico: '', banca: 'FCC', enunciado: '',
    gabarito: 'A', sua_resposta: '', justificativa: '',
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    await onSave(form)
    onClose()
  }

  const Field = ({ label, children }) => (
    <div>
      <label className="block text-[11px] text-muted font-medium uppercase tracking-wider mb-1.5">{label}</label>
      {children}
    </div>
  )

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-start sm:items-center justify-center p-3 sm:p-4 overflow-y-auto">
      <div className="surface-menu w-full max-w-lg my-4 p-5 sm:p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-bold text-primary text-base">Registrar Erro Manual</h2>
          <button onClick={onClose} className="text-muted hover:text-primary p-1 rounded-btn hover:bg-accent-soft transition-colors">
            <X size={18} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Data">
              <input type="date" value={form.data} onChange={e => setForm(p => ({ ...p, data: e.target.value }))} className={inputCls} />
            </Field>
            <Field label="Banca">
              <input value={form.banca} onChange={e => setForm(p => ({ ...p, banca: e.target.value }))} className={inputCls} />
            </Field>
          </div>
          <Field label="Disciplina *">
            <input required value={form.disciplina} onChange={e => setForm(p => ({ ...p, disciplina: e.target.value }))} placeholder="ex: COBIT 2019" className={inputCls} />
          </Field>
          <Field label="Subtópico">
            <input value={form.subtopico} onChange={e => setForm(p => ({ ...p, subtopico: e.target.value }))} className={inputCls} />
          </Field>
          <Field label="Enunciado *">
            <textarea required value={form.enunciado} onChange={e => setForm(p => ({ ...p, enunciado: e.target.value }))} rows={3} className={`${inputCls} resize-none`} />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Gabarito *">
              <select required value={form.gabarito} onChange={e => setForm(p => ({ ...p, gabarito: e.target.value }))} className={inputCls}>
                {['A', 'B', 'C', 'D', 'E'].map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            </Field>
            <Field label="Sua resposta">
              <select value={form.sua_resposta} onChange={e => setForm(p => ({ ...p, sua_resposta: e.target.value }))} className={inputCls}>
                <option value="">—</option>
                {['A', 'B', 'C', 'D', 'E'].map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            </Field>
          </div>
          <Field label="Por que errei">
            <textarea value={form.justificativa} onChange={e => setForm(p => ({ ...p, justificativa: e.target.value }))} rows={2} className={`${inputCls} resize-none`} />
          </Field>
          <div className="flex gap-2 pt-1">
            <button type="button" onClick={onClose}
              className="flex-1 py-2 rounded-btn surface-input text-muted hover:text-primary text-[13px] font-medium transition-colors">
              Cancelar
            </button>
            <button type="submit"
              className="flex-1 py-2 rounded-btn bg-accent hover:bg-accent-hover text-white text-[13px] font-semibold transition-colors">
              Salvar
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function Errors() {
  const [errors, setErrors] = useState([])
  const [disciplines, setDisciplines] = useState([])
  const [staleCount, setStaleCount] = useState(0)
  const [filters, setFilters] = useState({ disciplina: '', revisado: '', dias: '' })
  const [showModal, setShowModal] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadData() }, [filters])

  async function loadData() {
    setLoading(true)
    try {
      const params = {}
      if (filters.disciplina) params.disciplina = filters.disciplina
      if (filters.revisado !== '') params.revisado = filters.revisado === 'nao' ? false : filters.revisado === 'sim' ? true : undefined
      if (filters.dias) params.dias = parseInt(filters.dias)
      const [errRes, discRes, staleRes] = await Promise.all([
        api.getErrors(params), api.getDisciplines(), api.getStaleCount(),
      ])
      setErrors(errRes.data); setDisciplines(discRes.data); setStaleCount(staleRes.data.count)
    } finally { setLoading(false) }
  }

  async function handleReview(id) { await api.markErrorReviewed(id); loadData() }
  async function handleDelete(id) { if (!confirm('Deletar este erro?')) return; await api.deleteError(id); loadData() }
  async function handleSave(data) { await api.createError(data); loadData() }

  // Atualiza o card in-place após re-resposta (sem reload, pra não perder o
  // feedback visual); o stale count é recarregado à parte.
  function handleAnswered(id, res) {
    setErrors(prev => prev.map(e => e.id === id
      ? {
          ...e,
          gabarito: res.gabarito,
          justificativa: res.comentario,
          revisado_em: res.acertou ? new Date().toISOString() : e.revisado_em,
        }
      : e
    ))
    api.getStaleCount().then(r => setStaleCount(r.data.count)).catch(() => {})
  }

  const selectCls = 'rounded-btn text-[12px] text-primary surface-input px-3 py-2 focus:outline-none focus:border-accent'

  return (
    <div className="space-y-5 sm:space-y-6">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h1 className="text-xl sm:text-2xl font-extrabold text-primary tracking-tight">Caderno de Erros</h1>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1.5 px-3 sm:px-4 py-2 bg-accent hover:bg-accent-hover rounded-btn text-white text-[13px] font-semibold transition-colors"
        >
          <Plus size={13} strokeWidth={2} /> <span className="hidden sm:inline">Erro Manual</span><span className="sm:hidden">Novo</span>
        </button>
      </div>

      {staleCount > 0 && (
        <div
          className="flex items-center gap-3 rounded-container px-4 py-3"
          style={{
            background: 'color-mix(in srgb, var(--color-danger) 8%, transparent)',
            border: '0.5px solid color-mix(in srgb, var(--color-danger) 30%, transparent)',
          }}
        >
          <AlertTriangle size={16} className="text-danger shrink-0" strokeWidth={1.75} />
          <p className="text-[13px] text-danger font-medium">
            {staleCount} erro{staleCount > 1 ? 's' : ''} não revisado{staleCount > 1 ? 's' : ''} há mais de 7 dias
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 sm:flex gap-2 sm:flex-wrap items-stretch sm:items-center">
        <select value={filters.disciplina} onChange={e => setFilters(p => ({ ...p, disciplina: e.target.value }))} className={selectCls + ' w-full sm:w-auto'}>
          <option value="">Todas as disciplinas</option>
          {disciplines.map(d => <option key={d} value={d}>{d}</option>)}
        </select>
        <div className="grid grid-cols-2 sm:flex gap-2">
          <select value={filters.revisado} onChange={e => setFilters(p => ({ ...p, revisado: e.target.value }))} className={selectCls + ' w-full sm:w-auto'}>
            <option value="">Todos</option>
            <option value="nao">Não revisados</option>
            <option value="sim">Revisados</option>
          </select>
          <select value={filters.dias} onChange={e => setFilters(p => ({ ...p, dias: e.target.value }))} className={selectCls + ' w-full sm:w-auto'}>
            <option value="">Todo período</option>
            <option value="7">Últimos 7 dias</option>
            <option value="30">Últimos 30 dias</option>
          </select>
        </div>
        <span className="text-[12px] text-subtle font-mono sm:self-center">{errors.length} erros</span>
      </div>

      {loading ? (
        <p className="text-subtle text-sm animate-pulse">Carregando...</p>
      ) : errors.length === 0 ? (
        <div className="text-center py-16">
          <AlertTriangle size={32} className="mx-auto mb-3 text-subtle/50" strokeWidth={1.5} />
          <p className="text-[13px] text-muted">Nenhum erro encontrado</p>
        </div>
      ) : (
        <div className="space-y-3">
          {errors.map(e => (
            <ErrorCard key={e.id} error={e} onReview={handleReview} onDelete={handleDelete} onAnswered={handleAnswered} />
          ))}
        </div>
      )}

      {showModal && <ManualErrorModal onClose={() => setShowModal(false)} onSave={handleSave} />}
    </div>
  )
}
