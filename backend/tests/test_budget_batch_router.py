# -*- coding: utf-8 -*-
"""
budget_batch 路由集成测试（专业 + 批次 CRUD）。

范式：FastAPI app + httpx.ASGITransport（async），无需启 uvicorn；用内存 SQLite
重定向 routers.budget_batch.get_db，让测试隔离不污染真实数据文件。
注：Starlette 0.35 + httpx 0.28 已弃用 TestClient(app=...) 形式，故用 async client。
"""
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
import routers.budget_batch as budget_batch_mod  # noqa: E402


@pytest.fixture
def test_db():
    """内存 SQLite；每个测试函数全新库。
    用 StaticPool 让单 connection 跨线程共享（ASGI async 会在另一线程读 DB）。
    """
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    orig_get_db = budget_batch_mod.get_db
    budget_batch_mod.get_db = lambda: Session()
    try:
        yield Session
    finally:
        budget_batch_mod.get_db = orig_get_db
        Base.metadata.drop_all(engine)
        engine.dispose()


def build_client():
    """构建 async httpx client（用 ASGITransport 直连 ASGI app，不启 socket）。"""
    app = FastAPI()
    app.include_router(budget_batch_mod.router, prefix="/api/budget-batch")
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


# ── 专业 CRUD ────────────────────────────────────────────────

class TestSpecialtiesCRUD:
    @pytest.mark.asyncio
    async def test_list_empty(self, test_db):
        async with build_client() as c:
            r = await c.get("/api/budget-batch/specialties")
        assert r.status_code == 200
        assert r.json() == []

    @pytest.mark.asyncio
    async def test_add_specialty_then_list(self, test_db):
        async with build_client() as c:
            r = await c.post("/api/budget-batch/specialties", json={"name": "通信", "sort_order": 0})
            assert r.status_code == 200
            created = r.json()
            assert created["name"] == "通信"
            assert isinstance(created["id"], int)

            r = await c.get("/api/budget-batch/specialties")
            assert r.status_code == 200
            rows = r.json()
            assert len(rows) == 1
            assert rows[0]["name"] == "通信"

    @pytest.mark.asyncio
    async def test_add_duplicate_name_rejected(self, test_db):
        async with build_client() as c:
            await c.post("/api/budget-batch/specialties", json={"name": "信号", "sort_order": 0})
            r = await c.post("/api/budget-batch/specialties", json={"name": "信号", "sort_order": 1})
            assert r.status_code == 400

    @pytest.mark.asyncio
    async def test_update_specialty_name(self, test_db):
        async with build_client() as c:
            created = (await c.post("/api/budget-batch/specialties", json={"name": "信号", "sort_order": 0})).json()
            sid = created["id"]
            r = await c.put(f"/api/budget-batch/specialties/{sid}", json={"name": "信号工程"})
            assert r.status_code == 200
            assert r.json()["name"] == "信号工程"

    @pytest.mark.asyncio
    async def test_update_nonexistent_specialty_404(self, test_db):
        async with build_client() as c:
            r = await c.put("/api/budget-batch/specialties/9999", json={"name": "X"})
            assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_update_specialty_dup_name_rejected(self, test_db):
        async with build_client() as c:
            await c.post("/api/budget-batch/specialties", json={"name": "通信", "sort_order": 0})
            b = (await c.post("/api/budget-batch/specialties", json={"name": "信号", "sort_order": 1})).json()
            r = await c.put(f"/api/budget-batch/specialties/{b['id']}", json={"name": "通信"})
            assert r.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_specialty(self, test_db):
        async with build_client() as c:
            created = (await c.post("/api/budget-batch/specialties", json={"name": "电力", "sort_order": 0})).json()
            r = await c.delete(f"/api/budget-batch/specialties/{created['id']}")
            assert r.status_code == 200
            assert r.json()["ok"] is True
            assert (await c.get("/api/budget-batch/specialties")).json() == []

    @pytest.mark.asyncio
    async def test_delete_nonexistent_specialty_404(self, test_db):
        async with build_client() as c:
            r = await c.delete("/api/budget-batch/specialties/9999")
            assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_reorder_specialties(self, test_db):
        async with build_client() as c:
            a = (await c.post("/api/budget-batch/specialties", json={"name": "A", "sort_order": 1})).json()
            b = (await c.post("/api/budget-batch/specialties", json={"name": "B", "sort_order": 2})).json()
            r = await c.put("/api/budget-batch/specialties/reorder/batch",
                            json=[{"id": a["id"], "sort_order": 5}, {"id": b["id"], "sort_order": 0}])
            assert r.status_code == 200
            assert r.json()["ok"] is True
            rows = (await c.get("/api/budget-batch/specialties")).json()
            assert rows[0]["name"] == "B"
            assert rows[1]["name"] == "A"


