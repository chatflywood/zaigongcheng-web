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
        <div style="font-size:12.5px;color:var(--ink-3);margin-top:6px">
          代替原「大屏」页面。每个指标自带叙事，可截图直接用作周/月度汇报。
        </div>
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
        <button class="ki-btn ghost" @click="openAddModal">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="none"><path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          添加工作
        </button>
        <button class="ki-btn ghost" @click="togglePresentationMode">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="none"><path d="M2 5V2h3M11 2h3v3M2 11v3h3M14 11v3h-3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
          {{ presentationMode ? '退出展示' : '投屏' }}
        </button>
        <button class="ki-btn primary">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="none"><path d="M3 12v1.5h10V12M5 8l3 3 3-3M8 3v8" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
          导出 PNG
        </button>
      </div>
    </header>

    <!-- ── 4 Core KPI Donut Gauges (2×2 hairline grid) ── -->
    <div class="section">
      <div class="section-head">
        <h2>四个核心指标</h2>
        <span class="sub">对比目标 · 含叙事说明</span>
      </div>
      <div class="ki-gauge-grid">

        <!-- Card 1: 资本性支出年度进度 -->
        <div class="ki-gauge-cell">
          <div class="ki-gauge-donut">
            <svg width="120" height="120" viewBox="0 0 120 120">
              <circle cx="60" cy="60" r="50" fill="none" stroke="var(--paper-2)" stroke-width="10"/>
              <circle cx="60" cy="60" r="50" fill="none"
                :stroke="gaugeColor(parseFloat(capitalProgress), 100)"
                stroke-width="10"
                stroke-linecap="round"
                stroke-dasharray="314.16"
                :stroke-dashoffset="314.16 * (1 - Math.min(parseFloat(capitalProgress), 100) / 100)"
                transform="rotate(-90 60 60)"
              />
            </svg>
            <div class="ki-gauge-center">
              <div class="mono ki-gauge-val">{{ capitalProgress }}</div>
              <div class="ki-gauge-target">目标 100%</div>
            </div>
          </div>
          <div class="ki-gauge-info">
            <div class="ki-gauge-label">资本性支出年度进度</div>
            <div class="ki-gauge-sub mono">{{ props.zaigongData?.metrics?.capital?.toFixed(1) || '0.0' }} / {{ displayTargetValue }} 万</div>
            <div class="ki-gauge-delta" :class="parseFloat(capitalProgress) >= 80 ? 'ok' : 'up'">
              <span class="tri-up"></span>缺口 {{ props.zaigongData?.metrics?.deficit?.toFixed(1) || '0.0' }} 万
            </div>
            <div class="ki-gauge-narrative">
              已完成年度目标的 {{ capitalProgress }}%，距离全年 {{ displayTargetValue }} 万元目标还差 {{ props.zaigongData?.metrics?.deficit?.toFixed(1) || '—' }} 万。
            </div>
          </div>
        </div>

        <!-- Card 2: 转固率 -->
        <div class="ki-gauge-cell">
          <div class="ki-gauge-donut">
            <svg width="120" height="120" viewBox="0 0 120 120">
              <circle cx="60" cy="60" r="50" fill="none" stroke="var(--paper-2)" stroke-width="10"/>
              <circle cx="60" cy="60" r="50" fill="none"
                :stroke="gaugeColor(parseFloat(transferRate), 80)"
                stroke-width="10"
                stroke-linecap="round"
                stroke-dasharray="314.16"
                :stroke-dashoffset="314.16 * (1 - Math.min(parseFloat(transferRate), 100) / 100)"
                transform="rotate(-90 60 60)"
              />
            </svg>
            <div class="ki-gauge-center">
              <div class="mono ki-gauge-val">{{ transferRate }}</div>
              <div class="ki-gauge-target">目标 80%</div>
            </div>
          </div>
          <div class="ki-gauge-info">
            <div class="ki-gauge-label">转固率</div>
            <div class="ki-gauge-sub mono">期末余额 vs 年初数</div>
            <div class="ki-gauge-delta" :class="parseFloat(transferRate) < 10 ? 'down' : 'flat'">
              <span v-if="parseFloat(transferRate) < 10" class="tri-dn"></span>
              {{ parseFloat(transferRate) < 10 ? '低位' : '—' }}
            </div>
            <div class="ki-gauge-narrative">
              整体转固率 {{ transferRate }}%，{{ parseFloat(transferRate) < 80 ? '低于 80% 期望值。期末余额仍有较大规模尚未转为固定资产。' : '已达标。' }}
            </div>
          </div>
        </div>

        <!-- Card 3: 预算执行率 -->
        <div class="ki-gauge-cell">
          <div class="ki-gauge-donut">
            <svg width="120" height="120" viewBox="0 0 120 120">
              <circle cx="60" cy="60" r="50" fill="none" stroke="var(--paper-2)" stroke-width="10"/>
              <circle cx="60" cy="60" r="50" fill="none"
                :stroke="gaugeColor(parseFloat(annualCapitalProgress), 100)"
                stroke-width="10"
                stroke-linecap="round"
                stroke-dasharray="314.16"
                :stroke-dashoffset="314.16 * (1 - Math.min(parseFloat(annualCapitalProgress), 100) / 100)"
                transform="rotate(-90 60 60)"
              />
            </svg>
            <div class="ki-gauge-center">
              <div class="mono ki-gauge-val">{{ annualCapitalProgress }}</div>
              <div class="ki-gauge-target">目标 100%</div>
            </div>
          </div>
          <div class="ki-gauge-info">
            <div class="ki-gauge-label">预算执行率</div>
            <div class="ki-gauge-sub mono">{{ props.budgetData?.annual_spend_total?.toFixed(1) || '0.0' }} / {{ props.budgetData?.budget_total?.toFixed(1) || '0.0' }} 万</div>
            <div class="ki-gauge-delta" :class="parseFloat(annualCapitalProgress) > 100 ? 'down' : 'up'">
              <span v-if="parseFloat(annualCapitalProgress) > 100" class="tri-dn"></span>
              <span v-else class="tri-up"></span>
              {{ parseFloat(annualCapitalProgress) > 100 ? '超支' : `${(100 - parseFloat(annualCapitalProgress)).toFixed(1)}pp 待执行` }}
            </div>
            <div class="ki-gauge-narrative">
              全年支出占预算 {{ annualCapitalProgress }}%。{{ parseFloat(annualCapitalProgress) > 100 ? '已超预算，需关注。' : '执行中，未超支。' }}
            </div>
          </div>
        </div>

        <!-- Card 4: 立项进度 -->
        <div class="ki-gauge-cell">
          <div class="ki-gauge-donut">
            <svg width="120" height="120" viewBox="0 0 120 120">
              <circle cx="60" cy="60" r="50" fill="none" stroke="var(--paper-2)" stroke-width="10"/>
              <circle cx="60" cy="60" r="50" fill="none"
                :stroke="gaugeColor(parseFloat(approvalProgress), 90)"
                stroke-width="10"
                stroke-linecap="round"
                stroke-dasharray="314.16"
                :stroke-dashoffset="314.16 * (1 - Math.min(parseFloat(approvalProgress), 100) / 100)"
                transform="rotate(-90 60 60)"
              />
            </svg>
            <div class="ki-gauge-center">
              <div class="mono ki-gauge-val">{{ approvalProgress }}</div>
              <div class="ki-gauge-target">目标 90%</div>
            </div>
          </div>
          <div class="ki-gauge-info">
            <div class="ki-gauge-label">立项进度</div>
            <div class="ki-gauge-sub mono">{{ props.budgetData?.occupied_total?.toFixed(1) || '0.0' }} / {{ props.budgetData?.budget_total?.toFixed(1) || '0.0' }} 万</div>
            <div class="ki-gauge-delta" :class="parseFloat(approvalProgress) < 90 ? 'up' : 'flat'">
              {{ parseFloat(approvalProgress) < 90 ? `${(90 - parseFloat(approvalProgress)).toFixed(1)}pp 未绑定` : '已达标' }}
            </div>
            <div class="ki-gauge-narrative">
              预算占用率 {{ approvalProgress }}%，{{ parseFloat(approvalProgress) >= 90 ? '已超配。' : '部分预算尚未绑定立项。' }}
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- ── Manager contribution + Top 6 balances ── -->
    <div class="section" v-if="props.zaigongData?.summary?.length || props.zaigongData?.detail?.length">
      <div class="section-head">
        <h2>责任分布 & 最大在建</h2>
      </div>
      <div class="ki-two-col">

        <!-- Manager contribution bars -->
        <div class="ki-card" v-if="props.zaigongData?.summary?.length">
          <div class="ki-card-head">
            <div>
              <div class="ki-card-title">本年支出 · 管理员贡献</div>
              <div class="ki-card-sub">占总支出比重</div>
            </div>
          </div>
          <div class="ki-card-body">
            <template v-for="(row, i) in mgrShares" :key="row.name">
              <div class="ki-mgr-row" :style="{ borderBottom: i < mgrShares.length - 1 ? '1px dashed var(--line)' : 'none' }">
                <div class="ki-mgr-name">{{ row.manager || row['工程管理员'] }}</div>
                <div class="ki-mgr-bar-wrap">
                  <div class="ki-mgr-bar" :style="{ width: row.share + '%', background: row.capital < 0 ? 'var(--bad)' : 'var(--accent)' }"></div>
                </div>
                <div class="ki-mgr-amount mono">{{ (row.capital || row['本年累计资本性支出'] || 0).toFixed(1) }}万</div>
                <div class="ki-mgr-share mono muted">{{ row.share.toFixed(1) }}%</div>
              </div>
            </template>
          </div>
        </div>

        <!-- Top 6 by balance -->
        <div class="ki-card" v-if="props.zaigongData?.detail?.length">
          <div class="ki-card-head">
            <div>
              <div class="ki-card-title">期末余额 · Top 6</div>
              <div class="ki-card-sub">规模最大的在建工程</div>
            </div>
          </div>
          <div style="padding:0">
            <div v-for="(p, i) in topProjects" :key="p.name"
              style="padding:14px 20px;display:grid;grid-template-columns:24px 1fr 80px;align-items:center;gap:12px"
              :style="{ borderBottom: i < topProjects.length - 1 ? '1px solid var(--line)' : 'none' }">
              <span class="mono muted" style="font-size:11px">{{ i + 1 }}</span>
              <div style="min-width:0">
                <div style="font-size:13px;color:var(--ink);overflow:hidden;text-overflow:ellipsis;white-space:nowrap" :title="p.name">{{ p.name }}</div>
                <div style="font-size:11px;color:var(--ink-3);margin-top:2px">{{ p.manager }}</div>
              </div>
              <div class="num mono" style="font-size:14px;font-weight:500">{{ p.balance?.toFixed(1) }}<span style="font-size:10px;color:var(--ink-3);margin-left:2px;font-weight:400">万</span></div>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- ── 近期重点工作 ── -->
    <div class="section" v-if="sortedWorkItems.length > 0 || !props.zaigongData">
      <div class="section-head">
        <h2>近期重点工作</h2>
        <button class="ki-btn ghost" @click="openAddModal">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="none"><path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          添加
        </button>
      </div>
      <div v-if="sortedWorkItems.length === 0" class="ki-card" style="padding:32px;text-align:center;color:var(--ink-3);font-size:13px">
        暂无重点工作 · 点击上方添加
      </div>
      <div v-else class="ki-card">
        <div v-for="item in sortedWorkItems" :key="item.id" class="ki-work-item" :class="{ completed: item.status === 'completed' }">
          <div class="ki-work-head">
            <span class="ki-priority" :class="'pri-' + item.level">{{ item.levelText }}</span>
            <span v-if="item.owner" class="ki-work-owner">{{ item.owner }}</span>
            <span class="ki-work-due mono">{{ item.dueDate }}</span>
          </div>
          <div class="ki-work-title">{{ item.content }}</div>
          <div class="ki-work-actions" v-if="!presentationMode">
            <button @click="openEditModal(item)">编辑</button>
            <button class="danger" @click="deleteItem(item.id)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Narrative summary ── -->
    <div class="section" v-if="props.zaigongData?.metrics">
      <div class="section-head">
        <h2>一段话摘要 · 可粘贴</h2>
        <span class="sub">为周报起草</span>
      </div>
      <div class="ki-narrative-card">
        <p class="ki-narrative-text">
          本年累计资本性支出 <strong class="mono">{{ props.zaigongData?.metrics?.capital?.toFixed(2) || '—' }} 万元</strong>（年度目标 {{ displayTargetValue }} 万，进度 <strong style="color:var(--accent)">{{ capitalProgress }}%</strong>），年度缺口 <strong class="mono" style="color:var(--warn)">{{ props.zaigongData?.metrics?.deficit?.toFixed(2) || '—' }} 万</strong>。全年预算执行率 <strong style="color:var(--accent)">{{ annualCapitalProgress }}%</strong>，立项进度 {{ approvalProgress }}%。在建工程期末余额规模较大，整体转固率仅 <strong class="mono" style="color:var(--bad)">{{ transferRate }}%</strong>，需在下一周期集中推进转固。
        </p>
        <div class="ki-narrative-foot">
          <span>AUTO-DRAFTED · 基于上传数据</span>
          <button class="ki-btn ghost" style="height:28px;font-size:11px">复制纯文本</button>
        </div>
      </div>
    </div>

    <!-- Work item modal -->
    <div v-if="modalVisible" class="ki-modal-overlay" @click.self="closeModal">
      <div class="ki-modal">
        <div class="ki-modal-head">
          <h4>{{ modalMode === 'add' ? '添加重点工作' : '编辑重点工作' }}</h4>
          <button @click="closeModal" class="ki-modal-close">×</button>
        </div>
        <div class="ki-modal-body">
          <label>工作内容</label>
          <textarea v-model="formContent" rows="3" placeholder="输入重点工作内容"></textarea>
          <label>优先级</label>
          <select v-model="formLevel">
            <option value="urgent">紧急</option>
            <option value="high">跟进</option>
            <option value="normal">准备</option>
          </select>
          <label>责任人</label>
          <input v-model="formOwner" type="text" placeholder="输入责任人姓名" />
          <label>完成日期</label>
          <input v-model="formDueDate" type="date" />
          <div v-if="formError" class="ki-form-error">{{ formError }}</div>
        </div>
        <div class="ki-modal-foot">
          <button class="ki-btn ghost" @click="closeModal">取消</button>
          <button class="ki-btn primary" @click="saveItem">保存</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  zaigongData: Object,
  budgetData: Object,
  zaigongDate: String,
  budgetDate: String,
  fourClassWarnings: Object
})

