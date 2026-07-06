# -*- coding: utf-8 -*-
"""
archive 路由集成测试（上传 / 列表 / 下载 / 删除）。

范式同 test_budget_batch_router：内存 SQLite + httpx.ASGITransport (async)。
上传落盘目录重定向到临时 tmpdir，不污染真实 uploads/archive。
"""
import io
import os
import sys
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Base  # noqa: E402
import routers.archive as archive_mod  # noqa: E402


@pytest.fixture
def test_env(tmp_path):
    """临时 ARCHIVE_DIR + 内存库。"""
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    orig_get_db = archive_mod.get_db
    orig_archive_dir = archive_mod.ARCHIVE_DIR
    archive_mod.get_db = lambda: Session()
    archive_mod.ARCHIVE_DIR = str(tmp_path)
    try:
        yield Session
    finally:
        archive_mod.get_db = orig_get_db
        archive_mod.ARCHIVE_DIR = orig_archive_dir
        Base.metadata.drop_all(engine)
        engine.dispose()


def build_client():
    app = FastAPI()
    app.include_router(archive_mod.router, prefix="/api/archive")
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


def _xlsx_bytes() -> bytes:
    """最小合法 xlsx（一个 sheet + 一行数据）。"""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["header"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class TestArchiveRouter:
    @pytest.mark.asyncio
    async def test_list_empty(self, test_env):
        async with build_client() as c:
            r = await c.get("/api/archive/list")
        assert r.status_code == 200
        assert r.json() == []

    @pytest.mark.asyncio
    async def test_upload_then_list_then_download_then_delete(self, test_env):
        xlsx = _xlsx_bytes()
        async with build_client() as c:
            # 上传
            r = await c.post(
                "/api/archive/upload",
                data={"category": "年度建设情况", "year": "2026", "note": "测试"},
                files={"file": ("demo.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
            assert r.status_code == 200
            created = r.json()
            assert created["original_filename"] == "demo.xlsx"
            assert created["category"] == "年度建设情况"
            assert created["file_size"] == len(xlsx)
            assert isinstance(created["id"], int)

            # 列表
            rows = (await c.get("/api/archive/list")).json()
            assert len(rows) == 1
            assert rows[0]["id"] == created["id"]
            assert rows[0]["ext"] == ".xlsx"

            # 下载
            r = await c.get(f"/api/archive/file/{created['id']}")
            assert r.status_code == 200
            assert r.content == xlsx

            # 删除
            r = await c.post(f"/api/archive/delete/{created['id']}")
            assert r.status_code == 200
            assert r.json()["success"] is True
            # 删后列表空
            assert (await c.get("/api/archive/list")).json() == []

    @pytest.mark.asyncio
    async def test_upload_invalid_category_rejected(self, test_env):
        xlsx = _xlsx_bytes()
        async with build_client() as c:
            r = await c.post(
                "/api/archive/upload",
                data={"category": "非法类别", "year": "2026"},
                files={"file": ("demo.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
            assert r.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_invalid_ext_rejected(self, test_env):
        async with build_client() as c:
            r = await c.post(
                "/api/archive/upload",
                data={"category": "年度建设情况", "year": "2026"},
                files={"file": ("demo.txt", b"hello", "text/plain")},
            )
            assert r.status_code == 400

    @pytest.mark.asyncio
    async def test_download_nonexistent_404(self, test_env):
        async with build_client() as c:
            r = await c.get("/api/archive/file/9999")
            assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_404(self, test_env):
        async with build_client() as c:
            r = await c.post("/api/archive/delete/9999")
            assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_upload_pdf_allowed(self, test_env):
        """pdf 在白名单内，允许上传但前端预览未实现（独立校验上传部分）。"""
        async with build_client() as c:
            r = await c.post(
                "/api/archive/upload",
                data={"category": "投资预算报告", "year": "2026"},
                files={"file": ("report.pdf", b"%PDF-1.4...", "application/pdf")},
            )
            assert r.status_code == 200
            assert r.json()["original_filename"] == "report.pdf"