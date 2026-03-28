# 在建工程大屏 AI 分析与重点工作 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 KeyIndicators.vue 升级为大屏展示，新增 AI 智能分析（MiniMax）和重点工作手动维护模块

**Architecture:**
- 后端：新增 `GET /api/ai/status` 与 `POST /api/ai/analyze`，调用 MiniMax API，Key 存 `.env`
- 前端：KeyIndicators.vue 新增 AI 分析区块 + 重点工作区块，localStorage 存重点工作
- AI 缓存：localStorage 缓存 AI 分析结果，使用数据快照哈希判断失效

**Tech Stack:** FastAPI + Vue3 + ECharts + localStorage + MiniMax API

---

## Task 0: 风险修正（先做）

**目标：** 先修掉当前计划中的高风险点，避免后续返工。

- [ ] **Step 1: 修正后端示例代码中的变量错误**
  - `manager_table = "\n".join(manager_lines) if manager_table else ...` 必须改成判断 `manager_lines`。
- [ ] **Step 2: 明确环境变量加载**
  - 在 `backend/main.py` 或 `backend/routers/ai.py` 中显式调用 `load_dotenv()`。
- [ ] **Step 3: 去除依赖重复**
  - `backend/requirements.txt` 仅保留一条 `httpx==0.28.1`。
- [ ] **Step 4: 增加 AI 响应解析兜底**
  - 不要假设固定返回结构，需支持多个字段路径回退。
- [ ] **Step 5: 缓存失效策略改为数据快照哈希**
  - 仅用 `uploaded_at` 或单个数值判断会误判，改为哈希关键数据字段。

---

## File Map

```
backend/
├── main.py                           # MODIFY: register ai router
├── requirements.txt                  # MODIFY: add httpx, python-dotenv
├── .env.example                      # CREATE: MiniMax env vars template
└── routers/
    ├── analysis.py                   # (no change)
    ├── budget.py                    # (no change)
    └── ai.py                        # CREATE: POST /api/ai/analyze

frontend/
└── src/
    ├── api/
    │   └── index.js                 # MODIFY: add generateAIAnalysis()
    └── views/
        └── KeyIndicators.vue        # MODIFY: major refactor - add AI + work items
```

---

## Task 1: 环境配置

**Files:**
- Create: `backend/.env.example`
- Modify: `backend/requirements.txt:1-11`

- [ ] **Step 1: Create .env.example**

Create file `backend/.env.example`:

```
# MiniMax API Configuration
MINIMAX_API_KEY=your_api_key_here
MINIMAX_GROUP_ID=your_group_id_here
MINIMAX_API_URL=https://api.minimax.chat/v1/text/chatcompletion_pro
```

- [ ] **Step 2: Update requirements.txt**

Modify `backend/requirements.txt` to add `httpx` and `python-dotenv`:

```
fastapi==0.109.0
uvicorn==0.27.0
python-multipart==0.0.6
openpyxl==3.1.2
sqlalchemy==2.0.25
httpx==0.28.1
python-dotenv==1.0.0

# 测试依赖
pytest==8.4.2
pytest-asyncio==1.2.0
```

- [ ] **Step 3: Commit**

```bash
cd /Users/liangsha/Documents/zaigongcheng-web
git add backend/.env.example backend/requirements.txt
git commit -m "chore: add MiniMax API env config and httpx dependency"
```

---

## Task 2: 后端 AI 路由

**Files:**
- Create: `backend/routers/ai.py`
- Modify: `backend/main.py:3,21-22`

- [ ] **Step 1: Create backend/routers/ai.py**

