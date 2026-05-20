import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('audifaz_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  // Override de brand persistido pelo BrandProvider; o backend já aceita X-Brand
  const brandOverride = localStorage.getItem('audifaz_brand_override')
  if (brandOverride) config.headers['X-Brand'] = brandOverride
  return config
})

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('audifaz_token')
      localStorage.removeItem('audifaz_username')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// Auth + brand
export const authLogin = (username, password) => api.post('/auth/login', { username, password })
export const authRegister = (username, password) => api.post('/auth/register', { username, password })
export const authSignup = (body) => api.post('/auth/signup', body)
export const authMe = () => api.get('/auth/me')
export const getCurrentBrand = () => api.get('/brand')

// Billing
export const getMySubscriptions = () => api.get('/billing/me')
export const createCheckout = (concurso_id) => api.post(`/billing/checkout/${concurso_id}`)

// LGPD
export const exportMyData = () => api.get('/me/export')
export const deleteMyAccount = () => api.delete('/me')

// Days
export const getToday = () => api.get('/days/today')
export const getDay = (id) => api.get(`/days/${id}`)
export const getDayByDate = (dateStr) => api.get(`/days/by-date/${dateStr}`)
export const getWeekContext = (id) => api.get(`/days/${id}/week-context`)
export const updateDayStatus = (id, status) => api.put(`/days/${id}/status`, { status })
export const updateDayNotes = (id, notas) => api.put(`/days/${id}/notes`, { notas })

// Topics
export const toggleTopic = (id) => api.put(`/topics/${id}/toggle`)

// Material
export const getMaterial = (dayId) => api.get(`/days/${dayId}/material`)
export const generateMaterial = (dayId, model = 'claude-sonnet-4-6') =>
  api.post(`/days/${dayId}/material/generate?model=${model}`, {})
export const recordAttempt = (questionId, alternativa_escolhida, observacao) =>
  api.post(`/days/questions/${questionId}/attempt`, { alternativa_escolhida, observacao })

// Errors
export const getErrors = (params) => api.get('/errors', { params })
export const getStaleCount = () => api.get('/errors/stale-count')
export const getDisciplines = () => api.get('/errors/disciplines')
export const createError = (data) => api.post('/errors', data)
export const markErrorReviewed = (id) => api.put(`/errors/${id}/review`)
export const deleteError = (id) => api.delete(`/errors/${id}`)

// Mocks
export const getMocks = () => api.get('/mocks')
export const createMock = (data) => api.post('/mocks', data)
export const deleteMock = (id) => api.delete(`/mocks/${id}`)

// Progress
export const getProgress = () => api.get('/progress')

// Plano completo (esqueleto: fases > semanas > dias > tópicos, sem conteúdo gerado)
export const getPlano = () => api.get('/plano')

// Content reports (reportar erro em questão/material/redação)
export const reportContent = (data) => api.post('/content-reports', data)
export const listMyReports = () => api.get('/content-reports/me')
export const adminListReports = (status) => api.get('/admin/content-reports', { params: status ? { status } : {} })
export const adminResolveReport = (id, status, nota_admin) =>
  api.put(`/admin/content-reports/${id}/resolve`, { status, nota_admin })

// Audio / Podcast
export const getAudio = (dayId) => api.get(`/days/${dayId}/audio`)
export const generateAudio = (dayId) => api.post(`/days/${dayId}/audio/generate`)
export const getPodcastFeed = () => api.get('/podcast/me')
export const regeneratePodcastToken = () => api.post('/podcast/regenerate-token')

// Redação
export const getRedacaoTemas = () => api.get('/redacao/temas')
export const listRedacoes = () => api.get('/redacao')
export const getRedacao = (id) => api.get(`/redacao/${id}`)
export const submitRedacao = (tema_id, texto) => api.post('/redacao', { tema_id, texto })
export const deleteRedacao = (id) => api.delete(`/redacao/${id}`)

// Blocos / Metricas
export const getBlocos = () => api.get('/blocos')
export const getMetricasBlocos = () => api.get('/metricas/blocos')
export const adminCreateBloco = (data) => api.post('/admin/blocos', data)
export const adminUpdateBloco = (id, data) => api.put(`/admin/blocos/${id}`, data)
export const adminDeleteBloco = (id) => api.delete(`/admin/blocos/${id}`)

// Concursos
export const getConcursos = () => api.get('/concursos')
export const getConcursosPublicos = () => api.get('/concursos/disponiveis')
export const setConcursoAtual = (id) => api.put(`/me/concurso-atual/${id}`)
export const adminCreateConcurso = (data) => api.post('/admin/concursos', data)
export const adminPreviewPlano = (concursoId, file) => {
  const fd = new FormData(); fd.append('file', file)
  return api.post(`/admin/concursos/${concursoId}/preview-plano`, fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const adminImportPlano = (concursoId, file) => {
  const fd = new FormData(); fd.append('file', file)
  return api.post(`/admin/concursos/${concursoId}/importar-plano`, fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