const emit = defineEmits(['presentation-change'])

// 当前日期
const currentDate = computed(() => {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
})

// 目标值
const targetValue = computed(() => {
  const value = Number(props.zaigongData?.metrics?.yearTarget)
  return Number.isFinite(value) && value > 0 ? value : null
})

const displayTargetValue = computed(() => {
  return targetValue.value === null ? '—' : targetValue.value.toFixed(2)
})

// 日期格式化
const normalizedZaigongDate = computed(() => formatDisplayDate(props.zaigongDate))
const normalizedBudgetDate = computed(() => formatDisplayDate(props.budgetDate))

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

// 指标计算
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

const rateStatusClass = computed(() => {
  const rate = props.zaigongData?.metrics?.rate || 0
  if (rate >= 0.6) return 'good'
  if (rate >= 0.3) return 'warning'
  return 'danger'
})

// Donut gauge color helper
function gaugeColor(value, target) {
  if (value >= target * 0.95) return 'var(--ok)'
  if (value >= target * 0.80) return 'var(--accent)'
  if (value >= target * 0.50) return 'var(--warn)'
  return 'var(--bad)'
}

// Manager contribution derived from summary rows
const mgrShares = computed(() => {
  const rows = props.zaigongData?.summary || []
  const filtered = rows.filter(r => r.manager !== '合计' && r['工程管理员'] !== '合计')
  const totalSpend = filtered.reduce((s, r) => s + Math.max(r.capital || r['本年累计资本性支出'] || 0, 0), 0) || 1
  return filtered
    .map(r => ({
      ...r,
      share: (Math.max(r.capital || r['本年累计资本性支出'] || 0, 0) / totalSpend) * 100,
    }))
    .sort((a, b) => b.share - a.share)
    .slice(0, 8)
})

