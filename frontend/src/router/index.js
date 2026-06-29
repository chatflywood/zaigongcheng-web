import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/',        name: 'key-indicators', component: () => import('../views/KeyIndicators.vue') },
  { path: '/zaigong', name: 'zaigong',        component: () => import('../views/Dashboard.vue') },
  { path: '/budget',  name: 'budget',         component: () => import('../views/Budget.vue') },
  { path: '/archive', name: 'archive',        component: () => import('../views/Archive.vue') },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
