<script setup>
/**
 * 通用弹窗组件
 *
 * Props:
 *   - visible (v-model): 控制显示/隐藏
 *   - title: 弹窗标题
 *   - size: 'sm' | 'md' | 'lg'（默认 md）
 *
 * Slots:
 *   - header-actions: 标题栏右侧操作区
 *   - default: 弹窗内容
 */
const props = defineProps({
  visible: Boolean,
  title: { type: String, default: '' },
  size: { type: String, default: 'md' },
})

const emit = defineEmits(['update:visible'])

function close() {
  emit('update:visible', false)
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="modal-overlay" @click.self="close">
        <div class="modal-container" :class="`modal-${size}`">
          <div class="modal-header">
            <h3>{{ title }}</h3>
            <div class="modal-header-actions">
              <slot name="header-actions" />
              <button class="modal-close-btn" @click="close">✕</button>
            </div>
          </div>
          <div class="modal-body">
            <slot />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; z-index: 9999;
  background: rgba(31,29,24,0.45);
  display: flex; align-items: center; justify-content: center;
  padding: 32px;
}
.modal-container {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-xl);
  box-shadow: var(--shadow-pop);
  max-height: 85vh;
  display: flex; flex-direction: column;
  overflow: hidden;
}
.modal-sm { width: 360px; max-width: 95vw; }
.modal-md { width: 560px; max-width: 95vw; }
.modal-lg { width: 980px; max-width: 98vw; }

.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--line);
  flex-shrink: 0;
}
.modal-header h3 {
  margin: 0; font-size: 15px; font-weight: 600; color: var(--ink);
}
.modal-header-actions {
  display: flex; align-items: center; gap: 8px;
}
.modal-close-btn {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  background: var(--surface); border: 1px solid var(--line-2);
  border-radius: var(--r-md); color: var(--ink-2);
  cursor: pointer; font-size: 14px;
  transition: 0.12s;
}
.modal-close-btn:hover { background: var(--paper-2); color: var(--ink); }

.modal-body {
  flex: 1; overflow-y: auto; padding: 18px;
}

.modal-fade-enter-active, .modal-fade-leave-active {
  transition: opacity 0.15s ease;
}
.modal-fade-enter-from, .modal-fade-leave-to {
  opacity: 0;
}
</style>
