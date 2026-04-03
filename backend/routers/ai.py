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

from services.trend import compute_trend_signals

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


class FourClassWarningItem(BaseModel):
    """四类工程预警单条"""
    status: str  # "已触发" / "预警"
    type: str  # "列账不及时" / "预转固不及时" / "关闭不及时" / "长期挂账"
    name: str
    manager: str
    days_label: str
    suggestion: str


class FourClassWarningSummary(BaseModel):
    """四类工程预警汇总"""
    hit_count: int = 0  # 已触发总数
    warn_count: int = 0  # 预警总数
    summary: dict = {}  # {"列账不及时": {"triggered": 0, "warning": 0}, ...}
    top_items: list[FourClassWarningItem] = []  # 最紧急的5条


class AnalyzeRequest(BaseModel):
    metrics: MetricsInput
    summary: list[ManagerSummary]
    budget: Optional[BudgetInput] = None
    analysis_date: Optional[str] = None
    style: str = "management"
    four_class_warnings: Optional[FourClassWarningSummary] = None
    history_records: Optional[list[dict]] = None  # [{"month": "2026-03", "total_capital": ..., "pending": ..., "rate": ...}]
    use_rule_only: bool = False  # 跳过 AI 调用，直接返回规则分析结果


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
    four_class: Optional[FourClassWarningSummary] = None,
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
    # 四类预警风险加成
    if four_class and four_class.hit_count > 0:
        risk_score += min(four_class.hit_count, 3)  # 最多+3

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

    # 四类预警风险描述
    four_class_risk_text = ""
    if four_class and four_class.hit_count > 0:
        type_hits = []
        for type_name, counts in four_class.summary.items():
            if counts.get("triggered", 0) > 0:
                type_hits.append(f"{type_name}{counts.get('triggered', 0)}项")
        if type_hits:
            four_class_risk_text = f"四类工程预警：已触发 {four_class.hit_count} 项（{', '.join(type_hits)}），预警 {four_class.warn_count} 项。"
            basis.append(four_class_risk_text)

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
        "four_class_summary": four_class.summary if four_class else {},
        "four_class_hit_count": four_class.hit_count if four_class else 0,
        "four_class_warn_count": four_class.warn_count if four_class else 0,
        "basis": [line for line in basis if str(line).strip()],
    }


