import { createContext, useContext, useEffect, useState } from 'react'
import * as api from '../api'

const BrandContext = createContext({ brand: 'audifaz', loading: true })

const BRAND_META = {
  audifaz: {
    nome: 'AudiFaz',
    tagline: 'Plataforma pessoal de estudos para concursos',
    theme: 'audifaz',
  },
  anajud: {
    nome: 'AnaJud',
    tagline: 'Estudo dirigido para concursos jurídicos',
    theme: 'lexlumina',
  },
}

const VALID_BRANDS = Object.keys(BRAND_META)
const STORAGE_KEY = 'audifaz_brand'
const OVERRIDE_KEY = 'audifaz_brand_override'

/** Lê `?brand=` da URL na primeira render e persiste como override.
 * O override sobrescreve a detecção via Host: até ser limpo com `?brand=auto`. */
function readQueryOverride() {
  if (typeof window === 'undefined') return null
  const params = new URLSearchParams(window.location.search)
  const v = params.get('brand')
  if (v === 'auto') {
    localStorage.removeItem(OVERRIDE_KEY)
    return null
  }
  if (v && VALID_BRANDS.includes(v)) {
    localStorage.setItem(OVERRIDE_KEY, v)
    return v
  }
  return localStorage.getItem(OVERRIDE_KEY) || null
}

export function BrandProvider({ children }) {
  // Override > último brand detectado > default
  const override = typeof window !== 'undefined' ? readQueryOverride() : null
  const initial = override || localStorage.getItem(STORAGE_KEY) || 'audifaz'
  const [brand, setBrand] = useState(initial)
  const [audioEnabled, setAudioEnabled] = useState(false)
  const [loading, setLoading] = useState(!override)

  useEffect(() => {
    // Sempre consulta /brand pra capturar feature flags (audio_enabled),
    // mas só aplica o brand do backend se não houver override manual.
    if (override) localStorage.setItem(STORAGE_KEY, override)
    api.getCurrentBrand()
      .then(r => {
        setAudioEnabled(!!r.data?.audio_enabled)
        if (!override) {
          const b = r.data?.brand || 'audifaz'
          localStorage.setItem(STORAGE_KEY, b)
          setBrand(b)
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, []) // eslint-disable-line

  const meta = BRAND_META[brand] || BRAND_META.audifaz

  // Título da aba acompanha o brand (AnaJud no TJ, AudiFaz no SEFAZ)
  useEffect(() => {
    if (typeof document !== 'undefined' && meta?.nome) document.title = meta.nome
  }, [meta?.nome])

  return (
    <BrandContext.Provider value={{ brand, meta, loading, audioEnabled, hasOverride: !!override }}>
      {children}
    </BrandContext.Provider>
  )
}

export const useBrand = () => useContext(BrandContext)
