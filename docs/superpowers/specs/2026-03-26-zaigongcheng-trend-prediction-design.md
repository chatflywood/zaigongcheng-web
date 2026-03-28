# 在建工程趋势分析与预测功能设计规格

## 1. 概述

### 1.1 项目背景

zaigongcheng-web 是一个在建工程数据分析平台，目前支持按工程管理员维度的数据汇总、核心指标展示、历史版本对比。但缺乏**时间序列分析**和**预测能力**，无法直观看到月度趋势变化，也无法预判年度目标能否完成。

### 1.2 需求目标

在现有 KeyIndicators.vue 大屏页面基础上，新增两个功能区块：

1. **趋势分析区块** — 基于历史快照数据，展示月度趋势折线图
2. **预测分析区块** — 基于历史数据计算完成时间预测、资金需求预测、风险预警

### 1.3 数据来源

- **数据基础**：每次上传 Excel 时存储的 `metrics_data`（包含 capital、pending、monthSpend、rate、progress 等指标）以及 `uploaded_at` 时间戳
- **历史记录获取**：调用已有的 `/api/zaigong/history` 接口获取所有历史快照
- **数据排序**：按 `file_date`（从文件名解析的日期如 20260320）升序排列，构成时间序列

---

## 2. 功能详细设计

### 2.1 页面结构

在 KeyIndicators.vue 中新增一个 **Tab 切换**，在现有"关键指标"和新增的"趋势与预测"之间切换。

```
┌─────────────────────────────────────────────┐
│  [关键指标]  [趋势与预测]      ← Tab 切换    │
├─────────────────────────────────────────────┤
│  （当前三大仪表盘，保持不变）                  │
│                                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │立项进度 │ │资本支出 │ │转固率  │       │
│  └─────────┘ └─────────┘ └─────────┘       │
└─────────────────────────────────────────────┘
         ↓ 切换到"趋势与预测"
┌─────────────────────────────────────────────┐
│  [关键指标]  [趋势与预测]                     │
├─────────────────────────────────────────────┤
│  趋势分析区块                                │
│  ┌───────────────────────────────────────┐  │
│  │ 累计资本性支出进度趋势（折线图）         │  │
│  │ X轴：月份  Y轴：金额/进度%             │  │
│  └───────────────────────────────────────┘  │
│  ┌───────────────────────────────────────┐  │
│  │ 各月支出与待收货趋势（双Y轴折线图）      │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  预测分析区块                                │
│  ┌────────┐ ┌────────┐ ┌────────┐         │
│  │完成时间│ │资金需求│ │风险预警│         │
│  │预测卡片│ │预测卡片│ │预测卡片│         │
│  └────────┘ └────────┘ └────────┘         │
└─────────────────────────────────────────────┘
```

### 2.2 趋势分析区块

#### 2.2.1 累计资本性支出进度趋势图

- **图表类型**：带标记点的折线图
- **X 轴**：月份标签（从历史数据中提取，如"1月"、"2月"、...、"3月"）
- **Y 轴左侧**：累计资本性支出（万元），数值轴
- **Y 轴右侧**：完成进度（%），百分比轴，固定 0-100% 范围
- **数据线**：
  - 实际累计支出（实线，主色 #00d4ff）
  - 目标线（水平虚线，#ff9500），目标值固定 503 万元
- **数据点**：每个快照一个点，hover 显示具体数值
- **如果历史数据不足 2 条**：显示"数据不足，暂无法生成趋势图"提示

#### 2.2.2 各月支出与待收货趋势图

- **图表类型**：柱状 + 折线组合图
- **X 轴**：月份
- **Y 轴左侧**：本月资本性支出（柱状图，主色 #7b5cff）
- **Y 轴右侧**：已下单待收货（折线，#ff9500）
- **用途**：观察每月支出节奏和待收货压力变化

### 2.3 预测分析区块

三个预测卡片并排展示。

#### 2.3.1 完成时间预测卡片

- **标题**：预计完成时间
- **核心数值**：预测完成月份（如"预计 11 月完成"）
- **计算逻辑**：
  ```
  根据已有历史数据计算月均支出 = 最新累计支出 / 已过月份数
  预测完成月份 = 最新月份 + ceil((年度目标 - 最新累计支出) / 月均支出)
  ```
