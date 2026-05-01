import { useState, useEffect } from 'react'
import { format, parseISO } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import { TrendingUp, Target, CalendarCheck, BookOpen } from 'lucide-react'
import * as api from '../api'

const glass = {
  background: 'rgba(255,255,255,0.05)',
  border: '0.5px solid rgba(255,255,255,0.10)',
  backdropFilter: 'blur(12px)',
  WebkitBackdropFilter: 'blur(12px)',
}

function GlassCard({ children, className = '' }) {
  return <div className={`rounded-container ${className}`} style={glass}>{children}</div>
}

function SectionLabel({ children }) {
  return <p className="text-[11px] font-medium text-white/40 uppercase tracking-widest mb-4">{children}</p>
}

function StatCard({ icon: Icon, value, label, accent }) {
  const color = accent || '#5B9EF4'
  return (
    <div
      className="rounded-card p-4 flex flex-col items-center text-center"
      style={{ background: 'rgba(255,255,255,0.05)', border: '0.5px solid rgba(255,255,255,0.09)' }}
    >
      <Icon size={22} strokeWidth={1.5} style={{ color, opacity: 0.7 }} />
      <p className="mt-2 text-[22px] font-bold leading-none" style={{ color }}>{value}</p>
      <p className="mt-1.5 text-[10px] text-white/40 uppercase tracking-wider">{label}</p>
    </div>
  )
}

