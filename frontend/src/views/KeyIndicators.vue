<template>
  <div class="ki-page" :class="{ 'ki-fullscreen': presentationMode }">

    <!-- Fullscreen nav (presentation mode only) -->
    <nav v-if="presentationMode" class="ki-pres-nav">
      <div style="display:flex;align-items:center;gap:10px">
        <div class="ki-nav-mark">ZT</div>
        <span style="font-size:16px;font-weight:500;color:var(--ink)">工程数据分析</span>
      </div>
      <div style="font-size:12px;color:var(--ink-3);font-family:var(--font-mono)">
        实时数据 · {{ currentDate }}
      </div>
      <button class="ki-exit-btn" @click="togglePresentationMode">退出展示模式</button>
    </nav>

    <!-- ── Page Header ── -->
    <header class="page-head">
      <div class="page-head-l">
        <span class="eyebrow">关键指标 / Quarterly Briefing</span>
        <h1 class="page-title-h1">关键指标摘要</h1>
        <div class="page-meta">
          <span>数据截止 · 当前周期</span>
          <span class="ph-sep"></span>
          <span>年度目标 {{ displayTargetValue }} 万</span>
          <template v-if="normalizedZaigongDate">
            <span class="ph-sep"></span>
            <span>{{ normalizedZaigongDate }}</span>
          </template>
        </div>
      </div>
      <div class="page-actions">
        <button class="ki-btn ghost" @click="togglePresentationMode">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="none"><path d="M2 5V2h3M11 2h3v3M2 11v3h3M14 11v3h-3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
          {{ presentationMode ? '退出展示' : '投屏' }}
        </button>
        <button class="ki-btn primary" @click="exportPNG" :disabled="exportLoading">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="none"><path d="M3 12v1.5h10V12M5 8l3 3 3-3M8 3v8" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
          {{ exportLoading ? '生成中…' : '导出 PNG' }}
        </button>
      </div>
    </header>

    <!-- ── Summary banner ── -->
    <div class="ki-summary-banner" v-if="props.zaigongData?.metrics">
      <p class="ki-summary-text">
        当期资本性支出 <strong class="mono">{{ props.zaigongData?.metrics?.capital?.toFixed(2) || '—' }} 万元</strong>（当期目标 {{ displayTargetValue }} 万，进度 <strong style="color:var(--accent)">{{ capitalProgress }}%</strong>），缺口 <strong class="mono" style="color:var(--warn)">{{ props.zaigongData?.metrics?.deficit?.toFixed(2) || '—' }} 万</strong>。全年支出进度 <strong style="color:var(--accent)">{{ annualCapitalProgress }}%</strong>，立项进度 {{ approvalProgress }}%。整体转固率仅 <strong class="mono" :style="{ color: parseFloat(transferRate) < 60 ? 'var(--bad)' : 'var(--ok)' }">{{ transferRate }}%</strong>{{ parseFloat(transferRate) < 60 ? '，低于60%期望值，需在下一周期集中推进转固。' : '，已达标。' }}
      </p>
      <div class="ki-summary-foot">
        <span>AUTO-DRAFTED · 基于上传数据</span>
        <button class="ki-btn ghost" style="height:24px;font-size:11px" @click="copyNarrative">复制文本</button>
      </div>
    </div>

    <!-- ── Two-Column Magazine Layout ── -->
    <div class="ki-two-col">

      <!-- Left: 2×2 KPI Donut Grid (60%) -->
      <div class="ki-left-col">
        <div class="ki-kpi-grid">

          <!-- Card 1: 资本性支出进度 -->
          <div class="ki-kpi-card">
            <div class="ki-kpi-donut">
              <svg width="110" height="110" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="48" fill="none" stroke="var(--paper-2)" stroke-width="9"/>
                <circle cx="60" cy="60" r="48" fill="none"
                  :stroke="gaugeColor(animatedGauges[0], 100)"
                  stroke-width="9" stroke-linecap="round" stroke-dasharray="301.59"
                  :stroke-dashoffset="301.59 * (1 - Math.min(animatedGauges[0], 100) / 100)"
                  transform="rotate(-90 60 60)"
                />
              </svg>
              <div class="ki-kpi-center">
                <div class="ki-kpi-val">{{ animatedGauges[0].toFixed(1) }}<span class="ki-kpi-unit">%</span></div>
                <div class="ki-kpi-target">目标 100%</div>
              </div>
            </div>
            <div class="ki-kpi-label">资本性支出进度</div>
            <div class="ki-kpi-sub mono">{{ props.zaigongData?.metrics?.capital?.toFixed(1) || '0.0' }} / {{ displayTargetValue }} 万</div>
            <div class="ki-kpi-delta" :class="parseFloat(capitalProgress) >= 80 ? 'ok' : 'up'">
              <span class="tri-up"></span>缺口 {{ props.zaigongData?.metrics?.deficit?.toFixed(1) || '0.0' }} 万
            </div>
          </div>

          <!-- Card 2: 转固率 -->
          <div class="ki-kpi-card">
            <div class="ki-kpi-donut">
              <svg width="110" height="110" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="48" fill="none" stroke="var(--paper-2)" stroke-width="9"/>
                <circle cx="60" cy="60" r="48" fill="none"
                  :stroke="gaugeColor(animatedGauges[1], 60)"
                  stroke-width="9" stroke-linecap="round" stroke-dasharray="301.59"
                  :stroke-dashoffset="301.59 * (1 - Math.min(animatedGauges[1], 100) / 100)"
                  transform="rotate(-90 60 60)"
                />
              </svg>
              <div class="ki-kpi-center">
                <div class="ki-kpi-val" :class="parseFloat(transferRate) < 60 ? 'is-low' : ''">{{ animatedGauges[1].toFixed(1) }}<span class="ki-kpi-unit">%</span></div>
                <div class="ki-kpi-target">目标 60%</div>
              </div>
            </div>
            <div class="ki-kpi-label">转固率</div>
            <div class="ki-kpi-sub mono">期末余额 vs 年初数</div>
            <div class="ki-kpi-delta" :class="parseFloat(transferRate) < 10 ? 'down' : 'flat'">
              <span v-if="parseFloat(transferRate) < 10" class="tri-dn"></span>
              {{ parseFloat(transferRate) < 10 ? '低位' : '—' }}
            </div>
          </div>

          <!-- Card 3: 预算执行率 -->
          <div class="ki-kpi-card">
            <div class="ki-kpi-donut">
              <svg width="110" height="110" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="48" fill="none" stroke="var(--paper-2)" stroke-width="9"/>
                <circle cx="60" cy="60" r="48" fill="none"
                  :stroke="gaugeColor(animatedGauges[2], 100)"
                  stroke-width="9" stroke-linecap="round" stroke-dasharray="301.59"
                  :stroke-dashoffset="301.59 * (1 - Math.min(animatedGauges[2], 100) / 100)"
                  transform="rotate(-90 60 60)"
                />
              </svg>
              <div class="ki-kpi-center">
                <div class="ki-kpi-val" :class="parseFloat(annualCapitalProgress) > 100 ? 'is-low' : ''">{{ animatedGauges[2].toFixed(1) }}<span class="ki-kpi-unit">%</span></div>
                <div class="ki-kpi-target">目标 100%</div>
              </div>
            </div>
            <div class="ki-kpi-label">支出进度</div>
            <div class="ki-kpi-sub mono">{{ props.budgetData?.annual_spend_total?.toFixed(1) || '0.0' }} / {{ props.budgetData?.budget_total?.toFixed(1) || '0.0' }} 万</div>
            <div class="ki-kpi-delta" :class="parseFloat(annualCapitalProgress) > 100 ? 'down' : 'up'">
              <span v-if="parseFloat(annualCapitalProgress) > 100" class="tri-dn"></span>
              <span v-else class="tri-up"></span>
              {{ parseFloat(annualCapitalProgress) > 100 ? '超支' : `${(100 - parseFloat(annualCapitalProgress)).toFixed(1)}pp 待执行` }}
            </div>
          </div>

          <!-- Card 4: 立项进度 -->
          <div class="ki-kpi-card">
            <div class="ki-kpi-donut">
              <svg width="110" height="110" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="48" fill="none" stroke="var(--paper-2)" stroke-width="9"/>
                <circle cx="60" cy="60" r="48" fill="none"
                  :stroke="gaugeColor(animatedGauges[3], 90)"
                  stroke-width="9" stroke-linecap="round" stroke-dasharray="301.59"
                  :stroke-dashoffset="301.59 * (1 - Math.min(animatedGauges[3], 100) / 100)"
                  transform="rotate(-90 60 60)"
                />
              </svg>
              <div class="ki-kpi-center">
                <div class="ki-kpi-val">{{ animatedGauges[3].toFixed(1) }}<span class="ki-kpi-unit">%</span></div>
                <div class="ki-kpi-target">目标 90%</div>
              </div>
            </div>
            <div class="ki-kpi-label">立项进度</div>
            <div class="ki-kpi-sub mono">{{ props.budgetData?.occupied_total?.toFixed(1) || '0.0' }} / {{ props.budgetData?.budget_total?.toFixed(1) || '0.0' }} 万</div>
            <div class="ki-kpi-delta" :class="parseFloat(approvalProgress) < 90 ? 'up' : 'flat'">
              {{ parseFloat(approvalProgress) < 90 ? `${(90 - parseFloat(approvalProgress)).toFixed(1)}pp 未绑定` : '已达标' }}
            </div>
          </div>

        </div>
      </div>

      <!-- Right: Unified panel (aligns with left KPI grid) -->
      <div class="ki-right-panel">

        <!-- 四类工程预警 -->
        <div class="ki-right-section">
          <div class="ki-right-section-head">
            <div><h3>四类工程预警</h3><div class="sub">预警期 60 天</div></div>
            <button class="ki-btn ghost" v-if="fcWarnings?.items?.length" @click="showFourClassAllDetail">
              <svg width="12" height="12" viewBox="0 0 16 16" fill="none"><path d="M2 4h12M4 8h8M6 12h4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
              全部
            </button>
          </div>
          <div class="ki-right-section-body" v-if="fcWarnings?.summary">
            <div
              v-for="type in fourClassTypes"
              :key="type.name"
              class="warning-item"
              @click="showFourClassDetail(type.name)"
            >
              <div style="min-width:0">
                <span class="pill" :class="getWarningPillClass(type.key)"><span class="dot"></span>{{ type.name }}</span>
              </div>
              <div class="warning-count">
                {{ (fcWarnings.summary?.[type.name]?.triggered || 0) + (fcWarnings.summary?.[type.name]?.warning || 0) }}
              </div>
              <div class="warning-mgr-text">{{ getManagerTextForType(type.name) }}</div>
            </div>
          </div>
          <div v-else class="ki-right-empty">暂无预警数据</div>
        </div>

        <!-- 管理员视图 -->
        <div class="ki-right-section ki-manager-section" v-if="managerViewRows.length">
          <div class="mgr-header">
            <span class="mgr-rank-hd">#</span>
            <span class="mgr-name-hd">管理员</span>
            <span class="mgr-count-hd">在管</span>
            <span class="mgr-capital-hd">本年支出</span>
            <span class="mgr-rate-hd">转固率</span>
          </div>
          <div
            v-for="(row, idx) in managerViewRows"
            :key="row.manager"
            class="mgr-row"
          >
              <span class="mgr-rank" :class="{ 'top': idx < 3 }">{{ idx + 1 }}</span>
              <span class="mgr-name">{{ row.manager }}</span>
              <span class="mgr-count mono muted">{{ row.count }}项</span>
              <span class="mgr-capital mono" :class="{ 'neg': row.capital < 0 }">{{ formatNum(row.capital) }}</span>
              <div class="mgr-rate">
                <span class="mgr-rate-pct">{{ row.rate.toFixed(1) }}%</span>
                <div class="mgr-rate-track"><div class="mgr-rate-fill" :class="getRateBarClass(row.rate / 100)" :style="{ width: Math.min(row.rate, 100) + '%' }"></div></div>
              </div>
            </div>
        </div>

      </div>

    </div>

    <!-- ── 四类工程预警明细弹窗 ── -->
    <div v-if="fourClassDetailVisible" class="four-class-modal-overlay" @click.self="fourClassDetailVisible = false">
      <div class="four-class-modal">
        <div class="modal-header">
          <div class="modal-title-wrap">
            <h3>{{ fourClassDetailType }}</h3>
            <span v-if="fcWarnings?.summary?.analysis_date" class="modal-date">数据日期：{{ fcWarnings.summary.analysis_date }}</span>
          </div>
          <div class="modal-header-actions">
            <button class="export-btn-primary" @click="exportFourClassWarnings" :disabled="!props.recordId">
              <span>↓</span> 导出预警清单
            </button>
            <button class="modal-close" @click="fourClassDetailVisible = false">✕</button>
          </div>
        </div>
        <div class="modal-body">
          <!-- Grouped view -->
          <template v-if="fourClassDetailType === '四类工程预警明细'">
            <template v-for="type in fourClassTypes" :key="type.name">
              <div v-if="getGroupItems(type.name).length > 0" class="four-class-group" :class="'group-' + type.key">
                <div class="group-header">
                  <span class="group-title">{{ type.name }}</span>
                  <span class="group-count">已触发 {{ getGroupStats(type.name).triggered }} / 预警 {{ getGroupStats(type.name).warning }}</span>
                </div>
                <table class="data-table four-class-modal-table">
                  <thead><tr><th class="col-status">状态</th><th class="col-name">工程名称</th><th class="col-accept">验收类型</th><th class="col-manager">管理员</th><th class="col-date">关键日期</th><th class="col-date">截止日期</th><th class="col-project-status">工程状态</th><th class="col-days">天数</th><th class="col-suggestion">处置建议</th></tr></thead>
                  <tbody>
                    <tr v-for="item in getGroupItems(type.name)" :key="item.id" :class="'row-' + item.status">
                      <td class="col-status"><span class="status-tag" :class="item.status">{{ item.status }}</span></td>
                      <td class="col-name" :title="item.name">{{ item.name }}</td>
                      <td class="col-accept">{{ item.acceptType }}</td>
                      <td class="col-manager">{{ item.manager }}</td>
                      <td class="col-date">{{ item.keyDate }}</td>
                      <td class="col-date">{{ item.deadline || '-' }}</td>
                      <td class="col-project-status">{{ item.projectStatus || '—' }}</td>
                      <td class="col-days" :class="getDaysClass(item.daysLabel, item.status)"><span v-if="item.status === '预警' && parseInt(item.daysLabel?.match(/\d+/)?.[0]) <= 30" style="margin-right:2px">⚠️</span>{{ item.daysLabel }}</td>
                      <td class="col-suggestion">{{ item.suggestion }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </template>
          </template>
          <!-- Single-type view -->
          <template v-else>
            <table class="data-table four-class-modal-table">
              <thead><tr><th class="col-status">状态</th><th class="col-name">工程名称</th><th class="col-accept">验收类型</th><th class="col-manager">管理员</th><th class="col-date">关键日期</th><th class="col-date">截止日期</th><th class="col-project-status">工程状态</th><th class="col-days">天数</th><th class="col-suggestion">处置建议</th></tr></thead>
              <tbody>
                <tr v-for="item in fourClassDetailItems" :key="item.id" :class="'row-' + item.status">
                  <td class="col-status"><span class="status-tag" :class="item.status">{{ item.status }}</span></td>
                  <td class="col-name" :title="item.name">{{ item.name }}</td>
                  <td class="col-accept">{{ item.acceptType }}</td>
                  <td class="col-manager">{{ item.manager }}</td>
                  <td class="col-date">{{ item.keyDate }}</td>
                  <td class="col-date">{{ item.deadline || '-' }}</td>
                  <td class="col-project-status">{{ item.projectStatus || '—' }}</td>
                  <td class="col-days" :class="getDaysClass(item.daysLabel, item.status)"><span v-if="item.status === '预警' && parseInt(item.daysLabel?.match(/\d+/)?.[0]) <= 30" style="margin-right:2px">⚠️</span>{{ item.daysLabel }}</td>
                  <td class="col-suggestion">{{ item.suggestion }}</td>
                </tr>
              </tbody>
            </table>
          </template>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import html2canvas from 'html2canvas'

const props = defineProps({
  zaigongData: Object,
  budgetData: Object,
  zaigongDate: String,
  budgetDate: String,
  fourClassWarnings: Object,
  recordId: { type: [Number, String], default: null },
})

const emit = defineEmits(['presentation-change'])

const currentDate = computed(() => {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
})

const targetValue = computed(() => {
  const value = Number(props.zaigongData?.metrics?.yearTarget)
  return Number.isFinite(value) && value > 0 ? value : null
})

const displayTargetValue = computed(() => {
  return targetValue.value === null ? '—' : targetValue.value.toFixed(2)
})

const normalizedZaigongDate = computed(() => formatDisplayDate(props.zaigongDate))

function formatDisplayDate(value) {
  if (!value) return ''
  const raw = String(value).trim()
  const matched = raw.match(/(\d{4})[-/](\d{1,2})[-/](\d{1,2})/)
  if (matched) {
    const [, year, month, day] = matched
    return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`
  }
  const date = new Date(raw)
  if (Number.isNaN(date.getTime())) return raw
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const capitalProgress = computed(() => {
  if (!props.zaigongData?.metrics?.capital || !targetValue.value || targetValue.value <= 0) return '0.0'
  return ((props.zaigongData.metrics.capital / targetValue.value) * 100).toFixed(1)
})

const annualCapitalProgress = computed(() => {
  const annualSpend = Number(props.budgetData?.annual_spend_total || 0)
  const budgetTotal = Number(props.budgetData?.budget_total || 0)
  if (!annualSpend || !budgetTotal || budgetTotal <= 0) return '0.0'
  return ((annualSpend / budgetTotal) * 100).toFixed(1)
})

const approvalProgress = computed(() => {
  if (!props.budgetData?.approval_progress) return '0.0'
  return (props.budgetData.approval_progress * 100).toFixed(1)
})

const transferRate = computed(() => {
  if (!props.zaigongData?.metrics?.rate) return '0.0'
  return (props.zaigongData.metrics.rate * 100).toFixed(1)
})

function gaugeColor(value, target) {
  if (value >= target * 0.95) return 'var(--ok)'
  if (value >= target * 0.80) return 'var(--accent)'
  if (value >= target * 0.50) return 'var(--warn)'
  return 'var(--bad)'
}

// Gauge count-up animation
const animatedGauges = ref([0, 0, 0, 0])

function runGaugeCountUp() {
  const targets = [
    parseFloat(capitalProgress.value) || 0,
    parseFloat(transferRate.value) || 0,
    parseFloat(annualCapitalProgress.value) || 0,
    parseFloat(approvalProgress.value) || 0,
  ]
  const duration = 900
  const startTs = performance.now()
  function tick(ts) {
    const t = Math.min((ts - startTs) / duration, 1)
    const eased = 1 - Math.pow(1 - t, 3)
    animatedGauges.value = targets.map(v => v * eased)
    if (t < 1) requestAnimationFrame(tick)
    else animatedGauges.value = [...targets]
  }
  requestAnimationFrame(tick)
}

watch([capitalProgress, transferRate, annualCapitalProgress, approvalProgress], runGaugeCountUp, { immediate: true })

// Four-class warnings
const fourClassTypes = [
  { name: '列账不及时',   key: 'liezhang' },
  { name: '预转固不及时', key: 'yuzhuang' },
  { name: '关闭不及时',   key: 'guanbi'   },
  { name: '长期挂账',     key: 'guazhang' },
]

const fourClassWarningsLocal = ref(null)
const fourClassDetailVisible = ref(false)
const fourClassDetailType = ref('')
const fourClassDetailItems = ref([])

const fcWarnings = computed(() => fourClassWarningsLocal.value || props.fourClassWarnings)

// Manager view (管理员视图)
const managerViewRows = computed(() => {
  const data = props.zaigongData
  if (!data) return []
  const summary = data.summary || []
  const detail = data.detail || []

  const countMap = {}
  detail.forEach(p => {
    const mgr = p['工程管理员'] || p.manager || '未分配'
    countMap[mgr] = (countMap[mgr] || 0) + 1
  })

  return summary
    .filter(r => {
      const name = r.manager || r['工程管理员'] || ''
      return name !== '合计'
    })
    .map(r => ({
      manager: r.manager || r['工程管理员'] || '未知',
      count: countMap[r.manager || r['工程管理员']] || (detail.length > 0 ? 0 : (r._count || 0)),
      capital: r.capital || r['本年累计资本性支出'] || 0,
      rate: ((r.rate ?? r['转固率']) || 0) * 100,
    }))
    .sort((a, b) => b.capital - a.capital)
})

function formatNum(v) {
  if (v == null || Number.isNaN(v)) return '—'
  return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

function getRateBarClass(rate) {
  if (rate >= 0.6) return 'ok'
  if (rate >= 0.3) return 'warn'
  return 'bad'
}

function showFourClassDetail(typeName) {
  if (!fcWarnings.value?.items) return
  fourClassDetailType.value = typeName
  fourClassDetailItems.value = fcWarnings.value.items.filter(i => i.type === typeName)
  fourClassDetailVisible.value = true
}

function showFourClassAllDetail() {
  fourClassDetailType.value = '四类工程预警明细'
  fourClassDetailItems.value = fcWarnings.value?.items || []
  fourClassDetailVisible.value = true
}

async function exportFourClassWarnings() {
  if (!props.recordId) return
  try {
    const { exportFourClassExcel } = await import('../api')
    const blob = await exportFourClassExcel(props.recordId)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `四类工程预警_${currentDate.value}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('导出失败', e)
  }
}

function getGroupItems(typeName) {
  return (fcWarnings.value?.items || []).filter(i => i.type === typeName)
}

function getGroupStats(typeName) {
  const items = getGroupItems(typeName)
  return {
    triggered: items.filter(i => i.status === '已触发' || i.status === '已触发(超期完成)').length,
    warning: items.filter(i => i.status === '预警').length,
  }
}

const MGR_COLORS = ['var(--info)', 'var(--ok)', 'var(--accent)', 'var(--warn)']
const mgrColorIndex = {}
let mgrColorSeq = 0
function getMgrChipColor(name) {
  if (mgrColorIndex[name] === undefined) mgrColorIndex[name] = mgrColorSeq++ % MGR_COLORS.length
  return MGR_COLORS[mgrColorIndex[name]]
}

function getManagersForType(typeName) {
  const items = getGroupItems(typeName)
  if (!items.length) return []
  const map = {}
  items.forEach(item => {
    const mgr = item.manager || '未知'
    map[mgr] = (map[mgr] || 0) + 1
  })
  return Object.entries(map)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 3)
}

