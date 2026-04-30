import { useState, useEffect } from 'react'
import { format, parseISO } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { AlertTriangle, CheckCircle, Trash2, ChevronDown, ChevronUp, Plus, X } from 'lucide-react'
import * as api from '../api'

function ErrorCard({ error, onReview, onDelete }) {
  const [expanded, setExpanded] = useState(false)
  const reviewed = !!error.revisado_em

  return (
    <div className={`bg-slate-900 rounded-xl border p-4 space-y-3 ${reviewed ? 'border-slate-800 opacity-60' : 'border-slate-700'}`}>
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="text-xs font-medium text-indigo-300">{error.disciplina}</span>
            {error.subtopico && <span className="text-xs text-slate-500">{error.subtopico}</span>}
            {error.banca && (
              <span className="text-xs bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded">{error.banca}</span>
            )}
            <span className="text-xs text-slate-600">{format(parseISO(error.data), 'dd/MM/yy', { locale: ptBR })}</span>
            {reviewed && <span className="text-xs text-emerald-600">✓ revisado</span>}
            {error.sua_resposta && (
              <span className="text-xs text-rose-400">
                Você: {error.sua_resposta} · Gabarito: {error.gabarito}
              </span>
            )}
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-sm text-slate-200 text-left hover:text-white"
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
              className="p-1.5 rounded hover:bg-emerald-900/40 text-emerald-600 hover:text-emerald-400 transition-colors"
              title="Marcar como revisado"
            >
              <CheckCircle size={15} />
            </button>
          )}
          <button
            onClick={() => onDelete(error.id)}
            className="p-1.5 rounded hover:bg-rose-900/40 text-slate-600 hover:text-rose-400 transition-colors"
            title="Deletar"
          >
            <Trash2 size={15} />
          </button>
        </div>
      </div>

      {expanded && error.justificativa && (
        <div className="bg-slate-800/50 rounded-lg p-3 text-xs text-slate-400 leading-relaxed">
          <span className="font-medium text-slate-300">Comentário: </span>
          {error.justificativa}
        </div>
      )}

      {error.enunciado.length > 150 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-slate-500 hover:text-slate-300 flex items-center gap-1"
        >
          {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          {expanded ? 'Mostrar menos' : 'Mostrar mais'}
        </button>
      )}
    </div>
  )
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

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 rounded-2xl border border-slate-700 w-full max-w-lg p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-slate-200">Registrar Erro Manual</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300">
            <X size={18} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-slate-500 block mb-1">Data</label>
              <input type="date" value={form.data} onChange={e => setForm(p => ({ ...p, data: e.target.value }))}
                className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-600" />
            </div>
            <div>
              <label className="text-xs text-slate-500 block mb-1">Banca</label>
              <input value={form.banca} onChange={e => setForm(p => ({ ...p, banca: e.target.value }))}
                className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-600" />
            </div>
          </div>
          <div>
            <label className="text-xs text-slate-500 block mb-1">Disciplina *</label>
            <input required value={form.disciplina} onChange={e => setForm(p => ({ ...p, disciplina: e.target.value }))}
              placeholder="ex: COBIT 2019, ISO 27001, Direito Tributário"
              className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-600" />
          </div>
          <div>
            <label className="text-xs text-slate-500 block mb-1">Subtópico</label>
            <input value={form.subtopico} onChange={e => setForm(p => ({ ...p, subtopico: e.target.value }))}
              className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-600" />
          </div>
          <div>
            <label className="text-xs text-slate-500 block mb-1">Enunciado *</label>
            <textarea required value={form.enunciado} onChange={e => setForm(p => ({ ...p, enunciado: e.target.value }))}
              rows={3}
              className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-600 resize-none" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-slate-500 block mb-1">Gabarito *</label>
              <select required value={form.gabarito} onChange={e => setForm(p => ({ ...p, gabarito: e.target.value }))}
                className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-600">
                {['A', 'B', 'C', 'D', 'E'].map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-500 block mb-1">Sua resposta</label>
              <select value={form.sua_resposta} onChange={e => setForm(p => ({ ...p, sua_resposta: e.target.value }))}
                className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-600">
                <option value="">—</option>
                {['A', 'B', 'C', 'D', 'E'].map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="text-xs text-slate-500 block mb-1">Justificativa / Por que errei</label>
            <textarea value={form.justificativa} onChange={e => setForm(p => ({ ...p, justificativa: e.target.value }))}
              rows={2}
              className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-600 resize-none" />
          </div>
          <div className="flex gap-2 pt-1">
            <button type="button" onClick={onClose}
              className="flex-1 py-2 rounded-lg border border-slate-700 text-slate-400 hover:text-slate-200 text-sm transition-colors">
              Cancelar
            </button>
            <button type="submit"
              className="flex-1 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors">
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

  useEffect(() => {
    loadData()
  }, [filters])

  async function loadData() {
    setLoading(true)
    try {
      const params = {}
      if (filters.disciplina) params.disciplina = filters.disciplina
      if (filters.revisado !== '') params.revisado = filters.revisado === 'nao'
        ? false : filters.revisado === 'sim' ? true : undefined
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

  async function handleReview(id) {
    await api.markErrorReviewed(id)
    loadData()
  }

  async function handleDelete(id) {
    if (!confirm('Deletar este erro?')) return
    await api.deleteError(id)
    loadData()
  }

  async function handleSave(data) {
    await api.createError(data)
    loadData()
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Caderno de Erros</h1>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition-colors"
        >
          <Plus size={14} /> Erro Manual
        </button>
      </div>

      {staleCount > 0 && (
        <div className="flex items-center gap-2 bg-amber-900/20 border border-amber-800/50 rounded-lg px-4 py-3">
          <AlertTriangle size={15} className="text-amber-400" />
          <p className="text-sm text-amber-300">
            {staleCount} erro{staleCount > 1 ? 's' : ''} não revisado{staleCount > 1 ? 's' : ''} há mais de 7 dias
          </p>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        <select
          value={filters.disciplina}
          onChange={e => setFilters(p => ({ ...p, disciplina: e.target.value }))}
          className="bg-slate-800 border border-slate-700 rounded-md text-sm text-slate-300 px-2 py-1.5 focus:outline-none focus:border-indigo-600"
        >
          <option value="">Todas as disciplinas</option>
          {disciplines.map(d => <option key={d} value={d}>{d}</option>)}
        </select>
        <select
          value={filters.revisado}
          onChange={e => setFilters(p => ({ ...p, revisado: e.target.value }))}
          className="bg-slate-800 border border-slate-700 rounded-md text-sm text-slate-300 px-2 py-1.5 focus:outline-none focus:border-indigo-600"
        >
          <option value="">Todos</option>
          <option value="nao">Não revisados</option>
          <option value="sim">Revisados</option>
        </select>
        <select
          value={filters.dias}
          onChange={e => setFilters(p => ({ ...p, dias: e.target.value }))}
          className="bg-slate-800 border border-slate-700 rounded-md text-sm text-slate-300 px-2 py-1.5 focus:outline-none focus:border-indigo-600"
        >
          <option value="">Todo período</option>
          <option value="7">Últimos 7 dias</option>
          <option value="30">Últimos 30 dias</option>
        </select>
        <span className="text-sm text-slate-500 self-center">{errors.length} erros</span>
      </div>

      {loading ? (
        <div className="text-slate-500 text-sm animate-pulse">Carregando...</div>
      ) : errors.length === 0 ? (
        <div className="text-center py-12 text-slate-600">
          <AlertTriangle size={32} className="mx-auto mb-3 opacity-50" />
          <p className="text-sm">Nenhum erro encontrado</p>
        </div>
      ) : (
        <div className="space-y-3">
          {errors.map(e => (
            <ErrorCard key={e.id} error={e} onReview={handleReview} onDelete={handleDelete} />
          ))}
        </div>
      )}

      {showModal && (
        <ManualErrorModal onClose={() => setShowModal(false)} onSave={handleSave} />
      )}
    </div>
  )
}
