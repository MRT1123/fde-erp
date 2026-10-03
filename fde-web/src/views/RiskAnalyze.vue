<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, RefreshRight } from '@element-plus/icons-vue'
import { analyzeRisk } from '../api/client'
import type { AnalyzeRequest, AnalyzeResponse, SupplierReport, AnomalyAlert } from '../api/types'

const loading = ref(false)
const result = ref<AnalyzeResponse | null>(null)
const activeTab = ref('overview')

const form = reactive<AnalyzeRequest>({
  request_id: 0,
  title: '',
  department: '',
  applicant: '',
  supplier_id: 0,
  supplier_name: '',
  supplier_credit_score: 0,
  supplier_risk_level: '',
  total_amount: 0,
  purpose: '',
  first_cooperation: false,
  budget_limit: 0,
  items: [
    { material_name: '', quantity: 1, unit_price: 0 },
  ],
})

async function run() {
  loading.value = true
  result.value = null
  try {
    result.value = await analyzeRisk(form)
    activeTab.value = 'overview'
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '风控分析失败，请确认 FDE 服务已启动'
    ElMessage.error(String(msg))
  } finally {
    loading.value = false
  }
}

function fillDemo() {
  Object.assign(form, {
    request_id: Math.floor(Math.random() * 9000) + 1000,
    title: '采购交换机 8 台',
    department: '网络部',
    applicant: '李强',
    supplier_id: 1,
    supplier_name: '测试供应商A',
    supplier_credit_score: 85,
    supplier_risk_level: 'low',
    total_amount: 80000,
    purpose: '办公网络改造升级',
    first_cooperation: true,
    budget_limit: 100000,
    items: [{ material_name: '交换机', quantity: 8, unit_price: 10000 }],
  })
}

const final = computed(() => (result.value?.final_result || result.value || {}) as Record<string, unknown>)
const riskScore = computed(() => Number(final.value.risk_score ?? 0))
const riskLevel = computed(() => String(final.value.risk_level ?? 'unknown'))
const riskAnalysis = computed(() => String(final.value.risk_analysis || final.value.analysis || ''))
const approvalDecision = computed(() => String(final.value.approval_decision || ''))
const decisionReasons = computed(() => (final.value.decision_reasons || []) as string[])
const supplierReport = computed(() => (final.value.supplier_report || null) as SupplierReport | null)
const anomalyAlerts = computed(() => (final.value.anomaly_alerts || []) as AnomalyAlert[])
const needsHuman = computed(() => Boolean(final.value.needs_human_review))

const scoreColor = computed(() => {
  if (riskLevel.value === 'high') return '#ef4444'
  if (riskLevel.value === 'medium') return '#f59e0b'
  return '#10b981'
})

const levelText = computed(() => {
  if (riskLevel.value === 'high') return '高风险'
  if (riskLevel.value === 'medium') return '中风险'
  return '低风险'
})

const levelTag = computed(() => {
  if (riskLevel.value === 'high') return 'danger'
  if (riskLevel.value === 'medium') return 'warning'
  return 'success'
})

const decisionTag = computed(() => {
  if (approvalDecision.value === 'approve') return 'success'
  if (approvalDecision.value === 'reject') return 'danger'
  return 'warning'
})

const decisionText = computed(() => {
  if (approvalDecision.value === 'approve') return '建议通过'
  if (approvalDecision.value === 'reject') return '建议驳回'
  return '建议人工复核'
})
</script>

