import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
    },
    {
      path: '/auth/verify',
      name: 'auth-verify',
      component: () => import('@/views/AuthVerifyView.vue'),
    },
    {
      path: '/',
      name: 'home',
      component: () => import('@/components/StatementExample.vue'),
    },
  ],
})

export default router
