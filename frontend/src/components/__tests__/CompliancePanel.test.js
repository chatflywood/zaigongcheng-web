import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import CompliancePanel from '../CompliancePanel.vue'
import { getCompliance, saveComplianceReview, exportCompliance } from '../../api'

vi.mock('../../api', () => ({ getCompliance: vi.fn(), saveComplianceReview: vi.fn(), exportCompliance: vi.fn() }))
const fixtures = () => ({ start_date: '2026-09-02', end_date: '2026-11-02', source_filename: '在建工程20261102.xlsx',
  checks: Object.fromEntries(['safety', 'quality'].map(kind => [kind, {
    total: 2, pending: 2, normal: 0, issues: 0, missing_dates: 0, invalid_dates: 0, excluded: kind === 'safety' ? 20 : 0,
    items: [1, 2].map(index => ({ code: `GC${index}`, name: `核查项目${index}`, manager: '伍建勋', project_type: '常规项目',
      project_status: '工程已开工', construction_unit: '施工单位A', key_date: '2026-09-28',
      current_safety_fee: 1901.79, total_safety_fee: 1901.79, status: '待核实', reviewed_on: '', note: '' })),
  }])) })
let wrappers = []
function create(recordId = 167) {
  const wrapper = mount(CompliancePanel, { props: { recordId }, global: { stubs: { teleport: true } } })
  wrappers.push(wrapper)
  return wrapper
}
beforeEach(() => {
  vi.clearAllMocks()
  getCompliance.mockResolvedValue({ success: true, data: fixtures() })
})
afterEach(() => { for (const wrapper of wrappers) wrapper.unmount(); wrappers = []; document.body.style.overflow = '' })

