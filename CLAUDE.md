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
│   │   │   ├── KpiGrid.vue          # KPI 指标卡网格
│   │   │   └── HistoryPanel.vue     # 历史快照抽屉（跨页面复用）
│   │   └── __tests__/      # 前端单元测试（Vitest，300 用例）
│   └── package.json
├── backend/
│   ├── main.py             # FastAPI 入口，CORS 允许 localhost:5173
│   ├── models.py           # SQLAlchemy 数据模型
│   ├── routers/            # 路由模块（analysis、budget、ai、notify、report、archive）
│   ├── uploads/archive/    # 数据档案文件存储目录
│   ├── services/           # 业务逻辑
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

> v1.32.0 完成四波重构后剩余计划。用户说"继续优化"时按此清单推进，每步需 300/300 测试全绿 + 目视确认。

### 已完成（v1.32.0, 2026-07-02）

- ✅ 第一波：清理 Budget/Dashboard 死代码 CSS（-1124 行）
- ✅ 第二波：抽取 3 个 composables（useFormatters/useHistoryPanel/useFileUpload，消除 14 函数重复）
- ✅ 第三波：Dashboard 拆分 3 个弹窗子组件（FourClassWarningModal/ManagerDetailDrawer/TransferPriorityModal）
- ✅ 方向 1：抽取 KpiGrid + HistoryPanel（跨页面复用）

当前状态：Budget.vue 2450 行（CSS 1379 行 / 279 处 !important / 163 处硬编码 hex），Dashboard.vue 1683 行。

### 🔴 P1 — Budget CSS 治理（最高优先级，关键路径）

Budget.vue 的 CSS 仍占 56%，是当前最大技术债，且是后续 CSS 工作的拦路虎。

- **P1-a：第 4 层 !important 降级**
  - 第 4 层（Budget replica）还剩 279 处 `!important`（第一波只降了第 3 层 205 处）
  - 第 4 层是最终生效层，删 `!important` 后同特异性后定义胜出，逻辑不变
  - 需逐块分析确认无视觉变化，类似第一波 Phase B
  - 收益：`!important` 279 → 0
- **P1-b：硬编码 hex → Editorial token 迁移**
  - 163 处 `#ffffff`/`#1c1b18`/`#e4e3dc`/`#6b6a63` 等 → `var(--surface)`/`var(--ink)`/`var(--line)`/`var(--ink-3)`
  - 需建立颜色映射表，逐一确认对应关系
  - 收益：Budget 与 Dashboard 统一 token 体系，解锁 P2

### 🟠 P2 — 抽共享 CSS（依赖 P1-b 完成）

- 新建 `src/styles/shared.css`，抽出 `.rate-badge`/`.modal-close`/`.loader-ring`/`.btn`/`.overlay-divider` 等共享样式
- main.js import 全局样式，子组件删除自带的重复 CSS
- 前提：P1-b 完成后 Budget/Dashboard token 对齐才能有效抽共享
- 收益：消除子组件间 ~30 行 + Dashboard/Budget 间 ~200 行 CSS 重复

### 🟡 P3 — Budget 批次管理 UI 拆分

- 抽 `BatchManageModal.vue`（批次创建/编辑弹窗 + 专业面板）
- 状态留 Budget（测试 wrapper.vm 访问），子组件搬 template + CSS + 纯展示
- 收益：Budget template 650 → ~350 行
- 风险：中（批次 reactive 逻辑复杂，Budget.test.js 有批次测试）

### 🟢 P4 — Dashboard 主体区块拆分（可选，收益递减）

- 上传空状态页：先复用已有 `UploadZone.vue`（components/ 下有但从未被 import），再拆 `UploadEmptyState.vue`
- 管理员视图卡：耦合最深（~20 依赖），需先抽 target 编辑状态到 composable
- 收益：Dashboard template -~200 行
- 风险：中-高（耦合深，需小心 props/emit 拆分）

### ⚪ P5 — Budget 上传区复用 UploadZone（小收益，可随时穿插）

- `components/UploadZone.vue` 已存在但从未被 import，Budget/Dashboard 上传区都是内联实现
- 替换为 `<UploadZone>` 引用，消除内联上传 UI 重复 ~40 行
- 风险：低，需适配两页面交互差异

### 推荐执行顺序

```
P1-a → P1-b → P2 → P3
              ↘ P5（可随时穿插）
                   ↘ P4（可选）
```

### 重构约定（沿用 v1.32.0 验证过的模式）

- 子组件：`<script setup>` + defineProps 对象风格 + defineEmits 数组 + JSDoc + scoped style + 全 `var(--xxx)` token + 2 字母 class 前缀
- composable：全局共享用模块级单例，视图私有用工厂 per-instance（ref 定义在 export 函数内）
- 状态留页面（测试 wrapper.vm 访问），子组件只搬 template + CSS + 纯展示函数
- 每步 300/300 测试 + 目视确认，分步提交
