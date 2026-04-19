<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import Dashboard from './views/Dashboard.vue'
import Budget from './views/Budget.vue'
import KeyIndicators from './views/KeyIndicators.vue'
import { getHistory, getHistorySnapshot, getBudgetHistory, getBudgetHistorySnapshot, getNotifyConfig, saveNotifyConfig, clearNotifyConfig, testNotifyWebhook, pushNotify, generateBriefImage } from './api'

const currentView = ref('zaigong')
const isAnalystMode = computed(() => currentView.value !== 'key-indicators')

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
const zaigongFourClassWarnings = ref(null)  // 四类工程预警数据（当前视图）
const zaigongLatestFourClassWarnings = ref(null)  // 四类工程预警数据（最新）
const historyCenterVisible = ref(false)
const historyCenterLoading = ref(false)
const historyTab = ref('all')
const zaigongHistory = ref([])
const budgetHistory = ref([])
const zaigongCompareSelection = ref({ left: null, right: null })
const budgetCompareSelection = ref({ left: null, right: null })
const zaigongCompareResult = ref(null)
const budgetCompareResult = ref(null)
const presentationMode = ref(false)

const canShowKeyIndicators = computed(() => {
  return zaigongData.value && budgetData.value
})

const readinessText = computed(() => {
  const total = Number(Boolean(zaigongLatestData.value)) + Number(Boolean(budgetLatestData.value))
  return `${total}/2 模块已就绪`
})

const activeViewLabel = computed(() => {
  if (currentView.value === 'overview') return '设计说明'
  if (currentView.value === 'budget') return '预算立项'
  if (currentView.value === 'key-indicators') return '关键指标'
  return '在建工程'
})

const currentMonthLabel = computed(() => {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const q = Math.ceil((now.getMonth() + 1) / 3)
  return `${y}.${m} · 第 ${q} 季度`
})

const overviewPages = [
  { id: 'zaigong', t: '在建工程', d: '资本性支出进度、管理员排名、四类工程预警、转固推进', count: '2026.03 数据' },
  { id: 'budget', t: '预算立项', d: '总预算 vs 已占用/预占用，按专业拆分，新建项目流水', count: '7 个专业' },
  { id: 'key-indicators', t: '关键指标', d: '4 个核心 KPI 仪表盘 + 重点工作清单（替代旧大屏）', count: '可投屏' },
]

function switchView(view) {
  currentView.value = view
  if (view !== 'key-indicators') {
    presentationMode.value = false
  }
}

function onPresentationChange(active) {
  presentationMode.value = Boolean(active)
}

const currentDate = computed(() => {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
})

async function togglePresentationMode() {
  try {
    if (!document.fullscreenElement) {
      await document.documentElement.requestFullscreen()
      presentationMode.value = true
    } else {
      await document.exitFullscreen()
      presentationMode.value = false
    }
  } catch (error) {
    console.error('切换展示模式失败:', error)
  }
}

function handleAppFullscreenChange() {
  presentationMode.value = Boolean(document.fullscreenElement)
}