# ── 批次 CRUD ────────────────────────────────────────────────────

class TestBatchesCRUD:
    @pytest.mark.asyncio
    async def test_list_empty(self, test_db):
        async with build_client() as c:
            r = await c.get("/api/budget-batch/batches")
        assert r.status_code == 200
        assert r.json() == {"specialties": [], "batches": [], "totals": {}}

    @pytest.mark.asyncio
    async def test_create_and_list_batch(self, test_db):
        async with build_client() as c:
            await c.post("/api/budget-batch/specialties", json={"name": "通信", "sort_order": 0})
            r = await c.post("/api/budget-batch/batches", json={
                "batch_date": "2026-07-01",
                "note": "首批",
                "amounts": {"通信": 100},
                "notes": {"通信": "首批下达"},
            })
            assert r.status_code == 200
            row = r.json()
            assert row["batch_date"] == "2026-07-01"
            assert row["amounts"] == {"通信": 100}

            r = await c.get("/api/budget-batch/batches")
            body = r.json()
            assert body["specialties"] == ["通信"]
            assert len(body["batches"]) == 1
            assert body["totals"] == {"通信": 100}

    @pytest.mark.asyncio
    async def test_update_batch(self, test_db):
        async with build_client() as c:
            created = (await c.post("/api/budget-batch/batches", json={
                "batch_date": "2026-07-01", "note": "", "amounts": {}, "notes": {},
            })).json()
            r = await c.put(f"/api/budget-batch/batches/{created['id']}", json={
                "batch_date": "2026-08-01",
                "amounts": {"通信": 50},
            })
            assert r.status_code == 200
            row = r.json()
            assert row["batch_date"] == "2026-08-01"
            assert row["amounts"] == {"通信": 50}

    @pytest.mark.asyncio
    async def test_update_nonexistent_batch_404(self, test_db):
        async with build_client() as c:
            r = await c.put("/api/budget-batch/batches/9999", json={"note": "x"})
            assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_batch(self, test_db):
        async with build_client() as c:
            created = (await c.post("/api/budget-batch/batches", json={
                "batch_date": "2026-07-01", "note": "", "amounts": {}, "notes": {},
            })).json()
            r = await c.delete(f"/api/budget-batch/batches/{created['id']}")
            assert r.status_code == 200
            body = (await c.get("/api/budget-batch/batches")).json()
            assert len(body["batches"]) == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_batch_404(self, test_db):
        async with build_client() as c:
            r = await c.delete("/api/budget-batch/batches/9999")
            assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_totals_aggregation(self, test_db):
        async with build_client() as c:
            await c.post("/api/budget-batch/specialties", json={"name": "通信", "sort_order": 0})
            await c.post("/api/budget-batch/batches", json={
                "batch_date": "2026-07-01", "note": "", "amounts": {"通信": 100.5}, "notes": {},
            })
            await c.post("/api/budget-batch/batches", json={
                "batch_date": "2026-08-01", "note": "", "amounts": {"通信": 50}, "notes": {},
            })
            body = (await c.get("/api/budget-batch/batches")).json()
            assert body["totals"] == {"通信": 150.5}

    @pytest.mark.asyncio
    async def test_specialty_rename_propagates_to_batches(self, test_db):
        async with build_client() as c:
            s = (await c.post("/api/budget-batch/specialties", json={"name": "通信", "sort_order": 0})).json()
            await c.post("/api/budget-batch/batches", json={
                "batch_date": "2026-07-01", "note": "", "amounts": {"通信": 30},
                "notes": {"通信": "首批备注"},
            })
            r = await c.put(f"/api/budget-batch/specialties/{s['id']}", json={"name": "通信工程"})
            assert r.status_code == 200
            body = (await c.get("/api/budget-batch/batches")).json()
            assert body["specialties"] == ["通信工程"]
            assert body["batches"][0]["amounts"] == {"通信工程": 30}
            assert body["batches"][0]["notes"] == {"通信工程": "首批备注"}