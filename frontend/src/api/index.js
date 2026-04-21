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

export async function getTransferPriority(recordId) {
  const response = await axios.get(`${API_BASE}/zaigong/transfer-priority/${recordId}`)
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

export async function exportFourClassExcel(recordId) {
  const response = await axios.get(
    `${API_BASE}/zaigong/four-class-warnings/${recordId}/export`,
    { responseType: 'blob' }
  )
  return response.data
}

export async function getNotifyConfig() {
  const response = await axios.get(`${API_BASE}/notify/config`)
  return response.data
}

export async function saveNotifyConfig(webhookUrl, autoPush) {
  const response = await axios.post(`${API_BASE}/notify/config`, {
    webhook_url: webhookUrl,
    auto_push: autoPush,
  })
  return response.data
}

export async function clearNotifyConfig() {
  const response = await axios.post(`${API_BASE}/notify/config/clear`)
  return response.data
}

export async function testNotifyWebhook(webhookUrl) {
  const response = await axios.post(`${API_BASE}/notify/test`, { webhook_url: webhookUrl })
  return response.data
}

export async function pushNotify(recordId) {
  const response = await axios.post(`${API_BASE}/notify/push/${recordId}`)
  return response.data
}

export async function generateBriefImage(zaigongId, budgetId) {
  const params = { zaigong_id: zaigongId }
  if (budgetId) params.budget_id = budgetId
  const response = await axios.get(`${API_BASE}/report/image`, {
    params,
    responseType: 'blob',
  })
  return response.data
}


export async function updateTargetValue(recordId, target) {
  const response = await axios.post(`${API_BASE}/zaigong/history/${recordId}/target`, null, {
    params: { target }
  })
  return response.data
}

export async function refreshBudgetSpend() {
  const response = await axios.post(`${API_BASE}/budget/refresh-spend`)
  return response.data
}

export async function listArchives() {
  const response = await axios.get(`${API_BASE}/archive/list`)
  return response.data
}

export async function uploadArchive(file, category, year, note = '') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('category', category)
  formData.append('year', year)
  formData.append('note', note)
  const response = await axios.post(`${API_BASE}/archive/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}

export function getArchiveFileUrl(recordId) {
  return `${API_BASE}/archive/file/${recordId}`
}

export async function deleteArchive(recordId) {
  const response = await axios.post(`${API_BASE}/archive/delete/${recordId}`)
  return response.data
}

export async function exportTransferPriority(recordId, targetRate) {
  const params = targetRate ? { target_rate: targetRate / 100 } : {}
  const response = await axios.get(
    `${API_BASE}/zaigong/transfer-priority/${recordId}/export`,
    { params, responseType: 'blob' }
  )
  return response.data
}
