<script setup>
/**
 * 转固推进清单弹窗
 *
 * 展示各管理员待转固项目，支持目标转固率测算与导出。状态与计算由父组件持有
 * （测试需通过 wrapper.vm 访问），本组件只做展示与事件上抛。
 *
 * Props:
 *   - visible (Boolean): 是否显示
 *   - data (Array): transferPriorityData 各管理员分组
 *   - loading (Boolean): 加载中
 *   - error (String): 错误信息
 *   - exporting (Boolean): 导出中
 *   - recordId (Number|null): 当前记录 id（禁用导出按钮用）
 *   - computedTarget (Object|null): 目标测算结果
 *   - displayManagers (Array): 展示用的管理员分组列表
 *   - targetRate (String): 目标转固率输入值（双向绑定）
 *
 * Events:
 *   - update:visible(visible): 关闭弹窗
 *   - update:targetRate(value): 目标转固率输入变化
 *   - export(): 请求导出 Excel
 */
import { useFormatters } from '../composables/useFormatters'

defineProps({
  visible: { type: Boolean, default: false },
  data: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  exporting: { type: Boolean, default: false },
  recordId: { type: [Number, null], default: null },
  computedTarget: { type: Object, default: null },
  displayManagers: { type: Array, default: () => [] },
  targetRate: { type: String, default: '' },
})

const emit = defineEmits(['update:visible', 'update:targetRate', 'export'])
const { formatNum, formatPercent } = useFormatters()

function getRateClass(rate) {
  if (rate >= 1) return 'success'
  if (rate >= 0.6) return 'normal'
  if (rate >= 0.3) return 'warning'
  return 'danger'
}
</script>

