<template>
  <section class="ic-metric" aria-label="投资结转率" :class="{ 'is-within-target': rate !== null && amount >= 0 && !aboveTarget }">
    <div class="ic-head">
      <span>投资结转率</span>
      <span class="ic-goal">年底 ≤22%</span>
    </div>
    <div class="ic-main">
      <strong class="ic-value">{{ rate === null ? '—' : rate.toFixed(2) }}<span v-if="rate !== null">%</span></strong>
      <span class="ic-status">{{ unavailableReason || (amount < 0 ? '负值待核查' : aboveTarget ? `高于目标 ${gap.toFixed(2)}pp` : '已在目标范围内') }}</span>
    </div>
    <div class="ic-foot">
      <span>结转额 {{ money(amount) }} 万</span>
      <button ref="trigger" type="button" aria-haspopup="dialog" @click="openDetails">口径 ↗</button>
    </div>

    <Teleport to="body">
      <div v-if="detailsVisible" class="ic-overlay" @click.self="closeDetails" @keydown.esc.stop.prevent="closeDetails" @keydown.tab.prevent="closeButton?.focus()">
        <section class="ic-dialog" role="dialog" aria-modal="true" :aria-labelledby="`${id}-title`" :aria-describedby="`${id}-description`">
          <h2 :id="`${id}-title`">投资结转率 · 口径</h2>
          <p :id="`${id}-description`">结转额 ÷ 正式本年预算 × 100%<br>结转额 = 单项总投资 − 累计资本性支出</p>
          <p class="ic-calculation">{{ money(amount) }} ÷ {{ money(budget) }}<template v-if="rate !== null"> ≈ <b>{{ rate.toFixed(2) }}%</b></template><template v-else><br><span>{{ unavailableReason }}，暂不计算结转率。</span></template></p>
          <p>年底目标 ≤22% · 越低越好<template v-if="rate !== null"><br>按当前预算，结转额上限 <b>{{ money(targetAmount) }} 万</b><br>还需压降约 <b>{{ money(reduction) }} 万</b></template></p>
          <p v-if="amount !== null && amount < 0" class="ic-date-note">结转额为负值，请核查总投资与累计支出。</p>
          <p class="ic-date-note">工程数据：{{ engineeringDate || '日期未确认' }}<br>预算数据：{{ budgetDate || '日期未确认' }}<template v-if="dateMismatch"> · 数据日期不同</template></p>
          <div class="ic-dialog-footer"><button ref="closeButton" type="button" @click="closeDetails">关闭</button></div>
        </section>
      </div>
    </Teleport>
  </section>
</template>

<script setup>
import { computed, nextTick, ref, useId } from 'vue'

const props = defineProps({
  amount: { type: Number, default: null },
  budget: { type: Number, default: null },
  engineeringDate: { type: String, default: '' },
  budgetDate: { type: String, default: '' },
})

const id = useId()
const detailsVisible = ref(false)
const trigger = ref(null)
const closeButton = ref(null)
const amount = computed(() => Number.isFinite(props.amount) ? props.amount : null)
const budget = computed(() => Number.isFinite(props.budget) && props.budget > 0 ? props.budget : null)

function validDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false
  const date = new Date(`${value}T00:00:00Z`)
  return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === value
}

const unavailableReason = computed(() => {
  if (amount.value === null) return '结转额缺失'
  if (budget.value === null) return '本年预算缺失或无效'
  if (!validDate(props.engineeringDate) || !validDate(props.budgetDate)) return '数据日期待确认'
  if (props.engineeringDate.slice(0, 4) !== props.budgetDate.slice(0, 4)) return '数据年度不一致'
  return ''
})
const dateMismatch = computed(() => validDate(props.engineeringDate) && validDate(props.budgetDate) && props.engineeringDate !== props.budgetDate)
// 使用正式预算，与支出目标、转固率各自独立；负值和超过 100% 的结果保留。
const rate = computed(() => unavailableReason.value ? null : amount.value / budget.value * 100)
const targetAmount = computed(() => budget.value === null ? null : budget.value * 0.22)
const aboveTarget = computed(() => rate.value !== null && amount.value > targetAmount.value)
const gap = computed(() => rate.value === null ? null : Math.max(0, rate.value - 22))
const reduction = computed(() => rate.value === null ? null : Math.max(0, amount.value - targetAmount.value))

function money(value) {
  return Number.isFinite(value) ? value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—'
}
async function openDetails() {
  detailsVisible.value = true
  await nextTick()
  closeButton.value?.focus()
}
async function closeDetails() {
  detailsVisible.value = false
  await nextTick()
  trigger.value?.focus()
}
</script>

<style scoped>
.ic-metric { border-left: 1px solid var(--line-2); padding-left: 22px; align-self: stretch; display: flex; flex-direction: column; justify-content: space-between; min-height: 90px; min-width: 0; gap: 10px; }
.ic-head { display: flex; flex-wrap: wrap; gap: 6px; justify-content: space-between; align-items: center; font-size: 12px; font-weight: 500; color: var(--ink); }
.ic-goal { font-size: 10px; color: var(--ink-3); font-weight: 400; border: 1px solid var(--line); padding: 2px 6px; border-radius: var(--r-sm); white-space: nowrap; }
.ic-main { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 8px; }
.ic-value { font-family: var(--font-mono); font-size: 30px; font-weight: 550; color: var(--accent-ink); letter-spacing: -1.2px; line-height: 1; max-width: 100%; overflow-wrap: anywhere; }
.ic-value span { font-size: 15px; letter-spacing: 0; margin-left: 1px; }
.ic-status { font-size: 10px; color: var(--accent-ink); text-align: right; }
.is-within-target .ic-value, .is-within-target .ic-status { color: var(--ok); }
.ic-foot { font-family: var(--font-mono); font-size: 10px; color: var(--ink-3); display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 8px; }
.ic-foot button { border: 0; background: none; padding: 0; color: var(--ink-3); font-size: 10px; white-space: nowrap; }
.ic-foot button:hover { color: var(--accent-ink); }
button:focus-visible { outline: 2px solid var(--accent); outline-offset: 4px; }
.ic-overlay { position: fixed; inset: 0; background: rgba(31,29,24,0.38); z-index: 10001; display: grid; place-items: center; padding: 16px; }
.ic-dialog { width: 420px; max-width: 100%; max-height: calc(100dvh - 32px); overflow-y: auto; padding: 24px; border: 1px solid var(--line); border-radius: var(--r-lg); background: var(--surface); box-shadow: var(--shadow-pop); }
.ic-dialog h2 { margin: 0 0 20px; font-size: 18px; font-weight: 500; color: var(--ink); }
.ic-dialog p { font-size: 13px; line-height: 1.9; margin: 12px 0; color: var(--ink-2); }
.ic-dialog .ic-calculation { font-family: var(--font-mono); }
.ic-dialog .ic-date-note { font-size: 11px; color: var(--warn); }
.ic-dialog-footer { display: flex; justify-content: flex-end; margin-top: 18px; }
.ic-dialog-footer button { padding: 6px 14px; background: var(--ink); color: var(--paper); border: 0; border-radius: var(--r-md); font-size: 12px; }
@media (max-width: 1200px) { .ic-metric { padding-left: 16px; } }
@media (max-width: 960px) { .ic-metric { border-left: 0; border-top: 1px solid var(--line-2); padding: 14px 0 0; gap: 12px; } }
</style>
