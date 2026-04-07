# -*- coding: utf-8 -*-
"""
消息推送服务 - 支持企业微信群机器人 / 飞书自定义机器人
根据 Webhook URL 自动识别平台。
"""
import httpx
from datetime import datetime
from typing import Optional


def _detect_platform(url: str) -> str:
    if "open.feishu.cn" in url or "open.larksuite.com" in url:
        return "feishu"
    return "wework"


def _extract(record_data: dict, budget_data: Optional[dict]):
    """提取两份数据的关键指标，统一到一个字典"""
    metrics = record_data.get("metrics", {})
    four_class = record_data.get("four_class_warnings", {})
    file_date = record_data.get("file_date", "")

    if file_date and len(file_date) == 8:
        date_str = f"{file_date[:4]}-{file_date[4:6]}-{file_date[6:]}"
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # 卡2：当期资本性支出
    capital = float(metrics.get("total_current") or 0)
    year_target = float(metrics.get("year_target") or 503)
    capital_pct = capital / year_target * 100 if year_target else 0
    capital_done = capital_pct >= 100

    # 卡4：综合转固率
    rate = float(metrics.get("total_rate") or 0)
    rate_pct = rate * 100
    rate_gap = 60.0 - rate_pct

    # 卡1：立项进度（预算）
    approval_pct = float((budget_data or {}).get("approval_progress") or 0) * 100
    occupied = float((budget_data or {}).get("occupied_total") or 0)
    preoccupied = float((budget_data or {}).get("preoccupied_total") or 0)
    has_budget = budget_data is not None

    # 卡3：全年资本性支出（预算）
    annual_spend = float((budget_data or {}).get("annual_spend_total") or 0)
    budget_total = float((budget_data or {}).get("budget_total") or 0)
    annual_pct = annual_spend / budget_total * 100 if budget_total else 0

    # 四类预警：items 列表，按 type 字段分组
    all_items = four_class.get("items", [])
    from collections import defaultdict
    grouped = defaultdict(list)
    for item in all_items:
        grouped[item.get("type", "其他")].append(item)
    overdue_transfer = grouped.get("预转固不及时", [])
    overdue_close = grouped.get("关闭不及时", [])
    long_construction = grouped.get("长期在建", []) or grouped.get("长期挂账", [])
    abnormal = grouped.get("异常在建", [])
    # 收集剩余未归类的预警类型
    known = {"预转固不及时", "关闭不及时", "长期在建", "长期挂账", "异常在建"}
    other_types = {t: v for t, v in grouped.items() if t not in known}
    total_warnings = len(all_items)

    return {
        "date_str": date_str,
        # 卡2
        "capital": capital, "year_target": year_target,
        "capital_pct": capital_pct, "capital_done": capital_done,
        # 卡4
        "rate": rate, "rate_pct": rate_pct, "rate_gap": rate_gap,
        # 卡1
        "has_budget": has_budget, "approval_pct": approval_pct,
        "occupied": occupied, "preoccupied": preoccupied,
        # 卡3
        "annual_spend": annual_spend, "budget_total": budget_total, "annual_pct": annual_pct,
        # 四类
        "overdue_transfer": overdue_transfer, "overdue_close": overdue_close,
        "long_construction": long_construction, "abnormal": abnormal,
        "other_types": other_types,
        "total_warnings": total_warnings,
    }


# ── 飞书卡片 ──────────────────────────────────────────────

