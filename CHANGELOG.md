# 功能更新日志

## v1.36.0 (2026-08-31)

### 月报简报重构（HTML 卡片版式 + Playwright 高清渲染）+ 管理员导出汇总页 + 演示环境支持

#### 1. 月报简报大改版（`routers/report.py`）

- 指标口径对齐：新增 `_extract_core_kpis()`，与前端 KeyIndicators 四个进度圆环完全同口径——当期资本性支出进度（目标 100%）、转固率（目标 60%）、整体支出进度（目标 100%）、整体立项进度（目标 90%）；兼容 camelCase（前端归一化）与 snake_case（存库）双字段命名
- 新增 `build_brief_html()`：卡片式 HTML 简报——四张 KPI 卡（进度条 + 目标标注 + 缺口/达标判词）、四类预警徽章（已触发 / 预警计数）、管理员转固率 Top6 榜单、已触发预警明细
- 渲染管线升级：`/report/image` 优先 Playwright 无头浏览器 HTML→高清 PNG（`_ensure_browser()` / `_render_html_to_png()`），失败自动回退 Pillow 逐像素绘制，零硬故障；`/report/brief` 同步切换为 HTML 卡片版式

#### 2. 管理员明细导出增强（`routers/analysis.py`）

- 导出全部管理员：首个 sheet 改为「全部管理员」汇总页（全部工程清单，含管理员 / 施工单位列 + 表头自动筛选），其后每个管理员一个 sheet
- 汇总页转固率口径修正：优先取 summary「合计」行，缺失时回填存库核心指标 `metrics_data.total_rate`，不再用 结转额/期末余额 近似替代
- 单管理员导出补「施工单位」列；`_build_manager_sheet` 参数化（可选管理员 / 施工单位列、自定义 sheet / 报告 / 明细标题，负数标红列位自适应）

#### 3. 演示与部署环境

- `models.py`：支持 `ANALYSIS_DB_PATH` 环境变量指向独立数据库（竞赛演示与日常数据隔离）
- `services/analysis.py`：管理员排序序扩展 管理员A–F
- 依赖：后端 `requirements.txt` 与前端 `package.json` 新增 playwright

#### 4. 前端

- 推送设置 Webhook 配置指引合并：企业微信 / 飞书 / 量子密信三平台说明统一展示

#### 测试与版本

- 后端 **178/178** 全绿（+4 例：汇总 sheet 优先、核心口径回填、无合计行兜底、单管理员布局不变）；前端 **304/304**
- `test_api.py` 样例 Excel 补全工程编码 / 一级专业 / 验收类型等 12 列真实字段，对齐真实数据结构
- `frontend/package.json` / `backend/main.py` → **1.36.0**

## 量子密信群 Webhook（2026-08-09）

- 推送渠道扩展：企业微信、飞书之外新增量子密信群机器人（provider：`wework|feishu|quantum`）
- 渠道配置入库，并按 Webhook URL 自动识别实际渠道；配置渠道与 URL 识别结果不一致时拒绝保存
- 推送配置接口返回脱敏 Webhook URL（`_mask`，仅保留末 8 位）
- 前端推送设置支持三渠道切换与配置指引；`test_notify_quantum.py` 新增、`test_notify_router.py` 扩展

## 安全加固（2026-08-08）

- 档案预览：SheetJS 升级至官方 `0.20.3`，限制预览文件、工作表、行列和单元格规模；Excel / Word 转换结果统一经 DOMPurify 清洗。
- Webhook：仅允许企业微信、飞书官方 HTTPS 主机、端口和路径，阻断 `/api/notify/test` 等入口的 SSRF。
- Excel 导出：所有用户可控文本写入工作簿前进行公式中和，避免 `= / + / - / @` 触发公式执行。
- 上传解析：升级 FastAPI / Starlette / python-multipart 解析栈，并在 multipart 解析前实施请求体大小限制。
- Electron：升级至 `43.3.0`，启用渲染进程沙箱，阻止应用窗口导航到不可信页面。
- 验证：前端 `302/302`、后端安全提交树 `152/152`；npm 与 Python 依赖审计均为 0 个已知漏洞。

## v1.35.0 (2026-07-29)

### P0：数字信任 + 备份恢复 + 快照语义 + 文档对齐

承接优化清单 P0-1～P0-5，先锁「算得对 / 传得对 / 丢不了 / 说得清」。

#### P0-1 口径黄金样例测试
- 新增 `backend/tests/test_golden_metrics.py`
- 固定在建工程样例：资本支出 150 万、待收货 20 万、本月 15 万、综合转固率 `1 - 55/205`、目标 500 时进度 30%
- 固定预算样例：年度预算 300、已占用 80、预占用 10、立项进度 30%、年度支出 60、支出进度 20%
- 公式改动必须显式改黄金测试，防止静默漂移

#### P0-2 上传校验摘要
- 新增 `backend/services/validation.py`
- 在建上传响应增加 `validation`：行数、管理员数、金额 checksum（万）、四类预警排除行、缺列/空管理员 warnings、`summary_text`
- 预算上传响应增加 `validation`：专业数、项目数、预算/占用/支出 checksum、立项/支出进度
- 上传成功 `message` 直接带摘要文案；Dashboard / Budget / 数据管理面板展示

#### P0-3 一键备份 / 恢复
- 新增 `backend/services/backup.py` + `routers/backup.py`（`/api/backup/status|export|restore`）
- 备份 zip：`analysis.db` + `uploads/archive/*` + `backup_manifest.json`
- 恢复前覆盖当前库与档案；非法 zip / 缺 manifest 返回 400；防 zip-slip
- 前端「数据管理」面板新增「③ 数据备份与恢复」：导出 / 从备份恢复（二次确认）
- 测试：`tests/test_backup_router.py` 6 例（service 往返 + 路由）

#### P0-4 文档矛盾清理
- PRD / requirements：删除「预算仍可能依赖本地源文件回查」过时限制
- 统一导航信息架构：侧栏「上传历史」中心 + 独立「数据档案」页（Archive）
- 明确非目标：无登录鉴权、单机本机数据
- README / CLAUDE 同步 v1.35.0、备份接口、测试用例数

#### P0-5 历史快照语义写死
- 产品约定：**快照 = 上传当时计算结果（不可变）**，口径变更不自动重算历史
- UI：历史中心注记、HistoryPanel 副文案、全局 snapshotLabel、上传 checklist 同步该语义

### 版本
- `frontend/package.json` / `backend/main.py` → **1.35.0**
- 后端测试：124 → **136**（+6 golden +6 backup）

---

## v1.34.5 (2026-07-23)

### P0 工程卫生：版本对齐 + Electron 本机绑定 + 仓库清理 + 施工单位护栏

- **版本对齐**：`frontend/package.json` `1.14.0` → `1.34.4`（与 CHANGELOG 主线对齐；本版起为 `1.34.5`）；`backend/main.py` FastAPI / root 接口 `1.0.0` → `1.34.5`
- **Electron 安全默认值**：`electron/main.cjs` 后端启动 host `0.0.0.0` → `127.0.0.1`，避免桌面端无鉴权 API 暴露到局域网
- **仓库清理**：`dashboard-*-prototype.html` / `dashboard-demo.html` / `zaigongcheng-handoff.zip` 从 git 索引移除并加入 `.gitignore`；删除误放根目录空 `node_modules/`
- **四类预警补「施工单位」**（承接未提交 WIP）：
  - `services/analysis.py`：`build_four_class_warnings` item 增加 `constructionUnit`（缺列 / NaN → 空串）
  - `routers/analysis.py`：导出表多一列「施工单位」；旧记录 JSON 无字段时从 `raw_data` 按工程编码回查；导出文件名加当日日期后缀
  - 前端 `Dashboard.vue` / `KeyIndicators.vue`：下载文件名与后端一致（数据日期 + 导出日期）
- **测试护栏**（+8 例，116→124 全绿）：
  - `test_analysis_services.py` +3：有施工单位 / 缺列 / NaN
  - 新增 `test_analysis_export_router.py` +5：表头 15 列、item 直写优先、raw_data 回查兜底、文件名日期后缀、404

## v1.34.4 (2026-07-09)

### 后端补测：预算路由算钱盲区（+22 例，94→116 全绿）

此前 94/94 gate 模式里预算页"上传 → 一级专业年度支出汇总 → 与预算目标对比 → 刷新 / 历史快照"整条链路零覆盖，是 `docs/prd.md` 第 11 章 P1 唯一未落地项。其余 P1 两条（一级专业入库、脱离本地源文件回查）早在 v1.29.0 落地，但 PRD 第 10 章"当前限制"仍写"依赖本地源文件回查"，文档与代码长期脱节。

- 新增 `backend/tests/test_budget_router.py`，沿用 `test_budget_batch_router` 范式（httpx.ASGITransport + 内存 SQLite + StaticPool + patch `get_db`），6 类 22 例：
  - `build_zaigong_spend_summary_from_record` 三分支：detail_data 含一级专业 / 退回 raw_data（字符串数字可转）/ record=None，含空 category 过滤、必需列缺失
  - `load_budget_sheets` 年份无关 + 缺项目 sheet 返回 None；`clean_nan` 嵌套 NaN/Inf→None 递归
  - `analyze_budget` 端到端算账（ward_total / annual_spend_total / approval_progress / spend_progress / 单专业 spend_progress）；spend_summary=None 全 0 初始化态
  - 4 个路由端点：upload 入库 / 非 Excel 400 / 超 20MB 400 / 缺 sheet 抛 ValueError 400；refresh-spend 重算落库 / 无预算及无在建兜底；history 空库 / desc 时序 + limit / current+previous 快照 / id 不存在 404 + 空库 404
