import { useState, useEffect } from 'react'
import { format, parseISO } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { AlertTriangle, CheckCircle, Trash2, ChevronDown, ChevronUp, Plus, X } from 'lucide-react'
import * as api from '../api'

function ErrorCard({ error, onReview, onDelete }) {
  const [expanded, setExpanded] = useState(false)
  const reviewed = !!error.revisado_em

  return (
    <div className={`bg-white rounded-card shadow-card border-l-4 p-4 space-y-3 transition-opacity ${
      reviewed ? 'border-l-surface-border opacity-60' : 'border-l-coral'
    }`}>
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1.5">
            <span className="text-xs font-bold text-brand">{error.disciplina}</span>
            {error.subtopico && <span className="text-xs text-text-muted">{error.subtopico}</span>}
            {error.banca && (
              <span className="text-xs bg-brand-light text-brand px-2 py-0.5 rounded-full font-medium">{error.banca}</span>
            )}
            <span className="text-xs text-text-faint">{format(parseISO(error.data), 'dd/MM/yy', { locale: ptBR })}</span>
            {reviewed && <span className="text-xs text-sage font-medium">✓ revisado</span>}
            {error.sua_resposta && (
              <span className="text-xs text-coral font-medium">
                Você: {error.sua_resposta} · Gabarito: {error.gabarito}
              </span>
            )}
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-sm text-text-main text-left hover:text-brand transition-colors"
          >
            {error.enunciado.length > 150 && !expanded
              ? error.enunciado.slice(0, 150) + '...'
              : error.enunciado}
          </button>
        </div>
        <div className="flex gap-1 shrink-0">
          {!reviewed && (
            <button
              onClick={() => onReview(error.id)}
              className="p-1.5 rounded-lg hover:bg-green-50 text-text-faint hover:text-sage transition-colors"
              title="Marcar como revisado"
            >
              <CheckCircle size={15} />
            </button>
          )}
          <button
            onClick={() => onDelete(error.id)}
            className="p-1.5 rounded-lg hover:bg-red-50 text-text-faint hover:text-coral transition-colors"
            title="Deletar"
          >
            <Trash2 size={15} />
          </button>
        </div>
      </div>

      {expanded && error.justificativa && (
        <div className="bg-surface-bg border border-surface-border rounded-xl p-3 text-xs text-text-muted leading-relaxed">
          <span className="font-semibold text-text-main">Comentário: </span>
          {error.justificativa}
        </div>
      )}

      {error.enunciado.length > 150 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-text-faint hover:text-brand flex items-center gap-1 transition-colors"
        >
          {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          {expanded ? 'Mostrar menos' : 'Mostrar mais'}
        </button>
      )}
    </div>
  )
}

function inputCls() {
  return 'w-full bg-surface-bg border border-surface-border rounded-xl px-3 py-2 text-sm text-text-main placeholder-text-faint focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/10 transition-all'
}