def _feishu_payload(record_data: dict, budget_data: Optional[dict]) -> dict:
    m = _extract(record_data, budget_data)

    # 标题颜色：有预警红，转固率低橙，其余蓝
    if m["total_warnings"] > 0:
        header_color = "red"
    elif m["rate_pct"] < 30:
        header_color = "orange"
    else:
        header_color = "turquoise"

    # 状态 emoji
    def pct_icon(v): return "🟢" if v >= 100 else ("🟡" if v >= 60 else "🔴")
    def rate_icon(v): return "🟢" if v >= 60 else ("🟡" if v >= 30 else "🔴")

    # ── 四张卡片文本 ──
    card1 = (
        f"**📋 立项进度**\n"
        f"{pct_icon(m['approval_pct'])} **{m['approval_pct']:.1f}%**　"
        f"已占用 {m['occupied']:.1f}万 ＋ 预占用 {m['preoccupied']:.1f}万"
    ) if m["has_budget"] else "**📋 立项进度**\n暂无预算数据"

    capital_status = "✅ 已完成" if m["capital_done"] else f"缺口 {m['year_target'] - m['capital']:.1f}万"
    card2 = (
        f"**💰 当期资本性支出**\n"
        f"{pct_icon(m['capital_pct'])} **{m['capital_pct']:.1f}%**　"
        f"{m['capital']:.1f}万 / 目标 {m['year_target']:.0f}万　{capital_status}"
    )

    card3 = (
        f"**📈 全年资本性支出**\n"
        f"{pct_icon(m['annual_pct'])} **{m['annual_pct']:.1f}%**　"
        f"年度支出 {m['annual_spend']:.1f}万 / 预算 {m['budget_total']:.1f}万"
    ) if m["has_budget"] else "**📈 全年资本性支出**\n暂无预算数据"

    rate_status = "✅ 已达标" if m["rate_pct"] >= 60 else f"差距 {m['rate_gap']:.1f}pct"
    card4 = (
        f"**⚡ 综合转固率**\n"
        f"{rate_icon(m['rate_pct'])} **{m['rate_pct']:.2f}%**　"
        f"年度目标 60%　{rate_status}"
    )

    kpi_text = f"{card1}\n\n{card2}\n\n{card3}\n\n{card4}"

    # ── 四类预警 ──
    if m["total_warnings"] > 0:
        warn_lines = [f"**⚠️ 四类预警（共 {m['total_warnings']} 项）**"]
        categories = [
            (m["overdue_transfer"], "预转固不及时"),
            (m["overdue_close"], "关闭不及时"),
            (m["long_construction"], "长期在建"),
            (m["abnormal"], "异常在建"),
        ] + [(v, k) for k, v in m["other_types"].items()]
        for items, label in categories:
            if not items:
                continue
            warn_lines.append(f"**{label}**：{len(items)} 项")
            for item in items[:3]:
                name = item.get("name") or item.get("工程名称", "")
                manager = item.get("manager") or item.get("工程管理员", "")
                days = item.get("daysLabel", "")
                prefix = f"【{days}】" if days else ""
                warn_lines.append(f"· {prefix}{name}（{manager}）")
            if len(items) > 3:
                warn_lines.append(f"· …共 {len(items)} 项")
        warn_text = "\n".join(warn_lines)
    else:
        warn_text = "✅ 暂无四类预警"

    elements = [
        {"tag": "div", "text": {"tag": "lark_md", "content": f"**数据日期**　{m['date_str']}"}},
        {"tag": "hr"},
        {"tag": "div", "text": {"tag": "lark_md", "content": kpi_text}},
        {"tag": "hr"},
        {"tag": "div", "text": {"tag": "lark_md", "content": warn_text}},
        {"tag": "note", "elements": [
            {"tag": "plain_text", "content": f"在建工程数据驾驶舱自动推送 · {datetime.now().strftime('%H:%M')}"}
        ]},
    ]

    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "工程建设进度播报"},
                "template": header_color,
            },
            "elements": elements,
        },
    }


# ── 企业微信 Markdown ─────────────────────────────────────

