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
│   │   ├── services/       # API 封装
│   │   └── router/         # 路由
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
- **routers/analysis.py**：在建工程数据分析接口
- **routers/notify.py**：飞书/企业微信消息推送
- **routers/report.py**：月报生成
- **routers/ai.py**：AI 分析接口（MiniMax）
- **routers/archive.py**：数据档案上传、列表、下载、删除接口

## 注意事项

- 后端 `.env` 文件包含 MiniMax API Key，不要提交到 git
- CORS 只允许 `http://localhost:5173`，本地开发需前后端同时运行
- Excel 导出功能依赖 OpenPyXL，修改导出逻辑时注意列宽、样式兼容性
- Electron 打包前需先执行 `npm run build`
