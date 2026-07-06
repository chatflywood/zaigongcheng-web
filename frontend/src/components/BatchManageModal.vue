<script setup>
/**
 * 批次管理弹窗 + 专业管理抽屉
 *
 * 承载 Budget.vue 的「新增/编辑批次」弹窗与「管理专业列表」抽屉两块交互。
 * 状态与计算由父组件持有（测试需通过 wrapper.vm 访问），本组件只做展示与事件上举。
 *
 * Props:
 *   - modalVisible (Boolean): 批次弹窗是否显示
 *   - modalMode (String): 'create' | 'edit'
 *   - modalForm (Object): batchModal.form，含 batch_date / note / amounts / notes（对象引用，子组件直接 v-model 其字段）
 *   - noteFieldsOpen (Object): 各专业批注折叠状态（reactive 对象，读取用，切换走 emit）
 *   - specialties (Array): batchData.specialties，表格列序
 *   - specialtyVisible (Boolean): 专业抽屉是否显示
 *   - specialtyList (Array): 专业列表
 *   - editingSpecialty (Object|null): 正在重命名的专业对象（v-model .name 字段）
 *   - newSpecialtyName (String): 新增专业名输入值（双向绑定）
 *   - modalSubtotal (Number|String): 本批小计
 *   - modalLoading (Boolean): 保存中
 *
 * Events:
 *   - update:modal-visible(visible): 关闭批次弹窗
 *   - update:specialty-visible(visible): 关闭专业抽屉
 *   - update:editing-specialty(obj|null): 取消/退出重命名
 *   - update:new-specialty-name(value): 新增专业名输入
 *   - close-batch-modal(): 关闭批次弹窗
 *   - set-amount(specialty, value): 专业金额输入变更
 *   - toggle-note-field(s): 切换某专业批注折叠
 *   - save-batch(): 保存批次
 *   - start-edit-specialty(s): 进入重命名
 *   - save-specialty-edit(): 提交重命名
 *   - add-new-specialty(): 添加新专业
 *   - confirm-delete-specialty(s): 删除专业
 */

defineProps({
  modalVisible: { type: Boolean, default: false },
  modalMode: { type: String, default: 'create' },
  modalForm: { type: Object, required: true },
  noteFieldsOpen: { type: Object, default: () => ({}) },
  specialties: { type: Array, default: () => [] },
  specialtyVisible: { type: Boolean, default: false },
  specialtyList: { type: Array, default: () => [] },
  editingSpecialty: { type: Object, default: null },
  newSpecialtyName: { type: String, default: '' },
  modalSubtotal: { type: [Number, String], default: 0 },
  modalLoading: { type: Boolean, default: false },
})

const emit = defineEmits([
  'update:modal-visible',
  'update:specialty-visible',
  'update:editing-specialty',
  'update:new-specialty-name',
  'close-batch-modal',
  'set-amount',
  'toggle-note-field',
  'save-batch',
  'start-edit-specialty',
  'save-specialty-edit',
  'add-new-specialty',
  'confirm-delete-specialty',
])

