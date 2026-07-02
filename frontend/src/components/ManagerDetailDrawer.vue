<script setup>
/**
 * 管理员明细抽屉
 *
 * 展示某管理员的财务摘要与所属工程明细表（可排序）。状态与计算由父组件持有
 * （测试需通过 wrapper.vm 访问），本组件只做展示与事件上抛。
 *
 * Props:
 *   - visible (Boolean): 是否显示
 *   - manager (String): 管理员姓名
 *   - loading (Boolean): 明细加载中
 *   - sortedData (Array): 已排序的工程明细行
 *   - rank (Number|String): 排名
 *   - totalProjects (Number): 在管项目数
 *   - activeCount (Number): 在建项目数
 *   - reversedCount (Number): 冲回项目数
 *   - managerRateStr (String): 转固率字符串
 *   - balance (Number): 期末余额合计
 *   - spendYTD (Number): 本年累计资本性支出
 *   - spendMo (Number): 本月资本性支出
 *   - transfer (Number): 结转额
 *   - pending (Number): 已下单待收货
 *   - projectsForDrawer (Array): 明细列表（含长度展示）
 *   - sortKey (String): 当前排序字段
 *   - sortOrder (String): 当前排序方向
 *
 * Events:
 *   - update:visible(visible): 关闭抽屉
 *   - sort(key): 请求排序（父组件调 toggleSort）
 *   - export(): 请求导出明细
 */
import { useFormatters } from '../composables/useFormatters'

const props = defineProps({
  visible: { type: Boolean, default: false },
  manager: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  sortedData: { type: Array, default: () => [] },
  rank: { type: [Number, String], default: '—' },
  totalProjects: { type: Number, default: 0 },
  activeCount: { type: Number, default: 0 },
  reversedCount: { type: Number, default: 0 },
  managerRateStr: { type: String, default: '0.00%' },
  balance: { type: Number, default: 0 },
  spendYtd: { type: Number, default: 0 },
  spendMo: { type: Number, default: 0 },
  transfer: { type: Number, default: 0 },
  pending: { type: Number, default: 0 },
  projectsForDrawer: { type: Array, default: () => [] },
  sortKey: { type: String, default: '' },
  sortOrder: { type: String, default: 'desc' },
})

const emit = defineEmits(['update:visible', 'sort', 'export'])
const { formatNum, formatPercent } = useFormatters()

function getSortIcon(key) {
  if (props.sortKey !== key) return '⇅'
  return props.sortOrder === 'asc' ? '↑' : '↓'
}

function getSortClass(key) {
  return props.sortKey === key ? 'active' : ''
}

function getRateClass(rate) {
  if (rate >= 1) return 'success'
  if (rate >= 0.6) return 'normal'
  if (rate >= 0.3) return 'warning'
  return 'danger'
}
</script>

