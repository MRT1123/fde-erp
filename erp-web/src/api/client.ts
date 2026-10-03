// ERP API 客户端
import axios from 'axios'
import type {
  Approval,
  ApprovalAction,
  ApprovalListItem,
  ApprovalTimelineItem,
  DashboardRiskDistribution,
  DashboardStatusDistribution,
  DashboardSummary,
  DepartmentBudget,
  DepartmentBudgetDetail,
  EligibleRequest,
  Employee,
  Inventory,
  LoginResponse,
  Material,
  MaterialCreate,
  MaterialUpdate,
  PurchaseOrder,
  PurchaseRequest,
  PurchaseRequestCreate,
  StockChangeIn,
  StockMovement,
  Supplier,
  SupplierCreate,
  SupplierRiskItem,
  SupplierRiskReport,
  SupplierUpdate,
} from './types'

const baseURL = import.meta.env.VITE_ERP_API_BASE || '/api/v1'

const http = axios.create({
  baseURL,
  timeout: 30000,
})

// 认证与组织
export async function fetchEmployees(): Promise<Employee[]> {
  const { data } = await http.get<Employee[]>('/employees')
  return data
}

export async function login(employee_no: string): Promise<LoginResponse> {
  const { data } = await http.post<LoginResponse>('/auth/login', { employee_no })
  return data
}

// 采购
export async function fetchPurchaseRequests(): Promise<PurchaseRequest[]> {
  const { data } = await http.get<PurchaseRequest[]>('/purchase-requests')
  return data
}

export async function fetchPurchaseRequest(id: number): Promise<PurchaseRequest> {
  const { data } = await http.get<PurchaseRequest>(`/purchase-requests/${id}`)
  return data
}

export async function createPurchaseRequest(payload: PurchaseRequestCreate): Promise<PurchaseRequest> {
  const { data } = await http.post<PurchaseRequest>('/purchase-requests', payload)
  return data
}

export async function submitPurchaseRequest(id: number): Promise<PurchaseRequest> {
  const { data } = await http.post<PurchaseRequest>(`/purchase-requests/${id}/submit`)
  return data
}

export async function withdrawPurchaseRequest(id: number): Promise<PurchaseRequest> {
  const { data } = await http.post<PurchaseRequest>(`/purchase-requests/${id}/withdraw`)
  return data
}

// 审批
export async function fetchApprovals(): Promise<ApprovalListItem[]> {
  const { data } = await http.get<ApprovalListItem[]>('/approvals')
  return data
}

export async function fetchApproval(id: number): Promise<Approval> {
  const { data } = await http.get<Approval>(`/approvals/${id}`)
  return data
}

export async function approveApproval(id: number, comment?: string): Promise<Approval> {
  const { data } = await http.post<Approval>(`/approvals/${id}/approve`, { comment })
  return data
}

export async function rejectApproval(id: number, reason: string): Promise<Approval> {
  const { data } = await http.post<Approval>(`/approvals/${id}/reject`, { reason })
  return data
}

export async function fetchApprovalActions(id: number): Promise<ApprovalAction[]> {
  const { data } = await http.get<ApprovalAction[]>(`/approvals/${id}/actions`)
  return data
}

// 供应商
export async function fetchSuppliers(): Promise<Supplier[]> {
  const { data } = await http.get<Supplier[]>('/suppliers')
  return data
}

export async function createSupplier(payload: SupplierCreate): Promise<Supplier> {
  const { data } = await http.post<Supplier>('/suppliers', payload)
  return data
}

export async function updateSupplier(id: number, payload: SupplierUpdate): Promise<Supplier> {
  const { data } = await http.put<Supplier>(`/suppliers/${id}`, payload)
  return data
}

export async function fetchSupplierRiskReport(id: number): Promise<SupplierRiskReport> {
  const { data } = await http.get<SupplierRiskReport>(`/suppliers/${id}/risk-report`)
  return data
}

// 物料
export async function fetchMaterials(): Promise<Material[]> {
  const { data } = await http.get<Material[]>('/materials')
  return data
}

export async function createMaterial(payload: MaterialCreate): Promise<Material> {
  const { data } = await http.post<Material>('/materials', payload)
  return data
}

export async function updateMaterial(id: number, payload: MaterialUpdate): Promise<Material> {
  const { data } = await http.put<Material>(`/materials/${id}`, payload)
  return data
}

// 库存
export async function fetchInventory(): Promise<Inventory[]> {
  const { data } = await http.get<Inventory[]>('/inventory')
  return data
}

export async function fetchStockMovements(): Promise<StockMovement[]> {
  const { data } = await http.get<StockMovement[]>('/inventory/movements')
  return data
}

export async function createStockChange(payload: StockChangeIn): Promise<StockMovement> {
  const { data } = await http.post<StockMovement>('/inventory/changes', payload)
  return data
}

// 预算管控
export async function fetchBudgetDepartments(): Promise<DepartmentBudget[]> {
  const { data } = await http.get<DepartmentBudget[]>('/budget/departments')
  return data
}

export async function fetchBudgetDepartmentDetail(id: number): Promise<DepartmentBudgetDetail> {
  const { data } = await http.get<DepartmentBudgetDetail>(`/budget/departments/${id}`)
  return data
}

export async function updateBudgetLimit(id: number, budget_limit: number): Promise<DepartmentBudget> {
  const { data } = await http.put<DepartmentBudget>(`/budget/departments/${id}/limit`, { budget_limit })
  return data
}

// 看板
// 采购订单
export async function fetchPurchaseOrders(): Promise<PurchaseOrder[]> {
  const { data } = await http.get<PurchaseOrder[]>('/purchase-orders')
  return data
}

export async function fetchPurchaseOrderDetail(id: number): Promise<PurchaseOrder> {
  const { data } = await http.get<PurchaseOrder>(`/purchase-orders/${id}`)
  return data
}

export async function fetchEligibleRequests(): Promise<EligibleRequest[]> {
  const { data } = await http.get<EligibleRequest[]>('/purchase-orders/eligible')
  return data
}

export async function createPurchaseOrderFromRequest(requestId: number, remark?: string): Promise<PurchaseOrder> {
  const { data } = await http.post<PurchaseOrder>(`/purchase-orders/from-request/${requestId}`, { remark })
  return data
}

export async function receivePurchaseOrder(
  orderId: number,
  warehouse: string,
  items: { order_item_id: number; quantity: number }[],
  remark?: string,
): Promise<PurchaseOrder> {
  const { data } = await http.post<PurchaseOrder>(`/purchase-orders/${orderId}/receive`, { warehouse, items, remark })
  return data
}

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const { data } = await http.get<DashboardSummary>('/dashboard/summary')
  return data
}

export async function fetchRiskDistribution(): Promise<DashboardRiskDistribution> {
  const { data } = await http.get<DashboardRiskDistribution>('/dashboard/risk-distribution')
  return data
}

export async function fetchStatusDistribution(): Promise<DashboardStatusDistribution> {
  const { data } = await http.get<DashboardStatusDistribution>('/dashboard/status-distribution')
  return data
}

export async function fetchSupplierRisk(): Promise<SupplierRiskItem[]> {
  const { data } = await http.get<SupplierRiskItem[]>('/dashboard/supplier-risk')
  return data
}

export async function fetchApprovalTimeline(): Promise<ApprovalTimelineItem[]> {
  const { data } = await http.get<ApprovalTimelineItem[]>('/dashboard/approval-timeline')
  return data
}

export { http }
