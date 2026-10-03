<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, RefreshRight } from '@element-plus/icons-vue'
import { dueDiligence } from '../api/client'
import type { DueDiligenceReport } from '../api/types'

const loading = ref(false)
const result = ref<DueDiligenceReport | null>(null)

const form = reactive({
  supplier_id: 0,
  supplier_name: '',
})

async function run() {
  loading.value = true
  result.value = null
  try {
    result.value = await dueDiligence(form.supplier_id, form.supplier_name)
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '尽调失败，请确认 FDE 服务已启动'
    ElMessage.error(String(msg))
  } finally {
    loading.value = false
  }
}

function fillDemo() {
  Object.assign(form, {
    supplier_id: 2,
    supplier_name: '华信科技',
  })
}

const riskLevel = () => result.value?.risk_level || 'unknown'
const levelTag = () => {
  const lv = riskLevel()
  if (lv === 'high') return 'danger'
  if (lv === 'medium') return 'warning'
  return 'success'
}
const levelText = () => {
  const lv = riskLevel()
  if (lv === 'high') return '高风险'
  if (lv === 'medium') return '中风险'
  return '低风险'
}
</script>

<template>
  <div class="dd-page">
    <!-- 输入 -->
    <el-card class="form-card" shadow="never">
      <template #header>
        <div class="card-head">
          <span class="card-title">供应商尽调输入</span>
          <el-button size="small" :icon="RefreshRight" @click="fillDemo">填入示例</el-button>
        </div>
      </template>
      <el-form label-width="110px" label-position="left">
        <el-row :gutter="16">
          <el-col :md="8" :sm="12" :xs="24">
            <el-form-item label="供应商 ID">
              <el-input-number v-model="form.supplier_id" :min="0" placeholder="如：2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :md="12" :sm="12" :xs="24">
            <el-form-item label="供应商名称">
              <el-input v-model="form.supplier_name" placeholder="供应商名称" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <div class="form-actions">
              <el-button type="primary" size="large" :loading="loading" :icon="Search" @click="run">
                {{ loading ? '尽调中…' : '开始供应商尽调' }}
              </el-button>
            </div>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 结果 -->
    <template v-if="result">
      <div class="result-grid">
        <el-card shadow="never" class="score-card">
          <template #header><span class="card-title">尽调结论</span></template>
          <div class="verdict-wrap">
            <el-tag :type="levelTag()" size="large" effect="dark">{{ levelText() }}</el-tag>
            <div class="risk-count">风险信号 <b>{{ result.risk_flags?.length ?? 0 }}</b> 条</div>
            <el-descriptions :column="1" size="small" class="score-desc">
              <el-descriptions-item label="供应商">{{ result.supplier_name }}</el-descriptions-item>
              <el-descriptions-item label="供应商 ID">{{ result.supplier_id }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>

        <el-card shadow="never" class="analysis-card">
          <template #header><span class="card-title">尽调报告</span></template>
          <p class="analysis-text">{{ result.report_content || '未生成尽调报告。' }}</p>
        </el-card>
      </div>

      <el-card shadow="never" class="reason-card">
        <template #header><span class="card-title">风险信号</span></template>
        <ul class="reason-list">
          <li v-for="(f, i) in result.risk_flags || []" :key="i">{{ f }}</li>
          <li v-if="!result.risk_flags?.length">未发现明确风险信号。</li>
        </ul>
      </el-card>

      <el-card shadow="never" class="reason-card">
        <template #header><span class="card-title">舆情信息（公开搜索）</span></template>
        <template v-if="result.news?.length">
          <el-table :data="result.news" stripe>
            <el-table-column prop="title" label="标题" min-width="220" />
            <el-table-column prop="source" label="来源" width="140" />
            <el-table-column prop="date" label="时间" width="130" />
            <el-table-column prop="snippet" label="摘要" min-width="260" />
          </el-table>
        </template>
        <el-empty v-else description="未搜索到相关舆情" />
      </el-card>
    </template>
    <el-empty v-else-if="!loading" description="填写供应商信息后，点击「开始供应商尽调」" class="empty-hint" />
  </div>
</template>

<style scoped>
.dd-page {
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
.form-card, .score-card, .analysis-card, .reason-card {
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
.verdict-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  padding: 14px 0;
}
.risk-count {
  color: #64748b;
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
.empty-hint {
  padding: 60px 0;
}
</style>