<template>
  <div v-if="visible" class="mgr-drawer-overlay" @click.self="emit('update:visible', false)">
    <aside class="mgr-drawer">

      <header class="mgr-drawer-head">
        <div style="min-width:0;flex:1">
          <div class="eyebrow" style="margin-bottom:8px">工程管理员 · 明细</div>
          <h2 class="mgr-drawer-name">{{ manager }}</h2>
          <div class="mgr-drawer-meta">
            <span>排名 <strong>#{{ rank }}</strong></span>
            <span class="mgr-sep"></span>
            <span>在管 <strong>{{ totalProjects }}</strong> 项 · 在建 {{ activeCount }}</span>
            <span class="mgr-sep"></span>
            <span>转固率 <strong>{{ managerRateStr }}</strong></span>
            <span v-if="reversedCount > 0" class="ds-pill warn" style="font-size:10px;margin-left:4px">
              <span class="dot"></span>{{ reversedCount }} 项冲回
            </span>
          </div>
        </div>
        <button class="modal-close" @click="emit('update:visible', false)">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
        </button>
      </header>

      <div class="mgr-drawer-body">

        <!-- Financial summary -->
        <div class="mgr-section">
          <div class="mgr-section-head">
            <span class="mgr-section-title">财务摘要</span>
            <span class="mgr-section-sub">单位：万元</span>
          </div>
          <div class="mgr-stat-grid">
            <div class="mgr-stat">
              <div class="mgr-stat-label">在建工程期末余额</div>
              <div class="mgr-stat-value">{{ formatNum(balance) }}<span class="mgr-stat-unit">万</span></div>
            </div>
            <div class="mgr-stat">
              <div class="mgr-stat-label">本年累计资本性支出</div>
              <div class="mgr-stat-value" :style="{ color: spendYtd < 0 ? 'var(--bad)' : '' }">
                {{ formatNum(spendYtd) }}<span class="mgr-stat-unit">万</span>
              </div>
            </div>
            <div class="mgr-stat">
              <div class="mgr-stat-label">本月资本性支出</div>
              <div class="mgr-stat-value" :style="{ color: spendMo < 0 ? 'var(--bad)' : '' }">
                {{ formatNum(spendMo) }}<span class="mgr-stat-unit">万</span>
              </div>
            </div>
            <div class="mgr-stat">
              <div class="mgr-stat-label">结转额 · 期初</div>
              <div class="mgr-stat-value">{{ formatNum(transfer) }}<span class="mgr-stat-unit">万</span></div>
            </div>
            <div class="mgr-stat">
              <div class="mgr-stat-label">已下单待收货</div>
              <div class="mgr-stat-value">{{ formatNum(pending) }}<span class="mgr-stat-unit">万</span></div>
            </div>
            <div class="mgr-stat">
              <div class="mgr-stat-label">转固率</div>
              <div class="mgr-stat-value">{{ managerRateStr }}</div>
            </div>
          </div>
        </div>

        <!-- Projects detail table -->
        <div class="mgr-section">
          <div class="mgr-section-head">
            <span class="mgr-section-title">所属工程明细 · {{ projectsForDrawer.length }} 项</span>
            <span class="mgr-section-sub">期末余额合计 <strong style="color:var(--ink)">{{ formatNum(balance) }}</strong> 万</span>
          </div>
          <div v-if="loading" class="modal-loading"><div class="loader-ring"></div></div>
          <div v-else-if="projectsForDrawer.length === 0" class="modal-empty">暂无工程记录</div>
          <div v-else class="mgr-tbl-wrap">
            <table class="detail-table">
              <thead>
                <tr>
                  <th class="sortable" style="min-width:200px" @click="emit('sort', '工程名称')">
                    工程名称 <span class="sort-icon" :class="getSortClass('工程名称')">{{ getSortIcon('工程名称') }}</span>
                  </th>
                  <th class="num sortable" title="结转额" @click="emit('sort', '结转额')">
                    结转额 <span class="sort-icon" :class="getSortClass('结转额')">{{ getSortIcon('结转额') }}</span>
                  </th>
                  <th class="num sortable" title="本年累计资本性支出" @click="emit('sort', '本年累计资本性支出')">
                    本年支出 <span class="sort-icon" :class="getSortClass('本年累计资本性支出')">{{ getSortIcon('本年累计资本性支出') }}</span>
                  </th>
                  <th class="num sortable" title="已下单待收货" @click="emit('sort', '已下单待收货')">
                    已下单待收货 <span class="sort-icon" :class="getSortClass('已下单待收货')">{{ getSortIcon('已下单待收货') }}</span>
                  </th>
                  <th class="num sortable" title="本月资本性支出" @click="emit('sort', '本月资本性支出')">
                    本月支出 <span class="sort-icon" :class="getSortClass('本月资本性支出')">{{ getSortIcon('本月资本性支出') }}</span>
                  </th>
                  <th class="num sortable" title="在建工程期末余额" @click="emit('sort', '在建工程期末余额')">
                    期末余额 <span class="sort-icon" :class="getSortClass('在建工程期末余额')">{{ getSortIcon('在建工程期末余额') }}</span>
                  </th>
                  <th class="sortable" @click="emit('sort', '转固率')">
                    转固率 <span class="sort-icon" :class="getSortClass('转固率')">{{ getSortIcon('转固率') }}</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in sortedData" :key="item['工程名称']">
                  <td>
                    <div class="mgr-proj-name" :title="item['工程名称']">{{ item['工程名称'] }}</div>
                  </td>
                  <td class="num mono muted">{{ formatNum(item['结转额']) }}</td>
                  <td class="num mono" :class="(Number(item['本年累计资本性支出']) || 0) < 0 ? 'val-bad' : ''">
                    {{ formatNum(item['本年累计资本性支出']) }}
                  </td>
                  <td class="num mono muted">{{ formatNum(item['已下单待收货']) }}</td>
                  <td class="num mono" :class="(Number(item['本月资本性支出']) || 0) < 0 ? 'val-bad' : ''">
                    {{ formatNum(item['本月资本性支出']) }}
                  </td>
                  <td class="num mono val-primary">{{ formatNum(item['在建工程期末余额']) }}</td>
                  <td>
                    <span class="rate-badge" :class="getRateClass(item['转固率'])">{{ formatPercent(item['转固率']) }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>

      <footer class="mgr-drawer-foot">
        <span class="muted" style="font-size:11.5px">Esc 关闭 · 点击其他姓名可跳转</span>
        <button class="ds-btn ghost" :disabled="loading || !sortedData.length" @click="emit('export')">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="none"><path d="M3 12v1.5h10V12M5 8l3 3 3-3M8 3v8" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
          导出明细
        </button>
      </footer>

    </aside>
  </div>
</template>

<style scoped>
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }
@keyframes spin { to { transform: rotate(360deg); } }

