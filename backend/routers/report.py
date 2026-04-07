# -*- coding: utf-8 -*-
"""
报告生成路由
GET /api/report/image  - 手机简报 PNG
GET /api/report/brief  - 手机简报 HTML（备用）
"""
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, StreamingResponse
import json
import io
from datetime import datetime
from models import ZaigongRecord, BudgetRecord, get_db
from services.analysis import build_transfer_priority

router = APIRouter()





def _fmt_pct(v, decimals=1):
    if v is None:
        return "—"
    return f"{v * 100:.{decimals}f}%"


def _fmt_wan(v, decimals=2):
    if v is None:
        return "—"
    return f"{v:,.{decimals}f}"


def _fmt_date(s):
    if not s:
        return "—"
    return str(s)[:10]


def _parse_report_month(file_date, uploaded_at) -> str:
    """从 file_date 或 uploaded_at 推断报告月份，返回 YYYY年MM月"""
    if file_date:
        fd = file_date.strip()
        if len(fd) == 8:        # YYYYMMDD
            return f"{fd[:4]}年{fd[4:6]}月"
        elif len(fd) == 4:      # MMDD
            year = uploaded_at.year if uploaded_at else datetime.now().year
            return f"{year}年{fd[:2]}月"
    if uploaded_at:
        return f"{uploaded_at.year}年{uploaded_at.month:02d}月"
    return f"{datetime.now().year}年{datetime.now().month:02d}月"


# ══════════════════════════════════════════════════════════════════
#  手机简报 HTML 生成
# ══════════════════════════════════════════════════════════════════