function formatBatchNum(v) {
  if (v === null || v === undefined || v === 0) return '—'
  return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>

<template>
  <!-- ── 新增 / 编辑批次弹窗 ── -->
  <div v-if="modalVisible" class="modal-overlay" @click.self="emit('update:modal-visible', false)">
    <div class="modal-box batch-modal-box">
      <div class="modal-head">
        <h3>{{ modalMode === 'create' ? '新增批次' : '编辑批次' }}</h3>
        <button class="modal-close" @click="emit('close-batch-modal')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
      <div class="modal-body">
        <div class="form-row">
          <label class="form-label">批次日期</label>
          <input type="date" v-model="modalForm.batch_date" class="form-input" />
        </div>
        <div class="form-row">
          <label class="form-label">用途说明</label>
          <textarea v-model="modalForm.note" class="form-textarea" rows="2"
            placeholder="简述本次批次下达的用途、专项背景..."></textarea>
        </div>
        <div class="form-section-title">
          各专业下达金额
          <span class="form-section-hint">（万元，不填为 0，支持负数表示调减）</span>
        </div>
        <div class="amounts-grid">
          <div v-for="s in specialties" :key="s" class="amount-cell">
            <div class="amount-cell-top">
              <label class="amount-label" :title="s">{{ s }}</label>
              <button class="btn-note-toggle"
                :class="{ active: modalForm.notes[s] || noteFieldsOpen[s] }"
                @click="emit('toggle-note-field', s)">批注</button>
            </div>
            <input type="number" step="0.001"
              :value="modalForm.amounts[s] ?? ''"
              @input="emit('set-amount', s, $event.target.value)"
              class="amount-input" placeholder="—" />
            <textarea v-if="noteFieldsOpen[s] || modalForm.notes[s]"
              v-model="modalForm.notes[s]"
              class="amount-note-textarea"
              placeholder="输入此专业的批注说明..."
              rows="2"></textarea>
          </div>
        </div>
        <div class="modal-subtotal-bar">
          本批小计：<strong class="mono">{{ formatBatchNum(modalSubtotal) }}</strong> 万元
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn ghost" @click="emit('close-batch-modal')">取消</button>
        <button class="btn primary" @click="emit('save-batch')" :disabled="modalLoading">
          {{ modalLoading ? '保存中...' : '保存批次' }}
        </button>
      </div>
    </div>
  </div>

  <!-- ── 专业管理抽屉 ── -->
  <div v-if="specialtyVisible" class="specialty-overlay" @click.self="emit('update:specialty-visible', false)">
    <aside class="specialty-drawer">
      <div class="specialty-drawer-head">
        <div>
          <h3>管理专业列表</h3>
          <p>共 {{ specialtyList.length }} 个专业 · 顺序即表格列顺序</p>
        </div>
        <button class="modal-close" @click="emit('update:specialty-visible', false)">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
      <div class="specialty-list">
        <div v-for="s in specialtyList" :key="s.id" class="specialty-item">
          <template v-if="editingSpecialty?.id === s.id">
            <input v-model="editingSpecialty.name" class="specialty-edit-input"
              @keyup.enter="emit('save-specialty-edit')" @keyup.escape="emit('update:editing-specialty', null)" />
            <button class="btn-sm" @click="emit('save-specialty-edit')">保存</button>
            <button class="btn-sm ghost" @click="emit('update:editing-specialty', null)">取消</button>
          </template>
          <template v-else>
            <span class="specialty-item-name">{{ s.name }}</span>
            <div class="specialty-item-ops">
              <button class="btn-sm ghost" @click="emit('start-edit-specialty', s)">重命名</button>
              <button class="btn-sm danger" @click="emit('confirm-delete-specialty', s)">删除</button>
            </div>
          </template>
        </div>
      </div>
      <div class="specialty-add-row">
        <input :value="newSpecialtyName" class="form-input specialty-add-input"
          placeholder="输入新增专业名称"
          @input="emit('update:new-specialty-name', $event.target.value)"
          @keyup.enter="emit('add-new-specialty')" />
        <button class="btn primary" @click="emit('add-new-specialty')" :disabled="!newSpecialtyName.trim()">添加</button>
      </div>
      <p class="specialty-footer-hint">重命名后，所有历史批次对应金额会自动更新专业名。</p>
    </aside>
  </div>
</template>

<style scoped>
/* 批次弹窗 */
.batch-modal-box {
  width: min(700px, 96vw); max-height: 90vh;
  display: flex; flex-direction: column;
}
.modal-body { overflow-y: auto; flex: 1; padding: 24px 28px; }
.form-row { margin-bottom: 18px; }
.form-label { display: block; font-size: 12px; font-weight: 500; color: var(--ink-2); margin-bottom: 8px; }
.form-input {
  width: 100%; padding: 8px 12px; border-radius: var(--r-md);
  border: 1px solid var(--line-2); background: var(--surface);
  color: var(--ink); font-size: 13px; font-family: inherit; outline: none; box-sizing: border-box;
}
.form-input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(46,117,182,0.12); }
.form-textarea {
  width: 100%; padding: 8px 12px; border-radius: var(--r-md);
  border: 1px solid var(--line-2); background: var(--surface);
  color: var(--ink); font-size: 13px; font-family: inherit; outline: none;
  resize: vertical; box-sizing: border-box;
}
.form-textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(46,117,182,0.12); }
.form-section-title {
  font-size: 12px; font-weight: 600; color: var(--ink-2);
  margin: 22px 0 14px; padding-bottom: 8px; border-bottom: 1px solid var(--line);
}
.form-section-hint { font-weight: 400; color: var(--ink-4); font-size: 11px; }