```python
# -*- coding: utf-8 -*-
"""
AI 分析路由 - 调用 MiniMax API 生成工程进度分析报告
"""
import os
import httpx
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

router = APIRouter()
load_dotenv()

# ========== Request/Response Models ==========

class ManagerSummary(BaseModel):
    manager: str
    capital: float
    pending: float
    rate: float

class MetricsInput(BaseModel):
    year_target: float
    total_current: float
    progress_pct: float
    month_spend: float
    pending: float
    transfer_rate: float

class AnalyzeRequest(BaseModel):
    metrics: MetricsInput
    summary: List[ManagerSummary]

class AnalyzeResponse(BaseModel):
    content: str
    generated_at: str
    model: str

# ========== MiniMax API Call ==========

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
MINIMAX_GROUP_ID = os.getenv("MINIMAX_GROUP_ID")
MINIMAX_API_URL = os.getenv("MINIMAX_API_URL", "https://api.minimax.chat/v1/text/chatcompletion_pro")


def build_prompt(metrics: MetricsInput, summary: List[ManagerSummary]) -> str:
    """构建发给 MiniMax 的 prompt"""
    # 构建管理员表格
    manager_lines = []
    for m in sorted(summary, key=lambda x: x.capital, reverse=True):
        manager_lines.append(f"- {m.manager}：累计支出 {m.capital:.2f} 万元，待收货 {m.pending:.2f} 万元，转固率 {m.rate*100:.1f}%")

    manager_table = "\n".join(manager_lines) if manager_lines else "暂无管理员数据"

    prompt = f"""你是一位专业的在建工程数据分析师。请根据以下数据，生成一份结构化的工程进度分析报告。

## 数据摘要
- 年度资本性支出目标：{metrics.year_target} 万元
- 当前累计资本性支出：{metrics.total_current:.2f} 万元
- 当前完成进度：{metrics.progress_pct:.1f}%
- 本月资本性支出：{metrics.month_spend:.2f} 万元
- 已下单待收货：{metrics.pending:.2f} 万元
- 综合转固率：{metrics.transfer_rate*100:.1f}%
- 各管理员支出（按累计支出降序）：
{manager_table}

## 输出要求
请按以下6个维度输出，每行一个维度，格式如下：

**综合评估**：[1-2句话总结整体情况]
**进度评估**：[当前进度是否达标，与序时进度的差距]
**支出分析**：[支出最高/最低的管理员点评]
**转固率分析**：[转固率是否达标，点评]
**风险预警**：[列出1-3个主要风险点，如无风险则写"暂无明显风险"]
**下月预测**：[按当前月均支出预测下月累计完成情况，是否能完成月度目标]"""

    return prompt


async def call_minimax(prompt: str) -> str:
    """调用 MiniMax API，返回文本内容"""
    if not MINIMAX_API_KEY or not MINIMAX_GROUP_ID:
        raise ValueError("MiniMax API 未配置，请检查环境变量")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MINIMAX_API_KEY}"
    }

    payload = {
        "model": "abab6.5s-chat",
        "tokens_to_generate": 512,
        "messages": [
            {
                "sender_type": "USER",
                "text": prompt
            }
        ],
        "role_type": "BOT"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{MINIMAX_API_URL}?GroupId={MINIMAX_GROUP_ID}"
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        # MiniMax 返回结构提取（兼容不同返回结构）
        choices = data.get("choices") or []
        if choices:
            first = choices[0] or {}
            msg = first.get("message") or {}
            if isinstance(msg, dict) and msg.get("content"):
                return msg["content"]
            messages = first.get("messages") or []
            if messages and isinstance(messages[0], dict):
                text = messages[0].get("text")
                if text:
                    return text
        if data.get("reply"):
            return data["reply"]
        if data.get("text"):
            return data["text"]
        raise ValueError("MiniMax 返回内容为空或格式不支持")


# ========== Routes ==========

@router.post("/analyze")
async def analyze(request: AnalyzeRequest):
    """
    生成 AI 工程进度分析报告
    """
    try:
        prompt = build_prompt(request.metrics, request.summary)
        content = await call_minimax(prompt)

        return {
            "success": True,
            "data": {
                "content": content,
                "generated_at": datetime.now().isoformat(),
                "model": "abab6.5s-chat"
            }
        }
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "AI_NOT_CONFIGURED", "message": str(e)}
        )
    except httpx.HTTPStatusError as e:
        return JSONResponse(
            status_code=502,
            content={"success": False, "error": "AI_SERVICE_ERROR", "message": f"MiniMax API 调用失败: {e.response.status_code}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "INTERNAL_ERROR", "message": str(e)}
        )


@router.get("/status")
async def ai_status():
    """
    检查 AI 服务配置状态
    """
    configured = bool(MINIMAX_API_KEY and MINIMAX_GROUP_ID)
    return {
        "success": True,
        "data": {
            "configured": configured,
            "model": "abab6.5s-chat" if configured else None
        }
    }
```

- [ ] **Step 2: Modify backend/main.py**

Modify `backend/main.py` to register AI router:

Change line 3:
```python
from routers import analysis, budget, ai
```

Change lines 21-22 to add:
```python
app.include_router(analysis.router, prefix="/api/zaigong", tags=["在建工程"])
app.include_router(budget.router, prefix="/api/budget", tags=["预算分析"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI分析"])
```