function formatUploadDate(dateLike = new Date()) {
  return new Date(dateLike).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

function formatHistoryTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatFileDate(value) {
  if (!value) return '-'
  const raw = String(value)
  if (/^\d{8}$/.test(raw)) return `${raw.slice(0, 4)}-${raw.slice(4, 6)}-${raw.slice(6, 8)}`
  if (/^\d{4}$/.test(raw)) return `${raw.slice(0, 2)}-${raw.slice(2, 4)}`
  return raw
}

function getRecordDateLabel(sectionKey, record) {
  if (!record) return '未选择'
  if (sectionKey === 'zaigong' && record.file_date) return formatFileDate(record.file_date)
  return formatHistoryTime(record.uploaded_at)
}

function onZaigongDataUpdate(data) {
  zaigongData.value = data
  zaigongLatestData.value = data
  zaigongSnapshotLabel.value = ''
  if (data) {
    const date = formatUploadDate()
    zaigongDate.value = date
    zaigongLatestDate.value = date
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

// ── 趋势图数据计算 ─────────────────────────────────────────────
const trendPoints = computed(() => {
  const records = [...zaigongHistory.value]
    .filter(r => r.metrics && (r.target_value > 0 || r.metrics.year_target > 0))
    .reverse() // 最旧在左

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
    progressPoints,
    ratePoints,
    labels,
    yTicks,
    refY60: py(60),
    showLabels: n <= 8,
  }
})

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

async function openHistoryCenter() {
  historyCenterVisible.value = true
  historyCenterLoading.value = true
  try {
    const [zaigongResult, budgetResult] = await Promise.all([
      getHistory(20),
      getBudgetHistory(20)
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

async function openZaigongSnapshot(recordId) {
  const result = await getHistorySnapshot(recordId)
  if (!result.success || !result.data?.current) return
  currentView.value = 'zaigong'
  zaigongData.value = result.data.current.dashboard
  zaigongDate.value = result.data.current.file_date
    ? formatFileDate(result.data.current.file_date)
    : formatHistoryTime(result.data.current.uploaded_at)
  zaigongSnapshotLabel.value = '当前查看：全局历史快照'
  // 加载四类工程预警数据
  zaigongFourClassWarnings.value = result.data.current.four_class_warnings || null
  console.log('[DEBUG] openZaigongSnapshot four_class_warnings:', result.data.current.four_class_warnings)
  closeHistoryCenter()
}

async function openBudgetSnapshot(recordId) {
  const result = await getBudgetHistorySnapshot(recordId)
  if (!result.success || !result.data?.current?.data) return
  currentView.value = 'budget'
  budgetData.value = result.data.current.data
  budgetDate.value = formatHistoryTime(result.data.current.uploaded_at)
  budgetSnapshotLabel.value = '当前查看：全局历史快照'
  closeHistoryCenter()
}

function restoreCurrentModuleLatest() {
  if (currentView.value === 'zaigong' && zaigongLatestData.value) {
    zaigongData.value = zaigongLatestData.value
    zaigongDate.value = zaigongLatestDate.value
    zaigongSnapshotLabel.value = ''
  }
  if (currentView.value === 'budget' && budgetLatestData.value) {
    budgetData.value = budgetLatestData.value
    budgetDate.value = budgetLatestDate.value
    budgetSnapshotLabel.value = ''
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

function onZaigongWarningsUpdate(warnings) {
  zaigongFourClassWarnings.value = warnings
  // 如果当前不是查看历史，则同时更新最新的四类预警
  if (!zaigongSnapshotLabel.value) {
    zaigongLatestFourClassWarnings.value = warnings
  }
}

function onBudgetRestoreLatest() {
  budgetSnapshotLabel.value = ''
  if (budgetLatestData.value) {
    budgetData.value = budgetLatestData.value
    budgetDate.value = budgetLatestDate.value
  }
}

function isSelectedForCompare(sectionKey, slot, recordId) {
  const selection = sectionKey === 'zaigong' ? zaigongCompareSelection.value : budgetCompareSelection.value
  return selection[slot]?.id === recordId
}

async function selectCompareRecord(sectionKey, slot, record) {
  const targetSelection = sectionKey === 'zaigong' ? zaigongCompareSelection : budgetCompareSelection
  targetSelection.value = {
    ...targetSelection.value,
    [slot]: record,
  }
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
  } catch (err) {
    console.error('自动加载最新数据失败:', err)
  }
}

function handleDocClick(e) {
  if (!e.target.closest('.more-menu-wrap')) closeMoreMenu()
}

onMounted(() => {
  loadLatestDataOnMount()
  document.addEventListener('fullscreenchange', handleAppFullscreenChange)
  document.addEventListener('click', handleDocClick)
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', handleAppFullscreenChange)
  document.removeEventListener('click', handleDocClick)
})

// ── 通知设置 ──────────────────────────────────────────────
const notifyModalVisible = ref(false)
const notifyWebhookInput = ref('')
const notifyAutoPush = ref(false)
const notifyConfigured = ref(false)
const notifyMaskedUrl = ref('')
const notifySaving = ref(false)
const notifyTesting = ref(false)
const notifyMsg = ref('')
const notifyMsgType = ref('') // 'success' | 'error'

async function openNotifyModal() {
  notifyMsg.value = ''
  notifyWebhookInput.value = ''
  notifyModalVisible.value = true
  try {
    const res = await getNotifyConfig()
    if (res.success) {
      notifyConfigured.value = res.configured
      notifyMaskedUrl.value = res.masked_url
      notifyAutoPush.value = res.auto_push
    }
  } catch (e) {
    console.error('获取通知配置失败', e)
  }
}

async function saveNotify() {
  if (!notifyWebhookInput.value.trim() && !notifyConfigured.value) {
    notifyMsg.value = '请输入 Webhook URL'
    notifyMsgType.value = 'error'
    return
  }
  notifySaving.value = true
  notifyMsg.value = ''
  try {
    const res = await saveNotifyConfig(notifyWebhookInput.value.trim(), notifyAutoPush.value)
    if (res.success) {
      notifyMsg.value = '配置已保存'
      notifyMsgType.value = 'success'
      notifyConfigured.value = true
      const cfg = await getNotifyConfig()
      if (cfg.success) notifyMaskedUrl.value = cfg.masked_url
      notifyWebhookInput.value = ''
    } else {
      notifyMsg.value = res.message || '保存失败'
      notifyMsgType.value = 'error'
    }
  } catch (e) {
    notifyMsg.value = e?.response?.data?.message || e?.message || '保存失败'
    notifyMsgType.value = 'error'
  } finally {
    notifySaving.value = false
  }
}

async function testNotify() {
  const url = notifyWebhookInput.value.trim()
  // 输入框有值则测试新 URL，否则用已保存的配置
  if (!url && !notifyConfigured.value) {
    notifyMsg.value = '请先输入 Webhook URL 再测试'
    notifyMsgType.value = 'error'
    return
  }
  notifyTesting.value = true
  notifyMsg.value = ''
  try {
    const res = await testNotifyWebhook(url)  // url 为空时后端自动用已保存的
    if (res.success) {
      notifyMsg.value = '✅ 测试消息已发送，请在群内查看'
      notifyMsgType.value = 'success'
    } else {
      notifyMsg.value = res.message || '发送失败'
      notifyMsgType.value = 'error'
    }
  } catch (e) {
    notifyMsg.value = e?.response?.data?.message || e?.message || '请求失败'
    notifyMsgType.value = 'error'
  } finally {
    notifyTesting.value = false
  }
}

async function clearNotify() {
  if (!confirm('确认清除 Webhook 配置？')) return
  try {
    await clearNotifyConfig()
    notifyConfigured.value = false
    notifyMaskedUrl.value = ''
    notifyWebhookInput.value = ''
    notifyAutoPush.value = false
    notifyMsg.value = '已清除'
    notifyMsgType.value = 'success'
  } catch (e) {
    notifyMsg.value = '清除失败'
    notifyMsgType.value = 'error'
  }
}

const moreMenuOpen = ref(false)
function toggleMoreMenu() { moreMenuOpen.value = !moreMenuOpen.value }
function closeMoreMenu() { moreMenuOpen.value = false }

const briefGenerating = ref(false)
async function handleGenerateBrief() {
  if (!zaigongLatestRecordId.value || briefGenerating.value) return
  briefGenerating.value = true
  try {
    const blob = await generateBriefImage(
      zaigongLatestRecordId.value,
      budgetLatestRecordId.value || null
    )
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `在建工程简报.png`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (e) {
    const msg = e?.response?.data?.message || e?.message || '简报生成失败'
    alert(msg)
  } finally {
    briefGenerating.value = false
  }
}


const navPushing = ref(false)
async function handleNavPush() {
  if (!zaigongLatestRecordId.value || navPushing.value) return
  navPushing.value = true
  try {
    const res = await pushNotify(zaigongLatestRecordId.value)
    if (res.success) {
      alert('推送成功，请在飞书/企业微信中查看')
    } else {
      alert(res.message || '推送失败')
    }
  } catch (e) {
    const msg = e?.response?.data?.message || e?.message || '推送失败'
    alert(msg)
  } finally {
    navPushing.value = false
  }
}
</script>


<template>
  <div class="app-shell" :class="{ 'presentation-mode': presentationMode }">

    <!-- ── Sidebar ───────────────────────────────────────── -->
    <aside class="app-sidebar" v-if="!presentationMode">
      <div class="sidebar-brand">
        <div class="brand-mark">CTC</div>
        <div>
          <div class="brand-name">工程数据分析</div>
          <span class="brand-sub">仙桃 · 云网发展部</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <div class="side-section">
          <div class="side-label">分析</div>
          <div class="side-link" :class="{ active: currentView === 'overview' }" @click="switchView('overview')">
            <svg class="side-icn" viewBox="0 0 16 16" fill="none"><path d="M8 2l1.5 4.5L14 8l-4.5 1.5L8 14l-1.5-4.5L2 8l4.5-1.5L8 2z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/></svg>
            <span>设计说明</span>
          </div>
          <div class="side-link" :class="{ active: currentView === 'zaigong' }" @click="switchView('zaigong')">
            <svg class="side-icn" viewBox="0 0 16 16" fill="none"><path d="M8 2l6 3-6 3-6-3 6-3zM2 8l6 3 6-3M2 11l6 3 6-3" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/></svg>
            <span>在建工程</span>
            <span v-if="zaigongData" class="side-badge">24</span>
          </div>
          <div class="side-link" :class="{ active: currentView === 'budget' }" @click="switchView('budget')">
            <svg class="side-icn" viewBox="0 0 16 16" fill="none"><path d="M2 13h12M4 10v3M7 6v7M10 8v5M13 4v9" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
            <span>预算立项</span>
          </div>
          <div class="side-link"
            :class="{ active: currentView === 'key-indicators', disabled: !canShowKeyIndicators }"
            @click="canShowKeyIndicators && switchView('key-indicators')"
          >
            <svg class="side-icn" viewBox="0 0 16 16" fill="none"><path d="M3 11a5 5 0 0110 0M8 11l3-3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
            <span>关键指标</span>
          </div>
        </div>
        <div class="side-section">
          <div class="side-label">工具</div>
          <div class="side-link disabled">
            <svg class="side-icn" viewBox="0 0 16 16" fill="none"><path d="M5 5h6v6H5zM5 5V3a2 2 0 00-2 2h2zM11 5V3a2 2 0 012 2h-2zM5 11v2a2 2 0 01-2-2h2zM11 11v2a2 2 0 002-2h-2z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/></svg>
            <span>预警规则</span>
            <span class="side-wip">WIP</span>
          </div>
          <div class="side-link disabled">
            <svg class="side-icn" viewBox="0 0 16 16" fill="none"><path d="M8 3v8M5 8l3 3 3-3M3 13h10" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span>导出与分享</span>
            <span class="side-wip">WIP</span>
          </div>
          <div class="side-link" @click="openHistoryCenter">
            <svg class="side-icn" viewBox="0 0 16 16" fill="none"><path d="M2 5h12v9H2V5zM2 5V3h12v2M5 2v3M11 2v3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span>上传历史</span>
          </div>
          <div class="side-link" @click="openNotifyModal">
            <svg class="side-icn" viewBox="0 0 16 16" fill="none"><path d="M12 5a4 4 0 0 0-8 0c0 5-2 6-2 6h12s-2-1-2-6M9 13.5a1 1 0 0 1-2 0" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
            <span>通知设置</span>
            <span v-if="notifyConfigured" class="side-dot ok"></span>
          </div>
        </div>
      </nav>

      <div class="sidebar-foot">
        <strong>当月窗口</strong>
        <span>{{ currentMonthLabel }}</span>
        <span class="side-version">v0.4 · 内部预览</span>
        <div v-if="zaigongLatestRecordId" class="sidebar-actions">
          <div class="more-menu-wrap" @click.stop>
            <button class="side-more-btn" :class="{ open: moreMenuOpen }" @click="toggleMoreMenu">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><circle cx="12" cy="5" r="1.2" fill="currentColor"/><circle cx="12" cy="12" r="1.2" fill="currentColor"/><circle cx="12" cy="19" r="1.2" fill="currentColor"/></svg>
              更多操作
            </button>
            <div v-if="moreMenuOpen" class="more-menu-dropdown">
              <button class="more-menu-item" :disabled="briefGenerating" @click="handleGenerateBrief(); closeMoreMenu()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><rect x="5" y="2" width="14" height="20" rx="2"/><path d="M12 18h.01"/></svg>
                {{ briefGenerating ? '生成中…' : '手机简报' }}
              </button>
              <button v-if="notifyConfigured" class="more-menu-item" :disabled="navPushing" @click="handleNavPush(); closeMoreMenu()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><path d="M22 2L11 13"/><path d="M22 2L15 22 11 13 2 9l20-7z"/></svg>
                {{ navPushing ? '推送中…' : '推送播报' }}
              </button>
            </div>
          </div>
          <button v-if="currentView === 'key-indicators'" class="side-more-btn" @click="togglePresentationMode">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="13" height="13"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
            展示模式
          </button>
        </div>
      </div>
    </aside>

    <!-- ── Canvas ─────────────────────────────────────────── -->
    <main class="app-canvas">
      <div v-if="currentView === 'overview'" class="page">
        <header class="page-head">
          <div class="page-head-l">
            <span class="eyebrow">重设计提案 · v0.4</span>
            <h1 class="page-title">给「工程数据分析」一次安静的呼吸</h1>
            <div class="page-meta">
              <span>提案人 · Claude</span>
              <span class="sep"></span>
              <span>基于 dashboard.html / budget.html / key-indicators.html</span>
            </div>
          </div>
        </header>
        <div class="section">
          <div class="section-head"><h2>四个原则</h2></div>
          <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:1px;background:var(--line);border:1px solid var(--line);border-radius:var(--r-lg)">
            <div style="background:var(--surface);padding:24px 26px">
              <div style="font-family:var(--font-mono);font-size:11px;color:var(--accent);letter-spacing:0.08em;margin-bottom:10px">P · 01</div>
              <div style="font-size:16px;font-weight:500;color:var(--ink);margin-bottom:6px">克制压倒装饰</div>
              <div style="font-size:13px;color:var(--ink-2);line-height:1.6">纸感背景、单一强调色、高对比层级。装饰只在必要处出现。</div>
            </div>
            <div style="background:var(--surface);padding:24px 26px">
              <div style="font-family:var(--font-mono);font-size:11px;color:var(--accent);letter-spacing:0.08em;margin-bottom:10px">P · 02</div>
              <div style="font-size:16px;font-weight:500;color:var(--ink);margin-bottom:6px">空间是数据的呼吸</div>
              <div style="font-size:13px;color:var(--ink-2);line-height:1.6">KPI 之间留 1px 分隔线，section 之间 56px，卡片之间 24px。</div>
            </div>
            <div style="background:var(--surface);padding:24px 26px">
              <div style="font-family:var(--font-mono);font-size:11px;color:var(--accent);letter-spacing:0.08em;margin-bottom:10px">P · 03</div>
              <div style="font-size:16px;font-weight:500;color:var(--ink);margin-bottom:6px">数字优先于图表</div>
              <div style="font-size:13px;color:var(--ink-2);line-height:1.6">所有数字 tabular-nums，右对齐。图表只在解释趋势时出现。</div>
            </div>
            <div style="background:var(--surface);padding:24px 26px">
              <div style="font-family:var(--font-mono);font-size:11px;color:var(--accent);letter-spacing:0.08em;margin-bottom:10px">P · 04</div>
              <div style="font-size:16px;font-weight:500;color:var(--ink);margin-bottom:6px">可截图汇报</div>
              <div style="font-size:13px;color:var(--ink-2);line-height:1.6">每个区块独立成稿，配色和留白考虑截图贴入周报 PPT 的场景。</div>
            </div>
          </div>
        </div>
        <div class="section">
          <div class="section-head"><h2>三个页面</h2><span class="sub">点击进入</span></div>
          <div style="display:flex;flex-direction:column;border:1px solid var(--line);border-radius:var(--r-lg);overflow:hidden;background:var(--surface)">
            <div v-for="(s, i) in overviewPages" :key="s.id"
              style="padding:20px 24px;display:flex;align-items:center;gap:24px;cursor:pointer;transition:background 0.12s"
              :style="{ borderBottom: i < overviewPages.length - 1 ? '1px solid var(--line)' : 'none' }"
              @click="switchView(s.id)"
              @mouseenter="$event.currentTarget.style.background='var(--surface-2)'"
              @mouseleave="$event.currentTarget.style.background='var(--surface)'"
            >
              <div style="font-family:var(--font-mono);font-size:11px;color:var(--ink-3);width:24px">0{{i+1}}</div>
              <div style="flex:1">
                <div style="font-size:15px;font-weight:500;color:var(--ink)">{{ s.t }}</div>
                <div style="font-size:12.5px;color:var(--ink-3);margin-top:3px">{{ s.d }}</div>
              </div>
              <div style="font-size:11px;color:var(--ink-3);font-family:var(--font-mono)">{{ s.count }}</div>
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" style="opacity:0.4"><path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </div>
          </div>
        </div>
      </div>
      <Dashboard
        v-if="currentView === 'zaigong'"
        :initial-data="zaigongData"
        :initial-record-id="zaigongLatestRecordId"
        :analysis-date="zaigongDate"
        :latest-data="zaigongLatestData"
        :snapshot-label="zaigongSnapshotLabel"
        :four-class-warnings="zaigongFourClassWarnings"
        @data-update="onZaigongDataUpdate"
        @restore-latest="onZaigongRestoreLatest"
        @warnings-update="onZaigongWarningsUpdate"
      />
      <Budget
        v-else-if="currentView === 'budget'"
        :initial-data="budgetData"
        :analysis-date="budgetDate"
        :latest-data="budgetLatestData"
        :snapshot-label="budgetSnapshotLabel"
        @data-update="onBudgetDataUpdate"
        @restore-latest="onBudgetRestoreLatest"
      />
      <KeyIndicators
        v-else-if="currentView === 'key-indicators'"
        :zaigong-data="zaigongData"
        :budget-data="budgetData"
        :zaigong-date="zaigongDate"
        :budget-date="budgetDate"
        :four-class-warnings="zaigongFourClassWarnings"
        @presentation-change="onPresentationChange"
      />
    </main>

    <!-- ── 历史记录中心 ──────────────────────────────────── -->
    <div v-if="historyCenterVisible" class="gh-overlay" @click.self="closeHistoryCenter">
      <aside class="gh-panel">
        <div class="gh-head">
          <div class="gh-head-left">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            <h3>历史记录中心</h3>
            <span class="gh-badge">{{ zaigongHistory.length + budgetHistory.length }}</span>
          </div>
          <button class="gh-close" @click="closeHistoryCenter">×</button>
        </div>

        <div class="gh-tabs">
          <button :class="{ active: historyTab === 'all' }" @click="historyTab = 'all'">全部</button>
          <button :class="{ active: historyTab === 'zaigong' }" @click="historyTab = 'zaigong'">在建工程</button>
          <button :class="{ active: historyTab === 'budget' }" @click="historyTab = 'budget'">预算立项</button>
          <button :class="{ active: historyTab === 'trend' }" @click="historyTab = 'trend'">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            趋势图
          </button>
        </div>

        <div v-if="historyCenterLoading" class="gh-empty"><p>正在读取历史记录…</p></div>

        <div v-else-if="historyTab === 'trend'" class="gh-trend">
          <div v-if="!trendPoints" class="gh-empty">在建工程数据不足，上传至少 2 次后可查看趋势图。</div>
          <template v-else>
            <div class="gh-trend-head">
              <h4>在建工程指标趋势</h4>
              <div class="gh-legend">
                <span><span class="gh-dot" style="background:var(--accent)"></span>支出进度</span>
                <span><span class="gh-dot" style="background:var(--warn)"></span>转固率</span>
                <span style="font-size:11px;color:var(--ink-4)">— 60% 参考线</span>
              </div>
            </div>
            <svg class="gh-svg" viewBox="0 0 560 270" preserveAspectRatio="xMidYMid meet">
              <g v-for="tick in trendPoints.yTicks" :key="tick.label">
                <line :x1="48" :y1="tick.y" :x2="545" :y2="tick.y" stroke="#807A6C" stroke-opacity="0.15" stroke-width="1"/>
                <text :x="42" :y="tick.y + 4" text-anchor="end" font-size="10" fill="#807A6C" opacity="0.7">{{ tick.label }}</text>
              </g>
              <line :x1="48" :y1="trendPoints.refY60" :x2="545" :y2="trendPoints.refY60" stroke="#B8842C" stroke-opacity="0.4" stroke-width="1" stroke-dasharray="5 4"/>
              <line x1="48" y1="215" x2="545" y2="215" stroke="#807A6C" stroke-opacity="0.2" stroke-width="1"/>
              <polyline :points="trendPoints.progressPolyline" fill="none" stroke="#C96442" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
              <polyline :points="trendPoints.ratePolyline" fill="none" stroke="#B8842C" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
              <g v-for="(p, i) in trendPoints.progressPoints" :key="'cp'+i">
                <title>{{ trendPoints.labels[i].text }}｜支出进度 {{ p.v }}%</title>
                <circle :cx="p.x" :cy="p.y" r="4.5" fill="#C96442" stroke="#fff" stroke-width="1.5"/>
                <text v-if="trendPoints.showLabels" :x="p.x" :y="p.y - 9" text-anchor="middle" font-size="9" fill="#C96442">{{ p.v }}%</text>
              </g>
              <g v-for="(p, i) in trendPoints.ratePoints" :key="'rp'+i">
                <title>{{ trendPoints.labels[i].text }}｜转固率 {{ p.v }}%</title>
                <circle :cx="p.x" :cy="p.y" r="4.5" fill="#B8842C" stroke="#fff" stroke-width="1.5"/>
                <text v-if="trendPoints.showLabels" :x="p.x" :y="p.y - 9" text-anchor="middle" font-size="9" fill="#B8842C">{{ p.v }}%</text>
              </g>
              <text v-for="label in trendPoints.labels" :key="'xl'+label.x" :x="label.x" y="220" text-anchor="end" :transform="`rotate(-35, ${label.x}, 220)`" font-size="10" fill="#807A6C">{{ label.text }}</text>
            </svg>
          </template>
        </div>

        <div v-else class="gh-body">
          <section v-for="section in historySections" :key="section.key" class="gh-section">
            <div class="gh-section-head">
              <div class="gh-sec-left">
                <h4>{{ section.title }}</h4>
                <span class="gh-count">{{ section.records.length }}</span>
              </div>
              <button
                v-if="(section.key === 'zaigong' && zaigongSnapshotLabel) || (section.key === 'budget' && budgetSnapshotLabel)"
                class="gh-restore"
                @click="switchView(section.key === 'zaigong' ? 'zaigong' : 'budget'); restoreCurrentModuleLatest()"
              >↩ 返回最新</button>
            </div>

            <div v-if="section.records.length === 0" class="gh-empty compact"><p>暂无记录</p></div>

            <div v-else class="gh-card-list">
              <button
                v-for="record in section.records"
                :key="`${section.key}-${record.id}`"
                class="gh-card"
                @click="section.key === 'zaigong' ? openZaigongSnapshot(record.id) : openBudgetSnapshot(record.id)"
              >
                <div class="ghc-top">
                  <strong class="ghc-name">{{ record.source_filename }}</strong>
                  <span class="ghc-id">#{{ record.id }}</span>
                </div>
                <div class="ghc-chips">
                  <span class="ghc-chip">{{ formatHistoryTime(record.uploaded_at) }}</span>
                  <span v-if="section.key === 'zaigong' && record.file_date" class="ghc-chip">{{ formatFileDate(record.file_date) }}</span>
                  <span v-if="section.key === 'zaigong' && record.target_value" class="ghc-chip">目标 {{ record.target_value }} 万</span>
                </div>
                <div v-if="section.key === 'zaigong' && record.metrics && record.metrics.progress_pct != null" class="ghc-kpis">
                  <span class="ghc-kpi"><em>支出进度</em><b>{{ (record.metrics.progress_pct || 0).toFixed(1) }}%</b></span>
                  <span class="ghc-sep"></span>
                  <span class="ghc-kpi"><em>转固率</em><b>{{ ((record.metrics.total_rate || 0) * 100).toFixed(1) }}%</b></span>
                  <span class="ghc-sep"></span>
                  <span class="ghc-kpi"><em>资本支出</em><b>{{ (record.metrics.total_current || 0).toFixed(0) }} 万</b></span>
                </div>
                <div class="ghc-actions" @click.stop>
                  <button class="ghc-slot" :class="{ active: isSelectedForCompare(section.key, 'left', record.id) }" @click.stop="selectCompareRecord(section.key, 'left', record)">A</button>
                  <button class="ghc-slot" :class="{ active: isSelectedForCompare(section.key, 'right', record.id) }" @click.stop="selectCompareRecord(section.key, 'right', record)">B</button>
                </div>
              </button>
            </div>

            <div v-if="section.key === 'zaigong'" class="gh-compare">
              <div class="ghcmp-head">
                <h5>历史对比</h5>
                <span>{{ getRecordDateLabel('zaigong', zaigongCompareSelection.left) }} vs {{ getRecordDateLabel('zaigong', zaigongCompareSelection.right) }}</span>
              </div>
              <div v-if="zaigongCompareResult" class="ghcmp-grid">
                <div class="ghcmp-card">
                  <span>资本性支出</span>
                  <strong>{{ zaigongCompareResult.capitalCurrent.toFixed(2) }} 万</strong>
                  <p>{{ zaigongCompareResult.capitalDiff >= 0 ? '+' : '' }}{{ zaigongCompareResult.capitalDiff.toFixed(2) }} 万，完成率 {{ zaigongCompareResult.progressDiff >= 0 ? '+' : '' }}{{ zaigongCompareResult.progressDiff.toFixed(1) }} pct</p>
                </div>
                <div class="ghcmp-card">
                  <span>转固率</span>
                  <strong>{{ (zaigongCompareResult.rateCurrent * 100).toFixed(1) }}%</strong>
                  <p>变化 {{ zaigongCompareResult.rateDiff >= 0 ? '+' : '' }}{{ zaigongCompareResult.rateDiff.toFixed(1) }} pct</p>
                </div>
              </div>
              <div v-if="zaigongCompareResult" class="ghcmp-table">
                <div class="ghcmp-table-head">管理员推进 Top 5</div>
                <table>
                  <thead><tr><th>管理员</th><th>当前</th><th>变化</th></tr></thead>
                  <tbody>
                    <tr v-for="item in zaigongCompareResult.top5" :key="item.name">
                      <td>{{ item.name }}</td><td>{{ item.current.toFixed(2) }}</td>
                      <td :class="item.diff >= 0 ? 'delta-up' : 'delta-down'">{{ item.diff >= 0 ? '+' : '' }}{{ item.diff.toFixed(2) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div v-if="section.key === 'budget'" class="gh-compare">
              <div class="ghcmp-head">
                <h5>历史对比</h5>
                <span>{{ getRecordDateLabel('budget', budgetCompareSelection.left) }} vs {{ getRecordDateLabel('budget', budgetCompareSelection.right) }}</span>
              </div>
              <div v-if="budgetCompareResult" class="ghcmp-grid">
                <div class="ghcmp-card">
                  <span>年度预算</span>
                  <strong>{{ budgetCompareResult.budgetCurrent.toFixed(2) }} 万</strong>
                  <p>变化 {{ budgetCompareResult.budgetDiff >= 0 ? '+' : '' }}{{ budgetCompareResult.budgetDiff.toFixed(2) }} 万</p>
                </div>
                <div class="ghcmp-card">
                  <span>立项进度</span>
                  <strong>{{ (budgetCompareResult.progressCurrent * 100).toFixed(1) }}%</strong>
                  <p>变化 {{ budgetCompareResult.progressDiff >= 0 ? '+' : '' }}{{ budgetCompareResult.progressDiff.toFixed(1) }} pct</p>
                </div>
              </div>
              <div v-if="budgetCompareResult" class="ghcmp-table">
                <div class="ghcmp-table-head">专业推进 Top 5</div>
                <table>
                  <thead><tr><th>专业</th><th>当前</th><th>变化</th></tr></thead>
                  <tbody>
                    <tr v-for="item in budgetCompareResult.top5" :key="item.name">
                      <td>{{ item.name }}</td><td>{{ (item.currentProgress * 100).toFixed(1) }}%</td>
                      <td :class="item.diff >= 0 ? 'delta-up' : 'delta-down'">{{ item.diff >= 0 ? '+' : '' }}{{ item.diff.toFixed(1) }} pct</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        </div>
      </aside>
    </div>

    <!-- ── 通知设置弹窗 ──────────────────────────────────── -->
    <div v-if="notifyModalVisible" class="notify-overlay" @click.self="notifyModalVisible = false">
      <div class="notify-modal">
        <div class="notify-modal-header">
          <h3>通知设置</h3>
          <button class="modal-close" @click="notifyModalVisible = false">×</button>
        </div>
        <div class="notify-modal-body">
          <div class="notify-status-row">
            <span class="notify-status-label">当前状态：</span>
            <span v-if="notifyConfigured" class="notify-badge configured">已配置</span>
            <span v-else class="notify-badge unconfigured">未配置</span>
            <span v-if="notifyConfigured" class="notify-masked">{{ notifyMaskedUrl }}</span>
            <button v-if="notifyConfigured" class="notify-clear-btn" @click="clearNotify">清除</button>
          </div>
          <div class="notify-field">
            <label>Webhook URL</label>
            <input v-model="notifyWebhookInput" type="text" placeholder="飞书或企业微信 Webhook URL" class="notify-input" />
            <p class="notify-hint">飞书：添加自定义机器人 → 复制 Webhook<br>企业微信：群聊 → 添加群机器人 → 复制 Webhook</p>
          </div>
          <div class="notify-field notify-toggle-row">
            <label>上传后自动推送</label>
            <label class="toggle-switch">
              <input type="checkbox" v-model="notifyAutoPush" />
              <span class="toggle-slider"></span>
            </label>
          </div>
          <div v-if="notifyMsg" :class="['notify-msg', notifyMsgType]">{{ notifyMsg }}</div>
          <div class="notify-actions">
            <button class="notify-btn-test" :disabled="notifyTesting" @click="testNotify">{{ notifyTesting ? '发送中…' : '发送测试消息' }}</button>
            <button class="notify-btn-save" :disabled="notifySaving" @click="saveNotify">{{ notifySaving ? '保存中…' : '保存配置' }}</button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

/* ── App shell: sidebar + canvas ── */
#app {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 232px 1fr;
}

.app-shell {
  display: contents;
}

.app-shell.presentation-mode {
  display: block;
}

.app-shell.presentation-mode .app-canvas {
  padding: 0;
  min-height: 100vh;
  background: #07111f;
}

/* ── Sidebar ── */
.app-sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--paper-2);
  border-right: 1px solid var(--line);
  padding: 24px 18px;
  overflow-y: auto;
  z-index: 10;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 6px;
  margin-bottom: 20px;
}

.brand-mark {
  width: 28px;
  height: 28px;
  border-radius: 7px;
  background: var(--accent);
  color: #fff;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.05em;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.brand-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--ink);
  letter-spacing: -0.005em;
  line-height: 1.2;
}

.brand-sub {
  display: block;
  font-size: 11px;
  color: var(--ink-3);
  margin-top: 2px;
  font-weight: 400;
}

/* Nav */
.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.side-section {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.side-label {
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-4);
  padding: 0 8px 6px;
}

.side-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 8px;
  border-radius: var(--r-md);
  font-size: 13px;
  color: var(--ink-2);
  cursor: pointer;
  user-select: none;
  transition: background 0.12s, color 0.12s;
}

.side-link:hover:not(.disabled) {
  background: rgba(31,29,24,0.04);
  color: var(--ink);
}

.side-link.active {
  background: rgba(31,29,24,0.06);
  color: var(--ink);
  font-weight: 500;
}

.side-link.disabled {
  opacity: 0.4;
  cursor: default;
}

.side-icn {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  opacity: 0.7;
}

.side-link.active .side-icn { opacity: 1; }

.side-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  margin-left: auto;
  flex-shrink: 0;
}

.side-dot.ok { background: var(--ok); }

.side-badge {
  margin-left: auto;
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--ink-3);
  padding: 1px 5px;
  background: var(--paper);
  border-radius: 3px;
}

.side-wip {
  margin-left: auto;
  font-size: 10px;
  color: var(--ink-4);
  font-weight: 500;
}

/* Sidebar footer */
.sidebar-foot {
  margin-top: auto;
  padding-top: 14px;
  border-top: 1px solid var(--line);
  font-size: 11px;
  color: var(--ink-3);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sidebar-foot > strong {
  font-size: 12px;
  color: var(--ink-2);
  font-weight: 500;
}

.side-version {
  color: var(--ink-4);
  margin-bottom: 4px;
}

.sidebar-status {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ss-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11.5px;
  color: var(--ink-3);
}

.ss-row strong {
  font-size: 11.5px;
  font-weight: 500;
  color: var(--ink-2);
}

.sidebar-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.side-more-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 6px 8px;
  border-radius: var(--r-md);
  border: 1px solid var(--line);
  background: var(--surface);
  color: var(--ink-3);
  font-size: 12px;
  cursor: pointer;
  transition: 0.12s;
}

.side-more-btn:hover,
.side-more-btn.open {
  background: var(--paper);
  color: var(--ink);
  border-color: var(--line-2);
}

/* More dropdown */
.more-menu-wrap { position: relative; }

.more-menu-dropdown {
  position: absolute;
  bottom: calc(100% + 6px);
  left: 0;
  right: 0;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  padding: 4px;
  box-shadow: var(--shadow-pop);
  z-index: 200;
  animation: fadeUp .14s ease both;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(4px); }
  to   { opacity: 1; transform: translateY(0); }
}

.more-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 7px 10px;
  border-radius: var(--r-md);
  border: none;
  background: none;
  color: var(--ink-2);
  font-family: inherit;
  font-size: 12.5px;
  cursor: pointer;
  transition: .12s;
}

.more-menu-item:hover:not(:disabled) {
  background: var(--paper-2);
  color: var(--ink);
}

.more-menu-item:disabled { opacity: .4; cursor: not-allowed; }

/* ── Canvas ── */
.app-canvas {
  min-width: 0;
  background: var(--paper);
  min-height: 100vh;
  overflow-y: auto;
}

/* ── Page chrome (from new design) ── */
.page {
  max-width: 1180px;
  margin: 0 auto;
  padding: 56px 40px;
}

.page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  padding-bottom: 28px;
  margin-bottom: 36px;
  border-bottom: 1px solid var(--line);
}

.page-head-l {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.eyebrow {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--accent);
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.eyebrow::after {
  content: '';
  width: 28px;
  height: 1px;
  background: currentColor;
  opacity: 0.5;
}

.page-title {
  font-size: 30px;
  font-weight: 500;
  letter-spacing: -0.02em;
  color: var(--ink);
  margin: 0;
  line-height: 1.15;
}

.page-meta {
  display: flex;
  align-items: center;
  gap: 18px;
  color: var(--ink-3);
  font-size: 12px;
  margin-top: 4px;
}

.page-meta .sep {
  width: 3px;
  height: 3px;
  background: var(--ink-4);
  border-radius: 50%;
}

.section {
  margin-bottom: 56px;
}

.section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 16px;
  gap: 16px;
}

.section-head h2 {
  font-size: 13px;
  font-weight: 500;
  color: var(--ink-3);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin: 0;
}

.section-head .sub {
  font-size: 12px;
  color: var(--ink-3);
}

/* ── History center overlay ── */
.gh-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: flex;
  justify-content: flex-end;
  background: rgba(31,29,24,0.4);
  backdrop-filter: blur(4px);
}

