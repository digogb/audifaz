import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import * as api from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('audifaz_token'))
  const [username, setUsername] = useState(() => localStorage.getItem('audifaz_username'))
  const [isAdmin, setIsAdmin] = useState(() => localStorage.getItem('audifaz_is_admin') === '1')

  const login = useCallback(async (tok, user) => {
    localStorage.setItem('audifaz_token', tok)
    localStorage.setItem('audifaz_username', user)
    setToken(tok)
    setUsername(user)
    try {
      const me = await api.authMe()
      const admin = !!me.data.is_admin
      localStorage.setItem('audifaz_is_admin', admin ? '1' : '0')
      setIsAdmin(admin)
    } catch {
      localStorage.setItem('audifaz_is_admin', '0')
      setIsAdmin(false)
    }
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('audifaz_token')
    localStorage.removeItem('audifaz_username')
    localStorage.removeItem('audifaz_is_admin')
    setToken(null); setUsername(null); setIsAdmin(false)
  }, [])

  // Refresh is_admin on mount if already logged in
  useEffect(() => {
    if (!token) return
    api.authMe()
      .then(r => {
        const admin = !!r.data.is_admin
        localStorage.setItem('audifaz_is_admin', admin ? '1' : '0')
        setIsAdmin(admin)
      })
      .catch(() => {})
  }, [token])

  return (
    <AuthContext.Provider value={{ token, username, isAdmin, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
