<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DataAnalysis, Guide, Shop, Warning } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const title = computed(() => (route.meta.title as string) || '')
const menus = [
  { path: '/risk', label: '风控分析', icon: DataAnalysis },
  { path: '/due-diligence', label: '供应商尽调', icon: Shop },
  { path: '/anomaly', label: '异常检测', icon: Warning },
  { path: '/guide', label: '使用说明', icon: Guide },
]
</script>

<template>
  <div class="fde-shell">
    <aside class="fde-sidebar">
      <div class="brand">
        <div class="brand-logo">FDE</div>
        <div class="brand-text">
          <div class="brand-name">智能风控 Agent</div>
          <div class="brand-sub">Financial Risk Engine</div>
        </div>
      </div>
      <nav class="menu">
        <div
          v-for="m in menus"
          :key="m.path"
          class="menu-item"
          :class="{ active: route.path.startsWith(m.path) }"
          @click="router.push(m.path)"
        >
          <el-icon :size="18"><component :is="m.icon" /></el-icon>
          <span>{{ m.label }}</span>
        </div>
      </nav>
      <div class="sidebar-foot">LangGraph Supervisor 架构</div>
    </aside>
    <div class="fde-main">
      <header class="fde-header">
        <div class="header-title">{{ title }}</div>
        <div class="header-right">
          <span class="pill">DeepSeek LLM</span>
          <span class="pill pill-soft">4 Agent 协作</span>
        </div>
      </header>
      <main class="fde-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.fde-shell {
  display: flex;
  min-height: 100vh;
  background: #f6f8fb;
}
.fde-sidebar {
  width: 240px;
  background: linear-gradient(180deg, #ffffff 0%, #f4f8fe 100%);
  border-right: 1px solid #e7edf5;
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 8px;
}
.brand-logo {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: linear-gradient(135deg, #2563eb, #38bdf8);
  color: #fff;
  font-weight: 800;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 14px rgba(37, 99, 235, 0.25);
}
.brand-name {
  font-weight: 700;
  color: #0f172a;
  font-size: 14px;
}
.brand-sub {
  color: #8aa0b8;
  font-size: 11px;
}
.menu {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 14px;
  border-radius: 10px;
  color: #475569;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}
.menu-item:hover {
  background: #eef3fb;
  color: #1d4ed8;
}
.menu-item.active {
  background: linear-gradient(135deg, #2563eb, #3b82f6);
  color: #fff;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.22);
}
.sidebar-foot {
  margin-top: auto;
  color: #9aa8bd;
  font-size: 11px;
  padding: 8px;
}
.fde-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.fde-header {
  height: 64px;
  background: #ffffff;
  border-bottom: 1px solid #e7edf5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
}
.header-title {
  font-size: 17px;
  font-weight: 700;
  color: #0f172a;
}
.header-right {
  display: flex;
  gap: 8px;
}
.pill {
  padding: 4px 12px;
  border-radius: 20px;
  background: #eef4ff;
  color: #2563eb;
  font-size: 12px;
  font-weight: 600;
}
.pill-soft {
  background: #f1f6fb;
  color: #64748b;
}
.fde-content {
  flex: 1;
  padding: 24px 28px;
  overflow: auto;
}
</style>
