/**
 * App.vue 核心交互单元测试
 *
 * 覆盖：
 *   - 默认视图
 *   - 视图切换
 *   - 计算属性（isAnalystMode / readinessText / canShowKeyIndicators）
 *   - 数据管理器面板
 *   - 历史中心
 *   - 投屏模式
 *   - 状态管理
 */
import { describe, it, expect, vi, beforeAll } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

// ── Mock API 全部函数 ──
vi.mock('../api', () => ({
  getHistory: vi.fn(() => Promise.resolve({ success: false, data: [] })),
  getHistorySnapshot: vi.fn(() => Promise.resolve({ success: false })),
  getBudgetHistory: vi.fn(() => Promise.resolve({ success: false, data: [] })),
  getBudgetHistorySnapshot: vi.fn(() => Promise.resolve({ success: false })),
  getNotifyConfig: vi.fn(() => Promise.resolve({ success: false })),
  saveNotifyConfig: vi.fn(),
  clearNotifyConfig: vi.fn(),
  testNotifyWebhook: vi.fn(),
  pushNotify: vi.fn(),
  generateBriefImage: vi.fn(),
  uploadExcel: vi.fn(),
  uploadBudget: vi.fn(),
  refreshBudgetSpend: vi.fn(),
}))

// ── Stub 子组件（避免 onMounted 中的 API 调用导致报错）──
const StubDashboard = { template: '<div class="stub-dashboard"><slot /></div>', props: ['initialData', 'initialRecordId', 'latestData', 'historyComparison', 'analysisDate', 'snapshotLabel', 'fourClassWarnings'], emits: ['dataUpdate', 'restoreLatest', 'warningsUpdate'] }
const StubBudget = { template: '<div class="stub-budget"><slot /></div>', props: ['initialData', 'latestData', 'historyComparison', 'analysisDate', 'snapshotLabel'], emits: ['dataUpdate', 'restoreLatest'] }
const StubKeyIndicators = { template: '<div class="stub-key-indicators"><slot /></div>', props: ['zaigongData', 'budgetData', 'fourClassWarnings', 'zaigongLatestDate', 'budgetLatestDate'], emits: [] }
const StubArchive = { template: '<div class="stub-archive"><slot /></div>', props: [], emits: [] }

let App
beforeAll(async () => {
  App = (await import('../App.vue')).default
}, 15000)

function mountApp() {
  return mount(App, {
    global: {
      stubs: {
        Dashboard: StubDashboard,
        Budget: StubBudget,
        KeyIndicators: StubKeyIndicators,
        Archive: StubArchive,
      },
    },
  })
}


// ──────────────────────────────────────────────────────────────
// 1. 初始状态
// ──────────────────────────────────────────────────────────────

describe('初始状态', () => {
  it('默认展示关键指标页', () => {
    const wrapper = mountApp()
    expect(wrapper.vm.currentView).toBe('key-indicators')
  })

  it('关键指标页为默认视图时子组件渲染', () => {
    const wrapper = mountApp()
    expect(wrapper.find('.stub-key-indicators').exists()).toBe(true)
  })

  it('默认不在分析师模式（关键指标页不算分析师模式）', () => {
    const wrapper = mountApp()
    expect(wrapper.vm.isAnalystMode).toBe(false)
  })

  it('历史中心默认关闭', () => {
    const wrapper = mountApp()
    expect(wrapper.vm.historyCenterVisible).toBe(false)
  })

  it('数据管理器默认关闭', () => {
    const wrapper = mountApp()
    expect(wrapper.vm.showDataManager).toBe(false)
  })

  it('投屏模式默认关闭', () => {
    const wrapper = mountApp()
    expect(wrapper.vm.presentationMode).toBe(false)
  })
})


// ──────────────────────────────────────────────────────────────
// 2. 视图切换
// ──────────────────────────────────────────────────────────────

