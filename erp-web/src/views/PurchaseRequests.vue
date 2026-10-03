<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createPurchaseRequest, fetchMaterials, fetchPurchaseRequests, fetchSuppliers, submitPurchaseRequest } from '../api/client'
import type { Material, PurchaseRequest, Supplier } from '../api/types'
import { useCurrentUser } from '../composables/useCurrentUser'

const router = useRouter()
const { currentUser } = useCurrentUser()
const loading = ref(false)
const list = ref<PurchaseRequest[]>([])
const materials = ref<Material[]>([])
const suppliers = ref<Supplier[]>([])
const keyword = ref('')

const statusMap: Record<string, { label: string; type: 'info' | 'warning' | 'success' | 'danger' }> = {
  draft: { label: '草稿', type: 'info' },
  pending_approval: { label: '待审批', type: 'warning' },
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' },
  withdrawn: { label: '已撤回', type: 'info' },
}
const riskMap: Record<string, { label: string; type: 'success' | 'warning' | 'danger' }> = {
  low: { label: '低', type: 'success' },
  medium: { label: '中', type: 'warning' },
  high: { label: '高', type: 'danger' },
}

const filtered = () => {
  if (!keyword.value) return list.value
  const k = keyword.value.toLowerCase()
  return list.value.filter(
    (p) => p.request_no.toLowerCase().includes(k) || p.title.toLowerCase().includes(k)
  )
}

// 新建采购单
const dialogVisible = ref(false)
const saving = ref(false)
const form = ref({
  title: '',
  supplier_id: undefined as number | undefined,
  purpose: '',
  items: [{ material_name: '', quantity: 1, unit_price: 0, spec: '', remark: '' }],
})

function openCreate() {
  if (!currentUser.value) {
    ElMessage.warning('请先在右上角选择登录用户')
    return
  }
  form.value = { title: '', supplier_id: undefined, purpose: '', items: [{ material_name: '', quantity: 1, unit_price: 0, spec: '', remark: '' }] }
  dialogVisible.value = true
}

function addItem() {
  form.value.items.push({ material_name: '', quantity: 1, unit_price: 0, spec: '', remark: '' })
}
function removeItem(i: number) {
  if (form.value.items.length > 1) form.value.items.splice(i, 1)
}

async function submitCreate() {
  if (!form.value.title) { ElMessage.warning('请填写采购标题'); return }
  const validItems = form.value.items.filter((it) => it.material_name && it.quantity > 0)
  if (!validItems.length) { ElMessage.warning('请至少填写一条有效的采购明细'); return }
  saving.value = true
  try {
    const created = await createPurchaseRequest({
      title: form.value.title,
      supplier_id: form.value.supplier_id ?? null,
      purpose: form.value.purpose || null,
      applicant_id: currentUser.value?.id ?? null,
      department_id: currentUser.value?.department_id ?? null,
      items: validItems.map((it) => ({
        material_name: it.material_name,
        spec: it.spec || null,
        quantity: it.quantity,
        unit_price: it.unit_price || null,
        remark: it.remark || null,
      })),
    })
    ElMessage.success(`采购单 ${created.request_no} 创建成功`)
    dialogVisible.value = false
    await load()
    router.push(`/purchase/${created.id}`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '创建失败')
  } finally {
    saving.value = false
  }
}

function pickMaterial(i: number, name: string) {
  const m = materials.value.find((x) => x.name === name)
  if (m) {
    form.value.items[i].spec = m.spec || ''
    if (!form.value.items[i].unit_price && m.default_price) form.value.items[i].unit_price = m.default_price
  }
}

async function submitRequest(p: PurchaseRequest) {
  try {
    await submitPurchaseRequest(p.id)
    ElMessage.success('已提交风控分析')
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '提交失败')
  }
}

async function load() {
  loading.value = true
  try {
    list.value = await fetchPurchaseRequests()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载采购单失败')
  }
  loading.value = false
}

onMounted(async () => {
  await load()
  try { materials.value = await fetchMaterials() } catch { materials.value = [] }
  try { suppliers.value = await fetchSuppliers() } catch { suppliers.value = [] }
})
</script>

<template>
  <div>
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索单号 / 标题" clearable style="width: 260px">
          <template #prefix><span>🔍</span></template>
        </el-input>
        <el-button type="primary" @click="openCreate">＋ 新建采购申请</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="filtered()" empty-text="暂无采购申请" @row-click="(row: PurchaseRequest) => router.push(`/purchase/${row.id}`)">
        <el-table-column prop="request_no" label="单号" width="150">
          <template #default="{ row }"><span class="no">{{ row.request_no }}</span></template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column label="金额" width="120">
          <template #default="{ row }"><span class="amount">¥{{ row.total_amount.toLocaleString() }}</span></template>
        </el-table-column>
        <el-table-column label="风险" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.risk_level" :type="riskMap[row.risk_level]?.type" effect="light" round>
              {{ riskMap[row.risk_level]?.label }} {{ row.risk_score ?? '' }}
            </el-tag>
            <span v-else class="muted">未评估</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type" effect="light" round>{{ statusMap[row.status]?.label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="人工复核" width="100">
          <template #default="{ row }">
            <el-icon v-if="row.needs_human_review" color="#f59e0b"><Warning /></el-icon>
            <span v-else class="muted">自动</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">{{ row.created_at?.replace('T', ' ').slice(0, 16) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'draft'" size="small" type="primary" text @click.stop="submitRequest(row)">提交</el-button>
            <el-button size="small" text @click.stop="router.push(`/purchase/${row.id}`)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="新建采购申请" width="640px" destroy-on-close>
      <el-form label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" placeholder="如：采购服务器 50 台" />
        </el-form-item>
        <el-form-item label="供应商">
          <el-select v-model="form.supplier_id" placeholder="选择供应商（可选）" clearable filterable style="width: 100%">
            <el-option v-for="s in suppliers" :key="s.id" :label="`${s.name}（${s.code}）`" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="采购用途">
          <el-input v-model="form.purpose" type="textarea" :rows="2" placeholder="如：机房扩容，新增算力节点" />
        </el-form-item>
      </el-form>

      <div class="items-header">
        <span class="items-title">采购明细</span>
        <el-button size="small" text type="primary" @click="addItem">＋ 添加明细</el-button>
      </div>
      <div v-for="(it, i) in form.items" :key="i" class="item-row">
        <el-select v-model="it.material_name" filterable allow-create placeholder="物料名称" style="flex: 2" @change="(v: string) => pickMaterial(i, v)">
          <el-option v-for="m in materials" :key="m.id" :label="m.name" :value="m.name" />
        </el-select>
        <el-input-number v-model="it.quantity" :min="1" placeholder="数量" style="width: 90px" />
        <el-input-number v-model="it.unit_price" :min="0" :precision="2" placeholder="单价" style="width: 110px" />
        <el-input v-model="it.spec" placeholder="规格(可选)" style="flex: 1" />
        <el-button size="small" text type="danger" :disabled="form.items.length === 1" @click="removeItem(i)">删除</el-button>
      </div>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitCreate">创建并提交风控</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar-card {
  margin-bottom: 14px;
}
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.no {
  color: #2f6fed;
  font-weight: 600;
}
.amount {
  font-weight: 600;
  color: #1f2d3d;
}
.muted {
  color: #a5b6c9;
  font-size: 12px;
}
.items-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 12px 0 8px;
}
.items-title {
  font-weight: 600;
  color: #24344a;
}
.item-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
</style>