- **边界情况**：
  - 如果当前进度已 ≥ 100%：显示"已达成目标"
  - 如果月均支出 ≤ 0：显示"数据不足，无法预测"
  - 如果预测月份超出年度（如 13 月+）：显示"按当前进度，年度目标预计无法完成"

#### 2.3.2 资金需求预测卡片

- **标题**：年度资金需求
- **核心数值**：到年底仍需资本性支出（万元）
- **计算逻辑**：
  ```
  剩余目标 = 年度目标 - 最新累计支出
  预测资金需求 = max(0, 剩余目标)
  ```
- **附加信息**：显示"月均支出 XX 万元"作为参考
- **边界情况**：
  - 如果当前进度已 ≥ 100%：显示"已达成目标，暂无新增需求"

#### 2.3.3 风险预警卡片

- **标题**：风险预警
- **预警项**：按管理员维度分析，列出可能无法完成年度目标的管理员
- **计算逻辑**：
  ```
  对每个管理员：
    管理员年度目标 = 年度目标 * (管理员累计支出 / 全局累计支出)
    管理员剩余目标 = 管理员年度目标 - 管理员累计支出
    管理员月均支出 = 管理员累计支出 / 已过月份数
    预测管理员年底支出 = 管理员累计支出 + 管理员月均支出 * 剩余月份数
    如果 预测管理员年底支出 < 管理员年度目标：标记为风险
  ```
- **显示方式**：
  - 无风险：绿色状态"各管理员进度正常"
  - 有风险：显示风险管理员列表，每个显示名称 + 预计完成率 + 预警图标

### 2.4 Tab 切换逻辑

- 在 KeyIndicators.vue 页面头部新增 Tab 按钮组
- 点击 Tab 切换显示"关键指标视图"或"趋势与预测视图"
- 切换时保持已初始化的 ECharts 实例不重复初始化
- 默认显示"关键指标视图"

---

## 3. 后端接口设计

### 3.1 新增接口

#### GET `/api/zaigong/trend`

获取趋势分析所需的历史数据。

**请求参数**：
- `limit`: int, 可选，默认 12，限制返回的历史记录数量（最近 N 条）

**响应结构**：
```json
{
  "success": true,
  "data": {
    "year_target": 503.0,
    "history": [
      {
        "file_date": "202603",
        "month_label": "3月",
        "metrics": {
          "capital": 120.5,
          "pending": 35.2,
          "monthSpend": 45.0,
          "progress": 0.24,
          "rate": 0.45
        },
        "manager_summary": [
          {
            "manager": "伍建勋",
            "capital": 30.0,
            "year_target_proportion": 0.25
          }
        ]
      }
    ],
    "summary": {
      "total_records": 5,
      "date_range": {
        "start": "202603",
        "end": "202603"
      }
    }
  }
}
```

**实现要点**：
- 从 `zaigong_history` 表读取最近的 limit 条记录
- 按 `file_date` 升序排列（用于时间序列）
- 如果 `file_date` 为空，使用 `uploaded_at` 作为备选
- `month_label` 由 `file_date` 解析生成，如 "202603" → "3月"
- `manager_summary` 包含每个管理员的当月 capital 和分配的目标比例（用于风险预测计算）

### 3.2 现有接口复用

- `GET /api/zaigong/history` — 已有，用于获取历史列表
- `GET /api/zaigong/history/{id}` — 已有，用于获取单条快照详情
- `GET /api/zaigong/compare` — 已有，用于获取最新和上一条对比

---

## 4. 前端实现设计

### 4.1 组件结构

在 `KeyIndicators.vue` 中：

