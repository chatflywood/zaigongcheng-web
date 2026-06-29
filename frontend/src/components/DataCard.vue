<script setup>
/**
 * 数据指标卡片
 *
 * Props:
 *   - label: 指标名称
 *   - value: 数值
 *   - unit: 单位
 *   - delta: 变化量文字
 *   - deltaDir: 'up' | 'down' | 'flat'
 *   - badge: 徽标文字
 *   - badgeClass: 徽标样式类
 *   - valueClass: 数值样式类
 */
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: '—' },
  unit: { type: String, default: '' },
  delta: { type: String, default: '' },
  deltaDir: { type: String, default: '' },
  badge: { type: String, default: '' },
  badgeClass: { type: String, default: '' },
  valueClass: { type: String, default: '' },
  inlineNote: { type: String, default: '' },
})
</script>

<template>
  <div class="dc-card">
    <div class="dc-label">{{ label }}</div>
    <div class="dc-value">
      <span class="mono" :class="valueClass">{{ value }}</span>
      <span v-if="unit" class="dc-unit">{{ unit }}</span>
    </div>
    <div class="dc-foot">
      <span v-if="inlineNote" class="dc-note">{{ inlineNote }}</span>
      <span v-if="badge" class="dc-pill" :class="badgeClass">{{ badge }}</span>
      <span v-if="delta" class="dc-delta" :class="deltaDir">
        <span v-if="deltaDir === 'up'" class="tri-up"></span>
        <span v-else-if="deltaDir === 'down'" class="tri-dn"></span>
        {{ delta }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.dc-card {
  display: flex; flex-direction: column; gap: 8px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  padding: 18px 20px;
}
.dc-label {
  font-size: 11px; font-weight: 500; color: var(--ink-3);
  text-transform: uppercase; letter-spacing: 0.04em;
}
.dc-value {
  font-size: 24px; font-weight: 500; color: var(--ink);
  letter-spacing: -0.02em; font-variant-numeric: tabular-nums;
}
.dc-unit { font-size: 13px; color: var(--ink-3); font-weight: 400; margin-left: 4px; }
.dc-foot {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  font-size: 11px; color: var(--ink-3);
}
.dc-note { font-size: 11px; color: var(--ink-3); }
.dc-pill {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 1px 7px; border-radius: 999px;
  font-size: 10.5px; font-weight: 500;
}
.dc-pill.ok { background: var(--ok-soft); color: var(--ok); }
.dc-pill.warn { background: var(--warn-soft); color: var(--warn); }
.dc-pill.bad { background: var(--bad-soft); color: var(--bad); }
.dc-pill.info { background: var(--info-soft); color: var(--info); }
.dc-delta {
  font-family: var(--font-mono); font-size: 11px;
  display: inline-flex; align-items: center; gap: 2px;
}
.dc-delta.up { color: var(--ok); }
.dc-delta.down { color: var(--bad); }
.dc-delta.flat { color: var(--ink-4); }
.tri-up::before { content: '▲'; font-size: 7px; }
.tri-dn::before { content: '▼'; font-size: 7px; }
</style>
