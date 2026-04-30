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
  'TI Geral',
  'COBIT / ITIL',
  'Segurança da Informação',
  'Cloud / DevOps',
  'Engenharia de Software',
  'Banco de Dados',
  'Ciência de Dados / IA',
  'Direito Tributário',
  'Contabilidade',
  'Auditoria',
  'Direito Constitucional/Administrativo',
  'Língua Portuguesa',
  'Matemática / Estatística / Lógica',
  'Economia',
]

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
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-slate-900 rounded-2xl border border-slate-700 w-full max-w-lg my-4">
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-slate-200">Registrar Simulado</h2>
            <button onClick={onClose} className="text-slate-500 hover:text-slate-300"><X size={18} /></button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-slate-500 block mb-1">Data</label>
                <input type="date" required value={form.data} onChange={e => setForm(p => ({ ...p, data: e.target.value }))}
                  className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-600" />
              </div>
              <div>
                <label className="text-xs text-slate-500 block mb-1">Tipo</label>
                <select value={form.tipo} onChange={e => setForm(p => ({ ...p, tipo: e.target.value }))}
                  className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-600">
                  {TIPOS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
            </div>

            <div>
              <label className="text-xs text-slate-500 block mb-1">Observações</label>
              <input value={form.observacoes} onChange={e => setForm(p => ({ ...p, observacoes: e.target.value }))}
                placeholder="ex: SEFAZ-BA 2019, QConcursos - filtro FCC"
                className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-600" />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs text-slate-500 uppercase tracking-wider">Resultados por disciplina</label>
                <button type="button" onClick={addResult}
                  className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
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
                    className="flex-1 bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-600"
                  />
                  <input type="number" min={0} max={999} value={r.acertos}
                    onChange={e => updateResult(i, 'acertos', e.target.value)}
                    placeholder="✓"
                    className="w-14 bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-xs text-slate-200 text-center focus:outline-none focus:border-indigo-600" />
                  <span className="text-slate-600 text-xs">/</span>
                  <input type="number" min={1} max={999} value={r.total}
                    onChange={e => updateResult(i, 'total', e.target.value)}
                    placeholder="tot"
                    className="w-14 bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-xs text-slate-200 text-center focus:outline-none focus:border-indigo-600" />
                  <button type="button" onClick={() => removeResult(i)} className="text-slate-600 hover:text-rose-400">
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
    </div>
  )
}

function MockCard({ mock, onDelete }) {
  const totalAcertos = mock.results.reduce((a, r) => a + r.acertos, 0)
  const totalQ = mock.results.reduce((a, r) => a + r.total, 0)
  const pct = totalQ > 0 ? Math.round(totalAcertos / totalQ * 100) : 0
  const tipoLabel = TIPOS.find(t => t.value === mock.tipo)?.label || mock.tipo

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 p-4 space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-slate-200">{tipoLabel}</span>
            <span className="text-xs text-slate-500">
              {format(parseISO(mock.data), "d 'de' MMMM", { locale: ptBR })}
            </span>
            {mock.observacoes && <span className="text-xs text-slate-500">· {mock.observacoes}</span>}
          </div>
          <div className="flex items-center gap-2 mt-1">
            <span className={`text-xl font-bold ${pct >= 70 ? 'text-emerald-400' : pct >= 50 ? 'text-amber-400' : 'text-rose-400'}`}>
              {pct}%
            </span>
            <span className="text-xs text-slate-500">{totalAcertos}/{totalQ} questões</span>
          </div>
        </div>
        <button onClick={() => onDelete(mock.id)} className="text-slate-600 hover:text-rose-400 p-1">
          <Trash2 size={15} />
        </button>
      </div>

      {mock.results.length > 0 && (
        <div className="space-y-1.5">
          {mock.results.map(r => {
            const p = r.total > 0 ? Math.round(r.acertos / r.total * 100) : 0
            return (
              <div key={r.id} className="flex items-center gap-2">
                <span className="text-xs text-slate-400 w-40 truncate">{r.disciplina}</span>
                <div className="flex-1 bg-slate-800 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full ${p >= 70 ? 'bg-emerald-500' : p >= 50 ? 'bg-amber-500' : 'bg-rose-500'}`}
                    style={{ width: `${p}%` }}
                  />
                </div>
                <span className="text-xs text-slate-500 w-16 text-right">{r.acertos}/{r.total} ({p}%)</span>
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

  useEffect(() => {
    api.getMocks().then(r => setMocks(r.data))
  }, [])

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
        <h1 className="text-xl font-semibold">Simulados</h1>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition-colors"
        >
          <Plus size={14} /> Registrar
        </button>
      </div>

      {mocks.length === 0 ? (
        <div className="text-center py-12 text-slate-600">
          <p className="text-sm">Nenhum simulado registrado</p>
          <p className="text-xs mt-1">Registre seus resultados de simulados do QConcursos, provas anteriores, etc.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {mocks.map(m => (
            <MockCard key={m.id} mock={m} onDelete={handleDelete} />
          ))}
        </div>
      )}

      {showForm && <MockForm onClose={() => setShowForm(false)} onSave={handleSave} />}
    </div>
  )
}
