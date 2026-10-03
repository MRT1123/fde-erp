<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchPurchaseRequest, submitPurchaseRequest, withdrawPurchaseRequest } from '../api/client'
import type { PurchaseRequest } from '../api/types'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const detail = ref<PurchaseRequest | null>(null)

const statusMap: Record<string, { label: string; type: 'info' | 'warning' | 'success' | 'danger' }> = {
  draft: { label: '草稿', type: 'info' },
  pending_approval: { label: '待审批', type: 'warning' },
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' },
  withdrawn: { label: '已撤回', type: 'info' },
}

const riskColor = computed(() => {
  const lv = detail.value?.risk_level
  if (lv === 'high') return '#ef4444'
  if (lv === 'medium') return '#f59e0b'
  return '#34c98f'
})

async function load() {
  loading.value = true
  try {
    detail.value = await fetchPurchaseRequest(Number(route.params.id))
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载失败')
  }
  loading.value = false
}

async function submit() {
  if (!detail.value) return
  try {
    await submitPurchaseRequest(detail.value.id)
    ElMessage.success('已提交，正在执行风控分析')
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '提交失败')
  }
}

async function withdraw() {
  if (!detail.value) return
  try {
    await withdrawPurchaseRequest(detail.value.id)
    ElMessage.success('已撤回')
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '撤回失败')
  }
}

onMounted(load)
</script>

<template>
  <div v-loading="loading" class="detail-page">
    <div class="detail-head">
      <el-button text @click="router.push('/purchase')">← 返回列表</el-button>
    </div>

    <template v-if="detail">
      <el-card shadow="never" class="head-card">
        <div class="head-row">
          <div>
            <div class="head-title">{{ detail.title }}</div>
            <div class="head-meta">
              <span class="no">{{ detail.request_no }}</span>
              <span>创建：{{ detail.created_at?.replace('T', ' ').slice(0, 16) }}</span>
              <span v-if="detail.submitted_at">提交：{{ detail.submitted_at?.replace('T', ' ').slice(0, 16) }}</span>
            </div>
          </div>
          <div class="head-right">
            <el-tag :type="statusMap[detail.status]?.type" effect="light" round size="large">
              {{ statusMap[detail.status]?.label }}
            </el-tag>
            <div v-if="detail.risk_score != null" class="risk-badge" :style="{ borderColor: riskColor, color: riskColor }">
              <div class="risk-score">{{ detail.risk_score }}</div>
              <div class="risk-label">风险分 · {{ detail.risk_level === 'high' ? '高风险' : detail.risk_level === 'medium' ? '中风险' : '低风险' }}</div>
            </div>
          </div>
        </div>
        <div v-if="detail.status === 'draft'" class="head-actions">
          <el-button type="primary" @click="submit">提交风控分析</el-button>
          <el-button @click="withdraw">撤回</el-button>
        </div>
        <div v-else-if="detail.status === 'pending_approval'" class="head-actions">
          <el-button type="primary" @click="router.push('/approvals')">前往审批工作台</el-button>
        </div>
      </el-card>

      <div class="detail-grid">
        <el-card shadow="never">
          <template #header><span class="card-title">基本信息</span></template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="金额">¥{{ detail.total_amount.toLocaleString() }}（{{ detail.currency }}）</el-descriptions-item>
            <el-descriptions-item label="供应商ID">{{ detail.supplier_id ?? '未指定' }}</el-descriptions-item>
            <el-descriptions-item label="申请人ID">{{ detail.applicant_id }}</el-descriptions-item>
            <el-descriptions-item label="部门ID">{{ detail.department_id }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card shadow="never">
          <template #header><span class="card-title">Agent 风控摘要</span></template>
          <div v-if="detail.agent_summary" class="summary-text">{{ detail.agent_summary }}</div>
          <div v-else class="empty-text">尚未提交风控分析，提交后将在此展示 Agent 分析摘要。</div>
          <div class="summary-flags">
            <el-tag v-if="detail.needs_human_review" type="warning" effect="light" round>需要人工复核</el-tag>
            <el-tag v-else type="success" effect="light" round>自动放行</el-tag>
          </div>
        </el-card>
      </div>

      <el-card shadow="never">
        <template #header><span class="card-title">采购明细</span></template>
        <el-table :data="detail.items || []" size="small">
          <el-table-column prop="material_name" label="物料" min-width="160" />
          <el-table-column prop="spec" label="规格" min-width="120" />
          <el-table-column prop="quantity" label="数量" width="90" />
          <el-table-column label="单价" width="110">
            <template #default="{ row }">{{ row.unit_price != null ? `¥${row.unit_price}` : '-' }}</template>
          </el-table-column>
          <el-table-column label="小计" width="130">
            <template #default="{ row }"><span class="amount">¥{{ row.amount.toLocaleString() }}</span></template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" min-width="120" />
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<style scoped>
.detail-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.detail-head {
  margin-bottom: -4px;
}
.head-card :deep(.el-card__body) {
  padding: 22px 24px;
}
.head-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}
.head-title {
  font-size: 20px;
  font-weight: 700;
  color: #1f2d3d;
}
.head-meta {
  display: flex;
  gap: 16px;
  margin-top: 8px;
  color: #8ba0b8;
  font-size: 13px;
}
.no {
  color: #2f6fed;
  font-weight: 600;
}
.head-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.risk-badge {
  border: 2px solid;
  border-radius: 12px;
  padding: 6px 18px;
  text-align: center;
}
.risk-score {
  font-size: 24px;
  font-weight: 700;
}
.risk-label {
  font-size: 12px;
}
.head-actions {
  margin-top: 16px;
  display: flex;
  gap: 10px;
}
.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.card-title {
  font-weight: 600;
  color: #24344a;
}
.summary-text {
  line-height: 1.7;
  color: #44566c;
  white-space: pre-wrap;
}
.empty-text {
  color: #a5b6c9;
  font-size: 13px;
  line-height: 1.6;
}
.summary-flags {
  margin-top: 14px;
  display: flex;
  gap: 8px;
}
.amount {
  font-weight: 600;
}
</style>
