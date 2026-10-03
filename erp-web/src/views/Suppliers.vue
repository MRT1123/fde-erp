<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createSupplier, fetchSupplierRiskReport, fetchSuppliers, updateSupplier,
} from '../api/client'
import type { Supplier, SupplierRiskReport } from '../api/types'

const loading = ref(true)
const list = ref<Supplier[]>([])
const keyword = ref('')

// 新建 / 编辑
const dialogVisible = ref(false)
const editMode = ref(false)
const saving = ref(false)
const form = ref({
  name: '', contact_person: '', phone: '', email: '', address: '', tax_no: '',
})
const editId = ref<number | null>(null)

// 风险报告
const reportVisible = ref(false)
const report = ref<SupplierRiskReport | null>(null)
const reportLoading = ref(false)

const riskMap: Record<string, { label: string; type: 'success' | 'warning' | 'danger' | 'info' }> = {
  low: { label: '低', type: 'success' },
  medium: { label: '中', type: 'warning' },
  high: { label: '高', type: 'danger' },
}
const qualMap: Record<string, { label: string; type: 'success' | 'warning' | 'danger' | 'info' }> = {
  verified: { label: '已认证', type: 'success' },
  pending: { label: '待认证', type: 'warning' },
  expired: { label: '已过期', type: 'danger' },
  unverified: { label: '未认证', type: 'info' },
}

const filtered = () => {
  if (!keyword.value) return list.value
  const k = keyword.value.toLowerCase()
  return list.value.filter((s) => s.name.toLowerCase().includes(k) || s.code.toLowerCase().includes(k))
}

function openCreate() {
  editMode.value = false
  editId.value = null
  form.value = { name: '', contact_person: '', phone: '', email: '', address: '', tax_no: '' }
  dialogVisible.value = true
}

function openEdit(row: Supplier) {
  editMode.value = true
  editId.value = row.id
  form.value = {
    name: row.name, contact_person: row.contact_person || '', phone: row.phone || '',
    email: row.email || '', address: '', tax_no: '',
  }
  dialogVisible.value = true
}

async function save() {
  if (!form.value.name) { ElMessage.warning('请填写供应商名称'); return }
  saving.value = true
  try {
    if (editMode.value && editId.value != null) {
      await updateSupplier(editId.value, { name: form.value.name, contact_person: form.value.contact_person || null, phone: form.value.phone || null, email: form.value.email || null })
      ElMessage.success('供应商已更新')
    } else {
      await createSupplier({ name: form.value.name, contact_person: form.value.contact_person || null, phone: form.value.phone || null, email: form.value.email || null, address: form.value.address || null, tax_no: form.value.tax_no || null })
      ElMessage.success('供应商已创建')
    }
    dialogVisible.value = false
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function openReport(row: Supplier) {
  reportLoading.value = true
  reportVisible.value = true
  try {
    report.value = await fetchSupplierRiskReport(row.id)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '获取风险报告失败')
    reportVisible.value = false
  } finally {
    reportLoading.value = false
  }
}

async function load() {
  loading.value = true
  try {
    list.value = await fetchSuppliers()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载供应商失败')
  }
  loading.value = false
}

onMounted(load)
</script>

<template>
  <div>
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索名称 / 编码" clearable style="width: 260px" />
        <el-button type="primary" @click="openCreate">＋ 新增供应商</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="filtered()" empty-text="暂无供应商">
        <el-table-column prop="code" label="编码" width="130">
          <template #default="{ row }"><span class="no">{{ row.code }}</span></template>
        </el-table-column>
        <el-table-column prop="name" label="名称" min-width="180" />
        <el-table-column prop="contact_person" label="联系人" width="110" />
        <el-table-column prop="phone" label="电话" width="140" />
        <el-table-column label="资质" width="100">
          <template #default="{ row }">
            <el-tag :type="qualMap[row.qualification_status]?.type || 'info'" effect="light" size="small">
              {{ qualMap[row.qualification_status]?.label || row.qualification_status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="风险" width="100">
          <template #default="{ row }">
            <el-tag :type="riskMap[row.risk_level]?.type || 'info'" effect="light" size="small">
              {{ riskMap[row.risk_level]?.label || row.risk_level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="首次合作" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.first_cooperation" type="warning" effect="light" size="small">是</el-tag>
            <span v-else class="muted">否</span>
          </template>
        </el-table-column>
        <el-table-column prop="credit_score" label="信用分" width="90">
          <template #default="{ row }">{{ row.credit_score ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="openReport(row)">风险报告</el-button>
            <el-button size="small" text @click="openEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editMode ? '编辑供应商' : '新增供应商'" width="520px">
      <el-form label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="供应商全称" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact_person" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item v-if="!editMode" label="地址">
          <el-input v-model="form.address" />
        </el-form-item>
        <el-form-item v-if="!editMode" label="税号">
          <el-input v-model="form.tax_no" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="reportVisible" title="供应商风险报告" width="560px">
      <div v-loading="reportLoading">
        <template v-if="report">
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="供应商">{{ report.supplier_name }}</el-descriptions-item>
            <el-descriptions-item label="风险等级">
              <el-tag :type="riskMap[report.risk_level]?.type || 'info'" effect="light">
                {{ riskMap[report.risk_level]?.label || report.risk_level }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="报告日期">{{ report.report_date }}</el-descriptions-item>
          </el-descriptions>
          <div v-if="report.risk_flags?.length" class="flag-box">
            <div class="flag-title">风险信号</div>
            <el-tag v-for="(f, i) in report.risk_flags" :key="i" type="warning" effect="light" class="flag-tag">{{ f }}</el-tag>
          </div>
          <div v-if="report.report_content" class="content-box">
            <div class="content-title">报告内容</div>
            <div class="content-text">{{ report.report_content }}</div>
          </div>
        </template>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar-card { margin-bottom: 14px; }
.toolbar { display: flex; align-items: center; justify-content: space-between; }
.no { color: #2f6fed; font-weight: 600; }
.muted { color: #a5b6c9; font-size: 12px; }
.flag-box { margin-top: 14px; }
.flag-title { font-weight: 600; color: #24344a; margin-bottom: 8px; font-size: 13px; }
.flag-tag { margin: 0 8px 8px 0; }
.content-box { margin-top: 14px; }
.content-title { font-weight: 600; color: #24344a; margin-bottom: 8px; font-size: 13px; }
.content-text { color: #44566c; line-height: 1.7; font-size: 13px; white-space: pre-wrap; background: #f6faff; border-radius: 10px; padding: 12px 14px; }
</style>