```
<template>
  <div class="key-indicators">
    <!-- Tab 切换 -->
    <div class="view-tabs">
      <button :class="{ active: currentView === 'overview' }" @click="switchView('overview')">关键指标</button>
      <button :class="{ active: currentView === 'trend' }" @click="switchView('trend')">趋势与预测</button>
    </div>

    <!-- 关键指标视图（现有内容） -->
    <div v-show="currentView === 'overview'" class="view-content">
      ... 现有的三大仪表盘和摘要栏 ...
    </div>

    <!-- 趋势与预测视图 -->
    <div v-show="currentView === 'trend'" class="view-content trend-view">
      <!-- 趋势分析区块 -->
      <div class="trend-section">
        <div class="chart-card">
          <h3>累计资本性支出进度趋势</h3>
          <div ref="progressTrendChart" class="chart"></div>
        </div>
        <div class="chart-card">
          <h3>月度支出与待收货趋势</h3>
          <div ref="monthlyTrendChart" class="chart"></div>
        </div>
      </div>

      <!-- 预测分析区块 -->
      <div class="prediction-section">
        <div class="prediction-card">
          <div class="pred-icon">⏱</div>
          <div class="pred-title">预计完成时间</div>
          <div class="pred-value">{{ completionPrediction }}</div>
          <div class="pred-detail">{{ completionDetail }}</div>
        </div>
        <div class="prediction-card">
          <div class="pred-icon">💰</div>
          <div class="pred-title">年度资金需求</div>
          <div class="pred-value">{{ fundRequirement }}</div>
          <div class="pred-detail">{{ fundDetail }}</div>
        </div>
        <div class="prediction-card" :class="riskClass">
          <div class="pred-icon">⚠</div>
          <div class="pred-title">风险预警</div>
          <div class="pred-value">{{ riskStatus }}</div>
          <div class="pred-detail" v-if="riskManagers.length > 0">
            <span v-for="m in riskManagers" :key="m.name">{{ m.name }} {{ m.rate }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
```

### 4.2 新增 State

```javascript
const currentView = ref('overview') // 'overview' | 'trend'
const trendData = ref(null)          // 后端返回的趋势数据
const trendLoading = ref(false)      // 加载状态
const progressTrendChart = ref(null) // 进度趋势图 DOM
const monthlyTrendChart = ref(null)  // 月度趋势图 DOM
let progressTrendInstance = null
let monthlyTrendInstance = null
```

### 4.3 数据获取逻辑

```javascript
async function fetchTrendData() {
  if (trendData.value) return // 已有数据不重复获取
  trendLoading.value = true
  try {
    const res = await fetch('/api/zaigong/trend?limit=12')
    const json = await res.json()
    if (json.success) {
      trendData.value = json.data
      nextTick(() => initTrendCharts())
    }
  } finally {
    trendLoading.value = false
  }
}

function switchView(view) {
  currentView.value = view
  if (view === 'trend') {
    fetchTrendData()
  }
}
```

### 4.4 预测计算逻辑

```javascript
// 完成时间预测
function predictCompletion() {
  const history = trendData.value?.history || []
  if (history.length < 2) return { text: '数据不足', detail: '需要至少2个月的历史数据' }

  const latest = history[history.length - 1]
  const first = history[0]
  const yearTarget = trendData.value.year_target

  // 计算已过月份数
  const latestMonth = parseInt(latest.file_date.slice(-2))
  const elapsed = latestMonth || 1

  // 月均支出
  const avgMonthly = latest.metrics.capital / elapsed

  if (avgMonthly <= 0) return { text: '无法预测', detail: '月均支出数据异常' }

  const remaining = yearTarget - latest.metrics.capital
  if (remaining <= 0) return { text: '已达成', detail: '年度目标已完成' }

  const monthsNeeded = Math.ceil(remaining / avgMonthly)
  const predictMonth = latestMonth + monthsNeeded

  if (predictMonth > 12) {
    return { text: '无法完成', detail: `按当前进度，年度目标预计${predictMonth}月完成，超出年度范围` }
  }

  return { text: `${predictMonth}月完成`, detail: `月均支出 ${avgMonthly.toFixed(2)} 万元` }
}

// 资金需求预测
function predictFundRequirement() {
  const history = trendData.value?.history || []
  if (history.length < 1) return { text: '—', detail: '' }

  const latest = history[history.length - 1]
  const yearTarget = trendData.value.year_target
  const remaining = yearTarget - latest.metrics.capital

  if (remaining <= 0) return { text: '已达成', detail: '年度目标已完成' }

  const latestMonth = parseInt(latest.file_date.slice(-2)) || 1
  const avgMonthly = latest.metrics.capital / latestMonth

  return {
    text: `${remaining.toFixed(1)} 万元`,
    detail: `月均支出 ${avgMonthly.toFixed(2)} 万元，剩余 ${(12 - latestMonth)} 个月`
  }
}

// 风险预警
function analyzeRisk() {
  const history = trendData.value?.history || []
  if (history.length < 1) return { status: '数据不足', managers: [], isRisk: false }

  const latest = history[history.length - 1]
  const latestMonth = parseInt(latest.file_date.slice(-2)) || 1
  const remaining = 12 - latestMonth

  const riskManagers = []
  const globalCapital = latest.metrics.capital
  const yearTarget = trendData.value.year_target

  for (const mgr of latest.manager_summary || []) {
    if (globalCapital <= 0) continue

    const proportion = mgr.capital / globalCapital
    const mgrTarget = yearTarget * proportion
    const avgMonthly = mgr.capital / latestMonth
    const predictYearEnd = mgr.capital + avgMonthly * remaining

    if (predictYearEnd < mgrTarget - 1) { // 留1万容差
      riskManagers.push({
        name: mgr.manager,
        rate: `${((predictYearEnd / mgrTarget) * 100).toFixed(0)}%`
      })
    }
  }

  return {
    status: riskManagers.length === 0 ? '进度正常' : `${riskManagers.length} 位风险`,
    managers: riskManagers,
    isRisk: riskManagers.length > 0
  }
}
```

