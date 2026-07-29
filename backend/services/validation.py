# -*- coding: utf-8 -*-
"""
上传校验摘要 — 帮助业务确认「传对表、算对数」。

不改变分析结果，只在上传响应中附带结构化 validation 字段。
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import pandas as pd

from services.analysis import (
    FOUR_CLASS_COLUMNS,
    REQUIRED_COLUMNS,
    safe_float,
)


OPTIONAL_HINT_COLUMNS = [
    "一级专业",
    "工程编码",
    "施工单位",
    "验收类型",
    "工程关闭状态",
    "初验批复日期",
    "预转固日期",
    "决算转固日期",
    "终验批复日期",
    "立项批复日期",
]


def _round2(v: float) -> float:
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return 0.0
        return round(f, 2)
    except (TypeError, ValueError):
        return 0.0


def build_zaigong_validation(df: pd.DataFrame, metrics: Optional[dict] = None) -> Dict[str, Any]:
    """在建工程上传校验摘要。df 为原始读入表（单位：元）。"""
    total_rows = int(len(df))
    columns = [str(c) for c in df.columns]

    missing_required = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    missing_optional = [c for c in OPTIONAL_HINT_COLUMNS if c not in df.columns]
    missing_four_class = [c for c in FOUR_CLASS_COLUMNS if c not in df.columns]

    empty_manager_rows = 0
    if "工程管理员" in df.columns:
        s = df["工程管理员"]
        empty_manager_rows = int(s.isna().sum() + (s.astype(str).str.strip() == "").sum())

    # 金额 checksum（元 → 万元，与 metrics 对齐）
    capital_yuan = 0.0
    pending_yuan = 0.0
    month_yuan = 0.0
    if "本年累计资本性支出" in df.columns:
        capital_yuan = float(pd.to_numeric(df["本年累计资本性支出"], errors="coerce").fillna(0).sum())
    if "累计订单金额(列帐及时性)" in df.columns and "累计收货金额(列帐及时性)" in df.columns:
        orders = pd.to_numeric(df["累计订单金额(列帐及时性)"], errors="coerce").fillna(0)
        receipts = pd.to_numeric(df["累计收货金额(列帐及时性)"], errors="coerce").fillna(0)
        pending_yuan = float((orders - receipts).sum())
    if "本月资本性支出" in df.columns:
        month_yuan = float(pd.to_numeric(df["本月资本性支出"], errors="coerce").fillna(0).sum())

    # 四类预警分析对象过滤预估（与 build_four_class_warnings 同口径的粗算）
    four_class_excluded = 0
    four_class_base = total_rows
    if "工程名称" in df.columns or "一级专业" in df.columns:
        mask_exclude = pd.Series(False, index=df.index)
        if "工程名称" in df.columns:
            mask_exclude = mask_exclude | df["工程名称"].astype(str).str.contains("局房|基础设施", na=False, regex=True)
        if "一级专业" in df.columns:
            mask_exclude = mask_exclude | df["一级专业"].astype(str).str.contains("局房|基础设施", na=False, regex=True)
        if "工程关闭状态" in df.columns:
            mask_exclude = mask_exclude | (df["工程关闭状态"].astype(str) == "工程已关闭")
        four_class_excluded = int(mask_exclude.sum())
        four_class_base = total_rows - four_class_excluded

    manager_count = 0
    if "工程管理员" in df.columns:
        managers = (
            df["工程管理员"].fillna("未分配").astype(str).str.strip().replace("", "未分配").unique()
        )
        manager_count = int(len([m for m in managers if m]))

    capital_wan = _round2(capital_yuan / 10000)
    pending_wan = _round2(pending_yuan / 10000)
    month_wan = _round2(month_yuan / 10000)

    warnings: List[str] = []
    if missing_required:
        warnings.append("缺少必要列: " + "、".join(missing_required))
    if missing_four_class:
        warnings.append("四类预警字段不完整，相关预警可能不可用")
    if "一级专业" not in df.columns:
        warnings.append("缺少「一级专业」，预算页年度支出无法按专业汇总")
    if empty_manager_rows:
        warnings.append(f"{empty_manager_rows} 行工程管理员为空，已归入「未分配」")

    notes: List[str] = [
        f"共 {total_rows} 行 · {manager_count} 位管理员",
        f"本年累计资本性支出合计 {capital_wan:.2f} 万元",
        f"已下单待收货合计 {pending_wan:.2f} 万元",
    ]
    if metrics:
        # 与计算结果交叉核对（容差 0.02 万）
        m_cap = safe_float(metrics.get("total_current"))
        m_pend = safe_float(metrics.get("total_pending"))
        if abs(m_cap - capital_wan) > 0.02:
            warnings.append(
                f"校验合计与计算结果不一致：资本支出 checksum={capital_wan:.2f} / metrics={m_cap:.2f}"
            )
        if abs(m_pend - pending_wan) > 0.02:
            warnings.append(
                f"校验合计与计算结果不一致：待收货 checksum={pending_wan:.2f} / metrics={m_pend:.2f}"
            )
        notes.append(
            f"综合转固率 {safe_float(metrics.get('total_rate')) * 100:.2f}% · 目标进度 {safe_float(metrics.get('progress_pct')):.2f}%"
        )

    if four_class_excluded:
        notes.append(f"四类预警分析对象排除 {four_class_excluded} 行（局房/基础设施/已关闭）")

    return {
        "kind": "zaigong",
        "total_rows": total_rows,
        "manager_count": manager_count,
        "empty_manager_rows": empty_manager_rows,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "missing_four_class": missing_four_class,
        "four_class_base_rows": four_class_base,
        "four_class_excluded_rows": four_class_excluded,
        "checksums": {
            "capital_wan": capital_wan,
            "pending_wan": pending_wan,
            "month_spend_wan": month_wan,
            "capital_yuan": _round2(capital_yuan),
            "pending_yuan": _round2(pending_yuan),
            "month_spend_yuan": _round2(month_yuan),
        },
        "columns_present": columns,
        "warnings": warnings,
        "notes": notes,
        "summary_text": "；".join(notes + ([f"注意：{'；'.join(warnings)}"] if warnings else [])),
    }


def build_budget_validation(
    df_summary: pd.DataFrame,
    df_projects: Optional[pd.DataFrame],
    result: Optional[dict] = None,
    project_sheet_name: Optional[str] = None,
) -> Dict[str, Any]:
    """预算上传校验摘要。"""
    summary_rows = int(len(df_summary)) if df_summary is not None else 0
    project_rows = int(len(df_projects)) if df_projects is not None else 0
    # pandas 读入后第一行常为标题被当列名，项目表同理；这里报告原始 sheet 行数感即可
    categories = (result or {}).get("categories") or []
    projects = (result or {}).get("projects") or []

    warnings: List[str] = []
    if df_projects is None:
        warnings.append("未识别到「新建项目明细」sheet，占用/预占用将依赖汇总表")
    if not categories:
        warnings.append("未解析到一级专业分类行")

    budget_total = _round2((result or {}).get("budget_total") or 0)
    occupied_total = _round2((result or {}).get("occupied_total") or 0)
    preoccupied_total = _round2((result or {}).get("preoccupied_total") or 0)
    annual_spend_total = _round2((result or {}).get("annual_spend_total") or 0)
    approval_progress = safe_float((result or {}).get("approval_progress"))
    spend_progress = safe_float((result or {}).get("spend_progress"))

    notes: List[str] = [
        f"汇总 sheet {summary_rows} 行 · 识别专业 {len(categories)} 个",
        f"项目明细 {len(projects)} 条" + (f"（sheet：{project_sheet_name}）" if project_sheet_name else ""),
        f"年度预算 {budget_total:.2f} · 已占用 {occupied_total:.2f} · 预占用 {preoccupied_total:.2f}",
        f"立项进度 {approval_progress * 100:.2f}% · 支出进度 {spend_progress * 100:.2f}%（年度支出 {annual_spend_total:.2f}）",
    ]

    return {
        "kind": "budget",
        "summary_rows": summary_rows,
        "project_sheet_rows": project_rows,
        "project_sheet_name": project_sheet_name,
        "category_count": len(categories),
        "project_count": len(projects),
        "checksums": {
            "budget_total": budget_total,
            "occupied_total": occupied_total,
            "preoccupied_total": preoccupied_total,
            "annual_spend_total": annual_spend_total,
            "approval_progress": round(approval_progress, 4),
            "spend_progress": round(spend_progress, 4),
        },
        "warnings": warnings,
        "notes": notes,
        "summary_text": "；".join(notes + ([f"注意：{'；'.join(warnings)}"] if warnings else [])),
    }


def format_validation_message(validation: Optional[dict], prefix: str = "分析完成") -> str:
    """把 validation 压成一行上传反馈文案。"""
    if not validation:
        return prefix
    text = validation.get("summary_text") or ""
    return f"{prefix}。{text}" if text else prefix
