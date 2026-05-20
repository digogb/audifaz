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

export function BrandProvider({ children }) {
  const [brand, setBrand] = useState(() => localStorage.getItem('audifaz_brand') || 'audifaz')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getCurrentBrand()
      .then(r => {
        const b = r.data?.brand || 'audifaz'
        localStorage.setItem('audifaz_brand', b)
        setBrand(b)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const meta = BRAND_META[brand] || BRAND_META.audifaz
  return (
    <BrandContext.Provider value={{ brand, meta, loading }}>
      {children}
    </BrandContext.Provider>
  )
}

export const useBrand = () => useContext(BrandContext)
