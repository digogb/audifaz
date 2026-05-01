import { useState, useEffect } from 'react'
import { format, parseISO } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { Plus, Trash2, X } from 'lucide-react'
import * as api from '../api'

const TIPOS = [
  { value: 'ti_especifico', label: 'TI Específico' },
  { value: 'conhec_gerais', label: 'Conhecimentos Gerais' },
  { value: 'discursiva', label: 'Discursiva' },
  { value: 'completo', label: 'Simulado Completo' },
]

const DISCIPLINAS_SUGERIDAS = [
  'TI Geral', 'COBIT / ITIL', 'Segurança da Informação', 'Cloud / DevOps',
  'Engenharia de Software', 'Banco de Dados', 'Ciência de Dados / IA',
  'Direito Tributário', 'Contabilidade', 'Auditoria',
  'Direito Constitucional/Administrativo', 'Língua Portuguesa',
  'Matemática / Estatística / Lógica', 'Economia',
]

const inputCls = 'w-full bg-surface-bg border border-surface-border rounded-xl px-3 py-2 text-sm text-text-main placeholder-text-faint focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/10 transition-all'

function MockForm({ onClose, onSave }) {
  const [form, setForm] = useState({
    data: new Date().toISOString().split('T')[0],
    tipo: 'ti_especifico',
    observacoes: '',
  })
  const [results, setResults] = useState(
    DISCIPLINAS_SUGERIDAS.slice(0, 4).map(d => ({ disciplina: d, acertos: '', total: '' }))
  )

  const addResult = () => setResults(p => [...p, { disciplina: '', acertos: '', total: '' }])
  const removeResult = (i) => setResults(p => p.filter((_, idx) => idx !== i))
  const updateResult = (i, field, val) => setResults(p => p.map((r, idx) => idx === i ? { ...r, [field]: val } : r))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const validResults = results
      .filter(r => r.disciplina && r.acertos !== '' && r.total !== '')
      .map(r => ({ disciplina: r.disciplina, acertos: parseInt(r.acertos), total: parseInt(r.total) }))
    await onSave({ ...form, results: validResults })
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-card shadow-card-hover w-full max-w-lg my-4 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-bold text-text-main">Registrar Simulado</h2>
          <button onClick={onClose} className="text-text-faint hover:text-text-main p-1 rounded-lg hover:bg-surface-bg transition-colors">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-text-muted font-semibold uppercase tracking-wider block mb-1.5">Data</label>
              <input type="date" required value={form.data} onChange={e => setForm(p => ({ ...p, data: e.target.value }))} className={inputCls} />
            </div>
            <div>
              <label className="text-xs text-text-muted font-semibold uppercase tracking-wider block mb-1.5">Tipo</label>
              <select value={form.tipo} onChange={e => setForm(p => ({ ...p, tipo: e.target.value }))} className={inputCls}>
                {TIPOS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs text-text-muted font-semibold uppercase tracking-wider block mb-1.5">Observações</label>
            <input value={form.observacoes} onChange={e => setForm(p => ({ ...p, observacoes: e.target.value }))}
              placeholder="ex: SEFAZ-BA 2019, QConcursos - filtro FCC"
              className={inputCls} />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs text-text-muted font-semibold uppercase tracking-wider">Por disciplina</label>
              <button type="button" onClick={addResult} className="text-xs text-brand hover:text-brand-dark flex items-center gap-1 font-medium">
                <Plus size={12} /> Adicionar
              </button>
            </div>
            {results.map((r, i) => (
              <div key={i} className="flex gap-2 items-center">
                <input
                  list="disciplinas-list"
                  value={r.disciplina}
                  onChange={e => updateResult(i, 'disciplina', e.target.value)}
                  placeholder="Disciplina"
                  className="flex-1 bg-surface-bg border border-surface-border rounded-xl px-2 py-1.5 text-xs text-text-main focus:outline-none focus:border-brand"
                />
                <input type="number" min={0} max={999} value={r.acertos}
                  onChange={e => updateResult(i, 'acertos', e.target.value)}
                  placeholder="✓"
                  className="w-14 bg-surface-bg border border-surface-border rounded-xl px-2 py-1.5 text-xs text-text-main text-center focus:outline-none focus:border-brand" />
                <span className="text-text-faint text-xs">/</span>
                <input type="number" min={1} max={999} value={r.total}
                  onChange={e => updateResult(i, 'total', e.target.value)}
                  placeholder="tot"
                  className="w-14 bg-surface-bg border border-surface-border rounded-xl px-2 py-1.5 text-xs text-text-main text-center focus:outline-none focus:border-brand" />
                <button type="button" onClick={() => removeResult(i)} className="text-text-faint hover:text-coral p-1 transition-colors">
                  <X size={14} />
                </button>
              </div>
            ))}
            <datalist id="disciplinas-list">
              {DISCIPLINAS_SUGERIDAS.map(d => <option key={d} value={d} />)}
            </datalist>
          </div>

          <div className="flex gap-2 pt-1">
            <button type="button" onClick={onClose}
              className="flex-1 py-2 rounded-xl border border-surface-border text-text-muted hover:text-text-main text-sm font-medium transition-colors">
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

function MockCard({ mock, onDelete }) {
  const totalAcertos = mock.results.reduce((a, r) => a + r.acertos, 0)
  const totalQ = mock.results.reduce((a, r) => a + r.total, 0)
  const pct = totalQ > 0 ? Math.round(totalAcertos / totalQ * 100) : 0
  const tipoLabel = TIPOS.find(t => t.value === mock.tipo)?.label || mock.tipo

  const accentColor = pct >= 70 ? 'border-l-sage' : pct >= 50 ? 'border-l-gold' : 'border-l-coral'
  const pctColor = pct >= 70 ? 'text-sage' : pct >= 50 ? 'text-gold' : 'text-coral'

  return (
    <div className={`bg-white rounded-card shadow-card border-l-4 ${accentColor} p-5 space-y-4`}>
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-bold text-text-main">{tipoLabel}</span>
            <span className="text-xs text-text-muted">
              {format(parseISO(mock.data), "d 'de' MMMM", { locale: ptBR })}
            </span>
            {mock.observacoes && <span className="text-xs text-text-faint">· {mock.observacoes}</span>}
          </div>
          <div className="flex items-baseline gap-2 mt-1">
            <span className={`text-2xl font-bold ${pctColor}`}>{pct}%</span>
            <span className="text-xs text-text-muted">{totalAcertos}/{totalQ} questões</span>
          </div>
        </div>
        <button onClick={() => onDelete(mock.id)} className="text-text-faint hover:text-coral p-1.5 rounded-lg hover:bg-red-50 transition-colors">
          <Trash2 size={15} />
        </button>
      </div>

      {mock.results.length > 0 && (
        <div className="space-y-2">
          {mock.results.map(r => {
            const p = r.total > 0 ? Math.round(r.acertos / r.total * 100) : 0
            const barColor = p >= 70 ? '#27AE60' : p >= 50 ? '#F39C12' : '#F04747'
            return (
              <div key={r.id} className="flex items-center gap-3">
                <span className="text-xs text-text-muted w-40 truncate">{r.disciplina}</span>
                <div className="flex-1 bg-surface-bg rounded-full h-1.5">
                  <div className="h-1.5 rounded-full transition-all" style={{ width: `${p}%`, backgroundColor: barColor }} />
                </div>
                <span className="text-xs text-text-muted w-20 text-right">{r.acertos}/{r.total} ({p}%)</span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default function Mocks() {
  const [mocks, setMocks] = useState([])
  const [showForm, setShowForm] = useState(false)

  useEffect(() => { api.getMocks().then(r => setMocks(r.data)) }, [])

  async function handleSave(data) {
    await api.createMock(data)
    const r = await api.getMocks()
    setMocks(r.data)
  }

  async function handleDelete(id) {
    if (!confirm('Deletar este simulado?')) return
    await api.deleteMock(id)
    setMocks(p => p.filter(m => m.id !== id))
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-text-main">Simulados</h1>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-1.5 px-4 py-2 bg-brand hover:bg-brand-dark rounded-xl text-white text-sm font-semibold shadow-sm transition-colors"
        >
          <Plus size={14} /> Registrar
        </button>
      </div>

      {mocks.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-sm text-text-muted">Nenhum simulado registrado</p>
          <p className="text-xs text-text-faint mt-1">Registre seus resultados do QConcursos, provas anteriores, etc.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {mocks.map(m => <MockCard key={m.id} mock={m} onDelete={handleDelete} />)}
        </div>
      )}

      {showForm && <MockForm onClose={() => setShowForm(false)} onSave={handleSave} />}
    </div>
  )
}
