<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  fetchBudgetDepartments, fetchBudgetDepartmentDetail, updateBudgetLimit,
} from '../api/client'
import type { DepartmentBudget, DepartmentBudgetDetail } from '../api/types'

const loading = ref(true)
const departments = ref<DepartmentBudget[]>([])
const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = ref<DepartmentBudgetDetail | null>(null)
const limitDialogVisible = ref(false)
const limitSaving = ref(false)
const editing = ref<DepartmentBudget | null>(null)
const newLimit = ref<number | undefined>(undefined)

const statusMap: Record<string, { label: string; type: 'success' | 'danger' | 'info' }> = {
  ok: { label: '预算正常', type: 'success' },
  over_budget: { label: '超预算', type: 'danger' },
  unknown: { label: '未设上限', type: 'info' },
}

const summary = computed(() => {
  const limit = departments.value.reduce((s, d) => s + (d.budget_limit || 0), 0)
  const used = departments.value.reduce((s, d) => s + d.used, 0)
  const pending = departments.value.reduce((s, d) => s + d.pending, 0)
  const available = departments.value.reduce((s, d) => s + (d.available || 0), 0)
  return { limit, used, pending, available }
})

function fmt(n: number | null | undefined): string {
  if (n == null) return '-'
  return n.toLocaleString('zh-CN', { maximumFractionDigits: 2 })
}

function openLimit(row: DepartmentBudget) {
  editing.value = row
  newLimit.value = row.budget_limit ?? undefined
  limitDialogVisible.value = true
}

async function saveLimit() {
  if (!editing.value || newLimit.value == null) { ElMessage.warning('请输入预算上限'); return }
  if (newLimit.value < 0) { ElMessage.warning('预算上限不能为负数'); return }
  limitSaving.value = true
  try {
    await updateBudgetLimit(editing.value.department_id, newLimit.value)
    ElMessage.success('预算上限已更新')
    limitDialogVisible.value = false
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '更新失败')
  } finally {
    limitSaving.value = false
  }
}

async function openDetail(row: DepartmentBudget) {
  detailVisible.value = true
  detailLoading.value = true
  detail.value = null
  try {
    detail.value = await fetchBudgetDepartmentDetail(row.department_id)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载明细失败')
  } finally {
    detailLoading.value = false
  }
}

