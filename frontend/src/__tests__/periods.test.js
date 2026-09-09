import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../api', () => ({
  getHistory: vi.fn(), getHistorySnapshot: vi.fn(),
  getBudgetHistory: vi.fn(), getBudgetHistorySnapshot: vi.fn(),
  refreshBudgetSpend: vi.fn(), uploadExcel: vi.fn(), uploadBudget: vi.fn(),
}))

let api, state
beforeEach(async () => {
  vi.resetModules()
  api = await import('../api')
  vi.resetAllMocks()
  state = (await import('../composables/useGlobalData')).useGlobalData()
  api.getHistory.mockResolvedValue({ success: true, data: [{ id: 10 }] })
  api.getHistorySnapshot.mockResolvedValue({ success: true, data: { current: {
    id: 10, period: { business_date: '2026-09-01' },
    dashboard: { record_id: 10, metrics: { capital: 200 }, period: { business_date: '2026-09-01' } },
    four_class_warnings: { summary: { analysis_date: '2026-09-01' } },
  } } })
  api.getBudgetHistory.mockResolvedValue({ success: true, data: [{
    id: 20, period: { business_date: '2026-09-01' },
  }] })
  api.refreshBudgetSpend.mockResolvedValue({ success: true, data: {
    record_id: 20, period: { business_date: '2026-09-01' }, annual_spend_total: 200,
    source_link: { zaigong_record_id: 10, warnings: [] },
  } })
})

describe('P0 current period and snapshot state', () => {
  it('backfilled engineering upload restores current business period and matching record ID', async () => {
    await state.onZaigongDataUpdate({ record_id: 11, metrics: { capital: 100 }, period: { business_date: '2026-08-01' } })
    expect(state.zaigongData.value.metrics.capital).toBe(200)
    expect(state.zaigongLatestRecordId.value).toBe(10)
    expect(state.zaigongDate.value).toBe('2026-09-01')
    expect(state.budgetData.value.source_link.zaigong_record_id).toBe(10)
  })
  it('backfilled budget upload does not become the current budget', async () => {
    await state.onBudgetDataUpdate({ record_id: 21, period: { business_date: '2026-08-01' } })
    expect(state.budgetLatestRecordId.value).toBe(20)
    expect(state.budgetDate.value).toBe('2026-09-01')
  })
  it('budget history displays the saved snapshot, and restoring current returns the live result', async () => {
    await state.loadLatestDataOnMount()
    api.getBudgetHistorySnapshot.mockResolvedValue({ success: true, data: { current: {
      id: 18, period: { business_date: '2026-08-01' }, data: {
        annual_spend_total: 80, period: { business_date: '2026-08-01' },
        source_link: { zaigong_record_id: 8, warnings: [] },
      },
    } } })
    await state.openBudgetSnapshot(18)
    expect(state.budgetData.value.annual_spend_total).toBe(80)
    expect(state.budgetSnapshotLabel.value).toContain('历史快照')
    expect(state.periodNotice.value).toContain('日期不一致')
    expect(state.periodNotice.value).toContain('版本 #8')
    state.onBudgetRestoreLatest()
    expect(state.budgetData.value.annual_spend_total).toBe(200)
    expect(state.periodNotice.value).toBe('')
  })
  it('unknown dates and unavailable sources remain visible', () => {
    state.zaigongData.value = { period: { business_date: null } }
    state.budgetData.value = { period: { business_date: '2027-01-01' }, source_link: {
      warnings: ['无同年度工程数据'], spend_available: false,
    } }
    expect(state.periodNotice.value).toContain('工程数据日期未确认')
    expect(state.periodNotice.value).toContain('无同年度工程数据')
  })
})