.gh-panel {
  width: min(600px, 100%);
  height: 100%;
  background: var(--surface);
  border-left: 1px solid var(--line);
  box-shadow: -8px 0 40px rgba(31,29,24,0.08);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.gh-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--line);
  flex-shrink: 0;
}

.gh-head-left {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--ink-3);
}

.gh-head-left h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
}

.gh-badge {
  padding: 1px 7px;
  border-radius: 999px;
  background: var(--paper-2);
  color: var(--ink-3);
  font-size: 11px;
  font-weight: 600;
  font-family: var(--font-mono);
}

.gh-close {
  width: 28px;
  height: 28px;
  border-radius: var(--r-md);
  border: 1px solid var(--line);
  background: transparent;
  color: var(--ink-3);
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: 0.12s;
}
.gh-close:hover { background: var(--paper-2); color: var(--ink); }

.gh-tabs {
  display: flex;
  gap: 2px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--line);
  flex-shrink: 0;
}

.gh-tabs button {
  height: 28px;
  padding: 0 12px;
  border-radius: var(--r-md);
  border: none;
  background: transparent;
  color: var(--ink-3);
  font: inherit;
  font-size: 12.5px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: 0.12s;
}

.gh-tabs button:hover:not(.active) { background: var(--paper-2); color: var(--ink); }
.gh-tabs button.active { background: var(--ink); color: var(--surface); }

