import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import * as api from '../api'

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
    <div className="min-h-screen flex items-center justify-center bg-surface-bg px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center space-y-1">
          <h1 className="text-3xl font-bold text-brand tracking-tight">AudiFaz</h1>
          <p className="text-sm text-text-muted">Plataforma de estudos SEFAZ-CE 2026</p>
        </div>

        <div className="bg-white rounded-card shadow-card p-6 space-y-5">
          <div className="flex rounded-xl bg-surface-bg p-1">
            {['login', 'register'].map(t => (
              <button
                key={t}
                onClick={() => { setTab(t); setError(null) }}
                className={`flex-1 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                  tab === t
                    ? 'bg-white text-brand shadow-sm'
                    : 'text-text-muted hover:text-text-main'
                }`}
              >
                {t === 'login' ? 'Entrar' : 'Criar conta'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-text-muted mb-1.5 font-medium uppercase tracking-wider">Usuário</label>
                <input
                  type="text"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  required
                  autoFocus
                  className="w-full bg-surface-bg border border-surface-border rounded-xl px-3 py-2.5 text-sm text-text-main placeholder-text-faint focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/10 transition-all"
                  placeholder="seu_usuario"
                />
              </div>
              <div>
                <label className="block text-xs text-text-muted mb-1.5 font-medium uppercase tracking-wider">Senha</label>
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  className="w-full bg-surface-bg border border-surface-border rounded-xl px-3 py-2.5 text-sm text-text-main placeholder-text-faint focus:outline-none focus:border-brand focus:ring-2 focus:ring-brand/10 transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                <p className="text-coral text-sm">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-xl bg-brand hover:bg-brand-dark disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold transition-colors shadow-sm"
            >
              {loading ? 'Aguarde...' : tab === 'login' ? 'Entrar' : 'Criar conta'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
