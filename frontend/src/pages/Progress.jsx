import { useState, useEffect } from 'react'
import { format, parseISO } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import { TrendingUp, Target, CalendarCheck, BookOpen } from 'lucide-react'
import * as api from '../api'

// Track/superfície sutil que adapta ao tema (claro/escuro) via color-mix com o texto.
const TRACK = 'color-mix(in srgb, var(--color-text) 8%, transparent)'
const HAIRLINE = 'color-mix(in srgb, var(--color-text) 10%, transparent)'
const ACCENT_FILL = 'var(--color-accent)'

function GlassCard({ children, className = '' }) {
  return <div className={`surface-card ${className}`}>{children}</div>
}

function SectionLabel({ children }) {
  return <p className="text-[11px] font-medium text-subtle uppercase tracking-widest mb-4">{children}</p>
}

function StatCard({ icon: Icon, value, label, accent }) {
  const color = accent || 'var(--color-accent-text)'
  return (
    <div className="surface-card p-4 flex flex-col items-center text-center">
      <Icon size={22} strokeWidth={1.5} style={{ color, opacity: 0.85 }} />
      <p className="mt-2 text-[22px] font-bold leading-none" style={{ color }}>{value}</p>
      <p className="mt-1.5 text-[10px] text-subtle uppercase tracking-wider">{label}</p>
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
          let bg = TRACK
          if (d.tipo === 'prova') bg = 'color-mix(in srgb, var(--color-danger) 85%, transparent)'
          else if (d.status === 'concluido') bg = `color-mix(in srgb, var(--color-accent) ${Math.round((0.30 + intensity * 0.65) * 100)}%, transparent)`
          else if (d.status === 'em_andamento') bg = 'color-mix(in srgb, var(--color-danger) 45%, transparent)'
          else if (d.tipo === 'sabado' || d.tipo === 'domingo') bg = 'color-mix(in srgb, var(--color-text) 4%, transparent)'

          const label = format(parseISO(d.data), 'EEE dd/MM', { locale: ptBR })
          return (
            <div
              key={d.data}
              title={`${label} · ${d.status} · ${d.topics_done}/${d.topics_total}`}
              style={{ width: 14, height: 14, borderRadius: 3, backgroundColor: bg, border: `0.5px solid ${HAIRLINE}` }}
            />
          )
        })}
      </div>
      <div className="flex items-center gap-3 mt-4 text-[11px] text-subtle flex-wrap">
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ backgroundColor: TRACK }} /> Pendente</span>
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ backgroundColor: 'color-mix(in srgb, var(--color-danger) 45%, transparent)' }} /> Em andamento</span>
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ backgroundColor: 'var(--color-accent)' }} /> Concluído</span>
        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm inline-block" style={{ backgroundColor: 'var(--color-danger)' }} /> Prova</span>
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

  if (loading) return <p className="text-subtle text-sm animate-pulse">Carregando...</p>
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

  // Resolve cores do tema ativo (recharts precisa de strings de cor, não classes CSS).
  const css = typeof window !== 'undefined' ? getComputedStyle(document.documentElement) : null
  const cv = (name, fallback) => (css?.getPropertyValue(name).trim() || fallback)
  const cText = cv('--color-text', '#1A202C')
  const cSubtle = cv('--color-text-subtle', '#718096')
  const cSurface = cv('--color-bg-surface', '#FFFFFF')
  const cAccent = cv('--color-accent-text', '#1F4D3A')
  const cDanger = cv('--color-danger', '#C53030')
  const cSecondary = cv('--color-secondary', '#A8B5CC')
  const COLORS = [cAccent, cDanger, cSecondary, cAccent, cDanger, cSecondary]

  return (
    <div className="space-y-5 sm:space-y-6">
      <h1 className="text-xl sm:text-2xl font-extrabold text-primary tracking-tight">Progresso</h1>

      {/* Stat cards row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-3">
        <StatCard icon={Target} value={`${totalPct}%`} label="Geral" />
        <StatCard icon={CalendarCheck} value={doneDays} label="Concluídos" />
        <StatCard icon={BookOpen} value={inProgressDays} label="Em andamento" accent="var(--color-danger)" />
        <StatCard icon={TrendingUp} value={data.mocks.length} label="Simulados" accent="var(--color-text-muted)" />
      </div>

      {/* Overall bar */}
      <GlassCard className="p-4 sm:p-5">
        <SectionLabel>Progresso geral</SectionLabel>
        <div className="flex items-end justify-between mb-3">
          <p className="text-muted text-[13px]">{doneDays} de {totalDays} dias concluídos</p>
          <span className="text-3xl font-bold text-text-blue font-mono">{totalPct}%</span>
        </div>
        <div className="w-full rounded-full h-2 overflow-hidden" style={{ background: TRACK }}>
          <div
            className="h-2 rounded-full transition-all"
            style={{ width: `${totalPct}%`, background: ACCENT_FILL }}
          />
        </div>
      </GlassCard>

      {/* Heatmap */}
      <GlassCard className="p-4 sm:p-5">
        <SectionLabel>Calendário de estudo</SectionLabel>
        <Heatmap days={data.days} />
      </GlassCard>

      {/* Phase progress */}
      <GlassCard className="p-4 sm:p-5">
        <SectionLabel>Por fase</SectionLabel>
        <div className="space-y-5">
          {data.phases.map(p => (
            <div key={p.numero} className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[13px] font-medium text-primary">
                  <span className="text-text-blue">Fase {p.numero}</span> · {p.nome}
                </span>
                <span className="text-[13px] font-bold text-text-blue font-mono">{p.pct}%</span>
              </div>
              <div className="w-full rounded-full h-1.5 overflow-hidden" style={{ background: TRACK }}>
                <div
                  className="h-1.5 rounded-full transition-all"
                  style={{ width: `${p.pct}%`, background: ACCENT_FILL }}
                />
              </div>
              <p className="text-[11px] text-subtle font-mono">{p.done_days}/{p.total_days} dias</p>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* Mock chart */}
      {data.mocks.length > 0 ? (
        <GlassCard className="p-4 sm:p-5">
          <SectionLabel>Evolução em simulados</SectionLabel>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={cText} strokeOpacity={0.12} />
                <XAxis dataKey="data" tick={{ fill: cSubtle, fontSize: 11 }} stroke={cText} strokeOpacity={0.2} />
                <YAxis domain={[0, 100]} tick={{ fill: cSubtle, fontSize: 11 }} tickFormatter={v => `${v}%`} stroke={cText} strokeOpacity={0.2} />
                <Tooltip
                  contentStyle={{ background: cSurface, border: `1px solid ${cText}22`, borderRadius: 10, fontSize: 12 }}
                  labelStyle={{ color: cText, fontWeight: 600 }}
                  itemStyle={{ color: cSubtle }}
                  formatter={v => [`${v}%`]}
                />
                <Legend wrapperStyle={{ fontSize: 11, color: cSubtle }} />
                <Line type="monotone" dataKey="total" stroke={cAccent} strokeWidth={2.5} dot={{ r: 4, fill: cAccent }} name="Total" />
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
          <p className="text-[13px] text-muted">Nenhum simulado registrado ainda</p>
          <p className="text-[11px] text-subtle mt-1 font-mono">Registre na aba Simulados</p>
        </div>
      )}
    </div>
  )
}