.gh-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.gh-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 20px;
  color: var(--ink-4);
  font-size: 13px;
}

.gh-empty.compact { padding: 20px; }

.gh-trend { flex: 1; overflow-y: auto; padding: 16px; }

.gh-trend-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.gh-trend-head h4 { font-size: 13px; font-weight: 600; color: var(--ink); margin: 0; }

.gh-legend {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 11.5px;
  color: var(--ink-3);
}

.gh-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  margin-right: 4px;
}

.gh-svg { width: 100%; height: auto; display: block; overflow: visible; }

.gh-section { display: flex; flex-direction: column; gap: 10px; }

.gh-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.gh-sec-left { display: flex; align-items: center; gap: 8px; }

.gh-sec-left h4 {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--ink-3);
  margin: 0;
}

.gh-count {
  height: 16px;
  padding: 0 5px;
  border-radius: 999px;
  background: var(--paper-2);
  color: var(--ink-4);
  font-size: 10.5px;
  font-weight: 600;
  display: flex;
  align-items: center;
  font-family: var(--font-mono);
}

.gh-restore {
  font-size: 11.5px;
  color: var(--accent);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}
.gh-restore:hover { text-decoration: underline; }

.gh-card-list { display: flex; flex-direction: column; gap: 6px; }

.gh-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
  text-align: left;
  padding: 10px 12px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  cursor: pointer;
  transition: 0.12s;
}

