"""P0 integration gate: real Excel uploads against an isolated SQLite database."""
import json
from io import BytesIO

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models import Base, ZaigongRecord, BudgetRecord
from routers import analysis, budget
from services.periods import new_period, period_of
from tests.test_golden_metrics import make_golden_zaigong_df
from tests.test_budget_router import create_budget_excel


@pytest_asyncio.fixture
async def system(monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(analysis, 'get_db', session)
    monkeypatch.setattr(budget, 'get_db', session)
    app = FastAPI()
    app.include_router(analysis.router, prefix='/z')
    app.include_router(budget.router, prefix='/b')
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        yield client, session
    engine.dispose()


def engineering_excel(capital=150):
    df = make_golden_zaigong_df()
    df['本年累计资本性支出'] = [capital * 10000, 0]
    stream = BytesIO()
    df.to_excel(stream, index=False)
    return stream.getvalue()


async def upload_z(client, day='2026-09-01', capital=150):
    r = await client.post('/z/upload', params={'target': 500, 'business_date': day},
                          files={'file': ('工程.xlsx', engineering_excel(capital))})
    assert r.status_code == 200, r.text
    return r.json()['record_id']


async def upload_b(client, day='2026-09-01'):
    r = await client.post('/b/upload', params={'business_date': day},
                          files={'file': ('预算.xlsx', create_budget_excel().getvalue())})
    assert r.status_code == 200, r.text
    return r.json()['record_id']


@pytest.mark.asyncio
async def test_same_filename_keeps_both_snapshots(system):
    client, session = system
    first = await upload_z(client)
    original = (await client.get(f'/z/history/{first}')).json()['data']['current']
    second = await upload_z(client, capital=200)
    assert first != second
    assert (await client.get(f'/z/history/{first}')).json()['data']['current'] == original
    b1, b2 = await upload_b(client), await upload_b(client)
    assert b1 != b2
    with session() as db:
        assert db.query(ZaigongRecord).count() == 2
        assert db.query(BudgetRecord).count() == 2


@pytest.mark.asyncio
async def test_backfill_does_not_replace_current_period(system):
    client, _ = system
    current = await upload_z(client, '2026-09-01', 200)
    await upload_z(client, '2026-08-01', 100)
    assert (await client.get('/z/history?limit=1')).json()['data'][0]['id'] == current
    assert (await client.get('/z/compare')).json()['data']['latest']['id'] == current
    latest_budget = await upload_b(client, '2026-09-01')
    await upload_b(client, '2026-08-01')
    live = (await client.post('/b/refresh-spend')).json()['data']
    assert live['record_id'] == latest_budget
    assert live['annual_spend_total'] == 200
    assert live['source_link']['zaigong_record_id'] == current


@pytest.mark.asyncio
async def test_refresh_and_target_edit_do_not_mutate_snapshots(system):
    client, _ = system
    z1 = await upload_z(client)
    b1 = await upload_b(client)
    old_budget = (await client.get(f'/b/history/{b1}')).json()['data']['current']
    z2 = await upload_z(client, capital=220)
    live = (await client.post('/b/refresh-spend')).json()['data']
    assert live['annual_spend_total'] == 220
    assert live['source_link']['zaigong_record_id'] == z2
    assert (await client.get(f'/b/history/{b1}')).json()['data']['current'] == old_budget
    before = (await client.get(f'/z/history/{z1}')).json()['data']['current']
    changed = (await client.post(f'/z/history/{z1}/target?target=300')).json()
    assert changed['record_id'] != z1
    assert (await client.get(f'/z/history/{z1}')).json()['data']['current'] == before
    new = (await client.get(f'/z/history/{changed["record_id"]}')).json()['data']['current']
    assert new['metrics']['progress_ratio'] == .5
    assert new['metrics']['deficit'] == 150


@pytest.mark.asyncio
async def test_cross_year_and_future_sources_are_excluded(system):
    client, _ = system
    await upload_z(client, '2025-12-31', 900)
    await upload_z(client, '2026-10-01', 600)
    b1 = await upload_b(client, '2026-09-01')
    current = (await client.get(f'/b/history/{b1}')).json()['data']['current']['data']
    assert current['source_link']['zaigong_record_id'] is None
    assert current['source_link']['spend_available'] is False
    assert current['source_link']['warnings']
    eligible = await upload_z(client, '2026-08-31', 250)
    live = (await client.post('/b/refresh-spend')).json()['data']
    assert live['source_link']['zaigong_record_id'] == eligible
    assert live['annual_spend_total'] == 250
    assert '日期不一致' in live['source_link']['warnings'][0]


@pytest.mark.asyncio
async def test_explicit_date_and_warning_calculation_date(system):
    client, _ = system
    rid = await upload_z(client, '2026-03-20')
    snap = (await client.get(f'/z/history/{rid}')).json()['data']['current']
    assert snap['period']['business_date'] == '2026-03-20'
    assert snap['four_class_warnings']['analysis_date'] == '2026-03-20'
    r = await client.post('/z/upload?business_date=2026-02-30', files={'file': ('bad.xlsx', engineering_excel())})
    assert r.status_code == 400


def test_legacy_dates_are_not_invented():
    record = ZaigongRecord(source_filename='工程(0320).xlsx', metrics_data='{}')
    assert period_of(record)['business_date'] is None
    record.source_filename = '工程(20260320).xlsx'
    assert period_of(record)['business_date'] == '2026-03-20'
    assert new_period('预算2026-09-01.xlsx')['business_date'] == '2026-09-01'
    assert new_period('预算20260901.xlsx', '2026-08-31')['date_source'] == 'user'


@pytest.mark.asyncio
async def test_ai_history_uses_business_month_and_deduplicates_versions(system, monkeypatch):
    from routers import ai
    client, session = system
    monkeypatch.setattr(ai, 'get_db', session)
    await upload_z(client, '2025-12-31', 900)
    await upload_z(client, '2026-08-10', 100)
    await upload_z(client, '2026-08-31', 200)
    await upload_z(client, '2026-09-01', 300)
    await upload_z(client, '2026-07-31', 80)
    history = ai._fetch_history_from_db(analysis_date='2026-09-01')
    assert [(r['month'], r['total_capital']) for r in history] == [('2026-08', 200), ('2026-07', 80)]


def test_forecast_uses_report_month_even_when_viewed_later():
    from services.trend import compute_trend_signals
    result = compute_trend_signals({'total_current': 100, 'year_target': 1000, 'total_today_month': 20}, [], analysis_date='2026-03-20')
    assert result['required_monthly_to_target'] == 100
