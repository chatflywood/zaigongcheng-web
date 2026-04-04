<script setup>
import { ref, computed, onMounted } from 'vue'
import Dashboard from './views/Dashboard.vue'
import Budget from './views/Budget.vue'
import KeyIndicators from './views/KeyIndicators.vue'
import { getHistory, getHistorySnapshot, getBudgetHistory, getBudgetHistorySnapshot, getNotifyConfig, saveNotifyConfig, clearNotifyConfig, testNotifyWebhook, pushNotify } from './api'

const currentView = ref('zaigong')
const isAnalystMode = computed(() => currentView.value !== 'key-indicators')

const zaigongLatestData = ref(null)
const budgetLatestData = ref(null)
const zaigongData = ref(null)
const budgetData = ref(null)
const zaigongLatestRecordId = ref(null)
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
  if (currentView.value === 'budget') return '预算立项'
  if (currentView.value === 'key-indicators') return '大屏模式'
  return '在建工程'
})

function switchView(view) {
  currentView.value = view
  if (view !== 'key-indicators') {
    presentationMode.value = false
  }
}

function onPresentationChange(active) {
  presentationMode.value = Boolean(active)
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
        budgetDate.value = formatHistoryTime(cur.uploaded_at)
        budgetLatestDate.value = budgetDate.value
      }
    }
  } catch (err) {
    console.error('自动加载最新数据失败:', err)
  }
}

