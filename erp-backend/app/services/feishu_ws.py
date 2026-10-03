"""飞书长连接事件订阅客户端（官方推荐模式）。

无需公网域名、Encrypt Key、Verification Token：使用 lark-oapi SDK 建立长连接，
飞书平台自动推送事件到客户端，SDK 完成鉴权与解密。
启动后可在飞书开放平台「事件配置」点击「验证」检查连接状态。

事件协议说明（实测 2026-10-03）：
- 飞书实际推送的审批事件走 v1.0 协议（payload 顶层有 uuid、无 schema），
  SDK 会将事件类型取 event.type 后注册为 key `p1.<type>`。
- 实测到达的事件（同模板不同实例/不同时段可能推送不同类型，均需注册）：
    * `approval_instance`：审批实例状态变更，event.type=approval_instance，
      event.instance_code + event.status ∈ {APPROVED, REJECTED, ...}
    * `approval`：审批实例状态变更（另一变体），event.type=approval，
      event.instance_code + event.event ∈ {approve, reject, ...}
    * `approval_task`：审批任务状态变更，event.type=approval_task，
      event.instance_code + event.status ∈ {APPROVED, REJECTED, ...}
- 文档「审批事件列表」写的 v4 handler（key=p2.approval.instance.status_changed_v4）
  对应 v2.0 schema，与实际 v1.0 推送不匹配，故统一改用下方 p1 注册方式。
"""
import asyncio
import threading

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.approval import Approval
from app.services import approval_service

_status = {"running": False, "last_error": None, "ready": False}

# approval 事件 event 字段 → ERP 审批终态
_APPROVAL_EVENT_MAP = {
    "approve": "APPROVED",
    "reject": "REJECTED",
    "cancel": "CANCELED",
    "delete": "CANCELED",
    "withdraw": "CANCELED",
}

# approval_task 事件 status 字段已经是 ERP 终态风格，直接映射同义值
_APPROVAL_TASK_STATUS_MAP = {
    "APPROVED": "APPROVED",
    "REJECTED": "REJECTED",
    "CANCELED": "CANCELED",
}


def _build_handler():
    import lark_oapi as lark

    def on_approval_instance_v1(data: lark.event.dispatcher_handler.CustomizedEvent) -> None:
        """审批实例状态变更（p1.approval_instance）：
        data.event = {"type":"approval_instance","instance_code":..., "status":"APPROVED", ...}
        """
        evt = data.event or {}
        instance_code = evt.get("instance_code") or ""
        status = (evt.get("status") or "").upper()
        _dispatch(instance_code, status)

    def on_approval_v1(data: lark.event.dispatcher_handler.CustomizedEvent) -> None:
        """审批实例状态变更（p1.approval）：
        data.event = {"type":"approval","instance_code":..., "event":"approve", ...}
        """
        evt = data.event or {}
        instance_code = evt.get("instance_code") or ""
        status = _APPROVAL_EVENT_MAP.get(evt.get("event") or "", "")
        _dispatch(instance_code, status)

    def on_approval_task_v1(data: lark.event.dispatcher_handler.CustomizedEvent) -> None:
        """审批任务状态变更（p1.approval_task）：
        data.event = {"type":"approval_task","instance_code":..., "status":"APPROVED", ...}
        """
        evt = data.event or {}
        instance_code = evt.get("instance_code") or ""
        status = _APPROVAL_TASK_STATUS_MAP.get((evt.get("status") or "").upper(), "")
        _dispatch(instance_code, status)

    def _dispatch(instance_code: str, status: str) -> None:
        if not instance_code or not status:
            print(f"[feishu-ws] skip event: instance_code={instance_code!r} status={status!r}")
            return
        # 重要：SDK 在自身 event loop 内同步调用本回调，禁止在此使用 asyncio.run()
        # （会抛 "asyncio.run() cannot be called from a running event loop"）。
        # 改为把协程调度进同一个 running loop，并注册 done 回调打印异常。
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            try:
                asyncio.run(_process_event(instance_code, status))
            except Exception as exc:  # noqa: BLE001
                print(f"[feishu-ws] handle approval event failed (no loop): {exc!r}")
            return

        task = loop.create_task(_process_event(instance_code, status))
        task.add_done_callback(_on_process_done)

    def _on_process_done(task: asyncio.Task) -> None:
        try:
            task.result()
        except Exception as exc:  # noqa: BLE001
            print(f"[feishu-ws] handle approval event failed: {exc!r}")

    handler = (
        lark.EventDispatcherHandler.builder("", "")
        # 实测：v1.0 事件，类型可能是 approval_instance / approval / approval_task
        .register_p1_customized_event("approval_instance", on_approval_instance_v1)
        .register_p1_customized_event("approval", on_approval_v1)
        .register_p1_customized_event("approval_task", on_approval_task_v1)
        # 兼容：若开放平台切换到 v2.0 schema 推送，仍可命中
        .register_p2_approval_instance_status_changed_v4(
            lambda data: _dispatch(data.event.instance_code, data.event.status)
        )
        .build()
    )
    return handler


