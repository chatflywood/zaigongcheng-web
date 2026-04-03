<template>
  <div class="key-indicators" :class="{ 'fullscreen-mode': presentationMode }">
    <!-- 背景光晕层 -->
    <div class="bg-mesh"></div>

    <!-- 大屏专用导航栏 -->
    <nav class="nav">
      <div class="nav-brand">
        <div class="nav-mark">ZT</div>
        <span class="nav-title">工程建设数据驾舱</span>
      </div>
      <div class="nav-center">
        <div class="nav-date">
          <div class="nav-dot"></div>
          实时数据 · {{ currentDate }} · 仙桃分公司 云网发展部
        </div>
      </div>
      <div class="nav-end">
        <button class="nav-chip exit" @click="togglePresentationMode">
          <svg v-if="presentationMode" width="11" height="11" viewBox="0 0 11 11" fill="none">
            <rect x="1" y="1" width="9" height="9" rx="2" stroke="currentColor" stroke-width="1"/>
            <path d="M4 4l3 3M7 4l-3 3" stroke="currentColor" stroke-width="1" stroke-linecap="round"/>
          </svg>
          <svg v-else width="11" height="11" viewBox="0 0 11 11" fill="none">
            <rect x="1" y="1" width="9" height="9" rx="2" stroke="currentColor" stroke-width="1"/>
            <path d="M3.5 5.5L7.5 3.5V7.5H3.5V5.5Z" fill="currentColor"/>
          </svg>
          {{ presentationMode ? '退出展示模式' : '进入展示模式' }}
        </button>
      </div>
    </nav>

    <!-- 四大 KPI 指标卡 -->
    <div class="kpi-grid">
      <!-- 卡1：立项进度 -->
      <div class="card kpi-card c-violet">
        <div class="kpi-top">
          <div class="kpi-icon violet">📋</div>
          <div class="kpi-badge badge-violet">预算</div>
        </div>
        <div class="kpi-name">立项进度</div>
        <div class="gauge-wrap">
          <svg width="140" height="80" viewBox="0 0 140 80">
            <path d="M15 75 A55 55 0 0 1 125 75" fill="none" stroke="rgba(167,139,250,0.1)" stroke-width="8" stroke-linecap="round"/>
            <path class="gauge-arc" d="M15 75 A55 55 0 0 1 125 75" fill="none" stroke="url(#g-violet)" stroke-width="8" stroke-linecap="round"
              stroke-dasharray="172.8" :stroke-dashoffset="dashOffset(approvalProgress)"/>
            <defs>
              <linearGradient id="g-violet" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#7C3AED"/>
                <stop offset="100%" stop-color="#A78BFA"/>
              </linearGradient>
            </defs>
            <text x="70" y="62" text-anchor="middle" font-size="26" font-weight="500" fill="#A78BFA" font-family="DM Mono,monospace" letter-spacing="-1">{{ approvalProgress }}%</text>
            <text x="70" y="78" text-anchor="middle" font-size="10" fill="#4A505A" font-family="DM Sans,sans-serif">{{ Number(approvalProgress) >= 100 ? '已完成' : '进行中' }}</text>
          </svg>
        </div>
        <div class="kpi-divider"></div>
        <div class="kpi-meta-row">
          <div class="kpi-meta">
            <div class="kpi-meta-label">已占用</div>
            <div class="kpi-meta-val violet">{{ budgetData?.occupied_total?.toFixed(2) || '0.00' }}</div>
            <div class="kpi-meta-unit">万元</div>
          </div>
          <div class="kpi-meta">
            <div class="kpi-meta-label">预占用</div>
            <div class="kpi-meta-val muted">{{ budgetData?.preoccupied_total?.toFixed(2) || '0.00' }}</div>
            <div class="kpi-meta-unit">万元</div>
          </div>
        </div>
        <div class="kpi-date">📅 {{ normalizedBudgetDate || '—' }}</div>
      </div>

      <!-- 卡2：当期资本性支出进度 -->
      <div class="card kpi-card c-cyan">
        <div class="kpi-top">
          <div class="kpi-icon cyan">💰</div>
          <div class="kpi-badge badge-cyan">当期</div>
        </div>
        <div class="kpi-name">当期资本性支出进度</div>
        <div class="gauge-wrap">
          <svg width="140" height="80" viewBox="0 0 140 80">
            <path d="M15 75 A55 55 0 0 1 125 75" fill="none" stroke="rgba(34,211,238,0.1)" stroke-width="8" stroke-linecap="round"/>
            <path class="gauge-arc" d="M15 75 A55 55 0 0 1 125 75" fill="none" stroke="url(#g-cyan)" stroke-width="8" stroke-linecap="round"
              stroke-dasharray="172.8" :stroke-dashoffset="dashOffset(capitalProgress)"/>
            <defs>
              <linearGradient id="g-cyan" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#0891B2"/>
                <stop offset="100%" stop-color="#22D3EE"/>
              </linearGradient>
            </defs>
            <text x="70" y="62" text-anchor="middle" font-size="26" font-weight="500" fill="#22D3EE" font-family="DM Mono,monospace" letter-spacing="-1">{{ capitalProgress }}%</text>
            <text x="70" y="78" text-anchor="middle" font-size="10" fill="#4A505A" font-family="DM Sans,sans-serif">{{ Number(capitalProgress) >= 100 ? '已完成' : '进行中' }}</text>
          </svg>
        </div>
        <div class="kpi-divider"></div>
        <div class="kpi-meta-row">
          <div class="kpi-meta">
            <div class="kpi-meta-label">已完成</div>
            <div class="kpi-meta-val cyan">{{ zaigongData?.metrics?.capital?.toFixed(2) || '0.00' }}</div>
            <div class="kpi-meta-unit">万元</div>
          </div>
          <div class="kpi-meta">
            <div class="kpi-meta-label">目标</div>
            <div class="kpi-meta-val muted">{{ displayTargetValue }}</div>
            <div class="kpi-meta-unit">万元</div>
          </div>
        </div>
        <div class="kpi-date">📅 {{ normalizedZaigongDate || '—' }}</div>
      </div>

      <!-- 卡3：全年资本性支出进度 -->
      <div class="card kpi-card c-blue">
        <div class="kpi-top">
          <div class="kpi-icon blue">📈</div>
          <div class="kpi-badge badge-blue">全年</div>
        </div>
        <div class="kpi-name">全年资本性支出进度</div>
        <div class="gauge-wrap">
          <svg width="140" height="80" viewBox="0 0 140 80">
            <path d="M15 75 A55 55 0 0 1 125 75" fill="none" stroke="rgba(96,165,250,0.1)" stroke-width="8" stroke-linecap="round"/>
            <path class="gauge-arc" d="M15 75 A55 55 0 0 1 125 75" fill="none" stroke="url(#g-blue)" stroke-width="8" stroke-linecap="round"
              stroke-dasharray="172.8" :stroke-dashoffset="dashOffset(annualCapitalProgress)"/>
            <defs>
              <linearGradient id="g-blue" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#1D4ED8"/>
                <stop offset="100%" stop-color="#60A5FA"/>
              </linearGradient>
            </defs>
            <text x="70" y="62" text-anchor="middle" font-size="26" font-weight="500" fill="#60A5FA" font-family="DM Mono,monospace" letter-spacing="-1">{{ annualCapitalProgress }}%</text>
            <text x="70" y="78" text-anchor="middle" font-size="10" fill="#4A505A" font-family="DM Sans,sans-serif">年度支出</text>
          </svg>
        </div>
        <div class="kpi-divider"></div>
        <div class="kpi-meta-row">
          <div class="kpi-meta">
            <div class="kpi-meta-label">年度支出</div>
            <div class="kpi-meta-val blue">{{ budgetData?.annual_spend_total?.toFixed(2) || '0.00' }}</div>
            <div class="kpi-meta-unit">万元</div>
          </div>
          <div class="kpi-meta">
            <div class="kpi-meta-label">年度预算</div>
            <div class="kpi-meta-val muted">{{ budgetData?.budget_total?.toFixed(2) || '0.00' }}</div>
            <div class="kpi-meta-unit">万元</div>
          </div>
        </div>
        <div class="kpi-date">📅 {{ normalizedBudgetDate || '—' }}</div>
      </div>

      <!-- 卡4：综合转固率 -->
      <div class="card kpi-card c-red">
        <div class="kpi-top">
          <div class="kpi-icon red">⚡</div>
          <div class="kpi-badge badge-red" :class="{ 'badge-amber': rateStatusClass !== 'danger' }">
            {{ rateStatusClass === 'danger' ? '⚠ 转固率异常' : (rateStatusClass === 'warning' ? '转固率偏低' : '转固率正常') }}
          </div>
        </div>
        <div class="kpi-name">综合转固率</div>
        <div class="gauge-wrap">
          <svg width="140" height="80" viewBox="0 0 140 80">
            <path d="M15 75 A55 55 0 0 1 125 75" fill="none" stroke="rgba(248,113,113,0.1)" stroke-width="8" stroke-linecap="round"/>
            <path class="gauge-arc" d="M15 75 A55 55 0 0 1 125 75" fill="none" stroke="url(#g-red)" stroke-width="8" stroke-linecap="round"
              stroke-dasharray="172.8" :stroke-dashoffset="dashOffset(transferRate)"/>
            <defs>
              <linearGradient id="g-red" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#991B1B"/>
                <stop offset="100%" stop-color="#F87171"/>
              </linearGradient>
            </defs>
            <!-- 目标标记 -->
            <line v-if="transferRate < 60" x1="121" y1="43" x2="125" y2="37" stroke="rgba(251,191,36,0.6)" stroke-width="1.5" stroke-linecap="round"/>
            <text x="70" y="62" text-anchor="middle" font-size="26" font-weight="500" fill="#F87171" font-family="DM Mono,monospace" letter-spacing="-1">{{ transferRate }}%</text>
            <text x="70" y="78" text-anchor="middle" font-size="10" fill="#4A505A" font-family="DM Sans,sans-serif">转固</text>
          </svg>
        </div>
        <div class="kpi-divider"></div>
        <div class="kpi-meta-row">
          <div class="kpi-meta">
            <div class="kpi-meta-label">当前转固率</div>
            <div class="kpi-meta-val red">{{ transferRate }}%</div>
            <div class="kpi-meta-unit">当期</div>
          </div>
          <div class="kpi-meta">
            <div class="kpi-meta-label">年度目标</div>
            <div class="kpi-meta-val amber">60.0%</div>
            <div class="kpi-meta-unit">{{ Number(transferRate) >= 60 ? '已达标' : `差距 ${(60 - Number(transferRate)).toFixed(1)}pct` }}</div>
          </div>
        </div>
        <div class="kpi-date">📅 {{ normalizedZaigongDate || '—' }}</div>
      </div>
    </div>

    <!-- 底部全宽 -->
    <div class="bottom-grid">
      <!-- 近期重点工作 -->
      <div class="card todo-card">
        <div class="section-head">
          <div class="section-title-group">
            <span class="section-tag tag-todo">TODO</span>
            <span class="section-title">近期重点工作</span>
          </div>
          <div class="section-actions">
            <button class="todo-add-btn" @click="openAddModal">+ 添加</button>
          </div>
        </div>

        <div v-if="sortedWorkItems.length === 0" class="ai-empty">
          <p>暂无自定义重点工作</p>
        </div>
        <div class="todo-list" v-else>
          <div class="todo-item" v-for="item in sortedWorkItems" :key="item.id" :class="{ completed: item.status === 'completed' }">
            <div class="todo-item-head">
              <span class="todo-priority" :class="'priority-' + item.level">{{ item.levelText }}</span>
              <span class="todo-owner" v-if="item.owner">责任人：{{ item.owner }}</span>
              <span class="todo-due">{{ item.dueDate }}</span>
            </div>
            <div class="todo-title">{{ item.content }}</div>
            <div class="todo-actions" v-if="item.status !== 'completed' && !presentationMode">
              <button @click="openEditModal(item)">编辑</button>
              <button class="danger" @click="deleteItem(item.id)">删除</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 新增/编辑弹窗 -->
    <div v-if="modalVisible" class="modal-overlay" @click.self="closeModal">
      <div class="modal-panel">
        <div class="modal-header">
          <h4>{{ modalMode === 'add' ? '添加重点工作' : '编辑重点工作' }}</h4>
          <button @click="closeModal">×</button>
        </div>
        <div class="modal-body">
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
          <div v-if="formError" class="form-error">{{ formError }}</div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="closeModal">取消</button>
          <button class="btn-save" @click="saveItem">保存</button>
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
/* CSS 变量 */
.key-indicators {
  --bg-deep: #080C12;
  --glass: rgba(255,255,255,0.04);
  --glass-2: rgba(255,255,255,0.07);
  --border-dim: rgba(255,255,255,0.07);
  --border-glow: rgba(255,255,255,0.14);
  --text-1: #F0F2F5;
  --text-2: #8B9099;
  --text-3: #4A505A;
  --cyan: #22D3EE;
  --cyan-dim: rgba(34,211,238,0.12);
  --blue: #60A5FA;
  --blue-dim: rgba(96,165,250,0.12);
  --violet: #A78BFA;
  --violet-dim: rgba(167,139,250,0.12);
  --amber: #FBBF24;
  --amber-dim: rgba(251,191,36,0.12);
  --red: #F87171;
  --red-dim: rgba(248,113,113,0.14);
  --green: #34D399;
  --green-dim: rgba(52,211,153,0.12);
  --font: 'DM Sans', system-ui, sans-serif;
  --mono: 'DM Mono', 'Courier New', monospace;
}

