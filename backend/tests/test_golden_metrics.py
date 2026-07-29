# -*- coding: utf-8 -*-
"""
口径黄金样例 — 固定输入 → 精确 KPI 输出。

目的：任何转固率 / 待收货 / 预算立项 / 支出进度公式改动都必须显式改测试，
防止「看起来能跑但数已经漂了」。
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.analysis import analyze, calculate_total_rate, load_dataframe
from services.budget import analyze_budget
from services.validation import (
    build_budget_validation,
    build_zaigong_validation,
    format_validation_message,
)


def make_golden_zaigong_df() -> pd.DataFrame:
    """
    手工可复算的在建工程样例（金额单位：元）。

    行1 张三:
      本年资本 1_000_000
      订单 800_000 / 收货 600_000 → 待收货 200_000
      本月 100_000
      期末在建 300_000 / 物资 50_000
      年初在建 400_000 / 物资年初 50_000
      行转固分母 = 100万+40万+5万 = 145万
      行转固分子 = 30万+5万 = 35万
      行转固率 = 1 - 35/145 = 110/145 ≈ 0.7586206897

    行2 李四:
      本年资本 500_000
      订单 400_000 / 收货 400_000 → 待收货 0
      本月 50_000
      期末在建 200_000 / 物资 0
      年初在建 100_000 / 物资年初 0
      分母 = 50+10+0 = 60万；分子 = 20+0 = 20万
      行转固率 = 1 - 20/60 = 2/3 ≈ 0.6666666667

    合计:
      本年资本 150万 → 150.00 万元
      待收货 20万 → 20.00 万元
      本月 15万 → 15.00 万元
      综合转固分母 = 150 + 50 + 5 = 205 万（元口径: 1.5e6+0.5e6+5e4=2.05e6）
      综合转固分子 = 50 + 5 = 55 万（元: 5e5+5e4=5.5e5）
      综合转固率 = 1 - 550000/2050000 = 1 - 55/205 = 150/205 ≈ 0.7317073171
    """
    return pd.DataFrame(
        {
            "工程管理员": ["张三", "李四"],
            "工程名称": ["黄金样例工程A", "黄金样例工程B"],
            "结转额（工程总投资-累计资本支出）": [100_000, 80_000],
            "本年累计资本性支出": [1_000_000, 500_000],
            "累计订单金额(列帐及时性)": [800_000, 400_000],
            "累计收货金额(列帐及时性)": [600_000, 400_000],
            "本月资本性支出": [100_000, 50_000],
            "在建工程期末余额": [300_000, 200_000],
            "工程物资": [50_000, 0],
            "在建工程年初数": [400_000, 100_000],
            "工程物资年初数": [50_000, 0],
            # 预算支出汇总 / 四类预警可选字段
            "一级专业": ["传输", "5G"],
            "工程编码": ["GOLD001", "GOLD002"],
            "施工单位": ["一公司", "二公司"],
            "验收类型": ["一次验收", "两次验收"],
            "工程关闭状态": ["在建", "在建"],
            "初验批复日期": [None, None],
            "预转固日期": [None, None],
            "决算转固日期": [None, None],
            "终验批复日期": [None, None],
            "应预转固日期": [None, None],
            "应关闭日期": [None, None],
            "长期挂账建议关闭日期": [None, None],
            "立项批复日期": [None, None],
            "工程状态": ["在建", "在建"],
        }
    )


EXPECTED_TOTAL_RATE = 1 - 550_000 / 2_050_000  # ≈ 0.7317073170731707
EXPECTED_CAPITAL_WAN = 150.0
EXPECTED_PENDING_WAN = 20.0
EXPECTED_MONTH_WAN = 15.0
YEAR_TARGET = 500.0
EXPECTED_PROGRESS = EXPECTED_CAPITAL_WAN / YEAR_TARGET  # 0.3
EXPECTED_DEFICIT = YEAR_TARGET - EXPECTED_CAPITAL_WAN  # 350


class TestGoldenZaigongMetrics:
    def test_total_rate_hand_calculated(self):
        df = load_dataframe(make_golden_zaigong_df())
        rate = calculate_total_rate(df)
        assert rate == pytest.approx(EXPECTED_TOTAL_RATE, abs=1e-12)

    def test_analyze_metrics_locked(self):
        # 四类预警内部用 datetime.now()，与 KPI 无关；仍 patch 固定日期避免偶发
        with patch("services.analysis.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 15, 12, 0, 0)
            mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
            result = analyze(make_golden_zaigong_df(), year_target=YEAR_TARGET)

        assert result["success"] is True
        metrics = result["data"]["metrics"]
        assert metrics["total_current"] == EXPECTED_CAPITAL_WAN
        assert metrics["total_pending"] == EXPECTED_PENDING_WAN
        assert metrics["total_today_month"] == EXPECTED_MONTH_WAN
        assert metrics["total_rate"] == pytest.approx(round(EXPECTED_TOTAL_RATE, 4), abs=1e-9)
        assert metrics["year_target"] == YEAR_TARGET
        assert metrics["progress_ratio"] == pytest.approx(EXPECTED_PROGRESS, abs=1e-9)
        assert metrics["progress_pct"] == pytest.approx(30.0, abs=1e-9)
        assert metrics["deficit"] == EXPECTED_DEFICIT

        # summary 合计行
        summary = result["data"]["summary"]
        total_row = next(r for r in summary if r.get("工程管理员") == "合计")
        assert total_row["本年累计资本性支出"] == pytest.approx(EXPECTED_CAPITAL_WAN)
        assert total_row["已下单待收货"] == pytest.approx(EXPECTED_PENDING_WAN)
        assert total_row["本月资本性支出"] == pytest.approx(EXPECTED_MONTH_WAN)
        assert total_row["转固率"] == pytest.approx(EXPECTED_TOTAL_RATE, abs=1e-9)

    def test_zero_denominator_rate_is_zero(self):
        df = make_golden_zaigong_df()
        df["本年累计资本性支出"] = 0
        df["在建工程年初数"] = 0
        df["工程物资年初数"] = 0
        rate = calculate_total_rate(load_dataframe(df))
        assert rate == 0.0

    def test_validation_checksum_matches_metrics(self):
        with patch("services.analysis.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 6, 15, 12, 0, 0)
            mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
            result = analyze(make_golden_zaigong_df(), year_target=YEAR_TARGET)
        metrics = result["data"]["metrics"]
        validation = build_zaigong_validation(make_golden_zaigong_df(), metrics)
        assert validation["total_rows"] == 2
        assert validation["manager_count"] == 2
        assert validation["checksums"]["capital_wan"] == EXPECTED_CAPITAL_WAN
        assert validation["checksums"]["pending_wan"] == EXPECTED_PENDING_WAN
        assert validation["checksums"]["month_spend_wan"] == EXPECTED_MONTH_WAN
        assert validation["warnings"] == []
        assert "共 2 行" in validation["summary_text"]
        msg = format_validation_message(validation, "分析完成")
        assert msg.startswith("分析完成。")


def make_golden_budget_frames():
    """
    预算黄金样例（与 production 解析约定一致：
    summary 首行标题被 pandas 提为列名，analyze 跳过 i==0 的列名行）。

    专业:
      传输: 预算 100，占用 20，预占 10 → 小计 30，立项进度 0.3
      5G:   预算 200，占用 60，预占 0  → 小计 60，立项进度 0.3
      合计预算 300，已占用 80，预占用 10，立项进度 90/300=0.3

    spend_summary（万元）:
      传输 40，5G 20 → 年度支出 60，支出进度 60/300=0.2
    """
    summary_df = pd.DataFrame(
        [
            ["2026年预算下达及立项进度表", "", "", "", ""],
            ["一级专业", "年度预算", "已占用", "预占用", "立项进度"],
            ["传输", 100, 20, 10, 0.3],
            ["5G", 200, 60, 0, 0.3],
            ["合计", 300, 80, 10, 0.3],
        ]
    )
    # 模拟 pd.read_excel header=0：第一行变列名
    summary_df.columns = summary_df.iloc[0]
    summary_df = summary_df[1:].reset_index(drop=True)

    projects_df = pd.DataFrame(
        [
            ["项目编号", "项目名称", "工程管理员", "一级专业", "已占用", "预占用"],
            ["XM001", "基站A", "张三", "传输", 20, 10],
            ["XM002", "基站B", "李四", "5G", 60, 0],
        ]
    )
    projects_df.columns = projects_df.iloc[0]
    projects_df = projects_df[1:].reset_index(drop=True)

    spend_summary = {"传输": 40.0, "5G": 20.0}
    return summary_df, projects_df, spend_summary


class TestGoldenBudgetMetrics:
    def test_analyze_budget_locked(self):
        df_summary, df_projects, spend = make_golden_budget_frames()
        result = analyze_budget(df_summary, df_projects, spend)

        assert result["budget_total"] == 300
        assert result["occupied_total"] == 80
        assert result["preoccupied_total"] == 10
        assert result["total_used"] == 90
        assert result["approval_progress"] == pytest.approx(0.3, abs=1e-9)
        assert result["annual_spend_total"] == 60.0
        assert result["spend_progress"] == pytest.approx(0.2, abs=1e-9)

        cats = {c["name"]: c for c in result["categories"]}
        assert cats["传输"]["budget"] == 100
        assert cats["传输"]["occupied"] == 20
        assert cats["传输"]["preoccupied"] == 10
        assert cats["传输"]["subtotal"] == 30
        assert cats["传输"]["progress"] == pytest.approx(0.3, abs=1e-9)
        assert cats["传输"]["annual_spend"] == 40.0
        assert cats["传输"]["spend_progress"] == pytest.approx(0.4, abs=1e-9)

        assert cats["5G"]["budget"] == 200
        assert cats["5G"]["occupied"] == 60
        assert cats["5G"]["annual_spend"] == 20.0
        assert cats["5G"]["spend_progress"] == pytest.approx(0.1, abs=1e-9)

        assert len(result["projects"]) == 2

    def test_budget_validation_summary(self):
        df_summary, df_projects, spend = make_golden_budget_frames()
        result = analyze_budget(df_summary, df_projects, spend)
        validation = build_budget_validation(
            df_summary, df_projects, result, project_sheet_name="2026年新建项目明细"
        )
        assert validation["kind"] == "budget"
        assert validation["category_count"] == 2
        assert validation["project_count"] == 2
        assert validation["checksums"]["budget_total"] == 300
        assert validation["checksums"]["annual_spend_total"] == 60
        assert validation["checksums"]["approval_progress"] == pytest.approx(0.3)
        assert validation["checksums"]["spend_progress"] == pytest.approx(0.2)
        assert validation["warnings"] == []
