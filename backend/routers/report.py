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
import logging
from datetime import datetime
from models import ZaigongRecord, BudgetRecord, get_db
from services.analysis import build_transfer_priority

router = APIRouter()

logger = logging.getLogger(__name__)





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


def _safe_float(v, default=0.0) -> float:
    try:
        if v is None or v == "":
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def _extract_core_kpis(metrics: dict, budget: dict | None) -> dict:
    """
    与前端 KeyIndicators.vue 四个进度圆环同一口径：
      1. 当期资本性支出进度 = capital / yearTarget × 100，目标 100%
      2. 转固率             = rate × 100，目标 60%
      3. 整体支出进度       = annual_spend_total / budget_total × 100，目标 100%
      4. 整体立项进度       = approval_progress × 100，目标 90%

    metrics_data 存库为 snake_case（total_current / year_target / total_rate…），
    前端 dashboard 归一化为 camelCase（capital / yearTarget / rate…），两边都兼容。
    """
    metrics = metrics or {}
    budget = budget or {}

    # 兼容两种字段命名：前端 camelCase（capital/yearTarget/rate） 与后端 snake_case（total_current/year_target/total_rate）
    _cap = metrics.get("capital")
    _cap = metrics.get("total_current") if _cap is None else _cap
    capital = _safe_float(_cap)

    _yt = metrics.get("yearTarget")
    _yt = metrics.get("year_target") if _yt is None else _yt
    year_target = _safe_float(_yt)

    _r = metrics.get("rate")
    _r = metrics.get("total_rate") if _r is None else _r
    rate = _safe_float(_r)

    deficit = _safe_float(metrics.get("deficit"), default=0.0)

    _ms = metrics.get("monthSpend")
    _ms = metrics.get("total_today_month") if _ms is None else _ms
    month_spend = _safe_float(_ms)

    _pend = metrics.get("pending")
    _pend = metrics.get("total_pending") if _pend is None else _pend
    pending = _safe_float(_pend)

    capital_progress = (capital / year_target * 100.0) if year_target > 0 else 0.0
    transfer_rate = rate * 100.0

    annual_spend = _safe_float(budget.get("annual_spend_total"))
    budget_total = _safe_float(budget.get("budget_total"))
    occupied_total = _safe_float(budget.get("occupied_total"))
    approval_progress = _safe_float(budget.get("approval_progress")) * 100.0
    annual_progress = (annual_spend / budget_total * 100.0) if budget_total > 0 else 0.0

    if deficit < 0:
        deficit_label = f"已超额 {_fmt_wan(abs(deficit), 2)} 万"
        deficit_tone = "ok"
    elif deficit == 0 and year_target > 0:
        deficit_label = "恰好达标"
        deficit_tone = "ok"
    elif year_target > 0:
        deficit_label = f"缺口 {_fmt_wan(deficit, 2)} 万"
        deficit_tone = "up"
    else:
        deficit_label = "—"
        deficit_tone = "flat"

    if transfer_rate < 60:
        transfer_delta = f"距目标 {60 - transfer_rate:.1f}pp"
        transfer_tone = "up"
    else:
        transfer_delta = "已达标"
        transfer_tone = "ok"

    if annual_progress > 100:
        annual_delta = "超支"
        annual_tone = "down"
    elif budget_total > 0:
        annual_delta = f"{max(100 - annual_progress, 0):.1f}pp 待执行"
        annual_tone = "up"
    else:
        annual_delta = "暂无预算数据"
        annual_tone = "flat"

    if approval_progress < 90:
        approval_delta = f"{max(90 - approval_progress, 0):.1f}pp 未绑定"
        approval_tone = "up"
    elif budget_total > 0:
        approval_delta = "已达标"
        approval_tone = "flat"
    else:
        approval_delta = "暂无预算数据"
        approval_tone = "flat"

    return {
        "capital": capital,
        "year_target": year_target,
        "capital_progress": capital_progress,
        "deficit": deficit,
        "deficit_label": deficit_label,
        "deficit_tone": deficit_tone,
        "transfer_rate": transfer_rate,
        "transfer_delta": transfer_delta,
        "transfer_tone": transfer_tone,
        "annual_spend": annual_spend,
        "budget_total": budget_total,
        "annual_progress": annual_progress,
        "annual_delta": annual_delta,
        "annual_tone": annual_tone,
        "occupied_total": occupied_total,
        "approval_progress": approval_progress,
        "approval_delta": approval_delta,
        "approval_tone": approval_tone,
        "month_spend": month_spend,
        "pending": pending,
        "has_budget": budget_total > 0,
        # 与 KeyIndicators 四个圆环一一对应
        "gauges": [
            {
                "label": "当期资本性支出进度",
                "value": capital_progress,
                "target": 100.0,
                "sub": f"{capital:.1f} / {year_target:.1f} 万" if year_target > 0 else f"{capital:.1f} 万",
                "delta": deficit_label,
                "tone": deficit_tone,
            },
            {
                "label": "转固率",
                "value": transfer_rate,
                "target": 60.0,
                "sub": "期末余额 vs 年初数",
                "delta": transfer_delta,
                "tone": transfer_tone,
            },
            {
                "label": "整体支出进度",
                "value": annual_progress,
                "target": 100.0,
                "sub": (
                    f"{annual_spend:.1f} / {budget_total:.1f} 万"
                    if budget_total > 0 else "暂无预算数据"
                ),
                "delta": annual_delta,
                "tone": annual_tone,
            },
            {
                "label": "整体立项进度",
                "value": approval_progress,
                "target": 90.0,
                "sub": (
                    f"{occupied_total:.1f} / {budget_total:.1f} 万"
                    if budget_total > 0 else "暂无预算数据"
                ),
                "delta": approval_delta,
                "tone": approval_tone,
            },
        ],
    }


