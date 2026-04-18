# -*- coding: utf-8 -*-
"""
AI 路由单元测试（不依赖外部 MiniMax 服务）。
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

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
        assert "综合定论" in body["data"]["content"]
        assert body["data"]["structured"]["verdict"]
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

    def test_compute_rule_signals_risk_levels(self):
        """验证风险等级边界：进度严重滞后 + 转固率极低 → 高风险"""
        metrics_high = ai.MetricsInput(
            year_target=503.0,
            total_current=50.0,
            progress_pct=10.0,   # 大幅低于年内节奏
            month_spend=5.0,
            pending=90.0,        # 超过 80 阈值
            transfer_rate=0.10,  # 低于 0.3 阈值
        )
        signals = ai.compute_rule_signals(metrics_high, [], None, "2026-06-01")
        assert signals["risk_level"] == "高"

        metrics_low = ai.MetricsInput(
            year_target=503.0,
            total_current=450.0,
            progress_pct=90.0,
            month_spend=50.0,
            pending=10.0,
            transfer_rate=0.85,
        )
        signals_low = ai.compute_rule_signals(metrics_low, [], None, "2026-09-01")
        assert signals_low["risk_level"] == "低"

    def test_compute_rule_signals_no_budget(self):
        """无预算数据时 approval_spend_gap_pct 应为 0"""
        metrics = ai.MetricsInput(
            year_target=503.0, total_current=200.0, progress_pct=39.8,
            month_spend=40.0, pending=20.0, transfer_rate=0.5,
        )
        signals = ai.compute_rule_signals(metrics, [], None, "2026-04-01")
        assert signals["approval_spend_gap_pct"] == 0.0
        assert signals["budget_spend_progress_pct"] == 0.0
        assert isinstance(signals["basis"], list)
        assert len(signals["basis"]) > 0

    def test_compute_rule_signals_top_managers(self):
        """top_pending_managers / top_capital_managers 按金额降序排列"""
        summary = [
            ai.ManagerSummary(manager="甲", capital=300.0, pending=5.0, rate=0.7, month_spend=30.0),
            ai.ManagerSummary(manager="乙", capital=100.0, pending=80.0, rate=0.3, month_spend=10.0),
            ai.ManagerSummary(manager="丙", capital=50.0, pending=60.0, rate=0.4, month_spend=5.0),
        ]
        metrics = ai.MetricsInput(
            year_target=503.0, total_current=200.0, progress_pct=39.8,
            month_spend=45.0, pending=145.0, transfer_rate=0.5,
        )
        signals = ai.compute_rule_signals(metrics, summary, None, "2026-04-01")
        assert signals["top_capital_managers"][0]["manager"] == "甲"
        assert signals["top_pending_managers"][0]["manager"] == "乙"

    def test_build_fallback_analysis_structure(self):
        """build_fallback_analysis 返回结构包含所有必要字段"""
        metrics = ai.MetricsInput(
            year_target=503.0, total_current=200.0, progress_pct=39.8,
            month_spend=40.0, pending=50.0, transfer_rate=0.4,
        )
        summary = [
            ai.ManagerSummary(manager="张三", capital=120.0, pending=50.0, rate=0.4, month_spend=20.0),
        ]
        rule_signals = ai.compute_rule_signals(metrics, summary, None, "2026-04-01")
        from services.trend import compute_trend_signals
        trend_signals = compute_trend_signals(
            {"total_current": 200.0, "total_pending": 50.0, "total_today_month": 40.0, "total_rate": 0.4, "year_target": 503.0},
            [],
        )
        result = ai.build_fallback_analysis(metrics, summary, None, "management", rule_signals, trend_signals)
        for key in ("verdict", "diagnosis", "person_bound_actions", "risk_scenarios", "red_flags"):
            assert key in result, f"缺少字段: {key}"
        assert isinstance(result["diagnosis"], list)
        assert len(result["diagnosis"]) == 3
        assert isinstance(result["person_bound_actions"], list)


class TestComputeTrendSignals:
    def test_no_history_returns_fallback(self):
        """无历史数据时返回合理的兜底结构"""
        from services.trend import compute_trend_signals
        metrics = {
            "total_current": 200.0, "total_pending": 40.0,
            "total_today_month": 35.0, "total_rate": 0.5, "year_target": 503.0,
        }
        result = compute_trend_signals(metrics, [])
        assert result["mom_capital_change"] == 0.0
        assert result["avg_monthly_spend_3m"] == 35.0  # 兜底用本月支出
        assert result["required_monthly_to_target"] > 0

    def test_with_two_history_records(self):
        """两条历史数据时能正确计算环比和月均"""
        from services.trend import compute_trend_signals
        metrics = {
            "total_current": 300.0, "total_pending": 45.0,
            "total_today_month": 50.0, "total_rate": 0.55, "year_target": 503.0,
        }
        history = [
            {"month": "2026-02", "total_capital": 200.0, "pending": 35.0, "rate": 0.45},
            {"month": "2026-01", "total_capital": 150.0, "pending": 30.0, "rate": 0.40},
        ]
        result = compute_trend_signals(metrics, history)
        # 环比：300 - 200 = 100，增长 50%
        assert result["mom_capital_change"] == 100.0
        assert result["mom_capital_change_pct"] == 50.0
        assert result["mom_pending_change"] == 10.0  # 45 - 35

    def test_scenario_predictions_ordering(self):
        """最佳情景 >= 一般情景 >= 最差情景"""
        from services.trend import compute_trend_signals
        metrics = {
            "total_current": 250.0, "total_pending": 30.0,
            "total_today_month": 40.0, "total_rate": 0.6, "year_target": 503.0,
        }
        history = [
            {"month": "2026-03", "total_capital": 200.0, "pending": 25.0, "rate": 0.55},
            {"month": "2026-02", "total_capital": 150.0, "pending": 20.0, "rate": 0.50},
        ]
        result = compute_trend_signals(metrics, history)
        assert result["scenario_best"] >= result["scenario_likely"] >= result["scenario_worst"]

    def test_high_pending_surge_triggers_risk(self):
        """待收货环比激增超过20万时应产生 high 级别风险项"""
        from services.trend import compute_trend_signals
        metrics = {
            "total_current": 200.0, "total_pending": 70.0,
            "total_today_month": 30.0, "total_rate": 0.4, "year_target": 503.0,
        }
        history = [
            {"month": "2026-03", "total_capital": 170.0, "pending": 40.0, "rate": 0.38},
        ]
        result = compute_trend_signals(metrics, history)
        high_risks = [r for r in result["risk_items"] if r["severity"] == "high"]
        assert any(r["type"] == "pending_surge" for r in high_risks)

    def test_fetch_history_from_db_returns_list(self):
        """_fetch_history_from_db 在 DB 为空时应返回空列表而不是抛异常"""
        mock_db = MagicMock()
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
        with patch("routers.ai.get_db", return_value=mock_db):
            result = ai._fetch_history_from_db()
        assert result == []
        mock_db.close.assert_called_once()
