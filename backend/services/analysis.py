# -*- coding: utf-8 -*-
"""
在建工程分析服务 - 核心业务逻辑
"""
import math
import pandas as pd
from datetime import datetime, timedelta

def safe_float(val):
    """安全转换为 float，处理 NaN 和 Infinity"""
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return 0.0
        return f
    except (ValueError, TypeError):
        return 0.0

# ===== 字段常量 =====
REQUIRED_COLUMNS = [
    "工程管理员",
    "工程名称",
    "结转额（工程总投资-累计资本支出）",
    "本年累计资本性支出",
    "累计订单金额(列帐及时性)",
    "累计收货金额(列帐及时性)",
    "本月资本性支出",
    "在建工程期末余额",
    "工程物资",
    "在建工程年初数",
    "工程物资年初数",
]

NUMERIC_COLUMNS = [
    "结转额（工程总投资-累计资本支出）",
    "本年累计资本性支出",
    "累计订单金额(列帐及时性)",
    "累计收货金额(列帐及时性)",
    "本月资本性支出",
    "在建工程期末余额",
    "工程物资",
    "在建工程年初数",
    "工程物资年初数",
]

# 工程管理员自定义排序顺序
ADMIN_SORT_ORDER = ["伍建勋", "张文", "袁爱平", "魏东"]


def load_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """验证并预处理 DataFrame"""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError("缺少必要列: " + ", ".join(missing))

    df = df.copy()
    df["工程管理员"] = df["工程管理员"].fillna("未分配").astype(str).str.strip()
    df.loc[df["工程管理员"] == "", "工程管理员"] = "未分配"

    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # 计算待收货金额
    df["待收货金额"] = df["累计订单金额(列帐及时性)"] - df["累计收货金额(列帐及时性)"]

    # 计算转固率
    denominator = df["本年累计资本性支出"] + df["在建工程年初数"] + df["工程物资年初数"]
    numerator = df["在建工程期末余额"] + df["工程物资"]
    df["转固率"] = 0.0
    valid_mask = denominator != 0
    df.loc[valid_mask, "转固率"] = 1 - numerator[valid_mask] / denominator[valid_mask]

    # 清理无效值
    df["转固率"] = df["转固率"].replace([float('inf'), float('-inf')], 0.0)
    df["转固率"] = df["转固率"].fillna(0.0)

    return df


def calculate_total_rate(df: pd.DataFrame) -> float:
    """计算综合转固率"""
    denominator = (
        df["本年累计资本性支出"].sum()
        + df["在建工程年初数"].sum()
        + df["工程物资年初数"].sum()
    )
    if denominator == 0:
        return 0.0
    numerator = df["在建工程期末余额"].sum() + df["工程物资"].sum()
    return 1 - numerator / denominator


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    """按工程管理员汇总"""
    grouped = (
        df.groupby("工程管理员", dropna=False)
        .agg(
            {
                "结转额（工程总投资-累计资本支出）": "sum",
                "本年累计资本性支出": "sum",
                "待收货金额": "sum",
                "本月资本性支出": "sum",
                "在建工程期末余额": "sum",
                "工程物资": "sum",
                "在建工程年初数": "sum",
                "工程物资年初数": "sum",
            }
        )
        .reset_index()
    )

    # 按自定义顺序排序
    admin_order = {name: i for i, name in enumerate(ADMIN_SORT_ORDER)}
    grouped["_sort_key"] = grouped["工程管理员"].map(
        lambda x: admin_order.get(x, len(ADMIN_SORT_ORDER) + hash(x) % 1000)
    )
    grouped = grouped.sort_values(by="_sort_key", ascending=True, ignore_index=True)
    grouped = grouped.drop(columns=["_sort_key"])

    # 转为万元
    for col in [
        "结转额（工程总投资-累计资本支出）",
        "本年累计资本性支出",
        "待收货金额",
        "本月资本性支出",
    ]:
        grouped[col] = grouped[col] / 10000

    # 计算管理员维度的转固率
    def calc_rate(row):
        capital_w = row["本年累计资本性支出"]
        begin_w = row["在建工程年初数"] / 10000
        mat_begin_w = row["工程物资年初数"] / 10000
        balance_w = row["在建工程期末余额"] / 10000
        mat_w = row["工程物资"] / 10000
        denom = capital_w + begin_w + mat_begin_w
        if denom == 0:
            return 0.0
        numer = balance_w + mat_w
        rate = 1 - numer / denom
        # 清理无效值
        if not (-1000 < rate < 1000):
            return 0.0
        return rate

    grouped["转固率"] = grouped.apply(calc_rate, axis=1)
    # 确保没有 NaN 或 Infinity
    grouped["转固率"] = grouped["转固率"].replace([float('inf'), float('-inf')], 0.0).fillna(0.0)

    # 重命名列
    grouped = grouped.rename(
        columns={
            "结转额（工程总投资-累计资本支出）": "结转额",
            "待收货金额": "已下单待收货",
        }
    )

    # 添加合计行
    total_rate = calculate_total_rate(df)
    total_row = pd.DataFrame(
        [
            {
                "工程管理员": "合计",
                "结转额": grouped["结转额"].sum(),
                "本年累计资本性支出": grouped["本年累计资本性支出"].sum(),
                "已下单待收货": grouped["已下单待收货"].sum(),
                "本月资本性支出": grouped["本月资本性支出"].sum(),
                "转固率": total_rate,
            }
        ]
    )

    return pd.concat([grouped, total_row], ignore_index=True)


