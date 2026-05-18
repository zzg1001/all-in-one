import { createRouter, createWebHistory } from 'vue-router'
import config from '@/config'

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
      path: '/agent-studio',
      name: 'agent-studio',
      component: () => import('../views/AgentStudioView.vue'),
      meta: { title: 'Agent 工作室', requiresAuth: false },
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
    // Admin 跳转到独立的 Admin 应用
    {
      path: '/admin/:path*',
      redirect: () => {
        window.location.href = config.adminUrl
        return '/'
      }
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

// Cookie 读取函数 (SSO)
function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`))
  return match ? decodeURIComponent(match[2]) : null
}

// 部门到主题颜色的映射
const departmentThemeMap: Record<string, string> = {
  'HR': 'blue',
  '销售': 'purple',
  '采购': 'cyan',
  '行政': 'orange',
  '财务': 'green',
}

// 根据用户角色获取默认跳转页面
function getDefaultRedirectFromCookie(): string {
  const userCookie = getCookie('auth_user')
  if (!userCookie) return '/'

  try {
    const user = JSON.parse(userCookie)

    // admin 和 boss 跳转首页
    if (user.role === 'admin' || user.role === 'boss') {
      return '/'
    }

    // 普通用户跳转到对应部门的 Agent 对话页面
    if (user.department) {
      const agentName = `${user.department}部门 Agent`
      const theme = departmentThemeMap[user.department] || 'blue'
      return `/app?from=login&agent=${encodeURIComponent(agentName)}&theme=${theme}`
    }
  } catch (e) {
    // 解析失败，跳转首页
  }

  return '/'
}

// 路由守卫
router.beforeEach(async (to, _from, next) => {
  // 获取 token - 从 Cookie 读取 (SSO)
  const token = getCookie('auth_token')
  const isAuthenticated = !!token

  // 如果是登录页，且已登录，根据角色跳转
  if (to.name === 'login' && isAuthenticated) {
    const defaultRedirect = getDefaultRedirectFromCookie()
    next(defaultRedirect)
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

  next()
})

export default router
