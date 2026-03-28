# -*- coding: utf-8 -*-
"""
后端 API 测试
使用 httpx 直接测试 API
"""
import pytest
import sys
import os
from pathlib import Path

# 添加 backend 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from io import BytesIO
import httpx


# 测试服务器地址
BASE_URL = "http://localhost:8000"

# 测试文件名前缀（用于识别和清理测试数据）
TEST_FILE_PREFIX = "test_upload_"


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_data():
    """测试结束后清理测试数据"""
    yield  # 测试运行
    # 测试结束后清理
    from models import SessionLocal, ZaigongRecord, BudgetRecord
    db = SessionLocal()
    try:
        # 删除测试产生的记录
        db.query(ZaigongRecord).filter(
            ZaigongRecord.source_filename.like(f"%{TEST_FILE_PREFIX}%")
        ).delete(synchronize_session=False)
        db.query(BudgetRecord).filter(
            BudgetRecord.source_filename.like(f"%{TEST_FILE_PREFIX}%")
        ).delete(synchronize_session=False)
        db.commit()
    except Exception as e:
        print(f"清理测试数据失败: {e}")
        db.rollback()
    finally:
        db.close()


def create_test_excel():
    """创建测试用的 Excel 文件"""
    data = {
        '工程管理员': ['张三', '李四', '王五'],
        '工程名称': ['工程A', '工程B', '工程C'],
        '结转额（工程总投资-累计资本支出）': [100, 200, 150],
        '本年累计资本性支出': [50, 80, 60],
        '累计订单金额(列帐及时性)': [30, 40, 35],
        '累计收货金额(列帐及时性)': [20, 30, 25],
        '本月资本性支出': [10, 20, 15],
        '在建工程期末余额': [500, 600, 550],
        '工程物资': [10, 20, 15],
        '在建工程年初数': [400, 500, 450],
        '工程物资年初数': [5, 10, 8],
    }
    df = pd.DataFrame(data)
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer


def create_budget_excel(project_sheet_name="2026年新建项目明细"):
    """创建预算测试 Excel 文件。"""
    summary_df = pd.DataFrame([
        ["一级专业", "年度预算", "已占用", "预占用", "立项进度"],
        ["传输", 100, 20, 10, 0.3],
        ["合计", 100, 20, 10, 0.3],
    ])
    projects_df = pd.DataFrame([
        ["XM001", "项目A", "传输", 12, 3],
        ["XM002", "项目B", "传输", 8, 1],
    ])

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="预算下达及立项进度", index=False, header=False)
        projects_df.to_excel(writer, sheet_name=project_sheet_name, index=False, header=False)
    buffer.seek(0)
    return buffer


@pytest.fixture(scope="module")
def client():
    """创建 HTTP 客户端 - 禁用代理"""
    # 禁用代理环境变量
    old_env = {}
    for key in ['http_proxy', 'https_proxy', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']:
        old_env[key] = os.environ.pop(key, None)

    transport = httpx.HTTPTransport(local_address="127.0.0.1")
    client = httpx.Client(base_url=BASE_URL, timeout=30.0, transport=transport)

    yield client

    # 恢复环境变量
    client.close()
    for key, val in old_env.items():
        if val is not None:
            os.environ[key] = val


class TestHealthCheck:
    """健康检查测试"""

    def test_root(self, client):
        """测试根路径返回正常"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data


class TestZaigongAPI:
    """在建工程 API 测试"""

    def test_upload_excel(self, client):
        """测试上传 Excel 文件"""
        files = {'file': ('test_upload_20260321.xlsx', create_test_excel(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = client.post("/api/zaigong/upload", files=files, params={'target': 888.0})
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result
        assert "metrics" in result["data"]
        assert result["data"]["metrics"]["year_target"] == 888.0
        assert result["data"]["dashboard"]["metrics"]["yearTarget"] == 888.0

    def test_metrics(self, client):
        """测试获取指标接口"""
        response = client.get("/api/zaigong/metrics")
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "data" in result
        assert "year_target" in result["data"]

    def test_history(self, client):
        """测试获取历史记录接口"""
        response = client.get("/api/zaigong/history?limit=10")
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert isinstance(result["data"], list)

    def test_history_snapshot(self, client):
        """测试获取指定历史快照接口"""
        history_response = client.get("/api/zaigong/history?limit=10")
        assert history_response.status_code == 200
        history = history_response.json()["data"]
        assert history

        record_id = history[0]["id"]
        response = client.get(f"/api/zaigong/history/{record_id}")
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "current" in result["data"]
        assert result["data"]["current"]["id"] == record_id
        assert "dashboard" in result["data"]["current"]

    def test_compare(self, client):
        """测试对比接口"""
        response = client.get("/api/zaigong/compare")
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True


class TestAnalysisLogic:
    """分析逻辑测试（不需要服务器运行）"""

    def test_data_processing(self):
        """测试数据处理逻辑"""
        from services.analysis import load_dataframe, build_summary

        data = {
            '工程管理员': ['张三', '张三', '李四'],
            '工程名称': ['工程A', '工程B', '工程C'],
            '结转额（工程总投资-累计资本支出）': [100, 200, 150],
            '本年累计资本性支出': [50, 80, 60],
            '累计订单金额(列帐及时性)': [30, 40, 35],
            '累计收货金额(列帐及时性)': [20, 30, 25],
            '本月资本性支出': [10, 20, 15],
            '在建工程期末余额': [500, 600, 550],
            '工程物资': [10, 20, 15],
            '工程物资年初数': [5, 10, 8],
            '在建工程年初数': [400, 500, 450],
        }
        df = pd.DataFrame(data)
        df_processed = load_dataframe(df)

        # 验证数据处理
        assert len(df_processed) == 3
        assert '转固率' in df_processed.columns
        assert '待收货金额' in df_processed.columns

        # 验证汇总
        summary = build_summary(df_processed)
        assert len(summary) > 0
        assert '工程管理员' in summary.columns


class TestBudgetLogic:
    """预算逻辑测试（不需要服务器运行）。"""

    def test_budget_history_snapshot_endpoints(self, client):
        """测试预算历史记录与快照接口。"""
        files = {'file': (f'{TEST_FILE_PREFIX}budget_history_20260325.xlsx', create_budget_excel(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        upload_response = client.post("/api/budget/upload", files=files)
        assert upload_response.status_code == 200

        history_response = client.get("/api/budget/history?limit=10")
        assert history_response.status_code == 200
        history_result = history_response.json()
        assert history_result["success"] is True
        assert isinstance(history_result["data"], list)
        assert history_result["data"]

        record_id = history_result["data"][0]["id"]
        snapshot_response = client.get(f"/api/budget/history/{record_id}")
        assert snapshot_response.status_code == 200
        snapshot_result = snapshot_response.json()
        assert snapshot_result["success"] is True
        assert snapshot_result["data"]["current"]["id"] == record_id
        assert "data" in snapshot_result["data"]["current"]

    def test_budget_sheet_name_is_year_agnostic(self):
        """测试项目明细 sheet 可以兼容年份变化。"""
        from routers.budget import load_budget_sheets

        df_summary, df_projects = load_budget_sheets(
            create_budget_excel(project_sheet_name="2027年新建项目明细").getvalue()
        )

        assert len(df_summary) == 3
        assert df_projects is not None
        assert len(df_projects) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
