# -*- coding: utf-8 -*-
"""
企业微信、飞书、量子密信通知配置与推送接口
"""
from services.periods import select_source, period_of
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
PROVIDER_KEY = "notify_provider"
VALID_PROVIDERS = {"wework", "feishu", "quantum"}


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


def _mask(value: str, visible: int = 6) -> str:
    if not value:
        return ""
    if len(value) <= visible:
        return "*" * len(value)
    return "*" * (len(value) - visible) + value[-visible:]


def _detect_webhook_provider(url: str) -> str:
    if "imtwo.zdxlz.com" in url:
        return "quantum"
    return "feishu" if "open.feishu.cn" in url or "open.larksuite.com" in url else "wework"


def _get_provider(db) -> str:
    provider = _get_config(db, PROVIDER_KEY) or ""
    if provider in VALID_PROVIDERS:
        return provider
    webhook_url = _get_config(db, WEBHOOK_KEY) or ""
    return _detect_webhook_provider(webhook_url) if webhook_url else "wework"


# ── 配置接口 ──────────────────────────────────────────────

@router.get("/config")
def get_notify_config():
    """获取通知配置；所有 URL、ID 和密钥均只返回脱敏状态。"""
    db = get_db()
    try:
        url = _get_config(db, WEBHOOK_KEY) or ""
        auto_push = _get_config(db, AUTO_PUSH_KEY) or "false"
        provider = _get_provider(db)
        return {
            "success": True,
            "provider": provider,
            "configured": bool(url),
            "masked_url": _mask(url, 8),
            "auto_push": auto_push == "true",
        }
    finally:
        db.close()


@router.post("/config")
async def save_notify_config(body: dict):
    """
    保存通知配置
    body: {
      provider: wework|feishu|quantum, webhook_url: str,
      auto_push: bool
    }
    """
    webhook_url = (body.get("webhook_url") or "").strip()
    auto_push = bool(body.get("auto_push", False))

    db = get_db()
    try:
        provider = str(body.get("provider") or (_detect_webhook_provider(webhook_url) if webhook_url else _get_provider(db))).strip()
        if provider not in VALID_PROVIDERS:
            return JSONResponse(status_code=400, content={"success": False, "message": "不支持的通知平台"})

        webhook_url = webhook_url or (_get_config(db, WEBHOOK_KEY) or "")
        try:
            webhook_url = validate_webhook_url(webhook_url)
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"success": False, "message": str(exc)})
        actual_provider = _detect_webhook_provider(webhook_url)
        if actual_provider != provider:
            return JSONResponse(status_code=400, content={"success": False, "message": "Webhook 地址与所选平台不匹配"})
        _set_config(db, WEBHOOK_KEY, webhook_url)

        _set_config(db, PROVIDER_KEY, provider)
        _set_config(db, AUTO_PUSH_KEY, "true" if auto_push else "false")
        return {"success": True, "message": "配置已保存"}
    finally:
        db.close()


@router.post("/config/clear")
def clear_notify_config():
    """清除全部通知平台凭证。"""
    db = get_db()
    try:
        keys = [WEBHOOK_KEY, AUTO_PUSH_KEY, PROVIDER_KEY]
        rows = db.query(AppConfig).filter(AppConfig.key.in_(keys)).all()
        for row in rows:
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
        provider = _get_provider(db)
        webhook_url = _get_config(db, WEBHOOK_KEY) or ""
        if not webhook_url:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "尚未配置通知渠道，请先打开通知设置完成配置"},
            )
        try:
            webhook_url = validate_webhook_url(webhook_url)
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"success": False, "message": str(exc)})
        if _detect_webhook_provider(webhook_url) != provider:
            return JSONResponse(status_code=400, content={"success": False, "message": "Webhook 地址与所选平台不匹配"})

        record = db.query(ZaigongRecord).filter(ZaigongRecord.id == record_id).first()
        if not record:
            return JSONResponse(status_code=404, content={"success": False, "message": "记录不存在"})

        snapshot = build_dashboard_snapshot(record)

        # 加载最新预算数据
        budget_record = select_source(db, BudgetRecord, period_of(record).get("business_date"))
        budget_data = json.loads(budget_record.budget_data) if budget_record and budget_record.budget_data else None

        try:
            result = await push_record(webhook_url, snapshot, budget_data)
        except Exception as exc:
            logger.exception("手动消息推送失败")
            return JSONResponse(
                status_code=502,
                content={"success": False, "message": f"消息推送失败：{type(exc).__name__}"},
            )

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
    """向指定通知渠道发送测试消息；未传的字段使用已保存配置。"""
    webhook_url = (body.get("webhook_url") or "").strip()
    db = get_db()
    try:
        provider = str(body.get("provider") or (_detect_webhook_provider(webhook_url) if webhook_url else _get_provider(db))).strip()
        if provider not in VALID_PROVIDERS:
            return JSONResponse(status_code=400, content={"success": False, "message": "不支持的通知平台"})
        webhook_url = webhook_url or (_get_config(db, WEBHOOK_KEY) or "")
        if not webhook_url:
            return JSONResponse(status_code=400, content={"success": False, "message": "请先输入 Webhook URL"})
        try:
            webhook_url = validate_webhook_url(webhook_url)
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"success": False, "message": str(exc)})
        if _detect_webhook_provider(webhook_url) != provider:
            return JSONResponse(status_code=400, content={"success": False, "message": "Webhook 地址与所选平台不匹配"})
    finally:
        db.close()

    try:
        result = await send_test(webhook_url)
        if result.get("errcode") == 0 or result.get("code") == 0:
            return {"success": True, "message": "测试消息发送成功，请在所选平台中查看"}
        else:
            errmsg = result.get("errmsg") or result.get("msg") or "未知错误"
            return JSONResponse(
                status_code=502,
                content={"success": False, "message": f"平台返回错误：{errmsg}"},
            )
    except Exception as e:
        logger.exception("消息推送请求失败")
        return JSONResponse(status_code=502, content={"success": False, "message": f"消息推送失败：{type(e).__name__}"})
