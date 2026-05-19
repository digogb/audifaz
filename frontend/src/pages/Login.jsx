import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import * as api from '../api'

export default function Login() {
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
      const res = await api.authLogin(username, password)
      await login(res.data.token, res.data.username)
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
          <h1 className="font-heading text-4xl font-extrabold tracking-tight">
            <span className="text-accent-text">Audi</span>
            <span className="text-primary">Faz</span>
          </h1>
          <p className="text-[13px] text-subtle">Plataforma de estudos para concursos</p>
        </div>

        <form onSubmit={handleSubmit} className="surface-card rounded-hero p-6 space-y-4">
          <div>
            <label className="block text-[11px] text-subtle mb-2 font-medium uppercase tracking-wider">Usuário</label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              autoFocus
              className="surface-input w-full rounded-btn px-3 py-2.5 text-[14px] text-primary placeholder:text-subtle focus:outline-none focus:border-accent transition-colors"
              placeholder="seu_usuario"
            />
          </div>
          <div>
            <label className="block text-[11px] text-subtle mb-2 font-medium uppercase tracking-wider">Senha</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              className="surface-input w-full rounded-btn px-3 py-2.5 text-[14px] text-primary placeholder:text-subtle focus:outline-none focus:border-accent transition-colors"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <div className="rounded-btn px-3 py-2" style={{ background: 'color-mix(in srgb, var(--color-danger) 10%, transparent)', border: '0.5px solid color-mix(in srgb, var(--color-danger) 35%, transparent)' }}>
              <p className="text-danger text-[13px]">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-btn bg-accent hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed text-[13px] font-semibold transition-colors"
            style={{ color: 'var(--color-bg)' }}
          >
            {loading ? 'Aguarde...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  )
}
