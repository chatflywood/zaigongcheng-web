# -*- coding: utf-8 -*-
"""
企业微信通知配置与推送接口
"""
import json
import logging
from typing import Optional
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from models import AppConfig, ZaigongRecord, BudgetRecord, get_db
from routers.analysis import build_dashboard_snapshot
from services.notify import push_record, send_test, validate_webhook_url

router = APIRouter()

logger = logging.getLogger(__name__)

WEBHOOK_KEY = "wework_webhook_url"
AUTO_PUSH_KEY = "wework_auto_push"


def _get_config(db, key: str) -> Optional[str]:
    row = db.query(AppConfig).filter(AppConfig.key == key).first()
    return row.value if row else None


def _set_config(db, key: str, value: str):
    row = db.query(AppConfig).filter(AppConfig.key == key).first()
    if row:
        row.value = value
    else:
        db.add(AppConfig(key=key, value=value))
    db.commit()


# ── 配置接口 ──────────────────────────────────────────────

@router.get("/config")
def get_notify_config():
    """获取通知配置（webhook URL 脱敏展示）"""
    db = get_db()
    try:
        url = _get_config(db, WEBHOOK_KEY) or ""
        auto_push = _get_config(db, AUTO_PUSH_KEY) or "false"
        # 脱敏：只显示末尾 8 位
        masked = ("*" * (len(url) - 8) + url[-8:]) if len(url) > 8 else ("*" * len(url))
        return {
            "success": True,
            "configured": bool(url),
            "masked_url": masked if url else "",
            "auto_push": auto_push == "true",
        }
    finally:
        db.close()


@router.post("/config")
async def save_notify_config(body: dict):
    """
    保存通知配置
    body: { webhook_url: str, auto_push: bool }
    """
    webhook_url = (body.get("webhook_url") or "").strip()
    auto_push = bool(body.get("auto_push", False))

    if webhook_url:
        try:
            webhook_url = validate_webhook_url(webhook_url)
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"success": False, "message": str(exc)})

    db = get_db()
    try:
        if webhook_url:
            _set_config(db, WEBHOOK_KEY, webhook_url)
        _set_config(db, AUTO_PUSH_KEY, "true" if auto_push else "false")
        return {"success": True, "message": "配置已保存"}
    finally:
        db.close()


@router.post("/config/clear")
def clear_notify_config():
    """清除 webhook URL"""
    db = get_db()
    try:
        row = db.query(AppConfig).filter(AppConfig.key == WEBHOOK_KEY).first()
        if row:
            db.delete(row)
            db.commit()
        return {"success": True, "message": "已清除"}
    finally:
        db.close()


# ── 推送接口 ──────────────────────────────────────────────

@router.post("/push/{record_id}")
async def manual_push(record_id: int):
    """手动推送指定记录的数据播报"""
    db = get_db()
    try:
        webhook_url = _get_config(db, WEBHOOK_KEY) or ""
        if not webhook_url:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "尚未配置 Webhook，请先点右上角 🔔 填写飞书或企业微信的 Webhook 地址"},
            )
        try:
            webhook_url = validate_webhook_url(webhook_url)
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"success": False, "message": str(exc)})

        record = db.query(ZaigongRecord).filter(ZaigongRecord.id == record_id).first()
        if not record:
            return JSONResponse(status_code=404, content={"success": False, "message": "记录不存在"})

        snapshot = build_dashboard_snapshot(record)

        # 加载最新预算数据
        budget_record = db.query(BudgetRecord).order_by(BudgetRecord.id.desc()).first()
        budget_data = json.loads(budget_record.budget_data) if budget_record and budget_record.budget_data else None

        result = await push_record(webhook_url, snapshot, budget_data)

        if result.get("errcode") == 0 or result.get("code") == 0:
            return {"success": True, "message": "推送成功"}
        else:
            errmsg = result.get("errmsg") or result.get("msg") or "未知错误"
            return JSONResponse(
                status_code=502,
                content={"success": False, "message": f"平台返回错误：{errmsg}"},
            )
    finally:
        db.close()


@router.post("/test")
async def test_push(body: dict):
    """向指定 webhook 发送测试消息；若不传 webhook_url 则使用已保存的配置"""
    webhook_url = (body.get("webhook_url") or "").strip()
    if not webhook_url:
        db = get_db()
        try:
            row = db.query(AppConfig).filter(AppConfig.key == WEBHOOK_KEY).first()
            webhook_url = row.value if row else ""
        finally:
            db.close()
    if not webhook_url:
        return JSONResponse(status_code=400, content={"success": False, "message": "请先输入 Webhook URL"})
    try:
        webhook_url = validate_webhook_url(webhook_url)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"success": False, "message": str(exc)})

    try:
        result = await send_test(webhook_url)
        # 企业微信 errcode=0，飞书 code=0，均视为成功
        if result.get("errcode") == 0 or result.get("code") == 0:
            return {"success": True, "message": "测试消息发送成功，请在飞书/企业微信中查看"}
        else:
            errmsg = result.get("errmsg") or result.get("msg") or "未知错误"
            return JSONResponse(
                status_code=502,
                content={"success": False, "message": f"平台返回错误：{errmsg}"},
            )
    except Exception as e:
        logger.exception("消息推送请求失败")
        return JSONResponse(status_code=502, content={"success": False, "message": f"消息推送失败：{type(e).__name__}"})
