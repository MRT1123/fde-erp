<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  DataAnalysis, DocumentChecked, ShoppingCart, User, Box,
  Coin, Grid, Aim, Money, Tickets,
} from '@element-plus/icons-vue'
import { fetchEmployees } from '../api/client'
import type { Employee } from '../api/types'
import { useCurrentUser } from '../composables/useCurrentUser'

const route = useRoute()
const activeMenu = computed(() => route.path)
const pageTitle = computed(() => (route.meta.title as string) || '智能采购风控平台')

const employees = ref<Employee[]>([])
const { currentUser, setUser } = useCurrentUser()
const selectedUserId = ref<number | null>(currentUser.value?.id ?? null)

async function loadEmployees() {
  try {
    employees.value = await fetchEmployees()
  } catch {
    employees.value = []
  }
}

function onUserChange(id: number) {
  const emp = employees.value.find((e) => e.id === id) ?? null
  setUser(emp)
}

onMounted(loadEmployees)

const navItems = [
  { path: '/dashboard', label: '数据看板', icon: Grid },
  { path: '/purchase', label: '采购申请', icon: ShoppingCart },
  { path: '/approvals', label: '审批工作台', icon: DocumentChecked },
  { path: '/suppliers', label: '供应商管理', icon: User },
  { path: '/materials', label: '物料档案', icon: Box },
  { path: '/inventory', label: '库存管理', icon: Coin },
  { path: '/budget', label: '预算管控', icon: Money },
  { path: '/purchase-orders', label: '采购订单', icon: Tickets },
  { path: '/risk', label: 'AI 风控分析', icon: Aim },
]
</script>

<template>
  <el-container class="app-shell">
    <el-aside width="232px" class="app-aside">
      <div class="brand">
        <div class="brand-logo">ERP</div>
        <div class="brand-text">
          <div class="brand-name">智能采购风控</div>
          <div class="brand-sub">ERP · FDE</div>
        </div>
      </div>
      <el-menu :default-active="activeMenu" router class="side-menu" background-color="transparent">
        <el-menu-item v-for="item in navItems" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>
      <div class="aside-footer">
        <div class="status-dot"></div>
        风控引擎运行中
      </div>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <div class="header-title">
          <el-icon class="header-icon"><DataAnalysis /></el-icon>
          <span>{{ pageTitle }}</span>
        </div>
        <div class="header-actions">
          <el-select
            v-model="selectedUserId"
            placeholder="选择登录用户"
            style="width: 180px"
            @change="onUserChange"
          >
            <el-option
              v-for="e in employees"
              :key="e.id"
              :label="`${e.name}（${e.employee_no}）`"
              :value="e.id"
            />
          </el-select>
          <el-tag type="success" effect="light" round>DeepSeek Agent</el-tag>
          <el-tag type="info" effect="plain" round>飞书联动</el-tag>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
}
.app-aside {
  background: linear-gradient(180deg, #ffffff 0%, #f7fafd 100%);
  border-right: 1px solid #e8eef5;
  display: flex;
  flex-direction: column;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 22px 20px 18px;
}
.brand-logo {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, #4f8cff 0%, #6ec6ff 100%);
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 14px rgba(79, 140, 255, 0.28);
}
.brand-name {
  font-weight: 700;
  font-size: 15px;
  color: #1f2d3d;
}
.brand-sub {
  font-size: 12px;
  color: #8ba0b8;
  letter-spacing: 1px;
}
.side-menu {
  border-right: none;
  flex: 1;
}
.side-menu :deep(.el-menu-item) {
  height: 46px;
  margin: 3px 12px;
  border-radius: 10px;
  color: #5b6b7d;
}
.side-menu :deep(.el-menu-item:hover) {
  background: #f2f7ff;
  color: #3b82f6;
}
.side-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, #eaf2ff, #f0f7ff);
  color: #2f6fed;
  font-weight: 600;
}
.side-menu :deep(.el-menu-item .el-icon) {
  color: inherit;
}
.aside-footer {
  padding: 16px 20px;
  font-size: 12px;
  color: #7a8fa5;
  display: flex;
  align-items: center;
  gap: 8px;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #34c98f;
  box-shadow: 0 0 0 3px rgba(52, 201, 143, 0.18);
}
.app-header {
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid #e8eef5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 24px;
}
.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: #24344a;
}
.header-icon {
  color: #3b82f6;
  font-size: 20px;
}
.header-actions {
  display: flex;
  gap: 10px;
}
.app-main {
  background: #f4f8fc;
  padding: 20px 24px;
}
</style>
