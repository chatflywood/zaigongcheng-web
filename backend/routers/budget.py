from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
import pandas as pd
from io import BytesIO
import math
import re
import json
from pathlib import Path
from services.budget import analyze_budget
from models import ZaigongRecord, BudgetRecord, SessionLocal

router = APIRouter()


def clean_nan(obj):
    """清理数据中的 NaN 和 Infinity 值"""
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    return obj


def load_budget_sheets(contents: bytes):
    """读取预算汇总和项目明细，兼容年份变化的 sheet 名。"""
    workbook = pd.ExcelFile(BytesIO(contents))
    df_summary = pd.read_excel(workbook, sheet_name="预算下达及立项进度")

    project_sheet_name = next(
        (
            name for name in workbook.sheet_names
            if re.search(r"新建项目明细$", str(name))
        ),
        None,
    )
    df_projects = pd.read_excel(workbook, sheet_name=project_sheet_name) if project_sheet_name else None

    return df_summary, df_projects


def build_zaigong_spend_summary_from_record(record):
    """从最近一次在建工程记录或源文件构建一级专业年度支出汇总。"""
    detail_data = json.loads(record.detail_data) if record and record.detail_data else []
    if detail_data and any("一级专业" in item for item in detail_data):
        summary = {}
        for item in detail_data:
            category = str(item.get("一级专业") or "").strip()
            if not category:
                continue
            summary[category] = summary.get(category, 0) + float(item.get("本年累计资本性支出") or 0)
        return {key: round(value / 10000, 2) for key, value in summary.items()}

    if not record or not record.source_filename:
        return {}

    downloads_dir = Path.home() / "Downloads"
    import re as _re

    def _valid_xlsx(p):
        return p.suffix.lower() == ".xlsx" and not p.name.startswith(".")

    # 先精确匹配，失败则按文件名关键词模糊匹配（兼容日期略有不同的情况）
    matches = [p for p in downloads_dir.rglob(record.source_filename) if _valid_xlsx(p)]
    if not matches:
        base = _re.sub(r'\(\d+\)', '', Path(record.source_filename).stem).strip()
        matches = sorted(
            [p for p in downloads_dir.rglob("*.xlsx") if _valid_xlsx(p) and base in p.stem],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    if not matches:
        return {}

    try:
        df = pd.read_excel(matches[0])
    except Exception:
        return {}

    required_columns = {"一级专业", "本年累计资本性支出"}
    if not required_columns.issubset(set(df.columns)):
        return {}

    grouped = (
        df.assign(
            一级专业=df["一级专业"].fillna("").astype(str).str.strip(),
            本年累计资本性支出=pd.to_numeric(df["本年累计资本性支出"], errors="coerce").fillna(0),
        )
        .groupby("一级专业", dropna=False)["本年累计资本性支出"]
        .sum()
    )

    return {
        str(key): round(float(value) / 10000, 2)
        for key, value in grouped.items()
        if str(key).strip()
    }


def get_latest_zaigong_spend_summary():
    """获取最近一次在建工程上传数据的一级专业年度支出汇总。"""
    db = SessionLocal()
    try:
        latest = db.query(ZaigongRecord).order_by(ZaigongRecord.uploaded_at.desc()).first()
        if not latest:
            return {}
        return build_zaigong_spend_summary_from_record(latest)
    finally:
        db.close()


def build_budget_snapshot(record: BudgetRecord) -> dict:
    """恢复预算历史快照。"""
    return {
        "id": record.id,
        "uploaded_at": record.uploaded_at.isoformat(),
        "source_filename": record.source_filename,
        "data": json.loads(record.budget_data) if record.budget_data else {},
    }


@router.post("/upload")
async def upload_budget(file: UploadFile = File(...)):
    """
    上传预算 Excel 文件，返回分析结果
    """
    try:
        contents = await file.read()
        df_summary, df_projects = load_budget_sheets(contents)
        spend_summary = get_latest_zaigong_spend_summary()

        result = analyze_budget(df_summary, df_projects, spend_summary)

        # 清理 NaN 值
        cleaned_data = clean_nan(result)

        db = SessionLocal()
        try:
            existing = db.query(BudgetRecord).filter(
                BudgetRecord.source_filename == file.filename
            ).first()
            if existing:
                db.delete(existing)

            record = BudgetRecord(
                source_filename=file.filename,
                budget_data=json.dumps(cleaned_data, ensure_ascii=False),
            )
            db.add(record)
            db.commit()
        finally:
            db.close()

        return {
            "success": True,
            "message": "分析完成",
            "filename": file.filename,
            "data": cleaned_data
        }
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )


@router.post("/refresh-spend")
async def refresh_budget_spend():
    """
    用最新在建工程数据重新计算预算的全年支出，无需重新上传预算文件。
    在建工程数据更新后自动调用此接口同步 Budget / KeyIndicators 页面数据。
    """
    db = SessionLocal()
    try:
        record = db.query(BudgetRecord).order_by(BudgetRecord.uploaded_at.desc()).first()
        if not record or not record.budget_data:
            return {"success": False, "message": "暂无预算记录，请先上传预算文件"}

        stored = json.loads(record.budget_data)
        spend_summary = get_latest_zaigong_spend_summary()

        # 按专业更新 annual_spend
        categories = stored.get("categories", [])
        for cat in categories:
            cat["annual_spend"] = round(spend_summary.get(cat["name"], 0), 2)
            budget = cat.get("budget") or 0
            cat["spend_progress"] = round(cat["annual_spend"] / budget, 4) if budget > 0 else 0

        annual_spend_total = round(sum(c.get("annual_spend", 0) for c in categories), 2)
        budget_total = stored.get("budget_total") or 0
        stored["annual_spend_total"] = annual_spend_total
        stored["spend_progress"] = round(annual_spend_total / budget_total, 4) if budget_total > 0 else 0
        stored["categories"] = categories

        cleaned = clean_nan(stored)
        record.budget_data = json.dumps(cleaned, ensure_ascii=False)
        db.commit()

        return {"success": True, "data": cleaned}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        db.close()


@router.get("/history")
async def get_budget_history(limit: int = 10):
    """获取预算分析历史记录。"""
    db = SessionLocal()
    try:
        records = db.query(BudgetRecord).order_by(
            BudgetRecord.uploaded_at.desc()
        ).limit(limit).all()

        return {
            "success": True,
            "data": [
                {
                    "id": record.id,
                    "uploaded_at": record.uploaded_at.isoformat(),
                    "source_filename": record.source_filename,
                }
                for record in records
            ]
        }
    finally:
        db.close()


@router.get("/history/{record_id}")
async def get_budget_history_snapshot(record_id: int):
    """获取指定预算历史快照。"""
    db = SessionLocal()
    try:
        all_records = db.query(BudgetRecord).order_by(
            BudgetRecord.uploaded_at.desc()
        ).all()

        if not all_records:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "暂无历史记录"}
            )

        current_index = next((index for index, item in enumerate(all_records) if item.id == record_id), None)
        if current_index is None:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "记录不存在"}
            )

        record = all_records[current_index]
        previous_record = all_records[current_index + 1] if current_index + 1 < len(all_records) else None

        return {
            "success": True,
            "data": {
                "current": build_budget_snapshot(record),
                "previous": build_budget_snapshot(previous_record) if previous_record else None,
            }
        }
    finally:
        db.close()
