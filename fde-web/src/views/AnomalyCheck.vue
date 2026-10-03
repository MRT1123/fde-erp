<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Plus, Delete } from '@element-plus/icons-vue'
import { anomalyCheck } from '../api/client'
import type { AnomalyCheckResult, HistoryRecord } from '../api/types'

const loading = ref(false)
const result = ref<AnomalyCheckResult | null>(null)

const rows = ref<HistoryRecord[]>([])

function addRow() {
  rows.value.push({ supplier_id: 0, amount: 0, created_at: '', title: '' })
}
function removeRow(i: number) {
  rows.value.splice(i, 1)
}

async function run() {
  if (!rows.value.length) {
    ElMessage.warning('请至少添加一条历史采购记录')
    return
  }
  loading.value = true
  result.value = null
  try {
    result.value = await anomalyCheck(rows.value)
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '异常检测失败，请确认 FDE 服务已启动'
    ElMessage.error(String(msg))
  } finally {
    loading.value = false
  }
}


const sevTag = (s?: string) => {
  if (s === 'high') return 'danger'
  if (s === 'warning') return 'warning'
  return 'info'
}
const typeText = (t?: string) => {
  if (t === 'split_order') return '拆分订单'
  return t || '-'
}
</script>

<template>
  <div class="ac-page">
    <!-- 输入 -->
    <el-card class="form-card" shadow="never">
      <template #header>
        <div class="card-head">
          <span class="card-title">历史采购记录</span>
          <div>
            <el-button size="small" type="primary" plain :icon="Plus" @click="addRow">添加一行</el-button>
          </div>
        </div>
      </template>
      <el-table :data="rows" stripe border>
        <el-table-column label="供应商 ID" min-width="130">
          <template #default="{ row }">
            <el-input-number v-model="row.supplier_id" :min="0" size="small" style="width: 120px" />
          </template>
        </el-table-column>
        <el-table-column label="金额" min-width="140">
          <template #default="{ row }">
            <el-input-number v-model="row.amount" :min="0" :step="1000" size="small" placeholder="如：10000" style="width: 130px" />
          </template>
        </el-table-column>
        <el-table-column label="采购日期" min-width="150">
          <template #default="{ row }">
            <el-input v-model="row.created_at" size="small" placeholder="如 2026-09-01" />
          </template>
        </el-table-column>
        <el-table-column label="标题" min-width="180">
          <template #default="{ row }">
            <el-input v-model="row.title" size="small" placeholder="采购内容" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ $index }">
            <el-button size="small" type="danger" link :icon="Delete" @click="removeRow($index)" />
          </template>
        </el-table-column>
      </el-table>
      <div class="form-actions">
        <el-button type="primary" size="large" :loading="loading" :icon="Search" @click="run">
          {{ loading ? '检测中…' : '开始异常检测' }}
        </el-button>
      </div>
    </el-card>

    <!-- 结果 -->
    <el-card v-if="result" shadow="never" class="reason-card">
      <template #header><span class="card-title">异常告警（{{ result.alerts?.length ?? 0 }} 条）</span></template>
      <template v-if="result.alerts?.length">
        <el-table :data="result.alerts" stripe>
          <el-table-column label="类型" width="160">
            <template #default="{ row }">{{ typeText(row.alert_type) }}</template>
          </el-table-column>
          <el-table-column label="目标" width="180">
            <template #default="{ row }">{{ row.target_type }} #{{ row.target_id }}</template>
          </el-table-column>
          <el-table-column label="级别" width="120">
            <template #default="{ row }">
              <el-tag :type="sevTag(row.severity)" size="small">{{ row.severity }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="描述" min-width="280">
            <template #default="{ row }">{{ row.description }}</template>
          </el-table-column>
        </el-table>
      </template>
      <el-empty v-else description="未发现异常行为" />
    </el-card>
    <el-empty v-else-if="!loading" description="输入历史采购记录后，点击「开始异常检测」" class="empty-hint" />
  </div>
</template>

<style scoped>
.ac-page {
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
.form-card, .reason-card {
  border-radius: 14px;
  border: 1px solid #e7edf5;
}
.form-actions {
  display: flex;
  justify-content: center;
  padding-top: 18px;
}
.empty-hint {
  padding: 60px 0;
}
</style>