onMounted(loadLatestDataOnMount)

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
  <div class="app-shell" :class="{ 'analyst-mode': isAnalystMode, 'presentation-mode': presentationMode }">
    <div class="backdrop backdrop-grid"></div>
    <div class="backdrop backdrop-glow glow-a"></div>
    <div class="backdrop backdrop-glow glow-b"></div>

    <header v-if="!presentationMode" class="top-nav" :class="{ 'analyst-nav': isAnalystMode }">
      <div class="nav-brand">
        <div class="brand-mark">ZT</div>
        <div class="brand-copy">
          <span class="brand-text">工程建设数据驾驶舱</span>
        </div>
      </div>

      <div class="nav-links nav-main-links">
        <button
          :class="{ active: currentView === 'zaigong' }"
          @click="switchView('zaigong')"
        >
          <span class="btn-label">在建工程</span>
          <span v-if="zaigongData" class="data-indicator"></span>
        </button>
        <button
          :class="{ active: currentView === 'budget' }"
          @click="switchView('budget')"
        >
          <span class="btn-label">预算立项</span>
          <span v-if="budgetData" class="data-indicator warning"></span>
        </button>
        <button
          :class="{ active: currentView === 'key-indicators', disabled: !canShowKeyIndicators }"
          @click="switchView('key-indicators')"
          :title="canShowKeyIndicators ? '查看大屏模式' : '请先上传两个分析数据'"
        >
          <span class="btn-label">大屏模式</span>
          <span v-if="canShowKeyIndicators" class="data-indicator success"></span>
        </button>
      </div>
      <div class="nav-links nav-end-links">
        <button class="history-nav-button" @click="openHistoryCenter">
          <span class="btn-label">历史记录</span>
        </button>
        <button
          v-if="notifyConfigured && zaigongLatestRecordId"
          class="push-nav-button"
          :disabled="navPushing"
          @click="handleNavPush"
          title="推送最新数据播报"
        >
          <span class="btn-label">{{ navPushing ? '推送中…' : '📤 推送播报' }}</span>
        </button>
        <button class="notify-nav-button" :class="{ configured: notifyConfigured }" @click="openNotifyModal" title="通知设置">
          <span class="btn-label">🔔</span>
        </button>
      </div>
    </header>

    <section v-if="currentView !== 'key-indicators' && !presentationMode" class="hero-strip">
      <div class="hero-status">
        <div class="status-card">
          <span class="status-label">当前视图</span>
          <strong>{{ activeViewLabel }}</strong>
        </div>
        <div class="status-card">
          <span class="status-label">数据准备度</span>
          <strong>{{ readinessText }}</strong>
        </div>
        <div class="status-card compact">
          <span class="status-label">在建工程</span>
          <strong>{{ zaigongLatestDate || '待上传' }}</strong>
        </div>
        <div class="status-card compact">
          <span class="status-label">预算立项</span>
          <strong>{{ budgetLatestDate || '待上传' }}</strong>
        </div>
      </div>
    </section>

    <main class="main-content">
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

    <div v-if="historyCenterVisible" class="global-history-overlay" @click.self="closeHistoryCenter">
      <aside class="global-history-panel">
        <div class="global-history-header">
          <div>
            <span class="brand-kicker">Unified History Center</span>
            <h3>全局历史记录</h3>
            <p>统一查看在建工程和预算立项的上传版本，并一键跳转到对应页面。</p>
          </div>
          <button class="close-btn" @click="closeHistoryCenter">×</button>
        </div>

        <div class="history-tabs">
          <button :class="{ active: historyTab === 'all' }" @click="historyTab = 'all'">全部</button>
          <button :class="{ active: historyTab === 'zaigong' }" @click="historyTab = 'zaigong'">在建工程</button>
          <button :class="{ active: historyTab === 'budget' }" @click="historyTab = 'budget'">预算立项</button>
        </div>

        <div v-if="historyCenterLoading" class="history-center-empty">
          <p>正在读取历史记录...</p>
        </div>
        <div v-else class="history-sections">
          <section v-for="section in historySections" :key="section.key" class="history-group">
            <div class="history-group-head">
              <h4>{{ section.title }}</h4>
              <button
                v-if="(section.key === 'zaigong' && zaigongSnapshotLabel) || (section.key === 'budget' && budgetSnapshotLabel)"
                class="restore-link"
                @click="switchView(section.key === 'zaigong' ? 'zaigong' : 'budget'); restoreCurrentModuleLatest()"
              >
                返回最新
              </button>
            </div>

            <div v-if="section.records.length === 0" class="history-center-empty compact">
              <p>暂无记录</p>
            </div>

            <div v-else class="history-card-list">
              <button
                v-for="record in section.records"
                :key="`${section.key}-${record.id}`"
                class="history-card"
                @click="section.key === 'zaigong' ? openZaigongSnapshot(record.id) : openBudgetSnapshot(record.id)"
              >
                <div class="history-card-top">
                  <strong>{{ record.source_filename }}</strong>
                  <span>#{{ record.id }}</span>
                </div>
                <div class="history-card-meta">
                  <span>上传时间：{{ formatHistoryTime(record.uploaded_at) }}</span>
                  <span v-if="section.key === 'zaigong' && record.file_date">文件日期：{{ formatFileDate(record.file_date) }}</span>
                  <span v-if="section.key === 'zaigong'">目标：{{ record.target_value ?? '—' }} 万元</span>
                </div>
                <div class="history-card-actions">
                  <button
                    class="compare-slot"
                    :class="{ active: isSelectedForCompare(section.key, 'left', record.id) }"
                    @click.stop="selectCompareRecord(section.key, 'left', record)"
                  >
                    设为 A
                  </button>
                  <button
                    class="compare-slot"
                    :class="{ active: isSelectedForCompare(section.key, 'right', record.id) }"
                    @click.stop="selectCompareRecord(section.key, 'right', record)"
                  >
                    设为 B
                  </button>
                </div>
              </button>
            </div>

            <div v-if="section.key === 'zaigong'" class="history-compare-panel">
              <div class="history-compare-head">
                <h5>历史对比</h5>
                <span>对比日期：{{ getRecordDateLabel('zaigong', zaigongCompareSelection.left) }} vs {{ getRecordDateLabel('zaigong', zaigongCompareSelection.right) }}</span>
              </div>
              <div v-if="zaigongCompareResult" class="compare-result-grid">
                <div class="compare-result-card">
                  <span>资本性支出进度</span>
                  <strong>{{ zaigongCompareResult.rightLabel }}</strong>
                  <em>{{ zaigongCompareResult.leftLabel }} -> {{ zaigongCompareResult.rightLabel }}</em>
                  <p>{{ zaigongCompareResult.capitalCurrent.toFixed(2) }} 万元，变化 {{ zaigongCompareResult.capitalDiff >= 0 ? '+' : '' }}{{ zaigongCompareResult.capitalDiff.toFixed(2) }} 万元</p>
                  <p>完成率变化 {{ zaigongCompareResult.progressDiff >= 0 ? '+' : '' }}{{ zaigongCompareResult.progressDiff.toFixed(1) }} pct</p>
                </div>
                <div class="compare-result-card">
                  <span>转固率</span>
                  <strong>{{ (zaigongCompareResult.rateCurrent * 100).toFixed(1) }}%</strong>
                  <em>{{ zaigongCompareResult.leftLabel }} -> {{ zaigongCompareResult.rightLabel }}</em>
                  <p>变化 {{ zaigongCompareResult.rateDiff >= 0 ? '+' : '' }}{{ zaigongCompareResult.rateDiff.toFixed(1) }} pct</p>
                </div>
              </div>
              <div v-if="zaigongCompareResult" class="compare-mini-table">
                <div class="compare-mini-head">管理员推进 Top 5</div>
                <table>
                  <thead>
                    <tr>
                      <th>工程管理员</th>
                      <th>{{ zaigongCompareResult.rightLabel }}</th>
                      <th>变化</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in zaigongCompareResult.top5" :key="item.name">
                      <td>{{ item.name }}</td>
                      <td>{{ item.current.toFixed(2) }}</td>
                      <td :class="item.diff >= 0 ? 'delta-up' : 'delta-down'">{{ item.diff >= 0 ? '+' : '' }}{{ item.diff.toFixed(2) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div v-if="section.key === 'budget'" class="history-compare-panel">
              <div class="history-compare-head">
                <h5>历史对比</h5>
                <span>对比日期：{{ getRecordDateLabel('budget', budgetCompareSelection.left) }} vs {{ getRecordDateLabel('budget', budgetCompareSelection.right) }}</span>
              </div>
              <div v-if="budgetCompareResult" class="compare-result-grid">
                <div class="compare-result-card">
                  <span>年度预算</span>
                  <strong>{{ budgetCompareResult.budgetCurrent.toFixed(2) }} 万元</strong>
                  <em>{{ budgetCompareResult.leftLabel }} -> {{ budgetCompareResult.rightLabel }}</em>
                  <p>变化 {{ budgetCompareResult.budgetDiff >= 0 ? '+' : '' }}{{ budgetCompareResult.budgetDiff.toFixed(2) }} 万元</p>
                </div>
                <div class="compare-result-card">
                  <span>立项进度</span>
                  <strong>{{ (budgetCompareResult.progressCurrent * 100).toFixed(1) }}%</strong>
                  <em>{{ budgetCompareResult.leftLabel }} -> {{ budgetCompareResult.rightLabel }}</em>
                  <p>变化 {{ budgetCompareResult.progressDiff >= 0 ? '+' : '' }}{{ budgetCompareResult.progressDiff.toFixed(1) }} pct</p>
                </div>
              </div>
              <div v-if="budgetCompareResult" class="compare-mini-table">
                <div class="compare-mini-head">专业推进 Top 5</div>
                <table>
                  <thead>
                    <tr>
                      <th>一级专业</th>
                      <th>{{ budgetCompareResult.rightLabel }}</th>
                      <th>变化</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in budgetCompareResult.top5" :key="item.name">
                      <td>{{ item.name }}</td>
                      <td>{{ (item.currentProgress * 100).toFixed(1) }}%</td>
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

  <!-- 通知设置弹窗 -->
  <div v-if="notifyModalVisible" class="notify-overlay" @click.self="notifyModalVisible = false">
    <div class="notify-modal">
      <div class="notify-modal-header">
        <h3>🔔 企业微信通知设置</h3>
        <button class="modal-close" @click="notifyModalVisible = false">×</button>
      </div>
      <div class="notify-modal-body">

        <!-- 当前状态 -->
        <div class="notify-status-row">
          <span class="notify-status-label">当前状态：</span>
          <span v-if="notifyConfigured" class="notify-badge configured">已配置</span>
          <span v-else class="notify-badge unconfigured">未配置</span>
          <span v-if="notifyConfigured" class="notify-masked">{{ notifyMaskedUrl }}</span>
          <button v-if="notifyConfigured" class="notify-clear-btn" @click="clearNotify">清除</button>
        </div>

        <!-- Webhook URL 输入 -->
        <div class="notify-field">
          <label>Webhook URL</label>
          <input
            v-model="notifyWebhookInput"
            type="text"
            placeholder="飞书：https://open.feishu.cn/open-apis/bot/v2/hook/...  或企业微信 Webhook"
            class="notify-input"
          />
          <p class="notify-hint">飞书：在与自己的对话或群聊 → 添加机器人 → 自定义机器人 → 复制 Webhook<br>企业微信：群聊 → 右上角设置 → 添加群机器人 → 复制 Webhook</p>
        </div>

        <!-- 自动推送开关 -->
        <div class="notify-field notify-toggle-row">
          <label>上传数据后自动推送</label>
          <label class="toggle-switch">
            <input type="checkbox" v-model="notifyAutoPush" />
            <span class="toggle-slider"></span>
          </label>
        </div>

        <!-- 操作反馈 -->
        <div v-if="notifyMsg" :class="['notify-msg', notifyMsgType]">{{ notifyMsg }}</div>

        <!-- 操作按钮 -->
        <div class="notify-actions">
          <button class="notify-btn-test" :disabled="notifyTesting" @click="testNotify">
            {{ notifyTesting ? '发送中…' : '发送测试消息' }}
          </button>
          <button class="notify-btn-save" :disabled="notifySaving" @click="saveNotify">
            {{ notifySaving ? '保存中…' : '保存配置' }}
          </button>
        </div>
      </div>
    </div>
  </div>

  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;600;700&family=Orbitron:wght@500;700;800&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --bg-primary: #07111f;
  --bg-secondary: #0d1a2d;
  --bg-panel: rgba(10, 20, 37, 0.82);
  --bg-panel-strong: rgba(8, 17, 32, 0.94);
  --surface-muted: rgba(133, 189, 255, 0.08);
  --accent-cyan: #67dfff;
  --accent-teal: #8cf0c9;
  --accent-amber: #ffb65c;
  --accent-coral: #ff7e70;
  --text-primary: #edf5ff;
  --text-secondary: #98adc4;
  --text-muted: #5f748d;
  --border-soft: rgba(138, 178, 221, 0.16);
  --border-strong: rgba(103, 223, 255, 0.28);
  --shadow-panel: 0 30px 80px rgba(0, 0, 0, 0.28);
}

html,
body,
#app {
  min-height: 100%;
}

