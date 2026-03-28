# -*- coding: utf-8 -*-
"""
AI 分析路由 - 调用 MiniMax API 生成工程进度分析报告
"""
from datetime import datetime
import json
import os
from pathlib import Path
import re
from typing import Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - fallback for environments without python-dotenv
    def load_dotenv(*_args, **_kwargs):
        return False


load_dotenv()
router = APIRouter()


class ManagerSummary(BaseModel):
    manager: str
    capital: float
    pending: float
    rate: float
    month_spend: float = 0
    transfer: float = 0


class MetricsInput(BaseModel):
    year_target: float
    total_current: float
    progress_pct: float
    month_spend: float
    pending: float
    transfer_rate: float


class BudgetInput(BaseModel):
    total_budget: float = 0
    approval_progress_pct: float = 0
    annual_spend_total: float = 0
    occupied_total: float = 0
    preoccupied_total: float = 0


class AnalyzeRequest(BaseModel):
    metrics: MetricsInput
    summary: list[ManagerSummary]
    budget: Optional[BudgetInput] = None
    analysis_date: Optional[str] = None
    style: str = "management"


def get_ai_env() -> Tuple[Optional[str], Optional[str], str]:
    # 实时读取环境变量，避免服务启动后修改 .env 不生效
    load_dotenv()
    api_key = os.getenv("MINIMAX_API_KEY")
    group_id = os.getenv("MINIMAX_GROUP_ID")
    api_url = os.getenv("MINIMAX_API_URL", "https://api.minimax.chat/v1/text/chatcompletion_v2")

    # 如果 python-dotenv 不可用，回退到手动解析 backend/.env
    if not api_key:
        env_path = Path(__file__).resolve().parent.parent / ".env"
        if env_path.exists():
            try:
                for raw in env_path.read_text(encoding="utf-8").splitlines():
                    line = raw.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if key == "MINIMAX_API_KEY" and not api_key:
                        api_key = value
                    elif key == "MINIMAX_GROUP_ID" and not group_id:
                        group_id = value
                    elif key == "MINIMAX_API_URL" and value:
                        api_url = value
            except Exception:
                # 保持静默，交由上层统一报未配置
                pass
    return api_key, group_id, api_url


def normalize_style(style: str) -> str:
    style_value = (style or "").strip().lower()
    if style_value in ("execution", "execute", "action"):
        return "execution"
    return "management"


