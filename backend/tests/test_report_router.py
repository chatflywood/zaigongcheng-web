# -*- coding: utf-8 -*-
"""
report 路由集成测试（HTML 简报 + PNG 简报）。

范式同 test_budget_batch_router：内存 SQLite + httpx.ASGITransport (async) +
StaticPool。brief/image 真实绘制 PNG 用 Pillow，速度慢且耦合性高，这里 mock
掉 build_brief_html / build_brief_image 与 _parse_report_month 解耦，只测
路由层：参数校验、404、500 友好响应、StreamingResponse content-type。
"""
import sys
from pathlib import Path
from unittest.mock import patch
from datetime import datetime

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Base, ZaigongRecord, BudgetRecord  # noqa: E402
import routers.report as report_mod  # noqa: E402


@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    orig_get_db = report_mod.get_db
    report_mod.get_db = lambda: Session()
    try:
        yield Session
    finally:
        report_mod.get_db = orig_get_db
        Base.metadata.drop_all(engine)
        engine.dispose()


def build_client():
    app = FastAPI()
    app.include_router(report_mod.router, prefix="/api/report")
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


def _seed_record(db, filename="test.xlsx", file_date="0320"):
    rec = ZaigongRecord(
        source_filename=filename,
        file_date=file_date,
        summary_data="{}",
        metrics_data="{}",
        detail_data="[]",
        raw_data="[]",
        uploaded_at=datetime.now(),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def _seed_budget(db, budget_data='{"foo":1}'):
    rec = BudgetRecord(source_filename="budget.xlsx", budget_data=budget_data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


class TestReportRouter:
    @pytest.mark.asyncio
    async def test_brief_404_for_missing_zaigong(self, test_db):
        async with build_client() as c:
            r = await c.get("/api/report/brief", params={"zaigong_id": 9999})
            assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_brief_returns_html_stream(self, test_db):
        db = test_db()
        rec = _seed_record(db)
        db.close()
        async with build_client() as c:
            with patch.object(report_mod, "build_brief_html", return_value="<html>OK</html>"):
                r = await c.get("/api/report/brief", params={"zaigong_id": rec.id})
            assert r.status_code == 200
            assert "OK" in r.text
            # StreamingResponse 应是 text/html（Content-Type 含 html）
            assert "html" in r.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_brief_handles_render_error_gracefully(self, test_db):
        """渲染异常时不裸露 traceback，仅返回友好 message（v1.34 改造点）。"""
        db = test_db()
        rec = _seed_record(db)
        db.close()
        async with build_client() as c:
            with patch.object(report_mod, "build_brief_html", side_effect=RuntimeError("字体丢失")):
                r = await c.get("/api/report/brief", params={"zaigong_id": rec.id})
            assert r.status_code == 500
            body = r.json()
            assert body["success"] is False
            assert "字体丢失" in body["message"]
            # 关键：不包含 detail 字段（v1.34 已移除 traceback 泄露）
            assert "detail" not in body

    @pytest.mark.asyncio
    async def test_brief_with_optional_budget_id(self, test_db):
        db = test_db()
        z = _seed_record(db)
        b = _seed_budget(db)
        db.close()
        async with build_client() as c:
            with patch.object(report_mod, "build_brief_html", return_value="<html></html>") as m:
                r = await c.get("/api/report/brief", params={"zaigong_id": z.id, "budget_id": b.id})
                assert r.status_code == 200
                m.assert_called_once()
                # zaigong_rec 必传入且 id 正确
                assert m.call_args.args[0].id == z.id

    @pytest.mark.asyncio
    async def test_image_404_for_missing_zaigong(self, test_db):
        async with build_client() as c:
            r = await c.get("/api/report/image", params={"zaigong_id": 9999})
            assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_image_returns_png_stream(self, test_db):
        db = test_db()
        rec = _seed_record(db)
        db.close()
        async with build_client() as c:
            fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
            with patch.object(report_mod, "build_brief_image", return_value=fake_png):
                r = await c.get("/api/report/image", params={"zaigong_id": rec.id})
            assert r.status_code == 200
            assert r.content == fake_png
            ct = r.headers.get("content-type", "").lower()
            assert "image/png" in ct or "octet-stream" in ct

    @pytest.mark.asyncio
    async def test_image_handles_render_error_gracefully(self, test_db):
        db = test_db()
        rec = _seed_record(db)
        db.close()
        async with build_client() as c:
            with patch.object(report_mod, "build_brief_image", side_effect=RuntimeError("Pillow 不可用")):
                r = await c.get("/api/report/image", params={"zaigong_id": rec.id})
            assert r.status_code == 500
            body = r.json()
            assert body["success"] is False
            assert "Pillow 不可用" in body["message"]
            assert "detail" not in body  # 无 traceback