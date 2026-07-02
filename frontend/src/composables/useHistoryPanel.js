/**
 * 历史快照抽屉 composable
 *
 * 管理 Dashboard / Budget 视图本地的历史面板状态与操作。
 * 采用工厂模式（per-instance）：每次调用创建独立状态，避免两视图共享串数据。
 * 与 useHistoryCenter（全局对比中心）互补，作用域不同，不可合并。
 *
 * @param {object} opts
 * @param {'zaigong'|'budget'} opts.type - 数据类型，决定调用哪组 API
 */
import { ref, computed } from 'vue'
import {
  getHistory, getHistorySnapshot,
  getBudgetHistory, getBudgetHistorySnapshot,
} from '../api'

export function useHistoryPanel({ type }) {
  // ── 状态（per-instance，定义在函数体内） ──
  const historyVisible = ref(false)
  const historyLoading = ref(false)
  const historyRecords = ref([])
  const currentRecordId = ref(null)
  const isViewingHistory = ref(false)
  const snapshotDisplayDate = ref(null)

  // ── 计算属性 ──
  const recentHistoryCards = computed(() => historyRecords.value.slice(0, 4))

  // ── 按 type 分流 API ──
  const fetchList = type === 'budget' ? getBudgetHistory : getHistory
  const fetchSnapshot = type === 'budget' ? getBudgetHistorySnapshot : getHistorySnapshot

  // ── 操作 ──

  async function loadHistoryList() {
    historyLoading.value = true
    try {
      const result = await fetchList(30)
      if (result.success) {
        const records = result.data || []
        const enriched = await Promise.all(records.map(async (record, index) => {
          if (index > 3) return record
          try {
            const snapshotResult = await fetchSnapshot(record.id)
            if (snapshotResult.success && snapshotResult.data?.current) {
              // zaigong 富化字段为 dashboard_snapshot，budget 为 snapshot_data
              const snapshotPayload = type === 'budget'
                ? snapshotResult.data.current.data
                : snapshotResult.data.current.dashboard
              const field = type === 'budget' ? 'snapshot_data' : 'dashboard_snapshot'
              return { ...record, [field]: snapshotPayload }
            }
          } catch (error) {
            console.error('获取历史快照摘要失败:', error)
          }
          return record
        }))
        historyRecords.value = enriched
      }
    } catch (error) {
      console.error('获取历史列表失败:', error)
      historyRecords.value = []
    } finally {
      historyLoading.value = false
    }
  }

  async function openHistoryPanel() {
    historyVisible.value = true
    if (!historyRecords.value.length) await loadHistoryList()
  }

  function closeHistoryPanel() {
    historyVisible.value = false
  }

  /**
   * 拉取历史快照。
   * composable 只负责 historyLoading + closeHistoryPanel + 返回 { current, previous }。
   * currentRecordId / isViewingHistory / snapshotDisplayDate / previous 落点由调用方在各自的
   * 快照应用逻辑中设置（applyDashboardData/applyBudgetData + previousData/localComparison），
   * 保持原有页面业务行为不变。
   * @param {number} recordId
   * @returns {Promise<{current: object, previous: object|null}|null>} 快照数据，失败返回 null
   */
  async function viewHistorySnapshot(recordId) {
    historyLoading.value = true
    try {
      const result = await fetchSnapshot(recordId)
      if (result.success && result.data?.current) {
        closeHistoryPanel()
        return { current: result.data.current, previous: result.data.previous }
      }
      return null
    } catch (error) {
      console.error('获取历史快照失败:', error)
      alert('读取历史快照失败，请稍后重试')
      return null
    } finally {
      historyLoading.value = false
    }
  }

  return {
    // 状态
    historyVisible,
    historyLoading,
    historyRecords,
    currentRecordId,
    isViewingHistory,
    snapshotDisplayDate,
    // 计算属性
    recentHistoryCards,
    // 操作
    loadHistoryList,
    openHistoryPanel,
    closeHistoryPanel,
    viewHistorySnapshot,
  }
}
