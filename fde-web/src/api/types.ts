// FDE 风控 Agent API 类型定义

export interface AnalyzeItem {
  material_name: string
  quantity: number
  unit_price: number
  amount?: number
}

export interface AnalyzeRequest {
  request_id: string | number
  title: string
  department: string
  applicant: string
  supplier_id: number
  supplier_name: string
  supplier_credit_score?: number
  supplier_risk_level?: string
  total_amount: number
  purpose: string
  items: AnalyzeItem[]
  first_cooperation?: boolean
  history?: Array<Record<string, unknown>>
  budget_limit?: number
}

export interface SupplierReport {
  supplier_id?: number
  supplier_name?: string
  credit_score?: number
  qualification_status?: string
  risk_level?: string
  compliance_issues?: string[]
  recommendations?: string[]
  report?: string
}

export interface AnomalyAlert {
  type: string
  level: string
  message: string
  [key: string]: unknown
}

export interface FinalResult {
  risk_score?: number
  risk_level?: string
  risk_analysis?: string
  dimensions?: Record<string, number | string | null>
  supplier_report?: SupplierReport | null
  approval_decision?: string
  decision_reasons?: string[]
  needs_human_review?: boolean
  anomaly_alerts?: AnomalyAlert[]
}

export interface AnalyzeResponse {
  request_id?: string | number
  status?: string
  final_result?: FinalResult
  [key: string]: unknown
}

// 供应商尽调（/due-diligence 独立接口）
export interface DueDiligenceNewsItem {
  title?: string
  snippet?: string
  url?: string
  source?: string
  date?: string
}

export interface DueDiligenceReport {
  supplier_id?: number
  supplier_name?: string
  news?: DueDiligenceNewsItem[]
  risk_flags?: string[]
  risk_level?: string
  report_content?: string
}

// 异常检测（/anomaly-check 独立接口）
export interface AnomalyAlertItem {
  alert_type?: string
  target_type?: string
  target_id?: string | number
  description?: string
  severity?: string
}

export interface AnomalyCheckResult {
  alerts?: AnomalyAlertItem[]
}

// 历史采购记录（异常检测输入）
export interface HistoryRecord {
  supplier_id?: number | string
  amount?: number
  created_at?: string
  title?: string
}
