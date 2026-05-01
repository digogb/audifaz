import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import * as api from '../api'

const glassStyle = {
  background: 'rgba(255,255,255,0.05)',
  border: '0.5px solid rgba(255,255,255,0.10)',
  backdropFilter: 'blur(12px)',
  WebkitBackdropFilter: 'blur(12px)',
}

export default function Login() {
  const [tab, setTab] = useState('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = tab === 'login'
        ? await api.authLogin(username, password)
        : await api.authRegister(username, password)
      login(res.data.token, res.data.username)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao autenticar')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center px-4">
      <div className="relative z-10 w-full max-w-sm space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-extrabold tracking-tight">
            <span className="text-text-blue">Audi</span>
            <span className="text-text-primary">Faz</span>
          </h1>
          <p className="text-[13px] text-white/50">Plataforma de estudos · SEFAZ-CE 2026</p>
        </div>

        <div className="rounded-hero p-6 space-y-5" style={glassStyle}>
          <div className="flex p-1 rounded-btn" style={{ background: 'rgba(255,255,255,0.04)' }}>
            {['login', 'register'].map(t => (
              <button
                key={t}
                onClick={() => { setTab(t); setError(null) }}
                className={`flex-1 py-2 text-[13px] font-medium rounded-md transition-all ${
                  tab === t
                    ? 'bg-accent-blue text-white shadow-sm'
                    : 'text-white/60 hover:text-white'
                }`}
              >
                {t === 'login' ? 'Entrar' : 'Criar conta'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[11px] text-white/50 mb-2 font-medium uppercase tracking-wider">Usuário</label>
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                required
                autoFocus
                className="w-full rounded-btn px-3 py-2.5 text-[14px] text-white placeholder-white/30 focus:outline-none focus:border-accent-blue transition-colors"
                style={{ background: 'rgba(255,255,255,0.04)', border: '0.5px solid rgba(255,255,255,0.12)' }}
                placeholder="seu_usuario"
              />
            </div>
            <div>
              <label className="block text-[11px] text-white/50 mb-2 font-medium uppercase tracking-wider">Senha</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                className="w-full rounded-btn px-3 py-2.5 text-[14px] text-white placeholder-white/30 focus:outline-none focus:border-accent-blue transition-colors"
                style={{ background: 'rgba(255,255,255,0.04)', border: '0.5px solid rgba(255,255,255,0.12)' }}
                placeholder="••••••••"
              />
            </div>

            {error && (
              <div className="rounded-btn px-3 py-2" style={{ background: 'rgba(212, 132, 90, 0.10)', border: '0.5px solid rgba(212, 132, 90, 0.35)' }}>
                <p className="text-accent-orange text-[13px]">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-btn bg-accent-blue hover:bg-accent-blue/90 disabled:opacity-50 disabled:cursor-not-allowed text-white text-[13px] font-semibold transition-colors"
            >
              {loading ? 'Aguarde...' : tab === 'login' ? 'Entrar' : 'Criar conta'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
