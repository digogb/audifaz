import { NavLink } from 'react-router-dom'
import { BookOpen, AlertCircle, BarChart2, FileText } from 'lucide-react'

const nav = [
  { to: '/', label: 'Hoje', icon: BookOpen },
  { to: '/erros', label: 'Erros', icon: AlertCircle },
  { to: '/progresso', label: 'Progresso', icon: BarChart2 },
  { to: '/simulados', label: 'Simulados', icon: FileText },
]

export default function Layout({ children }) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
          <span className="font-bold text-indigo-400 tracking-tight text-lg">audifaz</span>
          <nav className="flex gap-1">
            {nav.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-indigo-600 text-white'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                  }`
                }
              >
                <Icon size={14} />
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-6">{children}</main>
    </div>
  )
}
