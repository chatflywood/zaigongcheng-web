# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from models import BatchSpecialty, BudgetBatch, get_db
from datetime import datetime
import json

router = APIRouter()


# ── Pydantic schemas ─────────────────────────────────────────────

class SpecialtyCreate(BaseModel):
    name: str
    sort_order: int = 0


class SpecialtyUpdate(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None


class BatchCreate(BaseModel):
    batch_date: str          # "2026-01-08"
    note: str = ""
    amounts: dict = {}       # {专业名: 金额}
    notes: dict = {}         # {专业名: "批注文字"}


class BatchUpdate(BaseModel):
    batch_date: Optional[str] = None
    note: Optional[str] = None
    amounts: Optional[dict] = None
    notes: Optional[dict] = None


# ── 专业管理 ─────────────────────────────────────────────────────

@router.get("/specialties")
def list_specialties():
    db = get_db()
    try:
        rows = db.query(BatchSpecialty).order_by(BatchSpecialty.sort_order, BatchSpecialty.id).all()
        return [{"id": r.id, "name": r.name, "sort_order": r.sort_order} for r in rows]
    finally:
        db.close()


@router.post("/specialties")
def add_specialty(body: SpecialtyCreate):
    db = get_db()
    try:
        exists = db.query(BatchSpecialty).filter(BatchSpecialty.name == body.name).first()
        if exists:
            raise HTTPException(400, f"专业「{body.name}」已存在")
        s = BatchSpecialty(name=body.name, sort_order=body.sort_order)
        db.add(s)
        db.commit()
        db.refresh(s)
        return {"id": s.id, "name": s.name, "sort_order": s.sort_order}
    finally:
        db.close()


@router.put("/specialties/{sid}")
def update_specialty(sid: int, body: SpecialtyUpdate):
    db = get_db()
    try:
        s = db.query(BatchSpecialty).filter(BatchSpecialty.id == sid).first()
        if not s:
            raise HTTPException(404, "专业不存在")
        if body.name is not None:
            dup = db.query(BatchSpecialty).filter(
                BatchSpecialty.name == body.name, BatchSpecialty.id != sid
            ).first()
            if dup:
                raise HTTPException(400, f"专业「{body.name}」已存在")
            # 同步更新所有批次中该专业名的 key
            old_name = s.name
            batches = db.query(BudgetBatch).all()
            for b in batches:
                amounts = json.loads(b.amounts or '{}')
                if old_name in amounts:
                    amounts[body.name] = amounts.pop(old_name)
                    b.amounts = json.dumps(amounts, ensure_ascii=False)
                batch_notes = json.loads(b.notes or '{}')
                if old_name in batch_notes:
                    batch_notes[body.name] = batch_notes.pop(old_name)
                    b.notes = json.dumps(batch_notes, ensure_ascii=False)
            s.name = body.name
        if body.sort_order is not None:
            s.sort_order = body.sort_order
        db.commit()
        return {"id": s.id, "name": s.name, "sort_order": s.sort_order}
    finally:
        db.close()


@router.delete("/specialties/{sid}")
def delete_specialty(sid: int):
    db = get_db()
    try:
        s = db.query(BatchSpecialty).filter(BatchSpecialty.id == sid).first()
        if not s:
            raise HTTPException(404, "专业不存在")
        db.delete(s)
        db.commit()
        return {"ok": True}
    finally:
        db.close()


@router.put("/specialties/reorder/batch")
def reorder_specialties(order: list[dict]):
    """批量更新排序: [{id, sort_order}, ...]"""
    db = get_db()
    try:
        for item in order:
            s = db.query(BatchSpecialty).filter(BatchSpecialty.id == item["id"]).first()
            if s:
                s.sort_order = item["sort_order"]
        db.commit()
        return {"ok": True}
    finally:
        db.close()


# ── 批次 CRUD ────────────────────────────────────────────────────

def _batch_to_dict(b: BudgetBatch):
    return {
        "id": b.id,
        "batch_date": b.batch_date,
        "note": b.note or "",
        "amounts": json.loads(b.amounts or '{}'),
        "notes": json.loads(b.notes or '{}'),
        "created_at": b.created_at.isoformat() if b.created_at else None,
        "updated_at": b.updated_at.isoformat() if b.updated_at else None,
    }


@router.get("/batches")
def list_batches():
    db = get_db()
    try:
        # 专业列表（有序）
        specialties = [
            r.name for r in db.query(BatchSpecialty)
            .order_by(BatchSpecialty.sort_order, BatchSpecialty.id).all()
        ]
        batches = db.query(BudgetBatch).order_by(BudgetBatch.batch_date).all()
        rows = [_batch_to_dict(b) for b in batches]

        # 计算合计行
        totals = {}
        for r in rows:
            for k, v in r["amounts"].items():
                totals[k] = round(totals.get(k, 0) + (v or 0), 6)

        return {"specialties": specialties, "batches": rows, "totals": totals}
    finally:
        db.close()


@router.post("/batches")
def create_batch(body: BatchCreate):
    db = get_db()
    try:
        b = BudgetBatch(
            batch_date=body.batch_date,
            note=body.note,
            amounts=json.dumps(body.amounts, ensure_ascii=False),
            notes=json.dumps(body.notes, ensure_ascii=False),
        )
        db.add(b)
        db.commit()
        db.refresh(b)
        return _batch_to_dict(b)
    finally:
        db.close()


@router.put("/batches/{bid}")
def update_batch(bid: int, body: BatchUpdate):
    db = get_db()
    try:
        b = db.query(BudgetBatch).filter(BudgetBatch.id == bid).first()
        if not b:
            raise HTTPException(404, "批次不存在")
        if body.batch_date is not None:
            b.batch_date = body.batch_date
        if body.note is not None:
            b.note = body.note
        if body.amounts is not None:
            b.amounts = json.dumps(body.amounts, ensure_ascii=False)
        if body.notes is not None:
            b.notes = json.dumps(body.notes, ensure_ascii=False)
        b.updated_at = datetime.now()
        db.commit()
        return _batch_to_dict(b)
    finally:
        db.close()


@router.delete("/batches/{bid}")
def delete_batch(bid: int):
    db = get_db()
    try:
        b = db.query(BudgetBatch).filter(BudgetBatch.id == bid).first()
        if not b:
            raise HTTPException(404, "批次不存在")
        db.delete(b)
        db.commit()
        return {"ok": True}
    finally:
        db.close()
