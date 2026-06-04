import { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react'
import { useConcurso } from './ConcursoContext'
import { useBrand } from './BrandContext'
import { resolveTheme, DEFAULT_THEME } from '../themes'

const CACHE_KEY = 'audifaz_theme_slug'
const OVERRIDE_KEY = 'audifaz_theme_override'

const ThemeContext = createContext(null)

function applyTheme(slug) {
  const theme = resolveTheme(slug)
  const html = document.documentElement
  html.setAttribute('data-theme', theme.slug)
  html.setAttribute('data-theme-mode', theme.mode)
  return theme
}

function ensureFontLinks(theme) {
  // Remove links anteriores deste sistema
  document.querySelectorAll('link[data-theme-font]').forEach(el => el.remove())
  for (const href of theme.fonts || []) {
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = href
    link.setAttribute('data-theme-font', theme.slug)
    document.head.appendChild(link)
  }
}

/**
 * Aplica o tema no <html>. Prioridade:
 *   1. Override manual escolhido pelo usuário (localStorage, persiste entre concursos)
 *   2. Tema do concurso atual
 *   3. Brand do host
 *   4. Default
 * Antes de o concurso carregar, usa o último slug salvo em localStorage p/ evitar flash.
 */
export function ThemeProvider({ children }) {
  const { current } = useConcurso()
  const { meta: brandMeta } = useBrand()
  const appliedRef = useRef(null)
  const [override, setOverrideState] = useState(() => localStorage.getItem(OVERRIDE_KEY) || null)

  // Aplica cached theme antes da primeira render
  if (appliedRef.current === null) {
    const cached = override || localStorage.getItem(CACHE_KEY) || DEFAULT_THEME
    const theme = applyTheme(cached)
    ensureFontLinks(theme)
    appliedRef.current = cached
  }

  const slug = override || current?.theme_slug || brandMeta?.theme || DEFAULT_THEME

  useEffect(() => {
    if (slug === appliedRef.current) return
    const theme = applyTheme(slug)
    ensureFontLinks(theme)
    localStorage.setItem(CACHE_KEY, slug)
    appliedRef.current = slug
  }, [slug])

  const setOverride = useCallback((value) => {
    if (value) localStorage.setItem(OVERRIDE_KEY, value)
    else localStorage.removeItem(OVERRIDE_KEY)
    setOverrideState(value || null)
  }, [])

  return (
    <ThemeContext.Provider value={{ themeSlug: slug, override, setOverride }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => useContext(ThemeContext)