---

## 5. 图表详细设计

### 5.1 进度趋势图 ECharts 配置

```javascript
{
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(10, 16, 32, 0.95)',
    borderColor: 'rgba(0, 212, 255, 0.3)',
    textStyle: { color: '#e8f4f8' }
  },
  legend: {
    data: ['累计支出', '目标线'],
    textStyle: { color: '#6b8a9e' }
  },
  grid: { left: '3%', right: '8%', bottom: '8%', top: '15%', containLabel: true },
  xAxis: {
    type: 'category',
    data: monthLabels,
    axisLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.2)' } },
    axisLabel: { color: '#6b8a9e' }
  },
  yAxis: [
    {
      type: 'value',
      name: '万元',
      axisLine: { show: false },
      axisLabel: { color: '#6b8a9e' },
      splitLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.06)' } }
    },
    {
      type: 'value',
      name: '进度%',
      max: 100,
      axisLine: { show: false },
      axisLabel: { color: '#6b8a9e' },
      splitLine: { show: false }
    }
  ],
  series: [
    {
      name: '累计支出',
      type: 'line',
      yAxisIndex: 0,
      data: capitalValues,
      smooth: true,
      lineStyle: { color: '#00d4ff', width: 3 },
      itemStyle: { color: '#00d4ff' },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(0, 212, 255, 0.3)' },
            { offset: 1, color: 'rgba(0, 212, 255, 0.02)' }
          ]
        }
      }
    },
    {
      name: '目标线',
      type: 'line',
      yAxisIndex: 0,
      data: Array(monthLabels.length).fill(yearTarget),
      lineStyle: { color: '#ff9500', width: 2, type: 'dashed' },
      symbol: 'none'
    },
    {
      name: '完成进度',
      type: 'line',
      yAxisIndex: 1,
      data: progressValues,
      smooth: true,
      lineStyle: { color: '#00ff88', width: 2 },
      itemStyle: { color: '#00ff88' },
      symbol: 'circle'
    }
  ]
}
```

### 5.2 月度趋势图 ECharts 配置

```javascript
{
  tooltip: { trigger: 'axis' },
  legend: {
    data: ['本月支出', '待收货'],
    textStyle: { color: '#6b8a9e' }
  },
  grid: { left: '3%', right: '8%', bottom: '8%', top: '15%', containLabel: true },
  xAxis: {
    type: 'category',
    data: monthLabels,
    axisLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.2)' } },
    axisLabel: { color: '#6b8a9e' }
  },
  yAxis: [
    { type: 'value', name: '万元', axisLine: { show: false }, axisLabel: { color: '#6b8a9e' }, splitLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.06)' } } },
    { type: 'value', name: '万元', axisLine: { show: false }, axisLabel: { color: '#6b8a9e' }, splitLine: { show: false } }
  ],
  series: [
    {
      name: '本月支出',
      type: 'bar',
      yAxisIndex: 0,
      data: monthSpendValues,
      itemStyle: { color: '#7b5cff', borderRadius: [4, 4, 0, 0] }
    },
    {
      name: '待收货',
      type: 'line',
      yAxisIndex: 1,
      data: pendingValues,
      smooth: true,
      lineStyle: { color: '#ff9500', width: 2 },
      itemStyle: { color: '#ff9500' }
    }
  ]
}
```