/* 整体布局 */
.key-indicators {
  position: relative;
  min-height: 100vh;
  background: var(--bg-deep);
  font-family: var(--font);
  display: flex;
  flex-direction: column;
  padding: 20px 28px 28px;
  gap: 18px;
}

/* 全屏展示模式 - 去掉留白 */
.key-indicators.fullscreen-mode {
  position: fixed;
  inset: 0;
  z-index: 9999;
  padding: 0;
  gap: 0;
  min-height: 100vh;
  min-width: 100vw;
}

.key-indicators.fullscreen-mode .nav {
  padding: 12px 24px;
  background: rgba(8, 12, 18, 0.9);
}

.key-indicators.fullscreen-mode .kpi-grid {
  flex: 1;
  padding: 16px 24px;
  align-content: center;
}

.key-indicators.fullscreen-mode .bottom-grid {
  padding: 0 24px 16px;
}

/* 背景光晕 */
.bg-mesh {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(ellipse 60% 50% at 20% 10%, rgba(96,165,250,0.07) 0%, transparent 70%),
    radial-gradient(ellipse 50% 40% at 80% 80%, rgba(34,211,238,0.06) 0%, transparent 70%),
    radial-gradient(ellipse 40% 30% at 60% 30%, rgba(167,139,250,0.05) 0%, transparent 70%);
}

