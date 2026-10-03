// ERP 前端类型定义（与 erp-backend schemas 对齐）
export interface PurchaseItem {
  id: number
  material_name: string
  spec?: string | null
  quantity: number
  unit_price?: number | null
  amount: number
  remark?: string | null
}

export interface PurchaseRequest {
  id: number
  request_no: string
  title: string
  applicant_id: number
  department_id: number
  supplier_id?: number | null
  total_amount: number
  currency: string
  status: string
  risk_score?: number | null
  risk_level?: string | null
  needs_human_review: boolean
  agent_summary?: string | null
  created_at: string
  submitted_at?: string | null
  items?: PurchaseItem[]
}

export interface PurchaseItemCreate {
  material_id?: number | null
  material_name: string
  spec?: string | null
  quantity: number
  unit_price?: number | null
  remark?: string | null
}

export interface PurchaseRequestCreate {
  title: string
  supplier_id?: number | null
  purpose?: string | null
  applicant_id?: number | null
  department_id?: number | null
  items: PurchaseItemCreate[]
}

// 组织：员工（登录用户 / 申请人）
export interface Employee {
  id: number
  employee_no: string
  name: string
  email?: string | null
  department_id?: number | null
  role: string
  approval_limit?: number | null
  status: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  employee: Employee
}

export interface Approval {
  id: number
  purchase_request_id: number
  approval_no: string
  feishu_instance_code?: string | null
  approver_id?: number | null
  status: string
  decision?: string | null
  comment?: string | null
  risk_score_snapshot?: number | null
  started_at?: string | null
  finished_at?: string | null
  timeout_at?: string | null
}

export interface ApprovalListItem extends Approval {
  purchase_title?: string | null
  purchase_amount?: number
}

export interface ApprovalAction {
  id: number
  action: string
  operator_id?: number | null
  comment?: string | null
  from_status?: string | null
  to_status?: string | null
  created_at: string
}

export interface Supplier {
  id: number
  code: string
  name: string
  contact_person?: string | null
  phone?: string | null
  email?: string | null
  qualification_status: string
  risk_level: string
  credit_score?: number | null
  first_cooperation: boolean
  status: string
}

export interface SupplierCreate {
  name: string
  contact_person?: string | null
  phone?: string | null
  email?: string | null
  address?: string | null
  tax_no?: string | null
}

export interface SupplierUpdate {
  name?: string | null
  contact_person?: string | null
  phone?: string | null
  email?: string | null
  address?: string | null
  tax_no?: string | null
  qualification_status?: string | null
  risk_level?: string | null
  credit_score?: number | null
  first_cooperation?: boolean | null
  remark?: string | null
  status?: string | null
}

export interface SupplierRiskReport {
  supplier_id: number
  supplier_name: string
  risk_level: string
  report_date: string
  business_info?: Record<string, unknown> | null
  risk_flags: unknown[]
  report_content?: string | null
}

export interface Material {
  id: number
  code: string
  name: string
  category: string
  spec?: string | null
  unit: string
  default_price?: number | null
  status: string
}

export interface MaterialCreate {
  code: string
  name: string
  category: string
  spec?: string | null
  unit: string
  default_price?: number | null
}

export interface MaterialUpdate {
  name?: string | null
  category?: string | null
  spec?: string | null
  unit?: string | null
  default_price?: number | null
  status?: string | null
}

export interface Inventory {
  id: number
  material_id: number
  warehouse: string
  quantity: number
  reserved_quantity: number
  safety_stock?: number | null
  updated_at: string
}

export interface StockMovement {
  id: number
  material_id: number
  movement_type: string
  quantity: number
  reference_type?: string | null
  reference_id?: number | null
  remark?: string | null
  created_at: string
}

export interface StockChangeIn {
  material_id: number
  movement_type: string
  quantity: number
  warehouse: string
  reference_type?: string | null
  reference_id?: number | null
  remark?: string | null
}

export interface DashboardSummary {
  total_requests: number
  approved: number
  pending_approval: number
  total_amount: number
  high_risk_requests: number
  supplier_count: number
}

export interface DashboardRiskDistribution {
  [level: string]: number
}

export interface DashboardStatusDistribution {
  [status: string]: number
}

export interface SupplierRiskItem {
  supplier_id: number
  supplier_name: string
  risk_level: string
  request_count: number
  total_amount: number
}

export interface ApprovalTimelineItem {
  date: string
  count: number
  amount: number
}

// 预算管控
export interface DepartmentBudget {
  department_id: number
  department_name: string
  department_code: string
  budget_limit: number | null
  used: number
  pending: number
  available: number | null
  utilization: number | null
  status: string // ok / over_budget / unknown
}

export interface BudgetRequestItem {
  id: number
  request_no: string
  title: string
  total_amount: number
  status: string
  budget_status?: string | null
  risk_level?: string | null
  created_at?: string | null
}

export interface DepartmentBudgetDetail extends DepartmentBudget {
  requests: BudgetRequestItem[]
}

export interface PurchaseOrderItem {
  id: number
  material_name: string
  spec?: string | null
  quantity: number
  unit_price: number | null
  amount: number
  received_quantity: number
}

export interface PurchaseOrder {
  id: number
  order_no: string
  purchase_request_id: number
  request_no: string
  supplier_id: number | null
  supplier_name: string
  department_id: number | null
  department_name: string
  total_amount: number
  status: string // draft / confirmed / partial_received / received / closed / cancelled
  remark?: string | null
  created_at: string
  items: PurchaseOrderItem[]
}

export interface ReceiptOrder {
  id: number
  receipt_no: string
  purchase_order_id: number
  order_no: string
  warehouse: string
  status: string // draft / completed
  remark?: string | null
  received_at?: string | null
  created_at: string
  items: {
    id: number
    order_item_id: number
    material_name: string
    quantity: number
  }[]
}

export interface EligibleRequest {
  id: number
  request_no: string
  title: string
  supplier_id: number | null
  supplier_name: string
  department_id: number | null
  department_name: string
  total_amount: number
  risk_level?: string | null
  budget_status?: string | null
  created_at?: string | null
}
