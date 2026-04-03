# -*- coding: utf-8 -*-
"""
趋势分析服务 - 为AI分析提供历史对比数据和趋势计算
"""
from datetime import datetime
from typing import Optional


def compute_trend_signals(
    current_metrics: dict,
    history_records: list[dict],
) -> dict:
    """
    基于历史数据计算趋势指标

    Args:
        current_metrics: 当前指标 {"total_current", "total_pending", "total_today_month", "total_rate", "year_target"}
        history_records: 历史快照列表 [{"month": "2026-03", "total_capital": ..., "pending": ..., "rate": ...}]
    """
    if not history_records or len(history_records) < 1:
        return _compute_fallback_trends(current_metrics)

    # 按月份排序（倒序，最新的在前）
    sorted_history = sorted(history_records, key=lambda x: x.get("month", ""), reverse=True)

    # === 环比计算 ===
    last_month = sorted_history[0] if len(sorted_history) >= 1 else None
    two_months_ago = sorted_history[1] if len(sorted_history) >= 2 else None

    mom_capital = 0.0
    mom_capital_pct = 0.0
    mom_pending_change = 0.0
    mom_rate_change = 0.0

    if last_month:
        prev_capital = last_month.get("total_capital", 0)
        curr_capital = current_metrics.get("total_current", 0)
        if prev_capital > 0:
            mom_capital = curr_capital - prev_capital
            mom_capital_pct = (mom_capital / prev_capital) * 100

        curr_pending = current_metrics.get("total_pending", 0)
        prev_pending = last_month.get("pending", 0)
        mom_pending_change = curr_pending - prev_pending

        curr_rate = current_metrics.get("total_rate", 0)
        prev_rate = last_month.get("rate", 0)
        mom_rate_change = curr_rate - prev_rate

    # === 近3月月均支出（velocity）===
    recent_records = sorted_history[:3] if len(sorted_history) >= 3 else sorted_history
    if len(recent_records) >= 2:
        first_record = recent_records[-1]  # 最早的一条
        last_record = recent_records[0]  # 最近的一条
        months_span = len(recent_records) - 1
        capital_diff = last_record.get("total_capital", 0) - first_record.get("total_capital", 0)
        avg_monthly_spend = capital_diff / months_span if months_span > 0 else 0
    else:
        # fallback：用本月支出作为月均
        avg_monthly_spend = current_metrics.get("total_today_month", 0)

    # === 支出节奏分析 ===
    month_index = datetime.now().month
    expected_cumulative = avg_monthly_spend * month_index

    # === 目标完成预测 ===
    year_target = current_metrics.get("year_target", 0)
    total_current = current_metrics.get("total_current", 0)
    remaining = year_target - total_current
    months_left = max(12 - month_index, 1)
    required_monthly = remaining / months_left if remaining > 0 else 0

    # 场景预测
    best_case = total_current + (avg_monthly_spend * 1.2 * months_left)
    likely_case = total_current + (avg_monthly_spend * months_left)
    worst_case = total_current + (avg_monthly_spend * 0.6 * months_left)

    # === 风险项检测 ===
    risk_items = []

    # 待收货异常增长
    if mom_pending_change > 20:
        risk_items.append({
            "type": "pending_surge",
            "severity": "high",
            "description": f"待收货较上月激增 {mom_pending_change:.1f} 万元，增长过快",
            "implication": "订单执行脱节，需立即核查订单到货进度"
        })
    elif mom_pending_change > 10:
        risk_items.append({
            "type": "pending_rise",
            "severity": "medium",
            "description": f"待收货较上月增加 {mom_pending_change:.1f} 万元",
            "implication": "需关注订单转化效率"
        })

    # 支出放缓检测
    if avg_monthly_spend > 0 and required_monthly > 0:
        if avg_monthly_spend < required_monthly * 0.5:
            risk_items.append({
                "type": "spend_slowdown",
                "severity": "high",
                "description": f"月均支出 {avg_monthly_spend:.1f} 万元，低于达标所需的 {required_monthly:.1f} 万元/月",
                "implication": f"按此趋势，年度目标将缺口约 {max(year_target - likely_case, 0):.1f} 万元"
            })
        elif avg_monthly_spend < required_monthly * 0.8:
            risk_items.append({
                "type": "spend_gap",
                "severity": "medium",
                "description": f"月均支出 {avg_monthly_spend:.1f} 万元，略低于达标所需的 {required_monthly:.1f} 万元/月",
                "implication": "需适当提速才能完成年度目标"
            })

    # 转固率下滑
    if last_month:
        prev_rate = last_month.get("rate", 0)
        current_rate = current_metrics.get("total_rate", 0)
        if prev_rate > 0 and current_rate < prev_rate - 0.1:
            risk_items.append({
                "type": "rate_decline",
                "severity": "medium",
                "description": f"转固率较上月下降 {(prev_rate - current_rate) * 100:.1f} 个百分点",
                "implication": "工程结转进度放缓，需加快验收流程"
            })

    # 支出为0或极低
    if avg_monthly_spend < 0.01 and total_current < year_target * 0.3:
        risk_items.append({
            "type": "stall_risk",
            "severity": "high",
            "description": "近月支出几乎停滞（低于0.01万元），项目推进严重滞后",
            "implication": "需立即排查项目停滞原因，推动重启"
        })

    return {
        # 趋势数据
        "mom_capital_change": round(mom_capital, 2),
        "mom_capital_change_pct": round(mom_capital_pct, 1),
        "mom_pending_change": round(mom_pending_change, 2),
        "mom_rate_change": round(mom_rate_change, 4),
        "avg_monthly_spend_3m": round(avg_monthly_spend, 2),
        "expected_cumulative_by_now": round(expected_cumulative, 2),

        # 预测
        "required_monthly_to_target": round(required_monthly, 2),
        "scenario_best": round(best_case, 2),
        "scenario_likely": round(likely_case, 2),
        "scenario_worst": round(worst_case, 2),
        "target_gap_likely": round(max(year_target - likely_case, 0), 2),

        # 风险
        "risk_items": risk_items,
        "risk_count": len(risk_items),

        # 辅助判断
        "velocity_status": "正常" if avg_monthly_spend >= required_monthly else "不足",
    }


def _compute_fallback_trends(current_metrics: dict) -> dict:
    """无历史数据时的趋势计算兜底"""
    avg_monthly = current_metrics.get("total_today_month", 0)
    year_target = current_metrics.get("year_target", 0)
    total_current = current_metrics.get("total_current", 0)
    remaining = year_target - total_current
    months_left = max(12 - datetime.now().month, 1)
    required = remaining / months_left if remaining > 0 else 0

    return {
        "mom_capital_change": 0.0,
        "mom_capital_change_pct": 0.0,
        "mom_pending_change": 0.0,
        "mom_rate_change": 0.0,
        "avg_monthly_spend_3m": round(avg_monthly, 2),
        "expected_cumulative_by_now": 0.0,
        "required_monthly_to_target": round(required, 2),
        "scenario_best": 0.0,
        "scenario_likely": 0.0,
        "scenario_worst": 0.0,
        "target_gap_likely": round(max(year_target - total_current - avg_monthly * months_left, 0), 2),
        "risk_items": [],
        "risk_count": 0,
        "velocity_status": "未知",
    }
