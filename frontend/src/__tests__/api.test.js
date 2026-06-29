/**
 * api/index.js 接口函数单元测试
 *
 * 覆盖：
 *   - 每个导出函数的 HTTP 方法和 URL
 *   - 参数拼装（query params / request body / FormData）
 *   - 默认参数处理
 *   - 边界条件
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Mock axios ──
const mockAxios = {
  get: vi.fn(() => Promise.resolve({ data: {} })),
  post: vi.fn(() => Promise.resolve({ data: {} })),
  put: vi.fn(() => Promise.resolve({ data: {} })),
  delete: vi.fn(() => Promise.resolve({ data: {} })),
}

vi.mock('axios', () => ({ default: mockAxios }))

let api
beforeEach(async () => {
  vi.clearAllMocks()
  api = await import('../api')
})

const BASE = 'http://localhost:8000/api'


// ──────────────────────────────────────────────────────────────
// 1. 在建工程接口
// ──────────────────────────────────────────────────────────────

describe('在建工程接口', () => {
  it('uploadExcel POST /zaigong/upload', async () => {
    const file = new File(['data'], 'test.xlsx')
    await api.uploadExcel(file, 503)
    expect(mockAxios.post).toHaveBeenCalledTimes(1)
    const [url, formData, config] = mockAxios.post.mock.calls[0]
    expect(url).toBe(`${BASE}/zaigong/upload`)
    expect(config.params.target).toBe(503)
    expect(config.headers['Content-Type']).toBe('multipart/form-data')
  })

  it('getMetrics GET /zaigong/metrics', async () => {
    await api.getMetrics()
    expect(mockAxios.get).toHaveBeenCalledWith(`${BASE}/zaigong/metrics`)
  })

  it('getCompare GET /zaigong/compare', async () => {
    await api.getCompare()
    expect(mockAxios.get).toHaveBeenCalledWith(`${BASE}/zaigong/compare`)
  })

  it('getHistory 默认 limit=10', async () => {
    await api.getHistory()
    expect(mockAxios.get).toHaveBeenCalledWith(`${BASE}/zaigong/history`, { params: { limit: 10 } })
  })

  it('getHistory 自定义 limit', async () => {
    await api.getHistory(20)
    expect(mockAxios.get).toHaveBeenCalledWith(`${BASE}/zaigong/history`, { params: { limit: 20 } })
  })

  it('getHistorySnapshot GET /zaigong/history/:id', async () => {
    await api.getHistorySnapshot(42)
    expect(mockAxios.get).toHaveBeenCalledWith(`${BASE}/zaigong/history/42`)
  })

  it('getManagerDetails 带 record_id 和 manager 参数', async () => {
    await api.getManagerDetails(42, '张三')
    expect(mockAxios.get).toHaveBeenCalledWith(`${BASE}/zaigong/manager-details`, {
      params: { record_id: 42, manager: '张三' },
    })
  })

  it('exportManagerDetailsExcel responseType blob', async () => {
    await api.exportManagerDetailsExcel(42, '张三')
    expect(mockAxios.get).toHaveBeenCalledWith(
      `${BASE}/zaigong/manager-details/42/export`,
      { params: { manager: '张三' }, responseType: 'blob' },
    )
  })

  it('exportAllManagerDetailsExcel responseType blob', async () => {
    await api.exportAllManagerDetailsExcel(42)
    expect(mockAxios.get).toHaveBeenCalledWith(
      `${BASE}/zaigong/manager-details/42/export-all`,
      { responseType: 'blob' },
    )
  })

  it('getTransferPriority GET /zaigong/transfer-priority/:id', async () => {
    await api.getTransferPriority(42)
    expect(mockAxios.get).toHaveBeenCalledWith(`${BASE}/zaigong/transfer-priority/42`)
  })

  it('exportTransferPriority 带 target_rate 参数', async () => {
    await api.exportTransferPriority(42, 80)
    expect(mockAxios.get).toHaveBeenCalledWith(
      `${BASE}/zaigong/transfer-priority/42/export`,
      { params: { target_rate: 0.8 }, responseType: 'blob' },
    )
  })

  it('exportTransferPriority 无 targetRate 不传参', async () => {
    await api.exportTransferPriority(42)
    expect(mockAxios.get).toHaveBeenCalledWith(
      `${BASE}/zaigong/transfer-priority/42/export`,
      { params: {}, responseType: 'blob' },
    )
  })

  it('exportFourClassExcel responseType blob', async () => {
    await api.exportFourClassExcel(42)
    expect(mockAxios.get).toHaveBeenCalledWith(
      `${BASE}/zaigong/four-class-warnings/42/export`,
      { responseType: 'blob' },
    )
  })

  it('updateTargetValue POST 带 target 参数', async () => {
    await api.updateTargetValue(42, 503)
    expect(mockAxios.post).toHaveBeenCalledWith(
      `${BASE}/zaigong/history/42/target`,
      null,
      { params: { target: 503 } },
    )
  })
})


// ──────────────────────────────────────────────────────────────
// 2. 预算接口
// ──────────────────────────────────────────────────────────────

describe('预算接口', () => {
  it('uploadBudget POST /budget/upload', async () => {
    const file = new File(['data'], 'budget.xlsx')
    await api.uploadBudget(file)
    const [url, , config] = mockAxios.post.mock.calls[0]
    expect(url).toBe(`${BASE}/budget/upload`)
    expect(config.headers['Content-Type']).toBe('multipart/form-data')
  })

  it('getBudgetHistory 默认 limit=10', async () => {
    await api.getBudgetHistory()
    expect(mockAxios.get).toHaveBeenCalledWith(`${BASE}/budget/history`, { params: { limit: 10 } })
  })

  it('getBudgetHistory 自定义 limit', async () => {
    await api.getBudgetHistory(5)
    expect(mockAxios.get).toHaveBeenCalledWith(`${BASE}/budget/history`, { params: { limit: 5 } })
  })

  it('getBudgetHistorySnapshot GET /budget/history/:id', async () => {
    await api.getBudgetHistorySnapshot(99)
    expect(mockAxios.get).toHaveBeenCalledWith(`${BASE}/budget/history/99`)
  })

  it('refreshBudgetSpend POST /budget/refresh-spend', async () => {
    await api.refreshBudgetSpend()
    expect(mockAxios.post).toHaveBeenCalledWith(`${BASE}/budget/refresh-spend`)
  })
})


// ──────────────────────────────────────────────────────────────
// 3. AI 接口
// ──────────────────────────────────────────────────────────────

describe('AI 接口', () => {
  it('generateAIAnalysis POST /ai/analyze', async () => {
    const payload = { data: { metrics: {} }, style: 'executive' }
    await api.generateAIAnalysis(payload)
    expect(mockAxios.post).toHaveBeenCalledWith(`${BASE}/ai/analyze`, payload)
  })

  it('getAIStatus GET /ai/status', async () => {
    await api.getAIStatus()
    expect(mockAxios.get).toHaveBeenCalledWith(`${BASE}/ai/status`)
  })
})


// ──────────────────────────────────────────────────────────────
// 4. 通知接口
// ──────────────────────────────────────────────────────────────

describe('通知接口', () => {
  it('getNotifyConfig GET /notify/config', async () => {
    await api.getNotifyConfig()
    expect(mockAxios.get).toHaveBeenCalledWith(`${BASE}/notify/config`)
  })

  it('saveNotifyConfig POST /notify/config', async () => {
    await api.saveNotifyConfig('https://hook.example.com', true)
    expect(mockAxios.post).toHaveBeenCalledWith(`${BASE}/notify/config`, {
      webhook_url: 'https://hook.example.com',
      auto_push: true,
    })
  })

  it('clearNotifyConfig POST /notify/config/clear', async () => {
    await api.clearNotifyConfig()
    expect(mockAxios.post).toHaveBeenCalledWith(`${BASE}/notify/config/clear`)
  })

  it('testNotifyWebhook POST /notify/test', async () => {
    await api.testNotifyWebhook('https://hook.example.com')
    expect(mockAxios.post).toHaveBeenCalledWith(`${BASE}/notify/test`, {
      webhook_url: 'https://hook.example.com',
    })
  })

  it('pushNotify POST /notify/push/:id', async () => {
    await api.pushNotify(42)
    expect(mockAxios.post).toHaveBeenCalledWith(`${BASE}/notify/push/42`)
  })
})


// ──────────────────────────────────────────────────────────────
// 5. 报告接口
// ──────────────────────────────────────────────────────────────

describe('报告接口', () => {
  it('generateBriefImage 带 zaigong_id', async () => {
    await api.generateBriefImage(1)
    expect(mockAxios.get).toHaveBeenCalledWith(`${BASE}/report/image`, {
      params: { zaigong_id: 1 },
      responseType: 'blob',
    })
  })

  it('generateBriefImage 同时带 budget_id', async () => {
    await api.generateBriefImage(1, 2)
    expect(mockAxios.get).toHaveBeenCalledWith(`${BASE}/report/image`, {
      params: { zaigong_id: 1, budget_id: 2 },
      responseType: 'blob',
    })
  })

  it('generateBriefImage budgetId 为 null 不传', async () => {
    await api.generateBriefImage(1, null)
    const params = mockAxios.get.mock.calls[0][1].params
    expect(params).toEqual({ zaigong_id: 1 })
    expect(params.budget_id).toBeUndefined()
  })
})


// ──────────────────────────────────────────────────────────────
// 6. 档案接口
// ──────────────────────────────────────────────────────────────

describe('档案接口', () => {
  it('listArchives GET /archive/list', async () => {
    await api.listArchives()
    expect(mockAxios.get).toHaveBeenCalledWith(`${BASE}/archive/list`)
  })

  it('uploadArchive POST /archive/upload FormData', async () => {
    const file = new File(['data'], 'doc.xlsx')
    await api.uploadArchive(file, '年度建设情况', '2025', '备注')
    const [url, formData, config] = mockAxios.post.mock.calls[0]
    expect(url).toBe(`${BASE}/archive/upload`)
    expect(config.headers['Content-Type']).toBe('multipart/form-data')
  })

  it('getArchiveFileUrl 返回正确的 URL', () => {
    const url = api.getArchiveFileUrl(42)
    expect(url).toBe(`${BASE}/archive/file/42`)
  })

  it('deleteArchive POST /archive/delete/:id', async () => {
    await api.deleteArchive(42)
    expect(mockAxios.post).toHaveBeenCalledWith(`${BASE}/archive/delete/42`)
  })
})


// ──────────────────────────────────────────────────────────────
// 7. 批次下达接口
// ──────────────────────────────────────────────────────────────

describe('批次下达接口', () => {
  it('getBatchData GET /budget-batch/batches', async () => {
    await api.getBatchData()
    expect(mockAxios.get).toHaveBeenCalledWith(`${BASE}/budget-batch/batches`)
  })

  it('createBatch POST /budget-batch/batches', async () => {
    const payload = { batch_date: '2026-06-20', amounts: { '5G': 100 } }
    await api.createBatch(payload)
    expect(mockAxios.post).toHaveBeenCalledWith(`${BASE}/budget-batch/batches`, payload)
  })

  it('updateBatch PUT /budget-batch/batches/:id', async () => {
    const payload = { batch_date: '2026-06-20', amounts: { '5G': 200 } }
    await api.updateBatch(42, payload)
    expect(mockAxios.put).toHaveBeenCalledWith(`${BASE}/budget-batch/batches/42`, payload)
  })

  it('deleteBatch DELETE /budget-batch/batches/:id', async () => {
    await api.deleteBatch(42)
    expect(mockAxios.delete).toHaveBeenCalledWith(`${BASE}/budget-batch/batches/42`)
  })

  it('getSpecialties GET /budget-batch/specialties', async () => {
    await api.getSpecialties()
    expect(mockAxios.get).toHaveBeenCalledWith(`${BASE}/budget-batch/specialties`)
  })

  it('addSpecialty POST /budget-batch/specialties', async () => {
    await api.addSpecialty('5G')
    expect(mockAxios.post).toHaveBeenCalledWith(`${BASE}/budget-batch/specialties`, {
      name: '5G',
      sort_order: 999,
    })
  })

  it('updateSpecialty PUT /budget-batch/specialties/:id', async () => {
    await api.updateSpecialty(42, { name: '传输' })
    expect(mockAxios.put).toHaveBeenCalledWith(`${BASE}/budget-batch/specialties/42`, { name: '传输' })
  })

  it('deleteSpecialty DELETE /budget-batch/specialties/:id', async () => {
    await api.deleteSpecialty(42)
    expect(mockAxios.delete).toHaveBeenCalledWith(`${BASE}/budget-batch/specialties/42`)
  })

  it('reorderSpecialties PUT /budget-batch/specialties/reorder/batch', async () => {
    const order = [3, 1, 2]
    await api.reorderSpecialties(order)
    expect(mockAxios.put).toHaveBeenCalledWith(`${BASE}/budget-batch/specialties/reorder/batch`, order)
  })
})
