import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import * as api from '../api'
import { useAuth } from '../contexts/AuthContext'
import { useBrand } from '../contexts/BrandContext'

export default function Signup() {
  const [searchParams] = useSearchParams()
  const concursoSlug = searchParams.get('concurso') || null

  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [aceita, setAceita] = useState(false)
  const [err, setErr] = useState(null)
  const [loading, setLoading] = useState(false)
  const [concursos, setConcursos] = useState([])
  const { meta: brand } = useBrand()
  const { login } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    api.getConcursosPublicos().then(r => setConcursos(r.data)).catch(() => {})
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setErr(null); setLoading(true)
    try {
      const res = await api.authSignup({ username, email, password, aceita_termos: aceita, concurso_slug: concursoSlug })
      await login(res.data.token, res.data.username)
      navigate('/')
    } catch (e) {
      setErr(e.response?.data?.detail || 'Erro no cadastro')
    } finally {
      setLoading(false)
    }
  }

  const concurso = concursoSlug
    ? concursos.find(c => c.slug === concursoSlug)
    : concursos[0]

  return (
    <div className="relative min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center space-y-2">
          <h1 className="font-heading text-3xl font-extrabold tracking-tight text-primary">
            Criar conta no {brand.nome}
          </h1>
          {concurso && (
            <p className="text-[13px] text-muted">
              {concurso.nome} · 7 dias grátis · depois R$ {(concurso.preco_cents || 0) / 100}
            </p>
          )}
        </div>

        <form onSubmit={handleSubmit} className="surface-card rounded-hero p-6 space-y-4">
          <div>
            <label className="block text-[11px] text-subtle mb-2 font-medium uppercase tracking-wider">Usuário</label>
            <input
              type="text" value={username} onChange={e => setUsername(e.target.value)} required autoFocus minLength={3}
              className="surface-input w-full rounded-btn px-3 py-2.5 text-[14px] text-primary placeholder:text-subtle focus:outline-none focus:border-accent"
              placeholder="seu_usuario"
            />
          </div>
          <div>
            <label className="block text-[11px] text-subtle mb-2 font-medium uppercase tracking-wider">E-mail</label>
            <input
              type="email" value={email} onChange={e => setEmail(e.target.value)} required
              className="surface-input w-full rounded-btn px-3 py-2.5 text-[14px] text-primary placeholder:text-subtle focus:outline-none focus:border-accent"
              placeholder="voce@exemplo.com"
            />
          </div>
          <div>
            <label className="block text-[11px] text-subtle mb-2 font-medium uppercase tracking-wider">Senha</label>
            <input
              type="password" value={password} onChange={e => setPassword(e.target.value)} required minLength={6}
              className="surface-input w-full rounded-btn px-3 py-2.5 text-[14px] text-primary placeholder:text-subtle focus:outline-none focus:border-accent"
              placeholder="mínimo 6 caracteres"
            />
          </div>

          <label className="flex items-start gap-2 text-[12px] text-muted cursor-pointer">
            <input
              type="checkbox" checked={aceita} onChange={e => setAceita(e.target.checked)} required
              className="mt-0.5 accent-current"
            />
            <span>
              Li e aceito os{' '}
              <a href="/termos" target="_blank" rel="noreferrer" className="text-accent-text hover:underline">Termos de Uso</a>{' '}
              e a{' '}
              <a href="/privacidade" target="_blank" rel="noreferrer" className="text-accent-text hover:underline">Política de Privacidade</a>.
            </span>
          </label>

          {err && (
            <div className="rounded-btn px-3 py-2" style={{ background: 'color-mix(in srgb, var(--color-danger) 10%, transparent)', border: '0.5px solid color-mix(in srgb, var(--color-danger) 35%, transparent)' }}>
              <p className="text-danger text-[13px]">{err}</p>
            </div>
          )}

          <button
            type="submit" disabled={loading}
            className="w-full py-2.5 rounded-btn bg-accent hover:bg-accent-hover disabled:opacity-50 text-[13px] font-semibold transition-colors"
            style={{ color: 'var(--color-bg)' }}
          >
            {loading ? 'Criando...' : 'Começar trial grátis'}
          </button>

          <p className="text-center text-[12px] text-subtle">
            Já tem conta? <Link to="/login" className="text-accent-text hover:underline">Entrar</Link>
          </p>
        </form>
      </div>
    </div>
  )
}
