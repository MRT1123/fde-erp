import axios from 'axios'
import type { AnalyzeRequest, AnalyzeResponse, AnomalyCheckResult, DueDiligenceReport, HistoryRecord } from './types'

const http = axios.create({
  baseURL: '/fde',
  timeout: 120000,
})

export async function analyzeRisk(payload: AnalyzeRequest): Promise<AnalyzeResponse> {
  const { request_id, history, ...purchase } = payload
  const body = {
    request_id,
    purchase_request: { ...purchase },
    history: history || [],
  }
  const { data } = await http.post<AnalyzeResponse>('/analyze', body)
  return data
}

export async function health(): Promise<Record<string, unknown>> {
  const { data } = await http.get<Record<string, unknown>>('/health')
  return data
}

export async function dueDiligence(supplier_id: number, supplier_name: string): Promise<DueDiligenceReport> {
  const { data } = await http.post<DueDiligenceReport>('/due-diligence', {
    supplier_id,
    supplier_name,
  })
  return data
}

export async function anomalyCheck(history: HistoryRecord[]): Promise<AnomalyCheckResult> {
  const { data } = await http.post<AnomalyCheckResult>('/anomaly-check', { history })
  return data
}
