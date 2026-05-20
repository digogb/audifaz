import { useEffect, useState } from 'react'
import { Headphones, Copy, RefreshCw, Check, ExternalLink, AlertTriangle, FileUp, Plus, Download, Trash2 } from 'lucide-react'
import * as api from '../api'
import { useAuth } from '../contexts/AuthContext'
import { useConcurso } from '../contexts/ConcursoContext'

function GlassCard({ children, className = '' }) {
  return <div className={`surface-card ${className}`}>{children}</div>
}

function SectionLabel({ children }) {
  return <p className="text-[11px] font-medium text-subtle uppercase tracking-widest mb-3">{children}</p>
}

export default function Config() {
  const [feed, setFeed] = useState(null)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)
  const [regenerating, setRegenerating] = useState(false)
  const [error, setError] = useState(null)

  async function load() {
    setError(null)
    try {
      const res = await api.getPodcastFeed()
      setFeed(res.data)
    } catch (e) {
      if (e.response?.status === 404) {
        setFeed(null)  // ainda não tem token
      } else {
        setError(e.response?.data?.detail || 'Erro ao carregar feed')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function handleRegenerate() {
    if (feed && !confirm('Isso vai invalidar a URL atual nos apps de podcast já assinados. Continuar?')) return
    setRegenerating(true)
    setError(null)
    try {
      const res = await api.regeneratePodcastToken()
      setFeed(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Falha ao gerar token')
    } finally {
      setRegenerating(false)
    }
  }

  async function handleCopy() {
    if (!feed?.feed_url) return
    try {
      await navigator.clipboard.writeText(feed.feed_url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      setError('Falha ao copiar — copie manualmente')
    }
  }

  const isRelativeUrl = feed?.feed_url && !feed.feed_url.startsWith('http')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-primary">Configurações</h1>
        <p className="text-[13px] text-subtle mt-1">Preferências da sua conta</p>
      </div>

      <GlassCard className="p-5 sm:p-6 space-y-4">
        <div className="flex items-center gap-2.5">
          <Headphones size={18} strokeWidth={1.75} className="text-accent-text" />
          <h2 className="font-heading text-base font-bold text-primary">Podcast diário</h2>
        </div>
        <p className="text-[13px] text-muted leading-relaxed">
          Assine este feed RSS no seu app de podcast favorito. Episódios novos aparecem
          automaticamente todo dia depois que o material é gerado.
        </p>

        {loading && <p className="text-[12px] text-subtle animate-pulse">Carregando...</p>}

        {!loading && !feed && (
          <button
            onClick={handleRegenerate}
            disabled={regenerating}
            className="flex items-center gap-2 px-4 py-2 rounded-btn bg-accent hover:bg-accent-hover disabled:opacity-50 text-[13px] font-semibold"
            style={{ color: 'var(--color-bg)' }}
          >
            {regenerating ? <RefreshCw size={13} className="animate-spin" /> : <RefreshCw size={13} />}
            Gerar URL do feed
          </button>
        )}

        {feed && (
          <>
            <SectionLabel>URL do feed</SectionLabel>
            <div className="flex items-stretch gap-2">
              <input
                type="text"
                readOnly
                value={feed.feed_url}
                onClick={(e) => e.target.select()}
                className="surface-input flex-1 rounded-btn px-3 py-2 text-[12px] text-primary font-mono focus:outline-none focus:border-accent"
              />
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 px-3 py-2 rounded-btn bg-accent hover:bg-accent-hover text-[12px] font-semibold transition-colors"
                style={{ color: 'var(--color-bg)' }}
              >
                {copied ? <Check size={12} /> : <Copy size={12} />}
                {copied ? 'Copiado' : 'Copiar'}
              </button>
            </div>

            {isRelativeUrl && (
              <div className="rounded-btn px-3 py-2 flex items-start gap-2"
                   style={{ background: 'color-mix(in srgb, var(--color-danger) 10%, transparent)', border: '0.5px solid color-mix(in srgb, var(--color-danger) 35%, transparent)' }}>
                <AlertTriangle size={12} className="text-danger shrink-0 mt-0.5" />
                <p className="text-[11px] text-danger">
                  URL relativa — apps de podcast precisam de URL absoluta. Defina <code className="font-mono">PUBLIC_BASE_URL</code> no docker-compose e reinicie.
                </p>
              </div>
            )}

            <SectionLabel>Como assinar</SectionLabel>
            <ol className="space-y-1.5 text-[12px] text-muted list-decimal list-inside">
              <li>Copie a URL acima</li>
              <li><strong className="text-primary">Pocket Casts / Overcast / Castro:</strong> Buscar → colar URL</li>
              <li><strong className="text-primary">Apple Podcasts:</strong> Biblioteca → ··· → Seguir um programa por URL</li>
              <li><strong className="text-primary">Spotify:</strong> não suporta RSS privado — use outro app</li>
            </ol>

            <div className="pt-2 flex flex-wrap items-center gap-3">
              <a
                href={feed.feed_url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1.5 text-[12px] text-accent-text hover:underline"
              >
                <ExternalLink size={11} /> Abrir feed (XML)
              </a>
              <button
                onClick={handleRegenerate}
                disabled={regenerating}
                className="surface-input flex items-center gap-1.5 px-3 py-1.5 rounded-btn text-[12px] text-muted hover:text-danger transition-colors"
              >
                <RefreshCw size={11} className={regenerating ? 'animate-spin' : ''} />
                Regenerar token
              </button>
            </div>
          </>
        )}

        {error && (
          <div className="rounded-btn px-3 py-2" style={{ background: 'color-mix(in srgb, var(--color-danger) 10%, transparent)', border: '0.5px solid color-mix(in srgb, var(--color-danger) 35%, transparent)' }}>
            <p className="text-[12px] text-danger">{error}</p>
          </div>
        )}
      </GlassCard>

      <AdminPlanImport />
      <AdminConcursoCreate />
      <DataPrivacyCard />
    </div>
  )
}


function DataPrivacyCard() {
  const { isAdmin } = useAuth()
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)
  const [info, setInfo] = useState(null)

  async function handleExport() {
    setBusy(true); setErr(null); setInfo(null)
    try {
      const res = await api.exportMyData()
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `audifaz-export-${new Date().toISOString().slice(0,10)}.json`
      document.body.appendChild(a); a.click()
      a.remove(); URL.revokeObjectURL(url)
      setInfo('Arquivo baixado.')
    } catch (e) {
      setErr(e.response?.data?.detail || 'Falha ao exportar')
    } finally { setBusy(false) }
  }

  async function handleDelete() {
    const phrase = prompt('Para confirmar, digite EXCLUIR (sem aspas):')
    if (phrase !== 'EXCLUIR') return
    setBusy(true); setErr(null)
    try {
      await api.deleteMyAccount()
      localStorage.clear()
      window.location.href = '/login'
    } catch (e) {
      setErr(e.response?.data?.detail || 'Falha ao excluir')
      setBusy(false)
    }
  }

  return (
    <GlassCard className="p-5 sm:p-6 space-y-4">
      <div className="flex items-center gap-2.5">
        <Download size={18} strokeWidth={1.75} className="text-accent-text" />
        <h2 className="font-heading text-base font-bold text-primary">Dados e privacidade</h2>
      </div>
      <p className="text-[13px] text-muted leading-relaxed">
        Direitos LGPD (art. 18): você pode baixar uma cópia de todos os seus dados ou apagar a conta a qualquer momento.
      </p>

      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={handleExport} disabled={busy}
          className="surface-input flex items-center gap-2 px-4 py-2 rounded-btn text-[12px] font-semibold text-primary hover:bg-accent-soft transition-colors disabled:opacity-50"
        >
          <Download size={13} /> Exportar meus dados (JSON)
        </button>
        {!isAdmin && (
          <button
            onClick={handleDelete} disabled={busy}
            className="flex items-center gap-2 px-4 py-2 rounded-btn text-[12px] font-semibold text-danger hover:bg-accent-soft transition-colors disabled:opacity-50"
            style={{ border: '1px solid color-mix(in srgb, var(--color-danger) 30%, transparent)' }}
          >
            <Trash2 size={13} /> Excluir minha conta
          </button>
        )}
      </div>

      {info && <p className="text-[12px] text-success">{info}</p>}
      {err && <p className="text-[12px] text-danger">{err}</p>}
      {isAdmin && (
        <p className="text-[11px] text-subtle">
          Contas internas (admin) não podem ser excluídas pela API — peça pra remover manualmente no banco.
        </p>
      )}
    </GlassCard>
  )
}


function AdminPlanImport() {
  const { isAdmin } = useAuth()
  const { concursos, refresh } = useConcurso()
  const [concursoId, setConcursoId] = useState('')
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [importing, setImporting] = useState(false)
  const [previewing, setPreviewing] = useState(false)
  const [result, setResult] = useState(null)
  const [err, setErr] = useState(null)

  if (!isAdmin) return null

  async function handlePreview() {
    if (!file || !concursoId) return
    setErr(null); setResult(null); setPreviewing(true)
    try {
      const res = await api.adminPreviewPlano(concursoId, file)
      setPreview(res.data)
    } catch (e) {
      setErr(e.response?.data?.detail || 'Erro no parse')
    } finally {
      setPreviewing(false)
    }
  }

  async function handleImport() {
    if (!file || !concursoId) return
    if (!confirm('Isso apaga todo o plano atual deste concurso (fases/semanas/dias/tópicos). Continuar?')) return
    setErr(null); setImporting(true)
    try {
      const res = await api.adminImportPlano(concursoId, file)
      setResult(res.data)
      setPreview(null)
      await refresh()
    } catch (e) {
      setErr(e.response?.data?.detail || 'Erro ao importar')
    } finally {
      setImporting(false)
    }
  }

  return (
    <GlassCard className="p-5 sm:p-6 space-y-4">
      <div className="flex items-center gap-2.5">
        <FileUp size={18} strokeWidth={1.75} className="text-text-blue" />
        <h2 className="text-base font-bold text-primary">Importar plano (admin)</h2>
      </div>
      <p className="text-[13px] text-muted leading-relaxed">
        Faz upload de um plano em markdown (formato SEFAZ ou TJCE) e substitui Phase/Week/StudyDay/Topic do concurso escolhido.
      </p>

      <SectionLabel>Concurso destino</SectionLabel>
      <select
        value={concursoId}
        onChange={(e) => { setConcursoId(e.target.value); setPreview(null); setResult(null) }}
        className="surface-input w-full rounded-btn px-3 py-2 text-[13px] text-primary focus:outline-none focus:border-accent"
      >
        <option value="">— escolha —</option>
        {concursos.map(c => (
          <option key={c.id} value={c.id} className="bg-zinc-900">{c.slug} · {c.nome}</option>
        ))}
      </select>

      <SectionLabel>Arquivo .md</SectionLabel>
      <input
        type="file"
        accept=".md,text/markdown,text/plain"
        onChange={(e) => { setFile(e.target.files?.[0] || null); setPreview(null); setResult(null) }}
        className="text-[12px] text-muted file:mr-3 file:py-1.5 file:px-3 file:rounded-btn file:border-0 file:bg-accent-soft file:text-primary file:text-[12px] file:cursor-pointer hover:file:bg-accent-soft"
      />

      <div className="flex flex-wrap gap-2 pt-2">
        <button
          onClick={handlePreview}
          disabled={!file || !concursoId || previewing}
          className="px-4 py-2 rounded-btn bg-accent-soft hover:bg-accent-hover disabled:opacity-40 text-primary text-[12px] font-semibold transition-colors"
        >
          {previewing ? 'Analisando...' : 'Pré-visualizar'}
        </button>
        <button
          onClick={handleImport}
          disabled={!file || !concursoId || importing}
          className="px-4 py-2 rounded-btn bg-accent hover:bg-accent-hover disabled:opacity-40 text-primary text-[12px] font-semibold transition-colors"
        >
          {importing ? 'Importando...' : 'Importar (substitui plano atual)'}
        </button>
      </div>

      {preview && (
        <div className="rounded-btn px-3 py-2 text-[12px] text-muted">
          <p className="font-mono">
            formato: <span className="text-text-blue">{preview.formato}</span> ·
            fases: <span className="text-primary">{preview.fases}</span> ·
            semanas: <span className="text-primary">{preview.semanas}</span> ·
            dias: <span className="text-primary">{preview.dias}</span> ·
            tópicos: <span className="text-primary">{preview.topicos}</span>
          </p>
          {preview.primeira_semana && (
            <p className="text-[11px] text-subtle mt-1">
              1ª semana: S{preview.primeira_semana.numero} ({preview.primeira_semana.inicio} → {preview.primeira_semana.fim}) — {preview.primeira_semana.tema}
            </p>
          )}
        </div>
      )}

      {result && (
        <div className="rounded-btn px-3 py-2 text-[12px] text-primary" style={{ background: 'rgba(122,199,127,0.10)', border: '0.5px solid rgba(122,199,127,0.35)' }}>
          ✓ Importado: {result.phases} fases · {result.weeks} semanas · {result.days} dias · {result.topics} tópicos
        </div>
      )}

      {err && (
        <div className="rounded-btn px-3 py-2" style={{ background: 'rgba(212,132,90,0.10)', border: '0.5px solid rgba(212,132,90,0.35)' }}>
          <p className="text-[12px] text-accent-orange">{err}</p>
        </div>
      )}
    </GlassCard>
  )
}


function AdminConcursoCreate() {
  const { isAdmin } = useAuth()
  const { refresh } = useConcurso()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({
    slug: '', nome: '', banca: 'FCC', orgao: '', cargo: '',
    data_prova: '', descricao: '', edital_url: '', publico: false,
  })
  const [saving, setSaving] = useState(false)
  const [err, setErr] = useState(null)
  const [ok, setOk] = useState(null)

  if (!isAdmin) return null

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true); setErr(null); setOk(null)
    try {
      const payload = { ...form, data_prova: form.data_prova || null }
      Object.keys(payload).forEach(k => { if (payload[k] === '') payload[k] = null })
      const res = await api.adminCreateConcurso(payload)
      setOk(`Criado: ${res.data.slug} (id=${res.data.id})`)
      setForm({ slug: '', nome: '', banca: 'FCC', orgao: '', cargo: '', data_prova: '', descricao: '', edital_url: '', publico: false })
      await refresh()
    } catch (e) {
      setErr(e.response?.data?.detail || 'Erro')
    } finally {
      setSaving(false)
    }
  }

  return (
    <GlassCard className="p-5 sm:p-6 space-y-3">
      <button onClick={() => setOpen(o => !o)} className="flex items-center gap-2.5 w-full text-left">
        <Plus size={18} strokeWidth={1.75} className="text-text-blue" />
        <h2 className="text-base font-bold text-primary">Criar concurso (admin)</h2>
        <span className="ml-auto text-[11px] text-subtle">{open ? 'fechar' : 'abrir'}</span>
      </button>

      {open && (
        <form onSubmit={handleSubmit} className="space-y-3 pt-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {[
              ['slug', 'slug (ex: tjce-2026)', true],
              ['nome', 'nome completo', true],
              ['banca', 'banca', true],
              ['orgao', 'órgão', true],
              ['cargo', 'cargo', true],
              ['data_prova', 'data prova (YYYY-MM-DD)', false],
              ['edital_url', 'url do edital', false],
            ].map(([k, label, required]) => (
              <input
                key={k}
                required={required}
                placeholder={label}
                value={form[k]}
                onChange={e => setForm(f => ({ ...f, [k]: e.target.value }))}
                className="surface-input rounded-btn px-3 py-2 text-[12px] text-primary focus:outline-none focus:border-accent"
              />
            ))}
          </div>
          <textarea
            placeholder="descrição (opcional)"
            value={form.descricao}
            onChange={e => setForm(f => ({ ...f, descricao: e.target.value }))}
            rows={2}
            className="surface-input w-full rounded-btn px-3 py-2 text-[12px] text-primary focus:outline-none focus:border-accent"
          />
          <label className="flex items-center gap-2 text-[12px] text-muted">
            <input type="checkbox" checked={form.publico} onChange={e => setForm(f => ({ ...f, publico: e.target.checked }))} />
            Listar no catálogo público (/concursos/disponiveis)
          </label>
          <button
            type="submit"
            disabled={saving}
            className="px-4 py-2 rounded-btn bg-accent hover:bg-accent-hover disabled:opacity-40 text-primary text-[12px] font-semibold"
          >
            {saving ? 'Salvando...' : 'Criar concurso'}
          </button>
          {ok && <p className="text-[12px] text-accent-green">{ok}</p>}
          {err && <p className="text-[12px] text-accent-orange">{err}</p>}
        </form>
      )}
    </GlassCard>
  )
}
