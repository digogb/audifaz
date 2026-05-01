import { useState, useEffect } from 'react'
import { format, parseISO } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { AlertTriangle, CheckCircle, Trash2, ChevronDown, ChevronUp, Plus, X } from 'lucide-react'
import * as api from '../api'

const glass = {
  background: 'rgba(255,255,255,0.05)',
  border: '0.5px solid rgba(255,255,255,0.10)',
  backdropFilter: 'blur(12px)',
  WebkitBackdropFilter: 'blur(12px)',
}

const inputStyle = {
  background: 'rgba(255,255,255,0.04)',
  border: '0.5px solid rgba(255,255,255,0.12)',
}

function ErrorCard({ error, onReview, onDelete }) {
  const [expanded, setExpanded] = useState(false)
  const reviewed = !!error.revisado_em

  return (
    <div
      className={`rounded-container p-4 space-y-3 transition-opacity ${reviewed ? 'opacity-50' : ''}`}
      style={glass}
    >
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <span className="text-[11px] font-bold text-text-blue uppercase tracking-wider">{error.disciplina}</span>
            {error.subtopico && <span className="text-[11px] text-white/55">{error.subtopico}</span>}
            {error.banca && (
              <span
                className="text-[10px] px-2 py-0.5 rounded-full text-white/75 font-medium uppercase tracking-wider"
                style={{ background: 'rgba(91,158,244,0.12)', border: '0.5px solid rgba(91,158,244,0.30)' }}
              >
                {error.banca}
              </span>
            )}
            <span className="text-[11px] text-white/35 font-mono">{format(parseISO(error.data), 'dd/MM/yy', { locale: ptBR })}</span>
            {reviewed && <span className="text-[11px] text-text-blue font-medium">✓ revisado</span>}
            {error.sua_resposta && (
              <span className="text-[11px] text-accent-orange font-mono">
                {error.sua_resposta} → {error.gabarito}
              </span>
            )}
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-[14px] text-white/85 text-left hover:text-white transition-colors leading-relaxed"
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
              className="p-1.5 rounded-btn text-white/40 hover:text-text-blue hover:bg-text-blue/10 transition-colors"
              title="Marcar como revisado"
            >
              <CheckCircle size={14} strokeWidth={1.75} />
            </button>
          )}
          <button
            onClick={() => onDelete(error.id)}
            className="p-1.5 rounded-btn text-white/40 hover:text-accent-orange hover:bg-accent-orange/10 transition-colors"
            title="Deletar"
          >
            <Trash2 size={14} strokeWidth={1.75} />
          </button>
        </div>
      </div>

      {expanded && error.justificativa && (
        <div
          className="rounded-btn p-3 text-[12px] text-white/70 leading-relaxed"
          style={{ background: 'rgba(255,255,255,0.03)', border: '0.5px solid rgba(255,255,255,0.08)' }}
        >
          <span className="font-semibold text-text-blue">Comentário · </span>
          {error.justificativa}
        </div>
      )}

      {error.enunciado.length > 150 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-[11px] text-white/40 hover:text-text-blue flex items-center gap-1 transition-colors"
        >
          {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          {expanded ? 'Mostrar menos' : 'Mostrar mais'}
        </button>
      )}
    </div>
  )
}

