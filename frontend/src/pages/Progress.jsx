import { useState, useEffect } from 'react'
import { format, parseISO } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import * as api from '../api'

const STATUS_COLORS = {
  concluido: '#10b981',
  em_andamento: '#f59e0b',
  pendente: '#1e293b',
  prova: '#ef4444',
}

function Heatmap({ days }) {
  if (!days.length) return null

  return (
    <div className="overflow-x-auto">
      <div className="flex flex-wrap gap-1" style={{ maxWidth: '100%' }}>
        {days.map((d, i) => {
          const intensity = d.topics_total > 0 ? d.topics_done / d.topics_total : 0
          let bg = '#1e293b'
          if (d.tipo === 'prova') bg = '#7f1d1d'
          else if (d.status === 'concluido') bg = `rgba(16,185,129,${0.3 + intensity * 0.7})`
          else if (d.status === 'em_andamento') bg = 'rgba(245,158,11,0.5)'
          else if (d.tipo === 'sabado' || d.tipo === 'domingo') bg = '#0f172a'

          const label = format(parseISO(d.data), 'EEE dd/MM', { locale: ptBR })
          return (
            <div
              key={d.data}
              title={`${label} · ${d.status} · ${d.topics_done}/${d.topics_total}`}
              style={{ width: 16, height: 16, borderRadius: 3, backgroundColor: bg }}
            />
          )
        })}
      </div>
      <div className="flex items-center gap-2 mt-3 text-xs text-slate-500">
        <div className="w-3 h-3 rounded-sm bg-slate-800" /> Pendente
        <div className="w-3 h-3 rounded-sm bg-amber-500/50" /> Em andamento
        <div className="w-3 h-3 rounded-sm bg-emerald-500/70" /> Concluído
        <div className="w-3 h-3 rounded-sm bg-rose-900/70" /> Prova
      </div>
    </div>
  )
}

export default function Progress() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getProgress().then(r => setData(r.data)).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-slate-500 text-sm animate-pulse">Carregando...</div>
  if (!data) return null

  const totalDays = data.days.length
  const doneDays = data.days.filter(d => d.status === 'concluido').length
  const totalPct = totalDays > 0 ? Math.round(doneDays / totalDays * 100) : 0

  // Build chart series from mocks
  const chartData = data.mocks.map(m => {
    const point = { data: format(parseISO(m.data), 'dd/MM'), total: m.pct }
    m.por_disciplina.forEach(d => { point[d.disciplina] = d.pct })
    return point
  })

  const allDisciplines = [...new Set(data.mocks.flatMap(m => m.por_disciplina.map(d => d.disciplina)))]
  const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#84cc16']

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold">Progresso</h1>

      {/* Overall */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">Progresso geral</span>
          <span className="text-2xl font-bold text-slate-100">{totalPct}%</span>
        </div>
        <div className="w-full bg-slate-800 rounded-full h-2">
          <div
            className="bg-indigo-500 h-2 rounded-full transition-all"
            style={{ width: `${totalPct}%` }}
          />
        </div>
        <p className="text-xs text-slate-500">{doneDays} de {totalDays} dias concluídos</p>
      </div>

      {/* Heatmap */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 space-y-3">
        <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider">Calendário de estudo</h2>
        <Heatmap days={data.days} />
      </div>

      {/* Phase progress */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 space-y-4">
        <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider">Por fase</h2>
        {data.phases.map(p => (
          <div key={p.numero} className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">
                Fase {p.numero}: {p.nome}
              </span>
              <span className="text-sm font-semibold text-slate-200">{p.pct}%</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-1.5">
              <div
                className="bg-indigo-500 h-1.5 rounded-full transition-all"
                style={{ width: `${p.pct}%` }}
              />
            </div>
            <p className="text-xs text-slate-600">{p.done_days}/{p.total_days} dias</p>
          </div>
        ))}
      </div>

      {/* Mock chart */}
      {data.mocks.length > 0 && (
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 space-y-4">
          <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider">Evolução em simulados</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="data" tick={{ fill: '#64748b', fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 11 }} tickFormatter={v => `${v}%`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: 8 }}
                  labelStyle={{ color: '#94a3b8', fontSize: 11 }}
                  itemStyle={{ fontSize: 11 }}
                  formatter={v => [`${v}%`]}
                />
                <Legend wrapperStyle={{ fontSize: 11, color: '#64748b' }} />
                <Line type="monotone" dataKey="total" stroke="#6366f1" strokeWidth={2} dot={{ r: 4 }} name="Total" />
                {allDisciplines.map((d, i) => (
                  <Line key={d} type="monotone" dataKey={d} stroke={COLORS[(i + 1) % COLORS.length]}
                    strokeWidth={1.5} dot={{ r: 3 }} name={d} strokeDasharray="4 2" />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {data.mocks.length === 0 && (
        <div className="text-center py-8 text-slate-600">
          <p className="text-sm">Nenhum simulado registrado ainda</p>
          <p className="text-xs mt-1">Registre seus primeiros simulados na aba Simulados</p>
        </div>
      )}
    </div>
  )
}
