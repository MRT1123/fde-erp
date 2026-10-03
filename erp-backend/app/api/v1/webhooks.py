"""飞书 Webhook 回调 API。

包含两类回调入口：
- POST /feishu-event   飞书「原生事件订阅」入口：支持 URL 验证(challenge)、Verification Token 校验、
                        Encrypt Key AES 解密，处理 approval.instance.status.changed 审批状态变更事件。
- POST /feishu-approval 兼容模式回调入口：简单的 JSON 直调（供调试/手动触发，无签名校验）。
"""
import json

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.api.deps import DbSession
from app.core.config import settings
from app.services import approval_service, feishu_ws

router = APIRouter()


class FeishuApprovalEvent(BaseModel):
    code: str  # 飞书审批实例 code
    status: str  # APPROVED / REJECTED / CANCELED
    comment: str = ""


def _decrypt_body(raw: bytes) -> dict:
    """解密飞书事件推送 body，返回解析后的 JSON。

    配置了 FEISHU_ENCRYPT_KEY 时按飞书 AES 协议解密；未配置时按明文 JSON 解析。
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="invalid body encoding")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="invalid json body")

    encrypt = data.get("encrypt")
    if encrypt:
        if not settings.FEISHU_ENCRYPT_KEY:
            raise HTTPException(status_code=400, detail="encrypt key not configured")
        try:
            from lark_oapi.core.utils import AESCipher

            plain = AESCipher(settings.FEISHU_ENCRYPT_KEY).decrypt_str(encrypt)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"decrypt failed: {exc!r}") from exc
        try:
            data = json.loads(plain)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="invalid decrypted payload")
    return data


@router.post("/feishu-event")
async def feishu_event_callback(request: Request, db: DbSession):
    """飞书原生事件订阅回调。

    支持 url_verification（返回 challenge）与 approval.instance.status.changed 事件。
    """
    raw = await request.body()
    data = _decrypt_body(raw)

    # Verification Token 校验（配置后生效）
    token = data.get("header", {}).get("token") or data.get("token")
    if settings.FEISHU_VERIFICATION_TOKEN and token:
        if token != settings.FEISHU_VERIFICATION_TOKEN:
            raise HTTPException(status_code=403, detail="invalid verification token")

    # URL 验证：飞书后台保存回调地址时校验
    if data.get("type") == "url_verification":
        challenge = data.get("challenge")
        if challenge is None:
            raise HTTPException(status_code=400, detail="challenge missing")
        return {"challenge": challenge}

    # 审批实例状态变更事件
    event_type = data.get("header", {}).get("event_type", "")
    if event_type == "approval.instance.status.changed":
        evt = data.get("event", {})
        instance_code = evt.get("instance_code")
        status = evt.get("status")  # APPROVED / REJECTED / CANCELED
        comment = evt.get("comment") or ""
        if not instance_code or not status:
            raise HTTPException(status_code=400, detail="instance_code or status missing")
        try:
            await approval_service.handle_feishu_callback(db, instance_code, status, comment)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"code": 0, "msg": "success"}


@router.get("/feishu-ws-status")
async def feishu_ws_status():
    """飞书长连接事件订阅客户端状态（用于验证连接是否成功）。"""
    return feishu_ws.status()


@router.post("/feishu-approval")
async def feishu_approval_callback(event: FeishuApprovalEvent, db: DbSession):
    """飞书审批状态回调（兼容模式）：更新 ERP 审批状态与采购单状态。"""
    try:
        await approval_service.handle_feishu_callback(db, event.code, event.status, event.comment)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"code": 0, "message": "ok"}