def parse_analysis_date(raw_value: Optional[str]) -> datetime:
    if raw_value:
        raw_value = str(raw_value).strip()
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%Y-%m", "%Y/%m"):
            try:
                return datetime.strptime(raw_value, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(raw_value)
        except ValueError:
            pass
    return datetime.now()


def pct(value: float) -> float:
    return round(float(value or 0), 1)


def compute_rule_signals(
    metrics: MetricsInput,
    summary: list[ManagerSummary],
    budget: Optional[BudgetInput],
    analysis_date: Optional[str],
) -> dict:
    analysis_dt = parse_analysis_date(analysis_date)
    month_index = max(1, min(analysis_dt.month, 12))
    expected_progress_pct = month_index / 12 * 100
    progress_gap_pct = metrics.progress_pct - expected_progress_pct
    remaining_target = max(metrics.year_target - metrics.total_current, 0)
    months_left = max(12 - month_index, 1)
    avg_monthly_required = remaining_target / months_left if remaining_target > 0 else 0

    budget_spend_progress_pct = 0.0
    approval_spend_gap_pct = 0.0
    occupied_pressure_pct = 0.0
    preoccupied_pressure_pct = 0.0
    if budget and budget.total_budget > 0:
        budget_spend_progress_pct = budget.annual_spend_total / budget.total_budget * 100
        occupied_pressure_pct = budget.occupied_total / budget.total_budget * 100
        preoccupied_pressure_pct = budget.preoccupied_total / budget.total_budget * 100
    if budget:
        approval_spend_gap_pct = budget.approval_progress_pct - budget_spend_progress_pct

    top_capital = sorted(summary, key=lambda item: item.capital, reverse=True)[:3]
    top_pending = sorted(summary, key=lambda item: item.pending, reverse=True)[:3]
    low_rate = [item for item in sorted(summary, key=lambda item: item.rate) if item.rate < 0.3][:3]
    slow_month = [item for item in sorted(summary, key=lambda item: item.month_spend) if item.month_spend <= 0.01][:3]

    risk_score = 0
    if progress_gap_pct < -10:
        risk_score += 2
    elif progress_gap_pct < -5:
        risk_score += 1
    if metrics.transfer_rate < 0.3:
        risk_score += 2
    elif metrics.transfer_rate < 0.6:
        risk_score += 1
    if metrics.pending >= 80:
        risk_score += 2
    elif metrics.pending >= 30:
        risk_score += 1
    if approval_spend_gap_pct >= 15:
        risk_score += 1

    if risk_score >= 4:
        risk_level = "高"
    elif risk_score >= 2:
        risk_level = "中"
    else:
        risk_level = "低"

    basis = [
        f"当前资本开支完成率 {pct(metrics.progress_pct)}%，按 {analysis_dt.month} 月时点测算的年内应达节奏约 {pct(expected_progress_pct)}%，偏差 {progress_gap_pct:+.1f}pct。",
        f"当前累计支出 {metrics.total_current:.2f} 万元，距年度目标尚差 {remaining_target:.2f} 万元，后续月均仍需完成 {avg_monthly_required:.2f} 万元。",
        f"待收货 {metrics.pending:.2f} 万元，综合转固率 {metrics.transfer_rate * 100:.1f}%，风险等级判定为 {risk_level}。",
    ]
    if budget:
        basis.append(
            f"预算侧立项进度 {pct(budget.approval_progress_pct)}%，年度支出进度 {pct(budget_spend_progress_pct)}%，二者差值 {approval_spend_gap_pct:+.1f}pct。"
        )
    if top_pending:
        basis.append(
            "待收货压力靠前管理员："
            + "；".join([f"{item.manager} {item.pending:.2f} 万元" for item in top_pending if item.pending > 0])
        )

    return {
        "analysis_month": analysis_dt.month,
        "expected_progress_pct": pct(expected_progress_pct),
        "progress_gap_pct": round(progress_gap_pct, 1),
        "remaining_target": round(remaining_target, 2),
        "avg_monthly_required": round(avg_monthly_required, 2),
        "budget_spend_progress_pct": pct(budget_spend_progress_pct),
        "approval_spend_gap_pct": round(approval_spend_gap_pct, 1),
        "occupied_pressure_pct": pct(occupied_pressure_pct),
        "preoccupied_pressure_pct": pct(preoccupied_pressure_pct),
        "risk_level": risk_level,
        "top_capital_managers": [
            {"manager": item.manager, "capital": round(item.capital, 2), "month_spend": round(item.month_spend, 2)}
            for item in top_capital
        ],
        "top_pending_managers": [
            {"manager": item.manager, "pending": round(item.pending, 2), "rate_pct": pct(item.rate * 100)}
            for item in top_pending
            if item.pending > 0
        ],
        "low_rate_managers": [
            {"manager": item.manager, "rate_pct": pct(item.rate * 100), "pending": round(item.pending, 2)}
            for item in low_rate
        ],
        "slow_month_spend_managers": [
            {"manager": item.manager, "month_spend": round(item.month_spend, 2), "capital": round(item.capital, 2)}
            for item in slow_month
        ],
        "basis": [line for line in basis if str(line).strip()],
    }


def build_prompt(
    metrics: MetricsInput,
    summary: list[ManagerSummary],
    budget: Optional[BudgetInput],
    style: str,
    rule_signals: dict,
) -> str:
    """构建发给 MiniMax 的 prompt。"""
    manager_lines = []
    for item in sorted(summary, key=lambda x: x.capital, reverse=True):
        manager_lines.append(
            (
                f"- {item.manager}：累计支出 {item.capital:.2f} 万元，"
                f"本月支出 {item.month_spend:.2f} 万元，待收货 {item.pending:.2f} 万元，"
                f"转固率 {item.rate * 100:.1f}%，结转额 {item.transfer:.2f} 万元"
            )
        )
    manager_table = "\n".join(manager_lines) if manager_lines else "暂无管理员数据"

    if budget:
        budget_block = f"""
- 年度预算总额：{budget.total_budget:.2f} 万元
- 立项进度：{budget.approval_progress_pct:.1f}%
- 年度预算支出：{budget.annual_spend_total:.2f} 万元
- 已占用：{budget.occupied_total:.2f} 万元
- 预占用：{budget.preoccupied_total:.2f} 万元"""
    else:
        budget_block = "\n- 预算侧指标：暂无"

    style_text = (
        "输出风格：管理汇报版。优先给结论、差距、风险等级和三条关键动作，语言凝练。"
        if style == "management"
        else "输出风格：执行推进版。优先给责任对象、推进动作、时间节奏，语言直接。"
    )

    rule_lines = "\n".join([f"- {line}" for line in rule_signals.get("basis", [])])

    return f"""你是一位专业的在建工程数据分析师，需要基于给定指标做“先判断、再归因、再给动作”的分析。

## 原始数据
- 年度资本性支出目标：{metrics.year_target:.2f} 万元
- 当前累计资本性支出：{metrics.total_current:.2f} 万元
- 当前完成进度：{metrics.progress_pct:.1f}%
- 本月资本性支出：{metrics.month_spend:.2f} 万元
- 已下单待收货：{metrics.pending:.2f} 万元
- 综合转固率：{metrics.transfer_rate * 100:.1f}%
{budget_block}
- 各管理员推进情况（按累计支出降序）：
{manager_table}

## 已计算规则信号
{rule_lines}

## 分析要求
1. 先判断整体进度是否跑赢或落后当前月份应有节奏，再说明差距。
2. 必须结合预算侧指标判断“立项推进”和“支出兑现”是否脱节。
3. 必须点出最关键的风险来源，优先从待收货、转固率、支出兑现三个角度归因。
4. 至少点名 1-2 个管理员现象，不能只说泛泛结论。
5. 每一条结论尽量引用具体数字，不要空话。
6. {style_text}

## 输出要求
请只输出一个 JSON 对象，不要输出 Markdown，不要输出代码块，不要包含额外说明文字。
JSON 字段如下：
{{
  "overall": "综合评估，1-2句，要带数字",
  "progress": "进度评估，1句，要说明与当前月份节奏的差距",
  "spend": "支出分析，1句，要提预算或管理员兑现情况",
  "rate": "转固率分析，1句，要提具体比例",
  "risk": "风险预警，1句，要说明最关键风险来源",
  "next_month": "下月预测，1句，要有依据",
  "actions": ["重点动作1", "重点动作2", "重点动作3"],
  "basis": ["分析依据1", "分析依据2", "分析依据3"]
}}"""


def build_fallback_analysis(
    metrics: MetricsInput,
    summary: list[ManagerSummary],
    budget: Optional[BudgetInput],
    style: str,
    rule_signals: dict,
) -> dict:
    """AI 响应异常时的兜底结构化分析，确保前端始终可展示结果。"""
    progress_gap_pct = rule_signals["progress_gap_pct"]
    remaining = rule_signals["remaining_target"]
    avg_monthly_required = rule_signals["avg_monthly_required"]
    risk_level = rule_signals["risk_level"]
    rate_pct = metrics.transfer_rate * 100
    top_capital = rule_signals.get("top_capital_managers", [])
    top_pending = rule_signals.get("top_pending_managers", [])
    low_rate = rule_signals.get("low_rate_managers", [])

    if progress_gap_pct >= 5:
        progress_eval = "快于年内节奏"
    elif progress_gap_pct >= -5:
        progress_eval = "基本贴合年内节奏"
    else:
        progress_eval = "低于年内节奏"

    if budget and abs(rule_signals["approval_spend_gap_pct"]) >= 10:
        spend_eval = (
            f"立项进度 {budget.approval_progress_pct:.1f}% 与年度支出进度 "
            f"{rule_signals['budget_spend_progress_pct']:.1f}% 存在 "
            f"{rule_signals['approval_spend_gap_pct']:+.1f}pct 差距，兑现偏慢。"
        )
    else:
        lead = top_capital[0] if top_capital else None
        spend_eval = (
            f"{lead['manager']}累计支出领先 {lead['capital']:.2f} 万元，当前支出推进仍需继续放大。"
            if lead
            else "当前缺少管理员明细支撑，支出分析以总体完成率为主。"
        )

    if top_pending:
        risk_text = (
            f"风险等级 {risk_level}，待收货压力主要集中在 {top_pending[0]['manager']} "
            f"等管理员，最高 {top_pending[0]['pending']:.2f} 万元。"
        )
    elif low_rate:
        risk_text = (
            f"风险等级 {risk_level}，转固率偏低管理员已出现，最低仅 {low_rate[0]['rate_pct']:.1f}%。"
        )
    else:
        risk_text = f"当前风险等级 {risk_level}，暂无明显单点异常，但仍需跟踪兑现节奏。"

    next_month = (
        f"若下月月度支出仍低于 {avg_monthly_required:.2f} 万元，年度目标缺口将继续扩大；"
        "若同步压降待收货并提升转固率，完成率仍有改善空间。"
    )
    actions = [
        f"围绕剩余 {remaining:.2f} 万元缺口，按月倒排支出目标，单月至少完成 {avg_monthly_required:.2f} 万元。",
        "逐项清理待收货项目，优先推动高待收货管理员在本周明确到货与列账时间。",
        "按周复盘低转固率和低月度支出管理员，形成责任到人的推进清单。",
    ]
    if style == "execution":
        actions = [
            "本周完成高待收货项目逐项盘点，明确到货时间、责任人和列账节点。",
            "对低月度支出管理员下达周目标，例会逐人通报完成情况。",
            "同步清理可转固项目，按周更新转固明细并追踪闭环。",
        ]

    return {
        "overall": (
            f"当前累计支出 {metrics.total_current:.2f} 万元，完成 {metrics.progress_pct:.1f}%，"
            f"较当前月份应有节奏 {rule_signals['expected_progress_pct']:.1f}% {progress_eval}。"
        ),
        "progress": (
            f"距离年度目标仍差 {remaining:.2f} 万元，当前进度较时点节奏 {progress_gap_pct:+.1f}pct。"
        ),
        "spend": spend_eval,
        "rate": f"综合转固率 {rate_pct:.1f}%，{'偏低' if rate_pct < 60 else '总体正常'}，需和支出兑现同步推进。",
        "risk": risk_text,
        "next_month": next_month,
        "actions": actions,
        "basis": rule_signals.get("basis", [])[:4],
    }


def format_analysis_to_text(analysis: dict) -> str:
    actions = analysis.get("actions") or []
    basis = analysis.get("basis") or []
    action_text = "；".join([str(a) for a in actions if str(a).strip()])
    basis_text = "；".join([str(item) for item in basis if str(item).strip()])
    lines = [
        f"**综合评估**：{analysis.get('overall', '')}",
        f"**进度评估**：{analysis.get('progress', '')}",
        f"**支出分析**：{analysis.get('spend', '')}",
        f"**转固率分析**：{analysis.get('rate', '')}",
        f"**风险预警**：{analysis.get('risk', '')}",
        f"**下月预测**：{analysis.get('next_month', '')}",
        f"**重点动作**：{action_text}",
    ]
    if basis_text:
        lines.append(f"**分析依据**：{basis_text}")
    return "\n".join(lines)


def parse_structured_analysis(text: str) -> Optional[dict]:
    if not text:
        return None
    normalized = text.strip()
    # 去掉 markdown 代码块包裹
    normalized = re.sub(r"^```(?:json)?\s*", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\s*```$", "", normalized)

    candidates = [normalized]
    first_brace = normalized.find("{")
    last_brace = normalized.rfind("}")
    if first_brace >= 0 and last_brace > first_brace:
        candidates.append(normalized[first_brace:last_brace + 1])

    for candidate in candidates:
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
        except Exception:
            continue
    return None


def normalize_analysis_payload(payload: Optional[dict], fallback: dict) -> dict:
    source = payload or {}
    actions = source.get("actions")
    if not isinstance(actions, list):
        actions = []
    actions = [str(item).strip() for item in actions if str(item).strip()][:3]
    if not actions:
        actions = fallback.get("actions", [])

    basis = source.get("basis")
    if not isinstance(basis, list):
        basis = []
    basis = [str(item).strip() for item in basis if str(item).strip()][:4]
    if not basis:
        basis = fallback.get("basis", [])

    return {
        "overall": str(source.get("overall") or fallback.get("overall") or "").strip(),
        "progress": str(source.get("progress") or fallback.get("progress") or "").strip(),
        "spend": str(source.get("spend") or fallback.get("spend") or "").strip(),
        "rate": str(source.get("rate") or fallback.get("rate") or "").strip(),
        "risk": str(source.get("risk") or fallback.get("risk") or "").strip(),
        "next_month": str(source.get("next_month") or fallback.get("next_month") or "").strip(),
        "actions": actions,
        "basis": basis,
    }


def _normalize_text(value) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                if item.strip():
                    parts.append(item.strip())
            elif isinstance(item, dict):
                # 兼容 content 为数组对象，如 {"type":"text","text":"..."}
                text = item.get("text") or item.get("content")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
        return "\n".join(parts).strip()
    return ""


def extract_text_from_minimax(data: dict) -> str:
    """兼容不同 MiniMax/OpenAI 风格返回结构。"""
    choices = data.get("choices") or []
    if choices:
        first = choices[0] or {}
        msg = first.get("message") or {}
        if isinstance(msg, dict):
            content = _normalize_text(msg.get("content"))
            if content:
                return content
            text = _normalize_text(msg.get("text"))
            if text:
                return text

        messages = first.get("messages") or []
        if messages and isinstance(messages[0], dict):
            text = _normalize_text(messages[0].get("text"))
            if text:
                return text
            content = _normalize_text(messages[0].get("content"))
            if content:
                return content

    # 兜底字段
    for key in ("reply", "text", "output_text", "response", "content"):
        text = _normalize_text(data.get(key))
        if text:
            return text
    return ""


async def call_minimax(prompt: str) -> str:
    minimax_api_key, minimax_group_id, minimax_api_url = get_ai_env()

    if not minimax_api_key:
        raise ValueError("MiniMax API 未配置，请检查环境变量")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {minimax_api_key}",
    }
    # 兼容两种接口参数风格：
    # 1) chatcompletion_pro: sender_type/text + tokens_to_generate
    # 2) chatcompletion_v2(OpenAI-like): role/content + max_tokens
    if "chatcompletion_pro" in minimax_api_url:
        payload = {
            "model": "abab6.5s-chat",
            "tokens_to_generate": 1024,
            "messages": [{"sender_type": "USER", "text": prompt}],
            "role_type": "BOT",
        }
    else:
        payload = {
            "model": "MiniMax-M2.5",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
            "temperature": 0.4,
        }

    # 避免被系统 SOCKS/HTTP 代理环境变量影响，导致缺少 socksio 时调用失败
    async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
        url = minimax_api_url
        if minimax_group_id:
            parsed = urlparse(minimax_api_url)
            query = dict(parse_qsl(parsed.query, keep_blank_values=True))
            query.setdefault("GroupId", minimax_group_id)
            url = urlunparse(parsed._replace(query=urlencode(query)))
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        text = extract_text_from_minimax(data)
        if not text:
            # 再重试一次，降低偶发空响应带来的失败概率
            retry_response = await client.post(url, headers=headers, json=payload)
            retry_response.raise_for_status()
            text = extract_text_from_minimax(retry_response.json())
        if not text:
            raise ValueError("MiniMax 返回内容为空或格式不支持")
        return text


@router.get("/status")
async def ai_status():
    minimax_api_key, minimax_group_id, _ = get_ai_env()
    configured = bool(minimax_api_key)
    return {
        "success": True,
        "data": {
            "configured": configured,
            "model": "MiniMax-M2.5" if configured else None,
            "group_id_configured": bool(minimax_group_id),
        },
    }


@router.post("/analyze")
async def analyze(request: AnalyzeRequest):
    style = normalize_style(request.style)
    rule_signals = compute_rule_signals(request.metrics, request.summary, request.budget, request.analysis_date)
    try:
        prompt = build_prompt(request.metrics, request.summary, request.budget, style, rule_signals)
        raw_text = await call_minimax(prompt)
        fallback = build_fallback_analysis(request.metrics, request.summary, request.budget, style, rule_signals)
        structured = normalize_analysis_payload(parse_structured_analysis(raw_text), fallback)
        return {
            "success": True,
            "data": {
                "content": format_analysis_to_text(structured),
                "structured": structured,
                "style": style,
                "generated_at": datetime.now().isoformat(),
                "model": "MiniMax-M2.5",
                "signals": rule_signals,
            },
        }
    except ValueError as exc:
        if "返回内容为空或格式不支持" in str(exc):
            fallback = build_fallback_analysis(request.metrics, request.summary, request.budget, style, rule_signals)
            return {
                "success": True,
                "data": {
                    "content": format_analysis_to_text(fallback),
                    "structured": fallback,
                    "style": style,
                    "generated_at": datetime.now().isoformat(),
                    "model": "local-fallback",
                    "signals": rule_signals,
                },
            }
        error_code = "AI_NOT_CONFIGURED" if "未配置" in str(exc) else "AI_RESPONSE_ERROR"
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": error_code, "message": str(exc)},
        )
    except httpx.HTTPStatusError as exc:
        detail = ""
        try:
            detail = exc.response.text[:200]
        except Exception:
            detail = ""
        return JSONResponse(
            status_code=502,
            content={
                "success": False,
                "error": "AI_SERVICE_ERROR",
                "message": f"MiniMax API 调用失败: {exc.response.status_code}{' - ' + detail if detail else ''}",
            },
        )
    except httpx.RequestError as exc:
        return JSONResponse(
            status_code=502,
            content={
                "success": False,
                "error": "AI_NETWORK_ERROR",
                "message": f"MiniMax 网络请求失败: {exc}",
            },
        )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "INTERNAL_ERROR",
                "message": f"{type(exc).__name__}: {exc}",
            },
        )
