# -*- coding: utf-8 -*-
"""
预算分析服务
"""
import math
import pandas as pd


def safe_float(val):
    """安全转换为 float，处理 NaN 和 Infinity"""
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def extract_budget_totals(df, project_totals=None):
    """从预算汇总表提取合计行"""
    project_totals = project_totals or {}
    for _, row in df.iterrows():
        first_val = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
        if "合计" not in first_val:
            continue
        try:
            budget = safe_float(row.iloc[1]) if pd.notna(row.iloc[1]) else 0
            occupied = project_totals.get("occupied_total", safe_float(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else 0)
            preoccupied = project_totals.get("preoccupied_total", safe_float(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else 0)
            return {"年度预算": round(budget or 0, 2), "已占用": round(occupied or 0, 2), "预占用": round(preoccupied or 0, 2)}
        except (ValueError, TypeError):
            pass
    return {"年度预算": 0, "已占用": 0, "预占用": 0}


def build_budget_categories(df, project_summary=None, spend_summary=None):
    """提取预算分类明细"""
    project_summary = project_summary or {}
    spend_summary = spend_summary or {}
    cats = []
    for i, row in df.iterrows():
        if i == 0:
            continue
        try:
            cat_name = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
            if not cat_name or "合计" in cat_name:
                continue
            budget = safe_float(row.iloc[1]) if pd.notna(row.iloc[1]) else 0
            occupied = project_summary.get(cat_name, {}).get("occupied", safe_float(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else 0)
            preoccupied = project_summary.get(cat_name, {}).get("preoccupied", safe_float(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else 0)
            annual_spend = spend_summary.get(cat_name, 0) or 0
            subtotal = (occupied or 0) + (preoccupied or 0)
            progress = subtotal / budget if budget else 0
            spend_progress = annual_spend / budget if budget else 0
            cats.append({
                "name": cat_name,
                "budget": round(budget or 0, 2),
                "annual_spend": round(annual_spend or 0, 2),
                "occupied": round(occupied or 0, 2),
                "preoccupied": round(preoccupied or 0, 2),
                "subtotal": round(subtotal, 2),
                "progress": round(progress or 0, 4),
                "spend_progress": round(spend_progress or 0, 4),
            })
        except Exception:
            pass
    return cats


def summarize_projects(df):
    """按一级专业汇总项目占用和预占用。"""
    if df is None:
        return {}, {"occupied_total": 0, "preoccupied_total": 0}

    category_map = {}
    occupied_total = 0
    preoccupied_total = 0

    for _, row in df.iterrows():
        try:
            category = str(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else ""
            occupied = safe_float(row.iloc[4]) if len(row) > 4 and pd.notna(row.iloc[4]) else 0
            preoccupied = safe_float(row.iloc[5]) if len(row) > 5 and pd.notna(row.iloc[5]) else 0
            if not category:
                continue

            category_map.setdefault(category, {"occupied": 0, "preoccupied": 0})
            category_map[category]["occupied"] += occupied or 0
            category_map[category]["preoccupied"] += preoccupied or 0
            occupied_total += occupied or 0
            preoccupied_total += preoccupied or 0
        except Exception:
            pass

    return (
        {
            key: {
                "occupied": round(value["occupied"], 2),
                "preoccupied": round(value["preoccupied"], 2),
            }
            for key, value in category_map.items()
        },
        {
            "occupied_total": round(occupied_total, 2),
            "preoccupied_total": round(preoccupied_total, 2),
        },
    )


def build_project_details(df):
    """提取新建项目明细"""
    projects = []
    for _, row in df.iterrows():
        try:
            code = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
            name = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ""
            manager = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else ""
            category = str(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else ""
            occupied = safe_float(row.iloc[4]) if len(row) > 4 and pd.notna(row.iloc[4]) else 0
            preoccupied = safe_float(row.iloc[5]) if len(row) > 5 and pd.notna(row.iloc[5]) else 0
            if code or name:
                projects.append({
                    "code": code,
                    "name": name,
                    "manager": manager,
                    "category": category,
                    "occupied": round(occupied or 0, 2),
                    "preoccupied": round(preoccupied or 0, 2),
                })
        except Exception:
            pass
    return projects


def analyze_budget(df_summary, df_projects, spend_summary=None):
    """分析预算数据"""
    spend_summary = spend_summary or {}
    project_summary, project_totals = summarize_projects(df_projects)
    totals = extract_budget_totals(df_summary, project_totals)

    total_budget = totals.get("年度预算", 0) or 0
    total_occupied = totals.get("已占用", 0) or 0
    total_preoccupied = totals.get("预占用", 0) or 0
    total_used = total_occupied + total_preoccupied
    approval_progress = (total_used / total_budget) if total_budget > 0 else 0

    categories = build_budget_categories(df_summary, project_summary, spend_summary)
    annual_spend_total = round(sum(item.get("annual_spend", 0) for item in categories), 2)
    spend_progress = (annual_spend_total / total_budget) if total_budget > 0 else 0

    projects = build_project_details(df_projects) if df_projects is not None else []

    return {
        "budget_total": total_budget,
        "annual_spend_total": annual_spend_total,
        "occupied_total": total_occupied,
        "preoccupied_total": total_preoccupied,
        "total_used": round(total_used, 2),
        "approval_progress": round(approval_progress, 4),
        "spend_progress": round(spend_progress, 4),
        "categories": categories,
        "projects": projects,
    }