- 不动业务代码一行（纯加测试）
- 文档同步：删 PRD 第 10 章"本地源文件回查"限制（已不再成立），第 11 章 P1 三条标 ✅；`requirements.md` 同步两处口径与第 11 章；`CLAUDE.md` 用例数 94→116

## v1.34.3 (2026-07-08)

### 后端健壮性：字体跨平台 + 错误信息脱敏 + 补日志

延续 v1.34.2 的安全治理，修掉两颗会随"打包成桌面应用 / 换机部署"引爆的定时炸弹，并补上后端长期缺失的日志基础设施。

#### 1. 月报字体路径跨平台化（`routers/report.py`）

- 原状：`FONT_ZH / FONT_MONO` 写死 macOS 专有路径（`/System/Library/Fonts/STHeiti Medium.ttc` / `SFNSMono.ttf`）。Mac 本地正常，但**打包成 Electron 或部署到 Windows / Linux 后，月报 PNG 中文字符变方框 □□□**（`font()` 有 try/except 不致崩溃，但默认字体不含 CJK）
- 改造：字体改为"候选列表 + 运行时解析首个可用项"，覆盖三大系统：
  - 中文：macOS 黑体/苹方/宋体 → Windows simhei/msyh/simsun → Linux 文泉驿/Noto CJK
  - 等宽：macOS SF Mono/Menlo/Monaco → Windows consola/cour → Linux DejaVu/Liberation
  - 新增 `_resolve_font()` 探测性加载（`os.path.exists` + `ImageFont.truetype` 双重校验），全不可用返回 `None`，`font()/mono()` 走原 try/except 退默认字体，**不崩溃**
- 行为不变：macOS 实测仍解析到原 STHeiti / SFNSMono，零视觉回归

#### 2. 路由层错误信息脱敏 + 后端补日志（7 处）

- 现状评估：v1.34.2 已把最危险的"完整 Python 堆栈经 `detail=traceback.format_exc()` 泄露"修掉，降级为 `str(e)` 一行摘要。但该摘要仍可能含数据库表名/文件路径/DSN 等内部细节
- 改造：7 处 500/502 异常响应统一脱敏 -- 前端只返回异常类型名（如"生成简报失败：RuntimeError"），不返回 `str(e)` 内容；同时 `logger.exception()` 把**完整堆栈 + 异常消息**记到后端控制台，排查不丢线索
  - `analysis.py`：upload 500、update_target 500
  - `budget.py`：upload 500、refresh-spend 500
  - `report.py`：brief HTML 500、image PNG 500
  - `notify.py`：webhook 推送 502
- `main.py` 新增 `logging.basicConfig`（level=INFO + 统一格式），补上后端此前完全空白的日志基础设施 -- 500 异常、运行信息现在可在 uvicorn 终端查看
- 不动 400 `ValueError`：业务校验文案（如"仅支持 Excel 文件"）本就是给用户看的提示，非内部泄露
- 实测验证（构造含 `SuperSecret123` 密码的异常）：前端响应不含密码 / 无 `detail` 字段 / message 含类型名；后端日志含完整密码 + Traceback -- 5 项断言全过
- 测试同步：`test_report_router.py` 两处 500 断言由"含异常文本"改为"含 `RuntimeError` 类型名"，**94/94 仍全绿**

## v1.34.2 (2026-07-06)

### 后端 4 路由补集成测试 + 安全/上传健壮性修复

#### 安全与健壮性修复

- `routers/report.py`: 两处月报生成失败响应（HTML / PNG）删除 `detail=traceback.format_exc()`，不再把完整 Python 堆栈原样返回前端——避免潜在信息泄露
- `README.md`: 本地启动 `uvicorn --host` 由 `0.0.0.0` 改为 `127.0.0.1`，默认只允许本机访问，避免无意中把后端 API 暴露到局域网/公网；"部署说明"段保留 `0.0.0.0` 并加注"需自行加反代+鉴权"
- `routers/budget.py /upload`: 新增 `.xlsx/.xls` 扩展名校验 + 20MB 大小上限（与 `analysis.py /upload` 一致），避免误传大文件爆内存
- `routers/archive.py /upload`: 新增 50MB 大小上限（档案可含 docx/pdf，门限比 Excel 放宽），读入内存后落盘前校验

#### 后端补集成测试（+41 例，94/94 全绿）

补回此前"路由层零集成测试"的结构性债：archive / notify / report / budget_batch 4 个路由原本 0 例覆盖。新增 4 个测试文件，沿用 `test_ai_router_unit.py` 范式并扩展：

| 文件 | 例数 | 覆盖端点 |
|---|---|---|
| `test_budget_batch_router.py` | 17 | 专业 + 批次 CRUD，含重命名传播、批次 totals 累加、dup name 400、404、reorder |
| `test_archive_router.py` | 7 | 上传 → 列表 → 下载 → 删除全闭环，含非法分类/扩展名、pdf 上传白名单、不存在的 404 |
| `test_notify_router.py` | 10 | 配置读写 + 脱敏、飞书/企微 URL 白名单、clear、push 未配置/不存在 400/404、test push 用 mock 隔离外部 webhook 的成功/错误路径 |
| `test_report_router.py` | 7 | brief HTML + image PNG，含 404、渲染异常友好响应（验证 v1.34 trace 泄露不复活）、可选 budget_id 透传、StreamingResponse Content-Type |

测试范式：
- FastAPI mini-app + `httpx.ASGITransport`（async client 直连 ASGI，不启 uvicorn）
- 内存 SQLite + `StaticPool` + `check_same_thread=False`，跨 async 线程安全
- `get_db` monkeypatch 到内存库，与生产 SQLite 物理隔离零污染
- 外部依赖（`build_brief_html/image`、`send_test` webhook）用 `patch` 隔离

验证：`python -m pytest tests/ --ignore=tests/test_api.py` = 94/94 绿（53 旧 + 41 新）。`test_api.py` 既有 2 个 baseline 失败（`test_upload_excel` / `test_budget_sheet_name_is_year_agnostic`）与本次改动无关，已在前续步骤用 `git stash` 验证。

## v1.34.1 (2026-07-06)

### 抽 Shared CSS — P2 第一波

延续 v1.34.0 抽弹窗子组件后发现的"每抽一个组件就复制一份 .btn/.rate-badge"结构性复制趋势，新建全局 shared.css，止住这个趋势。

- 新增 `frontend/src/styles/shared.css`（36 行）：
  - `.rate-badge` + `.success/.normal/.warning/.danger`（ManagerDetailDrawer + TransferPriorityModal 逐字一致，全 `var(--ok-soft)/var(--info-soft)/var(--warn-soft)/var(--bad-soft)` token）
  - `.btn / .primary / .ghost / :hover / svg / :disabled`（Budget + Dashboard + BatchManageModal 一致，全 token；正典取 Budget/Dashboard 的 `padding: 7px 12px` + `border-radius: var(--r-md)` + `transition: all 120ms; white-space: nowrap` 版本）
- 技术要点：用 `:where(.xxx) {}` 把特异性降为 0,0,0，任何 scoped 副本（带 `[data-v-xxx]` = 0,1,0）都能自然覆盖本文件，零回归风险
- 清理 5 处副本：ManagerDetailDrawer -8 / TransferPriorityModal -8 / BatchManageModal -18（含修复一处 .btn-sm 误删）/ Budget.vue -14 / Dashboard.vue -12，净减 19 行
- `main.js` 在 `style.css` 之后紧接 `import './styles/shared.css'`
- 未抽（保留各自 scoped）：`.modal-close`（A 套 surface 底 vs B 套 transparent 底语义分歧）、`.loader-ring`（Budget 字面 hex 色 / Dashboard 三段 nth-child 色）、`.btn-sm`（仅 BatchManageModal 单处使用）
- 300/300 测试全绿 + build 通过，零视觉回归

## v1.34.0 (2026-07-06)

### Budget 批次管理 UI 拆分 — P3 完成

延续 v1.32.0/v1.33.0 的 Budget 瘦身，完成 P3 抽取批次管理弹窗为独立子组件。

- 新增 `frontend/src/components/BatchManageModal.vue`（293 行）：承载「新增/编辑批次弹窗」+「专业管理抽屉」两块交互。沿用 TransferPriorityModal 范式 —— script-first / JSDoc 含 Props+Events / `v-model:visible` / 状态留父组件供 `wrapper.vm` 测试访问 / 全 `var(--xxx)` token / scoped style
  - 11 个 Props：`modalVisible / modalMode / modalForm / noteFieldsOpen / specialties / specialtyVisible / specialtyList / editingSpecialty / newSpecialtyName / modalSubtotal / modalLoading`
  - 12 个 Events：`update:modal-visible / update:specialty-visible / update:editing-specialty / update:new-specialty-name / close-batch-modal / set-amount / toggle-note-field / save-batch / start-edit-specialty / save-specialty-edit / add-new-specialty / confirm-delete-specialty`
  - 内部纯函数 `formatBatchNum`（复制实现，不污染测试 wrapper.vm）
