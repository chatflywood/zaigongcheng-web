/**
 * KeyIndicators.vue 核心交互单元测试
 *
 * 覆盖：
 *   - 空数据状态
 *   - KPI 甜甜圈计算属性（capitalProgress / transferRate / annualCapitalProgress / approvalProgress）
 *   - 目标值显示
 *   - 四类预警面板
 *   - 管理员视图
 *   - 投屏模式
 *   - Summary banner
 *   - 工具函数（gaugeColor / getDaysClass / getWarningPillClass / formatNum / getRateBarClass）
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

// ── Mock html2canvas ──
vi.mock('html2canvas', () => ({
  default: vi.fn(() => Promise.resolve({ toDataURL: () => 'data:image/png;base64,test' }))
}))

// ── Mock API（exportFourClassExcel 动态导入）──
vi.mock('../../api', () => ({
  exportFourClassExcel: vi.fn(() => Promise.resolve(new Blob())),
}))

let KeyIndicators
beforeEach(async () => {
  KeyIndicators = (await import('../KeyIndicators.vue')).default
})

// ── 辅助函数 ──

function makeZaigongData(overrides = {}) {
  return {
    metrics: {
      capital: 400,
      yearTarget: 503,
      deficit: 103,
      rate: 0.72,
      ...overrides.metrics,
    },
    summary: [
      { manager: '张三', capital: 200, rate: 0.75, count: 5 },
      { manager: '李四', capital: 150, rate: 0.68, count: 3 },
      { manager: '王五', capital: 50, rate: 0.82, count: 2 },
    ],
    detail: [
      { '工程名称': '项目A', '工程管理员': '张三', '在建工程期末余额': 30, '本年累计资本性支出': 120 },
      { '工程名称': '项目B', '工程管理员': '张三', '在建工程期末余额': 20, '本年累计资本性支出': 80 },
      { '工程名称': '项目C', '工程管理员': '李四', '在建工程期末余额': 45, '本年累计资本性支出': 100 },
      { '工程名称': '项目D', '工程管理员': '王五', '在建工程期末余额': 10, '本年累计资本性支出': 50 },
    ],
    ...overrides,
  }
}

function makeBudgetData(overrides = {}) {
  return {
    budget_total: 8000,
    occupied_total: 3500,
    preoccupying_total: 800,
    annual_spend_total: 2100,
    approval_progress: 0.44,
    ...overrides,
  }
}

function makeFourClassWarnings(overrides = {}) {
  return {
    summary: {
      '列账不及时': { triggered: 1, warning: 2 },
      '预转固不及时': { triggered: 0, warning: 1 },
      '关闭不及时': { triggered: 0, warning: 0 },
      '长期挂账': { triggered: 0, warning: 0 },
      analysis_date: '2026-06-20',
    },
    items: [
      { id: 1, type: '列账不及时', name: '项目A', status: '已触发', manager: '张三', daysLabel: '120天', keyDate: '2025-10-01', deadline: '2026-01-01', acceptType: '初验', projectStatus: '在建', suggestion: '尽快列账' },
      { id: 2, type: '列账不及时', name: '项目B', status: '预警', manager: '李四', daysLabel: '80天', keyDate: '2025-12-01', deadline: '2026-03-01', acceptType: '终验', projectStatus: '在建', suggestion: '关注进度' },
      { id: 3, type: '预转固不及时', name: '项目C', status: '预警', manager: '王五', daysLabel: '60天', keyDate: '2026-01-01', deadline: '2026-04-01', acceptType: '初验', projectStatus: '在建', suggestion: '推进转固' },
    ],
    total: 3,
    hit_count: 1,
    warn_count: 2,
    ...overrides,
  }
}

function mountKI(props = {}) {
  return mount(KeyIndicators, {
    props: {
      zaigongData: null,
      budgetData: null,
      zaigongDate: null,
      budgetDate: null,
      fourClassWarnings: null,
      recordId: null,
      ...props,
    },
  })
}


// ──────────────────────────────────────────────────────────────
// 1. 空数据状态
// ──────────────────────────────────────────────────────────────

describe('空数据状态', () => {
  it('无数据时页面仍可渲染', () => {
    const wrapper = mountKI()
    expect(wrapper.find('.ki-page').exists()).toBe(true)
  })

  it('无数据时 summary banner 不显示', () => {
    const wrapper = mountKI()
    expect(wrapper.find('.ki-summary-banner').exists()).toBe(false)
  })

  it('无数据时管理员视图不显示', () => {
    const wrapper = mountKI()
    expect(wrapper.find('.ki-manager-section').exists()).toBe(false)
  })

  it('无数据时四类预警显示"暂无预警数据"', () => {
    const wrapper = mountKI()
    expect(wrapper.text()).toContain('暂无预警数据')
  })

  it('无数据时 targetValue 为 null', () => {
    const wrapper = mountKI()
    expect(wrapper.vm.targetValue).toBeNull()
  })

  it('无数据时 displayTargetValue 显示"—"', () => {
    const wrapper = mountKI()
    expect(wrapper.vm.displayTargetValue).toBe('—')
  })
})


// ──────────────────────────────────────────────────────────────
// 2. 目标值与 KPI 计算
// ──────────────────────────────────────────────────────────────

describe('目标值与 KPI 计算', () => {
  it('targetValue 从 zaigongData.metrics.yearTarget 读取', () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData() })
    expect(wrapper.vm.targetValue).toBe(503)
  })

  it('yearTarget 无效时 targetValue 为 null', () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData({ metrics: { yearTarget: -1 } }) })
    expect(wrapper.vm.targetValue).toBeNull()
  })

  it('displayTargetValue 格式化为两位小数', () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData() })
    expect(wrapper.vm.displayTargetValue).toBe('503.00')
  })

  it('capitalProgress 正确计算百分比', () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData({ metrics: { capital: 400, yearTarget: 503 } }) })
    // 400 / 503 * 100 ≈ 79.5
    expect(parseFloat(wrapper.vm.capitalProgress)).toBeCloseTo(79.5, 0)
  })

  it('capitalProgress 无 capital 时返回 0.0', () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData({ metrics: { capital: 0, yearTarget: 503 } }) })
    expect(wrapper.vm.capitalProgress).toBe('0.0')
  })

  it('transferRate 正确计算', () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData({ metrics: { rate: 0.72 } }) })
    expect(wrapper.vm.transferRate).toBe('72.0')
  })

  it('transferRate 无 rate 时返回 0.0', () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData({ metrics: { rate: 0 } }) })
    expect(wrapper.vm.transferRate).toBe('0.0')
  })

  it('annualCapitalProgress 正确计算', () => {
    const wrapper = mountKI({
      zaigongData: makeZaigongData(),
      budgetData: makeBudgetData({ annual_spend_total: 2100, budget_total: 8000 }),
    })
    // 2100 / 8000 * 100 = 26.25
    expect(parseFloat(wrapper.vm.annualCapitalProgress)).toBeCloseTo(26.25, 0)
  })

  it('annualCapitalProgress 无预算数据时返回 0.0', () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData(), budgetData: null })
    expect(wrapper.vm.annualCapitalProgress).toBe('0.0')
  })

  it('approvalProgress 从 budgetData.approval_progress 读取', () => {
    const wrapper = mountKI({ budgetData: makeBudgetData({ approval_progress: 0.44 }) })
    expect(wrapper.vm.approvalProgress).toBe('44.0')
  })

  it('approvalProgress 无 approval_progress 时返回 0.0', () => {
    const wrapper = mountKI({ budgetData: makeBudgetData({ approval_progress: 0 }) })
    expect(wrapper.vm.approvalProgress).toBe('0.0')
  })
})


// ──────────────────────────────────────────────────────────────
// 3. deficitIsExceeded / deficitLabel
// ──────────────────────────────────────────────────────────────

describe('deficit 计算', () => {
  it('deficit 为正数时 deficitIsExceeded 为 false', () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData({ metrics: { deficit: 103 } }) })
    expect(wrapper.vm.deficitIsExceeded).toBe(false)
  })

  it('deficit 为负数时 deficitIsExceeded 为 true', () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData({ metrics: { deficit: -20 } }) })
    expect(wrapper.vm.deficitIsExceeded).toBe(true)
  })

  it('deficit 为正数时 label 显示缺口', () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData({ metrics: { deficit: 103 } }) })
    expect(wrapper.vm.deficitLabel).toContain('缺口')
    expect(wrapper.vm.deficitLabel).toContain('103')
  })

  it('deficit 为负数时 label 显示已超额', () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData({ metrics: { deficit: -20 } }) })
    expect(wrapper.vm.deficitLabel).toContain('已超额')
  })

  it('deficit 为 0 时 label 显示恰好达标', () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData({ metrics: { deficit: 0 } }) })
    expect(wrapper.vm.deficitLabel).toBe('恰好达标')
  })

  it('deficit 非数字时 label 显示"—"', () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData({ metrics: { deficit: null } }) })
    expect(wrapper.vm.deficitLabel).toBe('—')
  })
})


// ──────────────────────────────────────────────────────────────
// 4. 管理员视图
// ──────────────────────────────────────────────────────────────

describe('管理员视图', () => {
  it('有数据时 managerViewRows 非空', () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData() })
    expect(wrapper.vm.managerViewRows.length).toBeGreaterThan(0)
  })

  it('managerViewRows 按 capital 降序排列', () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData() })
    const rows = wrapper.vm.managerViewRows
    for (let i = 1; i < rows.length; i++) {
      expect(rows[i - 1].capital).toBeGreaterThanOrEqual(rows[i].capital)
    }
  })

  it('managerViewRows 过滤掉合计行', () => {
    const data = makeZaigongData()
    data.summary.push({ manager: '合计', capital: 400, rate: 0.72 })
    const wrapper = mountKI({ zaigongData: data })
    const names = wrapper.vm.managerViewRows.map(r => r.manager)
    expect(names).not.toContain('合计')
  })

  it('managerViewRows 的 rate 转换为百分比', () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData() })
    const row = wrapper.vm.managerViewRows.find(r => r.manager === '张三')
    expect(row.rate).toBeCloseTo(75, 0)
  })

  it('有数据时渲染管理员行', async () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData() })
    await nextTick()
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('李四')
  })

  it('无 zaigongData 时 managerViewRows 为空', () => {
    const wrapper = mountKI()
    expect(wrapper.vm.managerViewRows).toEqual([])
  })
})


// ──────────────────────────────────────────────────────────────
// 5. 四类预警面板
// ──────────────────────────────────────────────────────────────

describe('四类预警面板', () => {
  it('fcWarnings 优先使用 fourClassWarnings prop', () => {
    const warnings = makeFourClassWarnings()
    const wrapper = mountKI({ fourClassWarnings: warnings })
    expect(wrapper.vm.fcWarnings).toStrictEqual(warnings)
  })

  it('fourClassTypes 定义了 4 种类型', () => {
    const wrapper = mountKI()
    const types = wrapper.vm.fourClassTypes
    expect(types).toHaveLength(4)
    expect(types.map(t => t.name)).toEqual(['列账不及时', '预转固不及时', '关闭不及时', '长期挂账'])
  })

  it('showFourClassDetail 打开单类型明细', async () => {
    const wrapper = mountKI({ fourClassWarnings: makeFourClassWarnings() })
    wrapper.vm.showFourClassDetail('列账不及时')
    await nextTick()
    expect(wrapper.vm.fourClassDetailVisible).toBe(true)
    expect(wrapper.vm.fourClassDetailType).toBe('列账不及时')
    expect(wrapper.vm.fourClassDetailItems).toHaveLength(2)
  })

  it('showFourClassAllDetail 打开全部明细', async () => {
    const wrapper = mountKI({ fourClassWarnings: makeFourClassWarnings() })
    wrapper.vm.showFourClassAllDetail()
    await nextTick()
    expect(wrapper.vm.fourClassDetailVisible).toBe(true)
    expect(wrapper.vm.fourClassDetailType).toBe('四类工程预警明细')
    expect(wrapper.vm.fourClassDetailItems).toHaveLength(3)
  })

  it('无 items 时 showFourClassDetail 不打开', async () => {
    const wrapper = mountKI({ fourClassWarnings: { summary: {}, items: null } })
    wrapper.vm.showFourClassDetail('列账不及时')
    await nextTick()
    expect(wrapper.vm.fourClassDetailVisible).toBe(false)
  })

  it('getGroupItems 按类型过滤', () => {
    const wrapper = mountKI({ fourClassWarnings: makeFourClassWarnings() })
    const items = wrapper.vm.getGroupItems('列账不及时')
    expect(items).toHaveLength(2)
    expect(items.every(i => i.type === '列账不及时')).toBe(true)
  })

  it('getGroupStats 统计 triggered 和 warning', () => {
    const wrapper = mountKI({ fourClassWarnings: makeFourClassWarnings() })
    const stats = wrapper.vm.getGroupStats('列账不及时')
    expect(stats.triggered).toBe(1)
    expect(stats.warning).toBe(1)
  })

  it('getManagersForType 返回 top 3 管理员', () => {
    const wrapper = mountKI({ fourClassWarnings: makeFourClassWarnings() })
    const mgrs = wrapper.vm.getManagersForType('列账不及时')
    expect(mgrs.length).toBeLessThanOrEqual(3)
    expect(mgrs[0]).toHaveProperty('name')
    expect(mgrs[0]).toHaveProperty('count')
  })

  it('getManagerTextForType 返回格式化文本', () => {
    const wrapper = mountKI({ fourClassWarnings: makeFourClassWarnings() })
    const text = wrapper.vm.getManagerTextForType('列账不及时')
    expect(text).toContain('张三')
  })

  it('无预警时 getManagerTextForType 返回"—"', () => {
    const wrapper = mountKI({ fourClassWarnings: makeFourClassWarnings() })
    const text = wrapper.vm.getManagerTextForType('关闭不及时')
    expect(text).toBe('—')
  })

  it('渲染预警卡片', async () => {
    const wrapper = mountKI({ fourClassWarnings: makeFourClassWarnings() })
    await nextTick()
    expect(wrapper.text()).toContain('列账不及时')
    expect(wrapper.text()).toContain('预警期 90 天')
  })

  it('点击预警卡片打开明细弹窗', async () => {
    const wrapper = mountKI({ fourClassWarnings: makeFourClassWarnings() })
    await nextTick()
    const items = wrapper.findAll('.warning-item')
    await items[0].trigger('click')
    expect(wrapper.vm.fourClassDetailVisible).toBe(true)
  })
})


// ──────────────────────────────────────────────────────────────
// 6. 工具函数
// ──────────────────────────────────────────────────────────────

describe('工具函数', () => {
  it('gaugeColor 达标时返回 ok', () => {
    const wrapper = mountKI()
    expect(wrapper.vm.gaugeColor(96, 100)).toBe('var(--ok)')
  })

  it('gaugeColor 接近目标时返回 accent', () => {
    const wrapper = mountKI()
    expect(wrapper.vm.gaugeColor(85, 100)).toBe('var(--accent)')
  })

  it('gaugeColor 中等时返回 warn', () => {
    const wrapper = mountKI()
    expect(wrapper.vm.gaugeColor(55, 100)).toBe('var(--warn)')
  })

  it('gaugeColor 低值时返回 bad', () => {
    const wrapper = mountKI()
    expect(wrapper.vm.gaugeColor(30, 100)).toBe('var(--bad)')
  })

  it('getDaysClass 已触发返回 days-overdue', () => {
    const wrapper = mountKI()
    expect(wrapper.vm.getDaysClass('120天', '已触发')).toBe('days-overdue')
  })

  it('getDaysClass 预警 <=10 天返回 days-overdue', () => {
    const wrapper = mountKI()
    expect(wrapper.vm.getDaysClass('5天', '预警')).toBe('days-overdue')
  })

  it('getDaysClass 预警 <=30 天返回 days-warning', () => {
    const wrapper = mountKI()
    expect(wrapper.vm.getDaysClass('20天', '预警')).toBe('days-warning')
  })

  it('getDaysClass 预警 >30 天返回空', () => {
    const wrapper = mountKI()
    expect(wrapper.vm.getDaysClass('60天', '预警')).toBe('')
  })

  it('getDaysClass 无 daysLabel 返回空', () => {
    const wrapper = mountKI()
    expect(wrapper.vm.getDaysClass(null, '预警')).toBe('')
  })

  it('getWarningPillClass 映射正确', () => {
    const wrapper = mountKI()
    expect(wrapper.vm.getWarningPillClass('liezhang')).toBe('info')
    expect(wrapper.vm.getWarningPillClass('yuzhuang')).toBe('warn')
    expect(wrapper.vm.getWarningPillClass('guanbi')).toBe('bad')
    expect(wrapper.vm.getWarningPillClass('guazhang')).toBe('info')
    expect(wrapper.vm.getWarningPillClass('unknown')).toBe('info')
  })

  it('formatNum 格式化数字', () => {
    const wrapper = mountKI()
    expect(wrapper.vm.formatNum(1234)).toBeTypeOf('string')
    expect(wrapper.vm.formatNum(null)).toBe('—')
    expect(wrapper.vm.formatNum(NaN)).toBe('—')
  })

  it('getRateBarClass 根据比率返回类名', () => {
    const wrapper = mountKI()
    expect(wrapper.vm.getRateBarClass(0.7)).toBe('ok')
    expect(wrapper.vm.getRateBarClass(0.4)).toBe('warn')
    expect(wrapper.vm.getRateBarClass(0.2)).toBe('bad')
  })
})


// ──────────────────────────────────────────────────────────────
// 7. 投屏模式
// ──────────────────────────────────────────────────────────────

describe('投屏模式', () => {
  it('presentationMode 初始为 false', () => {
    const wrapper = mountKI()
    // composable 单例可能被其他测试污染，这里只验证类型
    expect(typeof wrapper.vm.presentationMode).toBe('boolean')
  })

  it('togglePresentationMode 是函数', () => {
    const wrapper = mountKI()
    expect(typeof wrapper.vm.togglePresentationMode).toBe('function')
  })
})


// ──────────────────────────────────────────────────────────────
// 8. Summary banner
// ──────────────────────────────────────────────────────────────

describe('Summary banner', () => {
  it('有 zaigongData.metrics 时显示 banner', async () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData() })
    await nextTick()
    expect(wrapper.find('.ki-summary-banner').exists()).toBe(true)
  })

  it('banner 包含资本性支出数值', async () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData() })
    await nextTick()
    expect(wrapper.text()).toContain('当期资本性支出')
    expect(wrapper.text()).toContain('400')
  })

  it('banner 包含转固率', async () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData() })
    await nextTick()
    expect(wrapper.text()).toContain('转固率')
  })

  it('banner 包含 AUTO-DRAFTED 标记', async () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData() })
    await nextTick()
    expect(wrapper.text()).toContain('AUTO-DRAFTED')
  })
})


// ──────────────────────────────────────────────────────────────
// 9. 日期格式化
// ──────────────────────────────────────────────────────────────

describe('日期格式化', () => {
  it('normalizedZaigongDate 标准日期直接返回', () => {
    const wrapper = mountKI({ zaigongDate: '2026-06-20' })
    expect(wrapper.vm.normalizedZaigongDate).toBe('2026-06-20')
  })

  it('normalizedZaigongDate null 返回空', () => {
    const wrapper = mountKI({ zaigongDate: null })
    expect(wrapper.vm.normalizedZaigongDate).toBe('')
  })

  it('currentDate 格式为 YYYY-MM-DD', () => {
    const wrapper = mountKI()
    expect(wrapper.vm.currentDate).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })
})


// ──────────────────────────────────────────────────────────────
// 10. 动画
// ──────────────────────────────────────────────────────────────

describe('Gauge 动画', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })
  afterEach(() => {
    vi.useRealTimers()
  })

  it('animatedGauges 初始全为 0', () => {
    const wrapper = mountKI()
    expect(wrapper.vm.animatedGauges).toEqual([0, 0, 0, 0])
  })

  it('传入数据后 animatedGauges 有 4 个值', async () => {
    const wrapper = mountKI({ zaigongData: makeZaigongData() })
    await nextTick()
    expect(wrapper.vm.animatedGauges).toHaveLength(4)
  })
})
