import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // ============ 登录页 ============
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { requiresAuth: false },
    },
    // ============ 首页 ============
    {
      path: '/',
      name: 'home',
      component: () => import('../views/home/HomePage.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/skills-market',
      name: 'skills-market',
      component: () => import('../views/home/SkillsMarketplace.vue'),
      meta: { requiresAuth: false },
    },
    // ============ Portal 应用 ============
    {
      path: '/app',
      name: 'app',
      component: () => import('../views/SkillsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/monitor',
      name: 'monitor',
      component: () => import('../views/MonitorView.vue'),
    },
    {
      path: '/architecture',
      name: 'architecture',
      component: () => import('../views/ArchitectureView.vue'),
    },
    // 模块详情页面
    {
      path: '/modules/memory',
      name: 'module-memory',
      component: () => import('../views/modules/MemoryModuleView.vue'),
    },
    {
      path: '/modules/reasoning',
      name: 'module-reasoning',
      component: () => import('../views/modules/ReasoningModuleView.vue'),
    },
    {
      path: '/modules/planning',
      name: 'module-planning',
      component: () => import('../views/modules/PlanningModuleView.vue'),
    },
    {
      path: '/modules/tools',
      name: 'module-tools',
      component: () => import('../views/modules/ToolsModuleView.vue'),
    },
    {
      path: '/modules/actions',
      name: 'module-actions',
      component: () => import('../views/modules/ActionsModuleView.vue'),
    },
    // 多 Agent 协同模块
    {
      path: '/modules/registry',
      name: 'module-registry',
      component: () => import('../views/modules/RegistryModuleView.vue'),
    },
    {
      path: '/modules/orchestrator',
      name: 'module-orchestrator',
      component: () => import('../views/modules/OrchestratorModuleView.vue'),
    },
    {
      path: '/modules/bus',
      name: 'module-bus',
      component: () => import('../views/modules/BusModuleView.vue'),
    },
    {
      path: '/modules/governance',
      name: 'module-governance',
      component: () => import('../views/modules/GovernanceModuleView.vue'),
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
    },
    // ============ Admin 管理 ============
    {
      path: '/admin',
      component: () => import('../layouts/AdminLayout.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
      children: [
        {
          path: '',
          redirect: '/admin/dashboard',
        },
        {
          path: 'dashboard',
          name: 'admin-dashboard',
          component: () => import('../views/admin/dashboard/DashboardView.vue'),
          meta: { title: '驾驶舱' },
        },
        {
          path: 'agents',
          name: 'admin-agents',
          component: () => import('../views/admin/agents/AgentsView.vue'),
          meta: { title: 'Agent 管理' },
        },
        {
          path: 'agent-studio',
          name: 'admin-agent-studio',
          component: () => import('../views/admin/agents/AgentStudioView.vue'),
          meta: { title: 'Agent 工坊' },
        },
        {
          path: 'models',
          name: 'admin-models',
          component: () => import('../views/admin/models/ModelsView.vue'),
          meta: { title: '模型配置' },
        },
        {
          path: 'tokens',
          name: 'admin-tokens',
          component: () => import('../views/admin/tokens/TokensView.vue'),
          meta: { title: 'Token 管理' },
        },
        {
          path: 'users',
          name: 'admin-users',
          component: () => import('../views/admin/users/UsersView.vue'),
          meta: { title: '用户权限' },
        },
        {
          path: 'permissions',
          name: 'admin-permissions',
          component: () => import('../views/admin/permissions/PermissionsView.vue'),
          meta: { title: '用户权限' },
        },
        {
          path: 'logs',
          name: 'admin-logs',
          component: () => import('../views/admin/logs/LogsView.vue'),
          meta: { title: '日志查看' },
        },
        {
          path: 'apis',
          name: 'admin-apis',
          component: () => import('../views/admin/apis/ApisView.vue'),
          meta: { title: 'API 管理' },
        },
      ],
    },
  ],
  scrollBehavior(to, _from, savedPosition) {
    if (to.hash) {
      return { el: to.hash, behavior: 'smooth' }
    }
    if (savedPosition) {
      return savedPosition
    }
    return { top: 0 }
  }
})

// 路由守卫
router.beforeEach(async (to, _from, next) => {
  // 获取 token
  const token = localStorage.getItem('auth_token')
  const isAuthenticated = !!token

  // 如果是登录页，且已登录，跳转到首页
  if (to.name === 'login' && isAuthenticated) {
    next({ name: 'home' })
    return
  }

  // 如果需要认证且未登录，跳转到登录页
  if (to.meta.requiresAuth !== false && !isAuthenticated) {
    next({
      name: 'login',
      query: { redirect: to.fullPath },
    })
    return
  }

  // 如果需要管理员权限
  if (to.path.startsWith('/admin')) {
    const userStr = localStorage.getItem('auth_user')
    if (userStr) {
      try {
        const user = JSON.parse(userStr)
        if (user.role !== 'admin') {
          // 非管理员，跳转到首页
          next({ name: 'home' })
          return
        }
      } catch (e) {
        next({ name: 'login' })
        return
      }
    } else {
      next({ name: 'login' })
      return
    }
  }

  next()
})

export default router
