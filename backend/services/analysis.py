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


# ===== 四类工程分析所需字段 =====
FOUR_CLASS_COLUMNS = [
    "工程编码",
    "工程名称",
    "一级专业",
    "验收类型",
    "工程管理员",
    "工程关闭状态",
    "初验批复日期",
    "预转固日期",
    "决算转固日期",
    "终验批复日期",
    "应预转固日期",
    "应关闭日期",
    "长期挂账建议关闭日期",
    "累计订单金额(列帐及时性)",
    "累计收货金额(列帐及时性)",
    "立项批复日期",
]

# 四类工程类型常量
TYPE_LIEZHANG = "列账不及时"
TYPE_YUZZHUANG = "预转固不及时"
TYPE_GUANBI = "关闭不及时"
TYPE_GUAZHANG = "长期挂账"

# 颜色常量
C_NAVY = "1B2A4A"
C_BLUE = "2E5F9E"
C_RED = "C00000"
C_GREEN = "375623"
C_YELLOW = "FFFF00"


def parse_date(df, col):
    """解析日期列，返回处理后的 Series（datetime 或 NaT）"""
    return pd.to_datetime(df[col], errors="coerce")


def build_four_class_warnings(df: pd.DataFrame) -> dict:
    """
    按照Agent规范构建四类工程预警数据
    """
    # ========== 配置参数 ==========
    WARN_DAYS = 60        # 预警窗口（天）
    PRETRANSFER_DAYS = 60  # 预转固截止天数
    ONE_VERIFY_DAYS = 150 # 一次验收关闭截止天数
    TWO_VERIFY_DAYS = 90  # 两次验收关闭截止天数

    df = df.copy()

    # 检查必要的列是否存在
    missing = [col for col in FOUR_CLASS_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"四类工程分析缺少必要列: {', '.join(missing)}")

    # ========== 日期列解析 ==========
    date_cols = [
        "初验批复日期", "预转固日期", "决算转固日期", "终验批复日期",
        "应预转固日期", "应关闭日期", "长期挂账建议关闭日期", "立项批复日期",
        "工程关闭日期"
    ]
    for col in date_cols:
        if col in df.columns:
            df[col] = parse_date(df, col)

    # ========== 数据过滤 ==========
    mask_exclude = (
        df["工程名称"].str.contains("局房|基础设施", na=False, regex=True) |
        df["一级专业"].str.contains("局房|基础设施", na=False, regex=True)
    )
    df_work = df[~mask_exclude].copy()
    # 排除已关闭工程
    if "工程关闭状态" in df_work.columns:
        df_work = df_work[df_work["工程关闭状态"] != "工程已关闭"]

    # 派生字段：实际预转固日期
    df_work["实际预转固日期"] = df_work["预转固日期"].fillna(df_work["决算转固日期"])

    # 当前日期
    today = datetime.now()
    today_ts = pd.Timestamp(today)
    today_str = today.strftime("%Y-%m-%d")

    warnings = []
    seq = 1  # 序号

    # ========== 状态排序映射 ==========
    STATUS_ORDER = {"已触发": 1, "已触发(超期完成)": 2, "预警": 3}
    TYPE_ORDER = {"列账不及时": 1, "预转固不及时": 2, "关闭不及时": 3, "长期挂账": 4}

    def get_diff_days(end, start):
        """计算天数差异（end - start）"""
        if pd.isna(end) or pd.isna(start):
            return 0
        return (end - start).days

    def parse_days_from_label(label):
        """从天数文字中提取数字"""
        import re
        match = re.search(r'(\d+)', label)
        return int(match.group(1)) if match else 0

    # ========== TYPE A: 列账不及时 ==========
    # 触发：receiptRate < 0.85，预警：0.85 <= receiptRate < 0.90
    df_a = df_work[df_work["初验批复日期"].notna()].copy()
    for _, row in df_a.iterrows():
        order_amt = safe_float(row["累计订单金额(列帐及时性)"])
        receive_amt = safe_float(row["累计收货金额(列帐及时性)"])
        receipt_rate = receive_amt / order_amt if order_amt > 0 else 0

        if receipt_rate < 0.85:
            status = "已触发"
            pct_str = f"{receipt_rate * 100:.1f}"
            days_label = f"收货{pct_str}%"
            suggestion = f"收货占比{pct_str}%，低于85%红线，立即协调施工单位完成量价推送及收货列账"
        elif receipt_rate < 0.90:
            status = "预警"
            pct_str = f"{receipt_rate * 100:.1f}"
            days_label = f"收货{pct_str}%"
            suggestion = f"收货占比{pct_str}%，接近85%红线，请关注列账进度，避免触发四类工程考核"
        else:
            continue  # 正常，不记录

        warnings.append({
            "id": seq,
            "status": status,
            "type": "列账不及时",
            "code": str(row.get("工程编码", "")) if pd.notna(row.get("工程编码")) else "",
            "name": str(row["工程名称"])[:50],
            "major": str(row["一级专业"]) if pd.notna(row["一级专业"]) else "",
            "acceptType": str(row["验收类型"]) if pd.notna(row["验收类型"]) else "",
            "manager": str(row["工程管理员"]) if pd.notna(row["工程管理员"]) else "",
            "keyDate": row["初验批复日期"].strftime("%Y-%m-%d") if pd.notna(row["初验批复日期"]) else "",
            "keyDateLabel": "初验批复日期",
            "deadline": "",
            "projectStatus": (str(row["工程状态"]) if pd.notna(row["工程状态"]) else "") if "工程状态" in row.index else "",
            "daysLabel": days_label,
            "suggestion": suggestion,
        })
        seq += 1

    # ========== TYPE B: 预转固不及时 ==========
    # 前提：初验批复日期不为空
    # 已触发（未完成）：actualTransferDate为空 && preTransferDeadline < TODAY
    # 已触发（超期完成）：actualTransferDate不为空 && actualTransferDate > preTransferDeadline
    # 预警：actualTransferDate为空 && (preTransferDeadline - TODAY) <= 60天
    df_b = df_work[df_work["初验批复日期"].notna()].copy()
    for _, row in df_b.iterrows():
        key_date = row["初验批复日期"]
        actual_date = row["实际预转固日期"]

        # 优先用系统字段，否则手动计算
        if pd.notna(row.get("应预转固日期")):
            deadline = row["应预转固日期"]
        else:
            deadline = key_date + pd.Timedelta(days=PRETRANSFER_DAYS)

        deadline_str = deadline.strftime("%Y-%m-%d") if pd.notna(deadline) else ""

        if pd.notna(actual_date):
            # 有实际预转固日期，检查是否超期完成
            diff = get_diff_days(actual_date, deadline)
            if diff > 0:
                status = "已触发(超期完成)"
                days_label = f"超期{diff}天完成"
                suggestion = f"预转固已完成但超出60天截止期{diff}天，注意留存整改说明"
            else:
                continue  # 提前完成或正常，不记录
        else:
            # 未完成，检查是否已触发或预警
            diff = get_diff_days(today_ts, deadline)
            if diff > 0:
                status = "已触发"
                days_label = f"逾期{diff}天"
                suggestion = "初验批复已超60天截止期仍未预转固，立即协调财务办理预转固手续"
            elif diff >= -WARN_DAYS:
                status = "预警"
                days_label = f"剩余{abs(diff)}天"
                suggestion = f"距预转固截止日期仅{abs(diff)}天，尽快准备预转固材料提交财务"
            else:
                continue  # 距离截止日期还早

        warnings.append({
            "id": seq,
            "status": status,
            "type": "预转固不及时",
            "code": str(row.get("工程编码", "")) if pd.notna(row.get("工程编码")) else "",
            "name": str(row["工程名称"])[:50],
            "major": str(row["一级专业"]) if pd.notna(row["一级专业"]) else "",
            "acceptType": str(row["验收类型"]) if pd.notna(row["验收类型"]) else "",
            "manager": str(row["工程管理员"]) if pd.notna(row["工程管理员"]) else "",
            "keyDate": key_date.strftime("%Y-%m-%d") if pd.notna(key_date) else "",
            "keyDateLabel": "初验批复日期",
            "deadline": deadline_str,
            "projectStatus": (str(row["工程状态"]) if pd.notna(row["工程状态"]) else "") if "工程状态" in row.index else "",
            "daysLabel": days_label,
            "suggestion": suggestion,
        })
        seq += 1

    # ========== TYPE C: 关闭不及时 ==========
    # 前提：终验批复日期不为空
    # 已触发：closeDeadline < TODAY
    # 预警：(closeDeadline - TODAY) <= 60天
    df_c = df_work[df_work["终验批复日期"].notna()].copy()
    for _, row in df_c.iterrows():
        key_date = row["终验批复日期"]
        accept_type = str(row["验收类型"]) if pd.notna(row["验收类型"]) else ""

        # 优先用系统字段，否则手动计算
        if pd.notna(row.get("应关闭日期")):
            deadline = row["应关闭日期"]
        else:
            days_limit = TWO_VERIFY_DAYS if accept_type == "两次验收" else ONE_VERIFY_DAYS
            deadline = key_date + pd.Timedelta(days=days_limit)

        deadline_str = deadline.strftime("%Y-%m-%d") if pd.notna(deadline) else ""

        diff = get_diff_days(today_ts, deadline)
        if diff > 0:
            status = "已触发"
            days_label = f"逾期{diff}天"
            if accept_type == "两次验收":
                suggestion = "终验批复后已超90天期限，须立即启动工程关闭（正式转固）流程"
            else:
                suggestion = "终验批复后已超150天期限，须立即启动工程关闭（正式转固）流程"
        elif diff >= -WARN_DAYS:
            status = "预警"
            days_label = f"剩余{abs(diff)}天"
            if accept_type == "两次验收":
                suggestion = f"距90天截止期仅{abs(diff)}天，加快推进结算审计和工程关闭手续"
            else:
                suggestion = f"距150天截止期仅{abs(diff)}天，加快推进结算审计和工程关闭手续"
        else:
            continue  # 距离截止日期还早

        warnings.append({
            "id": seq,
            "status": status,
            "type": "关闭不及时",
            "code": str(row.get("工程编码", "")) if pd.notna(row.get("工程编码")) else "",
            "name": str(row["工程名称"])[:50],
            "major": str(row["一级专业"]) if pd.notna(row["一级专业"]) else "",
            "acceptType": accept_type,
            "manager": str(row["工程管理员"]) if pd.notna(row["工程管理员"]) else "",
            "keyDate": key_date.strftime("%Y-%m-%d") if pd.notna(key_date) else "",
            "keyDateLabel": "终验批复日期",
            "deadline": deadline_str,
            "projectStatus": (str(row["工程状态"]) if pd.notna(row["工程状态"]) else "") if "工程状态" in row.index else "",
            "daysLabel": days_label,
            "suggestion": suggestion,
        })
        seq += 1

    # ========== TYPE D: 长期挂账 ==========
    # 前提：长期挂账建议关闭日期不为空
    # 已触发：长期挂账建议关闭日期 < TODAY
    # 预警：(长期挂账建议关闭日期 - TODAY) <= 60天
    df_d = df_work[df_work["长期挂账建议关闭日期"].notna()].copy()
    for _, row in df_d.iterrows():
        key_date = row["立项批复日期"]
        deadline = row["长期挂账建议关闭日期"]

        deadline_str = deadline.strftime("%Y-%m-%d") if pd.notna(deadline) else ""
        key_date_str = key_date.strftime("%Y-%m-%d") if pd.notna(key_date) else ""

        diff = get_diff_days(today_ts, deadline)
        if diff > 0:
            status = "已触发"
            days_label = f"逾期{diff}天"
            suggestion = "实际工期已超建议工期2倍，属长期挂账工程，优先推动验收及关闭"
        elif diff >= -WARN_DAYS:
            status = "预警"
            days_label = f"剩余{abs(diff)}天"
            suggestion = f"距长期挂账建议关闭日期仅{abs(diff)}天，工程存在超期挂账风险，加快推进"
        else:
            continue  # 距离截止日期还早

        warnings.append({
            "id": seq,
            "status": status,
            "type": "长期挂账",
            "code": str(row.get("工程编码", "")) if pd.notna(row.get("工程编码")) else "",
            "name": str(row["工程名称"])[:50],
            "major": str(row["一级专业"]) if pd.notna(row["一级专业"]) else "",
            "acceptType": str(row["验收类型"]) if pd.notna(row["验收类型"]) else "",
            "manager": str(row["工程管理员"]) if pd.notna(row["工程管理员"]) else "",
            "keyDate": key_date_str,
            "keyDateLabel": "立项批复日期",
            "deadline": deadline_str,
            "projectStatus": (str(row["工程状态"]) if pd.notna(row["工程状态"]) else "") if "工程状态" in row.index else "",
            "daysLabel": days_label,
            "suggestion": suggestion,
        })
        seq += 1

    # ========== 排序 ==========
    def sort_key(w):
        s_order = STATUS_ORDER.get(w["status"], 99)
        t_order = TYPE_ORDER.get(w["type"], 99)
        # 第三级排序
        num = parse_days_from_label(w["daysLabel"])
        if w["status"].startswith("已触发"):
            # 已触发按逾期天数降序
            return (s_order, t_order, -num)
        else:
            # 预警按剩余天数升序
            return (s_order, t_order, num)

    warnings.sort(key=sort_key)

    # 重新编号
    for i, w in enumerate(warnings, 1):
        w["id"] = i

    # ========== 统计汇总 ==========
    type_summary = {
        "列账不及时": {"triggered": 0, "warning": 0},
        "预转固不及时": {"triggered": 0, "warning": 0},
        "关闭不及时": {"triggered": 0, "warning": 0},
        "长期挂账": {"triggered": 0, "warning": 0},
    }
    for w in warnings:
        if w["status"].startswith("已触发"):
            type_summary[w["type"]]["triggered"] += 1
        else:
            type_summary[w["type"]]["warning"] += 1

    hit_count = sum(1 for w in warnings if w["status"].startswith("已触发"))
    warn_count = sum(1 for w in warnings if w["status"] == "预警")

    return {
        "summary": type_summary,
        "items": warnings,
        "analysis_date": today_str,
        "total": len(warnings),
        "hit_count": hit_count,
        "warn_count": warn_count,
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

    # 构建四类工程预警
    four_class = build_four_class_warnings(df)

    return {
        "success": True,
        "data": {
            "summary": summary.to_dict(orient="records"),
            "metrics": metrics,
            "dashboard": dashboard_data,
            "four_class_warnings": four_class,
        }
    }