// Top 6 projects by balance
const topProjects = computed(() => {
  const detail = props.zaigongData?.detail || []
  return detail
    .map(p => ({
      name: p.name || p['工程名称'] || '',
      manager: p.manager || p['工程管理员'] || '',
      balance: Number(p.balance || p['在建工程期末余额'] || 0),
    }))
    .filter(p => p.balance > 0)
    .sort((a, b) => b.balance - a.balance)
    .slice(0, 6)
})

// SVG 仪表盘 dashOffset 计算
const dashOffset = (value) => {
  const num = Math.min(100, Math.max(0, parseFloat(value) || 0))
  return Math.round(172.8 * (1 - num / 100))
}

// 全屏展示模式
const presentationMode = ref(false)

async function togglePresentationMode() {
  try {
    if (!document.fullscreenElement) {
      await document.documentElement.requestFullscreen()
      presentationMode.value = true
      emit('presentation-change', true)
    } else {
      await document.exitFullscreen()
      presentationMode.value = false
      emit('presentation-change', false)
    }
  } catch (error) {
    console.error('切换展示模式失败:', error)
  }
}

function handleFullscreenChange() {
  presentationMode.value = Boolean(document.fullscreenElement)
  emit('presentation-change', presentationMode.value)
}

// 重点工作
const workItems = ref([])
const workItemsStorageKey = 'key_work_items_v2'
const modalVisible = ref(false)
const modalMode = ref('add')
const editingItem = ref(null)
const formContent = ref('')
const formLevel = ref('normal')
const formOwner = ref('')
const formDueDate = ref('')
const formError = ref('')

