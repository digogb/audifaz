import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import * as api from '../api'
import { useAuth } from './AuthContext'

const ConcursoContext = createContext(null)

export function ConcursoProvider({ children }) {
  const { isAuthenticated } = useAuth()
  const [concursos, setConcursos] = useState([])
  const [current, setCurrent] = useState(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    if (!isAuthenticated) {
      setConcursos([])
      setCurrent(null)
      setLoading(false)
      return
    }
    try {
      const res = await api.getConcursos()
      setConcursos(res.data)
      setCurrent(res.data.find(c => c.atual) || res.data[0] || null)
    } catch {
      setConcursos([])
      setCurrent(null)
    } finally {
      setLoading(false)
    }
  }, [isAuthenticated])

  useEffect(() => { refresh() }, [refresh])

  const switchTo = useCallback(async (id) => {
    if (current?.id === id) return
    await api.setConcursoAtual(id)
    // Recarrega para invalidar qualquer estado em cache nas páginas
    window.location.reload()
  }, [current])

  return (
    <ConcursoContext.Provider value={{ concursos, current, loading, switchTo, refresh }}>
      {children}
    </ConcursoContext.Provider>
  )
}

export const useConcurso = () => useContext(ConcursoContext)
