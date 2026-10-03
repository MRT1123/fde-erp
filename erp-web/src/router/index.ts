import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/dashboard' },
  {
    path: '/',
    component: () => import('../layout/AppLayout.vue'),
    children: [
      { path: 'dashboard', name: 'dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '数据看板' } },
      { path: 'purchase', name: 'purchase', component: () => import('../views/PurchaseRequests.vue'), meta: { title: '采购申请' } },
      { path: 'purchase/:id', name: 'purchase-detail', component: () => import('../views/PurchaseDetail.vue'), meta: { title: '采购详情' } },
      { path: 'approvals', name: 'approvals', component: () => import('../views/Approvals.vue'), meta: { title: '审批工作台' } },
      { path: 'suppliers', name: 'suppliers', component: () => import('../views/Suppliers.vue'), meta: { title: '供应商' } },
      { path: 'materials', name: 'materials', component: () => import('../views/Materials.vue'), meta: { title: '物料档案' } },
      { path: 'inventory', name: 'inventory', component: () => import('../views/Inventory.vue'), meta: { title: '库存管理' } },
      { path: 'budget', name: 'budget', component: () => import('../views/Budget.vue'), meta: { title: '预算管控' } },
      { path: 'purchase-orders', name: 'purchase-orders', component: () => import('../views/PurchaseOrders.vue'), meta: { title: '采购订单' } },
      { path: 'risk', name: 'risk', component: () => import('../views/FdeRisk.vue'), meta: { title: '风控分析' } },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
