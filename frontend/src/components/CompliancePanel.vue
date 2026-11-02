<script setup>
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import { exportCompliance, getCompliance, saveComplianceReview } from '../api'

const props = defineProps({ recordId: { type: Number, default: null } })
const data = ref(null)
const loading = ref(false)
const error = ref('')
const visible = ref(false)
const active = ref('safety')
const manager = ref('')
const status = ref('')
const showRules = ref(false)
const exporting = ref(false)
const saving = ref('')
const saveError = ref('')
const savedMessage = ref('')
const drafts = ref({})
const modal = ref(null)
const kinds = [{ key: 'safety', label: '安全生产费核实' }, { key: 'quality', label: '质检申报核实' }]
const statuses = ['待核实', '已核实正常', '发现问题']
let requestVersion = 0
let previousFocus = null
let previousOverflow = ''

const current = computed(() => data.value?.checks?.[active.value])
const managers = computed(() => [...new Set((current.value?.items || []).map(item => item.manager))].sort())
const items = computed(() => (current.value?.items || []).filter(item =>
  (!manager.value || item.manager === manager.value) && (!status.value || item.status === status.value)))
const keyFor = (kind, code) => `${kind}:${code}`
const initialDraft = item => ({ status: item.status, reviewed_on: item.reviewed_on || '', note: item.note || '' })
const draftFor = item => drafts.value[keyFor(active.value, item.code)]
const changed = item => JSON.stringify(draftFor(item)) !== JSON.stringify(initialDraft(item))
const money = value => value == null ? '未提供' : Number(value).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const statusClass = value => value === '发现问题' ? 'issue' : value === '已核实正常' ? 'normal' : 'pending'
function messageFrom(err, fallback) {
  const message = err?.response?.data?.detail || err?.response?.data?.message
  return typeof message === 'string' ? message : fallback
}

async function load() {
  const version = ++requestVersion
  const recordId = props.recordId
  data.value = null
  drafts.value = {}
  error.value = ''
  visible.value = false
  manager.value = ''
  status.value = ''
  saving.value = ''
  saveError.value = ''
  savedMessage.value = ''
  if (!recordId) { loading.value = false; return }
  loading.value = true
  try {
    const result = await getCompliance(recordId)
    if (version !== requestVersion) return
    if (!result?.success || !result.data) throw new Error('核查数据加载失败')
    data.value = result.data
    for (const kind of kinds) {
      for (const item of result.data.checks[kind.key].items) {
        drafts.value[keyFor(kind.key, item.code)] = initialDraft(item)
      }
    }
  } catch (err) {
    if (version === requestVersion) error.value = messageFrom(err, '核查数据加载失败，请重试')
  } finally {
    if (version === requestVersion) loading.value = false
  }
}
watch(() => props.recordId, load, { immediate: true })
watch(active, () => { manager.value = ''; status.value = ''; saveError.value = ''; savedMessage.value = '' })

function open(kind) {
  active.value = kind
  showRules.value = false
  previousFocus = document.activeElement
  visible.value = true
}
watch(visible, async value => {
  if (value) {
    previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    await nextTick()
    modal.value?.querySelector('.compliance-close')?.focus()
  } else {
    document.body.style.overflow = previousOverflow
    previousFocus?.focus?.()
  }
})
onUnmounted(() => {
  requestVersion++
  if (visible.value) document.body.style.overflow = previousOverflow
})

function trapFocus(event) {
  const controls = [...modal.value.querySelectorAll('button:not(:disabled), select, input, textarea, a[href]')]
    .filter(el => el.offsetParent !== null)
  const first = controls[0], last = controls[controls.length - 1]
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
}

function changeStatus(item) {
  const draft = draftFor(item)
  if (draft.status === '待核实') draft.reviewed_on = ''
  else if (!draft.reviewed_on) {
    const now = new Date()
    draft.reviewed_on = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  }
}

