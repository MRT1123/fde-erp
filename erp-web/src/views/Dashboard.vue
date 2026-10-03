<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import {
  fetchDashboardSummary, fetchRiskDistribution, fetchStatusDistribution,
  fetchSupplierRisk, fetchApprovalTimeline,
} from '../api/client'
import type { DashboardSummary } from '../api/types'

const loading = ref(true)
const summary = ref<DashboardSummary>({
  total_requests: 0, approved: 0, pending_approval: 0, total_amount: 0,
  high_risk_requests: 0, supplier_count: 0,
})
const supplierRisk = ref<Array<{ supplier_name: string; risk_level: string; request_count: number; total_amount: number }>>([])

const statCards = computed(() => [
  { label: '采购申请总数', value: summary.value.total_requests, color: '#3b82f6', icon: '📋' },
  { label: '已审批通过', value: summary.value.approved, color: '#34c98f', icon: '✅' },
  { label: '待人工审批', value: summary.value.pending_approval, color: '#f59e0b', icon: '⏳' },
  { label: '采购总额', value: `¥${(summary.value.total_amount / 10000).toFixed(1)}万`, color: '#8b5cf6', icon: '💰' },
  { label: '高风险申请', value: summary.value.high_risk_requests, color: '#ef4444', icon: '⚠️' },
  { label: '供应商数', value: summary.value.supplier_count, color: '#06b6d4', icon: '🏢' },
])

let riskChart: echarts.ECharts | null = null
let statusChart: echarts.ECharts | null = null
let timelineChart: echarts.ECharts | null = null

function renderCharts() {
  const riskEl = document.getElementById('riskChart')
  const statusEl = document.getElementById('statusChart')
  const timelineEl = document.getElementById('timelineChart')
  if (!riskEl || !statusEl || !timelineEl) return

  riskChart?.dispose()
  statusChart?.dispose()
  timelineChart?.dispose()

  // 风险分布 - 环形图
  loadRiskDist().then((data) => {
    const labels: Record<string, string> = { high: '高风险', medium: '中风险', low: '低风险' }
    const seriesData = Object.entries(data).map(([k, v]) => ({ name: labels[k] || k, value: v }))
    riskChart = echarts.init(riskEl)
    riskChart.setOption({
      color: ['#ef4444', '#f59e0b', '#34c98f'],
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, textStyle: { color: '#5b6b7d' } },
      series: [{
        type: 'pie', radius: ['42%', '66%'], center: ['50%', '44%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
        label: { show: false },
        emphasis: { label: { show: true, fontWeight: 'bold' } },
        data: seriesData,
      }],
    })
  })

  // 状态分布 - 柱状图
  loadStatusDist().then((data) => {
    const labels: Record<string, string> = {
      draft: '草稿', pending_approval: '待审批', approved: '已通过',
      rejected: '已驳回', withdrawn: '已撤回',
    }
    statusChart = echarts.init(statusEl)
    statusChart.setOption({
      color: ['#3b82f6'],
      tooltip: { trigger: 'axis' },
      grid: { left: 32, right: 16, top: 24, bottom: 30 },
      xAxis: { type: 'category', data: Object.keys(data).map((k) => labels[k] || k), axisLabel: { color: '#5b6b7d' } },
      yAxis: { type: 'value', axisLabel: { color: '#8ba0b8' }, splitLine: { lineStyle: { color: '#eef3f9' } } },
      series: [{
        type: 'bar', data: Object.values(data),
        barWidth: 34, itemStyle: { borderRadius: [8, 8, 0, 0] },
      }],
    })
  })

  // 审批时间线 - 折线图
  loadTimeline().then((data) => {
    timelineChart = echarts.init(timelineEl)
    timelineChart.setOption({
      color: ['#3b82f6', '#8b5cf6'],
      tooltip: { trigger: 'axis' },
      legend: { data: ['审批数', '金额(万)'], bottom: 0, textStyle: { color: '#5b6b7d' } },
      grid: { left: 44, right: 16, top: 30, bottom: 44 },
      xAxis: { type: 'category', data: data.map((d) => d.date), axisLabel: { color: '#5b6b7d' } },
      yAxis: [
        { type: 'value', name: '审批数', axisLabel: { color: '#8ba0b8' }, splitLine: { lineStyle: { color: '#eef3f9' } } },
        { type: 'value', name: '金额(万)', axisLabel: { color: '#8ba0b8' }, splitLine: { show: false } },
      ],
      series: [
        { name: '审批数', type: 'line', smooth: true, data: data.map((d) => d.count), areaStyle: { opacity: 0.12 } },
        { name: '金额(万)', type: 'line', yAxisIndex: 1, smooth: true, data: data.map((d) => +(d.amount / 10000).toFixed(1)) },
      ],
    })
  })
}