- [ ] **Step 3: Test the API locally**

Run: `cd /Users/liangsha/Documents/zaigongcheng-web/backend && python -c "from routers.ai import router; print('AI router OK')"`

Expected: `AI router OK`

- [ ] **Step 4: Commit**

```bash
git add backend/routers/ai.py backend/main.py
git commit -m "feat: add AI analysis endpoint with MiniMax integration"
```

---

## Task 3: 前端 API 方法

**Files:**
- Modify: `frontend/src/api/index.js:1-59`

- [ ] **Step 1: Add generateAIAnalysis to frontend/src/api/index.js**

Add at the end of `frontend/src/api/index.js`:

```javascript
export async function generateAIAnalysis(metrics, summary) {
  const response = await axios.post(`${API_BASE}/ai/analyze`, { metrics, summary })
  return response.data
}

export async function getAIStatus() {
  const response = await axios.get(`${API_BASE}/ai/status`)
  return response.data
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/index.js
git commit -m "feat: add generateAIAnalysis and getAIStatus API methods"
```

---

## Task 4: KeyIndicators.vue - AI 分析区块

**Files:**
- Modify: `frontend/src/views/KeyIndicators.vue`

- [ ] **Step 1: Read current KeyIndicators.vue structure**

The current file is 870+ lines. We will add new state and methods while preserving existing functionality.

- [ ] **Step 2: Add AI Analysis section state and methods**

In the `<script setup>` section, add after the existing refs:

```javascript
// AI Analysis state
const aiAnalysisContent = ref('')
const aiAnalysisLoading = ref(false)
const aiAnalysisError = ref('')
const aiAnalysisGeneratedAt = ref('')
const aiCacheKey = 'ai_analysis_cache'

function getAICache() {
  try {
    const raw = localStorage.getItem(aiCacheKey)
    if (!raw) return null
    return JSON.parse(raw)
  } catch { return null }
}

function buildAISnapshotHash() {
  const metrics = props.zaigongData?.metrics || {}
  const summary = (props.zaigongData?.summary || [])
    .filter(r => (r.manager || r['工程管理员']) !== '合计')
    .map(r => ({
      manager: r.manager || r['工程管理员'],
      capital: Number(r.capital || r['本年累计资本性支出'] || 0),
      pending: Number(r.pending || r['已下单待收货'] || 0),
      rate: Number(r.rate || r['转固率'] || 0)
    }))
  return JSON.stringify({
    yearTarget: Number(metrics.yearTarget || 0),
    capital: Number(metrics.capital || 0),
    pending: Number(metrics.pending || 0),
    monthSpend: Number(metrics.monthSpend || 0),
    rate: Number(metrics.rate || 0),
    summary
  })
}

function saveAICache(content, generatedAt) {
  const cache = {
    content,
    generatedAt,
    snapshotHash: buildAISnapshotHash()
  }
  localStorage.setItem(aiCacheKey, JSON.stringify(cache))
}

function isCacheStale() {
  const cache = getAICache()
  if (!cache || !cache.snapshotHash) return true
  if (!props.zaigongData?.metrics) return false
  return cache.snapshotHash !== buildAISnapshotHash()
}

async function refreshAIAnalysis() {
  if (!props.zaigongData?.metrics) {
    aiAnalysisError.value = '请先上传数据'
    return
  }
  aiAnalysisLoading.value = true
  aiAnalysisError.value = ''
  try {
    const metrics = props.zaigongData.metrics
    const summary = (props.zaigongData.summary || [])
      .filter(r => r.manager !== '合计')
      .map(r => ({
        manager: r.manager || r['工程管理员'],
        capital: Number(r.capital || r['本年累计资本性支出'] || 0),
        pending: Number(r.pending || r['已下单待收货'] || 0),
        rate: Number(r.rate || r['转固率'] || 0)
      }))

    const result = await generateAIAnalysis({
      year_target: metrics.yearTarget || 503,
      total_current: metrics.capital || 0,
      progress_pct: (metrics.progress || 0) * 100,
      month_spend: metrics.monthSpend || 0,
      pending: metrics.pending || 0,
      transfer_rate: metrics.rate || 0
    }, summary)

    if (result.success) {
      aiAnalysisContent.value = result.data.content
      aiAnalysisGeneratedAt.value = result.data.generated_at
      saveAICache(result.data.content, result.data.generated_at)
    } else {
      aiAnalysisError.value = result.message || '生成失败'
    }
  } catch (error) {
    aiAnalysisError.value = 'AI 服务调用失败，请稍后重试'
  } finally {
    aiAnalysisLoading.value = false
  }
}

function loadAICache() {
  const cache = getAICache()
  if (cache) {
    aiAnalysisContent.value = cache.content
    aiAnalysisGeneratedAt.value = cache.generatedAt
    if (isCacheStale()) {
      aiAnalysisError.value = '数据已更新，请点击刷新'
    }
  }
}
```

