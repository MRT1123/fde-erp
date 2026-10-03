<template>
  <div class="page">
    <el-card shadow="never" class="page-card">
      <div class="page-head">
        <div>
          <h2 class="page-title">采购订单</h2>
          <p class="page-sub">审批通过的采购申请在此生成订单，收货后自动入库</p>
        </div>
        <el-button type="primary" :icon="Plus" @click="openCreateDialog">生成采购订单</el-button>
      </div>

      <el-table :data="orders" v-loading="loading" stripe>
        <el-table-column prop="order_no" label="订单号" width="150" />
        <el-table-column prop="request_no" label="采购申请号" width="150" />
        <el-table-column prop="supplier_name" label="供应商" min-width="140" />
        <el-table-column prop="department_name" label="部门" width="110" />
        <el-table-column label="金额" width="110" align="right">
          <template #default="{ row }">¥{{ row.total_amount.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">{{ fmt(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
            <el-button
              v-if="['confirmed', 'partial_received'].includes(row.status)"
              link
              type="success"
              @click="openReceive(row)"
            >收货</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 生成订单对话框 -->
    <el-dialog v-model="createVisible" title="生成采购订单" width="560px">
      <p class="dlg-tip">选择已审批通过、尚未下单的采购申请：</p>
      <el-select v-model="selectedRequest" placeholder="选择采购申请" style="width: 100%" filterable>
        <el-option
          v-for="r in eligible"
          :key="r.id"
          :label="`${r.request_no} · ${r.title} · ¥${r.total_amount.toLocaleString()}`"
          :value="r.id"
        />
      </el-select>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" :disabled="!selectedRequest" @click="doCreate">确认生成</el-button>
      </template>
    </el-dialog>

    <!-- 订单详情抽屉 -->
    <el-drawer v-model="detailVisible" :title="detail?.order_no || '订单详情'" size="560px">
      <template v-if="detail">
        <el-descriptions :column="2" border class="mb-16">
          <el-descriptions-item label="采购申请">{{ detail.request_no }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ statusLabel(detail.status) }}</el-descriptions-item>
          <el-descriptions-item label="供应商">{{ detail.supplier_name }}</el-descriptions-item>
          <el-descriptions-item label="部门">{{ detail.department_name }}</el-descriptions-item>
          <el-descriptions-item label="总金额">¥{{ detail.total_amount.toLocaleString() }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ fmt(detail.created_at) }}</el-descriptions-item>
        </el-descriptions>

        <el-table :data="detail.items" border size="small">
          <el-table-column prop="material_name" label="物料" min-width="120" />
          <el-table-column prop="spec" label="规格" width="100" />
          <el-table-column prop="quantity" label="订购" width="70" align="right" />
          <el-table-column prop="received_quantity" label="已收" width="70" align="right" />
          <el-table-column label="金额" width="100" align="right">
            <template #default="{ row }">¥{{ row.amount.toLocaleString() }}</template>
          </el-table-column>
        </el-table>
      </template>
    </el-drawer>

    <!-- 收货对话框 -->
    <el-dialog v-model="receiveVisible" :title="`收货入库 · ${receiveOrder?.order_no || ''}`" width="600px">
      <template v-if="receiveOrder">
        <el-form label-width="90px">
          <el-form-item label="仓库" required>
            <el-input v-model="receiveWarehouse" placeholder="如：主仓 / 华东仓" />
          </el-form-item>
          <el-form-item label="收货明细">
            <div class="receive-items">
              <div v-for="it in receivableItems" :key="it.id" class="receive-item">
                <span class="ri-name">{{ it.material_name }}<el-tag size="small" class="ri-tag">剩余 {{ remaining(it) }}</el-tag></span>
                <el-input-number
                  v-model="it._qty"
                  :min="0"
                  :max="remaining(it)"
                  :step="1"
                  size="small"
                />
              </div>
            </div>
          </el-form-item>
          <el-form-item label="备注">
            <el-input v-model="receiveRemark" placeholder="可选" />
          </el-form-item>
        </el-form>
      </template>
      <template #footer>
        <el-button @click="receiveVisible = false">取消</el-button>
        <el-button type="success" :loading="receiving" @click="doReceive">确认收货</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  fetchPurchaseOrders,
  fetchPurchaseOrderDetail,
  fetchEligibleRequests,
  createPurchaseOrderFromRequest,
  receivePurchaseOrder,
} from '../api/client'
import type { PurchaseOrder, PurchaseOrderItem, EligibleRequest } from '../api/types'