body {
  font-family: 'IBM Plex Sans', 'Noto Sans SC', sans-serif;
  -webkit-font-smoothing: antialiased;
  background:
    radial-gradient(circle at top left, rgba(103, 223, 255, 0.1), transparent 30%),
    radial-gradient(circle at 85% 10%, rgba(140, 240, 201, 0.08), transparent 22%),
    linear-gradient(180deg, #06101c 0%, #091525 40%, #07111f 100%);
  color: var(--text-primary);
}

body:has(.app-shell.analyst-mode) {
  background: #f6f5f2;
  color: #1c1b18;
}

.app-shell {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  padding: 24px;
}

.app-shell.presentation-mode {
  padding: 18px;
}

.backdrop {
  position: absolute;
  pointer-events: none;
}

.backdrop-grid {
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.025) 1px, transparent 1px);
  background-size: 64px 64px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.6), transparent 90%);
}

.backdrop-glow {
  width: 38rem;
  height: 38rem;
  border-radius: 50%;
  filter: blur(70px);
  opacity: 0.25;
}

.glow-a {
  top: -8rem;
  left: -8rem;
  background: rgba(103, 223, 255, 0.28);
}

.glow-b {
  right: -10rem;
  top: 8rem;
  background: rgba(140, 240, 201, 0.18);
}