---

## 6. API 实现（后端）

### 6.1 新增 `/api/zaigong/trend` 路由

在 `backend/routers/analysis.py` 中新增：

```python
@router.get("/trend")
async def get_trend_data(limit: int = Query(12, ge=2, le=24)):
    """
    获取趋势分析数据
    - 按 file_date 升序返回最近 limit 条记录
    - 包含各月指标和按管理员维度的汇总（用于风险预测）
    """
    db = get_db()
    try:
        records = db.query(ZaigongRecord).order_by(
            ZaigongRecord.file_date.asc()
        ).limit(limit).all()

        if len(records) < 2:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "历史数据不足2条，无法生成趋势"}
            )

        history = []
        for r in records:
            summary = json.loads(r.summary_data) if r.summary_data else []
            metrics = json.loads(r.metrics_data) if r.metrics_data else {}

            # 提取各管理员数据（排除合计行）
            manager_summary = []
            for row in summary:
                mgr = row.get("工程管理员") or row.get("manager", "")
                capital = row.get("本年累计资本性支出") or row.get("capital", 0)
                if mgr and mgr != "合计":
                    manager_summary.append({
                        "manager": mgr,
                        "capital": float(capital) / 10000  # 转为万元
                    })

            # 解析月份标签
            file_date = r.file_date or ""
            if len(file_date) >= 6:
                month_label = f"{int(file_date[-2:])}月"
            else:
                month = r.uploaded_at.month
                month_label = f"{month}月"

            history.append({
                "file_date": file_date[-6:] if len(file_date) >= 6 else str(r.uploaded_at.year * 100 + r.uploaded_at.month),
                "month_label": month_label,
                "metrics": {
                    "capital": float(metrics.get("total_current", 0)),
                    "pending": float(metrics.get("total_pending", 0)),
                    "monthSpend": float(metrics.get("total_today_month", 0)),
                    "progress": float(metrics.get("progress_ratio", 0)),
                    "rate": float(metrics.get("total_rate", 0))
                },
                "manager_summary": manager_summary
            })

        # 获取年度目标（从最新记录中取）
        year_target = records[-1].target_value if records else 503.0

        return {
            "success": True,
            "data": {
                "year_target": year_target,
                "history": history,
                "summary": {
                    "total_records": len(records),
                    "date_range": {
                        "start": history[0]["file_date"] if history else None,
                        "end": history[-1]["file_date"] if history else None
                    }
                }
            }
        }
    finally:
        db.close()
```

---

## 7. 文件修改清单

| 文件 | 修改类型 | 说明 |
|------|----------|------|
| `backend/routers/analysis.py` | 新增路由 | 添加 `/api/zaigong/trend` 端点 |
| `frontend/src/views/KeyIndicators.vue` | 功能扩展 | 添加 Tab 切换、趋势图、预测分析区块 |
| `frontend/src/api/index.js` | 新增 API | 添加 `getTrendData()` 接口调用 |

---

## 8. 验收标准

1. **Tab 切换正常** — 点击"趋势与预测"Tab 可切换视图，切换后正确调用接口
2. **进度趋势图正确** — 折线图 X 轴为月份，Y 轴左侧为累计支出，右侧为完成进度%，目标线为水平虚线
3. **月度趋势图正确** — 柱状图为每月支出，折线为待收货金额
4. **完成时间预测** — 至少 2 条历史数据时显示预测月份，不足时显示提示
5. **资金需求预测** — 显示到年底还需多少资本性支出
6. **风险预警** — 按管理员维度分析，显示可能无法完成的管理员
7. **图表响应式** — 窗口 resize 时图表自适应调整
8. **风格统一** — 新增区块风格与现有大屏风格保持一致（渐变卡片、圆角、配色）
