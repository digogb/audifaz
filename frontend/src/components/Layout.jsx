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
    <div className="min-h-screen flex flex-col bg-surface-bg">
      <header className="bg-white border-b border-surface-border sticky top-0 z-10 shadow-sm">
        <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
          <span className="font-bold text-brand tracking-tight text-lg">AudiFaz</span>
          <nav className="flex items-center gap-0.5">
            {nav.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-1 text-sm font-medium transition-colors border-b-2 ${
                    isActive
                      ? 'border-brand text-brand'
                      : 'border-transparent text-text-muted hover:text-text-main hover:border-surface-border'
                  }`
                }
              >
                <Icon size={14} />
                {label}
              </NavLink>
            ))}
            <div className="ml-3 flex items-center gap-2 pl-3 border-l border-surface-border">
              <span className="text-xs text-text-faint">{username}</span>
              <button
                onClick={logout}
                title="Sair"
                className="p-1.5 rounded-md text-text-faint hover:text-coral hover:bg-red-50 transition-colors"
              >
                <LogOut size={14} />
              </button>
            </div>
          </nav>
        </div>
      </header>
      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-6">{children}</main>
    </div>
  )
}
