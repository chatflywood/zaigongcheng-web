#!/usr/bin/env python3
"""Build an isolated, sanitized competition demo database."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Any

import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from services.analysis import analyze  # noqa: E402


MONEY_MARKERS = (
    "金额", "投资", "支出", "余额", "资金", "订单", "收货", "资本",
    "材料费", "施工费", "管理费", "补偿", "补贴", "工程物资",
    "年初数", "增加数", "减少数", "占用",
)
MONEY_EXCLUSIONS = ("占比", "比例", "进度", "转固率", "百分比")
CODE_MARKERS = ("编码", "文号", "工号", "合同号", "订单号", "协议级项目")
PERSON_MARKERS = ("管理员", "负责人", "联系人", "提出人", "工程会计")
DEPARTMENT_MARKERS = ("部门", "利润中心", "管理单位")
UNIT_COLUMNS = ("公司名称", "建设单位", "设计单位", "监理单位", "施工单位")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=BACKEND_DIR / "data" / "analysis.db",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=BACKEND_DIR / "data" / "competition-demo.db",
    )
    parser.add_argument(
        "--excel-output",
        type=Path,
        default=PROJECT_DIR / "competition" / "demo-data" / "在建工程演示数据.xlsx",
    )
    parser.add_argument("--records", type=int, default=4)
    parser.add_argument("--budget-records", type=int, default=3)
    return parser.parse_args()


def clean_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: clean_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [clean_json(item) for item in value]
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def stable_index(value: str, modulo: int) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % modulo


def admin_alias(index: int) -> str:
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if index < len(letters):
        return f"管理员{letters[index]}"
    return f"管理员{index + 1:02d}"


class Sanitizer:
    def __init__(self) -> None:
        self.manager_map: dict[str, str] = {}
        self.project_map: dict[str, str] = {}
        self.unit_map: dict[str, str] = {}

    def manager(self, value: Any) -> str:
        text = str(value or "").strip()
        if not text or text in {"nan", "None"}:
            return "未分配"
        if text == "合计":
            return text
        if text not in self.manager_map:
            self.manager_map[text] = admin_alias(len(self.manager_map))
        return self.manager_map[text]

    def project(self, value: Any) -> str:
        text = str(value or "").strip()
        if not text or text in {"nan", "None"}:
            return "示例工程-000"
        if text not in self.project_map:
            self.project_map[text] = f"示例工程-{len(self.project_map) + 1:03d}"
        return self.project_map[text]

    def unit(self, value: Any) -> str:
        text = str(value or "").strip()
        if not text or text in {"nan", "None"}:
            return ""
        if text not in self.unit_map:
            self.unit_map[text] = f"示例单位-{len(self.unit_map) + 1:02d}"
        return self.unit_map[text]

    def row_factor(self, project_name: str) -> float:
        # 0.67-0.83 的固定扰动，同一工程各金额字段保持内部比例。
        return 0.67 + stable_index(project_name, 17) / 100

    def sanitize_dataframe(self, frame: pd.DataFrame) -> pd.DataFrame:
        # 脱敏会把部分数值列替换成演示编码，也会给整数金额加入小数扰动。
        result = frame.astype(object).copy()
        if "工程管理员" in result.columns:
            for value in result["工程管理员"].tolist():
                self.manager(value)

        original_projects = (
            result["工程名称"].fillna("").astype(str)
            if "工程名称" in result.columns
            else pd.Series([""] * len(result), index=result.index)
        )

        for row_index in result.index:
            original_project = original_projects.loc[row_index]
            factor = self.row_factor(original_project)
            project_alias = self.project(original_project)

            for column in result.columns:
                value = result.at[row_index, column]
                column_text = str(column)

                if column_text == "工程名称":
                    result.at[row_index, column] = project_alias
                elif column_text == "建设项目名称":
                    result.at[row_index, column] = f"示例建设项目-{stable_index(str(value), 999) + 1:03d}"
                elif column_text == "工程管理员":
                    result.at[row_index, column] = self.manager(value)
                elif column_text in UNIT_COLUMNS:
                    result.at[row_index, column] = self.unit(value)
                elif any(marker in column_text for marker in DEPARTMENT_MARKERS):
                    result.at[row_index, column] = "演示部门"
                elif any(marker in column_text for marker in CODE_MARKERS):
                    result.at[row_index, column] = f"DEMO-{stable_index(f'{column_text}:{value}', 999999):06d}"
                elif any(marker in column_text for marker in PERSON_MARKERS):
                    result.at[row_index, column] = self.manager(value)
                elif column_text in {"投资地域", "地市", "需求提出单位"}:
                    result.at[row_index, column] = "演示区域"
                elif self._is_money_column(column_text) and self._is_number(value):
                    result.at[row_index, column] = round(float(value) * factor, 2)

        return result

    @staticmethod
    def _is_money_column(column: str) -> bool:
        return (
            any(marker in column for marker in MONEY_MARKERS)
            and not any(marker in column for marker in MONEY_EXCLUSIONS)
        )

    @staticmethod
    def _is_number(value: Any) -> bool:
        if value is None or isinstance(value, bool):
            return False
        try:
            number = float(value)
        except (TypeError, ValueError):
            return False
        return math.isfinite(number)


def sanitize_budget_value(value: Any, key: str, sanitizer: Sanitizer) -> Any:
    if isinstance(value, list):
        return [sanitize_budget_value(item, key, sanitizer) for item in value]
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for child_key, child_value in value.items():
            if child_key == "manager":
                output[child_key] = sanitizer.manager(child_value)
            elif child_key in {"name", "project_name", "工程名称"} and key == "projects":
                output[child_key] = sanitizer.project(child_value)
            else:
                output[child_key] = sanitize_budget_value(child_value, child_key, sanitizer)
        return output
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if key in {"approval_progress", "spend_progress", "progress", "rate"}:
            return value
        return round(float(value) * 0.76, 2)
    return value


def sanitize_zaigong_records(
    source: sqlite3.Connection,
    target: sqlite3.Connection,
    sanitizer: Sanitizer,
    limit: int,
    excel_output: Path,
) -> None:
    rows = source.execute(
        """
        SELECT uploaded_at, source_filename, file_date, target_value, raw_data
        FROM zaigong_records
        WHERE raw_data IS NOT NULL AND raw_data != ''
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    rows.reverse()

    target.execute("DELETE FROM zaigong_records")
    latest_frame: pd.DataFrame | None = None
    for index, row in enumerate(rows, 1):
        raw_rows = json.loads(row["raw_data"])
        frame = sanitizer.sanitize_dataframe(pd.DataFrame(raw_rows))
        target_value = round(float(row["target_value"] or 503.0) * 0.76, 2)
        result = clean_json(analyze(frame, year_target=target_value)["data"])
        source_filename = f"在建工程演示数据-{index:02d}.xlsx"

        target.execute(
            """
            INSERT INTO zaigong_records (
                uploaded_at, source_filename, file_date, summary_data,
                metrics_data, target_value, detail_data,
                four_class_warnings, raw_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["uploaded_at"],
                source_filename,
                row["file_date"],
                json.dumps(result.get("summary", []), ensure_ascii=False),
                json.dumps(result.get("metrics", {}), ensure_ascii=False),
                target_value,
                json.dumps(result.get("dashboard", {}).get("detail", []), ensure_ascii=False),
                json.dumps(result.get("four_class_warnings", {}), ensure_ascii=False),
                json.dumps(clean_json(frame.to_dict(orient="records")), ensure_ascii=False, default=str),
            ),
        )
        latest_frame = frame

    if latest_frame is None:
        raise RuntimeError("源数据库没有可用于生成演示数据的在建工程记录")

    excel_output.parent.mkdir(parents=True, exist_ok=True)
    latest_frame.to_excel(excel_output, index=False)


def sanitize_budget_records(
    source: sqlite3.Connection,
    target: sqlite3.Connection,
    sanitizer: Sanitizer,
    limit: int,
) -> None:
    rows = source.execute(
        """
        SELECT uploaded_at, budget_data
        FROM budget_records
        WHERE budget_data IS NOT NULL AND budget_data != ''
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    rows.reverse()

    target.execute("DELETE FROM budget_records")
    for index, row in enumerate(rows, 1):
        payload = json.loads(row["budget_data"])
        sanitized = sanitize_budget_value(payload, "", sanitizer)
        target.execute(
            """
            INSERT INTO budget_records (uploaded_at, source_filename, budget_data)
            VALUES (?, ?, ?)
            """,
            (
                row["uploaded_at"],
                f"预算立项演示数据-{index:02d}.xlsx",
                json.dumps(sanitized, ensure_ascii=False),
            ),
        )


def sanitize_supporting_tables(target: sqlite3.Connection) -> None:
    target.execute("DELETE FROM app_config")
    target.executemany(
        "INSERT INTO app_config (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
        [
            ("wework_webhook_url", ""),
            ("wework_auto_push", "false"),
        ],
    )
    target.execute("UPDATE archive_records SET note = '竞赛展示文件'")

    batches = target.execute("SELECT id, amounts FROM budget_batches").fetchall()
    for row in batches:
        amounts = json.loads(row["amounts"] or "{}")
        scaled = {
            key: round(float(value or 0) * 0.76, 2)
            for key, value in amounts.items()
        }
        target.execute(
            """
            UPDATE budget_batches
            SET note = '演示预算批次', amounts = ?, notes = '{}'
            WHERE id = ?
            """,
            (json.dumps(scaled, ensure_ascii=False), row["id"]),
        )


def write_manifest(
    output: Path,
    excel_output: Path,
    sanitizer: Sanitizer,
    connection: sqlite3.Connection,
) -> None:
    manifest = {
        "database": str(output),
        "excel": str(excel_output),
        "zaigong_records": connection.execute("SELECT count(*) FROM zaigong_records").fetchone()[0],
        "budget_records": connection.execute("SELECT count(*) FROM budget_records").fetchone()[0],
        "archive_records": connection.execute("SELECT count(*) FROM archive_records").fetchone()[0],
        "manager_aliases": sorted(set(sanitizer.manager_map.values())),
        "project_alias_count": len(sanitizer.project_map),
        "archive_filenames_preserved": True,
        "webhook_cleared": True,
    }
    manifest_path = output.with_suffix(".manifest.json")
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    source_path = args.source.resolve()
    output_path = args.output.resolve()
    excel_output = args.excel_output.resolve()

    if source_path == output_path:
        raise SystemExit("输出数据库不能覆盖真实数据库")
    if not source_path.exists():
        raise SystemExit(f"找不到源数据库：{source_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, output_path)

    source = sqlite3.connect(f"file:{source_path}?mode=ro", uri=True)
    target = sqlite3.connect(output_path)
    source.row_factory = sqlite3.Row
    target.row_factory = sqlite3.Row
    sanitizer = Sanitizer()

    try:
        target.execute("PRAGMA foreign_keys = OFF")
        sanitize_zaigong_records(
            source,
            target,
            sanitizer,
            args.records,
            excel_output,
        )
        sanitize_budget_records(
            source,
            target,
            sanitizer,
            args.budget_records,
        )
        sanitize_supporting_tables(target)
        target.commit()
        target.execute("VACUUM")
        write_manifest(output_path, excel_output, sanitizer, target)
    finally:
        source.close()
        target.close()

    print(f"演示数据库：{output_path}")
    print(f"演示 Excel：{excel_output}")
    print(f"管理员别名：{len(sanitizer.manager_map)}")
    print(f"工程别名：{len(sanitizer.project_map)}")


if __name__ == "__main__":
    main()
