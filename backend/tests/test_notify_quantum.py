# -*- coding: utf-8 -*-
"""量子密信群机器人 Webhook 协议单元测试。"""
from unittest.mock import AsyncMock, patch

import pytest

import services.notify as notify


QUANTUM_URL = "https://imtwo.zdxlz.com/im-external/v1/webhook/send?key=robot-key"


@pytest.mark.parametrize("url", [
    QUANTUM_URL,
    "https://imtwo.zdxlz.com/im-external/v1/webhook/send?key=1234567890",
])
def test_quantum_webhook_url_is_accepted(url):
    assert notify.validate_webhook_url(url) == url


@pytest.mark.parametrize("url", [
    "http://imtwo.zdxlz.com/im-external/v1/webhook/send?key=x",
    "https://imtwo.zdxlz.com/im-external/v1/webhook/send",
    "https://imtwo.zdxlz.com/im-external/v1/webhook/send?key=",
    "https://imtwo.zdxlz.com/im-external/v1/webhook/send?key=x&next=https://evil.test",
    "https://imtwo.zdxlz.com.evil.test/im-external/v1/webhook/send?key=x",
    "https://imtwo.zdxlz.com/im-external/v1/webhook/send/extra?key=x",
])
def test_invalid_quantum_webhook_url_is_rejected(url):
    with pytest.raises(ValueError):
        notify.validate_webhook_url(url)


@pytest.mark.asyncio
async def test_quantum_record_uses_text_message_schema():
    post_mock = AsyncMock(return_value={"ok": True, "code": 200, "message": "成功"})
    record_data = {
        "file_date": "20260809",
        "metrics": {"total_current": 100, "year_target": 200, "total_rate": 0.5},
        "four_class_warnings": {"items": []},
    }
    with patch.object(notify, "_post", new=post_mock):
        result = await notify.push_record(QUANTUM_URL, record_data)

    assert result == {"errcode": 0}
    url, payload = post_mock.await_args.args
    assert url == QUANTUM_URL
    assert payload["type"] == "text"
    assert set(payload) == {"type", "textMsg"}
    assert "工程建设进度播报" in payload["textMsg"]["content"]
    assert "<font" not in payload["textMsg"]["content"]


@pytest.mark.asyncio
async def test_quantum_test_uses_text_message_schema():
    post_mock = AsyncMock(return_value={"ok": True, "code": 200})
    with patch.object(notify, "_post", new=post_mock):
        result = await notify.send_test(QUANTUM_URL)

    assert result == {"errcode": 0}
    assert post_mock.await_args.args[1] == {
        "type": "text",
        "textMsg": {"content": "在建工程数据驾驶舱 Webhook 配置成功！\n这是一条测试消息，可以忽略。"},
    }
