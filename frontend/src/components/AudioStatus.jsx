import { useEffect, useState, useRef } from 'react'
import { Headphones, Download, RefreshCw, Sparkles, AlertTriangle } from 'lucide-react'
import * as api from '../api'
import { useAuth } from '../contexts/AuthContext'

const glass = {
  background: 'rgba(255,255,255,0.05)',
  border: '0.5px solid rgba(255,255,255,0.10)',
  backdropFilter: 'blur(12px)',
  WebkitBackdropFilter: 'blur(12px)',
}

function formatDuration(seconds) {
  if (!seconds) return ''
  const m = Math.floor(seconds / 60)
  const s = String(seconds % 60).padStart(2, '0')
  return `${m}:${s}`
}

function formatBytes(b) {
  if (!b) return ''
  const mb = b / (1024 * 1024)
  return `${mb.toFixed(1)} MB`
}

export default function AudioStatus({ dayId, materialReady }) {
  const { isAdmin } = useAuth()
  const [audio, setAudio] = useState(null)
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState(false)
  const [error, setError] = useState(null)
  const pollRef = useRef(null)

  async function load() {
    try {
      const res = await api.getAudio(dayId)
      setAudio(res.data)
    } catch {
      setAudio(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!dayId) return
    setLoading(true)
    load()
  }, [dayId])

  useEffect(() => {
    const polling = audio?.status === 'pendente' || audio?.status === 'gerando'
    if (!polling) {
      clearInterval(pollRef.current)
      return
    }
    pollRef.current = setInterval(load, 15000)
    return () => clearInterval(pollRef.current)
  }, [audio?.status])

  async function handleTrigger() {
    setTriggering(true)
    setError(null)
    try {
      const res = await api.generateAudio(dayId)
      setAudio(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Falha ao iniciar geração')
    } finally {
      setTriggering(false)
    }
  }

  if (loading || !materialReady) return null

  // Sem áudio ainda
  if (!audio) {
    if (!isAdmin) {
      return (
        <div className="rounded-card px-4 py-3 flex items-center gap-3" style={glass}>
          <Headphones size={15} strokeWidth={1.75} className="text-white/40" />
          <p className="text-[12px] text-white/50">Podcast será gerado em breve</p>
        </div>
      )
    }
    return (
      <div className="rounded-card px-4 py-3 flex items-center justify-between gap-3 flex-wrap" style={glass}>
        <div className="flex items-center gap-2">
          <Headphones size={15} strokeWidth={1.75} className="text-text-blue" />
          <p className="text-[12px] text-white/70">Podcast deste dia ainda não foi gerado</p>
        </div>
        <button
          onClick={handleTrigger}
          disabled={triggering}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-btn bg-accent-blue hover:bg-accent-blue/90 disabled:opacity-50 text-white text-[12px] font-semibold transition-colors"
        >
          <Sparkles size={11} strokeWidth={2} />
          Gerar podcast
        </button>
      </div>
    )
  }

  if (audio.status === 'pendente' || audio.status === 'gerando') {
    return (
      <div className="rounded-card px-4 py-3 flex items-center gap-3" style={glass}>
        <RefreshCw size={15} strokeWidth={1.75} className="text-accent-orange animate-spin" />
        <div>
          <p className="text-[12px] font-medium text-white">Gerando podcast...</p>
          <p className="text-[11px] text-white/40 font-mono">~ 3–10 min · você pode fechar a página</p>
        </div>
      </div>
    )
  }

  if (audio.status === 'erro') {
    return (
      <div className="rounded-card px-4 py-3 flex items-center justify-between gap-3 flex-wrap"
           style={{ background: 'rgba(212,132,90,0.10)', border: '0.5px solid rgba(212,132,90,0.35)' }}>
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <AlertTriangle size={15} strokeWidth={1.75} className="text-accent-orange shrink-0" />
          <p className="text-[12px] text-accent-orange truncate">
            Erro ao gerar áudio: {audio.error_msg || 'desconhecido'}
          </p>
        </div>
        {isAdmin && (
          <button
            onClick={handleTrigger}
            disabled={triggering}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-btn bg-accent-orange/20 hover:bg-accent-orange/30 text-accent-orange text-[12px] font-semibold transition-colors"
          >
            <RefreshCw size={11} strokeWidth={2} />
            Tentar novamente
          </button>
        )}
      </div>
    )
  }

  // done
  return (
    <div className="rounded-card px-4 py-3 flex items-center justify-between gap-3 flex-wrap" style={glass}>
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <Headphones size={16} strokeWidth={1.75} className="text-text-blue shrink-0" />
        <div className="min-w-0">
          <p className="text-[12px] font-medium text-white">Podcast pronto</p>
          <p className="text-[11px] text-white/40 font-mono">
            {formatDuration(audio.duracao_seg)}{audio.tamanho_bytes ? ` · ${formatBytes(audio.tamanho_bytes)}` : ''}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {audio.arquivo_url && (
          <a
            href={audio.arquivo_url}
            download
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-btn bg-accent-blue hover:bg-accent-blue/90 text-white text-[12px] font-semibold transition-colors"
          >
            <Download size={11} strokeWidth={2} />
            Baixar mp3
          </a>
        )}
        {isAdmin && (
          <button
            onClick={handleTrigger}
            disabled={triggering}
            title="Regenerar"
            className="p-1.5 rounded-btn text-white/50 hover:text-white hover:bg-white/5 transition-colors"
          >
            <RefreshCw size={12} strokeWidth={2} />
          </button>
        )}
      </div>
      {error && <p className="text-[11px] text-accent-orange w-full">{error}</p>}
    </div>
  )
}
