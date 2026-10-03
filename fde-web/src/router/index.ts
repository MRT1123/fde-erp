import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/risk' },
    {
      path: '/',
      component: () => import('../layout/AppLayout.vue'),
      children: [
        { path: 'risk', name: 'risk', component: () => import('../views/RiskAnalyze.vue'), meta: { title: '风控分析' } },
        { path: 'due-diligence', name: 'due-diligence', component: () => import('../views/DueDiligence.vue'), meta: { title: '供应商尽调' } },
        { path: 'anomaly', name: 'anomaly', component: () => import('../views/AnomalyCheck.vue'), meta: { title: '异常检测' } },
        { path: 'guide', name: 'guide', component: () => import('../views/Guide.vue'), meta: { title: '使用说明' } },
      ],
    },
  ],
})

export default router