- [ ] **Step 3: Add AI Analysis template section**

Add in `<template>` after the `indicators-grid` div (before `summary-bar`):

```html
<!-- AI 分析区块 -->
<div class="section-card ai-analysis-card">
  <div class="section-header">
    <div class="section-title">
      <span class="section-icon">🤖</span>
      <h3>AI 工程进度分析</h3>
    </div>
    <button class="refresh-btn" @click="refreshAIAnalysis" :disabled="aiAnalysisLoading">
      <svg v-if="aiAnalysisLoading" class="spin-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 12a9 9 0 1 1-2.64-6.36"/>
      </svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M23 4v6h-6M1 20v-6h6"/>
        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
      </svg>
      {{ aiAnalysisLoading ? '分析中...' : '刷新分析' }}
    </button>
  </div>

  <div v-if="aiAnalysisError" class="ai-error">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <circle cx="12" cy="12" r="10"/>
      <line x1="12" y1="8" x2="12" y2="12"/>
      <line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>
    {{ aiAnalysisError }}
  </div>

  <div v-else-if="!aiAnalysisContent" class="ai-empty">
    <p>点击「刷新分析」生成 AI 分析报告</p>
  </div>

  <div v-else class="ai-content">
    <div class="ai-generated-time" v-if="aiAnalysisGeneratedAt">
      生成于 {{ new Date(aiAnalysisGeneratedAt).toLocaleString('zh-CN') }}
    </div>
    <div class="ai-text" v-html="formatAIAnalysis(aiAnalysisContent)"></div>
  </div>
</div>
```

- [ ] **Step 4: Add AI Analysis formatting and CSS**

Add helper function:

```javascript
function formatAIAnalysis(text) {
  if (!text) return ''
  // 将 **标题** 格式转为 <strong>，换行转为 <br>
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}
```

Add CSS to `<style scoped>`:

```css
/* AI Analysis Section */
.section-card {
  background: linear-gradient(145deg, rgba(12, 20, 40, 0.95), rgba(10, 16, 32, 0.98));
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 28px;
  padding: 28px 32px;
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-icon {
  font-size: 24px;
}

.section-title h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 38px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid rgba(0, 212, 255, 0.3);
  background: rgba(0, 212, 255, 0.08);
  color: #00d4ff;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.25s;
}

.refresh-btn:hover:not(:disabled) {
  background: rgba(0, 212, 255, 0.15);
  border-color: rgba(0, 212, 255, 0.5);
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-btn svg {
  width: 16px;
  height: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.spin-icon {
  animation: spin 1s linear infinite;
}

.ai-error {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  background: rgba(255, 68, 68, 0.1);
  border: 1px solid rgba(255, 68, 68, 0.2);
  border-radius: 16px;
  color: #ff6b6b;
  font-size: 14px;
}

.ai-error svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.ai-empty {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
  font-size: 14px;
}

.ai-content {
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-secondary);
}

.ai-generated-time {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.08);
}

.ai-text strong {
  color: #00d4ff;
  font-weight: 600;
}
```

- [ ] **Step 5: Add onMounted to load cache**

Update the existing `onMounted` to call `loadAICache`:

```javascript
onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
  initCharts()
  loadAICache()  // NEW
  window.addEventListener('resize', handleResize)
})
```

- [ ] **Step 6: Add AI section to template (before summary-bar)**

Insert the AI section template between `indicators-grid` and `summary-bar` divs in the existing template.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/views/KeyIndicators.vue
git commit -m "feat: add AI analysis section to KeyIndicators"
```

---

## Task 5: KeyIndicators.vue - 重点工作区块

**Files:**
- Modify: `frontend/src/views/KeyIndicators.vue`

- [ ] **Step 1: Add KeyWorkItems state and methods**

Add in `<script setup>`:

```javascript
// Key Work Items state
const workItems = ref([])
const workItemsStorageKey = 'key_work_items'
const modalVisible = ref(false)
const modalMode = ref('add') // 'add' | 'edit'
const editingItem = ref(null)
const formContent = ref('')
const formOwner = ref('')
const formDueDate = ref('')
const formError = ref('')

