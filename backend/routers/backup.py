# -*- coding: utf-8 -*-
"""数据备份 / 恢复 API。"""
from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse, Response

from services.backup import create_backup_zip, get_backup_status, restore_backup_zip

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/status")
async def backup_status():
    """查看当前可备份资源概况。"""
    try:
        status = get_backup_status()
        return {"success": True, "data": status}
    except Exception:
        logger.exception("读取备份状态失败")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "读取备份状态失败：RuntimeError"},
        )


@router.get("/export")
async def export_backup():
    """导出完整备份 zip（analysis.db + uploads/archive）。"""
    try:
        content, filename, manifest = create_backup_zip()
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Backup-Created-At": manifest.get("created_at", ""),
        }
        return Response(
            content=content,
            media_type="application/zip",
            headers=headers,
        )
    except FileNotFoundError as e:
        return JSONResponse(status_code=404, content={"success": False, "message": str(e)})
    except Exception:
        logger.exception("导出备份失败")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "导出备份失败：RuntimeError"},
        )


@router.post("/restore")
async def restore_backup(file: UploadFile = File(...)):
    """
    从备份 zip 恢复。

    警告：会覆盖当前 analysis.db 与 uploads/archive。
    前端应二次确认后再调用。
    """
    name = (file.filename or "").lower()
    if not name.endswith(".zip"):
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "仅支持 .zip 备份文件"},
        )
    try:
        content = await file.read()
        if len(content) > 500 * 1024 * 1024:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "备份文件不能超过 500MB"},
            )
        result = restore_backup_zip(content)
        result["restored_at"] = datetime.now().isoformat(timespec="seconds")
        return result
    except ValueError as e:
        return JSONResponse(status_code=400, content={"success": False, "message": str(e)})
    except Exception:
        logger.exception("恢复备份失败")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "恢复备份失败：RuntimeError"},
        )