def _wework_text(record_data: dict, budget_data: Optional[dict]) -> str:
    m = _extract(record_data, budget_data)

    def pct_icon(v): return "🟢" if v >= 100 else ("🟡" if v >= 60 else "🔴")
    def rate_icon(v): return "🟢" if v >= 60 else ("🟡" if v >= 30 else "🔴")

    rate_status = "已达标" if m["rate_pct"] >= 60 else f"差距 {m['rate_gap']:.1f}pct"

    lines = [
        "## 工程建设进度播报",
        f"> **数据日期**：{m['date_str']}",
        "",
        "**📊 四项核心指标**",
    ]

    if m["has_budget"]:
        lines.append(f"> 📋 立项进度：{pct_icon(m['approval_pct'])} **{m['approval_pct']:.1f}%**　已占用 {m['occupied']:.1f}万 ＋ 预占用 {m['preoccupied']:.1f}万")
    lines.append(f"> 💰 当期资本性支出：{pct_icon(m['capital_pct'])} **{m['capital_pct']:.1f}%**　{m['capital']:.1f}万 / 目标 {m['year_target']:.0f}万")
    if m["has_budget"]:
        lines.append(f"> 📈 全年资本性支出：{pct_icon(m['annual_pct'])} **{m['annual_pct']:.1f}%**　年度支出 {m['annual_spend']:.1f}万 / 预算 {m['budget_total']:.1f}万")
    lines.append(f"> ⚡ 综合转固率：{rate_icon(m['rate_pct'])} **{m['rate_pct']:.2f}%**　年度目标60%，{rate_status}")

    lines += [""]
    if m["total_warnings"] > 0:
        lines.append(f"**⚠️ 四类预警（共 {m['total_warnings']} 项）**")
        categories = [
            (m["overdue_transfer"], "预转固不及时"),
            (m["overdue_close"], "关闭不及时"),
            (m["long_construction"], "长期在建"),
            (m["abnormal"], "异常在建"),
        ] + [(v, k) for k, v in m["other_types"].items()]
        for items, label in categories:
            if not items:
                continue
            lines.append(f"> **{label}**：{len(items)} 项")
            for item in items[:3]:
                name = item.get("name") or item.get("工程名称", "")
                manager = item.get("manager") or item.get("工程管理员", "")
                days = item.get("daysLabel", "")
                prefix = f"【{days}】" if days else ""
                lines.append(f"　　· {prefix}{name}（{manager}）")
            if len(items) > 3:
                lines.append(f"　　· …共 {len(items)} 项")
    else:
        lines.append("> ✅ 暂无四类预警")

    lines += ["", f'<font color="comment">在建工程数据驾驶舱自动推送 · {datetime.now().strftime("%H:%M")}</font>']
    return "\n".join(lines)


# ── HTTP 发送 ─────────────────────────────────────────────

async def _post(url: str, payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


# ── 对外统一接口 ──────────────────────────────────────────

async def push_record(webhook_url: str, record_data: dict, budget_data: Optional[dict] = None) -> dict:
    """格式化并推送数据播报，自动识别平台"""
    platform = _detect_platform(webhook_url)
    if platform == "feishu":
        result = await _post(webhook_url, _feishu_payload(record_data, budget_data))
        return {"errcode": 0} if result.get("code") == 0 else result
    else:
        return await _post(webhook_url, {
            "msgtype": "markdown",
            "markdown": {"content": _wework_text(record_data, budget_data)},
        })


async def send_test(webhook_url: str) -> dict:
    """发送测试消息"""
    platform = _detect_platform(webhook_url)
    if platform == "feishu":
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {"title": {"tag": "plain_text", "content": "✅ 配置测试成功"}, "template": "green"},
                "elements": [
                    {"tag": "div", "text": {"tag": "lark_md",
                        "content": "在建工程数据驾驶舱 Webhook 配置成功！\n后续数据更新将推送至此。"}},
                    {"tag": "note", "elements": [{"tag": "plain_text", "content": "这是一条测试消息，可以忽略"}]},
                ],
            },
        }
        result = await _post(webhook_url, payload)
        return {"errcode": 0} if result.get("code") == 0 else result
    else:
        msg = (
            "## ✅ 在建工程数据驾驶舱 - 测试消息\n"
            "> Webhook 配置成功！后续数据更新将自动推送。\n"
            '<font color="comment">这是一条测试消息，可以忽略。</font>'
        )
        return await _post(webhook_url, {"msgtype": "markdown", "markdown": {"content": msg}})