function loadWorkItems() {
  try {
    const raw = localStorage.getItem(workItemsStorageKey)
    if (!raw) {
      workItems.value = []
      return
    }
    const items = JSON.parse(raw)
    // Sort: pending first (by dueDate asc), completed last
    const pending = items.filter(i => i.status === 'pending').sort((a, b) => a.dueDate.localeCompare(b.dueDate))
    const completed = items.filter(i => i.status === 'completed')
    workItems.value = [...pending, ...completed]
  } catch {
    workItems.value = []
  }
}

function saveWorkItems() {
  localStorage.setItem(workItemsStorageKey, JSON.stringify(workItems.value))
}

function openAddModal() {
  modalMode.value = 'add'
  editingItem.value = null
  formContent.value = ''
  formOwner.value = ''
  formDueDate.value = ''
  formError.value = ''
  modalVisible.value = true
}

function openEditModal(item) {
  modalMode.value = 'edit'
  editingItem.value = item
  formContent.value = item.content
  formOwner.value = item.owner
  formDueDate.value = item.dueDate
  formError.value = ''
  modalVisible.value = true
}

function closeModal() {
  modalVisible.value = false
}

function validateForm() {
  if (!formContent.value.trim()) {
    formError.value = '请输入工作内容'
    return false
  }
  if (!formOwner.value.trim()) {
    formError.value = '请输入责任人'
    return false
  }
  if (!formDueDate.value) {
    formError.value = '请选择完成日期'
    return false
  }
  const today = new Date().toISOString().split('T')[0]
  if (formDueDate.value < today && modalMode.value === 'add') {
    formError.value = '完成日期不能早于今天'
    return false
  }
  return true
}

