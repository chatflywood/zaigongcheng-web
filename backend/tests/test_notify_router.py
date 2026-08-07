# -*- coding: utf-8 -*-
"""
notify 路由集成测试（配置读写 + 测试推送）。

范式同 test_budget_batch_router：内存 SQLite + httpx.ASGITransport (async) +
StaticPool。push/test 因涉及外部 webhook，用 unittest.mock 伪造 services。
"""
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Base  # noqa: E402
import routers.notify as notify_mod  # noqa: E402


@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    orig_get_db = notify_mod.get_db
    notify_mod.get_db = lambda: Session()
    try:
        yield Session
    finally:
        notify_mod.get_db = orig_get_db
        Base.metadata.drop_all(engine)
        engine.dispose()


def build_client():
    app = FastAPI()
    app.include_router(notify_mod.router, prefix="/api/notify")
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


class TestNotifyConfig:
    @pytest.mark.asyncio
    async def test_get_config_empty_when_not_configured(self, test_db):
        async with build_client() as c:
            r = await c.get("/api/notify/config")
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["configured"] is False
        assert body["masked_url"] == ""
        assert body["auto_push"] is False

    @pytest.mark.asyncio
    async def test_save_valid_feishu_url_then_get(self, test_db):
        async with build_client() as c:
            url = "https://open.feishu.cn/openapi/bot/v2/hook/abcdef123456"
            r = await c.post("/api/notify/config", json={"webhook_url": url, "auto_push": True})
            assert r.status_code == 200
            assert r.json()["success"] is True

            r = await c.get("/api/notify/config")
            body = r.json()
            assert body["configured"] is True
            assert body["auto_push"] is True
            # 脱敏：末 8 位明文 + 前面 *
            assert body["masked_url"].endswith("123456")
            assert "*" in body["masked_url"]

    @pytest.mark.asyncio
    async def test_save_invalid_url_rejected(self, test_db):
        async with build_client() as c:
            r = await c.post("/api/notify/config", json={"webhook_url": "http://evil.com/", "auto_push": False})
            assert r.status_code == 400

    @pytest.mark.asyncio
    @pytest.mark.parametrize("url", [
        "https://open.feishu.cn.evil.test/open-apis/bot/v2/hook/key",
        "https://open.feishu.cn@127.0.0.1/open-apis/bot/v2/hook/key",
        "https://open.feishu.cn:8443/open-apis/bot/v2/hook/key",
        "https://qyapi.weixin.qq.com/other/path?key=xxx",
    ])
    async def test_save_host_confusion_and_wrong_paths_rejected(self, test_db, url):
        async with build_client() as c:
            r = await c.post("/api/notify/config", json={"webhook_url": url, "auto_push": False})
        assert r.status_code == 400

    @pytest.mark.asyncio
    async def test_save_qyapi_url_accepted(self, test_db):
        async with build_client() as c:
            r = await c.post("/api/notify/config",
                              json={"webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx", "auto_push": False})
            assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_clear_config(self, test_db):
        async with build_client() as c:
            await c.post("/api/notify/config",
                         json={"webhook_url": "https://open.feishu.cn/openapi/bot/v2/hook/abcd1234", "auto_push": False})
            r = await c.post("/api/notify/config/clear")
            assert r.status_code == 200
            assert r.json()["success"] is True
            body = (await c.get("/api/notify/config")).json()
            assert body["configured"] is False


class TestNotifyPush:
    @pytest.mark.asyncio
    async def test_push_without_webhook_returns_400(self, test_db):
        async with build_client() as c:
            r = await c.post("/api/notify/push/1")
            assert r.status_code == 400

    @pytest.mark.asyncio
    async def test_push_nonexistent_record_returns_404(self, test_db):
        async with build_client() as c:
            # 先配置 webhook
            await c.post("/api/notify/config",
                         json={"webhook_url": "https://open.feishu.cn/openapi/bot/v2/hook/abcd1234", "auto_push": False})
            r = await c.post("/api/notify/push/9999")
            assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_test_push_without_url_returns_400(self, test_db):
        async with build_client() as c:
            r = await c.post("/api/notify/test", json={})
            assert r.status_code == 400

    @pytest.mark.asyncio
    async def test_test_push_success_mocked(self, test_db):
        """对外部 webhook 用 mock 隔离，只验证路由逻辑。"""
        async with build_client() as c:
            with patch.object(notify_mod, "send_test", new=AsyncMock(return_value={"errcode": 0})):
                r = await c.post("/api/notify/test",
                                 json={"webhook_url": "https://open.feishu.cn/openapi/bot/v2/hook/abcd1234"})
            assert r.status_code == 200
            assert r.json()["success"] is True

    @pytest.mark.asyncio
    async def test_test_push_rejects_ssrf_before_network_call(self, test_db):
        send_mock = AsyncMock(return_value={"errcode": 0})
        async with build_client() as c:
            with patch.object(notify_mod, "send_test", new=send_mock):
                r = await c.post(
                    "/api/notify/test",
                    json={"webhook_url": "https://127.0.0.1/internal"},
                )
        assert r.status_code == 400
        send_mock.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_test_push_platform_error_mocked(self, test_db):
        async with build_client() as c:
            with patch.object(notify_mod, "send_test", new=AsyncMock(return_value={"errcode": 93000, "errmsg": "无效 webhook"})):
                r = await c.post("/api/notify/test",
                                 json={"webhook_url": "https://open.feishu.cn/openapi/bot/v2/hook/abcd1234"})
            assert r.status_code == 502
