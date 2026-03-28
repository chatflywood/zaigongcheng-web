from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import JSONResponse
import pandas as pd
from io import BytesIO
import math
import json
from datetime import datetime
from services.analysis import analyze
from models import ZaigongRecord, get_db

router = APIRouter()

# 全年资本性支出目标（单位：万元）
YEARLY_TARGET = 503.0


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


def build_dashboard_snapshot(record: ZaigongRecord) -> dict:
    """将数据库记录恢复为前端可直接使用的快照结构。"""
    raw_summary = json.loads(record.summary_data) if record.summary_data else []
    raw_metrics = json.loads(record.metrics_data) if record.metrics_data else {}
    detail_data = json.loads(record.detail_data) if record.detail_data else []

    detail_rows = [
        row for row in raw_summary
        if (row.get("工程管理员") or row.get("manager")) != "合计"
    ]
    pending_pressure = sum(1 for row in detail_rows if float(row.get("已下单待收货", 0) or row.get("pending", 0) or 0) > 30)
    total_rate = float(raw_metrics.get("total_rate", 0) or 0)
    deficit = float(raw_metrics.get("deficit", 0) or 0)

    return {
        "id": record.id,
        "uploaded_at": record.uploaded_at.isoformat(),
        "source_filename": record.source_filename,
        "file_date": record.file_date,
        "target_value": record.target_value,
        "dashboard": {
            "metrics": {
                "capital": raw_metrics.get("total_current", 0),
                "pending": raw_metrics.get("total_pending", 0),
                "monthSpend": raw_metrics.get("total_today_month", 0),
                "transfer": raw_metrics.get("total_transfer", 0),
                "rate": total_rate,
                "progress": raw_metrics.get("progress_ratio", 0),
                "deficit": deficit,
                "yearTarget": raw_metrics.get("year_target", record.target_value),
            },
            "summary": detail_rows,
            "detail": detail_data,
            "alerts": [
                {
                    "title": "待收货压力",
                    "value": f"{pending_pressure} 位管理员超过30万元",
                },
                {
                    "title": "转固率状态",
                    "value": "偏低" if total_rate < 0.6 else "正常",
                },
                {
                    "title": "目标差额",
                    "value": f"{deficit:.2f} 万元" if deficit > 0 else "已达成目标",
                },
            ],
        },
        "summary": raw_summary,
        "metrics": raw_metrics,
    }


