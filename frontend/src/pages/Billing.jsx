import { useEffect, useState } from 'react'
import { Copy, Check, RefreshCw, AlertTriangle, CheckCircle2 } from 'lucide-react'
import { format, parseISO } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import * as api from '../api'
import { useConcurso } from '../contexts/ConcursoContext'

const STATUS_LABEL = {
  trial:     { label: 'Trial',     cls: 'text-secondary' },
  ativa:     { label: 'Ativa',     cls: 'text-success' },
  expirada:  { label: 'Expirada',  cls: 'text-danger' },
  cancelada: { label: 'Cancelada', cls: 'text-subtle' },
}

function fmtDate(s) {
  if (!s) return '—'
  return format(parseISO(s), "dd 'de' MMM 'de' yyyy", { locale: ptBR })
}

export default function Billing() {
  const { current } = useConcurso()
  const [subs, setSubs] = useState([])
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState(null)
  const [checkout, setCheckout] = useState(null)
  const [requesting, setRequesting] = useState(false)
  const [copied, setCopied] = useState(false)

  async function load() {
    try {
      const r = await api.getMySubscriptions()
      setSubs(r.data)
    } catch (e) {
      setErr(e.response?.data?.detail || 'Erro ao carregar assinaturas')
    } finally {
      setLoading(false)
    }
  }
  useEffect(() => { load() }, [])

  async function startCheckout() {
    if (!current) return
    setRequesting(true); setErr(null)
    try {
      const r = await api.createCheckout(current.id)
      setCheckout(r.data)
    } catch (e) {
      setErr(e.response?.data?.detail || 'Não foi possível criar o pagamento')
    } finally {
      setRequesting(false)
    }
  }

  async function copyCode() {
    if (!checkout?.qr_code) return
    await navigator.clipboard.writeText(checkout.qr_code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (loading) return <p className="text-subtle text-sm animate-pulse">Carregando...</p>

  const subCurrent = current ? subs.find(s => s.concurso_id === current.id) : null

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-2xl sm:text-3xl font-extrabold tracking-tight text-primary">Assinatura</h1>
        <p className="text-[13px] text-subtle mt-1">Status, pagamento e histórico.</p>
      </div>

      {err && (
        <div className="rounded-btn px-4 py-3" style={{ background: 'color-mix(in srgb, var(--color-danger) 10%, transparent)', border: '0.5px solid color-mix(in srgb, var(--color-danger) 35%, transparent)' }}>
          <p className="text-danger text-[13px]">{err}</p>
        </div>
      )}

      {current && subCurrent ? (
        <div className="surface-card p-5 space-y-3">
          <div className="flex items-baseline justify-between flex-wrap gap-2">
            <p className="font-heading text-lg font-bold text-primary">{current.nome}</p>
            <span className={`text-[12px] font-semibold uppercase tracking-wider ${STATUS_LABEL[subCurrent.status]?.cls || ''}`}>
              {STATUS_LABEL[subCurrent.status]?.label || subCurrent.status}
            </span>
          </div>
          <dl className="grid sm:grid-cols-2 gap-x-6 gap-y-1.5 text-[13px]">
            <div className="flex justify-between"><dt className="text-subtle">Tipo</dt><dd className="text-primary font-mono">{subCurrent.tipo}</dd></div>
            <div className="flex justify-between"><dt className="text-subtle">Valor</dt><dd className="text-primary font-mono">R$ {((subCurrent.valor_cents || 0) / 100).toFixed(2)}</dd></div>
            <div className="flex justify-between"><dt className="text-subtle">Trial até</dt><dd className="text-primary">{fmtDate(subCurrent.trial_ate)}</dd></div>
            <div className="flex justify-between"><dt className="text-subtle">Pago em</dt><dd className="text-primary">{fmtDate(subCurrent.paid_at)}</dd></div>
            <div className="flex justify-between"><dt className="text-subtle">Expira em</dt><dd className="text-primary">{fmtDate(subCurrent.expira_em)}</dd></div>
            <div className="flex justify-between"><dt className="text-subtle">Pagamento</dt><dd className="text-primary font-mono">{subCurrent.payment_provider || '—'}</dd></div>
          </dl>

          {subCurrent.status !== 'ativa' && (
            <div className="pt-2">
              {!checkout ? (
                <button
                  onClick={startCheckout}
                  disabled={requesting}
                  className="px-4 py-2 rounded-btn bg-accent hover:bg-accent-hover disabled:opacity-50 text-[13px] font-semibold"
                  style={{ color: 'var(--color-bg)' }}
                >
                  {requesting ? 'Gerando QR Pix...' : `Pagar R$ ${((current.preco_cents || 0) / 100).toFixed(2)} via Pix`}
                </button>
              ) : (
                <div className="space-y-3 pt-2">
                  <div className="surface-input rounded-btn p-3">
                    <p className="text-[11px] font-medium uppercase tracking-widest text-subtle mb-2">Pix Copia e Cola</p>
                    <textarea
                      readOnly
                      value={checkout.qr_code || ''}
                      rows={3}
                      onClick={(e) => e.target.select()}
                      className="w-full bg-transparent text-[11px] text-primary font-mono focus:outline-none resize-none"
                    />
                    <div className="flex items-center gap-2 pt-2">
                      <button onClick={copyCode} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-btn bg-accent hover:bg-accent-hover text-[12px] font-semibold" style={{ color: 'var(--color-bg)' }}>
                        {copied ? <Check size={12} /> : <Copy size={12} />} {copied ? 'Copiado' : 'Copiar'}
                      </button>
                      {checkout.ticket_url && (
                        <a href={checkout.ticket_url} target="_blank" rel="noreferrer" className="text-[12px] text-accent-text hover:underline">Abrir comprovante</a>
                      )}
                    </div>
                  </div>
                  {checkout.qr_code_base64 && (
                    <img
                      alt="QR Pix"
                      src={`data:image/png;base64,${checkout.qr_code_base64}`}
                      className="w-48 h-48 mx-auto rounded-btn bg-white p-2"
                    />
                  )}
                  <p className="text-[12px] text-subtle">
                    Após o pagamento, a confirmação chega via webhook. Esta página atualiza sozinha em até 1 min.
                    <button onClick={load} className="ml-2 inline-flex items-center gap-1 text-accent-text hover:underline">
                      <RefreshCw size={11} /> Atualizar agora
                    </button>
                  </p>
                </div>
              )}
            </div>
          )}

          {subCurrent.status === 'ativa' && (
            <div className="flex items-center gap-2 text-[13px] text-success">
              <CheckCircle2 size={14} /> Acesso liberado até a expiração.
            </div>
          )}
        </div>
      ) : (
        <div className="surface-card p-5">
          <p className="text-[13px] text-muted">Sem assinatura ativa para o concurso atual.</p>
        </div>
      )}

      {subs.length > 1 && (
        <div className="space-y-2">
          <p className="text-[11px] font-medium uppercase tracking-widest text-subtle">Histórico</p>
          {subs.map(s => (
            <div key={s.id} className="surface-card px-4 py-3 flex items-center gap-3 text-[12px]">
              <span className="font-mono text-subtle">{s.tipo}</span>
              <span className={`font-semibold ${STATUS_LABEL[s.status]?.cls || ''}`}>{STATUS_LABEL[s.status]?.label}</span>
              <span className="text-muted">R$ {((s.valor_cents || 0) / 100).toFixed(2)}</span>
              <span className="ml-auto text-subtle font-mono">{fmtDate(s.paid_at || s.trial_ate)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