describe('工程合规核查', () => {
  it('主数字只计待处理，默认隐藏正常项，已核实与全部入口可回查', async () => {
    const data = fixtures()
    const third = { ...data.checks.safety.items[0], code: 'GC3', name: '问题项目', status: '发现问题' }
    for (const item of data.checks.safety.items) Object.assign(item, { status: '已核实正常', reviewed_on: '2026-11-02' })
    data.checks.safety.items.push(third)
    Object.assign(data.checks.safety, { total: 3, actionable: 1, pending: 0, normal: 2, issues: 1 })
    getCompliance.mockResolvedValue({ success: true, data })
    const wrapper = create()
    await flushPromises()
    expect(wrapper.find('.compliance-tile-count').text()).toBe('1项待处理')
    expect(wrapper.find('.compliance-card-links').text()).toContain('已核实正常 2')
    await wrapper.find('.compliance-tile').trigger('click')
    expect(wrapper.findAll('.compliance-table tbody tr')).toHaveLength(1)
    expect(wrapper.find('.compliance-table').text()).toContain('问题项目')
    expect(wrapper.find('.compliance-table').text()).not.toContain('核查项目1')
    await wrapper.findAll('.compliance-filters select')[1].setValue('发现问题')
    await wrapper.findAll('.compliance-views button')[1].trigger('click')
    expect(wrapper.findAll('.compliance-filters select')[1].element.value).toBe('')
    expect(wrapper.findAll('.compliance-table tbody tr')).toHaveLength(2)
    await wrapper.findAll('.compliance-views button')[2].trigger('click')
    expect(wrapper.findAll('.compliance-table tbody tr')).toHaveLength(3)
    await wrapper.find('.compliance-close').trigger('click')
    await wrapper.find('.compliance-card-links button').trigger('click')
    expect(wrapper.findAll('.compliance-views button')[1].attributes('aria-pressed')).toBe('true')
    expect(wrapper.findAll('.compliance-table tbody tr')).toHaveLength(2)
  })

  it('最后一项核实正常后待处理清零，结果保留在已核实视图', async () => {
    const data = fixtures()
    data.checks.safety.items = [data.checks.safety.items[0]]
    Object.assign(data.checks.safety, { total: 1, actionable: 1, pending: 1 })
    getCompliance.mockResolvedValue({ success: true, data })
    const wrapper = create()
    await flushPromises()
    await wrapper.find('.compliance-tile').trigger('click')
    await wrapper.find('select[aria-label="GC1 核实状态"]').setValue('已核实正常')
    const updated = structuredClone(data)
    Object.assign(updated.checks.safety, { actionable: 0, pending: 0, normal: 1 })
    Object.assign(updated.checks.safety.items[0], { status: '已核实正常', reviewed_on: '2026-11-06' })
    saveComplianceReview.mockResolvedValue({ success: true, data: updated })
    await wrapper.find('.compliance-save').trigger('click')
    await flushPromises()
    expect(wrapper.find('.compliance-tile-count').text()).toBe('0项待处理')
    expect(wrapper.text()).toContain('暂无待处理事项')
    await wrapper.findAll('.compliance-views button')[1].trigger('click')
    expect(wrapper.find('.compliance-table').text()).toContain('核查项目1')
    expect(wrapper.find('input[aria-label="GC1 核实日期"]').element.value).toBe('2026-11-06')
  })

  it('复核显示具体变化和上次核实信息，持续跟踪标记与数据保留', async () => {
    const data = fixtures()
    Object.assign(data.checks.safety.items[0], { needs_recheck: true, carried_forward: true,
      previous_status: '已核实正常', previous_reviewed_on: '2026-11-02',
      tracking_note: '累计安全生产费（元）：1901.79 → 2000.00；持续跟踪，处理完成后移出待处理清单',
      key_date: '' })
    getCompliance.mockResolvedValue({ success: true, data })
    const wrapper = create()
    await flushPromises()
    await wrapper.find('.compliance-tile').trigger('click')
    expect(wrapper.text()).toContain('需重新核实')
    expect(wrapper.text()).toContain('1901.79 → 2000.00')
    expect(wrapper.text()).toContain('持续跟踪')
    expect(wrapper.text()).toContain('上次：已核实正常 · 2026-11-02')
    expect(wrapper.find('select[aria-label="GC1 核实状态"]').element.value).toBe('待核实')
    expect(wrapper.find('.compliance-table').text()).toContain('未提供')
  })

  it('重新上传相同核实结果后维持零待处理，正常项仍能查到', async () => {
    const data = fixtures()
    Object.assign(data.checks.safety, { actionable: 0, pending: 0, normal: 2 })
    data.checks.safety.items.forEach(item => { item.status = '已核实正常'; item.reviewed_on = '2026-11-06' })
    getCompliance.mockResolvedValue({ success: true, data })
    const wrapper = create(168)
    await flushPromises()
    await wrapper.setProps({ recordId: 169 })
    await flushPromises()
    expect(wrapper.find('.compliance-tile-count').text()).toBe('0项待处理')
    await wrapper.find('.compliance-tile').trigger('click')
    expect(wrapper.text()).toContain('暂无待处理事项')
    await wrapper.findAll('.compliance-views button')[1].trigger('click')
    expect(wrapper.findAll('.compliance-table tbody tr')).toHaveLength(2)
  })

  it('显示区间和数量，点击卡片打开对应类型，费用有值仍为待核实', async () => {
    const wrapper = create()
    await flushPromises()
    expect(wrapper.text()).toContain('2026-09-02 — 2026-11-02')
    expect(wrapper.findAll('.compliance-tile')).toHaveLength(2)
    await wrapper.findAll('.compliance-tile')[0].trigger('click')
    expect(wrapper.find('[role=dialog]').exists()).toBe(true)
    expect(wrapper.find('.compliance-table').text()).toContain('1,901.79')
    expect(wrapper.find('select[aria-label="GC1 核实状态"]').element.value).toBe('待核实')
    await wrapper.find('#compliance-tab-quality').trigger('click')
    expect(wrapper.find('.compliance-table').text()).toContain('首次设计批复')
    expect(wrapper.find('.compliance-table').text()).not.toContain('本年安全费')
  })

  it('保存结果后更新数量，同时保留其他项目未保存的备注', async () => {
    const wrapper = create()
    await flushPromises()
    await wrapper.findAll('.compliance-tile')[0].trigger('click')
    await wrapper.find('textarea[aria-label="GC2 核实备注"]').setValue('另一项目未保存的备注')
    await wrapper.find('select[aria-label="GC1 核实状态"]').setValue('已核实正常')
    await wrapper.find('input[aria-label="GC1 核实日期"]').setValue('2026-11-02')
    await wrapper.find('textarea[aria-label="GC1 核实备注"]').setValue('已核对支付凭证')
    const updated = fixtures()
    Object.assign(updated.checks.safety.items[0], { status: '已核实正常', reviewed_on: '2026-11-02', note: '已核对支付凭证' })
    Object.assign(updated.checks.safety, { pending: 1, normal: 1 })
    saveComplianceReview.mockResolvedValue({ success: true, data: updated })
    await wrapper.findAll('.compliance-save')[0].trigger('click')
    await flushPromises()
    expect(saveComplianceReview).toHaveBeenCalledWith(167, 'safety', 'GC1', { status: '已核实正常', reviewed_on: '2026-11-02', note: '已核对支付凭证' })
    expect(wrapper.findAll('.compliance-tile')[0].text()).toContain('待核实 1')
    expect(wrapper.find('textarea[aria-label="GC2 核实备注"]').element.value).toBe('另一项目未保存的备注')
    expect(wrapper.text()).toContain('核实结果已保存')
  })

  it('管理员和已保存状态筛选匹配明细，空结果不伪造成功', async () => {
    const data = fixtures()
    data.checks.safety.items[1].manager = '张文'
    getCompliance.mockResolvedValue({ success: true, data })
    const wrapper = create()
    await flushPromises()
    await wrapper.findAll('.compliance-tile')[0].trigger('click')
    await wrapper.find('.compliance-filters select').setValue('张文')
    expect(wrapper.find('.compliance-table').text()).toContain('核查项目2')
    expect(wrapper.find('.compliance-table').text()).not.toContain('核查项目1')
    await wrapper.findAll('.compliance-filters select')[1].setValue('发现问题')
    expect(wrapper.text()).toContain('没有符合筛选条件的项目')
  })

  it('旧版本请求迟到时不覆盖当前版本', async () => {
    let resolveOld
    getCompliance.mockImplementationOnce(() => new Promise(resolve => { resolveOld = resolve }))
    const wrapper = create(1)
    await wrapper.setProps({ recordId: 2 })
    await flushPromises()
    const old = fixtures()
    old.start_date = '2020-01-01'
    resolveOld({ success: true, data: old })
    await flushPromises()
    expect(wrapper.text()).toContain('2026-09-02')
    expect(wrapper.text()).not.toContain('2020-01-01')
  })

  it('加载失败显示重试，不显示零项', async () => {
    getCompliance.mockRejectedValueOnce(new Error('network error'))
    const wrapper = create()
    await flushPromises()
    expect(wrapper.find('[role=alert]').text()).toContain('加载失败')
    expect(wrapper.find('.compliance-tile').exists()).toBe(false)
    await wrapper.find('[role=alert] button').trigger('click')
    await flushPromises()
    expect(wrapper.findAll('.compliance-tile')).toHaveLength(2)
  })

  it('关闭弹窗和卸载恢复页面滚动，导出当前版本清单', async () => {
    URL.createObjectURL = vi.fn(() => 'blob:compliance')
    URL.revokeObjectURL = vi.fn()
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
    exportCompliance.mockResolvedValue(new Blob(['workbook']))
    const wrapper = create()
    await flushPromises()
    await wrapper.findAll('.compliance-tile')[1].trigger('click')
    expect(document.body.style.overflow).toBe('hidden')
    await wrapper.find('.compliance-actions .btn').trigger('click')
    await flushPromises()
    expect(exportCompliance).toHaveBeenCalledWith(167)
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:compliance')
    // A download can leave keyboard focus outside the dialog.
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await flushPromises()
    expect(wrapper.find('.compliance-overlay').exists()).toBe(false)
    expect(document.body.style.overflow).toBe('')
    click.mockRestore()
  })
})