async function loadRiskDist() {
  try { return await fetchRiskDistribution() } catch { return {} }
}
async function loadStatusDist() {
  try { return await fetchStatusDistribution() } catch { return {} }
}
async function loadTimeline() {
  try { return await fetchApprovalTimeline() } catch { return [] }
}

async function loadAll() {
  loading.value = true
  try {
    summary.value = await fetchDashboardSummary()
  } catch (e) {
    console.error(e)
  }
  try { supplierRisk.value = await fetchSupplierRisk() } catch { supplierRisk.value = [] }
  renderCharts()
  loading.value = false
}

onMounted(loadAll)
</script>

<template>
  <div class="dashboard">
    <div class="stat-grid">
      <el-card v-for="card in statCards" :key="card.label" shadow="never" class="stat-card">
        <div class="stat-inner">
          <div class="stat-icon" :style="{ background: card.color + '1a', color: card.color }">{{ card.icon }}</div>
          <div>
            <div class="stat-value" :style="{ color: card.color }">{{ card.value }}</div>
            <div class="stat-label">{{ card.label }}</div>
          </div>
        </div>
      </el-card>
    </div>

    <div class="chart-grid">
      <el-card shadow="never" class="chart-card">
        <template #header>
          <div class="card-title">风险分布</div>
        </template>
        <div id="riskChart" class="chart"></div>
      </el-card>
      <el-card shadow="never" class="chart-card">
        <template #header>
          <div class="card-title">申请状态分布</div>
        </template>
        <div id="statusChart" class="chart"></div>
      </el-card>
    </div>

    <div class="chart-grid">
      <el-card shadow="never" class="chart-card wide">
        <template #header>
          <div class="card-title">审批趋势</div>
        </template>
        <div id="timelineChart" class="chart chart-tall"></div>
      </el-card>
      <el-card shadow="never" class="chart-card">
        <template #header>
          <div class="card-title">供应商风险</div>
        </template>
        <el-table :data="supplierRisk" size="small" empty-text="暂无数据">
          <el-table-column prop="supplier_name" label="供应商" min-width="100" />
          <el-table-column label="风险" width="80">
            <template #default="{ row }">
              <el-tag :type="row.risk_level === 'high' ? 'danger' : row.risk_level === 'medium' ? 'warning' : 'success'" size="small">
                {{ row.risk_level === 'high' ? '高' : row.risk_level === 'medium' ? '中' : '低' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="request_count" label="申请数" width="70" />
          <el-table-column label="金额(万)" width="90">
            <template #default="{ row }">{{ (row.total_amount / 10000).toFixed(1) }}</template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.stat-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 14px;
}
.stat-card :deep(.el-card__body) {
  padding: 18px;
}
.stat-inner {
  display: flex;
  align-items: center;
  gap: 12px;
}
.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}
.stat-value {
  font-size: 22px;
  font-weight: 700;
  line-height: 1.2;
}
.stat-label {
  font-size: 12px;
  color: #8ba0b8;
  margin-top: 2px;
}
.chart-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.chart-card.wide {
  grid-column: span 1;
}
.card-title {
  font-weight: 600;
  color: #24344a;
}
.chart {
  height: 240px;
}
.chart-tall {
  height: 300px;
}
@media (max-width: 1100px) {
  .stat-grid { grid-template-columns: repeat(3, 1fr); }
  .chart-grid { grid-template-columns: 1fr; }
}
</style>