function saveItem() {
  if (!validateForm()) return
  if (modalMode.value === 'add') {
    const newItem = {
      id: crypto.randomUUID(),
      content: formContent.value.trim(),
      owner: formOwner.value.trim(),
      dueDate: formDueDate.value,
      status: 'pending',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
    workItems.value.unshift(newItem)
  } else {
    const idx = workItems.value.findIndex(i => i.id === editingItem.value.id)
    if (idx !== -1) {
      workItems.value[idx] = {
        ...workItems.value[idx],
        content: formContent.value.trim(),
        owner: formOwner.value.trim(),
        dueDate: formDueDate.value,
        updatedAt: new Date().toISOString()
      }
    }
  }
  saveWorkItems()
  loadWorkItems()
  closeModal()
}

function deleteItem(id) {
  if (!confirm('确定删除该重点工作？')) return
  workItems.value = workItems.value.filter(i => i.id !== id)
  saveWorkItems()
}

function toggleStatus(item) {
  const idx = workItems.value.findIndex(i => i.id === item.id)
  if (idx !== -1) {
    workItems.value[idx].status = item.status === 'pending' ? 'completed' : 'pending'
    workItems.value[idx].updatedAt = new Date().toISOString()
    saveWorkItems()
    loadWorkItems()
  }
}

function isOverdue(item) {
  if (item.status === 'completed') return false
  const today = new Date().toISOString().split('T')[0]
  return item.dueDate < today
}
```

- [ ] **Step 2: Add KeyWorkItems template section**

Add in `<template>` after the AI Analysis section:

```html
<!-- 重点工作区块 -->
<div class="section-card work-items-card">
  <div class="section-header">
    <div class="section-title">
      <span class="section-icon">📋</span>
      <h3>近期重点工作</h3>
    </div>
    <button class="refresh-btn" @click="openAddModal">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="12" y1="5" x2="12" y2="19"/>
        <line x1="5" y1="12" x2="19" y2="12"/>
      </svg>
      添加
    </button>
  </div>

  <div v-if="workItems.length === 0" class="work-empty">
    <p>暂无重点工作，点击「添加」新增</p>
  </div>

  <div v-else class="work-grid">
    <div
      v-for="item in workItems"
      :key="item.id"
      class="work-card"
      :class="{ completed: item.status === 'completed', overdue: isOverdue(item) }"
    >
      <div class="work-card-header">
        <button
          class="status-toggle"
          :class="{ checked: item.status === 'completed' }"
          @click="toggleStatus(item)"
          :title="item.status === 'pending' ? '标记完成' : '取消完成'"
        >
          <svg v-if="item.status === 'completed'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="20,6 9,17 4,12"/>
          </svg>
        </button>
        <span class="work-status-badge" :class="item.status">
          {{ item.status === 'completed' ? '已完成' : '进行中' }}
        </span>
        <span v-if="isOverdue(item)" class="overdue-badge">已逾期</span>
      </div>

      <div class="work-content">{{ item.content }}</div>

      <div class="work-meta">
        <span class="work-owner">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>
          {{ item.owner }}
        </span>
        <span class="work-date">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/>
            <line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
          {{ item.dueDate }}
        </span>
      </div>

      <div class="work-actions">
        <button class="work-action-btn" @click="openEditModal(item)">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
          编辑
        </button>
        <button class="work-action-btn danger" @click="deleteItem(item.id)">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3,6 5,6 21,6"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          </svg>
          删除
        </button>
      </div>
    </div>
  </div>
</div>

<!-- 添加/编辑弹窗 -->
<div v-if="modalVisible" class="modal-overlay" @click.self="closeModal">
  <div class="modal-container">
    <div class="modal-header">
      <h3>{{ modalMode === 'add' ? '添加重点工作' : '编辑重点工作' }}</h3>
      <button class="modal-close" @click="closeModal">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
    <div class="modal-body">
      <div v-if="formError" class="form-error">{{ formError }}</div>

      <div class="form-group">
        <label>工作内容</label>
        <textarea v-model="formContent" rows="3" placeholder="输入重点工作内容..."></textarea>
      </div>

      <div class="form-group">
        <label>责任人</label>
        <input type="text" v-model="formOwner" placeholder="输入责任人姓名">
      </div>

      <div class="form-group">
        <label>完成日期</label>
        <input type="date" v-model="formDueDate">
      </div>
    </div>
    <div class="modal-footer">
      <button class="btn-cancel" @click="closeModal">取消</button>
      <button class="btn-save" @click="saveItem">保存</button>
    </div>
  </div>
</div>
```

- [ ] **Step 3: Add WorkItems CSS**

Add to `<style scoped>`:

```css
/* Work Items Section */
.work-empty {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
  font-size: 14px;
}

.work-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.work-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(0, 212, 255, 0.08);
  border-radius: 20px;
  padding: 20px;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.work-card:hover {
  border-color: rgba(0, 212, 255, 0.2);
  background: rgba(0, 212, 255, 0.04);
}

.work-card.completed {
  opacity: 0.6;
}

.work-card.completed .work-content {
  text-decoration: line-through;
  color: var(--text-muted);
}

.work-card.overdue {
  border-color: rgba(255, 68, 68, 0.25);
}

.work-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-toggle {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  border: 2px solid rgba(0, 212, 255, 0.3);
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  padding: 0;
}

.status-toggle svg {
  width: 14px;
  height: 14px;
  color: #00d4ff;
}

.status-toggle.checked {
  background: rgba(0, 212, 255, 0.15);
  border-color: #00d4ff;
}

.work-status-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 999px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.work-status-badge.pending {
  background: rgba(0, 212, 255, 0.1);
  color: #00d4ff;
}

.work-status-badge.completed {
  background: rgba(0, 255, 136, 0.1);
  color: #00ff88;
}

.overdue-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 999px;
  background: rgba(255, 68, 68, 0.1);
  color: #ff4444;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.work-content {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.6;
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.work-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  color: var(--text-secondary);
}

.work-owner, .work-date {
  display: flex;
  align-items: center;
  gap: 5px;
}

.work-owner svg, .work-date svg {
  width: 13px;
  height: 13px;
  color: var(--text-muted);
}

