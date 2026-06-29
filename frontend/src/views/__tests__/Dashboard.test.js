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