.mgr-drawer-overlay {
  position: fixed; inset: 0;
  background: rgba(31,29,24,0.35);
  z-index: 1000; backdrop-filter: blur(2px);
  animation: fadeIn 0.2s ease;
}
.mgr-drawer {
  position: fixed; top: 0; right: 0; bottom: 0;
  width: min(960px, 95vw);
  background: var(--surface); border-left: 1px solid var(--line);
  display: flex; flex-direction: column;
  box-shadow: -8px 0 32px rgba(31,29,24,0.12);
  animation: slideIn 0.22s cubic-bezier(0.22,1,0.36,1);
  overflow: hidden;
}
.mgr-drawer-head {
  display: flex; gap: 16px; align-items: flex-start;
  padding: 28px 32px 24px; border-bottom: 1px solid var(--line);
  background: var(--surface-2); flex-shrink: 0;
}
.mgr-drawer-name { font-size: 22px; font-weight: 500; color: var(--ink); letter-spacing: -0.02em; margin: 0; }
.mgr-drawer-meta {
  display: flex; gap: 12px; margin-top: 10px;
  font-size: 12px; color: var(--ink-3); flex-wrap: wrap; align-items: center;
}
.mgr-drawer-meta strong { color: var(--ink-2); font-weight: 500; }
.mgr-sep { width: 3px; height: 3px; background: var(--ink-4); border-radius: 50%; flex-shrink: 0; align-self: center; }
.mgr-drawer-body { flex: 1; overflow-y: auto; padding: 28px 32px; display: flex; flex-direction: column; gap: 28px; }
.mgr-drawer-foot {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 32px; border-top: 1px solid var(--line);
  background: var(--surface-2); flex-shrink: 0;
}
.mgr-section {}
.mgr-section-head {
  display: flex; align-items: baseline; justify-content: space-between;
  margin-bottom: 14px;
}
.mgr-section-title { font-size: 11px; font-weight: 500; color: var(--ink-3); text-transform: uppercase; letter-spacing: 0.08em; }
.mgr-section-sub { font-size: 12px; color: var(--ink-3); }
.mgr-stat-grid {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 1px; background: var(--line);
  border: 1px solid var(--line); border-radius: var(--r-lg); overflow: hidden;
}
.mgr-stat {
  background: var(--surface); padding: 16px 18px;
}
.mgr-stat-label { font-size: 11px; color: var(--ink-3); margin-bottom: 8px; }
.mgr-stat-value { font-size: 22px; font-weight: 500; color: var(--ink); font-family: var(--font-mono); letter-spacing: -0.02em; line-height: 1; }
.mgr-stat-unit { font-size: 11px; color: var(--ink-3); margin-left: 3px; font-weight: 400; font-family: var(--font-sans); }
.modal-close {
  width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;
  background: transparent; border: 1px solid var(--line-2);
  border-radius: var(--r-md); color: var(--ink-2); cursor: pointer; transition: 0.15s; flex-shrink: 0;
}
.modal-close:hover { background: var(--paper-2); color: var(--ink); }
.modal-loading { display: flex; justify-content: center; align-items: center; padding: 60px; }
.modal-loading .loader-ring {
  width: 36px; height: 36px; border: 2px solid transparent;
  border-top-color: var(--ink-3); border-radius: 50%;
  animation: spin 1s linear infinite;
}
.modal-empty { text-align: center; padding: 60px; color: var(--ink-3); }

.mgr-tbl-wrap {
  border: 1px solid var(--line); border-radius: var(--r-lg);
  overflow-x: auto; overflow-y: visible;
}
.detail-table { width: 100%; border-collapse: collapse; white-space: nowrap; font-size: 12.5px; }
.detail-table thead th {
  padding: 10px 14px; text-align: left; font-weight: 500;
  font-size: 11px; color: var(--ink-3); text-transform: uppercase; letter-spacing: 0.06em;
  background: var(--surface-2); border-bottom: 1px solid var(--line);
  cursor: default; user-select: none; white-space: nowrap;
}
.detail-table thead th.num { text-align: right; }
.detail-table thead th.sortable { cursor: pointer; }
.detail-table thead th.sortable:hover { color: var(--ink); background: var(--paper-2); }
.detail-table .sort-icon { margin-left: 4px; font-size: 10px; opacity: 0.35; }
.detail-table .sort-icon.active { opacity: 1; color: var(--accent); }
.detail-table tbody td {
  padding: 11px 14px; border-bottom: 1px solid var(--line);
  color: var(--ink); font-variant-numeric: tabular-nums; vertical-align: middle;
}
.detail-table tbody tr:last-child td { border-bottom: none; }
.detail-table tbody tr:hover td { background: var(--surface-2); }
.detail-table .num { text-align: right; font-family: var(--font-mono); }
.detail-table .muted { color: var(--ink-3); }
.mgr-proj-name {
  max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  font-size: 13px; color: var(--ink);
}
.val-bad { color: var(--bad) !important; }
.val-primary { font-weight: 500; color: var(--ink); }
.rate-badge {
  display: inline-block; padding: 2px 8px; border-radius: 999px;
  font-size: 11.5px; font-weight: 500; font-family: var(--font-mono); white-space: nowrap;
}
.rate-badge.success { background: var(--ok-soft); color: var(--ok); }
.rate-badge.normal { background: var(--info-soft); color: var(--info); }
.rate-badge.warning { background: var(--warn-soft); color: var(--warn); }
.rate-badge.danger { background: var(--bad-soft); color: var(--bad); }
</style>
