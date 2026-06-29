<script setup>
/**
 * 拖拽上传区组件
 *
 * Props:
 *   - accept: 接受的文件类型（如 '.xlsx,.xls'）
 *   - hint: 提示文字
 *   - fileName: 已选文件名（空则显示拖拽区）
 *
 * Events:
 *   - file-select(file): 选择了文件
 */
import { ref } from 'vue'

const props = defineProps({
  accept: { type: String, default: '.xlsx,.xls' },
  hint: { type: String, default: '支持 .xlsx 格式' },
  fileName: { type: String, default: '' },
})

const emit = defineEmits(['file-select'])
const fileInput = ref(null)
const isDragging = ref(false)

function triggerInput() { fileInput.value?.click() }

function onFileChange(e) {
  const f = e.target.files[0]
  if (f) emit('file-select', f)
}

function onDrop(e) {
  isDragging.value = false
  const f = e.dataTransfer.files[0]
  if (f) emit('file-select', f)
}

function onDragOver() { isDragging.value = true }
function onDragLeave() { isDragging.value = false }
</script>

<template>
  <div class="uz-zone" :class="{ dragging: isDragging }"
    @dragover.prevent="onDragOver"
    @dragleave="onDragLeave"
    @drop.prevent="onDrop"
    @click="triggerInput"
  >
    <input ref="fileInput" type="file" :accept="accept" hidden @change="onFileChange" />
    <slot v-if="fileName" name="selected">
      <svg width="18" height="18" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="9" stroke="#047857" stroke-width="1.2"/><path d="M6 10l3 3 5-5" stroke="#047857" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
      <span class="uz-name">{{ fileName }}</span>
    </slot>
    <slot v-else>
      <svg width="20" height="20" viewBox="0 0 34 34" fill="none">
        <rect x="4" y="7" width="26" height="22" rx="3" stroke="currentColor" stroke-width="1.2"/>
        <path d="M11 14h12M11 18.5h8" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        <path d="M21.5 3v7M18 6l3.5-3.5L25 6" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span>拖拽或<em>点击选择</em></span>
      <span class="uz-hint">{{ hint }}</span>
    </slot>
  </div>
</template>

<style scoped>
.uz-zone {
  border: 1.5px dashed var(--line-2);
  border-radius: var(--r-md);
  padding: 20px;
  display: flex; align-items: center; justify-content: center;
  gap: 10px; flex-wrap: wrap;
  cursor: pointer; text-align: center;
  font-size: 12.5px; color: var(--ink-3);
  min-height: 72px;
  transition: border-color 0.15s, background 0.15s;
}
.uz-zone:hover, .uz-zone.dragging {
  border-color: var(--accent);
  background: var(--surface-2);
  color: var(--ink-2);
}
.uz-zone em { color: var(--accent); font-style: normal; text-decoration: underline; text-underline-offset: 2px; }
.uz-name { font-size: 12.5px; color: var(--ink); font-weight: 500; word-break: break-all; }
.uz-hint { font-size: 11px; color: var(--ink-4); }
</style>