- 改 `frontend/src/views/Budget.vue` 2451 → 2276 行（-175）：
  - template 489–578 段（弹窗 + 抽屉）替换为单个 `<BatchManageModal/>` 调用
  - script 新增 `import BatchManageModal`，所有 ref/computed/方法保留供 `wrapper.vm` 测试访问
  - scoped CSS 删除弹窗/抽屉专属规则 ~110 行（`.batch-modal-box / .form-* / .amount-* / .modal-subtotal-bar / .modal-footer / .specialty-* / .btn-sm`），保留 `.btn` 系列（被 batch-view-head 按钮仍用）、`.cell-note-popup`（fixed 全局弹层仍留 Budget）、`.batch-tbl / .bc-* / .br-*`（表格本体留 Budget）

**风险控制**：`Budget.test.js` 60 条用例通过 `wrapper.vm.XXX` 访问全部批次/专业标识符，已通过 Explore agent 精确列出标识符清单，全部确认留在 Budget.vue，**无需改测试**。视觉零回归（保留原 class 名 + scoped 副本，弹窗 UI 完全照旧）。300/300 测试全绿 + `npm run build` 通过。

## v1.33.0 (2026-07-03)

### Budget CSS 治理 — !important 清零 + 中性色 token 化

延续 v1.32.0 的 Budget CSS 瘦身，完成 P1 两步治理。Budget.vue 全文 `!important` 清零，文字/边框色统一到 Editorial token 体系。

#### P1-a：第 4 层 !important 全部清零（279→0）

- 批量删除第 4 层（Budget upload page replica 段）279 处 `!important`，保留属性值不变
- 其中 277 处可直接删除（第 4 层是最终生效层，删后同特异性后定义胜出，逻辑不变）
- 2 处需升级选择器特异性替代 `!important`：
  - `.bc-date` → `.batch-tbl th.bc-date`（反超 `.batch-tbl th` 的 `text-align:right`，保持"批次日期"表头左对齐）
  - `.bc-note-muted` → `.br-total td.bc-note-muted`（反超 `.br-total td` 的 `color:ink`，保持"共 N 批次"文字灰色）
- 分析方法：用脚本提取第 4 层 {选择器→声明} 映射，逐一检查同选择器在第 4 层内外是否有竞争规则

#### P1-b：中性色 hex → Editorial token（文字/边框系，~50 处）

- 文字色 ink 系替换：`#1c1b18`→`var(--ink)`、`#6b6a63`/`#8a867f`/`#6e6a62`→`var(--ink-3)`、`#4f4a43`/`#5f5b53`/`#5e5a52`→`var(--ink-2)`、`#a8a79f`/`#b8b6ae`→`var(--ink-4)`
- 边框色 line 系替换：`#e4e3dc`/`#e5e0d6`/`#e8e4dc`/`#e6e4dd`/`#e4e0d6`→`var(--line)`、`#d0cfc6`/`#d8d5cc`/`#ddd8cd`/`#dfd9cf`→`var(--line-2)`
- **底色保留原 hex**：Budget 冷灰底色（`#f6f5f2` 等）与 Editorial 暖米 token（`--paper`=#F7F5EE）色温不同，转 token 会导致页面底色变化（已踩坑还原）
- 鲜艳语义色（`#047857` 鲜绿/`#c43131` 纯红/`#b85a08` 橙）和主题色（`#5f36da` 紫/`#1a56a4` 蓝）保留不动——Budget 视觉身份
- 建立了完整的 hex→token 映射表（含置信度标注），见 CLAUDE.md 路线图

### 成果

| 指标 | 改前 | 改后 |
|---|---|---|
| Budget.vue !important | 279 处 | 0 处 |
| Budget.vue 硬编码 hex | 163 处 | 96 处（底色+鲜艳色+主题色） |
| Budget.vue 总行数 | 2450 | 2451（行数不变，只换写法） |

300/300 测试全绿，视觉无变化。

---

## v1.32.0 (2026-07-02)

### 前端组件瘦身 — 四波重构，净减 2086 行

延续 v1.31.0 的组件化方向，对两个臃肿视图（Budget.vue 3733 行、Dashboard.vue 2487 行）做四波渐进式重构，全程 300/300 测试保底、零视觉变化、零逻辑变化。

#### 第一波：清理死代码 CSS

- **Budget.vue 3733→2647**：删除被 `!important` 完全覆盖的第 1/2 层深色/亮色主题 CSS（~1030 行死代码），4 个无引用 `@keyframes`，5 个未定义 CSS 变量引用（`--text-primary` 等），第 3 层 205 处 `!important` 降级为普通声明
- **Dashboard.vue 2487→2449**：删除已下线的 `upload-overlay` 家族及 6 个孤儿选择器（`.btn.primary`/`.sortable-th`/`.table-footnote` 等）

#### 第二波：抽取 3 个共享 composables

- **`useFormatters.js`**：`formatNum` 参数化（`{nullText, min, max}`）+ `formatPercent`/`formatDelta`/`formatHistoryDateOnly`，消除三处 `formatNum` 重复（Dashboard/Budget/KeyIndicators 各不同小数位与占位符）
- **`useHistoryPanel.js`**：工厂模式 per-instance，按 `{type:'zaigong'|'budget'}` 分流 API，`viewHistorySnapshot` 返回 `{current, previous}` 供调用方各自 apply
- **`useFileUpload.js`**：工厂模式 per-instance，注入 `{requireTarget, processFile}`，共享 `triggerFileInput`/`handleFileChange`/`handleDrop`/`clearSelectedFile`
- `formatHistoryTime`/`formatFileDate` 复用 `useGlobalData` 已有实现，不再重复定义
- Dashboard 14 个、Budget 14 个同名函数全部消除

#### 第三波：Dashboard 拆分 3 个弹窗子组件

- **`FourClassWarningModal.vue`**：四类预警明细弹窗（单类/全部两种视图）
- **`ManagerDetailDrawer.vue`**：管理员明细抽屉（财务摘要 + 可排序工程表）
- **`TransferPriorityModal.vue`**：转固推进清单弹窗（目标测算 + 待转固表，`targetRate` v-model 双向绑定）
- **拆分策略**：状态 ref + 业务 computed 留 Dashboard（测试通过 `wrapper.vm.xxx` 访问 21 个标识符，零改动），子组件只搬 template + CSS + 纯展示函数，props 接收计算结果、emit 上抛操作
- Dashboard 2380→1796

#### 方向 1：KpiGrid + HistoryPanel 跨页面复用

- **`KpiGrid.vue`**：Dashboard KPI 指标卡网格，动画逻辑内化（`animatedValues`/`runCountUp`/`watch`），纯展示零事件
- **`HistoryPanel.vue`**：跨 Dashboard/Budget 复用历史面板，prop + scoped slot 接口
  - props：`visible`/`loading`/`records`/`currentRecordId`/`title`/`subtitle`/`kickerClass`
  - scoped slots：`#kpi-capital`/`#kpi-progress`/`#kpi-delta`/`#meta` 处理两页面 KPI 取数差异
  - 统一 var-based CSS，Budget 删除两处 hex 覆盖块，用 `:deep(.budget-kicker)` 保留主题色
- Dashboard 1796→1683，Budget 2550→2450
- 顺手清理 Budget 3 个孤儿 computed（`metrics`/`progressStatus`/`progressBadgeClass`，template 从未引用）

### 成果汇总

| 文件 | 最初 | 当前 | 变化 |
|---|---|---|---|
| Budget.vue | 3733 | 2450 | -1283 行 |
| Dashboard.vue | 2487 | 1683 | -804 行 |
| **合计** | 6220 | 4133 | **-2087 行** |

新增 6 个文件：3 composables（`useFormatters`/`useHistoryPanel`/`useFileUpload`）+ 5 子组件（`FourClassWarningModal`/`ManagerDetailDrawer`/`TransferPriorityModal`/`KpiGrid`/`HistoryPanel`），全部遵循现有 `<script setup>` + defineProps/defineEmits + JSDoc + scoped style 约定。

---

## v1.31.0 (2026-06-29)

### Vue Router + 共享 UI 组件重构

- **引入 Vue Router 4**：4 个视图从手动 `v-if` 切换升级为标准路由（`/`、`/zaigong`、`/budget`、`/archive`），支持 URL 导航、浏览器前进/后退、链接分享
  - 使用 `createWebHashHistory` 兼容 Electron `file://` 协议
  - 路由组件懒加载（`() => import()`）
  - `<keep-alive>` 保持页面状态
- **全局状态 Composable 化**：App.vue 47 个 ref 拆分为 3 个 composable：
  - `useGlobalData()` — 核心数据（在建工程/预算立项的 data/latest/date/warnings）
  - `useHistoryCenter()` — 历史记录面板、趋势图、双版本对比
  - `useAppTools()` — 数据管理面板、通知设置、简报生成、推送播报
  - 模块级 ref 单例，所有组件共享同一份状态
- **新增 4 个共享 UI 组件**（`src/components/`）：
  - `Modal.vue` — 通用弹窗壳（Teleport + Transition + 可配置尺寸）
  - `UploadZone.vue` — 拖拽上传区（拖拽/点击/文件选择/已选状态）
  - `DataCard.vue` — 数据指标卡片（标签/数值/单位/delta/徽标）
  - `FileRow.vue` — 文件列表行（扩展名徽标/文件名/元信息/操作区）
