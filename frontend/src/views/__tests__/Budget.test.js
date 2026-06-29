/**
 * Budget.vue 核心交互单元测试
 *
 * 覆盖：
 *   - 空数据 / 数据加载状态
 *   - 标签栏切换（预算执行 / 批次下达）
 *   - 上传区域交互
 *   - KPI count-up 动画
 *   - 计算属性
 *   - 历史面板
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

// ── Mock API 模块 ──
vi.mock('../../api', () => ({
  uploadBudget: vi.fn(),
  getBudgetHistory: vi.fn(),
  getBudgetHistorySnapshot: vi.fn(),
  getBatchData: vi.fn(),
  createBatch: vi.fn(),
  updateBatch: vi.fn(),
  deleteBatch: vi.fn(),
  getSpecialties: vi.fn(),
  addSpecialty: vi.fn(),
  updateSpecialty: vi.fn(),
  deleteSpecialty: vi.fn(),
}))

// ── Mock html2canvas ──
vi.mock('html2canvas', () => ({
  default: vi.fn(() => Promise.resolve({ toDataURL: () => 'data:image/png;base64,test' }))
}))

// ── 存根：避免 onMounted 中 API 调用报错 ──
const api = await import('../../api')
api.getBudgetHistory.mockResolvedValue({ success: false, data: [] })
api.getBatchData.mockResolvedValue({
  specialties: [],
  batches: [],
  totals: {},
})

// ── 重置 composable 单例状态，避免测试间泄漏 ──
const globalData = await import('../../composables/useGlobalData')

let Budget
beforeEach(async () => {
  // 重置 composable 状态
  const gd = globalData.useGlobalData()
  gd.budgetData.value = null
  gd.budgetLatestData.value = null
  gd.budgetDate.value = null
  gd.budgetSnapshotLabel.value = ''
  gd.zaigongData.value = null
  gd.zaigongLatestData.value = null
  gd.zaigongDate.value = null
  gd.zaigongSnapshotLabel.value = ''
  gd.zaigongFourClassWarnings.value = null
  gd.zaigongLatestFourClassWarnings.value = null

  Budget = (await import('../Budget.vue')).default
})

// ──────────────────────────────────────────────────────────────
// 辅助函数
// ──────────────────────────────────────────────────────────────

function makeBudgetData(overrides = {}) {
  return {
    budget_total: 8000,
    occupied_total: 3500,
    preoccupying_total: 800,
    annual_spend_total: 2100,
    spend_progress: 0.26,
    approval_progress: 0.44,
    categories: [
      { name: '5G', budget: 2000, occupied: 900, preoccupying: 200, annual_spend: 600, spend_progress: 0.3, approval_progress: 0.45 },
      { name: '传输', budget: 1500, occupied: 700, preoccupying: 100, annual_spend: 500, spend_progress: 0.33, approval_progress: 0.47 },
    ],
    projects: [
      { code: 'XM001', name: '项目A', major: '5G', budget: 12, occupied: 3 },
      { code: 'XM002', name: '项目B', major: '传输', budget: 8, occupied: 1 },
    ],
    ...overrides,
  }
}

function mountBudget(props = {}) {
  return mount(Budget, {
    props: {
      initialData: null,
      latestData: null,
      ...props,
    },
    global: {
      stubs: {
        'v-chart': { template: '<div class="v-chart-stub"></div>' },
      },
    },
  })
}


// ──────────────────────────────────────────────────────────────
// 1. 初始状态
// ──────────────────────────────────────────────────────────────

describe('初始状态', () => {
  it('无数据时显示预算执行上传界面', () => {
    const wrapper = mountBudget()
    expect(wrapper.find('.upload-section').exists()).toBe(true)
    expect(wrapper.text()).toContain('预算立项')
    expect(wrapper.text()).toContain('Budget Approval Intake')
  })

  it('hasData 初始值为 false', () => {
    const wrapper = mountBudget()
    expect(wrapper.vm.hasData).toBe(false)
  })

  it('默认在"预算执行"标签页', () => {
    const wrapper = mountBudget()
    expect(wrapper.vm.batchTab).toBe('budget')
    // 上传界面可见（预算执行 tab 的内容）
    expect(wrapper.find('.upload-section').exists()).toBe(true)
  })
})


// ──────────────────────────────────────────────────────────────
// 2. 数据加载
// ──────────────────────────────────────────────────────────────

describe('数据加载', () => {
  it('传入 initialData 后 hasData 变为 true', async () => {
    const wrapper = mountBudget({
      initialData: makeBudgetData(),
    })
    await nextTick()
    expect(wrapper.vm.hasData).toBe(true)
  })

  it('传入数据后隐藏上传界面', async () => {
    const wrapper = mountBudget({
      initialData: makeBudgetData(),
    })
    await nextTick()
    expect(wrapper.find('.upload-section').exists()).toBe(false)
  })

  it('传入数据后 data 对象包含预算总额', async () => {
    const wrapper = mountBudget({
      initialData: makeBudgetData(),
    })
    await nextTick()
    expect(wrapper.vm.data.budget_total).toBe(8000)
  })

  it('传入数据后 watch 将数据同步到 data ref', async () => {
    const wrapper = mountBudget({
      initialData: makeBudgetData(),
    })
    await nextTick()
    // data 对象包含 budget_total 即说明 watch 已触发
    expect(wrapper.vm.data.budget_total).toBe(8000)
  })
})


// ──────────────────────────────────────────────────────────────
// 3. 标签页切换
// ──────────────────────────────────────────────────────────────

describe('标签页切换', () => {
  it('点击"批次下达"标签切换 batchTab', async () => {
    const wrapper = mountBudget()
    const batchTabBtn = wrapper.find('.bpage-tab:nth-child(2)')
    expect(batchTabBtn.exists()).toBe(true)
    await batchTabBtn.trigger('click')
    await nextTick()
    expect(wrapper.vm.batchTab).toBe('batch')
  })

  it('默认"预算执行"标签激活', () => {
    const wrapper = mountBudget()
    const tabs = wrapper.findAll('.bpage-tab')
    expect(tabs[0].classes()).toContain('active')
  })

  it('切换到批次标签后预算执行内容隐藏', async () => {
    const wrapper = mountBudget()
    await wrapper.findAll('.bpage-tab')[1].trigger('click')
    await nextTick()
    // 预算执行的 upload-section 应该被 v-show 隐藏
    const uploadSection = wrapper.find('.upload-section')
    expect(uploadSection.isVisible()).toBe(false)
  })
})


// ──────────────────────────────────────────────────────────────
// 4. 上传区域交互
// ──────────────────────────────────────────────────────────────

describe('上传区域', () => {
  it('渲染上传指示文字', () => {
    const wrapper = mountBudget()
    expect(wrapper.text()).toContain('拖拽文件到此处')
    expect(wrapper.text()).toContain('预算执行情况')
  })

  it('input[type=file] 隐藏存在', () => {
    const wrapper = mountBudget()
    const input = wrapper.find('input[type="file"]')
    expect(input.exists()).toBe(true)
    expect(input.attributes('hidden')).toBeDefined()
  })

  it('selectedFileName 为空时不显示文件选中状态', () => {
    const wrapper = mountBudget()
    expect(wrapper.find('.selected-file-banner').exists()).toBe(false)
  })

  it('selectedFileName 有值时显示文件选中状态', async () => {
    const wrapper = mountBudget()
    wrapper.vm.selectedFileName = '预算执行情况.xlsx'
    await nextTick()
    expect(wrapper.find('.selected-file-banner').exists()).toBe(true)
    expect(wrapper.text()).toContain('预算执行情况.xlsx')
  })

  it('显示上次上传时间占位', () => {
    const wrapper = mountBudget()
    expect(wrapper.text()).toContain('上次上传')
  })
})


// ──────────────────────────────────────────────────────────────
// 5. KPI count-up 动画
// ──────────────────────────────────────────────────────────────

describe('KPI count-up 动画', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })
  afterEach(() => {
    vi.useRealTimers()
  })

  it('无数据时 animatedBudget 全为零', () => {
    const wrapper = mountBudget()
    expect(wrapper.vm.animatedBudget).toEqual([0, 0, 0, 0])
  })

  it('传入数据后 animatedBudget 有 4 个值', async () => {
    const wrapper = mountBudget({
      initialData: makeBudgetData(),
    })
    await nextTick()
    expect(wrapper.vm.animatedBudget).toHaveLength(4)
  })

  it('动画结束后 animatedBudget 等于目标值', async () => {
    const wrapper = mountBudget({
      initialData: makeBudgetData({ budget_total: 5000, occupied_total: 1000, preoccupying_total: 0, annual_spend_total: 0 }),
    })
    // 推进 fake timers 1 秒让动画跑完
    await vi.advanceTimersByTimeAsync(1000)
    expect(wrapper.vm.animatedBudget[0]).toBe(5000)
    expect(wrapper.vm.animatedBudget[1]).toBe(1000)
  })
})


// ──────────────────────────────────────────────────────────────
// 6. 计算属性
// ──────────────────────────────────────────────────────────────

describe('计算属性', () => {
  it('displayAnalysisDate 为空时返回 null', () => {
    const wrapper = mountBudget()
    expect(wrapper.vm.displayAnalysisDate).toBeNull()
  })

  it('传入 analysisDate 后 displayAnalysisDate 有值', () => {
    const wrapper = mountBudget({ analysisDate: '2026年06月' })
    expect(wrapper.vm.displayAnalysisDate).toBe('2026年06月')
  })

  it('不带历史对比时 shouldShowHistoryCompare 为 false', async () => {
    const wrapper = mountBudget({ initialData: makeBudgetData() })
    await nextTick()
    expect(wrapper.vm.shouldShowHistoryCompare).toBe(false)
  })

  it('带 historyComparison 时为 true', async () => {
    const wrapper = mountBudget({
      initialData: makeBudgetData(),
      historyComparison: { data: makeBudgetData() },
    })
    await nextTick()
    expect(wrapper.vm.shouldShowHistoryCompare).toBe(true)
  })

  it('categories 从 data 中获取', async () => {
    const wrapper = mountBudget({ initialData: makeBudgetData() })
    await nextTick()
    const cats = wrapper.vm.data.categories
    expect(cats).toHaveLength(2)
    expect(cats[0].name).toBe('5G')
  })
})


// ──────────────────────────────────────────────────────────────
// 7. 历史面板
// ──────────────────────────────────────────────────────────────

describe('历史面板', () => {
  it('historyVisible 初始为 false', () => {
    const wrapper = mountBudget()
    expect(wrapper.vm.historyVisible).toBe(false)
  })

  it('isViewingHistory 初始为 false', () => {
    const wrapper = mountBudget()
    expect(wrapper.vm.isViewingHistory).toBe(false)
  })

  it('currentRecordId 初始为 null', () => {
    const wrapper = mountBudget()
    expect(wrapper.vm.currentRecordId).toBeNull()
  })
})


// ──────────────────────────────────────────────────────────────
// 8. 事件发射
// ──────────────────────────────────────────────────────────────

describe('事件发射', () => {
  it('emit 函数存在且可调用', () => {
    const wrapper = mountBudget()
    expect(typeof wrapper.vm.emit).toBe('function')
  })
})


// ──────────────────────────────────────────────────────────────
// 9. 工具函数
// ──────────────────────────────────────────────────────────────

describe('工具函数', () => {
  it('formatNum 格式化数字', () => {
    const wrapper = mountBudget()
    expect(wrapper.vm.formatNum(1234.56)).toBeTypeOf('string')
  })

  it('formatPercent 格式化百分比', () => {
    const wrapper = mountBudget()
    expect(wrapper.vm.formatPercent(0.755)).toBeTypeOf('string')
  })
})


// ──────────────────────────────────────────────────────────────
// 10. 批次下达 — 基础状态
// ──────────────────────────────────────────────────────────────

describe('批次下达 — 基础状态', () => {
  it('batchTab 默认为 budget', () => {
    const wrapper = mountBudget()
    expect(wrapper.vm.batchTab).toBe('budget')
  })

  it('batchData 初始结构正确', () => {
    const wrapper = mountBudget()
    expect(wrapper.vm.batchData.specialties).toEqual([])
    expect(wrapper.vm.batchData.batches).toEqual([])
    expect(wrapper.vm.batchData.totals).toEqual({})
  })

  it('batchModal 初始不可见', () => {
    const wrapper = mountBudget()
    expect(wrapper.vm.batchModal.visible).toBe(false)
    expect(wrapper.vm.batchModal.mode).toBe('create')
    expect(wrapper.vm.batchModal.editId).toBeNull()
  })

  it('specialtyPanel 初始关闭', () => {
    const wrapper = mountBudget()
    expect(wrapper.vm.specialtyPanel).toBe(false)
  })

  it('specialtyList 初始为空', () => {
    const wrapper = mountBudget()
    expect(wrapper.vm.specialtyList).toEqual([])
  })
})


// ──────────────────────────────────────────────────────────────
// 11. 批次下达 — 计算属性
// ──────────────────────────────────────────────────────────────

describe('批次下达 — 计算属性', () => {
  it('grandTotal 计算所有批次总额', () => {
    const wrapper = mountBudget()
    wrapper.vm.batchData = {
      specialties: ['5G', '传输'],
      batches: [],
      totals: { '5G': 100, '传输': 200 },
    }
    expect(wrapper.vm.grandTotal).toBe(300)
  })

  it('grandTotal totals 为空时返回 0', () => {
    const wrapper = mountBudget()
    expect(wrapper.vm.grandTotal).toBe(0)
  })

  it('modalSubtotal 计算当前表单小计', () => {
    const wrapper = mountBudget()
    wrapper.vm.batchModal.form.amounts = { '5G': 100, '传输': '200' }
    expect(wrapper.vm.modalSubtotal).toBe(300)
  })

  it('modalSubtotal 空值忽略', () => {
    const wrapper = mountBudget()
    wrapper.vm.batchModal.form.amounts = { '5G': 100, '传输': null, '无线': '' }
    expect(wrapper.vm.modalSubtotal).toBe(100)
  })

  it('batchSubtotal 计算单批次小计', () => {
    const wrapper = mountBudget()
    const batch = { amounts: { '5G': 50, '传输': 80 } }
    expect(wrapper.vm.batchSubtotal(batch)).toBe(130)
  })

  it('formatBatchNum 格式化批次金额', () => {
    const wrapper = mountBudget()
    expect(wrapper.vm.formatBatchNum(1234.5)).toContain('1,234.50')
    expect(wrapper.vm.formatBatchNum(0)).toBe('—')
    expect(wrapper.vm.formatBatchNum(null)).toBe('—')
  })
})


// ──────────────────────────────────────────────────────────────
// 12. 批次下达 — CRUD 操作
// ──────────────────────────────────────────────────────────────

describe('批次下达 — CRUD 操作', () => {
  it('openCreateModal 设置 modal 状态', () => {
    const wrapper = mountBudget()
    wrapper.vm.batchData.specialties = ['5G', '传输']
    wrapper.vm.openCreateModal()
    expect(wrapper.vm.batchModal.visible).toBe(true)
    expect(wrapper.vm.batchModal.mode).toBe('create')
    expect(wrapper.vm.batchModal.editId).toBeNull()
    expect(wrapper.vm.batchModal.form.amounts).toHaveProperty('5G')
    expect(wrapper.vm.batchModal.form.amounts).toHaveProperty('传输')
    expect(wrapper.vm.batchModal.form.amounts['5G']).toBeNull()
  })

  it('openEditModal 填充已有数据', () => {
    const wrapper = mountBudget()
    wrapper.vm.batchData.specialties = ['5G', '传输']
    const batch = {
      id: 42,
      batch_date: '2026-06-20',
      note: '第一批',
      amounts: { '5G': 100, '传输': 200 },
      notes: { '5G': '备注1' },
    }
    wrapper.vm.openEditModal(batch)
    expect(wrapper.vm.batchModal.visible).toBe(true)
    expect(wrapper.vm.batchModal.mode).toBe('edit')
    expect(wrapper.vm.batchModal.editId).toBe(42)
    expect(wrapper.vm.batchModal.form.batch_date).toBe('2026-06-20')
    expect(wrapper.vm.batchModal.form.note).toBe('第一批')
    expect(wrapper.vm.batchModal.form.amounts['5G']).toBe(100)
    expect(wrapper.vm.batchModal.form.notes['5G']).toBe('备注1')
  })

  it('closeBatchModal 关闭弹窗', () => {
    const wrapper = mountBudget()
    wrapper.vm.batchModal.visible = true
    wrapper.vm.closeBatchModal()
    expect(wrapper.vm.batchModal.visible).toBe(false)
  })

  it('setAmount 设置金额', () => {
    const wrapper = mountBudget()
    wrapper.vm.batchModal.form.amounts = { '5G': null }
    wrapper.vm.setAmount('5G', '100')
    expect(wrapper.vm.batchModal.form.amounts['5G']).toBe(100)
  })

  it('setAmount 空字符串设为 null', () => {
    const wrapper = mountBudget()
    wrapper.vm.batchModal.form.amounts = { '5G': 100 }
    wrapper.vm.setAmount('5G', '')
    expect(wrapper.vm.batchModal.form.amounts['5G']).toBeNull()
  })

  it('toggleNoteField 切换备注字段', () => {
    const wrapper = mountBudget()
    expect(wrapper.vm.noteFieldsOpen['5G']).toBeUndefined()
    wrapper.vm.toggleNoteField('5G')
    expect(wrapper.vm.noteFieldsOpen['5G']).toBe(true)
    wrapper.vm.toggleNoteField('5G')
    expect(wrapper.vm.noteFieldsOpen['5G']).toBe(false)
  })

  it('showCellNote 设置 tooltip 状态', () => {
    const wrapper = mountBudget()
    const event = { currentTarget: { getBoundingClientRect: () => ({ left: 100, bottom: 200 }) } }
    wrapper.vm.showCellNote(event, '测试备注')
    expect(wrapper.vm.cellNoteVisible).toBe(true)
    expect(wrapper.vm.cellNoteText).toBe('测试备注')
    expect(wrapper.vm.cellNoteX).toBe(100)
    expect(wrapper.vm.cellNoteY).toBe(206)
  })

  it('hideCellNote 隐藏 tooltip', () => {
    const wrapper = mountBudget()
    wrapper.vm.cellNoteVisible = true
    wrapper.vm.hideCellNote()
    expect(wrapper.vm.cellNoteVisible).toBe(false)
  })
})


// ──────────────────────────────────────────────────────────────
// 13. 批次下达 — 专业管理
// ──────────────────────────────────────────────────────────────

describe('批次下达 — 专业管理', () => {
  it('openSpecialtyPanel 加载专业列表', async () => {
    api.getSpecialties.mockResolvedValue([
      { id: 1, name: '5G', sort_order: 1 },
      { id: 2, name: '传输', sort_order: 2 },
    ])
    const wrapper = mountBudget()
    await wrapper.vm.openSpecialtyPanel()
    expect(wrapper.vm.specialtyPanel).toBe(true)
    expect(wrapper.vm.specialtyList).toHaveLength(2)
  })

  it('startEditSpecialty 设置编辑状态', () => {
    const wrapper = mountBudget()
    wrapper.vm.startEditSpecialty({ id: 1, name: '5G' })
    expect(wrapper.vm.editingSpecialty).toEqual({ id: 1, name: '5G' })
  })

  it('saveSpecialtyEdit 调用 updateSpecialty', async () => {
    api.updateSpecialty.mockResolvedValue({})
    api.getSpecialties.mockResolvedValue([{ id: 1, name: '传输' }])
    api.getBatchData.mockResolvedValue({ specialties: ['传输'], batches: [], totals: {} })
    const wrapper = mountBudget()
    wrapper.vm.editingSpecialty = { id: 1, name: '传输' }
    await wrapper.vm.saveSpecialtyEdit()
    expect(api.updateSpecialty).toHaveBeenCalledWith(1, { name: '传输' })
    expect(wrapper.vm.editingSpecialty).toBeNull()
  })

  it('saveSpecialtyEdit 无编辑状态时不调用', async () => {
    vi.clearAllMocks()
    const wrapper = mountBudget()
    wrapper.vm.editingSpecialty = null
    await wrapper.vm.saveSpecialtyEdit()
    expect(api.updateSpecialty).not.toHaveBeenCalled()
  })

  it('addNewSpecialty 调用 addSpecialty', async () => {
    vi.clearAllMocks()
    api.addSpecialty.mockResolvedValue({})
    api.getSpecialties.mockResolvedValue([{ id: 1, name: '5G' }])
    api.getBatchData.mockResolvedValue({ specialties: ['5G'], batches: [], totals: {} })
    const wrapper = mountBudget()
    wrapper.vm.newSpecialtyName = '5G'
    await wrapper.vm.addNewSpecialty()
    expect(api.addSpecialty).toHaveBeenCalledWith('5G')
    expect(wrapper.vm.newSpecialtyName).toBe('')
  })

  it('addNewSpecialty 空名称不调用', async () => {
    vi.clearAllMocks()
    const wrapper = mountBudget()
    wrapper.vm.newSpecialtyName = '  '
    await wrapper.vm.addNewSpecialty()
    expect(api.addSpecialty).not.toHaveBeenCalled()
  })

  it('confirmDeleteSpecialty 调用 deleteSpecialty', async () => {
    vi.clearAllMocks()
    const origConfirm = global.confirm
    global.confirm = vi.fn(() => true)
    api.deleteSpecialty.mockResolvedValue({})
    api.getSpecialties.mockResolvedValue([])
    api.getBatchData.mockResolvedValue({ specialties: [], batches: [], totals: {} })
    const wrapper = mountBudget()
    await wrapper.vm.confirmDeleteSpecialty({ id: 1, name: '5G' })
    expect(api.deleteSpecialty).toHaveBeenCalledWith(1)
    global.confirm = origConfirm
  })

  it('confirmDeleteSpecialty 取消时不调用', async () => {
    vi.clearAllMocks()
    const origConfirm = global.confirm
    global.confirm = vi.fn(() => false)
    const wrapper = mountBudget()
    await wrapper.vm.confirmDeleteSpecialty({ id: 1, name: '5G' })
    expect(api.deleteSpecialty).not.toHaveBeenCalled()
    global.confirm = origConfirm
  })
})


// ──────────────────────────────────────────────────────────────
// 14. 批次下达 — 切换与加载
// ──────────────────────────────────────────────────────────────

describe('批次下达 — 切换与加载', () => {
  it('switchToBatchTab 切换标签', async () => {
    api.getBatchData.mockResolvedValue({ specialties: ['5G'], batches: [], totals: {} })
    const wrapper = mountBudget()
    await wrapper.vm.switchToBatchTab()
    expect(wrapper.vm.batchTab).toBe('batch')
  })

  it('switchToBatchTab 加载批次数据', async () => {
    api.getBatchData.mockResolvedValue({
      specialties: ['5G'],
      batches: [{ id: 1, batch_date: '2026-06-20', note: '', amounts: { '5G': 100 }, notes: {} }],
      totals: { '5G': 100 },
    })
    const wrapper = mountBudget()
    await wrapper.vm.switchToBatchTab()
    expect(api.getBatchData).toHaveBeenCalled()
    expect(wrapper.vm.batchData.batches).toHaveLength(1)
  })

  it('switchToBatchTab 已有数据时不重复加载', async () => {
    const wrapper = mountBudget()
    wrapper.vm.batchData.batches = [{ id: 1, amounts: { '5G': 100 }, notes: {} }]
    vi.clearAllMocks()
    await wrapper.vm.switchToBatchTab()
    expect(api.getBatchData).not.toHaveBeenCalled()
  })

  it('loadBatchData 失败时静默处理', async () => {
    api.getBatchData.mockRejectedValue(new Error('网络错误'))
    const wrapper = mountBudget()
    await wrapper.vm.loadBatchData()
    expect(wrapper.vm.batchLoading).toBe(false)
  })
})