function Heatmap({ days }) {
  if (!days.length) return null
  return (
    <div className="overflow-x-auto">
      <div className="flex flex-wrap gap-1">
        {days.map((d) => {
          const intensity = d.topics_total > 0 ? d.topics_done / d.topics_total : 0
          let bg = 'rgba(255,255,255,0.05)'
          if (d.tipo === 'prova') bg = 'rgba(212,132,90,0.85)'
          else if (d.status === 'concluido') bg = `rgba(91,158,244,${0.30 + intensity * 0.65})`
          else if (d.status === 'em_andamento') bg = 'rgba(212,132,90,0.45)'
          else if (d.tipo === 'sabado' || d.tipo === 'domingo') bg = 'rgba(255,255,255,0.03)'

          const label = format(parseISO(d.data), 'EEE dd/MM', { locale: ptBR })
          return (
            <div
              key={d.data}
              title={`${label} · ${d.status} · ${d.topics_done}/${d.topics_total}`}
              style={{ width: 14, height: 14, borderRadius: 3, backgroundColor: bg, border: '0.5px solid rgba(255,255,255,0.06)' }}
            />
          )
        })}
      </div>
      <div className="flex items-center gap-3 mt-4 text-[11px] text-white/45 flex-wrap">
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ backgroundColor: 'rgba(255,255,255,0.05)' }} /> Pendente</span>
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ backgroundColor: 'rgba(212,132,90,0.45)' }} /> Em andamento</span>
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ backgroundColor: 'rgba(91,158,244,0.85)' }} /> Concluído</span>
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ backgroundColor: 'rgba(212,132,90,0.85)' }} /> Prova</span>
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

  if (loading) return <p className="text-white/40 text-sm animate-pulse">Carregando...</p>
  if (!data) return null

  const totalDays = data.days.length
  const doneDays = data.days.filter(d => d.status === 'concluido').length
  const inProgressDays = data.days.filter(d => d.status === 'em_andamento').length
  const totalPct = totalDays > 0 ? Math.round(doneDays / totalDays * 100) : 0

  const chartData = data.mocks.map(m => {
    const point = { data: format(parseISO(m.data), 'dd/MM'), total: m.pct }
    m.por_disciplina.forEach(d => { point[d.disciplina] = d.pct })
    return point
  })

  const allDisciplines = [...new Set(data.mocks.flatMap(m => m.por_disciplina.map(d => d.disciplina)))]
  const COLORS = ['#5B9EF4', '#D4845A', '#A8B5CC', '#2D72D9', '#E8865A', '#7BB0F7', '#C9956F']

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-extrabold text-white tracking-tight">Progresso</h1>

      {/* Stat cards row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard icon={Target} value={`${totalPct}%`} label="Geral" />
        <StatCard icon={CalendarCheck} value={doneDays} label="Concluídos" />
        <StatCard icon={BookOpen} value={inProgressDays} label="Em andamento" accent="#D4845A" />
        <StatCard icon={TrendingUp} value={data.mocks.length} label="Simulados" accent="#A8B5CC" />
      </div>

      {/* Overall bar */}
      <GlassCard className="p-5">
        <SectionLabel>Progresso geral</SectionLabel>
        <div className="flex items-end justify-between mb-3">
          <p className="text-white/55 text-[13px]">{doneDays} de {totalDays} dias concluídos</p>
          <span className="text-3xl font-bold text-text-blue font-mono">{totalPct}%</span>
        </div>
        <div className="w-full rounded-full h-2 overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
          <div
            className="h-2 rounded-full transition-all"
            style={{ width: `${totalPct}%`, background: 'linear-gradient(90deg, #2D72D9, #5B9EF4)' }}
          />
        </div>
      </GlassCard>

      {/* Heatmap */}
      <GlassCard className="p-5">
        <SectionLabel>Calendário de estudo</SectionLabel>
        <Heatmap days={data.days} />
      </GlassCard>

      {/* Phase progress */}
      <GlassCard className="p-5">
        <SectionLabel>Por fase</SectionLabel>
        <div className="space-y-5">
          {data.phases.map(p => (
            <div key={p.numero} className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[13px] font-medium text-white">
                  <span className="text-text-blue">Fase {p.numero}</span> · {p.nome}
                </span>
                <span className="text-[13px] font-bold text-text-blue font-mono">{p.pct}%</span>
              </div>
              <div className="w-full rounded-full h-1.5 overflow-hidden" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <div
                  className="h-1.5 rounded-full transition-all"
                  style={{ width: `${p.pct}%`, background: 'linear-gradient(90deg, #2D72D9, #5B9EF4)' }}
                />
              </div>
              <p className="text-[11px] text-white/40 font-mono">{p.done_days}/{p.total_days} dias</p>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* Mock chart */}
      {data.mocks.length > 0 ? (
        <GlassCard className="p-5">
          <SectionLabel>Evolução em simulados</SectionLabel>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="data" tick={{ fill: 'rgba(255,255,255,0.45)', fontSize: 11 }} stroke="rgba(255,255,255,0.10)" />
                <YAxis domain={[0, 100]} tick={{ fill: 'rgba(255,255,255,0.45)', fontSize: 11 }} tickFormatter={v => `${v}%`} stroke="rgba(255,255,255,0.10)" />
                <Tooltip
                  contentStyle={{ background: '#1A2D50', border: '0.5px solid rgba(255,255,255,0.15)', borderRadius: 10, fontSize: 12 }}
                  labelStyle={{ color: '#FFFFFF', fontWeight: 600 }}
                  itemStyle={{ color: '#A8B5CC' }}
                  formatter={v => [`${v}%`]}
                />
                <Legend wrapperStyle={{ fontSize: 11, color: 'rgba(255,255,255,0.5)' }} />
                <Line type="monotone" dataKey="total" stroke="#5B9EF4" strokeWidth={2.5} dot={{ r: 4, fill: '#5B9EF4' }} name="Total" />
                {allDisciplines.map((d, i) => (
                  <Line key={d} type="monotone" dataKey={d} stroke={COLORS[(i + 1) % COLORS.length]}
                    strokeWidth={1.5} dot={{ r: 3 }} name={d} strokeDasharray="5 3" />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      ) : (
        <div className="text-center py-12">
          <p className="text-[13px] text-white/55">Nenhum simulado registrado ainda</p>
          <p className="text-[11px] text-white/35 mt-1 font-mono">Registre na aba Simulados</p>
        </div>
      )}
    </div>
  )
}
