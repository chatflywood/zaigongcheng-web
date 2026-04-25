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
            <button v-for="record in recentHistoryCards" :key="record.id" class="recent-upload-item" @click="viewHistorySnapshot(record.id)">
              <div class="recent-upload-date">{{ formatHistoryDateOnly(record.uploaded_at) }}</div>
              <div class="recent-upload-value">{{ formatNum(record.dashboard_snapshot?.metrics?.capital || 0) }} <span>万元</span></div>
              <div class="recent-upload-meta">目标 {{ formatNum(record.target_value || 0) }} · {{ formatHistoryProgress(record) }}</div>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Data state (dashboard with data) ── -->
    <div v-else class="d2-page">
      <!-- Page head -->
      <div class="d2-head">
        <div class="d2-head-top">
          <h1>在建工程进度看板 <span class="d2-crumb-tag">CAPEX TRACKING</span></h1>
          <div class="d2-head-actions">
            <button class="d2-tbtn" @click="openHistoryPanel">
              <svg width="13" height="13" viewBox="0 0 16 16" fill="none"><path d="M2 5h12v9H2V5zM2 5V3h12v2M5 2v3M11 2v3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
              历史记录
            </button>
            <button v-if="(isViewingHistory || props.snapshotLabel) && (props.latestData || props.initialData)" class="d2-tbtn" @click="restoreLatestView">返回最新</button>
            <button class="d2-tbtn d2-tbtn-primary" @click="showUpload = true">
              <svg width="13" height="13" viewBox="0 0 16 16" fill="none"><path d="M8 11V3M5 6l3-3 3 3M3 12v1h10v-1" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
              上传数据
            </button>
          </div>
        </div>
        <div class="d2-head-meta">
          <span>在建工程分析.xlsx</span>
          <span class="d2-dot"></span>
          <span>共 {{ summaryRows.length }} 人</span>
          <span class="d2-dot"></span>
          <template v-if="!editingTarget">
            <span>年度目标 <b>{{ targetValue || '—' }}</b> 万</span>
            <button v-if="currentRecordId" class="d2-edit-btn" @click="startEditTarget" title="编辑目标">
              <svg width="10" height="10" viewBox="0 0 16 16" fill="none"><path d="M2 14l3-1 8-8-2-2-8 8-1 3z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </button>
          </template>
          <template v-else>
            <div class="d2-target-edit">
              <input ref="targetEditInput" v-model="targetEditValue" type="number" class="d2-target-input" @keyup.enter="confirmEditTarget" @keyup.esc="cancelEditTarget" />
              <span class="d2-target-unit">万</span>
              <button class="d2-tbtn d2-tbtn-xs" @click="confirmEditTarget" :disabled="targetSaving">确认</button>
              <button class="d2-tbtn d2-tbtn-xs" @click="cancelEditTarget">取消</button>
            </div>
          </template>
          <template v-if="displayAnalysisDate">
            <span class="d2-dot"></span>
            <span>{{ displayAnalysisDate }}</span>
          </template>
        </div>
      </div>

      <!-- Main 3-row grid -->
      <div class="d2-main">

        <!-- KPI row -->
        <div class="d2-kpi-row">
          <!-- Health card -->
          <div class="d2-health">
            <div class="d2-health-icon">
              <svg viewBox="0 0 48 48" fill="none">
                <rect x="8" y="6" width="28" height="36" rx="3" fill="#F5B892" stroke="#E86A33" stroke-width="1.5"/>
                <rect x="12" y="12" width="20" height="1.5" fill="#E86A33" opacity="0.6"/>
                <rect x="12" y="17" width="14" height="1.5" fill="#E86A33" opacity="0.5"/>
                <circle cx="22" cy="30" r="7" fill="#E86A33"/>
                <path d="M18 30l3 3 5-5" stroke="#fff" stroke-width="1.6" stroke-linecap="round" fill="none"/>
              </svg>
            </div>
            <div class="d2-health-body">
              <div class="d2-health-label">整体健康度</div>
              <div class="d2-health-value" :class="healthCard.cls">{{ healthCard.label }}</div>
              <div class="d2-health-desc">{{ healthCard.desc }}</div>
              <div class="d2-health-footline"></div>
              <div class="d2-health-slip">{{ healthCard.slip }}</div>
            </div>
          </div>

          <!-- KPI 1 · 本年累计资本性支出 -->
          <div class="d2-kpi-card">
            <div class="d2-kpi-head">
              <div class="d2-kpi-label">本年累计·资本性支出</div>
              <div class="d2-kpi-ic">
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M2 3h12v10H2V3zM2 6h12M5 3v3M11 3v3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
              </div>
            </div>
            <div class="d2-kpi-val">{{ formatNum(dashboard?.metrics?.capital || 0) }}<span class="d2-kpi-unit">万元</span></div>
            <div>
              <div class="d2-kpi-prog">
                <div class="d2-kpi-prog-fill" :style="{ width: Math.min(100, targetValue > 0 ? (dashboard?.metrics?.capital || 0) / targetValue * 100 : 0) + '%' }"></div>
              </div>
              <div class="d2-kpi-prog-label">
                <span>目标 {{ targetValue || '—' }} 万元</span>
                <span class="d2-pct">{{ targetValue > 0 ? ((dashboard?.metrics?.capital || 0) / targetValue * 100).toFixed(1) : '0.0' }}%</span>
              </div>
            </div>
            <div class="d2-kpi-foot">{{ deficitHint }}</div>
          </div>

          <!-- KPI 2 · 已下单待收货 -->
          <div class="d2-kpi-card">
            <div class="d2-kpi-head">
              <div class="d2-kpi-label">已下单待收货</div>
              <div class="d2-kpi-ic">
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M2 5l6-3 6 3v6l-6 3-6-3V5zM2 5l6 3M14 5L8 8M8 8v6" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              </div>
            </div>
            <div class="d2-kpi-val">{{ formatNum(dashboard?.metrics?.pending || 0) }}<span class="d2-kpi-unit">万元</span></div>
            <div style="flex:1"></div>
            <div class="d2-kpi-foot">{{ pendingOverLimitCount }} 人超30万</div>
          </div>

          <!-- KPI 3 · 本月资本性支出 -->
          <div class="d2-kpi-card">
            <div class="d2-kpi-head">
              <div class="d2-kpi-label">本月资本性支出</div>
              <div class="d2-kpi-ic">
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M2 4h12v8H2V4zM8 10a2 2 0 100-4 2 2 0 000 4z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
              </div>
            </div>
            <div class="d2-kpi-val" :class="(dashboard?.metrics?.monthSpend || 0) < 0 ? 'd2-neg' : ''">
              {{ formatNum(dashboard?.metrics?.monthSpend || 0) }}<span class="d2-kpi-unit">万元</span>
            </div>
            <div style="flex:1"></div>
            <div class="d2-kpi-foot">数据日期 {{ displayAnalysisDate || '-' }}</div>
          </div>

          <!-- KPI 4 · 综合转固率 -->
          <div class="d2-kpi-card">
            <div class="d2-kpi-head">
              <div class="d2-kpi-label">综合转固率</div>
              <div class="d2-kpi-ic">
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M3 8a5 5 0 105-5v5H3z M8 3a5 5 0 015 5h-5V3z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
              </div>
            </div>
            <div class="d2-kpi-val d2-accent">{{ formatPercent(dashboard?.metrics?.rate || 0) }}</div>
            <div style="flex:1"></div>
            <div class="d2-kpi-foot">目标 60% · <span :class="(dashboard?.metrics?.rate || 0) >= 0.6 ? 'd2-ok' : 'd2-warn-text'">{{ (dashboard?.metrics?.rate || 0) >= 0.6 ? '已达标' : '偏低' }}</span></div>
          </div>
        </div>

        <!-- Mid row -->
        <div class="d2-mid-row">
          <!-- Trend chart -->
          <div class="d2-panel">
            <div class="d2-panel-head">
              <h3>累计支出趋势</h3>
              <div class="d2-legend-row">
                <span class="d2-legend-item"><span class="d2-lsw d2-lsw-orange"></span>累计支出</span>
                <span class="d2-legend-item"><span class="d2-lsw d2-lsw-green"></span>转固率</span>
                <span class="d2-legend-item"><span class="d2-lsw d2-lsw-dashed"></span>年度目标</span>
              </div>
            </div>
            <div class="d2-trend-wrap" v-if="trendData">
              <svg :viewBox="`0 0 ${trendData.W} ${trendData.H}`" class="d2-trend-svg" preserveAspectRatio="none"
                   @mouseleave="trendHover = null">
                <defs>
                  <linearGradient id="td2-grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#F8C5A8" stop-opacity="0.55"/>
                    <stop offset="100%" stop-color="#F8C5A8" stop-opacity="0"/>
                  </linearGradient>
                  <linearGradient id="td2-rate-grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#6BBF8E" stop-opacity="0.4"/>
                    <stop offset="100%" stop-color="#6BBF8E" stop-opacity="0"/>
                  </linearGradient>
                </defs>
                <g class="d2-trend-grid">
                  <line v-for="(y, i) in trendData.gridYs" :key="'g'+i" :x1="trendData.pl" :x2="trendData.W - trendData.pr" :y1="y" :y2="y"/>
                </g>
                <g class="d2-trend-axis">
                  <text v-for="(lbl, i) in trendData.yLabels" :key="'yl'+i" :x="trendData.pl - 5" :y="trendData.gridYs[i] + 3" text-anchor="end">{{ lbl }}</text>
                </g>
                <g class="d2-trend-axis d2-trend-axis-r">
                  <text v-for="(lbl, i) in trendData.yRateLabels" :key="'yr'+i" :x="trendData.W - trendData.pr + 5" :y="trendData.gridYs[i] + 3" text-anchor="start">{{ lbl }}</text>
                </g>
                <g class="d2-trend-axis">
                  <text v-for="(lbl, i) in trendData.labels" :key="'xl'+i" :x="trendData.dots[i].x" :y="trendData.H - 4" text-anchor="middle">{{ lbl }}</text>
                </g>
                <line v-if="trendData.tgtY" class="d2-trend-target" :x1="trendData.pl" :x2="trendData.W - trendData.pr" :y1="trendData.tgtY" :y2="trendData.tgtY"/>
                <polygon class="d2-trend-rate-area" :points="trendData.rateArea"/>
                <polyline class="d2-trend-rate-line" :points="trendData.ratePts"/>
                <polygon class="d2-trend-area" :points="trendData.capitalArea"/>
                <polyline class="d2-trend-line" :points="trendData.capitalPts"/>
                <line v-if="trendHover != null && trendData.dots[trendHover]"
                  :x1="trendData.dots[trendHover].x" :x2="trendData.dots[trendHover].x"
                  :y1="trendData.pt" :y2="trendData.pt + trendData.ih"
                  class="d2-trend-hover-line"/>
                <circle v-for="(d, i) in trendData.dots" :key="'cd'+i"
                  :cx="d.x" :cy="d.cy" :r="trendHover === i ? 4.5 : 3"
                  :class="trendHover === i ? 'd2-pt-active' : 'd2-pt'"
                  @mouseenter="trendHover = i" style="cursor:pointer"/>
                <circle v-for="(d, i) in trendData.rateDots" :key="'rd'+i"
                  :cx="d.x" :cy="d.cy" r="2.5" class="d2-pt-rate"
                  @mouseenter="trendHover = i" style="cursor:pointer"/>
              </svg>
              <div v-if="trendHover != null && trendData.dots[trendHover]" class="d2-trend-tip"
                :style="{
                  left: trendData.dots[trendHover].pctX > 65 ? 'calc(' + trendData.dots[trendHover].pctX + '% - 128px)' : 'calc(' + trendData.dots[trendHover].pctX + '% + 12px)',
                  top: 'calc(' + trendData.dots[trendHover].pctY + '% - 36px)'
                }">
                <strong>{{ trendData.labels[trendHover] }}</strong>
                <span>支出 {{ trendData.dots[trendHover].capital.toFixed(2) }} 万</span>
                <em>转固率 {{ (trendData.dots[trendHover].rate * 100).toFixed(1) }}%</em>
              </div>
            </div>
            <div v-else class="d2-trend-empty">暂无历史数据</div>
          </div>

          <!-- Funnel -->
          <div class="d2-panel">
            <div class="d2-panel-head">
              <h3>项目阶段分布</h3>
            </div>
            <div class="d2-funnel">
              <div v-for="(s, i) in funnelStages" :key="s.key" class="d2-funnel-row">
                <div class="d2-funnel-bar-wrap">
                  <div class="d2-funnel-bar" :class="'d2-funnel-l' + (i+1)"
                    :style="{ '--fw': (funnelStages[0].count > 0 ? s.count / funnelStages[0].count * 100 : 0) + '%' }">
                  </div>
                </div>
                <div class="d2-funnel-meta">
                  <span class="d2-funnel-label">{{ s.label }}</span>
                  <span class="d2-funnel-count">{{ s.count }}</span>
                  <span class="d2-funnel-pct">{{ funnelStages[0].count > 0 ? (s.count / funnelStages[0].count * 100).toFixed(0) : 0 }}%</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Manager ranking -->
          <div class="d2-panel">
            <div class="d2-panel-head">
              <h3>管理员工作量排名 <span class="d2-sub">按本年累计支出</span></h3>
              <button v-if="currentRecordId" class="d2-tbtn d2-tbtn-sm" @click="openTransferPriority">转固推进清单</button>
            </div>
            <table class="d2-rank-tbl">
              <thead>
                <tr>
                  <th>排名</th>
                  <th>管理员</th>
                  <th class="num">在管</th>
                  <th class="num">本年支出(万元)</th>
                  <th class="bar">转固率</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="m in rankedManagers.slice(0, 4)" :key="m.name" class="d2-rank-row" @click="openManagerModal(m.name)">
                  <td><span class="d2-rank-badge" :class="m.rank === 1 ? 'r1' : m.rank === 2 ? 'r2' : m.rank === 3 ? 'r3' : ''">{{ m.rank }}</span></td>
                  <td class="d2-rank-name">{{ m.name }}</td>
                  <td class="num">{{ m.projects }}</td>
                  <td class="num" :class="m.spendYTD < 0 ? 'd2-neg' : ''">{{ formatNum(m.spendYTD) }}</td>
                  <td>
                    <div class="d2-mini-bar-wrap">
                      <div class="d2-mini-bar">
                        <div class="d2-mini-fill" :style="{ width: Math.min(100, managerMaxSpend > 0 ? Math.abs(m.spendYTD) / managerMaxSpend * 100 : 0) + '%' }"></div>
                      </div>
                      <span class="d2-rate-text">{{ formatPercent(m.rate) }}</span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Bot row -->
        <div class="d2-bot-row">
          <!-- Warnings -->
          <div class="d2-panel">
            <div class="d2-panel-head">
              <h3>预警 &amp; 风险</h3>
              <span class="d2-warn-count" v-if="d2WarningItems.length">共 <b>{{ d2WarningItems.length }}</b> 项</span>
            </div>
            <div class="d2-warn-list" v-if="d2WarningItems.length">
              <div v-for="(w, i) in d2WarningItems" :key="i" class="d2-warn-item"
                :class="{ 'clickable': w.key }"
                @click="w.key ? showFourClassDetail(w.key) : undefined">
                <div class="d2-warn-ic" :class="'sev-' + w.sev">
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                    <path v-if="w.sev === 'high'" d="M8 2l6 11H2L8 2zM8 6v4M8 11.5v.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                    <path v-else d="M8 3a5 5 0 100 10 5 5 0 000-10zM8 5v3l2 2" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                  </svg>
                </div>
                <div class="d2-warn-body">
                  <div class="d2-warn-title">{{ w.title }}</div>
                  <div class="d2-warn-desc">{{ w.desc }}</div>
                </div>
                <div class="d2-warn-sev" :class="'sev-' + w.sev">{{ w.sev === 'high' ? '严重' : w.sev === 'med' ? '中等' : '轻微' }}</div>
              </div>
            </div>
            <div v-else class="d2-warn-empty">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none"><circle cx="16" cy="16" r="12" stroke="currentColor" stroke-width="1.2" opacity="0.3"/><path d="M12 16l3 3 5-5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
              <span>暂无预警</span>
            </div>
            <div v-if="fcWarnings?.items?.length" class="d2-warn-more" @click="showFourClassAllDetail">查看四类工程预警明细 →</div>
          </div>

          <!-- Project table -->
          <div class="d2-panel d2-panel-scroll">
            <div class="d2-ptable-bar">
              <h3>在建工程项目列表</h3>
              <div class="d2-search">
                <svg width="11" height="11" viewBox="0 0 16 16" fill="none"><path d="M7 13a6 6 0 100-12 6 6 0 000 12zM11 11l4 4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
                <input v-model="ptSearch" placeholder="搜索项目名称" @input="ptPage = 1"/>
              </div>
              <select class="d2-sel" v-model="ptStageFilter" @change="ptPage = 1">
                <option value="all">全部阶段</option>
                <option value="lixiang">立项</option>
                <option value="zaijian">在建</option>
                <option value="daishouhuo">待收货</option>
                <option value="zhuangu">已转固</option>
              </select>
              <select class="d2-sel" v-model="ptStatusFilter" @change="ptPage = 1">
                <option value="all">全部状态</option>
                <option value="ok">正常</option>
                <option value="warn">预警</option>
                <option value="bad">异常</option>
              </select>
            </div>
            <div class="d2-ptable-wrap">
              <table class="d2-ptable">
                <colgroup>
                  <col style="width:28px"/>
                  <col/>
                  <col style="width:68px"/>
                  <col style="width:54px"/>
                  <col style="width:88px"/>
                  <col style="width:74px"/>
                  <col style="width:62px"/>
                  <col style="width:52px"/>
                </colgroup>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>项目名称</th>
                    <th>阶段</th>
                    <th>管理员</th>
                    <th class="num">本年支出</th>
                    <th class="num">待到货</th>
                    <th class="num">转固率</th>
                    <th>状态</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="p in ptPageRows" :key="p.name">
                    <td class="d2-idx">{{ p.idx }}</td>
                    <td class="d2-pname" :title="p.name">{{ p.name }}</td>
                    <td><span class="d2-stage-tag" :class="'st-' + p.stage">{{ p.stageLabel }}</span></td>
                    <td class="d2-mgr-link" @click.stop="openManagerModal(p.manager)">{{ p.manager }}</td>
                    <td class="num" :class="p.spendYTD < 0 ? 'd2-neg' : ''">{{ formatNum(p.spendYTD) }}</td>
                    <td class="num d2-muted">{{ formatNum(p.pending) }}</td>
                    <td class="num">{{ (p.rate * 100).toFixed(1) }}%</td>
                    <td>
                      <span class="d2-status-dot" :class="'sd-' + p.status">
                        <span class="d"></span>{{ p.statusLabel }}
                      </span>
                    </td>
                  </tr>
                  <tr v-if="ptPageRows.length === 0">
                    <td colspan="8" class="d2-empty-row">无匹配项目</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="d2-pager">
              <span class="d2-pager-count">共 {{ ptFiltered.length }} 条</span>
              <div class="d2-pager-ctrls">
                <button :disabled="ptPage <= 1" @click="ptPage = Math.max(1, ptPage - 1)">‹</button>
                <button v-for="n in Math.min(ptTotalPages, 5)" :key="n" :class="{ 'on': ptPage === n }" @click="ptPage = n">{{ n }}</button>
                <button :disabled="ptPage >= ptTotalPages" @click="ptPage = Math.min(ptTotalPages, ptPage + 1)">›</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Upload overlay (triggered from topbar) -->
      <div v-if="showUpload" class="upload-overlay" @click.self="showUpload = false">
        <div class="upload-overlay-card">
          <div class="upload-overlay-head">
            <h3>上传数据</h3>
            <button class="modal-close" @click="showUpload = false">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            </button>
          </div>
          <div class="upload-overlay-body">
            <div class="overlay-target-row">
              <span class="overlay-target-label">年度目标</span>
              <div class="overlay-target-input-wrap">
                <input type="number" v-model.number="targetValue" placeholder="如 503"/>
                <span class="overlay-target-unit">万元</span>
              </div>
            </div>
            <div class="overlay-divider"></div>
            <div class="upload-zone" @dragover.prevent @drop.prevent="handleDrop; showUpload = false" @click="triggerFileInput">
              <template v-if="selectedFileName">
                <div class="selected-file-banner">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="9" stroke="#047857" stroke-width="1.2"/><path d="M6 10l3 3 5-5" stroke="#047857" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  <div class="selected-file-copy">
                    <div class="selected-file-name">{{ selectedFileName }}</div>
                    <div class="selected-file-meta">已选择文件 · 等待上传</div>
                  </div>
                  <span class="selected-file-change" @click.stop="clearSelectedFile">更换</span>
                </div>
              </template>
              <template v-else>
                <div class="upload-icon-wrap">
                  <svg class="upload-icon" viewBox="0 0 34 34" fill="none"><rect x="4" y="7" width="26" height="22" rx="3" stroke="currentColor" stroke-width="1.2"/><path d="M11 14h12M11 18.5h8" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/><path d="M21.5 3v7M18 6l3.5-3.5L25 6" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </div>
                <h2>拖拽文件到此处，或<span class="link">点击选择</span></h2>
                <p class="upload-hint">支持 .xlsx 格式 · 在建工程明细总表</p>
              </template>
            </div>
            <div v-if="uploadMessage" class="upload-feedback" :class="uploadMessageType">{{ uploadMessage }}</div>
            <input ref="fileInput" type="file" accept=".xlsx,.xls" @change="handleFileChange; showUpload = false" hidden/>
          </div>
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
          <button v-for="(record, index) in historyRecords" :key="record.id" class="history-item" :class="{ active: currentRecordId === record.id }" @click="viewHistorySnapshot(record.id)">
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
    <div v-if="modalVisible" class="mgr-drawer-overlay" @click.self="closeModal">
      <aside class="mgr-drawer">

        <header class="mgr-drawer-head">
          <div style="min-width:0;flex:1">
            <div class="eyebrow" style="margin-bottom:8px">工程管理员 · 明细</div>
            <h2 class="mgr-drawer-name">{{ modalManager }}</h2>
            <div class="mgr-drawer-meta">
              <span>排名 <strong>#{{ modalRank }}</strong></span>
              <span class="mgr-sep"></span>
              <span>在管 <strong>{{ modalTotalProjects }}</strong> 项 · 在建 {{ modalActiveCount }}</span>
              <span class="mgr-sep"></span>
              <span>转固率 <strong>{{ modalManagerRateStr }}</strong></span>
              <span v-if="modalReversedCount > 0" class="ds-pill warn" style="font-size:10px;margin-left:4px">
                <span class="dot"></span>{{ modalReversedCount }} 项冲回
              </span>
            </div>
          </div>
          <button class="modal-close" @click="closeModal">
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
                <div class="mgr-stat-value">{{ formatNum(modalBalance) }}<span class="mgr-stat-unit">万</span></div>
              </div>
              <div class="mgr-stat">
                <div class="mgr-stat-label">本年累计资本性支出</div>
                <div class="mgr-stat-value" :style="{ color: modalSpendYTD < 0 ? 'var(--bad)' : '' }">
                  {{ formatNum(modalSpendYTD) }}<span class="mgr-stat-unit">万</span>
                </div>
              </div>
              <div class="mgr-stat">
                <div class="mgr-stat-label">本月资本性支出</div>
                <div class="mgr-stat-value" :style="{ color: modalSpendMo < 0 ? 'var(--bad)' : '' }">
                  {{ formatNum(modalSpendMo) }}<span class="mgr-stat-unit">万</span>
                </div>
              </div>
              <div class="mgr-stat">
                <div class="mgr-stat-label">结转额 · 期初</div>
                <div class="mgr-stat-value">{{ formatNum(modalTransfer) }}<span class="mgr-stat-unit">万</span></div>
              </div>
              <div class="mgr-stat">
                <div class="mgr-stat-label">已下单待收货</div>
                <div class="mgr-stat-value">{{ formatNum(modalPending) }}<span class="mgr-stat-unit">万</span></div>
              </div>
              <div class="mgr-stat">
                <div class="mgr-stat-label">转固率</div>
                <div class="mgr-stat-value">{{ modalManagerRateStr }}</div>
              </div>
            </div>
          </div>

          <!-- Projects detail table -->
          <div class="mgr-section">
            <div class="mgr-section-head">
              <span class="mgr-section-title">所属工程明细 · {{ modalProjectsForDrawer.length }} 项</span>
              <span class="mgr-section-sub">期末余额合计 <strong style="color:var(--ink)">{{ formatNum(modalBalance) }}</strong> 万</span>
            </div>
            <div v-if="modalLoading" class="modal-loading"><div class="loader-ring"></div></div>
            <div v-else-if="modalProjectsForDrawer.length === 0" class="modal-empty">暂无工程记录</div>
            <div v-else class="mgr-tbl-wrap">
              <table class="detail-table">
                <thead>
                  <tr>
                    <th class="sortable" style="min-width:200px" @click="toggleSort('工程名称')">
                      工程名称 <span class="sort-icon" :class="getSortClass('工程名称')">{{ getSortIcon('工程名称') }}</span>
                    </th>
                    <th class="num sortable" title="结转额" @click="toggleSort('结转额')">
                      结转额 <span class="sort-icon" :class="getSortClass('结转额')">{{ getSortIcon('结转额') }}</span>
                    </th>
                    <th class="num sortable" title="本年累计资本性支出" @click="toggleSort('本年累计资本性支出')">
                      本年支出 <span class="sort-icon" :class="getSortClass('本年累计资本性支出')">{{ getSortIcon('本年累计资本性支出') }}</span>
                    </th>
                    <th class="num sortable" title="已下单待收货" @click="toggleSort('已下单待收货')">
                      已下单 <span class="sort-icon" :class="getSortClass('已下单待收货')">{{ getSortIcon('已下单待收货') }}</span>
                    </th>
                    <th class="num sortable" title="本月资本性支出" @click="toggleSort('本月资本性支出')">
                      本月支出 <span class="sort-icon" :class="getSortClass('本月资本性支出')">{{ getSortIcon('本月资本性支出') }}</span>
                    </th>
                    <th class="num sortable" title="在建工程期末余额" @click="toggleSort('在建工程期末余额')">
                      期末余额 <span class="sort-icon" :class="getSortClass('在建工程期末余额')">{{ getSortIcon('在建工程期末余额') }}</span>
                    </th>
                    <th class="sortable" @click="toggleSort('转固率')">
                      转固率 <span class="sort-icon" :class="getSortClass('转固率')">{{ getSortIcon('转固率') }}</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in sortedModalData" :key="item['工程名称']">
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
          <button class="ds-btn ghost">
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none"><path d="M3 12v1.5h10V12M5 8l3 3 3-3M8 3v8" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
            导出此人明细
          </button>
        </footer>

      </aside>
    </div>

    <!-- Four-class detail modal -->
    <div v-if="fourClassDetailVisible" class="four-class-modal-overlay" @click.self="fourClassDetailVisible = false">
      <div class="four-class-modal">
        <div class="modal-header">
          <div class="modal-title-wrap">
            <h3>{{ fourClassDetailType }}</h3>
            <span v-if="fourClassWarnings?.analysis_date" class="modal-date">数据日期：{{ fourClassWarnings.analysis_date }}</span>
          </div>
          <div class="modal-header-actions">
            <button class="export-btn-primary" @click="exportFourClassWarnings" :disabled="!currentRecordId">
              <span>↓</span> 导出预警清单
            </button>
            <button class="modal-close" @click="fourClassDetailVisible = false">✕</button>
          </div>
        </div>
        <div class="modal-body">
          <template v-if="fourClassDetailType === '四类工程预警明细'">
            <template v-for="type in fourClassTypes" :key="type.name">
              <div v-if="getGroupItems(type.name).length > 0" class="four-class-group" :class="'group-' + type.key">
                <div class="group-header">
                  <span class="group-title">{{ type.name }}</span>
                  <span class="group-count">已触发 {{ getGroupStats(type.name).triggered }} / 预警 {{ getGroupStats(type.name).warning }}</span>
                </div>
                <table class="data-table four-class-modal-table">
                  <thead><tr><th class="col-status">状态</th><th class="col-name">工程名称</th><th class="col-accept">验收类型</th><th class="col-manager">管理员</th><th class="col-date">关键日期</th><th class="col-date">截止日期</th><th class="col-project-status">工程状态</th><th class="col-days">天数</th><th class="col-suggestion">处置建议</th></tr></thead>
                  <tbody>
                    <tr v-for="item in getGroupItems(type.name)" :key="item.id" :class="'row-' + item.status">
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
                <tr v-for="item in fourClassDetailItems" :key="item.id" :class="'row-' + item.status">
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

    <!-- Transfer priority modal -->
    <div v-if="transferPriorityVisible" class="tp-overlay" @click.self="transferPriorityVisible = false">
      <div class="tp-modal">
        <div class="tp-header">
          <div class="tp-header-left">
            <h3>转固推进清单</h3>
            <span class="tp-subtitle">各管理员待转固项目 · 按转固贡献从高到低排序</span>
          </div>
          <div class="tp-header-actions">
            <button class="tp-export-btn" :disabled="transferExporting || !transferPriorityData.length" @click="handleExportTransferPriority">
              <span v-if="transferExporting">导出中…</span>
              <span v-else>导出 Excel</span>
            </button>
            <button class="modal-close" @click="transferPriorityVisible = false">✕</button>
          </div>
        </div>
        <div v-if="transferPriorityLoading" class="tp-loading">
          <div class="loader-ring" style="width:32px;height:32px;position:relative"></div>
          <p>正在计算...</p>
        </div>
        <div v-else-if="transferPriorityError" class="tp-empty tp-error"><p>{{ transferPriorityError }}</p></div>
        <div v-else-if="!transferPriorityData.length" class="tp-empty"><p>暂无待转固项目数据</p></div>
        <template v-else>
          <div class="tp-calc-bar">
            <div class="tp-calc-left">
              <span class="tp-calc-label">转固率目标测算</span>
              <div class="tp-calc-input-wrap">
                <input v-model="targetRate" type="number" min="1" max="100" step="1" placeholder="输入目标 %" class="tp-calc-input" @keyup.enter="$event.target.blur()" />
                <span class="tp-calc-unit">%</span>
                <button v-if="targetRate" class="tp-calc-clear" @click="targetRate = ''" title="清除">✕</button>
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
                        <td colspan="7">
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { uploadExcel, getCompare, getHistory, getHistorySnapshot, getManagerDetails, getTransferPriority, exportTransferPriority, pushNotify, updateTargetValue } from '../api'

