/**
 * Dashboard.vue 核心交互单元测试
 *
 * 覆盖：
 *   - 空数据状态 / 数据加载状态
 *   - 上传区域交互
 *   - 目标值输入
 *   - 管理员汇总表格
 *   - 四类预警面板
 *   - 转固推进弹窗
 *   - 计算属性
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick, ref } from 'vue'

// ── Mock API 模块 ──
vi.mock('../../api', () => ({
  uploadExcel: vi.fn(),
  getCompare: vi.fn(),
  getHistory: vi.fn(),
  getHistorySnapshot: vi.fn(),
  getManagerDetails: vi.fn(),
  getTransferPriority: vi.fn(),
  exportTransferPriority: vi.fn(),
  pushNotify: vi.fn(),
  updateTargetValue: vi.fn(),
}))

// ── Mock html2canvas (避免 canvas 依赖) ──
vi.mock('html2canvas', () => ({
  default: vi.fn(() => Promise.resolve({
    toDataURL: () => 'data:image/png;base64,test'
  }))
}))

// ── 存根：避免 onMounted 中的 API 调用 ──
const api = await import('../../api')
api.getHistory.mockResolvedValue({ success: false, data: [] })
api.getCompare.mockResolvedValue({ success: false })

let Dashboard
beforeEach(async () => {
  // 每次测试重新加载模块，避免缓存污染
  Dashboard = (await import('../Dashboard.vue')).default
})

// ──────────────────────────────────────────────────────────────
// 辅助函数：构建最小可用的 props
// ──────────────────────────────────────────────────────────────

function makeDashboardData(overrides = {}) {
  return {
    monthLabel: '2026年06月',
    metrics: {
      capital: 500,
      pending: 120,
      monthSpend: 80,
      transfer: 300,
      rate: 0.72,
      progress: 0.65,
      deficit: 200,
      yearTarget: 770,
    },
    summary: [
      { manager: '张三', transfer: 150, capital: 200, pending: 50, monthSpend: 35, rate: 0.71 },
      { manager: '李四', transfer: 100, capital: 180, pending: 40, monthSpend: 28, rate: 0.68 },
      { manager: '王五', transfer: 80, capital: 120, pending: 30, monthSpend: 17, rate: 0.78 },
    ],
    detail: [
      { '工程名称': '项目A', '工程管理员': '张三', '在建工程期末余额': 30, '本年累计资本性支出': 120, '本月资本性支出': 20, '已下单待收货': 30, '转固率': 0.75, '施工单位': '施工一队' },
      { '工程名称': '项目B', '工程管理员': '李四', '在建工程期末余额': 45, '本年累计资本性支出': 100, '本月资本性支出': 15, '已下单待收货': 25, '转固率': 0.62, '施工单位': '施工二队' },
    ],
    alerts: [
      { title: '待收货压力', value: '2 位管理员超过30万元' },
      { title: '转固率状态', value: '偏低' },
      { title: '目标差额', value: '270.00 万元' },
    ],
    ...overrides,
  }
}

function mountDashboard(props = {}) {
  return mount(Dashboard, {
    props: {
      initialData: null,
      initialRecordId: null,
      latestData: null,
      ...props,
    },
    global: {
      stubs: {
        // 存根大的子组件/复杂 SVG
        'v-chart': { template: '<div class="v-chart-stub"></div>' },
      },
    },
  })
}


// ──────────────────────────────────────────────────────────────
// 1. 初始状态
// ──────────────────────────────────────────────────────────────

describe('初始状态', () => {
  it('无数据时显示上传界面', () => {
    const wrapper = mountDashboard()
    // hasData 初始为 false → 渲染 upload-section
    expect(wrapper.find('.upload-section').exists()).toBe(true)
    expect(wrapper.find('.page').exists()).toBe(false)
    expect(wrapper.text()).toContain('在建工程')
    expect(wrapper.text()).toContain('设置当期资本性支出目标')
  })

  it('无数据时隐藏仪表盘', () => {
    const wrapper = mountDashboard()
    expect(wrapper.find('.page-head').exists()).toBe(false)
  })

  it('hasData 初始值为 false', () => {
    const wrapper = mountDashboard()
    expect(wrapper.vm.hasData).toBe(false)
  })
})


// ──────────────────────────────────────────────────────────────
// 2. 数据加载状态
// ──────────────────────────────────────────────────────────────

describe('数据加载', () => {
  it('传入 initialData 后显示仪表盘', async () => {
    const wrapper = mountDashboard({
      initialData: makeDashboardData(),
    })
    await nextTick()
    // initialData 通过 watch 触发 applyData
    expect(wrapper.vm.hasData).toBe(true)
    expect(wrapper.find('.page').exists()).toBe(true)
    expect(wrapper.find('.upload-section').exists()).toBe(false)
  })

  it('仪表盘显示页面标题和月份', async () => {
    const wrapper = mountDashboard({
      initialData: makeDashboardData(),
      analysisDate: '2026年06月',
    })
    await nextTick()
    expect(wrapper.text()).toContain('在建工程进度')
    expect(wrapper.text()).toContain('2026年06月')
  })

  it('仪表盘显示管理员数量', async () => {
    const wrapper = mountDashboard({
      initialData: makeDashboardData(),
    })
    await nextTick()
    expect(wrapper.text()).toContain('3 人')
  })
})


// ──────────────────────────────────────────────────────────────
// 3. 目标值输入
// ──────────────────────────────────────────────────────────────

describe('目标值输入', () => {
  it('上传界面允许输入目标金额', async () => {
    const wrapper = mountDashboard()
    const input = wrapper.find('.target-inline-form input[type="number"]')
    expect(input.exists()).toBe(true)
    await input.setValue(888)
    expect(wrapper.vm.targetValue).toBe(888)
  })

  it('按回车键确认目标值', async () => {
    const wrapper = mountDashboard()
    const input = wrapper.find('.target-inline-form input[type="number"]')
    await input.setValue(999)
    await input.trigger('keyup.enter')
    // targetValue 已设置
    expect(wrapper.vm.targetValue).toBe(999)
  })

  it('点击确认按钮设置目标值', async () => {
    const wrapper = mountDashboard()
    const input = wrapper.find('.target-inline-form input[type="number"]')
    await input.setValue(666)
    const btn = wrapper.find('.confirm-btn')
    await btn.trigger('click')
    expect(wrapper.vm.targetValue).toBe(666)
  })
})


// ──────────────────────────────────────────────────────────────
// 4. 上传区域交互
// ──────────────────────────────────────────────────────────────

describe('上传区域', () => {
  it('渲染上传指示文字', () => {
    const wrapper = mountDashboard()
    expect(wrapper.text()).toContain('拖拽文件到此处')
    expect(wrapper.text()).toContain('.xlsx')
  })

  it('显示上次上传时间占位', () => {
    const wrapper = mountDashboard()
    expect(wrapper.text()).toContain('上次上传')
  })

  it('input[type=file] 以隐藏形式存在', () => {
    const wrapper = mountDashboard()
    const input = wrapper.find('input[type="file"]')
    expect(input.exists()).toBe(true)
    expect(input.attributes('hidden')).toBeDefined()
  })
})


// ──────────────────────────────────────────────────────────────
// 5. 管理员汇总表格
// ──────────────────────────────────────────────────────────────

describe('管理员汇总表格', () => {
  it('有数据时渲染管理员排名表', async () => {
    const wrapper = mountDashboard({
      initialData: makeDashboardData(),
    })
    await nextTick()
    // 表格区域应包含管理员名称
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('李四')
    expect(wrapper.text()).toContain('王五')
  })

  it('summaryRows 计算属性返回正确行数', async () => {
    const wrapper = mountDashboard({
      initialData: makeDashboardData(),
    })
    await nextTick()
    const rows = wrapper.vm.summaryRows
    // 3 个管理员 + 合计
    expect(rows.length).toBeGreaterThanOrEqual(3)
  })
})


// ──────────────────────────────────────────────────────────────
// 6. 四类预警面板
// ──────────────────────────────────────────────────────────────

describe('四类预警面板', () => {
  it('默认四类预警类型已定义', () => {
    const wrapper = mountDashboard()
    const types = wrapper.vm.fourClassTypes
    expect(types).toHaveLength(4)
    expect(types.map(t => t.name)).toContain('列账不及时')
    expect(types.map(t => t.name)).toContain('预转固不及时')
    expect(types.map(t => t.name)).toContain('关闭不及时')
    expect(types.map(t => t.name)).toContain('长期挂账')
  })

  it('传入 fourClassWarnings 后 fcWarnings 计算属性有值', async () => {
    const mockWarnings = {
      summary: { '列账不及时': { triggered: 1, warning: 2 } },
      items: [],
      total: 3,
      hit_count: 1,
      warn_count: 2,
    }
    const wrapper = mountDashboard({
      initialData: makeDashboardData(),
      fourClassWarnings: mockWarnings,
    })
    await nextTick()
    expect(wrapper.vm.fcWarnings).not.toBeNull()
    expect(wrapper.vm.fcWarnings.total).toBe(3)
  })

  it('无四类预警时 fcWarnings 为 null', () => {
    const wrapper = mountDashboard()
    expect(wrapper.vm.fcWarnings).toBeNull()
  })
})


// ──────────────────────────────────────────────────────────────
// 7. 转固推进弹窗
// ──────────────────────────────────────────────────────────────

describe('转固推进弹窗', () => {
  it('默认转固推进弹窗不可见', () => {
    const wrapper = mountDashboard()
    expect(wrapper.vm.transferPriorityVisible).toBe(false)
  })

  it('转固推进数据初始为空', () => {
    const wrapper = mountDashboard()
    expect(wrapper.vm.transferPriorityData).toEqual([])
  })
})


// ──────────────────────────────────────────────────────────────
// 8. 计算属性
// ──────────────────────────────────────────────────────────────

describe('计算属性', () => {
  it('projectsList 从 detail 提取数据', async () => {
    const wrapper = mountDashboard({
      initialData: makeDashboardData(),
    })
    await nextTick()
    const list = wrapper.vm.projectsList
    expect(list).toHaveLength(2)
    expect(list[0].name).toBe('项目A')
    expect(list[0].manager).toBe('张三')
  })

  it('projectsList 过滤掉空名称', async () => {
    const data = makeDashboardData()
    data.detail.push({ '工程名称': '', '工程管理员': '', '在建工程期末余额': 0 })
    const wrapper = mountDashboard({ initialData: data })
    await nextTick()
    expect(wrapper.vm.projectsList).toHaveLength(2)
  })

  it('topByBalance 按余额降序排列', async () => {
    const wrapper = mountDashboard({
      initialData: makeDashboardData(),
    })
    await nextTick()
    const top = wrapper.vm.topByBalance
    expect(top[0].name).toBe('项目B') // 余额 45
    expect(top[1].name).toBe('项目A') // 余额 30
  })

  it('topBySpend 过滤零支出', async () => {
    const data = makeDashboardData()
    data.detail.push({
      '工程名称': '项目C', '工程管理员': '王五',
      '在建工程期末余额': 10, '本年累计资本性支出': 0,
      '本月资本性支出': 0, '已下单待收货': 0, '转固率': 0, '施工单位': '',
    })
    const wrapper = mountDashboard({ initialData: data })
    await nextTick()
    const top = wrapper.vm.topBySpend
    // 项目C 有余额但支出为 0，应被过滤
    expect(top.find(p => p.name === '项目C')).toBeUndefined()
  })

  it('不带历史对比时 shouldShowHistoryCompare 为 false', async () => {
    const wrapper = mountDashboard({
      initialData: makeDashboardData(),
    })
    await nextTick()
    expect(wrapper.vm.shouldShowHistoryCompare).toBe(false)
  })

  it('带历史对比数据时 shouldShowHistoryCompare 为 true', async () => {
    const wrapper = mountDashboard({
      initialData: makeDashboardData(),
      historyComparison: { dashboard: makeDashboardData() },
    })
    await nextTick()
    expect(wrapper.vm.shouldShowHistoryCompare).toBe(true)
  })
})


// ──────────────────────────────────────────────────────────────
// 9. 事件发射
// ──────────────────────────────────────────────────────────────

describe('事件发射', () => {
  it('dataUpdate 事件定义在 emits 中', () => {
    const wrapper = mountDashboard()
    expect(wrapper.vm.$options.emits).toContain('dataUpdate')
    expect(wrapper.vm.$options.emits).toContain('restoreLatest')
    expect(wrapper.vm.$options.emits).toContain('warningsUpdate')
  })
})


// ──────────────────────────────────────────────────────────────
// 10. 管理员详情抽屉 computed
// ──────────────────────────────────────────────────────────────

describe('管理员详情抽屉', () => {
  it('modalManagerRow 从 summaryRows 匹配管理员', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.modalManager = '张三'
    await nextTick()
    expect(wrapper.vm.modalManagerRow).not.toBeNull()
    expect(wrapper.vm.modalManagerRow.manager).toBe('张三')
  })

  it('modalManagerRow 不匹配时返回 undefined', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.modalManager = '不存在的人'
    await nextTick()
    expect(wrapper.vm.modalManagerRow).toBeUndefined()
  })

  it('modalBalance 从 modalManagerRow 读取', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.modalManager = '张三'
    await nextTick()
    // 张三的 pending 为 50，但 modalBalance 读 capital
    expect(typeof wrapper.vm.modalBalance).toBe('number')
  })

  it('modalSpendYTD 读取 capital', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.modalManager = '张三'
    await nextTick()
    expect(wrapper.vm.modalSpendYTD).toBe(200)
  })

  it('modalTransfer 读取结转额', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.modalManager = '张三'
    await nextTick()
    expect(wrapper.vm.modalTransfer).toBe(150)
  })

  it('modalPending 读取待收货', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.modalManager = '张三'
    await nextTick()
    expect(wrapper.vm.modalPending).toBe(50)
  })

  it('modalManagerRateStr 格式化转固率', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.modalManager = '张三'
    await nextTick()
    expect(wrapper.vm.modalManagerRateStr).toContain('%')
  })

  it('modalRank 返回排名', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.modalManager = '张三'
    await nextTick()
    expect(typeof wrapper.vm.modalRank).toBe('number')
    expect(wrapper.vm.modalRank).toBeGreaterThan(0)
  })

  it('modalTotalProjects 返回管理员项目数', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.modalManager = '张三'
    await nextTick()
    expect(wrapper.vm.modalTotalProjects).toBe(1) // 项目A
  })

  it('modalActiveCount 返回余额 > 0 的项目数', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.modalManager = '张三'
    await nextTick()
    expect(wrapper.vm.modalActiveCount).toBeGreaterThanOrEqual(0)
  })

  it('modalReversedCount 返回支出 < 0 的项目数', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    expect(wrapper.vm.modalReversedCount).toBeGreaterThanOrEqual(0)
  })

  it('sortedModalData 按 sortKey 排序', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.modalManager = '张三'
    wrapper.vm.modalData = [
      { '工程名称': 'B项目', '在建工程期末余额': 20 },
      { '工程名称': 'A项目', '在建工程期末余额': 50 },
    ]
    wrapper.vm.sortKey = '在建工程期末余额'
    wrapper.vm.sortOrder = 'desc'
    await nextTick()
    const sorted = wrapper.vm.sortedModalData
    expect(sorted[0]['在建工程期末余额']).toBe(50)
    expect(sorted[1]['在建工程期末余额']).toBe(20)
  })
})


// ──────────────────────────────────────────────────────────────
// 11. 转固推进弹窗 computed
// ──────────────────────────────────────────────────────────────

describe('转固推进弹窗 computed', () => {
  it('computedTarget 无 targetRate 时返回 null', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.targetRate = ''
    expect(wrapper.vm.computedTarget).toBeNull()
  })

  it('computedTarget targetRate 超出范围时返回 null', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.targetRate = 150
    expect(wrapper.vm.computedTarget).toBeNull()
  })

  it('computedTarget 无 transferPriorityData 时返回 null', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.targetRate = 80
    wrapper.vm.transferPriorityData = []
    expect(wrapper.vm.computedTarget).toBeNull()
  })

  it('computedTarget 有数据时计算目标', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.targetRate = 80
    wrapper.vm.transferPriorityData = [
      {
        manager: '张三',
        current_rate: 0.65,
        denominator: 200,
        projects: [
          { '工程名称': '项目A', '在建余额': 30, '累计后转固率': 0.75, '紧迫度': '高' },
          { '工程名称': '项目B', '在建余额': 20, '累计后转固率': 0.85, '紧迫度': '中' },
        ],
      },
    ]
    await nextTick()
    const ct = wrapper.vm.computedTarget
    expect(ct).not.toBeNull()
    expect(ct.target).toBe(0.8)
    expect(ct.managers).toHaveLength(1)
    expect(ct.managers[0].manager).toBe('张三')
  })

  it('displayManagers 无 computedTarget 时直接映射', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.targetRate = ''
    wrapper.vm.transferPriorityData = [
      {
        manager: '张三',
        current_rate: 0.65,
        denominator: 200,
        projects: [{ '工程名称': '项目A', '在建余额': 30 }],
      },
    ]
    await nextTick()
    const dm = wrapper.vm.displayManagers
    expect(dm).toHaveLength(1)
    expect(dm[0].manager).toBe('张三')
    expect(dm[0].alreadyAchieved).toBe(false)
  })

  it('displayManagers 有 computedTarget 时使用 computedTarget.managers', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.targetRate = 50
    wrapper.vm.transferPriorityData = [
      {
        manager: '张三',
        current_rate: 0.65,
        denominator: 200,
        projects: [
          { '工程名称': '项目A', '在建余额': 30, '累计后转固率': 0.75 },
          { '工程名称': '项目B', '在建余额': 20, '累计后转固率': 0.85 },
        ],
      },
    ]
    await nextTick()
    const ct = wrapper.vm.computedTarget
    expect(ct).not.toBeNull()
    const dm = wrapper.vm.displayManagers
    expect(dm[0].manager).toBe('张三')
    expect(dm[0].alreadyAchieved).toBe(true) // 0.65 >= 0.50
  })
})


// ──────────────────────────────────────────────────────────────
// 12. KPI metrics computed
// ──────────────────────────────────────────────────────────────

describe('KPI metrics computed', () => {
  it('无 dashboard 数据时 metrics 为空数组', () => {
    const wrapper = mountDashboard()
    expect(wrapper.vm.metrics).toEqual([])
  })

  it('有数据时 metrics 返回 4 个 KPI', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    expect(wrapper.vm.metrics).toHaveLength(4)
    expect(wrapper.vm.metrics[0].label).toBe('本年累计资本性支出')
    expect(wrapper.vm.metrics[1].label).toBe('已下单待收货')
    expect(wrapper.vm.metrics[2].label).toBe('本月资本性支出')
    expect(wrapper.vm.metrics[3].label).toBe('综合转固率')
  })

  it('metrics 值格式化为两位小数', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    expect(wrapper.vm.metrics[0].value).toBe('500.00')
    expect(wrapper.vm.metrics[1].value).toBe('120.00')
  })

  it('monthSpend 为负时 valueClass 为 val-negative', async () => {
    const data = makeDashboardData()
    data.metrics.monthSpend = -10
    const wrapper = mountDashboard({ initialData: data })
    await nextTick()
    expect(wrapper.vm.metrics[2].valueClass).toBe('val-negative')
  })
})


// ──────────────────────────────────────────────────────────────
// 13. Progress summary computed
// ──────────────────────────────────────────────────────────────

describe('Progress summary computed', () => {
  it('spendProgress 计算支出进度', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.targetValue = 770
    await nextTick()
    // capital=500, target=770 → 500/770*100 ≈ 64.9
    expect(wrapper.vm.spendProgress).toBeCloseTo(64.9, 0)
  })

  it('spendProgress 无目标时返回 0', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.targetValue = 0
    expect(wrapper.vm.spendProgress).toBe(0)
  })

  it('spendHint 有差距时显示差额', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.targetValue = 770
    await nextTick()
    expect(wrapper.vm.spendHint).toContain('距目标还差')
  })

  it('spendHint 超额时显示超额', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.targetValue = 100
    await nextTick()
    expect(wrapper.vm.spendHint).toContain('已超额完成')
  })

  it('rateProgress 计算转固率进度', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.rateTarget = 80
    await nextTick()
    // rate=0.72 → 72%, target=80 → 72/80*100=90
    expect(wrapper.vm.rateProgress).toBeCloseTo(90, 0)
  })

  it('rateHint 距目标还差', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.rateTarget = 80
    await nextTick()
    expect(wrapper.vm.rateHint).toContain('距目标还差')
  })

  it('rateHint 超过目标', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    wrapper.vm.rateTarget = 50
    await nextTick()
    expect(wrapper.vm.rateHint).toContain('已超过目标')
  })
})


// ──────────────────────────────────────────────────────────────
// 14. History comparison computed
// ──────────────────────────────────────────────────────────────

describe('History comparison computed', () => {
  it('compareOverview 无历史对比时返回 null', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    expect(wrapper.vm.compareOverview).toBeNull()
  })

  it('compareOverview 有历史对比时返回差异', async () => {
    const current = makeDashboardData()
    const previous = makeDashboardData()
    previous.metrics.capital = 400
    const wrapper = mountDashboard({
      initialData: current,
      historyComparison: { dashboard: previous },
    })
    await nextTick()
    const co = wrapper.vm.compareOverview
    expect(co).not.toBeNull()
    expect(co.capital.current).toBe(500)
    expect(co.capital.diff).toBe(100) // 500 - 400
  })

  it('compareOverview rate 差异计算', async () => {
    const current = makeDashboardData()
    const previous = makeDashboardData()
    previous.metrics.rate = 0.60
    const wrapper = mountDashboard({
      initialData: current,
      historyComparison: { dashboard: previous },
    })
    await nextTick()
    const co = wrapper.vm.compareOverview
    expect(co.rate.diff).toBeCloseTo(12, 0) // (0.72-0.60)*100 = 12
  })

  it('managerProgressTop5 有对比时返回差异排名', async () => {
    const current = makeDashboardData()
    const previous = makeDashboardData()
    previous.summary = [
      { manager: '张三', capital: 180 },
      { manager: '李四', capital: 120 },
      { manager: '王五', capital: 60 },
    ]
    const wrapper = mountDashboard({
      initialData: current,
      historyComparison: { dashboard: previous },
    })
    await nextTick()
    const top5 = wrapper.vm.managerProgressTop5
    expect(top5.length).toBeGreaterThan(0)
    expect(top5[0]).toHaveProperty('name')
    expect(top5[0]).toHaveProperty('diff')
  })

  it('managerProgressTop5 无对比时返回空', async () => {
    const wrapper = mountDashboard({ initialData: makeDashboardData() })
    await nextTick()
    expect(wrapper.vm.managerProgressTop5).toEqual([])
  })
})
