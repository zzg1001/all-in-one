import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/dashboard/DashboardView.vue'),
      meta: { title: '驾驶舱', requiresAuth: true }
    },
    // AI 管理
    {
      path: '/models',
      name: 'models',
      component: () => import('@/views/models/ModelsView.vue'),
      meta: { title: '模型配置', requiresAuth: true }
    },
    {
      path: '/tokens',
      name: 'tokens',
      component: () => import('@/views/tokens/TokensView.vue'),
      meta: { title: 'Token 用量', requiresAuth: true }
    },
    // 系统管理
    {
      path: '/users',
      name: 'users',
      component: () => import('@/views/users/UsersView.vue'),
      meta: { title: '用户管理', requiresAuth: true }
    },
    {
      path: '/permissions',
      name: 'permissions',
      component: () => import('@/views/permissions/PermissionsView.vue'),
      meta: { title: '权限管理', requiresAuth: true }
    },
    {
      path: '/logs',
      name: 'logs',
      component: () => import('@/views/logs/LogsView.vue'),
      meta: { title: '日志审计', requiresAuth: true }
    },
    {
      path: '/apis',
      name: 'apis',
      component: () => import('@/views/apis/ApisView.vue'),
      meta: { title: 'API 管理', requiresAuth: true }
    },
    {
      path: '/feedback',
      name: 'feedback',
      component: () => import('@/views/feedback/FeedbackView.vue'),
      meta: { title: '用户反馈', requiresAuth: true }
    },
    {
      path: '/agents',
      name: 'agents',
      component: () => import('@/views/agents/AgentsView.vue'),
      meta: { title: 'Agent 数据权限', requiresAuth: true }
    },
    {
      path: '/agent-manage',
      name: 'agent-manage',
      component: () => import('@/views/agents/AgentManageView.vue'),
      meta: { title: 'Agent 管理', requiresAuth: true }
    },
    {
      path: '/skills',
      name: 'skills',
      component: () => import('@/views/skills/SkillsManageView.vue'),
      meta: { title: '技能管理', requiresAuth: true }
    }
  ]
})

// 路由守卫
router.beforeEach(async (to, _from, next) => {
  const token = localStorage.getItem('auth_token')
  const isAuthenticated = !!token

  // 如果是登录页且已登录，跳转到首页
  if (to.name === 'login' && isAuthenticated) {
    next({ name: 'dashboard' })
    return
  }

  // 如果需要认证且未登录
  if (to.meta.requiresAuth !== false && !isAuthenticated) {
    next({
      name: 'login',
      query: { redirect: to.fullPath }
    })
    return
  }

  next()
})

export default router