def build_prompt(
    metrics: MetricsInput,
    summary: list[ManagerSummary],
    budget: Optional[BudgetInput],
    style: str,
    rule_signals: dict,
    trend_signals: dict,
    four_class: Optional[FourClassWarningSummary] = None,
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
        budget_block = "- 预算侧指标：暂无"

    # === 四类工程预警文本 ===
    four_class_text = ""
    if four_class and (four_class.hit_count > 0 or four_class.warn_count > 0):
        type_summary_lines = []
        for type_name, counts in four_class.summary.items():
            if counts.get("triggered", 0) > 0 or counts.get("warning", 0) > 0:
                type_summary_lines.append(
                    f"{type_name}：已触发 {counts.get('triggered', 0)} 项，预警 {counts.get('warning', 0)} 项"
                )

        top_items_text = ""
        if four_class.top_items:
            item_lines = []
            for item in four_class.top_items[:5]:  # 最多5条
                item_lines.append(
                    f"  • [{item.status}] {item.name}（{item.manager}）：{item.days_label}，建议：{item.suggestion}"
                )
            top_items_text = "\n最紧急的预警项：\n" + "\n".join(item_lines)

        four_class_text = f"""
## 四类工程预警（已触发 {four_class.hit_count} 项，预警 {four_class.warn_count} 项）
{'；'.join(type_summary_lines) if type_summary_lines else '暂无预警'}
{top_items_text}
"""

    # === 趋势变化文本 ===
    trend_text = ""
    if trend_signals.get("avg_monthly_spend_3m", 0) > 0:
        trend_parts = []
        mom_capital_pct = trend_signals.get("mom_capital_change_pct", 0)
        mom_pending = trend_signals.get("mom_pending_change", 0)
        if mom_capital_pct != 0:
            trend_parts.append(f"资本支出环比 {mom_capital_pct:+.1f}%")
        if mom_pending != 0:
            trend_parts.append(f"待收货环比 {mom_pending:+.2f} 万元")
        if trend_parts:
            trend_text = "\n## 趋势变化\n- " + "\n- ".join(trend_parts)

    # === 场景预测文本 ===
    scenario_text = ""
    scenario_likely = trend_signals.get("scenario_likely", 0)
    scenario_best = trend_signals.get("scenario_best", 0)
    scenario_worst = trend_signals.get("scenario_worst", 0)
    required_monthly = trend_signals.get("required_monthly_to_target", 0)
    avg_monthly = trend_signals.get("avg_monthly_spend_3m", 0)
    if scenario_likely > 0:
        scenario_text = f"""
## 目标完成预测
- 按当前月均支出 {avg_monthly:.2f} 万元 计算：
  - 最佳情景（支出提速20%）：{scenario_best:.2f} 万元
  - 一般情景：{scenario_likely:.2f} 万元
  - 最差情景（支出放缓40%）：{scenario_worst:.2f} 万元
- 要完成年度目标 {metrics.year_target:.2f} 万元，后续月均需达到 {required_monthly:.2f} 万元"""

    style_text = (
        "输出风格：管理汇报版。优先给结论、差距、风险等级和三条关键动作，语言凝练。"
        if style == "management"
        else "输出风格：执行推进版。优先给责任对象、推进动作、时间节奏，语言直接。"
    )

    rule_lines = "\n".join([f"- {line}" for line in rule_signals.get("basis", [])])

    return f"""你是一位专业的在建工程数据分析师，负责诊断工程进度健康度、预判风险、给出可落地动作。

## 分析范式要求（请严格遵循）
1. **先判断、后归因、再给动作** — 不要只描述数字，要解释原因和影响
2. **四类工程预警优先** — 已触发的预警必须点名，说明如果不处理的后果
3. **纵向趋势分析** — 结合环比变化，判断趋势是加速还是放缓
4. **横向对比** — 点名具体管理员的相对表现，不能泛泛说"部分管理员"
5. **情景预测** — 明确告知维持现状 vs 干预的结果差异
6. **动作要具体** — 每条必须包含：谁、做什、什么时间、解决什么问题

## 原始数据
- 年度资本性支出目标：{metrics.year_target:.2f} 万元
- 当前累计资本性支出：{metrics.total_current:.2f} 万元
- 当前完成进度：{metrics.progress_pct:.1f}%
- 本月资本性支出：{metrics.month_spend:.2f} 万元
- 已下单待收货：{metrics.pending:.2f} 万元
- 综合转固率：{metrics.transfer_rate * 100:.1f}%
{budget_block}

## 四类工程预警（重点关注，已触发项必须点名分析）{"（暂无预警）" if not four_class_text else ""}
{four_class_text if four_class_text else ""}

## 趋势变化
{trend_text if trend_text else "- 暂无历史数据，无法分析趋势"}

## 目标完成预测
{scenario_text if scenario_text else "- 数据不足，无法预测"}

## 已计算规则信号
{rule_lines}

## 输出要求
请只输出一个 JSON 对象，不要输出 Markdown，不要输出代码块：
{{
  "verdict": "一句话定性判断，包含进度状态和最关键风险",
  "diagnosis": [
    "诊断1：重点指出四类预警中哪类问题最严重及原因（必须点名具体工程名称）",
    "诊断2：结合趋势变化分析当前进度是真慢还是假慢",
    "诊断3：识别最关键的待收货/转固/支出风险及其根因"
  ],
  "person_bound_actions": [
    "动作1：[四类预警相关] 责任人A，在X月X日前完成[具体整改事项]，解决[哪类预警]",
    "动作2：[趋势相关] 责任人B，在X月X日前完成[具体事项]，改善[哪项趋势指标]",
    "动作3：[综合] 责任人C，协调[资源/部门]，确保[目标]达成"
  ],
  "four_class_priority": [
    {{
      "type": "列账不及时/预转固不及时/关闭不及时/长期挂账",
      "top_item_name": "最紧急的工程名称",
      "owner": "责任人",
      "urgency": "超期X天或剩余X天",
      "if_not_handled": "不处理将导致的直接后果",
      "recommended_action": "具体可落地的整改动作"
    }}
  ],
  "risk_scenarios": {{
    "if_continue": "如果四类预警不处理 + 维持当前支出节奏，N月后预计[结果]",
    "if_take_action": "如果落实上述动作，可达到[结果]",
    "critical_point": "关键节点：若[X]四类预警超[Y]天未处理，会导致[Z]后果"
  }},
  "red_flags": ["四类预警相关异常项1", "趋势相关异常项2"],
  "confidence": "高/中/低（基于数据完整性判断）"
}}"""


def build_fallback_analysis(
    metrics: MetricsInput,
    summary: list[ManagerSummary],
    budget: Optional[BudgetInput],
    style: str,
    rule_signals: dict,
    trend_signals: dict,
    four_class: Optional[FourClassWarningSummary] = None,
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

    # 四类预警相关
    four_class_hit = rule_signals.get("four_class_hit_count", 0)
    four_class_warn = rule_signals.get("four_class_warn_count", 0)
    four_class_summary = rule_signals.get("four_class_summary", {})

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

    # 风险文本
    risk_items = []
    if four_class_hit > 0:
        type_hits = []
        for type_name, counts in four_class_summary.items():
            if counts.get("triggered", 0) > 0:
                type_hits.append(f"{type_name}{counts.get('triggered', 0)}项")
        if type_hits:
            risk_items.append(f"四类工程预警：{', '.join(type_hits)}已触发，{four_class_warn}项预警")
    if top_pending:
        risk_items.append(
            f"待收货压力主要集中在 {top_pending[0]['manager']} 等，最高 {top_pending[0]['pending']:.2f} 万元"
        )
    elif low_rate:
        risk_items.append(f"转固率偏低管理员已出现，最低仅 {low_rate[0]['rate_pct']:.1f}%")

    risk_text = f"风险等级 {risk_level}，" + "；".join(risk_items) if risk_items else f"当前风险等级 {risk_level}，暂无明显单点异常"

    # 场景预测
    scenario_likely = trend_signals.get("scenario_likely", 0)
    scenario_best = trend_signals.get("scenario_best", 0)
    if scenario_likely > 0:
        scenario_text = (
            f"按当前月均支出 {trend_signals.get('avg_monthly_spend_3m', 0):.2f} 万元推算，"
            f"预计全年可达 {scenario_likely:.2f} 万元（最佳情景 {scenario_best:.2f} 万元），"
            f"较年度目标 {metrics.year_target:.2f} 万元{'可完成' if scenario_likely >= metrics.year_target else '存在缺口'}"
        )
    else:
        scenario_text = f"若下月月度支出仍低于 {avg_monthly_required:.2f} 万元，年度目标缺口将继续扩大"

    # 动作
    actions = []
    if four_class_hit > 0:
        actions.append(f"优先处理四类工程预警：已触发 {four_class_hit} 项，需在本周内完成整改")
    if remaining > 0:
        actions.append(
            f"围绕剩余 {remaining:.2f} 万元缺口，按月倒排支出目标，单月至少完成 {avg_monthly_required:.2f} 万元"
        )
    else:
        actions.append("年度资本性支出目标已超额完成，重点转向待收货清理和转固率提升")
    if top_pending:
        actions.append(
            f"逐项清理待收货项目，优先推动 {top_pending[0]['manager']} 等管理员明确到货与列账时间"
        )
    if style == "execution":
        actions = [
            f"本周完成四类工程预警整改（已触发 {four_class_hit} 项）",
            "本周完成高待收货项目逐项盘点，明确到货时间、责任人和列账节点",
            "对低月度支出管理员下达周目标，例会逐人通报完成情况",
        ]

    # 四类预警优先级
    four_class_priority = []
    if four_class and four_class.top_items:
        for item in four_class.top_items[:3]:
            four_class_priority.append({
                "type": item.type,
                "top_item_name": item.name,
                "owner": item.manager,
                "urgency": item.days_label,
                "if_not_handled": "将影响工程结算和转固进度",
                "recommended_action": item.suggestion
            })

    # 根据实际情况组织 verdict，避免"进度良好"和"风险等级高"同时出现造成混淆
    if metrics.progress_pct >= 100:
        if four_class_hit > 0:
            verdict_risk = f"存在四类工程预警 {four_class_hit} 项需处理。"
        elif top_pending and top_pending[0]['pending'] > 30:
            verdict_risk = f"注意待收货压力（{top_pending[0]['manager']} {top_pending[0]['pending']:.1f} 万元）。"
        elif rate_pct < 60:
            verdict_risk = f"转固率 {rate_pct:.1f}% 仍需提升至 60%。"
        else:
            verdict_risk = ""
    else:
        verdict_risk = f"风险等级 {risk_level}。"

    # diagnosis[1]：目标已完成时不说"差0.00万元"
    if remaining <= 0:
        diagnosis_progress = f"年度资本性支出目标已超额完成（{metrics.progress_pct:.1f}%），较时点节奏超出 {progress_gap_pct:+.1f}pct。"
    else:
        diagnosis_progress = f"支出进度{progress_eval}：较时点节奏 {progress_gap_pct:+.1f}pct，距年度目标差 {remaining:.2f} 万元。"

    return {
        "verdict": (
            f"当前累计支出 {metrics.total_current:.2f} 万元（{metrics.progress_pct:.1f}%），{progress_eval}。"
            f"{verdict_risk}"
        ),
        "diagnosis": [
            f"四类工程预警{'严重' if four_class_hit > 3 else '存在'}：已触发 {four_class_hit} 项，预警 {four_class_warn} 项，"
            + (", ".join([f"{k}{v.get('triggered', 0)}项" for k, v in four_class_summary.items() if v.get('triggered', 0) > 0]) if four_class_hit > 0 else "暂无")
            + "，需优先处理。" if four_class_hit > 0 else "暂无预警。",
            diagnosis_progress,
            f"待收货压力：{top_pending[0]['manager']} 等最高 {top_pending[0]['pending']:.2f} 万元，需加快订单转化。"
            if top_pending else "待收货暂无异常。"
        ],
        "person_bound_actions": actions[:3],
        "four_class_priority": four_class_priority,
        "risk_scenarios": {
            "if_continue": scenario_text + "，缺口可能持续扩大。",
            "if_take_action": "若落实上述整改动作，可加速推进工程进度和四类预警销项。",
            "critical_point": f"关键节点：四类预警超期处理将影响工程结算；支出节奏持续偏慢将导致年度目标缺口。"
        },
        "red_flags": [
            f"四类工程预警{four_class_hit}项已触发",
            f"进度较时点节奏 {progress_gap_pct:+.1f}pct",
            f"待收货压力 {top_pending[0]['pending']:.2f} 万元" if top_pending else "待收货正常"
        ],
        "confidence": "中（基于规则计算，AI分析异常时使用兜底逻辑）",
    }


def format_analysis_to_text(analysis: dict) -> str:
    """将结构化分析结果格式化为可读文本"""
    lines = []

    # 综合定论
    verdict = analysis.get("verdict") or analysis.get("overall", "")
    if verdict:
        lines.append(f"**综合定论**：{verdict}")

    # 诊断发现
    diagnosis = analysis.get("diagnosis", [])
    if diagnosis:
        lines.append("**诊断分析**：")
        for i, d in enumerate(diagnosis, 1):
            lines.append(f"  {i}. {d}")

    # 四类预警优先级
    four_class_priority = analysis.get("four_class_priority", [])
    if four_class_priority:
        lines.append("**四类预警（按紧急程度）**：")
        for item in four_class_priority:
            lines.append(f"  • [{item.get('type', '')}] {item.get('top_item_name', '')}（{item.get('owner', '')}）：{item.get('urgency', '')}")
            lines.append(f"   建议：{item.get('recommended_action', '')}")

    # 风险情景
    risk_scenarios = analysis.get("risk_scenarios", {})
    if risk_scenarios:
        if_continue = risk_scenarios.get("if_continue", "")
        if if_continue:
            lines.append(f"**维持现状**：{if_continue}")
        if_take_action = risk_scenarios.get("if_take_action", "")
        if if_take_action:
            lines.append(f"**干预效果**：{if_take_action}")
        critical = risk_scenarios.get("critical_point", "")
        if critical:
            lines.append(f"**关键节点**：{critical}")

    # 重点动作
    actions = analysis.get("person_bound_actions") or analysis.get("actions", [])
    if actions:
        action_text = "；".join([str(a) for a in actions if str(a).strip()])
        lines.append(f"**重点动作**：{action_text}")

    # 风险标识
    red_flags = analysis.get("red_flags", [])
    if red_flags:
        flags_text = "、".join([str(f) for f in red_flags if str(f).strip()])
        lines.append(f"**风险标识**：{flags_text}")

    # 分析依据（旧格式兼容）
    basis = analysis.get("basis", [])
    if basis:
        basis_text = "；".join([str(b) for b in basis if str(b).strip()])
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
    """兼容新旧两种输出格式的解析"""
    source = payload or {}

    # 尝试从新格式解析
    verdict = str(source.get("verdict") or fallback.get("verdict") or "").strip()
    diagnosis = source.get("diagnosis")
    if isinstance(diagnosis, list):
        diagnosis = [str(d).strip() for d in diagnosis if str(d).strip()]
    else:
        diagnosis = fallback.get("diagnosis", [])

    actions = source.get("person_bound_actions")
    if isinstance(actions, list):
        actions = [str(a).strip() for a in actions if str(a).strip()][:3]
    else:
        # 兼容旧格式
        actions = source.get("actions")
        if isinstance(actions, list):
            actions = [str(a).strip() for a in actions if str(a).strip()]
        else:
            actions = fallback.get("person_bound_actions", fallback.get("actions", []))

    four_class_priority = source.get("four_class_priority")
    if not isinstance(four_class_priority, list):
        four_class_priority = fallback.get("four_class_priority", [])

    risk_scenarios = source.get("risk_scenarios")
    if not isinstance(risk_scenarios, dict):
        risk_scenarios = fallback.get("risk_scenarios", {})

    red_flags = source.get("red_flags")
    if isinstance(red_flags, list):
        red_flags = [str(r).strip() for r in red_flags if str(r).strip()]
    else:
        # 兼容旧格式的 risk 字段
        risk = str(source.get("risk") or "").strip()
        red_flags = [risk] if risk else fallback.get("red_flags", [])

    confidence = str(source.get("confidence") or fallback.get("confidence") or "").strip()

    # 兼容旧格式的字段
    overall = str(source.get("overall") or fallback.get("overall") or verdict or "").strip()
    progress = str(source.get("progress") or fallback.get("progress") or "").strip()
    spend = str(source.get("spend") or fallback.get("spend") or "").strip()
    rate = str(source.get("rate") or fallback.get("rate") or "").strip()
    next_month = str(source.get("next_month") or fallback.get("next_month") or "").strip()
    basis = source.get("basis")
    if isinstance(basis, list):
        basis = [str(b).strip() for b in basis if str(b).strip()]
    else:
        basis = fallback.get("basis", [])

    return {
        # 新格式
        "verdict": verdict,
        "diagnosis": diagnosis,
        "person_bound_actions": actions,
        "four_class_priority": four_class_priority,
        "risk_scenarios": risk_scenarios,
        "red_flags": red_flags,
        "confidence": confidence,
        # 旧格式兼容
        "overall": overall,
        "progress": progress,
        "spend": spend,
        "rate": rate,
        "risk": str(source.get("risk") or fallback.get("risk") or "").strip(),
        "next_month": next_month,
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
    four_class = request.four_class_warnings

    # 计算规则信号
    rule_signals = compute_rule_signals(
        request.metrics,
        request.summary,
        request.budget,
        request.analysis_date,
        four_class,
    )

    # 计算趋势信号
    history_records = request.history_records or []
    trend_signals = compute_trend_signals(
        {
            "total_current": request.metrics.total_current,
            "total_pending": request.metrics.pending,
            "total_today_month": request.metrics.month_spend,
            "total_rate": request.metrics.transfer_rate,
            "year_target": request.metrics.year_target,
        },
        history_records,
    )

    fallback = build_fallback_analysis(
        request.metrics,
        request.summary,
        request.budget,
        style,
        rule_signals,
        trend_signals,
        four_class,
    )

    if request.use_rule_only:
        structured = normalize_analysis_payload(None, fallback)
        return {
            "success": True,
            "data": {
                "content": format_analysis_to_text(structured),
                "structured": structured,
                "style": style,
                "generated_at": datetime.now().isoformat(),
                "model": "rule-based",
                "signals": rule_signals,
                "trends": trend_signals,
            },
        }

    try:
        prompt = build_prompt(
            request.metrics,
            request.summary,
            request.budget,
            style,
            rule_signals,
            trend_signals,
            four_class,
        )
        raw_text = await call_minimax(prompt)
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
                "trends": trend_signals,
            },
        }
    except ValueError as exc:
        if "返回内容为空或格式不支持" in str(exc):
            return {
                "success": True,
                "data": {
                    "content": format_analysis_to_text(fallback),
                    "structured": fallback,
                    "style": style,
                    "generated_at": datetime.now().isoformat(),
                    "model": "local-fallback",
                    "signals": rule_signals,
                    "trends": trend_signals,
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