.top-nav,
.hero-strip,
.main-content {
  position: relative;
  z-index: 1;
  max-width: 1520px;
  margin: 0 auto;
}

.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 18px 24px;
  background: linear-gradient(180deg, rgba(9, 18, 33, 0.88), rgba(9, 18, 33, 0.72));
  border: 1px solid var(--border-soft);
  border-radius: 28px;
  backdrop-filter: blur(24px);
  box-shadow: var(--shadow-panel);
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.brand-mark {
  width: 52px;
  height: 52px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(103, 223, 255, 0.22), rgba(140, 240, 201, 0.1));
  border: 1px solid rgba(103, 223, 255, 0.28);
  color: var(--accent-cyan);
  font-family: 'Orbitron', sans-serif;
  font-size: 16px;
  font-weight: 800;
  letter-spacing: 0.16em;
}

.brand-copy {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.brand-text {
  font-size: 28px;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: 0.02em;
}

.nav-links {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.nav-links button {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-height: 44px;
  padding: 0 18px;
  border-radius: 999px;
  border: 1px solid transparent;
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-secondary);
  cursor: pointer;
  transition: 0.25s ease;
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
}

.nav-links button:hover:not(.disabled) {
  color: var(--text-primary);
  border-color: rgba(103, 223, 255, 0.2);
  background: rgba(103, 223, 255, 0.07);
}

.nav-links button.active {
  color: #04111d;
  border-color: rgba(103, 223, 255, 0.5);
  background: linear-gradient(135deg, var(--accent-cyan), rgba(140, 240, 201, 0.92));
  box-shadow: 0 10px 30px rgba(103, 223, 255, 0.2);
}

.nav-links button.disabled {
  opacity: 0.42;
  cursor: not-allowed;
}

.history-nav-button {
  border-color: rgba(255, 182, 92, 0.18) !important;
  background: rgba(255, 182, 92, 0.08) !important;
  color: #ffd7a0 !important;
}

.history-nav-button:hover {
  border-color: rgba(255, 182, 92, 0.32) !important;
  background: rgba(255, 182, 92, 0.14) !important;
}

.push-nav-button {
  border-color: rgba(74, 222, 128, 0.22) !important;
  background: rgba(74, 222, 128, 0.08) !important;
  color: #86efac !important;
}
.push-nav-button:hover:not(:disabled) {
  border-color: rgba(74, 222, 128, 0.4) !important;
  background: rgba(74, 222, 128, 0.15) !important;
}
.push-nav-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.notify-nav-button {
  border-color: rgba(120, 200, 120, 0.18) !important;
  background: rgba(120, 200, 120, 0.08) !important;
  color: #a8d8a8 !important;
  font-size: 15px !important;
  padding: 4px 10px !important;
}
.notify-nav-button:hover {
  border-color: rgba(120, 200, 120, 0.32) !important;
  background: rgba(120, 200, 120, 0.16) !important;
}
.notify-nav-button.configured {
  border-color: rgba(74, 222, 128, 0.35) !important;
  background: rgba(74, 222, 128, 0.12) !important;
  color: #4ade80 !important;
}

/* ── 通知设置弹窗 ── */
.notify-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.45);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.notify-modal {
  background: #fff;
  border-radius: 12px;
  width: 480px;
  max-width: 95vw;
  box-shadow: 0 8px 40px rgba(0,0,0,0.18);
  overflow: hidden;
}
.notify-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 12px;
  border-bottom: 1px solid #e4e3dc;
}
.notify-modal-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #1c1b18;
}
.notify-modal-header .modal-close {
  background: none;
  border: none;
  font-size: 20px;
  color: #888;
  cursor: pointer;
  line-height: 1;
  padding: 0 4px;
}
.notify-modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.notify-status-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #555;
}
.notify-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
}
.notify-badge.configured {
  background: #dcfce7;
  color: #15803d;
}
.notify-badge.unconfigured {
  background: #f3f4f6;
  color: #9ca3af;
}
.notify-masked {
  font-size: 12px;
  color: #9ca3af;
  font-family: monospace;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.notify-clear-btn {
  font-size: 12px;
  padding: 2px 10px;
  border: 1px solid #fca5a5;
  border-radius: 4px;
  background: #fff;
  color: #dc2626;
  cursor: pointer;
  flex-shrink: 0;
}
.notify-clear-btn:hover { background: #fef2f2; }
.notify-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.notify-field label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}
.notify-input {
  width: 100%;
  padding: 8px 10px;
  font-size: 13px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  outline: none;
  box-sizing: border-box;
  color: #1c1b18;
}
.notify-input:focus { border-color: #2563eb; }
.notify-hint {
  margin: 0;
  font-size: 11px;
  color: #9ca3af;
  line-height: 1.4;
}
.notify-toggle-row {
  flex-direction: row !important;
  align-items: center;
  justify-content: space-between;
}
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 22px;
  cursor: pointer;
}
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.toggle-slider {
  position: absolute;
  inset: 0;
  background: #d1d5db;
  border-radius: 22px;
  transition: background 0.2s;
}
.toggle-slider::before {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  left: 3px;
  top: 3px;
  background: #fff;
  border-radius: 50%;
  transition: transform 0.2s;
}
.toggle-switch input:checked + .toggle-slider { background: #2563eb; }
.toggle-switch input:checked + .toggle-slider::before { transform: translateX(18px); }
.notify-msg {
  font-size: 13px;
  padding: 8px 12px;
  border-radius: 6px;
}
.notify-msg.success { background: #dcfce7; color: #15803d; }
.notify-msg.error { background: #fef2f2; color: #dc2626; }
.notify-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}
.notify-btn-test {
  padding: 7px 16px;
  font-size: 13px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  color: #374151;
  cursor: pointer;
  font-weight: 500;
}
.notify-btn-test:hover:not(:disabled) { background: #f9fafb; }
.notify-btn-save {
  padding: 7px 20px;
  font-size: 13px;
  border: none;
  border-radius: 6px;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
  font-weight: 600;
}
.notify-btn-save:hover:not(:disabled) { background: #1d4ed8; }
.notify-btn-test:disabled,
.notify-btn-save:disabled { opacity: 0.5; cursor: not-allowed; }

.data-indicator {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--accent-cyan);
  box-shadow: 0 0 0 5px rgba(103, 223, 255, 0.14);
}

.data-indicator.warning {
  background: var(--accent-amber);
  box-shadow: 0 0 0 5px rgba(255, 182, 92, 0.14);
}

.data-indicator.success {
  background: var(--accent-teal);
  box-shadow: 0 0 0 5px rgba(140, 240, 201, 0.14);
}

.hero-strip {
  margin-top: 18px;
  margin-bottom: 24px;
}

.hero-status {
  background: linear-gradient(180deg, rgba(9, 18, 33, 0.78), rgba(9, 18, 33, 0.58));
  border: 1px solid var(--border-soft);
  border-radius: 26px;
  backdrop-filter: blur(22px);
  box-shadow: var(--shadow-panel);
}

.hero-status {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  padding: 18px;
}

.status-card {
  min-height: 108px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 18px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.status-label {
  display: block;
  margin-bottom: 10px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.12em;
  color: var(--text-muted);
  text-transform: uppercase;
}

.status-card strong {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.status-card.compact strong {
  font-size: 15px;
  color: var(--text-secondary);
}

.main-content {
  padding-bottom: 28px;
}

.app-shell.presentation-mode .main-content {
  max-width: 100%;
  padding-bottom: 0;
}

.global-history-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: flex;
  justify-content: flex-end;
  background: rgba(4, 10, 20, 0.64);
  backdrop-filter: blur(8px);
}

.global-history-panel {
  width: min(620px, 100%);
  height: 100%;
  padding: 28px 24px;
  background: linear-gradient(180deg, rgba(7, 15, 28, 0.97), rgba(9, 18, 33, 0.99));
  border-left: 1px solid var(--border-soft);
  box-shadow: -24px 0 70px rgba(0, 0, 0, 0.35);
  overflow-y: auto;
}

.global-history-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 20px;
}

.global-history-header h3 {
  margin: 8px 0 10px;
  font-size: 26px;
}

.global-history-header p {
  color: var(--text-secondary);
  line-height: 1.7;
  font-size: 14px;
}

.close-btn {
  width: 38px;
  height: 38px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 22px;
  line-height: 1;
}

.history-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.history-tabs button {
  height: 38px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
  cursor: pointer;
  font: inherit;
}

.history-tabs button.active {
  color: #04111d;
  background: linear-gradient(135deg, var(--accent-cyan), rgba(140, 240, 201, 0.92));
  border-color: rgba(103, 223, 255, 0.4);
}

.history-sections {
  display: grid;
  gap: 22px;
}

.history-group {
  padding: 18px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.history-group-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.history-group-head h4 {
  font-size: 16px;
}

.restore-link {
  border: none;
  background: transparent;
  color: var(--accent-cyan);
  cursor: pointer;
  font: inherit;
}

.history-card-list {
  display: grid;
  gap: 12px;
}

.history-card {
  width: 100%;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(103, 223, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
  transition: 0.22s ease;
}

.history-card:hover {
  transform: translateY(-2px);
  border-color: rgba(103, 223, 255, 0.22);
  background: rgba(103, 223, 255, 0.07);
}

.history-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.history-card-top strong {
  flex: 1;
  font-size: 14px;
  line-height: 1.6;
}

.history-card-top span {
  color: var(--text-muted);
  font-size: 12px;
}

.history-card-meta {
  display: grid;
  gap: 6px;
  color: var(--text-secondary);
  font-size: 12px;
}

.history-card-actions {
  display: flex;
  gap: 10px;
  margin-top: 14px;
}

.compare-slot {
  height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
  cursor: pointer;
  font: inherit;
}

.compare-slot.active {
  color: #04111d;
  border-color: rgba(103, 223, 255, 0.4);
  background: linear-gradient(135deg, var(--accent-cyan), rgba(140, 240, 201, 0.92));
}

.history-compare-panel {
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.history-compare-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.history-compare-head h5 {
  font-size: 15px;
}

.history-compare-head span {
  color: var(--text-secondary);
  font-size: 12px;
}

.compare-result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
  margin-bottom: 14px;
}

.compare-result-card {
  display: grid;
  gap: 8px;
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.compare-result-card span,
.compare-mini-head {
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.compare-result-card strong {
  font-size: 22px;
}

.compare-result-card em {
  color: var(--text-secondary);
  font-size: 12px;
  font-style: normal;
}

.compare-result-card p {
  color: var(--text-secondary);
  font-size: 13px;
}

.compare-mini-table {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.compare-mini-head {
  margin-bottom: 12px;
}

.compare-mini-table table {
  width: 100%;
  border-collapse: collapse;
}

.compare-mini-table th,
.compare-mini-table td {
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  text-align: left;
  font-size: 13px;
}

.compare-mini-table th {
  color: var(--text-muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.history-center-empty {
  min-height: 220px;
  display: grid;
  place-items: center;
  text-align: center;
  color: var(--text-secondary);
}

.history-center-empty.compact {
  min-height: 100px;
}

@media (max-width: 1100px) {
  .hero-status {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .status-card {
    min-height: 96px;
  }
}

@media (max-width: 900px) {
  .app-shell {
    padding: 16px;
  }

  .top-nav {
    flex-direction: column;
    align-items: stretch;
  }

  .nav-links {
    justify-content: flex-start;
  }

  .global-history-panel {
    width: 100%;
  }

  .history-compare-head {
    align-items: flex-start;
    flex-direction: column;
  }
}

@media (max-width: 640px) {
  .hero-status {
    border-radius: 24px;
  }

  .hero-status {
    grid-template-columns: 1fr;
  }

  .brand-text {
    font-size: 22px;
  }

  .nav-links button {
    flex: 1 1 calc(50% - 10px);
    justify-content: center;
  }
}

/* ===== Analyst Mode (match zaigong_analysis_page style) ===== */
.app-shell.analyst-mode {
  padding: 0;
  background: #f6f5f2;
  font-family: 'IBM Plex Sans', 'Noto Sans SC', sans-serif;
  box-shadow: 0 0 0 100vmax #f6f5f2;
  clip-path: inset(0 -100vmax);
}

.app-shell.analyst-mode .backdrop {
  display: none;
}

.app-shell.analyst-mode .top-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  height: 62px;
  margin: 0;
  border-radius: 0;
  border: none;
  border-bottom: 1px solid #e4e3dc;
  background: #ffffff;
  box-shadow: none;
  backdrop-filter: none;
  padding: 0 24px;
  gap: 0;
}

.app-shell.analyst-mode .nav-brand {
  gap: 10px;
  margin-right: 28px;
}

.app-shell.analyst-mode .brand-mark {
  width: 28px;
  height: 28px;
  border-radius: 7px;
  background: #1c1b18;
  border: none;
  color: #fff;
  font-size: 10px;
  letter-spacing: 0.2px;
}

.app-shell.analyst-mode .brand-copy {
  gap: 0;
}

.app-shell.analyst-mode .brand-text {
  font-size: 19px;
  font-weight: 700;
  letter-spacing: 0;
  color: #1c1b18;
  line-height: 1;
}

.app-shell.analyst-mode .nav-links {
  gap: 2px;
}

.app-shell.analyst-mode .nav-main-links {
  margin-left: 12px;
  justify-content: flex-start;
}

.app-shell.analyst-mode .nav-end-links {
  margin-left: auto;
  justify-content: flex-end;
}

.app-shell.analyst-mode .nav-links button {
  min-height: 30px;
  height: 30px;
  border-radius: 5px;
  border: none;
  background: transparent;
  color: #6b6a63;
  padding: 0 12px;
  font-size: 13px;
  font-weight: 400;
}

.app-shell.analyst-mode .nav-links button:hover:not(.disabled) {
  background: #f0efe9;
  color: #1c1b18;
}

.app-shell.analyst-mode .nav-links button.active {
  background: #1c1b18;
  color: #fff;
  box-shadow: none;
}

.app-shell.analyst-mode .history-nav-button {
  border: 1px solid #d0cfc6 !important;
  background: #fff !important;
  color: #6b6a63 !important;
}

.app-shell.analyst-mode .data-indicator {
  width: 5px;
  height: 5px;
  box-shadow: none;
  background: #34c77b;
}

.app-shell.analyst-mode .data-indicator.warning {
  background: #f59e0b;
  box-shadow: none;
}

.app-shell.analyst-mode .data-indicator.success {
  background: #34c77b;
  box-shadow: none;
}

.app-shell.analyst-mode .main-content {
  max-width: 1200px;
  padding: 16px 24px 28px;
}

.app-shell.analyst-mode .hero-strip {
  display: none;
}

.app-shell.analyst-mode .global-history-overlay {
  background: rgba(28, 27, 24, 0.25);
}

.app-shell.analyst-mode .global-history-panel {
  background: #ffffff;
  border-left: 1px solid #e4e3dc;
  box-shadow: -12px 0 30px rgba(28, 27, 24, 0.15);
}

.app-shell.analyst-mode .global-history-header h3,
.app-shell.analyst-mode .history-group-head h4,
.app-shell.analyst-mode .history-compare-head h5 {
  color: #1c1b18;
}

.app-shell.analyst-mode .global-history-header p,
.app-shell.analyst-mode .history-card-meta,
.app-shell.analyst-mode .history-compare-head span {
  color: #6b6a63;
}

.app-shell.analyst-mode .brand-kicker,
.app-shell.analyst-mode .history-center-empty p,
.app-shell.analyst-mode .history-card-top span,
.app-shell.analyst-mode .restore-link,
.app-shell.analyst-mode .compare-result-card em,
.app-shell.analyst-mode .compare-mini-table th {
  color: #6b6a63;
}

.app-shell.analyst-mode .global-history-header .brand-kicker,
.app-shell.analyst-mode .history-group-head h4,
.app-shell.analyst-mode .history-card-top strong,
.app-shell.analyst-mode .compare-mini-head {
  color: #1c1b18;
}

.app-shell.analyst-mode .close-btn,
.app-shell.analyst-mode .history-tabs button,
.app-shell.analyst-mode .compare-slot {
  background: #fff;
  border: 1px solid #d0cfc6;
  color: #6b6a63;
}

.app-shell.analyst-mode .history-tabs button.active,
.app-shell.analyst-mode .compare-slot.active {
  background: #1c1b18;
  border-color: #1c1b18;
  color: #fff;
}

.app-shell.analyst-mode .history-group,
.app-shell.analyst-mode .history-card,
.app-shell.analyst-mode .compare-result-card,
.app-shell.analyst-mode .compare-mini-table {
  background: #fff;
  border: 1px solid #e4e3dc;
}

.app-shell.analyst-mode .compare-result-card span,
.app-shell.analyst-mode .compare-mini-head,
.app-shell.analyst-mode .compare-mini-table th {
  color: #a8a79f;
}

.app-shell.analyst-mode .compare-result-card strong,
.app-shell.analyst-mode .compare-result-card p,
.app-shell.analyst-mode .compare-mini-table td {
  color: #1c1b18;
}
</style>