@router.post("/upload")
async def upload_excel(file: UploadFile = File(...), target: float = Query(503.0)):
    """
    上传 Excel 文件，返回分析结果，并保存到数据库
    """
    try:
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))

        # 执行分析
        result = analyze(df, year_target=target)

        # 清理 NaN 值
        cleaned_data = clean_nan(result["data"])

        # 从文件名提取日期（如 "在建工程明细总表(实时)(20260320).xlsx" -> "20260320"）
        import re
        # 匹配括号内的日期，如 (20260320) 或 (0320)
        date_match = re.search(r'\((\d{4,8})\)', file.filename)
        file_date = date_match.group(1) if date_match else None

        # 保存到数据库
        db = get_db()
        try:
            # 检查是否已存在相同文件名的记录，存在则删除
            existing = db.query(ZaigongRecord).filter(
                ZaigongRecord.source_filename == file.filename
            ).first()
            if existing:
                db.delete(existing)

            record = ZaigongRecord(
                uploaded_at=datetime.now(),
                source_filename=file.filename,
                file_date=file_date,
                summary_data=json.dumps(cleaned_data.get("summary", []), ensure_ascii=False),
                metrics_data=json.dumps(cleaned_data.get("metrics", {}), ensure_ascii=False),
                detail_data=json.dumps(cleaned_data.get("dashboard", {}).get("detail", []), ensure_ascii=False),
                target_value=target
            )
            db.add(record)
            db.commit()
        finally:
            db.close()

        return {
            "success": True,
            "message": "分析完成",
            "filename": file.filename,
            "rows": len(df),
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


@router.get("/history")
async def get_history(limit: int = Query(10, ge=1, le=100)):
    """
    获取历史记录列表（按实际上传时间降序）
    """
    db = get_db()
    try:
        records = db.query(ZaigongRecord).order_by(
            ZaigongRecord.uploaded_at.desc()
        ).limit(limit).all()

        return {
            "success": True,
            "data": [
                {
                    "id": r.id,
                    "uploaded_at": r.uploaded_at.isoformat(),
                    "source_filename": r.source_filename,
                    "file_date": r.file_date,
                    "target_value": r.target_value
                }
                for r in records
            ]
        }
    finally:
        db.close()


@router.get("/history/{record_id}")
async def get_history_snapshot(record_id: int):
    """
    获取指定历史记录的完整快照，并附带该记录上一版数据用于对比。
    """
    db = get_db()
    try:
        all_records = db.query(ZaigongRecord).order_by(
            ZaigongRecord.uploaded_at.desc()
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

        current_record = all_records[current_index]
        previous_record = all_records[current_index + 1] if current_index + 1 < len(all_records) else None

        return {
            "success": True,
            "data": {
                "current": build_dashboard_snapshot(current_record),
                "previous": build_dashboard_snapshot(previous_record) if previous_record else None
            }
        }
    finally:
        db.close()


@router.get("/compare")
async def compare_with_previous():
    """
    获取最近一次数据，用于对比
    - latest: 数据库中最近一次上传的记录
    - previous: 数据库中倒数第二次上传的记录（按实际上传时间 uploaded_at 排序）
    """
    db = get_db()
    try:
        # 按实际上传时间降序排序，获取所有记录
        all_records = db.query(ZaigongRecord).order_by(
            ZaigongRecord.uploaded_at.desc()
        ).all()

        if not all_records:
            return {"success": True, "data": None}

        # 获取最新的记录（最近一次上传）
        latest = all_records[0]

        # 获取上一条记录（按实际上传时间，排除同一条记录）
        previous = all_records[1] if len(all_records) > 1 else None

        result = {
            "latest": {
                "id": latest.id,
                "uploaded_at": latest.uploaded_at.isoformat(),
                "source_filename": latest.source_filename,
                "file_date": latest.file_date,
                "summary": json.loads(latest.summary_data) if latest.summary_data else [],
                "metrics": json.loads(latest.metrics_data) if latest.metrics_data else {},
                "target_value": latest.target_value
            },
            "previous": None
        }

        if previous:
            result["previous"] = {
                "id": previous.id,
                "uploaded_at": previous.uploaded_at.isoformat(),
                "source_filename": previous.source_filename,
                "file_date": previous.file_date,
                "summary": json.loads(previous.summary_data) if previous.summary_data else [],
                "metrics": json.loads(previous.metrics_data) if previous.metrics_data else {},
                "target_value": previous.target_value
            }

        return {"success": True, "data": result}
    finally:
        db.close()


@router.get("/manager-details")
async def get_manager_details(record_id: int = Query(...), manager: str = Query(...)):
    """
    获取指定记录中某工程管理员的明细数据
    """
    db = get_db()
    try:
        record = db.query(ZaigongRecord).filter(ZaigongRecord.id == record_id).first()
        if not record:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "记录不存在"}
            )

        detail_data = json.loads(record.detail_data) if record.detail_data else []
        # 筛选指定管理员的明细
        filtered = [d for d in detail_data if d.get("工程管理员") == manager]

        return {
            "success": True,
            "data": {
                "manager": manager,
                "details": filtered
            }
        }
    finally:
        db.close()


@router.get("/metrics")
async def get_metrics():
    """
    获取核心指标
    """
    return {
        "success": True,
        "data": {
            "year_target": YEARLY_TARGET,
        }
    }
