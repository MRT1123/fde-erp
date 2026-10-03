<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { fetchMaterials, fetchSuppliers } from '../api/client'
import type { Material, Supplier } from '../api/types'

const fdeBase = import.meta.env.VITE_FDE_API_BASE || '/fde'

const materials = ref<Material[]>([])
const suppliers = ref<Supplier[]>([])
const loading = ref(false)

// 输入表单
const form = ref({
  title: '',
  supplier_id: undefined as number | undefined,
  supplier_name: '',
  total_amount: 0,
  purpose: '',
  items: [{ material_name: '', quantity: 1, unit_price: 0 }],
  history: [],
})

// 结果
interface FdeResult {
  risk_score?: number
  risk_level?: string
  risk_analysis?: string
  supplier_report?: {
    supplier_id?: number
    supplier_name?: string
    news?: unknown[]
    risk_flags?: unknown[]
    risk_level?: string
    report_content?: string
  } | null
  approval_decision?: string
  decision_reasons?: string[]
  needs_human_review?: boolean
  anomaly_alerts?: Array<{
    alert_type: string
    target_type?: string
    target_id?: string
    description?: string
    severity?: string
  }>
}

const result = ref<FdeResult | null>(null)
const summary = ref('')
const error = ref('')

const decisionMap: Record<string, { label: string; type: 'success' | 'warning' | 'danger' | 'info' }> = {
  approve: { label: '建议通过', type: 'success' },
  reject: { label: '建议驳回', type: 'danger' },
  supplement: { label: '补充材料', type: 'warning' },
  human: { label: '人工复核', type: 'warning' },
  auto_approve: { label: '自动通过', type: 'success' },
}

const riskScoreColor = computed(() => {
  const s = result.value?.risk_score || 0
  if (s >= 70) return '#ef4444'
  if (s >= 40) return '#f59e0b'
  return '#34c98f'
})
const riskLevelLabel = computed(() => {
  const lv = result.value?.risk_level
  if (lv === 'high') return '高风险'
  if (lv === 'medium') return '中风险'
  return '低风险'
})

function pickSupplier(id: number) {
  const s = suppliers.value.find((x) => x.id === id)
  form.value.supplier_name = s?.name || ''
}

async function runAnalyze() {
  if (!form.value.title) { ElMessage.warning('请填写采购标题'); return }
  loading.value = true
  error.value = ''
  result.value = null
  summary.value = ''
  try {
    const payload = {
      request_id: Math.floor(Math.random() * 9000) + 1000,
      purchase_request: {
        title: form.value.title,
        supplier_id: form.value.supplier_id ?? null,
        supplier_name: form.value.supplier_name,
        total_amount: form.value.total_amount,
        purpose: form.value.purpose,
        items: form.value.items,
      },
      history: form.value.history,
    }
    const { data } = await axios.post(`${fdeBase}/analyze`, payload, { timeout: 120000 })
    result.value = data.final_result || {}
    summary.value = data.summary || ''
    ElMessage.success('风控分析完成')
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || '调用 FDE 服务失败'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try { materials.value = await fetchMaterials() } catch { materials.value = [] }
  try { suppliers.value = await fetchSuppliers() } catch { suppliers.value = [] }
})
</script>