const props = defineProps({
  initialData: { type: Object, default: null },
  initialRecordId: { type: Number, default: null },
  latestData: { type: Object, default: null },
  historyComparison: { type: Object, default: null },
  analysisDate: { type: String, default: null },
  snapshotLabel: { type: String, default: '' },
  fourClassWarnings: { type: Object, default: null }
})

const emit = defineEmits(['dataUpdate', 'restoreLatest', 'warningsUpdate'])

// ── Core state ──
const fileInput = ref(null)
const loading = ref(false)
const uploadMessage = ref('')
const uploadMessageType = ref('info')
const hasData = ref(false)
const showUpload = ref(false)
const dashboard = ref(null)
const summaryRows = ref([])
const maxCapital = ref(0)
const targetValue = ref(null)
const previousData = ref(null)
const selectedFile = ref(null)
const selectedFileName = ref('')
const currentRecordId = ref(null)
const isViewingHistory = ref(false)
const snapshotDisplayDate = ref(null)

// ── Manager detail (drawer) ──
const modalVisible = ref(false)
const modalData = ref([])
const modalManager = ref('')
const modalLoading = ref(false)
const sortKey = ref('本年累计资本性支出')
const sortOrder = ref('desc')

// ── History ──
const historyVisible = ref(false)
const historyLoading = ref(false)
const historyRecords = ref([])

