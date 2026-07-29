# -*- coding: utf-8 -*-
"""
数据备份 / 恢复。

打包内容：
- analysis.db（SQLite 全库：在建/预算/批次/档案元数据/配置）
- uploads/archive/*（档案原文件）

快照语义：备份是磁盘级拷贝，恢复会覆盖当前库与档案目录。
"""
from __future__ import annotations

import io
import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from typing import Any, Dict, Tuple

from models import DB_PATH

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS_DIR = os.path.join(BACKEND_ROOT, "uploads")
ARCHIVE_DIR = os.path.join(UPLOADS_DIR, "archive")
DATA_DIR = os.path.dirname(DB_PATH)

MANIFEST_NAME = "backup_manifest.json"
BACKUP_FORMAT = "zaigongcheng-backup"
BACKUP_VERSION = 1


def _file_size(path: str) -> int:
    try:
        return os.path.getsize(path) if os.path.isfile(path) else 0
    except OSError:
        return 0


def get_backup_status() -> Dict[str, Any]:
    """返回当前可备份资源概况。"""
    archive_files = []
    if os.path.isdir(ARCHIVE_DIR):
        for name in sorted(os.listdir(ARCHIVE_DIR)):
            path = os.path.join(ARCHIVE_DIR, name)
            if os.path.isfile(path) and not name.startswith("."):
                archive_files.append({"name": name, "size": os.path.getsize(path)})

    db_exists = os.path.isfile(DB_PATH)
    return {
        "db_path": DB_PATH,
        "db_exists": db_exists,
        "db_size": _file_size(DB_PATH) if db_exists else 0,
        "archive_dir": ARCHIVE_DIR,
        "archive_count": len(archive_files),
        "archive_total_size": sum(f["size"] for f in archive_files),
        "archive_files": archive_files,
    }


def create_backup_zip() -> Tuple[bytes, str, Dict[str, Any]]:
    """生成备份 zip 字节流，返回 (bytes, filename, manifest)。"""
    status = get_backup_status()
    if not status["db_exists"]:
        raise FileNotFoundError("数据库文件不存在，无法备份")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"zaigongcheng_backup_{stamp}.zip"
    manifest = {
        "format": BACKUP_FORMAT,
        "version": BACKUP_VERSION,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "db_size": status["db_size"],
        "archive_count": status["archive_count"],
        "archive_files": [f["name"] for f in status["archive_files"]],
        "note": "恢复将覆盖当前 analysis.db 与 uploads/archive",
    }

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(MANIFEST_NAME, json.dumps(manifest, ensure_ascii=False, indent=2))
        zf.write(DB_PATH, arcname="data/analysis.db")
        for item in status["archive_files"]:
            src = os.path.join(ARCHIVE_DIR, item["name"])
            zf.write(src, arcname=f"uploads/archive/{item['name']}")

    return buf.getvalue(), filename, manifest


def _safe_extract_member(zf: zipfile.ZipFile, member: str, dest_dir: str) -> str:
    """防 zip-slip：只允许解压到 dest_dir 内。"""
    target = os.path.realpath(os.path.join(dest_dir, member))
    dest_real = os.path.realpath(dest_dir)
    if not target.startswith(dest_real + os.sep) and target != dest_real:
        raise ValueError(f"非法备份路径: {member}")
    parent = os.path.dirname(target)
    os.makedirs(parent, exist_ok=True)
    with zf.open(member) as src, open(target, "wb") as dst:
        shutil.copyfileobj(src, dst)
    return target


def restore_backup_zip(content: bytes) -> Dict[str, Any]:
    """从备份 zip 恢复。覆盖当前 DB 与 archive 目录。"""
    if not content:
        raise ValueError("备份文件为空")

    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as e:
        raise ValueError("不是有效的 zip 备份文件") from e

    with zf:
        names = set(zf.namelist())
        if MANIFEST_NAME not in names:
            raise ValueError("缺少 backup_manifest.json，不是本系统备份包")
        if "data/analysis.db" not in names:
            raise ValueError("备份包缺少 data/analysis.db")

        try:
            manifest = json.loads(zf.read(MANIFEST_NAME).decode("utf-8"))
        except Exception as e:
            raise ValueError("backup_manifest.json 无法解析") from e

        if manifest.get("format") != BACKUP_FORMAT:
            raise ValueError(f"备份格式不匹配: {manifest.get('format')}")

        # 解到临时目录，成功后再原子替换
        with tempfile.TemporaryDirectory(prefix="zaigong_restore_") as tmp:
            db_tmp = _safe_extract_member(zf, "data/analysis.db", tmp)
            archive_tmp_dir = os.path.join(tmp, "uploads", "archive")
            os.makedirs(archive_tmp_dir, exist_ok=True)
            restored_archives = []
            for name in names:
                if name.startswith("uploads/archive/") and not name.endswith("/"):
                    base = os.path.basename(name)
                    if not base or base.startswith("."):
                        continue
                    _safe_extract_member(zf, name, tmp)
                    restored_archives.append(base)

            # 替换 DB
            os.makedirs(DATA_DIR, exist_ok=True)
            db_backup_old = DB_PATH + ".pre_restore"
            if os.path.isfile(DB_PATH):
                shutil.copy2(DB_PATH, db_backup_old)
            shutil.copy2(db_tmp, DB_PATH)

            # 替换 archive：先清空再拷入
            os.makedirs(ARCHIVE_DIR, exist_ok=True)
            for existing in os.listdir(ARCHIVE_DIR):
                path = os.path.join(ARCHIVE_DIR, existing)
                if os.path.isfile(path):
                    os.remove(path)
            for base in restored_archives:
                src = os.path.join(archive_tmp_dir, base)
                if os.path.isfile(src):
                    shutil.copy2(src, os.path.join(ARCHIVE_DIR, base))

            # 清理临时 .pre_restore（保留一份也可，但避免堆积：仅保留最新）
            # 若恢复后想回滚，用户应先自己做导出；这里删掉中间文件以免混淆
            if os.path.isfile(db_backup_old):
                try:
                    os.remove(db_backup_old)
                except OSError:
                    pass

        return {
            "success": True,
            "message": "恢复完成",
            "manifest": manifest,
            "restored_archive_count": len(restored_archives),
            "db_size": _file_size(DB_PATH),
        }