/* 导航栏 */
.nav {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  height: 44px;
}

.nav-brand { display: flex; align-items: center; gap: 10px; }
.nav-mark {
  width: 32px; height: 32px; border-radius: 9px;
  background: linear-gradient(135deg, #60A5FA 0%, #22D3EE 100%);
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 500; color: #fff;
  font-family: var(--mono); letter-spacing: 0.3px;
  box-shadow: 0 0 16px rgba(34,211,238,0.3);
}
.nav-title { font-size: 18px; font-weight: 500; color: var(--text-1); letter-spacing: -0.3px; }
.nav-center { flex: 1; display: flex; justify-content: center; }
.nav-date {
  font-size: 12px; color: var(--text-2); font-family: var(--mono);
  display: flex; align-items: center; gap: 6px;
}
.nav-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--green); box-shadow: 0 0 6px var(--green); }
.nav-end { display: flex; align-items: center; gap: 8px; }
.nav-chip {
  padding: 5px 13px; border-radius: 20px; font-size: 12px;
  border: 0.5px solid var(--border-glow); color: var(--text-2);
  background: var(--glass); cursor: pointer; transition: all .2s;
  display: flex; align-items: center; gap: 5px; font-family: var(--font);
}
.nav-chip:hover { background: var(--glass-2); color: var(--text-1); }
.nav-chip.exit { border-color: rgba(96,165,250,0.3); color: var(--blue); background: var(--blue-dim); }