async function load() {
  loading.value = true
  try {
    departments.value = await fetchBudgetDepartments()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载预算数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <el-row :gutter="14" class="stat-row">
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">年度预算总额</div>
          <div class="stat-value">{{ fmt(summary.limit) }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">已用（已批准）</div>
          <div class="stat-value warn">{{ fmt(summary.used) }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">在途占用</div>
          <div class="stat-value">{{ fmt(summary.pending) }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">可用余额</div>
          <div class="stat-value success">{{ fmt(summary.available) }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>部门预算总览</span>
          <span class="hint">已用=已批准采购金额；在途=审批中/分析中金额；超预算采购单将在风险分析中加计风险分</span>
        </div>
      </template>
      <el-table v-loading="loading" :data="departments" empty-text="暂无部门预算数据">
        <el-table-column label="部门" min-width="160">
          <template #default="{ row }">
            <div class="dept-name">{{ row.department_name }}</div>
            <div class="dept-code">{{ row.department_code }}</div>
          </template>
        </el-table-column>
        <el-table-column label="年度预算上限（元）" width="160">
          <template #default="{ row }">
            <span class="money">{{ fmt(row.budget_limit) }}</span>
            <el-button link type="primary" size="small" @click="openLimit(row)">设置</el-button>
          </template>
        </el-table-column>
        <el-table-column label="已用（元）" width="140">
          <template #default="{ row }"><span class="money">{{ fmt(row.used) }}</span></template>
        </el-table-column>
        <el-table-column label="在途（元）" width="130">
          <template #default="{ row }"><span class="money">{{ fmt(row.pending) }}</span></template>
        </el-table-column>
        <el-table-column label="可用（元）" width="140">
          <template #default="{ row }">
            <span :class="['money', row.status === 'over_budget' ? 'danger-text' : '']">{{ fmt(row.available) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="使用率" width="180">
          <template #default="{ row }">
            <div class="usage-cell">
              <el-progress
                :percentage="row.utilization ?? 0"
                :stroke-width="10"
                :color="row.utilization > 100 ? '#f56c6c' : row.utilization > 80 ? '#e6a23c' : '#34c98f'"
              />
              <span class="usage-num">{{ row.utilization == null ? '-' : row.utilization + '%' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type || 'info'" effect="light" size="small">
              {{ statusMap[row.status]?.label || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDetail(row)">查看明细</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="limitDialogVisible" title="设置部门年度预算上限" width="420px">
      <el-form label-width="120px">
        <el-form-item label="部门">
          <span>{{ editing?.department_name }}</span>
        </el-form-item>
        <el-form-item label="预算上限（元）" required>
          <el-input-number v-model="newLimit" :min="0" :step="10000" :precision="0" style="width: 200px" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="limitDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="limitSaving" @click="saveLimit">保存</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" :title="detail ? `${detail.department_name} · 预算明细` : '预算明细'" size="560px">
      <div v-loading="detailLoading">
        <template v-if="detail">
          <el-descriptions :column="2" border class="detail-desc">
            <el-descriptions-item label="预算上限">{{ fmt(detail.budget_limit) }}</el-descriptions-item>
            <el-descriptions-item label="可用余额">{{ fmt(detail.available) }}</el-descriptions-item>
            <el-descriptions-item label="已用">{{ fmt(detail.used) }}</el-descriptions-item>
            <el-descriptions-item label="在途">{{ fmt(detail.pending) }}</el-descriptions-item>
          </el-descriptions>
          <el-divider content-position="left">采购申请明细</el-divider>
          <el-table :data="detail.requests" empty-text="暂无采购申请" size="small">
            <el-table-column prop="request_no" label="单号" width="150" />
            <el-table-column prop="title" label="标题" min-width="140" show-overflow-tooltip />
            <el-table-column label="金额" width="110">
              <template #default="{ row }">{{ fmt(row.total_amount) }}</template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag size="small" effect="plain">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="预算" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.budget_status === 'over_budget'" type="danger" size="small" effect="light">超预算</el-tag>
                <el-tag v-else-if="row.budget_status === 'ok'" type="success" size="small" effect="light">正常</el-tag>
                <el-tag v-else type="info" size="small" effect="plain">未校验</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="风险" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.risk_level === 'high'" type="danger" size="small" effect="dark">高</el-tag>
                <el-tag v-else-if="row.risk_level === 'medium'" type="warning" size="small" effect="plain">中</el-tag>
                <el-tag v-else-if="row.risk_level === 'low'" type="success" size="small" effect="plain">低</el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.stat-row { margin-bottom: 14px; }
.stat-card { text-align: left; }
.stat-label { font-size: 13px; color: #7a8fa5; margin-bottom: 8px; }
.stat-value { font-size: 24px; font-weight: 700; color: #24344a; }
.stat-value.warn { color: #e6a23c; }
.stat-value.success { color: #34c98f; }
.card-header { display: flex; align-items: baseline; justify-content: space-between; }
.hint { font-size: 12px; color: #8ba0b8; }
.dept-name { font-weight: 600; }
.dept-code { font-size: 12px; color: #8ba0b8; }
.money { font-variant-numeric: tabular-nums; }
.danger-text { color: #f56c6c; font-weight: 600; }
.usage-cell { display: flex; align-items: center; gap: 8px; }
.usage-cell .el-progress { flex: 1; }
.usage-num { font-size: 12px; color: #5b6b7d; min-width: 44px; text-align: right; }
.detail-desc { margin-bottom: 4px; }
</style>
