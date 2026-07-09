# -*- coding: utf-8 -*-
"""
budget 路由集成测试 + 算钱纯函数单测。

覆盖预算页「上传 → 一级专业年度支出汇总 → 与预算目标对比 → 刷新 / 历史快照」
整条链路——此前 94/94 gate 模式里这一段零覆盖，是 PRD 第 11 章 P1 唯一未落地项。

范式同 test_budget_batch_router / test_report_router：内存 SQLite + httpx.ASGITransport
(async) + StaticPool，patch `routers.budget.get_db`，无需启 uvicorn。
纯函数段 (`build_zaigong_spend_summary_from_record` / `load_budget_sheets` /
`clean_nan` / `analyze_budget`) 不入库，直接调模块符号。
注：Starlette 0.35 + httpx 0.28 已弃用 TestClient(app=...) 形式，故用 async client。
"""
import json
import sys
import math
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import httpx
import pandas as pd
import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Base, BudgetRecord, ZaigongRecord  # noqa: E402
import routers.budget as budget_mod  # noqa: E402
from services.budget import analyze_budget  # noqa: E402


# ── 公共夹具 / 助手 ────────────────────────────────────────────

@pytest.fixture
def test_db():
    """内存 SQLite；每个测试函数全新库。
    StaticPool 让单 connection 跨线程共享（ASGI async 会在另一线程读 DB）。
    """
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    orig_get_db = budget_mod.get_db
    budget_mod.get_db = lambda: Session()
    try:
        yield Session
    finally:
        budget_mod.get_db = orig_get_db
        Base.metadata.drop_all(engine)
        engine.dispose()


def build_client():
    """构建 async httpx client（用 ASGITransport 直连 ASGI app，不启 socket）。"""
    app = FastAPI()
    app.include_router(budget_mod.router, prefix="/api/budget")
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


def create_budget_excel(project_sheet_name="2026年新建项目明细"):
    """造一份最小可用预算 Excel（BytesIO），列结构对齐生产格式与 services.budget 期望。

    生产格式在 summary sheet 首行是大标题（合并单元格位置由 pandas 退化为单行），
    真正的列名在第二行——pd.read_excel 默认 header=0 把第一行提升为列名，
    让 analyze_budget 的 `if i==0: continue` 跳过列名行，于是 传输/5G 都进得了 categories。
    列位置：summary 0=一级专业, 1=年度预算, 2=已占用, 3=预占用；
            projects 0=code, 1=name, 2=manager, 3=一级专业, 4=占用, 5=预占用。
    """
    summary_df = pd.DataFrame([
        ["2026年预算下达及立项进度表", "", "", "", ""],   # row 0 — 标题（被 pandas 提为列名）
        ["一级专业", "年度预算", "已占用", "预占用", "立项进度"],  # row 1 — 列名（被 analyze 跳过）
        ["传输", 100, 20, 10, 0.3],
        ["5G", 200, 60, 0, 0.3],
        ["合计", 300, 80, 10, 0.3],
    ])
    projects_df = pd.DataFrame([
        ["项目编号", "项目名称", "工程管理员", "一级专业", "已占用", "预占用"],  # 表头（被 pandas 提为列名）
        ["XM001", "基站A", "张三", "传输", 20, 10],
        ["XM002", "基站B", "李四", "5G", 60, 0],
    ])
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="预算下达及立项进度", index=False, header=False)
        projects_df.to_excel(writer, sheet_name=project_sheet_name, index=False, header=False)
    buffer.seek(0)
    return buffer


def create_wrong_sheet_excel():
    """造一份有效 xlsx 但 sheet 名不含『预算下达及立项进度』，触发 load_budget_sheets ValueError。
    单行单列，不带表头，足够让 pd.ExcelFile 成功打开、再让 read_excel 抛 ValueError。"""
    df = pd.DataFrame([["x"]])
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Sheet1", index=False, header=False)
    buffer.seek(0)
    return buffer