/* 玻璃卡片基础 */
.card {
  background: var(--glass);
  border: 0.5px solid var(--border-dim);
  border-radius: 16px;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  position: relative;
  overflow: hidden;
  transition: border-color .3s;
}
.card::before {
  content: '';
  position: absolute; inset: 0; border-radius: 16px; pointer-events: none;
  background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, transparent 60%);
}
.card:hover { border-color: var(--border-glow); }

/* KPI 网格 */
.kpi-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.kpi-card { padding: 22px 22px 18px; }
.kpi-card::after {
  content: '';
  position: absolute; top: 0; left: 0; right: 0;
  height: 2px; border-radius: 16px 16px 0 0;
}
.kpi-card.c-violet::after { background: linear-gradient(90deg, transparent, var(--violet), transparent); }
.kpi-card.c-cyan::after { background: linear-gradient(90deg, transparent, var(--cyan), transparent); }
.kpi-card.c-blue::after { background: linear-gradient(90deg, transparent, var(--blue), transparent); }
.kpi-card.c-red::after { background: linear-gradient(90deg, transparent, var(--red), transparent); }

.kpi-top {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px;
}
.kpi-icon {
  width: 30px; height: 30px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center; font-size: 14px;
}
.kpi-icon.violet { background: var(--violet-dim); }
.kpi-icon.cyan { background: var(--cyan-dim); }
.kpi-icon.blue { background: var(--blue-dim); }
.kpi-icon.red { background: var(--red-dim); }

