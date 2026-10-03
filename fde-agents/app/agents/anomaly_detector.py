"""异常检测 Agent：识别拆分订单、频繁更换供应商等异常模式。"""
from typing import Any


class AnomalyDetector:
    """基于历史采购数据统计的异常检测（骨架）。"""

    def __init__(self) -> None:
        pass

    async def detect(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """输入历史采购记录列表，输出异常告警。"""
        alerts: list[dict[str, Any]] = []

        # 规则：同一供应商短期内多次采购（拆分订单风险）
        supplier_counts: dict[str, int] = {}
        for record in history:
            supplier = record.get("supplier_id")
            supplier_counts[str(supplier)] = supplier_counts.get(str(supplier), 0) + 1
        for supplier, count in supplier_counts.items():
            if count >= 3:
                alerts.append(
                    {
                        "alert_type": "split_order",
                        "target_type": "supplier",
                        "target_id": supplier,
                        "description": f"供应商 {supplier} 短期内出现 {count} 笔采购，疑似拆分规避审批",
                        "severity": "warning",
                    }
                )
        return alerts
