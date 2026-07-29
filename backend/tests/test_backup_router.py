# -*- coding: utf-8 -*-
"""备份 / 恢复路由与 service 测试。"""
from __future__ import annotations

import io
import json
import os
import sys
import zipfile
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).parent.parent))

import routers.backup as backup_mod  # noqa: E402
import services.backup as backup_svc  # noqa: E402
from models import Base, BudgetRecord, ZaigongRecord  # noqa: E402


@pytest.fixture
def tmp_data_env(tmp_path, monkeypatch):
    """把 DB_PATH / ARCHIVE_DIR 指到临时目录，避免动真实库。"""
    data_dir = tmp_path / "data"
    archive_dir = tmp_path / "uploads" / "archive"
    data_dir.mkdir(parents=True)
    archive_dir.mkdir(parents=True)
    db_path = data_dir / "analysis.db"

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    db = Session()
    db.add(
        ZaigongRecord(
            source_filename="golden.xlsx",
            file_date="20260615",
            summary_data="[]",
            metrics_data=json.dumps({"total_current": 150}),
            detail_data="[]",
            four_class_warnings="{}",
            raw_data="[]",
            target_value=500,
        )
    )
    db.add(
        BudgetRecord(
            source_filename="budget.xlsx",
            budget_data=json.dumps({"budget_total": 300}),
        )
    )
    db.commit()
    db.close()

    # 档案样例文件
    sample = archive_dir / "doc1.pdf"
    sample.write_bytes(b"%PDF-1.4 golden-archive")

    monkeypatch.setattr(backup_svc, "DB_PATH", str(db_path))
    monkeypatch.setattr(backup_svc, "DATA_DIR", str(data_dir))
    monkeypatch.setattr(backup_svc, "ARCHIVE_DIR", str(archive_dir))
    monkeypatch.setattr(backup_svc, "UPLOADS_DIR", str(tmp_path / "uploads"))

    yield {
        "db_path": str(db_path),
        "archive_dir": str(archive_dir),
        "engine": engine,
        "Session": Session,
        "tmp_path": tmp_path,
    }
    engine.dispose()


def build_client():
    app = FastAPI()
    app.include_router(backup_mod.router, prefix="/api/backup")
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


class TestBackupService:
    def test_status_and_create_zip(self, tmp_data_env):
        status = backup_svc.get_backup_status()
        assert status["db_exists"] is True
        assert status["archive_count"] == 1
        assert status["db_size"] > 0

        content, filename, manifest = backup_svc.create_backup_zip()
        assert filename.startswith("zaigongcheng_backup_")
        assert filename.endswith(".zip")
        assert manifest["format"] == "zaigongcheng-backup"
        assert manifest["archive_count"] == 1

        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            names = set(zf.namelist())
            assert "backup_manifest.json" in names
            assert "data/analysis.db" in names
            assert "uploads/archive/doc1.pdf" in names

    def test_restore_roundtrip(self, tmp_data_env):
        content, _, _ = backup_svc.create_backup_zip()

        # 破坏当前数据
        Path(tmp_data_env["db_path"]).write_bytes(b"broken")
        arch = Path(tmp_data_env["archive_dir"]) / "doc1.pdf"
        arch.write_bytes(b"changed")
        (Path(tmp_data_env["archive_dir"]) / "extra.bin").write_bytes(b"x")

        result = backup_svc.restore_backup_zip(content)
        assert result["success"] is True
        assert result["restored_archive_count"] == 1

        # DB 可查
        engine = create_engine(f"sqlite:///{tmp_data_env['db_path']}")
        with engine.connect() as conn:
            n = conn.execute(text("select count(*) from zaigong_records")).scalar()
            assert n == 1
            n2 = conn.execute(text("select count(*) from budget_records")).scalar()
            assert n2 == 1
        engine.dispose()

        assert (Path(tmp_data_env["archive_dir"]) / "doc1.pdf").read_bytes() == b"%PDF-1.4 golden-archive"
        assert not (Path(tmp_data_env["archive_dir"]) / "extra.bin").exists()

    def test_restore_rejects_bad_zip(self, tmp_data_env):
        with pytest.raises(ValueError, match="有效的 zip"):
            backup_svc.restore_backup_zip(b"not-a-zip")

    def test_restore_rejects_missing_manifest(self, tmp_data_env):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("data/analysis.db", b"sqlite")
        with pytest.raises(ValueError, match="manifest"):
            backup_svc.restore_backup_zip(buf.getvalue())


@pytest.mark.asyncio
class TestBackupRouter:
    async def test_status_export_restore(self, tmp_data_env):
        async with build_client() as client:
            r = await client.get("/api/backup/status")
            assert r.status_code == 200
            body = r.json()
            assert body["success"] is True
            assert body["data"]["db_exists"] is True
            assert body["data"]["archive_count"] == 1

            r = await client.get("/api/backup/export")
            assert r.status_code == 200
            assert r.headers["content-type"].startswith("application/zip")
            zip_bytes = r.content
            assert len(zip_bytes) > 100

            # 破坏后恢复
            Path(tmp_data_env["db_path"]).write_bytes(b"x")
            files = {"file": ("backup.zip", zip_bytes, "application/zip")}
            r = await client.post("/api/backup/restore", files=files)
            assert r.status_code == 200
            body = r.json()
            assert body["success"] is True
            assert body["restored_archive_count"] == 1

    async def test_restore_non_zip_400(self, tmp_data_env):
        async with build_client() as client:
            files = {"file": ("x.txt", b"hello", "text/plain")}
            r = await client.post("/api/backup/restore", files=files)
            assert r.status_code == 400
            assert "zip" in r.json()["message"].lower()