const inputCls = 'w-full rounded-btn px-3 py-2 text-[13px] text-white placeholder-white/30 focus:outline-none focus:border-accent-blue transition-colors'

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
      <label className="block text-[11px] text-white/50 font-medium uppercase tracking-wider mb-1.5">{label}</label>
      {children}
    </div>
  )

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-start sm:items-center justify-center p-3 sm:p-4 overflow-y-auto">
      <div className="rounded-hero w-full max-w-lg my-4 p-5 sm:p-6 space-y-4" style={{ background: '#1A2D50', border: '0.5px solid rgba(255,255,255,0.15)' }}>
        <div className="flex items-center justify-between">
          <h2 className="font-bold text-white text-base">Registrar Erro Manual</h2>
          <button onClick={onClose} className="text-white/50 hover:text-white p-1 rounded-btn hover:bg-white/5 transition-colors">
            <X size={18} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Data">
              <input type="date" value={form.data} onChange={e => setForm(p => ({ ...p, data: e.target.value }))} className={inputCls} style={inputStyle} />
            </Field>
            <Field label="Banca">
              <input value={form.banca} onChange={e => setForm(p => ({ ...p, banca: e.target.value }))} className={inputCls} style={inputStyle} />
            </Field>
          </div>
          <Field label="Disciplina *">
            <input required value={form.disciplina} onChange={e => setForm(p => ({ ...p, disciplina: e.target.value }))} placeholder="ex: COBIT 2019" className={inputCls} style={inputStyle} />
          </Field>
          <Field label="Subtópico">
            <input value={form.subtopico} onChange={e => setForm(p => ({ ...p, subtopico: e.target.value }))} className={inputCls} style={inputStyle} />
          </Field>
          <Field label="Enunciado *">
            <textarea required value={form.enunciado} onChange={e => setForm(p => ({ ...p, enunciado: e.target.value }))} rows={3} className={`${inputCls} resize-none`} style={inputStyle} />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Gabarito *">
              <select required value={form.gabarito} onChange={e => setForm(p => ({ ...p, gabarito: e.target.value }))} className={inputCls} style={inputStyle}>
                {['A', 'B', 'C', 'D', 'E'].map(l => <option key={l} value={l} className="bg-bg-base">{l}</option>)}
              </select>
            </Field>
            <Field label="Sua resposta">
              <select value={form.sua_resposta} onChange={e => setForm(p => ({ ...p, sua_resposta: e.target.value }))} className={inputCls} style={inputStyle}>
                <option value="" className="bg-bg-base">—</option>
                {['A', 'B', 'C', 'D', 'E'].map(l => <option key={l} value={l} className="bg-bg-base">{l}</option>)}
              </select>
            </Field>
          </div>
          <Field label="Por que errei">
            <textarea value={form.justificativa} onChange={e => setForm(p => ({ ...p, justificativa: e.target.value }))} rows={2} className={`${inputCls} resize-none`} style={inputStyle} />
          </Field>
          <div className="flex gap-2 pt-1">
            <button type="button" onClick={onClose}
              className="flex-1 py-2 rounded-btn text-white/65 hover:text-white text-[13px] font-medium transition-colors"
              style={{ background: 'rgba(255,255,255,0.05)', border: '0.5px solid rgba(255,255,255,0.12)' }}>
              Cancelar
            </button>
            <button type="submit"
              className="flex-1 py-2 rounded-btn bg-accent-blue hover:bg-accent-blue/90 text-white text-[13px] font-semibold transition-colors">
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

  const selectCls = 'rounded-btn text-[12px] text-white/80 px-3 py-2 focus:outline-none focus:border-accent-blue'

  return (
    <div className="space-y-5 sm:space-y-6">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">Caderno de Erros</h1>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1.5 px-3 sm:px-4 py-2 bg-accent-blue hover:bg-accent-blue/90 rounded-btn text-white text-[13px] font-semibold transition-colors"
        >
          <Plus size={13} strokeWidth={2} /> <span className="hidden sm:inline">Erro Manual</span><span className="sm:hidden">Novo</span>
        </button>
      </div>

      {staleCount > 0 && (
        <div
          className="flex items-center gap-3 rounded-container px-4 py-3"
          style={{ background: 'rgba(212,132,90,0.08)', border: '0.5px solid rgba(212,132,90,0.30)' }}
        >
          <AlertTriangle size={16} className="text-accent-orange shrink-0" strokeWidth={1.75} />
          <p className="text-[13px] text-accent-orange font-medium">
            {staleCount} erro{staleCount > 1 ? 's' : ''} não revisado{staleCount > 1 ? 's' : ''} há mais de 7 dias
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 sm:flex gap-2 sm:flex-wrap items-stretch sm:items-center">
        <select value={filters.disciplina} onChange={e => setFilters(p => ({ ...p, disciplina: e.target.value }))} className={selectCls + ' w-full sm:w-auto'} style={inputStyle}>
          <option value="" className="bg-bg-base">Todas as disciplinas</option>
          {disciplines.map(d => <option key={d} value={d} className="bg-bg-base">{d}</option>)}
        </select>
        <div className="grid grid-cols-2 sm:flex gap-2">
          <select value={filters.revisado} onChange={e => setFilters(p => ({ ...p, revisado: e.target.value }))} className={selectCls + ' w-full sm:w-auto'} style={inputStyle}>
            <option value="" className="bg-bg-base">Todos</option>
            <option value="nao" className="bg-bg-base">Não revisados</option>
            <option value="sim" className="bg-bg-base">Revisados</option>
          </select>
          <select value={filters.dias} onChange={e => setFilters(p => ({ ...p, dias: e.target.value }))} className={selectCls + ' w-full sm:w-auto'} style={inputStyle}>
            <option value="" className="bg-bg-base">Todo período</option>
            <option value="7" className="bg-bg-base">Últimos 7 dias</option>
            <option value="30" className="bg-bg-base">Últimos 30 dias</option>
          </select>
        </div>
        <span className="text-[12px] text-white/45 font-mono sm:self-center">{errors.length} erros</span>
      </div>

      {loading ? (
        <p className="text-white/40 text-sm animate-pulse">Carregando...</p>
      ) : errors.length === 0 ? (
        <div className="text-center py-16">
          <AlertTriangle size={32} className="mx-auto mb-3 text-white/20" strokeWidth={1.5} />
          <p className="text-[13px] text-white/55">Nenhum erro encontrado</p>
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
