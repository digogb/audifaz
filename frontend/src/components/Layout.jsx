import { NavLink } from 'react-router-dom'
import { BookOpen, AlertCircle, BarChart2, FileText, LogOut } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

const nav = [
  { to: '/', label: 'Hoje', icon: BookOpen },
  { to: '/erros', label: 'Erros', icon: AlertCircle },
  { to: '/progresso', label: 'Progresso', icon: BarChart2 },
  { to: '/simulados', label: 'Simulados', icon: FileText },
]

export default function Layout({ children }) {
  const { username, logout } = useAuth()

  return (
    <div className="relative min-h-screen flex flex-col">
      <header className="sticky top-4 z-20 px-4">
        <div className="max-w-5xl mx-auto">
          <div
            className="flex items-center justify-between rounded-container px-5 py-3"
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '0.5px solid rgba(255,255,255,0.10)',
              backdropFilter: 'blur(12px)',
              WebkitBackdropFilter: 'blur(12px)',
            }}
          >
            <span className="font-semibold text-text-primary tracking-tight text-sm">
              Audi<span className="text-text-blue">Faz</span>
            </span>

            <nav className="flex items-center gap-0.5">
              {nav.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) =>
                    `flex items-center gap-1.5 px-3 py-1.5 rounded-btn text-[13px] font-medium transition-all ${
                      isActive
                        ? 'bg-accent-blue/20 text-text-blue'
                        : 'text-white/60 hover:text-white hover:bg-white/5'
                    }`
                  }
                >
                  <Icon size={13} strokeWidth={1.75} />
                  {label}
                </NavLink>
              ))}
            </nav>

            <div className="flex items-center gap-3">
              <span className="text-[12px] text-white/50 font-mono">{username}</span>
              <button
                onClick={logout}
                title="Sair"
                className="p-1.5 rounded-btn text-white/50 hover:text-accent-orange hover:bg-white/5 transition-colors"
              >
                <LogOut size={13} strokeWidth={1.75} />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="relative z-10 flex-1 max-w-5xl mx-auto w-full px-4 py-8">{children}</main>
    </div>
  )
}
