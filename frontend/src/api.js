import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('audifaz_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
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

// Auth
export const authLogin = (username, password) => api.post('/auth/login', { username, password })
export const authRegister = (username, password) => api.post('/auth/register', { username, password })
export const authMe = () => api.get('/auth/me')

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
  api.post(`/days/${dayId}/material/generate?model=${model}`, {}, { timeout: 300000 })
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