- **App.vue 瘦身**：2041 行 → ~500 行模板 + ~100 行脚本，视图切换、数据管理、历史中心逻辑全部下沉到 composable
- **视图组件适配**：Dashboard/Budget/KeyIndicators 通过 Proxy 实现 props 优先 + composable fallback，测试可继续传 props
- **测试全部通过**：300 个用例（6 个测试文件），适配 Vue Router 的 App.test.js 使用 `createMemoryHistory` 测试路由

---

## v1.30.0 (2026-06-29)

### 后端质量提升 — 部署可靠性 + 安全收敛

- **补全 `requirements.txt`**：新增 `pandas==2.2.0` 和 `Pillow==10.2.0`，此前这两个包被 7 个文件引用但未声明，新环境 `pip install -r requirements.txt` 必然崩溃
- **消除 `~/Downloads` 回退逻辑**：`build_zaigong_spend_summary_from_record()` 原先在数据库 `detail_data` 缺字段时会回退到硬编码 `~/Downloads` 搜索原始 Excel，服务器部署时静默失败。现已改为从 v1.29.0 新增的 `raw_data`（202 列全字段）中提取
- **统一 Session 管理**：`routers/budget.py` 中 5 处 `SessionLocal()` 改为 `get_db()`，全局一致
- **CORS 改为环境变量配置**：`main.py` 中 `allow_origins` 由硬编码 `localhost:5173` 改为读取 `CORS_ORIGINS` 环境变量（逗号分隔，默认不变）

### 前端测试体系建立 — 0 → 304 个用例

- **后端单测**：新增 `tests/test_analysis_services.py`，37 个用例覆盖核心算法：
  - `safe_float`（6）、`load_dataframe`（6）、`calculate_total_rate`（3）、`build_summary`（3）、`build_metrics`（4）、四类预警 TYPE A/B/C/D（11）、转固推进优先级（4）
- **前端单测**：基于 Vitest + @vue/test-utils 建立前端测试体系，304 个用例覆盖全部 5 个页面组件 + API 层：
  - `App.test.js`（26 个）：视图切换、计算属性、数据管理器、历史中心、投屏模式、工具函数、状态管理
  - `Dashboard.test.js`（87 个）：初始状态、数据加载、目标值输入、上传区、管理员表、四类预警、转固推进弹窗（computedTarget/displayManagers）、管理员详情抽屉（12 个 modalXxx computed）、KPI metrics、Progress summary、History comparison、事件发射
  - `Budget.test.js`（89 个）：初始状态、数据加载、标签切换、上传区、KPI 动画、计算属性、历史面板、工具函数、批次下达基础状态/计算属性/CRUD 操作/专业管理/切换与加载
  - `KeyIndicators.test.js`（60 个）：空状态、KPI 甜甜圈计算（4 个仪表盘）、deficit 逻辑、管理员视图、四类预警面板（11 个用例）、工具函数（gaugeColor/getDaysClass/getWarningPillClass/formatNum/getRateBarClass）、投屏模式、Summary banner、日期格式化、动画
  - `Archive.test.js`（35 个）：空状态、文件列表渲染、上传弹窗（年份/文件/拖拽）、预览面板（Excel/Word/不支持格式）、删除确认、工具函数
  - `api.test.js`（60 个）：覆盖全部 30+ 个 API 函数的 HTTP 方法、URL、参数拼装、默认值、边界条件（在建工程/预算/AI/通知/报告/档案/批次下达 7 大模块）
- **新增 npm scripts**：`npm run test`（一次性运行）、`npm run test:watch`（持续监听）
- **安装测试依赖**：`vitest`、`@vue/test-utils`、`jsdom`

### 文档同步

- 修正 README.md 中过时的设计语言描述（暗色玻璃拟态 → Editorial 暖纸色调）
- 更新 README.md 项目结构（补充 Archive.vue、`__tests__/` 目录、API 层说明）和测试用例数
- 补充 `.gitignore`：`backend/uploads/`、`.claude/`、`frontend/.claude/`
- 删除脚手架残留 `frontend/src/components/HelloWorld.vue`

---

## v1.29.0 (2026-06-26)

### 原始数据全字段存储 — 支持回溯查询

- **raw_data 字段**：上传 Excel 时自动保存原始文件全部 202 列数据到数据库 `raw_data` 字段（JSON 格式），不再仅保留 10 个分析字段
- **回溯查询能力**：后续可随时从数据库中查询任意原始字段（如安全生产费、开工日期、施工单位等），无需重新上传 Excel
- **向前兼容**：现有的 `detail_data`、`summary_data`、`metrics_data`、`four_class_warnings` 字段及前端展示逻辑不受影响
- **数据库迁移**：`zaigong_records` 表新增 `raw_data TEXT` 列，已有记录该字段为空，新上传的记录自动填充

---

## v1.28.0 (2026-05-12)

### 转固推进清单 — 新增施工单位列与导出扁平化

- **施工单位列**：转固推进清单新增"施工单位"列（位于工程名称后），数据来源于原始 Excel 的施工单位字段，需重新上传 Excel 后生效
- **导出 Excel 扁平化**：移除每个管理员的重复表头、组头说明行和小计行，改为单一表头 + 所有项目连续排列，便于筛选和排序
- **导出新增工程管理员列**：在序号与工程名称之间插入工程管理员列，方便按管理员筛选
- **Modal 宽度适配**：转固推进清单弹窗宽度从 1100px 扩展至 1240px，施工单位列限宽 120px 超长省略

---

## v1.27.0 (2026-04-27)

### 关键指标页面 — 布局精细化与交互对齐

- **KPI 卡片**：移除四张卡底部冗余叙事文字，信息层次更清晰
- **右侧面板均衡布局**：四类预警与管理员视图各占 50% 高度（flex 均分），warning-item 与 mgr-row 自动填满各自区域；进度条由 4px 加粗至 6px
- **四类预警条目精简**：移除每条重复的"预警期 60 天"副标题（标题栏已展示）
- **四类预警弹窗对齐**：弹窗样式、列宽、分组 header、导出按钮全面对齐在建工程页面；空分组自动隐藏；App.vue 传入 recordId 支持导出
- **投屏模式修复**：全屏下第 4 条预警项溢出问题（补全 overflow: hidden 与 min-height: 0 链路）；调整全屏下 section-head / warning-item padding 避免内容被裁切
- **四类预警管理员信息**：右列由"已触发 X · 预警 Y"改为按项目数排名的管理员姓名（如"魏东 3 · 张文 1"），右列固定宽 88px 保证数字竖向对齐
- **管理员视图表格**：列间距收窄（16px → 10px），列宽微调，转固率列头对齐修正

---

## v1.26.0 (2026-04-26)

### 关键指标页面 — 杂志式双栏布局重构

- 摘要文字移至顶部静态横幅，关键数字高亮
- KPI 环形图区域改为左栏 2×2 网格（110px donut），保留 delta 徽标与叙述文字
- 四类工程预警改为右栏卡片式 layout，与在建工程页面样式统一（pill 色标 + 横向 warning-item）
- 新增右栏底部「管理员视图」：在管项目数、本年支出、转固率进度条，数据复用在建工程 summary
- 左右两栏边框齐平，管理员表格列宽固定对齐，列间与边缘间距均等

---

## ~~v1.25.0 (2026-04-25) [临时版本 · 已回退]~~

### Dashboard整体重构 · 布局优化 · 与图表修复

#### 整体重构 

- 临时重构”在建工程”页面，实现”一页可读”效果，整体显示效果待进一步优化

#### 布局优化
- 删除顶部topbar，整合标题和按钮到页面头部区域
- 优化页面纵向结构，减少空间浪费

#### 图表修复
- 修复累计支出趋势图横坐标显示（改为月/日格式，如4/25）
- 修复图表数据源（使用后端metrics字段）
- 修复双Y轴刻度对齐问题（左边纵坐标和右边纵坐标各5个刻度）
- 修复管理员排名本年支出数据字段顺序

---

## v1.24.0 (2026-04-22)

### 批次下达 · 单元格批注功能

#### 表格批注显示
- 有批注的单元格右上角显示红色三角角标（仿 Excel 批注样式）
- 鼠标悬停时弹出批注内容卡片，使用 `position: fixed` 定位，不受横向滚动容器裁剪

#### 编辑弹窗新增批注输入
- 每个专业金额输入旁新增「批注」小按钮，点击展开文本域
- 已有批注的专业打开编辑弹窗时自动展开，按钮高亮为橙色
- 批注内容随金额数据一起保存，支持多行文本

#### 技术实现
- 后端：`budget_batches` 表新增 `notes TEXT` 列（JSON 格式 `{专业名: "批注文字"}`），`init_db()` 自动执行 `ALTER TABLE` 兼容已有数据库
- 专业重命名时自动同步 `notes` 字段中的 key，与 `amounts` 联动一致
- 前端：新增 `cellNoteVisible` / `cellNoteText` / `cellNoteX` / `cellNoteY` refs 及 `noteFieldsOpen` reactive 对象管理弹窗状态
- API：`getBatchData` 返回结构新增 `notes` 字段；`createBatch` / `updateBatch` 接受 `notes` 参数

---

## v1.23.0 (2026-04-22)

### 投资预算批次下达 · 完整功能上线

#### 新增「批次下达」Tab（预算立项页面）
- 预算立项页面顶部新增标签栏，在「预算执行」与「批次下达」之间切换
- 批次下达 tab 角标实时显示当前批次数量

