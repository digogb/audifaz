import { useEffect, useRef } from 'react'
import { useConcurso } from './ConcursoContext'
import { useBrand } from './BrandContext'
import { resolveTheme, DEFAULT_THEME } from '../themes'

const CACHE_KEY = 'audifaz_theme_slug'

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
 * Aplica o tema do concurso atual no <html>. Antes de o concurso carregar,
 * usa o último slug salvo em localStorage para evitar flash.
 */
export function ThemeProvider({ children }) {
  const { current } = useConcurso()
  const { meta: brandMeta } = useBrand()
  const appliedRef = useRef(null)

  // Aplica cached theme antes da primeira render
  if (appliedRef.current === null) {
    const cached = localStorage.getItem(CACHE_KEY) || DEFAULT_THEME
    const theme = applyTheme(cached)
    ensureFontLinks(theme)
    appliedRef.current = cached
  }

  useEffect(() => {
    // Prioridade: concurso atual > brand do host > default
    const slug = current?.theme_slug || brandMeta?.theme || DEFAULT_THEME
    if (slug === appliedRef.current) return
    const theme = applyTheme(slug)
    ensureFontLinks(theme)
    localStorage.setItem(CACHE_KEY, slug)
    appliedRef.current = slug
  }, [current?.theme_slug, brandMeta?.theme])

  return children
}