function getManagerTextForType(typeName) {
  const mgrs = getManagersForType(typeName)
  if (!mgrs.length) return '—'
  return mgrs.map(m => `${m.name} ${m.count}`).join(' · ')
}

function getDaysClass(daysLabel, status) {
  const days = parseInt(daysLabel)
  if (status === '已触发' || status === '已触发(超期完成)' || days <= 10) return 'days-overdue'
  if (days <= 30) return 'days-warning'
  return ''
}

function getWarningPillClass(key) {
  const map = { liezhang: 'info', yuzhuang: 'warn', guanbi: 'bad', guazhang: 'info' }
  return map[key] || 'info'
}

// Presentation mode
const presentationMode = ref(false)

async function togglePresentationMode() {
  const entering = !presentationMode.value
  presentationMode.value = entering
  emit('presentation-change', entering)
  try {
    if (entering) {
      await document.documentElement.requestFullscreen?.()
    } else {
      if (document.fullscreenElement) await document.exitFullscreen()
    }
  } catch (_) {}
}

function handleFullscreenChange() {
  if (!document.fullscreenElement && presentationMode.value) {
    presentationMode.value = false
    emit('presentation-change', false)
  }
}

function copyNarrative() {
  const text = `当期资本性支出 ${props.zaigongData?.metrics?.capital?.toFixed(2) || '—'} 万元（当期目标 ${displayTargetValue.value} 万，进度 ${capitalProgress.value}%），缺口 ${props.zaigongData?.metrics?.deficit?.toFixed(2) || '—'} 万。全年支出进度 ${annualCapitalProgress.value}%，立项进度 ${approvalProgress.value}%。整体转固率仅 ${transferRate.value}%，需在下一周期集中推进转固。`
  navigator.clipboard.writeText(text).catch(() => {})
}