async function save(item) {
  const kind = active.value, recordId = props.recordId, version = requestVersion
  const key = keyFor(kind, item.code)
  const draft = { ...drafts.value[key] }
  saveError.value = ''
  savedMessage.value = ''
  if (draft.status !== '待核实' && !draft.reviewed_on) { saveError.value = '请选择核实日期'; return }
  saving.value = key
  try {
    const result = await saveComplianceReview(recordId, kind, item.code, { ...draft, reviewed_on: draft.reviewed_on || null })
    if (version !== requestVersion) return
    if (!result?.success || !result.data) throw new Error('保存失败')
    data.value = result.data
    const updated = result.data.checks[kind].items.find(row => row.code === item.code)
    drafts.value[key] = initialDraft(updated)
    savedMessage.value = `${item.code} 核实结果已保存`
  } catch (err) {
    if (version === requestVersion) saveError.value = messageFrom(err, '核实结果保存失败，请重试')
  } finally {
    if (version === requestVersion) saving.value = ''
  }
}

async function download() {
  if (exporting.value) return
  const recordId = props.recordId, endDate = data.value.end_date
  exporting.value = true
  saveError.value = ''
  let url
  try {
    const blob = await exportCompliance(recordId)
    url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `工程合规核查_${endDate}.xlsx`
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch { saveError.value = '清单导出失败，请重试' }
  finally {
    if (url) URL.revokeObjectURL(url)
    exporting.value = false
  }
}
</script>

<template>
  <section class="compliance-panel" aria-label="工程合规核查">
    <div class="compliance-panel-head">
      <h3>工程合规核查</h3>
      <button class="compliance-text-button" :disabled="!data" @click="open('safety'); showRules = true">筛选口径</button>
    </div>
    <p v-if="data" class="compliance-range">{{ data.start_date }} — {{ data.end_date }}<span>近两个月</span></p>
    <div v-if="loading" class="compliance-placeholder" role="status">正在加载核查清单…</div>
    <div v-else-if="error" class="compliance-placeholder compliance-error" role="alert">{{ error }} <button class="compliance-text-button" @click="load">重试</button></div>
    <div v-else-if="!data" class="compliance-placeholder">加载在建工程数据后查看核查清单</div>
    <div v-else class="compliance-cards">
      <button v-for="kind in kinds" :key="kind.key" class="compliance-tile" @click="open(kind.key)">
        <span class="compliance-tile-label">{{ kind.label }}<span aria-hidden="true">↗</span></span>
        <span class="compliance-tile-count">{{ data.checks[kind.key].total }}<small>项</small></span>
        <span class="compliance-tile-detail">待核实 {{ data.checks[kind.key].pending }}<span v-if="data.checks[kind.key].issues" class="compliance-error"> · 问题 {{ data.checks[kind.key].issues }}</span><span v-else> · 已核实 {{ data.checks[kind.key].normal }}</span></span>
      </button>
    </div>
  </section>

  <Teleport to="body">
    <div v-if="visible && data" class="compliance-overlay" @click.self="visible = false" @keydown.esc.stop.prevent="visible = false" @keydown.tab="trapFocus">
      <section ref="modal" class="compliance-modal" role="dialog" aria-modal="true" aria-labelledby="compliance-dialog-title">
        <header class="compliance-modal-head">
          <div><h3 id="compliance-dialog-title">工程合规核查</h3><p>{{ data.start_date }} 至 {{ data.end_date }}，包含首尾两天</p></div>
          <div class="compliance-actions">
            <button class="btn primary" :disabled="exporting || !!saving" @click="download">{{ exporting ? '正在导出…' : '导出清单' }}</button>
            <button class="compliance-close" aria-label="关闭工程合规核查" @click="visible = false">✕</button>
          </div>
        </header>
        <div class="compliance-tabs" role="tablist" aria-label="核查类型">
          <button v-for="kind in kinds" :id="`compliance-tab-${kind.key}`" :key="kind.key" role="tab" :aria-selected="active === kind.key" aria-controls="compliance-tab-panel" :class="{ active: active === kind.key }" @click="active = kind.key">{{ kind.label }} <span>{{ data.checks[kind.key].total }}</span></button>
          <button class="compliance-text-button compliance-rules-toggle" :aria-expanded="showRules" @click="showRules = !showRules">{{ showRules ? '收起口径' : '筛选口径' }}</button>
        </div>
        <div v-if="showRules" class="compliance-rules">
          <p>以本次原始报表上传日往前推两个自然月，包含首尾。安全生产费按“工程开工日期”筛选，剔除“单纯购置项目”（含“单纯性购置项目”）及“零星购置项目”。质检申报按“设计批复日期(初次)”筛选。</p>
          <p>不额外按工程状态、专业或费用金额排除。费用为账面金额，实际支付及申报情况需核实。核实记录独立保存，后续上传会继承；查看历史版本时展示当前登记结果。</p>
          <p>本类日期缺失 {{ current.missing_dates }} 项，日期无效 {{ current.invalid_dates }} 项，未纳入清单。<span v-if="active === 'safety'">本期按项目类型剔除 {{ current.excluded }} 项。</span></p>
        </div>
        <div class="compliance-toolbar">
          <div class="compliance-filters"><label>管理员 <select v-model="manager"><option value="">全部</option><option v-for="name in managers" :key="name">{{ name }}</option></select></label><label>核实状态 <select v-model="status"><option value="">全部</option><option v-for="value in statuses" :key="value">{{ value }}</option></select></label></div>
          <span>待核实 {{ current.pending }} · 已核实正常 {{ current.normal }} · 发现问题 {{ current.issues }}</span>
        </div>
        <p v-if="saveError" class="compliance-feedback compliance-error" role="alert">{{ saveError }}</p>
        <p v-else-if="savedMessage" class="compliance-feedback" role="status">{{ savedMessage }}</p>
        <div id="compliance-tab-panel" class="compliance-table-scroll" role="tabpanel" :aria-labelledby="`compliance-tab-${active}`">
          <table class="compliance-table">
            <thead><tr><th class="compliance-project">工程名称 / 编码</th><th class="compliance-manager">管理员 / 类型</th><th class="compliance-date">{{ active === 'safety' ? '工程开工日期' : '首次设计批复' }}</th><th class="compliance-project-status">工程状态 / 施工单位</th><template v-if="active === 'safety'"><th class="compliance-fee">本年安全费<br>（元）</th><th class="compliance-fee">累计安全费<br>（元）</th></template><th class="compliance-review">核实结果登记</th></tr></thead>
            <tbody><tr v-for="item in items" :key="`${active}:${item.code}`">
              <td><div class="compliance-project-name">{{ item.name }}</div><span class="compliance-secondary mono">{{ item.code }}</span></td>
              <td>{{ item.manager }}<span class="compliance-secondary">{{ item.project_type || '未提供' }}</span></td>
              <td class="mono">{{ item.key_date }}</td>
              <td>{{ item.project_status || '未提供' }}<span class="compliance-secondary">{{ item.construction_unit || '施工单位未提供' }}</span></td>
              <template v-if="active === 'safety'"><td class="compliance-number mono">{{ money(item.current_safety_fee) }}</td><td class="compliance-number mono">{{ money(item.total_safety_fee) }}</td></template>
              <td><div class="compliance-review-fields">
                <select v-model="draftFor(item).status" :disabled="saving === keyFor(active, item.code)" :aria-label="`${item.code} 核实状态`" :class="statusClass(draftFor(item).status)" @change="changeStatus(item)"><option v-for="value in statuses" :key="value">{{ value }}</option></select>
                <input v-model="draftFor(item).reviewed_on" :disabled="saving === keyFor(active, item.code)" type="date" :aria-label="`${item.code} 核实日期`">
                <textarea v-model="draftFor(item).note" :disabled="saving === keyFor(active, item.code)" rows="2" maxlength="4000" placeholder="填写支付凭证、申报情况或其他核实备注" :aria-label="`${item.code} 核实备注`"></textarea>
                <button class="compliance-save" :disabled="!!saving || !changed(item)" @click="save(item)">{{ saving === keyFor(active, item.code) ? '保存中…' : '保存核实结果' }}</button>
              </div></td>
            </tr><tr v-if="!items.length"><td :colspan="active === 'safety' ? 7 : 5" class="compliance-empty">{{ current.total ? '没有符合筛选条件的项目' : '本期没有符合核查条件的项目' }}</td></tr></tbody>
          </table>
        </div>
        <footer class="compliance-modal-footer">{{ data.source_filename }}<span>核实记录为当前登记结果，上传报表不会清空</span></footer>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.compliance-panel { padding: 13px 16px 15px; border-top: 1px solid var(--line); margin-top: auto; }
.compliance-panel-head { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 8px; }
.compliance-panel h3 { margin: 0; font-size: 14px; font-weight: 500; color: var(--ink); white-space: nowrap; }
.compliance-text-button { padding: 2px 0; border: 0; background: transparent; color: var(--ink-3); font-size: 11px; }
.compliance-text-button:hover { color: var(--accent); }
.compliance-text-button:disabled { opacity: .5; cursor: default; }
.compliance-range { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 4px; margin: 6px 0 10px; color: var(--ink-3); font-size: 11px; font-variant-numeric: tabular-nums; }
.compliance-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(140px, 100%), 1fr)); gap: 10px; }
.compliance-tile { text-align: left; border: 1px solid var(--line); border-radius: var(--r-md); background: var(--surface-2); padding: 10px 12px; color: var(--ink); min-width: 0; transition: border-color 120ms, background 120ms; }
.compliance-tile:hover { border-color: var(--accent); background: var(--paper); }
.compliance-tile-label { display: flex; align-items: center; justify-content: space-between; gap: 4px; font-size: 12px; }
.compliance-tile-label > span { color: var(--ink-3); flex-shrink: 0; }
.compliance-tile-count { display: block; margin: 6px 0 4px; font-family: var(--font-mono); font-size: 24px; line-height: 1; font-weight: 500; }
.compliance-tile-count small { margin-left: 5px; font-family: var(--font-sans); font-size: 11px; font-weight: 400; color: var(--ink-3); }
.compliance-tile-detail { display: block; font-size: 10.5px; color: var(--ink-3); line-height: 1.5; }
.compliance-placeholder { padding: 18px 0 5px; color: var(--ink-3); font-size: 12px; line-height: 1.6; }
.compliance-error { color: var(--bad) !important; }
.compliance-overlay { position: fixed; inset: 0; z-index: 1200; background: rgba(31,29,24,.38); padding: 30px 20px; display: flex; justify-content: center; align-items: center; }
.compliance-modal { width: min(1340px, 100%); max-height: 90vh; display: flex; flex-direction: column; min-height: 350px; border: 1px solid var(--line-2); border-radius: var(--r-xl); background: var(--surface); box-shadow: var(--shadow-pop); color: var(--ink); overflow: hidden; }
.compliance-modal-head { padding: 20px 24px 16px; display: flex; justify-content: space-between; align-items: center; gap: 18px; }
.compliance-modal-head h3 { font-size: 18px; font-weight: 500; margin: 0; }
.compliance-modal-head p { font-size: 12px; color: var(--ink-3); margin-top: 7px; }
.compliance-actions { display: flex; align-items: center; gap: 12px; }
.compliance-close { width: 32px; height: 32px; border: 1px solid var(--line); border-radius: var(--r-md); background: var(--surface); color: var(--ink-2); }
.compliance-tabs { display: flex; align-items: center; padding: 0 24px; gap: 24px; border-bottom: 1px solid var(--line); }
.compliance-tabs > button[role=tab] { padding: 13px 0; border: 0; border-bottom: 2px solid transparent; background: transparent; color: var(--ink-3); font-size: 13px; }
.compliance-tabs > button.active { color: var(--accent-ink); border-bottom-color: var(--accent); }
.compliance-tabs button span { margin-left: 5px; font-family: var(--font-mono); }
.compliance-rules-toggle { margin-left: auto; }
.compliance-rules { padding: 12px 24px; background: var(--paper); color: var(--ink-2); font-size: 12px; line-height: 1.7; max-height: 200px; overflow: auto; border-bottom: 1px solid var(--line); }
.compliance-rules p + p { margin-top: 5px; }
.compliance-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; padding: 14px 24px; font-size: 12px; color: var(--ink-3); }
.compliance-filters { display: flex; flex-wrap: wrap; gap: 14px; }
.compliance-filters label { display: flex; align-items: center; gap: 7px; }
.compliance-modal select, .compliance-modal input, .compliance-modal textarea { border: 1px solid var(--line-2); background: var(--surface); color: var(--ink-2); font-family: inherit; font-size: 12px; padding: 6px 8px; border-radius: var(--r-sm); min-width: 0; }
.compliance-table-scroll { overflow: auto; padding: 0 24px; flex: 1; min-height: 0; }
.compliance-table { width: 100%; min-width: 1030px; border-collapse: collapse; table-layout: fixed; font-size: 12px; }
.compliance-table th { text-align: left; background: var(--paper-2); position: sticky; top: 0; z-index: 1; color: var(--ink-3); font-size: 11px; font-weight: 500; padding: 10px 9px; }
.compliance-table td { padding: 12px 9px; border-bottom: 1px solid var(--line); vertical-align: top; overflow-wrap: anywhere; }
.compliance-project { width: 25%; }
.compliance-manager { width: 90px; }
.compliance-date { width: 105px; }
.compliance-project-status { width: 150px; }
.compliance-fee { width: 90px; text-align: right !important; }
.compliance-review { width: 280px; }
.compliance-project-name { line-height: 1.65; }
.compliance-secondary { display: block; margin-top: 6px; font-size: 11px; color: var(--ink-3); line-height: 1.5; }
.compliance-number { text-align: right; white-space: nowrap; }
.compliance-review-fields { display: grid; grid-template-columns: 1fr 1fr; gap: 7px; }
.compliance-review-fields textarea { grid-column: 1 / -1; resize: vertical; line-height: 1.5; }
.compliance-review-fields .pending { color: var(--warn); }
.compliance-review-fields .issue { color: var(--bad); }
.compliance-review-fields .normal { color: var(--ok); }
.compliance-save { grid-column: 2; justify-self: end; padding: 5px 8px; background: var(--ink); color: var(--surface); border: 1px solid var(--ink); border-radius: var(--r-sm); font-size: 11px; }
.compliance-save:disabled { opacity: .4; cursor: default; }
.compliance-feedback { padding: 0 24px 10px; color: var(--ok); font-size: 12px; }
.compliance-empty { text-align: center; color: var(--ink-3); padding: 35px !important; }
.compliance-modal-footer { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px; padding: 12px 24px; font-size: 11px; color: var(--ink-3); border-top: 1px solid var(--line); }
@media(max-width: 600px) {
  .compliance-overlay { padding: 12px 8px; }
  .compliance-modal { max-height: 94vh; }
  .compliance-modal-head { padding: 16px; align-items: flex-start; }
  .compliance-modal-head h3 { font-size: 16px; }
  .compliance-modal-head p { max-width: 185px; line-height: 1.6; }
  .compliance-actions { gap: 6px; }
  .compliance-actions .btn { font-size: 11px; padding: 6px 8px; }
  .compliance-tabs { padding: 0 16px; gap: 16px; flex-wrap: wrap; }
  .compliance-tabs > button[role=tab] { font-size: 12px; }
  .compliance-rules-toggle { margin-left: 0; }
  .compliance-toolbar, .compliance-rules, .compliance-modal-footer { padding: 12px 16px; }
  .compliance-table-scroll { padding: 0 16px; }
}
</style>
