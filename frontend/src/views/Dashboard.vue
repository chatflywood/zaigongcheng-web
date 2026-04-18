<template>
  <div class="dashboard">
    <div v-if="!hasData || showUpload" class="upload-section">
      <div class="upload-shell">
        <div class="upload-page-header">
          <div class="upload-page-header-row">
            <div>
              <h1>在建工程</h1>
              <p>设置当期目标，上传明细后自动生成支出进度与管理员排名</p>
            </div>
            <button v-if="hasData && showUpload" class="back-to-dashboard-btn" @click="showUpload = false">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                <polyline points="9 22 9 12 15 12 15 22"/>
              </svg>
              返回看板
            </button>
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
                <input
                  type="number"
                  v-model.number="targetValue"
                  placeholder="如 503"
                  @keyup.enter="confirmTargetValue"
                />
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
            <button
              v-for="record in recentHistoryCards"
              :key="record.id"
              class="recent-upload-item"
              @click="viewHistorySnapshot(record.id)"
            >
              <div class="recent-upload-date">{{ formatHistoryDateOnly(record.uploaded_at) }}</div>
              <div class="recent-upload-value">{{ formatNum(record.dashboard_snapshot?.metrics?.capital || 0) }} <span>万元</span></div>
              <div class="recent-upload-meta">目标 {{ formatNum(record.target_value || 0) }} · {{ formatHistoryProgress(record) }}</div>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="data-section">
      <div class="section-header section-header-rich">
        <div class="header-main">
          <div class="page-title page-title-rich">
          <h2>在建工程分析</h2>
          </div>
          <span v-if="viewingSnapshotLabel" class="snapshot-badge">{{ viewingSnapshotLabel }}</span>
          <span class="date-badge" v-if="displayAnalysisDate">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
              <line x1="16" y1="2" x2="16" y2="6"/>
              <line x1="8" y1="2" x2="8" y2="6"/>
              <line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
            {{ displayAnalysisDate }}
          </span>
        </div>

        <div class="header-side">
          <button class="ghost-action --history" @click="openHistoryPanel">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 12a9 9 0 1 0 3-6.7"/>
              <path d="M3 4v5h5"/>
              <path d="M12 7v5l3 3"/>
            </svg>
            历史记录
          </button>
          <button v-if="(isViewingHistory || props.snapshotLabel) && (props.latestData || props.initialData)" class="ghost-action --restore" @click="restoreLatestView">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12a9 9 0 1 1-2.64-6.36"/>
              <path d="M21 3v6h-6"/>
            </svg>
            返回最新
          </button>
          <button class="ghost-action --danger" @click="showUpload = true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
              <path d="M3 3v5h5"/>
            </svg>
            重新上传
          </button>
        </div>
      </div>

      <div class="metrics-row">
        <div class="metric-card" v-for="(metric, index) in metrics" :key="metric.label" :style="{ animationDelay: index * 0.08 + 's' }">
          <div class="metric-label">{{ metric.label }}</div>
          <div class="metric-value-row">
            <div class="metric-value" :class="metric.class">{{ animatedValues[index] ?? metric.value }}</div>
            <div v-if="metric.unit" class="metric-value-unit">{{ metric.unit }}</div>
          </div>
          <div class="metric-meta-row">
            <div v-if="metric.inlineNote" class="metric-inline-note">{{ metric.inlineNote }}</div>
            <div v-if="metric.badgeText" class="metric-badge" :class="metric.badgeClass">{{ metric.badgeText }}</div>
          </div>
          <div class="metric-glow" :class="metric.class"></div>
        </div>
      </div>

      <div v-if="compareOverview" class="compare-section">
        <div class="card-header compare-header">
          <h3>历史对比概览</h3>
          <span class="compare-caption">当前版本与上一版相比</span>
        </div>
        <div class="compare-cards">
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
        <div class="compare-table-shell">
          <div class="card-header compare-subheader">
            <h4>管理员推进 Top 5</h4>
            <span class="compare-caption">{{ managerProgressTop5.length }} 位管理员</span>
          </div>
          <div class="table-wrapper">
            <table class="data-table compare-table">
              <thead>
                <tr>
                  <th>工程管理员</th>
                  <th>当前支出</th>
                  <th>较上版变化</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in managerProgressTop5" :key="item.name">
                  <td>{{ item.name }}</td>
                  <td>{{ formatNum(item.current) }}</td>
                  <td :class="item.diff >= 0 ? 'delta-up' : 'delta-down'">{{ formatDelta(item.diff, '万元') }}</td>
                </tr>
                <tr v-if="managerProgressTop5.length === 0">
                  <td colspan="3" class="compare-empty">暂无可对比的管理员变化</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 四类工程预警面板 -->
      <div v-if="fourClassWarnings && fourClassWarnings.items && fourClassWarnings.items.length > 0" class="four-class-card">
        <div class="four-class-title-row" @click="showFourClassAllDetail" style="cursor:pointer">
          <h3>四类工程预警 <span class="four-class-subtitle">(预警期60天)</span></h3>
        </div>
        <div class="four-class-cards-row">
          <div class="four-class-mini-card" :class="'type-liezhang'" @click="showFourClassDetail('列账不及时')">
            <div class="mini-card-label">列账不及时</div>
            <div class="mini-card-nums">
              <div class="mini-card-triggered">
                <span class="num" :class="{ active: fourClassWarnings.summary?.['列账不及时']?.triggered > 0 }">
                  {{ fourClassWarnings.summary?.['列账不及时']?.triggered || 0 }}
                </span>
                <span class="label">已触发</span>
              </div>
              <div class="mini-card-warning">
                <span class="num" :class="{ active: fourClassWarnings.summary?.['列账不及时']?.warning > 0 }">
                  {{ fourClassWarnings.summary?.['列账不及时']?.warning || 0 }}
                </span>
                <span class="label">预警</span>
              </div>
            </div>
          </div>
          <div class="four-class-mini-card" :class="'type-yuzhuang'" @click="showFourClassDetail('预转固不及时')">
            <div class="mini-card-label">预转固不及时</div>
            <div class="mini-card-nums">
              <div class="mini-card-triggered">
                <span class="num" :class="{ active: fourClassWarnings.summary?.['预转固不及时']?.triggered > 0 }">
                  {{ fourClassWarnings.summary?.['预转固不及时']?.triggered || 0 }}
                </span>
                <span class="label">已触发</span>
              </div>
              <div class="mini-card-warning">
                <span class="num" :class="{ active: fourClassWarnings.summary?.['预转固不及时']?.warning > 0 }">
                  {{ fourClassWarnings.summary?.['预转固不及时']?.warning || 0 }}
                </span>
                <span class="label">预警</span>
              </div>
            </div>
          </div>
          <div class="four-class-mini-card" :class="'type-guanbi'" @click="showFourClassDetail('关闭不及时')">
            <div class="mini-card-label">关闭不及时</div>
            <div class="mini-card-nums">
              <div class="mini-card-triggered">
                <span class="num" :class="{ active: fourClassWarnings.summary?.['关闭不及时']?.triggered > 0 }">
                  {{ fourClassWarnings.summary?.['关闭不及时']?.triggered || 0 }}
                </span>
                <span class="label">已触发</span>
              </div>
              <div class="mini-card-warning">
                <span class="num" :class="{ active: fourClassWarnings.summary?.['关闭不及时']?.warning > 0 }">
                  {{ fourClassWarnings.summary?.['关闭不及时']?.warning || 0 }}
                </span>
                <span class="label">预警</span>
              </div>
            </div>
          </div>
          <div class="four-class-mini-card" :class="'type-guazhang'" @click="showFourClassDetail('长期挂账')">
            <div class="mini-card-label">长期挂账</div>
            <div class="mini-card-nums">
              <div class="mini-card-triggered">
                <span class="num" :class="{ active: fourClassWarnings.summary?.['长期挂账']?.triggered > 0 }">
                  {{ fourClassWarnings.summary?.['长期挂账']?.triggered || 0 }}
                </span>
                <span class="label">已触发</span>
              </div>
              <div class="mini-card-warning">
                <span class="num" :class="{ active: fourClassWarnings.summary?.['长期挂账']?.warning > 0 }">
                  {{ fourClassWarnings.summary?.['长期挂账']?.warning || 0 }}
                </span>
                <span class="label">预警</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 四类工程明细弹窗 -->
      <div v-if="fourClassDetailVisible" class="four-class-modal-overlay" @click.self="fourClassDetailVisible = false">
        <div class="four-class-modal">
          <div class="modal-header">
            <div class="modal-title-wrap">
              <h3>{{ fourClassDetailType }}</h3>
              <span v-if="fourClassWarnings?.analysis_date" class="modal-date">
                数据日期：{{ fourClassWarnings.analysis_date }}
              </span>
            </div>
            <div class="modal-header-actions">
              <button class="export-btn-primary" @click="exportFourClassWarnings" :disabled="!currentRecordId">
                <span>↓</span> 导出预警清单
              </button>
              <button class="modal-close" @click="fourClassDetailVisible = false">×</button>
            </div>
          </div>
          <div class="modal-body">
            <!-- 全部预警明细：分组显示 -->
            <template v-if="fourClassDetailType === '四类工程预警明细'">
              <template v-for="type in fourClassTypes" :key="type.name">
                <div v-if="getGroupItems(type.name).length > 0" class="four-class-group"
                  :class="'group-' + type.key">
                  <div class="group-header">
                    <span class="group-title">{{ type.name }}</span>
                    <span class="group-count">
                      已触发 {{ getGroupStats(type.name).triggered }} / 预警 {{ getGroupStats(type.name).warning }}
                    </span>
                  </div>
                <table class="data-table four-class-modal-table">
                  <thead>
                    <tr>
                      <th class="col-status">状态</th>
                      <th class="col-name">工程名称</th>
                      <th class="col-accept">验收类型</th>
                      <th class="col-manager">管理员</th>
                      <th class="col-date">关键日期</th>
                      <th class="col-date">截止日期</th>
                      <th class="col-project-status">工程状态</th>
                      <th class="col-days">天数</th>
                      <th class="col-suggestion">处置建议</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in getGroupItems(type.name)" :key="item.id" :class="'row-' + item.status">
                      <td class="col-status">
                        <span class="status-tag" :class="item.status">{{ item.status }}</span>
                      </td>
                      <td class="col-name" :title="item.name">{{ item.name }}</td>
                      <td class="col-accept">{{ item.acceptType }}</td>
                      <td class="col-manager">{{ item.manager }}</td>
                      <td class="col-date">{{ item.keyDate }}</td>
                      <td class="col-date">{{ item.deadline || '-' }}</td>
                      <td class="col-project-status">{{ item.projectStatus || '—' }}</td>
                      <td class="col-days" :class="getDaysClass(item.daysLabel, item.status)">
                        <span v-if="item.status === '预警' && parseInt(item.daysLabel?.match(/\d+/)?.[0]) <= 30" style="margin-right:2px">⚠️</span>{{ item.daysLabel }}
                      </td>
                      <td class="col-suggestion">{{ item.suggestion }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </template>
            </template>
            <!-- 单类型明细 -->
            <template v-else>
              <table class="data-table four-class-modal-table">
                <thead>
                  <tr>
                    <th class="col-status">状态</th>
                    <th class="col-name">工程名称</th>
                    <th class="col-accept">验收类型</th>
                    <th class="col-manager">管理员</th>
                    <th class="col-date">关键日期</th>
                    <th class="col-date">截止日期</th>
                    <th class="col-project-status">工程状态</th>
                    <th class="col-days">天数</th>
                    <th class="col-suggestion">处置建议</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in fourClassDetailItems" :key="item.id" :class="'row-' + item.status">
                    <td class="col-status">
                      <span class="status-tag" :class="item.status">{{ item.status }}</span>
                    </td>
                    <td class="col-name" :title="item.name">{{ item.name }}</td>
                    <td class="col-accept">{{ item.acceptType }}</td>
                    <td class="col-manager">{{ item.manager }}</td>
                    <td class="col-date">{{ item.keyDate }}</td>
                    <td class="col-date">{{ item.deadline || '-' }}</td>
                    <td class="col-project-status">{{ item.projectStatus || '—' }}</td>
                    <td class="col-days" :class="getDaysClass(item.daysLabel, item.status)">
                      <span v-if="item.status === '预警' && parseInt(item.daysLabel?.match(/\d+/)?.[0]) <= 30" style="margin-right:2px">⚠️</span>{{ item.daysLabel }}
                    </td>
                    <td class="col-suggestion">{{ item.suggestion }}</td>
                  </tr>
                </tbody>
              </table>
            </template>
          </div>
        </div>
      </div>

      <div class="progress-row">
        <div class="progress-label">当期资本性支出进度</div>
        <div class="progress-track-wrap">
          <div class="progress-nums-row">
            <span>已完成 {{ formatNum(dashboard?.metrics?.capital || 0) }} 万元</span>
            <span class="pct">{{ progressPercent }}%</span>
          </div>
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: Math.min(Number(progressPercent) || 0, 100) + '%' }"></div>
          </div>
        </div>
        <div class="progress-right">
          <div class="progress-completed">
            <template v-if="!editingTarget">
              目标 {{ formatNum(targetValue || 0) }} 万元
              <button v-if="currentRecordId && !isViewingHistory" class="target-edit-btn" @click="startEditTarget" title="修改目标金额">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </button>
            </template>
            <template v-else>
              <div class="target-edit-row">
                <input
                  ref="targetEditInput"
                  v-model.number="targetEditValue"
                  type="number"
                  class="target-edit-input"
                  @keyup.enter="confirmEditTarget"
                  @keyup.escape="cancelEditTarget"
                />
                <span class="target-edit-unit">万元</span>
                <button class="target-edit-save" @click="confirmEditTarget" :disabled="targetSaving">
                  {{ targetSaving ? '…' : '✓' }}
                </button>
                <button class="target-edit-cancel" @click="cancelEditTarget">✕</button>
              </div>
            </template>
          </div>
          <div class="progress-remaining" :class="{ exceeded: Number(dashboard?.metrics?.deficit || 0) < 0 }">
            {{ Number(dashboard?.metrics?.deficit || 0) >= 0 ? '还差' : '已超' }}
            {{ formatNum(Math.abs(dashboard?.metrics?.deficit || 0)) }} 万
          </div>
        </div>
      </div>

      <div class="table-card">
        <div class="card-header">
          <h3>各工程管理员汇总</h3>
          <button v-if="currentRecordId" class="ghost-action tp-btn" @click="openTransferPriority">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
              <path d="M3 6h18M3 12h12M3 18h8"/>
              <path d="M17 14l4 4-4 4"/>
            </svg>
            转固推进清单
          </button>
        </div>
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>排名</th>
                <th>工程管理员</th>
                <th>结转额</th>
                <th>本年累计资本性支出</th>
                <th>已下单待收货</th>
                <th>本月资本性支出</th>
                <th>转固率</th>
                <th>较上期变化</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in summaryRows" :key="row.manager || row['工程管理员']" :class="{ 'is-top': index === 0 }">
                <td class="rank-cell">
                  <span class="rank-badge" :class="{ top: index === 0 }">{{ index + 1 }}</span>
                </td>
                <td class="manager-name clickable" @click="openManagerModal(row.manager || row['工程管理员'])">{{ row.manager || row['工程管理员'] }}</td>
                <td>{{ formatNum(row.transfer || row['结转额']) }}</td>
                <td :class="{ 'value-highlight': (row.capital || row['本年累计资本性支出']) === maxCapital }">{{ formatNum(row.capital || row['本年累计资本性支出']) }}</td>
                <td :class="{ 'value-warning': (row.pending || row['已下单待收货']) > 30 }">{{ formatNum(row.pending || row['已下单待收货']) }}</td>
                <td>{{ formatNum(row.monthSpend || row['本月资本性支出']) }}</td>
                <td>
                  <span class="rate-badge" :class="getRateClass(row.rate || row['转固率'])">
                    {{ formatPercent(row.rate || row['转固率']) }}
                  </span>
                </td>
                <td>
                  <span class="change-cell" :class="getChangeClass(row.manager || row['工程管理员'], row.capital || row['本年累计资本性支出'])">
                    {{ getChangeText(row.manager || row['工程管理员'], row.capital || row['本年累计资本性支出']) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="table-footnote">
          <span>合计：累计支出 {{ formatNum(dashboard?.metrics?.capital || 0) }} 万 · 待收货 {{ formatNum(dashboard?.metrics?.pending || 0) }} 万 · 本月支出 {{ formatNum(dashboard?.metrics?.monthSpend || 0) }} 万</span>
          <span>数据日期：{{ displayAnalysisDate || '-' }}</span>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="loader">
        <div class="loader-ring"></div>
        <div class="loader-ring"></div>
        <div class="loader-ring"></div>
      </div>
      <p>分析中...</p>
    </div>

    <div v-if="historyVisible" class="history-overlay" @click.self="closeHistoryPanel">
      <aside class="history-panel">
        <div class="history-panel-header">
          <div>
            <span class="panel-kicker">History Snapshots</span>
            <h3>在建工程历史记录</h3>
            <p>选择某次上传记录，直接恢复当时的分析快照。</p>
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
              <span class="history-kpi-capital">{{ formatNum(record.dashboard_snapshot?.metrics?.capital || 0) }}<em>万元</em></span>
              <span class="history-kpi-progress">{{ formatHistoryProgress(record) }}</span>
              <span
                v-if="getCapitalDelta(record, index) !== null"
                class="history-kpi-delta"
                :class="getCapitalDelta(record, index) >= 0 ? 'delta-up' : 'delta-down'"
              >{{ getCapitalDelta(record, index) >= 0 ? '↑' : '↓' }} {{ formatNum(Math.abs(getCapitalDelta(record, index))) }}</span>
            </div>
            <div class="history-item-meta">
              <span>{{ formatHistoryTime(record.uploaded_at) }}</span>
              <span v-if="record.file_date">{{ formatFileDate(record.file_date) }}</span>
            </div>
          </button>
        </div>
      </aside>
    </div>

    <div v-if="modalVisible" class="modal-overlay" @click.self="closeModal">
      <div class="modal-container">
        <div class="modal-header">
          <h3>{{ modalManager }} - 工程明细</h3>
          <button class="modal-close" @click="closeModal">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div v-if="modalLoading" class="modal-loading">
            <div class="loader-ring"></div>
          </div>
          <div v-else-if="modalData.length === 0" class="modal-empty">
            <p>暂无数据</p>
          </div>
          <table v-else class="detail-table">
            <thead>
              <tr>
                <th @click="toggleSort('工程名称')" class="sortable">
                  工程名称
                  <span class="sort-icon" :class="getSortClass('工程名称')">{{ getSortIcon('工程名称') }}</span>
                </th>
                <th @click="toggleSort('结转额')" class="sortable">
                  结转额
                  <span class="sort-icon" :class="getSortClass('结转额')">{{ getSortIcon('结转额') }}</span>
                </th>
                <th @click="toggleSort('本年累计资本性支出')" class="sortable">
                  本年累计资本性支出
                  <span class="sort-icon" :class="getSortClass('本年累计资本性支出')">{{ getSortIcon('本年累计资本性支出') }}</span>
                </th>
                <th @click="toggleSort('已下单待收货')" class="sortable">
                  已下单待收货
                  <span class="sort-icon" :class="getSortClass('已下单待收货')">{{ getSortIcon('已下单待收货') }}</span>
                </th>
                <th @click="toggleSort('本月资本性支出')" class="sortable">
                  本月资本性支出
                  <span class="sort-icon" :class="getSortClass('本月资本性支出')">{{ getSortIcon('本月资本性支出') }}</span>
                </th>
                <th @click="toggleSort('在建工程期末余额')" class="sortable">
                  在建工程期末余额
                  <span class="sort-icon" :class="getSortClass('在建工程期末余额')">{{ getSortIcon('在建工程期末余额') }}</span>
                </th>
                <th @click="toggleSort('转固率')" class="sortable">
                  转固率
                  <span class="sort-icon" :class="getSortClass('转固率')">{{ getSortIcon('转固率') }}</span>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in sortedModalData" :key="item.工程名称">
                <td>{{ item.工程名称 }}</td>
                <td>{{ formatNum(item.结转额) }}</td>
                <td>{{ formatNum(item['本年累计资本性支出']) }}</td>
                <td>{{ formatNum(item.已下单待收货) }}</td>
                <td>{{ formatNum(item.本月资本性支出) }}</td>
                <td>{{ formatNum(item.在建工程期末余额) }}</td>
                <td>
                  <span class="rate-badge" :class="getRateClass(item.转固率)">
                    {{ formatPercent(item.转固率) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <!-- 转固推进清单弹窗 -->
  <div v-if="transferPriorityVisible" class="tp-overlay" @click.self="transferPriorityVisible = false">
    <div class="tp-modal">
      <div class="tp-header">
        <div class="tp-header-left">
          <h3>转固推进清单</h3>
          <span class="tp-subtitle">各管理员待转固项目 · 按转固贡献从高到低排序</span>
        </div>
        <div class="tp-header-actions">
          <button
            class="tp-export-btn"
            :disabled="transferExporting || !transferPriorityData.length"
            @click="handleExportTransferPriority"
          >
            <span v-if="transferExporting">导出中…</span>
            <span v-else>导出 Excel</span>
          </button>
          <button class="modal-close" @click="transferPriorityVisible = false">×</button>
        </div>
      </div>

      <div v-if="transferPriorityLoading" class="tp-loading">
        <div class="loader-ring"></div>
        <p>正在计算...</p>
      </div>

      <div v-else-if="transferPriorityError" class="tp-empty tp-error">
        <p>{{ transferPriorityError }}</p>
      </div>

      <div v-else-if="!transferPriorityData.length" class="tp-empty">
        <p>暂无待转固项目数据</p>
      </div>

      <template v-else>
      <!-- 测算输入条 -->
      <div class="tp-calc-bar">
        <div class="tp-calc-left">
          <span class="tp-calc-label">转固率目标测算</span>
          <div class="tp-calc-input-wrap">
            <input
              v-model="targetRate"
              type="number" min="1" max="100" step="1"
              placeholder="输入目标 %"
              class="tp-calc-input"
              @keyup.enter="$event.target.blur()"
            />
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
              <!-- 无目标时：显示待转固余额 & 全部完成后可达 -->
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
              <!-- 有目标时：显示任务分配结果 -->
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
                  <!-- 分隔线：从必做切换到可选 -->
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
            <!-- 有目标：显示任务分配摘要 -->
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
            <!-- 无目标：原有逻辑 -->
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

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { uploadExcel, getCompare, getHistory, getHistorySnapshot, getManagerDetails, getTransferPriority, exportTransferPriority, pushNotify, updateTargetValue } from '../api'
import * as echarts from 'echarts'

const props = defineProps({
  initialData: {
    type: Object,
    default: null
  },
  initialRecordId: {
    type: Number,
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
  },
  fourClassWarnings: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['dataUpdate', 'restoreLatest', 'warningsUpdate'])

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
const modalVisible = ref(false)
const modalData = ref([])
const modalManager = ref('')
const modalLoading = ref(false)
const selectedFile = ref(null)
const selectedFileName = ref('')
const sortKey = ref('本年累计资本性支出')
const sortOrder = ref('desc')
const currentRecordId = ref(null)
const historyVisible = ref(false)
const historyLoading = ref(false)
const historyRecords = ref([])
const isViewingHistory = ref(false)
const snapshotDisplayDate = ref(null)

const progressChart = ref(null)
const barChart = ref(null)
let progressChartInstance = null
let barChartInstance = null

// 四类工程预警
const fourClassWarnings = ref(null)
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

// 转固推进清单
const transferPriorityVisible = ref(false)
const transferPriorityData = ref([])
const transferPriorityLoading = ref(false)
const targetRate = ref('')

const transferPriorityError = ref('')

async function openTransferPriority() {
  if (!currentRecordId.value) return
  transferPriorityVisible.value = true
  if (transferPriorityData.value.length) return  // 已加载，直接展示
  transferPriorityLoading.value = true
  transferPriorityError.value = ''
  try {
    const result = await getTransferPriority(currentRecordId.value)
    if (result.success) {
      transferPriorityData.value = result.data || []
    } else {
      transferPriorityError.value = result.message || '获取数据失败'
    }
  } catch (e) {
    console.error('获取转固优先级失败:', e)
    transferPriorityError.value = e?.response?.data?.message || e?.message || '请求失败，请检查后端服务是否已重启'
  } finally {
    transferPriorityLoading.value = false
  }
}

watch(currentRecordId, () => {
  transferPriorityData.value = []
  transferPriorityError.value = ''
  targetRate.value = ''
})

const pushingNotify = ref(false)
async function handlePushNotify() {
  if (!currentRecordId.value || pushingNotify.value) return
  pushingNotify.value = true
  try {
    const res = await pushNotify(currentRecordId.value)
    if (res.success) {
      alert('推送成功，请在企业微信群查看')
    } else {
      alert(res.message || '推送失败')
    }
  } catch (e) {
    const msg = e?.response?.data?.message || e?.message || '推送失败'
    alert(msg.includes('Webhook') ? msg : `推送失败：${msg}`)
  } finally {
    pushingNotify.value = false
  }
}

const transferExporting = ref(false)
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
  } catch (e) {
    console.error('导出失败:', e)
    alert('导出失败，请重试')
  } finally {
    transferExporting.value = false
  }
}

// 转固率测算
const computedTarget = computed(() => {
  const raw = Number(targetRate.value)
  if (!targetRate.value || isNaN(raw) || raw <= 0 || raw > 100) return null
  if (!transferPriorityData.value.length) return null
  const target = raw / 100

  // 全局加总
  let globalDenom = 0
  let globalNumer = 0
  for (const m of transferPriorityData.value) {
    globalDenom += m.denominator
    globalNumer += (1 - m.current_rate) * m.denominator
  }
  const globalCurrentRate = globalDenom > 0 ? 1 - globalNumer / globalDenom : 0
  const globalRequired = Math.max(globalNumer - (1 - target) * globalDenom, 0)

  // 各管理员测算
  const managers = transferPriorityData.value.map(m => {
    const alreadyAchieved = m.current_rate >= target
    const managerRequired = alreadyAchieved ? 0 : (target - m.current_rate) * m.denominator

    // 找到累计后转固率首次 >= target 的项目索引（即最少需完成到第几个）
    const cutoffIdx = m.projects.findIndex(p => p['累计后转固率'] >= target)
    // cutoffIdx === -1 说明全做完也达不到目标（余额不够）
    const reachable = cutoffIdx !== -1

    const projects = m.projects.map((p, idx) => ({
      ...p,
      needed: alreadyAchieved ? false : (cutoffIdx === -1 ? true : idx <= cutoffIdx),
    }))

    const neededCount = alreadyAchieved ? 0 : (cutoffIdx === -1 ? m.projects.length : cutoffIdx + 1)
    const neededBalance = projects.filter(p => p.needed).reduce((s, p) => s + p['在建余额'], 0)

    return { ...m, projects, alreadyAchieved, reachable, managerRequired: Math.round(managerRequired * 100) / 100, neededCount, neededBalance: Math.round(neededBalance * 100) / 100 }
  })

  return {
    target,
    globalCurrentRate,
    globalRequired: Math.round(globalRequired * 100) / 100,
    alreadyGlobal: globalCurrentRate >= target,
    managers,
  }
})

const displayManagers = computed(() => {
  if (computedTarget.value) return computedTarget.value.managers
  return transferPriorityData.value.map(m => ({
    ...m,
    projects: m.projects.map(p => ({ ...p, needed: null })),
    alreadyAchieved: false,
    reachable: true,
    managerRequired: 0,
    neededCount: 0,
    neededBalance: 0,
  }))
})

function showFourClassDetail(type) {
  fourClassDetailType.value = type
  fourClassDetailItems.value = fourClassWarnings.value?.items?.filter(item => item.type === type) || []
  fourClassDetailVisible.value = true
}

function showFourClassAllDetail() {
  fourClassDetailType.value = '四类工程预警明细'
  fourClassDetailItems.value = fourClassWarnings.value?.items || []
  fourClassDetailVisible.value = true
}

function getGroupItems(type) {
  return fourClassWarnings.value?.items?.filter(item => item.type === type) || []
}

function getGroupStats(type) {
  const items = getGroupItems(type)
  return {
    triggered: items.filter(i => i.status === '已触发' || i.status === '已触发(超期完成)').length,
    warning: items.filter(i => i.status === '预警').length
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

async function exportFourClassWarnings() {
  try {
    const { exportFourClassExcel } = await import('../api')
    const blob = await exportFourClassExcel(currentRecordId.value)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const fileDate = fourClassWarnings.value?.summary?.analysis_date?.replace(/-/g, '') || ''
    link.download = `四类工程预警清单_${fileDate}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('导出失败:', error)
  }
}
const handleResize = () => {
  progressChartInstance?.resize()
  barChartInstance?.resize()
}

watch(() => props.initialData, async (newData) => {
  if (newData) {
    applyDashboardData(newData)
    // 如果父组件传入了记录 ID（自动加载场景），设置它
    if (props.initialRecordId) {
      currentRecordId.value = props.initialRecordId
    }
    isViewingHistory.value = false
    snapshotDisplayDate.value = null
    // 获取对比数据
    await fetchCompareData()
    nextTick(() => initCharts())
  }
}, { immediate: true })

watch(() => props.fourClassWarnings, (newWarnings) => {
  fourClassWarnings.value = newWarnings || null
  console.log('[DEBUG] props.fourClassWarnings changed:', newWarnings)
}, { immediate: true })

const displayAnalysisDate = computed(() => snapshotDisplayDate.value || props.analysisDate)

const comparisonSource = computed(() => props.historyComparison || previousData.value)
const shouldShowHistoryCompare = computed(() => Boolean(props.historyComparison))

const viewingSnapshotLabel = computed(() => {
  if (props.snapshotLabel) return props.snapshotLabel
  if (!isViewingHistory.value) return ''
  return '当前查看：历史快照'
})

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
    capital: {
      current: currentCapital,
      diff: currentCapital - previousCapital,
      progressDiff: (currentProgress - previousProgress) * 100,
    },
    rate: {
      current: currentRate,
      diff: (currentRate - previousRate) * 100,
    },
  }
})

const managerProgressTop5 = computed(() => {
  if (!shouldShowHistoryCompare.value) return []
  const previousSummary = getSourceSummary(comparisonSource.value)
  if (!previousSummary.length || !summaryRows.value.length) return []

  const previousMap = new Map(
    previousSummary.map(item => [
      item.manager || item['工程管理员'],
      Number(item.capital || item['本年累计资本性支出'] || 0)
    ])
  )

  const changes = summaryRows.value
    .map(item => {
      const name = item.manager || item['工程管理员']
      const current = Number(item.capital || item['本年累计资本性支出'] || 0)
      const previous = previousMap.get(name) || 0
      return {
        name,
        current,
        diff: current - previous,
      }
    })
    .filter(item => item.diff !== 0)
    .sort((a, b) => b.diff - a.diff)

  return changes.slice(0, 5)
})

const recentHistoryCards = computed(() => historyRecords.value.slice(0, 4))

const pendingOverLimitCount = computed(() => {
  return summaryRows.value.filter(item => {
    const value = Number(item.pending || item['已下单待收货'] || 0)
    return value > 30
  }).length
})

const deficitHint = computed(() => {
  const deficit = Number(dashboard.value?.metrics?.deficit || 0)
  if (deficit >= 0) return `目标差额：还差 ${formatNum(deficit)} 万`
  return `目标差额：已超 ${formatNum(Math.abs(deficit))} 万`
})

const pendingPressure = computed(() => {
  const count = pendingOverLimitCount.value
  if (count <= 0) {
    return { text: '压力正常', badgeClass: 'safe' }
  }
  return { text: `${count} 位超 30 万`, badgeClass: 'warning' }
})

const rateStatus = computed(() => {
  const rate = Number(dashboard.value?.metrics?.rate || 0)
  if (rate >= 0.6) {
    return { text: '达标，目标 60%', badgeClass: 'safe' }
  }
  return { text: '偏低，目标 60%', badgeClass: 'danger' }
})

const metrics = computed(() => {
  if (!dashboard.value?.metrics) return []
  const m = dashboard.value.metrics
  return [
    { label: '本年累计资本性支出', value: m.capital?.toFixed(2) || '0', unit: '万元', class: 'blue', inlineNote: deficitHint.value },
    { label: '已下单待收货', value: m.pending?.toFixed(2) || '0', unit: '万元', class: m.pending > 30 ? 'orange' : 'blue', badgeText: pendingPressure.value.text, badgeClass: pendingPressure.value.badgeClass },
    { label: '本月资本性支出', value: m.monthSpend?.toFixed(2) || '0', unit: '万元', class: 'purple' },
    { label: '综合转固率', value: formatPercent(m.rate || 0), unit: '', class: m.rate >= 0.6 ? 'green' : m.rate >= 0.3 ? 'orange' : 'red', badgeText: rateStatus.value.text, badgeClass: rateStatus.value.badgeClass },
  ]
})

// KPI count-up 动画
const animatedValues = ref([])

function runCountUp(newMetrics) {
  if (!newMetrics?.length) { animatedValues.value = []; return }
  const m = dashboard.value?.metrics
  if (!m) return
  // 与 metrics computed 同序：capital / pending / monthSpend / rate
  const targets = [
    m.capital   || 0,
    m.pending   || 0,
    m.monthSpend || 0,
    (m.rate || 0) * 100,
  ]
  const formatters = [
    v => v.toFixed(2),
    v => v.toFixed(2),
    v => v.toFixed(2),
    v => (v.toFixed(1) + '%'),
  ]
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

const progressPercent = computed(() => {
  if (!targetValue.value || targetValue.value <= 0) return '0.0'
  const capital = dashboard.value?.metrics?.capital || 0
  return ((capital / targetValue.value) * 100).toFixed(1)
})

const canUploadNow = computed(() => Boolean(targetValue.value) && Boolean(selectedFile.value))

function formatNum(num) {
  if (num === null || num === undefined || isNaN(num)) return '-'
  return Number(num).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
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

function formatFileDate(value) {
  if (!value) return '-'
  const raw = String(value)
  if (/^\d{8}$/.test(raw)) return `${raw.slice(0, 4)}-${raw.slice(4, 6)}-${raw.slice(6, 8)}`
  if (/^\d{4}$/.test(raw)) return `${raw.slice(0, 2)}-${raw.slice(2, 4)}`
  return raw
}

function formatPercent(value) {
  return (value * 100).toFixed(1) + '%'
}

function getCapitalDelta(record, index) {
  const prev = historyRecords.value[index + 1]
  if (!prev) return null
  const curr = Number(record?.dashboard_snapshot?.metrics?.capital || 0)
  const prevCapital = Number(prev?.dashboard_snapshot?.metrics?.capital || 0)
  return curr - prevCapital
}

function formatHistoryProgress(record) {
  const capital = Number(record?.dashboard_snapshot?.metrics?.capital || 0)
  const target = Number(record?.target_value || 0)
  if (!target) return '未设目标'
  return `${((capital / target) * 100).toFixed(1)}%`
}

function formatDelta(value, unit = '', alreadyPercent = false) {
  const numeric = Number(value || 0)
  const sign = numeric > 0 ? '+' : ''
  if (unit === 'pct') return `${sign}${numeric.toFixed(1)} pct`
  return `${sign}${numeric.toFixed(2)} ${unit}`.trim()
}

function getRateClass(rate) {
  if (rate >= 1) return 'success'
  if (rate >= 0.6) return 'normal'
  if (rate >= 0.3) return 'warning'
  return 'danger'
}

function getPreviousCapital(manager) {
  const prevSummary = getSourceSummary(comparisonSource.value)
  if (!prevSummary.length) return null
  const prev = prevSummary.find(r => (r.manager || r['工程管理员']) === manager)
  return prev ? (prev.capital || prev['本年累计资本性支出']) : null
}

function getSourceMetrics(source) {
  if (!source) return null
  return source.dashboard?.metrics || source.metrics || null
}

function getSourceSummary(source) {
  if (!source) return []
  return source.dashboard?.summary || source.summary || []
}

function getChangeClass(manager, currentCapital) {
  const prev = getPreviousCapital(manager)
  if (prev === null || isNaN(currentCapital) || isNaN(prev)) return 'no-change'
  // 保留2位小数比较
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
  if (prev === null || isNaN(currentCapital) || isNaN(prev)) return '― 0.00'
  // 保留2位小数比较
  const currentRounded = Math.round(currentCapital * 100) / 100
  const prevRounded = Math.round(prev * 100) / 100
  if (currentRounded === prevRounded) return '― 0.00'
  const diff = currentCapital - prev
  if (isNaN(diff)) return '― 0.00'
  const sign = diff > 0 ? '+' : ''
  const arrow = diff > 0 ? '↑' : '↓'
  return `${arrow} ${sign}${diff.toFixed(2)}`
}

function triggerFileInput() {
  if (!targetValue.value) {
    uploadMessage.value = '请先输入目标金额'
    uploadMessageType.value = 'error'
    return
  }
  uploadMessage.value = ''
  fileInput.value?.click()
}

function confirmTargetValue() {
  if (!targetValue.value) {
    uploadMessage.value = '请先输入目标金额'
    uploadMessageType.value = 'error'
    return
  }
  uploadMessage.value = `目标金额已设置为 ${Number(targetValue.value).toFixed(2)} 万元`
  uploadMessageType.value = 'info'
}

// ── 数据页内联编辑目标值 ──────────────────────────────────────
const editingTarget = ref(false)
const targetEditValue = ref(null)
const targetSaving = ref(false)
const targetEditInput = ref(null)

function startEditTarget() {
  targetEditValue.value = targetValue.value
  editingTarget.value = true
  nextTick(() => targetEditInput.value?.focus())
}

function cancelEditTarget() {
  editingTarget.value = false
  targetEditValue.value = null
}

async function confirmEditTarget() {
  const newTarget = Number(targetEditValue.value)
  if (!newTarget || newTarget <= 0) return
  if (newTarget === targetValue.value) { cancelEditTarget(); return }
  targetSaving.value = true
  try {
    await updateTargetValue(currentRecordId.value, newTarget)
    targetValue.value = newTarget
    if (dashboard.value?.metrics) {
      dashboard.value.metrics.deficit = (dashboard.value.metrics.capital || 0) - newTarget
    }
    editingTarget.value = false
  } catch (e) {
    console.error('更新目标失败', e)
  } finally {
    targetSaving.value = false
  }
}

function applyDashboardData(data) {
  dashboard.value = data
  targetValue.value = Number(data?.metrics?.yearTarget) || null
  const rawRows = data?.summary || []
  summaryRows.value = rawRows.filter(r => r.manager !== '合计' && r['工程管理员'] !== '合计')
  hasData.value = true
  currentRecordId.value = null
  if (summaryRows.value.length > 0) {
    maxCapital.value = Math.max(...summaryRows.value.map(r => r.capital || r['本年累计资本性支出'] || 0))
  } else {
    maxCapital.value = 0
  }
}

function applyHistorySnapshot(snapshot, previous = null) {
  if (!snapshot?.dashboard) return
  applyDashboardData(snapshot.dashboard)
  targetValue.value = Number(snapshot.dashboard.metrics?.yearTarget) || Number(snapshot.target_value) || null
  currentRecordId.value = snapshot.id
  previousData.value = previous
  isViewingHistory.value = true
  snapshotDisplayDate.value = snapshot.file_date
    ? formatFileDate(snapshot.file_date)
    : formatHistoryTime(snapshot.uploaded_at)
  // 加载四类工程预警数据
  fourClassWarnings.value = snapshot.four_class_warnings || null
  console.log('[DEBUG] applyHistorySnapshot four_class_warnings:', snapshot.four_class_warnings)
}

async function handleFileChange(e) {
  const file = e.target.files?.[0]
  if (file) {
    selectedFile.value = file
    selectedFileName.value = file.name
    uploadMessage.value = `已选择文件：${file.name}`
    uploadMessageType.value = 'info'
    if (targetValue.value && Number(targetValue.value) > 0) {
      await processFile(file)
    }
  }
}

async function handleDrop(e) {
  const file = e.dataTransfer.files?.[0]
  if (file) {
    selectedFile.value = file
    selectedFileName.value = file.name
    uploadMessage.value = `已选择文件：${file.name}`
    uploadMessageType.value = 'info'
    if (targetValue.value && Number(targetValue.value) > 0) {
      await processFile(file)
    }
  }
}

async function processSelectedFile() {
  if (!selectedFile.value) {
    uploadMessage.value = '请先选择需要上传的文件'
    uploadMessageType.value = 'error'
    return
  }
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
  uploadMessage.value = '文件已提交，正在分析，请稍候...'
  uploadMessageType.value = 'info'
  try {
    const result = await uploadExcel(file, targetValue.value)
    if (result.success) {
      const data = result.data?.dashboard || result.data
      if (!data?.metrics) {
        throw new Error('返回数据格式异常，未获取到分析结果')
      }
      applyDashboardData(data)
      targetValue.value = Number(data.metrics?.yearTarget) || Number(targetValue.value) || null
      // 存储四类工程预警数据
      fourClassWarnings.value = result.data?.four_class_warnings || null
      console.log('four_class_warnings:', fourClassWarnings.value)
      fourClassExpanded.value = false
      isViewingHistory.value = false
      snapshotDisplayDate.value = null
      showUpload.value = false
      clearSelectedFile()
      emit('dataUpdate', data)
      await nextTick()
      initCharts()
      // 获取对比数据
      await fetchCompareData()
      // 重新渲染图表以显示对比数据
      await nextTick()
      initCharts()
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
  } finally {
    loading.value = false
  }
}

async function loadHistoryList() {
  historyLoading.value = true
  try {
    const result = await getHistory(30)
    if (result.success) {
      const records = result.data || []
      const enriched = await Promise.all(records.map(async (record, index) => {
        if (index > 3) return record
        try {
          const snapshotResult = await getHistorySnapshot(record.id)
          if (snapshotResult.success && snapshotResult.data?.current) {
            return {
              ...record,
              dashboard_snapshot: snapshotResult.data.current.dashboard,
            }
          }
        } catch (error) {
          console.error('获取历史快照摘要失败:', error)
        }
        return record
      }))
      historyRecords.value = enriched
    }
  } catch (error) {
    console.error('获取历史列表失败:', error)
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
    const result = await getHistorySnapshot(recordId)
    console.log('[DEBUG] viewHistorySnapshot result:', result)
    if (result.success && result.data?.current) {
      applyHistorySnapshot(result.data.current, result.data.previous)
      closeHistoryPanel()
      await nextTick()
      initCharts()
    }
  } catch (error) {
    console.error('获取历史快照失败:', error)
    alert('读取历史快照失败，请稍后重试')
  } finally {
    historyLoading.value = false
  }
}

async function fetchCompareData() {
  try {
    const result = await getCompare()
    if (result.success && result.data) {
      if (result.data.latest) {
        currentRecordId.value = result.data.latest.id
      }
      if (result.data.previous) {
        previousData.value = result.data.previous
      } else {
        previousData.value = null
      }
    } else {
      previousData.value = null
    }
  } catch (error) {
    console.error('获取对比数据失败:', error)
    previousData.value = null
  }
  return Promise.resolve()
}

function clearData() {
  if (!window.confirm('确认重新上传？当前分析数据将被清除。')) return
  hasData.value = false
  showUpload.value = false
  dashboard.value = null
  summaryRows.value = []
  previousData.value = null
  currentRecordId.value = null
  isViewingHistory.value = false
  snapshotDisplayDate.value = null
  if (fileInput.value) fileInput.value.value = ''
  clearSelectedFile()
  emit('dataUpdate', null)
}

async function restoreLatestView() {
  const latest = props.latestData || props.initialData
  if (!latest) return
  applyDashboardData(latest)
  isViewingHistory.value = false
  snapshotDisplayDate.value = null
  emit('restoreLatest')
  await fetchCompareData()
  await nextTick()
  initCharts()
}

async function openManagerModal(manager) {
  modalManager.value = manager
  modalVisible.value = true
  modalLoading.value = true
  modalData.value = []

  try {
    // 获取当前记录的ID
    if (!currentRecordId.value) {
      // 尝试从 previousData 获取
      const result = await getCompare()
      if (result.success && result.data && result.data.latest) {
        currentRecordId.value = result.data.latest.id
      }
    }

    if (currentRecordId.value) {
      const res = await getManagerDetails(currentRecordId.value, manager)
      if (res.success) {
        modalData.value = res.data.details || []
      }
    }
  } catch (error) {
    console.error('获取明细失败:', error)
  } finally {
    modalLoading.value = false
  }
}

function closeModal() {
  modalVisible.value = false
}

function toggleSort(key) {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'desc'
  }
}

function getSortIcon(key) {
  if (sortKey.value !== key) return '⇅'
  return sortOrder.value === 'asc' ? '↑' : '↓'
}

function getSortClass(key) {
  return sortKey.value === key ? 'active' : ''
}

const sortedModalData = computed(() => {
  const data = [...modalData.value]
  data.sort((a, b) => {
    let aVal = a[sortKey.value]
    let bVal = b[sortKey.value]

    // 处理数字和字符串
    if (typeof aVal === 'string') {
      aVal = aVal.toLowerCase()
      bVal = bVal.toLowerCase()
    } else {
      aVal = Number(aVal) || 0
      bVal = Number(bVal) || 0
    }

    if (aVal < bVal) return sortOrder.value === 'asc' ? -1 : 1
    if (aVal > bVal) return sortOrder.value === 'asc' ? 1 : -1
    return 0
  })
  return data
})

function initCharts() {
  initProgressChart()
  initBarChart()
}

function initProgressChart() {
  if (!progressChart.value) return
  if (progressChartInstance) progressChartInstance.dispose()

  progressChartInstance = echarts.init(progressChart.value)

  const progress = targetValue.value > 0 ? (dashboard.value?.metrics?.capital || 0) / targetValue.value : 0
  const percent = Math.min(progress * 100, 150)
  const color = progress >= 1 ? '#00ff88' : progress >= 0.5 ? '#ff9500' : '#00d4ff'

  const option = {
    series: [
      // 外圈背景
      {
        type: 'gauge',
        startAngle: 220,
        endAngle: -40,
        radius: '95%',
        center: ['50%', '55%'],
        axisLine: {
          lineStyle: {
            width: 20,
            color: [[1, 'rgba(255,255,255,0.05)']]
          }
        },
        progress: { show: false },
        pointer: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        title: { show: false },
        detail: { show: false },
        data: [{ value: 0 }]
      },
      // 主进度环
      {
        type: 'gauge',
        startAngle: 220,
        endAngle: -40,
        radius: '95%',
        center: ['50%', '55%'],
        axisLine: {
          lineStyle: {
            width: 20,
            color: [[Math.min(percent / 100, 1), color]],
            shadowBlur: 20,
            shadowColor: color
          }
        },
        progress: { show: false },
        pointer: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        title: { show: false },
        detail: { show: false },
        data: [{ value: percent }]
      },
      // 内圈装饰
      {
        type: 'gauge',
        startAngle: 220,
        endAngle: -40,
        radius: '80%',
        center: ['50%', '55%'],
        axisLine: {
          lineStyle: {
            width: 3,
            color: [[1, 'rgba(255,255,255,0.03)']]
          }
        },
        progress: { show: false },
        pointer: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        title: { show: false },
        detail: { show: false },
        data: [{ value: 0 }]
      },
      // 小刻度线
      {
        type: 'gauge',
        startAngle: 220,
        endAngle: -40,
        radius: '88%',
        center: ['50%', '55%'],
        axisLine: { show: false },
        progress: { show: false },
        pointer: { show: false },
        axisTick: {
          length: 8,
          lineStyle: {
            width: 2,
            color: 'rgba(255,255,255,0.2)'
          },
          splitNumber: 10
        },
        splitLine: { show: false },
        axisLabel: { show: false },
        title: { show: false },
        detail: { show: false },
        data: [{ value: 0 }]
      }
    ]
  }

  progressChartInstance.setOption(option)
}

function initBarChart() {
  if (!barChart.value || summaryRows.value.length === 0) return
  if (barChartInstance) barChartInstance.dispose()

  barChartInstance = echarts.init(barChart.value)

  // 构建对比数据 - 使用和表格相同的获取方式
  const data = summaryRows.value.map(r => {
    const name = r.manager || r['工程管理员']
    let capital = r.capital || r['本年累计资本性支出']
    if (capital === null || capital === undefined || isNaN(capital)) {
      capital = 0
    }
    const prev = getPreviousCapital(name)
    let change = null
    let changeType = 'none'
    if (prev !== null && !isNaN(prev)) {
      // 保留2位小数比较，避免浮点数精度问题
      const capitalRounded = Math.round(capital * 100) / 100
      const prevRounded = Math.round(prev * 100) / 100
      if (capitalRounded === prevRounded) {
        change = 0
        changeType = 'none'
      } else {
        change = capital - prev
        changeType = change > 0 ? 'up' : 'down'
      }
    }
    return {
      name: name,
      value: capital,
      change: change,
      changeType: changeType
    }
  })

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 16, 32, 0.95)',
      borderColor: 'rgba(0, 212, 255, 0.3)',
      textStyle: { color: '#e8f4f8' },
      formatter: function(params) {
        const item = params[0]
        // 使用 name 查找对应的 data
        const extra = data.find(d => d.name === item.name)
        let tip = `${item.name}: ${item.value.toFixed(2)} 万元`
        if (extra && extra.change !== null && extra.change !== undefined && extra.change !== 0) {
          const sign = extra.change > 0 ? '+' : ''
          const color = extra.changeType === 'up' ? '#ff4444' : extra.changeType === 'down' ? '#00ff88' : '#888'
          const arrow = extra.change > 0 ? '↑' : '↓'
          tip += `<br/><span style="color:${color}">支出较上期: ${arrow} ${sign}${extra.change.toFixed(2)} 万元</span>`
        } else {
          tip += `<br/><span style="color:#888">支出较上期: ― 0.00 万元</span>`
        }
        return tip
      }
    },
    grid: { left: '3%', right: '8%', bottom: '8%', top: '5%', containLabel: true },
    xAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: '#6b8a9e', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.06)' } }
    },
    yAxis: {
      type: 'category',
      data: data.map(d => d.name).reverse(),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: '#e8f4f8',
        fontSize: 13,
        fontWeight: 500
      }
    },
    series: [{
      type: 'bar',
      data: data.map(d => d.value).reverse(),
      label: {
        show: true,
        position: 'right',
        formatter: function(params) {
          const extra = data.find(d => d.name === params.name)
          if (!extra || extra.change === null || extra.change === undefined || extra.change === 0) {
            return '― 0.0'
          }
          const sign = extra.change > 0 ? '+' : ''
          const arrow = extra.change > 0 ? '↑' : '↓'
          return arrow + ' ' + sign + extra.change.toFixed(1)
        },
        color: function(params) {
          const extra = data.find(d => d.name === params.name)
          if (!extra || extra.change === null || extra.change === undefined || extra.change === 0) return '#888'
          return extra.changeType === 'up' ? '#ff4444' : '#00ff88'
        },
        fontSize: 11
      },
      itemStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 1, y2: 0,
          colorStops: [
            { offset: 0, color: '#00d4ff' },
            { offset: 1, color: '#00ff88' }
          ]
        },
        borderRadius: [0, 8, 8, 0]
      },
      barWidth: 18,
      showBackground: true,
      backgroundStyle: {
        color: 'rgba(0, 212, 255, 0.04)',
        borderRadius: [0, 8, 8, 0]
      }
    }]
  }

  barChartInstance.setOption(option)
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  if (!historyRecords.value.length) {
    loadHistoryList()
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  progressChartInstance?.dispose()
  barChartInstance?.dispose()
})
</script>

<style scoped>
.dashboard {
  max-width: 1440px;
  margin: 0 auto;
}

/* ===== 上传区域 ===== */
.upload-section {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 200px);
  padding: 60px 0;
}

.upload-container {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
}

.upload-glow {
  position: absolute;
  width: 500px;
  height: 500px;
  border-radius: 50%;
  pointer-events: none;
  animation: glow-rotate 15s linear infinite;
}

.upload-glow-1 {
  background: radial-gradient(circle, rgba(0, 212, 255, 0.12) 0%, transparent 60%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.upload-glow-2 {
  background: radial-gradient(circle, rgba(0, 255, 136, 0.08) 0%, transparent 50%);
  width: 300px;
  height: 300px;
  animation-direction: reverse;
  animation-duration: 20s;
}

@keyframes glow-rotate {
  0% { transform: translate(-50%, -50%) rotate(0deg); }
  100% { transform: translate(-50%, -50%) rotate(360deg); }
}

.target-card {
  position: relative;
  width: 400px;
  background: linear-gradient(145deg, rgba(12, 20, 40, 0.98) 0%, rgba(8, 14, 28, 0.99) 100%);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 28px;
  padding: 48px 40px;
  text-align: center;
  backdrop-filter: blur(30px);
  box-shadow:
    0 0 60px rgba(0, 212, 255, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.target-card::before {
  content: '';
  position: absolute;
  top: -1px;
  left: 20%;
  right: 20%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #00d4ff, transparent);
  border-radius: 2px;
}

.target-header {
  margin-bottom: 32px;
}

.target-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  color: #00d4ff;
  animation: icon-pulse 3s ease-in-out infinite;
}

@keyframes icon-pulse {
  0%, 100% {
    filter: drop-shadow(0 0 10px rgba(0, 212, 255, 0.5));
    transform: scale(1);
  }
  50% {
    filter: drop-shadow(0 0 25px rgba(0, 212, 255, 0.8));
    transform: scale(1.05);
  }
}

.target-icon svg {
  width: 100%;
  height: 100%;
}

.target-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.02em;
}

.target-input-group {
  margin-bottom: 28px;
}

.input-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 212, 255, 0.03);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 14px;
  transition: all 0.3s;
}

.input-wrap:focus-within {
  border-color: #00d4ff;
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.15);
}

.input-wrap input {
  flex: 1;
  width: 100%;
  background: transparent;
  border: none;
  padding: 18px 20px;
  font-size: 24px;
  font-family: 'Orbitron', monospace;
  font-weight: 600;
  color: var(--text-primary);
  outline: none;
  text-align: center;
  text-align-last: center;
  box-sizing: border-box;
  appearance: none;
  -webkit-appearance: none;
}

.input-wrap input::placeholder {
  color: var(--text-dim);
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 16px;
  font-weight: 400;
  text-align: center;
  width: 100%;
}

.input-wrap .unit {
  padding-right: 20px;
  font-size: 16px;
  color: var(--text-secondary);
}

.upload-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  padding: 16px 24px;
  background: linear-gradient(135deg, #00d4ff 0%, #00ff88 100%);
  border: none;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 600;
  color: #050810;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 20px rgba(0, 212, 255, 0.3);
}

.upload-btn svg {
  width: 20px;
  height: 20px;
}

.upload-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 212, 255, 0.4);
}

.upload-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.upload-hint {
  margin-top: 16px;
  font-size: 13px;
  color: var(--text-dim);
}

/* ===== 数据展示 ===== */
.data-section {
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
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
  background: rgba(0, 212, 255, 0.08);
  border: 1px solid rgba(0, 212, 255, 0.2);
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
  background: linear-gradient(145deg, rgba(12, 20, 40, 0.9) 0%, rgba(10, 16, 32, 0.95) 100%);
  border: 1px solid rgba(0, 212, 255, 0.12);
  border-radius: 20px;
  padding: 28px 20px;
  text-align: center;
  overflow: hidden;
  animation: slideUp 0.5s ease both;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.metric-glow {
  position: absolute;
  bottom: -40%;
  left: 50%;
  transform: translateX(-50%);
  width: 180px;
  height: 120px;
  border-radius: 50%;
  filter: blur(40px);
  opacity: 0.25;
  pointer-events: none;
}

.metric-glow.blue { background: #00d4ff; }
.metric-glow.purple { background: #7b5cff; }
.metric-glow.orange { background: #ff9500; }
.metric-glow.green { background: #00ff88; }
.metric-glow.red { background: #ff4444; }

.metric-label {
  font-size: 11px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.1em;
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
.metric-value.red { color: #ff4444; }

.metric-value-row {
  display: flex;
  align-items: flex-end;
  gap: 6px;
}

.metric-value-unit {
  font-size: 12px;
  color: var(--text-dim);
  position: relative;
  transform: translateY(-2px);
}

.metric-meta-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 24px;
}

.metric-inline-note {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 600;
  position: relative;
}

.metric-badge {
  display: inline-flex;
  align-items: center;
  margin-top: 8px;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  position: relative;
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

/* ===== 主进度区域 ===== */
.main-progress-section {
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

/* 进度仪表卡 */
.progress-gauge-card {
  background: linear-gradient(145deg, rgba(12, 20, 40, 0.95) 0%, rgba(10, 16, 32, 0.98) 100%);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 24px;
  padding: 32px;
  box-shadow: 0 0 40px rgba(0, 212, 255, 0.05);
}

.gauge-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.gauge-header h3 {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
}

.target-badge {
  display: flex;
  align-items: baseline;
  gap: 4px;
  padding: 8px 16px;
  background: rgba(0, 212, 255, 0.08);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 20px;
}

.target-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.target-value {
  font-size: 18px;
  font-weight: 700;
  font-family: 'Orbitron', monospace;
  color: #00d4ff;
}

.target-unit {
  font-size: 11px;
  color: var(--text-secondary);
}

.gauge-container {
  position: relative;
  display: flex;
  justify-content: center;
  padding: 16px 0;
}

.gauge-chart {
  width: 320px;
  height: 280px;
}

.gauge-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -45%);
  text-align: center;
}

.gauge-value {
  font-size: 48px;
  font-weight: 700;
  font-family: 'Orbitron', monospace;
  color: var(--text-primary);
  line-height: 1;
  text-shadow: 0 0 30px rgba(0, 212, 255, 0.5);
}

.gauge-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 8px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.gauge-details {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 32px;
  padding-top: 24px;
  border-top: 1px solid rgba(0, 212, 255, 0.08);
}

.gauge-stat {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon svg {
  width: 20px;
  height: 20px;
}

.stat-icon.completed {
  background: rgba(0, 212, 255, 0.15);
  color: #00d4ff;
}

.stat-icon.remaining {
  background: rgba(255, 149, 0, 0.15);
  color: #ff9500;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 11px;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  font-family: 'Orbitron', monospace;
  color: var(--text-primary);
}

.stat-value.highlight { color: #00d4ff; }
.stat-value.warning { color: #ff9500; }
.stat-value.green { color: #00ff88; }

.stat-unit {
  font-size: 11px;
  color: var(--text-secondary);
}

.gauge-divider {
  width: 1px;
  height: 48px;
  background: linear-gradient(180deg, transparent, rgba(0, 212, 255, 0.3), transparent);
}

/* 排名卡 */
.rank-card {
  background: linear-gradient(145deg, rgba(12, 20, 40, 0.95) 0%, rgba(10, 16, 32, 0.98) 100%);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 24px;
  padding: 32px;
  box-shadow: 0 0 40px rgba(0, 212, 255, 0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.card-header h3 {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
}

.rank-hint {
  font-size: 12px;
  color: var(--text-dim);
}

.bar-chart {
  height: calc(100% - 60px);
  min-height: 300px;
}

/* ===== 表格 ===== */
.table-card {
  background: linear-gradient(145deg, rgba(12, 20, 40, 0.95) 0%, rgba(10, 16, 32, 0.98) 100%);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 24px;
  padding: 32px;
  margin-bottom: 24px;
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
  padding: 16px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  border-bottom: 1px solid rgba(0, 212, 255, 0.1);
}

.data-table td {
  padding: 18px 16px;
  font-size: 14px;
  color: var(--text-primary);
  border-bottom: 1px solid rgba(0, 212, 255, 0.04);
}

.data-table tbody tr {
  transition: background 0.2s;
}

.data-table tbody tr:hover {
  background: rgba(0, 212, 255, 0.03);
}

.data-table tbody tr.is-top {
  background: rgba(0, 212, 255, 0.05);
}

.rank-cell { width: 50px; }

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: rgba(0, 212, 255, 0.08);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.rank-badge.top {
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.2), rgba(0, 255, 136, 0.2));
  border-color: #00d4ff;
  color: #00d4ff;
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.3);
}

.manager-name { font-weight: 600; }

.value-highlight { color: #00ff88; font-weight: 600; }
.value-warning { color: #ff9500; font-weight: 600; }

.rate-badge {
  display: inline-block;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
}

.rate-badge.success { background: rgba(0, 255, 136, 0.15); color: #00ff88; }
.rate-badge.normal { background: rgba(0, 212, 255, 0.15); color: #00d4ff; }
.rate-badge.warning { background: rgba(255, 149, 0, 0.15); color: #ff9500; }
.rate-badge.danger { background: rgba(255, 68, 68, 0.15); color: #ff4444; }

.change-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-family: 'Orbitron', monospace;
  font-size: 13px;
  font-weight: 500;
}

.change-cell.change-up { color: #ff4444; }
.change-cell.change-down { color: #00ff88; }
.change-cell.no-change { color: #888; }

/* ===== 重新上传 ===== */
.reupload-bottom {
  text-align: center;
  padding: 24px;
}

.reupload-bottom button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 28px;
  background: transparent;
  border: 1px solid rgba(0, 212, 255, 0.25);
  color: #00d4ff;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.reupload-bottom button svg {
  width: 18px;
  height: 18px;
}

.reupload-bottom button:hover {
  background: rgba(0, 212, 255, 0.08);
  border-color: #00d4ff;
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
  border-top-color: #00d4ff;
  border-radius: 50%;
  animation: spin 1.2s linear infinite;
}

.loader-ring:nth-child(2) {
  inset: 8px;
  border-top-color: #00ff88;
  animation-delay: 0.15s;
  animation-direction: reverse;
}

.loader-ring:nth-child(3) {
  inset: 16px;
  border-top-color: #7b5cff;
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
@media (max-width: 1100px) {
  .main-progress-section {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .metrics-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .metrics-row {
    grid-template-columns: 1fr;
  }

  .target-card {
    width: 100%;
    padding: 36px 24px;
  }
}

/* ===== 明细弹窗 ===== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(5, 8, 16, 0.85);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(8px);
  animation: fadeIn 0.2s ease;
}

.modal-container {
  width: 95%;
  max-width: 1200px;
  max-height: 85vh;
  background: linear-gradient(145deg, rgba(12, 20, 40, 0.98) 0%, rgba(8, 14, 28, 0.99) 100%);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 24px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 0 60px rgba(0, 212, 255, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.1);
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
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
  background: rgba(255, 68, 68, 0.15);
  border-color: rgba(255, 68, 68, 0.3);
  color: #ff4444;
}

.modal-close svg {
  width: 18px;
  height: 18px;
}

.modal-body {
  flex: 1;
  overflow: auto;
  padding: 20px 28px;
}

.modal-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px;
}

.modal-loading .loader-ring {
  width: 48px;
  height: 48px;
  border: 3px solid transparent;
  border-top-color: #00d4ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.modal-empty {
  text-align: center;
  padding: 60px;
  color: var(--text-dim);
}

.detail-table {
  width: 100%;
  border-collapse: collapse;
}

.detail-table th {
  text-align: left;
  padding: 14px 16px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  border-bottom: 1px solid rgba(0, 212, 255, 0.1);
  white-space: nowrap;
}

.detail-table th.sortable {
  cursor: pointer;
  user-select: none;
  transition: color 0.2s;
}

.detail-table th.sortable:hover {
  color: #00d4ff;
}

.sort-icon {
  margin-left: 6px;
  font-size: 10px;
  opacity: 0.5;
}

.sort-icon.active {
  opacity: 1;
  color: #00d4ff;
}

.detail-table td {
  padding: 16px;
  font-size: 13px;
  color: var(--text-primary);
  border-bottom: 1px solid rgba(0, 212, 255, 0.04);
}

.detail-table tbody tr:hover {
  background: rgba(0, 212, 255, 0.03);
}

.manager-name.clickable {
  cursor: pointer;
  color: #00d4ff;
  font-weight: 600;
  transition: color 0.2s;
}

.manager-name.clickable:hover {
  color: #00ff88;
  text-decoration: underline;
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
.target-card,
.section-header-rich,
.metric-card,
.progress-gauge-card,
.rank-card,
.table-card {
  box-shadow: 0 28px 70px rgba(0, 0, 0, 0.22);
}

.upload-copy {
  position: relative;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 38px;
  background: linear-gradient(180deg, rgba(9, 20, 36, 0.92), rgba(11, 20, 38, 0.78));
  border: 1px solid rgba(103, 223, 255, 0.13);
  border-radius: 30px;
  overflow: hidden;
}

.upload-copy-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.upload-copy::before {
  content: '';
  position: absolute;
  inset: auto -10% -30% auto;
  width: 280px;
  height: 280px;
  background: radial-gradient(circle, rgba(103, 223, 255, 0.18), transparent 68%);
  pointer-events: none;
}

.upload-copy p {
  max-width: 54ch;
  margin-bottom: 20px;
  font-size: 14px;
  line-height: 1.75;
  color: var(--text-secondary);
}

.inline-target-card {
  margin-top: auto;
  padding: 18px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.035);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.inline-target-header {
  margin-bottom: 14px;
}

.inline-target-header h3 {
  font-size: 18px;
  color: var(--text-primary);
}

.upload-box {
  width: 100%;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 42px 34px;
  background: linear-gradient(180deg, rgba(9, 20, 36, 0.92), rgba(11, 20, 38, 0.78));
  border: 1px solid rgba(103, 223, 255, 0.13);
  border-radius: 30px;
  text-align: center;
  position: relative;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.upload-box::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(103, 223, 255, 0.04) 0%, transparent 50%);
  opacity: 0;
  transition: opacity 0.3s;
}

.upload-box:hover {
  border-color: rgba(103, 223, 255, 0.42);
  transform: translateY(-4px);
  box-shadow: 0 20px 60px rgba(103, 223, 255, 0.14);
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
  color: rgba(103, 223, 255, 0.72);
  transition: all 0.3s;
}

.upload-box:hover .upload-icon {
  color: var(--accent-cyan);
  filter: drop-shadow(0 0 20px rgba(103, 223, 255, 0.45));
}

.upload-glow {
  position: absolute;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(103, 223, 255, 0.08) 0%, transparent 70%);
  pointer-events: none;
  animation: glow-pulse 4s ease-in-out infinite;
}

@keyframes glow-pulse {
  0%, 100% { opacity: 0.5; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1.08); }
}

.upload-ring {
  position: absolute;
  inset: -8px;
  border: 2px dashed rgba(103, 223, 255, 0.24);
  border-radius: 50%;
  animation: rotate 20s linear infinite;
}

@keyframes rotate {
  to { transform: rotate(360deg); }
}

.upload-box h2 {
  font-size: 24px;
  margin-bottom: 10px;
  color: var(--text-primary);
}

.file-types {
  display: flex;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 22px;
}

.file-tag {
  padding: 4px 12px;
  background: rgba(103, 223, 255, 0.09);
  border: 1px solid rgba(103, 223, 255, 0.16);
  border-radius: 999px;
  font-size: 11px;
  color: var(--accent-cyan);
  font-weight: 500;
}

.upload-hint {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 20px;
}

.upload-hint .link {
  color: var(--accent-cyan);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.section-header-rich {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  padding: 28px 30px;
  margin-bottom: 24px;
  background: linear-gradient(180deg, rgba(8, 18, 33, 0.9), rgba(8, 18, 33, 0.68));
  border: 1px solid rgba(103, 223, 255, 0.12);
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
  color: var(--text-secondary);
  line-height: 1.75;
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
  border: 1px solid rgba(255, 182, 92, 0.18);
  background: rgba(255, 182, 92, 0.1);
  color: #ffd7a0;
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
  border: 1px solid rgba(103, 223, 255, 0.18);
  background: rgba(103, 223, 255, 0.06);
  color: var(--text-primary);
  cursor: pointer;
  transition: 0.25s ease;
}

.ghost-action:hover {
  background: rgba(103, 223, 255, 0.12);
}

.ghost-action svg {
  width: 16px;
  height: 16px;
}

.compare-section {
  margin-bottom: 22px;
  padding: 24px;
  border-radius: 28px;
  border: 1px solid rgba(103, 223, 255, 0.1);
  background: linear-gradient(180deg, rgba(8, 18, 33, 0.86), rgba(8, 18, 33, 0.68));
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

.compare-table-shell {
  margin-top: 6px;
}

.compare-table {
  margin-top: 0;
}

.delta-up {
  color: #5fe7ae;
}

.delta-down {
  color: #ff8e81;
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
  background: linear-gradient(180deg, rgba(7, 15, 28, 0.96), rgba(9, 18, 34, 0.98));
  border-left: 1px solid rgba(103, 223, 255, 0.14);
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
  border: 1px solid rgba(103, 223, 255, 0.1);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
  transition: 0.22s ease;
}

.history-item:hover,
.history-item.active {
  border-color: rgba(103, 223, 255, 0.28);
  background: rgba(103, 223, 255, 0.08);
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
  color: var(--accent-cyan);
  background: rgba(103, 223, 255, 0.1);
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

.metrics-row {
  gap: 18px;
  margin-bottom: 18px;
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

.alerts-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 22px;
}

.alert-pill {
  padding: 16px 18px;
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.02));
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.alert-title {
  display: block;
  margin-bottom: 10px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.alert-pill strong {
  font-size: 15px;
  color: var(--text-primary);
}

.main-progress-section {
  grid-template-columns: minmax(360px, 430px) minmax(0, 1fr);
  gap: 20px;
}

.progress-gauge-card,
.rank-card,
.table-card {
  border-radius: 28px;
  border-color: rgba(103, 223, 255, 0.1);
}

.card-header h3,
.gauge-header h3 {
  letter-spacing: 0.02em;
}

@media (max-width: 1180px) {
  .upload-container {
    grid-template-columns: 1fr;
  }

  .section-header-rich {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-main,
  .header-side {
    justify-content: flex-start;
  }

  .alerts-strip {
    grid-template-columns: 1fr;
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
  .target-card,
  .section-header-rich,
  .progress-gauge-card,
  .rank-card,
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

  .header-main,
  .header-side {
    width: 100%;
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

.upload-section {
  display: block !important;
  min-height: auto !important;
  padding: 0 !important;
  margin-top: -14px !important;
}

.upload-shell,
.data-section {
  max-width: 1160px;
  margin: 0 auto;
}

.upload-shell {
  max-width: 860px !important;
  width: 100% !important;
}

.data-section {
  display: grid;
  gap: 10px;
}

.upload-copy,
.upload-box,
.progress-gauge-card,
.rank-card,
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

.upload-page-header {
  margin-bottom: 2px;
  text-align: left !important;
}

.upload-page-header-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.back-to-dashboard-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border-radius: 8px;
  border: 1px solid #d8d5cc;
  background: #fff;
  color: #5f5b53;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: 0.15s;
  font-family: inherit;
  flex-shrink: 0;
}
.back-to-dashboard-btn:hover {
  background: #f0efe9;
  color: #1c1b18;
}
.back-to-dashboard-btn svg {
  width: 14px;
  height: 14px;
}

.upload-page-header h1 {
  font-size: 18px;
  font-weight: 500;
  color: #1c1b18;
  margin-bottom: 3px;
}

.upload-page-header p {
  font-size: 13px;
  color: #a8a79f;
}

.upload-container {
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) !important;
  gap: 16px !important;
  margin-bottom: 18px !important;
}

.upload-copy,
.upload-box {
  border-radius: 10px !important;
  padding: 18px 18px 16px !important;
}

.upload-copy-top {
  margin-bottom: 18px !important;
  justify-content: flex-start !important;
}

.panel-kicker {
  margin-bottom: 0 !important;
  line-height: 1 !important;
}

.inline-target-card {
  margin-top: 0 !important;
  padding: 0 !important;
  border: none !important;
  background: transparent !important;
}

.inline-target-header h3 {
  font-size: 16px !important;
  font-weight: 500 !important;
  color: #1c1b18 !important;
  margin-bottom: 18px !important;
  text-align: left !important;
  line-height: 1.2 !important;
}

.target-inline-form {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 18px;
}

.target-label {
  font-size: 13px;
  color: #6b6a63;
  white-space: nowrap;
}

.input-wrap {
  flex: 1;
  min-height: 44px;
  border-radius: 6px !important;
  overflow: hidden;
}

.input-wrap input {
  font-size: 14px !important;
  font-family: 'IBM Plex Mono', monospace !important;
  text-align: left !important;
  padding: 8px 12px !important;
}

.input-wrap .unit {
  padding: 0 12px !important;
  font-size: 13px !important;
  font-family: 'IBM Plex Mono', monospace !important;
  border-left: 0.5px solid #e4e3dc !important;
  background: #f0efe9 !important;
}

.confirm-btn {
  height: 44px;
  padding: 0 16px;
  border: none;
  border-radius: 6px;
  background: #1f1c17;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.target-divider {
  height: 0.5px;
  background: #e4e3dc;
  margin-bottom: 18px;
}

.upload-checklist {
  display: grid;
  gap: 12px;
}

.check-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: #5e5a52;
  font-size: 13px;
  line-height: 1.5;
}

.check-icon {
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  background: #ebf2fc;
  color: #1a56a4;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
  margin-top: 1px;
}

.upload-box {
  display: flex !important;
  flex-direction: column !important;
  overflow: hidden !important;
}

.upload-zone {
  flex: 1;
  border: 1.5px dashed #d0cfc6;
  border-radius: 8px;
  margin: 12px 12px 0;
  padding: 28px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
  background: #f6f5f2;
  min-height: 204px;
}

.upload-zone:hover {
  border-color: #1a56a4;
  background: #ebf2fc;
}

.upload-glow {
  display: none !important;
}

.upload-icon-wrap {
  width: 34px !important;
  height: 34px !important;
  margin: 0 auto 14px !important;
}

.upload-icon {
  width: 34px !important;
  height: 34px !important;
  color: #a8a79f !important;
}

.upload-ring {
  display: none !important;
}

.upload-box h2 {
  font-size: 16px !important;
  font-weight: 500 !important;
  line-height: 1.5 !important;
  margin-bottom: 4px !important;
}

.upload-hint {
  font-size: 12px !important;
  color: #a8a79f !important;
  margin-bottom: 12px !important;
}

.file-types {
  margin-bottom: 0 !important;
}

.upload-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
  margin-top: auto;
  padding: 12px 12px 10px;
}

.upload-feedback {
  width: 100%;
  margin-top: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.5;
}

.upload-feedback.info {
  background: rgba(17, 94, 89, 0.08);
  color: #0f766e;
  border: 1px solid rgba(15, 118, 110, 0.18);
}

.upload-feedback.error {
  background: rgba(220, 38, 38, 0.08);
  color: #b91c1c;
  border: 1px solid rgba(185, 28, 28, 0.18);
}

.upload-last {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #a8a79f;
  font-size: 12px;
}

.upload-last strong {
  color: #6b6a63;
  font-size: 12px;
  font-family: 'IBM Plex Mono', monospace;
}

.upload-submit-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 34px;
  padding: 0 18px;
  border: none;
  border-radius: 6px;
  background: #d0cfc6;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: not-allowed;
}

.upload-submit-btn.ready {
  background: #1c1b18;
  cursor: pointer;
}

.upload-submit-btn.ready:hover {
  background: #2d2d2a;
}

.auto-upload-tip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 6px;
  background: #f0efe9;
  color: #8a867f;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.selected-file-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #d1fae5;
  border-radius: 8px;
  padding: 12px 16px;
  margin-top: auto;
  width: 100%;
}

.selected-file-copy {
  flex: 1;
  min-width: 0;
}

.selected-file-name {
  font-size: 12px;
  font-weight: 500;
  color: #047857;
  font-family: 'IBM Plex Mono', monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.selected-file-meta {
  font-size: 11px;
  color: #a8a79f;
  margin-top: 2px;
}

.selected-file-change {
  font-size: 11px;
  color: #a8a79f;
  cursor: pointer;
  padding: 3px 7px;
  border-radius: 4px;
  border: 0.5px solid #e4e3dc;
  background: #fff;
}

.recent-uploads-card {
  background: #fff;
  border: 0.5px solid #e4e3dc;
  border-radius: 10px;
  padding: 14px 16px;
  margin-top: 0 !important;
}

.recent-uploads-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.recent-uploads-head h3 {
  font-size: 11px;
  font-weight: 500;
  color: #6b6a63;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.view-all-btn {
  background: transparent;
  border: none;
  color: #1a56a4;
  font-size: 11px;
  cursor: pointer;
}

.recent-uploads-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.recent-upload-item {
  border: 0.5px solid #e4e3dc;
  border-radius: 7px;
  background: #f6f5f2;
  padding: 10px 12px;
  text-align: left;
  cursor: pointer;
  transition: all 0.15s;
}

.recent-upload-item:hover {
  border-color: #d0cfc6;
  background: #fff;
}

.recent-upload-date {
  font-size: 11px;
  font-weight: 500;
  color: #1c1b18;
  margin-bottom: 3px;
  font-family: 'IBM Plex Mono', monospace;
}

.recent-upload-value {
  font-size: 12px;
  font-weight: 500;
  color: #245db0;
  margin-bottom: 2px;
  font-family: 'IBM Plex Mono', monospace;
}

.recent-upload-value span {
  font-size: 12px;
  font-family: 'IBM Plex Sans', 'Noto Sans SC', sans-serif;
}

.recent-upload-meta {
  font-size: 10px;
  color: #a8a79f;
}

.upload-copy,
.upload-box,
.history-panel,
.history-item {
  color: #1c1b18 !important;
}

.panel-kicker,
.upload-copy p,
.metric-label,
.metric-unit,
.date-badge,
.record-count,
.rank-hint {
  color: #6b6a63 !important;
}

.upload-copy h3,
.upload-box h2,
.history-panel-header h3,
.history-item-top strong,
.history-item-id {
  color: #1c1b18 !important;
}

.upload-copy p,
.upload-hint,
.history-panel-header p,
.history-item-meta,
.input-wrap .unit,
.input-wrap input::placeholder {
  color: #6b6a63 !important;
}

.file-tag,
.panel-kicker,
.upload-hint .link {
  color: #1a56a4 !important;
}

.file-tag {
  background: #eef3fb !important;
  border-color: #d9e4f4 !important;
}

.input-wrap {
  background: #f8f6f1 !important;
  border-color: #ddd8cd !important;
}

.input-wrap input {
  color: #1c1b18 !important;
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

.header-side {
  gap: 10px !important;
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
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8) !important;
  text-align: left !important;
}

.metric-card > .metric-label,
.metric-card > .metric-value-row,
.metric-card > .metric-meta-row {
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
  margin-top: 0 !important;
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
  transform: none !important;
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

.metric-value.blue {
  color: #245db0 !important;
}

.metric-value.purple {
  color: #6a39d7 !important;
}

.metric-value.orange {
  color: #bb5a08 !important;
}

.metric-value.green {
  color: #047857 !important;
}

.metric-value.red {
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

.alerts-strip {
  display: none !important;
}

.main-progress-section {
  grid-template-columns: 1fr 1fr !important;
  gap: 10px !important;
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
  font-size: 15px;
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
  display: flex;
  align-items: center;
  gap: 5px;
}

.target-edit-btn {
  display: inline-flex;
  align-items: center;
  padding: 2px;
  border: none;
  background: transparent;
  color: #c8c6be;
  cursor: pointer;
  border-radius: 3px;
  transition: color 0.15s;
}

.target-edit-btn:hover { color: #6b6a63; }

.target-edit-btn svg {
  width: 11px;
  height: 11px;
}

.target-edit-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.target-edit-input {
  width: 72px;
  height: 22px;
  padding: 0 6px;
  border: 1px solid #b8cef5;
  border-radius: 4px;
  background: #eff4ff;
  color: #1c1b18;
  font-size: 11px;
  font-family: 'IBM Plex Mono', monospace;
  outline: none;
}

.target-edit-input:focus { border-color: #2563eb; }

.target-edit-unit {
  font-size: 11px;
  color: #9b9790;
}

.target-edit-save,
.target-edit-cancel {
  height: 22px;
  width: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  border: none;
  font-size: 11px;
  cursor: pointer;
  transition: background 0.15s;
}

.target-edit-save {
  background: #2563eb;
  color: #fff;
}

.target-edit-save:hover:not(:disabled) { background: #1d4ed8; }
.target-edit-save:disabled { opacity: 0.5; cursor: not-allowed; }

.target-edit-cancel {
  background: #e4e3dc;
  color: #5f5b53;
}

.target-edit-cancel:hover { background: #d0cfc6; }

.progress-remaining {
  font-size: 12px;
  font-weight: 700;
  color: #b45309;
  font-family: 'IBM Plex Mono', monospace;
}

.progress-remaining.exceeded {
  color: #047857;
}

.gauge-header h3,
.card-header h3 {
  color: #1c1b18 !important;
  font-size: 15px !important;
}

.gauge-chart,
.bar-chart {
  background: #fff;
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

.rank-badge {
  width: 26px !important;
  height: 26px !important;
  font-size: 12px !important;
}

.rate-badge {
  padding: 4px 10px !important;
  font-size: 11px !important;
}

.change-cell {
  font-size: 11px !important;
}

.manager-name.clickable {
  color: #1a56a4 !important;
}

.history-overlay {
  background: rgba(28, 27, 24, 0.25) !important;
}

.history-panel {
  background: #fff !important;
  border-left: 1px solid #e4e3dc !important;
}

.modal-overlay {
  background: rgba(28, 27, 24, 0.25) !important;
  backdrop-filter: blur(4px) !important;
}

.modal-container {
  background: #ffffff !important;
  border: 1px solid #e4e3dc !important;
  border-radius: 16px !important;
  box-shadow: 0 18px 48px rgba(28, 27, 24, 0.14) !important;
}

.modal-header {
  padding: 16px 18px !important;
  border-bottom: 1px solid #e4e3dc !important;
}

.modal-header h3 {
  color: #1c1b18 !important;
  font-size: 15px !important;
  font-weight: 700 !important;
}

.modal-close {
  background: #fff !important;
  border: 1px solid #d8d5cc !important;
  color: #5f5b53 !important;
}

.modal-close:hover {
  background: #f0efe9 !important;
  border-color: #d8d5cc !important;
  color: #1c1b18 !important;
}

.modal-body {
  padding: 12px 18px 16px !important;
  background: #fff !important;
}

.modal-loading,
.modal-empty {
  color: #6b6a63 !important;
}

.detail-table th {
  background: #f0efe9 !important;
  color: #6b6a63 !important;
  font-size: 11px !important;
  padding: 10px 12px !important;
  border-bottom: 1px solid #e4e3dc !important;
  letter-spacing: 0 !important;
  text-transform: none !important;
}

.detail-table td {
  color: #1c1b18 !important;
  font-size: 12px !important;
  padding: 10px 12px !important;
  line-height: 1.2 !important;
  border-bottom: 1px solid #f0efe9 !important;
}

.detail-table tbody tr:hover {
  background: #f8f6f1 !important;
}

.detail-table .rate-badge {
  padding: 4px 10px !important;
  font-size: 11px !important;
}

.detail-table th.sortable:hover,
.sort-icon.active {
  color: #1a56a4 !important;
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

.history-kpi-capital {
  color: #1c1b18 !important;
}

.history-kpi-capital em {
  color: #6b6a63 !important;
}

.history-kpi-progress {
  background: #eef2f8 !important;
  color: #1a56a4 !important;
}

.history-kpi-delta.delta-up { color: #15803d !important; }
.history-kpi-delta.delta-down { color: #b91c1c !important; }

.history-item-meta {
  color: #9b9790 !important;
}

@media (max-width: 980px) {
  .main-progress-section {
    grid-template-columns: 1fr !important;
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

/* 四类工程预警面板 */
.four-class-card {
  background: #fff;
  border: 1px solid #e4e3dc;
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 16px;
}

.four-class-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.four-class-title-row h3 {
  margin: 0;
  font-size: 15px;
  color: #1c1b18;
}

.four-class-subtitle {
  font-size: 11px;
  color: #8a8680;
  font-weight: normal;
  margin-left: 8px;
}

.four-class-cards-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.four-class-mini-card {
  background: #f8f6f1;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, outline-color 0.18s ease;
  outline: 1.5px solid transparent;
}

.four-class-mini-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.1);
}

.four-class-mini-card.type-liezhang { border-left: 3px solid #1F497D; }
.four-class-mini-card.type-yuzhuang { border-left: 3px solid #7B3F00; }
.four-class-mini-card.type-guanbi { border-left: 3px solid #843C0C; }
.four-class-mini-card.type-guazhang { border-left: 3px solid #244062; }

.four-class-mini-card.type-liezhang:hover { outline-color: rgba(31, 73, 125, 0.45); }
.four-class-mini-card.type-yuzhuang:hover { outline-color: rgba(123, 63, 0, 0.45); }
.four-class-mini-card.type-guanbi:hover { outline-color: rgba(132, 60, 12, 0.45); }
.four-class-mini-card.type-guazhang:hover { outline-color: rgba(36, 64, 98, 0.45); }

.mini-card-label {
  font-size: 11px;
  color: #6b6a63;
  margin-bottom: 8px;
}

.mini-card-nums {
  display: flex;
  gap: 16px;
}

.mini-card-triggered .num,
.mini-card-warning .num {
  font-size: 22px;
  font-weight: 700;
  color: #aaa;
  display: block;
}

.mini-card-triggered .num.active { color: #C00000; }
.mini-card-warning .num.active { color: #D4A800; }

.mini-card-triggered .label,
.mini-card-warning .label {
  font-size: 10px;
  color: #8a8680;
}

/* 四类工程明细弹窗 */
.four-class-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.four-class-modal {
  background: #fff;
  border-radius: 10px;
  width: 98%;
  max-width: 1400px;
  max-height: 84vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 28px 70px rgba(0, 0, 0, 0.22);
}

.four-class-modal .modal-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e4e3dc;
}

.four-class-modal .modal-title-wrap {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.four-class-modal .modal-title-wrap h3 {
  font-size: 16px;
  font-weight: 700;
  color: #1c1b18;
  margin: 0;
}

.four-class-modal .modal-date {
  font-size: 11px;
  color: #8a8680;
}

.four-class-modal .modal-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.four-class-modal .export-btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: #1a56a4;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.four-class-modal .export-btn-primary:hover {
  background: #145293;
}

.four-class-modal .export-btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.four-class-modal .export-btn-primary span {
  font-size: 14px;
}

.four-class-modal-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 1000px;
  table-layout: fixed;
}

.four-class-modal-table th {
  background: #f8f6f1;
  color: #6b6a63;
  font-weight: 600;
  font-size: 11px;
  padding: 6px 4px;
  text-align: left;
  border-bottom: 1px solid #e4e3dc;
  position: sticky;
  top: 0;
  word-break: break-word;
}

.four-class-modal-table td {
  padding: 4px 4px;
  border-bottom: 1px solid #f0efe9;
  color: #1c1b18;
  font-size: 11px;
}

.four-class-modal-table tr:hover td {
  background: #faf9f7;
}

.four-class-modal-table .col-status {
  width: 48px;
  white-space: nowrap;
}

.four-class-modal-table .col-name {
  width: 240px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.four-class-modal-table .col-accept {
  width: 64px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.four-class-modal-table .col-manager {
  width: 52px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.four-class-modal-table .col-date {
  width: 76px;
  white-space: nowrap;
  font-size: 10px;
  color: #5e5a52;
  overflow: hidden;
  text-overflow: ellipsis;
}

.four-class-modal-table .col-project-status {
  width: 100px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.four-class-modal-table .col-days {
  width: 72px;
  white-space: nowrap;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
}

.four-class-modal-table .col-days.days-overdue {
  color: #C00000;
  font-weight: 700;
}

.four-class-modal-table .col-days.days-warning {
  color: #D4A800;
  font-weight: 700;
}

.four-class-group {
  margin-bottom: 20px;
}

.four-class-group .group-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 10px;
  border-radius: 4px;
  margin-bottom: 6px;
}

.four-class-group.group-liezhang .group-header { background: #DCE6F1; color: #1F497D; }
.four-class-group.group-yuzhuang .group-header { background: #FEF3E8; color: #7B3F00; }
.four-class-group.group-guanbi .group-header { background: #FFF0E5; color: #843C0C; }
.four-class-group.group-guazhang .group-header { background: #DDE8F0; color: #244062; }

.group-title {
  font-weight: 700;
  font-size: 13px;
}

.group-count {
  font-size: 11px;
  opacity: 0.8;
}

.four-class-modal-table .col-suggestion {
  color: #6b6a63;
  font-size: 11px;
  white-space: normal;
  line-height: 1.4;
  width: 140px;
  word-break: break-word;
}

.four-class-modal-table .status-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
}

.four-class-modal-table .status-tag.已触发,
.four-class-modal-table .row-已触发 td {
  background: rgba(192, 0, 0, 0.06);
  color: #C00000;
}

.four-class-modal-table .status-tag.已触发\(超期完成\),
.four-class-modal-table .row-已触发\(超期完成\) td {
  background: rgba(255, 153, 0, 0.06);
  color: #ED7D31;
}

.four-class-modal-table .status-tag.预警,
.four-class-modal-table .row-预警 td {
  color: #7B5200;
}

@media (max-width: 900px) {
  .four-class-cards-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* ===== 转固率测算条 ===== */
.tp-calc-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 11px 20px;
  background: #f5f7fb;
  border-bottom: 1px solid #e4e3dc;
  flex-wrap: wrap;
}
.tp-calc-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.tp-calc-label {
  font-size: 12px;
  color: #6b6a63;
  white-space: nowrap;
  font-weight: 500;
}
.tp-calc-input-wrap {
  display: flex;
  align-items: center;
  background: #fff;
  border: 1px solid #d0cfc8;
  border-radius: 6px;
  padding: 0 10px 0 8px;
  transition: border-color 0.15s;
}
.tp-calc-input-wrap:focus-within { border-color: #1a56a4; }
.tp-calc-input {
  background: none;
  border: none;
  outline: none;
  color: #1c1b18;
  font-size: 14px;
  font-weight: 600;
  width: 58px;
  padding: 5px 4px;
  text-align: right;
}
.tp-calc-input::placeholder { color: #c0bdb6; font-weight: 400; font-size: 12px; }
.tp-calc-unit { font-size: 13px; color: #6b6a63; }
.tp-calc-clear {
  background: none;
  border: none;
  color: #c0bdb6;
  cursor: pointer;
  font-size: 11px;
  padding: 0 0 0 6px;
  line-height: 1;
}
.tp-calc-clear:hover { color: #1c1b18; }
.tp-calc-result {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  flex-wrap: wrap;
}
.tp-calc-from { color: #6b6a63; }
.tp-calc-arrow { color: #c0bdb6; }
.tp-calc-to { color: #1a56a4; font-weight: 600; }
.tp-calc-divider { color: #d0cfc8; margin: 0 2px; }
.tp-calc-desc { color: #6b6a63; }
.tp-calc-amount { color: #b45309; font-size: 14px; font-weight: 700; }
.tp-calc-achieved { color: #15803d; font-size: 13px; font-weight: 600; }
.tp-calc-hint { color: #c0bdb6; font-size: 12px; font-style: italic; }

/* 管理员 stats — 目标模式 */
.tp-stat-required { color: #b45309 !important; font-weight: 600 !important; }
.tp-stat-count { color: #1a56a4 !important; font-weight: 700 !important; }
.tp-stat-achieved { font-size: 12px; color: #15803d; font-weight: 500; }
.tp-stat-warn { color: #b91c1c !important; font-size: 12px; }

/* 必做项目行高亮 */
.tp-row-needed {
  background: #fffbeb !important;
  border-left: 2px solid #f59e0b;
}
.tp-row-optional { opacity: 0.5; }
.tp-needed-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 3px;
  background: #fef3c7;
  color: #b45309;
  font-size: 10px;
  font-weight: 700;
  margin-right: 5px;
  flex-shrink: 0;
  border: 1px solid #fde68a;
}
.tp-rank-needed {
  background: #fef3c7 !important;
  color: #b45309 !important;
  border: 1px solid #fde68a;
}

/* 分隔线行 */
.tp-divider-row td { padding: 0; border: none !important; background: transparent; }
.tp-divider-line {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 10px;
  font-size: 11px;
  color: #c0bdb6;
}
.tp-divider-line::before, .tp-divider-line::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #e4e3dc;
}

/* ===== 转固推进清单按钮 ===== */
.tp-btn {
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 5px;
  background: #fff !important;
  border: 1px solid #d8d5cc !important;
  color: #5f5b53 !important;
}
.tp-btn:hover {
  background: #f0efe9 !important;
  color: #1c1b18 !important;
}
.push-btn {
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 5px;
  color: #16a34a !important;
  border-color: rgba(22, 163, 74, 0.25) !important;
}
.push-btn:hover:not(:disabled) {
  background: rgba(22, 163, 74, 0.07) !important;
  border-color: rgba(22, 163, 74, 0.45) !important;
}
.push-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ===== 转固推进清单弹窗 ===== */
.tp-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(3px);
  z-index: 1000;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 32px 16px;
  overflow-y: auto;
}
.tp-modal {
  background: #fff;
  border: 1px solid #e4e3dc;
  border-radius: 12px;
  width: 100%;
  max-width: 1100px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.16);
  display: flex;
  flex-direction: column;
}
.tp-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 18px 24px 14px;
  border-bottom: 1px solid #e4e3dc;
}
.tp-header-left h3 {
  margin: 0 0 3px;
  font-size: 16px;
  font-weight: 700;
  color: #1c1b18;
}
.tp-subtitle {
  font-size: 12px;
  color: #8a8680;
}
.tp-header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.tp-export-btn {
  padding: 5px 14px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  background: #2563eb;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}
.tp-export-btn:hover:not(:disabled) {
  background: #1d4ed8;
}
.tp-export-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.tp-loading, .tp-empty, .tp-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: #8a8680;
  gap: 12px;
  font-size: 13px;
}
.tp-error { color: #b91c1c; }
.tp-body {
  padding: 16px 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Manager block */
.tp-manager-block {
  background: #fff;
  border: 1px solid #e4e3dc;
  border-radius: 8px;
  overflow: hidden;
}
.tp-manager-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: #f5f7fb;
  border-bottom: 1px solid #e4e3dc;
  flex-wrap: wrap;
  gap: 8px;
}
.tp-manager-name {
  font-size: 13px;
  font-weight: 700;
  color: #1c1b18;
}
.tp-manager-stats {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6b6a63;
  flex-wrap: wrap;
}
.tp-stat-item { display: flex; align-items: center; gap: 5px; }
.tp-stat-sep { color: #d0cfc8; }
.tp-target-rate { color: #15803d !important; font-weight: 700 !important; }

/* Table */
.tp-table-wrap { overflow-x: auto; }
.tp-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.tp-table th {
  padding: 7px 10px;
  text-align: left;
  font-weight: 600;
  color: #6b6a63;
  background: #f0efe9;
  white-space: nowrap;
  border-bottom: 1px solid #e4e3dc;
  font-size: 11px;
  letter-spacing: 0.02em;
}
.tp-table td {
  padding: 8px 10px;
  border-bottom: 1px solid #f0efe9;
  vertical-align: middle;
  color: #1c1b18;
  font-size: 12px;
}
.tp-row:last-child td { border-bottom: none; }
.tp-row.urgency-已逾期 { background: #fff8f8; }
.tp-row.urgency-即将到期 { background: #fffbf5; }

.tp-col-rank { width: 42px; text-align: center; }
.tp-col-name { max-width: 240px; }
.tp-col-balance, .tp-col-contrib, .tp-col-urgency, .tp-col-action { white-space: nowrap; }
.tp-col-hint { font-size: 11px; color: #8a8680; min-width: 160px; }

.tp-rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 600;
  background: #f0efe9;
  color: #8a8680;
}
.tp-rank-badge.tp-rank-top {
  background: #dbeafe;
  color: #1d4ed8;
}

/* Contribution bar */
.tp-contrib-bar-wrap {
  display: flex;
  align-items: center;
  gap: 7px;
}
.tp-contrib-bar {
  height: 5px;
  background: linear-gradient(90deg, #3b82f6, #10b981);
  border-radius: 3px;
  min-width: 4px;
  max-width: 80px;
  transition: width 0.3s;
}

/* Urgency tag */
.tp-urgency-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}
.urgency-tag-已逾期 { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.urgency-tag-即将到期 { background: #fff7ed; color: #ea580c; border: 1px solid #fed7aa; }
.urgency-tag-正常 { background: #f0efe9; color: #8a8680; border: 1px solid #e4e3dc; }

/* After-transfer rate */
.tp-after-rate { font-weight: 700; color: #15803d; margin-right: 4px; }
.tp-rate-arrow { font-size: 11px; color: #6b6a63; }

/* Hint */
.tp-hint-line { margin-bottom: 2px; }
.tp-hint-type { color: #1d4ed8; margin-right: 3px; font-weight: 500; }
.tp-hint-normal { color: #d0cfc8; }

/* Manager footer */
.tp-manager-footer {
  padding: 8px 16px;
  font-size: 12px;
  color: #6b6a63;
  border-top: 1px solid #f0efe9;
  background: #fafaf8;
}
.tp-manager-footer strong { color: #15803d; margin: 0 3px; }
</style>
