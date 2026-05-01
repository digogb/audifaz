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

const inputCls = 'w-full rounded-btn px-3 py-2 text-[13px] text-white placeholder-white/30 focus:outline-none focus:border-accent-blue transition-colors'

function MockForm({ onClose, onSave }) {
  const [form, setForm] = useState({
    data: new Date().toISOString().split('T')[0], tipo: 'ti_especifico', observacoes: '',
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

  const Field = ({ label, children }) => (
    <div>
      <label className="block text-[11px] text-white/50 font-medium uppercase tracking-wider mb-1.5">{label}</label>
      {children}
    </div>
  )

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="rounded-hero w-full max-w-lg my-4 p-6 space-y-4" style={{ background: '#1A2D50', border: '0.5px solid rgba(255,255,255,0.15)' }}>
        <div className="flex items-center justify-between">
          <h2 className="font-bold text-white text-base">Registrar Simulado</h2>
          <button onClick={onClose} className="text-white/50 hover:text-white p-1 rounded-btn hover:bg-white/5 transition-colors">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Data">
              <input type="date" required value={form.data} onChange={e => setForm(p => ({ ...p, data: e.target.value }))} className={inputCls} style={inputStyle} />
            </Field>
            <Field label="Tipo">
              <select value={form.tipo} onChange={e => setForm(p => ({ ...p, tipo: e.target.value }))} className={inputCls} style={inputStyle}>
                {TIPOS.map(t => <option key={t.value} value={t.value} className="bg-bg-base">{t.label}</option>)}
              </select>
            </Field>
          </div>

          <Field label="Observações">
            <input value={form.observacoes} onChange={e => setForm(p => ({ ...p, observacoes: e.target.value }))}
              placeholder="ex: SEFAZ-BA 2019" className={inputCls} style={inputStyle} />
          </Field>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-[11px] text-white/50 font-medium uppercase tracking-wider">Por disciplina</label>
              <button type="button" onClick={addResult} className="text-[11px] text-text-blue hover:text-text-blue/80 flex items-center gap-1 font-medium">
                <Plus size={11} strokeWidth={2} /> Adicionar
              </button>
            </div>
            {results.map((r, i) => (
              <div key={i} className="flex gap-2 items-center">
                <input
                  list="disciplinas-list" value={r.disciplina}
                  onChange={e => updateResult(i, 'disciplina', e.target.value)}
                  placeholder="Disciplina"
                  className="flex-1 rounded-btn px-2 py-1.5 text-[12px] text-white placeholder-white/30 focus:outline-none focus:border-accent-blue"
                  style={inputStyle}
                />
                <input type="number" min={0} max={999} value={r.acertos}
                  onChange={e => updateResult(i, 'acertos', e.target.value)}
                  placeholder="✓"
                  className="w-14 rounded-btn px-2 py-1.5 text-[12px] text-white text-center focus:outline-none focus:border-accent-blue"
                  style={inputStyle} />
                <span className="text-white/30 text-xs">/</span>
                <input type="number" min={1} max={999} value={r.total}
                  onChange={e => updateResult(i, 'total', e.target.value)}
                  placeholder="tot"
                  className="w-14 rounded-btn px-2 py-1.5 text-[12px] text-white text-center focus:outline-none focus:border-accent-blue"
                  style={inputStyle} />
                <button type="button" onClick={() => removeResult(i)} className="text-white/40 hover:text-accent-orange p-1 transition-colors">
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

function MockCard({ mock, onDelete }) {
  const totalAcertos = mock.results.reduce((a, r) => a + r.acertos, 0)
  const totalQ = mock.results.reduce((a, r) => a + r.total, 0)
  const pct = totalQ > 0 ? Math.round(totalAcertos / totalQ * 100) : 0
  const tipoLabel = TIPOS.find(t => t.value === mock.tipo)?.label || mock.tipo

  const pctColor = pct >= 70 ? '#5B9EF4' : pct >= 50 ? '#A8B5CC' : '#D4845A'

  return (
    <div className="rounded-container p-5 space-y-4" style={glass}>
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="text-[14px] font-bold text-white">{tipoLabel}</span>
            <span className="text-[11px] text-white/45 font-mono">
              {format(parseISO(mock.data), "d MMM", { locale: ptBR })}
            </span>
            {mock.observacoes && <span className="text-[11px] text-white/40">· {mock.observacoes}</span>}
          </div>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-bold font-mono leading-none" style={{ color: pctColor }}>{pct}%</span>
            <span className="text-[11px] text-white/45 font-mono">{totalAcertos}/{totalQ} questões</span>
          </div>
        </div>
        <button onClick={() => onDelete(mock.id)} className="text-white/40 hover:text-accent-orange p-1.5 rounded-btn hover:bg-accent-orange/10 transition-colors">
          <Trash2 size={14} strokeWidth={1.75} />
        </button>
      </div>

      {mock.results.length > 0 && (
        <div className="space-y-2 pt-2" style={{ borderTop: '0.5px solid rgba(255,255,255,0.08)' }}>
          {mock.results.map(r => {
            const p = r.total > 0 ? Math.round(r.acertos / r.total * 100) : 0
            const barColor = p >= 70 ? '#5B9EF4' : p >= 50 ? '#A8B5CC' : '#D4845A'
            return (
              <div key={r.id} className="flex items-center gap-3 pt-1">
                <span className="text-[12px] text-white/65 w-40 truncate">{r.disciplina}</span>
                <div className="flex-1 rounded-full h-1.5" style={{ background: 'rgba(255,255,255,0.05)' }}>
                  <div className="h-1.5 rounded-full transition-all" style={{ width: `${p}%`, backgroundColor: barColor }} />
                </div>
                <span className="text-[11px] text-white/45 w-20 text-right font-mono">{r.acertos}/{r.total} ({p}%)</span>
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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-extrabold text-white tracking-tight">Simulados</h1>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-1.5 px-4 py-2 bg-accent-blue hover:bg-accent-blue/90 rounded-btn text-white text-[13px] font-semibold transition-colors"
        >
          <Plus size={13} strokeWidth={2} /> Registrar
        </button>
      </div>

      {mocks.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-[13px] text-white/55">Nenhum simulado registrado</p>
          <p className="text-[11px] text-white/35 mt-1 font-mono">Registre resultados de QConcursos, provas anteriores</p>
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