.kpi-badge {
  font-size: 10px; font-weight: 500; padding: 2px 8px;
  border-radius: 10px; white-space: nowrap;
  display: flex; align-items: center; gap: 4px;
}
.badge-violet { background: var(--violet-dim); color: var(--violet); border: 0.5px solid rgba(167,139,250,0.25); }
.badge-cyan { background: var(--cyan-dim); color: var(--cyan); border: 0.5px solid rgba(34,211,238,0.25); }
.badge-blue { background: var(--blue-dim); color: var(--blue); border: 0.5px solid rgba(96,165,250,0.25); }
.badge-red { background: var(--red-dim); color: var(--red); border: 0.5px solid rgba(248,113,113,0.3); animation: pulse-red 2s ease-in-out infinite; }
.badge-amber { background: var(--amber-dim); color: var(--amber); border: 0.5px solid rgba(251,191,36,0.25); animation: none; }

@keyframes pulse-red {
  0%,100% { box-shadow: 0 0 0 0 rgba(248,113,113,0); }
  50% { box-shadow: 0 0 0 3px rgba(248,113,113,0.15); }
}

.kpi-name { font-size: 12px; color: var(--text-2); margin-bottom: 10px; letter-spacing: 0.2px; }

.gauge-wrap { display: flex; justify-content: center; margin-bottom: 14px; }
.kpi-divider { height: 0.5px; background: var(--border-dim); margin: 14px 0; }

