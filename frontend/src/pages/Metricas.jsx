import { useEffect, useMemo, useState } from 'react'
import { Target, AlertTriangle, TrendingUp, CheckCircle2, MinusCircle } from 'lucide-react'
import * as api from '../api'

const STATUS_META = {
  ok:       { label: 'No alvo',       cls: 'text-success',     Icon: CheckCircle2 },
  alerta:   { label: 'Atenção',       cls: 'text-secondary',   Icon: AlertTriangle },
  critico:  { label: 'Crítico',       cls: 'text-danger',      Icon: AlertTriangle },
  sem_dados:{ label: 'Sem dados',     cls: 'text-subtle',      Icon: MinusCircle },
}

const PRIO_META = {
  alta:  { label: 'Alta',  cls: 'text-danger' },
  media: { label: 'Média', cls: 'text-secondary' },
  baixa: { label: 'Baixa', cls: 'text-subtle' },
}

function StatusBadge({ status }) {
  const m = STATUS_META[status] || STATUS_META.sem_dados
  const Icon = m.Icon
  return (
    <span className={`inline-flex items-center gap-1 text-[11px] font-medium ${m.cls}`}>
      <Icon size={12} strokeWidth={2} />
      {m.label}
    </span>
  )
}

function GapBar({ pct, meta }) {
  const width = Math.max(0, Math.min(100, pct))
  const metaPos = Math.max(0, Math.min(100, meta))
  return (
    <div className="relative w-full h-1.5 rounded-full overflow-hidden bg-accent-soft">
      <div
        className="absolute inset-y-0 left-0 bg-accent transition-all"
        style={{ width: `${width}%` }}
      />
      <div
        className="absolute inset-y-0 w-px bg-primary opacity-50"
        style={{ left: `${metaPos}%` }}
        title={`Meta: ${meta}%`}
      />
    </div>
  )
}

export default function Metricas() {
  const [data, setData] = useState(null)
  const [err, setErr] = useState(null)

  useEffect(() => {
    api.getMetricasBlocos()
      .then(res => setData(res.data))
      .catch(e => setErr(e.response?.data?.detail || 'Erro ao carregar métricas'))
  }, [])

  const bottleneck = useMemo(() => {
    if (!data) return null
    const candidatos = data
      .filter(b => b.total_attempts > 0 && b.gap_meta < 0)
      .map(b => ({ ...b, score: b.peso * Math.abs(b.gap_meta) }))
      .sort((a, b) => b.score - a.score)
    return candidatos[0] || null
  }, [data])

  if (err) return <p className="text-danger text-sm">{err}</p>
  if (!data) return <p className="text-subtle text-sm animate-pulse">Carregando métricas...</p>

  const total = data.reduce((s, b) => s + b.total_attempts, 0)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-2xl sm:text-3xl font-extrabold tracking-tight text-primary">Métricas por bloco</h1>
        <p className="text-[13px] text-subtle mt-1">
          Acerto por bloco temático, peso e meta. Cada bloco soma questões geradas + simulados.
        </p>
      </div>

      {bottleneck ? (
        <div className="surface-card p-4 sm:p-5 flex items-start gap-4">
          <div className="rounded-btn p-2 bg-accent-soft shrink-0">
            <Target size={18} className="text-accent" strokeWidth={2} />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-[11px] font-medium uppercase tracking-widest text-subtle">Próximo gargalo</p>
            <p className="text-base font-bold text-primary mt-0.5">{bottleneck.nome}</p>
            <p className="text-[12px] text-muted mt-1">
              Peso <span className="text-primary font-semibold">{bottleneck.peso}×</span> ·
              acerto <span className="text-danger font-semibold">{bottleneck.pct_acerto}%</span> ·
              meta <span className="text-primary font-semibold">{bottleneck.meta_acerto_pct}%</span> ·
              gap <span className="text-danger font-semibold">{bottleneck.gap_meta}pp</span>
            </p>
          </div>
        </div>
      ) : total > 0 ? (
        <div className="surface-card p-4 sm:p-5 flex items-center gap-3">
          <TrendingUp size={18} className="text-success" strokeWidth={2} />
          <p className="text-[13px] text-primary">Sem gargalo crítico no momento — todos os blocos com dados estão na meta.</p>
        </div>
      ) : (
        <div className="surface-card p-4 sm:p-5 flex items-center gap-3">
          <MinusCircle size={18} className="text-subtle" strokeWidth={2} />
          <p className="text-[13px] text-muted">Sem tentativas ainda. Responda questões dos dias ou registre simulados para ver métricas.</p>
        </div>
      )}

      <div className="surface-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="text-left text-[10px] uppercase tracking-widest text-subtle border-b" style={{ borderColor: 'var(--surface-border)' }}>
                <th className="px-4 py-3 font-medium">Bloco</th>
                <th className="px-3 py-3 font-medium text-center">Peso</th>
                <th className="px-3 py-3 font-medium">Prio</th>
                <th className="px-3 py-3 font-medium text-right">Tent.</th>
                <th className="px-3 py-3 font-medium text-right">Acerto</th>
                <th className="px-3 py-3 font-medium text-right">Meta</th>
                <th className="px-4 py-3 font-medium">Progresso</th>
                <th className="px-4 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {data.map(b => {
                const prio = PRIO_META[b.prioridade] || PRIO_META.media
                return (
                  <tr key={b.bloco_id} className="border-b" style={{ borderColor: 'var(--surface-border)' }}>
                    <td className="px-4 py-3">
                      <div className="font-medium text-primary">{b.nome}</div>
                      <div className="text-[10px] text-subtle font-mono">{b.slug}</div>
                    </td>
                    <td className="px-3 py-3 text-center text-primary font-mono">{b.peso}×</td>
                    <td className={`px-3 py-3 font-medium ${prio.cls}`}>{prio.label}</td>
                    <td className="px-3 py-3 text-right text-muted font-mono">{b.total_attempts}</td>
                    <td className="px-3 py-3 text-right text-primary font-mono">{b.total_attempts > 0 ? `${b.pct_acerto}%` : '—'}</td>
                    <td className="px-3 py-3 text-right text-subtle font-mono">{b.meta_acerto_pct}%</td>
                    <td className="px-4 py-3 min-w-[120px]">
                      <GapBar pct={b.pct_acerto} meta={b.meta_acerto_pct} />
                    </td>
                    <td className="px-4 py-3"><StatusBadge status={b.status} /></td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
