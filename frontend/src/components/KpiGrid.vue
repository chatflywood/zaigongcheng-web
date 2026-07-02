<script setup>
/**
 * KPI 指标卡网格
 *
 * 纯展示组件，4 列网格，支持数字滚动动画。仅 Dashboard 使用。
 *
 * Props:
 *   - metrics (Array): 展示对象数组，每项 { label, value, unit?, inlineNote?, valueClass?, badgeText?, badgeClass?, delta?, deltaDir? }
 *   - targets (Array): 动画目标原始数值数组（与 metrics 索引对齐），不传则不动画
 *   - formatters (Array): 每索引的格式化函数数组，默认 v => v.toFixed(2)
 *   - duration (Number): 动画时长 ms，默认 900
 *
 * Events: 无
 */
import { ref, watch } from 'vue'

const props = defineProps({
  metrics: { type: Array, required: true },
  targets: { type: Array, default: () => [] },
  formatters: { type: Array, default: () => [] },
  duration: { type: Number, default: 900 },
})

const animatedValues = ref([])

function runCountUp() {
  if (!props.metrics?.length || !props.targets.length) { animatedValues.value = []; return }
  const fmts = props.formatters.length ? props.formatters : props.targets.map(() => v => v.toFixed(2))
  const startTs = performance.now()
  function tick(ts) {
    const t = Math.min((ts - startTs) / props.duration, 1)
    const eased = 1 - Math.pow(1 - t, 3)
    animatedValues.value = props.targets.map((target, i) => fmts[i](target * eased))
    if (t < 1) requestAnimationFrame(tick)
    else animatedValues.value = props.targets.map((target, i) => fmts[i](target))
  }
  requestAnimationFrame(tick)
}

watch(() => [props.metrics, props.targets], runCountUp, { immediate: true, deep: true })
</script>

<template>
  <div class="kpi-grid">
    <div class="kpi" v-for="(k, i) in metrics" :key="i">
      <div class="kpi-label">{{ k.label }}</div>
      <div class="kpi-value"><span class="mono" :class="k.valueClass || ''">{{ animatedValues[i] || k.value }}</span><span v-if="k.unit" style="font-size:13px;color:var(--ink-3);font-weight:400;margin-left:4px">{{ k.unit }}</span></div>
      <div class="kpi-foot">
        <span v-if="k.inlineNote">{{ k.inlineNote }}</span>
        <span v-if="k.badgeText" class="pill" :class="k.badgeClass || ''">{{ k.badgeText }}</span>
        <span v-if="k.delta !== undefined && k.delta !== null" class="delta" :class="k.deltaDir || ''">
          <span :class="k.deltaDir === 'up' ? 'tri-up' : k.deltaDir === 'down' ? 'tri-dn' : ''"></span>{{ k.delta }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.kpi-grid {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 1px; background: var(--line);
  border: 1px solid var(--line); border-radius: var(--r-lg); overflow: hidden;
}
.kpi {
  background: var(--surface); padding: 22px 24px;
  display: flex; flex-direction: column; min-width: 0;
}
.kpi-label {
  font-size: 11.5px; color: var(--ink-3); letter-spacing: 0.02em; margin-bottom: 14px;
}
.kpi-value {
  font-size: 32px; font-weight: 500; color: var(--ink); line-height: 1;
  letter-spacing: -0.025em; font-variant-numeric: tabular-nums;
  display: flex; align-items: baseline; gap: 6px;
}
.kpi-value .mono { font-family: var(--font-mono); }
.kpi-foot {
  margin-top: 14px; padding-top: 12px; border-top: 1px dashed var(--line);
  font-size: 11.5px; color: var(--ink-3);
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
}
.kpi-foot .delta {
  display: inline-flex; align-items: center; gap: 4px;
  font-family: var(--font-mono); font-size: 11px; letter-spacing: -0.02em;
}
.delta.up { color: var(--ok); }
.delta.down { color: var(--bad); }
.tri-up::before { content: '▲'; font-size: 8px; margin-right: 3px; }
.tri-dn::before { content: '▼'; font-size: 8px; margin-right: 3px; }
.val-negative { color: var(--bad) !important; }
</style>
