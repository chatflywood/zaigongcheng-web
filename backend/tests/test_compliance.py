import io
import json
import sys
from datetime import date, datetime
from pathlib import Path

import httpx
import openpyxl
import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).parent.parent))
from models import AppConfig, Base, ZaigongRecord
from routers import compliance
from services.compliance import build_compliance


def project(code="GC1", **values):
    return {"工程编码": code, "工程名称": "工程A", "工程管理员": "伍建勋",
            "项目类型": "常规项目", "工程状态": "工程已关闭", "施工单位": "施工单位A",
            "工程开工日期": "2026-09-02", "设计批复日期(初次)": "2026-09-02",
            "安全生产费": 0, "累计待摊-安全生产费": 1901.79, **values}


def test_inclusive_dates_use_upload_date_and_keep_closed_zero_fee_projects():
    rows = [project("FIRST"), project("LAST", **{"工程开工日期": "2026-11-02"}),
            project("BEFORE", **{"工程开工日期": "2026-09-01"}),
            project("AFTER", **{"工程开工日期": "2026-11-03"}),
            project("MISSING", **{"工程开工日期": None}),
            project("INVALID", **{"工程开工日期": "bad-date"})]
    result = build_compliance(rows, datetime(2026, 11, 2, 8, 54))
    assert (result["start_date"], result["end_date"]) == ("2026-09-02", "2026-11-02")
    check = result["checks"]["safety"]
    assert [item["code"] for item in check["items"]] == ["FIRST", "LAST"]
    assert check["missing_dates"] == check["invalid_dates"] == 1
    assert check["pending"] == 2
    assert check["items"][0]["project_status"] == "工程已关闭"
    assert check["items"][0]["current_safety_fee"] == 0


@pytest.mark.parametrize("uploaded,start", [("2026-04-30", "2026-02-28"),
    ("2024-04-30", "2024-02-29"), ("2026-01-31", "2025-11-30")])
def test_calendar_month_clamping(uploaded, start):
    assert build_compliance([], uploaded)["start_date"] == start


def test_purchase_types_excluded_only_from_safety_and_name_is_not_a_filter():
    rows = [project(str(i), **{"项目类型": kind}) for i, kind in enumerate(
        ["单纯购置项目", "单纯性购置项目", "零星购置项目"])]
    rows.append(project("KEEP", **{"工程名称": "常规项目中的设备购置", "累计待摊-安全生产费": float("nan")}))
    result = build_compliance(rows, "2026-11-02")["checks"]
    assert result["safety"]["total"] == 1
    assert result["safety"]["excluded"] == 3
    assert result["safety"]["items"][0]["code"] == "KEEP"
    assert result["safety"]["items"][0]["total_safety_fee"] is None
    assert result["quality"]["total"] == 4


def test_quality_uses_first_design_approval_not_design_changes_or_project_approval():
    rows = [project("OLD", **{"设计批复日期(初次)": "2026-01-01",
                            "最近一次设计变更批复日期": "2026-10-20", "立项批复日期": "2026-10-10"}),
            project("NEW", **{"设计批复日期(初次)": "2026-09-02"})]
    assert [r["code"] for r in build_compliance(rows, "2026-11-02")["checks"]["quality"]["items"]] == ["NEW"]


def test_duplicate_or_missing_project_codes_do_not_produce_misleading_counts():
    with pytest.raises(ValueError, match="重复"):
        build_compliance([project(), project()], "2026-11-02")
    with pytest.raises(ValueError, match="编码缺失"):
        build_compliance([project("")], "2026-11-02")


@pytest.fixture
def database(monkeypatch):
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)
    monkeypatch.setattr(compliance, "get_db", session)
    yield session
    engine.dispose()


def seed(session, *, rows=None, uploaded=None, period=None):
    with session() as db:
        record = ZaigongRecord(uploaded_at=uploaded or datetime(2026, 11, 2, 8, 54),
            source_filename="在建工程_20261001.xlsx", raw_data=json.dumps(rows if rows is not None else [project()], ensure_ascii=False),
            metrics_data=json.dumps({"period": period or {"business_date": "2026-10-01"}}))
        db.add(record)
        db.commit()
        return record.id