<template>
  <div class="risk-page">
    <el-card shadow="never" class="input-card">
      <template #header>
        <div class="card-title">AI 采购风控分析</div>
      </template>
      <el-form label-width="110px">
        <div class="form-grid">
          <el-form-item label="采购标题">
            <el-input v-model="form.title" placeholder="如：采购服务器 50 台" />
          </el-form-item>
          <el-form-item label="总金额(元)">
            <el-input-number v-model="form.total_amount" :min="0" :step="10000" placeholder="如：600000" style="width: 100%" />
          </el-form-item>
          <el-form-item label="供应商">
            <el-select v-model="form.supplier_id" filterable clearable placeholder="选择供应商" style="width: 100%" @change="(v: number) => v && pickSupplier(v)">
              <el-option v-for="s in suppliers" :key="s.id" :label="s.name" :value="s.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="供应商名称">
            <el-input v-model="form.supplier_name" placeholder="未选供应商时手工填写" />
          </el-form-item>
          <el-form-item label="采购用途">
            <el-input v-model="form.purpose" />
          </el-form-item>
        </div>
        <div class="items-block">
          <div class="block-title">采购明细</div>
          <div v-for="(it, i) in form.items" :key="i" class="item-row">
            <el-input v-model="it.material_name" placeholder="如：服务器" style="flex: 2" />
            <el-input-number v-model="it.quantity" :min="1" placeholder="如：50" style="width: 100px" />
            <el-input-number v-model="it.unit_price" :min="0" :precision="2" placeholder="如：12000" style="width: 120px" />
          </div>
        </div>
        <div class="run-row">
          <el-button type="primary" size="large" :loading="loading" @click="runAnalyze">
            {{ loading ? 'Agent 分析中…' : '▶ 运行风控分析' }}
          </el-button>
          <span class="run-tip">将调用 FDE Supervisor（DeepSeek）执行风险分析、供应商尽调、审批建议与异常检测</span>
        </div>
      </el-form>
    </el-card>

    <template v-if="error">
      <el-card shadow="never" class="error-card">
        <el-alert type="error" :title="'FDE 服务调用失败'" :description="error" show-icon :closable="false" />
      </el-card>
    </template>

    <template v-if="result">
      <div class="result-grid">
        <el-card shadow="never" class="score-card">
          <template #header><span class="card-title">综合风险评分</span></template>
          <div class="score-wrap">
            <div class="score-ring" :style="{ borderColor: riskScoreColor }">
              <div class="score-num" :style="{ color: riskScoreColor }">{{ result.risk_score ?? 0 }}</div>
            </div>
            <div class="score-label" :style="{ color: riskScoreColor }">{{ riskLevelLabel }}</div>
            <div v-if="result.needs_human_review != null" class="score-sub">
              <el-tag :type="result.needs_human_review ? 'warning' : 'success'" effect="light" round>
                {{ result.needs_human_review ? '需要人工复核' : '可自动放行' }}
              </el-tag>
            </div>
          </div>
        </el-card>

        <el-card shadow="never">
          <template #header><span class="card-title">审批建议</span></template>
          <div v-if="result.approval_decision" class="decision-row">
            <el-tag :type="decisionMap[result.approval_decision]?.type || 'info'" effect="dark" size="large" round>
              {{ decisionMap[result.approval_decision]?.label || result.approval_decision }}
            </el-tag>
          </div>
          <div v-if="result.decision_reasons?.length" class="reason-list">
            <div v-for="(r, i) in result.decision_reasons" :key="i" class="reason-item">{{ r }}</div>
          </div>
        </el-card>
      </div>

      <div class="result-grid">
        <el-card shadow="never">
          <template #header><span class="card-title">风险分析</span></template>
          <div class="content-text">{{ result.risk_analysis || '无风险点' }}</div>
        </el-card>
        <el-card shadow="never">
          <template #header><span class="card-title">供应商尽调</span></template>
          <div v-if="result.supplier_report">
            <el-descriptions :column="1" size="small">
              <el-descriptions-item label="供应商">{{ result.supplier_report.supplier_name }}</el-descriptions-item>
              <el-descriptions-item label="尽调评级">
                <el-tag :type="result.supplier_report.risk_level === 'high' ? 'danger' : result.supplier_report.risk_level === 'medium' ? 'warning' : 'success'" effect="light" size="small">
                  {{ result.supplier_report.risk_level }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
            <div v-if="result.supplier_report.report_content" class="content-text report-text">
              {{ result.supplier_report.report_content }}
            </div>
          </div>
          <div v-else class="empty-text">暂无尽调数据</div>
        </el-card>
      </div>

      <el-card shadow="never">
        <template #header><span class="card-title">异常检测告警</span></template>
        <div v-if="result.anomaly_alerts?.length" class="alert-list">
          <el-alert
            v-for="(a, i) in result.anomaly_alerts"
            :key="i"
            :title="a.description || a.alert_type"
            :type="a.severity === 'critical' ? 'error' : a.severity === 'warning' ? 'warning' : 'info'"
            :description="`类型：${a.alert_type}`"
            show-icon
            :closable="false"
            class="alert-item"
          />
        </div>
        <div v-else class="empty-text">未发现异常信号</div>
      </el-card>

      <el-card v-if="summary" shadow="never">
        <template #header><span class="card-title">Agent 总结</span></template>
        <div class="content-text">{{ summary }}</div>
      </el-card>
    </template>
  </div>
</template>

<style scoped>
.risk-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.card-title { font-weight: 600; color: #24344a; }
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 20px;
}
.items-block { margin-top: 4px; }
.block-title { font-weight: 600; color: #24344a; margin-bottom: 8px; font-size: 13px; }
.item-row { display: flex; gap: 8px; margin-bottom: 8px; }
.run-row { display: flex; align-items: center; gap: 14px; margin-top: 8px; }
.run-tip { color: #8ba0b8; font-size: 12px; }
.result-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.score-card :deep(.el-card__body) { display: flex; justify-content: center; }
.score-wrap { text-align: center; padding: 10px 0; }
.score-ring {
  width: 110px; height: 110px; border-radius: 50%; border: 8px solid;
  display: flex; align-items: center; justify-content: center; margin: 0 auto;
  background: #fff;
}
.score-num { font-size: 36px; font-weight: 800; }
.score-label { margin-top: 10px; font-size: 16px; font-weight: 600; }
.score-sub { margin-top: 12px; }
.decision-row { margin-bottom: 10px; }
.reason-list { display: flex; flex-direction: column; gap: 8px; }
.reason-item {
  background: #f6faff; border-radius: 8px; padding: 10px 12px;
  color: #44566c; font-size: 13px; line-height: 1.6;
}
.content-text {
  color: #44566c; line-height: 1.8; font-size: 13px; white-space: pre-wrap;
}
.report-text {
  background: #f6faff; border-radius: 10px; padding: 12px 14px; margin-top: 10px;
}
.empty-text { color: #a5b6c9; font-size: 13px; }
.alert-list { display: flex; flex-direction: column; gap: 10px; }
.alert-item { border-radius: 10px; }
</style>
