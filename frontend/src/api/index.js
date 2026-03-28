import axios from 'axios'

const API_BASE = (import.meta.env.VITE_API_BASE || 'http://localhost:8000/api').replace(/\/$/, '')

export async function uploadExcel(file, target) {
  const formData = new FormData()
  formData.append('file', file)
  const response = await axios.post(`${API_BASE}/zaigong/upload`, formData, {
    params: { target },
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}

export async function uploadBudget(file) {
  const formData = new FormData()
  formData.append('file', file)
  const response = await axios.post(`${API_BASE}/budget/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}

export async function getBudgetHistory(limit = 10) {
  const response = await axios.get(`${API_BASE}/budget/history`, { params: { limit } })
  return response.data
}

export async function getBudgetHistorySnapshot(recordId) {
  const response = await axios.get(`${API_BASE}/budget/history/${recordId}`)
  return response.data
}

export async function getMetrics() {
  const response = await axios.get(`${API_BASE}/zaigong/metrics`)
  return response.data
}

export async function getCompare() {
  const response = await axios.get(`${API_BASE}/zaigong/compare`)
  return response.data
}

export async function getHistory(limit = 10) {
  const response = await axios.get(`${API_BASE}/zaigong/history`, { params: { limit } })
  return response.data
}

export async function getHistorySnapshot(recordId) {
  const response = await axios.get(`${API_BASE}/zaigong/history/${recordId}`)
  return response.data
}

export async function getManagerDetails(recordId, manager) {
  const response = await axios.get(`${API_BASE}/zaigong/manager-details`, {
    params: { record_id: recordId, manager }
  })
  return response.data
}

export async function generateAIAnalysis(payload) {
  const response = await axios.post(`${API_BASE}/ai/analyze`, payload)
  return response.data
}

export async function getAIStatus() {
  const response = await axios.get(`${API_BASE}/ai/status`)
  return response.data
}
