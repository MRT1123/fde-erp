<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createStockChange, fetchInventory, fetchMaterials, fetchStockMovements,
} from '../api/client'
import type { Inventory, Material, StockMovement } from '../api/types'

const loading = ref(true)
const inventory = ref<Inventory[]>([])
const movements = ref<StockMovement[]>([])
const materials = ref<Material[]>([])
const activeTab = ref('stock')
const keyword = ref('')

const dialogVisible = ref(false)
const saving = ref(false)
const form = ref({
  material_id: undefined as number | undefined,
  movement_type: 'in' as 'in' | 'out' | 'adjust',
  quantity: 1,
  warehouse: 'default',
  remark: '',
})

const moveMap: Record<string, { label: string; type: 'success' | 'warning' | 'danger' | 'info' }> = {
  in: { label: '入库', type: 'success' },
  out: { label: '出库', type: 'warning' },
  adjust: { label: '盘点', type: 'info' },
}

function materialName(id: number): string {
  return materials.value.find((m) => m.id === id)?.name || `#${id}`
}

const filteredInventory = () => {
  if (!keyword.value) return inventory.value
  const k = keyword.value.toLowerCase()
  return inventory.value.filter((inv) => materialName(inv.material_id).toLowerCase().includes(k))
}

function openChange() {
  form.value = { material_id: undefined, movement_type: 'in', quantity: 1, warehouse: 'default', remark: '' }
  dialogVisible.value = true
}

async function saveChange() {
  if (!form.value.material_id) { ElMessage.warning('请选择物料'); return }
  if (form.value.quantity <= 0) { ElMessage.warning('数量必须大于 0'); return }
  saving.value = true
  try {
    await createStockChange({
      material_id: form.value.material_id,
      movement_type: form.value.movement_type,
      quantity: form.value.quantity,
      warehouse: form.value.warehouse,
      remark: form.value.remark || null,
    })
    ElMessage.success('库存变动已记录')
    dialogVisible.value = false
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  } finally {
    saving.value = false
  }
}

async function load() {
  loading.value = true
  try {
    inventory.value = await fetchInventory()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载库存失败')
  }
  try {
    movements.value = await fetchStockMovements()
  } catch { movements.value = [] }
  try {
    materials.value = await fetchMaterials()
  } catch { materials.value = [] }
  loading.value = false
}

onMounted(load)
</script>

<template>
  <div>
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索物料名称" clearable style="width: 260px" />
        <el-button type="primary" @click="openChange">＋ 库存变动</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="实时库存" name="stock">
          <el-table v-loading="loading" :data="filteredInventory()" empty-text="暂无库存记录">
            <el-table-column label="物料" min-width="180">
              <template #default="{ row }">{{ materialName(row.material_id) }}</template>
            </el-table-column>
            <el-table-column prop="warehouse" label="仓库" width="120" />
            <el-table-column label="可用库存" width="110">
              <template #default="{ row }"><span class="qty">{{ row.quantity }}</span></template>
            </el-table-column>
            <el-table-column label="已预留" width="100">
              <template #default="{ row }">{{ row.reserved_quantity }}</template>
            </el-table-column>
            <el-table-column label="安全库存" width="100">
              <template #default="{ row }">{{ row.safety_stock ?? '-' }}</template>
            </el-table-column>
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.quantity <= (row.safety_stock || 0)" type="danger" effect="light" size="small">低于安全库存</el-tag>
                <el-tag v-else type="success" effect="light" size="small">正常</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="更新时间" width="170">
              <template #default="{ row }">{{ row.updated_at?.replace('T', ' ').slice(0, 16) }}</template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="出入库流水" name="movements">
          <el-table :data="movements" empty-text="暂无流水">
            <el-table-column label="物料" min-width="180">
              <template #default="{ row }">{{ materialName(row.material_id) }}</template>
            </el-table-column>
            <el-table-column label="类型" width="100">
              <template #default="{ row }">
                <el-tag :type="moveMap[row.movement_type]?.type || 'info'" effect="light" size="small">
                  {{ moveMap[row.movement_type]?.label || row.movement_type }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="数量" width="100">
              <template #default="{ row }"><span class="qty">{{ row.quantity }}</span></template>
            </el-table-column>
            <el-table-column prop="reference_type" label="来源" width="130">
              <template #default="{ row }">{{ row.reference_type || '手工' }}</template>
            </el-table-column>
            <el-table-column prop="remark" label="备注" min-width="160" show-overflow-tooltip />
            <el-table-column label="时间" width="170">
              <template #default="{ row }">{{ row.created_at?.replace('T', ' ').slice(0, 16) }}</template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="dialogVisible" title="库存变动" width="460px">
      <el-form label-width="80px">
        <el-form-item label="物料" required>
          <el-select v-model="form.material_id" filterable placeholder="选择物料" style="width: 100%">
            <el-option v-for="m in materials" :key="m.id" :label="`${m.name}（${m.code}）`" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型" required>
          <el-radio-group v-model="form.movement_type">
            <el-radio-button value="in">入库</el-radio-button>
            <el-radio-button value="out">出库</el-radio-button>
            <el-radio-button value="adjust">盘点调整</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="数量" required>
          <el-input-number v-model="form.quantity" :min="0.01" :precision="2" style="width: 180px" />
        </el-form-item>
        <el-form-item label="仓库">
          <el-input v-model="form.warehouse" style="width: 180px" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveChange">确认变动</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar-card { margin-bottom: 14px; }
.toolbar { display: flex; align-items: center; justify-content: space-between; }
.qty { font-weight: 600; }
</style>
