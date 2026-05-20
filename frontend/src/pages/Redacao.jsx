import { useEffect, useMemo, useState } from 'react'
import {
  PenLine, BookOpen, Send, Trash2, RefreshCw, ChevronLeft,
  CheckCircle2, AlertTriangle, MinusCircle,
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { format, parseISO } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import * as api from '../api'

const CRITERIOS = [
  { key: 'nota_recorte',        max: 2.0, label: 'Recorte temático' },
  { key: 'nota_interpretacao',  max: 2.0, label: 'Interpretação dos textos' },
  { key: 'nota_progressao',     max: 3.0, label: 'Progressão textual' },
  { key: 'nota_vocabular',      max: 0.8, label: 'Vocabulário' },
  { key: 'nota_coesao',         max: 1.6, label: 'Coesão' },
  { key: 'nota_morfo',          max: 0.6, label: 'Morfossintaxe' },
]

const STATUS_META = {
  pendente:  { label: 'Aguardando',  cls: 'text-subtle',     Icon: MinusCircle },
  corrigindo:{ label: 'Corrigindo',  cls: 'text-secondary',  Icon: RefreshCw },
  done:      { label: 'Corrigida',   cls: 'text-success',    Icon: CheckCircle2 },
  erro:      { label: 'Erro',        cls: 'text-danger',     Icon: AlertTriangle },
}

function StatusBadge({ status }) {
  const m = STATUS_META[status] || STATUS_META.pendente
  const Icon = m.Icon
  return (
    <span className={`inline-flex items-center gap-1 text-[11px] font-medium ${m.cls}`}>
      <Icon size={12} strokeWidth={2} className={status === 'corrigindo' ? 'animate-spin' : ''} />
      {m.label}
    </span>
  )
}

function CriterioBar({ valor, max }) {
  const pct = max > 0 ? Math.max(0, Math.min(100, (valor / max) * 100)) : 0
  return (
    <div className="w-full h-1 rounded-full overflow-hidden bg-accent-soft">
      <div className="h-full bg-accent transition-all" style={{ width: `${pct}%` }} />
    </div>
  )
}

function TemaList({ temas, onSelect }) {
  if (temas.length === 0) {
    return (
      <div className="surface-card p-6 text-center">
        <p className="text-[13px] text-muted">Nenhum tema disponível ainda para este concurso.</p>
      </div>
    )
  }
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {temas.map(t => (
        <button
          key={t.id}
          onClick={() => onSelect(t)}
          className="surface-card p-4 text-left hover:bg-accent-soft transition-colors"
        >
          <div className="flex items-start gap-3">
            <BookOpen size={16} className="text-accent-text shrink-0 mt-0.5" strokeWidth={1.75} />
            <div className="min-w-0">
              <p className="font-heading text-[14px] font-semibold text-primary leading-snug">{t.titulo}</p>
              <p className="text-[11px] text-subtle mt-1 line-clamp-2">{t.enunciado_md.replace(/[*_]/g, '').slice(0, 140)}</p>
            </div>
          </div>
        </button>
      ))}
    </div>
  )
}

function Editor({ tema, onCancel, onSubmitted }) {
  const [texto, setTexto] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [err, setErr] = useState(null)

  const linhasContent = useMemo(
    () => texto.split('\n').filter(ln => ln.trim()).length,
    [texto],
  )
  const linesColor =
    linhasContent === 0 ? 'text-subtle' :
    linhasContent <= 7 ? 'text-danger' :
    linhasContent < 20 ? 'text-secondary' :
    linhasContent <= 30 ? 'text-success' :
    'text-secondary'

  async function handleSubmit() {
    setErr(null); setSubmitting(true)
    try {
      const res = await api.submitRedacao(tema.id, texto)
      onSubmitted(res.data)
    } catch (e) {
      setErr(e.response?.data?.detail || 'Erro ao submeter')
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-4">
      <button onClick={onCancel} className="flex items-center gap-1.5 text-[12px] text-muted hover:text-primary transition-colors">
        <ChevronLeft size={13} /> Trocar tema
      </button>

      <div className="surface-card p-4 sm:p-5 space-y-3">
        <div className="flex items-start gap-2.5">
          <BookOpen size={18} className="text-accent-text shrink-0 mt-0.5" strokeWidth={1.75} />
          <h2 className="font-heading text-base font-bold text-primary">{tema.titulo}</h2>
        </div>
        <div className="prose-study text-[13px]">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{tema.enunciado_md}</ReactMarkdown>
        </div>
        {tema.textos_apoio_md && (
          <details className="text-[13px]">
            <summary className="cursor-pointer text-accent-text font-medium">Ver textos de apoio</summary>
            <div className="prose-study mt-2">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{tema.textos_apoio_md}</ReactMarkdown>
            </div>
          </details>
        )}
      </div>

      <div className="surface-card p-4 sm:p-5 space-y-3">
        <div className="flex items-center justify-between gap-2">
          <p className="text-[11px] font-medium text-subtle uppercase tracking-widest">Seu texto</p>
          <p className={`text-[12px] font-mono ${linesColor}`}>
            {linhasContent} {linhasContent === 1 ? 'linha' : 'linhas'} (alvo 20–30)
          </p>
        </div>
        <textarea
          value={texto}
          onChange={e => setTexto(e.target.value)}
          rows={20}
          placeholder="Escreva sua redação aqui. Texto dissertativo-argumentativo: introdução com tese clara, dois parágrafos de desenvolvimento e conclusão com proposta de intervenção articulada."
          className="surface-input w-full rounded-btn px-3 py-2.5 text-[13px] text-primary placeholder:text-subtle focus:outline-none focus:border-accent leading-relaxed font-mono"
        />
        {err && (
          <div className="rounded-btn px-3 py-2" style={{ background: 'color-mix(in srgb, var(--color-danger) 10%, transparent)', border: '0.5px solid color-mix(in srgb, var(--color-danger) 35%, transparent)' }}>
            <p className="text-[12px] text-danger">{err}</p>
          </div>
        )}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleSubmit}
            disabled={submitting || !texto.trim()}
            className="flex items-center gap-2 px-4 py-2 rounded-btn bg-accent hover:bg-accent-hover disabled:opacity-50 text-[13px] font-semibold transition-colors"
            style={{ color: 'var(--color-bg)' }}
          >
            {submitting ? <RefreshCw size={13} className="animate-spin" /> : <Send size={13} />}
            {submitting ? 'Enviando...' : 'Submeter para correção'}
          </button>
          <p className="text-[11px] text-subtle">~30s. Você pode fechar o app.</p>
        </div>
      </div>
    </div>
  )
}