def _gauge_color_hex(value: float, target: float) -> str:
    """与 KeyIndicators.vue gaugeColor 一致：95/80/50% 阈值。"""
    if target <= 0:
        return "#B0492F"  # bad
    if value >= target * 0.95:
        return "#5C7A3E"  # ok
    if value >= target * 0.80:
        return "#C96442"  # accent
    if value >= target * 0.50:
        return "#B8842C"  # warn
    return "#B0492F"      # bad


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
    kpis         = _extract_core_kpis(metrics, budget)

    # 四类预警
    hit_count  = four_cls.get("hit_count", 0)
    warn_count = four_cls.get("warn_count", 0)
    fc_summary = four_cls.get("summary", {})
    fc_items   = four_cls.get("items", [])

    fc_types = [
        ("列账不及时",   "info"),
        ("预转固不及时", "warn"),
        ("关闭不及时",   "bad"),
        ("长期挂账",     "info"),
    ]

    # 支出转固视图（去合计，按转固率降序，取前6）
    def _mgr_name(r):
        return r.get("manager") or r.get("工程管理员") or ""

    def _mgr_cap(r):
        return _safe_float(r.get("capital", r.get("本年累计资本性支出")))

    def _mgr_mon(r):
        return _safe_float(r.get("monthSpend", r.get("本月资本性支出")))

    def _mgr_rate(r):
        return _safe_float(r.get("rate", r.get("转固率"))) * 100

    mgr_rows = [r for r in summary if _mgr_name(r) != "合计"]
    mgr_rows.sort(key=_mgr_rate, reverse=True)
    mgr_rows = mgr_rows[:6]

    triggered_items = [it for it in fc_items if "已触发" in str(it.get("status", ""))][:5]

    tone_cls = {"ok": "ok", "up": "up", "down": "down", "flat": "flat"}

    kpi_cards = ""
    for idx, g in enumerate(kpis["gauges"], start=1):
        tcls = tone_cls.get(g["tone"], "flat")
        value = _safe_float(g["value"])
        progress = min(max(value, 0), 100)
        color = _gauge_color_hex(value, _safe_float(g["target"], 100))
        kpi_cards += f"""
        <div class="kpi-card tone-{tcls}">
          <div class="kpi-top">
            <div class="kpi-label"><span>{idx:02d}</span>{_esc(g["label"])}</div>
            <div class="kpi-target">目标 {g['target']:.0f}%</div>
          </div>
          <div class="kpi-value">{value:.1f}<small>%</small></div>
          <div class="kpi-track"><i style="width:{progress:.1f}%;background:{color}"></i></div>
          <div class="kpi-foot">
            <span class="kpi-sub">{_esc(g["sub"])}</span>
            <span class="kpi-delta {tcls}">{_esc(g["delta"])}</span>
          </div>
        </div>"""

    # 四类预警
    warn_badges = ""
    for t_name, t_tone in fc_types:
        d = fc_summary.get(t_name, {})
        tri = d.get("triggered", 0) or 0
        war = d.get("warning", 0) or 0
        total = tri + war
        if tri > 0:
            stripe = "bad"
        elif war > 0:
            stripe = "warn"
        else:
            stripe = "muted"
        tags = ""
        if tri > 0:
            tags += f'<span class="tag bad">已触发 {tri}</span>'
        if war > 0:
            tags += f'<span class="tag warn">预警 {war}</span>'
        if tri == 0 and war == 0:
            tags = '<span class="tag muted">正常</span>'
        warn_badges += f"""
        <div class="warn-row">
          <span class="warn-stripe {stripe}"></span>
          <div class="warn-body">
            <div class="warn-name">{_esc(t_name)}</div>
            <div class="warn-tags">{tags}</div>
          </div>
          <div class="warn-count {stripe if total else 'muted'}">{total if total else "—"}</div>
        </div>"""

    # 已触发工程
    triggered_html = ""
    if triggered_items:
        rows = ""
        for it in triggered_items:
            days = _esc(it.get("daysLabel", ""))
            rows += f"""
        <div class="trig-item">
          <div class="trig-top">
            <span class="tag bad">{_esc(it.get("type", ""))}</span>
            <span class="trig-days">{days}</span>
          </div>
          <div class="trig-name">{_esc(it.get("name", ""))}</div>
          <div class="trig-meta">责任人：{_esc(it.get("manager", ""))}</div>
        </div>"""
        triggered_html = f"""
<div class="section">
  <div class="section-head"><h3>已触发预警工程</h3></div>
  <div class="trig-list">{rows}</div>
</div>"""

    # 管理员排名
    mgr_rows_html = ""
    for i, r in enumerate(mgr_rows):
        rate = _mgr_rate(r)
        if rate >= 60:
            rate_c = "ok"
        elif rate >= 30:
            rate_c = "warn"
        else:
            rate_c = "bad"
        mgr_rows_html += f"""
        <div class="mgr-row">
          <div class="mgr-rank">{i + 1}</div>
          <div class="mgr-info">
            <div class="mgr-name">{_esc(_mgr_name(r))}</div>
            <div class="mgr-meta">本月支出 {_fmt_wan(_mgr_mon(r), 1)} 万 · 累计支出 {_fmt_wan(_mgr_cap(r), 1)} 万</div>
            <div class="mgr-track"><i style="width:{min(max(rate, 0), 100):.0f}%"></i></div>
          </div>
          <div class="mgr-rate {rate_c}"><span>转固率</span>{rate:.0f}%</div>
        </div>"""

    head_badges = ""
    if hit_count:
        head_badges += f'<span class="head-pill bad">已触发 {hit_count}</span>'
    if warn_count:
        head_badges += f'<span class="head-pill warn">预警 {warn_count}</span>'
    if not hit_count and not warn_count:
        head_badges = '<span class="head-pill ok">全部正常</span>'

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<meta name="format-detection" content="telephone=no">
<title>在建工程简报 · {_esc(report_month)}</title>
<style>
  :root {{
    --paper:#F2F0E9; --paper-2:#E9E6DC; --surface:#FFFEFA; --surface-2:#F8F6EF;
    --line:#DDD9CC; --line-2:#CBC5B6;
    --ink:#17222A; --ink-2:#44505A; --ink-3:#788087; --ink-4:#A9ADA9;
    --navy:#122630; --navy-2:#193743; --navy-3:#295362;
    --accent:#E06D45; --accent-soft:#F8E3D9; --accent-ink:#9B4528;
    --ok:#587747; --ok-soft:#E5EDD8;
    --warn:#AD7B27; --warn-soft:#F4E8C9;
    --bad:#B84B3A; --bad-soft:#F6DEDA;
    --info:#3F6E83; --info-soft:#DFEAF0;
    --r-md:10px; --r-lg:16px;
  }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{
    counter-reset:brief-section;
    font-family:"Avenir Next","PingFang SC","Hiragino Sans GB","Microsoft YaHei",
                "Source Han Sans SC","Noto Sans CJK SC",sans-serif;
    width:100%; min-width:0; overflow-x:hidden;
    background:var(--paper); color:var(--ink); font-size:14px; line-height:1.5;
    -webkit-text-size-adjust:100%; -webkit-font-smoothing:antialiased;
    text-rendering:geometricPrecision;
  }}
  .mono{{font-family:"DIN Alternate","Avenir Next Condensed",ui-monospace,SFMono-Regular,Menlo,monospace}}

  /* Header — dark executive masthead */
  .header{{
    padding:28px 22px 24px; min-height:282px; color:#fff;
    background:
      radial-gradient(circle at 92% 5%, rgba(77,130,148,.48), transparent 34%),
      linear-gradient(148deg,var(--navy-2) 0%,var(--navy) 62%,#0D1C24 100%);
    position:relative; overflow:hidden;
  }}
  .header::before{{
    content:''; position:absolute; inset:0; opacity:.15; pointer-events:none;
    background-image:linear-gradient(rgba(255,255,255,.24) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.24) 1px,transparent 1px);
    background-size:32px 32px; transform:skewY(-6deg) scale(1.2);
  }}
  .header::after{{
    content:''; position:absolute; width:132px; height:132px; border:1px solid rgba(255,255,255,.16);
    border-radius:50%; right:-42px; top:38px; box-shadow:0 0 0 22px rgba(255,255,255,.035),0 0 0 44px rgba(255,255,255,.025);
  }}
  .eyebrow{{
    position:relative; z-index:1; font-size:10px; letter-spacing:.17em; text-transform:uppercase;
    color:#9FC4CF; font-weight:650; display:flex; align-items:center; gap:9px;
  }}
  .eyebrow::before{{content:''; width:20px; height:2px; background:var(--accent); border-radius:2px}}
  .header-title{{
    position:relative; z-index:1; margin-top:15px; font-size:31px; font-weight:700; letter-spacing:.02em; line-height:1.12;
    text-shadow:0 2px 18px rgba(0,0,0,.18);
  }}
  .header-meta{{
    position:relative; z-index:1; margin-top:10px; display:flex; flex-wrap:wrap; gap:7px 9px;
    font-size:11px; color:rgba(255,255,255,.66); align-items:center;
  }}
  .header-meta .dot{{width:3px;height:3px;border-radius:50%;background:rgba(255,255,255,.35)}}
  .header-org{{position:relative;z-index:1;margin-top:6px;font-size:10.5px;color:rgba(255,255,255,.44)}}
  .hero-stats{{
    position:relative;z-index:1;display:grid;grid-template-columns:1.35fr 1fr .82fr;
    margin-top:22px;border-top:1px solid rgba(255,255,255,.13);border-bottom:1px solid rgba(255,255,255,.13);
  }}
  .hero-stat{{padding:13px 10px 12px;border-right:1px solid rgba(255,255,255,.13)}}
  .hero-stat:first-child{{padding-left:0}} .hero-stat:last-child{{border-right:0;padding-right:0}}
  .hero-label{{font-size:9.5px;letter-spacing:.08em;color:rgba(255,255,255,.48);white-space:nowrap}}
  .hero-value{{margin-top:4px;font-family:"DIN Alternate","Avenir Next Condensed",ui-monospace,monospace;font-size:22px;font-weight:700;letter-spacing:-.03em;color:#fff;white-space:nowrap}}
  .hero-value small{{font-family:inherit;font-size:10px;font-weight:500;color:rgba(255,255,255,.48);margin-left:3px;letter-spacing:0}}
  .hero-value.risk{{color:#FFB49B}}

  .section{{
    counter-increment:brief-section; margin:14px 12px 0; background:var(--surface);
    border:1px solid rgba(205,199,184,.72); border-radius:var(--r-lg); overflow:hidden;
    box-shadow:0 7px 24px rgba(40,45,42,.055),0 1px 2px rgba(40,45,42,.04);
  }}
  .section-head{{
    min-height:51px;padding:13px 16px; display:flex; align-items:center; justify-content:space-between; gap:10px;
    border-bottom:1px solid var(--line);background:linear-gradient(90deg,#FFFEFA 0%,#F8F6EF 100%);
  }}
  .section-head h3{{font-size:14px; font-weight:650; color:var(--ink); margin:0; letter-spacing:.01em;display:flex;align-items:center;gap:8px}}
  .section-head h3::before{{content:"0" counter(brief-section);font:700 10px/1 "DIN Alternate",ui-monospace,monospace;color:var(--accent);letter-spacing:.06em}}
  .head-pill{{
    font-size:10px; font-weight:600; padding:3px 8px; border-radius:999px;
  }}
  .head-pill.bad{{background:var(--bad-soft); color:var(--bad)}}
  .head-pill.warn{{background:var(--warn-soft); color:var(--warn)}}
  .head-pill.ok{{background:var(--ok-soft); color:var(--ok)}}

  /* 2×2 executive metric grid */
  .kpi-grid{{
    display:grid; grid-template-columns:1fr 1fr; gap:10px; padding:10px; background:var(--surface-2);
  }}
  .kpi-card{{
    min-width:0;background:var(--surface);padding:14px 13px 13px;border:1px solid var(--line);
    border-radius:12px;box-shadow:0 2px 8px rgba(23,34,42,.035);
  }}
  .kpi-top{{display:flex;align-items:flex-start;justify-content:space-between;gap:5px}}
  .kpi-label{{font-size:11.5px;color:var(--ink-2);font-weight:650;line-height:1.35}}
  .kpi-label span{{display:block;font:700 9px/1 "DIN Alternate",ui-monospace,monospace;color:var(--accent);margin-bottom:4px;letter-spacing:.08em}}
  .kpi-target{{font-size:9px;color:var(--ink-3);white-space:nowrap;padding-top:12px}}
  .kpi-value{{margin-top:12px;font:700 30px/1 "DIN Alternate","Avenir Next Condensed",ui-monospace,monospace;color:var(--ink);letter-spacing:-.045em}}
  .kpi-value small{{font-size:12px;font-weight:600;color:var(--ink-3);margin-left:2px}}
  .kpi-track{{height:5px;margin-top:11px;background:var(--paper-2);border-radius:99px;overflow:hidden}}
  .kpi-track i{{display:block;height:100%;border-radius:99px}}
  .kpi-foot{{margin-top:10px;display:flex;flex-direction:column;align-items:flex-start;gap:6px;min-width:0}}
  .kpi-sub{{font-size:9.5px;color:var(--ink-3);font-family:"DIN Alternate",ui-monospace,monospace;white-space:nowrap;max-width:100%;overflow:hidden;text-overflow:ellipsis}}
  .kpi-delta{{
    display:inline-flex;align-items:center;font-weight:600;font-size:9.5px;padding:3px 7px;border-radius:999px;white-space:nowrap;
  }}
  .kpi-delta.ok{{background:var(--ok-soft); color:var(--ok)}}
  .kpi-delta.up{{background:var(--info-soft); color:var(--info)}}
  .kpi-delta.down{{background:var(--bad-soft); color:var(--bad)}}
  .kpi-delta.flat{{background:var(--paper-2); color:var(--ink-3)}}

  /* 四类预警 */
  .warn-list{{display:grid;grid-template-columns:1fr 1fr;gap:9px;padding:10px;background:var(--surface-2)}}
  .warn-row{{
    position:relative;display:flex;align-items:flex-start;gap:9px;padding:13px 11px 12px;
    min-height:82px;border:1px solid var(--line);border-radius:11px;background:var(--surface);overflow:hidden;
  }}
  .warn-stripe{{position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--line-2)}}
  .warn-stripe.bad{{background:var(--bad)}}
  .warn-stripe.warn{{background:var(--warn)}}
  .warn-stripe.muted{{background:var(--line-2)}}
  .warn-body{{flex:1; min-width:0}}
  .warn-name{{font-size:12px;font-weight:650;color:var(--ink);padding-right:24px;white-space:nowrap}}
  .warn-tags{{display:flex;gap:4px;flex-wrap:wrap;margin-top:9px}}
  .warn-count{{
    position:absolute;right:10px;top:10px;font-family:"DIN Alternate",ui-monospace,monospace;
    font-size:21px;font-weight:700;color:var(--ink);letter-spacing:-.03em;min-width:20px;text-align:right;
  }}
  .warn-count.bad{{color:var(--bad)}}
  .warn-count.warn{{color:var(--warn)}}
  .warn-count.muted{{color:var(--ink-4)}}

  .tag{{
    display:inline-flex;align-items:center;font-size:9.5px;font-weight:600;
    padding:3px 7px;border-radius:999px;white-space:nowrap;
  }}
  .tag.bad{{background:var(--bad-soft); color:var(--bad)}}
  .tag.warn{{background:var(--warn-soft); color:var(--warn)}}
  .tag.muted{{background:var(--paper-2); color:var(--ink-3)}}
  .tag.ok{{background:var(--ok-soft); color:var(--ok)}}

  /* 已触发 */
  .trig-list{{padding:10px;display:flex;flex-direction:column;gap:8px;background:var(--surface-2)}}
  .trig-item{{padding:11px 12px 10px;border:1px solid #E9CFC8;border-radius:10px;background:#FFF9F7}}
  .trig-top{{display:flex; justify-content:space-between; align-items:center; margin-bottom:6px}}
  .trig-days{{font-size:11px; font-weight:600; color:var(--bad);
              font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
  .trig-name{{font-size:12.5px;font-weight:650;color:var(--ink);line-height:1.42;
              overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical}}
  .trig-meta{{font-size:11px; color:var(--ink-3); margin-top:4px}}

  /* 管理员 */
  .mgr-list{{padding:4px 0}}
  .mgr-row{{
    display:flex;align-items:center;gap:11px;padding:12px 15px;
    border-bottom:1px solid var(--line);
  }}
  .mgr-row:last-child{{border-bottom:none}}
  .mgr-rank{{
    width:28px;height:28px;border-radius:9px;background:var(--paper-2);color:var(--ink-2);
    display:grid; place-items:center;
    font-size:12px; font-weight:600;
    font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; flex-shrink:0;
    box-shadow:inset 0 0 0 1px var(--line);
  }}
  .mgr-row:nth-child(1) .mgr-rank{{background:var(--navy);color:#fff;box-shadow:none}}
  .mgr-row:nth-child(2) .mgr-rank{{background:var(--paper-2); color:var(--ink-2)}}
  .mgr-row:nth-child(3) .mgr-rank{{background:var(--warn-soft); color:var(--warn); box-shadow:inset 0 0 0 1px var(--warn-soft)}}
  .mgr-info{{flex:1; min-width:0}}
  .mgr-name{{font-size:13px;font-weight:650;color:var(--ink)}}
  .mgr-meta{{font-size:9.5px;color:var(--ink-3);margin-top:2px;white-space:nowrap;
             font-family:"DIN Alternate",ui-monospace,monospace}}
  .mgr-track{{height:3px;margin-top:7px;background:var(--paper-2);border-radius:99px;overflow:hidden}}
  .mgr-track i{{display:block;height:100%;border-radius:99px;background:var(--navy-3)}}
  .mgr-rate{{
    display:flex;flex-direction:column;align-items:flex-end;justify-content:center;gap:1px;
    font-size:19px;font-weight:700;flex-shrink:0;
    font-family:"DIN Alternate",ui-monospace,monospace;letter-spacing:-.03em;
  }}
  .mgr-rate span{{font-family:ui-sans-serif,system-ui,"PingFang SC","Microsoft YaHei",sans-serif;
                  font-size:10px; font-weight:500; color:var(--ink-3); letter-spacing:0}}
  .mgr-rate.ok{{color:var(--ok)}}
  .mgr-rate.warn{{color:var(--warn)}}
  .mgr-rate.bad{{color:var(--bad)}}

  .footer{{
    text-align:center;padding:22px 16px 28px;font-size:10px;color:var(--ink-4);
    font-family:"DIN Alternate",ui-monospace,monospace;
    border-top:1px solid var(--line);margin-top:16px;line-height:1.8;
  }}
</style>
</head>
<body>

<header class="header">
  <div class="eyebrow">Xiantao Telecom / Project Control</div>
  <div class="header-title">在建工程工作简报</div>
  <div class="header-meta">
    <span>{_esc(report_month)}</span>
    <span class="dot"></span>
    <span>{_esc(gen_time)} 生成</span>
    {'<span class="dot"></span><span>含预算数据</span>' if kpis['has_budget'] else ''}
  </div>
  <div class="header-org">中国电信股份有限公司仙桃分公司 · 云网运营部</div>
  <div class="hero-stats">
    <div class="hero-stat">
      <div class="hero-label">当期资本性支出</div>
      <div class="hero-value">{_fmt_wan(kpis['capital'], 1)}<small>万元</small></div>
    </div>
    <div class="hero-stat">
      <div class="hero-label">当期目标</div>
      <div class="hero-value">{_fmt_wan(kpis['year_target'], 1) if kpis['year_target'] else '—'}<small>万元</small></div>
    </div>
    <div class="hero-stat">
      <div class="hero-label">风险信号</div>
      <div class="hero-value risk">{hit_count}<small>触发</small> {warn_count}<small>预警</small></div>
    </div>
  </div>
</header>

<section class="section">
  <div class="section-head"><h3>核心指标</h3><span style="font-size:10px;color:var(--ink-3)">四项关键进度</span></div>
  <div class="kpi-grid">
    {kpi_cards}
  </div>
</section>

<section class="section">
  <div class="section-head">
    <h3>四类工程预警</h3>
    <div style="display:flex;gap:6px;flex-wrap:wrap">{head_badges}</div>
  </div>
  <div class="warn-list">
    {warn_badges}
  </div>
</section>

{triggered_html}

<section class="section">
  <div class="section-head"><h3>支出转固视图</h3><span style="font-size:10px;color:var(--ink-3)">按转固率排序</span></div>
  <div class="mgr-list">
    {mgr_rows_html if mgr_rows_html else '<div style="padding:20px;text-align:center;color:var(--ink-3);font-size:13px">暂无数据</div>'}
  </div>
</section>

<footer class="footer">
  仙桃电信云网运营部 · {_esc(report_month)} 在建工程简报<br>
  {_esc(gen_time)} 自动生成
</footer>

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
        logger.exception("生成简报HTML失败")
        return JSONResponse(status_code=500, content={"success": False, "message": f"生成简报失败：{type(e).__name__}"})

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
#  手机简报 PNG 图片生成
#  优先使用 Playwright 无头浏览器渲染 HTML → 高清 PNG
#  Playwright 不可用时回退到 Pillow 逐像素绘制
# ══════════════════════════════════════════════════════════════════

from PIL import Image as _PilImage, ImageDraw as _PilDraw, ImageFont, ImageFilter

# Playwright 渲染引擎（可选依赖）
try:
    from playwright.async_api import async_playwright as _async_playwright
    _HAS_PLAYWRIGHT = True
except ImportError:
    _HAS_PLAYWRIGHT = False

# 模块级浏览器单例，避免每次请求重新启动
_pw_instance = None
_browser = None


async def _ensure_browser():
    """懒初始化 Playwright 浏览器实例，复用跨请求。"""
    global _pw_instance, _browser
    if _browser is None or not _browser.is_connected():
        if _pw_instance:
            try:
                await _pw_instance.stop()
            except Exception:
                pass
        _pw_instance = await _async_playwright().start()
        _browser = await _pw_instance.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-software-rasterizer"],
        )
    return _browser


async def _render_html_to_png(
    html: str,
    viewport_width: int = 430,
    dpr: int = 4,
) -> bytes:
    """
    用 Playwright 无头浏览器渲染 HTML 为高清 PNG 截图。

    参数:
      viewport_width: CSS 逻辑宽度（px），430 对应主流大屏手机宽
      dpr: 设备像素比，4 → 输出 1720px 宽，适合微信/企微二次压缩后的清晰度

    返回:
      带有正确 DPI 元数据的 PNG 字节
    """
    browser = await _ensure_browser()
    page = await browser.new_page(
        viewport={"width": viewport_width, "height": 800},
        device_scale_factor=dpr,
    )
    try:
        await page.set_content(html, wait_until="networkidle", timeout=15000)
        await page.evaluate("document.fonts && document.fonts.ready")
        await page.wait_for_timeout(120)
        screenshot_bytes = await page.screenshot(full_page=True, type="png")
    finally:
        await page.close()

    # 用 Pillow 写入 DPI 元数据，确保微信/飞书分享后不被当作低清图二次缩放
    buf = io.BytesIO(screenshot_bytes)
    img = _PilImage.open(buf)
    output = io.BytesIO()
    dpi = 72 * dpr
    img.save(output, format="PNG", dpi=(dpi, dpi))
    return output.getvalue()

# 跨平台字体候选（macOS / Windows / Linux），按优先级取首个 PIL 可加载项；
# 都不可用时 FONT_* 为 None，font()/mono() 会退到 PIL 默认字体（中文变方框
# 但不崩溃）。避免写死单一 macOS 路径，导致打包/部署到 Win/Linux 后图片生成失败。
_ZH_FONT_CANDIDATES = [
    "/System/Library/Fonts/STHeiti Medium.ttc",              # macOS 黑体
    "/System/Library/Fonts/PingFang.ttc",                    # macOS 苹方
    "/Library/Fonts/Songti.ttc",                            # macOS 宋体
    "C:/Windows/Fonts/simhei.ttf",                           # Windows 黑体
    "C:/Windows/Fonts/msyh.ttc",                            # Windows 微软雅黑
    "C:/Windows/Fonts/simsun.ttc",                           # Windows 宋体
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",        # Linux 文泉驿微米黑
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Linux Noto CJK
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
]
_MONO_FONT_CANDIDATES = [
    "/System/Library/Fonts/SFNSMono.ttf",                   # macOS 等宽
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Monaco.ttf",
    "C:/Windows/Fonts/consola.ttf",                          # Windows Consolas
    "C:/Windows/Fonts/cour.ttf",                             # Windows Courier
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",   # Linux DejaVu
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
]

def _resolve_font(candidates):
    """从候选路径取首个存在且 PIL 可加载的；都不可用返回 None。"""
    import os
    for path in candidates:
        if not os.path.exists(path):
            continue
        try:
            ImageFont.truetype(path, 16)   # 探测性加载，确认 PIL 能解析
            return path
        except Exception:
            continue
    return None

FONT_ZH   = _resolve_font(_ZH_FONT_CANDIDATES)
FONT_MONO = _resolve_font(_MONO_FONT_CANDIDATES)

# Executive brief 设计令牌（与上方 HTML 模板对齐）
C_PAPER     = (242, 240, 233)   # --paper
C_PAPER_2   = (233, 230, 220)   # --paper-2
C_SURFACE   = (255, 254, 250)   # --surface
C_LINE      = (221, 217, 204)   # --line
C_LINE_2    = (203, 197, 182)   # --line-2
C_INK       = ( 23,  34,  42)   # --ink
C_INK_2     = ( 68,  80,  90)   # --ink-2
C_INK_3     = (120, 128, 135)   # --ink-3
C_INK_4     = (169, 173, 169)   # --ink-4
C_NAVY      = ( 18,  38,  48)   # --navy
C_NAVY_2    = ( 25,  55,  67)   # --navy-2
C_NAVY_3    = ( 41,  83,  98)   # --navy-3
C_ACCENT    = (224, 109,  69)   # --accent
C_ACCENT_SF = (248, 227, 217)   # --accent-soft
C_ACCENT_INK= (155,  69,  40)   # --accent-ink
C_OK        = ( 88, 119,  71)   # --ok
C_OK_SOFT   = (229, 237, 216)   # --ok-soft
C_WARN      = (173, 123,  39)   # --warn
C_WARN_SOFT = (244, 232, 201)   # --warn-soft
C_BAD       = (184,  75,  58)   # --bad
C_BAD_SOFT  = (246, 222, 218)   # --bad-soft
C_INFO      = ( 63, 110, 131)   # --info
C_INFO_SOFT = (223, 234, 240)   # --info-soft
C_WHITE     = (255, 255, 255)

# 兼容旧名（内部辅助仍可能引用）
C_BG      = C_PAPER
C_TEXT    = C_INK
C_SUBTEXT = C_INK_4
C_GRAY    = C_INK_3
C_LGRAY   = C_LINE
C_GREEN   = C_OK
C_ORANGE  = C_WARN
C_RED     = C_BAD
C_BLUE    = C_ACCENT
C_NAVY    = C_INK
C_BLUE_MID= C_ACCENT


def _hex2rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _gauge_color_rgb(value: float, target: float):
    """与 KeyIndicators.vue gaugeColor / _gauge_color_hex 同阈值。"""
    return _hex2rgb(_gauge_color_hex(value, target))


def _tone_colors(tone: str):
    """delta pill 色：bg, fg"""
    return {
        "ok":   (C_OK_SOFT, C_OK),
        "up":   (C_INFO_SOFT, C_INFO),
        "down": (C_BAD_SOFT, C_BAD),
        "flat": (C_PAPER_2, C_INK_3),
    }.get(tone, (C_PAPER_2, C_INK_3))


def _lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


class ImagePainter:
    W = 750          # canvas width (2x density → renders at 375 on phone)
    PAD = 28         # side padding
    CARD_R = 22      # card corner radius（对齐 --r-lg 量感）

    def __init__(self):
        self._rows = []
        self._y = 0

    @staticmethod
    def font(size, bold=False):
        try:
            return ImageFont.truetype(FONT_ZH, size)
        except Exception:
            return ImageFont.load_default()

    @staticmethod
    def mono(size):
        try:
            return ImageFont.truetype(FONT_MONO or FONT_ZH, size)
        except Exception:
            return ImageFont.load_default()

    def _card(self, draw, y, h, fill=C_SURFACE, radius=None, border=True):
        r = radius if radius is not None else self.CARD_R
        x0, x1 = self.PAD, self.W - self.PAD
        if border:
            # 外描边（line）+ 内填 surface，模拟 1px border
            draw.rounded_rectangle([x0, y, x1, y + h], radius=r, fill=C_LINE)
            draw.rounded_rectangle([x0 + 1, y + 1, x1 - 1, y + h - 1], radius=max(r - 1, 0), fill=fill)
        else:
            draw.rounded_rectangle([x0, y, x1, y + h], radius=r, fill=fill)

    def _text(self, draw, x, y, text, size=26, color=C_INK, bold=False, anchor="la"):
        f = self.font(size)
        draw.text((x, y), str(text), font=f, fill=color, anchor=anchor)

    def _text_r(self, draw, x, y, text, size=26, color=C_INK):
        f = self.font(size)
        draw.text((x, y), str(text), font=f, fill=color, anchor="ra")

    def _wrap_text(self, draw, x, y, text, size, color, max_width, line_height=None):
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
        return cy

    @staticmethod
    def _tag(draw, x, y, text, text_color, bg_color, size=20):
        f = ImagePainter.font(size)
        tw = int(f.getlength(text))
        pad_h, pad_v = 12, 5
        rw, rh = tw + pad_h * 2, size + pad_v * 2
        draw.rounded_rectangle([x, y, x + rw, y + rh], radius=rh // 2, fill=bg_color)
        draw.text((x + pad_h, y + pad_v // 2 + rh // 2), text, font=f, fill=text_color, anchor="lm")
        return rw

    @staticmethod
    def _donut(draw, cx, cy, value, target, radius=52, width=10):
        """绘制进度圆环（与 KeyIndicators SVG 同几何语义）。"""
        bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
        # 底环
        draw.arc(bbox, start=0, end=360, fill=C_PAPER_2, width=width)
        # 进度环：从 -90°（12 点）顺时针
        pct = max(0.0, min(float(value), 100.0)) / 100.0
        if pct > 0:
            # Pillow arc: 0° = 3 点方向，顺时针；要 12 点起 → start=-90
            start = -90
            end = -90 + 360 * pct
            color = _gauge_color_rgb(value, target)
            # 满环时 end==start+360，Pillow 可能不画；略收一点
            if pct >= 0.999:
                end = start + 359.9
            draw.arc(bbox, start=start, end=end, fill=color, width=width)


def build_brief_image(zaigong_rec: ZaigongRecord, budget_rec=None) -> bytes:
    from PIL import Image, ImageDraw
    import math

    metrics  = json.loads(zaigong_rec.metrics_data)   if zaigong_rec.metrics_data   else {}
    summary  = json.loads(zaigong_rec.summary_data)   if zaigong_rec.summary_data   else []
    four_cls = json.loads(zaigong_rec.four_class_warnings) if zaigong_rec.four_class_warnings else {}
    budget   = json.loads(budget_rec.budget_data) if budget_rec and budget_rec.budget_data else None

    report_month = _parse_report_month(zaigong_rec.file_date, zaigong_rec.uploaded_at)
    gen_time     = datetime.now().strftime("%Y-%m-%d %H:%M")
    kpis         = _extract_core_kpis(metrics, budget)

    fc_summary = four_cls.get("summary", {})
    fc_items   = four_cls.get("items", [])
    hit_count  = four_cls.get("hit_count", 0) or 0
    warn_count = four_cls.get("warn_count", 0) or 0

    def _mgr_name(r):
        return r.get("manager") or r.get("工程管理员") or ""

    def _mgr_cap(r):
        return _safe_float(r.get("capital", r.get("本年累计资本性支出")))

    def _mgr_mon(r):
        return _safe_float(r.get("monthSpend", r.get("本月资本性支出")))

    def _mgr_rate(r):
        return _safe_float(r.get("rate", r.get("转固率"))) * 100

    mgr_rows = [r for r in summary if _mgr_name(r) != "合计"]
    mgr_rows.sort(key=_mgr_rate, reverse=True)
    mgr_rows = mgr_rows[:6]

    triggered_items = [it for it in fc_items if "已触发" in str(it.get("status", ""))][:4]

    P = ImagePainter
    W   = P.W
    PAD = P.PAD
    IW  = W - PAD * 2

    # ── 高度预算 ─────────────────────────────────────────────────
    HEADER_H = 430

    # 2×2 进度卡 KPI
    KPI_HEAD_H = 56
    KPI_CELL_H = 210
    KPI_ROWS = 2
    kpi_body_h = KPI_HEAD_H + KPI_ROWS * KPI_CELL_H
    KPI_SECTION_GAP = 16

    FC_TYPES = ["列账不及时", "预转固不及时", "关闭不及时", "长期挂账"]
    WARN_HEAD_H = 56
    WARN_CELL_H = 106
    warn_body_h = WARN_HEAD_H + WARN_CELL_H * 2

    TRIG_HEAD_H = 56
    TRIG_ROW_H = 96
    trig_body_h = (TRIG_HEAD_H + len(triggered_items) * TRIG_ROW_H) if triggered_items else 0

    MGR_HEAD_H = 56
    MGR_ROW_H = 84
    mgr_n = max(len(mgr_rows), 1)
    mgr_body_h = MGR_HEAD_H + mgr_n * MGR_ROW_H

    FOOTER_H = 88
    GAP = 16

    total_h = (
        HEADER_H
        + GAP + kpi_body_h
        + GAP + warn_body_h
        + ((GAP + trig_body_h) if triggered_items else 0)
        + GAP + mgr_body_h
        + FOOTER_H
    )

    img  = Image.new("RGB", (W, total_h), C_PAPER)
    draw = ImageDraw.Draw(img)

    def font(size):
        return P.font(size)

    def mono(size):
        return P.mono(size)

    def text(x, y, t, size=26, color=C_INK, anchor="la", use_mono=False):
        f = mono(size) if use_mono else font(size)
        draw.text((x, y), str(t), font=f, fill=color, anchor=anchor)

    def text_r(x, y, t, size=26, color=C_INK, use_mono=False):
        f = mono(size) if use_mono else font(size)
        draw.text((x, y), str(t), font=f, fill=color, anchor="ra")

    def card(y, h):
        P()._card(draw, y, h, fill=C_SURFACE, border=True)

    def section_head(y, label, right_bits=None):
        """卡片顶部标题行，返回内容起始 y。"""
        text(PAD + 22, y + 18, label, size=26, color=C_INK)
        # 底部分割线
        draw.line([(PAD + 2, y + KPI_HEAD_H - 1), (W - PAD - 2, y + KPI_HEAD_H - 1)], fill=C_LINE, width=1)
        if right_bits:
            rx = W - PAD - 22
            for bit_text, fg, bg in reversed(right_bits):
                f = font(20)
                tw = int(f.getlength(bit_text))
                rw, rh = tw + 20, 28
                draw.rounded_rectangle([rx - rw, y + 14, rx, y + 14 + rh], radius=14, fill=bg)
                draw.text((rx - rw // 2, y + 14 + rh // 2), bit_text, font=f, fill=fg, anchor="mm")
                rx -= rw + 8
        return y + KPI_HEAD_H

    # ══════════════════════════════════════════════════════════════
    #  Header — 深色工程控制简报封面
    # ══════════════════════════════════════════════════════════════
    cy = 0
    draw.rectangle([0, 0, W, HEADER_H], fill=C_NAVY)
    grid = _lerp_color(C_NAVY, C_NAVY_3, 0.25)
    for gx in range(0, W + 1, 58):
        draw.line([(gx, 0), (gx, HEADER_H)], fill=grid, width=1)
    for gy in range(0, HEADER_H + 1, 58):
        draw.line([(0, gy), (W, gy)], fill=grid, width=1)

    # eyebrow
    draw.rounded_rectangle([PAD, 40, PAD + 34, 44], radius=2, fill=C_ACCENT)
    text(PAD + 48, 32, "XIANTAO TELECOM  /  PROJECT CONTROL", size=18, color=(159, 196, 207))

    # 主标题
    text(PAD, 83, "在建工程工作简报", size=50, color=C_WHITE)

    # meta 行
    meta = f"{report_month}   ·   {gen_time} 生成" + ("   ·   含预算数据" if kpis["has_budget"] else "")
    text(PAD, 156, meta, size=21, color=(166, 181, 187))

    text(PAD, 190, "中国电信股份有限公司仙桃分公司 · 云网运营部", size=19, color=(119, 143, 152))

    # 数据摘要
    stats_top = 252
    draw.line([(PAD, stats_top - 18), (W - PAD, stats_top - 18)], fill=(59, 84, 94), width=1)
    draw.line([(PAD, HEADER_H - 32), (W - PAD, HEADER_H - 32)], fill=(59, 84, 94), width=1)
    stat_w = (W - PAD * 2) // 3
    for i in (1, 2):
        sx = PAD + stat_w * i
        draw.line([(sx, stats_top - 18), (sx, HEADER_H - 32)], fill=(59, 84, 94), width=1)

    stats = [
        ("当期资本性支出", _fmt_wan(kpis["capital"], 1), "万元", C_WHITE),
        ("当期目标", _fmt_wan(kpis["year_target"], 1) if kpis["year_target"] else "—", "万元", C_WHITE),
        ("风险信号", f"{hit_count} / {warn_count}", "触发 / 预警", (255, 180, 155)),
    ]
    for i, (label, value, unit, value_color) in enumerate(stats):
        sx = PAD + stat_w * i + (0 if i == 0 else 20)
        text(sx, stats_top, label, size=18, color=(127, 151, 160))
        text(sx, stats_top + 48, value, size=36, color=value_color, use_mono=True)
        text(sx, stats_top + 92, unit, size=17, color=(127, 151, 160))

    cy = HEADER_H + GAP

    # ══════════════════════════════════════════════════════════════
    #  核心指标 — 2×2 紧凑进度卡
    # ══════════════════════════════════════════════════════════════
    card(cy, kpi_body_h)
    inner_y = section_head(cy, "核心指标")

    gauges = kpis["gauges"]
    cell_w = IW // 2
    # 网格分割线
    mid_x = PAD + cell_w
    mid_y = inner_y + KPI_CELL_H
    draw.line([(mid_x, inner_y + 8), (mid_x, cy + kpi_body_h - 10)], fill=C_LINE, width=1)
    draw.line([(PAD + 10, mid_y), (W - PAD - 10, mid_y)], fill=C_LINE, width=1)

    for idx, g in enumerate(gauges):
        row_i = idx // 2
        col_i = idx % 2
        cell_x0 = PAD + col_i * cell_w
        cell_y0 = inner_y + row_i * KPI_CELL_H
        content_x = cell_x0 + 24
        content_r = cell_x0 + cell_w - 22
        val = g["value"]
        low = (abs(g["target"] - 60) < 0.01 and val < 60) or (
            abs(g["target"] - 100) < 0.01 and val > 100
        )
        val_color = C_BAD if low else C_INK
        text(content_x, cell_y0 + 24, f"{idx + 1:02d}  {g['label']}", size=20, color=C_INK_2)
        text_r(content_r, cell_y0 + 24, f"目标 {g['target']:.0f}%", size=15, color=C_INK_3)
        text(content_x, cell_y0 + 65, f"{val:.1f}%", size=38, color=val_color, use_mono=True)

        track_y = cell_y0 + 118
        draw.rounded_rectangle([content_x, track_y, content_r, track_y + 7], radius=4, fill=C_PAPER_2)
        bar_w = int((content_r - content_x) * min(max(val, 0), 100) / 100)
        if bar_w > 0:
            draw.rounded_rectangle(
                [content_x, track_y, content_x + bar_w, track_y + 7],
                radius=4, fill=_gauge_color_rgb(val, g["target"]),
            )
        text(content_x, cell_y0 + 140, g["sub"], size=16, color=C_INK_3)

        bg, fg = _tone_colors(g["tone"])
        delta = g["delta"] or "—"
        f = font(18)
        try:
            tw = int(f.getlength(delta))
        except Exception:
            tw = len(delta) * 12
        rw, rh = tw + 22, 30
        dx0 = content_x
        dy0 = cell_y0 + 168
        draw.rounded_rectangle([dx0, dy0, dx0 + rw, dy0 + rh], radius=15, fill=bg)
        draw.text((dx0 + rw // 2, dy0 + rh // 2), delta, font=f, fill=fg, anchor="mm")

    cy = cy + kpi_body_h + GAP

    # ══════════════════════════════════════════════════════════════
    #  四类预警
    # ══════════════════════════════════════════════════════════════
    card(cy, warn_body_h)
    right_bits = []
    if hit_count:
        right_bits.append((f"已触发 {hit_count}", C_BAD, C_BAD_SOFT))
    if warn_count:
        right_bits.append((f"预警 {warn_count}", C_WARN, C_WARN_SOFT))
    if not hit_count and not warn_count:
        right_bits.append(("全部正常", C_OK, C_OK_SOFT))
    inner_y = section_head(cy, "四类工程预警", right_bits=right_bits)

    for i, t_name in enumerate(FC_TYPES):
        d = fc_summary.get(t_name, {}) or {}
        tri = int(d.get("triggered", 0) or 0)
        war = int(d.get("warning", 0) or 0)
        total = tri + war

        grid_row = i // 2
        grid_col = i % 2
        cell_w = IW // 2
        cell_x = PAD + grid_col * cell_w
        row_y = inner_y + grid_row * WARN_CELL_H
        box = [cell_x + 10, row_y + 9, cell_x + cell_w - 10, row_y + WARN_CELL_H - 9]
        draw.rounded_rectangle(box, radius=14, fill=C_SURFACE, outline=C_LINE, width=1)

        # 左色条
        if tri > 0:
            stripe = C_BAD
        elif war > 0:
            stripe = C_WARN
        else:
            stripe = C_LINE_2
        draw.rounded_rectangle(
            [cell_x + 11, row_y + 10, cell_x + 16, row_y + WARN_CELL_H - 10],
            radius=2, fill=stripe,
        )

        text(cell_x + 28, row_y + 22, t_name, size=22, color=C_INK)

        tag_x = cell_x + 28
        tag_y = row_y + 58
        if tri > 0:
            tw = P._tag(draw, tag_x, tag_y, f"已触发 {tri}", C_BAD, C_BAD_SOFT, size=18)
            tag_x += tw + 8
        if war > 0:
            P._tag(draw, tag_x, tag_y, f"预警 {war}", C_WARN, C_WARN_SOFT, size=18)
        if tri == 0 and war == 0:
            P._tag(draw, tag_x, tag_y, "正常", C_INK_3, C_PAPER_2, size=18)

        num_color = C_BAD if tri > 0 else (C_WARN if war > 0 else C_INK_4)
        text_r(cell_x + cell_w - 24, row_y + 22, str(total) if total > 0 else "—",
               size=30, color=num_color, use_mono=True)

    cy = cy + warn_body_h + GAP

    # ══════════════════════════════════════════════════════════════
    #  已触发预警工程
    # ══════════════════════════════════════════════════════════════
    if triggered_items:
        card(cy, trig_body_h)
        inner_y = section_head(cy, "已触发预警工程")

        for i, it in enumerate(triggered_items):
            row_y = inner_y + i * TRIG_ROW_H
            if i > 0:
                draw.line([(PAD + 18, row_y), (W - PAD - 18, row_y)], fill=C_LINE, width=1)

            draw.rounded_rectangle(
                [PAD + 18, row_y + 16, PAD + 22, row_y + TRIG_ROW_H - 16],
                radius=2, fill=C_BAD,
            )

            t_type = it.get("type", "") or ""
            days = it.get("daysLabel", "") or ""
            P._tag(draw, PAD + 36, row_y + 14, t_type, C_BAD, C_BAD_SOFT, size=18)
            text_r(W - PAD - 22, row_y + 16, days, size=20, color=C_BAD)

            name = it.get("name", "") or ""
            if len(name) > 28:
                name = name[:27] + "…"
            text(PAD + 36, row_y + 48, name, size=24, color=C_INK)
            text(PAD + 36, row_y + 76, f"责任人：{it.get('manager', '') or ''}",
                 size=20, color=C_INK_3)

        cy = cy + trig_body_h + GAP

    # ══════════════════════════════════════════════════════════════
    #  管理员排名
    # ══════════════════════════════════════════════════════════════
    card(cy, mgr_body_h)
    inner_y = section_head(cy, "支出转固视图", right_bits=[("按转固率排序", C_INK_3, C_PAPER_2)])

    if not mgr_rows:
        text(W // 2, inner_y + 40, "暂无数据", size=24, color=C_INK_3, anchor="mm")
    else:
        rank_fills = [C_ACCENT_SF, C_PAPER_2, C_WARN_SOFT]
        rank_fgs   = [C_ACCENT_INK, C_INK_2, C_WARN]
        for i, r in enumerate(mgr_rows):
            row_y = inner_y + i * MGR_ROW_H
            if i > 0:
                draw.line([(PAD + 18, row_y), (W - PAD - 18, row_y)], fill=C_LINE, width=1)

            # 名次圆
            cir_x, cir_y, cir_r = PAD + 46, row_y + MGR_ROW_H // 2, 20
            fill = rank_fills[i] if i < 3 else C_PAPER_2
            fg = rank_fgs[i] if i < 3 else C_INK_3
            draw.ellipse([cir_x - cir_r, cir_y - cir_r, cir_x + cir_r, cir_y + cir_r], fill=fill)
            text(cir_x, cir_y, str(i + 1), size=20, color=fg, anchor="mm", use_mono=True)

            cap = _mgr_cap(r)
            mon = _mgr_mon(r)
            mgr_name = _mgr_name(r)
            rate = _mgr_rate(r)

            text(PAD + 80, row_y + 18, mgr_name, size=28, color=C_INK)
            text(PAD + 80, row_y + 52,
                 f"本月支出 {_fmt_wan(mon, 1)} 万 · 累计支出 {_fmt_wan(cap, 1)} 万",
                 size=20, color=C_INK_3)

            if rate >= 60:
                rate_c = C_OK
            elif rate >= 30:
                rate_c = C_WARN
            else:
                rate_c = C_BAD
            text_r(W - PAD - 22, row_y + 18, "转固率", size=16, color=C_INK_3)
            text_r(W - PAD - 22, row_y + 50, f"{rate:.0f}%", size=32, color=rate_c, use_mono=True)

    cy = cy + mgr_body_h + 24

    # ══════════════════════════════════════════════════════════════
    #  Footer
    # ══════════════════════════════════════════════════════════════
    text(W // 2, cy, f"仙桃电信云网运营部  ·  {report_month}  在建工程简报",
         size=20, color=C_INK_4, anchor="mm")
    text(W // 2, cy + 30, gen_time + " 自动生成",
         size=18, color=C_INK_4, anchor="mm")

    export_scale = 2
    resample = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.LANCZOS)
    export_img = img.resize((W * export_scale, total_h * export_scale), resample)
    export_img = export_img.filter(ImageFilter.UnsharpMask(radius=1.1, percent=120, threshold=2))

    buf = io.BytesIO()
    export_img.save(buf, format="PNG", dpi=(144, 144), compress_level=6)
    return buf.getvalue()


@router.get("/image")
async def generate_brief_image(
    zaigong_id: int = Query(..., description="在建工程记录 ID"),
    budget_id:  int = Query(None, description="预算记录 ID（可选）"),
):
    """生成手机简报 PNG 图片（优先 Playwright 高清渲染，回退 Pillow）"""
    db = get_db()
    zaigong_rec = db.query(ZaigongRecord).filter(ZaigongRecord.id == zaigong_id).first()
    if not zaigong_rec:
        return JSONResponse(status_code=404, content={"success": False, "message": "在建工程记录不存在"})

    budget_rec = None
    if budget_id:
        budget_rec = db.query(BudgetRecord).filter(BudgetRecord.id == budget_id).first()

    png_bytes = None

    # 1) 优先使用 Playwright 渲染 HTML → 高清 PNG
    if _HAS_PLAYWRIGHT:
        try:
            html_content = build_brief_html(zaigong_rec, budget_rec)
            png_bytes = await _render_html_to_png(html_content)
        except Exception as e:
            logger.warning(f"Playwright 渲染失败，将回退 Pillow: {e}")

    # 2) 回退 Pillow 逐像素绘制
    if png_bytes is None:
        try:
            png_bytes = build_brief_image(zaigong_rec, budget_rec)
        except Exception as e:
            logger.exception("Pillow 渲染也失败")
            return JSONResponse(status_code=500,
                                content={"success": False, "message": f"生成图片失败：{type(e).__name__}"})

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