.gh-card:hover { border-color: var(--line-2); box-shadow: var(--shadow-card); }

.ghc-top { display: flex; align-items: center; justify-content: space-between; gap: 8px; }

.ghc-name { font-size: 12.5px; font-weight: 500; color: var(--ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.ghc-id { font-size: 10.5px; color: var(--ink-4); font-family: var(--font-mono); flex-shrink: 0; }

.ghc-chips { display: flex; gap: 4px; flex-wrap: wrap; }

.ghc-chip {
  font-size: 10.5px;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--paper-2);
  color: var(--ink-3);
  font-family: var(--font-mono);
}

.ghc-kpis {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-top: 4px;
  border-top: 1px dashed var(--line);
}

.ghc-kpi { display: flex; align-items: center; gap: 4px; font-size: 11.5px; }
.ghc-kpi em { color: var(--ink-4); font-style: normal; font-size: 10.5px; }
.ghc-kpi b { color: var(--ink); font-weight: 600; font-family: var(--font-mono); }
.ghc-sep { width: 1px; height: 10px; background: var(--line); }

.ghc-actions { display: flex; gap: 4px; }

.ghc-slot {
  height: 20px;
  min-width: 24px;
  padding: 0 6px;
  border-radius: 4px;
  border: 1px solid var(--line);
  background: var(--paper-2);
  color: var(--ink-4);
  font-size: 10.5px;
  font-weight: 700;
  cursor: pointer;
  transition: 0.12s;
}

.ghc-slot.active { background: var(--ink); color: var(--surface); border-color: var(--ink); }

/* Compare panel */
.gh-compare {
  padding: 12px;
  background: var(--paper-2);
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ghcmp-head { display: flex; align-items: center; gap: 8px; }
.ghcmp-head h5 { font-size: 12px; font-weight: 600; color: var(--ink); margin: 0; }
.ghcmp-head span { font-size: 11px; color: var(--ink-4); }

.ghcmp-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }

.ghcmp-card {
  padding: 10px 12px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ghcmp-card span { font-size: 11px; color: var(--ink-4); }
.ghcmp-card strong { font-size: 14px; font-weight: 600; color: var(--ink); font-family: var(--font-mono); }
.ghcmp-card p { font-size: 11px; color: var(--ink-3); margin: 0; }

.ghcmp-table { display: flex; flex-direction: column; gap: 4px; }
.ghcmp-table-head { font-size: 11px; font-weight: 600; color: var(--ink-3); }

.ghcmp-table table { width: 100%; border-collapse: collapse; font-size: 12px; }
.ghcmp-table th { text-align: left; padding: 4px 6px; color: var(--ink-4); font-weight: 500; }
.ghcmp-table td { padding: 4px 6px; border-bottom: 1px solid var(--line); color: var(--ink-2); }

.delta-up { color: var(--ok); font-weight: 600; }
.delta-down { color: var(--bad); font-weight: 600; }

/* ── Notify modal ── */
.notify-overlay {
  position: fixed;
  inset: 0;
  background: rgba(31,29,24,0.4);
  backdrop-filter: blur(4px);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.notify-modal {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-xl);
  width: 480px;
  max-width: 95vw;
  box-shadow: var(--shadow-pop);
}

.notify-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--line);
}