def _esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_brief_html(zaigong_rec: ZaigongRecord, budget_rec=None) -> str:
    metrics  = json.loads(zaigong_rec.metrics_data)   if zaigong_rec.metrics_data   else {}
    summary  = json.loads(zaigong_rec.summary_data)   if zaigong_rec.summary_data   else []
    four_cls = json.loads(zaigong_rec.four_class_warnings) if zaigong_rec.four_class_warnings else {}
    budget   = json.loads(budget_rec.budget_data) if budget_rec and budget_rec.budget_data else None

    report_month = _parse_report_month(zaigong_rec.file_date, zaigong_rec.uploaded_at)
    gen_time     = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 数值提取
    year_target   = metrics.get("year_target", 0) or 0
    total_current = metrics.get("total_current", 0) or 0
    progress_pct  = (metrics.get("progress_ratio", 0) or 0) * 100
    total_rate    = (metrics.get("total_rate", 0) or 0) * 100
    month_spend   = metrics.get("total_today_month", 0) or 0
    pending       = metrics.get("total_pending", 0) or 0
    deficit       = metrics.get("deficit", 0) or 0

    # 进度条颜色
    if progress_pct >= 80:
        prog_color = "#22c55e"
    elif progress_pct >= 50:
        prog_color = "#f59e0b"
    else:
        prog_color = "#ef4444"

    # 转固率颜色
    if total_rate >= 70:
        rate_color = "#22c55e"
    elif total_rate >= 50:
        rate_color = "#f59e0b"
    else:
        rate_color = "#ef4444"

    # 四类预警
    hit_count  = four_cls.get("hit_count", 0)
    warn_count = four_cls.get("warn_count", 0)
    fc_summary = four_cls.get("summary", {})
    fc_items   = four_cls.get("items", [])

    # 各类型统计
    fc_types = [
        ("列账不及时",   "⚠️"),
        ("预转固不及时", "🔔"),
        ("关闭不及时",   "🚨"),
        ("长期挂账",     "📌"),
    ]

    # 管理员排名（去合计，按累计支出降序，取前6）
    mgr_rows = [r for r in summary if r.get("工程管理员") != "合计"]
    mgr_rows.sort(key=lambda x: x.get("本年累计资本性支出", 0), reverse=True)
    mgr_rows = mgr_rows[:6]

    # 已触发预警工程（最多5条）
    triggered_items = [it for it in fc_items if "已触发" in it.get("status", "")][:5]

    # ── 构建 HTML ────────────────────────────────────────────────
    def kpi_card(icon, label, value, sub="", color="#2563eb", bg="#eff6ff"):
        return f"""
        <div class="kpi-card" style="border-top:3px solid {color};background:{bg}">
          <div class="kpi-icon">{icon}</div>
          <div class="kpi-body">
            <div class="kpi-value" style="color:{color}">{_esc(str(value))}</div>
            <div class="kpi-label">{_esc(label)}</div>
            {f'<div class="kpi-sub">{_esc(sub)}</div>' if sub else ''}
          </div>
        </div>"""

    kpi_section = ""
    kpi_section += kpi_card("📈", "年度完成率",
                             f"{progress_pct:.1f}%",
                             f"{_fmt_wan(total_current)} / {_fmt_wan(year_target)} 万元",
                             color=prog_color,
                             bg="#f0fdf4" if progress_pct >= 80 else ("#fffbeb" if progress_pct >= 50 else "#fef2f2"))
    kpi_section += kpi_card("🔄", "综合转固率",
                             f"{total_rate:.1f}%",
                             f"距目标差 {_fmt_wan(deficit)} 万元" if deficit > 0 else "已完成目标",
                             color=rate_color,
                             bg="#f0fdf4" if total_rate >= 70 else ("#fffbeb" if total_rate >= 50 else "#fef2f2"))
    kpi_section += kpi_card("💰", "本月资本性支出",
                             f"{_fmt_wan(month_spend)} 万元",
                             color="#7c3aed", bg="#f5f3ff")
    kpi_section += kpi_card("📦", "已下单待收货",
                             f"{_fmt_wan(pending)} 万元",
                             color="#0891b2", bg="#ecfeff")
    if budget:
        ap = (budget.get("approval_progress") or 0) * 100
        ap_color = "#22c55e" if ap >= 80 else ("#f59e0b" if ap >= 50 else "#ef4444")
        kpi_section += kpi_card("📋", "预算立项进度",
                                 f"{ap:.1f}%",
                                 f"年度预算 {_fmt_wan(budget.get('budget_total'))} 万元",
                                 color=ap_color,
                                 bg="#f0fdf4" if ap >= 80 else ("#fffbeb" if ap >= 50 else "#fef2f2"))

    # 四类预警 badge
    warn_badges = ""
    total_warn_all = 0
    for t_name, t_icon in fc_types:
        d = fc_summary.get(t_name, {})
        tri = d.get("triggered", 0)
        war = d.get("warning", 0)
        total_warn_all += tri + war
        if tri + war == 0:
            badge_color = "#6b7280"; badge_bg = "#f3f4f6"
        elif tri > 0:
            badge_color = "#b91c1c"; badge_bg = "#fee2e2"
        else:
            badge_color = "#92400e"; badge_bg = "#fef3c7"
        warn_badges += f"""
        <div class="warn-badge" style="background:{badge_bg};border-left:3px solid {badge_color}">
          <span class="warn-icon">{t_icon}</span>
          <div class="warn-info">
            <div class="warn-name" style="color:{badge_color}">{_esc(t_name)}</div>
            <div class="warn-counts">
              {'<span class="tag red">已触发 ' + str(tri) + '</span>' if tri > 0 else ''}
              {'<span class="tag orange">预警 ' + str(war) + '</span>' if war > 0 else ''}
              {'<span class="tag gray">正常</span>' if tri == 0 and war == 0 else ''}
            </div>
          </div>
        </div>"""

    # 已触发工程列表
    triggered_html = ""
    if triggered_items:
        triggered_html = '<div class="section-title">🚨 已触发预警工程</div>'
        for it in triggered_items:
            days = _esc(it.get("daysLabel", ""))
            triggered_html += f"""
        <div class="warn-item">
          <div class="warn-item-top">
            <span class="warn-type-tag">{_esc(it.get('type',''))}</span>
            <span class="warn-days red-text">{days}</span>
          </div>
          <div class="warn-item-name">{_esc(it.get('name',''))}</div>
          <div class="warn-item-meta">责任人：{_esc(it.get('manager',''))}</div>
        </div>"""

    # 管理员排名
    mgr_rows_html = ""
    for i, r in enumerate(mgr_rows):
        rate = (r.get("转固率") or 0) * 100
        cap  = r.get("本年累计资本性支出", 0) or 0
        mon  = r.get("本月资本性支出", 0) or 0
        rate_cls = "green-text" if rate >= 70 else ("orange-text" if rate >= 50 else "red-text")
        medal = ["🥇","🥈","🥉"][i] if i < 3 else f"{i+1}."
        mgr_rows_html += f"""
        <div class="mgr-row">
          <div class="mgr-rank">{medal}</div>
          <div class="mgr-info">
            <div class="mgr-name">{_esc(r.get('工程管理员',''))}</div>
            <div class="mgr-meta">本月 {_fmt_wan(mon)} 万 · 累计 {_fmt_wan(cap)} 万</div>
          </div>
          <div class="mgr-rate {rate_cls}">{rate:.0f}%</div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<meta name="format-detection" content="telephone=no">
<title>在建工程简报 · {_esc(report_month)}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Helvetica Neue",sans-serif;
       background:#f1f5f9;color:#1e293b;font-size:14px;line-height:1.5;
       -webkit-text-size-adjust:100%}}

  /* ── Header ── */
  .header{{background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);
           color:#fff;padding:20px 16px 16px;text-align:center}}
  .header-logo{{font-size:11px;opacity:.75;letter-spacing:.5px;margin-bottom:6px}}
  .header-title{{font-size:20px;font-weight:700;letter-spacing:.5px}}
  .header-month{{font-size:13px;opacity:.85;margin-top:4px}}
  .header-strip{{display:flex;justify-content:center;gap:16px;margin-top:12px;
                 font-size:11px;opacity:.7}}

  /* ── Sections ── */
  .section{{margin:12px 12px 0;background:#fff;border-radius:12px;
            overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.08)}}
  .section-title{{font-size:13px;font-weight:700;color:#374151;
                  padding:12px 14px 6px;border-bottom:1px solid #f3f4f6;
                  display:flex;align-items:center;gap:6px}}

  /* ── KPI Cards ── */
  .kpi-grid{{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:#e5e7eb}}
  .kpi-card{{padding:14px 12px;background:#fff;display:flex;align-items:flex-start;gap:10px}}
  .kpi-icon{{font-size:22px;margin-top:2px;flex-shrink:0}}
  .kpi-body{{min-width:0}}
  .kpi-value{{font-size:22px;font-weight:800;line-height:1.1;letter-spacing:-.5px}}
  .kpi-label{{font-size:11px;color:#6b7280;margin-top:2px}}
  .kpi-sub{{font-size:11px;color:#9ca3af;margin-top:1px;white-space:nowrap;
            overflow:hidden;text-overflow:ellipsis}}

  /* ── Progress bar ── */
  .progress-wrap{{padding:14px 14px 6px}}
  .progress-label{{display:flex;justify-content:space-between;
                   font-size:12px;color:#6b7280;margin-bottom:6px}}
  .progress-bar{{height:8px;background:#e5e7eb;border-radius:999px;overflow:hidden}}
  .progress-fill{{height:100%;border-radius:999px;transition:width .6s ease}}

  /* ── 四类预警 ── */
  .warn-grid{{padding:8px 10px 10px;display:flex;flex-direction:column;gap:8px}}
  .warn-badge{{display:flex;align-items:center;gap:10px;padding:10px 12px;
               border-radius:8px}}
  .warn-icon{{font-size:20px;flex-shrink:0}}
  .warn-info{{flex:1;min-width:0}}
  .warn-name{{font-size:13px;font-weight:600;margin-bottom:3px}}
  .warn-counts{{display:flex;gap:6px;flex-wrap:wrap}}
  .tag{{font-size:11px;padding:2px 8px;border-radius:999px;font-weight:600}}
  .tag.red{{background:#fecaca;color:#b91c1c}}
  .tag.orange{{background:#fed7aa;color:#92400e}}
  .tag.gray{{background:#e5e7eb;color:#6b7280}}

  /* ── 已触发列表 ── */
  .warn-item{{margin:0 12px 8px;padding:12px;background:#fff7f7;border-radius:8px;
              border-left:3px solid #ef4444}}
  .warn-item-top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}}
  .warn-type-tag{{font-size:11px;background:#fee2e2;color:#b91c1c;
                  padding:2px 7px;border-radius:999px;font-weight:600}}
  .warn-days{{font-size:11px;font-weight:700}}
  .warn-item-name{{font-size:13px;font-weight:600;color:#1e293b;margin-bottom:2px;
                   overflow:hidden;text-overflow:ellipsis;display:-webkit-box;
                   -webkit-line-clamp:2;-webkit-box-orient:vertical}}
  .warn-item-meta{{font-size:11px;color:#9ca3af}}

  /* ── 管理员排名 ── */
  .mgr-list{{padding:8px 12px 12px;display:flex;flex-direction:column;gap:2px}}
  .mgr-row{{display:flex;align-items:center;gap:10px;padding:10px 0;
            border-bottom:1px solid #f3f4f6}}
  .mgr-row:last-child{{border-bottom:none}}
  .mgr-rank{{font-size:18px;width:28px;text-align:center;flex-shrink:0}}
  .mgr-info{{flex:1;min-width:0}}
  .mgr-name{{font-size:14px;font-weight:600;color:#111827}}
  .mgr-meta{{font-size:11px;color:#9ca3af;margin-top:1px}}
  .mgr-rate{{font-size:18px;font-weight:800;flex-shrink:0}}

  /* ── Colors ── */
  .red-text{{color:#dc2626}}
  .orange-text{{color:#d97706}}
  .green-text{{color:#16a34a}}

  /* ── Footer ── */
  .footer{{text-align:center;padding:16px;font-size:11px;color:#9ca3af;margin-top:12px}}
</style>
</head>
<body>

<div class="header">
  <div class="header-logo">中国电信股份有限公司仙桃分公司 · 云网建设部</div>
  <div class="header-title">在建工程工作简报</div>
  <div class="header-month">{_esc(report_month)}</div>
  <div class="header-strip">
    <span>📊 {_esc(gen_time)} 生成</span>
    {'<span>📋 含预算立项数据</span>' if budget else ''}
  </div>
</div>

<!-- KPI 核心指标 -->
<div class="section" style="margin-top:12px">
  <div class="section-title">📊 核心指标</div>
  <div class="kpi-grid">
    {kpi_section}
  </div>
  <div class="progress-wrap">
    <div class="progress-label">
      <span>年度目标完成进度</span>
      <span style="font-weight:700;color:{prog_color}">{progress_pct:.1f}%</span>
    </div>
    <div class="progress-bar">
      <div class="progress-fill" style="width:{min(progress_pct,100):.1f}%;background:{prog_color}"></div>
    </div>
  </div>
</div>

<!-- 四类预警汇总 -->
<div class="section">
  <div class="section-title">
    🚦 四类工程预警
    {'<span style="margin-left:auto;font-size:11px;background:#fee2e2;color:#b91c1c;padding:2px 8px;border-radius:999px;font-weight:600">已触发 ' + str(hit_count) + '</span>' if hit_count > 0 else ''}
    {'<span style="margin-left:' + ('4px' if hit_count > 0 else 'auto') + ';font-size:11px;background:#fef3c7;color:#92400e;padding:2px 8px;border-radius:999px;font-weight:600">预警 ' + str(warn_count) + '</span>' if warn_count > 0 else ''}
    {'<span style="margin-left:auto;font-size:11px;background:#dcfce7;color:#166534;padding:2px 8px;border-radius:999px;font-weight:600">全部正常</span>' if hit_count == 0 and warn_count == 0 else ''}
  </div>
  <div class="warn-grid">
    {warn_badges}
  </div>
</div>

<!-- 已触发工程明细 -->
{'<div class="section">' + triggered_html + '</div>' if triggered_items else ''}

<!-- 管理员资本性支出排名 -->
<div class="section">
  <div class="section-title">🏆 资本性支出排名</div>
  <div class="mgr-list">
    {mgr_rows_html}
  </div>
</div>

<div class="footer">
  仙桃电信云网建设部 · {_esc(report_month)} 在建工程简报<br>
  {_esc(gen_time)} 自动生成
</div>

</body>
</html>"""
    return html