/* 金额输入网格 */
.amounts-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px 20px; }
.amount-cell { display: flex; flex-direction: column; gap: 5px; }
.amount-cell-top { display: flex; justify-content: space-between; align-items: center; gap: 4px; }
.amount-label {
  font-size: 11px; color: var(--ink-3); white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; font-weight: 500; flex: 1; min-width: 0;
}
.btn-note-toggle {
  flex-shrink: 0; font-size: 10px; padding: 1px 6px;
  border: 1px solid var(--line-2); border-radius: 3px;
  background: none; color: var(--ink-4); cursor: pointer; font-family: inherit;
  transition: all .15s; line-height: 1.6;
}
.btn-note-toggle:hover { border-color: var(--ink-3); color: var(--ink-2); }
.btn-note-toggle.active { border-color: #d97706; color: #d97706; background: #fffbeb; }
.amount-input {
  padding: 8px 12px; border-radius: var(--r-sm);
  border: 1px solid var(--line-2); background: var(--surface);
  color: var(--ink); font-size: 12px; font-family: var(--font-mono); outline: none;
  text-align: right; width: 100%; box-sizing: border-box;
}
.amount-input:focus { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(46,117,182,0.1); }
.amount-note-textarea {
  width: 100%; font-size: 11px; line-height: 1.5;
  border: 1px solid #fcd34d; border-radius: var(--r-sm);
  padding: 5px 8px; resize: vertical; font-family: inherit;
  background: #fffdf5; color: var(--ink); outline: none; box-sizing: border-box;
}
.amount-note-textarea:focus { border-color: #d97706; }

.modal-subtotal-bar {
  margin-top: 18px; padding: 12px 16px; border-radius: var(--r-md);
  background: var(--surface); font-size: 13px; color: var(--ink-2); text-align: right;
}
.modal-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 16px 28px; border-top: 1px solid var(--line);
}

/* ── 共享按钮（弹窗内自用副本，避免父组件 scoped 失效） ── */
.btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 14px; border-radius: var(--r-sm);
  font-size: 12.5px; font-weight: 500; cursor: pointer;
  border: 1px solid var(--line-2); background: var(--surface);
  color: var(--ink-2); font-family: inherit; transition: all 0.15s;
}
.btn:hover { background: var(--paper-2); color: var(--ink); border-color: var(--ink-4); }
.btn.primary { background: var(--ink); color: var(--paper); border-color: var(--ink); }
.btn.primary:hover { background: var(--accent); border-color: var(--accent); color: #fff; }
.btn.ghost { background: transparent; border-color: transparent; color: var(--ink-2); }
.btn.ghost:hover { background: var(--paper-2); }
.btn svg { width: 12px; height: 12px; opacity: 0.7; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* 小按钮 */
.btn-sm {
  padding: 3px 10px; border-radius: var(--r-sm); font-size: 11px;
  border: 1px solid var(--line-2); background: none; cursor: pointer;
  color: var(--ink-2); font-family: inherit; transition: all 0.15s;
}
.btn-sm:hover { background: var(--surface); }
.btn-sm.ghost { color: var(--ink-3); }
.btn-sm.danger { color: var(--bad); border-color: rgba(192,0,0,0.25); }
.btn-sm.danger:hover { background: rgba(192,0,0,0.06); }

/* 专业管理抽屉 */
.specialty-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.35); z-index: 1000;
  display: flex; align-items: stretch; justify-content: flex-end;
}
.specialty-drawer {
  width: 360px; background: var(--paper); box-shadow: -4px 0 32px rgba(0,0,0,0.18);
  display: flex; flex-direction: column; overflow: hidden;
}
.specialty-drawer-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding: 20px 20px 16px; border-bottom: 1px solid var(--line);
}
.specialty-drawer-head h3 { margin: 0 0 2px; font-size: 15px; color: var(--ink); }
.specialty-drawer-head p { margin: 0; font-size: 12px; color: var(--ink-3); }
.specialty-list { flex: 1; overflow-y: auto; padding: 8px 0; }
.specialty-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 16px; border-bottom: 1px solid var(--line);
}
.specialty-item:last-child { border-bottom: none; }
.specialty-item-name { flex: 1; font-size: 13px; color: var(--ink); }
.specialty-item-ops { display: flex; gap: 4px; flex-shrink: 0; }
.specialty-edit-input {
  flex: 1; padding: 4px 8px; border-radius: var(--r-sm);
  border: 1px solid var(--accent); background: var(--surface);
  color: var(--ink); font-size: 13px; font-family: inherit; outline: none;
}
.specialty-add-row { display: flex; gap: 8px; padding: 12px 16px; border-top: 1px solid var(--line); }
.specialty-add-input { flex: 1; }
.specialty-footer-hint { margin: 0; padding: 8px 16px 16px; font-size: 11px; color: var(--ink-4); line-height: 1.5; }
</style>