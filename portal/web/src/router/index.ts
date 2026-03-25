import { createRouter, createWebHistory } from 'vue-router'
import SkillsView from '../views/SkillsView.vue'
import config from '../config'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: SkillsView,
      beforeEnter: (to, from, next) => {
        // 如果没有 agent 参数，重定向到首页
        if (!to.query.agent) {
          window.location.href = config.homeUrl
          return
        }
        next()
      },
    },
    {
      path: '/agents',
      name: 'agents',
      component: () => import('../views/AgentsView.vue'),
    },
    {
      path: '/agent-studio',
      name: 'agent-studio',
      component: () => import('../views/AgentStudioView.vue'),
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
  ],
})

export default router
