# 大屏展示页 UI 改版规格文档
# 目标文件：src/views/KeyIndicators.vue
# 供编程智能体直接执行，不要创造文档以外的设计决策

---

## 一、任务说明

将现有 KeyIndicators.vue 的视觉风格升级为「暗色玻璃拟态」风格。
数据来源、API 调用、props 接口全部保持不变，只替换模板结构和样式。

---

## 二、整体视觉基调

- 背景：#080C12（近黑，不是纯黑）
- 卡片：半透明玻璃质感，backdrop-filter: blur(12px)
- 边框：极细，rgba(255,255,255,0.07)，hover 时 rgba(255,255,255,0.14)
- 字体：DM Sans（正文）+ DM Mono（所有数字金额）
- 颜色：四张指标卡各用一个主色（紫/青/蓝/红），不要全部用同一个颜色
- 动效：卡片入场 fadeSlideUp + 仪表盘弧线描边动画

---

## 三、引入字体

在 index.html 的 `<head>` 中添加：

```html
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
```

---

## 四、CSS 变量（在组件 `<style>` 顶部声明）

```css
:root {
  --bg-deep:     #080C12;
  --glass:       rgba(255,255,255,0.04);
  --glass-2:     rgba(255,255,255,0.07);
  --border-dim:  rgba(255,255,255,0.07);
  --border-glow: rgba(255,255,255,0.14);

  --text-1: #F0F2F5;
  --text-2: #8B9099;
  --text-3: #4A505A;

  --cyan:       #22D3EE;
  --cyan-dim:   rgba(34,211,238,0.12);
  --blue:       #60A5FA;
  --blue-dim:   rgba(96,165,250,0.12);
  --violet:     #A78BFA;
  --violet-dim: rgba(167,139,250,0.12);
  --amber:      #FBBF24;
  --amber-dim:  rgba(251,191,36,0.12);
  --red:        #F87171;
  --red-dim:    rgba(248,113,113,0.14);
  --green:      #34D399;
  --green-dim:  rgba(52,211,153,0.12);

  --font: 'DM Sans', system-ui, sans-serif;
  --mono: 'DM Mono', 'Courier New', monospace;
}
```

---

## 五、页面背景

```css
/* body 或最外层容器 */
background: var(--bg-deep);
font-family: var(--font);
min-height: 100vh;

/* 背景光晕层，position:fixed，z-index:0，pointer-events:none */
background:
  radial-gradient(ellipse 60% 50% at 20% 10%, rgba(96,165,250,0.07) 0%, transparent 70%),
  radial-gradient(ellipse 50% 40% at 80% 80%, rgba(34,211,238,0.06) 0%, transparent 70%),
  radial-gradient(ellipse 40% 30% at 60% 30%, rgba(167,139,250,0.05) 0%, transparent 70%);
```

页面内容层 z-index: 1，padding: 20px 28px 28px，display:flex，flex-direction:column，gap:18px。

---

## 六、导航栏（大屏专用，替换原有导航）

大屏页导航不显示「在建工程 / 预算立项 / 历史记录」这些后台入口，只保留三个元素：

```
高度：44px，display:flex，align-items:center

左侧 — 品牌区：
  Logo 方块：32×32px，border-radius:9px
  背景：linear-gradient(135deg, #60A5FA 0%, #22D3EE 100%)
  box-shadow：0 0 16px rgba(34,211,238,0.3)
  文字：ZT，11px，DM Mono，#fff

  系统名称：工程建设数据驾舱，18px，font-weight:500，color:var(--text-1)，letter-spacing:-0.3px

中部 — 实时状态（flex:1，justify-content:center）：
  绿色脉冲小圆点：5px，background:var(--green)，box-shadow:0 0 6px var(--green)
  文字：实时数据 · 2026-03-27 · 仙桃分公司 云网发展部
  样式：12px，color:var(--text-2)，font-family:var(--mono)

右侧 — 退出按钮：
  文字：退出展示模式
  样式：padding:5px 13px，border-radius:20px
  border：0.5px solid rgba(96,165,250,0.3)
  background：rgba(96,165,250,0.12)
  color：var(--blue)
  点击后跳转回 /（或调用原有路由逻辑）
```

