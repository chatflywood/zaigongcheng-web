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

let Budget
beforeEach(async () => {
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
  it('emits 中声明了 dataUpdate 和 restoreLatest', () => {
    const wrapper = mountBudget()
    expect(wrapper.vm.$options.emits).toContain('dataUpdate')
    expect(wrapper.vm.$options.emits).toContain('restoreLatest')
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
