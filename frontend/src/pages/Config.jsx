import { useEffect, useState } from 'react'
import { Headphones, Copy, RefreshCw, Check, ExternalLink, AlertTriangle } from 'lucide-react'
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
  return <p className="text-[11px] font-medium text-white/40 uppercase tracking-widest mb-3">{children}</p>
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
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">Configurações</h1>
        <p className="text-[13px] text-white/40 mt-1">Preferências da sua conta</p>
      </div>

      <GlassCard className="p-5 sm:p-6 space-y-4">
        <div className="flex items-center gap-2.5">
          <Headphones size={18} strokeWidth={1.75} className="text-text-blue" />
          <h2 className="text-base font-bold text-white">Podcast diário</h2>
        </div>
        <p className="text-[13px] text-white/60 leading-relaxed">
          Assine este feed RSS no seu app de podcast favorito. Episódios novos aparecem
          automaticamente todo dia depois que o material é gerado.
        </p>

        {loading && <p className="text-[12px] text-white/40 animate-pulse">Carregando...</p>}

        {!loading && !feed && (
          <button
            onClick={handleRegenerate}
            disabled={regenerating}
            className="flex items-center gap-2 px-4 py-2 rounded-btn bg-accent-blue hover:bg-accent-blue/90 disabled:opacity-50 text-white text-[13px] font-semibold"
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
                className="flex-1 rounded-btn px-3 py-2 text-[12px] text-white/85 font-mono focus:outline-none focus:border-accent-blue"
                style={{ background: 'rgba(255,255,255,0.04)', border: '0.5px solid rgba(255,255,255,0.12)' }}
              />
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 px-3 py-2 rounded-btn bg-accent-blue hover:bg-accent-blue/90 text-white text-[12px] font-semibold transition-colors"
              >
                {copied ? <Check size={12} /> : <Copy size={12} />}
                {copied ? 'Copiado' : 'Copiar'}
              </button>
            </div>

            {isRelativeUrl && (
              <div className="rounded-btn px-3 py-2 flex items-start gap-2"
                   style={{ background: 'rgba(212,132,90,0.10)', border: '0.5px solid rgba(212,132,90,0.35)' }}>
                <AlertTriangle size={12} className="text-accent-orange shrink-0 mt-0.5" />
                <p className="text-[11px] text-accent-orange">
                  URL relativa — apps de podcast precisam de URL absoluta. Defina <code className="font-mono">PUBLIC_BASE_URL</code> no docker-compose e reinicie.
                </p>
              </div>
            )}

            <SectionLabel>Como assinar</SectionLabel>
            <ol className="space-y-1.5 text-[12px] text-white/60 list-decimal list-inside">
              <li>Copie a URL acima</li>
              <li><strong className="text-white/80">Pocket Casts / Overcast / Castro:</strong> Buscar → colar URL</li>
              <li><strong className="text-white/80">Apple Podcasts:</strong> Biblioteca → ··· → Seguir um programa por URL</li>
              <li><strong className="text-white/80">Spotify:</strong> não suporta RSS privado — use outro app</li>
            </ol>

            <div className="pt-2 flex flex-wrap items-center gap-3">
              <a
                href={feed.feed_url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1.5 text-[12px] text-text-blue hover:underline"
              >
                <ExternalLink size={11} /> Abrir feed (XML)
              </a>
              <button
                onClick={handleRegenerate}
                disabled={regenerating}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-btn text-[12px] text-white/60 hover:text-accent-orange transition-colors"
                style={{ border: '0.5px solid rgba(255,255,255,0.12)' }}
              >
                <RefreshCw size={11} className={regenerating ? 'animate-spin' : ''} />
                Regenerar token
              </button>
            </div>
          </>
        )}

        {error && (
          <div className="rounded-btn px-3 py-2" style={{ background: 'rgba(212,132,90,0.10)', border: '0.5px solid rgba(212,132,90,0.35)' }}>
            <p className="text-[12px] text-accent-orange">{error}</p>
          </div>
        )}
      </GlassCard>
    </div>
  )
}