<template>
  <div class="risk-page">
    <!-- 分析输入 -->
    <el-card class="form-card" shadow="never">
      <template #header>
        <div class="card-head">
          <span class="card-title">采购申请信息</span>
          <el-button size="small" :icon="RefreshRight" @click="fillDemo">填入示例</el-button>
        </div>
      </template>
      <el-form label-width="90px" label-position="left">
        <el-row :gutter="16">
          <el-col :md="8" :sm="12" :xs="24">
            <el-form-item label="申请编号">
              <el-input v-model.number="form.request_id" placeholder="如 1001" />
            </el-form-item>
          </el-col>
          <el-col :md="8" :sm="12" :xs="24">
            <el-form-item label="采购标题">
              <el-input v-model="form.title" placeholder="如：采购服务器 20 台" />
            </el-form-item>
          </el-col>
          <el-col :md="8" :sm="12" :xs="24">
            <el-form-item label="申请部门">
              <el-input v-model="form.department" placeholder="技术部" />
            </el-form-item>
          </el-col>
          <el-col :md="8" :sm="12" :xs="24">
            <el-form-item label="申请人">
              <el-input v-model="form.applicant" placeholder="如：张伟" />
            </el-form-item>
          </el-col>
          <el-col :md="8" :sm="12" :xs="24">
            <el-form-item label="供应商">
              <el-input v-model="form.supplier_name" placeholder="如：华信科技" />
            </el-form-item>
          </el-col>
          <el-col :md="8" :sm="12" :xs="24">
            <el-form-item label="采购金额">
              <el-input-number v-model="form.total_amount" :min="0" :step="10000" placeholder="如：240000" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :md="8" :sm="12" :xs="24">
            <el-form-item label="信用评分">
              <el-input-number v-model="form.supplier_credit_score" :min="0" :max="100" placeholder="如：92" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :md="8" :sm="12" :xs="24">
            <el-form-item label="首次合作">
              <el-switch v-model="form.first_cooperation" />
            </el-form-item>
          </el-col>
          <el-col :md="8" :sm="12" :xs="24">
            <el-form-item label="预算上限">
              <el-input-number v-model="form.budget_limit" :min="0" :step="50000" placeholder="如：1000000" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="采购用途">
              <el-input v-model="form.purpose" type="textarea" :rows="2" placeholder="如：机房扩容，用于新业务线部署" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="物料清单">
              <el-input v-model="form.items[0].material_name" placeholder="如：服务器" style="width: 180px; margin-right: 8px" />
              <el-input-number v-model="form.items[0].quantity" :min="1" placeholder="如：20" style="width: 120px; margin-right: 8px" />
              <el-input-number v-model="form.items[0].unit_price" :min="1" placeholder="如：12000" style="width: 140px" />
            </el-form-item>
          </el-col>
        </el-row>
        <div class="form-actions">
          <el-button type="primary" size="large" :loading="loading" :icon="Search" @click="run">
            {{ loading ? 'Agent 分析中…' : '开始风控分析' }}
          </el-button>
        </div>
      </el-form>
    </el-card>

    <!-- 结果 -->
    <template v-if="result">
      <el-tabs v-model="activeTab" class="result-tabs">
        <el-tab-pane label="综合结论" name="overview">
          <div class="result-grid">
            <el-card shadow="never" class="score-card">
              <template #header><span class="card-title">风险评分</span></template>
              <div class="score-wrap">
                <div class="score-ring" :style="{ background: `conic-gradient(${scoreColor} ${Math.min(riskScore, 100) * 3.6}deg, #eef2f7 0deg)` }">
                  <div class="score-inner">
                    <span class="score-num" :style="{ color: scoreColor }">{{ riskScore }}</span>
                    <span class="score-label">/ 100</span>
                  </div>
                </div>
                <el-tag :type="levelTag" size="large" effect="dark" class="level-tag">{{ levelText }}</el-tag>
              </div>
              <el-descriptions :column="1" size="small" class="score-desc">
                <el-descriptions-item label="是否需人工">
                  <el-tag :type="needsHuman ? 'danger' : 'success'" size="small">{{ needsHuman ? '是' : '否' }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="审批建议">
                  <el-tag :type="decisionTag" size="small">{{ decisionText }}</el-tag>
                </el-descriptions-item>
              </el-descriptions>
            </el-card>

            <el-card shadow="never" class="analysis-card">
              <template #header><span class="card-title">风险分析</span></template>
              <p class="analysis-text">{{ riskAnalysis || 'Agent 未生成详细分析。' }}</p>
            </el-card>
          </div>

          <el-card shadow="never" class="reason-card">
            <template #header><span class="card-title">决策依据</span></template>
            <ul class="reason-list">
              <li v-for="(r, i) in decisionReasons" :key="i">{{ r }}</li>
              <li v-if="!decisionReasons.length">暂无决策依据。</li>
            </ul>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="供应商尽调" name="supplier">
          <el-card shadow="never">
            <template #header><span class="card-title">供应商尽调报告</span></template>
            <template v-if="supplierReport">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="供应商名称">{{ supplierReport.supplier_name || form.supplier_name }}</el-descriptions-item>
                <el-descriptions-item label="信用评分">{{ supplierReport.credit_score ?? '—' }}</el-descriptions-item>
                <el-descriptions-item label="资质状态">{{ supplierReport.qualification_status || '—' }}</el-descriptions-item>
                <el-descriptions-item label="风险等级">
                  <el-tag :type="supplierReport.risk_level === 'low' ? 'success' : supplierReport.risk_level === 'high' ? 'danger' : 'warning'" size="small">
                    {{ supplierReport.risk_level || '—' }}
                  </el-tag>
                </el-descriptions-item>
              </el-descriptions>
              <div v-if="supplierReport.compliance_issues?.length" class="sec-block">
                <div class="sec-title">合规问题</div>
                <ul class="reason-list">
                  <li v-for="(x, i) in supplierReport.compliance_issues" :key="i">{{ x }}</li>
                </ul>
              </div>
              <div v-if="supplierReport.recommendations?.length" class="sec-block">
                <div class="sec-title">尽调建议</div>
                <ul class="reason-list">
                  <li v-for="(x, i) in supplierReport.recommendations" :key="i">{{ x }}</li>
                </ul>
              </div>
              <div v-if="supplierReport.report" class="sec-block">
                <div class="sec-title">报告原文</div>
                <p class="analysis-text">{{ supplierReport.report }}</p>
              </div>
            </template>
            <el-empty v-else description="未生成供应商尽调报告" />
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="异常告警" name="anomaly">
          <el-card shadow="never">
            <template #header><span class="card-title">异常行为告警</span></template>
            <template v-if="anomalyAlerts.length">
              <el-table :data="anomalyAlerts" stripe>
                <el-table-column prop="type" label="类型" width="180" />
                <el-table-column label="级别" width="120">
                  <template #default="{ row }">
                    <el-tag :type="row.level === 'high' ? 'danger' : row.level === 'medium' ? 'warning' : 'info'" size="small">
                      {{ row.level }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="message" label="描述" />
              </el-table>
            </template>
            <el-empty v-else description="未发现异常行为" />
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </template>
    <el-empty v-else-if="!loading" description="填写采购信息后，点击「开始风控分析」" class="empty-hint" />
  </div>
</template>

<style scoped>
.risk-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-title {
  font-weight: 700;
  color: #0f172a;
  font-size: 15px;
}
.form-card {
  border-radius: 14px;
  border: 1px solid #e7edf5;
}
.form-actions {
  display: flex;
  justify-content: center;
  padding-top: 4px;
}
.result-grid {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 18px;
}
@media (max-width: 900px) {
  .result-grid { grid-template-columns: 1fr; }
}
.score-card, .analysis-card, .reason-card {
  border-radius: 14px;
  border: 1px solid #e7edf5;
}
.score-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  padding: 10px 0;
}
.score-ring {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.score-inner {
  width: 122px;
  height: 122px;
  border-radius: 50%;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.score-num {
  font-size: 42px;
  font-weight: 800;
  line-height: 1;
}
.score-label {
  color: #94a3b8;
  font-size: 12px;
  margin-top: 4px;
}
.level-tag {
  font-size: 14px;
}
.score-desc {
  margin-top: 6px;
}
.analysis-text {
  color: #334155;
  line-height: 1.8;
  font-size: 14px;
  white-space: pre-wrap;
}
.reason-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.reason-list li {
  position: relative;
  padding-left: 18px;
  color: #334155;
  font-size: 14px;
  line-height: 1.6;
}
.reason-list li::before {
  content: '';
  position: absolute;
  left: 2px;
  top: 9px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #3b82f6;
}
.sec-block {
  margin-top: 18px;
}
.sec-title {
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 8px;
  font-size: 14px;
}
.empty-hint {
  padding: 60px 0;
}
.result-tabs {
  margin-top: 4px;
}
</style>
