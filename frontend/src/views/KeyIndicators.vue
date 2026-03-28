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
              stroke-dasharray="251" :stroke-dashoffset="dashOffset(approvalProgress)"/>
            <defs>
              <linearGradient id="g-violet" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#7C3AED"/>
                <stop offset="100%" stop-color="#A78BFA"/>
              </linearGradient>
            </defs>
            <text x="70" y="62" text-anchor="middle" font-size="26" font-weight="500" fill="#A78BFA" font-family="DM Mono,monospace" letter-spacing="-1">{{ approvalProgress }}%</text>
            <text x="70" y="78" text-anchor="middle" font-size="10" fill="#4A505A" font-family="DM Sans,sans-serif">完成</text>
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
              stroke-dasharray="251" :stroke-dashoffset="dashOffset(capitalProgress)"/>
            <defs>
              <linearGradient id="g-cyan" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#0891B2"/>
                <stop offset="100%" stop-color="#22D3EE"/>
              </linearGradient>
            </defs>
            <text x="70" y="62" text-anchor="middle" font-size="26" font-weight="500" fill="#22D3EE" font-family="DM Mono,monospace" letter-spacing="-1">{{ capitalProgress }}%</text>
            <text x="70" y="78" text-anchor="middle" font-size="10" fill="#4A505A" font-family="DM Sans,sans-serif">完成</text>
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
              stroke-dasharray="251" :stroke-dashoffset="dashOffset(annualCapitalProgress)"/>
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
              stroke-dasharray="251" :stroke-dashoffset="dashOffset(transferRate)"/>
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
            <div class="kpi-meta-unit">差距 {{ (60 - transferRate).toFixed(1) }}pct</div>
          </div>
        </div>
        <div class="kpi-date">📅 {{ normalizedZaigongDate || '—' }}</div>
      </div>
    </div>

    <!-- 底部双栏 -->
    <div class="bottom-grid">
      <!-- AI 工程进度分析 -->
      <div class="card ai-card">
        <div class="section-head">
          <div class="section-title-group">
            <span class="section-tag tag-ai">AI</span>
            <span class="section-title">工程进度分析</span>
          </div>
          <div class="section-actions">
            <button class="action-btn" :class="{ active: aiMode === 'management' }" @click="switchAIMode('management')">管理汇报版</button>
            <button class="action-btn" :class="{ active: aiMode === 'execution' }" @click="switchAIMode('execution')">执行推进版</button>
            <button class="refresh-btn" @click="refreshAIAnalysis" :disabled="aiAnalysisLoading || !aiConfigured">
              <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
                <path d="M9 5.5A3.5 3.5 0 1 1 5.5 2a3.5 3.5 0 0 1 2.5 1.04" stroke="currentColor" stroke-width="1.1" stroke-linecap="round"/>
                <path d="M8 1v2.5H5.5" stroke="currentColor" stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              {{ aiAnalysisLoading ? '分析中...' : '刷新分析' }}
            </button>
          </div>
        </div>

        <div class="ai-timestamp" v-if="aiAnalysisGeneratedAt">生成于 {{ new Date(aiAnalysisGeneratedAt).toLocaleString('zh-CN') }}</div>

        <div v-if="!aiConfigured" class="ai-message error">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span>AI 服务未配置，请先配置后端 MiniMax 环境变量</span>
        </div>
        <div v-else-if="aiAnalysisError" class="ai-message" :class="aiMessageTone">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span>{{ aiAnalysisError }}</span>
        </div>
        <div v-else-if="!aiAnalysisContent" class="ai-empty">
          <p>点击"刷新分析"生成 AI 分析报告</p>
        </div>
        <div v-else class="ai-content-v2">
          <!-- ① 状态行 -->
          <div class="ai-status-bar">
            <div class="ai-status-left">
              <div class="ai-status-dot" :style="{ background: overallStatus.color, boxShadow: `0 0 8px ${overallStatus.color}` }"></div>
              <span class="ai-status-label" :style="{ color: overallStatus.color }">{{ overallStatus.label }}</span>
              <span class="ai-status-divider">·</span>
              <span class="ai-status-summary">{{ summaryOneLiner }}</span>
            </div>
            <span class="ai-timestamp-v2" v-if="aiAnalysisGeneratedAt">{{ new Date(aiAnalysisGeneratedAt).toLocaleString('zh-CN') }}</span>
          </div>

          <!-- ② 三格指标 -->
          <div class="ai-metrics-v2">
            <div class="ai-metric-v2">
              <div class="ai-metric-header">
                <span class="ai-metric-label-v2">进度评估</span>
                <span class="ai-metric-num" style="color:#60A5FA">{{ progressKeyNum }}</span>
              </div>
              <div class="ai-metric-text">{{ sanitizeAIContent(aiResult.progress || '').slice(0, 50) }}{{ (aiResult.progress || '').length > 50 ? '…' : '' }}</div>
            </div>

            <div class="ai-metric-v2">
              <div class="ai-metric-header">
                <span class="ai-metric-label-v2">支出分析</span>
                <span class="ai-metric-num" style="color:#22D3EE">{{ expendKeyInfo }}</span>
              </div>
              <div class="ai-metric-text">{{ sanitizeAIContent(aiResult.spend || '').slice(0, 50) }}{{ (aiResult.spend || '').length > 50 ? '…' : '' }}</div>
            </div>

            <div class="ai-metric-v2" :class="{ 'metric-danger': isHighRisk }">
              <div class="ai-metric-header">
                <span class="ai-metric-label-v2">风险预警</span>
                <span v-if="isHighRisk" class="ai-risk-badge">高风险</span>
              </div>
              <div class="ai-metric-text" :style="{ color: isHighRisk ? '#F87171' : 'var(--text-2)' }">
                {{ riskKeyText }}
              </div>
            </div>
          </div>

          <!-- ③ 重点动作 -->
          <div class="ai-actions-v2" v-if="parsedActions.length">
            <div class="ai-actions-header">重点动作</div>
            <div class="ai-action-list">
              <div
                v-for="(action, i) in parsedActions"
                :key="i"
                class="ai-action-item-v2"
                :title="action.fullText"
              >
                <span class="ai-priority-tag" :style="{ color: action.priority.color, background: action.priority.bg, border: `0.5px solid ${action.priority.color}40` }">
                  {{ action.priority.label }}
                </span>
                <span class="ai-action-text">{{ action.text }}</span>
                <div class="ai-person-chips" v-if="action.persons.length">
                  <span v-for="person in action.persons" :key="person" class="ai-person-chip">{{ person }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

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
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { generateAIAnalysis, getAIStatus } from '../api'

const props = defineProps({
  zaigongData: Object,
  budgetData: Object,
  zaigongDate: String,
  budgetDate: String
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
  const num = parseFloat(value) || 0
  return Math.round(251 * (1 - num / 100))
}

// AI 分析相关
const aiConfigured = ref(false)
const aiAnalysisContent = ref('')
const aiAnalysisStructured = ref(null)
const aiAnalysisLoading = ref(false)
const aiAnalysisError = ref('')
const aiAnalysisGeneratedAt = ref('')
const aiCacheKey = 'ai_analysis_cache_v2'
const aiMode = ref('management')

// AI 结果中文别名，兼容模板中的中文键名
const aiResult = computed(() => aiAnalysisStructured.value || {})

const aiMessageTone = computed(() => {
  const text = String(aiAnalysisError.value || '')
  if (text.includes('数据已更新') || text.includes('分析风格已切换')) return 'info'
  return 'error'
})

const parsedAISections = computed(() => {
  const source = String(aiAnalysisContent.value || '').trim()
  if (!source) return []
  const lines = source.split('\n').map(line => line.trim()).filter(Boolean)
  const sections = []
  for (const line of lines) {
    const matched = line.match(/^\*\*(.+?)\*\*[：:]\s*(.+)$/)
    if (matched) {
      sections.push({ title: matched[1].trim(), content: matched[2].trim() })
    }
  }
  return sections
})

// 处理 AI 返回内容中的"差距 0.00 万元"等不合理表述
function sanitizeAIContent(text) {
  if (!text) return text
  // 差距为0时，替换为"已达标"或"无需补充"
  return text
    .replace(/差距\s*0\.?\d*\s*万元/g, '已达标')
    .replace(/缺口\s*0\.?\d*\s*万元/g, '已达标')
    .replace(/单月至少完成\s*0\.?\d*\s*万元/g, '已完成目标')
    .replace(/剩余\s*0\.?\d*\s*万元/g, '已完成')
}

const displayAISections = computed(() => {
  const structured = aiAnalysisStructured.value || {}
  const mapping = [
    ['综合评估', structured.overall],
    ['进度评估', structured.progress],
    ['支出分析', structured.spend],
    ['转固率分析', structured.rate],
    ['风险预警', structured.risk],
    ['下月预测', structured.next_month]
  ]
  const sections = mapping.filter(([, content]) => String(content || '').trim())
    .map(([title, content]) => ({ title, content: sanitizeAIContent(String(content).trim()) }))
  if (sections.length) return sections
  return parsedAISections.value.map(s => ({ ...s, content: sanitizeAIContent(s.content) }))
})

const aiActionItems = computed(() => {
  const actions = aiAnalysisStructured.value?.actions
  if (!Array.isArray(actions)) return []
  return actions.map(item => sanitizeAIContent(String(item || '').trim())).filter(Boolean)
})

// ── AI 分析 V2 新增计算属性 ──

// 整体状态等级
const overallStatus = computed(() => {
  const text = aiResult.value?.overall || ''
  const pctMatch = text.match(/(\d+\.?\d*)%/)
  const pct = pctMatch ? parseFloat(pctMatch[1]) : 0
  if (text.includes('超额') || pct > 100) {
    return { level: 'good', label: '进度良好', color: '#34D399' }
  }
  if (text.includes('高风险') || text.includes('偏低') || text.includes('预警')) {
    return { level: 'warn', label: '需要关注', color: '#FBBF24' }
  }
  if (text.includes('严重') || text.includes('风险极高')) {
    return { level: 'danger', label: '立即处理', color: '#F87171' }
  }
  return { level: 'normal', label: '正常推进', color: '#60A5FA' }
})

// 综合评估一句话摘要
const summaryOneLiner = computed(() => {
  const text = aiResult.value?.overall || ''
  const parts = text.split(/[，,]/)
  const first = parts.slice(0, 2).join('，')
  return first.length > 42 ? first.slice(0, 40) + '…' : first
})

// 是否高风险
const isHighRisk = computed(() => {
  const text = aiResult.value?.risk || ''
  return text.includes('高风险') || text.includes('高 风险')
})

// 解析重点动作：优先级 + 截断 + 责任人提取
const parsedActions = computed(() => {
  return (aiResult.value?.actions || []).map((action, i) => {
    const actionStr = String(action || '')
    // 提取中文人名（2-3个汉字）
    const persons = actionStr.match(/[\u4e00-\u9fa5]{2,3}(?=[、；;]|负责|跟进|督促)/g) || []
    const priority = i === 0
      ? { label: '紧急', color: '#F87171', bg: 'rgba(248,113,113,0.12)' }
      : i === 1
      ? { label: '重要', color: '#FBBF24', bg: 'rgba(251,191,36,0.12)' }
      : { label: '跟进', color: '#34D399', bg: 'rgba(52,211,153,0.12)' }
    const shortText = actionStr.length > 34 ? actionStr.slice(0, 32) + '…' : actionStr
    return { text: shortText, fullText: actionStr, persons, priority }
  })
})

// 进度评估关键数字
const progressKeyNum = computed(() => {
  const text = aiResult.value?.progress || ''
  const match = text.match(/([+-]?\d+\.?\d*pct|[+-]?\d+\.?\d*%)/)
  return match ? match[1] : '—'
})

// 支出分析关键金额
const expendKeyInfo = computed(() => {
  const text = aiResult.value?.spend || ''
  const match = text.match(/(\d+\.?\d*)\s*万元/)
  return match ? match[1] + '万' : '—'
})

// 风险预警关键内容
const riskKeyText = computed(() => {
  const text = aiResult.value?.risk || ''
  return text.slice(0, 50) + (text.length > 50 ? '…' : '')
})

const riskMetrics = computed(() => {
  const metrics = []
  const progress = displayAISections.value.find(s => s.title === '进度评估')
  if (progress) {
    metrics.push({ label: '进度评估', content: progress.content, isRisk: false })
  }
  const spend = displayAISections.value.find(s => s.title === '支出分析')
  if (spend) {
    metrics.push({ label: '支出分析', content: spend.content, isRisk: false })
  }
  const risk = displayAISections.value.find(s => s.title === '风险预警')
  if (risk) {
    metrics.push({ label: '风险预警', content: risk.content, isRisk: true })
  }
  return metrics
})

function renderAIHighlight(text) {
  return text.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
}

function switchAIMode(mode) {
  if (mode === aiMode.value) return
  aiMode.value = mode
  if (aiAnalysisContent.value) {
    aiAnalysisError.value = '分析风格已切换，请点击刷新'
  }
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

// AI 分析
function buildAISnapshotHash() {
  const metrics = props.zaigongData?.metrics || {}
  const budget = props.budgetData || {}
  return JSON.stringify({
    yearTarget: Number(metrics.yearTarget || 0),
    capital: Number(metrics.capital || 0),
    pending: Number(metrics.pending || 0),
    rate: Number(metrics.rate || 0),
    budgetTotal: Number(budget.budget_total || 0),
    approvalProgress: Number(budget.approval_progress || 0),
    annualSpendTotal: Number(budget.annual_spend_total || 0)
  })
}

function saveAICache(content, structured, generatedAt, mode) {
  localStorage.setItem(aiCacheKey, JSON.stringify({
    content, structured, generatedAt, mode,
    snapshotHash: buildAISnapshotHash()
  }))
}

function isCacheStale() {
  try {
    const cache = JSON.parse(localStorage.getItem(aiCacheKey) || '{}')
    if (!cache.snapshotHash) return true
    if (cache.mode !== aiMode.value) return true
    return cache.snapshotHash !== buildAISnapshotHash()
  } catch { return true }
}

function loadAICache() {
  try {
    const cache = JSON.parse(localStorage.getItem(aiCacheKey) || '{}')
    if (!cache.content) return
    aiAnalysisStructured.value = cache.structured || null
    aiAnalysisContent.value = cache.content || ''
    aiAnalysisGeneratedAt.value = cache.generatedAt || ''
    if (isCacheStale()) {
      aiAnalysisError.value = '数据已更新，请点击刷新'
    }
  } catch {}
}

async function checkAIStatus() {
  try {
    const status = await getAIStatus()
    aiConfigured.value = Boolean(status?.success && status?.data?.configured)
  } catch {
    aiConfigured.value = false
  }
}

function buildAIRequestPayload() {
  const metrics = props.zaigongData?.metrics || {}
  const budget = props.budgetData || {}
  return {
    metrics: {
      year_target: Number(metrics.yearTarget || 0),
      total_current: Number(metrics.capital || 0),
      progress_pct: Number(metrics.progress || 0) * 100,
      month_spend: Number(metrics.monthSpend || 0),
      pending: Number(metrics.pending || 0),
      transfer_rate: Number(metrics.rate || 0)
    },
    summary: (props.zaigongData?.summary || [])
      .filter(r => (r.manager || r['工程管理员']) !== '合计')
      .map(r => ({
        manager: r.manager || r['工程管理员'],
        capital: Number(r.capital || r['本年累计资本性支出'] || 0),
        pending: Number(r.pending || r['已下单待收货'] || 0),
        rate: Number(r.rate || r['转固率'] || 0),
        month_spend: Number(r.monthSpend || r['本月资本性支出'] || 0),
        transfer: Number(r.transfer || r['结转额'] || 0)
      })),
    budget: {
      total_budget: Number(budget.budget_total || 0),
      approval_progress_pct: Number(budget.approval_progress || 0) * 100,
      annual_spend_total: Number(budget.annual_spend_total || 0),
      occupied_total: Number(budget.occupied_total || 0),
      preoccupied_total: Number(budget.preoccupied_total || 0)
    },
    analysis_date: normalizedZaigongDate.value || normalizedBudgetDate.value || '',
    style: aiMode.value
  }
}

async function refreshAIAnalysis() {
  if (!props.zaigongData?.metrics) {
    aiAnalysisError.value = '请先上传在建工程数据'
    return
  }
  if (!aiConfigured.value) {
    aiAnalysisError.value = 'AI 服务未配置'
    return
  }
  aiAnalysisLoading.value = true
  aiAnalysisError.value = ''
  try {
    const result = await generateAIAnalysis(buildAIRequestPayload())
    if (result?.success && result?.data?.content) {
      aiAnalysisContent.value = result.data.content
      aiAnalysisStructured.value = result.data.structured || null
      aiAnalysisGeneratedAt.value = result.data.generated_at || ''
      saveAICache(aiAnalysisContent.value, aiAnalysisStructured.value, aiAnalysisGeneratedAt.value, aiMode.value)
    } else {
      aiAnalysisError.value = result?.message || 'AI 分析生成失败'
    }
  } catch (error) {
    const backendMessage = error?.response?.data?.message
    aiAnalysisError.value = backendMessage || 'AI 服务调用失败，请稍后重试'
  } finally {
    aiAnalysisLoading.value = false
  }
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
  checkAIStatus()
  loadAICache()
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

.key-indicators.fullscreen-mode .ai-card {
  padding: 16px 20px;
}

.key-indicators.fullscreen-mode .ai-content-v2 {
  gap: 10px;
}

.key-indicators.fullscreen-mode .ai-metrics-v2 {
  gap: 10px;
}

.key-indicators.fullscreen-mode .ai-metric-v2 {
  padding: 10px 12px;
}

.key-indicators.fullscreen-mode .ai-metric-text {
  font-size: 11px;
  line-height: 1.4;
}

.key-indicators.fullscreen-mode .ai-actions-v2 {
  padding: 10px 12px;
}

.key-indicators.fullscreen-mode .ai-action-text {
  font-size: 11px;
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
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  flex: 1;
}

/* AI 卡片 */
.ai-card { padding: 20px 22px; display: flex; flex-direction: column; }
.section-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.section-title-group { display: flex; align-items: center; gap: 8px; }
.section-tag {
  font-size: 9px; font-weight: 500; padding: 2px 7px; border-radius: 4px;
  text-transform: uppercase; letter-spacing: 0.6px;
}
.tag-ai { background: var(--cyan-dim); color: var(--cyan); border: 0.5px solid rgba(34,211,238,0.2); }
.tag-todo { background: var(--violet-dim); color: var(--violet); border: 0.5px solid rgba(167,139,250,0.2); }
.section-title { font-size: 14px; font-weight: 500; color: var(--text-1); }
.section-actions { display: flex; align-items: center; gap: 6px; }

.action-btn {
  padding: 4px 11px; border-radius: 6px; font-size: 11px;
  border: 0.5px solid var(--border-dim); color: var(--text-2);
  background: var(--glass); cursor: pointer; font-family: var(--font); transition: all .2s;
}
.action-btn:hover { background: var(--glass-2); color: var(--text-1); border-color: var(--border-glow); }
.action-btn.active { background: var(--cyan-dim); color: var(--cyan); border-color: rgba(34,211,238,0.3); }
.refresh-btn {
  padding: 4px 11px; border-radius: 6px; font-size: 11px;
  background: var(--cyan-dim); color: var(--cyan);
  border: 0.5px solid rgba(34,211,238,0.3);
  cursor: pointer; font-family: var(--font); transition: all .2s;
  display: flex; align-items: center; gap: 5px;
}
.refresh-btn:hover { background: rgba(34,211,238,0.2); }
.refresh-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.ai-timestamp { font-size: 11px; color: var(--text-3); font-family: var(--mono); margin-bottom: 14px; }

.ai-content { flex: 1; display: flex; flex-direction: column; gap: 10px; }
.ai-summary { background: rgba(34,211,238,0.04); border: 0.5px solid rgba(34,211,238,0.12); border-radius: 10px; padding: 12px 14px; }
.ai-summary-label { font-size: 10px; color: var(--cyan); font-weight: 500; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 6px; }
.ai-summary-text { font-size: 12px; color: var(--text-2); line-height: 1.7; }
.ai-summary-text :deep(b) { color: var(--text-1); font-weight: 500; }

.ai-metrics-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.ai-metric { background: rgba(255,255,255,0.025); border: 0.5px solid var(--border-dim); border-radius: 8px; padding: 10px 12px; }
.ai-metric-label { font-size: 10px; color: var(--text-3); margin-bottom: 5px; letter-spacing: 0.3px; }
.ai-metric-val { font-size: 12px; color: var(--text-1); line-height: 1.5; }

.ai-actions-row { background: rgba(251,191,36,0.04); border: 0.5px solid rgba(251,191,36,0.12); border-radius: 10px; padding: 12px 14px; }
.ai-actions-label { font-size: 10px; color: var(--amber); font-weight: 500; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 8px; }
.ai-action-items { display: flex; flex-direction: column; gap: 5px; }
.ai-action-item { display: flex; align-items: flex-start; gap: 7px; font-size: 12px; color: var(--text-2); line-height: 1.5; }
.ai-action-num {
  width: 16px; height: 16px; border-radius: 4px; flex-shrink: 0;
  background: var(--amber-dim); color: var(--amber);
  font-size: 9px; font-weight: 500;
  display: flex; align-items: center; justify-content: center; margin-top: 1px;
}

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
@keyframes gaugeDraw {
  from { stroke-dashoffset: 251; }
}

.kpi-card { animation: fadeSlideUp .5s ease both; }
.kpi-card:nth-child(1) { animation-delay: .05s; }
.kpi-card:nth-child(2) { animation-delay: .12s; }
.kpi-card:nth-child(3) { animation-delay: .19s; }
.kpi-card:nth-child(4) { animation-delay: .26s; }
.bottom-grid { animation: fadeSlideUp .5s .35s ease both; }

.gauge-arc { animation: gaugeDraw .9s cubic-bezier(.4,0,.2,1) both; }
.kpi-card:nth-child(1) .gauge-arc { animation-delay: .3s; }
.kpi-card:nth-child(2) .gauge-arc { animation-delay: .37s; }
.kpi-card:nth-child(3) .gauge-arc { animation-delay: .44s; }
.kpi-card:nth-child(4) .gauge-arc { animation-delay: .51s; }

/* 响应式 */
@media (max-width: 1200px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .bottom-grid { grid-template-columns: 1fr; }
  .ai-metrics-grid { grid-template-columns: 1fr; }
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

/* ── AI 分析 V2 ── */
.ai-content-v2 {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
}

/* ① 状态行 */
.ai-status-bar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 10px 14px;
  background: rgba(255,255,255,0.03);
  border: 0.5px solid rgba(255,255,255,0.07);
  border-radius: 10px;
  gap: 12px;
}
.ai-status-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
  flex-wrap: wrap;
}
.ai-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.ai-status-label {
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  flex-shrink: 0;
}
.ai-status-divider {
  color: var(--text-3);
  flex-shrink: 0;
}
.ai-status-summary {
  font-size: 12px;
  color: var(--text-2);
  white-space: normal;
  overflow: visible;
  text-overflow: inherit;
  flex: 1;
  min-width: 0;
}
.ai-timestamp-v2 {
  font-size: 11px;
  color: var(--text-3);
  font-family: var(--mono);
  flex-shrink: 0;
  margin-left: 12px;
}

/* ② 三格指标 */
.ai-metrics-v2 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.ai-metric-v2 {
  background: rgba(255,255,255,0.025);
  border: 0.5px solid var(--border-dim);
  border-radius: 10px;
  padding: 11px 13px;
  transition: border-color .2s;
}
.ai-metric-v2:hover {
  border-color: var(--border-glow);
}
.ai-metric-v2.metric-danger {
  background: rgba(248,113,113,0.04);
  border-color: rgba(248,113,113,0.18);
}
.ai-metric-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.ai-metric-label-v2 {
  font-size: 10px;
  color: var(--text-3);
  letter-spacing: 0.3px;
}
.ai-metric-num {
  font-size: 14px;
  font-weight: 500;
  font-family: var(--mono);
  letter-spacing: -0.3px;
}
.ai-metric-text {
  font-size: 12px;
  color: var(--text-2);
  line-height: 1.5;
}
.ai-risk-badge {
  font-size: 10px;
  font-weight: 500;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(248,113,113,0.14);
  color: #F87171;
  border: 0.5px solid rgba(248,113,113,0.3);
  animation: pulse-red 2s ease-in-out infinite;
}

/* ③ 重点动作 */
.ai-actions-v2 {
  background: rgba(251,191,36,0.04);
  border: 0.5px solid rgba(251,191,36,0.12);
  border-radius: 10px;
  padding: 11px 14px;
}
.ai-actions-header {
  font-size: 10px;
  font-weight: 500;
  color: #FBBF24;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  margin-bottom: 9px;
}
.ai-action-list {
  display: flex;
  flex-direction: column;
  gap: 7px;
}
.ai-action-item-v2 {
  display: flex;
  align-items: center;
  gap: 7px;
  cursor: default;
}
.ai-action-item-v2:hover .ai-action-text {
  color: var(--text-1);
}
.ai-priority-tag {
  font-size: 10px;
  font-weight: 500;
  padding: 2px 7px;
  border-radius: 4px;
  white-space: nowrap;
  flex-shrink: 0;
}
.ai-action-text {
  font-size: 12px;
  color: var(--text-2);
  flex: 1;
  white-space: normal;
  overflow: visible;
  text-overflow: inherit;
  line-height: 1.4;
  transition: color .15s;
}
.ai-person-chips {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}
.ai-person-chip {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 10px;
  background: rgba(255,255,255,0.06);
  color: var(--text-2);
  border: 0.5px solid rgba(255,255,255,0.1);
  white-space: nowrap;
  font-family: var(--mono);
}

@keyframes pulse-red {
  0%,100% { box-shadow: 0 0 0 0 rgba(248,113,113,0); }
  50%      { box-shadow: 0 0 0 3px rgba(248,113,113,0.15); }
}
</style>