.work-actions {
  display: flex;
  gap: 8px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.work-action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.work-action-btn:hover {
  background: rgba(0, 212, 255, 0.08);
  border-color: rgba(0, 212, 255, 0.2);
  color: #00d4ff;
}

.work-action-btn.danger:hover {
  background: rgba(255, 68, 68, 0.08);
  border-color: rgba(255, 68, 68, 0.2);
  color: #ff4444;
}

.work-action-btn svg {
  width: 13px;
  height: 13px;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(5, 8, 16, 0.85);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(8px);
}

.modal-container {
  width: 95%;
  max-width: 480px;
  background: linear-gradient(145deg, rgba(12, 20, 40, 0.98), rgba(8, 14, 28, 0.99));
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 24px;
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
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.form-error {
  padding: 12px 16px;
  background: rgba(255, 68, 68, 0.1);
  border: 1px solid rgba(255, 68, 68, 0.2);
  border-radius: 12px;
  color: #ff6b6b;
  font-size: 13px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.form-group input,
.form-group textarea {
  padding: 12px 16px;
  background: rgba(0, 212, 255, 0.03);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 12px;
  color: var(--text-primary);
  font-size: 14px;
  font-family: inherit;
  outline: none;
  transition: all 0.2s;
  resize: none;
}

.form-group input:focus,
.form-group textarea:focus {
  border-color: #00d4ff;
  box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
}

.form-group input[type="date"] {
  color-scheme: dark;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 28px;
  border-top: 1px solid rgba(0, 212, 255, 0.08);
}

.btn-cancel, .btn-save {
  height: 42px;
  padding: 0 24px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-secondary);
}

.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.05);
}

.btn-save {
  background: linear-gradient(135deg, #00d4ff, #00ff88);
  border: none;
  color: #050810;
}

.btn-save:hover {
  box-shadow: 0 4px 20px rgba(0, 212, 255, 0.3);
}

/* Responsive */
@media (max-width: 1100px) {
  .work-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .work-grid {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 4: Add onMounted to load work items**

Add to existing `onMounted`:

```javascript
onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
  initCharts()
  loadAICache()
  loadWorkItems()  // NEW
  window.addEventListener('resize', handleResize)
})
```

- [ ] **Step 5: Import API functions**

Update the existing `import` at top of `<script setup>` to include:

```javascript
import { generateAIAnalysis, getAIStatus } from '../api'
```

(Only if not already imported - check the current imports)

- [ ] **Step 6: Test work items locally**

Verify: Add, edit, delete, toggle status all work with localStorage.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/views/KeyIndicators.vue
git commit -m "feat: add key work items management to KeyIndicators"
```

---

## Task 6: 集成联调

- [ ] **Step 1: Verify localStorage keys don't conflict**

Check that `ai_analysis_cache` and `key_work_items` don't conflict with existing localStorage usage in the project.

- [ ] **Step 2: Full end-to-end test**

1. Start backend: `cd backend && uvicorn main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Upload a test Excel file
4. Navigate to KeyIndicators
5. Click "刷新分析" → verify AI response appears
6. Add a work item → verify it persists after refresh
7. Refresh page → verify all data restored from localStorage

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete AI analysis and key work items dashboard"
```

---

## Spec Coverage Check

| Spec Section | Task |
|---|---|
| AI 分析 6 维度输出 | Task 4 |
| 刷新逻辑（手动+缓存） | Task 4 |
| 缓存失效提示 | Task 4 |
| 重点工作 CRUD | Task 5 |
| localStorage 持久化 | Task 5 |
| 页面布局（大屏风格） | Task 4+5 |
| 后端 MiniMax 调用 | Task 2 |
| API Key 后端存储 | Task 1+2 |
| .env 配置 | Task 1 |

---

## 上线前验收清单（修正版）

- [ ] `GET /api/ai/status` 在未配置 MiniMax 时返回 `configured=false`，前端显示“AI 未配置”而不是报错
- [ ] `POST /api/ai/analyze` 在 MiniMax 异常时返回友好错误，前端保留上一次缓存结果
- [ ] AI 解析逻辑可兼容至少两种 MiniMax 返回结构（`message.content`、`messages[0].text`）
- [ ] 首次进入关键指标页，无缓存时展示“点击刷新分析”
- [ ] 有缓存且数据未变时直接展示缓存
- [ ] 有缓存但数据快照哈希变化时提示“数据已更新，请点击刷新”
- [ ] 重点工作支持新增、编辑、删除、状态切换，并在刷新后保持
- [ ] KeyIndicators 在桌面和移动端均不出现布局溢出
- [ ] 本地运行 `npm run build` 与后端基础语法检查通过

---

## 执行建议（按风险优先）

1. 先完成 Task 0（风险修正）和 Task 1（配置）
2. 再完成 Task 2（后端 AI 路由）并先联调 `GET /api/ai/status`
3. 然后完成 Task 3 + Task 4（前端 AI 区块）
4. 最后完成 Task 5（重点工作）和 Task 6（集成联调）
