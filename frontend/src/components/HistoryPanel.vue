<script setup>
/**
 * 历史快照抽屉
 *
 * 跨 Dashboard / Budget 复用。状态由 useHistoryPanel composable 提供，
 * 本组件只做展示与事件上抛。kpis/meta 区通过 scoped slot 让调用方自定义取数与格式。
 *
 * Props:
 *   - visible (Boolean): 是否显示（v-model:visible）
 *   - loading (Boolean): 加载中
 *   - records (Array): 历史记录列表
 *   - currentRecordId (Number|null): 当前记录 id（高亮 active 项）
 *   - title (String): 面板标题
 *   - subtitle (String): 副文案
 *   - kickerClass (String): panel-kicker 额外 class（如 Budget 的 'budget-kicker'）
 *
 * Events:
 *   - update:visible(visible): 关闭
 *   - view-snapshot(recordId): 点击历史项
 *
 * Slots:
 *   - kpi-capital({ record }): 资本/占用金额展示
 *   - kpi-progress({ record }): 进度文案
 *   - kpi-delta({ record, index }): 增量展示（可选，不传则不显示）
 *   - meta({ record }): 底部元信息（日期等）
 */
defineProps({
  visible: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  records: { type: Array, default: () => [] },
  currentRecordId: { type: [Number, null], default: null },
  title: { type: String, default: '历史记录中心' },
  subtitle: { type: String, default: '' },
  kickerClass: { type: String, default: '' },
})

const emit = defineEmits(['update:visible', 'view-snapshot'])
</script>

<template>
  <div v-if="visible" class="history-overlay" @click.self="emit('update:visible', false)">
    <aside class="history-panel">
      <div class="history-panel-header">
        <div>
          <span class="panel-kicker" :class="kickerClass">History Snapshots</span>
          <h3>{{ title }}</h3>
          <p>{{ subtitle }}</p>
        </div>
        <button class="hp-close" @click="emit('update:visible', false)">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
        </button>
      </div>
      <div v-if="loading" class="history-loading">
        <div class="loader-ring" style="width:32px;height:32px;position:relative"></div>
        <p>正在读取历史记录...</p>
      </div>
      <div v-else-if="records.length === 0" class="history-empty">
        <p>暂无历史记录</p>
      </div>
      <div v-else class="history-list">
        <button
          v-for="(record, index) in records"
          :key="record.id"
          class="history-item"
          :class="{ active: currentRecordId === record.id }"
          @click="emit('view-snapshot', record.id)"
        >
          <div class="history-item-top">
            <strong>{{ record.source_filename }}</strong>
            <span class="history-item-id">#{{ record.id }}</span>
          </div>
          <div class="history-item-kpis">
            <span class="history-kpi-capital"><slot name="kpi-capital" :record="record" /></span>
            <span class="history-kpi-progress"><slot name="kpi-progress" :record="record" /></span>
            <slot name="kpi-delta" :record="record" :index="index" />
          </div>
          <div class="history-item-meta">
            <slot name="meta" :record="record" />
          </div>
        </button>
      </div>
    </aside>
  </div>
</template>

<style scoped>
@keyframes spin { to { transform: rotate(360deg); } }

.history-overlay {
  position: fixed; inset: 0; z-index: 980;
  display: flex; justify-content: flex-end; background: rgba(31,29,24,0.2);
}
.history-panel {
  width: min(480px, 100%); height: 100%; padding: 24px;
  background: var(--surface); border-left: 1px solid var(--line);
  box-shadow: -12px 0 40px rgba(31,29,24,0.08); overflow-y: auto; color: var(--ink);
}
.history-panel-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 16px; margin-bottom: 20px;
}
.history-panel-header h3 { margin: 6px 0 8px; font-size: 20px; font-weight: 500; color: var(--ink); }
.history-panel-header p { color: var(--ink-3); font-size: 13px; line-height: 1.6; }
.panel-kicker { display: inline-block; font-size: 11px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--accent); }
.hp-close {
  width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;
  background: transparent; border: 1px solid var(--line-2);
  border-radius: var(--r-md); color: var(--ink-2); cursor: pointer; transition: 0.15s; flex-shrink: 0;
}
.hp-close:hover { background: var(--paper-2); color: var(--ink); }
.history-loading, .history-empty { min-height: 200px; display: grid; place-items: center; color: var(--ink-3); text-align: center; }
.history-list { display: grid; gap: 8px; }
.history-item {
  width: 100%; padding: 14px; border-radius: var(--r-md);
  border: 1px solid var(--line); background: var(--surface);
  color: var(--ink); text-align: left; cursor: pointer; transition: 0.15s; font-family: inherit;
}
.history-item:hover { border-color: var(--line-2); background: var(--paper); }
.history-item.active { border-color: var(--line-2); background: var(--paper-2); }
.history-item-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 8px; }
.history-item-top strong { flex: 1; font-size: 13px; color: var(--ink); }
.history-item-id { flex-shrink: 0; color: var(--ink-4); font-size: 12px; font-family: var(--font-mono); }
.history-item-kpis { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; flex-wrap: wrap; }
.history-kpi-capital { font-size: 14px; font-weight: 500; color: var(--ink); display: flex; align-items: baseline; gap: 3px; font-family: var(--font-mono); }
.history-kpi-capital em { font-size: 11px; font-style: normal; font-weight: 400; color: var(--ink-3); font-family: var(--font-sans); }
.history-kpi-progress { font-size: 11px; color: var(--info); background: var(--info-soft); padding: 2px 8px; border-radius: 4px; }
.history-kpi-delta { font-size: 12px; font-weight: 500; font-family: var(--font-mono); }
.history-kpi-delta.delta-up { color: var(--ok); }
.history-kpi-delta.delta-down { color: var(--bad); }
.history-item-meta { display: flex; gap: 10px; flex-wrap: wrap; color: var(--ink-4); font-size: 11px; }
.loader-ring {
  width: 36px; height: 36px; border: 3px solid transparent;
  border-top-color: var(--ink-3); border-radius: 50%;
  animation: spin 1s linear infinite;
}
</style>
