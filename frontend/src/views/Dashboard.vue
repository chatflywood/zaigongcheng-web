<template>
  <div class="dashboard">
    <!-- ── Upload-only state (no data yet) ── -->
    <div v-if="!hasData" class="upload-section">
      <div class="upload-shell">
        <div class="upload-page-header">
          <div class="upload-page-header-row">
            <div>
              <h1>在建工程</h1>
              <p>设置当期目标，上传明细后自动生成支出进度与管理员排名</p>
            </div>
          </div>
        </div>
        <div class="upload-container">
          <div class="upload-copy">
            <div class="upload-copy-top">
              <span class="panel-kicker">Capital Expenditure Intake</span>
            </div>
            <div class="inline-target-card">
              <div class="inline-target-header">
                <h3>设置当期资本性支出目标</h3>
              </div>
              <div class="target-inline-form">
                <span class="target-label">目标金额</span>
                <div class="input-wrap">
                  <input type="number" v-model.number="targetValue" placeholder="如 503" @keyup.enter="confirmTargetValue" />
                  <span class="unit">万元</span>
                </div>
                <button class="confirm-btn" @click="confirmTargetValue">确认</button>
              </div>
              <div class="target-divider"></div>
              <div class="upload-checklist">
                <div class="check-item">
                  <span class="check-icon">✓</span>
                  <span>上传后自动计算支出进度、待收货压力和管理员排名</span>
                </div>
                <div class="check-item">
                  <span class="check-icon">✓</span>
                  <span>同名文件自动覆盖，保留历史快照可随时回溯</span>
                </div>
                <div class="check-item">
                  <span class="check-icon">✓</span>
                  <span>必需列：工程管理员、结转额、在建工程期末余额等</span>
                </div>
              </div>
            </div>
          </div>
          <div class="upload-box">
            <div class="upload-zone" @dragover.prevent @drop.prevent="handleDrop" @click="triggerFileInput">
              <template v-if="selectedFileName">
                <div class="selected-file-banner">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <circle cx="10" cy="10" r="9" stroke="#047857" stroke-width="1.2"/>
                    <path d="M6 10l3 3 5-5" stroke="#047857" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  <div class="selected-file-copy">
                    <div class="selected-file-name">{{ selectedFileName }}</div>
                    <div class="selected-file-meta">已选择文件 · 等待上传</div>
                  </div>
                  <span class="selected-file-change" @click.stop="clearSelectedFile">更换</span>
                </div>
              </template>
              <template v-else>
                <div class="upload-icon-wrap">
                  <svg class="upload-icon" viewBox="0 0 34 34" fill="none">
                    <rect x="4" y="7" width="26" height="22" rx="3" stroke="currentColor" stroke-width="1.2"/>
                    <path d="M11 14h12M11 18.5h8" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                    <path d="M21.5 3v7M18 6l3.5-3.5L25 6" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
                <h2>拖拽文件到此处，或<span class="link">点击选择</span></h2>
                <p class="upload-hint">支持 .xlsx 格式 · 在建工程明细总表</p>
                <div class="file-types">
                  <span class="file-tag">.xlsx</span>
                  <span class="file-tag">在建工程明细总表</span>
                </div>
              </template>
            </div>
            <div class="upload-footer">
              <div class="upload-last">
                <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
                  <circle cx="5.5" cy="5.5" r="4" stroke="currentColor" stroke-width="1"/>
                  <path d="M5.5 3v2.5l1.5 1" stroke="currentColor" stroke-width="1" stroke-linecap="round"/>
                </svg>
                <span>上次上传：</span>
                <strong>{{ recentHistoryCards[0] ? formatHistoryDateOnly(recentHistoryCards[0].uploaded_at) : '暂无' }}</strong>
              </div>
              <div class="auto-upload-tip">{{ loading ? '分析中...' : '上传后自动分析' }}</div>
            </div>
            <div v-if="uploadMessage" class="upload-feedback" :class="uploadMessageType">{{ uploadMessage }}</div>
            <input ref="fileInput" type="file" accept=".xlsx,.xls" @change="handleFileChange" hidden />
          </div>
        </div>
        <div v-if="recentHistoryCards.length" class="recent-uploads-card">
          <div class="recent-uploads-head">
            <h3>最近上传记录</h3>
            <button class="view-all-btn" @click="openHistoryPanel">查看全部 →</button>
          </div>
          <div class="recent-uploads-grid">
            <button v-for="record in recentHistoryCards" :key="record.id" class="recent-upload-item" @click="onViewHistorySnapshot(record.id)">
              <div class="recent-upload-date">{{ formatHistoryDateOnly(record.uploaded_at) }}</div>
              <div class="recent-upload-value">{{ formatNum(record.dashboard_snapshot?.metrics?.capital || 0) }} <span>万元</span></div>
              <div class="recent-upload-meta">目标 {{ formatNum(record.target_value || 0) }} · {{ formatHistoryProgress(record) }}</div>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Data state (dashboard with data) ── -->
    <div v-else class="page">
      <!-- Page header -->
      <header class="page-head">
        <div class="page-head-l">
          <span class="eyebrow">在建工程 / Capex Tracking</span>
          <h1 class="page-title">在建工程进度</h1>
          <div class="page-meta">
            <span>在建工程分析.xlsx</span>
            <span class="sep"></span>
            <span>共 {{ summaryRows.length }} 人 · 年度目标
              <template v-if="!editingTarget">
                {{ targetValue || '—' }} 万
                <button v-if="currentRecordId" class="target-edit-btn" @click="startEditTarget" title="修改目标">
                  <svg width="12" height="12" viewBox="0 0 16 16" fill="none"><path d="M11.5 2.5l2 2L5 13H3v-2l8.5-8.5z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </button>
              </template>
              <template v-else>
                <input ref="targetEditInput" type="number" v-model.number="targetEditValue" class="target-inline-input" @keyup.enter="confirmEditTarget" @keyup.escape="cancelEditTarget" />
                <button class="target-save-btn" @click="confirmEditTarget" :disabled="targetSaving">{{ targetSaving ? '…' : '✓' }}</button>
                <button class="target-cancel-btn" @click="cancelEditTarget">✕</button>
              </template>
            </span>
            <template v-if="displayAnalysisDate">
              <span class="sep"></span>
              <span>{{ displayAnalysisDate }}</span>
            </template>
          </div>
        </div>
        <div class="page-actions">
          <button v-if="(isViewingHistory || props.snapshotLabel) && (props.latestData || props.initialData)" class="btn ghost" @click="restoreLatestView">
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none"><path d="M2 4l1 3 3-1M14 12l-1-3-3 1M3 7a5 5 0 019-1M13 9a5 5 0 01-9 1" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
            返回最新
          </button>
        </div>
      </header>

      <!-- Upload strip (always on, even with data) -->
      <div class="upload-strip">
        <div class="up-icon">
          <svg width="18" height="18" viewBox="0 0 16 16" fill="none"><path d="M4 2h6l2 2v10H4V2zM10 2v2h2" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </div>
        <div class="up-meta">
          <div class="up-title">
            在建工程分析.xlsx
            <span v-if="currentRecordId" class="up-badge">已加载</span>
          </div>
          <div class="up-sub">
            <template v-if="displayAnalysisDate"><span>数据日期 {{ displayAnalysisDate }}</span></template>
            <span> · 共 {{ summaryRows.length }} 行</span>
            <template v-if="currentRecordId"><span> · 记录 #{{ currentRecordId }}</span></template>
          </div>
        </div>
        <div class="up-meter">
          <b>{{ summaryRows.length }}</b>
          <span>MANAGERS</span>
        </div>
        <div style="display:flex;gap:6px">
          <button class="btn ghost" @click="openHistoryPanel">
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none"><path d="M2 5h12v9H2V5zM2 5V3h12v2M5 2v3M11 2v3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
            历史记录
          </button>
        </div>
      </div>

      <!-- — KPI row — -->
      <div class="section" style="margin-bottom:48px">
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
      </div>

      <!-- History comparison (when available) -->
      <div v-if="compareOverview" class="section">
        <div class="section-head"><h2>历史对比概览</h2><span class="sub">当前版本与上一版相比</span></div>
        <div class="card" style="padding:20px">
          <div class="compare-cards-row">
            <div class="compare-card">
              <span class="compare-label">资本性支出进度</span>
              <strong>{{ formatNum(compareOverview.capital.current) }} 万元</strong>
              <span class="compare-detail">较上版 {{ formatDelta(compareOverview.capital.diff, '万元') }}</span>
              <span class="compare-detail">完成率 {{ formatDelta(compareOverview.capital.progressDiff, 'pct', true) }}</span>
            </div>
            <div class="compare-card">
              <span class="compare-label">转固率</span>
              <strong>{{ formatPercent(compareOverview.rate.current) }}</strong>
              <span class="compare-detail">较上版 {{ formatDelta(compareOverview.rate.diff, 'pct', true) }}</span>
            </div>
          </div>
          <div v-if="managerProgressTop5.length" class="compare-table-shell">
            <div class="card-header compare-subheader">
              <h4>管理员推进 Top 5</h4>
              <span class="compare-caption">{{ managerProgressTop5.length }} 位管理员</span>
            </div>
            <table class="tbl" style="font-size:12.5px">
              <thead><tr><th>工程管理员</th><th class="num">当前支出</th><th class="num">较上版变化</th></tr></thead>
              <tbody>
                <tr v-for="item in managerProgressTop5" :key="item.name">
                  <td>{{ item.name }}</td>
                  <td class="num mono">{{ formatNum(item.current) }}</td>
                  <td class="num"><span :class="item.diff >= 0 ? 'delta-up' : 'delta-down'">{{ formatDelta(item.diff, '万元') }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- — Warnings + manager ranking side by side — -->
      <div class="section">
        <div class="section-head">
          <h2>预警 & 管理员负荷</h2>
          <span class="sub">按真实数据规则推导 · 规则可在下方查看</span>
        </div>
        <div class="warning-manager-grid">
          <!-- Warnings -->
          <div class="card">
            <div class="card-head">
              <div><h3>四类工程预警</h3><div class="sub" style="margin-top:2">从数据中自动识别</div></div>
              <div style="display:flex;gap:6px">
                <button class="btn ghost tp-btn" @click="showFourClassAllDetail">
                  <svg width="12" height="12" viewBox="0 0 16 16" fill="none"><path d="M2 4h12M4 8h8M6 12h4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
                  查看全部
                </button>
              </div>
            </div>
            <div class="card-body" style="padding:0">
              <template v-if="fcWarnings?.summary">
                <div v-for="(type, idx) in fourClassTypes" :key="type.name" class="warning-item" @click="showFourClassDetail(type.name)">
                  <div style="min-width:0">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
                      <span class="pill" :class="getWarningPillClass(type.key)"><span class="dot"></span>{{ type.name }}</span>
                    </div>
                    <div v-if="type.key !== 'liezhang'" style="font-size:12px;color:var(--ink-3)">预警期 90 天</div>
                  </div>
                  <div style="font-family:var(--font-mono);font-size:24px;color:var(--ink);font-weight:500;letter-spacing:-0.02em">
                    {{ (fcWarnings.summary?.[type.name]?.triggered || 0) + (fcWarnings.summary?.[type.name]?.warning || 0) }}
                  </div>
                  <div style="font-size:10.5px;color:var(--ink-4);font-family:var(--font-mono);min-width:80px;text-align:right">
                    {{ fcWarnings.summary?.[type.name]?.triggered || 0 }} 已触发
                  </div>
                </div>
              </template>
              <div v-else class="empty" style="padding:32px 20px">暂无预警数据</div>
            </div>
          </div>

          <!-- Manager ranking -->
          <div class="card">
            <div class="card-head">
              <div><h3>管理员视图</h3><div class="sub" style="margin-top:2">数据日期：{{ displayAnalysisDate || '-' }}</div></div>
              <div style="display:flex;gap:6px">
                <button v-if="currentRecordId" class="btn ghost tp-btn" @click="openTransferPriority">
                  <svg width="12" height="12" viewBox="0 0 16 16" fill="none"><path d="M2 4h12M2 8h8M2 12h4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
                  转固推进清单
                </button>
              </div>
            </div>
            <div class="card-body" style="padding:0">
              <table class="tbl">
                <thead>
                  <tr>
                    <th style="width:36px">#</th>
                    <th>工程管理员</th>
                    <th class="num">在管</th>
                    <th class="num">本年支出</th>
                    <th class="num">结转额</th>
                    <th class="num">待收货</th>
                    <th class="num">支出变化</th>
                    <th>转固率</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, index) in summaryRows" :key="row.manager || row['工程管理员']" @click="openManagerModal(row.manager || row['工程管理员'])" style="cursor:pointer">
                    <td><span class="rank-num" :class="{ 'rank-top': index < 2 }">{{ index + 1 }}</span></td>
                    <td class="col-name link">{{ row.manager || row['工程管理员'] }}</td>
                    <td class="num mono muted">{{ getProjectCount(row.manager || row['工程管理员']) }}</td>
                    <td class="num mono" :style="{ fontWeight: 500, color: (row.capital || row['本年累计资本性支出']) < 0 ? 'var(--bad)' : 'var(--ink)' }">{{ formatNum(row.capital || row['本年累计资本性支出']) }}</td>
                    <td class="num mono muted">{{ formatNum(row.transfer || row['结转额']) }}</td>
                    <td class="num mono muted">{{ formatNum(row.pending || row['已下单待收货']) }}</td>
                    <td class="num mono" :style="{ color: getTrendDiff(row) > 0 ? 'var(--bad)' : getTrendDiff(row) < 0 ? 'var(--ok)' : 'var(--muted)' }">
                      <template v-if="getTrendDiff(row) !== null">{{ getTrendDiff(row) > 0 ? '↑' : getTrendDiff(row) < 0 ? '↓' : '—' }}{{ getTrendDiff(row) !== 0 ? Math.abs(getTrendDiff(row)).toFixed(1) : '' }}</template>
                      <template v-else>—</template>
                    </td>
                    <td style="overflow:hidden">
                      <div class="cell-bar-wrap">
                        <span class="cell-bar-pct">{{ ((row.rate || row['转固率'] || 0) * 100).toFixed(1) }}%</span>
                        <div class="cell-bar-track">
                          <div class="cell-bar-fill" :class="getRateBarClass(row.rate || row['转固率'] || 0)" :style="{ width: Math.min((row.rate || row['转固率'] || 0) * 100, 100) + '%' }"></div>
                        </div>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="progress-summary">
              <div class="ps-card">
                <div class="ps-head">
                  <span class="ps-label">支出进度</span>
                  <span class="ps-target" v-if="!editingSpendTarget">
                    当期目标 <b>{{ targetValue ? formatNum(targetValue) : '—' }}</b> 万
                    <button class="ps-edit-btn" @click="startEditSpendTarget" title="修改目标">
                      <svg width="11" height="11" viewBox="0 0 16 16" fill="none"><path d="M11.5 2.5l2 2L5 13H3v-2l8.5-8.5z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    </button>
                  </span>
                  <span class="ps-target" v-else>
                    当期目标 <input ref="spendTargetInput" type="number" v-model.number="spendTargetEdit" class="ps-inline-input" @keyup.enter="confirmEditSpendTarget" @keyup.escape="cancelEditSpendTarget" />
                    <button class="ps-save-btn" @click="confirmEditSpendTarget">✓</button>
                    <button class="ps-cancel-btn" @click="cancelEditSpendTarget">✕</button>
                  </span>
                </div>
                <div class="ps-body">
                  <div class="ps-value">{{ formatNum(dashboard?.metrics?.capital || 0) }} <span class="ps-unit">万元</span></div>
                  <div class="ps-bar-wrap">
                    <div class="ps-bar-track">
                      <div class="ps-bar-fill" :class="getProgressClass(spendProgress)" :style="{ width: Math.min(spendProgress, 100) + '%' }"></div>
                    </div>
                    <span class="ps-pct" :class="getProgressClass(spendProgress)">{{ spendProgress.toFixed(1) }}%</span>
                  </div>
                  <div class="ps-hint">{{ spendHint }}</div>
                </div>
              </div>
              <div class="ps-card">
                <div class="ps-head">
                  <span class="ps-label">转固进度</span>
                  <span class="ps-target" v-if="!editingRateTarget">
                    当期目标 <b>{{ rateTarget ? rateTarget + '%' : '—' }}</b>
                    <button class="ps-edit-btn" @click="startEditRateTarget" title="修改目标">
                      <svg width="11" height="11" viewBox="0 0 16 16" fill="none"><path d="M11.5 2.5l2 2L5 13H3v-2l8.5-8.5z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    </button>
                  </span>
                  <span class="ps-target" v-else>
                    当期目标 <input ref="rateTargetInput" type="number" v-model.number="rateTargetEdit" class="ps-inline-input" min="0" max="100" @keyup.enter="confirmEditRateTarget" @keyup.escape="cancelEditRateTarget" /> %
                    <button class="ps-save-btn" @click="confirmEditRateTarget">✓</button>
                    <button class="ps-cancel-btn" @click="cancelEditRateTarget">✕</button>
                  </span>
                </div>
                <div class="ps-body">
                  <div class="ps-value">{{ ((dashboard?.metrics?.rate || 0) * 100).toFixed(1) }}<span class="ps-unit">%</span></div>
                  <div class="ps-bar-wrap">
                    <div class="ps-bar-track">
                      <div class="ps-bar-fill" :class="getProgressClass(rateProgress)" :style="{ width: Math.min(rateProgress, 100) + '%' }"></div>
                    </div>
                    <span class="ps-pct" :class="getProgressClass(rateProgress)">{{ rateProgress.toFixed(1) }}%</span>
                  </div>
                  <div class="ps-hint">{{ rateHint }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- — Top 8 projects by balance — -->
      <div class="section">
        <div class="section-head">
          <h2>期末余额 · Top 8 项目</h2>
          <div style="display:flex;align-items:center;gap:12px">
            <span class="sub">按在建工程期末余额降序 · 单位：万元</span>
          </div>
        </div>
        <div class="card">
          <table class="tbl">
            <thead>
              <tr>
                <th style="width:28px">#</th>
                <th>工程名称</th>
                <th>管理员</th>
                <th class="num">期末余额</th>
                <th class="num">本年支出</th>
                <th class="num">待收货</th>
                <th>转固率</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(p, i) in topByBalance" :key="'bal-' + i">
                <td class="mono muted">{{ i + 1 }}</td>
                <td class="col-name" :title="p.name">{{ p.name }}</td>
                <td class="muted link" style="cursor:pointer;text-decoration:underline;text-decoration-color:var(--line-2);text-underline-offset:3px" @click.stop="openManagerModal(p.manager)">{{ p.manager }}</td>
                <td class="num mono" style="font-weight:500">{{ formatNum(p.balance) }}</td>
                <td class="num mono" :style="{ color: p.spendYTD < 0 ? 'var(--bad)' : 'var(--ink-2)' }">{{ formatNum(p.spendYTD) }}</td>
                <td class="num mono muted">{{ formatNum(p.pending) }}</td>
                <td>
                  <div class="cell-bar-wrap">
                    <span class="cell-bar-pct">{{ (p.rate * 100).toFixed(1) }}%</span>
                    <div class="cell-bar-track">
                      <div class="cell-bar-fill" :class="getRateBarClass(p.rate)" :style="{ width: Math.min(p.rate * 100, 100) + '%' }"></div>
                    </div>
                  </div>
                </td>
              </tr>
              <tr v-if="topByBalance.length === 0">
                <td colspan="7" style="text-align:center;color:var(--ink-3);padding:24px">暂无数据</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- — Top 6 most active projects — -->
      <div class="section">
        <div class="section-head">
          <h2>本年支出 · Top 6 最活跃</h2>
          <span class="sub">资本性支出金额最高的 6 个项目</span>
        </div>
        <div class="card">
          <table class="tbl">
            <thead>
              <tr>
                <th style="width:28px">#</th>
                <th>工程名称</th>
                <th>管理员</th>
                <th class="num">本年支出</th>
                <th class="num">本月支出</th>
                <th class="num">期末余额</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(p, i) in topBySpend" :key="'spend-' + i">
                <td class="mono muted">{{ i + 1 }}</td>
                <td class="col-name" :title="p.name">{{ p.name }}</td>
                <td class="muted link" style="cursor:pointer;text-decoration:underline;text-decoration-color:var(--line-2);text-underline-offset:3px" @click.stop="openManagerModal(p.manager)">{{ p.manager }}</td>
                <td class="num mono" style="font-weight:500">{{ formatNum(p.spendYTD) }}</td>
                <td class="num mono" :style="{ color: p.spendMo < 0 ? 'var(--bad)' : p.spendMo > 0 ? 'var(--ok)' : 'var(--ink-3)' }">{{ formatNum(p.spendMo) }}</td>
                <td class="num mono muted">{{ formatNum(p.balance) }}</td>
              </tr>
              <tr v-if="topBySpend.length === 0">
                <td colspan="6" style="text-align:center;color:var(--ink-3);padding:24px">暂无数据</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>

    <!-- Loading overlay -->
    <div v-if="loading" class="loading">
      <div class="loader">
        <div class="loader-ring"></div>
        <div class="loader-ring"></div>
        <div class="loader-ring"></div>
      </div>
      <p>分析中...</p>
    </div>

    <!-- History panel (full-screen overlay with tabs) -->
    <div v-if="historyVisible" class="history-overlay" @click.self="closeHistoryPanel">
      <div class="history-panel">
        <div class="history-panel-header">
          <div>
            <span class="panel-kicker">History Snapshots</span>
            <h3>历史记录中心</h3>
            <p>{{ historyRecords.length }} 条记录 · 选择某次上传可恢复快照</p>
          </div>
          <button class="drawer-close" @click="closeHistoryPanel">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          </button>
        </div>
        <div v-if="historyLoading" class="history-loading">
          <div class="loader-ring" style="width:32px;height:32px;position:relative"></div>
          <p>正在读取历史记录...</p>
        </div>
        <div v-else-if="historyRecords.length === 0" class="history-empty">
          <p>暂无历史记录</p>
        </div>
        <div v-else class="history-list">
          <button v-for="(record, index) in historyRecords" :key="record.id" class="history-item" :class="{ active: currentRecordId === record.id }" @click="onViewHistorySnapshot(record.id)">
            <div class="history-item-top">
              <strong>{{ record.source_filename }}</strong>
              <span class="history-item-id">#{{ record.id }}</span>
            </div>
            <div class="history-item-kpis">
              <span class="history-kpi-capital">{{ formatNum(record.dashboard_snapshot?.metrics?.capital || 0) }}<em>万元</em></span>
              <span class="history-kpi-progress">{{ formatHistoryProgress(record) }}</span>
              <span v-if="getCapitalDelta(record, index) !== null" class="history-kpi-delta" :class="getCapitalDelta(record, index) >= 0 ? 'delta-up' : 'delta-down'">{{ getCapitalDelta(record, index) >= 0 ? '↑' : '↓' }} {{ formatNum(Math.abs(getCapitalDelta(record, index))) }}</span>
            </div>
            <div class="history-item-meta">
              <span>{{ formatHistoryTime(record.uploaded_at) }}</span>
              <span v-if="record.file_date">{{ formatFileDate(record.file_date) }}</span>
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- Manager detail drawer -->
    <ManagerDetailDrawer
      v-model:visible="modalVisible"
      :manager="modalManager"
      :loading="modalLoading"
      :sorted-data="sortedModalData"
      :rank="modalRank"
      :total-projects="modalTotalProjects"
      :active-count="modalActiveCount"
      :reversed-count="modalReversedCount"
      :manager-rate-str="modalManagerRateStr"
      :balance="modalBalance"
      :spend-ytd="modalSpendYTD"
      :spend-mo="modalSpendMo"
      :transfer="modalTransfer"
      :pending="modalPending"
      :projects-for-drawer="modalProjectsForDrawer"
      :sort-key="sortKey"
      :sort-order="sortOrder"
      @sort="toggleSort"
      @export="exportAllManagerDetails"
    />

    <!-- Four-class detail modal -->
    <FourClassWarningModal
      v-model:visible="fourClassDetailVisible"
      :type="fourClassDetailType"
      :items="fourClassDetailItems"
      :warnings="fcWarnings"
      :record-id="currentRecordId"
      :types="fourClassTypes"
      @export="exportFourClassWarnings"
    />

    <!-- Transfer priority modal -->
    <TransferPriorityModal
      v-model:visible="transferPriorityVisible"
      v-model:target-rate="targetRate"
      :data="transferPriorityData"
      :loading="transferPriorityLoading"
      :error="transferPriorityError"
      :exporting="transferExporting"
      :record-id="currentRecordId"
      :computed-target="computedTarget"
      :display-managers="displayManagers"
      @export="handleExportTransferPriority"
    />

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { uploadExcel, getCompare, getHistorySnapshot, getManagerDetails, getTransferPriority, exportTransferPriority, pushNotify, updateTargetValue } from '../api'

import { useGlobalData } from '../composables/useGlobalData'
import { useFormatters } from '../composables/useFormatters'
import { useHistoryPanel } from '../composables/useHistoryPanel'
import { useFileUpload } from '../composables/useFileUpload'
import FourClassWarningModal from '../components/FourClassWarningModal.vue'
import ManagerDetailDrawer from '../components/ManagerDetailDrawer.vue'
import TransferPriorityModal from '../components/TransferPriorityModal.vue'

const globalData = useGlobalData()
const { formatNum, formatPercent, formatDelta, formatHistoryDateOnly } = useFormatters()
const { formatHistoryTime, formatFileDate } = globalData

// Props 优先（测试时传入），否则从 composable 读取
const _props = defineProps({
  initialData: { type: Object, default: undefined },
  initialRecordId: { type: Number, default: undefined },
  latestData: { type: Object, default: undefined },
  historyComparison: { type: Object, default: null },
  analysisDate: { type: String, default: undefined },
  snapshotLabel: { type: String, default: undefined },
  fourClassWarnings: { type: Object, default: undefined },
})

const props = {
  get initialData()       { return _props.initialData       ?? globalData.zaigongData.value },
  get initialRecordId()   { return _props.initialRecordId   ?? globalData.zaigongLatestRecordId.value },
  get latestData()        { return _props.latestData        ?? globalData.zaigongLatestData.value },
  get analysisDate()      { return _props.analysisDate      ?? globalData.zaigongDate.value },
  get snapshotLabel()     { return _props.snapshotLabel     ?? globalData.zaigongSnapshotLabel.value },
  get fourClassWarnings() { return _props.fourClassWarnings ?? globalData.zaigongFourClassWarnings.value },
  get historyComparison() { return _props.historyComparison ?? null },
}

const emit = (event, ...args) => {
  if (event === 'dataUpdate') globalData.onZaigongDataUpdate(...args)
  if (event === 'restoreLatest') globalData.onZaigongRestoreLatest()
  if (event === 'warningsUpdate') globalData.onZaigongWarningsUpdate(...args)
}

// ── Core state ──
const loading = ref(false)
const hasData = ref(false)
const showUpload = ref(false)
const dashboard = ref(null)
const summaryRows = ref([])
const maxCapital = ref(0)
const targetValue = ref(null)
const rateTarget = ref(loadPersistedRateTarget())

function loadPersistedRateTarget() {
  try {
    const v = localStorage.getItem('zaigong_rate_target')
    return v ? Number(v) : null
  } catch { return null }
}
function persistRateTarget(val) {
  try {
    if (val && val > 0 && val <= 100) {
      localStorage.setItem('zaigong_rate_target', String(val))
    } else {
      localStorage.removeItem('zaigong_rate_target')
    }
  } catch {}
}
const editingRateTarget = ref(false)
const previousData = ref(null)

// ── Manager detail (drawer) ──
const modalVisible = ref(false)
const modalData = ref([])
const modalManager = ref('')
const modalLoading = ref(false)
const sortKey = ref('本年累计资本性支出')
const sortOrder = ref('desc')

// ── History panel（composable 管理） ──
const {
  historyVisible, historyLoading, historyRecords, currentRecordId,
  isViewingHistory, snapshotDisplayDate, recentHistoryCards,
  loadHistoryList, openHistoryPanel, closeHistoryPanel, viewHistorySnapshot,
} = useHistoryPanel({ type: 'zaigong' })

// ── File upload（composable 管理；processFile 为页面业务编排，靠函数提升传引用） ──
const {
  fileInput, selectedFile, selectedFileName, uploadMessage, uploadMessageType,
  triggerFileInput, handleFileChange, handleDrop, clearSelectedFile,
} = useFileUpload({
  requireTarget: true,
  getTargetValue: () => targetValue.value,
  isReady: () => targetValue.value && Number(targetValue.value) > 0,
  processFile,
})

// ── Four-class warnings ──
const fourClassWarningsLocal = ref(null)
// 统一的可响应数据源：本地 > prop > composable 全局
const fcWarnings = ref(null)
watch(
  [fourClassWarningsLocal, () => _props.fourClassWarnings, () => globalData.zaigongFourClassWarnings.value],
  ([local, propVal, globalVal]) => { fcWarnings.value = local ?? propVal ?? globalVal ?? null },
  { immediate: true }
)
const fourClassDetailVisible = ref(false)
const fourClassDetailType = ref('')
const fourClassDetailItems = ref([])
const fourClassExpanded = ref(false)
const fourClassTypes = [
  { name: '列账不及时', key: 'liezhang' },
  { name: '预转固不及时', key: 'yuzhuang' },
  { name: '关闭不及时', key: 'guanbi' },
  { name: '长期挂账', key: 'guazhang' },
]

// ── Transfer priority ──
const transferPriorityVisible = ref(false)
const transferPriorityData = ref([])
const transferPriorityLoading = ref(false)
const targetRate = ref('')
const transferPriorityError = ref('')
const transferExporting = ref(false)
const pushingNotify = ref(false)

// ── Target editing ──
const editingTarget = ref(false)
const targetEditValue = ref(null)
const targetSaving = ref(false)
const targetEditInput = ref(null)

// ── KPI animation ──
const animatedValues = ref([])

// ── Computed: projects for tables ──
const projectsList = computed(() => {
  if (!dashboard.value?.detail) return []
  return (dashboard.value.detail || []).map(p => ({
    name: p['工程名称'] || p.name || '',
    manager: p['工程管理员'] || p.manager || '',
    balance: Number(p['在建工程期末余额'] || p.balance || 0),
    spendYTD: Number(p['本年累计资本性支出'] || p.spendYTD || p.capital || 0),
    spendMo: Number(p['本月资本性支出'] || p.spendMo || p.monthSpend || 0),
    pending: Number(p['已下单待收货'] || p.pending || 0),
    rate: Number(p['转固率'] || p.rate || 0),
  })).filter(p => p.name)
})

const topByBalance = computed(() => [...projectsList.value].sort((a, b) => b.balance - a.balance).slice(0, 8))
const topBySpend = computed(() => [...projectsList.value].filter(p => p.spendYTD > 0).sort((a, b) => b.spendYTD - a.spendYTD).slice(0, 6))

// ── Computed: history comparison ──
const displayAnalysisDate = computed(() => snapshotDisplayDate.value || _props.analysisDate || globalData.zaigongDate.value)
const comparisonSource = computed(() => _props.historyComparison || previousData.value)
const shouldShowHistoryCompare = computed(() => Boolean(_props.historyComparison))

const compareOverview = computed(() => {
  if (!shouldShowHistoryCompare.value) return null
  const previousMetrics = getSourceMetrics(comparisonSource.value)
  const currentMetrics = dashboard.value?.metrics
  if (!previousMetrics || !currentMetrics) return null
  const currentCapital = Number(currentMetrics.capital || 0)
  const previousCapital = Number(previousMetrics.capital || previousMetrics.total_current || 0)
  const currentProgress = Number(currentMetrics.progress || 0)
  const previousProgress = Number(previousMetrics.progress || previousMetrics.progress_ratio || 0)
  const currentRate = Number(currentMetrics.rate || 0)
  const previousRate = Number(previousMetrics.rate || previousMetrics.total_rate || 0)
  return {
    capital: { current: currentCapital, diff: currentCapital - previousCapital, progressDiff: (currentProgress - previousProgress) * 100 },
    rate: { current: currentRate, diff: (currentRate - previousRate) * 100 },
  }
})

const managerProgressTop5 = computed(() => {
  if (!shouldShowHistoryCompare.value) return []
  const previousSummary = getSourceSummary(comparisonSource.value)
  if (!previousSummary.length || !summaryRows.value.length) return []
  const previousMap = new Map(previousSummary.map(item => [item.manager || item['工程管理员'], Number(item.capital || item['本年累计资本性支出'] || 0)]))
  return summaryRows.value.map(item => {
    const name = item.manager || item['工程管理员']
    const current = Number(item.capital || item['本年累计资本性支出'] || 0)
    const previous = previousMap.get(name) || 0
    return { name, current, diff: current - previous }
  }).filter(item => item.diff !== 0).sort((a, b) => b.diff - a.diff).slice(0, 5)
})

// ── Per-manager trend (较上期) ──
const managerTrendMap = computed(() => {
  const source = previousData.value
  if (!source) return new Map()
  const prevSummary = source.dashboard?.summary || source.summary || []
  return new Map(prevSummary.map(item =>
    [item.manager || item['工程管理员'], Number(item.capital || item['本年累计资本性支出'] || 0)]
  ))
})

function getTrendDiff(row) {
  if (!managerTrendMap.value.size) return null
  const name = row.manager || row['工程管理员']
  const prev = managerTrendMap.value.get(name)
  if (prev === undefined) return null
  const curr = Number(row.capital || row['本年累计资本性支出'] || 0)
  return +(curr - prev).toFixed(2)
}

// recentHistoryCards 由 useHistoryPanel 提供

// ── Computed: KPI metrics ──
const pendingOverLimitCount = computed(() => summaryRows.value.filter(item => {
  const value = Number(item.pending || item['已下单待收货'] || 0)
  return value > 30
}).length)

const deficitHint = computed(() => {
  const deficit = Number(dashboard.value?.metrics?.deficit || 0)
  return deficit >= 0 ? `还差 ${formatNum(deficit)} 万` : `已超 ${formatNum(Math.abs(deficit))} 万`
})

const rateStatus = computed(() => {
  const rate = Number(dashboard.value?.metrics?.rate || 0)
  if (rate >= 0.6) return { text: '达标，目标 60%', badgeClass: 'ok' }
  return { text: '偏低，目标 60%', badgeClass: 'warn' }
})

// ── Progress summary (管理员视图底部) ──
const spendProgress = computed(() => {
  const capital = Number(dashboard.value?.metrics?.capital || 0)
  const target = Number(targetValue.value)
  if (!target || target <= 0) return 0
  return (capital / target) * 100
})

const spendHint = computed(() => {
  const capital = Number(dashboard.value?.metrics?.capital || 0)
  const target = Number(targetValue.value)
  if (!target || target <= 0) return '请设置年度目标'
  const diff = target - capital
  if (diff <= 0) return `已超额完成 ${formatNum(Math.abs(diff))} 万`
  return `距目标还差 ${formatNum(diff)} 万`
})

const rateProgress = computed(() => {
  const rate = Number(dashboard.value?.metrics?.rate || 0) * 100
  const target = Number(rateTarget.value)
  if (!target || target <= 0) return 0
  return (rate / target) * 100
})

const rateHint = computed(() => {
  const rate = Number(dashboard.value?.metrics?.rate || 0) * 100
  const target = Number(rateTarget.value)
  if (!target || target <= 0) return '请设置转固率目标'
  const diff = target - rate
  if (diff <= 0) return `已超过目标 ${Math.abs(diff).toFixed(1)} 个百分点`
  return `距目标还差 ${diff.toFixed(1)} 个百分点`
})

function getProgressClass(pct) {
  if (pct >= 90) return 'ok'
  if (pct >= 60) return 'warn'
  return 'bad'
}

// spend target inline edit
const editingSpendTarget = ref(false)
const spendTargetEdit = ref(null)
const spendTargetInput = ref(null)
function startEditSpendTarget() {
  spendTargetEdit.value = targetValue.value || null
  editingSpendTarget.value = true
  nextTick(() => spendTargetInput.value?.focus())
}
async function confirmEditSpendTarget() {
  const newTarget = Number(spendTargetEdit.value)
  if (newTarget && newTarget > 0 && newTarget !== targetValue.value) {
    targetEditValue.value = newTarget
    await confirmEditTarget()
  }
  editingSpendTarget.value = false
}
function cancelEditSpendTarget() { editingSpendTarget.value = false }

// rate target inline edit
const rateTargetEdit = ref(null)
const rateTargetInput = ref(null)
function startEditRateTarget() {
  rateTargetEdit.value = rateTarget.value || null
  editingRateTarget.value = true
  nextTick(() => rateTargetInput.value?.focus())
}
function confirmEditRateTarget() {
  if (rateTargetEdit.value && rateTargetEdit.value > 0 && rateTargetEdit.value <= 100) {
    rateTarget.value = Number(rateTargetEdit.value)
    persistRateTarget(rateTarget.value)
  }
  editingRateTarget.value = false
}
function cancelEditRateTarget() { editingRateTarget.value = false }

const metrics = computed(() => {
  if (!dashboard.value?.metrics) return []
  const m = dashboard.value.metrics
  const progressPct = targetValue.value > 0 ? ((m.capital || 0) / targetValue.value * 100).toFixed(1) : '0.0'
  return [
    {
      label: '本年累计资本性支出',
      value: (m.capital || 0).toFixed(2),
      unit: '万元',
      inlineNote: deficitHint.value,
      delta: `进度 ${progressPct}%`,
      deltaDir: 'up',
    },
    {
      label: '已下单待收货',
      value: (m.pending || 0).toFixed(2),
      unit: '万元',
    },
    {
      label: '本月资本性支出',
      value: (m.monthSpend || 0).toFixed(2),
      unit: '万元',
      valueClass: (m.monthSpend || 0) < 0 ? 'val-negative' : '',
    },
    {
      label: '综合转固率',
      value: formatPercent(m.rate || 0),
      badgeText: rateStatus.value.text,
      badgeClass: rateStatus.value.badgeClass,
      valueClass: (m.rate || 0) < 0.6 ? 'val-negative' : '',
    },
  ]
})

// ── Computed: transfer priority ──
const computedTarget = computed(() => {
  const raw = Number(targetRate.value)
  if (!targetRate.value || isNaN(raw) || raw <= 0 || raw > 100) return null
  if (!transferPriorityData.value.length) return null
  const target = raw / 100
  let globalDenom = 0, globalNumer = 0
  for (const m of transferPriorityData.value) {
    globalDenom += m.denominator
    globalNumer += (1 - m.current_rate) * m.denominator
  }
  const globalCurrentRate = globalDenom > 0 ? 1 - globalNumer / globalDenom : 0
  const globalRequired = Math.max(globalNumer - (1 - target) * globalDenom, 0)
  const managers = transferPriorityData.value.map(m => {
    const alreadyAchieved = m.current_rate >= target
    const managerRequired = alreadyAchieved ? 0 : (target - m.current_rate) * m.denominator
    const cutoffIdx = m.projects.findIndex(p => p['累计后转固率'] >= target)
    const reachable = cutoffIdx !== -1
    const projects = m.projects.map((p, idx) => ({ ...p, needed: alreadyAchieved ? false : (cutoffIdx === -1 ? true : idx <= cutoffIdx) }))
    const neededCount = alreadyAchieved ? 0 : (cutoffIdx === -1 ? m.projects.length : cutoffIdx + 1)
    const neededBalance = projects.filter(p => p.needed).reduce((s, p) => s + p['在建余额'], 0)
    return { ...m, projects, alreadyAchieved, reachable, managerRequired: Math.round(managerRequired * 100) / 100, neededCount, neededBalance: Math.round(neededBalance * 100) / 100 }
  })
  return { target, globalCurrentRate, globalRequired: Math.round(globalRequired * 100) / 100, alreadyGlobal: globalCurrentRate >= target, managers }
})

const displayManagers = computed(() => {
  if (computedTarget.value) return computedTarget.value.managers
  return transferPriorityData.value.map(m => ({
    ...m, projects: m.projects.map(p => ({ ...p, needed: null })), alreadyAchieved: false, reachable: true, managerRequired: 0, neededCount: 0, neededBalance: 0,
  }))
})

const sortedModalData = computed(() => {
  const data = [...modalData.value]
  data.sort((a, b) => {
    let aVal = a[sortKey.value], bVal = b[sortKey.value]
    if (typeof aVal === 'string') { aVal = aVal.toLowerCase(); bVal = bVal.toLowerCase() }
    else { aVal = Number(aVal) || 0; bVal = Number(bVal) || 0 }
    if (aVal < bVal) return sortOrder.value === 'asc' ? -1 : 1
    if (aVal > bVal) return sortOrder.value === 'asc' ? 1 : -1
    return 0
  })
  return data
})

// ── Transfer priority functions ──
async function openTransferPriority() {
  if (!currentRecordId.value) return
  transferPriorityVisible.value = true
  if (transferPriorityData.value.length) return
  transferPriorityLoading.value = true
  transferPriorityError.value = ''
  try {
    const result = await getTransferPriority(currentRecordId.value)
    if (result.success) { transferPriorityData.value = result.data || [] }
    else { transferPriorityError.value = result.message || '获取数据失败' }
  } catch (e) {
    console.error('获取转固优先级失败:', e)
    transferPriorityError.value = e?.response?.data?.message || e?.message || '请求失败，请检查后端服务是否已重启'
  } finally { transferPriorityLoading.value = false }
}

watch(currentRecordId, () => { transferPriorityData.value = []; transferPriorityError.value = ''; targetRate.value = '' })

async function handlePushNotify() {
  if (!currentRecordId.value || pushingNotify.value) return
  pushingNotify.value = true
  try {
    const res = await pushNotify(currentRecordId.value)
    if (res.success) alert('推送成功，请在企业微信群查看')
    else alert(res.message || '推送失败')
  } catch (e) {
    const msg = e?.response?.data?.message || e?.message || '推送失败'
    alert(msg.includes('Webhook') ? msg : `推送失败：${msg}`)
  } finally { pushingNotify.value = false }
}

async function handleExportTransferPriority() {
  if (!currentRecordId.value) return
  transferExporting.value = true
  try {
    const rate = targetRate.value ? Number(targetRate.value) : null
    const blob = await exportTransferPriority(currentRecordId.value, rate)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const suffix = rate ? `_目标${rate}pct` : ''
    a.download = `转固推进清单${suffix}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) { console.error('导出失败:', e); alert('导出失败，请重试') }
  finally { transferExporting.value = false }
}

// ── Four-class warning functions ──
function showFourClassDetail(type) {
  fourClassDetailType.value = type
  fourClassDetailItems.value = fcWarnings.value?.items?.filter(item => item.type === type) || []
  fourClassDetailVisible.value = true
}
function showFourClassAllDetail() {
  fourClassDetailType.value = '四类工程预警明细'
  fourClassDetailItems.value = fcWarnings.value?.items || []
  fourClassDetailVisible.value = true
}
// getGroupItems / getGroupStats / getDaysClass 已移入 FourClassWarningModal 组件
function getWarningPillClass(key) {
  const map = { liezhang: 'info', yuzhuang: 'warn', guanbi: 'bad', guazhang: 'info' }
  return map[key] || 'info'
}
async function exportAllManagerDetails() {
  try {
    if (!currentRecordId.value) return
    const { exportAllManagerDetailsExcel } = await import('../api')
    const blob = await exportAllManagerDetailsExcel(currentRecordId.value)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const dateStr = displayAnalysisDate.value?.replace(/-/g, '') || ''
    link.download = `全部管理员工程明细_${dateStr}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('导出明细失败:', error)
    alert('导出失败，请重试')
  }
}

async function exportFourClassWarnings() {
  try {
    const { exportFourClassExcel } = await import('../api')
    const blob = await exportFourClassExcel(currentRecordId.value)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const fileDate = fcWarnings.value?.summary?.analysis_date?.replace(/-/g, '') || ''
    link.download = `四类工程预警清单_${fileDate}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) { console.error('导出失败:', error) }
}

// ── Target editing ──
function startEditTarget() {
  targetEditValue.value = targetValue.value
  editingTarget.value = true
  nextTick(() => targetEditInput.value?.focus())
}
function cancelEditTarget() { editingTarget.value = false; targetEditValue.value = null }
async function confirmEditTarget() {
  const newTarget = Number(targetEditValue.value)
  if (!newTarget || newTarget <= 0) return
  if (newTarget === targetValue.value) { cancelEditTarget(); return }
  targetSaving.value = true
  try {
    await updateTargetValue(currentRecordId.value, newTarget)
    // Refetch snapshot from backend to get recalculated deficit and all derived fields
    const snapshot = await getHistorySnapshot(currentRecordId.value)
    if (snapshot.success && snapshot.data?.current) {
      const cur = snapshot.data.current
      applyDashboardData(cur.dashboard)
      currentRecordId.value = cur.id
      emit('dataUpdate', cur.dashboard)
    } else {
      // Fallback: local update if refetch fails
      targetValue.value = newTarget
      if (dashboard.value?.metrics) {
        const newDeficit = newTarget - (dashboard.value.metrics.capital || 0)
        dashboard.value = { ...dashboard.value, metrics: { ...dashboard.value.metrics, deficit: newDeficit, yearTarget: newTarget } }
      }
      emit('dataUpdate', dashboard.value)
    }
    editingTarget.value = false
  } catch (e) { console.error('更新目标失败', e) }
  finally { targetSaving.value = false }
}

// ── Data application ──
function applyDashboardData(data) {
  dashboard.value = data
  targetValue.value = Number(data?.metrics?.yearTarget) || null
  const rawRows = data?.summary || []
  summaryRows.value = rawRows.filter(r => r.manager !== '合计' && r['工程管理员'] !== '合计')
  hasData.value = true
  currentRecordId.value = null
  if (summaryRows.value.length > 0) {
    maxCapital.value = Math.max(...summaryRows.value.map(r => r.capital || r['本年累计资本性支出'] || 0))
  } else { maxCapital.value = 0 }
}

function applyHistorySnapshot(snapshot, previous = null) {
  if (!snapshot?.dashboard) return
  applyDashboardData(snapshot.dashboard)
  targetValue.value = Number(snapshot.dashboard.metrics?.yearTarget) || Number(snapshot.target_value) || null
  currentRecordId.value = snapshot.id
  previousData.value = previous
  isViewingHistory.value = true
  snapshotDisplayDate.value = snapshot.file_date ? formatFileDate(snapshot.file_date) : formatHistoryTime(snapshot.uploaded_at)
  fourClassWarningsLocal.value = snapshot.four_class_warnings || null
}

// ── File handling ──
// triggerFileInput / handleFileChange / handleDrop / clearSelectedFile 由 useFileUpload 提供
function confirmTargetValue() {
  if (!targetValue.value) { uploadMessage.value = '请先输入目标金额'; uploadMessageType.value = 'error'; return }
  uploadMessage.value = `目标金额已设置为 ${Number(targetValue.value).toFixed(2)} 万元`
  uploadMessageType.value = 'info'
}

async function processFile(file) {
  loading.value = true
  uploadMessage.value = '文件已提交，正在分析，请稍候...'
  uploadMessageType.value = 'info'
  try {
    const result = await uploadExcel(file, targetValue.value)
    if (result.success) {
      const data = result.data?.dashboard || result.data
      if (!data?.metrics) throw new Error('返回数据格式异常，未获取到分析结果')
      applyDashboardData(data)
      targetValue.value = Number(data.metrics?.yearTarget) || Number(targetValue.value) || null
      fourClassWarningsLocal.value = result.data?.four_class_warnings || null
      fourClassExpanded.value = false
      isViewingHistory.value = false
      snapshotDisplayDate.value = null
      showUpload.value = false
      clearSelectedFile()
      emit('dataUpdate', data)
      emit('warningsUpdate', result.data?.four_class_warnings || null)
      await fetchCompareData()
      uploadMessage.value = ''
    } else {
      uploadMessage.value = result?.message || '上传分析失败，请稍后重试'
      uploadMessageType.value = 'error'
      alert(uploadMessage.value)
    }
  } catch (error) {
    const backendMessage = error?.response?.data?.message
    uploadMessage.value = backendMessage || `分析失败：${error.message || '未知错误'}`
    uploadMessageType.value = 'error'
    alert(uploadMessage.value)
  } finally { loading.value = false }
}

// ── History ──
// loadHistoryList / openHistoryPanel / closeHistoryPanel 由 useHistoryPanel 提供
// viewHistorySnapshot 包装：composable 拉快照后，页面执行 applyHistorySnapshot（写 dashboard/targetValue/previousData 等）
async function onViewHistorySnapshot(recordId) {
  const snapshot = await viewHistorySnapshot(recordId)
  if (snapshot) applyHistorySnapshot(snapshot.current, snapshot.previous)
}

async function fetchCompareData() {
  try {
    const result = await getCompare()
    if (result.success && result.data) {
      if (result.data.latest) currentRecordId.value = result.data.latest.id
      previousData.value = result.data.previous || null
    } else { previousData.value = null }
  } catch (error) { console.error('获取对比数据失败:', error); previousData.value = null }
}

async function restoreLatestView() {
  const latest = _props.latestData ?? _props.initialData ?? globalData.zaigongLatestData.value ?? globalData.zaigongData.value
  if (!latest) return
  applyDashboardData(latest)
  isViewingHistory.value = false
  snapshotDisplayDate.value = null
  emit('restoreLatest')
  await fetchCompareData()
}

// ── Manager detail drawer ──
async function openManagerModal(manager) {
  modalManager.value = manager
  modalVisible.value = true
  modalLoading.value = true
  modalData.value = []
  try {
    if (!currentRecordId.value) {
      const result = await getCompare()
      if (result.success && result.data && result.data.latest) currentRecordId.value = result.data.latest.id
    }
    if (currentRecordId.value) {
      const res = await getManagerDetails(currentRecordId.value, manager)
      if (res.success) modalData.value = res.data.details || []
    }
  } catch (error) { console.error('获取明细失败:', error) }
  finally { modalLoading.value = false }
}
function closeModal() { modalVisible.value = false }
function toggleSort(key) {
  if (sortKey.value === key) sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  else { sortKey.value = key; sortOrder.value = 'desc' }
}
// getSortIcon / getSortClass 已移入 ManagerDetailDrawer 组件

// ── Formatting helpers ──
// formatNum / formatPercent / formatDelta / formatHistoryDateOnly 由 useFormatters 提供
// formatHistoryTime / formatFileDate 由 useGlobalData 提供
function formatHistoryProgress(record) {
  const capital = Number(record?.dashboard_snapshot?.metrics?.capital || 0)
  const target = Number(record?.target_value || 0)
  if (!target) return '未设目标'
  return `${((capital / target) * 100).toFixed(1)}%`
}
function getCapitalDelta(record, index) {
  const prev = historyRecords.value[index + 1]
  if (!prev) return null
  return Number(record?.dashboard_snapshot?.metrics?.capital || 0) - Number(prev?.dashboard_snapshot?.metrics?.capital || 0)
}
function getRateBarClass(rate) {
  if (rate >= 0.9) return 'ok'
  if (rate >= 0.6) return 'warn'
  return 'bad'
}
// getRateClass 已移入 ManagerDetailDrawer / TransferPriorityModal 组件
function getSourceMetrics(source) {
  if (!source) return null
  return source.dashboard?.metrics || source.metrics || null
}
function getSourceSummary(source) {
  if (!source) return []
  return source.dashboard?.summary || source.summary || []
}
function getPreviousCapital(manager) {
  const prevSummary = getSourceSummary(comparisonSource.value)
  if (!prevSummary.length) return null
  const prev = prevSummary.find(r => (r.manager || r['工程管理员']) === manager)
  return prev ? (prev.capital || prev['本年累计资本性支出']) : null
}
function getChangeClass(manager, currentCapital) {
  const prev = getPreviousCapital(manager)
  if (prev === null || isNaN(currentCapital) || isNaN(prev)) return 'no-change'
  const currentRounded = Math.round(currentCapital * 100) / 100
  const prevRounded = Math.round(prev * 100) / 100
  if (currentRounded === prevRounded) return 'no-change'
  const diff = currentCapital - prev
  if (isNaN(diff)) return 'no-change'
  if (diff > 0) return 'change-up'
  if (diff < 0) return 'change-down'
  return 'no-change'
}
function getChangeText(manager, currentCapital) {
  const prev = getPreviousCapital(manager)
  if (prev === null || isNaN(currentCapital) || isNaN(prev)) return '— 0.00'
  const currentRounded = Math.round(currentCapital * 100) / 100
  const prevRounded = Math.round(prev * 100) / 100
  if (currentRounded === prevRounded) return '— 0.00'
  const diff = currentCapital - prev
  if (isNaN(diff)) return '— 0.00'
  const sign = diff > 0 ? '+' : ''
  const arrow = diff > 0 ? '↑' : '↓'
  return `${arrow} ${sign}${diff.toFixed(2)}`
}
function getProjectCount(managerName) {
  return projectsList.value.filter(p => p.manager === managerName).length
}

// ── Manager drawer computed ──
const modalManagerRow = computed(() =>
  summaryRows.value.find(r => (r.manager || r['工程管理员']) === modalManager.value)
)
const modalBalance = computed(() =>
  projectsList.value.filter(p => p.manager === modalManager.value).reduce((s, p) => s + p.balance, 0)
)
const modalSpendYTD = computed(() => Number(modalManagerRow.value?.capital || modalManagerRow.value?.['本年累计资本性支出'] || 0))
const modalSpendMo = computed(() => {
  const row = modalManagerRow.value
  const v = Number(row?.monthSpend || row?.['本月资本性支出'] || 0)
  if (v) return v
  return projectsList.value.filter(p => p.manager === modalManager.value).reduce((s, p) => s + p.spendMo, 0)
})
const modalTransfer = computed(() => Number(modalManagerRow.value?.transfer || modalManagerRow.value?.['结转额'] || 0))
const modalPending = computed(() => Number(modalManagerRow.value?.pending || modalManagerRow.value?.['已下单待收货'] || 0))
const modalManagerRateStr = computed(() => {
  const rate = modalManagerRow.value?.rate || modalManagerRow.value?.['转固率'] || 0
  return (Number(rate) * 100).toFixed(2) + '%'
})
const modalRank = computed(() => {
  const idx = summaryRows.value.findIndex(r => (r.manager || r['工程管理员']) === modalManager.value)
  return idx >= 0 ? idx + 1 : '—'
})
const modalTotalProjects = computed(() => projectsList.value.filter(p => p.manager === modalManager.value).length)
const modalActiveCount = computed(() => projectsList.value.filter(p => p.manager === modalManager.value && p.balance > 0).length)
const modalReversedCount = computed(() => projectsList.value.filter(p => p.manager === modalManager.value && p.spendYTD < 0).length)
const modalProjectsForDrawer = computed(() =>
  [...modalData.value].sort((a, b) => Number(b['在建工程期末余额'] || 0) - Number(a['在建工程期末余额'] || 0))
)

function getManagerRate(managerName) {
  const row = summaryRows.value.find(r => (r.manager || r['工程管理员']) === managerName)
  if (!row) return '—'
  return formatPercent(row.rate || row['转固率'] || 0)
}

// ── KPI count-up animation ──
function runCountUp(newMetrics) {
  if (!newMetrics?.length) { animatedValues.value = []; return }
  const m = dashboard.value?.metrics
  if (!m) return
  const targets = [m.capital || 0, m.pending || 0, m.monthSpend || 0, (m.rate || 0) * 100]
  const formatters = [v => v.toFixed(2), v => v.toFixed(2), v => v.toFixed(2), v => v.toFixed(1) + '%']
  const duration = 900
  const startTs = performance.now()
  function tick(ts) {
    const t = Math.min((ts - startTs) / duration, 1)
    const eased = 1 - Math.pow(1 - t, 3)
    animatedValues.value = targets.map((target, i) => formatters[i](target * eased))
    if (t < 1) requestAnimationFrame(tick)
    else animatedValues.value = targets.map((target, i) => formatters[i](target))
  }
  requestAnimationFrame(tick)
}
watch(metrics, runCountUp, { immediate: true })

// ── Watchers ──
watch(
  () => _props.initialData ?? globalData.zaigongData.value,
  async (newData) => {
    if (newData) {
      applyDashboardData(newData)
      const rid = _props.initialRecordId ?? globalData.zaigongLatestRecordId.value
      if (rid) currentRecordId.value = rid
      isViewingHistory.value = false
      snapshotDisplayDate.value = null
      await fetchCompareData()
    }
  },
  { immediate: true }
)

// ── Lifecycle ──
onMounted(() => {
  if (!historyRecords.value.length) loadHistoryList()
  const onKey = (e) => { if (e.key === 'Escape' && modalVisible.value) closeModal() }
  document.addEventListener('keydown', onKey)
})
onUnmounted(() => {})
</script>

<style scoped>
/* ── Section / Card ─────────────────────────────────── */
.section { margin-bottom: 56px; }
.section-head {
  display: flex; align-items: baseline; justify-content: space-between;
  margin-bottom: 16px; gap: 16px;
}
.section-head h2 {
  font-size: 13px; font-weight: 500; color: var(--ink-3);
  text-transform: uppercase; letter-spacing: 0.08em; margin: 0;
}
.section-head .sub { font-size: 12px; color: var(--ink-3); }
.section-head .sub strong { color: var(--ink); font-weight: 500; }

.card {
  background: var(--surface); border: 1px solid var(--line);
  border-radius: var(--r-lg); overflow: hidden;
}
.card-head {
  padding: 16px 20px; display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid var(--line); gap: 16px;
}
.card-head h3 { font-size: 14px; font-weight: 500; color: var(--ink); margin: 0; letter-spacing: -0.005em; }
.card-head .sub { font-size: 11.5px; color: var(--ink-3); }
.card-body { padding: 20px; }

/* ── Buttons ──────────────────────────────────────── */
.btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 12px; border-radius: var(--r-md);
  font-size: 12.5px; color: var(--ink-2);
  background: var(--surface); border: 1px solid var(--line-2);
  transition: all 120ms; white-space: nowrap; cursor: pointer; font-family: inherit;
}
.btn:hover { background: var(--paper-2); color: var(--ink); border-color: var(--ink-4); }
.btn.ghost { background: transparent; border-color: transparent; color: var(--ink-2); }
.btn.ghost:hover { background: var(--paper-2); }
.btn svg { width: 12px; height: 12px; opacity: 0.7; }

/* ── Page header ─────────────────────────────────── */
.page {
  max-width: 1180px; margin: 0 auto; padding: 56px 40px;
}
.page-head {
  display: flex; align-items: flex-end; justify-content: space-between;
  gap: 24px; padding-bottom: 28px; margin-bottom: 36px;
  border-bottom: 1px solid var(--line);
}
.page-head-l { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.eyebrow {
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--accent); font-weight: 500;
  display: flex; align-items: center; gap: 8px;
}
.eyebrow::after { content: ''; width: 28px; height: 1px; background: currentColor; opacity: 0.5; }
.page-title {
  font-size: 30px; font-weight: 500; letter-spacing: -0.02em;
  color: var(--ink); margin: 0; line-height: 1.15;
}
.page-meta {
  display: flex; align-items: center; gap: 18px;
  color: var(--ink-3); font-size: 12px; margin-top: 4px;
}
.page-meta .sep { width: 3px; height: 3px; background: var(--ink-4); border-radius: 50%; }
.page-actions { display: flex; align-items: center; gap: 8px; }

/* ── Upload strip ────────────────────────────────── */
.upload-strip {
  background: var(--surface); border: 1px solid var(--line);
  border-radius: var(--r-lg); padding: 18px 22px; margin-bottom: 32px;
  display: grid; grid-template-columns: 44px 1fr auto auto;
  gap: 18px; align-items: center;
}
.upload-strip .up-icon {
  width: 44px; height: 44px; border-radius: 10px;
  background: var(--accent-soft); color: var(--accent);
  display: grid; place-items: center;
}
.upload-strip .up-meta { min-width: 0; }
.upload-strip .up-meta .up-title {
  font-size: 13.5px; font-weight: 500; color: var(--ink);
  display: flex; align-items: center; gap: 8px;
}
.upload-strip .up-meta .up-sub {
  font-size: 11.5px; color: var(--ink-3); margin-top: 3px;
  font-family: var(--font-mono);
}
.upload-strip .up-badge {
  font-size: 10px; padding: 2px 7px; border-radius: 10px;
  background: var(--ok-soft); color: var(--ok); font-weight: 500;
  font-family: var(--font-mono); letter-spacing: 0.02em;
}
.upload-strip .up-meter {
  display: flex; flex-direction: column; align-items: flex-end; gap: 4px;
  font-size: 10.5px; color: var(--ink-3); font-family: var(--font-mono);
}
.upload-strip .up-meter b { font-size: 14px; color: var(--ink); font-weight: 500; }

/* ── KPI grid ──────────────────────────────────── */
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
.val-negative { color: var(--bad) !important; }
.tri-up::before { content: '▲'; font-size: 8px; margin-right: 3px; }
.tri-dn::before { content: '▼'; font-size: 8px; margin-right: 3px; }

/* ── Table ─────────────────────────────────────── */
.tbl { width: 100%; font-size: 13px; color: var(--ink); border-collapse: collapse; }
.tbl thead th {
  text-align: left; font-weight: 500; font-size: 11.5px; color: var(--ink-3);
  text-transform: uppercase; letter-spacing: 0.06em;
  padding: 10px 16px; border-bottom: 1px solid var(--line);
  background: var(--surface-2); white-space: nowrap;
}
.tbl tbody td {
  padding: 12px 16px; border-bottom: 1px solid var(--line);
  vertical-align: middle; font-variant-numeric: tabular-nums;
}
.tbl tbody tr:last-child td { border-bottom: none; }
.tbl tbody tr:hover { background: var(--surface-2); }
.tbl .num, .tbl td.num, .tbl th.num { text-align: right; font-variant-numeric: tabular-nums; }
.tbl .col-name { font-weight: 500; }
.tbl .muted { color: var(--ink-3); }
.tbl .link { cursor: pointer; text-decoration: underline; text-decoration-color: var(--line-2); text-underline-offset: 3px; transition: all 120ms; }
.tbl .link:hover { color: var(--accent); text-decoration-color: var(--accent); }
.sort-icon { margin-left: 4px; font-size: 10px; opacity: 0.4; }
.sort-icon.active { opacity: 1; color: var(--accent); }

/* ── Cell bar ──────────────────────────────────── */
.cell-bar-wrap { display: flex; align-items: center; gap: 6px; min-width: 90px; overflow: hidden; }
.cell-bar-track { flex: 1; height: 4px; background: var(--paper-2); border-radius: 2px; overflow: hidden; min-width: 50px; }
.cell-bar-fill { height: 100%; border-radius: 2px; }
.cell-bar-fill.ok { background: var(--ok); }
.cell-bar-fill.warn { background: var(--warn); }
.cell-bar-fill.bad { background: var(--bad); }
.cell-bar-pct { font-family: var(--font-mono); font-size: 11.5px; color: var(--ink-2); width: 44px; text-align: right; }

/* ── Rank ──────────────────────────────────────── */
.rank-num {
  display: inline-flex; align-items: center; justify-content: center;
  width: 22px; height: 22px; border-radius: 5px;
  font-family: var(--font-mono); font-size: 11px; color: var(--ink-3);
  background: var(--paper-2);
}
.rank-num.rank-top { background: var(--ink); color: var(--paper); }

/* ── Pill ──────────────────────────────────────── */
.pill {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 2px 8px; border-radius: 999px;
  font-size: 11px; font-weight: 500;
  background: var(--paper-2); color: var(--ink-2);
  border: 1px solid var(--line); white-space: nowrap;
}
.pill.ok { background: var(--ok-soft); color: var(--ok); border-color: transparent; }
.pill.warn { background: var(--warn-soft); color: var(--warn); border-color: transparent; }
.pill.bad { background: var(--bad-soft); color: var(--bad); border-color: transparent; }
.pill.info { background: var(--info-soft); color: var(--info); border-color: transparent; }
.pill .dot { width: 5px; height: 5px; border-radius: 50%; background: currentColor; }

/* ── Progress summary ──────────────────────────── */
.progress-summary {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 1px; background: var(--line); border-top: 1px solid var(--line);
}
.ps-card {
  background: var(--surface); padding: 20px 22px 18px;
  display: flex; flex-direction: column; gap: 14px;
}
.ps-head {
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
}
.ps-label {
  font-size: 12px; font-weight: 600; color: var(--ink-2); letter-spacing: 0.03em;
}
.ps-target {
  font-size: 12px; color: var(--ink-3); display: flex; align-items: center; gap: 4px;
}
.ps-target b { color: var(--ink-2); font-weight: 600; font-family: var(--font-mono); }
.ps-edit-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 20px; height: 20px; border-radius: 4px; border: none;
  background: transparent; color: var(--ink-4); cursor: pointer; transition: all 120ms;
}
.ps-edit-btn:hover { background: var(--paper-2); color: var(--ink-2); }
.ps-inline-input {
  width: 72px; border: 1px solid var(--accent); border-radius: 4px;
  padding: 2px 6px; font-size: 12px; font-family: var(--font-mono);
  color: var(--ink); background: var(--paper); outline: none;
  font-variant-numeric: tabular-nums;
}
.ps-save-btn, .ps-cancel-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 20px; height: 20px; border-radius: 4px; border: none;
  font-size: 11px; cursor: pointer; transition: all 120ms;
}
.ps-save-btn { background: var(--ok-soft); color: var(--ok); }
.ps-save-btn:hover { background: var(--ok); color: #fff; }
.ps-cancel-btn { background: transparent; color: var(--ink-4); }
.ps-cancel-btn:hover { background: var(--paper-2); color: var(--ink-2); }
.ps-body {
  display: flex; flex-direction: column; gap: 10px;
}
.ps-value {
  font-size: 16px; font-weight: 500; color: var(--ink); line-height: 1;
  font-family: var(--font-mono); letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}
.ps-unit { font-size: 13px; color: var(--ink-3); font-weight: 400; margin-left: 2px; }
.ps-bar-wrap {
  display: flex; align-items: center; gap: 10px;
}
.ps-bar-track {
  flex: 1; height: 8px; background: var(--paper-2); border-radius: 4px; overflow: hidden;
}
.ps-bar-fill {
  height: 100%; border-radius: 4px; transition: width 500ms cubic-bezier(0.4, 0, 0.2, 1);
}
.ps-bar-fill.ok { background: var(--ok); }
.ps-bar-fill.warn { background: var(--warn); }
.ps-bar-fill.bad { background: var(--bad); }
.ps-pct {
  font-size: 11px; font-weight: 600; font-family: var(--font-mono);
  min-width: 52px; text-align: right;
  font-variant-numeric: tabular-nums;
}
.ps-pct.ok { color: var(--ok); }
.ps-pct.warn { color: var(--warn); }
.ps-pct.bad { color: var(--bad); }
.ps-hint {
  font-size: 11.5px; color: var(--ink-3);
}

/* ── Warning + Manager grid ────────────────────── */
.warning-manager-grid {
  display: grid; grid-template-columns: 1fr 1.5fr; gap: 24px;
}
.warning-item {
  padding: 16px 20px;
  border-bottom: 1px solid var(--line);
  display: grid; grid-template-columns: 1fr auto auto; align-items: center; gap: 14px;
  cursor: pointer; transition: background 120ms;
}
.warning-item:last-child { border-bottom: none; }
.warning-item:hover { background: var(--surface-2); }

/* ── Compare ──────────────────────────────────── */
.compare-cards-row { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 16px; }
.compare-card {
  display: grid; gap: 6px; padding: 14px;
  border-radius: var(--r-md); background: var(--paper); border: 1px solid var(--line);
}
.compare-label { color: var(--ink-4); font-size: 11px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.06em; }
.compare-card strong { font-size: 20px; color: var(--ink); font-weight: 500; font-family: var(--font-mono); }
.compare-detail { color: var(--ink-3); font-size: 12px; }
.delta-up { color: var(--ok); }
.delta-down { color: var(--bad); }
.compare-subheader { margin-bottom: 14px; }
.compare-subheader h4 { font-size: 14px; font-weight: 500; color: var(--ink); margin: 0; }
.compare-caption { color: var(--ink-3); font-size: 12px; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding: 0 4px; }

/* ── Upload section (no data state) ───────────── */
.dashboard { }
.upload-section { padding: 0; }
.upload-shell { max-width: 860px; width: 100%; }
.upload-page-header { margin-bottom: 20px; }
.upload-page-header-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.upload-page-header h1 { font-size: 22px; font-weight: 500; color: var(--ink); margin-bottom: 4px; letter-spacing: -0.01em; }
.upload-page-header p { font-size: 13px; color: var(--ink-3); }
.upload-container { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 16px; margin-bottom: 18px; }
.upload-copy {
  position: relative; display: flex; flex-direction: column; padding: 22px;
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg);
  box-shadow: var(--shadow-card);
}
.upload-copy-top { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }
.panel-kicker { display: inline-block; font-size: 11px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--accent); }
.inline-target-card { margin-top: 0; }
.inline-target-header { margin-bottom: 14px; }
.inline-target-header h3 { font-size: 15px; font-weight: 500; color: var(--ink); line-height: 1.3; }
.target-inline-form { display: flex; align-items: center; gap: 8px; margin-bottom: 18px; }
.target-label { font-size: 13px; color: var(--ink-3); white-space: nowrap; }
.input-wrap {
  flex: 1; display: flex; align-items: center; min-height: 40px;
  border-radius: var(--r-md); background: var(--paper); border: 1px solid var(--line-2);
  overflow: hidden; transition: border-color 0.15s;
}
.input-wrap:focus-within { border-color: var(--ink-3); }
.input-wrap input {
  flex: 1; background: transparent; border: none; padding: 8px 12px;
  font-size: 14px; font-family: var(--font-mono); color: var(--ink); outline: none;
}
.input-wrap input::placeholder { color: var(--ink-4); font-family: var(--font-sans); font-size: 13px; }
.input-wrap .unit { padding: 0 12px; font-size: 13px; color: var(--ink-3); border-left: 1px solid var(--line); background: var(--paper-2); height: 100%; display: flex; align-items: center; }
.confirm-btn {
  height: 40px; padding: 0 16px; border: none; border-radius: var(--r-md);
  background: var(--ink); color: var(--paper); font-size: 13px; font-weight: 500;
  cursor: pointer; font-family: inherit; transition: background 0.15s;
}
.confirm-btn:hover { background: var(--accent); }
.target-divider { height: 1px; background: var(--line); margin-bottom: 18px; }
.upload-checklist { display: grid; gap: 12px; }
.check-item { display: flex; align-items: flex-start; gap: 8px; color: var(--ink-2); font-size: 13px; line-height: 1.5; }
.check-icon {
  width: 18px; height: 18px; display: inline-flex; align-items: center; justify-content: center;
  border-radius: var(--r-sm); background: var(--info-soft); color: var(--info);
  font-size: 11px; font-weight: 700; flex-shrink: 0; margin-top: 1px;
}
.upload-box {
  display: flex; flex-direction: column; background: var(--surface);
  border: 1px solid var(--line); border-radius: var(--r-lg);
  box-shadow: var(--shadow-card); overflow: hidden;
}
.upload-zone {
  flex: 1; border: 1.5px dashed var(--line-2); border-radius: var(--r-md);
  margin: 12px 12px 0; padding: 28px 20px; display: flex; flex-direction: column;
  align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s;
  text-align: center; background: var(--paper); min-height: 200px;
}
.upload-zone:hover { border-color: var(--ink-3); background: var(--paper-2); }
.upload-icon-wrap { width: 34px; height: 34px; margin: 0 auto 14px; }
.upload-icon { width: 34px; height: 34px; color: var(--ink-4); }
.upload-box h2 { font-size: 15px; font-weight: 500; color: var(--ink); margin-bottom: 4px; line-height: 1.5; }
.upload-box h2 .link { color: var(--info); text-decoration: underline; text-underline-offset: 2px; }
.upload-hint { font-size: 12px; color: var(--ink-4); margin-bottom: 12px; }
.file-types { display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; }
.file-tag { padding: 3px 10px; background: var(--info-soft); border: 1px solid #c5d8ef; border-radius: 999px; font-size: 11px; color: var(--info); font-weight: 500; }
.upload-footer { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 10px 12px; margin-top: auto; }
.upload-feedback { margin: 0 12px 8px; padding: 8px 12px; border-radius: var(--r-md); font-size: 12px; line-height: 1.5; }
.upload-feedback.info { background: var(--ok-soft); color: var(--ok); border: 1px solid #bdd6aa; }
.upload-feedback.error { background: var(--bad-soft); color: var(--bad); border: 1px solid #e0b8ad; }
.upload-last { display: flex; align-items: center; gap: 5px; color: var(--ink-4); font-size: 12px; }
.upload-last strong { color: var(--ink-3); font-family: var(--font-mono); font-size: 12px; }
.auto-upload-tip { display: inline-flex; align-items: center; height: 32px; padding: 0 12px; border-radius: var(--r-md); background: var(--paper-2); color: var(--ink-3); font-size: 12px; font-weight: 500; white-space: nowrap; }
.selected-file-banner { display: flex; align-items: center; gap: 10px; background: var(--ok-soft); border-radius: var(--r-md); padding: 12px 16px; margin: 8px 12px; width: calc(100% - 24px); }
.selected-file-copy { flex: 1; min-width: 0; }
.selected-file-name { font-size: 12px; font-weight: 500; color: var(--ok); font-family: var(--font-mono); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.selected-file-meta { font-size: 11px; color: var(--ink-4); margin-top: 2px; }
.selected-file-change { font-size: 11px; color: var(--ink-3); cursor: pointer; padding: 3px 7px; border-radius: var(--r-sm); border: 1px solid var(--line); background: var(--surface); }
.recent-uploads-card { background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg); padding: 14px 16px; box-shadow: var(--shadow-card); }
.recent-uploads-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.recent-uploads-head h3 { font-size: 11px; font-weight: 500; color: var(--ink-3); text-transform: uppercase; letter-spacing: 0.06em; }
.view-all-btn { background: transparent; border: none; color: var(--info); font-size: 11px; cursor: pointer; font-family: inherit; }
.recent-uploads-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.recent-upload-item { border: 1px solid var(--line); border-radius: var(--r-md); background: var(--paper); padding: 10px 12px; text-align: left; cursor: pointer; transition: all 0.15s; font-family: inherit; }
.recent-upload-item:hover { border-color: var(--line-2); background: var(--surface); }
.recent-upload-date { font-size: 11px; font-weight: 500; color: var(--ink); margin-bottom: 3px; font-family: var(--font-mono); }
.recent-upload-value { font-size: 12px; font-weight: 500; color: var(--info); margin-bottom: 2px; font-family: var(--font-mono); }
.recent-upload-value span { font-family: var(--font-sans); }
.recent-upload-meta { font-size: 10px; color: var(--ink-4); }

/* ── Loading ──────────────────────────────────── */
.loading {
  position: fixed; inset: 0; background: rgba(247,245,238,0.92);
  display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 1000;
}
.loader { position: relative; width: 48px; height: 48px; }
.loader-ring {
  position: absolute; inset: 0; border: 2px solid transparent;
  border-top-color: var(--ink-3); border-radius: 50%;
  animation: spin 1.2s linear infinite;
}
.loader-ring:nth-child(2) { inset: 7px; border-top-color: var(--accent); animation-delay: 0.15s; animation-direction: reverse; }
.loader-ring:nth-child(3) { inset: 14px; border-top-color: var(--ok); animation-delay: 0.3s; }
@keyframes spin { to { transform: rotate(360deg); } }
.loading p { margin-top: 16px; font-size: 13px; color: var(--ink-3); }

/* ── History panel ────────────────────────────── */
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

/* ── Target edit inline ──────────────────────── */
.target-edit-btn { display: inline-flex; align-items: center; padding: 2px; border: none; background: transparent; color: var(--ink-4); cursor: pointer; border-radius: var(--r-sm); transition: color 0.15s; font-family: inherit; vertical-align: middle; }
.target-edit-btn:hover { color: var(--accent); }
.target-inline-input { width: 80px; height: 24px; padding: 0 6px; border: 1px solid var(--line-2); border-radius: var(--r-sm); font-size: 12px; font-family: var(--font-mono); background: var(--surface); color: var(--ink); outline: none; vertical-align: middle; }
.target-inline-input:focus { border-color: var(--accent); }
.target-save-btn, .target-cancel-btn { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border: 1px solid var(--line-2); border-radius: var(--r-sm); background: var(--surface); color: var(--ink-2); font-size: 12px; cursor: pointer; font-family: inherit; vertical-align: middle; margin-left: 2px; transition: all 0.15s; }
.target-save-btn:hover { background: var(--ok); color: #fff; border-color: var(--ok); }
.target-cancel-btn:hover { background: var(--paper-2); color: var(--ink); }
.target-save-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── Empty state ──────────────────────────────── */
.empty { padding: 40px; text-align: center; color: var(--ink-3); font-size: 13px; }

/* ── Responsive ───────────────────────────────── */
@media (max-width: 1180px) {
  .upload-container { grid-template-columns: 1fr; }
  .warning-manager-grid { grid-template-columns: 1fr; }
}
@media (max-width: 900px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .kpi-grid { grid-template-columns: 1fr; }
  .page { padding: 16px; }
  .upload-strip { grid-template-columns: 1fr; }
  .upload-strip .up-icon { display: none; }
  .upload-strip .up-meter { display: none; }
}
</style>