---

## 七、四张 KPI 指标卡

### 布局

```css
display: grid;
grid-template-columns: repeat(4, 1fr);
gap: 14px;
```

### 卡片基础样式（所有卡片共用）

```css
.kpi-card {
  background: var(--glass);
  border: 0.5px solid var(--border-dim);
  border-radius: 16px;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  padding: 22px 22px 18px;
  position: relative;
  overflow: hidden;
  transition: border-color .3s;
}
.kpi-card:hover {
  border-color: var(--border-glow);
}
/* 卡片顶部光泽 */
.kpi-card::before {
  content: '';
  position: absolute; inset: 0;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, transparent 60%);
  pointer-events: none;
}
/* 顶部渐变描边，高度2px */
.kpi-card::after {
  content: '';
  position: absolute; top: 0; left: 0; right: 0;
  height: 2px;
  border-radius: 16px 16px 0 0;
}
```

### 四张卡的顶部描边颜色（::after）

```css
/* 卡1 立项进度 */
.kpi-card.violet::after {
  background: linear-gradient(90deg, transparent, #A78BFA, transparent);
}
/* 卡2 当期资本支出 */
.kpi-card.cyan::after {
  background: linear-gradient(90deg, transparent, #22D3EE, transparent);
}
/* 卡3 全年资本支出 */
.kpi-card.blue::after {
  background: linear-gradient(90deg, transparent, #60A5FA, transparent);
}
/* 卡4 综合转固率 */
.kpi-card.red::after {
  background: linear-gradient(90deg, transparent, #F87171, transparent);
}
```

### 卡片内部结构（从上到下）

```
① 顶行（flex，justify-content:space-between，margin-bottom:16px）
   左：小图标块（30×30px，border-radius:8px，dim背景色）
   右：badge 标签

② 指标名（12px，color:var(--text-2)，margin-bottom:10px）

③ 仪表盘 SVG（见第八节）

④ 水平分隔线（height:0.5px，background:var(--border-dim)，margin:14px 0）

⑤ 两格 meta 数据（grid，2列，gap:6px）
   每格：background:rgba(255,255,255,0.03)，border-radius:8px，padding:8px 10px
     - 标签：10px，color:var(--text-3)，margin-bottom:4px
     - 数值：14px，font-weight:500，font-family:var(--mono)，对应颜色
     - 单位：10px，color:var(--text-3)，margin-top:1px

⑥ 日期（11px，color:var(--text-3)，font-family:var(--mono)，margin-top:12px）
```

### 四张卡的具体配置

**卡1 — 立项进度（.violet）**
```
图标背景：var(--violet-dim)
badge：预算，背景:var(--violet-dim)，色:var(--violet)，边框:rgba(167,139,250,0.25)
仪表盘颜色：#7C3AED → #A78BFA（渐变），数字颜色：var(--violet)
meta左：已占用，数值颜色：var(--violet)
meta右：预占用，数值颜色：var(--text-2)
```

**卡2 — 当期资本性支出进度（.cyan）**
```
图标背景：var(--cyan-dim)
badge：当期，背景:var(--cyan-dim)，色:var(--cyan)
仪表盘颜色：#0891B2 → #22D3EE，数字颜色：var(--cyan)
meta左：已完成，数值颜色：var(--cyan)
meta右：目标，数值颜色：var(--text-2)
```

**卡3 — 全年资本性支出进度（.blue）**
```
图标背景：var(--blue-dim)
badge：全年，背景:var(--blue-dim)，色:var(--blue)
仪表盘颜色：#1D4ED8 → #60A5FA，数字颜色：var(--blue)
meta左：年度支出，数值颜色：var(--blue)
meta右：年度预算，数值颜色：var(--text-2)
```

**卡4 — 综合转固率（.red）**
```
图标背景：var(--red-dim)
badge：⚠ 转固率异常，背景:var(--red-dim)，色:var(--red)
      border:0.5px solid rgba(248,113,113,0.3)
      带 pulse-red 动画（见第九节）
仪表盘颜色：#991B1B → #F87171，数字颜色：var(--red)
meta左：当前转固率，数值颜色：var(--red)
meta右：年度目标，数值颜色：var(--amber)，单位显示"差距 Xpct"
```