def client():
    app = FastAPI()
    app.include_router(compliance.router, prefix="/api/zaigong")
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_reviews_persist_across_uploads_and_do_not_rewrite_snapshots(database):
    first = seed(database)
    second = seed(database, uploaded=datetime(2026, 11, 3))
    async with client() as api:
        response = await api.put(f"/api/zaigong/compliance/{first}/safety/GC1", json={
            "status": "已核实正常", "reviewed_on": "2026-11-02", "note": "付款凭证已核对"})
        assert response.status_code == 200
        result = (await api.get(f"/api/zaigong/compliance/{second}")).json()["data"]
        assert result["checks"]["safety"]["normal"] == 1  # completed records remain accessible
        assert result["checks"]["safety"]["actionable"] == 0
        # A corrected milestone requires a new review while retaining the old evidence.
        third = seed(database, rows=[project(**{"工程开工日期": "2026-10-01"})], uploaded=datetime(2026, 11, 4))
        result = (await api.get(f"/api/zaigong/compliance/{third}")).json()["data"]
        assert result["checks"]["safety"]["normal"] == 0
        assert result["checks"]["safety"]["recheck"] == 1
        assert result["checks"]["safety"]["pending"] == 1
        assert result["checks"]["safety"]["items"][0]["previous_reviewed_on"] == "2026-11-02"
        assert result["checks"]["safety"]["items"][0]["note"] == "付款凭证已核对"
        assert result["checks"]["quality"]["items"] == []
        original = (await api.get(f"/api/zaigong/compliance/{first}")).json()["data"]
        assert original["checks"]["quality"]["pending"] == 1
    with database() as db:
        assert json.loads(db.query(ZaigongRecord).filter_by(id=first).one().raw_data) == [project()]
        assert db.query(AppConfig).count() == 1


@pytest.mark.asyncio
async def test_target_changes_keep_original_upload_anchor(database):
    original = seed(database)
    revision = seed(database, uploaded=datetime(2026, 12, 20), period={
        "business_date": "2026-10-01", "revision_reason": "target_change", "parent_record_id": original})
    async with client() as api:
        result = (await api.get(f"/api/zaigong/compliance/{revision}")).json()["data"]
        assert result["source_record_id"] == original
        assert result["end_date"] == "2026-11-02"
        assert result["checks"]["safety"]["total"] == 1


@pytest.mark.asyncio
async def test_invalid_reviews_and_unavailable_sources(database):
    rid = seed(database)
    async with client() as api:
        for payload in [{"status": "已支付"}, {"status": "发现问题"}, {"status": "待核实", "note": "x" * 4001}]:
            assert (await api.put(f"/api/zaigong/compliance/{rid}/safety/GC1", json=payload)).status_code == 422
        assert (await api.put(f"/api/zaigong/compliance/{rid}/safety/OTHER", json={"status": "待核实"})).status_code == 404
        assert (await api.get("/api/zaigong/compliance/999")).status_code == 404
    with database() as db:
        db.query(ZaigongRecord).filter_by(id=rid).update({"raw_data": None})
        db.commit()
    async with client() as api:
        assert (await api.get(f"/api/zaigong/compliance/{rid}")).status_code == 422


@pytest.mark.asyncio
async def test_export_reconciles_included_projects_and_neutralizes_formulas(database):
    rid = seed(database, rows=[project(**{"工程名称": "=HYPERLINK(\"bad\")"}),
                              project("BUY", **{"项目类型": "零星购置项目"})])
    async with client() as api:
        await api.put(f"/api/zaigong/compliance/{rid}/safety/GC1", json={
            "status": "发现问题", "reviewed_on": "2026-11-02", "note": "=1+1"})
        response = await api.get(f"/api/zaigong/compliance/{rid}/export")
    assert response.status_code == 200
    book = openpyxl.load_workbook(io.BytesIO(response.content))
    assert book.sheetnames == ["安全生产费核实", "质监申报核实"]
    sheet = book.worksheets[0]
    assert sheet.max_row == 7 and book.worksheets[1].max_row == 8
    assert sheet["A7"].value == "GC1"
    assert sheet["B7"].value.startswith("'=") and sheet["B7"].data_type == "s"
    assert sheet["E7"].value.date() == date(2026, 9, 2)
    assert sheet["I7"].value == 1901.79
    assert sheet["L7"].value == "'=1+1"
    assert sheet.freeze_panes == "C7"


