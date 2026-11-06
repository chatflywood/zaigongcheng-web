"""Date-window project lists for human compliance verification."""
import calendar
import math
from datetime import date, datetime, timedelta
from decimal import Decimal

CHECKS = {
    "safety": {"label": "安全生产费核实", "field": "工程开工日期"},
    "quality": {"label": "质监申报核实", "field": "设计批复日期(初次)"},
}
STATUSES = ("待核实", "已核实正常", "发现问题")
EXCLUDED_SAFETY_TYPES = {"单纯购置项目", "单纯性购置项目", "零星购置项目"}


def text(value):
    if value is None or isinstance(value, float) and not math.isfinite(value):
        return ""
    return str(value).strip()


def parse_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    value = text(value)
    if not value or value.lower() in {"nan", "nat", "none", "null"}:
        return None
    if len(value) == 8 and value.isdigit():
        return datetime.strptime(value, "%Y%m%d").date()
    if value.replace(".", "", 1).isdigit() and float(value) < 3000000:
        return date(1899, 12, 30) + timedelta(days=int(float(value)))
    return date.fromisoformat(value[:10].replace("/", "-"))


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None


def project_snapshot(kind, row):
    """Keep enough source evidence to follow a case after it leaves an upload."""
    try:
        milestone = parse_date(row.get(CHECKS[kind]["field"]))
    except (ValueError, OverflowError):
        milestone = None
    return {
        "code": text(row.get("工程编码")), "name": text(row.get("工程名称")),
        "manager": text(row.get("工程管理员")) or "未分配",
        "project_type": text(row.get("项目类型")), "project_status": text(row.get("工程状态")),
        "construction_unit": text(row.get("施工单位")),
        "key_date": milestone.isoformat() if milestone else "",
        "approval_number": text(row.get("设计批复文号（初次）")),
        "current_safety_fee": number(row.get("安全生产费")),
        "total_safety_fee": number(row.get("累计待摊-安全生产费")),
    }


def verification_basis(kind, item):
    def amount(value):
        return None if value is None else str(Decimal(str(value)).quantize(Decimal("0.01")))
    if kind == "safety":
        return {"工程开工日期": item["key_date"],
                "本年安全生产费（元）": amount(item["current_safety_fee"]),
                "累计安全生产费（元）": amount(item["total_safety_fee"])}
    return {"首次设计批复日期": item["key_date"], "首次设计批复文号": item["approval_number"]}


def changed_basis(kind, item, review, uploaded_at):
    baseline = review.get("baseline")
    # Looking at an older upload must not reopen a review of newer source data.
    basis_date = review.get("basis_uploaded_at")
    if basis_date and datetime.fromisoformat(str(uploaded_at)).replace(tzinfo=None) < datetime.fromisoformat(basis_date).replace(tzinfo=None):
        return []
    if baseline is None:
        return ["原核实依据不可用，请重新核实"] if review.get("status") == "已核实正常" else []
    current = verification_basis(kind, item)
    return [f"{field}：{baseline.get(field) if baseline.get(field) not in (None, '') else '未提供'} → {value if value not in (None, '') else '未提供'}"
            for field, value in current.items() if baseline.get(field) != value]


def build_compliance(rows, uploaded_at, reviews=None):
    """Windowed intake, open-case follow-up, and persistent completed records."""
    end = parse_date(uploaded_at)
    if end is None:
        raise ValueError("上传日期缺失，无法确定核查区间")
    year, month = divmod(end.year * 12 + end.month - 1 - 2, 12)
    start = date(year, month + 1, min(end.day, calendar.monthrange(year, month + 1)[1]))
    result = {"start_date": start.isoformat(), "end_date": end.isoformat(), "checks": {}}
    reviews = reviews or {}
    for kind, definition in CHECKS.items():
        items, missing, invalid, excluded = [], 0, 0, 0
        candidates = {}
        for row in rows:
            try:
                milestone = parse_date(row.get(definition["field"]))
            except (ValueError, OverflowError):
                invalid += 1
                milestone = None
            if milestone is None:
                if not text(row.get(definition["field"])) or text(row.get(definition["field"])).lower() in {"nan", "nat", "none", "null"}:
                    missing += 1
            in_window = milestone is not None and start <= milestone <= end
            excluded_type = kind == "safety" and text(row.get("项目类型")) in EXCLUDED_SAFETY_TYPES
            if in_window and excluded_type:
                excluded += 1
            code = text(row.get("工程编码"))
            if not code and in_window and not excluded_type:
                raise ValueError("核查范围内存在工程编码缺失的项目，请补充后重新上传")
            if not (in_window and not excluded_type) and (kind, code) not in reviews:
                continue
            if code in candidates:
                raise ValueError(f"核查范围内工程编码 {code} 重复，请核对上传明细")
            candidates[code] = (row, in_window and not excluded_type, excluded_type)
        for review_kind, code in reviews:
            if review_kind == kind and code not in candidates:
                candidates[code] = (None, False, False)
        for code, (row, in_window, excluded_type) in candidates.items():
            review = reviews.get((kind, code), {})
            source = project_snapshot(kind, row) if row is not None else review.get("source_item")
            if not source:
                source = project_snapshot(kind, {"工程编码": code, "工程名称": "工程资料待补充"})
            changes = changed_basis(kind, source, review, uploaded_at) if row is not None and not excluded_type and review else []
            previous_status = review.get("status", "待核实")
            needs_recheck = bool(changes) or bool(review.get("recheck_required"))
            status = "待核实" if previous_status == "已核实正常" and needs_recheck else previous_status
            follow_up = status == "发现问题" or bool(review.get("follow_up")) or needs_recheck
            if not in_window and status != "已核实正常" and not follow_up:
                continue
            tracking = []
            if changes:
                tracking.extend(changes)
            elif review.get("recheck_required"):
                tracking.append(review.get("recheck_reason") or "关键资料变化后尚未完成复核")
            if not in_window and status != "已核实正常":
                tracking.append("持续跟踪，处理完成后移出待处理清单")
            if row is None:
                tracking.append("本次报表未包含该工程，展示上次核实资料")
            elif not in_window and status == "已核实正常":
                tracking.append("已核实记录，当前不在新项目筛选范围内")
            items.append({
                **source, "status": status,
                "reviewed_on": "" if status != previous_status else review.get("reviewed_on", ""),
                "note": review.get("note", ""),
                "in_window": in_window, "source_missing": row is None,
                "follow_up": follow_up and status != "已核实正常",
                "needs_recheck": needs_recheck and status != "已核实正常",
                "carried_forward": not in_window and status != "已核实正常",
                "tracking_note": "；".join(tracking),
                "previous_status": previous_status if status != previous_status else review.get("previous_status", ""),
                "previous_reviewed_on": review.get("reviewed_on", "") if status != previous_status else review.get("previous_reviewed_on", ""),
            })
        items.sort(key=lambda item: ({"发现问题": 0, "待核实": 1, "已核实正常": 2}.get(item["status"], 1),
                                     item["key_date"], item["manager"], item["code"]))
        result["checks"][kind] = {
            **definition, "items": items, "total": len(items),
            "actionable": sum(item["status"] != "已核实正常" for item in items),
            "window_total": sum(item["in_window"] for item in items),
            "pending": sum(item["status"] == "待核实" for item in items),
            "normal": sum(item["status"] == "已核实正常" for item in items),
            "issues": sum(item["status"] == "发现问题" for item in items),
            "recheck": sum(item["needs_recheck"] for item in items),
            "carried_forward": sum(item["carried_forward"] for item in items),
            "missing_dates": missing, "invalid_dates": invalid, "excluded": excluded,
        }
    return result
