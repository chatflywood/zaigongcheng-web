# 工程建设数据驾舱 — 项目说明

## 项目概述

在建工程与预算分析自动化系统，支持上传 Excel 明细表后自动生成数据看板、AI 分析、月报及消息推送。
产品名：**工程建设数据驾舱**，当前版本见 `CHANGELOG.md`。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + ECharts + Axios |
| 桌面 | Electron（打包为本地桌面应用） |
| 后端 | FastAPI + SQLAlchemy + Uvicorn |
| 数据处理 | OpenPyXL（Excel 读写） |
| AI | MiniMax API（`backend/.env` 配置密钥） |

## 目录结构

```
zaigongcheng-web/
├── frontend/
│   ├── src/
│   │   ├── views/          # 页面组件（Dashboard.vue、Budget.vue、KeyIndicators.vue、Archive.vue）
│   │   ├── api/            # API 调用封装（30+ 接口）
│   │   ├── router/         # Vue Router 路由配置
│   │   ├── composables/    # 状态与逻辑 composable
│   │   │   ├── useGlobalData.js    # 核心数据（全局单例）
│   │   │   ├── useHistoryCenter.js # 历史记录中心（全局单例）
│   │   │   ├── useAppTools.js      # 工具功能（全局单例）
│   │   │   ├── useFormatters.js    # 通用格式化函数
│   │   │   ├── useHistoryPanel.js  # 历史快照抽屉（工厂 per-instance）
│   │   │   └── useFileUpload.js    # 文件上传交互（工厂 per-instance）
│   │   ├── components/     # 共享 UI 组件
│   │   │   ├── Modal.vue / DataCard.vue / UploadZone.vue / FileRow.vue  # 基础组件
│   │   │   ├── FourClassWarningModal.vue  # 四类预警明细弹窗
│   │   │   ├── ManagerDetailDrawer.vue   # 管理员明细抽屉
│   │   │   ├── TransferPriorityModal.vue # 转固推进清单弹窗
│   │   │   ├── BatchManageModal.vue  # 批次管理弹窗 + 专业抽屉（v1.34.0 抽出）
│   │   │   ├── KpiGrid.vue          # KPI 指标卡网格
│   │   │   └── HistoryPanel.vue     # 历史快照抽屉（跨页面复用）
│   │   ├── styles/        # 全局共享样式（v1.34.1 起抽 .btn/.rate-badge 等）
│   │   │   └── shared.css
│   │   └── __tests__/      # 前端单元测试（Vitest，300 用例）
│   └── package.json
├── backend/
│   ├── main.py             # FastAPI 入口，CORS 允许 localhost:5173
│   ├── models.py           # SQLAlchemy 数据模型
│   ├── routers/            # 路由模块（analysis、budget、ai、notify、report、archive）
│   ├── uploads/archive/    # 数据档案文件存储目录
│   ├── services/           # 业务逻辑
│   ├── tests/             # 后端集成测试（pytest，124 用例：analysis services / analysis export / ai router / archive / budget_batch / notify / report / budget_router）
│   └── .env                # 环境变量（MiniMax API Key，不提交 git）
└── docs/
```

## 常用命令

```bash
# 前端开发
cd frontend && npm run dev            # Vite 开发服务，端口 5173

# 桌面应用开发
cd frontend && npm run electron:dev

# 前端构建
cd frontend && npm run build
cd frontend && npm run electron:build

# 后端开发
cd backend && uvicorn main:app --reload

# 后端测试（FastAPI 集成 + 服务层单元，无需启 uvicorn）
cd backend && python -m pytest tests/ -q --ignore=tests/test_api.py   # 124 用例
cd backend && python -m pytest tests/test_api.py                        # 黑盒 HTTP，需先启 uvicorn

# 重启前后端（解决 Vite 缓存旧 CSS/JS 导致页面错乱）
lsof -ti:8000,5173 | xargs kill -9 2>/dev/null
cd backend && uvicorn main:app --host 127.0.0.1 --port 8000 --reload &
cd frontend && npm run dev
# 浏览器打开 http://localhost:5173/zaigongcheng-web/ 再按 Cmd+Shift+R 硬刷新
```

## 核心业务模块

- **Dashboard.vue**：在建工程主看板，含各工程管理员汇总、预警分析、转固推进清单
- **Budget.vue**：预算分析看板
- **KeyIndicators.vue**：关键指标页面
- **Archive.vue**：数据档案库，支持三类年度文档上传存储与在线预览（SheetJS + mammoth.js）
- **routers/analysis.py**：在建工程数据分析接口（上传时保存原始数据全字段到 `raw_data`）
- **routers/notify.py**：飞书/企业微信消息推送
- **routers/report.py**：月报生成
- **routers/ai.py**：AI 分析接口（MiniMax）
- **routers/archive.py**：数据档案上传、列表、下载、删除接口

## 注意事项

- 后端 `.env` 文件包含 MiniMax API Key，不要提交到 git
- CORS 只允许 `http://localhost:5173`，本地开发需前后端同时运行
- Excel 导出功能依赖 OpenPyXL，修改导出逻辑时注意列宽、样式兼容性
- Electron 打包前需先执行 `npm run build`
- `zaigong_records.raw_data` 存储原始 Excel 全部字段（JSON），用于回溯查询；旧记录该字段为空

## 前端优化路线图

> 用户说"继续优化"时按此清单推进。每步需 300/300 测试全绿 + 目视确认 + 分步提交。
> 下次接手时先读此段，按"推荐执行顺序"从下一个待办开始。

