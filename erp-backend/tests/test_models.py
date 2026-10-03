"""ORM 模型结构冒烟测试：确认所有模型可导入、表名唯一。"""
from app.models import Base
from app.models.approval import Approval, ApprovalAction
from app.models.audit import AuditLog
from app.models.inventory import Inventory, StockMovement
from app.models.material import Material
from app.models.org import Department, Employee
from app.models.purchase import PurchaseItem, PurchaseRequest
from app.models.risk import (
    AgentDecision,
    AgentRun,
    AnomalyAlert,
    RiskAssessment,
    RiskConfig,
    SupplierDueDiligence,
)
from app.models.supplier import Supplier, SupplierRating


def test_all_tables_registered():
    tables = Base.metadata.tables
    expected = {
        "departments", "employees", "materials",
        "suppliers", "supplier_ratings",
        "purchase_requests", "purchase_items",
        "approvals", "approval_actions",
        "inventories", "stock_movements",
        "audit_logs",
        "risk_assessments", "supplier_due_diligence",
        "agent_decisions", "anomaly_alerts", "agent_runs", "risk_configs",
    }
    assert expected.issubset(set(tables.keys()))


def test_purchase_request_relationship():
    assert "items" in PurchaseRequest.__mapper__.relationships