describe('视图切换', () => {
  it('切换到在建工程视图', async () => {
    const wrapper = mountApp()
    wrapper.vm.currentView = 'zaigong'
    await nextTick()
    expect(wrapper.vm.currentView).toBe('zaigong')
  })

  it('切换到预算立项视图', async () => {
    const wrapper = mountApp()
    wrapper.vm.currentView = 'budget'
    await nextTick()
    expect(wrapper.vm.currentView).toBe('budget')
  })

  it('切换到数据档案视图', async () => {
    const wrapper = mountApp()
    wrapper.vm.currentView = 'archive'
    await nextTick()
    expect(wrapper.vm.currentView).toBe('archive')
  })

  it('切换回关键指标', async () => {
    const wrapper = mountApp()
    wrapper.vm.currentView = 'zaigong'
    await nextTick()
    wrapper.vm.currentView = 'key-indicators'
    await nextTick()
    expect(wrapper.vm.currentView).toBe('key-indicators')
  })
})


// ──────────────────────────────────────────────────────────────
// 3. 计算属性
// ──────────────────────────────────────────────────────────────

describe('计算属性', () => {
  it('在建工程视图是分析师模式', async () => {
    const wrapper = mountApp()
    wrapper.vm.currentView = 'zaigong'
    await nextTick()
    expect(wrapper.vm.isAnalystMode).toBe(true)
  })

  it('预算立项视图是分析师模式', async () => {
    const wrapper = mountApp()
    wrapper.vm.currentView = 'budget'
    await nextTick()
    expect(wrapper.vm.isAnalystMode).toBe(true)
  })

  it('数据档案视图是分析师模式', async () => {
    const wrapper = mountApp()
    wrapper.vm.currentView = 'archive'
    await nextTick()
    expect(wrapper.vm.isAnalystMode).toBe(true)
  })

  it('canShowKeyIndicators 无数据时返回 falsy', () => {
    const wrapper = mountApp()
    // zaigongData 和 budgetData 均为 null → 返回 null
    expect(wrapper.vm.canShowKeyIndicators).toBeFalsy()
  })

  it('有在建工程数据但无预算数据时 canShowKeyIndicators 仍为 falsy', async () => {
    const wrapper = mountApp()
    wrapper.vm.zaigongData = { metrics: { capital: 100 } }
    await nextTick()
    // budgetData 仍为 null → falsy
    expect(wrapper.vm.canShowKeyIndicators).toBeFalsy()
  })

  it('两个数据源都有时 canShowKeyIndicators 为 truthy', async () => {
    const wrapper = mountApp()
    wrapper.vm.zaigongData = { metrics: { capital: 100 } }
    wrapper.vm.budgetData = { budget_total: 5000 }
    await nextTick()
    expect(wrapper.vm.canShowKeyIndicators).toBeTruthy()
  })

  it('readinessText 反映数据就绪状态', () => {
    const wrapper = mountApp()
    expect(wrapper.vm.readinessText).toBeTypeOf('string')
  })

  it('currentMonthLabel 格式为 YYYY.MM · 第 Q 季度', () => {
    const wrapper = mountApp()
    const label = wrapper.vm.currentMonthLabel
    expect(label).toMatch(/^\d{4}\.\d{2} · 第 [1-4] 季度$/)
  })
})


// ──────────────────────────────────────────────────────────────
// 4. 数据管理器面板
// ──────────────────────────────────────────────────────────────

describe('数据管理器面板', () => {
  it('openDataManager 打开面板', () => {
    const wrapper = mountApp()
    wrapper.vm.openDataManager()
    expect(wrapper.vm.showDataManager).toBe(true)
  })

  it('面板打开后 dmZaigongFileName 为空', () => {
    const wrapper = mountApp()
    wrapper.vm.openDataManager()
    expect(wrapper.vm.dmZaigongFileName).toBe('')
  })

  it('面板打开后 dmBudgetFileName 为空', () => {
    const wrapper = mountApp()
    wrapper.vm.openDataManager()
    expect(wrapper.vm.dmBudgetFileName).toBe('')
  })

  it('面板打开后 dmTargetValue 从 localStorage 读取目标值', async () => {
    localStorage.setItem('zaigong_target_value', '888')
    const wrapper = mountApp()
    wrapper.vm.openDataManager()
    await nextTick()
    expect(wrapper.vm.dmTargetValue).toBe(888)
    localStorage.removeItem('zaigong_target_value')
  })

  it('dmPickZaigong 触发文件选择器', () => {
    const wrapper = mountApp()
    // dmZaigongInput ref 在 jsdom 中为 null，但函数不应报错
    expect(() => wrapper.vm.dmPickZaigong()).not.toThrow()
  })

  it('dmPickBudget 触发文件选择器', () => {
    const wrapper = mountApp()
    expect(() => wrapper.vm.dmPickBudget()).not.toThrow()
  })
})