// ── Four-class warnings ──
const fourClassWarningsLocal = ref(null)
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

// ── Computed: warnings reference ──
const fcWarnings = computed(() => fourClassWarningsLocal.value || props.fourClassWarnings)

// ── Computed: history comparison ──
const displayAnalysisDate = computed(() => snapshotDisplayDate.value || props.analysisDate)
const comparisonSource = computed(() => props.historyComparison || previousData.value)
const shouldShowHistoryCompare = computed(() => Boolean(props.historyComparison))

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

const recentHistoryCards = computed(() => historyRecords.value.slice(0, 4))

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
    },
    {
      label: '综合转固率',
      value: formatPercent(m.rate || 0),
      badgeText: rateStatus.value.text,
      badgeClass: rateStatus.value.badgeClass,
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

// ── d2 Dashboard additions ──────────────────────────────
const trendHover = ref(null)
const ptSearch = ref('')
const ptStageFilter = ref('all')
const ptStatusFilter = ref('all')
const ptPage = ref(1)
const ptPerPage = 6

const healthCard = computed(() => {
  const m = dashboard.value?.metrics
  if (!m) return { label: '—', cls: '', desc: '暂无数据', slip: '' }
  const rate = Number(m.rate || 0)
  const deficit = Number(m.deficit || 0)
  if (rate >= 0.6) return {
    label: '健康', cls: 'd2-health-ok',
    desc: `转固率 ${formatPercent(rate)}，已达年度目标`,
    slip: deficit <= 0 ? `已超年度目标 ${formatNum(Math.abs(deficit))} 万元` : `还差 ${formatNum(deficit)} 万元达标`,
  }
  if (rate >= 0.3) return {
    label: '偏低', cls: 'd2-health-warn',
    desc: `转固率 ${formatPercent(rate)}，未达目标 60%`,
    slip: deficit > 0 ? `较目标进度滞后 ${formatNum(deficit)} 万元` : '支出已达目标，待推进转固',
  }
  return {
    label: '预警', cls: 'd2-health-bad',
    desc: `转固率 ${formatPercent(rate)}，严重偏低`,
    slip: `较目标进度滞后 ${formatNum(Math.max(0, deficit))} 万元`,
  }
})

const funnelStages = computed(() => {
  const projects = projectsList.value
  let lixiang = 0, zaijian = 0, daishouhuo = 0, zhuangu = 0
  for (const p of projects) {
    if (p.rate >= 0.9 || (p.balance === 0 && p.spendYTD > 0)) zhuangu++
    else if (p.pending > 0 && p.spendYTD > 0 && p.pending > p.spendYTD * 0.5) daishouhuo++
    else if (p.spendYTD < 5 && p.balance > 0) lixiang++
    else zaijian++
  }
  const total = projects.length
  return [
    { label: '在建工程', count: total, key: 'total' },
    { label: '积极推进中', count: zaijian + daishouhuo, key: 'active' },
    { label: '已下单待收货', count: daishouhuo, key: 'daishouhuo' },
    { label: '已转固', count: zhuangu, key: 'zhuangu' },
  ]
})

const rankedManagers = computed(() =>
  summaryRows.value.map((row, i) => ({
    name: row.manager || row['工程管理员'],
    rank: i + 1,
    projects: getProjectCount(row.manager || row['工程管理员']),
    spendYTD: Number(row['本年累计资本性支出'] || row.capital || 0),
    rate: Number(row['转固率'] || row.rate || 0),
  }))
)
const managerMaxSpend = computed(() => Math.max(...rankedManagers.value.map(m => Math.abs(m.spendYTD)), 1))

const d2WarningItems = computed(() => {
  const warnings = fcWarnings.value
  const items = []
  if (warnings?.summary) {
    for (const type of fourClassTypes) {
      const triggered = warnings.summary?.[type.name]?.triggered || 0
      const warning = warnings.summary?.[type.name]?.warning || 0
      const count = triggered + warning
      if (count > 0) items.push({
        title: type.name,
        desc: `${count} 项${triggered ? '（' + triggered + ' 项已触发）' : ''}`,
        sev: triggered > 0 ? 'high' : 'med',
        key: type.name,
      })
    }
  }
  if (!items.length) {
    const m = dashboard.value?.metrics
    if (m) {
      const rate = Number(m.rate || 0)
      if (rate < 0.3) items.push({ title: '转固率严重偏低', desc: `综合转固率 ${formatPercent(rate)}，低于目标 60%`, sev: 'high', key: null })
      else if (rate < 0.6) items.push({ title: '转固率偏低', desc: `综合转固率 ${formatPercent(rate)}，低于目标 60%`, sev: 'med', key: null })
      const deficit = Number(m.deficit || 0)
      if (deficit > 50) items.push({ title: '支出进度滞后', desc: `距年度目标还差 ${formatNum(deficit)} 万元`, sev: 'med', key: null })
      const reversed = projectsList.value.filter(p => p.spendYTD < 0).length
      if (reversed) items.push({ title: '冲回超额项目', desc: `${reversed} 个项目存在资本性支出冲回`, sev: 'low', key: null })
    }
  }
  return items
})

const trendData = computed(() => {
  const W = 380, H = 140, pl = 38, pr = 36, pt = 10, pb = 22
  const iw = W - pl - pr, ih = H - pt - pb
  const sorted = [...historyRecords.value]
    .filter(r => r.dashboard_snapshot?.metrics?.total_current != null || r.dashboard_snapshot?.metrics?.capital != null)
    .sort((a, b) => String(a.file_date || a.uploaded_at || '') < String(b.file_date || b.uploaded_at || '') ? -1 : 1)
    .slice(-8)
  if (!sorted.length) {
    const cur = dashboard.value?.metrics?.total_current || dashboard.value?.metrics?.capital
    if (!cur) return null
    sorted.push({ dashboard_snapshot: { metrics: { total_current: cur, total_rate: dashboard.value.metrics.total_rate || dashboard.value.metrics.rate } }, file_date: props.analysisDate || '' })
  }
  const capitals = sorted.map(r => Number(r.dashboard_snapshot?.metrics?.total_current || r.dashboard_snapshot?.metrics?.capital || 0))
  const rates = sorted.map(r => Number(r.dashboard_snapshot?.metrics?.total_rate || r.dashboard_snapshot?.metrics?.rate || 0))
  const target = Number(targetValue.value) || 0
  const maxC = Math.max(target * 1.05, ...capitals, 10)
  const n = sorted.length
  const xAt = i => pl + (n > 1 ? (i / (n - 1)) * iw : iw / 2)
  const yAtC = v => pt + ih - (Math.max(0, Math.min(v / maxC, 1)) * ih)
  const yAtR = v => pt + ih - (Math.max(0, Math.min(v, 1)) * ih)
  const capitalPts = capitals.map((v, i) => `${xAt(i).toFixed(1)},${yAtC(v).toFixed(1)}`).join(' ')
  const capitalArea = `${xAt(0).toFixed(1)},${(pt+ih).toFixed(1)} ${capitalPts} ${xAt(n-1).toFixed(1)},${(pt+ih).toFixed(1)}`
  const ratePts = rates.map((v, i) => `${xAt(i).toFixed(1)},${yAtR(v).toFixed(1)}`).join(' ')
  const rateArea = `${xAt(0).toFixed(1)},${(pt+ih).toFixed(1)} ${ratePts} ${xAt(n-1).toFixed(1)},${(pt+ih).toFixed(1)}`
  const tgtY = target > 0 ? +yAtC(target).toFixed(1) : null
  const labels = sorted.map(r => {
    const d = r.file_date ? String(r.file_date) : ''
    const up = (r.uploaded_at || '').substring(0, 10)
    // 8位数字格式：20260320
    if (/^\d{8}$/.test(d)) {
      const m = parseInt(d.slice(4, 6))
      const day = parseInt(d.slice(6, 8))
      return `${m}/${day}`
    }
    // 4位数字格式：0320
    if (/^\d{4}$/.test(d)) {
      const m = parseInt(d.slice(0, 2))
      const day = parseInt(d.slice(2, 4))
      return `${m}/${day}`
    }
    // 日期格式：2026-04-25 或 2026/04/25
    if (up.length >= 10) {
      const m = parseInt(up.slice(5, 7))
      const day = parseInt(up.slice(8, 10))
      return `${m}/${day}`
    }
    return '—'
  })
  const step = Math.ceil(maxC / 4 / 50) * 50 || 50
  const yLabels = [0, 1, 2, 3, 4].map(i => { const v = step * i; return v > maxC ? '' : (v >= 1000 ? (v / 1000).toFixed(1) + 'k' : String(v)) })
  const yRateLabels = ['0%', '25%', '50%', '75%', '100%']
  const gridYs = [0, 0.25, 0.5, 0.75, 1].map(p => +(pt + ih - p * ih).toFixed(1))
  const dots = capitals.map((v, i) => ({
    x: +xAt(i).toFixed(1), cy: +yAtC(v).toFixed(1),
    capital: v, rate: rates[i],
    pctX: +(xAt(i) / W * 100).toFixed(1), pctY: +(yAtC(v) / H * 100).toFixed(1),
  }))
  const rateDots = rates.map((v, i) => ({ x: +xAt(i).toFixed(1), cy: +yAtR(v).toFixed(1), v }))
  return { W, H, pl, pr, pt, pb, iw, ih, capitalPts, capitalArea, ratePts, rateArea, tgtY, labels, dots, rateDots, yLabels, yRateLabels, gridYs, target, maxC }
})

const ptProjectRows = computed(() =>
  projectsList.value.map((p, i) => {
    let stage = 'zaijian', stageLabel = '在建'
    if (p.rate >= 0.9 || (p.balance === 0 && p.spendYTD > 0)) { stage = 'zhuangu'; stageLabel = '已转固' }
    else if (p.pending > 0 && p.spendYTD > 0 && p.pending > p.spendYTD * 0.5) { stage = 'daishouhuo'; stageLabel = '待收货' }
    else if (p.spendYTD < 5 && p.balance > 0) { stage = 'lixiang'; stageLabel = '立项' }
    let status = 'ok', statusLabel = '正常'
    if (p.spendYTD < 0) { status = 'bad'; statusLabel = '异常' }
    else if (p.balance > 0 && p.spendYTD < p.balance * 0.05) { status = 'warn'; statusLabel = '预警' }
    return { ...p, stage, stageLabel, status, statusLabel, idx: i + 1 }
  })
)
const ptFiltered = computed(() =>
  ptProjectRows.value.filter(p => {
    if (ptSearch.value && !p.name.includes(ptSearch.value)) return false
    if (ptStageFilter.value !== 'all' && p.stage !== ptStageFilter.value) return false
    if (ptStatusFilter.value !== 'all' && p.status !== ptStatusFilter.value) return false
    return true
  })
)
const ptPageRows = computed(() => ptFiltered.value.slice((ptPage.value - 1) * ptPerPage, ptPage.value * ptPerPage))
const ptTotalPages = computed(() => Math.max(1, Math.ceil(ptFiltered.value.length / ptPerPage)))

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
function getGroupItems(type) { return fcWarnings.value?.items?.filter(item => item.type === type) || [] }
function getGroupStats(type) {
  const items = getGroupItems(type)
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
function getWarningPillClass(key) {
  const map = { liezhang: 'info', yuzhuang: 'warn', guanbi: 'bad', guazhang: 'info' }
  return map[key] || 'info'
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
    targetValue.value = newTarget
    if (dashboard.value?.metrics) { dashboard.value.metrics.deficit = (dashboard.value.metrics.capital || 0) - newTarget }
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
function triggerFileInput() {
  if (!targetValue.value) { uploadMessage.value = '请先输入目标金额'; uploadMessageType.value = 'error'; return }
  uploadMessage.value = ''
  fileInput.value?.click()
}
function confirmTargetValue() {
  if (!targetValue.value) { uploadMessage.value = '请先输入目标金额'; uploadMessageType.value = 'error'; return }
  uploadMessage.value = `目标金额已设置为 ${Number(targetValue.value).toFixed(2)} 万元`
  uploadMessageType.value = 'info'
}
async function handleFileChange(e) {
  const file = e.target.files?.[0]
  if (file) {
    selectedFile.value = file; selectedFileName.value = file.name
    uploadMessage.value = `已选择文件：${file.name}`; uploadMessageType.value = 'info'
    if (targetValue.value && Number(targetValue.value) > 0) await processFile(file)
  }
}
async function handleDrop(e) {
  const file = e.dataTransfer.files?.[0]
  if (file) {
    selectedFile.value = file; selectedFileName.value = file.name
    uploadMessage.value = `已选择文件：${file.name}`; uploadMessageType.value = 'info'
    if (targetValue.value && Number(targetValue.value) > 0) await processFile(file)
  }
}
function clearSelectedFile() {
  selectedFile.value = null; selectedFileName.value = ''; uploadMessage.value = ''
  if (fileInput.value) fileInput.value.value = ''
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
async function loadHistoryList() {
  historyLoading.value = true
  try {
    const result = await getHistory(30)
    if (result.success) {
      const records = result.data || []
      // 后端已返回metrics数据，直接使用
      const enriched = records.map(record => ({
        ...record,
        dashboard_snapshot: { metrics: record.metrics || {} }
      }))
      historyRecords.value = enriched
    }
  } catch (error) { console.error('获取历史列表失败:', error); historyRecords.value = [] }
  finally { historyLoading.value = false }
}
async function openHistoryPanel() {
  historyVisible.value = true
  if (!historyRecords.value.length) await loadHistoryList()
}
function closeHistoryPanel() { historyVisible.value = false }
async function viewHistorySnapshot(recordId) {
  historyLoading.value = true
  try {
    const result = await getHistorySnapshot(recordId)
    if (result.success && result.data?.current) {
      applyHistorySnapshot(result.data.current, result.data.previous)
      closeHistoryPanel()
    }
  } catch (error) { console.error('获取历史快照失败:', error); alert('读取历史快照失败，请稍后重试') }
  finally { historyLoading.value = false }
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
  const latest = props.latestData || props.initialData
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
function getSortIcon(key) {
  if (sortKey.value !== key) return '⇅'
  return sortOrder.value === 'asc' ? '↑' : '↓'
}
function getSortClass(key) { return sortKey.value === key ? 'active' : '' }

// ── Formatting helpers ──
function formatNum(num) {
  if (num === null || num === undefined || isNaN(num)) return '-'
  return Number(num).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function formatHistoryTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}
function formatHistoryDateOnly(value) {
  if (!value) return '-'
  return new Date(value).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }).replace(/\//g, '-')
}
function formatFileDate(value) {
  if (!value) return '-'
  const raw = String(value)
  if (/^\d{8}$/.test(raw)) return `${raw.slice(0, 4)}-${raw.slice(4, 6)}-${raw.slice(6, 8)}`
  if (/^\d{4}$/.test(raw)) return `${raw.slice(0, 2)}-${raw.slice(2, 4)}`
  return raw
}
function formatPercent(value) { return (value * 100).toFixed(1) + '%' }
function formatDelta(value, unit = '', alreadyPercent = false) {
  const numeric = Number(value || 0)
  const sign = numeric > 0 ? '+' : ''
  if (unit === 'pct') return `${sign}${numeric.toFixed(1)} pct`
  return `${sign}${numeric.toFixed(2)} ${unit}`.trim()
}
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
function getRateClass(rate) {
  if (rate >= 1) return 'success'
  if (rate >= 0.6) return 'normal'
  if (rate >= 0.3) return 'warning'
  return 'danger'
}
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
watch(() => props.initialData, async (newData) => {
  if (newData) {
    applyDashboardData(newData)
    if (props.initialRecordId) currentRecordId.value = props.initialRecordId
    isViewingHistory.value = false
    snapshotDisplayDate.value = null
    await fetchCompareData()
  }
}, { immediate: true })

watch(() => props.fourClassWarnings, (newWarnings) => {
  fourClassWarningsLocal.value = newWarnings || null
}, { immediate: true })

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
.btn.primary { background: var(--ink); color: var(--paper); border-color: var(--ink); }
.btn.primary:hover { background: var(--accent); border-color: var(--accent); color: #fff; }
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

/* ── Upload overlay ──────────────────────────────── */
.upload-overlay {
  position: fixed; inset: 0; background: rgba(31,29,24,0.42);
  z-index: 1000; display: grid; place-items: center; padding: 40px;
}
.upload-overlay-card {
  background: var(--paper); border: 1px solid var(--line-2);
  border-radius: var(--r-xl); width: min(560px, 100%);
  box-shadow: var(--shadow-pop);
}
.upload-overlay-head {
  padding: 18px 24px; border-bottom: 1px solid var(--line);
  display: flex; align-items: center; justify-content: space-between;
}
.upload-overlay-head h3 { font-size: 16px; font-weight: 500; color: var(--ink); margin: 0; }
.upload-overlay-body { padding: 20px 24px 24px; }
.overlay-target-row { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
.overlay-target-label { font-size: 13px; color: var(--ink-2); white-space: nowrap; flex-shrink: 0; }
.overlay-target-input-wrap { display: flex; align-items: center; gap: 6px; border: 1px solid var(--line-2); border-radius: var(--r-md); padding: 5px 10px; background: var(--paper); flex: 1; }
.overlay-target-input-wrap input { border: none; outline: none; background: transparent; font-size: 14px; color: var(--ink); width: 100%; font-variant-numeric: tabular-nums; }
.overlay-target-unit { font-size: 12px; color: var(--ink-3); white-space: nowrap; }
.overlay-target-confirm { padding: 6px 14px; border-radius: var(--r-md); background: var(--accent); color: #fff; font-size: 13px; font-weight: 500; border: none; cursor: pointer; white-space: nowrap; }
.overlay-target-confirm:hover { opacity: 0.88; }
.overlay-divider { height: 1px; background: var(--line); margin: 16px 0; }

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
.sortable-th { cursor: pointer; user-select: none; }
.sortable-th:hover { color: var(--ink) !important; }
.sort-icon { margin-left: 4px; font-size: 10px; opacity: 0.4; }
.sort-icon.active { opacity: 1; color: var(--accent); }

/* ── Cell bar ──────────────────────────────────── */
.cell-bar-wrap { display: flex; align-items: center; gap: 10px; min-width: 120px; }
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

/* ── Table footnote ────────────────────────────── */
.table-footnote {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; font-size: 11.5px; color: var(--ink-3);
  border-top: 1px solid var(--line); background: var(--surface-2);
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

/* ── Manager detail modal ─────────────────────── */
/* ── Manager drawer ── */
.mgr-drawer-overlay {
  position: fixed; inset: 0;
  background: rgba(31,29,24,0.35);
  z-index: 1000; backdrop-filter: blur(2px);
  animation: fadeIn 0.2s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.mgr-drawer {
  position: fixed; top: 0; right: 0; bottom: 0;
  width: min(960px, 95vw);
  background: var(--surface); border-left: 1px solid var(--line);
  display: flex; flex-direction: column;
  box-shadow: -8px 0 32px rgba(31,29,24,0.12);
  animation: slideIn 0.22s cubic-bezier(0.22,1,0.36,1);
  overflow: hidden;
}
@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }
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
.mgr-tbl-total td { background: var(--surface-2) !important; border-top: 1px solid var(--line); }
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

/* ── Detail table (manager drawer) ── */
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
.target-edit-btn { display: inline-flex; align-items: center; padding: 2px; border: none; background: transparent; color: var(--ink-4); cursor: pointer; border-radius: var(--r-sm); transition: color 0.15s; font-family: inherit; }
.target-edit-btn:hover { color: var(--ink-3); }

/* ── Four-class modal ────────────────────────── */
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
.four-class-modal-table .col-days.days-warning { color: var(--ink); font-weight: 700; }
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

/* ── TP modal (转固推进清单) ───────────────────── */
.tp-overlay { position: fixed; inset: 0; background: rgba(31,29,24,0.38); z-index: 1000; display: flex; align-items: flex-start; justify-content: center; padding: 28px 16px; overflow-y: auto; }
.tp-modal { background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg); width: 100%; max-width: 1100px; box-shadow: var(--shadow-pop); display: flex; flex-direction: column; }
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

/* ── Empty state ──────────────────────────────── */
.empty { padding: 40px; text-align: center; color: var(--ink-3); font-size: 13px; }

/* ── Responsive ───────────────────────────────── */
@media (max-width: 1180px) {
  .upload-container { grid-template-columns: 1fr; }
  .warning-manager-grid { grid-template-columns: 1fr; }
}
@media (max-width: 900px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .four-class-cards-row { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .kpi-grid { grid-template-columns: 1fr; }
  .page { padding: 16px; }
  .upload-strip { grid-template-columns: 1fr; }
  .upload-strip .up-icon { display: none; }
  .upload-strip .up-meter { display: none; }
}

/* ══ D2 Dashboard Layout ════════════════════════════════════ */
.d2-page {
  height: 100vh; overflow: hidden;
  display: flex; flex-direction: column;
  background: #F5F3ED; color: #1F1D18;
  font-family: var(--font-sans);
}

/* Page head */
.d2-head {
  padding: 10px 20px 8px; flex-shrink: 0; background: #F5F3ED;
}
.d2-head-top {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 5px;
}
.d2-head-top h1 {
  font-size: 20px; font-weight: 500; letter-spacing: -0.02em; color: #1F1D18; margin: 0;
  display: flex; align-items: center; gap: 10px;
}
.d2-head-actions { display: flex; align-items: center; gap: 8px; }
.d2-crumb-tag {
  font-size: 10.5px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
  color: #E86A33; background: #FBE6D9; padding: 2px 7px; border-radius: 4px;
}
.d2-tbtn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 11px; border-radius: 6px; font-size: 12px;
  color: #5A5649; background: #FFFFFF; border: 1px solid rgba(31,29,24,0.14);
  cursor: pointer; font-family: inherit; transition: all 120ms; white-space: nowrap;
}
.d2-tbtn:hover { background: #F5F3ED; color: #1F1D18; }
.d2-tbtn-primary { background: #E86A33 !important; color: #fff !important; border-color: #E86A33 !important; }
.d2-tbtn-primary:hover { background: #D45E28 !important; }
.d2-tbtn-sm { font-size: 11px; padding: 3px 9px; }
.d2-tbtn-xs { font-size: 11px; padding: 3px 8px; }
.d2-head-meta {
  display: flex; align-items: center; gap: 10px;
  font-size: 12px; color: #7A7569; flex-wrap: wrap;
}
.d2-dot { width: 3px; height: 3px; background: #C0BAB0; border-radius: 50%; flex-shrink: 0; }
.d2-head-meta b { color: #1F1D18; font-weight: 500; }
.d2-edit-btn { background: none; border: none; color: #9E9A91; cursor: pointer; padding: 0 2px; display: inline-flex; align-items: center; }
.d2-edit-btn:hover { color: #E86A33; }
.d2-target-edit { display: flex; align-items: center; gap: 5px; }
.d2-target-input { width: 70px; padding: 3px 6px; border: 1px solid #D0C9BF; border-radius: 5px; background: #fff; font-size: 13px; color: #1F1D18; font-family: var(--font-mono); outline: none; }
.d2-target-input:focus { border-color: #E86A33; }
.d2-target-unit { font-size: 12px; color: #9E9A91; }

/* Main grid */
.d2-main {
  flex: 1; min-height: 0;
  display: flex; flex-direction: column;
  gap: 10px; padding: 0 12px 10px;
  overflow: hidden;
}

/* KPI row */
.d2-kpi-row {
  display: grid; grid-template-columns: 1.25fr 1fr 1fr 1fr 1fr;
  gap: 10px; flex-shrink: 0; height: 128px;
}

/* Health card */
.d2-health {
  background: linear-gradient(135deg, #FBE9DB 0%, #F6D4B9 100%);
  border-radius: 10px; padding: 14px 16px;
  display: flex; gap: 12px; align-items: flex-start;
  border: 1px solid rgba(232,106,51,0.18); overflow: hidden;
}
.d2-health-icon { width: 44px; height: 44px; flex-shrink: 0; }
.d2-health-icon svg { width: 44px; height: 44px; }
.d2-health-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.d2-health-label { font-size: 11px; font-weight: 500; color: #9E6040; text-transform: uppercase; letter-spacing: 0.07em; }
.d2-health-value { font-size: 22px; font-weight: 500; letter-spacing: -0.02em; color: #1F1D18; line-height: 1.2; }
.d2-health-value.d2-health-ok { color: #2E7D32; }
.d2-health-value.d2-health-warn { color: #E86A33; }
.d2-health-value.d2-health-bad { color: #C0392B; }
.d2-health-desc { font-size: 11.5px; color: #8A7060; line-height: 1.4; }
.d2-health-footline { height: 1px; background: rgba(232,106,51,0.2); margin: 4px 0; }
.d2-health-slip { font-size: 11px; color: #7A5A40; }

/* KPI cards */
.d2-kpi-card {
  background: #FFFFFF; border-radius: 10px; padding: 12px 14px;
  display: flex; flex-direction: column;
  border: 1px solid rgba(31,29,24,0.08); overflow: hidden;
}
.d2-kpi-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.d2-kpi-label { font-size: 11px; color: #9E9A91; letter-spacing: 0.02em; }
.d2-kpi-ic {
  width: 24px; height: 24px; background: #FBE6D9; border-radius: 6px;
  display: flex; align-items: center; justify-content: center; color: #E86A33; flex-shrink: 0;
}
.d2-kpi-val {
  font-size: 22px; font-weight: 500; color: #1F1D18;
  letter-spacing: -0.025em; display: flex; align-items: baseline; gap: 3px; line-height: 1.1;
}
.d2-kpi-val.d2-accent { color: #E86A33; }
.d2-kpi-unit { font-size: 11px; color: #9E9A91; font-weight: 400; }
.d2-kpi-prog { height: 3px; background: #EBE7DD; border-radius: 2px; overflow: hidden; margin: 5px 0 3px; }
.d2-kpi-prog-fill { height: 100%; background: #E86A33; border-radius: 2px; transition: width 0.6s ease; }
.d2-kpi-prog-label { display: flex; justify-content: space-between; font-size: 10.5px; color: #9E9A91; }
.d2-pct { font-weight: 500; color: #E86A33; font-family: var(--font-mono); }
.d2-kpi-foot { font-size: 11px; color: #9E9A91; margin-top: auto; padding-top: 4px; }
.d2-ok { color: #2E7D32; }
.d2-warn-text { color: #E86A33; }
.d2-neg { color: #C0392B !important; }

/* Mid row */
.d2-mid-row {
  display: grid; grid-template-columns: 1.15fr 0.95fr 1.3fr;
  gap: 10px; height: 200px; flex-shrink: 0;
}

/* Bot row */
.d2-bot-row {
  display: grid; grid-template-columns: 0.75fr 1.55fr;
  gap: 10px; flex: 1; min-height: 0;
}

/* Panel */
.d2-panel {
  background: #FFFFFF; border-radius: 10px;
  border: 1px solid rgba(31,29,24,0.08);
  display: flex; flex-direction: column; overflow: hidden;
}
.d2-panel-scroll { overflow: hidden; }
.d2-panel-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px 8px; border-bottom: 1px solid rgba(31,29,24,0.07);
  flex-shrink: 0; gap: 8px; min-height: 38px;
}
.d2-panel-head h3 { font-size: 12.5px; font-weight: 500; color: #1F1D18; margin: 0; white-space: nowrap; }
.d2-sub { font-size: 10.5px; color: #9E9A91; font-weight: 400; }

/* Trend chart */
.d2-trend-wrap { flex: 1; min-height: 0; position: relative; padding: 4px 6px 0; overflow: hidden; }
.d2-trend-svg { width: 100%; height: 100%; display: block; }
.d2-trend-grid line { stroke: rgba(31,29,24,0.06); stroke-width: 1; }
.d2-trend-axis text { fill: #9E9A91; font-size: 9px; font-family: var(--font-mono); }
.d2-trend-axis-r text { fill: #6BBF8E; }
.d2-trend-target { stroke: #E86A33; stroke-width: 1; stroke-dasharray: 4 3; opacity: 0.7; }
.d2-trend-area { fill: url(#td2-grad); }
.d2-trend-rate-area { fill: url(#td2-rate-grad); }
.d2-trend-line { fill: none; stroke: #E86A33; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.d2-trend-rate-line { fill: none; stroke: #6BBF8E; stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round; }
.d2-pt { fill: #FFFFFF; stroke: #E86A33; stroke-width: 1.5; }
.d2-pt-active { fill: #E86A33; stroke: #E86A33; stroke-width: 1.5; }
.d2-pt-rate { fill: #6BBF8E; }
.d2-trend-hover-line { stroke: #E86A33; stroke-width: 1; stroke-dasharray: 3 2; opacity: 0.4; }
.d2-trend-tip {
  position: absolute; background: #1F1D18; color: #fff;
  padding: 6px 10px; border-radius: 6px; font-size: 11px; pointer-events: none;
  display: flex; flex-direction: column; gap: 2px; white-space: nowrap; z-index: 10;
}
.d2-trend-tip strong { font-size: 11.5px; }
.d2-trend-tip em { font-style: normal; color: #6BBF8E; }
.d2-trend-empty { flex: 1; display: flex; align-items: center; justify-content: center; font-size: 12px; color: #9E9A91; }
.d2-legend-row { display: flex; align-items: center; gap: 10px; }
.d2-legend-item { display: flex; align-items: center; gap: 4px; font-size: 10px; color: #9E9A91; white-space: nowrap; }
.d2-lsw { width: 16px; height: 2px; border-radius: 1px; display: inline-block; }
.d2-lsw-orange { background: #E86A33; }
.d2-lsw-green { background: #6BBF8E; }
.d2-lsw-dashed { background: none; border-top: 2px dashed #E86A33; opacity: 0.7; }

/* Funnel */
.d2-funnel { flex: 1; padding: 8px 14px; display: flex; flex-direction: column; justify-content: space-evenly; gap: 4px; overflow: hidden; }
.d2-funnel-row { display: flex; align-items: center; gap: 8px; }
.d2-funnel-bar-wrap { flex: 1; min-width: 0; }
.d2-funnel-bar { height: 18px; border-radius: 3px; width: var(--fw, 100%); transition: width 0.5s ease; }
.d2-funnel-l1 { background: #E86A33; }
.d2-funnel-l2 { background: #F0A077; }
.d2-funnel-l3 { background: #F5C2A0; }
.d2-funnel-l4 { background: #88C988; }
.d2-funnel-meta { display: flex; align-items: center; gap: 5px; flex-shrink: 0; }
.d2-funnel-label { font-size: 10.5px; color: #7A7569; min-width: 68px; text-align: right; }
.d2-funnel-count { font-size: 13px; font-weight: 500; color: #1F1D18; font-family: var(--font-mono); min-width: 22px; text-align: right; }
.d2-funnel-pct { font-size: 10px; color: #9E9A91; font-family: var(--font-mono); min-width: 34px; }

/* Manager ranking */
.d2-rank-tbl { width: 100%; border-collapse: collapse; font-size: 12px; }
.d2-rank-tbl thead th {
  padding: 6px 12px; font-weight: 500; font-size: 10.5px; color: #9E9A91;
  text-transform: uppercase; letter-spacing: 0.05em;
  border-bottom: 1px solid rgba(31,29,24,0.07); text-align: left;
}
.d2-rank-tbl thead th.num { text-align: right; }
.d2-rank-tbl tbody td { padding: 8px 12px; border-bottom: 1px solid rgba(31,29,24,0.05); vertical-align: middle; }
.d2-rank-tbl tbody tr:last-child td { border-bottom: none; }
.d2-rank-row { cursor: pointer; }
.d2-rank-row:hover td { background: #F8F6F2; }
.d2-rank-tbl .num { text-align: right; font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
.d2-rank-badge {
  display: inline-flex; align-items: center; justify-content: center;
  width: 20px; height: 20px; border-radius: 5px;
  font-size: 10.5px; font-family: var(--font-mono); background: #EBE7DD; color: #7A7569;
}
.d2-rank-badge.r1 { background: #1F1D18; color: #fff; }
.d2-rank-badge.r2 { background: #4A4740; color: #fff; }
.d2-rank-badge.r3 { background: #7A7569; color: #fff; }
.d2-rank-name { font-weight: 500; color: #1F1D18; }
.d2-mini-bar-wrap { display: flex; align-items: center; gap: 6px; }
.d2-mini-bar { flex: 1; height: 4px; background: #EBE7DD; border-radius: 2px; overflow: hidden; min-width: 30px; }
.d2-mini-fill { height: 100%; background: #E86A33; border-radius: 2px; }
.d2-rate-text { font-size: 10.5px; color: #7A7569; font-family: var(--font-mono); white-space: nowrap; min-width: 34px; text-align: right; }

/* Warnings */
.d2-warn-list { flex: 1; min-height: 0; overflow-y: auto; }
.d2-warn-count { font-size: 11px; color: #9E9A91; }
.d2-warn-count b { color: #E86A33; }
.d2-warn-item {
  display: grid; grid-template-columns: 28px 1fr auto;
  align-items: flex-start; gap: 8px; padding: 10px 14px;
  border-bottom: 1px solid rgba(31,29,24,0.05);
}
.d2-warn-item:last-child { border-bottom: none; }
.d2-warn-item.clickable { cursor: pointer; }
.d2-warn-item.clickable:hover { background: #F8F6F2; }
.d2-warn-ic { width: 28px; height: 28px; border-radius: 6px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.d2-warn-ic.sev-high { background: rgba(192,57,43,0.1); color: #C0392B; }
.d2-warn-ic.sev-med { background: rgba(232,106,51,0.1); color: #E86A33; }
.d2-warn-ic.sev-low { background: rgba(122,117,105,0.1); color: #7A7569; }
.d2-warn-body { min-width: 0; }
.d2-warn-title { font-size: 12px; font-weight: 500; color: #1F1D18; }
.d2-warn-desc { font-size: 11px; color: #7A7569; margin-top: 2px; }
.d2-warn-sev { font-size: 10.5px; font-weight: 500; padding: 2px 6px; border-radius: 4px; white-space: nowrap; align-self: center; }
.d2-warn-sev.sev-high { background: rgba(192,57,43,0.08); color: #C0392B; }
.d2-warn-sev.sev-med { background: rgba(232,106,51,0.08); color: #E86A33; }
.d2-warn-sev.sev-low { background: rgba(122,117,105,0.08); color: #7A7569; }
.d2-warn-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; color: #9E9A91; font-size: 12px; }
.d2-warn-more { padding: 8px 14px; font-size: 11px; color: #E86A33; cursor: pointer; border-top: 1px solid rgba(31,29,24,0.07); text-align: center; flex-shrink: 0; }
.d2-warn-more:hover { text-decoration: underline; }

/* Project table */
.d2-ptable-bar {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; border-bottom: 1px solid rgba(31,29,24,0.07); flex-shrink: 0;
}
.d2-ptable-bar h3 { font-size: 12.5px; font-weight: 500; color: #1F1D18; margin: 0; white-space: nowrap; flex-shrink: 0; }
.d2-search {
  display: flex; align-items: center; gap: 5px;
  background: #F5F3ED; border-radius: 6px; padding: 4px 8px;
  border: 1px solid rgba(31,29,24,0.1); flex: 1; min-width: 80px; max-width: 160px;
}
.d2-search svg { opacity: 0.5; flex-shrink: 0; }
.d2-search input { border: none; background: transparent; outline: none; font-size: 12px; color: #1F1D18; width: 100%; font-family: inherit; }
.d2-search input::placeholder { color: #9E9A91; }
.d2-sel {
  padding: 4px 8px; border-radius: 6px;
  border: 1px solid rgba(31,29,24,0.12); background: #FFFFFF;
  font-size: 11.5px; color: #5A5649; font-family: inherit; cursor: pointer; outline: none;
}
.d2-ptable-wrap { flex: 1; min-height: 0; overflow-y: auto; overflow-x: auto; }
.d2-ptable { width: 100%; border-collapse: collapse; font-size: 12px; min-width: 520px; }
.d2-ptable thead th {
  padding: 7px 10px; text-align: left; font-weight: 500; font-size: 10.5px;
  color: #9E9A91; text-transform: uppercase; letter-spacing: 0.05em;
  background: #F8F6F2; border-bottom: 1px solid rgba(31,29,24,0.08);
  position: sticky; top: 0; white-space: nowrap;
}
.d2-ptable thead th.num { text-align: right; }
.d2-ptable tbody td { padding: 7px 10px; border-bottom: 1px solid rgba(31,29,24,0.05); vertical-align: middle; }
.d2-ptable tbody tr:last-child td { border-bottom: none; }
.d2-ptable tbody tr:hover td { background: #F8F6F2; }
.d2-ptable .num { text-align: right; font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
.d2-idx { color: #9E9A91; font-family: var(--font-mono); font-size: 10.5px; }
.d2-pname { font-weight: 500; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.d2-muted { color: #9E9A91; }
.d2-mgr-link { color: #5A5649; cursor: pointer; }
.d2-mgr-link:hover { color: #E86A33; text-decoration: underline; text-underline-offset: 2px; }
.d2-stage-tag { display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 10.5px; font-weight: 500; white-space: nowrap; }
.st-zaijian { background: #EBF4FF; color: #1D6FA4; }
.st-lixiang { background: #F3EFF5; color: #7B5EA7; }
.st-daishouhuo { background: #FFF4E5; color: #B45309; }
.st-zhuangu { background: #EEFBEE; color: #2E7D32; }
.d2-status-dot { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; white-space: nowrap; }
.d2-status-dot .d { width: 5px; height: 5px; border-radius: 50%; }
.sd-ok .d { background: #4CAF50; } .sd-ok { color: #2E7D32; }
.sd-warn .d { background: #FF9800; } .sd-warn { color: #B45309; }
.sd-bad .d { background: #F44336; } .sd-bad { color: #C0392B; }
.d2-empty-row { text-align: center; padding: 24px; color: #9E9A91; font-size: 12px; }
.d2-pager {
  display: flex; align-items: center; justify-content: space-between;
  padding: 7px 12px; border-top: 1px solid rgba(31,29,24,0.07); flex-shrink: 0;
}
.d2-pager-count { font-size: 11px; color: #9E9A91; }
.d2-pager-ctrls { display: flex; align-items: center; gap: 3px; }
.d2-pager-ctrls button {
  min-width: 24px; height: 24px; padding: 0 6px; border-radius: 4px;
  border: 1px solid transparent; background: transparent; font-size: 12px;
  color: #5A5649; cursor: pointer; font-family: inherit;
  display: flex; align-items: center; justify-content: center;
}
.d2-pager-ctrls button:hover:not(:disabled) { background: #F5F3ED; }
.d2-pager-ctrls button.on { background: #E86A33; color: #fff; border-color: #E86A33; }
.d2-pager-ctrls button:disabled { opacity: 0.3; cursor: not-allowed; }

/* ds-pill / ds-btn for manager drawer (used inside d2-page) */
.ds-pill {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 7px; border-radius: 999px; font-size: 10.5px; font-weight: 500;
  background: var(--warn-soft); color: var(--warn); border: 1px solid transparent;
}
.ds-pill .dot { width: 5px; height: 5px; border-radius: 50%; background: currentColor; }
.ds-btn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 6px 12px; border-radius: var(--r-md); font-size: 12px;
  color: var(--ink-2); background: transparent; border: 1px solid var(--line-2);
  cursor: pointer; font-family: inherit; transition: all 120ms;
}
.ds-btn:hover { background: var(--paper-2); color: var(--ink); }
</style>