def build_metrics(df: pd.DataFrame, summary: pd.DataFrame, year_target: float) -> dict:
    """构建核心指标"""
    total_current = safe_float(summary.iloc[-1]["本年累计资本性支出"])
    total_pending = safe_float(summary.iloc[-1]["已下单待收货"])
    total_today_month = safe_float(summary.iloc[-1]["本月资本性支出"])
    total_transfer = safe_float(summary.iloc[-1]["结转额"])
    total_rate = safe_float(summary.iloc[-1]["转固率"])
    progress_ratio = 0.0 if year_target == 0 else total_current / year_target
    deficit = year_target - total_current

    return {
        "total_current": round(total_current, 2),
        "total_pending": round(total_pending, 2),
        "total_today_month": round(total_today_month, 2),
        "total_transfer": round(total_transfer, 2),
        "total_rate": round(total_rate, 4),
        "progress_ratio": round(progress_ratio, 4),
        "progress_pct": round(progress_ratio * 100, 2),
        "deficit": round(deficit, 2),
        "year_target": year_target,
    }


def build_dashboard_data(summary: pd.DataFrame, metrics: dict, month_label: str, detail_df: pd.DataFrame = None) -> dict:
    """构建大屏展示数据"""
    detail_rows = summary.iloc[:-1].copy()

    # 待收货压力预警（超过30万的管理员）
    top_pending = detail_rows.sort_values("已下单待收货", ascending=False)
    pending_pressure = len(top_pending[top_pending["已下单待收货"] > 30])

    # 转固率预警
    rate_status = "偏低" if metrics["total_rate"] < 0.6 else "正常"

    # 构建明细数据（工程维度）
    detail_list = []
    if detail_df is not None:
        for _, row in detail_df.iterrows():
            detail_list.append({
                "工程名称": str(row["工程名称"]),
                "工程管理员": str(row["工程管理员"]),
                "结转额": round(float(row["结转额（工程总投资-累计资本支出）"]), 2),
                "本年累计资本性支出": round(float(row["本年累计资本性支出"]), 2),
                "已下单待收货": round(float(row["待收货金额"]), 2),
                "本月资本性支出": round(float(row["本月资本性支出"]), 2),
                "在建工程期末余额": round(float(row["在建工程期末余额"]) / 10000, 4),
                "转固率": round(float(row["转固率"]), 4),
            })

    return {
        "monthLabel": month_label,
        "metrics": {
            "capital": metrics["total_current"],
            "pending": metrics["total_pending"],
            "monthSpend": metrics["total_today_month"],
            "transfer": metrics["total_transfer"],
            "rate": metrics["total_rate"],
            "progress": metrics["progress_ratio"],
            "deficit": metrics["deficit"],
            "yearTarget": metrics["year_target"],
        },
        "summary": [
            {
                "manager": row["工程管理员"],
                "transfer": round(float(row["结转额"]), 2),
                "capital": round(float(row["本年累计资本性支出"]), 2),
                "pending": round(float(row["已下单待收货"]), 2),
                "monthSpend": round(float(row["本月资本性支出"]), 2),
                "rate": round(float(row["转固率"]), 4),
            }
            for _, row in detail_rows.iterrows()
        ],
        "detail": detail_list,
        "alerts": [
            {
                "title": "待收货压力",
                "value": f"{pending_pressure} 位管理员超过30万元",
            },
            {
                "title": "转固率状态",
                "value": rate_status,
            },
            {
                "title": "目标差额",
                "value": f"{metrics['deficit']:.2f} 万元" if metrics["deficit"] > 0 else "已达成目标",
            },
        ],
    }


def analyze(df: pd.DataFrame, year_target: float = 503.0, month_label: str = None) -> dict:
    """
    核心分析函数 - 接收 DataFrame，返回分析结果字典
    """
    # 数据预处理
    df_processed = load_dataframe(df)

    # 构建汇总
    summary = build_summary(df_processed)

    # 构建指标
    metrics = build_metrics(df_processed, summary, year_target)

    # 构建大屏数据
    if month_label is None:
        month_label = datetime.now().strftime("%Y年%m月")
    dashboard_data = build_dashboard_data(summary, metrics, month_label, df_processed)

    return {
        "success": True,
        "data": {
            "summary": summary.to_dict(orient="records"),
            "metrics": metrics,
            "dashboard": dashboard_data,
        }
    }