@router.get("/brief")
async def generate_brief(
    zaigong_id: int = Query(..., description="在建工程记录 ID"),
    budget_id:  int = Query(None, description="预算记录 ID（可选）"),
):
    """生成移动端简报 HTML"""
    db = get_db()
    zaigong_rec = db.query(ZaigongRecord).filter(ZaigongRecord.id == zaigong_id).first()
    if not zaigong_rec:
        return JSONResponse(status_code=404, content={"success": False, "message": "在建工程记录不存在"})

    budget_rec = None
    if budget_id:
        budget_rec = db.query(BudgetRecord).filter(BudgetRecord.id == budget_id).first()

    try:
        html_content = build_brief_html(zaigong_rec, budget_rec)
    except Exception as e:
        import traceback
        return JSONResponse(status_code=500, content={"success": False, "message": f"生成简报失败：{e}", "detail": traceback.format_exc()})

    report_month = _parse_report_month(zaigong_rec.file_date, zaigong_rec.uploaded_at)
    filename = f"在建工程简报_{report_month}.html".replace("年", "").replace("月", "")
    from urllib.parse import quote
    encoded_filename = quote(filename)

    return StreamingResponse(
        io.BytesIO(html_content.encode("utf-8")),
        media_type="text/html; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        },
    )


# ══════════════════════════════════════════════════════════════════
#  手机简报 PNG 图片生成（Pillow）
# ══════════════════════════════════════════════════════════════════