async def _process_event(instance_code: str, status: str) -> None:
    """处理审批事件：更新 ERP 审批与采购单状态。

    幂等保护：approval 与 approval_task 两个事件几乎同时到达同一实例，
    先到者完成终态更新，后到者若再 approve 会因状态已终态抛 409，故先跳过。
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Approval).where(Approval.feishu_instance_code == instance_code)
        )
        approval = result.scalar_one_or_none()
        if approval is None:
            print(f"[feishu-ws] no approval found for instance {instance_code}")
            return
        if approval.status in {"approved", "rejected", "escalated"}:
            print(f"[feishu-ws] skip duplicate event: instance {instance_code} already {approval.status}")
            return
        await approval_service.handle_feishu_callback(db, instance_code, status, "")


def start() -> None:
    """在后台守护线程中启动长连接客户端（start() 阻塞，故用线程）。"""
    global _status
    if _status.get("running"):
        return
    if not settings.FEISHU_APP_ID or not settings.FEISHU_APP_SECRET:
        _status = {"running": False, "last_error": "FEISHU_APP_ID/SECRET 未配置", "ready": False}
        return

    def _run() -> None:
        global _status
        try:
            # 注意：必须在子线程内首次 import lark_oapi。SDK 的 ws/client.py 在模块
            # 导入时执行 asyncio.get_event_loop()；若在 uvicorn 主线程（已有 running
            # loop）导入，会把该 loop 绑定为 ws 的 loop，随后 client.start() 调用
            # run_until_complete 会报 "This event loop is already running"。
            import lark_oapi as lark
            # 顺带导入订阅所需模块，填充 sys.modules 缓存，避免订阅线程并发
            # import lark_oapi.api 模块树触发 Python 模块锁死锁（_DeadlockError）。
            from lark_oapi.api.approval.v4 import SubscribeApprovalRequest  # noqa: F401

            client = lark.ws.Client(
                settings.FEISHU_APP_ID,
                settings.FEISHU_APP_SECRET,
                event_handler=_build_handler(),
                log_level=lark.LogLevel.INFO,
            )
            _status = {"running": True, "last_error": None, "ready": True}
            client.start()
        except Exception as exc:  # noqa: BLE001
            _status = {"running": False, "last_error": repr(exc), "ready": False}

    def _subscribe_loop() -> None:
        """连接建立后订阅审批事件，并周期性重新订阅。

        长连接模式下「保存订阅配置时客户端必须在线」：订阅调用需在客户端在线时进行，
        且订阅不随连接永久保留——客户端离线后订阅可能失效。因此启动后立即订阅，
        并每隔一段时间重订阅一次，保证审批实例状态变更事件持续推送到本客户端。
        """
        import time

        def _do_subscribe() -> None:
            if not settings.FEISHU_APPROVAL_DEFINITION_CODE:
                return
            try:
                import lark_oapi as lark
                from lark_oapi.api.approval.v4 import SubscribeApprovalRequest

                rest_client = (
                    lark.Client.builder()
                    .app_id(settings.FEISHU_APP_ID)
                    .app_secret(settings.FEISHU_APP_SECRET)
                    .log_level(lark.LogLevel.ERROR)
                    .build()
                )
                req = (
                    SubscribeApprovalRequest.builder()
                    .approval_code(settings.FEISHU_APPROVAL_DEFINITION_CODE)
                    .build()
                )
                resp = rest_client.approval.v4.approval.subscribe(req)
                print(
                    f"[feishu-ws] subscribe approval events: code={resp.code} msg={resp.msg}"
                )
            except Exception as exc:  # noqa: BLE001
                print(f"[feishu-ws] subscribe approval events failed: {exc!r}")

        # 首次连接建立后订阅（等待 ws 就绪；也给 _run 线程留足 import/连接时间）
        time.sleep(5)
        _do_subscribe()
        # 周期性重订阅（每 10 分钟），防止订阅漂移
        while True:
            time.sleep(600)
            if _status.get("running"):
                _do_subscribe()

    threading.Thread(target=_run, daemon=True, name="feishu-ws").start()
    threading.Thread(target=_subscribe_loop, daemon=True, name="feishu-ws-subscribe").start()


def status() -> dict:
    return dict(_status)
