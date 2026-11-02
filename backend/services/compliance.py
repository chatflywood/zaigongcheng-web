"""Date-window project lists for human compliance verification."""
import calendar
import math
from datetime import date, datetime, timedelta

CHECKS = {
    "safety": {"label": "安全生产费核实", "field": "工程开工日期"},
    "quality": {"label": "质检申报核实", "field": "设计批复日期(初次)"},
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


def build_compliance(rows, uploaded_at, reviews=None):
    """Use the actual upload date, inclusive calendar-month boundaries, and raw fields."""
    end = parse_date(uploaded_at)
    if end is None:
        raise ValueError("上传日期缺失，无法确定核查区间")
    year, month = divmod(end.year * 12 + end.month - 1 - 2, 12)
    start = date(year, month + 1, min(end.day, calendar.monthrange(year, month + 1)[1]))
    result = {"start_date": start.isoformat(), "end_date": end.isoformat(), "checks": {}}
    reviews = reviews or {}
    for kind, definition in CHECKS.items():
        items, missing, invalid, excluded = [], 0, 0, 0
        seen = set()
        for row in rows:
            try:
                milestone = parse_date(row.get(definition["field"]))
            except (ValueError, OverflowError):
                invalid += 1
                continue
            if milestone is None:
                missing += 1
                continue
            if not start <= milestone <= end:
                continue
            if kind == "safety" and text(row.get("项目类型")) in EXCLUDED_SAFETY_TYPES:
                excluded += 1
                continue
            code = text(row.get("工程编码"))
            if not code:
                raise ValueError("核查范围内存在工程编码缺失的项目，请补充后重新上传")
            if code in seen:
                raise ValueError(f"核查范围内工程编码 {code} 重复，请核对上传明细")
            seen.add(code)
            review = reviews.get((kind, code), {})
            items.append({
                "code": code, "name": text(row.get("工程名称")),
                "manager": text(row.get("工程管理员")) or "未分配",
                "project_type": text(row.get("项目类型")),
                "project_status": text(row.get("工程状态")),
                "construction_unit": text(row.get("施工单位")),
                "key_date": milestone.isoformat(),
                "current_safety_fee": number(row.get("安全生产费")),
                "total_safety_fee": number(row.get("累计待摊-安全生产费")),
                "status": review.get("status", "待核实"),
                "reviewed_on": review.get("reviewed_on", ""),
                "note": review.get("note", ""),
            })
        items.sort(key=lambda item: (item["key_date"], item["manager"], item["code"]))
        result["checks"][kind] = {
            **definition, "items": items, "total": len(items),
            "pending": sum(item["status"] == "待核实" for item in items),
            "normal": sum(item["status"] == "已核实正常" for item in items),
            "issues": sum(item["status"] == "发现问题" for item in items),
            "missing_dates": missing, "invalid_dates": invalid, "excluded": excluded,
        }
    return result