---

## 八、仪表盘 SVG 规范

### 模板结构

```html
<svg width="140" height="80" viewBox="0 0 140 80">
  <!-- 轨道（底色弧） -->
  <path
    d="M15 75 A55 55 0 0 1 125 75"
    fill="none"
    stroke="rgba(对应色,0.1)"
    stroke-width="8"
    stroke-linecap="round"
  />
  <!-- 填充弧（数据弧） -->
  <path
    class="gauge-arc"
    d="M15 75 A55 55 0 0 1 125 75"
    fill="none"
    stroke="url(#gradient-id)"
    stroke-width="8"
    stroke-linecap="round"
    :stroke-dasharray="251"
    :stroke-dashoffset="dashOffset"
  />
  <defs>
    <linearGradient :id="gradientId" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" :stop-color="colorDark"/>
      <stop offset="100%" :stop-color="colorLight"/>
    </linearGradient>
  </defs>
  <!-- 中心数字 -->
  <text
    x="70" y="62"
    text-anchor="middle"
    font-size="26"
    font-weight="500"
    :fill="numColor"
    font-family="DM Mono,monospace"
    letter-spacing="-1"
  >{{ displayValue }}</text>
  <!-- 副文字 -->
  <text
    x="70" y="78"
    text-anchor="middle"
    font-size="10"
    fill="#4A505A"
    font-family="DM Sans,sans-serif"
  >{{ subLabel }}</text>
</svg>
```

### dashOffset 计算公式

```js
// value 为 0-100 的百分比数值
const dashOffset = computed(() => Math.round(251 * (1 - value / 100)))

// 示例（供验算）：
// 68.1% → 251 × 0.319 = 80
// 93.4% → 251 × 0.066 = 16
// 46.1% → 251 × 0.539 = 135
// 3.7%  → 251 × 0.963 = 242
```

---

## 九、动画规范

```css
/* 卡片入场 */
@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
.kpi-card { animation: fadeSlideUp .5s ease both; }
.kpi-card:nth-child(1) { animation-delay: .05s; }
.kpi-card:nth-child(2) { animation-delay: .12s; }
.kpi-card:nth-child(3) { animation-delay: .19s; }
.kpi-card:nth-child(4) { animation-delay: .26s; }

/* 底部区块入场 */
.bottom-grid { animation: fadeSlideUp .5s .35s ease both; }

/* 仪表盘弧线描边 */
@keyframes gaugeDraw {
  from { stroke-dashoffset: 251; }
  /* to 值由 :stroke-dashoffset binding 决定 */
}
.gauge-arc {
  animation: gaugeDraw .9s cubic-bezier(.4,0,.2,1) both;
}
/* 四张卡延迟对应入场 */
.kpi-card:nth-child(1) .gauge-arc { animation-delay: .3s; }
.kpi-card:nth-child(2) .gauge-arc { animation-delay: .37s; }
.kpi-card:nth-child(3) .gauge-arc { animation-delay: .44s; }
.kpi-card:nth-child(4) .gauge-arc { animation-delay: .51s; }

/* 转固率异常 badge 脉冲 */
@keyframes pulse-red {
  0%,100% { box-shadow: 0 0 0 0 rgba(248,113,113,0); }
  50%      { box-shadow: 0 0 0 3px rgba(248,113,113,0.15); }
}
.badge-red { animation: pulse-red 2s ease-in-out infinite; }
```

---

## 十、底部双栏布局

```css
.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  flex: 1; /* 撑满剩余高度 */
}
```

### 左栏 — AI 工程进度分析

卡片样式同 kpi-card（glass + border + blur），padding:20px 22px。