def _seed_budget(db, budget_data=None, source_filename="budget.xlsx", uploaded_at=None):
    """种一条 BudgetRecord。budget_data 任给；uploaded_at 控制时序。"""
    if budget_data is None:
        budget_data = {
            "budget_total": 300,
            "annual_spend_total": 0,
            "occupied_total": 80,
            "preoccupied_total": 10,
            "total_used": 90,
            "approval_progress": 0.3,
            "spend_progress": 0,
            "categories": [
                {"name": "传输", "budget": 100, "annual_spend": 0, "occupied": 20,
                 "preoccupied": 10, "subtotal": 30, "progress": 0.3, "spend_progress": 0},
                {"name": "5G", "budget": 200, "annual_spend": 0, "occupied": 60,
                 "preoccupied": 0, "subtotal": 60, "progress": 0.3, "spend_progress": 0},
            ],
            "projects": [],
        }
    rec = BudgetRecord(
        source_filename=source_filename,
        budget_data=json.dumps(budget_data, ensure_ascii=False),
        uploaded_at=uploaded_at or datetime.now(),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def _seed_zaigong(db, detail_rows=None, uploaded_at=None):
    """种一条 ZaigongRecord，detail_data 是 list[dict]，每项含『一级专业』『本年累计资本性支出』。"""
    if detail_rows is None:
        detail_rows = [
            {"一级专业": "传输", "本年累计资本性支出": 500000},   # 50 万元
            {"一级专业": "5G", "本年累计资本性支出": 800000},      # 80 万元
        ]
    rec = ZaigongRecord(
        source_filename="zaigong.xlsx",
        file_date="0320",
        summary_data="{}",
        metrics_data="{}",
        detail_data=json.dumps(detail_rows, ensure_ascii=False),
        raw_data="[]",
        uploaded_at=uploaded_at or datetime.now(),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


# ── 类 1：build_zaigong_spend_summary_from_record 三条分支 ─────

class TestBuildZaigongSpendSummary:
    def test_detail_data_with_profession_column(self):
        """分支 A：detail_data 含『一级专业』列 → 按 key 累加、/10000、空 category 被跳过。"""
        record = SimpleNamespace(
            detail_data=json.dumps([
                {"一级专业": "5G", "本年累计资本性支出": 1200000},
                {"一级专业": "5G", "本年累计资本性支出": 300000},
                {"一级专业": "传输", "本年累计资本性支出": 500000},
                {"一级专业": "其他", "本年累计资本性支出": 0},
                {"一级专业": "  ", "本年累计资本性支出": 999999},  # 空白 category 被跳过
            ], ensure_ascii=False),
            raw_data="[]",
        )
        out = budget_mod.build_zaigong_spend_summary_from_record(record)
        assert out == {"5G": 150.0, "传输": 50.0, "其他": 0.0}

    def test_fallback_to_raw_data_with_string_numbers(self):
        """分支 B：detail_data 不含一级专业 → 退到 raw_data，字符串数字可转。"""
        record = SimpleNamespace(
            detail_data=json.dumps([{"other_col": "x"}]),  # 不含『一级专业』，分支 A 落空
            raw_data=json.dumps([
                {"一级专业": "STN", "本年累计资本性支出": 880000},
                {"一级专业": "STN", "本年累计资本性支出": 120000},
                {"一级专业": "IDC", "本年累计资本性支出": "2500000"},  # 字符串数字
                {"一级专业": None, "本年累计资本性支出": 555555},     # 空 category 被过滤
            ], ensure_ascii=False),
        )
        out = budget_mod.build_zaigong_spend_summary_from_record(record)
        assert out == {"STN": 100.0, "IDC": 250.0}

    def test_raw_data_missing_required_column_returns_empty(self):
        """分支 B 出口：raw_data 缺必需列 → 返回 {}。"""
        record = SimpleNamespace(
            detail_data="[]",
            raw_data=json.dumps([{"一级专业": "5G", "另一列": 100}], ensure_ascii=False),
        )
        assert budget_mod.build_zaigong_spend_summary_from_record(record) == {}

    def test_record_none_returns_empty(self):
        """分支 C：record=None → 返回 {}。"""
        assert budget_mod.build_zaigong_spend_summary_from_record(None) == {}

    def test_both_empty_returns_empty(self):
        """detail_data=[] 且 raw_data=[] → 返回 {}（不进 if not record 分支，末尾兜底）。"""
        record = SimpleNamespace(detail_data="[]", raw_data="[]")
        assert budget_mod.build_zaigong_spend_summary_from_record(record) == {}


# ── 类 2：load_budget_sheets / clean_nan 纯函数 ────────────────

class TestBudgetHelpers:
    def test_load_budget_sheets_year_agnostic(self):
        """项目明细 sheet 名年份无关：『2027年新建项目明细』也应命中正则。"""
        df_summary, df_projects = budget_mod.load_budget_sheets(
            create_budget_excel(project_sheet_name="2027年新建项目明细").getvalue()
        )
        assert len(df_summary) == 4                 # 表头 + 传输 + 5G + 合计
        assert df_projects is not None
        assert len(df_projects) == 2

    def test_load_budget_sheets_missing_project_sheet(self):
        """Excel 没有以『新建项目明细』结尾的 sheet → df_projects 为 None。"""
        df = pd.DataFrame([["一级专业", "年度预算"], ["传输", 100]])
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="预算下达及立项进度", index=False, header=False)
        buffer.seek(0)
        _, df_projects = budget_mod.load_budget_sheets(buffer.getvalue())
        assert df_projects is None

    def test_clean_nan_recursive(self):
        """嵌套 dict/list 里的 NaN/Inf 应被递归替换为 None。"""
        data = {
            "a": float("nan"),
            "b": [1, float("inf"), {"c": float("-inf"), "d": 2.5}],
            "e": "ok",
            "f": 3,
        }
        out = budget_mod.clean_nan(data)
        assert out["a"] is None
        assert out["b"][0] == 1
        assert out["b"][1] is None
        assert out["b"][2]["c"] is None
        assert out["b"][2]["d"] == 2.5
        assert out["e"] == "ok"
        assert out["f"] == 3


# ── 类 3：analyze_budget 端到端算账 ────────────────────────────

class TestAnalyzeBudget:
    def test_aligned_budget_projects_spend(self):
        """预算 + 项目明细 + 在建 spend_summary 三者对齐，核对关键字段。"""
        df_summary = pd.DataFrame([
            ["一级专业", "年度预算", "已占用", "预占用"],
            ["5G", 1000.0, 0, 0],
            ["传输", 800.0, 0, 0],
            ["合计", 1800.0, 0, 0],
        ])
        df_projects = pd.DataFrame([
            ["P001", "基站A", "张三", "5G", 200.0, 50.0],
            ["P002", "传输B", "李四", "传输", 100.0, 0.0],
        ])
        spend_summary = {"5G": 150.0, "传输": 80.0}

        out = analyze_budget(df_summary, df_projects, spend_summary)

        assert out["budget_total"] == 1800.0
        # 项目占用优先取自 project_summary（200+100=300），覆盖合计行的 0
        assert out["occupied_total"] == 300.0
        assert out["preoccupied_total"] == 50.0
        assert out["total_used"] == 350.0
        assert out["approval_progress"] == round(350 / 1800, 4)
        assert out["annual_spend_total"] == 230.0
        assert out["spend_progress"] == round(230 / 1800, 4)

        # 单专业核对
        five_g = next(c for c in out["categories"] if c["name"] == "5G")
        assert five_g["budget"] == 1000.0
        assert five_g["occupied"] == 200.0
        assert five_g["preoccupied"] == 50.0
        assert five_g["annual_spend"] == 150.0
        assert five_g["spend_progress"] == round(150 / 1000, 4)
        assert five_g["progress"] == round(250 / 1000, 4)

    def test_spend_summary_none_yields_zero_spend(self):
        """还没传在建工程 → annual_spend 全 0、spend_progress 全 0。"""
        df_summary = pd.DataFrame([
            ["一级专业", "年度预算", "已占用", "预占用"],
            ["5G", 1000.0, 0, 0],
            ["合计", 1000.0, 0, 0],
        ])
        out = analyze_budget(df_summary, None, None)
        assert out["annual_spend_total"] == 0
        assert out["spend_progress"] == 0
        assert all(c["annual_spend"] == 0 for c in out["categories"])
        assert all(c["spend_progress"] == 0 for c in out["categories"])
        assert out["projects"] == []


# ── 类 4：POST /api/budget/upload ─────────────────────────────

class TestBudgetUpload:
    @pytest.mark.asyncio
    async def test_upload_valid_excel(self, test_db):
        """有效 Excel → 200、success True、categories 非空、BudgetRecord 入库。"""
        files = {
            "file": (
                "budget_ok.xlsx",
                create_budget_excel(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }
        async with build_client() as c:
            r = await c.post("/api/budget/upload", files=files)
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["filename"] == "budget_ok.xlsx"
        assert isinstance(body["data"]["categories"], list)
        assert body["data"]["categories"]
        # 真入库
        db = test_db()
        try:
            rows = db.query(BudgetRecord).all()
            assert len(rows) == 1
            assert rows[0].source_filename == "budget_ok.xlsx"
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_upload_non_excel_extension(self, test_db):
        """.txt → 400、『仅支持 Excel 文件』、不入库。"""
        files = {"file": ("bad.txt", BytesIO(b"hi"), "text/plain")}
        async with build_client() as c:
            r = await c.post("/api/budget/upload", files=files)
        assert r.status_code == 400
        assert r.json()["message"] == "仅支持 Excel 文件（.xlsx / .xls）"
        db = test_db()
        try:
            assert db.query(BudgetRecord).count() == 0
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_upload_too_large(self, test_db):
        """超过 20MB → 400、『文件大小不能超过 20MB』。"""
        payload = b"\0" * (20 * 1024 * 1024 + 1)
        files = {"file": ("big.xlsx", BytesIO(payload), "application/octet-stream")}
        async with build_client() as c:
            r = await c.post("/api/budget/upload", files=files)
        assert r.status_code == 400
        assert r.json()["message"] == "文件大小不能超过 20MB"

    @pytest.mark.asyncio
    async def test_upload_wrong_sheet_name_returns_400(self, test_db):
        """有效 xlsx 但缺『预算下达及立项进度』sheet → ValueError → 400。"""
        files = {
            "file": (
                "wrong_sheet.xlsx",
                create_wrong_sheet_excel(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }
        async with build_client() as c:
            r = await c.post("/api/budget/upload", files=files)
        assert r.status_code == 400
        assert r.json()["success"] is False
        assert "预算下达及立项进度" in r.json()["message"]


# ── 类 5：POST /api/budget/refresh-spend（最该守护的算钱盲区）──

class TestBudgetRefreshSpend:
    @pytest.mark.asyncio
    async def test_refresh_recomputes_spend(self, test_db):
        """有预算 + 有在建 → annual_spend / annual_spend_total / spend_progress 正确重算并落库。"""
        _seed_budget(test_db(), budget_data={
            "budget_total": 300,
            "annual_spend_total": 0,
            "occupied_total": 80,
            "preoccupied_total": 10,
            "total_used": 90,
            "approval_progress": 0.3,
            "spend_progress": 0,
            "categories": [
                {"name": "传输", "budget": 100, "annual_spend": 0, "occupied": 20,
                 "preoccupied": 10, "subtotal": 30, "progress": 0.3, "spend_progress": 0},
                {"name": "5G", "budget": 200, "annual_spend": 0, "occupied": 60,
                 "preoccupied": 0, "subtotal": 60, "progress": 0.3, "spend_progress": 0},
            ],
            "projects": [],
        })
        _seed_zaigong(test_db(), detail_rows=[
            {"一级专业": "传输", "本年累计资本性支出": 500000},  # 50 万
            {"一级专业": "5G", "本年累计资本性支出": 800000},     # 80 万
        ])

        async with build_client() as c:
            r = await c.post("/api/budget/refresh-spend")
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        data = body["data"]
        assert data["annual_spend_total"] == 130.0
        assert data["spend_progress"] == round(130 / 300, 4)
        cat_map = {c["name"]: c for c in data["categories"]}
        assert cat_map["传输"]["annual_spend"] == 50.0
        assert cat_map["传输"]["spend_progress"] == round(50 / 100, 4)
        assert cat_map["5G"]["annual_spend"] == 80.0
        assert cat_map["5G"]["spend_progress"] == round(80 / 200, 4)

        # 落库验证
        db = test_db()
        try:
            rec = db.query(BudgetRecord).order_by(BudgetRecord.uploaded_at.desc()).first()
            stored = json.loads(rec.budget_data)
            assert stored["annual_spend_total"] == 130.0
        finally:
            db.close()

    @pytest.mark.asyncio
    async def test_refresh_no_budget_record(self, test_db):
        """无预算记录 → 200、success False、『暂无预算记录』。"""
        async with build_client() as c:
            r = await c.post("/api/budget/refresh-spend")
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is False
        assert "暂无预算记录" in body["message"]

    @pytest.mark.asyncio
    async def test_refresh_with_budget_but_no_zaigong(self, test_db):
        """有预算但无在建 → annual_spend 全 0、不崩、写回全 0。"""
        _seed_budget(test_db())
        async with build_client() as c:
            r = await c.post("/api/budget/refresh-spend")
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["data"]["annual_spend_total"] == 0
        assert all(c["annual_spend"] == 0 for c in body["data"]["categories"])


# ── 类 6：GET /api/budget/history{,/{id}} ─────────────────────

class TestBudgetHistory:
    @pytest.mark.asyncio
    async def test_history_empty(self, test_db):
        """空库 → 200、data == []。"""
        async with build_client() as c:
            r = await c.get("/api/budget/history")
        assert r.status_code == 200
        assert r.json() == {"success": True, "data": []}

    @pytest.mark.asyncio
    async def test_history_returns_desc_by_time_and_limit(self, test_db):
        """seed 3 条不同时间 → 按 uploaded_at desc、limit 生效。"""
        base = datetime(2026, 7, 1, 12, 0, 0)
        db = test_db()
        try:
            _seed_budget(db, source_filename="old.xlsx", uploaded_at=base)
            _seed_budget(db, source_filename="mid.xlsx", uploaded_at=base + timedelta(hours=1))
            _seed_budget(db, source_filename="new.xlsx", uploaded_at=base + timedelta(hours=2))
        finally:
            db.close()

        async with build_client() as c:
            r_all = await c.get("/api/budget/history?limit=10")
            r_one = await c.get("/api/budget/history?limit=2")
        assert r_all.status_code == 200
        names_all = [item["source_filename"] for item in r_all.json()["data"]]
        assert names_all == ["new.xlsx", "mid.xlsx", "old.xlsx"]
        assert [item["source_filename"] for item in r_one.json()["data"]] == ["new.xlsx", "mid.xlsx"]

    @pytest.mark.asyncio
    async def test_history_snapshot_empty_library_404(self, test_db):
        """空库 GET /history/{id} → 404、『暂无历史记录』。"""
        async with build_client() as c:
            r = await c.get("/api/budget/history/1")
        assert r.status_code == 404
        assert r.json()["message"] == "暂无历史记录"

    @pytest.mark.asyncio
    async def test_history_snapshot_current_and_previous(self, test_db):
        """/history/{id} 命中 → current 命中、previous 是时间上一条。"""
        base = datetime(2026, 7, 1, 12, 0, 0)
        db = test_db()
        try:
            rec_old = _seed_budget(db, source_filename="old.xlsx", uploaded_at=base)
            rec_new = _seed_budget(db, source_filename="new.xlsx",
                                   uploaded_at=base + timedelta(hours=1))
        finally:
            db.close()

        async with build_client() as c:
            r = await c.get(f"/api/budget/history/{rec_new.id}")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["current"]["id"] == rec_new.id
        assert data["current"]["source_filename"] == "new.xlsx"
        assert data["previous"]["id"] == rec_old.id
        assert data["previous"]["source_filename"] == "old.xlsx"

    @pytest.mark.asyncio
    async def test_history_snapshot_not_found(self, test_db):
        """有记录但 id 不存在 → 404、『记录不存在』。"""
        db = test_db()
        try:
            _seed_budget(db)
        finally:
            db.close()
        async with build_client() as c:
            r = await c.get("/api/budget/history/99999")
        assert r.status_code == 404
        assert r.json()["message"] == "记录不存在"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])