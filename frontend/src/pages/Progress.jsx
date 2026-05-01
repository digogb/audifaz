import { useState, useEffect } from 'react'
import { format, parseISO } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import * as api from '../api'

function Heatmap({ days }) {
  if (!days.length) return null
  return (
    <div className="overflow-x-auto">
      <div className="flex flex-wrap gap-1">
        {days.map((d) => {
          const intensity = d.topics_total > 0 ? d.topics_done / d.topics_total : 0
          let bg = '#E8E8F0'
          if (d.tipo === 'prova') bg = '#F04747'
          else if (d.status === 'concluido') bg = `rgba(39,174,96,${0.25 + intensity * 0.75})`
          else if (d.status === 'em_andamento') bg = 'rgba(230,126,34,0.45)'
          else if (d.tipo === 'sabado' || d.tipo === 'domingo') bg = '#BDC3C7'

          const label = format(parseISO(d.data), 'EEE dd/MM', { locale: ptBR })
          return (
            <div
              key={d.data}
              title={`${label} · ${d.status} · ${d.topics_done}/${d.topics_total}`}
              style={{ width: 16, height: 16, borderRadius: 4, backgroundColor: bg }}
            />
          )
        })}
      </div>
      <div className="flex items-center gap-3 mt-3 text-xs text-text-muted flex-wrap">
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm inline-block" style={{ backgroundColor: '#E8E8F0' }} /> Pendente</span>
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm inline-block" style={{ backgroundColor: 'rgba(230,126,34,0.45)' }} /> Em andamento</span>
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm inline-block" style={{ backgroundColor: 'rgba(39,174,96,0.8)' }} /> Concluído</span>
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm inline-block" style={{ backgroundColor: '#F04747' }} /> Prova</span>
      </div>
    </div>
  )
}

function Card({ children, accent, className = '' }) {
  return (
    <div className={`bg-white rounded-card shadow-card border-l-4 ${accent ?? 'border-l-surface-border'} p-5 ${className}`}>
      {children}
    </div>
  )
}

function SectionLabel({ children }) {
  return <p className="text-xs font-semibold text-text-muted uppercase tracking-widest mb-4">{children}</p>
}

export default function Progress() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getProgress().then(r => setData(r.data)).finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-text-faint text-sm animate-pulse">Carregando...</p>
  if (!data) return null

  const totalDays = data.days.length
  const doneDays = data.days.filter(d => d.status === 'concluido').length
  const totalPct = totalDays > 0 ? Math.round(doneDays / totalDays * 100) : 0

  const chartData = data.mocks.map(m => {
    const point = { data: format(parseISO(m.data), 'dd/MM'), total: m.pct }
    m.por_disciplina.forEach(d => { point[d.disciplina] = d.pct })
    return point
  })

  const allDisciplines = [...new Set(data.mocks.flatMap(m => m.por_disciplina.map(d => d.disciplina)))]
  const COLORS = ['#8E44AD', '#27AE60', '#E67E22', '#F04747', '#2980B9', '#F39C12', '#1ABC9C']

  return (
    <div className="space-y-5">
      <h1 className="text-xl font-bold text-text-main">Progresso</h1>

      {/* Overall */}
      <Card accent="border-l-brand">
        <SectionLabel>Progresso geral</SectionLabel>
        <div className="flex items-end justify-between mb-3">
          <p className="text-text-muted text-sm">{doneDays} de {totalDays} dias concluídos</p>
          <span className="text-3xl font-bold text-brand">{totalPct}%</span>
        </div>
        <div className="w-full bg-surface-bg rounded-full h-3">
          <div
            className="h-3 rounded-full transition-all"
            style={{ width: `${totalPct}%`, backgroundColor: '#8E44AD' }}
          />
        </div>
      </Card>

      {/* Heatmap */}
      <Card accent="border-l-gold">
        <SectionLabel>Calendário de estudo</SectionLabel>
        <Heatmap days={data.days} />
      </Card>

      {/* Phase progress */}
      <Card accent="border-l-tangerine">
        <SectionLabel>Por fase</SectionLabel>
        <div className="space-y-5">
          {data.phases.map(p => (
            <div key={p.numero} className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-text-main">
                  Fase {p.numero}: {p.nome}
                </span>
                <span className="text-sm font-bold text-brand">{p.pct}%</span>
              </div>
              <div className="w-full bg-surface-bg rounded-full h-2">
                <div
                  className="h-2 rounded-full transition-all"
                  style={{ width: `${p.pct}%`, backgroundColor: '#8E44AD' }}
                />
              </div>
              <p className="text-xs text-text-faint">{p.done_days}/{p.total_days} dias</p>
            </div>
          ))}
        </div>
      </Card>

      {/* Mock chart */}
      {data.mocks.length > 0 ? (
        <Card accent="border-l-sage">
          <SectionLabel>Evolução em simulados</SectionLabel>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E8E8F0" />
                <XAxis dataKey="data" tick={{ fill: '#7F8C8D', fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fill: '#7F8C8D', fontSize: 11 }} tickFormatter={v => `${v}%`} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#fff', border: '1px solid #E8E8F0', borderRadius: 12, fontSize: 12 }}
                  labelStyle={{ color: '#2C3E50', fontWeight: 600 }}
                  formatter={v => [`${v}%`]}
                />
                <Legend wrapperStyle={{ fontSize: 11, color: '#7F8C8D' }} />
                <Line type="monotone" dataKey="total" stroke="#8E44AD" strokeWidth={2.5} dot={{ r: 4, fill: '#8E44AD' }} name="Total" />
                {allDisciplines.map((d, i) => (
                  <Line key={d} type="monotone" dataKey={d} stroke={COLORS[(i + 1) % COLORS.length]}
                    strokeWidth={1.5} dot={{ r: 3 }} name={d} strokeDasharray="5 3" />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      ) : (
        <div className="text-center py-12">
          <p className="text-sm text-text-muted">Nenhum simulado registrado ainda</p>
          <p className="text-xs text-text-faint mt-1">Registre seus resultados na aba Simulados</p>
        </div>
      )}
    </div>
  )
}