<template>
  <div v-if="visible" class="tp-overlay" @click.self="emit('update:visible', false)">
    <div class="tp-modal">
      <div class="tp-header">
        <div class="tp-header-left">
          <h3>转固推进清单</h3>
          <span class="tp-subtitle">各管理员待转固项目 · 按转固贡献从高到低排序</span>
        </div>
        <div class="tp-header-actions">
          <button class="tp-export-btn" :disabled="exporting || !data.length" @click="emit('export')">
            <span v-if="exporting">导出中…</span>
            <span v-else>导出 Excel</span>
          </button>
          <button class="modal-close" @click="emit('update:visible', false)">✕</button>
        </div>
      </div>
      <div v-if="loading" class="tp-loading">
        <div class="loader-ring" style="width:32px;height:32px;position:relative"></div>
        <p>正在计算...</p>
      </div>
      <div v-else-if="error" class="tp-empty tp-error"><p>{{ error }}</p></div>
      <div v-else-if="!data.length" class="tp-empty"><p>暂无待转固项目数据</p></div>
      <template v-else>
        <div class="tp-calc-bar">
          <div class="tp-calc-left">
            <span class="tp-calc-label">转固率目标测算</span>
            <div class="tp-calc-input-wrap">
              <input :value="targetRate" type="number" min="1" max="100" step="1" placeholder="输入目标 %" class="tp-calc-input" @input="emit('update:targetRate', $event.target.value)" @keyup.enter="$event.target.blur()" />
              <span class="tp-calc-unit">%</span>
              <button v-if="targetRate" class="tp-calc-clear" @click="emit('update:targetRate', '')" title="清除">✕</button>
            </div>
          </div>
          <div class="tp-calc-result">
            <template v-if="computedTarget">
              <template v-if="computedTarget.alreadyGlobal">
                <span class="tp-calc-achieved">当前 {{ formatPercent(computedTarget.globalCurrentRate) }} 已达目标，无需额外转固</span>
              </template>
              <template v-else>
                <span class="tp-calc-from">当前 {{ formatPercent(computedTarget.globalCurrentRate) }}</span>
                <span class="tp-calc-arrow">→</span>
                <span class="tp-calc-to">目标 {{ formatPercent(computedTarget.target) }}</span>
                <span class="tp-calc-divider">|</span>
                <span class="tp-calc-desc">全局还需减少在建余额</span>
                <strong class="tp-calc-amount">{{ formatNum(computedTarget.globalRequired) }} 万元</strong>
              </template>
            </template>
            <span v-else class="tp-calc-hint">设定目标后自动测算各管理员任务量</span>
          </div>
        </div>
        <div class="tp-body">
          <div v-for="managerGroup in displayManagers" :key="managerGroup.manager" class="tp-manager-block">
            <div class="tp-manager-header">
              <div class="tp-manager-name">{{ managerGroup.manager }}</div>
              <div class="tp-manager-stats">
                <span class="tp-stat-item">
                  当前转固率
                  <strong :class="'rate-badge ' + getRateClass(managerGroup.current_rate)">
                    {{ formatPercent(managerGroup.current_rate) }}
                  </strong>
                </span>
                <span class="tp-stat-sep">·</span>
                <template v-if="!computedTarget">
                  <span class="tp-stat-item">
                    待转固余额合计
                    <strong>{{ formatNum(managerGroup.total_balance) }} 万</strong>
                  </span>
                  <span class="tp-stat-sep">·</span>
                  <span class="tp-stat-item">
                    全部完成后可达
                    <strong class="tp-target-rate">
                      {{ managerGroup.projects.length ? formatPercent(managerGroup.projects[managerGroup.projects.length - 1]['累计后转固率']) : formatPercent(managerGroup.current_rate) }}
                    </strong>
                  </span>
                </template>
                <template v-else>
                  <template v-if="managerGroup.alreadyAchieved">
                    <span class="tp-stat-achieved">已达目标 {{ formatPercent(computedTarget.target) }}，无需额外操作</span>
                  </template>
                  <template v-else>
                    <span class="tp-stat-item">
                      需减少余额
                      <strong class="tp-stat-required">{{ formatNum(managerGroup.managerRequired) }} 万</strong>
                    </span>
                    <span class="tp-stat-sep">·</span>
                    <span class="tp-stat-item" v-if="managerGroup.reachable">
                      完成前 <strong class="tp-stat-count">{{ managerGroup.neededCount }}</strong> 个项目即可达标
                    </span>
                    <span class="tp-stat-item tp-stat-warn" v-else>
                      全部项目完成仍不足，需加快其他项目转固
                    </span>
                  </template>
                </template>
              </div>
            </div>
            <div class="tp-table-wrap">
              <table class="tp-table">
                <thead>
                  <tr>
                    <th class="tp-col-rank">优先</th>
                    <th class="tp-col-name">工程名称</th>
                    <th class="tp-col-contractor">施工单位</th>
                    <th class="tp-col-balance">在建余额(万)</th>
                    <th class="tp-col-contrib">转固贡献率</th>
                    <th class="tp-col-urgency">紧迫度</th>
                    <th class="tp-col-action">完成后转固率</th>
                    <th class="tp-col-hint">紧迫说明</th>
                  </tr>
                </thead>
                <tbody>
                  <template v-for="(proj, idx) in managerGroup.projects" :key="proj['工程名称']">
                    <tr v-if="computedTarget && proj.needed === false && idx > 0 && managerGroup.projects[idx-1].needed !== false"
                        class="tp-divider-row">
                      <td colspan="8">
                        <div class="tp-divider-line">
                          <span>以下为缓冲项目（完成上方任务后已达标）</span>
                        </div>
                      </td>
                    </tr>
                  <tr :class="['tp-row', 'urgency-' + proj['紧迫度'], { 'tp-row-needed': proj.needed === true, 'tp-row-optional': proj.needed === false && computedTarget }]">
                    <td class="tp-col-rank">
                      <span class="tp-rank-badge" :class="{ 'tp-rank-top': idx < 3, 'tp-rank-needed': proj.needed === true }">{{ idx + 1 }}</span>
                    </td>
                    <td class="tp-col-name" :title="proj['工程名称']">
                      <span v-if="proj.needed === true" class="tp-needed-mark">必</span>
                      {{ proj['工程名称'] }}
                    </td>
                    <td class="tp-col-contractor" :title="proj['施工单位']">{{ proj['施工单位'] || '—' }}</td>
                    <td class="tp-col-balance">{{ formatNum(proj['在建余额']) }}</td>
                    <td class="tp-col-contrib">
                      <div class="tp-contrib-bar-wrap">
                        <div class="tp-contrib-bar" :style="{ width: Math.min(proj['转固贡献率'] * 100 / 0.3, 100) + '%' }"></div>
                        <span>{{ (proj['转固贡献率'] * 100).toFixed(1) }}%</span>
                      </div>
                    </td>
                    <td class="tp-col-urgency">
                      <span class="tp-urgency-tag" :class="'urgency-tag-' + proj['紧迫度']">{{ proj['紧迫度'] }}</span>
                    </td>
                    <td class="tp-col-action">
                      <span class="tp-after-rate">{{ formatPercent(proj['累计后转固率']) }}</span>
                      <span class="tp-rate-arrow">↑{{ ((proj['累计后转固率'] - managerGroup.current_rate) * 100).toFixed(1) }}pct</span>
                    </td>
                    <td class="tp-col-hint">
                      <template v-if="proj.urgency_detail && proj.urgency_detail.length">
                        <div v-for="(u, ui) in proj.urgency_detail" :key="ui" class="tp-hint-line">
                          <span class="tp-hint-type">{{ u.type }}</span>
                          {{ u.daysLabel }}{{ u.deadline ? ' · 截止 ' + u.deadline : '' }}
                        </div>
                      </template>
                      <span v-else class="tp-hint-normal">—</span>
                    </td>
                  </tr>
                  </template>
                </tbody>
              </table>
            </div>
            <div class="tp-manager-footer">
              <template v-if="computedTarget && !managerGroup.alreadyAchieved">
                <template v-if="managerGroup.reachable">
                  需完成 <strong>{{ managerGroup.neededCount }}</strong> 个项目（转固
                  <strong>{{ formatNum(managerGroup.neededBalance) }} 万元</strong>），
                  转固率可从 {{ formatPercent(managerGroup.current_rate) }} 升至
                  <strong>{{ formatPercent(computedTarget.target) }}</strong>
                </template>
                <template v-else>
                  即使完成所有 {{ managerGroup.projects.length }} 个项目（{{ formatNum(managerGroup.total_balance) }} 万元），
                  转固率仍不足 {{ formatPercent(computedTarget.target) }}，需关注在建工程余额以外的工程物资转固
                </template>
              </template>
              <template v-else-if="!computedTarget">
                完成前 3 项后，转固率可达
                <strong>{{ formatPercent((managerGroup.projects[Math.min(2, managerGroup.projects.length - 1)] || managerGroup.projects[0])?.['累计后转固率'] ?? managerGroup.current_rate) }}</strong>
                <span v-if="managerGroup.projects.length > 3">（还有 {{ managerGroup.projects.length - 3 }} 个项目可继续推进）</span>
              </template>
              <template v-else>
                当前转固率已达 {{ formatPercent(computedTarget.target) }} 目标
              </template>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