function CorrecaoView({ redacao, onBack, onDeleted, refresh }) {
  const [poll, setPoll] = useState(0)
  useEffect(() => {
    if (redacao.status === 'done' || redacao.status === 'erro') return
    const t = setInterval(() => setPoll(p => p + 1), 3500)
    return () => clearInterval(t)
  }, [redacao.status])
  useEffect(() => { if (poll > 0) refresh() }, [poll]) // eslint-disable-line

  async function handleDelete() {
    if (!confirm('Apagar esta redação?')) return
    await api.deleteRedacao(redacao.id)
    onDeleted()
  }

  return (
    <div className="space-y-4">
      <button onClick={onBack} className="flex items-center gap-1.5 text-[12px] text-muted hover:text-primary transition-colors">
        <ChevronLeft size={13} /> Voltar
      </button>

      <div className="surface-card p-4 sm:p-5 space-y-2">
        <p className="text-[11px] font-medium uppercase tracking-widest text-subtle">Tema</p>
        <h1 className="font-heading text-lg sm:text-xl font-bold text-primary">{redacao.tema_titulo_snapshot}</h1>
        <div className="flex flex-wrap items-center gap-3 pt-1">
          <StatusBadge status={redacao.status} />
          <span className="text-[12px] text-subtle font-mono">{redacao.num_linhas} linhas</span>
          <span className="text-[11px] text-subtle font-mono">
            {format(parseISO(redacao.criado_em), "dd/MM HH:mm", { locale: ptBR })}
          </span>
          <button
            onClick={handleDelete}
            className="ml-auto inline-flex items-center gap-1 text-[11px] text-subtle hover:text-danger transition-colors"
          >
            <Trash2 size={11} /> Apagar
          </button>
        </div>
      </div>

      {redacao.status === 'erro' && (
        <div className="rounded-btn px-4 py-3" style={{ background: 'color-mix(in srgb, var(--color-danger) 10%, transparent)', border: '0.5px solid color-mix(in srgb, var(--color-danger) 35%, transparent)' }}>
          <p className="text-[13px] text-danger">{redacao.error_msg || 'Falha na correção'}</p>
        </div>
      )}

      {redacao.status === 'done' && (
        <>
          <div className="surface-card p-4 sm:p-5">
            <div className="flex items-baseline gap-3">
              <p className="font-heading text-4xl sm:text-5xl font-extrabold text-accent-text">
                {redacao.nota_total?.toFixed(1)}
              </p>
              <p className="text-[13px] text-subtle font-mono">/ 10,0</p>
              {redacao.zerou_motivo && (
                <p className="text-[12px] text-danger ml-2">(zerada: {redacao.zerou_motivo})</p>
              )}
            </div>
            <div className="grid sm:grid-cols-2 gap-3 mt-4">
              {CRITERIOS.map(c => {
                const valor = redacao[c.key] ?? 0
                return (
                  <div key={c.key} className="space-y-1">
                    <div className="flex items-baseline justify-between text-[12px]">
                      <span className="text-muted">{c.label}</span>
                      <span className="font-mono text-primary">{valor.toFixed(2)} <span className="text-subtle">/ {c.max.toFixed(1)}</span></span>
                    </div>
                    <CriterioBar valor={valor} max={c.max} />
                  </div>
                )
              })}
            </div>
          </div>

          {redacao.feedback_geral && (
            <div className="surface-card p-4 sm:p-5">
              <p className="text-[11px] font-medium uppercase tracking-widest text-subtle mb-2">Parecer geral</p>
              <p className="text-[13px] text-primary leading-relaxed whitespace-pre-wrap">{redacao.feedback_geral}</p>
            </div>
          )}

          {redacao.sugestoes && redacao.sugestoes.length > 0 && (
            <div className="surface-card p-4 sm:p-5 space-y-3">
              <p className="text-[11px] font-medium uppercase tracking-widest text-subtle">Pontos para revisar</p>
              {redacao.sugestoes.map((s, i) => (
                <div key={i} className="surface-input rounded-btn p-3 space-y-1.5">
                  <div className="flex items-baseline gap-2 flex-wrap">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-accent-text">{s.categoria}</span>
                  </div>
                  <p className="text-[12px] text-muted italic">&ldquo;{s.trecho}&rdquo;</p>
                  <p className="text-[12px] text-primary"><span className="text-danger font-semibold">Problema:</span> {s.problema}</p>
                  <p className="text-[12px] text-primary"><span className="text-success font-semibold">Sugestão:</span> {s.sugestao}</p>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      <div className="surface-card p-4 sm:p-5">
        <p className="text-[11px] font-medium uppercase tracking-widest text-subtle mb-2">Texto submetido</p>
        <pre className="text-[13px] text-primary whitespace-pre-wrap font-sans leading-relaxed">{redacao.texto}</pre>
      </div>
    </div>
  )
}

export default function Redacao() {
  const [temas, setTemas] = useState([])
  const [redacoes, setRedacoes] = useState([])
  const [selectedTema, setSelectedTema] = useState(null)
  const [viewing, setViewing] = useState(null)  // redacao_id selecionada
  const [viewingData, setViewingData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState(null)

  async function loadAll() {
    setErr(null)
    try {
      const [t, r] = await Promise.all([api.getRedacaoTemas(), api.listRedacoes()])
      setTemas(t.data); setRedacoes(r.data)
    } catch (e) {
      setErr(e.response?.data?.detail || 'Erro ao carregar')
    } finally {
      setLoading(false)
    }
  }
  useEffect(() => { loadAll() }, [])

  async function loadRedacao(id) {
    try {
      const res = await api.getRedacao(id)
      setViewingData(res.data)
    } catch {
      setViewingData(null)
    }
  }
  useEffect(() => {
    if (viewing) loadRedacao(viewing)
    else setViewingData(null)
  }, [viewing])

  if (loading) return <p className="text-subtle text-sm animate-pulse">Carregando...</p>
  if (err) return <p className="text-danger text-sm">{err}</p>

  if (viewing && viewingData) {
    return (
      <CorrecaoView
        redacao={viewingData}
        onBack={() => { setViewing(null); loadAll() }}
        onDeleted={() => { setViewing(null); loadAll() }}
        refresh={() => loadRedacao(viewing)}
      />
    )
  }

  if (selectedTema) {
    return (
      <Editor
        tema={selectedTema}
        onCancel={() => setSelectedTema(null)}
        onSubmitted={r => {
          setSelectedTema(null)
          setViewing(r.id)
          loadAll()
        }}
      />
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-3">
        <PenLine size={22} className="text-accent-text shrink-0 mt-1" strokeWidth={1.75} />
        <div>
          <h1 className="font-heading text-2xl sm:text-3xl font-extrabold tracking-tight text-primary">Redação</h1>
          <p className="text-[13px] text-subtle mt-1">
            Escreva sobre um dos temas e receba correção automática segundo a rubrica FCC.
          </p>
        </div>
      </div>

      {redacoes.length > 0 && (
        <div className="space-y-2">
          <p className="text-[11px] font-medium uppercase tracking-widest text-subtle">Minhas redações</p>
          <div className="space-y-1.5">
            {redacoes.map(r => (
              <button
                key={r.id}
                onClick={() => setViewing(r.id)}
                className="surface-card w-full text-left px-4 py-3 hover:bg-accent-soft transition-colors flex items-center gap-3"
              >
                <div className="min-w-0 flex-1">
                  <p className="text-[13px] font-medium text-primary truncate">{r.tema_titulo_snapshot}</p>
                  <p className="text-[11px] text-subtle font-mono mt-0.5">
                    {format(parseISO(r.criado_em), "dd/MM HH:mm", { locale: ptBR })} · {r.num_linhas} linhas
                  </p>
                </div>
                {r.nota_total !== null && r.nota_total !== undefined && (
                  <p className="font-heading text-lg font-bold text-accent-text shrink-0">{r.nota_total.toFixed(1)}</p>
                )}
                <StatusBadge status={r.status} />
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-2">
        <p className="text-[11px] font-medium uppercase tracking-widest text-subtle">Temas disponíveis</p>
        <TemaList temas={temas} onSelect={setSelectedTema} />
      </div>
    </div>
  )
}