**section head（flex，justify-content:space-between，margin-bottom:16px）：**
```
左：[AI] 标签（9px，uppercase，letter-spacing:0.6px，cyan-dim背景，cyan色）
    + "工程进度分析"（14px，font-weight:500，text-1）

右：
  "管理汇报版"按钮（active 时：cyan-dim背景，cyan色，cyan边框）
  "执行推进版"按钮（默认：glass背景，text-2色）
  "刷新分析"按钮（cyan-dim背景，cyan色，带刷新SVG图标）
  三个按钮：padding:4px 11px，border-radius:6px，font-size:11px
```

**时间戳：** 11px，text-3，mono，margin-bottom:14px

**AI 内容三层（flex column，gap:10px）：**

```
① 综合评估块：
   background: rgba(34,211,238,0.04)
   border: 0.5px solid rgba(34,211,238,0.12)
   border-radius: 10px，padding: 12px 14px
   小标题：综合评估，10px，cyan，uppercase，letter-spacing:0.5px，margin-bottom:6px
   正文：12px，text-2，line-height:1.7
   正文中关键数字/词用 <b> 包裹，color:var(--text-1)，font-weight:500

② 三格指标（grid 3列，gap:8px）：
   每格：background:rgba(255,255,255,0.025)
         border:0.5px solid var(--border-dim)
         border-radius:8px，padding:10px 12px
   标签：10px，text-3，margin-bottom:5px，letter-spacing:0.3px
   内容：12px，text-1，line-height:1.5
   风险预警格的内容颜色：var(--red)

③ 重点动作块：
   background: rgba(251,191,36,0.04)
   border: 0.5px solid rgba(251,191,36,0.12)
   border-radius: 10px，padding: 12px 14px
   小标题：重点动作，10px，amber，uppercase，margin-bottom:8px
   列表：flex column，gap:5px
   每条：flex，gap:7px，font-size:12px，text-2，line-height:1.5
   序号徽章：16×16px，border-radius:4px，amber-dim背景，amber色，9px font-weight:500
```

### 右栏 — 近期重点工作

卡片样式同左栏，padding:20px 22px。

**section head：**
```
左：[TODO] 标签（violet-dim背景，violet色）+ "近期重点工作"（14px，font-weight:500）
右：[+ 添加] 按钮（violet-dim背景，violet色，0.5px violet边框）
```

**todo-item 卡片列表（flex column，gap:10px）：**

```css
.todo-item {
  border: 0.5px solid var(--border-dim);
  border-radius: 10px;
  padding: 12px 14px;
  background: rgba(255,255,255,0.025);
  transition: border-color .2s;
}
.todo-item:hover { border-color: var(--border-glow); }
```

每个 todo-item 内部：
```
① 顶行（flex，justify-content:space-between，margin-bottom:6px）：
   左：优先级 badge
       紧急：red-dim背景，red色，0.5px red边框
       跟进：amber-dim背景，amber色，0.5px amber边框
       准备/其他：green-dim背景，green色，0.5px green边框
       样式：font-size:10px，font-weight:500，padding:2px 7px，border-radius:4px
   右：截止时间（10px，text-3）

② 标题：13px，font-weight:500，text-1，margin-bottom:4px，line-height:1.4

③ 描述：11px，text-3，line-height:1.5
```

---

## 十一、给智能体的执行指令

将本文档全文连同以下指令一起发给智能体：

```
请严格按照《大屏展示页 UI 改版规格文档》重写 KeyIndicators.vue。

约束：
1. 数据来源和 API 调用逻辑不变，所有数据继续从现有 props/store 读取
2. 只替换 <template> 结构和 <style> 样式，<script> 中仅新增计算属性
3. 新增一个 computed：dashOffset(value) = Math.round(251 * (1 - value / 100))
4. 字体从 Google Fonts 引入（见第三节），在 index.html 中添加
5. 所有金额和百分比数字使用 font-family: var(--mono)
6. 不引入任何新的 npm 包或 UI 库
7. 背景光晕层用 position:fixed 的 div，不影响布局
8. 转固率 badge 必须有 pulse-red 动画
9. 仪表盘弧线用 stroke-dashoffset 绑定实际数据，并有入场动画
10. 大屏页导航只保留：品牌 + 实时状态 + 退出展示模式按钮
    不显示在建工程/预算立项/历史记录等后台导航
```
