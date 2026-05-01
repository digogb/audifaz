import { createContext, useContext, useState, useCallback } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('audifaz_token'))
  const [username, setUsername] = useState(() => localStorage.getItem('audifaz_username'))

  const login = useCallback((tok, user) => {
    localStorage.setItem('audifaz_token', tok)
    localStorage.setItem('audifaz_username', user)
    setToken(tok)
    setUsername(user)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('audifaz_token')
    localStorage.removeItem('audifaz_username')
    setToken(null)
    setUsername(null)
  }, [])

  return (
    <AuthContext.Provider value={{ token, username, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
