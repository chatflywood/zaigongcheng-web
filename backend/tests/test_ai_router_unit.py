# -*- coding: utf-8 -*-
"""
AI 路由单元测试（不依赖外部 MiniMax 服务）。
"""
import sys
from pathlib import Path

from fastapi import FastAPI
import httpx
import pytest

# 添加 backend 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from routers import ai  # noqa: E402


def build_client():
    app = FastAPI()
    app.include_router(ai.router, prefix="/api/ai")
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


class TestAIRouterUnit:
    @pytest.mark.asyncio
    async def test_status_returns_success(self):
        async with build_client() as client:
            resp = await client.get("/api/ai/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "configured" in body["data"]
        assert "group_id_configured" in body["data"]

    @pytest.mark.asyncio
    async def test_status_configured_with_key_only(self, monkeypatch):
        monkeypatch.setenv("MINIMAX_API_KEY", "fake_key")
        monkeypatch.delenv("MINIMAX_GROUP_ID", raising=False)
        async with build_client() as client:
            resp = await client.get("/api/ai/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["configured"] is True
        assert body["data"]["group_id_configured"] is False

    @pytest.mark.asyncio
    async def test_analyze_returns_not_configured_when_env_missing(self, monkeypatch):
        monkeypatch.setattr(ai, "get_ai_env", lambda: (None, None, "https://api.minimax.chat/v1/text/chatcompletion_v2"))
        payload = {
            "metrics": {
                "year_target": 503.0,
                "total_current": 245.3,
                "progress_pct": 48.8,
                "month_spend": 80.0,
                "pending": 30.0,
                "transfer_rate": 0.62,
            },
            "summary": [{"manager": "张三", "capital": 100.0, "pending": 20.0, "rate": 0.5, "month_spend": 12.0}],
            "budget": {
                "total_budget": 800.0,
                "approval_progress_pct": 55.0,
                "annual_spend_total": 260.0,
                "occupied_total": 300.0,
                "preoccupied_total": 80.0,
            },
            "analysis_date": "2026-03-20",
        }
        async with build_client() as client:
            resp = await client.post("/api/ai/analyze", json=payload)
        assert resp.status_code == 400
        body = resp.json()
        assert body["success"] is False
        assert body["error"] == "AI_NOT_CONFIGURED"

    @pytest.mark.asyncio
    async def test_analyze_fallback_when_empty_response(self, monkeypatch):
        async def _raise_empty(_prompt):
            raise ValueError("MiniMax 返回内容为空或格式不支持")

        monkeypatch.setattr(ai, "call_minimax", _raise_empty)
        payload = {
            "metrics": {
                "year_target": 503.0,
                "total_current": 245.3,
                "progress_pct": 48.8,
                "month_spend": 80.0,
                "pending": 30.0,
                "transfer_rate": 0.62,
            },
            "summary": [{"manager": "张三", "capital": 100.0, "pending": 20.0, "rate": 0.5, "month_spend": 12.0}],
            "budget": {
                "total_budget": 800.0,
                "approval_progress_pct": 55.0,
                "annual_spend_total": 260.0,
                "occupied_total": 300.0,
                "preoccupied_total": 80.0,
            },
            "analysis_date": "2026-03-20",
        }
        async with build_client() as client:
            resp = await client.post("/api/ai/analyze", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["model"] == "local-fallback"
        assert "综合评估" in body["data"]["content"]
        assert body["data"]["structured"]["basis"]
        assert body["data"]["signals"]["risk_level"] in {"低", "中", "高"}

    def test_extract_text_from_minimax_fallback(self):
        data_a = {
            "choices": [{"message": {"content": "A结构文本"}}]
        }
        data_a2 = {
            "choices": [{"message": {"content": [{"type": "text", "text": "A2结构文本"}]}}]
        }
        data_b = {
            "choices": [{"messages": [{"text": "B结构文本"}]}]
        }
        data_c = {"reply": "C结构文本"}
        assert ai.extract_text_from_minimax(data_a) == "A结构文本"
        assert ai.extract_text_from_minimax(data_a2) == "A2结构文本"
        assert ai.extract_text_from_minimax(data_b) == "B结构文本"
        assert ai.extract_text_from_minimax(data_c) == "C结构文本"

    def test_parse_structured_analysis_json_block(self):
        text = """```json
{
  "overall": "整体平稳",
  "progress": "进度正常",
  "spend": "支出集中",
  "rate": "转固率正常",
  "risk": "暂无明显风险",
  "next_month": "预计继续提升",
  "actions": ["动作1", "动作2"]
}
```"""
        data = ai.parse_structured_analysis(text)
        assert isinstance(data, dict)
        assert data["overall"] == "整体平稳"
        assert data["actions"][0] == "动作1"

    def test_compute_rule_signals_with_budget_context(self):
        metrics = ai.MetricsInput(
            year_target=503.0,
            total_current=245.3,
            progress_pct=48.8,
            month_spend=80.0,
            pending=30.0,
            transfer_rate=0.62,
        )
        summary = [
            ai.ManagerSummary(manager="张三", capital=100.0, pending=20.0, rate=0.5, month_spend=12.0),
            ai.ManagerSummary(manager="李四", capital=80.0, pending=35.0, rate=0.25, month_spend=0.0),
        ]
        budget = ai.BudgetInput(
            total_budget=800.0,
            approval_progress_pct=55.0,
            annual_spend_total=260.0,
            occupied_total=300.0,
            preoccupied_total=80.0,
        )
        signals = ai.compute_rule_signals(metrics, summary, budget, "2026-03-20")
        assert signals["expected_progress_pct"] == 25.0
        assert signals["approval_spend_gap_pct"] == 22.5
        assert signals["basis"]