const levelMap = { urgent: '紧急', high: '跟进', normal: '准备' }
const levelPriority = { urgent: 0, high: 1, normal: 2 }

const sortedWorkItems = computed(() => {
  const pending = workItems.value
    .filter(item => item.status === 'pending')
    .sort((a, b) => {
      const pDiff = levelPriority[a.level] - levelPriority[b.level]
      if (pDiff !== 0) return pDiff
      return (a.dueDate || '').localeCompare(b.dueDate || '')
    })
  const completed = workItems.value
    .filter(item => item.status === 'completed')
    .sort((a, b) => (b.updatedAt || '').localeCompare(a.updatedAt || ''))
  return [...pending, ...completed].map(item => ({
    ...item,
    levelText: levelMap[item.level] || '准备'
  }))
})

function loadWorkItems() {
  try {
    const raw = localStorage.getItem(workItemsStorageKey)
    workItems.value = raw ? JSON.parse(raw) : []
  } catch {
    workItems.value = []
  }
}

function saveWorkItems() {
  localStorage.setItem(workItemsStorageKey, JSON.stringify(workItems.value))
}

function openAddModal() {
  modalMode.value = 'add'
  editingItem.value = null
  formContent.value = ''
  formLevel.value = 'normal'
  formOwner.value = ''
  formDueDate.value = ''
  formError.value = ''
  modalVisible.value = true
}

