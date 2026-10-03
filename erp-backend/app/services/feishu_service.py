"""飞书集成服务：审批流创建、消息通知。

使用 lark-oapi SDK（requirements.txt 已声明 lark-oapi，1.3.x 新版模型）。
- 未配置 FEISHU_APP_ID / FEISHU_APP_SECRET 时自动降级为 no-op（返回 None），
  便于本地开发 / 测试在无飞书凭据时不影响流程。
- 配置 FEISHU_APPROVAL_DEFINITION_CODE 后即可在飞书审批中心创建审批实例。
- 模板表单控件（用户已创建的「采购申请」模板，approval code 见 .env）：
  widget16510608596030001 采购单号 textarea
  widget16510608666360001 采购类型 radioV2
  widget16510608918180001 采购申请时间 date
  widget16510609006710001 采购明细 fieldList（子项：物料名称/规格/数量/金额）
  widget16510609389860001 附件 attachmentV2
"""
import datetime as dt
import json
from typing import List, Optional

from app.core.config import settings

# 审批模板中的审批节点（第一个需要审批人的节点）
APPROVAL_NODE_KEY = "b150009bfacabcd3e30e9fc4b10aa7db"


class FeishuService:
    """飞书开放平台封装。"""

    def __init__(self) -> None:
        self.app_id = settings.FEISHU_APP_ID
        self.app_secret = settings.FEISHU_APP_SECRET
        self.approval_code = settings.FEISHU_APPROVAL_DEFINITION_CODE
        self.ready = bool(self.app_id and self.app_secret)
        self._client = None

    def _get_client(self):
        """惰性构建 lark-oapi 客户端。"""
        if self._client is None:
            import lark_oapi as lark

            self._client = (
                lark.Client.builder()
                .app_id(self.app_id)
                .app_secret(self.app_secret)
                .log_level(lark.LogLevel.ERROR)
                .build()
            )
        return self._client

    @staticmethod
    def _build_form(request_no: str, applicant_name: str, amount: float,
                    risk_score: float, analysis: str) -> str:
        """按模板控件 id 构造 form JSON 字符串。

        控件格式遵循飞书「审批实例表单控件参数」：
        - date: RFC3339 字符串
        - number/amount: float
        - fieldList: 二维数组，每行是子控件对象数组
        """
        # 采购类型 radioV2：固定选「生产物料」（模板选项 value）
        purchase_type = "l2hj0e3h-81aosv8klcb-3"
        # 采购明细 fieldList：一行明细（物料名称/规格/数量/金额）
        detail_row = [
            {"id": "widget16510609105290001", "type": "input",
             "value": f"采购单 {request_no} 物料"},
            {"id": "widget16510609161480001", "type": "input",
             "value": f"申请人 {applicant_name}"},
            {"id": "widget16510609215120001", "type": "number", "value": 1.0},
            {"id": "widget16510609358260001", "type": "amount",
             "value": round(float(amount), 2)},
        ]
        form = [
            {"id": "widget16510608596030001", "type": "textarea", "value": request_no},
            {"id": "widget16510608666360001", "type": "radioV2", "value": purchase_type},
            {"id": "widget16510608918180001", "type": "date",
             "value": dt.datetime.now().strftime("%Y-%m-%dT00:00:00+08:00")},
            {"id": "widget16510609006710001", "type": "fieldList", "value": [detail_row]},
        ]
        return json.dumps(form, ensure_ascii=False)

    async def create_approval_instance(
        self,
        request_no: str,
        applicant_name: str,
        amount: float,
        risk_score: float,
        analysis: str,
        approver_user_ids: Optional[List[str]] = None,
        initiator_open_id: Optional[str] = None,
    ) -> Optional[str]:
        """创建飞书审批实例，返回 instance code；失败返回 None。

        - approver_user_ids: 审批人 open_id 列表（feishu_user_id 存的是 open_id）
        - initiator_open_id: 发起人 open_id；缺省时用第一个审批人作为系统代发起人
        """
        if not self.ready or not self.approval_code:
            return None
        try:
            import lark_oapi as lark
            from lark_oapi.api.approval.v4 import (
                CreateInstanceRequest,
                InstanceCreate,
                NodeApprover,
            )

            approvers = [uid for uid in (approver_user_ids or []) if uid]
            if not approvers:
                return None
            initiator = initiator_open_id or approvers[0]

            node_approver = (
                NodeApprover.builder()
                .key(APPROVAL_NODE_KEY)
                .value(approvers)
                .build()
            )
            body = (
                InstanceCreate.builder()
                .approval_code(self.approval_code)
                .open_id(initiator)
                .form(self._build_form(request_no, applicant_name, amount, risk_score, analysis))
                .title(f"采购审批 {request_no}")
                .node_approver_open_id_list([node_approver])
                .build()
            )
            req = CreateInstanceRequest.builder().request_body(body).build()
            resp = self._get_client().approval.v4.instance.create(req)
            if resp.success() and resp.data:
                return resp.data.instance_code
            if getattr(resp, "code", None) or getattr(resp, "msg", None):
                print(f"[feishu] create_approval_instance failed: code={getattr(resp, 'code', None)} msg={getattr(resp, 'msg', None)}")
            return None
        except Exception as exc:  # noqa: BLE001
            print(f"[feishu] create_approval_instance error: {exc!r}")
            return None

    async def send_message(self, user_id: str, text: str) -> bool:
        """向飞书用户发送文本消息；失败返回 False。user_id 为 open_id。"""
        if not self.ready:
            return False
        try:
            import json

            import lark_oapi as lark
            from lark_oapi.api.im.v1 import (
                CreateMessageRequest,
                CreateMessageRequestBody,
            )

            body = (
                CreateMessageRequestBody.builder()
                .receive_id(user_id)
                .msg_type("text")
                .content(json.dumps({"text": text}, ensure_ascii=False))
                .build()
            )
            req = (
                CreateMessageRequest.builder()
                .receive_id_type("open_id")
                .request_body(body)
                .build()
            )
            resp = self._get_client().im.v1.message.create(req)
            return bool(resp.success())
        except Exception:
            return False

    async def sync_contacts(self) -> None:
        """同步通讯录（骨架：供后续对接飞书通讯录使用）。"""
        return


feishu_service = FeishuService()