function ManualErrorModal({ onClose, onSave }) {
  const [form, setForm] = useState({
    data: new Date().toISOString().split('T')[0],
    disciplina: '',
    subtopico: '',
    banca: 'FCC',
    enunciado: '',
    gabarito: 'A',
    sua_resposta: '',
    justificativa: '',
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    await onSave(form)
    onClose()
  }

  const field = (label, children) => (
    <div>
      <label className="block text-xs text-text-muted font-semibold uppercase tracking-wider mb-1.5">{label}</label>
      {children}
    </div>
  )

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-card shadow-card-hover w-full max-w-lg p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-bold text-text-main">Registrar Erro Manual</h2>
          <button onClick={onClose} className="text-text-faint hover:text-text-main p-1 rounded-lg hover:bg-surface-bg transition-colors">
            <X size={18} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            {field('Data', <input type="date" value={form.data} onChange={e => setForm(p => ({ ...p, data: e.target.value }))} className={inputCls()} />)}
            {field('Banca', <input value={form.banca} onChange={e => setForm(p => ({ ...p, banca: e.target.value }))} className={inputCls()} />)}
          </div>
          {field('Disciplina *', <input required value={form.disciplina} onChange={e => setForm(p => ({ ...p, disciplina: e.target.value }))} placeholder="ex: COBIT 2019, ISO 27001" className={inputCls()} />)}
          {field('Subtópico', <input value={form.subtopico} onChange={e => setForm(p => ({ ...p, subtopico: e.target.value }))} className={inputCls()} />)}
          {field('Enunciado *', <textarea required value={form.enunciado} onChange={e => setForm(p => ({ ...p, enunciado: e.target.value }))} rows={3} className={`${inputCls()} resize-none`} />)}
          <div className="grid grid-cols-2 gap-3">
            {field('Gabarito *',
              <select required value={form.gabarito} onChange={e => setForm(p => ({ ...p, gabarito: e.target.value }))} className={inputCls()}>
                {['A', 'B', 'C', 'D', 'E'].map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            )}
            {field('Sua resposta',
              <select value={form.sua_resposta} onChange={e => setForm(p => ({ ...p, sua_resposta: e.target.value }))} className={inputCls()}>
                <option value="">—</option>
                {['A', 'B', 'C', 'D', 'E'].map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            )}
          </div>
          {field('Por que errei', <textarea value={form.justificativa} onChange={e => setForm(p => ({ ...p, justificativa: e.target.value }))} rows={2} className={`${inputCls()} resize-none`} />)}
          <div className="flex gap-2 pt-1">
            <button type="button" onClick={onClose}
              className="flex-1 py-2 rounded-xl border border-surface-border text-text-muted hover:text-text-main hover:border-text-muted text-sm font-medium transition-colors">
              Cancelar
            </button>
            <button type="submit"
              className="flex-1 py-2 rounded-xl bg-brand hover:bg-brand-dark text-white text-sm font-semibold transition-colors shadow-sm">
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
        api.getErrors(params),
        api.getDisciplines(),
        api.getStaleCount(),
      ])
      setErrors(errRes.data)
      setDisciplines(discRes.data)
      setStaleCount(staleRes.data.count)
    } finally {
      setLoading(false)
    }
  }

  async function handleReview(id) { await api.markErrorReviewed(id); loadData() }
  async function handleDelete(id) { if (!confirm('Deletar este erro?')) return; await api.deleteError(id); loadData() }
  async function handleSave(data) { await api.createError(data); loadData() }

  const selectCls = 'bg-white border border-surface-border rounded-xl text-sm text-text-main px-3 py-2 focus:outline-none focus:border-brand shadow-sm'

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-text-main">Caderno de Erros</h1>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1.5 px-4 py-2 bg-brand hover:bg-brand-dark rounded-xl text-white text-sm font-semibold shadow-sm transition-colors"
        >
          <Plus size={14} /> Erro Manual
        </button>
      </div>

      {staleCount > 0 && (
        <div className="flex items-center gap-3 bg-amber-50 border border-amber-200 rounded-card px-4 py-3">
          <AlertTriangle size={16} className="text-tangerine shrink-0" />
          <p className="text-sm text-tangerine font-medium">
            {staleCount} erro{staleCount > 1 ? 's' : ''} não revisado{staleCount > 1 ? 's' : ''} há mais de 7 dias
          </p>
        </div>
      )}

      <div className="flex gap-2 flex-wrap items-center">
        <select value={filters.disciplina} onChange={e => setFilters(p => ({ ...p, disciplina: e.target.value }))} className={selectCls}>
          <option value="">Todas as disciplinas</option>
          {disciplines.map(d => <option key={d} value={d}>{d}</option>)}
        </select>
        <select value={filters.revisado} onChange={e => setFilters(p => ({ ...p, revisado: e.target.value }))} className={selectCls}>
          <option value="">Todos</option>
          <option value="nao">Não revisados</option>
          <option value="sim">Revisados</option>
        </select>
        <select value={filters.dias} onChange={e => setFilters(p => ({ ...p, dias: e.target.value }))} className={selectCls}>
          <option value="">Todo período</option>
          <option value="7">Últimos 7 dias</option>
          <option value="30">Últimos 30 dias</option>
        </select>
        <span className="text-sm text-text-muted">{errors.length} erros</span>
      </div>

      {loading ? (
        <p className="text-text-faint text-sm animate-pulse">Carregando...</p>
      ) : errors.length === 0 ? (
        <div className="text-center py-16">
          <AlertTriangle size={32} className="mx-auto mb-3 text-text-faint" />
          <p className="text-sm text-text-muted">Nenhum erro encontrado</p>
        </div>
      ) : (
        <div className="space-y-3">
          {errors.map(e => (
            <ErrorCard key={e.id} error={e} onReview={handleReview} onDelete={handleDelete} />
          ))}
        </div>
      )}

      {showModal && <ManualErrorModal onClose={() => setShowModal(false)} onSave={handleSave} />}
    </div>
  )
}