function openEditModal(item) {
  modalMode.value = 'edit'
  editingItem.value = item
  formContent.value = item.content || ''
  formLevel.value = item.level || 'normal'
  formOwner.value = item.owner || ''
  formDueDate.value = item.dueDate || ''
  formError.value = ''
  modalVisible.value = true
}

function closeModal() {
  modalVisible.value = false
}

function validateForm() {
  if (!formContent.value.trim()) {
    formError.value = '请输入工作内容'
    return false
  }
  if (!formOwner.value.trim()) {
    formError.value = '请输入责任人'
    return false
  }
  if (!formDueDate.value) {
    formError.value = '请选择完成日期'
    return false
  }
  formError.value = ''
  return true
}

function makeItemId() {
  return globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function saveItem() {
  if (!validateForm()) return
  const now = new Date().toISOString()
  if (modalMode.value === 'add') {
    workItems.value.push({
      id: makeItemId(),
      content: formContent.value.trim(),
      level: formLevel.value,
      owner: formOwner.value.trim(),
      dueDate: formDueDate.value,
      status: 'pending',
      createdAt: now,
      updatedAt: now
    })
  } else {
    const idx = workItems.value.findIndex(item => item.id === editingItem.value?.id)
    if (idx >= 0) {
      workItems.value[idx] = {
        ...workItems.value[idx],
        content: formContent.value.trim(),
        level: formLevel.value,
        owner: formOwner.value.trim(),
        dueDate: formDueDate.value,
        updatedAt: now
      }
    }
  }
  saveWorkItems()
  closeModal()
}

function deleteItem(id) {
  if (!confirm('确定删除该重点工作？')) return
  workItems.value = workItems.value.filter(item => item.id !== id)
  saveWorkItems()
}

function toggleStatus(item) {
  const idx = workItems.value.findIndex(target => target.id === item.id)
  if (idx < 0) return
  workItems.value[idx] = {
    ...workItems.value[idx],
    status: item.status === 'pending' ? 'completed' : 'pending',
    updatedAt: new Date().toISOString()
  }
  saveWorkItems()
}

onMounted(() => {
  loadWorkItems()
  presentationMode.value = Boolean(document.fullscreenElement)
  document.addEventListener('fullscreenchange', handleFullscreenChange)
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
})
</script>

<style scoped>
/* Page layout */
.ki-page {
  max-width: 1180px; margin: 0 auto; padding: 56px 40px;
}
.ki-fullscreen {
  position: fixed; inset: 0; z-index: 9999;
  background: var(--paper); overflow-y: auto;
  padding: 0 40px 40px;
}

/* Presentation nav */
.ki-pres-nav {
  display: flex; align-items: center; justify-content: space-between;
  height: 56px; margin-bottom: 36px; padding: 0 8px;
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

/* Buttons */
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

/* 2×2 Gauge grid */
.ki-gauge-grid {
  display: grid; grid-template-columns: repeat(2, 1fr);
  gap: 1px; background: var(--line);
  border: 1px solid var(--line); border-radius: var(--r-lg); overflow: hidden;
}
.ki-gauge-cell {
  background: var(--surface); padding: 28px 30px;
  display: grid; grid-template-columns: 120px 1fr; gap: 24px; align-items: center;
}
.ki-gauge-donut {
  position: relative; display: grid; place-items: center;
  width: 120px; height: 120px;
}
.ki-gauge-center {
  position: absolute; text-align: center; pointer-events: none;
}
.ki-gauge-val {
  font-size: 24px; font-weight: 500; color: var(--ink);
  letter-spacing: -0.02em; line-height: 1;
}
.ki-gauge-target { font-size: 10px; color: var(--ink-3); margin-top: 2px; }

.ki-gauge-label { font-size: 13px; color: var(--ink-2); font-weight: 500; margin-bottom: 4px; }
.ki-gauge-sub { font-size: 11.5px; color: var(--ink-3); margin-bottom: 10px; font-family: var(--font-mono); }
.ki-gauge-delta {
  display: inline-flex; align-items: center; gap: 4px;
  font-family: var(--font-mono); font-size: 11.5px;
  padding: 2px 7px; border-radius: 999px; margin-bottom: 10px;
}
.ki-gauge-delta.ok { background: var(--ok-soft); color: var(--ok); }
.ki-gauge-delta.up { background: var(--info-soft); color: var(--info); }
.ki-gauge-delta.down { background: var(--bad-soft); color: var(--bad); }
.ki-gauge-delta.flat { background: var(--paper-2); color: var(--ink-3); }
.ki-gauge-narrative {
  font-size: 12.5px; color: var(--ink-2); line-height: 1.55;
  padding-top: 12px; border-top: 1px dashed var(--line);
}
.tri-up::before { content: '▲'; font-size: 8px; margin-right: 3px; }
.tri-dn::before { content: '▼'; font-size: 8px; margin-right: 3px; }

/* Two-column layout */
.ki-two-col {
  display: grid; grid-template-columns: 1fr 1.4fr; gap: 24px;
}

/* Card */
.ki-card {
  background: var(--surface); border: 1px solid var(--line);
  border-radius: var(--r-lg); overflow: hidden;
}
.ki-card-head {
  padding: 16px 20px; display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid var(--line);
}
.ki-card-title { font-size: 14px; font-weight: 500; color: var(--ink); margin: 0; }
.ki-card-sub { font-size: 11.5px; color: var(--ink-3); margin-top: 2px; }
.ki-card-body { padding: 16px 20px; }

/* Manager rows */
.ki-mgr-row {
  display: grid; grid-template-columns: 64px 1fr 64px 44px;
  align-items: center; gap: 12px; padding: 10px 0;
}
.ki-mgr-name { font-size: 13px; font-weight: 500; }
.ki-mgr-bar-wrap { height: 6px; background: var(--paper-2); border-radius: 3px; overflow: hidden; }
.ki-mgr-bar { height: 100%; border-radius: 3px; }
.ki-mgr-amount { font-size: 12px; text-align: right; }
.ki-mgr-share { font-size: 11px; text-align: right; }

/* Work items */
.ki-work-item {
  padding: 14px 20px; border-bottom: 1px solid var(--line);
  transition: background 120ms;
}
.ki-work-item:last-child { border-bottom: none; }
.ki-work-item:hover { background: var(--surface-2); }
.ki-work-item.completed { opacity: 0.55; }
.ki-work-head { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.ki-priority {
  font-size: 10px; font-weight: 500; padding: 2px 7px; border-radius: 4px;
}
.pri-urgent { background: var(--bad-soft); color: var(--bad); }
.pri-high { background: var(--warn-soft); color: var(--warn); }
.pri-normal { background: var(--ok-soft); color: var(--ok); }
.ki-work-owner { font-size: 11px; color: var(--ink-3); }
.ki-work-due { font-size: 11px; color: var(--ink-3); margin-left: auto; }
.ki-work-title { font-size: 13px; font-weight: 500; color: var(--ink); line-height: 1.4; }
.ki-work-actions { display: flex; gap: 8px; margin-top: 8px; }
.ki-work-actions button {
  height: 26px; padding: 0 10px; border-radius: 6px;
  border: 1px solid var(--line); background: var(--surface);
  color: var(--ink-2); font-size: 11px; cursor: pointer; font-family: inherit;
}
.ki-work-actions button.danger { border-color: var(--bad-soft); color: var(--bad); }
.ki-work-actions button:hover { background: var(--paper-2); }

/* Narrative */
.ki-narrative-card {
  background: var(--surface-2); border: 1px dashed var(--line-2);
  border-radius: var(--r-lg); padding: 28px 32px;
}
.ki-narrative-text {
  font-size: 14.5px; line-height: 1.85; color: var(--ink-2);
  max-width: 880px;
}
.ki-narrative-text strong { color: var(--ink); }
.ki-narrative-foot {
  margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--line);
  display: flex; justify-content: space-between; align-items: center;
  font-size: 11px; color: var(--ink-3); font-family: var(--font-mono);
}

/* Modal */
.ki-modal-overlay {
  position: fixed; inset: 0; z-index: 1300;
  background: rgba(31,29,24,0.45);
  display: grid; place-items: center;
  backdrop-filter: blur(4px);
}
.ki-modal {
  width: min(480px, 92vw); border-radius: var(--r-xl);
  background: var(--surface); border: 1px solid var(--line-2);
  box-shadow: var(--shadow-pop); overflow: hidden;
}
.ki-modal-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 1px solid var(--line);
}
.ki-modal-head h4 { color: var(--ink); font-size: 15px; font-weight: 500; margin: 0; }
.ki-modal-close {
  width: 28px; height: 28px; border: 1px solid var(--line);
  background: var(--surface); border-radius: var(--r-md);
  color: var(--ink-2); font-size: 18px; cursor: pointer; font-family: inherit;
}
.ki-modal-body { padding: 18px 20px; display: grid; gap: 10px; }
.ki-modal-body label { font-size: 12px; color: var(--ink-2); }
.ki-modal-body input,
.ki-modal-body textarea,
.ki-modal-body select {
  width: 100%; border-radius: var(--r-md); border: 1px solid var(--line-2);
  background: var(--surface); color: var(--ink);
  padding: 9px 12px; font: inherit; font-size: 13px;
}
.ki-form-error { color: var(--bad); font-size: 12px; }
.ki-modal-foot { padding: 0 20px 18px; display: flex; justify-content: flex-end; gap: 10px; }

/* Responsive */
@media (max-width: 1000px) {
  .ki-gauge-grid { grid-template-columns: 1fr; }
  .ki-two-col { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .ki-page { padding: 24px 16px; }
  .ki-gauge-cell { grid-template-columns: 100px 1fr; gap: 16px; padding: 20px; }
  .ki-gauge-val { font-size: 20px; }
}
</style>
