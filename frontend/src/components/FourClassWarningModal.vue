<script setup>
/**
 * 四类工程预警明细弹窗
 *
 * 展示单类或全部四类预警明细，支持导出。状态由父组件持有，本组件只做展示与事件上抛。
 *
 * Props:
 *   - visible (Boolean): 是否显示（默认 false）
 *   - type (String): 标题/视图类型，'四类工程预警明细' 为分组全部视图，其余为单类
 *   - items (Array): 单类视图的明细行
 *   - warnings (Object): 四类预警原始数据（含 analysis_date、items），用于分组视图
 *   - recordId (Number|null): 当前记录 id，仅用于禁用导出按钮
 *   - types (Array): 四类类型常量 [{ name, key }]
 *
 * Events:
 *   - update:visible(visible): 关闭弹窗
 *   - export(): 请求导出预警清单
 */
const props = defineProps({
  visible: { type: Boolean, default: false },
  type: { type: String, default: '' },
  items: { type: Array, default: () => [] },
  warnings: { type: Object, default: null },
  recordId: { type: [Number, null], default: null },
  types: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:visible', 'export'])

function getGroupItems(groupName) {
  return props.warnings?.items?.filter(item => item.type === groupName) || []
}

function getGroupStats(groupName) {
  const items = props.warnings?.items?.filter(item => item.type === groupName) || []
  return {
    triggered: items.filter(i => i.status === '已触发' || i.status === '已触发(超期完成)').length,
    warning: items.filter(i => i.status === '预警').length,
  }
}

function getDaysClass(daysLabel, status) {
  if (!daysLabel) return ''
  const match = daysLabel.match(/\d+/)
  if (!match) return ''
  const days = parseInt(match[0])
  if (status === '已触发' || status === '已触发(超期完成)') return 'days-overdue'
  if (days <= 10) return 'days-overdue'
  if (days <= 30) return 'days-warning'
  return ''
}
</script>

<template>
  <div v-if="visible" class="four-class-modal-overlay" @click.self="emit('update:visible', false)">
    <div class="four-class-modal">
      <div class="modal-header">
        <div class="modal-title-wrap">
          <h3>{{ type }}</h3>
          <span v-if="warnings?.analysis_date" class="modal-date">数据日期：{{ warnings.analysis_date }}</span>
        </div>
        <div class="modal-header-actions">
          <button class="export-btn-primary" :disabled="!recordId" @click="emit('export')">
            <span>↓</span> 导出预警清单
          </button>
          <button class="modal-close" @click="emit('update:visible', false)">✕</button>
        </div>
      </div>
      <div class="modal-body">
        <template v-if="type === '四类工程预警明细'">
          <template v-for="t in types" :key="t.name">
            <div class="four-class-group" :class="'group-' + t.key">
              <div class="group-header">
                <span class="group-title">{{ t.name }}</span>
                <span class="group-count">已触发 {{ getGroupStats(t.name).triggered }} / 预警 {{ getGroupStats(t.name).warning }}</span>
              </div>
              <table class="data-table four-class-modal-table">
                <thead><tr><th class="col-status">状态</th><th class="col-name">工程名称</th><th class="col-accept">验收类型</th><th class="col-manager">管理员</th><th class="col-date">关键日期</th><th class="col-date">截止日期</th><th class="col-project-status">工程状态</th><th class="col-days">天数</th><th class="col-suggestion">处置建议</th></tr></thead>
                <tbody>
                  <tr v-for="item in getGroupItems(t.name)" :key="item.id" :class="'row-' + item.status">
                    <td class="col-status"><span class="status-tag" :class="item.status">{{ item.status }}</span></td>
                    <td class="col-name" :title="item.name">{{ item.name }}</td>
                    <td class="col-accept">{{ item.acceptType }}</td>
                    <td class="col-manager">{{ item.manager }}</td>
                    <td class="col-date">{{ item.keyDate }}</td>
                    <td class="col-date">{{ item.deadline || '-' }}</td>
                    <td class="col-project-status">{{ item.projectStatus || '—' }}</td>
                    <td class="col-days" :class="getDaysClass(item.daysLabel, item.status)"><span v-if="item.status === '预警' && parseInt(item.daysLabel?.match(/\d+/)?.[0]) <= 30" style="margin-right:2px">⚠️</span>{{ item.daysLabel }}</td>
                    <td class="col-suggestion">{{ item.suggestion }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </template>
        <template v-else>
          <table class="data-table four-class-modal-table">
            <thead><tr><th class="col-status">状态</th><th class="col-name">工程名称</th><th class="col-accept">验收类型</th><th class="col-manager">管理员</th><th class="col-date">关键日期</th><th class="col-date">截止日期</th><th class="col-project-status">工程状态</th><th class="col-days">天数</th><th class="col-suggestion">处置建议</th></tr></thead>
            <tbody>
              <tr v-for="item in items" :key="item.id" :class="'row-' + item.status">
                <td class="col-status"><span class="status-tag" :class="item.status">{{ item.status }}</span></td>
                <td class="col-name" :title="item.name">{{ item.name }}</td>
                <td class="col-accept">{{ item.acceptType }}</td>
                <td class="col-manager">{{ item.manager }}</td>
                <td class="col-date">{{ item.keyDate }}</td>
                <td class="col-date">{{ item.deadline || '-' }}</td>
                <td class="col-project-status">{{ item.projectStatus || '—' }}</td>
                <td class="col-days" :class="getDaysClass(item.daysLabel, item.status)"><span v-if="item.status === '预警' && parseInt(item.daysLabel?.match(/\d+/)?.[0]) <= 30" style="margin-right:2px">⚠️</span>{{ item.daysLabel }}</td>
                <td class="col-suggestion">{{ item.suggestion }}</td>
              </tr>
            </tbody>
          </table>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.four-class-modal-overlay { position: fixed; inset: 0; background: rgba(31,29,24,0.45); display: flex; align-items: center; justify-content: center; z-index: 9999; }
.four-class-modal { background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg); width: 98%; max-width: 1400px; max-height: 84vh; display: flex; flex-direction: column; box-shadow: var(--shadow-pop); }
.four-class-modal .modal-header { padding: 14px 18px; border-bottom: 1px solid var(--line); display: flex; align-items: center; justify-content: space-between; }
.four-class-modal .modal-title-wrap { display: flex; align-items: baseline; gap: 12px; }
.four-class-modal .modal-title-wrap h3 { font-size: 15px; font-weight: 600; color: var(--ink); margin: 0; }
.four-class-modal .modal-date { font-size: 11px; color: var(--ink-3); }
.four-class-modal .modal-header-actions { display: flex; align-items: center; gap: 8px; }
.four-class-modal .export-btn-primary { display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; background: var(--info); color: #fff; border: none; border-radius: var(--r-md); font-size: 12px; font-weight: 600; cursor: pointer; font-family: inherit; transition: background 0.15s; }
.four-class-modal .export-btn-primary:hover { background: #145293; }
.four-class-modal .export-btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.four-class-modal .modal-body { flex: 1; overflow: auto; padding: 14px 20px 18px; }
.four-class-modal .modal-close { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; background: var(--surface); border: 1px solid var(--line-2); border-radius: var(--r-md); color: var(--ink-2); cursor: pointer; font-size: 14px; font-family: inherit; transition: 0.15s; }
.four-class-modal .modal-close:hover { background: var(--paper-2); color: var(--ink); }
.four-class-modal-table { width: 100%; border-collapse: collapse; min-width: 1000px; table-layout: fixed; }
.four-class-modal-table th { background: var(--paper-2); color: var(--ink-3); font-weight: 500; font-size: 11px; padding: 7px 6px; text-align: left; border-bottom: 1px solid var(--line); position: sticky; top: 0; word-break: break-word; }
.four-class-modal-table td { padding: 5px 6px; border-bottom: 1px solid var(--paper-2); color: var(--ink); font-size: 11px; }
.four-class-modal-table tr:hover td { background: var(--paper); }
.four-class-modal-table .col-status { width: 48px; white-space: nowrap; }
.four-class-modal-table .col-name { width: 240px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.four-class-modal-table .col-accept { width: 64px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.four-class-modal-table .col-manager { width: 52px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.four-class-modal-table .col-date { width: 76px; white-space: nowrap; font-size: 10px; color: var(--ink-2); overflow: hidden; text-overflow: ellipsis; }
.four-class-modal-table .col-project-status { width: 100px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.four-class-modal-table .col-days { width: 72px; white-space: nowrap; font-weight: 600; overflow: hidden; text-overflow: ellipsis; }
.four-class-modal-table .col-days.days-overdue { color: var(--bad); font-weight: 700; }
.four-class-modal-table .col-days.days-warning { color: var(--bad); font-weight: 700; }
.four-class-modal-table .col-suggestion { color: var(--ink-3); font-size: 11px; white-space: normal; line-height: 1.4; width: 140px; word-break: break-word; }
.four-class-modal-table .status-tag { display: inline-block; padding: 2px 7px; border-radius: var(--r-sm); font-size: 11px; font-weight: 600; }
.four-class-modal-table .status-tag.已触发, .four-class-modal-table .row-已触发 td { background: var(--bad-soft); color: var(--bad); }
.four-class-modal-table .status-tag.预警, .four-class-modal-table .row-预警 td { color: var(--ink); }
.four-class-group { margin-bottom: 20px; }
.four-class-group .group-header { display: flex; align-items: center; gap: 12px; padding: 6px 10px; border-radius: var(--r-sm); margin-bottom: 6px; }
.four-class-group.group-liezhang .group-header { background: var(--info-soft); color: #1F497D; }
.four-class-group.group-yuzhuang .group-header { background: var(--warn-soft); color: #7B3F00; }
.four-class-group.group-guanbi .group-header { background: var(--bad-soft); color: #843C0C; }
.four-class-group.group-guazhang .group-header { background: #dde5ee; color: #244062; }
.group-title { font-weight: 700; font-size: 13px; }
.group-count { font-size: 11px; opacity: 0.8; }
</style>