.kpi-meta-row { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.kpi-meta { background: rgba(255,255,255,0.03); border-radius: 8px; padding: 8px 10px; }
.kpi-meta-label { font-size: 10px; color: var(--text-3); margin-bottom: 4px; }
.kpi-meta-val { font-size: 14px; font-weight: 500; font-family: var(--mono); letter-spacing: -0.3px; }
.kpi-meta-val.violet { color: var(--violet); }
.kpi-meta-val.cyan { color: var(--cyan); }
.kpi-meta-val.blue { color: var(--blue); }
.kpi-meta-val.red { color: var(--red); }
.kpi-meta-val.amber { color: var(--amber); }
.kpi-meta-val.muted { color: var(--text-2); }
.kpi-meta-unit { font-size: 10px; color: var(--text-3); margin-top: 1px; }

.kpi-date { font-size: 11px; color: var(--text-3); font-family: var(--mono); margin-top: 12px; }

/* 底部网格 */
.bottom-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
  flex: 1;
}

/* 卡片头部 */
.section-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.section-title-group { display: flex; align-items: center; gap: 8px; }
.section-tag {
  font-size: 9px; font-weight: 500; padding: 2px 7px; border-radius: 4px;
  text-transform: uppercase; letter-spacing: 0.6px;
}
.tag-todo { background: var(--violet-dim); color: var(--violet); border: 0.5px solid rgba(167,139,250,0.2); }
.section-title { font-size: 14px; font-weight: 500; color: var(--text-1); }
.section-actions { display: flex; align-items: center; gap: 6px; }

.ai-message {
  padding: 14px 16px; border-radius: 10px; font-size: 12px;
  display: flex; align-items: center; gap: 10px;
}
.ai-message svg { width: 16px; height: 16px; flex-shrink: 0; }
.ai-message.info { background: rgba(34,211,238,0.08); border: 0.5px solid rgba(34,211,238,0.2); color: var(--cyan); }
.ai-message.error { background: rgba(248,113,113,0.08); border: 0.5px solid rgba(248,113,113,0.2); color: var(--red); }

/* TODO 卡片 */
.todo-card { padding: 20px 22px; display: flex; flex-direction: column; }
.todo-add-btn {
  padding: 4px 11px; border-radius: 6px; font-size: 11px;
  background: var(--violet-dim); color: var(--violet);
  border: 0.5px solid rgba(167,139,250,0.3);
  cursor: pointer; font-family: var(--font); transition: all .2s;
}
.todo-add-btn:hover { background: rgba(167,139,250,0.2); }

.todo-list { flex: 1; display: flex; flex-direction: column; gap: 10px; }
.todo-item {
  border: 0.5px solid var(--border-dim);
  border-radius: 10px; padding: 12px 14px;
  background: rgba(255,255,255,0.025);
  transition: border-color .2s;
}
.todo-item:hover { border-color: var(--border-glow); }
.todo-item.completed { opacity: 0.6; }
.todo-item-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.todo-priority { font-size: 10px; font-weight: 500; padding: 2px 7px; border-radius: 4px; margin-right: 10px; }
.priority-urgent { background: var(--red-dim); color: var(--red); border: 0.5px solid rgba(248,113,113,0.25); }
.priority-high { background: var(--amber-dim); color: var(--amber); border: 0.5px solid rgba(251,191,36,0.25); }
.priority-normal { background: var(--green-dim); color: var(--green); border: 0.5px solid rgba(52,211,153,0.25); }
.todo-due { font-size: 10px; color: var(--text-1); margin-left: auto; }
.todo-owner { font-size: 10px; color: var(--red); font-weight: 500; }
.todo-title { font-size: 13px; font-weight: 500; color: var(--text-1); margin-bottom: 4px; line-height: 1.4; }
.todo-desc { font-size: 11px; color: var(--text-3); line-height: 1.5; }
.todo-actions { display: flex; gap: 8px; margin-top: 8px; }
.todo-actions button {
  height: 26px; padding: 0 10px; border-radius: 6px;
  border: 0.5px solid var(--border-dim); background: var(--glass);
  color: var(--text-2); font-size: 11px; cursor: pointer; font-family: var(--font);
}
.todo-actions button.danger { border-color: rgba(248,113,113,0.3); color: var(--red); }
.todo-actions button:hover { background: var(--glass-2); }