#### 批次下达总览表
- 横向可滚动宽表格，行为批次、列为专业（23 个，可配置）
- 首行「预算下达合计」为所有批次各专业金额加总
- 无数据单元格显示「—」，负数（调减）显示为红色
- 顶部统计栏汇总：专业数 · 批次数 · 累计金额

#### 批次 CRUD
- 新增批次弹窗：批次日期、用途说明、各专业金额（3 列网格，支持负数）
- 弹窗底部实时显示本批小计
- 支持编辑已有批次、删除批次（含二次确认）

#### 专业列配置
- 右上角「管理专业」按钮打开侧边抽屉，支持添加、重命名、删除专业
- 重命名后所有历史批次 JSON 数据自动同步更新专业 key
- 默认内置 23 个专业（与省公司批次下达表对应）

#### 数据导入
- 2026 年已下达 7 批次数据已录入系统（合计 1,220.753 万元）

#### 技术实现
- 后端：新增 `BatchSpecialty` / `BudgetBatch` 数据模型，新增 `routers/budget_batch.py` 路由（含专业和批次完整 CRUD），`CORS` 新增 PUT / DELETE 方法支持
- 前端：`Budget.vue` 新增批次下达 tab、宽表格、CRUD 弹窗、专业管理抽屉，API 新增 9 个接口函数
- Excel 优化版：省公司批次下达表格优化版存档（`2026投资预算批次下达_优化版.xlsx`）

---

## v1.22.0 (2026-04-20)

### 数据档案库 · 年度文档存储与在线预览

#### 新增页面 — 数据档案
- 侧边栏新增「档案」分区入口，点击进入独立的「数据档案库」页面
- 三个固定分类，对应分公司年度核心文档：
  - **年度建设情况**：全年工程建设汇总、评分排名、专业指标（.xlsx）
  - **多年趋势汇总**：多年投资趋势、专业结构、省内排名对比（.xlsx）
  - **投资预算报告**：立项执行、招标结果、资本支出分析报告（.xlsx / .docx）
- 每个分类支持按年份上传，历年档案累积存储，无需覆盖旧数据

#### 上传功能
- 支持拖拽或点击选择文件（.xlsx / .xls / .docx / .pdf）
- 上传时可选择年份（当前年及前后共 6 年）、填写备注
- 文件存储在后端 `uploads/archive/` 目录，元数据（分类、年份、大小、上传时间）记录于数据库

#### 在线预览
- **Excel 文件**：使用 SheetJS 在浏览器端解析，表格完整渲染，支持多 Sheet 切换
- **Word 文件**：使用 mammoth.js 转换为 HTML 富文本，保留标题、段落、表格结构
- 预览以右侧滑出面板形式展现，不离开当前系统
- 预览面板内含直接下载按钮

#### 文件管理
- 每条档案显示：文件类型徽标、文件名、年份、大小、上传日期
- 支持下载原文件、删除档案（删除含二次确认弹窗）

#### 技术实现
- 后端：新增 `routers/archive.py`（FastAPI），新增 `ArchiveRecord` 数据库模型
- 前端：新增 `Archive.vue` 页面，安装 `xlsx`（SheetJS）与 `mammoth` npm 依赖
- API：新增 `uploadArchive` / `listArchives` / `getArchiveFileUrl` / `deleteArchive` 四个接口

---

## v1.21.0 (2026-04-20)

### UX/UI 全面优化 · 数据管理统一入口 · 关键指标动画修复

#### 全局 — 数据管理统一入口
- 新增侧边栏「数据管理」入口，整合两个数据源的上传操作
- 面板并排展示「在建工程明细总表」与「预算执行情况（预算占用）」，各含状态标签（已加载/未上传）、数据新鲜度提示（上传日期 · 距今 N 天，超 30 天变橙、超 60 天变红）
- 在建工程卡片内含当期资本性支出目标输入框，上传与目标设置合二为一
- 上传成功后自动刷新对应页面数据，无需手动切换
- 移除在建工程页面和预算立项页面各自的「替换源文件」按钮及弹窗，入口统一至侧边栏

#### 全局 — 侧边栏精简
- 删除「设计说明」页面及侧边栏入口，启动默认直达在建工程

#### 在建工程页面
- 管理员抽屉：「预警」行文字由金色改为黑色，剩余天数高亮同步改为黑色，阅读更清晰

#### 预算立项页面 — 按专业拆分表格
- 新增「预占用」独立列，展示已立项待审批金额（有值时显示橙色数字）
- 列宽通过 `<colgroup>` 固定，8 列均匀对齐
- 表头「占用结构」改为「预算使用进度」，「执行率」改为「支出完成率」，语义更白话
- 上传区文字居中对齐

#### 关键指标页面
- 修复 `watch` 未从 Vue 导入导致进入页面时 setup 函数报错、页面空白的问题
- 转固率卡片目标值由 80% 修正为 60%
- 4 个 donut 圆环与中心数值在数据加载时触发 900ms 缓出三次方 count-up 动画（与在建工程/预算立项 KPI 卡片一致）

---

## v1.19.0 (2026-04-18)

### 导航精简 + 页面切换 + KPI 动画 + 后端质量提升

#### 全局导航栏
- 右上角「手机简报」「推送播报」两个独立按钮合并为 ⋮ 竖点图标下拉菜单，减少导航栏拥挤
- 下拉菜单配色改为与主页面（analyst-mode）一致的白色/米色暖色风格，不再使用深色毛玻璃

#### 在建工程页面 — 上传/看板切换
- 「重新上传」按钮改为纯视图切换：点击跳转上传页但**不清除现有数据**
- 上传页右上角新增「返回看板」按钮，可无数据丢失地切回数据看板
- 成功上传新文件后自动切回看板视图

#### 在建工程页面 — KPI 数字动画
- KPI 卡片数值加载时以缓出三次方曲线做 900ms count-up 动画（requestAnimationFrame）
- 每次数据更新（含历史快照切换）自动重新触发动画

#### 后端 — AI 分析模块
- `get_db()` 会话管理简化，移除无效 `try/finally` 结构
- 新增 `_fetch_history_from_db()` 函数：分析时自动从数据库查询最近 6 期历史数据用于趋势分析，无需前端传入
- `call_minimax` max_tokens 从 1024 提升至 2048，减少 AI 输出被截断概率

#### 后端 — 单元测试
- 新增 `TestAIRouterUnit` 测试用例：风险等级边界、无预算数据、top 管理员排序、兜底分析结构验证
- 新增 `TestComputeTrendSignals` 测试类：无历史兜底、两期环比计算、情景预测排序、待收货激增风险、空数据库返回空列表
- 修复预存在的断言错误（`综合评估`→`综合定论`，`basis`→`verdict`），全部 16 个测试通过

#### Bug 修复
- 修复 `warningsUpdate` 事件未在 Dashboard `defineEmits` 中声明导致大量 Vue 警告的问题

---

## v1.18.0 (2026-04-07)

### UI 全面精细化 + 目标值在线编辑 + 历史中心趋势图

#### 在建工程页面
- 新增目标值在线编辑功能：展示模式下点击铅笔图标可直接修改当期目标值，回车或点击 ✓ 保存，ESC 取消
- 历史侧边栏信息密度提升：每条记录额外展示资本支出金额、支出进度、较上期变化

#### 预算立项页面
- 历史侧边栏信息密度提升：每条记录额外展示占用总额、立项进度、较上期变化
- 展开/收起按钮样式优化：高度缩小、背景色加深，与页面整体视觉区分度更强

#### 关键指标页面（大屏模式）
- 修复"驾舱"错别字 → "驾驶舱"
- 进入展示模式（全屏）后字体整体放大，提升远距演示可读性：
  - KPI 名称 17px、KPI 数值 22px、仪表盘 SVG 200×115px、重点工作标题 18px 等
- 内部导航栏仅在全屏展示模式下显示，普通分析模式不再叠加两层导航

#### 全局导航栏（大屏模式）
- 大屏模式导航栏高度与分析页面保持一致
- 分析专属按钮（历史记录、手机简报、推送播报、通知设置）在大屏模式下自动隐藏，避免拥挤
- 四个分析导航按钮图标由 Emoji 替换为 SVG 线条图标（一致性更强，暗/亮主题均清晰）

#### 四类工程预警卡片
- 鼠标悬停时轻微上移（translateY -2px）并显示彩色描边高亮，增强可点击指引

#### 历史记录中心 — 全面改版
- **头部**：移除英文 brand-kicker，改为时钟图标 + "历史记录中心" + 记录总数 badge；关闭按钮改为 SVG × 图标，带 hover 态
- **标签页**：外层新增 tab-rail 容器（圆角浅灰背景），按钮改为无边框样式内嵌，活跃态为渐变 pill + 阴影；"趋势图"标签带波形图标
- **分组标题**：改为全大写小字标签风格，右侧增加条目数量 badge；"返回最新"改为带刷新图标的 chip 按钮
- **历史卡片**：
  - 左侧新增彩色描边（在建工程=青色，预算立项=琥珀色）
  - 文件名加粗 13px，ID 改为右上角等宽字体 chip badge
  - 元数据改为横向 chip 标签行（上传时间 / 文件日期 / 目标值 各有颜色区分）
  - 在建工程卡片新增 KPI 数据行（支出进度 / 转固率 / 资本支出，三列等宽内嵌面板）
  - A/B 对比按钮改为紧凑 30×26px 方块，右对齐