// Export PNG
const exportLoading = ref(false)
async function exportPNG() {
  if (exportLoading.value) return
  exportLoading.value = true
  try {
    const el = document.querySelector('.ki-page')
    const canvas = await html2canvas(el, {
      backgroundColor: getComputedStyle(document.documentElement).getPropertyValue('--paper').trim() || '#f7f6f1',
      scale: 2,
      useCORS: true,
      logging: false,
    })
    const link = document.createElement('a')
    link.download = `关键指标摘要_${currentDate.value}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
  } catch (e) {
    console.error('导出失败', e)
  } finally {
    exportLoading.value = false
  }
}

onMounted(() => {
  presentationMode.value = Boolean(document.fullscreenElement)
  document.addEventListener('fullscreenchange', handleFullscreenChange)
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
})
</script>

<style scoped>
/* ── Page layout ── */
.ki-page {
  max-width: 1160px; margin: 0 auto; padding: 40px 36px 48px;
}
.ki-fullscreen {
  position: fixed; inset: 0; z-index: 9999;
  background: var(--paper); overflow-y: auto;
  padding: 0 56px 56px; max-width: none;
}
.ki-fullscreen .ki-two-col { gap: 32px; }
.ki-fullscreen .ki-kpi-card { padding: 28px 20px; }
.ki-fullscreen .ki-kpi-donut { width: 130px; height: 130px; }
.ki-fullscreen .ki-kpi-donut svg { width: 130px; height: 130px; }
.ki-fullscreen .ki-kpi-val { font-size: 28px; }
.ki-fullscreen .ki-kpi-label { font-size: 15px; }
.ki-fullscreen .ki-summary-text { font-size: 15px; line-height: 1.75; }
.ki-fullscreen .page-title-h1 { font-size: 28px; }
.ki-fullscreen .ki-right-section-head { padding: 10px 22px; }
.ki-fullscreen .warning-item { padding: 0 22px; }
.ki-fullscreen .mgr-row { padding: 0 22px; }

/* ── Presentation nav ── */
.ki-pres-nav {
  display: flex; align-items: center; justify-content: space-between;
  height: 56px; margin-bottom: 32px; padding: 0 8px;
  border-bottom: 1px solid var(--line);
}
.ki-nav-mark {
  width: 32px; height: 32px; border-radius: 8px;
  background: var(--accent); color: var(--paper);
  display: grid; place-items: center;
  font-size: 11px; font-weight: 600; font-family: var(--font-mono);
}
.ki-exit-btn {
  height: 32px; padding: 0 12px; border-radius: var(--r-md);
  border: 1px solid var(--line-2); background: var(--surface);
  color: var(--ink-2); font-size: 12px; cursor: pointer; font-family: inherit;
}
.ki-exit-btn:hover { background: var(--paper-2); }

/* ── Buttons ── */
.ki-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 12px; border-radius: var(--r-md);
  font-size: 12.5px; color: var(--ink-2);
  background: var(--surface); border: 1px solid var(--line-2);
  transition: all 120ms; white-space: nowrap; cursor: pointer; font-family: inherit;
}
.ki-btn:hover { background: var(--paper-2); color: var(--ink); border-color: var(--ink-4); }
.ki-btn.primary { background: var(--ink); color: var(--paper); border-color: var(--ink); }
.ki-btn.primary:hover { background: var(--accent); border-color: var(--accent); color: #fff; }
.ki-btn.ghost { background: transparent; border-color: transparent; color: var(--ink-2); }
.ki-btn.ghost:hover { background: var(--paper-2); }
.ki-btn svg { width: 12px; height: 12px; opacity: 0.7; }

/* ── Page Header ── */
.page-head {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 20px;
  padding-bottom: 0; border-bottom: none; gap: 16px;
}
.page-head-l { flex: 1; }
.eyebrow {
  font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--ink-3); font-family: var(--font-mono);
  display: inline; gap: 0; font-weight: 400;
}
.eyebrow::after { display: none; }
.page-title-h1 {
  font-size: 22px; font-weight: 650; color: var(--ink); margin: 4px 0 6px;
  letter-spacing: -0.02em;
}
.page-meta {
  display: flex; align-items: center; gap: 8px;
  font-size: 11.5px; color: var(--ink-3); font-family: var(--font-mono);
}
.ph-sep {
  width: 1px; height: 10px; background: var(--line-2);
}
.page-actions {
  display: flex; gap: 8px; align-items: center; flex-shrink: 0;
}

/* ── Summary banner ── */
.ki-summary-banner {
  margin-bottom: 24px;
  background: var(--surface-2);
  border: 1px dashed var(--line-2);
  border-radius: var(--r-lg);
  padding: 18px 20px 0;
}
.ki-summary-text {
  font-size: 13.5px; line-height: 1.8; color: var(--ink-2);
  margin: 0 0 14px;
}
.ki-summary-text strong { color: var(--ink); }
.ki-summary-text .mono { font-family: var(--font-mono); font-weight: 550; }
.ki-summary-foot {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 0; border-top: 1px solid var(--line);
  font-size: 10.5px; color: var(--ink-3); font-family: var(--font-mono);
}

/* ── Two-column layout ── */
.ki-two-col {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 20px;
  align-items: stretch;
}

/* ── Left: 2×2 KPI grid ── */
.ki-kpi-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  background: var(--line);
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  overflow: hidden;
}
.ki-kpi-card {
  background: var(--surface);
  padding: 24px 16px 20px;
  display: flex; flex-direction: column; align-items: center;
  text-align: center;
  gap: 10px;
}
.ki-kpi-donut {
  position: relative;
  display: grid; place-items: center;
  width: 110px; height: 110px; flex-shrink: 0;
}
.ki-kpi-center {
  position: absolute; text-align: center; pointer-events: none;
}
.ki-kpi-val {
  font-size: 22px; font-weight: 550; color: var(--ink);
  letter-spacing: -0.02em; line-height: 1;
}
.ki-kpi-val.is-low { color: var(--bad); }
.ki-kpi-unit {
  font-size: 13px; font-weight: 450; color: var(--ink-3);
  margin-left: 1px;
}
.ki-kpi-target {
  font-size: 9px; color: var(--ink-3); margin-top: 2px;
}
.ki-kpi-label {
  font-size: 12.5px; color: var(--ink-2); font-weight: 500;
}
.ki-kpi-sub {
  font-size: 10.5px; color: var(--ink-3);
  font-family: var(--font-mono);
}
.ki-kpi-delta {
  display: inline-flex; align-items: center; gap: 4px;
  font-family: var(--font-mono); font-size: 10.5px;
  padding: 2px 7px; border-radius: 999px;
}
.ki-kpi-delta.ok { background: var(--ok-soft); color: var(--ok); }
.ki-kpi-delta.up { background: var(--info-soft); color: var(--info); }
.ki-kpi-delta.down { background: var(--bad-soft); color: var(--bad); }
.ki-kpi-delta.flat { background: var(--paper-2); color: var(--ink-3); }
.tri-up::before { content: '▲'; font-size: 7px; margin-right: 2px; }
.tri-dn::before { content: '▼'; font-size: 7px; margin-right: 2px; }

/* ── Right: Unified panel (same border as left grid) ── */
.ki-right-panel {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  overflow: hidden;
  display: flex; flex-direction: column;
  height: 100%;
}
.ki-right-section {
  border-bottom: 1px solid var(--line);
  flex: 1; display: flex; flex-direction: column; min-height: 0; overflow: hidden;
}
.ki-right-section:last-child { border-bottom: none; }
.ki-right-section-head {
  padding: 10px 16px; display: flex; align-items: center; justify-content: space-between;
  gap: 12px; flex-shrink: 0;
}
.ki-right-section-head h3 { font-size: 13px; font-weight: 500; color: var(--ink); margin: 0; letter-spacing: -0.005em; }
.ki-right-section-head .sub { font-size: 11px; color: var(--ink-3); }
.ki-right-section-body { padding: 0; flex: 1; display: flex; flex-direction: column; min-height: 0; }
.ki-right-empty { padding: 28px 20px; text-align: center; color: var(--ink-3); font-size: 13px; }

.warning-item {
  flex: 1; padding: 0 18px;
  border-bottom: 1px solid var(--line);
  display: grid; grid-template-columns: 1fr auto 88px; align-items: center; gap: 12px;
  cursor: pointer; transition: background 120ms;
}
.warning-item:last-child { border-bottom: none; }
.warning-item:hover { background: var(--surface-2); }

.warning-count { font-family: var(--font-mono); font-size: 24px; color: var(--ink); font-weight: 500; letter-spacing: -0.02em; flex-shrink: 0; }
.warning-mgr-text { font-size: 10.5px; color: var(--ink-4); font-family: var(--font-mono); min-width: 80px; text-align: right; white-space: nowrap; }

/* Pill badges */
.pill {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 2px 8px; border-radius: 999px;
  font-size: 11px; font-weight: 500; white-space: nowrap;
}
.pill .dot { width: 5px; height: 5px; border-radius: 50%; background: currentColor; }
.pill.ok   { background: var(--ok-soft);   color: var(--ok);   }
.pill.warn { background: var(--warn-soft); color: var(--warn); }
.pill.bad  { background: var(--bad-soft);  color: var(--bad);  }
.pill.info { background: var(--info-soft); color: var(--info); }

/* ── Manager view rows ── */
.mgr-header, .mgr-row {
  display: grid;
  grid-template-columns: 22px 1fr 44px 76px 90px;
  column-gap: 10px;
  align-items: center;
  padding: 7px 16px;
}
.mgr-header {
  border-bottom: 1px solid var(--line);
  font-size: 10.5px; color: var(--ink-3); font-weight: 500;
  background: var(--surface-2);
}
.mgr-row {
  flex: 1; border-bottom: 1px solid var(--line);
  font-size: 12px; transition: background 100ms;
}
.mgr-row:last-child { border-bottom: none; }
.mgr-row:hover { background: var(--surface-2); }

/* Column header alignments */
.mgr-rank-hd { text-align: center; }
.mgr-name-hd { min-width: 0; }
.mgr-count-hd { text-align: right; }
.mgr-capital-hd { text-align: right; }
.mgr-rate-hd { padding-left: 36px; }

/* Rank badge */
.mgr-rank {
  width: 22px; height: 20px; border-radius: 4px;
  display: grid; place-items: center;
  font-size: 11px; font-weight: 500; color: var(--ink-3);
  background: var(--paper-2);
}
.mgr-rank.top { background: var(--accent); color: #fff; font-weight: 600; }

/* Name cell */
.mgr-name {
  min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  color: var(--ink); font-weight: 500;
}

/* Count cell */
.mgr-count { text-align: right; font-size: 11px; }

/* Capital cell */
.mgr-capital { text-align: right; font-size: 12px; font-weight: 500; color: var(--ink); }
.mgr-capital.neg { color: var(--bad); }

/* Rate cell */
.mgr-rate { display: flex; align-items: center; gap: 4px; }
.mgr-rate-pct {
  font-size: 11px; font-family: var(--font-mono); color: var(--ink-3);
  width: 36px; text-align: right; flex-shrink: 0;
}
.mgr-rate-track {
  flex: 1; height: 6px; border-radius: 3px;
  background: var(--paper-2); overflow: hidden;
  min-width: 0;
}
.mgr-rate-fill { height: 100%; border-radius: 3px; }
.mgr-rate-fill.ok { background: var(--ok); }
.mgr-rate-fill.warn { background: var(--warn); }
.mgr-rate-fill.bad { background: var(--bad); }

.mono { font-family: var(--font-mono); }
.muted { color: var(--ink-3); }

/* ── Modal ── */
.four-class-modal-overlay { position: fixed; inset: 0; background: rgba(31,29,24,0.45); display: flex; align-items: center; justify-content: center; z-index: 9999; }
.four-class-modal { background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg); width: 98%; max-width: 1400px; max-height: 84vh; display: flex; flex-direction: column; box-shadow: var(--shadow-pop); }
.four-class-modal .modal-header { padding: 14px 18px; border-bottom: 1px solid var(--line); display: flex; align-items: center; justify-content: space-between; }
.four-class-modal .modal-title-wrap { display: flex; align-items: baseline; gap: 12px; }
.four-class-modal .modal-title-wrap h3 { font-size: 15px; font-weight: 600; color: var(--ink); margin: 0; }
.four-class-modal .modal-date { font-size: 11px; color: var(--ink-3); }
.four-class-modal .modal-header-actions { display: flex; align-items: center; gap: 8px; }
.four-class-modal .export-btn-primary { display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: var(--info); color: #fff; border: none; border-radius: var(--r-md); font-size: 12px; font-weight: 600; cursor: pointer; font-family: inherit; transition: background 0.15s; }
.four-class-modal .export-btn-primary:hover { background: #145293; }
.four-class-modal .export-btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.four-class-modal .modal-body { flex: 1; overflow: auto; padding: 14px 20px 18px; }
.four-class-modal .modal-close { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; background: var(--surface); border: 1px solid var(--line-2); border-radius: var(--r-md); color: var(--ink-2); cursor: pointer; font-size: 14px; font-family: inherit; transition: 0.15s; }
.four-class-modal .modal-close:hover { background: var(--paper-2); color: var(--ink); }
.four-class-modal-table { width: 100%; border-collapse: collapse; min-width: 1000px; table-layout: fixed; }
.four-class-modal-table th { background: var(--paper-2); color: var(--ink-3); font-weight: 500; font-size: 11px; padding: 7px 6px; text-align: left; border-bottom: 1px solid var(--line); position: sticky; top: 0; word-break: break-word; }
.four-class-modal-table td { padding: 5px 6px; border-bottom: 1px solid var(--paper-2); color: var(--ink); font-size: 11px; }
.four-class-modal-table tr:hover td { background: var(--paper); }
.four-class-modal-table .col-status { width: 48px; white-space: nowrap; }
.four-class-modal-table .col-name { width: 240px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.four-class-modal-table .col-accept { width: 64px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.four-class-modal-table .col-manager { width: 52px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.four-class-modal-table .col-date { width: 76px; white-space: nowrap; font-size: 10px; color: var(--ink-2); overflow: hidden; text-overflow: ellipsis; }
.four-class-modal-table .col-project-status { width: 100px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.four-class-modal-table .col-days { width: 72px; white-space: nowrap; font-weight: 600; overflow: hidden; text-overflow: ellipsis; }
.four-class-modal-table .col-days.days-overdue { color: var(--bad); font-weight: 700; }
.four-class-modal-table .col-days.days-warning { color: var(--ink); font-weight: 700; }
.four-class-modal-table .col-suggestion { color: var(--ink-3); font-size: 11px; white-space: normal; line-height: 1.4; width: 140px; word-break: break-word; }
.four-class-modal-table .status-tag { display: inline-block; padding: 2px 7px; border-radius: var(--r-sm); font-size: 11px; font-weight: 600; }
.four-class-modal-table .status-tag.已触发, .four-class-modal-table .row-已触发 td { background: var(--bad-soft); color: var(--bad); }
.four-class-modal-table .status-tag.预警, .four-class-modal-table .row-预警 td { color: var(--ink); }
.four-class-group { margin-bottom: 20px; }
.four-class-group .group-header { display: flex; align-items: center; gap: 12px; padding: 6px 10px; border-radius: var(--r-sm); margin-bottom: 6px; }
.four-class-group.group-liezhang .group-header { background: var(--info-soft); color: #1F497D; }
.four-class-group.group-yuzhuang .group-header { background: var(--warn-soft); color: #7B3F00; }
.four-class-group.group-guanbi   .group-header { background: var(--bad-soft);  color: #843C0C; }
.four-class-group.group-guazhang .group-header { background: #dde5ee;          color: #244062; }
.group-title { font-weight: 700; font-size: 13px; }
.group-count { font-size: 11px; opacity: 0.8; }

/* ── Responsive ── */
@media (max-width: 960px) {
  .ki-two-col {
    grid-template-columns: 1fr;
  }
  .ki-kpi-grid { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 640px) {
  .ki-page { padding: 20px 12px; }
  .ki-kpi-grid { grid-template-columns: 1fr; }
  .ki-kpi-card { padding: 20px 16px; }
  .ki-pres-nav { padding: 0 12px; }
}
</style>
