"""Engineering compliance lists and separately persisted verification results."""
import io
import json
from datetime import date, datetime
from typing import Literal
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, model_validator

from models import AppConfig, ZaigongRecord, get_db
from services.compliance import CHECKS, build_compliance
from services.periods import period_of

router = APIRouter()
PREFIX = "compliance:"


class ReviewInput(BaseModel):
    status: Literal["待核实", "已核实正常", "发现问题"]
    reviewed_on: date | None = None
    note: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def require_review_date(self):
        if self.status != "待核实" and self.reviewed_on is None:
            raise ValueError("请选择核实日期")
        return self


def load_compliance(db, record_id):
    record = db.query(ZaigongRecord).filter(ZaigongRecord.id == record_id).first()
    if not record:
        raise HTTPException(404, "记录不存在")
    if not record.raw_data:
        raise HTTPException(422, "该版本没有原始工程明细，请重新上传在建工程报表")
    # Editing a target creates a new version, not a new engineering upload.
    source = record
    visited = {record.id}
    while period_of(source).get("revision_reason") == "target_change":
        parent_id = period_of(source).get("parent_record_id")
        if not parent_id or parent_id in visited:
            raise HTTPException(422, "无法确认原始上传日期，请核对版本来源")
        visited.add(parent_id)
        source = db.query(ZaigongRecord).filter(ZaigongRecord.id == parent_id).first()
        if source is None:
            raise HTTPException(422, "原始上传版本已删除，无法确认核查区间")
    reviews = {}
    for config in db.query(AppConfig).filter(AppConfig.key.startswith(PREFIX)).all():
        _, kind, code = config.key.split(":", 2)
        reviews[(kind, code)] = json.loads(config.value)
    try:
        data = build_compliance(json.loads(record.raw_data), source.uploaded_at, reviews)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {**data, "record_id": record.id, "source_record_id": source.id,
            "source_filename": record.source_filename}


@router.get("/compliance/{record_id}")
async def get_compliance(record_id: int):
    db = get_db()
    try:
        return {"success": True, "data": load_compliance(db, record_id)}
    finally:
        db.close()


@router.put("/compliance/{record_id}/{kind}/{code}")
async def save_compliance_review(record_id: int, kind: str, code: str, review: ReviewInput):
    if kind not in CHECKS or not code or len(code) > 64:
        raise HTTPException(422, "核查类型或工程编码无效")
    db = get_db()
    try:
        data = load_compliance(db, record_id)
        if not any(item["code"] == code for item in data["checks"][kind]["items"]):
            raise HTTPException(404, "该工程不在当前核查范围内")
        key = f"{PREFIX}{kind}:{code}"
        config = db.query(AppConfig).filter(AppConfig.key == key).first()
        if config is None:
            config = AppConfig(key=key)
            db.add(config)
        config.value = json.dumps({
            "status": review.status,
            "reviewed_on": review.reviewed_on.isoformat() if review.reviewed_on else "",
            "note": review.note.strip(), "record_id": record_id,
        }, ensure_ascii=False)
        config.updated_at = datetime.now()
        db.commit()
        return {"success": True, "data": load_compliance(db, record_id)}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.get("/compliance/{record_id}/export")
async def export_compliance(record_id: int):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from routers.analysis import neutralize_spreadsheet_formula

    db = get_db()
    try:
        data = load_compliance(db, record_id)
    finally:
        db.close()
    workbook = Workbook()
    workbook.remove(workbook.active)
    for kind, check in data["checks"].items():
        sheet = workbook.create_sheet(check["label"])
        headers = ["工程编码", "工程名称", "工程管理员", "项目类型", CHECKS[kind]["field"],
                   "工程状态", "施工单位"]
        if kind == "safety":
            headers += ["安全生产费（本年，元）", "累计安全生产费（元）"]
        headers += ["核实状态", "核实日期", "备注"]
        sheet.append([f"工程合规核查：{check['label']}"])
        sheet.append([f"核查区间：{data['start_date']} 至 {data['end_date']}（含首尾）"])
        sheet.append([neutralize_spreadsheet_formula(f"来源：{data['source_filename']}")])
        sheet.append(["安全生产费为账面金额，实际支付需核实。核实结果为当前登记结果。"
                      if kind == "safety" else "按首次设计批复日期筛选，核实结果为当前登记结果。"])
        if kind == "safety":
            sheet.append([f"剔除单纯购置项目（含单纯性购置项目）及零星购置项目，共{check['excluded']}项。"])
        else:
            sheet.append(["最近设计变更批复日期不参与筛选。"])
        sheet.append(headers)
        for item in check["items"]:
            values = [item["code"], item["name"], item["manager"], item["project_type"],
                      date.fromisoformat(item["key_date"]), item["project_status"], item["construction_unit"]]
            if kind == "safety":
                values += [item["current_safety_fee"], item["total_safety_fee"]]
            values += [item["status"], date.fromisoformat(item["reviewed_on"]) if item["reviewed_on"] else None,
                       item["note"]]
            sheet.append([neutralize_spreadsheet_formula(value) for value in values])
        sheet.sheet_view.showGridLines = False
        sheet.freeze_panes = "C7"
        sheet.auto_filter.ref = f"A6:{get_column_letter(len(headers))}{sheet.max_row}"
        for index, header in enumerate(headers, 1):
            sheet.column_dimensions[get_column_letter(index)].width = 65 if index == 2 else 40 if header in {"施工单位", "备注"} else 23
        for row in sheet:
            for cell in row:
                cell.font = Font(name="微软雅黑", size=10, color="1F1D18")
                cell.alignment = Alignment(vertical="center", wrap_text=True)
                if isinstance(cell.value, date):
                    cell.number_format = "yyyy-mm-dd"
                elif isinstance(cell.value, (float, int)):
                    cell.number_format = "#,##0.00"
            sheet.row_dimensions[row[0].row].height = 36 if row[0].row >= 6 else 24
        for cell in sheet[6]:
            cell.fill = PatternFill("solid", fgColor="44648A")
            cell.font = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
        sheet["A1"].font = Font(name="微软雅黑", size=14, bold=True)
    buffer = io.BytesIO()
    workbook.save(buffer)
    filename = f"工程合规核查_{data['end_date']}.xlsx"
    return StreamingResponse(io.BytesIO(buffer.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"})
