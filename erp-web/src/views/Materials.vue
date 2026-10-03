<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createMaterial, fetchMaterials, updateMaterial } from '../api/client'
import type { Material } from '../api/types'

const loading = ref(true)
const list = ref<Material[]>([])
const keyword = ref('')

const dialogVisible = ref(false)
const editMode = ref(false)
const editId = ref<number | null>(null)
const saving = ref(false)
const form = ref({
  code: '', name: '', category: '', spec: '', unit: '件', default_price: undefined as number | undefined,
})

const categories = ['服务器', '网络设备', '办公用品', '原材料', '耗材', '其他']

const filtered = () => {
  if (!keyword.value) return list.value
  const k = keyword.value.toLowerCase()
  return list.value.filter(
    (m) => m.name.toLowerCase().includes(k) || m.code.toLowerCase().includes(k) || m.category.toLowerCase().includes(k)
  )
}

function openCreate() {
  editMode.value = false
  editId.value = null
  form.value = { code: '', name: '', category: '其他', spec: '', unit: '件', default_price: undefined }
  dialogVisible.value = true
}

function openEdit(row: Material) {
  editMode.value = true
  editId.value = row.id
  form.value = {
    code: row.code, name: row.name, category: row.category, spec: row.spec || '',
    unit: row.unit, default_price: row.default_price ?? undefined,
  }
  dialogVisible.value = true
}

async function save() {
  if (!form.value.code || !form.value.name || !form.value.category) {
    ElMessage.warning('请填写编码、名称、分类'); return
  }
  saving.value = true
  try {
    if (editMode.value && editId.value != null) {
      await updateMaterial(editId.value, {
        name: form.value.name, category: form.value.category, spec: form.value.spec || null,
        unit: form.value.unit, default_price: form.value.default_price ?? null,
      })
      ElMessage.success('物料已更新')
    } else {
      await createMaterial({
        code: form.value.code, name: form.value.name, category: form.value.category,
        spec: form.value.spec || null, unit: form.value.unit, default_price: form.value.default_price ?? null,
      })
      ElMessage.success('物料已创建')
    }
    dialogVisible.value = false
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function load() {
  loading.value = true
  try {
    list.value = await fetchMaterials()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载物料失败')
  }
  loading.value = false
}

onMounted(load)
</script>

<template>
  <div>
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索名称 / 编码 / 分类" clearable style="width: 280px" />
        <el-button type="primary" @click="openCreate">＋ 新增物料</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table v-loading="loading" :data="filtered()" empty-text="暂无物料">
        <el-table-column prop="code" label="编码" width="130">
          <template #default="{ row }"><span class="no">{{ row.code }}</span></template>
        </el-table-column>
        <el-table-column prop="name" label="名称" min-width="170" />
        <el-table-column label="分类" width="110">
          <template #default="{ row }">
            <el-tag effect="plain" size="small">{{ row.category }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="spec" label="规格" min-width="140" />
        <el-table-column prop="unit" label="单位" width="70" />
        <el-table-column label="默认价" width="110">
          <template #default="{ row }">{{ row.default_price != null ? `¥${row.default_price}` : '-' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" effect="light" size="small">
              {{ row.status === 'active' ? '启用' : row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text @click="openEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editMode ? '编辑物料' : '新增物料'" width="520px">
      <el-form label-width="80px">
        <el-form-item label="编码" required>
          <el-input v-model="form.code" :disabled="editMode" placeholder="如：SRV-001" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="分类" required>
          <el-select v-model="form.category" filterable allow-create style="width: 100%">
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="规格">
          <el-input v-model="form.spec" />
        </el-form-item>
        <el-form-item label="单位">
          <el-input v-model="form.unit" style="width: 160px" />
        </el-form-item>
        <el-form-item label="默认价">
          <el-input-number v-model="form.default_price" :min="0" :precision="2" style="width: 180px" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar-card { margin-bottom: 14px; }
.toolbar { display: flex; align-items: center; justify-content: space-between; }
.no { color: #2f6fed; font-weight: 600; }
</style>
