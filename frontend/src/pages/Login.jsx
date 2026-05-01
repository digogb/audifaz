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
    <div className="min-h-screen flex items-center justify-center bg-slate-950 px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center space-y-1">
          <h1 className="text-2xl font-bold text-indigo-400 tracking-tight">AudiFaz</h1>
          <p className="text-sm text-slate-500">Plataforma de estudos SEFAZ-CE 2026</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-5">
          <div className="flex rounded-lg bg-slate-800 p-0.5">
            {['login', 'register'].map(t => (
              <button
                key={t}
                onClick={() => { setTab(t); setError(null) }}
                className={`flex-1 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  tab === t ? 'bg-slate-700 text-slate-100' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {t === 'login' ? 'Entrar' : 'Criar conta'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Usuário</label>
                <input
                  type="text"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  required
                  autoFocus
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-600"
                  placeholder="seu_usuario"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1.5 uppercase tracking-wider">Senha</label>
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-600"
                  placeholder="••••••••"
                />
              </div>
            </div>

            {error && <p className="text-rose-400 text-sm">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition-colors"
            >
              {loading ? 'Aguarde...' : tab === 'login' ? 'Entrar' : 'Criar conta'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