from PIL import Image as _PilImage, ImageDraw as _PilDraw, ImageFont

FONT_ZH   = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_MONO = "/System/Library/Fonts/SFNSMono.ttf"

# 颜色
C_BG        = (241, 245, 249)   # 页面背景 #f1f5f9
C_WHITE     = (255, 255, 255)
C_NAVY      = (30,  58,  95)    # 深蓝 header
C_BLUE      = (37,  99,  235)   # 主蓝
C_BLUE_MID  = (59, 130, 246)    # 中蓝（header渐变用）
C_GREEN     = (22, 163,  74)
C_ORANGE    = (217, 119,  6)
C_RED       = (220,  38,  38)
C_GRAY      = (107, 114, 128)
C_LGRAY     = (243, 244, 246)
C_TEXT      = ( 30,  41,  59)
C_SUBTEXT   = (148, 163, 184)

def _hex2rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _status_color(pct: float, lo=50, hi=80):
    if pct >= hi:   return C_GREEN
    if pct >= lo:   return C_ORANGE
    return C_RED

def _lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


class ImagePainter:
    W = 750          # canvas width (2x density → renders at 375 on phone)
    PAD = 36         # side padding
    CARD_R = 16      # card corner radius

    def __init__(self):
        self._rows = []   # list of (height_estimate, draw_fn)
        self._y = 0

    # ── font helpers ─────────────────────────────────────────────
    @staticmethod
    def font(size, bold=False):
        try:
            return ImageFont.truetype(FONT_ZH, size)
        except Exception:
            return ImageFont.load_default()

    @staticmethod
    def mono(size):
        try:
            return ImageFont.truetype(FONT_MONO, size)
        except Exception:
            return ImageFont.load_default()

    # ── low-level drawing helpers ─────────────────────────────────
    def _card(self, draw, y, h, fill=C_WHITE, radius=None, border_top=None):
        r = radius if radius is not None else self.CARD_R
        x0, x1 = self.PAD, self.W - self.PAD
        draw.rounded_rectangle([x0, y, x1, y + h], radius=r, fill=fill)
        if border_top:
            draw.rectangle([x0, y, x1, y + 4], fill=border_top)

    def _text(self, draw, x, y, text, size=26, color=C_TEXT, bold=False, anchor="la"):
        f = self.font(size)
        draw.text((x, y), str(text), font=f, fill=color, anchor=anchor)

    def _text_r(self, draw, x, y, text, size=26, color=C_TEXT):
        """right-aligned text ending at x"""
        f = self.font(size)
        draw.text((x, y), str(text), font=f, fill=color, anchor="ra")

    def _wrap_text(self, draw, x, y, text, size, color, max_width, line_height=None):
        """Simple word wrap for CJK (char by char)"""
        f = self.font(size)
        lh = line_height or int(size * 1.55)
        line = ""
        cy = y
        for ch in str(text):
            test = line + ch
            w = f.getlength(test)
            if w > max_width:
                draw.text((x, cy), line, font=f, fill=color, anchor="la")
                cy += lh
                line = ch
            else:
                line = test
        if line:
            draw.text((x, cy), line, font=f, fill=color, anchor="la")
            cy += lh
        return cy   # return new y after text

    def _progress_bar(self, draw, x, y, w, h, pct, color, bg=(229, 231, 235)):
        r = h // 2
        draw.rounded_rectangle([x, y, x + w, y + h], radius=r, fill=bg)
        fill_w = max(int(w * min(pct / 100, 1.0)), r * 2)
        draw.rounded_rectangle([x, y, x + fill_w, y + h], radius=r, fill=color)

    @staticmethod
    def _tag(draw, x, y, text, text_color, bg_color, size=20):
        f = ImagePainter.font(size)
        tw = int(f.getlength(text))
        pad_h, pad_v = 14, 6
        rw, rh = tw + pad_h * 2, size + pad_v * 2
        draw.rounded_rectangle([x, y, x + rw, y + rh], radius=rh // 2, fill=bg_color)
        draw.text((x + pad_h, y + pad_v), text, font=f, fill=text_color, anchor="la")
        return rw  # return tag width


def build_brief_image(zaigong_rec: ZaigongRecord, budget_rec=None) -> bytes:
    from PIL import Image, ImageDraw

    metrics  = json.loads(zaigong_rec.metrics_data)   if zaigong_rec.metrics_data   else {}
    summary  = json.loads(zaigong_rec.summary_data)   if zaigong_rec.summary_data   else []
    four_cls = json.loads(zaigong_rec.four_class_warnings) if zaigong_rec.four_class_warnings else {}
    budget   = json.loads(budget_rec.budget_data) if budget_rec and budget_rec.budget_data else None

    report_month = _parse_report_month(zaigong_rec.file_date, zaigong_rec.uploaded_at)
    gen_time     = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── 数值 ─────────────────────────────────────────────────────
    year_target   = metrics.get("year_target", 0) or 0
    total_current = metrics.get("total_current", 0) or 0
    progress_pct  = (metrics.get("progress_ratio", 0) or 0) * 100
    total_rate    = (metrics.get("total_rate", 0) or 0) * 100
    month_spend   = metrics.get("total_today_month", 0) or 0
    pending       = metrics.get("total_pending", 0) or 0
    deficit       = metrics.get("deficit", 0) or 0

    prog_color  = _status_color(progress_pct)
    rate_color  = _status_color(total_rate)

    fc_summary = four_cls.get("summary", {})
    fc_items   = four_cls.get("items", [])
    hit_count  = four_cls.get("hit_count", 0)
    warn_count = four_cls.get("warn_count", 0)

    mgr_rows = [r for r in summary if r.get("工程管理员") != "合计"]
    mgr_rows.sort(key=lambda x: x.get("本年累计资本性支出", 0), reverse=True)
    mgr_rows = mgr_rows[:6]

    triggered_items = [it for it in fc_items if "已触发" in it.get("status", "")][:4]

    P = ImagePainter

    W   = P.W
    PAD = P.PAD
    IW  = W - PAD * 2   # inner width

    # ── 先计算总高度（绘制两次：第一次量高，第二次正式画）──────────
    # 用列表收集各段高度，一次性创建 canvas

    sections_h = []

    # Header
    HEADER_H = 200
    sections_h.append(HEADER_H)

    # KPI section: title 50 + grid
    kpi_items = [
        ("年度完成率", f"{progress_pct:.1f}%",  f"累计 {_fmt_wan(total_current)} 万元",       prog_color),
        ("综合转固率", f"{total_rate:.1f}%",      f"差额 {_fmt_wan(deficit)} 万元",             rate_color),
        ("本月支出",   f"{_fmt_wan(month_spend)}", "万元",                                      (124, 58, 237)),
        ("待收货",     f"{_fmt_wan(pending)}",     "万元",                                      (8, 145, 178)),
    ]
    if budget:
        ap = (budget.get("approval_progress") or 0) * 100
        kpi_items.append(("立项进度", f"{ap:.1f}%",
                           f"预算 {_fmt_wan(budget.get('budget_total'))} 万",
                           _status_color(ap)))

    n_kpi = len(kpi_items)
    kpi_rows = (n_kpi + 1) // 2
    KPI_CARD_H = 130
    KPI_GAP    = 10
    kpi_h = 60 + kpi_rows * KPI_CARD_H + (kpi_rows - 1) * KPI_GAP  # title + grid
    # progress bar
    PROG_H = 80
    sections_h.append(kpi_h + PROG_H + 20)  # +20 gap below

    # 四类预警
    FC_TYPES = ["列账不及时", "预转固不及时", "关闭不及时", "长期挂账"]
    WARN_ROW_H = 80
    warn_h = 60 + len(FC_TYPES) * WARN_ROW_H + 20
    sections_h.append(warn_h)

    # 已触发工程
    TRIG_ROW_H = 90
    if triggered_items:
        trig_h = 60 + len(triggered_items) * TRIG_ROW_H + 20
        sections_h.append(trig_h)

    # 管理员排名
    MGR_ROW_H = 80
    mgr_h = 60 + len(mgr_rows) * MGR_ROW_H + 20
    sections_h.append(mgr_h)

    # Footer
    FOOTER_H = 70

    total_h = sum(sections_h) + FOOTER_H + 20  # 20 = gap before footer

    # ── 创建画布 ──────────────────────────────────────────────────
    img  = Image.new("RGB", (W, total_h), C_BG)
    draw = ImageDraw.Draw(img)

    def font(size):   return P.font(size)
    def text(x, y, t, size=26, color=C_TEXT, anchor="la"):
        draw.text((x, y), str(t), font=font(size), fill=color, anchor=anchor)
    def text_r(x, y, t, size=26, color=C_TEXT):
        draw.text((x, y), str(t), font=font(size), fill=color, anchor="ra")
    def card(y, h, fill=C_WHITE, border_top=None):
        draw.rounded_rectangle([PAD, y, W - PAD, y + h], radius=P.CARD_R, fill=fill)
        if border_top:
            draw.rectangle([PAD, y, W - PAD, y + 4], fill=border_top)
    def section_title(y, label):
        # 左侧蓝色竖线装饰
        draw.rectangle([PAD + 14, y + 14, PAD + 20, y + 46], fill=C_BLUE)
        text(PAD + 30, y + 16, label, size=28, color=C_TEXT)
        draw.rectangle([PAD + 16, y + 54, W - PAD - 16, y + 56], fill=C_LGRAY)
        return y + 62

    cy = 0  # current y

    # ══════════════════════════════════════════════════════════════
    #  Header（渐变蓝）
    # ══════════════════════════════════════════════════════════════
    for row in range(HEADER_H):
        t = row / HEADER_H
        c = _lerp_color(C_NAVY, C_BLUE_MID, t)
        draw.line([(0, row), (W, row)], fill=c)

    # 公司名
    text(W // 2, 34, "中国电信仙桃分公司  云网建设部",
         size=24, color=(200, 220, 255), anchor="mm")
    # 主标题
    text(W // 2, 80, "在建工程工作简报",
         size=46, color=C_WHITE, anchor="mm")
    # 月份
    text(W // 2, 128, report_month,
         size=34, color=(180, 210, 255), anchor="mm")
    # 生成时间
    text(W // 2, 170, f"数据时间  {gen_time}",
         size=20, color=(150, 185, 230), anchor="mm")

    cy = HEADER_H + 16

    # ══════════════════════════════════════════════════════════════
    #  KPI 核心指标
    # ══════════════════════════════════════════════════════════════
    card(cy, kpi_h + PROG_H + 10)
    inner_y = section_title(cy, "[ 核心指标 ]")

    # KPI 网格（两列）
    COL_W = (IW - KPI_GAP) // 2
    for idx, (label, val, sub, color) in enumerate(kpi_items):
        row_i = idx // 2
        col_i = idx % 2
        cx = PAD + col_i * (COL_W + KPI_GAP)
        cy_kpi = inner_y + row_i * (KPI_CARD_H + KPI_GAP)

        # 淡色背景（颜色 10% + 白 90%）
        light_bg = _lerp_color(C_WHITE, color, 0.08)
        draw.rounded_rectangle([cx + 4, cy_kpi, cx + COL_W - 4, cy_kpi + KPI_CARD_H - 4],
                                radius=12, fill=light_bg)
        # 顶部色条（5px）
        draw.rounded_rectangle([cx + 4, cy_kpi, cx + COL_W - 4, cy_kpi + 5],
                                radius=3, fill=color)
        # 数值（彩色大字）
        text(cx + 20, cy_kpi + 18, val, size=42, color=color)
        # 标签
        text(cx + 20, cy_kpi + 70, label, size=24, color=C_GRAY)
        # 副文字
        text(cx + 20, cy_kpi + 98, sub, size=20, color=C_SUBTEXT)

    inner_y += kpi_rows * (KPI_CARD_H + KPI_GAP)

    # 进度条
    prog_label_y = inner_y + 8
    text(PAD + 16, prog_label_y, "年度目标完成进度", size=24, color=C_GRAY)
    text_r(W - PAD - 16, prog_label_y, f"{progress_pct:.1f}%", size=26, color=prog_color)
    bar_y = prog_label_y + 36
    bar_x = PAD + 16
    bar_w = IW - 32
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + 16],
                            radius=8, fill=(229, 231, 235))
    fill_w = max(int(bar_w * min(progress_pct / 100, 1.0)), 16)
    draw.rounded_rectangle([bar_x, bar_y, bar_x + fill_w, bar_y + 16],
                            radius=8, fill=prog_color)

    cy = cy + kpi_h + PROG_H + 26

    # ══════════════════════════════════════════════════════════════
    #  四类预警
    # ══════════════════════════════════════════════════════════════
    card(cy, warn_h - 20)
    inner_y = section_title(cy, "[ 四类工程预警 ]")

    warn_label_map = {
        "列账不及时":   "列账不及时",
        "预转固不及时": "预转固不及时",
        "关闭不及时":   "关闭不及时",
        "长期挂账":     "长期挂账",
    }
    for i, t_name in enumerate(FC_TYPES):
        d   = fc_summary.get(t_name, {})
        tri = d.get("triggered", 0)
        war = d.get("warning",   0)

        row_y = inner_y + i * WARN_ROW_H
        # 分割线（除第一行）
        if i > 0:
            draw.line([(PAD + 20, row_y), (W - PAD - 20, row_y)], fill=C_LGRAY, width=1)
        row_y += 6

        # 左侧色条
        if tri > 0:
            stripe_c = C_RED
        elif war > 0:
            stripe_c = C_ORANGE
        else:
            stripe_c = (209, 213, 219)
        draw.rectangle([PAD + 16, row_y + 4, PAD + 20, row_y + WARN_ROW_H - 14], fill=stripe_c)

        # 类型名
        text(PAD + 30, row_y + 10, t_name, size=28, color=C_TEXT)

        # 标签
        tag_x = PAD + 30
        tag_y = row_y + 44
        if tri > 0:
            tw = P._tag(draw, tag_x, tag_y, f"已触发 {tri}", C_WHITE, C_RED, size=22)
            tag_x += tw + 10
        if war > 0:
            P._tag(draw, tag_x, tag_y, f"预警 {war}", (146, 64, 14), (254, 243, 199), size=22)
        if tri == 0 and war == 0:
            P._tag(draw, tag_x, tag_y, "正常", (74, 222, 128), (220, 252, 231), size=22)

        # 右侧汇总数字
        total = tri + war
        num_color = C_RED if tri > 0 else (C_ORANGE if war > 0 else C_SUBTEXT)
        text_r(W - PAD - 20, row_y + 20, str(total) if total > 0 else "—",
               size=40, color=num_color)

    cy = cy + warn_h

    # ══════════════════════════════════════════════════════════════
    #  已触发预警工程
    # ══════════════════════════════════════════════════════════════
    if triggered_items:
        trig_section_h = 60 + len(triggered_items) * TRIG_ROW_H + 10
        card(cy, trig_section_h)
        inner_y = section_title(cy, "[ 已触发预警工程 ]")

        for i, it in enumerate(triggered_items):
            row_y = inner_y + i * TRIG_ROW_H
            if i > 0:
                draw.line([(PAD + 20, row_y), (W - PAD - 20, row_y)], fill=C_LGRAY, width=1)
            row_y += 6

            # 红色左条
            draw.rectangle([PAD + 16, row_y + 2, PAD + 22, row_y + TRIG_ROW_H - 8], fill=C_RED)

            # 类型tag + 天数
            t_type = it.get("type", "")
            days   = it.get("daysLabel", "")
            P._tag(draw, PAD + 30, row_y + 6, t_type, C_WHITE, C_RED, size=20)
            text_r(W - PAD - 20, row_y + 6, days, size=22, color=C_RED)

            # 工程名（最多34字）
            name = it.get("name", "")
            if len(name) > 30:
                name = name[:29] + "…"
            text(PAD + 30, row_y + 38, name, size=26, color=C_TEXT)

            # 责任人
            text(PAD + 30, row_y + 68, f"责任人：{it.get('manager','')}", size=22, color=C_GRAY)

        cy = cy + trig_section_h + 16

    # ══════════════════════════════════════════════════════════════
    #  管理员排名
    # ══════════════════════════════════════════════════════════════
    card(cy, mgr_h - 10)
    inner_y = section_title(cy, "[ 资本性支出排名 ]")

    medal_colors = [C_ORANGE, C_GRAY, (180, 100, 50)]
    for i, r in enumerate(mgr_rows):
        row_y = inner_y + i * MGR_ROW_H
        if i > 0:
            draw.line([(PAD + 20, row_y), (W - PAD - 20, row_y)], fill=C_LGRAY, width=1)
        row_y += 10

        # 名次圆圈
        cir_x, cir_y, cir_r = PAD + 46, row_y + 34, 26
        cir_c = medal_colors[i] if i < 3 else C_SUBTEXT
        draw.ellipse([cir_x - cir_r, cir_y - cir_r, cir_x + cir_r, cir_y + cir_r], fill=cir_c)
        text(cir_x, cir_y, str(i + 1), size=24, color=C_WHITE, anchor="mm")

        cap = r.get("本年累计资本性支出", 0) or 0
        mon = r.get("本月资本性支出", 0) or 0
        mgr_name = r.get("工程管理员", "")
        rate = (r.get("转固率") or 0) * 100

        text(PAD + 90, row_y + 6,  mgr_name, size=30, color=C_TEXT)
        text(PAD + 90, row_y + 44, f"本月 {_fmt_wan(mon)} 万 · 累计 {_fmt_wan(cap)} 万",
             size=22, color=C_GRAY)

        rate_c = _status_color(rate)
        text_r(W - PAD - 20, row_y + 16, f"{rate:.0f}%", size=34, color=rate_c)

    cy = cy + mgr_h + 10

    # ══════════════════════════════════════════════════════════════
    #  Footer
    # ══════════════════════════════════════════════════════════════
    text(W // 2, cy + 20, f"仙桃电信云网建设部  ·  {report_month}  在建工程简报",
         size=22, color=C_SUBTEXT, anchor="mm")
    text(W // 2, cy + 48, gen_time + " 自动生成",
         size=20, color=C_SUBTEXT, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


@router.get("/image")
async def generate_brief_image(
    zaigong_id: int = Query(..., description="在建工程记录 ID"),
    budget_id:  int = Query(None, description="预算记录 ID（可选）"),
):
    """生成手机简报 PNG 图片"""
    db = get_db()
    zaigong_rec = db.query(ZaigongRecord).filter(ZaigongRecord.id == zaigong_id).first()
    if not zaigong_rec:
        return JSONResponse(status_code=404, content={"success": False, "message": "在建工程记录不存在"})

    budget_rec = None
    if budget_id:
        budget_rec = db.query(BudgetRecord).filter(BudgetRecord.id == budget_id).first()

    try:
        png_bytes = build_brief_image(zaigong_rec, budget_rec)
    except Exception as e:
        import traceback
        return JSONResponse(status_code=500,
                            content={"success": False, "message": f"生成图片失败：{e}",
                                     "detail": traceback.format_exc()})

    report_month = _parse_report_month(zaigong_rec.file_date, zaigong_rec.uploaded_at)
    filename = f"在建工程简报_{report_month}.png".replace("年", "").replace("月", "")
    from urllib.parse import quote
    encoded_filename = quote(filename)

    return StreamingResponse(
        io.BytesIO(png_bytes),
        media_type="image/png",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        },
    )
