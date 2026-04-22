<template>
  <div class="dashboard">

    <!-- ── 标签栏 ── -->
    <div class="bpage-tabs">
      <button class="bpage-tab" :class="{ active: batchTab === 'budget' }" @click="batchTab = 'budget'">预算执行</button>
      <button class="bpage-tab" :class="{ active: batchTab === 'batch' }" @click="switchToBatchTab">
        批次下达
        <span v-if="batchData.batches.length" class="bpage-tab-count">{{ batchData.batches.length }}</span>
      </button>
    </div>

    <!-- ── 预算执行 Tab ── -->
    <div v-show="batchTab === 'budget'">
    <div v-if="!hasData" class="upload-section">
      <div class="upload-shell">
        <div class="upload-page-header">
          <h1>预算立项</h1>
          <p>上传预算执行情况，自动生成立项进度、专业分布与项目明细</p>
        </div>
        <div class="upload-container">
          <div class="upload-copy">
            <div class="upload-copy-top">
              <span class="panel-kicker budget-kicker">Budget Approval Intake</span>
            </div>
            <div class="budget-intro-card">
              <div class="inline-target-header">
                <h3>预算下达及立项进度分析</h3>
              </div>
              <div class="budget-output-label">上传后自动产出</div>
              <div class="budget-output-block">
                <div class="budget-output-title">核心指标</div>
                <div class="budget-output-items">
                  <span class="budget-output-item blue">年度预算</span>
                  <span class="budget-output-item blue">已占用</span>
                  <span class="budget-output-item blue">预占用</span>
                  <span class="budget-output-item purple">立项进度</span>
                </div>
              </div>
              <div class="budget-output-block">
                <div class="budget-output-title">明细数据</div>
                <div class="budget-output-items">
                  <span class="budget-output-item amber">各专业进度表</span>
                  <span class="budget-output-item green">新建项目明细</span>
                </div>
              </div>
              <div class="upload-checklist budget-checklist">
                <div class="check-item">
                  <span class="check-icon purple">✓</span>
                  <span>自动识别<b>新建项目明细</b> sheet，无需手动指定年份</span>
                </div>
                <div class="check-item">
                  <span class="check-icon purple">✓</span>
                  <span>建议文件：<b>预算执行情况（预算占用）</b></span>
                </div>
                <div class="check-item">
                  <span class="check-icon purple">✓</span>
                  <span>同名文件自动覆盖，<b>保留历史快照</b>可随时回溯</span>
                </div>
              </div>
            </div>
          </div>

          <div class="upload-box">
            <div class="upload-zone budget-upload-zone" @dragover.prevent @drop.prevent="handleDrop" @click="triggerFileInput">
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
                <h2>拖拽文件到此处，或<span class="link budget-link">点击选择</span></h2>
                <p class="upload-hint">支持 .xlsx 格式 · 预算执行情况（预算占用）</p>
                <div class="file-types">
                  <span class="file-tag">.xlsx</span>
                  <span class="file-tag">预算执行情况（预算占用）</span>
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
        <div v-if="recentHistoryCards.length" class="recent-uploads-card budget-recent-card">
          <div class="recent-uploads-head">
            <h3>最近上传记录</h3>
            <button class="view-all-btn budget-view-all-btn" @click="openHistoryPanel">查看全部 →</button>
          </div>
          <div class="recent-uploads-grid">
            <button
              v-for="record in recentHistoryCards"
              :key="record.id"
              class="recent-upload-item"
              @click="viewHistorySnapshot(record.id)"
            >
              <div class="recent-upload-date">{{ formatHistoryDateOnly(record.uploaded_at) }}</div>
              <div class="recent-upload-value budget-recent-value">{{ formatBudgetHistoryProgress(record) }} <span>立项</span></div>
              <div class="recent-upload-meta">已占用 {{ formatNum(record.snapshot_data?.occupied_total || 0) }} 万</div>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="page">

      <!-- ── Page Header ── -->
      <header class="page-head">
        <div class="page-head-l">
          <span class="eyebrow">预算立项 / Budget Allocation</span>
          <h1 class="page-title-h1">年度预算执行</h1>
          <div class="page-meta">
            <svg width="11" height="11" viewBox="0 0 11 11" fill="none" style="color:var(--ink-3)"><rect x="1" y="1" width="9" height="9" rx="1" stroke="currentColor" stroke-width="1"/><path d="M3 4h5M3 6h3" stroke="currentColor" stroke-width="1" stroke-linecap="round"/></svg>
            <span>预算立项分析.xlsx</span>
            <span class="ph-sep"></span>
            <span>{{ data.categories?.length || 0 }} 个专业 · {{ data.projects?.length || 0 }} 个立项</span>
            <span class="ph-sep"></span>
            <span>预算合计 {{ data.budget_total?.toFixed(2) || '0.00' }} 万</span>
          </div>
        </div>
        <div class="page-actions">
          <button v-if="viewingSnapshotLabel" class="btn ghost" @click="restoreLatestView">
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none"><path d="M2 4l1 3 3-1M14 12l-1-3-3 1M3 7a5 5 0 019-1M13 9a5 5 0 01-9 1" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
            返回最新
          </button>
        </div>
      </header>

      <!-- ── Upload Strip ── -->
      <div class="ds-upload-strip">
        <div class="up-icon">
          <svg width="18" height="18" viewBox="0 0 16 16" fill="none"><path d="M4 2h6l2 2v10H4V2zM10 2v2h2" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </div>
        <div class="up-meta">
          <div class="up-title">
            预算立项分析.xlsx
            <span class="up-badge">已加载</span>
            <span v-if="viewingSnapshotLabel" class="snapshot-badge-sm">{{ viewingSnapshotLabel }}</span>
          </div>
          <div class="up-sub">
            <template v-if="displayAnalysisDate"><span>数据日期 {{ displayAnalysisDate }}</span> · </template>
            <span>{{ data.categories?.length || 0 }} 个专业</span>
          </div>
        </div>
        <div class="up-meter">
          <b>{{ data.projects?.length || 0 }}</b>
          <span>ITEMS</span>
        </div>
        <div style="display:flex;gap:6px">
          <button class="btn ghost" @click="openHistoryPanel">
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none"><path d="M2 5h12v9H2V5zM2 5V3h12v2M5 2v3M11 2v3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
            历史记录
          </button>
        </div>
      </div>

      <!-- ── Hero KPI + Stacked bar ── -->
      <div class="section" style="margin-bottom:48px">
        <div class="ds-card" style="padding:32px 36px">
          <div class="budget-hero-kpis">
            <div>
              <div class="bk-label">年度预算</div>
              <div class="bk-value mono">{{ animatedBudget[0].toFixed(2) }}<span class="bk-unit">万</span></div>
              <div class="bk-sub">预算入账总额</div>
            </div>
            <div>
              <div class="bk-label">已占用</div>
              <div class="bk-value mono accent">{{ animatedBudget[1].toFixed(2) }}</div>
              <div class="bk-sub">占预算 <span class="mono" style="color:var(--ink)">{{ data.budget_total > 0 ? ((data.occupied_total || 0) / data.budget_total * 100).toFixed(1) : '0.0' }}%</span></div>
            </div>
            <div>
              <div class="bk-label">全年支出</div>
              <div class="bk-value mono" style="color:var(--ink-2)">{{ animatedBudget[2].toFixed(2) }}</div>
              <div class="bk-sub">
                占预算 <span class="mono">{{ data.budget_total > 0 ? ((data.annual_spend_total || 0) / data.budget_total * 100).toFixed(1) : '0.0' }}%</span>
                <span v-if="data.budget_total > 0 && (data.annual_spend_total || 0) / data.budget_total > 1" style="color:var(--bad)"> ⚠</span>
              </div>
            </div>
            <div>
              <div class="bk-label">剩余可调度</div>
              <div class="bk-value mono">{{ animatedBudget[3].toFixed(2) }}</div>
              <div class="bk-sub">
                {{ data.budget_total > 0 ? Math.max(0, 100 - ((data.occupied_total || 0) + (data.preoccupied_total || 0)) / data.budget_total * 100).toFixed(1) : '0.0' }}% 未分配
              </div>
            </div>
          </div>
          <div>
            <div class="budget-bar-track">
              <div :style="{ width: (data.budget_total > 0 ? Math.min((data.occupied_total || 0) / data.budget_total * 100, 100) : 0) + '%', background: 'var(--accent)' }"></div>
              <div :style="{ width: (data.budget_total > 0 ? Math.min((data.preoccupied_total || 0) / data.budget_total * 100, 100) : 0) + '%', background: 'var(--accent-soft)' }"></div>
            </div>
            <div class="budget-bar-legend">
              <div class="bbl-item">
                <span class="bbl-dot" style="background:var(--accent)"></span>
                已占用 <span class="mono" style="color:var(--ink)">{{ data.budget_total > 0 ? ((data.occupied_total || 0) / data.budget_total * 100).toFixed(1) : '0.0' }}%</span>
              </div>
              <div class="bbl-item">
                <span class="bbl-dot" style="background:var(--accent-soft);border:1px solid #e0b08a"></span>
                预占用 <span class="mono" style="color:var(--ink)">{{ data.budget_total > 0 ? ((data.preoccupied_total || 0) / data.budget_total * 100).toFixed(1) : '0.0' }}%</span>
              </div>
              <div class="bbl-item">
                <span class="bbl-dot" style="background:var(--paper-2);border:1px solid var(--line)"></span>
                剩余 <span class="mono" style="color:var(--ink)">{{ data.budget_total > 0 ? Math.max(0, 100 - ((data.occupied_total || 0) + (data.preoccupied_total || 0)) / data.budget_total * 100).toFixed(1) : '0.0' }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── History comparison (when available) ── -->
      <div v-if="compareOverview" class="section">
        <div class="section-head">
          <h2>历史对比</h2>
          <span class="sub">当前版本与上一版相比</span>
        </div>
        <div class="ds-card" style="padding:20px">
          <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:16px">
            <div class="compare-chip">
              <span class="compare-chip-label">年度预算</span>
              <strong>{{ formatNum(compareOverview.budget.current) }} 万元</strong>
              <span class="compare-chip-detail">较上版 {{ formatDelta(compareOverview.budget.diff, '万元') }}</span>
            </div>
            <div class="compare-chip">
              <span class="compare-chip-label">立项进度</span>
              <strong>{{ formatPercent(compareOverview.progress.current) }}</strong>
              <span class="compare-chip-detail">较上版 {{ formatDelta(compareOverview.progress.diff, 'pct') }}</span>
            </div>
          </div>
          <div v-if="categoryProgressTop5.length">
            <div style="font-size:13px;font-weight:500;color:var(--ink);margin-bottom:10px">专业推进 Top 5</div>
            <table class="ds-tbl" style="font-size:12.5px">
              <thead><tr><th>一级专业</th><th class="num">当前立项进度</th><th class="num">较上版变化</th></tr></thead>
              <tbody>
                <tr v-for="item in categoryProgressTop5" :key="item.name">
                  <td>{{ item.name }}</td>
                  <td class="num mono">{{ formatPercent(item.currentProgress) }}</td>
                  <td class="num"><span :style="{ color: item.progressDiff >= 0 ? 'var(--ok)' : 'var(--bad)' }">{{ formatDelta(item.progressDiff, 'pct') }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ── 按专业拆分 ── -->
      <div class="section">
        <div class="section-head">
          <div>
            <h2>按专业拆分</h2>
            <span class="sub">共 <strong>{{ data.categories?.length || 0 }}</strong> 个专业 · 其中有预算或支出的</span>
          </div>
        </div>
        <div class="ds-card" style="padding:0">
          <table class="ds-tbl cat-tbl">
            <colgroup>
              <col style="width:28px">
              <col style="width:120px">
              <col style="width:100px">
              <col style="width:100px">
              <col style="width:100px">
              <col style="width:100px">
              <col>
              <col style="width:72px">
            </colgroup>
            <thead>
              <tr>
                <th></th>
                <th>专业</th>
                <th class="num">年度预算</th>
                <th class="num">已占用</th>
                <th class="num">预占用</th>
                <th class="num">全年支出</th>
                <th style="padding-left:12px">预算使用进度</th>
                <th class="num">支出完成率</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(cat, i) in (data.categories || [])" :key="cat.name"
                :style="{ opacity: cat.budget === 0 && cat.annual_spend === 0 ? 0.4 : 1 }">
                <td style="padding-left:16px">
                  <span :style="{ display:'block', width:'8px', height:'8px', borderRadius:'2px', background: `oklch(${72 - i*2.5}% 0.10 ${40 + i*22})` }"></span>
                </td>
                <td class="col-name" style="font-weight:500">{{ cat.name }}</td>
                <td class="num mono">{{ cat.budget > 0 ? formatNum(cat.budget) : '—' }}</td>
                <td class="num mono" :style="{ color: cat.occupied > 0 ? 'var(--ink)' : 'var(--ink-4)', fontWeight: cat.occupied > 0 ? 500 : 400 }">
                  {{ cat.occupied > 0 ? formatNum(cat.occupied) : '—' }}
                </td>
                <td class="num mono" :style="{ color: cat.preoccupied > 0 ? 'var(--warn)' : 'var(--ink-4)' }">
                  {{ cat.preoccupied > 0 ? formatNum(cat.preoccupied) : '—' }}
                </td>
                <td class="num mono" :style="{ color: cat.spend_progress > 1 ? 'var(--bad)' : 'var(--ink-2)' }">
                  {{ cat.annual_spend > 0 ? formatNum(cat.annual_spend) : '—' }}
                </td>
                <td style="padding-left:12px">
                  <div v-if="cat.budget > 0" style="display:flex;align-items:center;gap:10px">
                    <div style="flex:1;display:flex;height:5px;border-radius:3px;overflow:hidden;background:var(--paper-2);min-width:80px">
                      <div :style="{ width: Math.min((cat.occupied || 0) / cat.budget * 100, 100) + '%', background: (cat.occupied || 0) / cat.budget > 1 ? 'var(--bad)' : 'var(--accent)' }"></div>
                      <div :style="{ width: Math.min((cat.preoccupied || 0) / cat.budget * 100, 100) + '%', background: 'var(--warn)', opacity: 0.45 }"></div>
                    </div>
                    <span class="mono" style="font-size:11px;color:var(--ink-3);width:48px;text-align:right;flex-shrink:0">
                      {{ (((cat.occupied || 0) + (cat.preoccupied || 0)) / cat.budget * 100).toFixed(1) }}%
                    </span>
                  </div>
                  <span v-else style="font-size:11px;color:var(--ink-4)">无预算</span>
                </td>
                <td class="num mono" :style="{ color: cat.spend_progress > 1 ? 'var(--bad)' : cat.spend_progress > 0.8 ? 'var(--warn)' : 'var(--ink-3)' }">
                  {{ cat.budget > 0 ? (cat.spend_progress * 100).toFixed(1) + '%' : '—' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ── 立项清单 ── -->
      <div class="section" v-if="data.projects?.length">
        <div class="section-head">
          <div>
            <h2>2026 年立项清单</h2>
            <span class="sub">共 <strong>{{ filteredProjects.length }}</strong> 个立项项目 · 来源：立项表</span>
          </div>
          <div class="section-actions">
            <select v-model="selectedManager" class="filter-sel">
              <option value="">全部管理员</option>
              <option v-for="manager in managerOptions" :key="manager" :value="manager">{{ manager }}</option>
            </select>
            <select v-model="selectedCategory" class="filter-sel">
              <option value="">全部专业</option>
              <option v-for="category in categoryOptions" :key="category" :value="category">{{ category }}</option>
            </select>
          </div>
        </div>
        <div class="ds-card">
          <table class="ds-tbl">
            <thead>
              <tr>
                <th>立项编号</th>
                <th>项目名称</th>
                <th>专业</th>
                <th>负责人</th>
                <th class="num">占用预算</th>
                <th class="num">预占用</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="proj in filteredProjects" :key="proj.code">
                <td class="mono muted" style="font-size:12px">{{ proj.code }}</td>
                <td class="col-name" :title="proj.name">{{ proj.name }}</td>
                <td class="muted">{{ proj.category }}</td>
                <td>{{ proj.manager || '—' }}</td>
                <td class="num mono" :style="{ fontWeight: proj.occupied > 0 ? 500 : 400, color: proj.occupied > 0 ? 'var(--ink)' : 'var(--ink-4)' }">
                  {{ proj.occupied > 0 ? formatNum(proj.occupied) : '—' }}
                </td>
                <td class="num mono muted">{{ proj.preoccupied > 0 ? formatNum(proj.preoccupied) : '—' }}</td>
              </tr>
              <tr v-if="filteredProjects.length === 0">
                <td colspan="6" style="text-align:center;color:var(--ink-3);padding:32px">无匹配项目</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>



    </div><!-- /budget tab -->

    <!-- ══════════════════════════════════════════════════════════ -->
    <!-- 批次下达 Tab                                               -->
    <!-- ══════════════════════════════════════════════════════════ -->
    <div v-show="batchTab === 'batch'" class="batch-view">

      <div class="batch-view-head">
        <div>
          <span class="eyebrow">投资预算 / Budget Batches</span>
          <h1 class="page-title-h1">批次下达台账</h1>
          <div class="page-meta">
            <span>{{ batchData.specialties.length }} 个专业</span>
            <span class="ph-sep"></span>
            <span>{{ batchData.batches.length }} 批次</span>
            <span v-if="batchData.batches.length" class="ph-sep"></span>
            <span v-if="batchData.batches.length">累计下达 <strong>{{ formatBatchNum(grandTotal) }}</strong> 万元</span>
          </div>
        </div>
        <div class="batch-head-actions">
          <button class="btn ghost" @click="openSpecialtyPanel">
            <svg width="13" height="13" viewBox="0 0 16 16" fill="none"><rect x="2" y="2" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.3"/><rect x="9" y="2" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.3"/><rect x="2" y="9" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.3"/><path d="M11.5 9v5M9 11.5h5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
            管理专业
          </button>
          <button class="btn primary" @click="openCreateModal">
            <svg width="13" height="13" viewBox="0 0 16 16" fill="none"><path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            新增批次
          </button>
        </div>
      </div>

      <!-- 加载中 -->
      <div v-if="batchLoading" class="batch-loading-wrap">
        <div class="loader-ring"></div>
        <span>读取中...</span>
      </div>

      <!-- 表格 -->
      <div v-else class="ds-card" style="padding:0;overflow:hidden">
        <div class="batch-table-outer">
          <table class="batch-tbl">
            <thead>
              <tr>
                <th class="bc-date">批次日期</th>
                <th v-for="s in batchData.specialties" :key="s" class="bc-amount">{{ s }}</th>
                <th class="bc-subtotal">小计</th>
                <th class="bc-note">用途说明</th>
                <th class="bc-ops"></th>
              </tr>
            </thead>
            <tbody>
              <!-- 预算下达合计行 -->
              <tr class="br-total">
                <td class="bc-date">预算下达合计</td>
                <td v-for="s in batchData.specialties" :key="s" class="bc-amount">
                  <span v-if="batchData.totals[s]" :class="{ neg: batchData.totals[s] < 0 }">{{ formatBatchNum(batchData.totals[s]) }}</span>
                  <span v-else class="bc-zero">—</span>
                </td>
                <td class="bc-subtotal"><strong>{{ formatBatchNum(grandTotal) }}</strong></td>
                <td class="bc-note bc-note-muted">共 {{ batchData.batches.length }} 批次</td>
                <td class="bc-ops"></td>
              </tr>
              <!-- 各批次 -->
              <tr v-for="(batch, idx) in batchData.batches" :key="batch.id"
                class="br-batch" :class="{ 'br-even': idx % 2 === 1 }">
                <td class="bc-date">{{ batch.batch_date }}</td>
                <td v-for="s in batchData.specialties" :key="s" class="bc-amount">
                  <div class="bc-cell-wrap"
                    @mouseenter="batch.notes?.[s] ? showCellNote($event, batch.notes[s]) : null"
                    @mouseleave="hideCellNote">
                    <span v-if="batch.amounts[s] != null && batch.amounts[s] !== 0"
                      :class="{ neg: batch.amounts[s] < 0 }">{{ formatBatchNum(batch.amounts[s]) }}</span>
                    <span v-else class="bc-zero">—</span>
                    <span v-if="batch.notes?.[s]" class="bc-note-corner"></span>
                  </div>
                </td>
                <td class="bc-subtotal">{{ formatBatchNum(batchSubtotal(batch)) }}</td>
                <td class="bc-note" :title="batch.note">{{ batch.note }}</td>
                <td class="bc-ops">
                  <button class="btn-row-op" @click="openEditModal(batch)">编辑</button>
                  <button class="btn-row-op del" @click="confirmDeleteBatch(batch)">删除</button>
                </td>
              </tr>
              <!-- 空状态 -->
              <tr v-if="!batchData.batches.length">
                <td :colspan="batchData.specialties.length + 4" class="batch-empty-cell">
                  暂无批次记录，点击右上角「新增批次」开始
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ── 新增 / 编辑批次弹窗 ── -->
      <div v-if="batchModal.visible" class="modal-overlay" @click.self="closeBatchModal">
        <div class="modal-box batch-modal-box">
          <div class="modal-head">
            <h3>{{ batchModal.mode === 'create' ? '新增批次' : '编辑批次' }}</h3>
            <button class="modal-close" @click="closeBatchModal">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
          <div class="modal-body">
            <div class="form-row">
              <label class="form-label">批次日期</label>
              <input type="date" v-model="batchModal.form.batch_date" class="form-input" />
            </div>
            <div class="form-row">
              <label class="form-label">用途说明</label>
              <textarea v-model="batchModal.form.note" class="form-textarea" rows="2"
                placeholder="简述本次批次下达的用途、专项背景..."></textarea>
            </div>
            <div class="form-section-title">
              各专业下达金额
              <span class="form-section-hint">（万元，不填为 0，支持负数表示调减）</span>
            </div>
            <div class="amounts-grid">
              <div v-for="s in batchData.specialties" :key="s" class="amount-cell">
                <div class="amount-cell-top">
                  <label class="amount-label" :title="s">{{ s }}</label>
                  <button class="btn-note-toggle"
                    :class="{ active: batchModal.form.notes[s] || noteFieldsOpen[s] }"
                    @click="toggleNoteField(s)">批注</button>
                </div>
                <input type="number" step="0.001"
                  :value="batchModal.form.amounts[s] ?? ''"
                  @input="setAmount(s, $event.target.value)"
                  class="amount-input" placeholder="—" />
                <textarea v-if="noteFieldsOpen[s] || batchModal.form.notes[s]"
                  v-model="batchModal.form.notes[s]"
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
            <button class="btn ghost" @click="closeBatchModal">取消</button>
            <button class="btn primary" @click="saveBatch" :disabled="modalLoading">
              {{ modalLoading ? '保存中...' : '保存批次' }}
            </button>
          </div>
        </div>
      </div>

      <!-- ── 专业管理抽屉 ── -->
      <div v-if="specialtyPanel" class="specialty-overlay" @click.self="specialtyPanel = false">
        <aside class="specialty-drawer">
          <div class="specialty-drawer-head">
            <div>
              <h3>管理专业列表</h3>
              <p>共 {{ specialtyList.length }} 个专业 · 顺序即表格列顺序</p>
            </div>
            <button class="modal-close" @click="specialtyPanel = false">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
          <div class="specialty-list">
            <div v-for="s in specialtyList" :key="s.id" class="specialty-item">
              <template v-if="editingSpecialty?.id === s.id">
                <input v-model="editingSpecialty.name" class="specialty-edit-input"
                  @keyup.enter="saveSpecialtyEdit" @keyup.escape="editingSpecialty = null" />
                <button class="btn-sm" @click="saveSpecialtyEdit">保存</button>
                <button class="btn-sm ghost" @click="editingSpecialty = null">取消</button>
              </template>
              <template v-else>
                <span class="specialty-item-name">{{ s.name }}</span>
                <div class="specialty-item-ops">
                  <button class="btn-sm ghost" @click="startEditSpecialty(s)">重命名</button>
                  <button class="btn-sm danger" @click="confirmDeleteSpecialty(s)">删除</button>
                </div>
              </template>
            </div>
          </div>
          <div class="specialty-add-row">
            <input v-model="newSpecialtyName" class="form-input specialty-add-input"
              placeholder="输入新增专业名称" @keyup.enter="addNewSpecialty" />
            <button class="btn primary" @click="addNewSpecialty" :disabled="!newSpecialtyName.trim()">添加</button>
          </div>
          <p class="specialty-footer-hint">重命名后，所有历史批次对应金额会自动更新专业名。</p>
        </aside>
      </div>

    </div><!-- /batch tab -->

    <div v-if="historyVisible" class="history-overlay" @click.self="closeHistoryPanel">
      <aside class="history-panel">
        <div class="history-panel-header">
          <div>
            <span class="panel-kicker budget-kicker">History Snapshots</span>
            <h3>预算立项历史记录</h3>
            <p>选择某次上传记录，直接恢复当时的预算分析结果。</p>
          </div>
          <button class="modal-close" @click="closeHistoryPanel">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div v-if="historyLoading" class="history-loading">
          <div class="loader-ring"></div>
          <p>正在读取历史记录...</p>
        </div>
        <div v-else-if="historyRecords.length === 0" class="history-empty">
          <p>暂无历史记录</p>
        </div>
        <div v-else class="history-list">
          <button
            v-for="(record, index) in historyRecords"
            :key="record.id"
            class="history-item"
            :class="{ active: currentRecordId === record.id }"
            @click="viewHistorySnapshot(record.id)"
          >
            <div class="history-item-top">
              <strong>{{ record.source_filename }}</strong>
              <span class="history-item-id">#{{ record.id }}</span>
            </div>
            <div class="history-item-kpis">
              <span class="history-kpi-capital">{{ formatNum(record.snapshot_data?.occupied_total || 0) }}<em>万元</em></span>
              <span class="history-kpi-progress">{{ formatBudgetHistoryProgress(record) }}</span>
              <span
                v-if="getProgressDelta(record, index) !== null"
                class="history-kpi-delta"
                :class="getProgressDelta(record, index) >= 0 ? 'delta-up' : 'delta-down'"
              >{{ getProgressDelta(record, index) >= 0 ? '↑' : '↓' }} {{ Math.abs(getProgressDelta(record, index)).toFixed(1) }}pct</span>
            </div>
            <div class="history-item-meta">
              <span>{{ formatHistoryTime(record.uploaded_at) }}</span>
            </div>
          </button>
        </div>
      </aside>
    </div>

    <div v-if="loading" class="loading">
      <div class="loader">
        <div class="loader-ring"></div>
        <div class="loader-ring"></div>
        <div class="loader-ring"></div>
      </div>
      <p>分析中...</p>
    </div>

    <!-- 单元格批注悬浮提示（fixed 定位不受 overflow:auto 裁剪） -->
    <div v-if="cellNoteVisible" class="cell-note-popup"
      :style="{ left: cellNoteX + 'px', top: cellNoteY + 'px' }">
      {{ cellNoteText }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, reactive } from 'vue'
import { uploadBudget, getBudgetHistory, getBudgetHistorySnapshot,
  getBatchData, createBatch, updateBatch, deleteBatch,
  getSpecialties, addSpecialty, updateSpecialty, deleteSpecialty } from '../api'

const props = defineProps({
  initialData: {
    type: Object,
    default: null
  },
  latestData: {
    type: Object,
    default: null
  },
  historyComparison: {
    type: Object,
    default: null
  },
  analysisDate: {
    type: String,
    default: null
  },
  snapshotLabel: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['dataUpdate', 'restoreLatest'])

const fileInput = ref(null)
const loading = ref(false)
const hasData = ref(false)
const data = ref({})
const animatedBudget = ref([0, 0, 0, 0])

function runBudgetCountUp(d) {
  if (!d?.budget_total) { animatedBudget.value = [0, 0, 0, 0]; return }
  const targets = [
    d.budget_total || 0,
    d.occupied_total || 0,
    d.annual_spend_total || 0,
    Math.max(0, (d.budget_total || 0) - (d.occupied_total || 0) - (d.preoccupied_total || 0)),
  ]
  const duration = 900
  const startTs = performance.now()
  function tick(ts) {
    const t = Math.min((ts - startTs) / duration, 1)
    const eased = 1 - Math.pow(1 - t, 3)
    animatedBudget.value = targets.map(v => v * eased)
    if (t < 1) requestAnimationFrame(tick)
    else animatedBudget.value = [...targets]
  }
  requestAnimationFrame(tick)
}
const selectedManager = ref('')
const selectedCategory = ref('')
const historyVisible = ref(false)
const historyLoading = ref(false)
const historyRecords = ref([])
const currentRecordId = ref(null)
const isViewingHistory = ref(false)
const snapshotDisplayDate = ref(null)
const localComparison = ref(null)
const categoryTableCollapsed = ref(true)
const projectTableCollapsed = ref(true)
const selectedFile = ref(null)
const showUpload = ref(false)
const selectedFileName = ref('')
const uploadMessage = ref('')
const uploadMessageType = ref('info')

// 监听父组件传来的数据
watch(() => props.initialData, (newData) => {
  if (newData) {
    applyBudgetData(newData)
    isViewingHistory.value = false
    snapshotDisplayDate.value = null
  }
}, { immediate: true })

watch(data, (d) => runBudgetCountUp(d), { immediate: true })

const displayAnalysisDate = computed(() => snapshotDisplayDate.value || props.analysisDate)
const comparisonSource = computed(() => props.historyComparison || localComparison.value)
const shouldShowHistoryCompare = computed(() => Boolean(props.historyComparison))

const viewingSnapshotLabel = computed(() => {
  if (props.snapshotLabel) return props.snapshotLabel
  if (!isViewingHistory.value) return ''
  return '当前查看：历史快照'
})

const compareOverview = computed(() => {
  if (!shouldShowHistoryCompare.value) return null
  const previous = comparisonSource.value?.data || comparisonSource.value
  if (!previous || !data.value?.budget_total) return null
  return {
    budget: {
      current: Number(data.value.budget_total || 0),
      diff: Number(data.value.budget_total || 0) - Number(previous.budget_total || 0),
    },
    progress: {
      current: Number(data.value.approval_progress || 0),
      diff: (Number(data.value.approval_progress || 0) - Number(previous.approval_progress || 0)) * 100,
    },
  }
})

const categoryProgressTop5 = computed(() => {
  if (!shouldShowHistoryCompare.value) return []
  const previous = comparisonSource.value?.data || comparisonSource.value
  const previousCategories = previous?.categories || []
  const currentCategories = data.value?.categories || []
  if (!previousCategories.length || !currentCategories.length) return []

  const previousMap = new Map(previousCategories.map(item => [item.name, Number(item.progress || 0)]))

  return currentCategories
    .map(item => ({
      name: item.name,
      currentProgress: Number(item.progress || 0),
      progressDiff: (Number(item.progress || 0) - (previousMap.get(item.name) || 0)) * 100,
    }))
    .filter(item => item.progressDiff !== 0)
    .sort((a, b) => b.progressDiff - a.progressDiff)
    .slice(0, 5)
})

const progressStatus = computed(() => {
  const p = Number(data.value.approval_progress || 0)
  if (p >= 1) return { text: '已达年度目标', badgeClass: 'safe' }
  if (p >= 0.7) return { text: '推进中', badgeClass: 'warning' }
  return { text: '进度偏低', badgeClass: 'danger' }
})

const metrics = computed(() => {
  if (!data.value.budget_total) return []
  return [
    { label: '年度预算', value: formatNum(data.value.budget_total), unit: '万元', class: 'blue' },
    { label: '年度支出', value: formatNum(data.value.annual_spend_total), unit: '万元', class: 'purple' },
    { label: '已占用', value: formatNum(data.value.occupied_total), unit: '万元', class: 'green' },
    { label: '预占用', value: formatNum(data.value.preoccupied_total), unit: '万元', class: 'orange' },
    { label: '立项进度', value: formatPercent(data.value.approval_progress), unit: '', class: progressBadgeClass.value, badgeText: progressStatus.value.text, badgeClass: progressStatus.value.badgeClass },
  ]
})

const progressBadgeClass = computed(() => {
  const p = data.value.approval_progress || 0
  if (p >= 1) return 'success'
  if (p >= 0.5) return 'warning'
  return 'danger'
})

const progressText = computed(() => {
  const p = data.value.approval_progress || 0
  return `立项 ${(p * 100).toFixed(1)}%`
})

const recentHistoryCards = computed(() => historyRecords.value.slice(0, 4))
const canUploadNow = computed(() => Boolean(selectedFile.value))

const managerOptions = computed(() => {
  const values = new Set((data.value.projects || []).map(project => project.manager).filter(Boolean))
  return Array.from(values).sort((a, b) => a.localeCompare(b, 'zh-CN'))
})

const categoryOptions = computed(() => {
  const values = new Set((data.value.projects || []).map(project => project.category).filter(Boolean))
  return Array.from(values).sort((a, b) => a.localeCompare(b, 'zh-CN'))
})

const filteredProjects = computed(() => {
  return (data.value.projects || []).filter(project => {
    const matchManager = !selectedManager.value || project.manager === selectedManager.value
    const matchCategory = !selectedCategory.value || project.category === selectedCategory.value
    return matchManager && matchCategory
  })
})

function formatNum(num) {
  return Number(num || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatPercent(value) {
  return (value * 100).toFixed(1) + '%'
}

function formatDelta(value, unit = '') {
  const numeric = Number(value || 0)
  const sign = numeric > 0 ? '+' : ''
  if (unit === 'pct') return `${sign}${numeric.toFixed(1)} pct`
  return `${sign}${numeric.toFixed(2)} ${unit}`.trim()
}

function formatHistoryTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatHistoryDateOnly(value) {
  if (!value) return '-'
  return new Date(value).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).replace(/\//g, '-')
}

function getProgressDelta(record, index) {
  const prev = historyRecords.value[index + 1]
  if (!prev) return null
  const curr = Number(record?.snapshot_data?.approval_progress || 0)
  const prevProgress = Number(prev?.snapshot_data?.approval_progress || 0)
  return (curr - prevProgress) * 100
}

function formatBudgetHistoryProgress(record) {
  const progress = Number(record?.snapshot_data?.approval_progress || 0)
  return `${(progress * 100).toFixed(1)}%`
}

function applyBudgetData(nextData) {
  data.value = nextData || {}
  hasData.value = Boolean(nextData)
}

function triggerFileInput() {
  fileInput.value?.click()
}

async function handleFileChange(e) {
  const file = e.target.files?.[0]
  if (file) {
    selectedFile.value = file
    selectedFileName.value = file.name
    uploadMessage.value = `已选择文件：${file.name}`
    uploadMessageType.value = 'info'
    await processFile(file)
  }
}

async function handleDrop(e) {
  const file = e.dataTransfer.files?.[0]
  if (file) {
    selectedFile.value = file
    selectedFileName.value = file.name
    uploadMessage.value = `已选择文件：${file.name}`
    uploadMessageType.value = 'info'
    await processFile(file)
  }
}

async function processSelectedFile() {
  if (!selectedFile.value) return
  await processFile(selectedFile.value)
}

function clearSelectedFile() {
  selectedFile.value = null
  selectedFileName.value = ''
  uploadMessage.value = ''
  if (fileInput.value) fileInput.value.value = ''
}

async function processFile(file) {
  loading.value = true
  try {
    const result = await uploadBudget(file)
    if (result.success) {
      applyBudgetData(result.data)
      isViewingHistory.value = false
      snapshotDisplayDate.value = null
      currentRecordId.value = null
      localComparison.value = null
      clearSelectedFile()
      showUpload.value = false
      emit('dataUpdate', result.data)
    }
  } catch (error) {
    uploadMessage.value = '分析失败：' + (error.message || '未知错误')
    uploadMessageType.value = 'error'
  } finally {
    loading.value = false
  }
}

async function loadHistoryList() {
  historyLoading.value = true
  try {
    const result = await getBudgetHistory(30)
    if (result.success) {
      const records = result.data || []
      const enriched = await Promise.all(records.map(async (record, index) => {
        if (index > 3) return record
        try {
          const snapshotResult = await getBudgetHistorySnapshot(record.id)
          if (snapshotResult.success && snapshotResult.data?.current?.data) {
            return {
              ...record,
              snapshot_data: snapshotResult.data.current.data,
            }
          }
        } catch (error) {
          console.error('获取预算历史快照摘要失败:', error)
        }
        return record
      }))
      historyRecords.value = enriched
    }
  } catch (error) {
    console.error('获取预算历史列表失败:', error)
    historyRecords.value = []
  } finally {
    historyLoading.value = false
  }
}

async function openHistoryPanel() {
  historyVisible.value = true
  if (!historyRecords.value.length) {
    await loadHistoryList()
  }
}

function closeHistoryPanel() {
  historyVisible.value = false
}

async function viewHistorySnapshot(recordId) {
  historyLoading.value = true
  try {
    const result = await getBudgetHistorySnapshot(recordId)
    if (result.success && result.data?.current) {
      applyBudgetData(result.data.current.data)
      currentRecordId.value = result.data.current.id
      isViewingHistory.value = true
      snapshotDisplayDate.value = formatHistoryTime(result.data.current.uploaded_at)
      localComparison.value = result.data.previous
      closeHistoryPanel()
    }
  } catch (error) {
    console.error('获取预算历史快照失败:', error)
    alert('读取历史快照失败，请稍后重试')
  } finally {
    historyLoading.value = false
  }
}

function clearData() {
  if (!window.confirm('确认重新上传？当前分析数据将被清除。')) return
  hasData.value = false
  data.value = {}
  selectedManager.value = ''
  selectedCategory.value = ''
  currentRecordId.value = null
  isViewingHistory.value = false
  snapshotDisplayDate.value = null
  localComparison.value = null
  if (fileInput.value) fileInput.value.value = ''
  clearSelectedFile()
  // 通知父组件清除数据
  emit('dataUpdate', null)
}

function restoreLatestView() {
  const latest = props.latestData || props.initialData
  if (!latest) return
  applyBudgetData(latest)
  isViewingHistory.value = false
  snapshotDisplayDate.value = null
  localComparison.value = null
  emit('restoreLatest')
}

onMounted(() => {
  if (!historyRecords.value.length) {
    loadHistoryList()
  }
})

// ══════════════════════════════════════════════════════════════════
// 批次下达 Tab
// ══════════════════════════════════════════════════════════════════

const batchTab = ref('budget')
const batchData = ref({ specialties: [], batches: [], totals: {} })
const batchLoading = ref(false)

const batchModal = ref({
  visible: false, mode: 'create', editId: null,
  form: { batch_date: '', note: '', amounts: {}, notes: {} }
})
const noteFieldsOpen = reactive({})
const cellNoteVisible = ref(false)
const cellNoteText = ref('')
const cellNoteX = ref(0)
const cellNoteY = ref(0)
const modalLoading = ref(false)

const specialtyPanel = ref(false)
const specialtyList = ref([])
const newSpecialtyName = ref('')
const editingSpecialty = ref(null)

const grandTotal = computed(() =>
  Object.values(batchData.value.totals).reduce((s, v) => s + (v || 0), 0)
)
const modalSubtotal = computed(() =>
  Object.values(batchModal.value.form.amounts).reduce((s, v) => s + (parseFloat(v) || 0), 0)
)

function batchSubtotal(batch) {
  return Object.values(batch.amounts).reduce((s, v) => s + (v || 0), 0)
}

function formatBatchNum(v) {
  if (v === null || v === undefined || v === 0) return '—'
  return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function switchToBatchTab() {
  batchTab.value = 'batch'
  if (!batchData.value.batches.length && !batchLoading.value) {
    await loadBatchData()
  }
}

async function loadBatchData() {
  batchLoading.value = true
  try {
    batchData.value = await getBatchData()
  } catch (e) {
    console.error('加载批次数据失败', e)
  } finally {
    batchLoading.value = false
  }
}

function openCreateModal() {
  const amounts = {}
  batchData.value.specialties.forEach(s => { amounts[s] = null })
  Object.keys(noteFieldsOpen).forEach(k => delete noteFieldsOpen[k])
  batchModal.value = {
    visible: true, mode: 'create', editId: null,
    form: { batch_date: new Date().toISOString().slice(0, 10), note: '', amounts, notes: {} }
  }
}

function openEditModal(batch) {
  const amounts = {}
  const notes = {}
  batchData.value.specialties.forEach(s => {
    amounts[s] = batch.amounts[s] ?? null
    notes[s] = batch.notes?.[s] ?? ''
  })
  Object.keys(noteFieldsOpen).forEach(k => delete noteFieldsOpen[k])
  Object.entries(notes).forEach(([s, v]) => { if (v) noteFieldsOpen[s] = true })
  batchModal.value = {
    visible: true, mode: 'edit', editId: batch.id,
    form: { batch_date: batch.batch_date, note: batch.note, amounts, notes }
  }
}

function closeBatchModal() { batchModal.value.visible = false }

function setAmount(specialty, value) {
  batchModal.value.form.amounts[specialty] = value === '' ? null : parseFloat(value)
}

function toggleNoteField(s) {
  noteFieldsOpen[s] = !noteFieldsOpen[s]
}

function showCellNote(event, text) {
  const rect = event.currentTarget.getBoundingClientRect()
  cellNoteText.value = text
  cellNoteX.value = rect.left
  cellNoteY.value = rect.bottom + 6
  cellNoteVisible.value = true
}

function hideCellNote() {
  cellNoteVisible.value = false
}

async function saveBatch() {
  const { mode, editId, form } = batchModal.value
  if (!form.batch_date) { alert('请填写批次日期'); return }
  modalLoading.value = true
  try {
    const payload = {
      batch_date: form.batch_date,
      note: form.note,
      amounts: Object.fromEntries(
        Object.entries(form.amounts).filter(([, v]) => v !== null && v !== '' && !isNaN(v))
      ),
      notes: Object.fromEntries(
        Object.entries(form.notes || {}).filter(([, v]) => v?.trim())
      )
    }
    if (mode === 'create') await createBatch(payload)
    else await updateBatch(editId, payload)
    closeBatchModal()
    await loadBatchData()
  } catch (e) {
    alert('保存失败：' + (e.response?.data?.detail || e.message))
  } finally {
    modalLoading.value = false
  }
}

async function confirmDeleteBatch(batch) {
  if (!confirm(`确认删除 ${batch.batch_date} 这条批次记录？`)) return
  try {
    await deleteBatch(batch.id)
    await loadBatchData()
  } catch (e) { alert('删除失败：' + e.message) }
}

async function openSpecialtyPanel() {
  specialtyPanel.value = true
  specialtyList.value = await getSpecialties()
}

async function addNewSpecialty() {
  const name = newSpecialtyName.value.trim()
  if (!name) return
  try {
    await addSpecialty(name)
    newSpecialtyName.value = ''
    specialtyList.value = await getSpecialties()
    await loadBatchData()
  } catch (e) { alert('添加失败：' + (e.response?.data?.detail || e.message)) }
}

function startEditSpecialty(s) { editingSpecialty.value = { id: s.id, name: s.name } }

async function saveSpecialtyEdit() {
  if (!editingSpecialty.value) return
  try {
    await updateSpecialty(editingSpecialty.value.id, { name: editingSpecialty.value.name })
    editingSpecialty.value = null
    specialtyList.value = await getSpecialties()
    await loadBatchData()
  } catch (e) { alert('重命名失败：' + (e.response?.data?.detail || e.message)) }
}

async function confirmDeleteSpecialty(s) {
  if (!confirm(`确认删除专业「${s.name}」？已有批次中该专业的金额数据不受影响。`)) return
  try {
    await deleteSpecialty(s.id)
    specialtyList.value = await getSpecialties()
    await loadBatchData()
  } catch (e) { alert('删除失败：' + e.message) }
}
</script>

<style scoped>
.dashboard {
  max-width: 1440px;
  margin: 0 auto;
}
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
.overlay-divider { height: 1px; background: var(--line); margin: 16px 0; }
.drawer-close {
  background: none; border: none; cursor: pointer;
  color: var(--ink-3); font-size: 16px; padding: 2px 6px; border-radius: var(--r-sm);
}
.drawer-close:hover { background: var(--surface-2); color: var(--ink); }

/* ===== 上传区域 ===== */
.upload-section {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 200px);
  padding: 40px 0;
}

.upload-container {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
}

.upload-glow {
  position: absolute;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(123, 92, 255, 0.08) 0%, transparent 70%);
  pointer-events: none;
  animation: glow-pulse 4s ease-in-out infinite;
}

@keyframes glow-pulse {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.1); }
}

.upload-box {
  position: relative;
  width: 440px;
  padding: 48px 40px;
  background: linear-gradient(135deg, rgba(12, 20, 40, 0.9) 0%, rgba(10, 16, 32, 0.95) 100%);
  border: 1px solid rgba(123, 92, 255, 0.2);
  border-radius: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.upload-box::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(123, 92, 255, 0.03) 0%, transparent 50%);
  opacity: 0;
  transition: opacity 0.3s;
}

.upload-box:hover {
  border-color: rgba(123, 92, 255, 0.5);
  transform: translateY(-4px);
  box-shadow: 0 20px 60px rgba(123, 92, 255, 0.15);
}

.upload-box:hover::before {
  opacity: 1;
}

.upload-icon-wrap {
  position: relative;
  width: 80px;
  height: 80px;
  margin: 0 auto 24px;
}

.upload-icon {
  width: 80px;
  height: 80px;
  color: rgba(123, 92, 255, 0.6);
  transition: all 0.3s;
}

.upload-box:hover .upload-icon {
  color: #7b5cff;
  filter: drop-shadow(0 0 20px rgba(123, 92, 255, 0.5));
}

.upload-ring {
  position: absolute;
  inset: -8px;
  border: 2px dashed rgba(123, 92, 255, 0.3);
  border-radius: 50%;
  animation: rotate 20s linear infinite;
}

@keyframes rotate {
  to { transform: rotate(360deg); }
}

.upload-box h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.upload-hint {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 20px;
}

.upload-hint .link {
  color: #7b5cff;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.file-types {
  display: flex;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

.file-tag {
  padding: 4px 12px;
  background: rgba(123, 92, 255, 0.1);
  border: 1px solid rgba(123, 92, 255, 0.2);
  border-radius: 20px;
  font-size: 11px;
  color: #7b5cff;
  font-weight: 500;
}

/* ===== 数据展示 ===== */
.data-section {
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.section-header {
  margin-bottom: 28px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title h2 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.date-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: rgba(123, 92, 255, 0.08);
  border: 1px solid rgba(123, 92, 255, 0.2);
  border-radius: 20px;
  font-size: 13px;
  color: var(--text-secondary);
}

.date-badge svg {
  width: 14px;
  height: 14px;
}

.metrics-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.metric-card {
  position: relative;
  background: linear-gradient(135deg, rgba(12, 20, 40, 0.9) 0%, rgba(10, 16, 32, 0.95) 100%);
  border: 1px solid rgba(123, 92, 255, 0.15);
  border-radius: 16px;
  padding: 24px 20px;
  text-align: center;
  overflow: hidden;
  animation: slideUp 0.6s ease both;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}

.metric-glow {
  position: absolute;
  bottom: -50%;
  left: 50%;
  transform: translateX(-50%);
  width: 150px;
  height: 100px;
  border-radius: 50%;
  filter: blur(30px);
  opacity: 0.3;
  pointer-events: none;
}

.metric-glow.blue { background: #00d4ff; }
.metric-glow.purple { background: #7b5cff; }
.metric-glow.orange { background: #ff9500; }
.metric-glow.green { background: #00ff88; }
.metric-glow.success { background: #00ff88; }
.metric-glow.warning { background: #ff9500; }
.metric-glow.danger { background: #ff4444; }

.metric-label {
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 12px;
  position: relative;
}

.metric-value {
  font-size: 28px;
  font-weight: 700;
  font-family: 'Orbitron', monospace;
  color: var(--text-primary);
  margin-bottom: 4px;
  position: relative;
}

.metric-value.blue { color: #00d4ff; }
.metric-value.purple { color: #7b5cff; }
.metric-value.orange { color: #ff9500; }
.metric-value.green { color: #00ff88; }
.metric-value.success { color: #00ff88; }
.metric-value.warning { color: #ff9500; }
.metric-value.danger { color: #ff4444; }

.metric-unit {
  font-size: 12px;
  color: var(--text-dim);
  position: relative;
}

/* ===== 表格 ===== */
.table-card {
  background: linear-gradient(135deg, rgba(12, 20, 40, 0.9) 0%, rgba(10, 16, 32, 0.95) 100%);
  border: 1px solid rgba(123, 92, 255, 0.15);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.card-header-main {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.card-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.card-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.card-badge.success { background: rgba(0, 255, 136, 0.15); color: #00ff88; }
.card-badge.warning { background: rgba(255, 149, 0, 0.15); color: #ff9500; }
.card-badge.danger { background: rgba(255, 68, 68, 0.15); color: #ff4444; }

.record-count {
  font-size: 12px;
  color: var(--text-dim);
}

.header-tools {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.collapse-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 34px;
  padding: 0 12px;
  border-radius: 10px;
  border: 1px solid rgba(123, 92, 255, 0.18);
  background: rgba(123, 92, 255, 0.08);
  color: var(--text-primary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: 0.2s ease;
}

.collapse-toggle:hover {
  background: rgba(123, 92, 255, 0.14);
}

.collapse-toggle svg {
  width: 14px;
  height: 14px;
  transition: transform 0.2s ease;
}

.collapse-toggle svg.collapsed {
  transform: rotate(-90deg);
}

.filters-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-select {
  min-width: 140px;
  height: 36px;
  padding: 0 12px;
  border-radius: 10px;
  border: 1px solid rgba(123, 92, 255, 0.18);
  background: rgba(123, 92, 255, 0.08);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
}

.filter-select:focus {
  border-color: rgba(123, 92, 255, 0.4);
  box-shadow: 0 0 0 3px rgba(123, 92, 255, 0.12);
}

.table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 800px;
}

.data-table th {
  text-align: left;
  padding: 14px 16px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border-bottom: 1px solid rgba(123, 92, 255, 0.1);
}

.data-table td {
  padding: 16px;
  font-size: 14px;
  color: var(--text-primary);
  border-bottom: 1px solid rgba(123, 92, 255, 0.05);
}

.data-table tr {
  transition: background 0.2s;
}

.data-table tbody tr:hover {
  background: rgba(123, 92, 255, 0.03);
}

.category-name {
  font-weight: 600;
}

.subtotal {
  font-weight: 500;
}

.code {
  font-family: monospace;
  font-size: 12px;
  color: var(--text-secondary);
}

.project-name {
  max-width: 350px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.value-highlight { color: #00ff88; font-weight: 600; }
.value-warning { color: #ff9500; font-weight: 600; }

.total-row {
  background: rgba(123, 92, 255, 0.08);
}

.total-row td {
  font-weight: 600;
  color: #7b5cff;
}

.total-value {
  color: #7b5cff !important;
}

.progress-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: rgba(123, 92, 255, 0.15);
  border-radius: 4px;
  overflow: hidden;
  min-width: 60px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #7b5cff, #00d4ff);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.progress-fill.spend {
  background: linear-gradient(90deg, #ff9500, #7b5cff);
}

.progress-fill.complete {
  background: linear-gradient(90deg, #00ff88, #00d4ff);
}

.progress-text {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  min-width: 45px;
}

/* ===== 重新上传 ===== */
.reupload {
  text-align: center;
  padding: 20px;
}

.reupload button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 28px;
  background: transparent;
  border: 1px solid rgba(123, 92, 255, 0.3);
  color: #7b5cff;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.reupload button svg {
  width: 18px;
  height: 18px;
}

.reupload button:hover {
  background: rgba(123, 92, 255, 0.1);
  border-color: #7b5cff;
  box-shadow: 0 0 20px rgba(123, 92, 255, 0.2);
}

/* ===== 加载状态 ===== */
.loading {
  position: fixed;
  inset: 0;
  background: rgba(5, 8, 16, 0.95);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(10px);
}

.loader {
  position: relative;
  width: 80px;
  height: 80px;
}

.loader-ring {
  position: absolute;
  inset: 0;
  border: 3px solid transparent;
  border-top-color: #7b5cff;
  border-radius: 50%;
  animation: spin 1.2s linear infinite;
}

.loader-ring:nth-child(2) {
  inset: 8px;
  border-top-color: #00d4ff;
  animation-delay: 0.15s;
  animation-direction: reverse;
}

.loader-ring:nth-child(3) {
  inset: 16px;
  border-top-color: #00ff88;
  animation-delay: 0.3s;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading p {
  margin-top: 24px;
  font-size: 14px;
  color: var(--text-secondary);
  letter-spacing: 0.05em;
}

/* ===== 响应式 ===== */
@media (max-width: 900px) {
  .metrics-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .card-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .header-tools {
    width: 100%;
    justify-content: space-between;
  }
}

@media (max-width: 600px) {
  .metrics-row {
    grid-template-columns: 1fr;
  }

  .upload-box {
    width: 100%;
    max-width: 360px;
  }
}
.panel-kicker {
  display: inline-block;
  margin-bottom: 10px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--accent-cyan);
}

.budget-kicker {
  color: #8ea7ff;
}

.upload-shell {
  width: 100%;
}

.upload-container {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 420px);
  gap: 28px;
  align-items: stretch;
}

.upload-copy,
.upload-box,
.section-header-rich,
.metric-card,
.table-card {
  box-shadow: 0 28px 70px rgba(0, 0, 0, 0.22);
}

.upload-copy {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 38px;
  background: linear-gradient(180deg, rgba(10, 18, 35, 0.9), rgba(11, 18, 35, 0.72));
  border: 1px solid rgba(142, 167, 255, 0.14);
  border-radius: 30px;
}

.upload-copy-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.upload-copy p {
  max-width: 54ch;
  margin-bottom: 20px;
  font-size: 14px;
  line-height: 1.72;
  color: var(--text-secondary);
}

.upload-facts {
  display: grid;
  gap: 14px;
  margin-top: auto;
}

.fact-card {
  padding: 16px 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.fact-card span {
  display: block;
  margin-bottom: 8px;
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.fact-card strong {
  font-size: 15px;
  color: var(--text-primary);
}

.upload-box {
  width: 100%;
  min-height: 100%;
  border-radius: 30px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 42px 34px;
}

.upload-glow {
  inset: auto;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.section-header-rich {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  padding: 28px 30px;
  margin-bottom: 24px;
  background: linear-gradient(180deg, rgba(8, 16, 31, 0.9), rgba(8, 16, 31, 0.68));
  border: 1px solid rgba(142, 167, 255, 0.14);
  border-radius: 28px;
}

.page-title-rich {
  display: block;
}

.header-main {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.page-title-rich h2 {
  margin-bottom: 10px;
  font-size: 32px;
}

.page-title-rich p {
  max-width: 64ch;
  line-height: 1.75;
  color: var(--text-secondary);
}

.header-side {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.history-action {
  position: relative;
  z-index: 1;
}

.snapshot-badge {
  display: inline-flex;
  align-items: center;
  height: 36px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid rgba(142, 167, 255, 0.22);
  background: rgba(142, 167, 255, 0.12);
  color: #dbe4ff;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.ghost-action {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 42px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid rgba(142, 167, 255, 0.22);
  background: rgba(142, 167, 255, 0.08);
  color: var(--text-primary);
  cursor: pointer;
  transition: 0.25s ease;
}

.ghost-action:hover {
  background: rgba(142, 167, 255, 0.14);
}

.ghost-action svg {
  width: 16px;
  height: 16px;
}

.compare-section {
  margin-bottom: 22px;
  padding: 24px;
  border-radius: 28px;
  border: 1px solid rgba(142, 167, 255, 0.1);
  background: linear-gradient(180deg, rgba(8, 16, 31, 0.86), rgba(8, 16, 31, 0.68));
  box-shadow: 0 28px 70px rgba(0, 0, 0, 0.22);
}

.compare-header,
.compare-subheader {
  margin-bottom: 16px;
}

.compare-caption {
  color: var(--text-secondary);
  font-size: 12px;
}

.compare-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 18px;
}

.compare-card {
  display: grid;
  gap: 8px;
  padding: 18px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.compare-label {
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.compare-card strong {
  font-size: 24px;
  color: var(--text-primary);
}

.compare-detail {
  color: var(--text-secondary);
  font-size: 13px;
}

.delta-up {
  color: #8cf0c9;
}

.delta-down {
  color: #ff9d87;
}

.compare-empty {
  text-align: center;
  color: var(--text-secondary);
}

.history-overlay {
  position: fixed;
  inset: 0;
  z-index: 980;
  display: flex;
  justify-content: flex-end;
  background: rgba(4, 10, 20, 0.62);
  backdrop-filter: blur(6px);
}

.history-panel {
  width: min(520px, 100%);
  height: 100%;
  padding: 28px 24px;
  background: linear-gradient(180deg, rgba(8, 15, 30, 0.96), rgba(10, 17, 34, 0.98));
  border-left: 1px solid rgba(142, 167, 255, 0.14);
  box-shadow: -24px 0 70px rgba(0, 0, 0, 0.35);
  overflow-y: auto;
}

.history-panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.history-panel-header h3 {
  margin: 8px 0 10px;
  font-size: 24px;
  color: var(--text-primary);
}

.history-panel-header p {
  color: var(--text-secondary);
  line-height: 1.7;
  font-size: 14px;
}

.history-loading,
.history-empty {
  min-height: 220px;
  display: grid;
  place-items: center;
  color: var(--text-secondary);
  text-align: center;
}

.history-list {
  display: grid;
  gap: 12px;
}

.history-item {
  width: 100%;
  padding: 18px;
  border-radius: 20px;
  border: 1px solid rgba(142, 167, 255, 0.1);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
  transition: 0.22s ease;
}

.history-item:hover,
.history-item.active {
  border-color: rgba(142, 167, 255, 0.28);
  background: rgba(142, 167, 255, 0.08);
  transform: translateY(-2px);
}

.history-item-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.history-item-top strong {
  flex: 1;
  font-size: 14px;
  line-height: 1.6;
}

.history-item-id {
  flex-shrink: 0;
  color: var(--text-muted);
  font-size: 12px;
}

.history-item-kpis {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.history-kpi-capital {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: baseline;
  gap: 3px;
}

.history-kpi-capital em {
  font-size: 11px;
  font-style: normal;
  font-weight: 400;
  color: var(--text-secondary);
}

.history-kpi-progress {
  font-size: 12px;
  color: #a78bfa;
  background: rgba(167, 139, 250, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
}

.history-kpi-delta {
  font-size: 12px;
  font-weight: 500;
}

.history-kpi-delta.delta-up { color: #34d399; }
.history-kpi-delta.delta-down { color: #f87171; }

.history-item-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  color: var(--text-secondary);
  font-size: 12px;
}

.modal-close {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.modal-close:hover {
  background: rgba(255, 126, 112, 0.16);
  border-color: rgba(255, 126, 112, 0.28);
  color: #ffb3aa;
}

.metrics-row {
  gap: 18px;
  margin-bottom: 20px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.metric-card {
  text-align: left;
  border-radius: 24px;
  padding: 24px 22px;
}

.metric-label {
  margin-bottom: 18px;
}

.metric-value {
  margin-bottom: 8px;
}

.metric-value-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.metric-value-unit {
  font-size: 12px;
  color: var(--text-dim);
}

.metric-meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 24px;
}

.metric-inline-note {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 600;
}

.metric-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
}

.metric-badge.warning {
  background: rgba(255, 149, 0, 0.16);
  color: #ff9500;
}

.metric-badge.danger {
  background: rgba(255, 68, 68, 0.16);
  color: #ff6666;
}

.metric-badge.safe {
  background: rgba(0, 255, 136, 0.14);
  color: #00cc88;
}

.table-card {
  border-radius: 28px;
  border-color: rgba(142, 167, 255, 0.1);
}

@media (max-width: 1180px) {
  .upload-container {
    grid-template-columns: 1fr;
  }

  .section-header-rich {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-side {
    justify-content: flex-start;
  }

  .upload-copy-top {
    align-items: flex-start;
    flex-direction: column;
  }

  .compare-cards {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .upload-copy,
  .upload-box,
  .section-header-rich,
  .metric-card,
  .table-card {
    border-radius: 24px;
  }

  .upload-copy,
  .upload-box {
    padding: 26px 22px;
  }

  .page-title-rich h2 {
    font-size: 26px;
  }

  .history-panel {
    width: 100%;
    padding: 24px 18px;
  }
}

/* ===== Analyst UI Override (Light, compact) ===== */
.dashboard {
  background: #f6f5f2;
  color: #1c1b18;
  border-radius: 12px;
  padding: 10px 12px;
}

.upload-shell,
.data-section {
  max-width: 1160px;
  margin: 0 auto;
}

.data-section {
  display: grid;
  gap: 10px;
}

.upload-copy,
.upload-box,
.table-card,
.compare-section {
  background: #ffffff !important;
  border: 1px solid #e4e3dc !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}

.upload-copy,
.upload-box {
  padding: 18px !important;
}

.upload-copy,
.upload-box,
.history-panel,
.history-item,
.fact-card {
  color: #1c1b18 !important;
}

.panel-kicker,
.upload-copy p,
.metric-label,
.metric-unit,
.date-badge,
.record-count {
  color: #6b6a63 !important;
}

.upload-box h2,
.history-panel-header h3,
.history-item-top strong,
.fact-card strong,
.history-item-id {
  color: #1c1b18 !important;
}

.upload-copy p,
.upload-hint,
.history-panel-header p,
.history-item-meta,
.fact-card span {
  color: #6b6a63 !important;
}

.history-kpi-capital {
  color: #1c1b18 !important;
}

.history-kpi-capital em {
  color: #6b6a63 !important;
}

.history-kpi-progress {
  background: #f0eeff !important;
  color: #5b21b6 !important;
}

.history-kpi-delta.delta-up { color: #15803d !important; }
.history-kpi-delta.delta-down { color: #b91c1c !important; }

.file-tag,
.panel-kicker,
.upload-hint .link {
  color: #1a56a4 !important;
}

.file-tag {
  background: #eef3fb !important;
  border-color: #d9e4f4 !important;
}

.fact-card {
  background: #f8f6f1 !important;
  border-color: #e5e0d6 !important;
}

.section-header-rich {
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  padding: 0 !important;
  margin-bottom: 4px !important;
  box-shadow: none !important;
}

.page-title-rich h2 {
  font-size: 18px !important;
  color: #1c1b18 !important;
  margin: 0 !important;
}

.page-title-rich p {
  font-size: 12px !important;
  color: #6b6a63 !important;
}

.header-main {
  gap: 10px !important;
}

.metrics-row {
  gap: 12px !important;
  margin-bottom: 0 !important;
}

.metric-card {
  background: #fff !important;
  border: 1px solid #e4e3dc !important;
  border-radius: 18px !important;
  padding: 16px 18px 14px !important;
  min-height: 138px !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: flex-start !important;
  justify-content: flex-start !important;
  text-align: left !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8) !important;
}

.metric-card > .metric-label,
.metric-card > .metric-value-row,
.metric-card > .metric-meta-row {
  width: 100% !important;
  text-align: left !important;
}

.metric-value {
  font-size: 24px !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-weight: 700 !important;
  letter-spacing: -0.04em !important;
  line-height: 1.02 !important;
  margin: 10px 0 6px !important;
}

.metric-label {
  font-size: 12px !important;
  font-weight: 600 !important;
  color: #8a867f !important;
  margin-bottom: 0 !important;
  letter-spacing: 0 !important;
  text-transform: none !important;
  text-align: left !important;
}

.metric-value-row {
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 6px !important;
  width: 100% !important;
}

.metric-value-unit {
  font-size: 11px !important;
  color: #8a867f !important;
  line-height: 1 !important;
  white-space: nowrap !important;
}

.metric-meta-row {
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 6px !important;
  min-height: 20px !important;
  margin-top: 4px !important;
  flex-wrap: wrap !important;
  width: 100% !important;
  text-align: left !important;
}

.metric-inline-note {
  color: #8a867f !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  line-height: 1 !important;
  white-space: nowrap !important;
}

.metric-badge {
  border-radius: 12px !important;
  padding: 4px 9px !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  line-height: 1 !important;
  white-space: nowrap !important;
}

.metric-badge.warning {
  background: #f7e6d1 !important;
  color: #b85a08 !important;
}

.metric-badge.danger {
  background: #f4d9da !important;
  color: #c43131 !important;
}

.metric-badge.safe {
  background: #ddf4e7 !important;
  color: #047857 !important;
}

.metric-value.blue {
  color: #245db0 !important;
}

.metric-value.purple {
  color: #6a39d7 !important;
}

.metric-value.green {
  color: #047857 !important;
}

.metric-value.orange {
  color: #bb5a08 !important;
}

.metric-value.red,
.metric-value.success,
.metric-value.warning,
.metric-value.danger {
  color: #c43131 !important;
}

.metric-glow {
  display: none !important;
}

.ghost-action {
  height: 32px !important;
  padding: 0 14px !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
  font-size: 13px !important;
}

.ghost-action.--history {
  background: #fff !important;
  border: 1px solid #d8d5cc !important;
  color: #5f5b53 !important;
}

.ghost-action.--history:hover {
  background: #f0efe9 !important;
  color: #1c1b18 !important;
}

.ghost-action.--restore {
  background: #eff4ff !important;
  border: 1px solid #b8cef5 !important;
  color: #2563eb !important;
}

.ghost-action.--restore:hover {
  background: #deeaff !important;
  border-color: #93b8f0 !important;
}

.ghost-action.--danger {
  background: #fff !important;
  border: 1px solid #f0b8b8 !important;
  color: #c0392b !important;
}

.ghost-action.--danger:hover {
  background: #fff5f5 !important;
  border-color: #e07070 !important;
  color: #a02020 !important;
}

.snapshot-badge {
  height: 32px !important;
  padding: 0 12px !important;
  border-radius: 999px !important;
  border: none !important;
  background: #e7f0ff !important;
  color: #1a56a4 !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  letter-spacing: 0 !important;
}

.date-badge {
  height: 32px !important;
  padding: 0 12px !important;
  background: #f1eee8 !important;
  border: 1px solid #e4e0d6 !important;
  border-radius: 999px !important;
  color: #6b6a63 !important;
  font-size: 12px !important;
}


.progress-overview-card {
  background: #fff;
  border: 1px solid #e4e3dc;
  border-radius: 10px;
  overflow: hidden;
}

.progress-row-inner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
}

.progress-inner-divider {
  height: 1px;
  background: #f0efe9;
  margin: 0 14px;
}

.progress-row {
  background: #fff;
  border: 1px solid #e4e3dc;
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-label {
  font-size: 12px;
  font-weight: 600;
  color: #1c1b18;
  min-width: 132px;
}

.progress-track-wrap {
  flex: 1;
}

.progress-nums-row {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #6b6a63;
  margin-bottom: 4px;
}

.progress-nums-row .pct {
  color: #1a56a4;
  font-weight: 700;
  font-family: 'IBM Plex Mono', monospace;
}

.progress-nums-row .pct.spend {
  color: #b85a08;
}

.progress-track {
  height: 6px;
  background: #f0efe9;
  border: 1px solid #e4e3dc;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #1a56a4 !important;
  border-radius: 4px;
}

.progress-right {
  min-width: 120px;
  display: grid;
  gap: 2px;
  text-align: right;
}

.progress-completed {
  font-size: 11px;
  color: #a8a79f;
}

.progress-remaining {
  font-size: 12px;
  font-weight: 700;
  color: #b45309;
  font-family: 'IBM Plex Mono', monospace;
}

.card-header h3 {
  color: #1c1b18 !important;
  font-size: 13px !important;
}

.table-wrapper {
  background: #fff !important;
}

.table-footnote {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 12px;
  border-top: 1px solid #e4e3dc;
  font-size: 11px;
  color: #6b6a63;
}

.data-table thead th {
  background: #f0efe9 !important;
  color: #6b6a63 !important;
  font-size: 11px !important;
  padding: 10px 12px !important;
  border-bottom: 1px solid #e4e3dc !important;
}

.data-table tbody td {
  color: #1c1b18 !important;
  border-bottom: 1px solid #f0efe9 !important;
  font-size: 12px !important;
  padding: 10px 12px !important;
  line-height: 1.2 !important;
}

.table-card {
  padding: 14px 16px !important;
  margin-bottom: 0 !important;
}

.card-header {
  margin-bottom: 10px !important;
}

.card-header-main {
  gap: 8px !important;
}

.header-tools {
  gap: 10px !important;
}

.header-tools-collapsible {
  justify-content: flex-end !important;
}

.filters-row {
  gap: 8px !important;
}

.filter-select {
  min-height: 34px !important;
  padding: 0 10px !important;
}

.collapse-toggle {
  background: #f0efe9 !important;
  border: 1px solid #d0cfc6 !important;
  color: #5f5b53 !important;
  border-radius: 6px !important;
  height: 26px !important;
  padding: 0 10px !important;
  font-size: 12px !important;
  font-weight: 500 !important;
}

.collapse-toggle:hover {
  background: #e6e4dd !important;
  border-color: #b8b6ae !important;
  color: #1c1b18 !important;
}

.progress-cell {
  gap: 8px !important;
}

.table-card .progress-cell {
  gap: 10px !important;
}

.table-card .progress-bar {
  height: 10px !important;
  background: #e8e4dc !important;
  border: 1px solid #ddd8cd !important;
  border-radius: 999px !important;
  overflow: hidden !important;
  min-width: 72px !important;
}

.table-card .progress-fill {
  background: linear-gradient(90deg, #245db0, #5f8fdd) !important;
  border-radius: 999px !important;
}

.table-card .progress-fill.spend {
  background: linear-gradient(90deg, #b85a08, #e29b47) !important;
}

.table-card .progress-fill.complete {
  background: linear-gradient(90deg, #047857, #32a37e) !important;
}

.table-card .progress-text {
  font-size: 11px !important;
  font-weight: 700 !important;
  color: #4f4a43 !important;
  min-width: 52px !important;
  text-align: right !important;
}

.table-card .total-row .progress-text {
  color: #1c1b18 !important;
}

.card-badge {
  padding: 4px 10px !important;
  font-size: 11px !important;
}

.code {
  color: #6b6a63 !important;
}

.filter-select {
  background: #fff !important;
  border: 1px solid #d0cfc6 !important;
  color: #1c1b18 !important;
  border-radius: 6px !important;
}

.history-overlay {
  background: rgba(28, 27, 24, 0.25) !important;
}

.history-panel {
  background: #fff !important;
  border-left: 1px solid #e4e3dc !important;
}

.history-item {
  background: #fff !important;
  border: 1px solid #e4e3dc !important;
  border-radius: 8px !important;
}

.history-item:hover,
.history-item.active {
  background: #f0efe9 !important;
  border-color: #d0cfc6 !important;
}

/* ===== Budget upload page replica ===== */
.upload-section {
  min-height: auto !important;
  display: block !important;
  padding: 6px 0 6px !important;
}

.upload-shell {
  max-width: 860px !important;
  margin: 0 auto !important;
}

.upload-page-header {
  margin-bottom: 12px !important;
  padding-left: 0 !important;
  text-align: left !important;
  align-items: flex-start !important;
  justify-items: flex-start !important;
}

.upload-page-header h1 {
  margin: 0 0 8px !important;
  font-size: 18px !important;
  font-weight: 500 !important;
  color: #1c1b18 !important;
  line-height: 1.2 !important;
}

.upload-page-header p {
  margin: 0 !important;
  font-size: 13px !important;
  line-height: 1.45 !important;
  color: #a8a79f !important;
}

.upload-container {
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
  gap: 16px !important;
  align-items: stretch !important;
  margin-bottom: 14px !important;
}

.upload-copy,
.upload-box,
.recent-uploads-card {
  background: #ffffff !important;
  border: 1px solid #e4e3dc !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}

.upload-copy {
  display: block !important;
  min-height: 0 !important;
  padding: 16px 16px 14px !important;
  text-align: left !important;
}

.upload-copy-top {
  margin-bottom: 14px !important;
  justify-content: flex-start !important;
  align-items: flex-start !important;
}

.panel-kicker.budget-kicker {
  display: inline-block !important;
  margin: 0 !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  letter-spacing: 0.16em !important;
  text-transform: uppercase !important;
  color: #5f36da !important;
  line-height: 1 !important;
}

.budget-intro-card {
  display: grid;
  gap: 10px;
  text-align: left !important;
  justify-items: stretch !important;
  align-items: start !important;
}

.inline-target-header {
  width: 100% !important;
  text-align: left !important;
}

.inline-target-header h3 {
  margin: 0 !important;
  font-size: 16px !important;
  line-height: 1.2 !important;
  font-weight: 500 !important;
  color: #1c1b18 !important;
  text-align: left !important;
}

.budget-output-label {
  margin-top: 0 !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  color: #a8a79f !important;
  width: 100% !important;
  text-align: left !important;
}

.budget-output-block {
  padding: 10px 12px !important;
  border-radius: 8px !important;
  background: #f8f6f1 !important;
  border: 1px solid #e5e0d6 !important;
  width: 100% !important;
  text-align: left !important;
}

.budget-output-title {
  margin-bottom: 8px !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  color: #a8a79f !important;
  text-align: left !important;
}

.budget-output-items {
  display: flex !important;
  flex-wrap: wrap !important;
  gap: 6px !important;
  justify-content: flex-start !important;
  align-items: center !important;
}

.budget-output-item {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  min-height: 28px !important;
  padding: 0 10px !important;
  border-radius: 7px !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  line-height: 1 !important;
  border: none !important;
}

.budget-output-item.blue {
  background: #e9f0fe !important;
  color: #245db0 !important;
}

.budget-output-item.purple {
  background: #efe7ff !important;
  color: #6a39d7 !important;
}

.budget-output-item.amber {
  background: #ffefb7 !important;
  color: #a55508 !important;
}

.budget-output-item.green {
  background: #d8f6e5 !important;
  color: #147657 !important;
}

.budget-checklist {
  margin-top: 8px !important;
  gap: 12px !important;
  width: 100% !important;
  justify-items: start !important;
}

.budget-checklist .check-item {
  gap: 8px !important;
  align-items: flex-start !important;
  font-size: 12px !important;
  line-height: 1.6 !important;
  color: #5e5a52 !important;
  justify-content: flex-start !important;
  text-align: left !important;
}

.check-icon.purple {
  width: 18px !important;
  height: 18px !important;
  border-radius: 4px !important;
  background: #efe7ff !important;
  color: #5f36da !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  flex-shrink: 0;
  margin-top: 2px !important;
}

.budget-checklist b {
  color: #1c1b18 !important;
  font-weight: 700 !important;
}

.upload-box {
  min-height: 0 !important;
  display: flex !important;
  flex-direction: column !important;
  justify-content: space-between !important;
  padding: 16px 16px 14px !important;
}

.budget-upload-zone {
  min-height: 0 !important;
  flex: 1 !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  text-align: center !important;
  padding: 22px 18px !important;
  margin: 12px 12px 0 !important;
  border-radius: 8px !important;
  border: 1.5px dashed #d0cfc6 !important;
  background: #f6f5f2 !important;
  box-shadow: none !important;
  min-height: 180px !important;
}

.budget-upload-zone:hover {
  border-color: #5f36da !important;
  background: #f3efff !important;
  transform: none !important;
}

.budget-upload-zone .upload-icon-wrap {
  width: 34px !important;
  height: 34px !important;
  margin: 0 auto 14px !important;
}

.budget-upload-zone .upload-icon {
  width: 34px !important;
  height: 34px !important;
  color: #a8a79f !important;
  filter: none !important;
}

.budget-upload-zone h2 {
  margin: 0 0 4px !important;
  font-size: 16px !important;
  font-weight: 500 !important;
  color: #1c1b18 !important;
  line-height: 1.5 !important;
}

.budget-link {
  color: #5f36da !important;
  text-decoration: underline !important;
  text-decoration-thickness: 1px !important;
  text-underline-offset: 2px !important;
}

.budget-upload-zone .upload-hint {
  margin: 0 0 12px !important;
  font-size: 12px !important;
  color: #a8a79f !important;
}

.budget-upload-zone .file-types {
  gap: 8px !important;
}

.budget-upload-zone .file-tag {
  min-height: 0 !important;
  padding: 4px 12px !important;
  border-radius: 999px !important;
  background: #ffffff !important;
  border: 1px solid #dfd9cf !important;
  color: #6e6a62 !important;
  font-size: 11px !important;
  font-weight: 500 !important;
}

.upload-footer {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  gap: 16px !important;
  width: 100% !important;
  margin-top: auto !important;
  padding: 10px 12px 8px !important;
}

.upload-last {
  display: flex !important;
  align-items: center !important;
  gap: 5px !important;
  color: #a8a79f !important;
  font-size: 12px !important;
}

.upload-last strong {
  color: #6b6a63 !important;
  font-size: 12px !important;
  font-family: 'IBM Plex Mono', monospace !important;
}

.auto-upload-tip {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  min-height: 34px !important;
  padding: 0 12px !important;
  border-radius: 6px !important;
  background: #f0efe9 !important;
  color: #8a867f !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  white-space: nowrap !important;
}

.upload-feedback {
  width: 100% !important;
  margin-top: 8px !important;
  padding: 10px 12px !important;
  border-radius: 8px !important;
  font-size: 12px !important;
  line-height: 1.5 !important;
}

.upload-feedback.info {
  background: rgba(17, 94, 89, 0.08) !important;
  color: #0f766e !important;
  border: 1px solid rgba(15, 118, 110, 0.18) !important;
}

.upload-feedback.error {
  background: rgba(220, 38, 38, 0.08) !important;
  color: #b91c1c !important;
  border: 1px solid rgba(185, 28, 28, 0.18) !important;
}

.selected-file-banner {
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
  width: 100% !important;
  padding: 12px 16px !important;
  border-radius: 8px !important;
  background: #d1fae5 !important;
  border: none !important;
  text-align: left !important;
}

.selected-file-copy {
  flex: 1 !important;
}

.selected-file-name {
  color: #047857 !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  line-height: 1.35 !important;
  font-family: 'IBM Plex Mono', monospace !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}

.selected-file-meta,
.selected-file-change {
  color: #a8a79f !important;
  font-size: 11px !important;
}

.selected-file-meta {
  margin-top: 2px !important;
}

.selected-file-change {
  padding: 3px 7px !important;
  border-radius: 4px !important;
  border: 0.5px solid #e4e3dc !important;
  background: #fff !important;
}

.recent-uploads-card {
  margin-top: 0 !important;
  padding: 12px 14px !important;
}

.recent-uploads-head {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  margin-bottom: 12px !important;
}

.recent-uploads-head h3 {
  margin: 0 !important;
  font-size: 11px !important;
  font-weight: 500 !important;
  color: #6b6a63 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.5px !important;
}

.budget-view-all-btn {
  border: none !important;
  background: transparent !important;
  padding: 0 !important;
  color: #5f36da !important;
  font-size: 11px !important;
  font-weight: 500 !important;
}

.recent-uploads-grid {
  display: grid !important;
  grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
  gap: 8px !important;
}

.recent-upload-item {
  padding: 9px 10px !important;
  border-radius: 7px !important;
  border: 0.5px solid #e4e3dc !important;
  background: #f6f5f2 !important;
  text-align: left !important;
  cursor: pointer !important;
  transition: all 0.15s !important;
}

.recent-upload-item:hover {
  border-color: #d0cfc6 !important;
  background: #fff !important;
  transform: none !important;
}

.recent-upload-date {
  margin-bottom: 3px !important;
  font-size: 11px !important;
  font-weight: 500 !important;
  color: #1c1b18 !important;
  font-family: 'IBM Plex Mono', monospace !important;
}

.budget-recent-value {
  margin-bottom: 2px !important;
  color: #5f36da !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  line-height: 1.2 !important;
  font-family: 'IBM Plex Mono', monospace !important;
}

.budget-recent-value span {
  font-size: 12px !important;
  font-family: 'IBM Plex Sans', 'Noto Sans SC', sans-serif !important;
}

.recent-upload-meta {
  color: #a8a79f !important;
  font-size: 10px !important;
  font-weight: 400 !important;
}

@media (max-width: 980px) {
  .upload-container {
    grid-template-columns: 1fr !important;
  }

  .recent-uploads-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }

  .progress-row {
    flex-direction: column;
    align-items: stretch;
  }

  .progress-right {
    min-width: 0;
    text-align: left;
  }

  .table-footnote {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 640px) {
  .upload-copy,
  .upload-box,
  .recent-uploads-card {
    padding: 18px !important;
    border-radius: 18px !important;
  }

  .upload-page-header h1 {
    font-size: 22px !important;
  }

  .inline-target-header h3 {
    font-size: 20px !important;
  }

  .recent-uploads-grid {
    grid-template-columns: 1fr !important;
  }

  .upload-footer {
    flex-direction: column !important;
    align-items: stretch !important;
  }

  .upload-submit-btn {
    width: 100% !important;
  }
}

/* ── New handoff-style data section ─────────────────── */

/* Buttons (for data section) */
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

/* Budget hero KPI grid */
.budget-hero-kpis {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 32px; margin-bottom: 28px;
}
.bk-label {
  font-size: 11.5px; color: var(--ink-3);
  text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px;
}
.bk-value {
  font-size: 36px; font-weight: 500; color: var(--ink);
  letter-spacing: -0.025em; line-height: 1;
  font-family: var(--font-mono);
}
.bk-value.accent { color: var(--accent); }
.bk-unit { font-size: 14px; color: var(--ink-3); margin-left: 6px; font-family: var(--font-sans); font-weight: 400; }
.bk-sub { font-size: 12px; color: var(--ink-3); margin-top: 8px; }

/* Budget bar */
.budget-bar-track {
  display: flex; height: 12px; border-radius: 6px;
  overflow: hidden; background: var(--paper-2);
}
.budget-bar-legend {
  display: flex; gap: 24px; margin-top: 12px;
  font-size: 12px; color: var(--ink-2);
}
.bbl-item { display: flex; align-items: center; gap: 6px; }
.bbl-dot { width: 8px; height: 8px; border-radius: 2px; flex-shrink: 0; }

/* Snapshot badge */
.snapshot-badge-sm {
  font-size: 10px; padding: 2px 7px; border-radius: 10px;
  background: var(--warn-soft); color: var(--warn); font-weight: 500;
  font-family: var(--font-mono);
}

/* Compare chips */
.compare-chip {
  display: grid; gap: 6px; padding: 14px;
  border-radius: var(--r-md); background: var(--paper); border: 1px solid var(--line);
}
.compare-chip-label { color: var(--ink-4); font-size: 11px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.06em; }
.compare-chip strong { font-size: 20px; color: var(--ink); font-weight: 500; font-family: var(--font-mono); }
.compare-chip-detail { color: var(--ink-3); font-size: 12px; }

/* Filter select */
.filter-sel {
  height: 32px; padding: 0 10px; border-radius: var(--r-md);
  border: 1px solid var(--line-2); background: var(--surface);
  color: var(--ink-2); font-size: 12px; cursor: pointer; font-family: inherit;
}
.filter-sel:hover { border-color: var(--ink-4); }

/* ══════════════════════════════════════════════════════════════════
   批次下达 Tab
══════════════════════════════════════════════════════════════════ */

/* 标签栏 */
.bpage-tabs {
  display: flex; gap: 2px; padding: 0 0 0 2px; margin-bottom: 0;
  border-bottom: 1px solid var(--line);
}
.bpage-tab {
  display: flex; align-items: center; gap: 6px;
  padding: 10px 18px; border: none; background: none; cursor: pointer;
  font-size: 13px; font-weight: 500; color: var(--ink-3);
  border-bottom: 2px solid transparent; margin-bottom: -1px;
  transition: color 0.15s, border-color 0.15s; font-family: inherit;
}
.bpage-tab:hover { color: var(--ink-2); }
.bpage-tab.active { color: var(--ink); border-bottom-color: var(--accent); }
.bpage-tab-count {
  background: var(--accent); color: #fff; border-radius: 10px;
  padding: 1px 6px; font-size: 11px; font-weight: 600;
}

/* 批次视图框架 */
.batch-view { padding: 28px 0 48px; }
.batch-view-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  margin-bottom: 20px; gap: 16px;
}
.batch-head-actions { display: flex; gap: 8px; flex-shrink: 0; margin-top: 4px; }

/* 加载 */
.batch-loading-wrap {
  display: flex; align-items: center; gap: 12px;
  padding: 48px; color: var(--ink-3); font-size: 14px;
}

/* 表格容器 */
.batch-table-outer { overflow-x: auto; max-height: 65vh; overflow-y: auto; }

/* 批次表格 */
.batch-tbl { width: max-content; min-width: 100%; border-collapse: collapse; font-size: 12.5px; }
.batch-tbl thead { position: sticky; top: 0; z-index: 10; }
.batch-tbl thead tr { background: var(--surface); }
.batch-tbl th {
  padding: 10px 12px; font-weight: 600; font-size: 11px; color: var(--ink-3);
  text-align: right; white-space: nowrap; border-bottom: 2px solid var(--line);
  letter-spacing: 0.02em;
}
.batch-tbl td { padding: 9px 12px; border-bottom: 1px solid var(--line); vertical-align: middle; white-space: nowrap; }

/* 列宽 */
.bc-date { text-align: left !important; min-width: 110px; font-weight: 500; color: var(--ink); }
.bc-amount { min-width: 88px; text-align: right; color: var(--ink-2); font-family: var(--font-mono); font-size: 12px; }
.bc-subtotal { min-width: 100px; text-align: right; font-family: var(--font-mono); font-size: 12px; }
.bc-note { min-width: 200px; max-width: 300px; text-align: left; overflow: hidden; text-overflow: ellipsis; color: var(--ink-3); font-size: 12px; }
.bc-ops { min-width: 90px; text-align: right; padding-right: 14px; }

/* 行样式 */
.br-total { background: rgba(46,117,182,0.07); }
.br-total td { font-weight: 600; color: var(--ink); border-bottom: 2px solid var(--line); }
.br-total .bc-subtotal { color: #1F3864; }
.br-batch:hover { background: var(--surface); }
.br-even { background: var(--paper-2, #fafaf8); }
.br-even:hover { background: var(--surface); }

/* 零值 */
.bc-zero { color: var(--ink-4); }
.bc-note-muted { color: var(--ink-4) !important; font-style: italic; }

/* 负数 */
.neg { color: var(--bad, #c00000); }

/* 单元格批注角标 */
.bc-cell-wrap { position: relative; display: inline-flex; align-items: center; width: 100%; justify-content: flex-end; }
.bc-note-corner {
  position: absolute; top: -4px; right: -4px; pointer-events: none;
  width: 0; height: 0; border-style: solid;
  border-width: 0 7px 7px 0;
  border-color: transparent #e53e3e transparent transparent;
}

/* 全局批注弹窗（teleport to body） */
.cell-note-popup {
  position: fixed; z-index: 9999; pointer-events: none;
  background: #fff; border: 1px solid #e2e8f0;
  border-radius: 8px; padding: 9px 12px;
  font-size: 12px; line-height: 1.6; max-width: 280px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.13);
  color: #374151; white-space: pre-wrap;
}

/* 空状态 */
.batch-empty-cell { text-align: center; padding: 48px 24px; color: var(--ink-3); font-size: 14px; }

/* 行内操作按钮 */
.btn-row-op {
  padding: 3px 10px; border-radius: var(--r-sm); border: 1px solid var(--line-2);
  background: none; cursor: pointer; font-size: 11px; color: var(--ink-3);
  font-family: inherit; transition: all 0.15s;
}
.btn-row-op:hover { color: var(--ink); border-color: var(--ink-3); background: var(--surface); }
.btn-row-op.del:hover { color: var(--bad); border-color: var(--bad); background: rgba(192,0,0,0.05); }

/* 弹窗 */
.batch-modal-box {
  width: min(700px, 96vw); max-height: 90vh;
  display: flex; flex-direction: column;
}
.modal-body { overflow-y: auto; flex: 1; padding: 20px 24px; }
.form-row { margin-bottom: 14px; }
.form-label { display: block; font-size: 12px; font-weight: 500; color: var(--ink-2); margin-bottom: 5px; }
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
  margin: 18px 0 10px; padding-bottom: 6px; border-bottom: 1px solid var(--line);
}
.form-section-hint { font-weight: 400; color: var(--ink-4); font-size: 11px; }

/* 金额输入网格 */
.amounts-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px 16px; }
.amount-cell { display: flex; flex-direction: column; gap: 3px; }
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
  padding: 6px 10px; border-radius: var(--r-sm);
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
  margin-top: 14px; padding: 10px 14px; border-radius: var(--r-md);
  background: var(--surface); font-size: 13px; color: var(--ink-2); text-align: right;
}
.modal-footer {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 14px 24px; border-top: 1px solid var(--line);
}

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
</style>
