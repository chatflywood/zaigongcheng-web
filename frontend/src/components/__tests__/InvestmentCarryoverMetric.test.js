import { afterEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import InvestmentCarryoverMetric from '../InvestmentCarryoverMetric.vue'

const wrappers = []
function metric(overrides = {}) {
  const wrapper = mount(InvestmentCarryoverMetric, {
    props: {
      amount: 682.462796,
      budget: 2129.1913,
      engineeringDate: '2026-10-10',
      budgetDate: '2026-09-30',
      ...overrides,
    },
    global: { stubs: { teleport: true } },
  })
  wrappers.push(wrapper)
  return wrapper
}
afterEach(() => wrappers.splice(0).forEach(w => w.unmount()))

describe('投资结转率业务口径', () => {
  it('用未舍入的结转额和正式预算计算样例，并展示压降金额和数据日期差异', async () => {
    const wrapper = metric()
    expect(wrapper.find('.ic-value').text()).toBe('32.05%')
    expect(wrapper.find('.ic-status').text()).toBe('高于目标 10.05pp')
    await wrapper.find('.ic-foot button').trigger('click')
    const details = wrapper.find('[role="dialog"]').text()
    expect(details).toContain('2,129.19')
    expect(details).toContain('468.42 万')
    expect(details).toContain('214.04 万')
    expect(details).toContain('2026-10-10')
    expect(details).toContain('2026-09-30 · 数据日期不同')
    await wrapper.find('.ic-overlay').trigger('keydown', { key: 'Escape' })
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)
  })

  it.each([null, 0, -1, NaN, Infinity])('预算为 %s 时不伪装为 0%% 或使用替代分母', (budget) => {
    const wrapper = metric({ budget })
    expect(wrapper.find('.ic-value').text()).toBe('—')
    expect(wrapper.find('.ic-status').text()).toBe('本年预算缺失或无效')
  })

  it('缺失结转额时不当作真实零值', () => {
    const wrapper = metric({ amount: null })
    expect(wrapper.find('.ic-value').text()).toBe('—')
    expect(wrapper.find('.ic-status').text()).toBe('结转额缺失')
  })

  it.each(['', '日期未确认', '2026-02-30'])('日期 %s 未确认或无效时不计算', (engineeringDate) => {
    const wrapper = metric({ engineeringDate })
    expect(wrapper.find('.ic-value').text()).toBe('—')
    expect(wrapper.find('.ic-status').text()).toBe('数据日期待确认')
  })

  it('跨年度不混算结转额与预算', () => {
    const wrapper = metric({ engineeringDate: '2027-01-10' })
    expect(wrapper.find('.ic-value').text()).toBe('—')
    expect(wrapper.find('.ic-status').text()).toBe('数据年度不一致')
  })

  it.each([0, 220])('结转额 %s 在 22%% 边界内，含真实零值', async (amount) => {
    const wrapper = metric({ amount, budget: 1000 })
    expect(wrapper.find('.ic-value').text()).toBe(`${(amount / 10).toFixed(2)}%`)
    expect(wrapper.find('.ic-status').text()).toBe('已在目标范围内')
    await wrapper.find('.ic-foot button').trigger('click')
    expect(wrapper.find('[role="dialog"]').text()).toContain('还需压降约 0.00 万')
  })

  it('保留负值并提示核查，不截断为零', () => {
    const wrapper = metric({ amount: -10, budget: 1000 })
    expect(wrapper.find('.ic-value').text()).toBe('-1.00%')
    expect(wrapper.find('.ic-status').text()).toBe('负值待核查')
  })

  it('超过 100% 时保留实际比例', () => {
    expect(metric({ amount: 1500, budget: 1000 }).find('.ic-value').text()).toBe('150.00%')
  })

  it('更新预算后同步重新计算', async () => {
    const wrapper = metric({ amount: 220, budget: 1000 })
    await wrapper.setProps({ budget: 500 })
    expect(wrapper.find('.ic-value').text()).toBe('44.00%')
    expect(wrapper.find('.ic-status').text()).toBe('高于目标 22.00pp')
  })
})
