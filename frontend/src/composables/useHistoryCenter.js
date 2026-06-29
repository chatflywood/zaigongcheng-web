/**
 * 历史记录中心 composable
 *
 * 管理历史记录面板、趋势图、双版本对比的全局状态。
 */
import { ref, computed } from 'vue'
import { getHistory, getBudgetHistory, getHistorySnapshot, getBudgetHistorySnapshot } from '../api'
import { useGlobalData } from './useGlobalData'

const historyCenterVisible = ref(false)
const historyCenterLoading = ref(false)
const historyTab = ref('all')
const zaigongHistory = ref([])
const budgetHistory = ref([])
const zaigongCompareSelection = ref({ left: null, right: null })
const budgetCompareSelection = ref({ left: null, right: null })
const zaigongCompareResult = ref(null)
const budgetCompareResult = ref(null)

export function useHistoryCenter() {
  const { formatHistoryTime, formatFileDate } = useGlobalData()

  const historySections = computed(() => {
    const sections = []
    if (historyTab.value === 'all' || historyTab.value === 'zaigong') {
      sections.push({ key: 'zaigong', title: '在建工程', records: zaigongHistory.value })
    }
    if (historyTab.value === 'all' || historyTab.value === 'budget') {
      sections.push({ key: 'budget', title: '预算立项', records: budgetHistory.value })
    }
    return sections
  })

  // ── 趋势图数据 ──
  const trendPoints = computed(() => {
    const records = [...zaigongHistory.value]
      .filter(r => r.metrics && (r.target_value > 0 || r.metrics.year_target > 0))
      .reverse()

    if (records.length < 2) return null

    const L = 48, T = 15, W = 497, H = 200, YMAX = 130
    const n = records.length
    const xStep = W / (n - 1)
    const px = i => L + i * xStep
    const py = v => T + H - Math.min(Math.max(v, 0), YMAX) / YMAX * H

    const fmtLabel = r => {
      if (r.file_date) {
        const fd = String(r.file_date)
        if (fd.length === 4) return `${fd.slice(0, 2)}-${fd.slice(2)}`
        if (fd.length === 8) return `${fd.slice(4, 6)}-${fd.slice(6)}`
      }
      const d = new Date(r.uploaded_at)
      return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    }

    const progressPoints = records.map((r, i) => {
      const capital = r.metrics.total_current ?? r.metrics.capital ?? 0
      const target = r.target_value || r.metrics.year_target || 1
      const v = (capital / target) * 100
      return { x: px(i), y: py(v), v: v.toFixed(1) }
    })

    const ratePoints = records.map((r, i) => {
      const v = (r.metrics.total_rate ?? r.metrics.rate ?? 0) * 100
      return { x: px(i), y: py(v), v: v.toFixed(1) }
    })

    const labels = records.map((r, i) => ({ x: px(i), text: fmtLabel(r) }))
    const yTicks = [0, 30, 60, 90, 120].map(v => ({ y: py(v), label: `${v}%` }))

    return {
      progressPolyline: progressPoints.map(p => `${p.x},${p.y}`).join(' '),
      ratePolyline: ratePoints.map(p => `${p.x},${p.y}`).join(' '),
      progressPoints, ratePoints, labels, yTicks,
      refY60: py(60),
      showLabels: n <= 8,
    }
  })

  function getRecordDateLabel(sectionKey, record) {
    if (!record) return '未选择'
    if (sectionKey === 'zaigong' && record.file_date) return formatFileDate(record.file_date)
    return formatHistoryTime(record.uploaded_at)
  }

  async function openHistoryCenter() {
    historyCenterVisible.value = true
    historyCenterLoading.value = true
    try {
      const [zaigongResult, budgetResult] = await Promise.all([
        getHistory(20), getBudgetHistory(20)
      ])
      zaigongHistory.value = zaigongResult.success ? (zaigongResult.data || []) : []
      budgetHistory.value = budgetResult.success ? (budgetResult.data || []) : []
    } catch (error) {
      console.error('获取全局历史失败:', error)
      zaigongHistory.value = []
      budgetHistory.value = []
    } finally {
      historyCenterLoading.value = false
    }
  }

  function closeHistoryCenter() {
    historyCenterVisible.value = false
  }

  function isSelectedForCompare(sectionKey, slot, recordId) {
    const selection = sectionKey === 'zaigong' ? zaigongCompareSelection.value : budgetCompareSelection.value
    return selection[slot]?.id === recordId
  }

  async function selectCompareRecord(sectionKey, slot, record) {
    const targetSelection = sectionKey === 'zaigong' ? zaigongCompareSelection : budgetCompareSelection
    targetSelection.value = { ...targetSelection.value, [slot]: record }
    await buildComparison(sectionKey)
  }

  async function buildComparison(sectionKey) {
    const selection = sectionKey === 'zaigong' ? zaigongCompareSelection.value : budgetCompareSelection.value
    if (!selection.left || !selection.right || selection.left.id === selection.right.id) {
      if (sectionKey === 'zaigong') zaigongCompareResult.value = null
      if (sectionKey === 'budget') budgetCompareResult.value = null
      return
    }

    if (sectionKey === 'zaigong') {
      const [leftResult, rightResult] = await Promise.all([
        getHistorySnapshot(selection.left.id),
        getHistorySnapshot(selection.right.id),
      ])
      if (!leftResult.success || !rightResult.success) return
      const left = leftResult.data.current
      const right = rightResult.data.current
      const leftMap = new Map(
        (left.dashboard?.summary || []).map(item => [item.manager || item['工程管理员'], Number(item.capital || item['本年累计资本性支出'] || 0)])
      )
      zaigongCompareResult.value = {
        leftLabel: getRecordDateLabel('zaigong', selection.left),
        rightLabel: getRecordDateLabel('zaigong', selection.right),
        capitalCurrent: Number(right.dashboard?.metrics?.capital || 0),
        capitalDiff: Number(right.dashboard?.metrics?.capital || 0) - Number(left.dashboard?.metrics?.capital || 0),
        progressDiff: (Number(right.dashboard?.metrics?.progress || 0) - Number(left.dashboard?.metrics?.progress || 0)) * 100,
        rateCurrent: Number(right.dashboard?.metrics?.rate || 0),
        rateDiff: (Number(right.dashboard?.metrics?.rate || 0) - Number(left.dashboard?.metrics?.rate || 0)) * 100,
        top5: (right.dashboard?.summary || [])
          .map(item => {
            const name = item.manager || item['工程管理员']
            const current = Number(item.capital || item['本年累计资本性支出'] || 0)
            return { name, current, diff: current - (leftMap.get(name) || 0) }
          })
          .filter(item => item.diff !== 0)
          .sort((a, b) => b.diff - a.diff)
          .slice(0, 5),
      }
    }

    if (sectionKey === 'budget') {
      const [leftResult, rightResult] = await Promise.all([
        getBudgetHistorySnapshot(selection.left.id),
        getBudgetHistorySnapshot(selection.right.id),
      ])
      if (!leftResult.success || !rightResult.success) return
      const left = leftResult.data.current.data
      const right = rightResult.data.current.data
      const leftMap = new Map((left.categories || []).map(item => [item.name, Number(item.progress || 0)]))
      budgetCompareResult.value = {
        leftLabel: getRecordDateLabel('budget', selection.left),
        rightLabel: getRecordDateLabel('budget', selection.right),
        budgetCurrent: Number(right.budget_total || 0),
        budgetDiff: Number(right.budget_total || 0) - Number(left.budget_total || 0),
        progressCurrent: Number(right.approval_progress || 0),
        progressDiff: (Number(right.approval_progress || 0) - Number(left.approval_progress || 0)) * 100,
        top5: (right.categories || [])
          .map(item => ({
            name: item.name,
            currentProgress: Number(item.progress || 0),
            diff: (Number(item.progress || 0) - (leftMap.get(item.name) || 0)) * 100,
          }))
          .filter(item => item.diff !== 0)
          .sort((a, b) => b.diff - a.diff)
          .slice(0, 5),
      }
    }
  }

  return {
    historyCenterVisible, historyCenterLoading, historyTab,
    zaigongHistory, budgetHistory,
    zaigongCompareSelection, budgetCompareSelection,
    zaigongCompareResult, budgetCompareResult,
    historySections, trendPoints,
    openHistoryCenter, closeHistoryCenter,
    isSelectedForCompare, selectCompareRecord,
    getRecordDateLabel,
  }
}
