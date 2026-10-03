<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  approveApproval, fetchApproval, fetchApprovalActions, fetchApprovals, rejectApproval,
} from '../api/client'
import type { Approval, ApprovalAction, ApprovalListItem } from '../api/types'

const loading = ref(true)
const rows = ref<ApprovalListItem[]>([])
const keyword = ref('')

// 审批抽屉
const drawerVisible = ref(false)
const currentApproval = ref<Approval | null>(null)
const currentPurchaseTitle = ref('')
const currentPurchaseAmount = ref(0)
const actions = ref<ApprovalAction[]>([])
const acting = ref(false)
const rejectDialog = ref(false)
const rejectReason = ref('')

const approvalStatusMap: Record<string, { label: string; type: 'warning' | 'success' | 'danger' | 'info' }> = {
  pending: { label: '待审批', type: 'warning' },
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' },
  timeout: { label: '超时升级', type: 'info' },
}

async function load() {
  loading.value = true
  try {
    rows.value = await fetchApprovals()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载审批失败')
  }
  loading.value = false
}

async function openDetail(row: ApprovalListItem) {
  currentApproval.value = row
  currentPurchaseTitle.value = row.purchase_title || ''
  currentPurchaseAmount.value = row.purchase_amount || 0
  drawerVisible.value = true
  try {
    currentApproval.value = await fetchApproval(row.id)
    actions.value = await fetchApprovalActions(row.id)
  } catch (e) {
    actions.value = []
  }
}

async function doApprove(comment?: string) {
  if (!currentApproval.value) return
  acting.value = true
  try {
    await approveApproval(currentApproval.value.id, comment || undefined)
    ElMessage.success('审批已通过')
    drawerVisible.value = false
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  } finally {
    acting.value = false
  }
}

function openReject() {
  rejectReason.value = ''
  rejectDialog.value = true
}
async function doReject() {
  if (!currentApproval.value) return
  if (!rejectReason.value) { ElMessage.warning('请填写驳回原因'); return }
  acting.value = true
  try {
    await rejectApproval(currentApproval.value.id, rejectReason.value)
    ElMessage.success('已驳回')
    rejectDialog.value = false
    drawerVisible.value = false
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  } finally {
    acting.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索审批单号 / 采购标题" clearable style="width: 280px" />
        <el-tag type="warning" effect="light" round>人工审批工作台</el-tag>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="rows" empty-text="暂无审批任务">
        <el-table-column prop="approval_no" label="审批单号" width="160">
          <template #default="{ row }"><span class="no">{{ row.approval_no }}</span></template>
        </el-table-column>
        <el-table-column label="采购标题" min-width="200">
          <template #default="{ row }">{{ row.purchase_title || '-' }}</template>
        </el-table-column>
        <el-table-column label="金额" width="120">
          <template #default="{ row }">
            <span class="amount">¥{{ (row.purchase_amount || 0).toLocaleString() }}</span>
          </template>
        </el-table-column>
        <el-table-column label="风险快照" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.risk_score_snapshot != null" :type="(row.risk_score_snapshot || 0) >= 70 ? 'danger' : (row.risk_score_snapshot || 0) >= 40 ? 'warning' : 'success'" effect="light" round>
              {{ row.risk_score_snapshot }}
            </el-tag>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="approvalStatusMap[row.status]?.type" effect="light" round>
              {{ approvalStatusMap[row.status]?.label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="飞书审批" width="100">
          <template #default="{ row }">
            <el-icon v-if="row.feishu_instance_code" color="#2f6fed"><Promotion /></el-icon>
            <span v-else class="muted">未联动</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="openDetail(row)">处理</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-drawer v-model="drawerVisible" title="审批详情" size="480px">
      <template v-if="currentApproval">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="审批单号">{{ currentApproval.approval_no }}</el-descriptions-item>
          <el-descriptions-item label="采购标题">{{ currentPurchaseTitle || '-' }}</el-descriptions-item>
          <el-descriptions-item label="金额">¥{{ currentPurchaseAmount.toLocaleString() }}</el-descriptions-item>
          <el-descriptions-item label="风险快照">{{ currentApproval.risk_score_snapshot ?? '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ approvalStatusMap[currentApproval.status]?.label }}</el-descriptions-item>
          <el-descriptions-item label="飞书实例">
            {{ currentApproval.feishu_instance_code || '未联动' }}
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="currentPurchaseTitle" class="summary-box">
          <div class="summary-title">关联采购单</div>
          <div class="summary-text">{{ currentPurchaseTitle }}（¥{{ currentPurchaseAmount.toLocaleString() }}）</div>
        </div>

        <div class="actions-title">审批记录</div>
        <el-timeline>
          <el-timeline-item
            v-for="a in actions"
            :key="a.id"
            :timestamp="a.created_at?.replace('T', ' ').slice(0, 16)"
            :type="a.action === 'approve' ? 'success' : a.action === 'reject' ? 'danger' : 'primary'"
          >
            {{ a.action }}<span v-if="a.comment">：{{ a.comment }}</span>
          </el-timeline-item>
        </el-timeline>

        <div v-if="currentApproval.status === 'pending'" class="drawer-actions">
          <el-button type="success" :loading="acting" @click="doApprove()">通过</el-button>
          <el-button type="danger" :loading="acting" @click="openReject">驳回</el-button>
        </div>
      </template>
    </el-drawer>

    <el-dialog v-model="rejectDialog" title="驳回审批" width="420px">
      <el-input v-model="rejectReason" type="textarea" :rows="3" placeholder="请填写驳回原因（必填）" />
      <template #footer>
        <el-button @click="rejectDialog = false">取消</el-button>
        <el-button type="danger" :loading="acting" @click="doReject">确认驳回</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar-card { margin-bottom: 14px; }
.toolbar { display: flex; align-items: center; justify-content: space-between; }
.no { color: #2f6fed; font-weight: 600; }
.amount { font-weight: 600; }
.muted { color: #a5b6c9; font-size: 12px; }
.summary-box {
  background: #f6faff;
  border-radius: 10px;
  padding: 12px 14px;
  margin: 16px 0;
}
.summary-title { font-weight: 600; color: #2f6fed; margin-bottom: 6px; font-size: 13px; }
.summary-text { color: #44566c; line-height: 1.7; font-size: 13px; white-space: pre-wrap; }
.actions-title { font-weight: 600; color: #24344a; margin: 16px 0 10px; }
.drawer-actions { margin-top: 20px; display: flex; gap: 10px; }
</style>