.ai-message {
  padding: 14px 16px; border-radius: 10px; font-size: 12px;
  display: flex; align-items: center; gap: 10px;
}
.ai-message svg { width: 16px; height: 16px; flex-shrink: 0; }
.ai-message.info { background: rgba(34,211,238,0.08); border: 0.5px solid rgba(34,211,238,0.2); color: var(--cyan); }
.ai-message.error { background: rgba(248,113,113,0.08); border: 0.5px solid rgba(248,113,113,0.2); color: var(--red); }
.ai-empty { text-align: center; color: var(--text-3); padding: 24px 12px; font-size: 12px; }

/* 弹窗 */
.modal-overlay {
  position: fixed; inset: 0; z-index: 1300;
  background: rgba(0,0,0,0.6);
  display: grid; place-items: center;
  backdrop-filter: blur(4px);
}
.modal-panel {
  width: min(480px, 92vw); border-radius: 16px;
  border: 0.5px solid var(--border-dim);
  background: linear-gradient(145deg, rgba(15,22,36,0.98), rgba(10,16,28,0.98));
  overflow: hidden;
}
.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 0.5px solid var(--border-dim);
}
.modal-header h4 { color: var(--text-1); font-size: 16px; }
.modal-header button {
  width: 28px; height: 28px; border: none; border-radius: 6px;
  background: var(--glass); color: var(--text-2); font-size: 18px; cursor: pointer;
}
.modal-body { padding: 18px 20px; display: grid; gap: 12px; }
.modal-body label { font-size: 12px; color: var(--text-2); }
.modal-body input,
.modal-body textarea,
.modal-body select {
  width: 100%; border-radius: 8px; border: 0.5px solid var(--border-dim);
  background: rgba(255,255,255,0.04); color: var(--text-1);
  padding: 10px 12px; font: inherit; font-size: 13px;
}
.modal-body select { cursor: pointer; }
.form-error { color: var(--red); font-size: 12px; }
.modal-footer { padding: 0 20px 18px; display: flex; justify-content: flex-end; gap: 10px; }
.btn-cancel, .btn-save { height: 34px; padding: 0 14px; border-radius: 8px; font-size: 13px; cursor: pointer; }
.btn-cancel { border: 0.5px solid var(--border-dim); background: transparent; color: var(--text-2); }
.btn-save { border: none; background: linear-gradient(135deg, var(--cyan), var(--blue)); color: #fff; font-weight: 500; }

/* 动画 */
@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.kpi-card { animation: fadeSlideUp .5s ease both; }
.kpi-card:nth-child(1) { animation-delay: .05s; }
.kpi-card:nth-child(2) { animation-delay: .12s; }
.kpi-card:nth-child(3) { animation-delay: .19s; }
.kpi-card:nth-child(4) { animation-delay: .26s; }
.bottom-grid { animation: fadeSlideUp .5s .35s ease both; }

/* 圆环：无动画，直接显示计算后的值 */
/* stroke-dashoffset 由 Vue 绑定计算值 */

/* 响应式 */
@media (max-width: 1200px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .bottom-grid { grid-template-columns: 1fr; }
}

@media (max-width: 640px) {
  .key-indicators { padding: 16px 16px 20px; gap: 14px; }
  .kpi-grid { grid-template-columns: 1fr; }
  .nav-title { font-size: 16px; }
  .nav-center { display: none; }
}

/* 滚动条 */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }

</style>
