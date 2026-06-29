/**
 * 全局数据状态 composable
 *
 * 集中管理在建工程 / 预算立项的核心数据，供 App.vue 和所有路由组件共享。
 */
import { ref, computed } from 'vue'
import { getHistory, getHistorySnapshot, getBudgetHistory, getBudgetHistorySnapshot, uploadExcel, uploadBudget, refreshBudgetSpend } from '../api'

// ── 全局单例（模块级 ref，所有组件共享同一份） ──

const zaigongLatestData = ref(null)
const budgetLatestData = ref(null)
const zaigongData = ref(null)
const budgetData = ref(null)
const zaigongLatestRecordId = ref(null)
const budgetLatestRecordId = ref(null)
const zaigongLatestDate = ref(null)
const budgetLatestDate = ref(null)
const zaigongDate = ref(null)
const budgetDate = ref(null)
const zaigongSnapshotLabel = ref('')
const budgetSnapshotLabel = ref('')
const zaigongFourClassWarnings = ref(null)
const zaigongLatestFourClassWarnings = ref(null)

// ── 工具函数 ──

function formatUploadDate(dateLike = new Date()) {
  return new Date(dateLike).toLocaleDateString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit'
  })
}

function formatHistoryTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  })
}

function formatFileDate(value) {
  if (!value) return '-'
  const raw = String(value)
  if (/^\d{8}$/.test(raw)) return `${raw.slice(0, 4)}-${raw.slice(4, 6)}-${raw.slice(6, 8)}`
  if (/^\d{4}$/.test(raw)) return `${raw.slice(0, 2)}-${raw.slice(2, 4)}`
  return raw
}

// ── 数据更新 ──

async function onZaigongDataUpdate(data) {
  zaigongData.value = data
  zaigongLatestData.value = data
  zaigongSnapshotLabel.value = ''
  if (data) {
    const date = formatUploadDate()
    zaigongDate.value = date
    zaigongLatestDate.value = date
    try {
      const result = await refreshBudgetSpend()
      if (result.success && result.data) {
        budgetData.value = result.data
        budgetLatestData.value = result.data
      }
    } catch (e) { /* 未上传预算文件时静默忽略 */ }
  } else {
    zaigongDate.value = null
    zaigongLatestDate.value = null
    zaigongFourClassWarnings.value = null
  }
}

function onBudgetDataUpdate(data) {
  budgetData.value = data
  budgetLatestData.value = data
  budgetSnapshotLabel.value = ''
  if (data) {
    const date = formatUploadDate()
    budgetDate.value = date
    budgetLatestDate.value = date
  } else {
    budgetDate.value = null
    budgetLatestDate.value = null
  }
}

function onZaigongRestoreLatest() {
  zaigongSnapshotLabel.value = ''
  if (zaigongLatestData.value) {
    zaigongData.value = zaigongLatestData.value
    zaigongDate.value = zaigongLatestDate.value
    zaigongFourClassWarnings.value = zaigongLatestFourClassWarnings.value
  }
}

function onBudgetRestoreLatest() {
  budgetSnapshotLabel.value = ''
  if (budgetLatestData.value) {
    budgetData.value = budgetLatestData.value
    budgetDate.value = budgetLatestDate.value
  }
}

function onZaigongWarningsUpdate(warnings) {
  zaigongFourClassWarnings.value = warnings
  if (!zaigongSnapshotLabel.value) {
    zaigongLatestFourClassWarnings.value = warnings
  }
}

// ── 快照加载 ──

async function openZaigongSnapshot(recordId) {
  const result = await getHistorySnapshot(recordId)
  if (!result.success || !result.data?.current) return
  const cur = result.data.current
  zaigongData.value = cur.dashboard
  zaigongDate.value = cur.file_date
    ? formatFileDate(cur.file_date)
    : formatHistoryTime(cur.uploaded_at)
  zaigongSnapshotLabel.value = '当前查看：全局历史快照'
  zaigongFourClassWarnings.value = cur.four_class_warnings || null
}

async function openBudgetSnapshot(recordId) {
  const result = await getBudgetHistorySnapshot(recordId)
  if (!result.success || !result.data?.current?.data) return
  const cur = result.data.current
  budgetData.value = cur.data
  budgetDate.value = formatHistoryTime(cur.uploaded_at)
  budgetSnapshotLabel.value = '当前查看：全局历史快照'
}

// ── 启动时加载最新数据 ──

async function loadLatestDataOnMount() {
  try {
    const [zaigongResult, budgetResult] = await Promise.all([
      getHistory(1),
      getBudgetHistory(1),
    ])

    if (zaigongResult.success && zaigongResult.data?.length) {
      const latestRecord = zaigongResult.data[0]
      const snapshot = await getHistorySnapshot(latestRecord.id)
      if (snapshot.success && snapshot.data?.current) {
        const cur = snapshot.data.current
        zaigongData.value = cur.dashboard
        zaigongLatestData.value = cur.dashboard
        zaigongLatestRecordId.value = cur.id
        zaigongDate.value = cur.file_date
          ? formatFileDate(cur.file_date)
          : formatHistoryTime(cur.uploaded_at)
        zaigongLatestDate.value = zaigongDate.value
        zaigongFourClassWarnings.value = cur.four_class_warnings || null
        zaigongLatestFourClassWarnings.value = cur.four_class_warnings || null
      }
    }

    if (budgetResult.success && budgetResult.data?.length) {
      const latestBudget = budgetResult.data[0]
      try {
        const refreshed = await refreshBudgetSpend()
        if (refreshed.success && refreshed.data) {
          budgetData.value = refreshed.data
          budgetLatestData.value = refreshed.data
          budgetLatestRecordId.value = latestBudget.id
          budgetDate.value = formatHistoryTime(latestBudget.uploaded_at)
          budgetLatestDate.value = budgetDate.value
        } else {
          throw new Error('refresh failed')
        }
      } catch {
        const snapshot = await getBudgetHistorySnapshot(latestBudget.id)
        if (snapshot.success && snapshot.data?.current) {
          const cur = snapshot.data.current
          budgetData.value = cur.data
          budgetLatestData.value = cur.data
          budgetLatestRecordId.value = cur.id
          budgetDate.value = formatHistoryTime(cur.uploaded_at)
          budgetLatestDate.value = budgetDate.value
        }
      }
    }
  } catch (err) {
    console.error('自动加载最新数据失败:', err)
  }
}

// ── 计算属性（模块级） ──

const canShowKeyIndicators = computed(() => zaigongData.value && budgetData.value)
const readinessText = computed(() => {
  const total = Number(Boolean(zaigongLatestData.value)) + Number(Boolean(budgetLatestData.value))
  return `${total}/2 模块已就绪`
})

// ── Composable 导出 ──

export function useGlobalData() {
  return {
    // 状态
    zaigongLatestData, budgetLatestData,
    zaigongData, budgetData,
    zaigongLatestRecordId, budgetLatestRecordId,
    zaigongLatestDate, budgetLatestDate,
    zaigongDate, budgetDate,
    zaigongSnapshotLabel, budgetSnapshotLabel,
    zaigongFourClassWarnings, zaigongLatestFourClassWarnings,
    // 计算属性
    canShowKeyIndicators, readinessText,
    // 操作
    onZaigongDataUpdate, onBudgetDataUpdate,
    onZaigongRestoreLatest, onBudgetRestoreLatest,
    onZaigongWarningsUpdate,
    openZaigongSnapshot, openBudgetSnapshot,
    loadLatestDataOnMount,
    // 工具
    formatUploadDate, formatHistoryTime, formatFileDate,
  }
}