- 深色/分析师两套主题 CSS 同步更新

#### 历史记录中心 — 趋势图标签页（新增）
- 新增"趋势图"标签，展示在建工程各期支出进度与转固率的 SVG 折线图
- 支出进度（青色）、转固率（琥珀色）双折线，带 60% 目标参考线
- X 轴为上传日期标签（斜 -35° 防重叠），Y 轴为 0–120% 网格
- 数据点悬停放大，标签在数据点 ≤ 8 时自动显示百分比值
- 数据不足 2 条时显示引导提示

#### 后端
- 新增 `POST /api/zaigong/history/{record_id}/target` 接口，支持在线修改目标值并同步更新 metrics_data 中的 year_target 字段
- 新增 `backend/routers/report.py`（简报图片生成路由）

#### Bug 修复
- 修复趋势图折线不显示的问题：历史 API 返回的 metrics 字段使用 `total_current` / `total_rate` 键名，与前端原先访问的 `capital` / `rate` 不一致，已修正

#### 前端 API
- 新增 `updateTargetValue(recordId, target)`
- 新增 `generateBriefImage(zaigongId, budgetId)`
- 新增 `exportTransferPriority(recordId, targetRate)`

---

## v1.17.0 (2026-04-04)

### 转固推进清单 Excel 导出 + 企业微信/飞书消息推送

#### 转固推进清单 Excel 导出
- 后端新增 `GET /api/zaigong/transfer-priority/{record_id}/export` 接口
  - 支持可选 `target_rate` 参数，按测算目标标记"需完成"项目
  - 使用 openpyxl 生成专业 Excel：per-manager 分节、navy 标题行、黄色/红色条件着色
  - Sheet 2 附说明页，文件名含日期与目标百分比
- 前端新增 `exportTransferPriority(recordId, targetRate)` API 函数
- 转固推进清单弹窗标题栏新增蓝色"导出 Excel"按钮，加载中防重复点击

#### 企业微信 / 飞书消息推送
- **后端新模块**
  - `models.py` 新增 `AppConfig` 表（键值对，存储 webhook URL 与自动推送开关）
  - `services/notify.py` 推送服务：根据 URL 自动识别平台（飞书/企业微信）
    - 飞书：Interactive Card 卡片格式，标题颜色随预警状态变化（红/橙/蓝）
    - 企业微信：Markdown 格式
    - 推送内容对应大屏模式四张卡片：立项进度、当期资本性支出、全年资本性支出、综合转固率
    - 四类预警按类型分组展示，每条目前加「剩余 N 天」标注
    - 使用 `trust_env=False` 绕过系统 SOCKS 代理
  - `routers/notify.py` 新路由（`/api/notify`）
    - `GET /config` — 查询配置（URL 脱敏）
    - `POST /config` — 保存 webhook URL 与自动推送开关
    - `POST /config/clear` — 清除配置
    - `POST /test` — 发送测试消息（无输入时自动使用已保存 URL）
    - `POST /push/{record_id}` — 手动推送（同时加载最新预算数据）
  - `main.py` 注册 `/api/notify` 路由
  - `routers/analysis.py` 上传成功后若开启自动推送则后台触发

- **前端**
  - `api/index.js` 新增：`getNotifyConfig`、`saveNotifyConfig`、`clearNotifyConfig`、`testNotifyWebhook`、`pushNotify`
  - 导航栏右侧新增 🔔 通知设置按钮（已配置时显示绿色）
  - 点击 🔔 弹出设置面板：填写 Webhook URL、自动推送开���、测试消息、保存/清除
  - 导航栏新增 📤 推送播报按钮（已配置 + 有数据时显示，绿色调）
    - 推送当前最新加载数据，不依赖历史快照视图状态
  - `Dashboard.vue` 新增 `initialRecordId` prop，修复自动加载时 currentRecordId 未设置导致推送按钮不显示的问题
  - `App.vue` 自动加载时保存 `zaigongLatestRecordId`，传入 Dashboard 组件

#### Bug 修复
- 修复四类预警推送显示"暂无"：存储结构为 `{items: [{type, name, manager, daysLabel, ...}]}` 列表，原代码错误按顶层 key 读取
- 修复测试消息报错"请先输入 Webhook URL"：已配置时测试接口自动使用保存的 URL

#### 待办清单更新
- [x] 预警提醒/推送功能 — v1.17.0 已实现（飞书 + 企业微信 Webhook）
- [x] 转固推进清单导出 Excel — v1.17.0 已实现

---

## v1.16.0 (2026-04-03)

### 四类工程预警明细弹窗优化

#### 前端
- 明细表格列调整为：状态、工程名称、验收类型、管理员、关键日期、截止日期、工程状态、天数、处置建议
- 移除编号、一级专业列
- 弹窗标题样式优化：标题字体加大（16px），数据日期字体变小跟在标题后面
- 导出预警清单按钮移至弹窗右上角，优化按钮样式
- 处置建议列支持换行显示
- 整体弹窗和单类型弹窗显示格式统一
- 工程状态列宽加大确保显示完整
- 编号表头设置不换行

#### 页面样式统一
- 四类工程预警模块标题、各工程管理员汇总、当期资本性支出进度三个模块标题字体大小统一为 15px
- 移除各工程管理员汇总卡片右上角的"X位管理员"字样

#### 文档
- 更新 `docs/prd.md`（版本升至 v1.3，补充四类工程预警明细弹窗说明）
- 更新 `docs/requirements.md`（补充弹窗样式与列字段说明）

---

## v1.15.0 (2026-03-31)

### 四类工程预警模块

#### 后端
- 新增 `build_four_class_warnings()` 算法函数，实现四类工程判断逻辑
- 新增 `GET /api/zaigong/four-class-warnings/{record_id}` 接口返回预警结果
- 新增 `GET /api/zaigong/four-class-warnings/{record_id}/export` 接口导出预警 Excel
- 数据库 `zaigong_records` 表新增 `four_class_warnings` 字段存储预警结果 JSON
- 预警数据过滤：排除「局房及基础设施」和「工程已关闭」的记录
- Excel 导出字体统一使用「微软雅黑」

#### 前端（在建工程页面）
- 新增四类工程预警面板：四张统计卡片横排（列账不及时、预转固不及时、关闭不及时、长期挂账）
- 每张卡片显示「已触发 / 预警」数量
- 点击卡片展示该类型明细弹窗
- 点击模块标题展示全部预警明细（按四类分组显示）
- 预警明细弹窗中：剩余天数 ≤ 30 天的项目天数列显示 ⚠️ 图标
- 导出预警清单按钮，支持中文文件名下载
- 点击「当期资本性支出进度」行展开/收起「各工程管理员汇总」表格

#### 算法规则
- TYPE A 列账不及时：初验批复后收货率 < 85% 已触发 / 85%~90% 预警
- TYPE B 预转固不及时：初验批复后 60 天内未完成预转固
- TYPE C 关闭不及时：一次验收终验后 150 天 / 两次验收 90 天内未正式转固
- TYPE D 长期挂账：实际工期超建议工期 2 倍
- 预警窗口：60 天

#### 文档
- 更新 `docs/requirements.md`：补充四类工程预警展示区需求与数据口径
- 更新 `docs/prd.md`：补充四类工程预警功能范围与数据口径

---

## v1.14.0 (2026-03-28)

### 大屏展示页 UI 全面改版 + AI 模块可视化重构

#### 大屏展示页 UI（暗色玻璃拟态风格）

- 整体视觉基调：背景 `#080C12`，玻璃拟态卡片（半透明 + `backdrop-filter: blur(12px)`），极细边框
- 引入 Google Fonts：DM Sans（正文）+ DM Mono（数字/金额）
- 四张 KPI 指标卡各用独立主色（紫/青/蓝/红），顶部 2px 渐变描边
- 仪表盘全部改为 SVG 弧线（`stroke-dashoffset` 绑定数据 + 描边动画）
- 卡片入场动画：`fadeSlideUp` + 仪表盘描边 `gaugeDraw`
- 转固率异常 badge 带 `pulse-red` 脉冲动画

#### 大屏专用导航栏

- 左侧：品牌 Logo（32×32px 渐变方块）+ "工程建设数据驾舱"标题
- 中部：绿色脉冲点 + "实时数据 · 日期 · 仙桃分公司 云网发展部"
- 右侧：进入/退出展示模式按钮（根据状态动态切换文字和图标）
- 全屏模式：进入后铺满整个屏幕，去掉四周留白，导航栏和卡片区域自适应

#### AI 工程进度分析模块重构（可视化呈现）

- 状态行：状态点（带光晕）+ 状态词 + 一句话摘要（40字截断）
- 三格指标：标题 + 关键数字 + 28-50字判断文字
- 重点动作：优先级 tag（紧急/重要/跟进）+ 动作文本 + 责任人 chip
- 新增 computed：`overallStatus`（状态等级）、`summaryOneLiner`、`isHighRisk`、`parsedActions`（含责任人提取）、`progressKeyNum`、`expendKeyInfo`
- AI 内容后处理 `sanitizeAIContent`：自动将"差距 0.00 万元"、"缺口 0.00 万元"替换为"已达标"

#### TODO 事项优化