// ──────────────────────────────────────────────────────────────
// 5. 历史中心
// ──────────────────────────────────────────────────────────────

describe('历史中心', () => {
  it('historyCenterVisible 初始 false', () => {
    const wrapper = mountApp()
    expect(wrapper.vm.historyCenterVisible).toBe(false)
  })

  it('historyTab 默认 all', () => {
    const wrapper = mountApp()
    expect(wrapper.vm.historyTab).toBe('all')
  })

  it('zaigongHistory 初始空数组', () => {
    const wrapper = mountApp()
    expect(wrapper.vm.zaigongHistory).toEqual([])
  })

  it('budgetHistory 初始空数组', () => {
    const wrapper = mountApp()
    expect(wrapper.vm.budgetHistory).toEqual([])
  })

  it('比较选择初始为 null', () => {
    const wrapper = mountApp()
    expect(wrapper.vm.zaigongCompareSelection.left).toBeNull()
    expect(wrapper.vm.zaigongCompareSelection.right).toBeNull()
    expect(wrapper.vm.budgetCompareSelection.left).toBeNull()
    expect(wrapper.vm.budgetCompareSelection.right).toBeNull()
  })
})


// ──────────────────────────────────────────────────────────────
// 6. 投屏模式
// ──────────────────────────────────────────────────────────────

describe('投屏模式', () => {
  it('presentationMode 初始 false', () => {
    const wrapper = mountApp()
    expect(wrapper.vm.presentationMode).toBe(false)
  })

  it('切换投屏模式', async () => {
    const wrapper = mountApp()
    wrapper.vm.presentationMode = true
    await nextTick()
    expect(wrapper.vm.presentationMode).toBe(true)
    wrapper.vm.presentationMode = false
    await nextTick()
    expect(wrapper.vm.presentationMode).toBe(false)
  })
})


// ──────────────────────────────────────────────────────────────
// 7. 工具函数
// ──────────────────────────────────────────────────────────────

describe('工具函数', () => {
  it('daysSince 计算天数差', () => {
    const wrapper = mountApp()
    const today = new Date().toISOString().split('T')[0]
    expect(wrapper.vm.daysSince(today)).toBe(0)
  })

  it('daysSince 对旧日期返回正数', () => {
    const wrapper = mountApp()
    expect(wrapper.vm.daysSince('2020-01-01')).toBeGreaterThan(365)
  })

  it('dmFreshClass 返回数据新鲜度 CSS 类名', () => {
    const wrapper = mountApp()
    // 10 天 → stale-ok, 40 天 → stale-warn, 70 天 → stale-bad
    expect(wrapper.vm.dmFreshClass(10)).toContain('stale-ok')
    expect(wrapper.vm.dmFreshClass(40)).toContain('stale-warn')
    expect(wrapper.vm.dmFreshClass(70)).toContain('stale-bad')
    expect(wrapper.vm.dmFreshClass(null)).toBe('')
  })
})


// ──────────────────────────────────────────────────────────────
// 8. 状态管理
// ──────────────────────────────────────────────────────────────

describe('状态管理', () => {
  it('设置 zaigongLatestData 后可见', async () => {
    const wrapper = mountApp()
    wrapper.vm.zaigongLatestData = { dashboard: { metrics: {} } }
    await nextTick()
    expect(wrapper.vm.zaigongLatestData).not.toBeNull()
  })

  it('设置 budgetLatestData 后可见', async () => {
    const wrapper = mountApp()
    wrapper.vm.budgetLatestData = { budget_total: 100 }
    await nextTick()
    expect(wrapper.vm.budgetLatestData).not.toBeNull()
  })

  it('zaigongLatestDate 可设置和读取', async () => {
    const wrapper = mountApp()
    wrapper.vm.zaigongLatestDate = '2026-06-20'
    await nextTick()
    expect(wrapper.vm.zaigongLatestDate).toBe('2026-06-20')
  })

  it('budgetLatestDate 可设置和读取', async () => {
    const wrapper = mountApp()
    wrapper.vm.budgetLatestDate = '2026-06-15'
    await nextTick()
    expect(wrapper.vm.budgetLatestDate).toBe('2026-06-15')
  })
})