@pytest.mark.asyncio
async def test_two_normal_one_issue_unchanged_reupload_only_one_actionable(database):
    rows = [project(str(i), **{"工程开工日期": "2026-10-01"}) for i in range(3)]
    first = seed(database, rows=rows)
    async with client() as api:
        for i in range(3):
            response = await api.put(f"/api/zaigong/compliance/{first}/safety/{i}", json={
                "status": "发现问题" if i == 2 else "已核实正常", "reviewed_on": "2026-11-02", "note": f"核实记录{i}"})
            assert response.status_code == 200
        second = seed(database, rows=rows, uploaded=datetime(2026, 11, 6))
        check = (await api.get(f"/api/zaigong/compliance/{second}")).json()["data"]["checks"]["safety"]
        assert (check["total"], check["actionable"], check["normal"], check["issues"], check["pending"]) == (3, 1, 2, 1, 0)
        assert check["items"][0]["status"] == "发现问题"
        assert check["recheck"] == 0
        assert check["items"][1]["note"] == "核实记录0"


@pytest.mark.asyncio
async def test_open_issue_survives_window_expiry_and_missing_project_until_resolved(database):
    first = seed(database)
    async with client() as api:
        await api.put(f"/api/zaigong/compliance/{first}/safety/GC1", json={
            "status": "发现问题", "reviewed_on": "2026-11-02", "note": "安全生产费待补付"})
        later = seed(database, uploaded=datetime(2027, 1, 20))
        missing = seed(database, rows=[], uploaded=datetime(2027, 1, 21))
        for rid in (later, missing):
            check = (await api.get(f"/api/zaigong/compliance/{rid}")).json()["data"]["checks"]["safety"]
            assert check["issues"] == check["actionable"] == check["carried_forward"] == 1
            assert check["items"][0]["name"] == "工程A"
            assert check["items"][0]["note"] == "安全生产费待补付"
        pending = await api.put(f"/api/zaigong/compliance/{missing}/safety/GC1", json={
            "status": "待核实", "note": "转为复核中"})
        assert pending.json()["data"]["checks"]["safety"]["actionable"] == 1
        normal = await api.put(f"/api/zaigong/compliance/{missing}/safety/GC1", json={
            "status": "已核实正常", "reviewed_on": "2027-01-21", "note": "已补付"})
        check = normal.json()["data"]["checks"]["safety"]
        assert (check["actionable"], check["normal"], check["total"]) == (0, 1, 1)
        exported = await api.get(f"/api/zaigong/compliance/{missing}/export")
        book = openpyxl.load_workbook(io.BytesIO(exported.content))
        assert book.worksheets[0]["A7"].value == "GC1"
        assert book.worksheets[0]["J7"].value == "已核实正常"
        # Manually reopening an archived case must not drop it from the response
        # or lose its follow-up state on subsequent uploads.
        reopened = await api.put(f"/api/zaigong/compliance/{missing}/safety/GC1", json={
            "status": "待核实", "note": "再次核查"})
        assert reopened.json()["data"]["checks"]["safety"]["pending"] == 1
        next_upload = seed(database, rows=[], uploaded=datetime(2027, 2, 1))
        check = (await api.get(f"/api/zaigong/compliance/{next_upload}")).json()["data"]["checks"]["safety"]
        assert check["actionable"] == 1 and check["items"][0]["note"] == "再次核查"