@keyframes spin { to { transform: rotate(360deg); } }

.tp-overlay { position: fixed; inset: 0; background: rgba(31,29,24,0.38); z-index: 1000; display: flex; align-items: flex-start; justify-content: center; padding: 28px 16px; overflow-y: auto; }
.tp-modal { background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg); width: 100%; max-width: 1240px; box-shadow: var(--shadow-pop); display: flex; flex-direction: column; }
.tp-header { display: flex; align-items: flex-start; justify-content: space-between; padding: 18px 24px 14px; border-bottom: 1px solid var(--line); }
.tp-header-left h3 { margin: 0 0 3px; font-size: 16px; font-weight: 600; color: var(--ink); }
.tp-subtitle { font-size: 12px; color: var(--ink-3); }
.tp-header-actions { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.tp-export-btn { padding: 5px 14px; font-size: 13px; font-weight: 600; color: #fff; background: var(--info); border: none; border-radius: var(--r-md); cursor: pointer; font-family: inherit; transition: background 0.15s; }
.tp-export-btn:hover:not(:disabled) { background: #1d4ed8; }
.tp-export-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.tp-loading, .tp-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px; color: var(--ink-3); gap: 12px; font-size: 13px; }
.tp-error { color: var(--bad); }
.tp-body { padding: 14px 18px 20px; display: flex; flex-direction: column; gap: 14px; }
.tp-calc-bar { display: flex; align-items: center; gap: 16px; padding: 10px 20px; background: var(--surface-2); border-bottom: 1px solid var(--line); flex-wrap: wrap; }
.tp-calc-left { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.tp-calc-label { font-size: 12px; color: var(--ink-3); white-space: nowrap; font-weight: 500; }
.tp-calc-input-wrap { display: flex; align-items: center; background: var(--surface); border: 1px solid var(--line-2); border-radius: var(--r-md); padding: 0 10px 0 8px; transition: border-color 0.15s; }
.tp-calc-input-wrap:focus-within { border-color: var(--info); }
.tp-calc-input { background: none; border: none; outline: none; color: var(--ink); font-size: 14px; font-weight: 600; font-family: var(--font-mono); width: 58px; padding: 5px 4px; text-align: right; }
.tp-calc-input::placeholder { color: var(--ink-4); font-weight: 400; font-size: 12px; font-family: var(--font-sans); }
.tp-calc-unit { font-size: 13px; color: var(--ink-3); }
.tp-calc-clear { background: none; border: none; color: var(--ink-4); cursor: pointer; font-size: 11px; padding: 0 0 0 6px; line-height: 1; font-family: inherit; }
.tp-calc-clear:hover { color: var(--ink); }
.tp-calc-result { display: flex; align-items: center; gap: 8px; font-size: 13px; flex-wrap: wrap; }
.tp-calc-from { color: var(--ink-3); }
.tp-calc-arrow { color: var(--ink-4); }
.tp-calc-to { color: var(--info); font-weight: 600; }
.tp-calc-divider { color: var(--line-2); margin: 0 2px; }
.tp-calc-desc { color: var(--ink-3); }
.tp-calc-amount { color: var(--warn); font-size: 14px; font-weight: 700; }
.tp-calc-achieved { color: var(--ok); font-size: 13px; font-weight: 600; }
.tp-manager-block { background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-md); overflow: hidden; }
.tp-manager-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; background: var(--surface-2); border-bottom: 1px solid var(--line); flex-wrap: wrap; gap: 8px; }
.tp-manager-name { font-size: 13px; font-weight: 600; color: var(--ink); }
.tp-manager-stats { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--ink-3); flex-wrap: wrap; }
.tp-stat-item { display: flex; align-items: center; gap: 5px; }
.tp-stat-sep { color: var(--line-2); }
.tp-stat-count { color: var(--info) !important; font-weight: 700 !important; }
.tp-stat-required { color: var(--warn) !important; font-weight: 700 !important; }
.tp-stat-achieved { font-size: 12px; color: var(--ok); font-weight: 500; }
.tp-stat-warn { color: var(--bad) !important; font-size: 12px; }
.tp-calc-hint { font-size: 12px; color: var(--ink-4); }
.tp-hint-type { font-weight: 600; color: var(--ink-2); margin-right: 4px; }
.tp-target-rate { color: var(--ok) !important; font-weight: 700 !important; }
.tp-table-wrap { overflow-x: auto; }
.tp-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.tp-table th { padding: 7px 10px; text-align: left; font-weight: 500; color: var(--ink-3); background: var(--paper-2); white-space: nowrap; border-bottom: 1px solid var(--line); font-size: 11px; }
.tp-table td { padding: 8px 10px; border-bottom: 1px solid var(--paper-2); vertical-align: middle; color: var(--ink); font-size: 12px; }
.tp-row:last-child td { border-bottom: none; }
.tp-row.urgency-已逾期 { background: var(--bad-soft); }
.tp-row.urgency-即将到期 { background: var(--warn-soft); }
.tp-col-rank { width: 42px; text-align: center; }
.tp-col-name { max-width: 240px; }
.tp-col-contractor { max-width: 120px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tp-col-balance, .tp-col-contrib, .tp-col-urgency, .tp-col-action { white-space: nowrap; }
.tp-col-hint { font-size: 11px; color: var(--ink-3); min-width: 160px; }
.tp-rank-badge { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 50%; font-size: 11px; font-weight: 600; background: var(--paper-2); color: var(--ink-3); font-family: var(--font-mono); }
.tp-rank-badge.tp-rank-top { background: var(--info-soft); color: var(--info); }
.tp-contrib-bar-wrap { display: flex; align-items: center; gap: 7px; }
.tp-contrib-bar { height: 5px; background: linear-gradient(90deg, var(--info), var(--ok)); border-radius: 3px; min-width: 4px; max-width: 80px; transition: width 0.3s; }
.tp-urgency-tag { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 500; }
.urgency-tag-已逾期 { background: var(--bad-soft); color: var(--bad); border: 1px solid #e0b8ad; }
.urgency-tag-即将到期 { background: var(--warn-soft); color: var(--warn); border: 1px solid #e8c98a; }
.urgency-tag-正常 { background: var(--paper-2); color: var(--ink-3); border: 1px solid var(--line); }
.tp-after-rate { font-weight: 700; color: var(--ok); margin-right: 4px; }
.tp-rate-arrow { font-size: 11px; color: var(--ink-3); }
.tp-hint-line { margin-bottom: 2px; }
.tp-hint-normal { color: var(--ink-4); }
.tp-row-needed { background: var(--warn-soft) !important; border-left: 2px solid var(--warn); }
.tp-row-optional { opacity: 0.55; }
.tp-needed-mark { display: inline-flex; align-items: center; justify-content: center; width: 16px; height: 16px; border-radius: var(--r-sm); background: var(--warn-soft); color: var(--warn); font-size: 10px; font-weight: 700; margin-right: 5px; flex-shrink: 0; border: 1px solid #e8c98a; }
.tp-rank-needed { background: var(--warn-soft) !important; color: var(--warn) !important; border: 1px solid #e8c98a; }
.tp-divider-row td { padding: 0; border: none !important; background: transparent; }
.tp-divider-line { display: flex; align-items: center; gap: 10px; padding: 5px 10px; font-size: 11px; color: var(--ink-4); }
.tp-divider-line::before, .tp-divider-line::after { content: ''; flex: 1; height: 1px; background: var(--line); }
.tp-manager-footer { padding: 8px 16px; font-size: 12px; color: var(--ink-3); border-top: 1px solid var(--line); background: var(--surface-2); }
.tp-manager-footer strong { color: var(--ok); margin: 0 3px; }
.tp-btn { font-size: 12px; display: flex; align-items: center; gap: 5px; }
/* 共享样式（本组件自带，与 ManagerDetailDrawer 重复，后续可抽公共 CSS） */
.modal-close {
  width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;
  background: transparent; border: 1px solid var(--line-2);
  border-radius: var(--r-md); color: var(--ink-2); cursor: pointer; transition: 0.15s; flex-shrink: 0;
}
.modal-close:hover { background: var(--paper-2); color: var(--ink); }
.rate-badge {
  display: inline-block; padding: 2px 8px; border-radius: 999px;
  font-size: 11.5px; font-weight: 500; font-family: var(--font-mono); white-space: nowrap;
}
.rate-badge.success { background: var(--ok-soft); color: var(--ok); }
.rate-badge.normal { background: var(--info-soft); color: var(--info); }
.rate-badge.warning { background: var(--warn-soft); color: var(--warn); }
.rate-badge.danger { background: var(--bad-soft); color: var(--bad); }
.loader-ring {
  border: 3px solid transparent; border-top-color: var(--ink-3); border-radius: 50%;
  animation: spin 1s linear infinite;
}
</style>