.notify-modal-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
}

.notify-modal-header .modal-close {
  background: none;
  border: none;
  font-size: 18px;
  color: var(--ink-4);
  cursor: pointer;
  line-height: 1;
  padding: 0 4px;
}

.notify-modal-body {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.notify-status-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
  color: var(--ink-3);
}

.notify-badge {
  font-size: 10.5px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 20px;
}

.notify-badge.configured { background: var(--ok-soft); color: var(--ok); }
.notify-badge.unconfigured { background: var(--paper-2); color: var(--ink-4); }

.notify-masked {
  font-size: 11.5px;
  color: var(--ink-4);
  font-family: var(--font-mono);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notify-clear-btn {
  font-size: 11.5px;
  padding: 2px 9px;
  border: 1px solid var(--bad-soft);
  border-radius: 4px;
  background: transparent;
  color: var(--bad);
  cursor: pointer;
  flex-shrink: 0;
}
.notify-clear-btn:hover { background: var(--bad-soft); }

.notify-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.notify-field label { font-size: 12.5px; font-weight: 600; color: var(--ink-2); }

.notify-input {
  width: 100%;
  padding: 7px 10px;
  font-size: 12.5px;
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
  outline: none;
  color: var(--ink);
  background: var(--surface);
}
.notify-input:focus { border-color: var(--accent); }

.notify-hint { margin: 0; font-size: 11px; color: var(--ink-4); line-height: 1.5; }

.notify-toggle-row { flex-direction: row !important; align-items: center; justify-content: space-between; }

.toggle-switch { position: relative; display: inline-block; width: 36px; height: 20px; cursor: pointer; }
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.toggle-slider { position: absolute; inset: 0; background: var(--line-2); border-radius: 20px; transition: background 0.2s; }
.toggle-slider::before { content: ''; position: absolute; width: 14px; height: 14px; left: 3px; top: 3px; background: #fff; border-radius: 50%; transition: transform 0.2s; }
.toggle-switch input:checked + .toggle-slider { background: var(--accent); }
.toggle-switch input:checked + .toggle-slider::before { transform: translateX(16px); }

.notify-msg { font-size: 12.5px; padding: 7px 11px; border-radius: var(--r-md); }
.notify-msg.success { background: var(--ok-soft); color: var(--ok); }
.notify-msg.error { background: var(--bad-soft); color: var(--bad); }

.notify-actions { display: flex; gap: 8px; justify-content: flex-end; }

.notify-btn-test {
  padding: 6px 14px;
  font-size: 12.5px;
  border: 1px solid var(--line-2);
  border-radius: var(--r-md);
  background: var(--surface);
  color: var(--ink-2);
  cursor: pointer;
  font-weight: 500;
  font-family: inherit;
}
.notify-btn-test:hover:not(:disabled) { background: var(--paper-2); }

.notify-btn-save {
  padding: 6px 18px;
  font-size: 12.5px;
  border: none;
  border-radius: var(--r-md);
  background: var(--ink);
  color: var(--surface);
  cursor: pointer;
  font-weight: 600;
  font-family: inherit;
}
.notify-btn-save:hover:not(:disabled) { background: var(--ink-2); }
.notify-btn-test:disabled, .notify-btn-save:disabled { opacity: 0.45; cursor: not-allowed; }
</style>