@pytest.mark.parametrize("field,value,kind", [
    ("工程开工日期", "2026-10-02", "safety"),
    ("安全生产费", 2000, "safety"),
    ("累计待摊-安全生产费", 0, "safety"),
    ("设计批复日期(初次)", "2026-10-02", "quality"),
    ("设计批复文号（初次）", "新文号", "quality"),
])
@pytest.mark.asyncio
async def test_material_changes_reopen_normal_review_then_new_confirmation_clears_it(database, field, value, kind):
    row = project(**{"工程开工日期": "2026-10-01", "设计批复日期(初次)": "2026-10-01"})
    first = seed(database, rows=[row])
    async with client() as api:
        await api.put(f"/api/zaigong/compliance/{first}/{kind}/GC1", json={
            "status": "已核实正常", "reviewed_on": "2026-11-02", "note": "上次凭证"})
        later = seed(database, rows=[{**row, field: value}], uploaded=datetime(2026, 11, 6))
        result = (await api.get(f"/api/zaigong/compliance/{later}")).json()["data"]["checks"][kind]
        assert (result["pending"], result["normal"], result["recheck"], result["actionable"]) == (1, 0, 1, 1)
        item = result["items"][0]
        assert item["reviewed_on"] == "" and item["previous_status"] == "已核实正常"
        assert item["note"] == "上次凭证" and "→" in item["tracking_note"]
        normal = await api.put(f"/api/zaigong/compliance/{later}/{kind}/GC1", json={
            "status": "已核实正常", "reviewed_on": "2026-11-06", "note": "变化已复核"})
        assert normal.json()["data"]["checks"][kind]["actionable"] == 0
        historical = (await api.get(f"/api/zaigong/compliance/{first}")).json()["data"]["checks"][kind]
        assert historical["normal"] == 1 and historical["recheck"] == 0


@pytest.mark.asyncio
async def test_irrelevant_changes_and_equivalent_representation_do_not_reopen_review(database):
    first = seed(database)
    async with client() as api:
        await api.put(f"/api/zaigong/compliance/{first}/safety/GC1", json={
            "status": "已核实正常", "reviewed_on": "2026-11-02"})
        later = seed(database, rows=[project(**{"工程开工日期": "2026/09/02", "安全生产费": "0.00",
            "累计待摊-安全生产费": 1901.79000001, "工程管理员": "张文", "工程状态": "工程已开工",
            "工程名称": "更正后的工程名称", "最近一次设计变更批复日期": "2026-11-06"})], uploaded=datetime(2026, 11, 6))
        check = (await api.get(f"/api/zaigong/compliance/{later}")).json()["data"]["checks"]["safety"]
        assert check["normal"] == 1 and check["actionable"] == 0 and check["recheck"] == 0


@pytest.mark.asyncio
async def test_legacy_reviews_recover_baseline_without_mutating_saved_records(database):
    first = seed(database)
    values = {"status": "已核实正常", "reviewed_on": "2026-11-02", "record_id": first, "note": "旧版已核实备注"}
    original_json = json.dumps(values, ensure_ascii=False)
    with database() as db:
        db.add(AppConfig(key="compliance:safety:GC1", value=original_json))
        db.commit()
    later = seed(database, uploaded=datetime(2026, 11, 6))
    async with client() as api:
        check = (await api.get(f"/api/zaigong/compliance/{later}")).json()["data"]["checks"]["safety"]
        assert check["normal"] == 1 and check["actionable"] == 0
        changed = seed(database, rows=[project(**{"累计待摊-安全生产费": 5000})], uploaded=datetime(2026, 11, 7))
        check = (await api.get(f"/api/zaigong/compliance/{changed}")).json()["data"]["checks"]["safety"]
        assert check["recheck"] == 1 and check["items"][0]["note"] == values["note"]
    with database() as db:
        assert db.query(AppConfig).one().value == original_json


@pytest.mark.asyncio
async def test_saved_recheck_stays_actionable_outside_window_and_with_missing_source_date(database):
    first = seed(database)
    async with client() as api:
        await api.put(f"/api/zaigong/compliance/{first}/safety/GC1", json={
            "status": "已核实正常", "reviewed_on": "2026-11-02"})
        later = seed(database, rows=[project(**{"工程开工日期": None})], uploaded=datetime(2027, 1, 20))
        check = (await api.get(f"/api/zaigong/compliance/{later}")).json()["data"]["checks"]["safety"]
        assert check["pending"] == check["recheck"] == check["carried_forward"] == 1
        result = await api.put(f"/api/zaigong/compliance/{later}/safety/GC1", json={"status": "待核实", "note": "请补充日期"})
        assert result.status_code == 200
        check = result.json()["data"]["checks"]["safety"]
        assert check["pending"] == check["recheck"] == 1
        assert "复核" in check["items"][0]["tracking_note"] or "→" in check["items"][0]["tracking_note"]
