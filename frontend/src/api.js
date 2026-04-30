import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// Days
export const getToday = () => api.get('/days/today')
export const getDay = (id) => api.get(`/days/${id}`)
export const getWeekContext = (id) => api.get(`/days/${id}/week-context`)
export const updateDayStatus = (id, status) => api.put(`/days/${id}/status`, { status })
export const updateDayNotes = (id, notas) => api.put(`/days/${id}/notes`, { notas })

// Topics
export const toggleTopic = (id) => api.put(`/topics/${id}/toggle`)

// Material
export const getMaterial = (dayId) => api.get(`/days/${dayId}/material`)
export const recordAttempt = (questionId, alternativa_escolhida, observacao) =>
  api.post(`/days/questions/${questionId}/attempt`, { alternativa_escolhida, observacao })

export async function* streamMaterial(dayId, model = 'claude-sonnet-4-6') {
  const response = await fetch(`/api/days/${dayId}/material/generate?model=${model}`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error('Falha ao gerar material')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop()

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const data = line.slice(6).trim()
      if (data === '[DONE]') return
      try {
        yield JSON.parse(data)
      } catch {}
    }
  }
}

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
