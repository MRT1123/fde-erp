<script setup lang="ts">
import { Connection, Cpu, Files } from '@element-plus/icons-vue'

const steps = [
  { icon: Files, title: '录入申请', desc: '在「风控分析」页填写采购申请信息，包括供应商、金额、物料清单与预算。' },
  { icon: Cpu, title: 'Agent 协作分析', desc: 'Supervisor 调度 4 个 Agent：风险分析、供应商尽调、审批建议、异常检测，由 DeepSeek LLM 驱动。' },
  { icon: Connection, title: '输出结论', desc: '聚合风险评分、风险等级、审批建议与异常告警，供 ERP 审批流使用。' },
]

const dimensions = [
  { name: '金额规模', desc: '采购金额越高，风险权重越大（5万/20万/50万阶梯）' },
  { name: '供应商资质', desc: '信用评分、资质状态、首次合作加分' },
  { name: '预算偏差', desc: '是否超出部门预算上限' },
  { name: '历史行为', desc: '同一供应商历史采购频次与金额异常检测' },
]
</script>

<template>
  <div class="guide-page">
    <el-card shadow="never" class="guide-card">
      <template #header><span class="card-title">FDE 智能风控 Agent 使用说明</span></template>
      <div class="steps">
        <div v-for="(s, i) in steps" :key="i" class="step">
          <div class="step-icon"><el-icon :size="20"><component :is="s.icon" /></el-icon></div>
          <div class="step-body">
            <div class="step-no">STEP {{ i + 1 }}</div>
            <div class="step-title">{{ s.title }}</div>
            <div class="step-desc">{{ s.desc }}</div>
          </div>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="guide-card">
      <template #header><span class="card-title">风险维度</span></template>
      <el-table :data="dimensions" stripe>
        <el-table-column prop="name" label="维度" width="160" />
        <el-table-column prop="desc" label="说明" />
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.guide-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.card-title {
  font-weight: 700;
  color: #0f172a;
  font-size: 15px;
}
.guide-card {
  border-radius: 14px;
  border: 1px solid #e7edf5;
}
.steps {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.step {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}
.step-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #2563eb, #38bdf8);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.step-no {
  color: #3b82f6;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
}
.step-title {
  font-weight: 700;
  color: #0f172a;
  font-size: 15px;
  margin: 2px 0;
}
.step-desc {
  color: #475569;
  font-size: 13px;
  line-height: 1.7;
}
</style>
