# -*- coding: utf-8 -*-
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from models import ArchiveRecord, get_db
from datetime import datetime
import os
import uuid

router = APIRouter()

ARCHIVE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "archive")
os.makedirs(ARCHIVE_DIR, exist_ok=True)

ALLOWED_CATEGORIES = {"年度建设情况", "多年趋势汇总", "投资预算报告"}
ALLOWED_EXTS = {".xlsx", ".xls", ".docx", ".pdf"}


@router.post("/upload")
async def upload_archive(
    file: UploadFile = File(...),
    category: str = Form(...),
    year: str = Form(...),
    note: str = Form(""),
):
    if category not in ALLOWED_CATEGORIES:
        raise HTTPException(400, f"无效分类: {category}")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(400, f"不支持的文件格式: {ext}")

    stored_name = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(ARCHIVE_DIR, stored_name)

    content = await file.read()
    with open(dest, "wb") as f:
        f.write(content)

    db = get_db()
    try:
        record = ArchiveRecord(
            category=category,
            year=year,
            original_filename=file.filename,
            stored_filename=stored_name,
            file_size=len(content),
            note=note,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return {
            "success": True,
            "id": record.id,
            "category": record.category,
            "year": record.year,
            "original_filename": record.original_filename,
            "uploaded_at": record.uploaded_at.isoformat(),
            "file_size": record.file_size,
        }
    finally:
        db.close()


@router.get("/list")
def list_archives():
    db = get_db()
    try:
        records = db.query(ArchiveRecord).order_by(ArchiveRecord.uploaded_at.desc()).all()
        return [
            {
                "id": r.id,
                "category": r.category,
                "year": r.year,
                "original_filename": r.original_filename,
                "file_size": r.file_size,
                "note": r.note,
                "uploaded_at": r.uploaded_at.isoformat(),
                "ext": os.path.splitext(r.original_filename or "")[1].lower(),
            }
            for r in records
        ]
    finally:
        db.close()


@router.get("/file/{record_id}")
def download_archive(record_id: int):
    db = get_db()
    try:
        record = db.query(ArchiveRecord).filter(ArchiveRecord.id == record_id).first()
        if not record:
            raise HTTPException(404, "档案不存在")
        path = os.path.join(ARCHIVE_DIR, record.stored_filename)
        if not os.path.exists(path):
            raise HTTPException(404, "文件不存在")
        return FileResponse(
            path,
            filename=record.original_filename,
            media_type="application/octet-stream",
        )
    finally:
        db.close()


@router.post("/delete/{record_id}")
def delete_archive(record_id: int):
    db = get_db()
    try:
        record = db.query(ArchiveRecord).filter(ArchiveRecord.id == record_id).first()
        if not record:
            raise HTTPException(404, "档案不存在")
        path = os.path.join(ARCHIVE_DIR, record.stored_filename)
        if os.path.exists(path):
            os.remove(path)
        db.delete(record)
        db.commit()
        return {"success": True}
    finally:
        db.close()