- 责任人显示改为"责任人：XX"格式
- 责任人使用红色字体（`var(--red)`）
- 完成日期使用白色字体
- 编辑/删除按钮在全屏模式下自动隐藏（`v-if="!presentationMode"`）

#### API Key 安全加固

- MiniMax API Key 从 `.env` 文件迁移到系统环境变量 `~/.zshrc`
- `.env` 文件仅保留占位符和注释
- 后端启动时通过 `env` 命令传递环境变量

#### 验收
- 前端构建通过：`npm run build`
- 后端 API 测试通过：`curl` 验证 `/api/ai/analyze` 返回正常

---

## v1.13.1 (2026-03-27)

### AI 工程进度分析二次升级

#### 前端
- `KeyIndicators.vue` 的 AI 请求扩展为“在建工程指标 + 预算指标 + 管理员月度推进明细 + 分析日期”
- AI 分析结果新增“分析依据”展示区，便于解释结论来自哪些数字
- AI 本地缓存键升级为 `ai_analysis_cache_v2`，避免继续复用旧版分析结果
- AI 缓存快照补充预算侧指标与管理员月度支出/结转额，缓存失效判断更准确

#### 后端
- `/api/ai/analyze` 请求体新增 `budget` 与 `analysis_date` 上下文字段
- AI 分析前先计算规则信号：当前月份应有节奏、目标缺口、预算支出兑现差、风险等级、异常管理员等
- AI prompt 升级为“先判断、再归因、再给动作”的固定模板，并要求结论尽量引用具体数字
- AI 结构化返回新增 `basis`（分析依据）和 `signals`（规则信号）字段
- fallback 分析同步升级为预算联动 + 风险分级逻辑，避免空响应时退回到过于泛化的文案

#### 文档
- 更新项目总 README、前端 README 和 AI 设计规格，补充新版输入、输出与展示规则

#### 验收
- 前端构建通过：`npm run build`
- 后端 AI 单测通过：`pytest backend/tests/test_ai_router_unit.py`

---

## v1.13.0 (2026-03-26)

### 关键指标页聚焦重排 + AI 结构化输出

#### 前端
- 关键指标页移除顶部状态模块干扰（在“关键指标”视图下隐藏“当前视图/数据准备度/在建工程/预算立项”）
- 三大进度卡片整体缩紧，进度环重绘为更细致的渐变环样式
- 关键指标页布局调整为更聚焦的“3 指标 + AI 分析 + 近期重点工作”
- 移除关键指标页底部汇总条，减少非核心信息
- AI 分析区新增“管理汇报版 / 执行推进版”风格切换
- AI 分析渲染改为结构化区块 + 重点动作列表，提升可读性

#### 后端
- `/api/ai/analyze` 支持 `style` 参数（`management` / `execution`）
- AI prompt 改为固定 JSON 输出协议，后端统一做结构化解析
- 返回体新增 `structured` 和 `style` 字段，保留 `content` 兼容旧前端
- AI 解析失败时增加结构化兜底结果，避免前端空白

#### 验收
- 前端构建通过：`npm run build`
- 后端 AI 单测通过：`python -m pytest backend/tests/test_ai_router_unit.py -v`（6 passed）

---

## v1.12.1 (2026-03-26)

### 交付收口与文档同步

#### 文档
- 同步更新 `docs/prd.md`（版本升至 v1.1，补充关键指标页 AI 与重点工作范围）
- 同步更新 `docs/requirements.md`（补充 AI 分析与重点工作的展示与规则）
- 同步更新 `frontend/README.md`（补充 AI 分析与重点工作模块说明）

#### 验收
- 前端构建复验通过：`npm run build`
- 后端全量测试在本机环境触发 NumPy 初始化崩溃（非业务断言失败），当前已保留可用的 AI 路由单测作为回归兜底

---

## v1.12.0 (2026-03-26)

### 关键指标页 AI 升级与重点工作模块

#### 后端
- 新增 AI 路由：`/api/ai/status`、`/api/ai/analyze`
- 新增 MiniMax 环境变量模板：`backend/.env.example`
- 新增 `python-dotenv` 依赖并补充环境加载兜底，未安装依赖时不会导致后端直接崩溃
- AI 返回解析支持多种结构回退（`message.content`、`messages[0].text`、`reply`、`text`）
- 新增 AI 路由单元测试：`backend/tests/test_ai_router_unit.py`

#### 前端
- `KeyIndicators.vue` 新增 AI 工程进度分析区块（状态检查、手动刷新、缓存、缓存失效提示）
- `KeyIndicators.vue` 新增近期重点工作区块（新增、编辑、删除、完成状态切换）
- 重点工作与 AI 分析结果使用 `localStorage` 持久化
- 前端 API 新增：`generateAIAnalysis`、`getAIStatus`

#### 质量验证
- 前端构建通过：`npm run build`
- 后端语法检查通过：`python -m py_compile backend/main.py backend/routers/ai.py`
- AI 单元测试通过：`python -m pytest backend/tests/test_ai_router_unit.py -v`

---

## v1.11.0 (2026-03-25)

### 全局历史记录中心与双版本对比

#### 后端
- 预算上传结果正式保存到 `budget_records`，补齐预算历史持久化能力
- 新增 `/api/budget/history` 接口获取预算历史记录列表
- 新增 `/api/budget/history/{id}` 接口获取预算历史快照
- 预算历史快照接口返回“当前记录 + 上一条记录”，支持前端历史中心双版本对比
- 补充预算历史记录与快照接口测试

#### 前端
- 顶部导航新增“历史记录”统一入口
- 新增全局历史记录中心，支持按“全部 / 在建工程 / 预算立项”查看历史版本
- 历史中心支持为同一模块选择两条记录，分别设为 `A` / `B`
- 对比结果统一收口到历史记录中心，并明确展示两条记录的对比日期
- 在建工程历史对比精简为：资本性支出进度、转固率、管理员推进 Top 5
- 预算立项历史对比精简为：年度预算、立项进度、专业推进 Top 5
- 在建工程页和预算立项页不再直接展示历史对比结果，仅保留历史快照查看

---

## v1.10.0 (2026-03-24)

### 前端界面重构与交互修复

#### 顶部与页面框架
- 顶部区域改为标题条加 4 个状态模块
- 弱化首页大段说明文字，提升工作台信息密度
- 在建工程页与预算立项页统一为双栏上传区布局

#### 在建工程页面
- 上传区改为与预算立项一致的上传卡结构和动效
- 目标输入移动到左侧说明区下方
- 删除上传区步骤说明块
- 目标金额改为用户手动输入，不再展示默认目标提示
- 修复上传后最高值高亮计算异常问题

#### 预算立项页面
- 上传区和数据页视觉层级重构
- 上传说明文案压缩，模块间距和卡片比例重新统一
- 项目明细 sheet 改为自动兼容不同年份命名

#### 关键指标页面
- 修复资本性支出目标值固定回退到 503 的问题
- 资本性支出进度卡片改为显示真实上传目标，缺失时显示 `—`

#### 前后端契约与工程性优化
- 前端上传在建工程文件时会携带目标值参数
- `frontend/src/api/index.js` 支持 `VITE_API_BASE`
- 补充图表 `resize` 监听清理和实例销毁逻辑
- 补充预算 sheet 年份兼容和目标值透传相关测试代码

---

## v1.9.0 (2026-03-22)

### 工程明细弹窗功能

#### 后端
- 新增 `/api/zaigong/manager-details` 接口获取指定管理员的工程明细
- `detail_data` 字段存储工程维度明细数据
- 支持按管理员名称筛选

#### 前端
- 点击工程管理员名称弹出明细弹窗
- 明细表格包含 7 列：工程名称、结转额、本年累计资本性支出、已下单待收货、本月资本性支出、在建工程期末余额、转固率
- 每列支持升序/降序排序（点击表头切换）
- 弹窗关闭按钮和遮罩层点击关闭

---

## v1.8.0 (2026-03-22)

### 数据持久化与对比功能

#### 后端
- 新增 SQLite 数据库存储上传记录
- 新增 `/api/zaigong/history` 接口获取历史记录列表
- 新增 `/api/zaigong/compare` 接口获取最近两条数据对比
- 从文件名提取日期识别数据（如 "xxx(20260320).xlsx" → "20260320"）
- 相同文件名上传时自动覆盖已有记录
- 按文件名日期排序进行数据对比（最新日期 vs 日期最近的历史数据）

#### 前端
- 工程管理员支出排名图表显示支出较上期变化
  - 有变化：红色向上箭头↑ + 变化值（有变化时）
  - 无变化：灰色横线― + 0.00
- 各工程管理员汇总表格新增「较上期变化」列
- 上传成功后自动获取对比数据
- 页面切换后保持对比数据

### 自动化测试
- 新增 pytest 测试框架
- API 接口测试（上传、查询、对比）
- 数据分析逻辑单元测试
- 测试命令：`python -m pytest tests/ -v`

---

## v1.7.0 (2026-03-22)

### 在建工程页面上传流程优化

- 整合目标设置和文件上传到同一卡片
- 输入目标金额后点击按钮上传
- 删除独立的拖拽上传框（简化界面）

### 数据展示页面布局优化

- 删除「调整目标」模块
- 保留大进度仪表盘展示
- 工程管理员排名图表
- 汇总表格展示

---

## v1.6.0 (2026-03-22)

### UI/UX 大改版

