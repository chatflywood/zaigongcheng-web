<script setup>
/**
 * 文件列表行组件
 *
 * Props:
 *   - name: 文件名
 *   - ext: 扩展名（如 '.xlsx'）
 *   - meta: 元信息文字
 *   - active: 是否选中
 *
 * Events:
 *   - click: 点击行
 *
 * Slots:
 *   - actions: 右侧操作按钮区
 */
defineProps({
  name: { type: String, required: true },
  ext: { type: String, default: '' },
  meta: { type: String, default: '' },
  active: { type: Boolean, default: false },
})

const emit = defineEmits(['click'])

function extBadgeClass(ext) {
  if (['.xlsx', '.xls'].includes(ext)) return 'fr-ext-xlsx'
  if (ext === '.docx') return 'fr-ext-docx'
  return 'fr-ext-other'
}

function extLabel(ext) {
  return ext.replace('.', '').toUpperCase()
}
</script>

<template>
  <div class="fr-row" :class="{ active }" @click="emit('click')">
    <span class="fr-ext" :class="extBadgeClass(ext)">{{ extLabel(ext) }}</span>
    <div class="fr-info">
      <span class="fr-name">{{ name }}</span>
      <span v-if="meta" class="fr-meta">{{ meta }}</span>
    </div>
    <div class="fr-actions" @click.stop>
      <slot name="actions" />
    </div>
  </div>
</template>

<style scoped>
.fr-row {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px;
  cursor: pointer; transition: background 0.12s;
  border-radius: var(--r-md);
}
.fr-row:hover { background: var(--surface-2); }
.fr-row.active { background: var(--accent-soft); }

.fr-ext {
  font-size: 11px; font-weight: 700;
  padding: 2px 7px; border-radius: 4px;
  flex-shrink: 0;
}
.fr-ext-xlsx { background: #d1fae5; color: #065f46; }
.fr-ext-docx { background: #dbeafe; color: #1e40af; }
.fr-ext-other { background: var(--paper-2); color: var(--ink-3); }

.fr-info { flex: 1; min-width: 0; }
.fr-name {
  display: block; font-size: 13px; color: var(--ink);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.fr-meta {
  display: block; font-size: 11px; color: var(--ink-3); margin-top: 2px;
}

.fr-actions {
  display: flex; gap: 6px; flex-shrink: 0;
}
</style>