interface ReceiveLine extends PurchaseOrderItem {
  _qty: number
}

const loading = ref(false)
const orders = ref<PurchaseOrder[]>([])
const eligible = ref<EligibleRequest[]>([])
const creating = ref(false)
const createVisible = ref(false)
const selectedRequest = ref<number | null>(null)
const detailVisible = ref(false)
const detail = ref<PurchaseOrder | null>(null)
const receiveVisible = ref(false)
const receiveOrder = ref<PurchaseOrder | null>(null)
const receiveWarehouse = ref('主仓')
const receiveRemark = ref('')
const receiving = ref(false)

const receivableItems = computed<ReceiveLine[]>(() =>
  (receiveOrder.value?.items || [])
    .filter((it) => remaining(it) > 0)
    .map((it) => ({ ...it, _qty: remaining(it) })),
)

function statusType(s: string) {
  return ({ confirmed: 'warning', partial_received: 'primary', received: 'success', cancelled: 'info' } as Record<string, any>)[s] || 'info'
}
function statusLabel(s: string) {
  return ({ confirmed: '待收货', partial_received: '部分收货', received: '已收货', cancelled: '已取消' } as Record<string, string>)[s] || s
}
function fmt(v?: string | null) {
  return v ? v.replace('T', ' ').slice(0, 16) : '-'
}
function remaining(it: PurchaseOrderItem) {
  return Math.round((it.quantity - (it.received_quantity || 0)) * 100) / 100
}

async function load() {
  loading.value = true
  try {
    orders.value = await fetchPurchaseOrders()
  } finally {
    loading.value = false
  }
}

async function openCreateDialog() {
  eligible.value = await fetchEligibleRequests()
  selectedRequest.value = null
  createVisible.value = true
}

async function doCreate() {
  if (!selectedRequest.value) return
  creating.value = true
  try {
    await createPurchaseOrderFromRequest(selectedRequest.value)
    ElMessage.success('采购订单已生成')
    createVisible.value = false
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '生成失败')
  } finally {
    creating.value = false
  }
}

async function openDetail(row: PurchaseOrder) {
  detailVisible.value = true
  detail.value = await fetchPurchaseOrderDetail(row.id)
}

async function openReceive(row: PurchaseOrder) {
  receiveOrder.value = await fetchPurchaseOrderDetail(row.id)
  receiveWarehouse.value = '主仓'
  receiveRemark.value = ''
  receiveVisible.value = true
}

async function doReceive() {
  const order = receiveOrder.value
  if (!order || !receiveWarehouse.value.trim()) {
    ElMessage.warning('请填写仓库')
    return
  }
  const items = receivableItems.value
    .filter((it) => it._qty > 0)
    .map((it) => ({ order_item_id: it.id, quantity: it._qty }))
  if (!items.length) {
    ElMessage.warning('请选择收货数量')
    return
  }
  receiving.value = true
  try {
    await receivePurchaseOrder(order.id, receiveWarehouse.value.trim(), items, receiveRemark.value)
    ElMessage.success('收货成功，已自动入库')
    receiveVisible.value = false
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '收货失败')
  } finally {
    receiving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}
.page-title {
  margin: 0;
  font-size: 20px;
}
.page-sub {
  margin: 4px 0 0;
  color: #909399;
  font-size: 13px;
}
.dlg-tip {
  color: #909399;
  margin: 0 0 8px;
  font-size: 13px;
}
.mb-16 {
  margin-bottom: 16px;
}
.receive-items {
  width: 100%;
}
.receive-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px dashed #eee;
}
.ri-name {
  font-size: 14px;
}
.ri-tag {
  margin-left: 8px;
}
</style>
