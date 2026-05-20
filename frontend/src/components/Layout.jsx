import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { BookOpen, AlertCircle, BarChart2, FileText, LogOut, Menu, X, Settings, ChevronDown, Target, PenLine } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useConcurso } from '../contexts/ConcursoContext'

const nav = [
  { to: '/', label: 'Hoje', icon: BookOpen },
  { to: '/redacao', label: 'Redação', icon: PenLine },
  { to: '/erros', label: 'Erros', icon: AlertCircle },
  { to: '/progresso', label: 'Progresso', icon: BarChart2 },
  { to: '/metricas', label: 'Métricas', icon: Target },
  { to: '/simulados', label: 'Simulados', icon: FileText },
  { to: '/config', label: 'Config', icon: Settings },
]

function ConcursoSwitcher() {
  const { concursos, current, switchTo } = useConcurso()
  const [open, setOpen] = useState(false)

  if (!current || concursos.length <= 1) {
    return current ? (
      <span className="hidden sm:inline text-[11px] text-subtle font-mono truncate max-w-[200px]">
        {current.slug}
      </span>
    ) : null
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-1 px-2 py-1 rounded-btn text-[11px] font-mono text-muted hover:text-primary hover:bg-accent-soft transition-colors"
      >
        <span className="truncate max-w-[160px]">{current.slug}</span>
        <ChevronDown size={11} strokeWidth={1.75} />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full mt-1 min-w-[240px] z-20 surface-card py-1">
            {concursos.map(c => (
              <button
                key={c.id}
                onClick={() => { setOpen(false); switchTo(c.id) }}
                className={`w-full text-left px-3 py-2 text-[12px] transition-colors ${
                  c.id === current.id
                    ? 'bg-accent-soft text-accent-text'
                    : 'text-muted hover:bg-accent-soft hover:text-primary'
                }`}
              >
                <div className="font-medium">{c.nome}</div>
                <div className="text-[10px] text-subtle font-mono">{c.banca} · {c.cargo}</div>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export default function Layout({ children }) {
  const { username, logout } = useAuth()
  const [open, setOpen] = useState(false)

  return (
    <div className="relative min-h-screen flex flex-col">
      <header className="sticky top-3 sm:top-4 z-30 px-3 sm:px-4">
        <div className="max-w-5xl mx-auto">
          <div className="surface-card flex items-center justify-between px-4 sm:px-5 py-2.5 sm:py-3">
            <div className="flex items-center gap-3">
              <span className="font-heading font-semibold text-primary tracking-tight text-sm">
                Audi<span className="text-accent-text">Faz</span>
              </span>
              <ConcursoSwitcher />
            </div>

            {/* Desktop nav */}
            <nav className="hidden md:flex items-center gap-0.5">
              {nav.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) =>
                    `flex items-center gap-1.5 px-3 py-1.5 rounded-btn text-[13px] font-medium transition-all ${
                      isActive
                        ? 'bg-accent-soft text-accent-text'
                        : 'text-muted hover:text-primary hover:bg-accent-soft'
                    }`
                  }
                >
                  <Icon size={13} strokeWidth={1.75} />
                  {label}
                </NavLink>
              ))}
            </nav>

            <div className="flex items-center gap-2">
              <span className="hidden sm:inline text-[12px] text-subtle font-mono">{username}</span>
              <button
                onClick={logout}
                title="Sair"
                className="hidden md:flex p-1.5 rounded-btn text-subtle hover:text-danger hover:bg-accent-soft transition-colors"
              >
                <LogOut size={13} strokeWidth={1.75} />
              </button>
              {/* Mobile menu toggle */}
              <button
                onClick={() => setOpen(!open)}
                className="md:hidden p-1.5 rounded-btn text-muted hover:text-primary hover:bg-accent-soft transition-colors"
                aria-label="Menu"
              >
                {open ? <X size={18} strokeWidth={1.75} /> : <Menu size={18} strokeWidth={1.75} />}
              </button>
            </div>
          </div>

          {/* Mobile drawer */}
          {open && (
            <div className="md:hidden mt-2 surface-card p-2 space-y-0.5">
              {nav.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === '/'}
                  onClick={() => setOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-3 py-2.5 rounded-btn text-[14px] font-medium transition-all ${
                      isActive
                        ? 'bg-accent-soft text-accent-text'
                        : 'text-muted hover:text-primary hover:bg-accent-soft'
                    }`
                  }
                >
                  <Icon size={15} strokeWidth={1.75} />
                  {label}
                </NavLink>
              ))}
              <div className="pt-2 mt-2 flex items-center justify-between px-3 py-1" style={{ borderTop: 'var(--surface-border)' }}>
                <span className="text-[12px] text-subtle font-mono">{username}</span>
                <button
                  onClick={() => { setOpen(false); logout() }}
                  className="flex items-center gap-1.5 text-[12px] text-muted hover:text-danger transition-colors"
                >
                  <LogOut size={13} strokeWidth={1.75} /> Sair
                </button>
              </div>
            </div>
          )}
        </div>
      </header>

      <main className="relative z-10 flex-1 max-w-5xl mx-auto w-full px-3 sm:px-4 py-6 sm:py-8">{children}</main>
    </div>
  )
}
