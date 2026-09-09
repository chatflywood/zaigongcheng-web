"""Business dates and immutable snapshot provenance, stored in existing JSON fields.

No database migration is required. Legacy records are read without rewriting them.
"""
import json
import re
from datetime import date, datetime

CALCULATION_VERSION = "1.37.0"


def filename_date(filename):
    matches = re.findall(r"(?<!\d)(20\d{2})[-_年]?(\d{2})[-_月]?(\d{2})(?!\d)", filename or "")
    for parts in matches:
        try:
            return date(*map(int, parts)).isoformat()
        except ValueError:
            continue
    return None


def new_period(filename, business_date=None):
    if business_date:
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", business_date):
                raise ValueError()
            value = date.fromisoformat(business_date).isoformat()
        except ValueError:
            raise ValueError("数据日期必须为有效的 YYYY-MM-DD 日期")
        source = "user"
    else:
        value = filename_date(filename)
        source = "filename" if value else "unknown"
    return {"business_date": value, "date_source": source,
            "calculation_version": CALCULATION_VERSION}


def period_of(record):
    if record is None:
        return {"business_date": None, "date_source": "unknown"}
    payload = json.loads((getattr(record, "metrics_data", None) or
                          getattr(record, "budget_data", None)) or "{}")
    if payload.get("period"):
        return dict(payload["period"])
    legacy_date = filename_date(record.source_filename) or filename_date(getattr(record, "file_date", None))
    return {"business_date": legacy_date,
            "date_source": "legacy_filename" if legacy_date else "unknown",
            "calculation_version": "legacy"}


def ordered_records(db, model):
    records = db.query(model).all()
    # Confirmed dates always take precedence over undated legacy uploads.
    return sorted(records, key=lambda r: (
        period_of(r).get("business_date") or "",
        r.uploaded_at or datetime.min, r.id or 0), reverse=True)


def select_source(db, model, business_date=None):
    records = ordered_records(db, model)
    if business_date:
        # Never mix fiscal years or use future observations for a past period.
        return next((r for r in records if (period_of(r).get("business_date") or "")[:4] == business_date[:4]
                     and period_of(r)["business_date"] <= business_date), None)
    return records[0] if records else None


def linkage(period, source):
    source_date = period_of(source).get("business_date")
    own_date = period.get("business_date")
    warnings = []
    if not own_date:
        warnings.append("预算数据日期未确认；请指定数据日期后重新上传")
    if source is None:
        warnings.append("无同年度且不晚于预算日期的工程数据，年度支出暂不可用")
    elif not source_date:
        warnings.append("工程数据日期未确认，无法核对数据期间")
    elif own_date and own_date != source_date:
        warnings.append(f"数据日期不一致：预算 {own_date}，工程 {source_date}")
    return {"zaigong_record_id": source.id if source else None,
            "zaigong_business_date": source_date, "warnings": warnings,
            "spend_available": source is not None}
