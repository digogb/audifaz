import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { format, parseISO, isSameDay } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import {
  ChevronDown, ChevronRight, CalendarDays, CheckCircle2,
  CircleDot, Lock, Target,
} from 'lucide-react'
import * as api from '../api'

const STATUS_CLS = {
  pendente: 'text-subtle',
  em_andamento: 'text-secondary',
  concluido: 'text-accent-text',
}

const TIPO_CLS = {
  util: 'text-muted',
  sabado: 'text-accent-text',
  domingo: 'text-accent-text',
  feriado: 'text-danger',
  prova: 'text-danger font-bold',
}

function StatusDot({ status }) {
  if (status === 'concluido') return <CheckCircle2 size={14} className="text-accent-text" strokeWidth={2} />
  if (status === 'em_andamento') return <CircleDot size={14} className="text-secondary" strokeWidth={2} />
  return <span className="inline-block w-3.5 h-3.5 rounded-full border border-subtle" />
}

function ProgressBar({ pct }) {
  const w = Math.max(0, Math.min(100, pct))
  return (
    <div className="w-full h-1 rounded-full overflow-hidden bg-accent-soft">
      <div className="h-full bg-accent transition-all" style={{ width: `${w}%` }} />
    </div>
  )
}

function DiaCard({ dia, isToday, onClick }) {
  const tipoCls = TIPO_CLS[dia.tipo] || TIPO_CLS.util
  const statusCls = STATUS_CLS[dia.status] || STATUS_CLS.pendente
  const dateLabel = format(parseISO(dia.data), "EEE, dd 'de' MMM", { locale: ptBR })

  return (
    <button
      onClick={onClick}
      className={`surface-card text-left w-full p-3 sm:p-4 hover:bg-accent-soft transition-colors ${
        isToday ? 'ring-1 ring-accent' : ''
      }`}
    >
      <div className="flex items-start gap-3">
        <div className="pt-0.5">
          <StatusDot status={dia.status} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-baseline gap-2 flex-wrap">
            <span className="font-mono text-[12px] text-primary font-semibold capitalize">{dateLabel}</span>
            <span className={`text-[10px] uppercase tracking-wider ${tipoCls}`}>{dia.tipo}</span>
            {isToday && <span className="text-[10px] uppercase tracking-wider text-accent font-bold">hoje</span>}
            <span className="ml-auto text-[11px] font-mono text-subtle">
              {dia.topics_done}/{dia.topics_total} tópicos
            </span>
          </div>
          {dia.topicos.length > 0 && (
            <ul className="mt-2 space-y-1">
              {dia.topicos.map(t => (
                <li
                  key={t.id}
                  className={`text-[12px] leading-snug flex items-start gap-1.5 ${
                    t.concluido ? 'text-subtle line-through' : 'text-muted'
                  }`}
                >
                  <span className="text-subtle shrink-0">·</span>
                  <span className="flex-1">{t.descricao}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </button>
  )
}

function SemanaBlock({ semana, today, onPickDia }) {
  const [open, setOpen] = useState(() => {
    const ini = parseISO(semana.data_inicio)
    const fim = parseISO(semana.data_fim)
    return today >= ini && today <= fim
  })
  const dias = semana.dias
  const totalTopicos = dias.reduce((s, d) => s + d.topics_total, 0)
  const doneTopicos = dias.reduce((s, d) => s + d.topics_done, 0)
  const pct = totalTopicos > 0 ? Math.round((doneTopicos / totalTopicos) * 100) : 0

  const sini = format(parseISO(semana.data_inicio), "dd/MM")
  const sfim = format(parseISO(semana.data_fim), "dd/MM")

  return (
    <div className="space-y-2">
      <button
        onClick={() => setOpen(o => !o)}
        className="surface-input w-full flex items-center gap-2 px-3 py-2 rounded-btn text-left hover:bg-accent-soft transition-colors"
      >
        {open ? <ChevronDown size={14} className="text-subtle shrink-0" /> : <ChevronRight size={14} className="text-subtle shrink-0" />}
        <span className="text-[12px] font-mono text-accent-text font-semibold shrink-0">Semana {semana.numero}</span>
        <span className="text-[12px] text-primary truncate">{semana.tema}</span>
        <span className="ml-auto text-[11px] text-subtle font-mono shrink-0">{sini}–{sfim}</span>
        <span className="text-[11px] font-mono text-primary shrink-0">{pct}%</span>
      </button>

      {open && (
        <div className="pl-2 sm:pl-4 space-y-2">
          {dias.map(d => (
            <DiaCard
              key={d.id}
              dia={d}
              isToday={isSameDay(parseISO(d.data), today)}
              onClick={() => onPickDia(d)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function FaseBlock({ fase, today, onPickDia }) {
  const [open, setOpen] = useState(true)

  return (
    <div className="space-y-3">
      <button
        onClick={() => setOpen(o => !o)}
        className="surface-card w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-accent-soft transition-colors"
      >
        {open ? <ChevronDown size={16} className="text-accent-text shrink-0" /> : <ChevronRight size={16} className="text-accent-text shrink-0" />}
        <div className="min-w-0 flex-1">
          <p className="font-heading text-[15px] font-bold text-primary">
            <span className="text-accent-text">Fase {fase.numero}</span> · {fase.nome}
          </p>
          <p className="text-[11px] text-subtle font-mono mt-0.5">
            {fase.done_days}/{fase.total_days} dias · {fase.pct}% concluído
          </p>
        </div>
        <div className="w-24 sm:w-32 shrink-0">
          <ProgressBar pct={fase.pct} />
        </div>
      </button>

      {open && (
        <div className="pl-2 sm:pl-6 space-y-3">
          {fase.semanas.map(w => (
            <SemanaBlock key={w.numero} semana={w} today={today} onPickDia={onPickDia} />
          ))}
        </div>
      )}
    </div>
  )
}

export default function Plano() {
  const [data, setData] = useState(null)
  const [err, setErr] = useState(null)
  const navigate = useNavigate()
  const today = useMemo(() => new Date(), [])

  useEffect(() => {
    api.getPlano()
      .then(r => setData(r.data))
      .catch(e => setErr(e.response?.data?.detail || 'Erro ao carregar plano'))
  }, [])

  function pickDia(d) {
    const todayStr = format(today, 'yyyy-MM-dd')
    if (d.data === todayStr) navigate('/')
    else navigate(`/?data=${d.data}`)
  }

  if (err) return <p className="text-danger text-sm">{err}</p>
  if (!data) return <p className="text-subtle text-sm animate-pulse">Carregando plano...</p>

  const totalDias = data.fases.reduce((s, f) => s + f.total_days, 0)
  const doneDias = data.fases.reduce((s, f) => s + f.done_days, 0)
  const pctGeral = totalDias > 0 ? Math.round((doneDias / totalDias) * 100) : 0

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-3">
        <CalendarDays size={22} className="text-accent-text shrink-0 mt-1" strokeWidth={1.75} />
        <div className="min-w-0">
          <h1 className="font-heading text-2xl sm:text-3xl font-extrabold tracking-tight text-primary">Plano de Estudos</h1>
          <p className="text-[13px] text-subtle mt-1">
            Visão completa do percurso. O conteúdo aprofundado (material, questões, áudio) está em cada dia.
          </p>
        </div>
      </div>

      <div className="surface-card p-4 sm:p-5 flex items-center gap-4">
        <Target size={18} className="text-accent shrink-0" strokeWidth={2} />
        <div className="min-w-0 flex-1">
          <p className="text-[11px] uppercase tracking-widest text-subtle">Progresso geral</p>
          <p className="text-[13px] text-primary mt-0.5">
            <span className="font-bold">{doneDias}</span> de <span className="font-bold">{totalDias}</span> dias concluídos
          </p>
        </div>
        <span className="font-heading text-2xl font-bold text-accent-text font-mono">{pctGeral}%</span>
      </div>

      <div className="space-y-5">
        {data.fases.map(f => (
          <FaseBlock key={f.numero} fase={f} today={today} onPickDia={pickDia} />
        ))}
      </div>

      <div
        className="rounded-btn p-3 flex items-start gap-2"
        style={{ background: 'var(--input-bg)', border: 'var(--input-border)' }}
      >
        <Lock size={12} className="text-subtle shrink-0 mt-0.5" strokeWidth={2} />
        <p className="text-[11px] text-subtle leading-relaxed">
          Clique em qualquer dia para acessar o conteúdo aprofundado: material gerado, questões, áudio do podcast e, quando disponível, redação.
        </p>
      </div>
    </div>
  )
}