#### 导航栏优化
- 品牌图标添加呼吸发光效果
- 标签按钮更大更醒目（15px 字体）
- 渐变边框和悬停光晕效果
- 数据指示点动画

#### 上传页面优化
- 目标设置卡片更精致紧凑
- 旋转虚线边框装饰
- 动画光晕背景

#### 数据展示优化
- 指标卡片带底部光晕
- 数字使用 Orbitron 等宽字体
- 表格更精致带悬停效果
- 进度条渐变色设计
- 加载动画更现代

#### 进度仪表盘美化
- 更大的圆环尺寸（320px）
- 中心显示完成百分比
- 进度条发光效果
- 多层装饰环增加质感

---

## v1.5.0 (2026-03-22)

### 分析日期显示

- 在建工程分析页面显示分析日期
- 预算立项页面显示分析日期
- 日期自动记录为上传时间
- 关键指标页面汇总显示各分析日期

---

## v1.4.0 (2026-03-22)

### 数据状态保持

- 上传数据后切换页面保持数据不丢失
- 导航栏显示数据指示点
- 关键指标页面入口权限控制（需上传两个分析数据）

---

## v1.3.0 (2026-03-22)

### 关键指标进度页面

- 新增关键指标页面，展示三大核心指标：
  - 资本性支出进度
  - 立项进度
  - 综合转固率
- 大圆环仪表盘可视化
- 底部汇总信息栏
- 实时时钟显示

---

## v1.2.0 (2026-03-22)

### 预算分析功能

- 新增预算分析 API 和页面
- 支持上传「预算执行情况（预算占用）」Excel 文件
- 各专业预算立项进度表格展示
- 2026年新建项目明细表格展示
- 立项进度计算和展示

---

## v1.1.0 (2026-03-22)

### 新增页面导航

- 在建工程分析页面
- 预算下达及立项页面
- 顶部导航栏切换
- 数据上传后标签页显示指示点

---

## v1.0.0 (2026-03-22)

### 首次发布

#### 后端
- 基于 FastAPI 构建 RESTful API
- 在建工程分析服务：读取 Excel、计算转固率、汇总数据
- 预算分析服务：读取预算文件、提取立项进度
- 支持文件上传和跨域访问

#### 前端
- Vue 3 + Vite 项目初始化
- 深色科技风格 UI 设计
- 响应式布局适配

---

## 待完善功能

以下功能为规划中，尚未实现：

- [x] 数据持久化（数据库存储） - v1.8.0 已实现
- [ ] 目标金额本地记忆
- [ ] Excel 报告导出功能
- [ ] PDF 报告生成
- [ ] 用户登录系统
- [ ] 多用户权限管理
- [ ] 定时自动抓取最新文件
- [ ] 移动端适配优化
- [x] 数据对比功能（按文件名日期对比） - v1.8.0 已实现
- [x] 工程明细弹窗（点击管理员查看明细） - v1.9.0 已实现
- [x] 四类工程预警功能 - v1.15.0 已实现
- [x] 预警提醒/推送功能（飞书 + 企业微信 Webhook）- v1.17.0 已实现

---

## 版本历史说明

| 版本号 | 日期 | 主要内容 |
|---|---|---|
| v1.36.0 | 2026-08-31 | 月报简报重构（HTML 卡片版式 + Playwright 高清渲染，四圆环口径对齐）、管理员导出新增全部工程汇总页、ANALYSIS_DB_PATH 演示隔离（后端测试 152→178 例） |
| v1.35.0 | 2026-07-29 | P0 数字信任：口径黄金样例测试、上传校验摘要、一键备份/恢复、历史快照语义写死、文档对齐（后端测试 124→136 例） |
| v1.34.5 | 2026-07-23 | P0 工程卫生：前后端版本对齐、Electron 后端绑定 127.0.0.1、仓库清理、四类预警补施工单位列（+8 测试） |
| v1.34.4 | 2026-07-09 | 预算路由补集成测试 +22 例（覆盖上传→汇总→对比→快照算钱链路），删除 PRD 过时的本地回查限制 |
| v1.34.3 | 2026-07-08 | 后端健壮性：月报字体跨平台化（macOS/Win/Linux 候选解析）、7 处路由错误脱敏、补后端日志基础设施 |
| v1.34.2 | 2026-07-06 | 后端 4 路由补集成测试 +41 例（archive/notify/report/budget_batch）、堆栈泄露修复、上传扩展名与大小校验 |
| v1.34.1 | 2026-07-06 | 抽 shared.css 第一波（.btn/.rate-badge 全局共享，:where 零特异性），清理 5 处副本净减 19 行 |
| v1.34.0 | 2026-07-06 | Budget 批次管理弹窗+专业抽屉抽为 BatchManageModal 子组件，Budget.vue -175 行 |
| v1.33.0 | 2026-07-03 | Budget CSS 治理：!important 279→0 清零，文字/边框中性色 hex → Editorial token（~50 处） |
| v1.32.0 | 2026-07-02 | 前端四波重构净减 2086 行：死代码 CSS 清理、3 个共享 composables、Dashboard 拆 3 弹窗组件、KpiGrid/HistoryPanel 跨页复用 |
| v1.31.0 | 2026-06-29 | 引入 Vue Router 4（hash 模式兼容 Electron）、全局状态拆 3 个 composable 单例、新增 4 个共享 UI 组件、App.vue 2041→600 行 |
| v1.30.0 | 2026-06-29 | 后端质量提升（requirements 补全、Downloads 回退消除、CORS 环境变量）、前端测试体系建立（93 个用例）、文档同步 |
| v1.29.0 | 2026-06-26 | 原始数据全字段存储（raw_data 202列入库，支持回溯查询，前端无影响） |
| v1.28.0 | 2026-05-12 | 转固推进清单新增施工单位列、导出扁平化、导出新增工程管理员列 |
| v1.27.0 | 2026-04-27 | 关键指标页精细化（KPI 卡精简、右栏均衡布局、预警弹窗对齐、投屏修复、管理员信息替换、数字对齐） |
| v1.26.0 | 2026-04-26 | 关键指标页杂志式双栏布局重构（摘要横幅、KPI 左栏 2×2、预警右栏卡片式、新增管理员视图） |
| v1.25.0 | 2026-04-25 | Dashboard 整体重构（一页可读、布局优化、图表修复）[已回退] |
| v1.24.0 | 2026-04-22 | 批次下达单元格批注功能（红色角标、悬停卡片、编辑弹窗批注输入） |
| v1.23.0 | 2026-04-22 | 投资预算批次下达完整上线（批次总览表、批次 CRUD、专业列配置、7 批数据录入） |
| v1.22.0 | 2026-04-20 | 数据档案库（三类年度文档存储、上传/下载/删除、Excel/Word 在线预览） |
| v1.21.0 | 2026-04-20 | UX/UI 全面优化（数据管理统一入口、侧边栏精简、预算页按专业拆分表格、KPI 动画修复） |
| v1.19.0 | 2026-04-18 | 导航精简、页面切换保留数据、KPI 数字动画、AI 模块后端优化、单元测试补充 |
| v1.18.0 | 2026-04-07 | UI 精细化（大屏模式、按钮图标、预警卡 hover）、目标值在线编辑、历史中心全面改版（卡片 KPI、趋势图标签页）、趋势折线 bug 修复 |
| v1.17.0 | 2026-04-04 | 转固推进清单 Excel 导出、飞书/企业微信推送（四卡片指标 + 四类预警含剩余天数）、推送按钮移至导航栏 |
| v1.16.0 | 2026-04-03 | 四类工程预警明细弹窗优化（列宽调整、样式统一、导出按钮位置优化） |
| v1.15.0 | 2026-03-31 | 四类工程预警模块（四类判断算法、预警卡片、分类明细弹窗、Excel 导出、60 天预警窗口、各工程管理员汇总展开收起） |
| v1.14.0 | 2026-03-28 | 大屏展示页暗色玻璃拟态改版、AI 模块可视化重构、全屏模式优化、TODO 优化、API Key 安全加固 |
| v1.13.1 | 2026-03-27 | AI 工程进度分析二次升级（预算联动、规则信号、basis 字段） |
| v1.13.0 | 2026-03-26 | 关键指标页聚焦重排、AI 结构化输出、风格切换（管理/执行） |
| v1.12.0 | 2026-03-26 | 关键指标页 AI 分析、重点工作模块、AI 后端路由与单测 |
| v1.11.0 | 2026-03-25 | 全局历史记录中心、预算历史持久化、双版本历史对比 |
| v1.10.0 | 2026-03-24 | 前端界面重构、目标值链路修复、预算 sheet 年份兼容 |
| v1.9.0 | 2026-03-22 | 工程明细弹窗功能 |
| v1.8.0 | 2026-03-22 | 数据持久化与对比功能 |
| v1.7.0 | 2026-03-22 | 上传流程和布局优化 |
| v1.6.0 | 2026-03-22 | UI/UX 大改版 |
| v1.5.0 | 2026-03-22 | 分析日期显示 |
| v1.4.0 | 2026-03-22 | 数据状态保持 |
| v1.3.0 | 2026-03-22 | 关键指标进度页面 |
| v1.2.0 | 2026-03-22 | 预算分析功能 |
| v1.1.0 | 2026-03-22 | 页面导航系统 |
| v1.0.0 | 2026-03-22 | 项目初始化，基础框架搭建 |

---

*最后更新：2026-08-31*