### 已完成

#### v1.32.0 (2026-07-02) — 四波重构，净减 2086 行

- ✅ 第一波：清理 Budget/Dashboard 死代码 CSS（-1124 行）
- ✅ 第二波：抽取 3 个 composables（useFormatters/useHistoryPanel/useFileUpload，消除 14 函数重复）
- ✅ 第三波：Dashboard 拆分 3 个弹窗子组件（FourClassWarningModal/ManagerDetailDrawer/TransferPriorityModal）
- ✅ 方向 1：抽取 KpiGrid + HistoryPanel（跨页面复用）

#### v1.33.0 (2026-07-03) — Budget CSS 治理

- ✅ P1-a：Budget 第 4 层 `!important` 全部清零（279→0）。其中 277 处直接删除，2 处升级选择器特异性替代（`.batch-tbl th.bc-date` 反超 `.batch-tbl th`；`.br-total td.bc-note-muted` 反超 `.br-total td`）
- ✅ P1-b：Budget 中性色 hex→token。文字色（ink 系 9 个 hex）+ 边框色（line 系 9 个 hex）共 ~50 处转为 `var(--ink)`/`var(--ink-3)`/`var(--line)` 等。**底色保留原 hex**——Budget 冷灰底色（`#f6f5f2` 等）与 Editorial 暖米 token（`--paper`=#F7F5EE）色温不同，转 token 会导致视觉变化（已踩坑还原）。鲜艳语义色（绿/红/橙）和主题色（紫/蓝）也保留不动

**当前状态**：Budget.vue 2276 行（!important 0 处 / 硬编码 hex 96 处：底色+鲜艳色+主题色），Dashboard.vue 1683 行。Budget CSS 可维护性已大幅提升。

#### v1.34.0 (2026-07-06) — Budget 批次管理 UI 拆分

- ✅ P3：抽取 `BatchManageModal.vue`（293 行）—— 批次创建/编辑弹窗 + 专业管理抽屉两块交互。沿用 TransferPriorityModal 范式（script-first / JSDoc Props+Events / v-model:visible / 状态留父供 wrapper.vm 测试访问）。Props 11 个 / Events 12 个 / 内部纯函数 `formatBatchNum`。Budget template 489-578 段替换为单个 `<BatchManageModal/>`，Budget scoped CSS 删除弹窗/抽屉专属规则 ~110 行。Budget.vue 2451 → 2276 行（-175）。视觉零回归（保留原 class 名 + scoped 副本）。300/300 测试全绿无需改测试。

#### v1.34.1 (2026-07-06) — 抽 Shared CSS（P2 第一波）

- ✅ P2 第一波：新建 `src/styles/shared.css`（36 行），抽 `.rate-badge` + 4 状态（MDD/TDM 逐字一致）+ `.btn` 系（Budget/Dashboard/BatchManageModal 一致）。用 `:where(.xxx) {}` 把特异性降为 0,0,0，任何 scoped 副本（带 `[data-v-xxx]` = 0,1,0）自然覆盖本文件，零回归风险
- 清理 5 处副本（MDD/TDM 各 -8 / BatchManageModal -18 / Budget -14 / Dashboard -12），净减 19 行
- main.js 在 `style.css` 之后紧接 import `./styles/shared.css`
- 未抽（保留各自 scoped）：`.modal-close`（A 套 surface 底 vs B 套 transparent 底语义分歧）、`.loader-ring`（Budget 字面 hex 色 / Dashboard 三段 nth-child 色）、`.btn-sm`（仅 BatchManageModal 单处）
- 300/300 测试全绿 + build 通过

**所有 P2-P5 路线图项已于 v1.34.0 / v1.34.1 完成。** 后续若新增弹窗组件又复制 `.modal-close / .loader-ring` 各 ≥3 次，再回过头抽 `shared.css` 第二波。

### 重构约定（沿用 v1.32.0/v1.33.0/v1.34.0/v1.34.1 验证过的模式）

- 子组件：`<script setup>` + defineProps 对象风格 + defineEmits 数组 + JSDoc + scoped style + 全 `var(--xxx)` token + 2 字母 class 前缀
- composable：全局共享用模块级单例，视图私有用工厂 per-instance（ref 定义在 export 函数内）
- 状态留页面（测试 wrapper.vm 访问），子组件只搬 template + CSS + 纯展示函数
- CSS token 迁移：**底色（paper/surface 系）不可跨页面统一**（Budget 冷灰 vs Editorial 暖米色温不同），只统一文字（ink 系）和边框（line 系）
- 每步 300/300 测试 + 目视确认，分步提交

### 后端健壮性（v1.34.3）

- **字体跨平台**：`routers/report.py` 月报 PNG 字体不再写死 macOS 路径。`FONT_ZH/FONT_MONO` 由 `_resolve_font()` 从跨平台候选列表（macOS/Windows/Linux）取首个可用项，全不可用返回 `None` 由 `font()/mono()` 退默认字体不崩溃。打包到 Electron / 部署 Win/Linux 不再中文变方框
- **错误脱敏**：7 处路由 500/502 异常统一脱敏 -- 前端只返回异常类型名（如 `生成简报失败：RuntimeError`），不返回 `str(e)` 内容；完整堆栈走 `logger.exception()` 记后端控制台。约定：400 `ValueError` 业务文案不动（是给用户的提示，非泄露）
- **后端日志**：`main.py` 配 `logging.basicConfig(level=INFO)`。500 排查看 uvicorn 终端，不再凭空猜
