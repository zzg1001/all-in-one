<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { modulesApi, type ModuleDefinition, type ModuleMetricsResponse } from '@/api'

const router = useRouter()
const emit = defineEmits(['select-module'])

// 当前选中/悬停的模块
const selectedModule = ref<string | null>(null)
const hoveredModule = ref<string | null>(null)
const showDevPanel = ref(false)
const activeDetailTab = ref<'overview' | 'api' | 'metrics' | 'develop'>('overview')

// 实时数据模拟
const systemTime = ref(new Date().toLocaleTimeString())
const dataFlowActive = ref(true)

// API 数据加载状态
const loading = ref(true)
const error = ref<string | null>(null)
const moduleDefinitions = ref<ModuleDefinition[]>([])

// 图标映射（API 返回的是 icon 名称字符串）
const iconMap: Record<string, string> = {
  'brain': '🧠',
  'lightbulb': '💡',
  'map': '🎯',
  'wrench': '🔧',
  'play': '⚡',
  'server': '📋',
  'git-branch': '🎭',
  'radio': '🔀',
  'shield': '🛡️',
}

// 从 API 获取模块定义并转换为组件需要的格式
const transformModule = (def: ModuleDefinition, index: number) => {
  const isCore = def.category === 'core'
  const baseFeatures = Object.keys(def.default_config || {}).slice(0, 4).map(k =>
    k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  )

  return {
    id: def.type,
    name: def.name,
    nameCn: def.description.split('，')[0] || def.description.slice(0, 15),
    icon: iconMap[def.icon] || '📦',
    color: def.color,
    gradient: `linear-gradient(135deg, ${def.color}, ${adjustColor(def.color, 30)})`,
    desc: def.description.slice(0, 20),
    detail: def.description,
    status: 'active',
    version: 'v2.0.0',
    metrics: getDefaultMetrics(def.type),
    features: baseFeatures.length > 0 ? baseFeatures : ['模块化设计', '可扩展', '高性能', '易配置'],
    dependencies: getDependencies(def.type, isCore),
  }
}

// 调整颜色亮度
const adjustColor = (color: string, amount: number): string => {
  const hex = color.replace('#', '')
  const r = Math.min(255, parseInt(hex.slice(0, 2), 16) + amount)
  const g = Math.min(255, parseInt(hex.slice(2, 4), 16) + amount)
  const b = Math.min(255, parseInt(hex.slice(4, 6), 16) + amount)
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`
}

// 获取默认指标数据
const getDefaultMetrics = (type: string): Record<string, string> => {
  const metricsMap: Record<string, Record<string, string>> = {
    memory: { items: '2,456', queries: '156/min', hitRate: '94.2%', avgLatency: '8ms' },
    reasoning: { depth: 'L3-L5', accuracy: '94.7%', chains: '1,234', avgSteps: '4.2' },
    planning: { tasks: '128', pending: '12', completed: '1,892', successRate: '97.3%' },
    tools: { tools: '47', calls: '3,891', cacheHit: '67%', errorRate: '0.3%' },
    actions: { exec: '12,456', success: '98.1%', avgTime: '1.2s', streaming: 'ON' },
    registry: { agents: '24', online: '21', types: '8', health: '99.9%' },
    orchestrator: { flows: '15', running: '7', queued: '23', throughput: '450/h' },
    bus: { msg: '3.2K/s', latency: '12ms', channels: '156', buffer: '2.1GB' },
    governance: { rules: '89', alerts: '3', audits: '45K', blocked: '127' },
  }
  return metricsMap[type] || { status: 'active', calls: '0', errors: '0', latency: '0ms' }
}

// 获取模块依赖
const getDependencies = (type: string, isCore: boolean): string[] => {
  const depsMap: Record<string, string[]> = {
    memory: ['reasoning', 'planning'],
    reasoning: ['memory', 'planning'],
    planning: ['tools', 'actions'],
    tools: ['actions'],
    actions: [],
    registry: ['orchestrator', 'bus'],
    orchestrator: ['bus', 'governance'],
    bus: ['governance'],
    governance: [],
  }
  return depsMap[type] || []
}

// 单 Agent 核心五大组件（从 API 加载或使用默认值）
const coreModules = computed(() => {
  if (moduleDefinitions.value.length > 0) {
    return moduleDefinitions.value
      .filter(def => def.category === 'core')
      .map((def, i) => transformModule(def, i))
  }
  // 默认静态数据作为后备
  return [
  {
    id: 'memory',
    name: 'Memory',
    nameCn: '记忆模块',
    icon: '🧠',
    color: '#a855f7',
    gradient: 'linear-gradient(135deg, #a855f7, #6366f1)',
    desc: '记忆存储与检索引擎',
    detail: '管理短期记忆、长期记忆、工作记忆，支持向量存储和语义检索。基于 FAISS 实现高效相似度搜索，支持记忆压缩与遗忘机制。',
    status: 'active',
    version: 'v2.1.0',
    metrics: {
      items: '2,456',
      queries: '156/min',
      hitRate: '94.2%',
      avgLatency: '8ms'
    },
    features: ['向量存储', '语义检索', '记忆压缩', '遗忘机制'],
    dependencies: ['reasoning', 'planning']
  },
  {
    id: 'reasoning',
    name: 'Reasoning',
    nameCn: '推理模块',
    icon: '💡',
    color: '#f59e0b',
    gradient: 'linear-gradient(135deg, #f59e0b, #ef4444)',
    desc: '多模态推理引擎',
    detail: '链式思考、反思机制、假设验证，支持多种推理模式。实现 ReAct、CoT、ToT 等先进推理框架，支持自我纠错与推理路径回溯。',
    status: 'active',
    version: 'v3.0.1',
    metrics: {
      depth: 'L3-L5',
      accuracy: '94.7%',
      chains: '1,234',
      avgSteps: '4.2'
    },
    features: ['链式思考', '反思机制', '假设验证', '路径回溯'],
    dependencies: ['memory', 'planning']
  },
  {
    id: 'planning',
    name: 'Planning',
    nameCn: '规划模块',
    icon: '🎯',
    color: '#10b981',
    gradient: 'linear-gradient(135deg, #10b981, #06b6d4)',
    desc: '任务规划与分解器',
    detail: '任务分解、执行计划、动态调整，支持层次化目标管理。采用 HTN 规划算法，支持计划重规划与并行任务调度。',
    status: 'active',
    version: 'v2.4.0',
    metrics: {
      tasks: '128',
      pending: '12',
      completed: '1,892',
      successRate: '97.3%'
    },
    features: ['任务分解', 'HTN规划', '动态调整', '并行调度'],
    dependencies: ['tools', 'actions']
  },
  {
    id: 'tools',
    name: 'Tool Use',
    nameCn: '工具模块',
    icon: '🔧',
    color: '#3b82f6',
    gradient: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
    desc: '工具调用与管理',
    detail: '工具发现、参数构造、结果解析，支持动态工具注册。实现工具能力描述、参数验证、错误重试与结果缓存。',
    status: 'active',
    version: 'v2.2.3',
    metrics: {
      tools: '47',
      calls: '3,891',
      cacheHit: '67%',
      errorRate: '0.3%'
    },
    features: ['工具发现', '参数构造', '结果缓存', '错误重试'],
    dependencies: ['actions']
  },
  {
    id: 'actions',
    name: 'Actions',
    nameCn: '行动模块',
    icon: '⚡',
    color: '#ef4444',
    gradient: 'linear-gradient(135deg, #ef4444, #ec4899)',
    desc: '执行引擎与输出',
    detail: '执行引擎、输出格式化、反馈收集，支持多模态输出。管理执行队列、超时控制、结果流式输出与用户反馈循环。',
    status: 'active',
    version: 'v2.0.5',
    metrics: {
      exec: '12,456',
      success: '98.1%',
      avgTime: '1.2s',
      streaming: 'ON'
    },
    features: ['执行队列', '流式输出', '超时控制', '反馈循环'],
    dependencies: []
  }
]
})

// 多 Agent 协同四大模块
const multiAgentModules = computed(() => {
  if (moduleDefinitions.value.length > 0) {
    return moduleDefinitions.value
      .filter(def => def.category === 'multi')
      .map((def, i) => transformModule(def, i))
  }
  // 默认静态数据作为后备
  return [
  {
    id: 'registry',
    name: 'Registry',
    nameCn: '注册中心',
    icon: '📋',
    color: '#6366f1',
    gradient: 'linear-gradient(135deg, #6366f1, #a855f7)',
    desc: 'Agent 注册与发现',
    detail: 'Agent 注册、发现、能力描述、版本管理。实现服务注册、健康检查、负载信息上报与能力匹配查询。',
    status: 'active',
    version: 'v1.5.0',
    metrics: {
      agents: '24',
      online: '21',
      types: '8',
      health: '99.9%'
    },
    features: ['服务注册', '能力描述', '版本管理', '健康检查'],
    dependencies: ['orchestrator', 'bus']
  },
  {
    id: 'orchestrator',
    name: 'Orchestrator',
    nameCn: '编排器',
    icon: '🎭',
    color: '#ec4899',
    gradient: 'linear-gradient(135deg, #ec4899, #f43f5e)',
    desc: '任务编排与调度',
    detail: '任务分配、负载均衡、故障转移、流程编排。支持 DAG 工作流定义、条件分支、并行执行与状态机管理。',
    status: 'active',
    version: 'v2.1.0',
    metrics: {
      flows: '15',
      running: '7',
      queued: '23',
      throughput: '450/h'
    },
    features: ['DAG工作流', '负载均衡', '故障转移', '状态机'],
    dependencies: ['bus', 'governance']
  },
  {
    id: 'bus',
    name: 'Agent Bus',
    nameCn: '通信总线',
    icon: '🔀',
    color: '#14b8a6',
    gradient: 'linear-gradient(135deg, #14b8a6, #22d3ee)',
    desc: '消息通信与同步',
    detail: '消息路由、事件广播、状态同步、协议适配。基于消息队列实现异步通信，支持发布订阅、请求响应等模式。',
    status: 'active',
    version: 'v1.8.2',
    metrics: {
      msg: '3.2K/s',
      latency: '12ms',
      channels: '156',
      buffer: '2.1GB'
    },
    features: ['消息路由', '事件广播', '状态同步', '协议适配'],
    dependencies: ['governance']
  },
  {
    id: 'governance',
    name: 'Governance',
    nameCn: '治理模块',
    icon: '🛡️',
    color: '#f97316',
    gradient: 'linear-gradient(135deg, #f97316, #fbbf24)',
    desc: '安全与资源治理',
    detail: '权限控制、审计日志、资源配额、安全策略。实现 RBAC 权限模型、操作审计、限流熔断与安全沙箱。',
    status: 'active',
    version: 'v2.0.0',
    metrics: {
      rules: '89',
      alerts: '3',
      audits: '45K',
      blocked: '127'
    },
    features: ['RBAC权限', '审计日志', '限流熔断', '安全沙箱'],
    dependencies: []
  }
]
})

// 加载模块定义
const loadModules = async () => {
  loading.value = true
  error.value = null
  try {
    moduleDefinitions.value = await modulesApi.getAll()
  } catch (e) {
    console.error('Failed to load modules:', e)
    error.value = e instanceof Error ? e.message : '加载模块失败'
    // 使用默认数据继续显示
  } finally {
    loading.value = false
  }
}

// 计算环形布局位置 - 内环
const getCorePosition = (index: number, total: number) => {
  const angle = (index * 360 / total) - 90
  const radius = 130
  const x = Math.cos(angle * Math.PI / 180) * radius
  const y = Math.sin(angle * Math.PI / 180) * radius
  return { x, y, angle }
}

// 计算环形布局位置 - 外环
const getMultiPosition = (index: number, total: number) => {
  const angle = (index * 360 / total) - 45
  const radius = 235
  const x = Math.cos(angle * Math.PI / 180) * radius
  const y = Math.sin(angle * Math.PI / 180) * radius
  return { x, y, angle }
}

const selectModule = (moduleId: string) => {
  selectedModule.value = moduleId
  activeDetailTab.value = 'overview'
  emit('select-module', moduleId)
}

const getModuleById = (id: string) => {
  return [...coreModules.value, ...multiAgentModules.value].find(m => m.id === id)
}

const currentModule = computed(() => {
  const id = hoveredModule.value || selectedModule.value
  return id ? getModuleById(id) : null
})

const isCoreModule = (id: string) => {
  return coreModules.value.some(m => m.id === id)
}

// 模块操作
const configureModule = (moduleId: string) => {
  // 核心模块有专门的配置页面
  const coreModuleRoutes: Record<string, string> = {
    'memory': '/modules/memory',
    'reasoning': '/modules/reasoning',
    'planning': '/modules/planning',
    'tools': '/modules/tools',
    'actions': '/modules/actions'
  }

  // 多 Agent 协同模块
  const multiAgentRoutes: Record<string, string> = {
    'registry': '/modules/registry',
    'orchestrator': '/modules/orchestrator',
    'bus': '/modules/bus',
    'governance': '/modules/governance'
  }

  if (coreModuleRoutes[moduleId]) {
    router.push(coreModuleRoutes[moduleId])
  } else if (multiAgentRoutes[moduleId]) {
    router.push(multiAgentRoutes[moduleId])
  } else {
    router.push({ path: '/agent-studio/module', query: { id: moduleId, action: 'config' } })
  }
}

const viewMonitor = (moduleId: string) => {
  router.push({ path: '/monitor', query: { module: moduleId } })
}

const viewDocs = (moduleId: string) => {
  window.open(`/docs/modules/${moduleId}`, '_blank')
}

const startDevelopment = (moduleId: string) => {
  router.push({ path: '/agent-studio/develop', query: { module: moduleId } })
}

// 时钟更新
let clockInterval: number
onMounted(async () => {
  // 加载模块数据
  await loadModules()

  // 启动时钟
  clockInterval = setInterval(() => {
    systemTime.value = new Date().toLocaleTimeString()
  }, 1000) as unknown as number
})

onUnmounted(() => {
  if (clockInterval) clearInterval(clockInterval)
})
</script>

<template>
  <div class="neural-command-center">
    <!-- 背景网格 -->
    <div class="bg-grid"></div>
    <div class="bg-glow"></div>

    <!-- 顶部控制栏 -->
    <header class="command-header">
      <div class="header-left">
        <div class="system-logo">
          <span class="logo-icon">◈</span>
          <div class="logo-text">
            <h1>AGENT NEURAL CORE</h1>
            <span class="logo-subtitle">Modular Architecture System v3.0</span>
          </div>
        </div>
      </div>

      <div class="header-center">
        <div class="system-stats">
          <div class="stat-block">
            <span class="stat-value">9</span>
            <span class="stat-label">MODULES</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-block">
            <span class="stat-value online">100%</span>
            <span class="stat-label">ONLINE</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-block">
            <span class="stat-value">12ms</span>
            <span class="stat-label">LATENCY</span>
          </div>
        </div>
      </div>

      <div class="header-right">
        <div class="system-clock">
          <span class="clock-label">SYS.TIME</span>
          <span class="clock-value">{{ systemTime }}</span>
        </div>
        <div class="status-indicator">
          <span class="pulse-dot"></span>
          <span>SYSTEM ACTIVE</span>
        </div>
      </div>
    </header>

    <div class="command-body">
      <!-- 左侧：核心可视化区 -->
      <div class="visualization-panel">
        <div class="viz-container">
          <!-- 层级标签 -->
          <div class="layer-labels">
            <div class="layer-label inner-label">
              <span class="layer-line"></span>
              <span class="layer-text">SINGLE AGENT CORE</span>
            </div>
            <div class="layer-label outer-label">
              <span class="layer-line"></span>
              <span class="layer-text">MULTI-AGENT FRAMEWORK</span>
            </div>
          </div>

          <svg class="architecture-svg" viewBox="-300 -300 600 600">
            <defs>
              <!-- 发光效果 -->
              <filter id="glow-strong" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
              <filter id="glow-soft" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>

              <!-- 核心渐变 -->
              <radialGradient id="core-gradient" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#22d3ee" stop-opacity="0.4"/>
                <stop offset="50%" stop-color="#6366f1" stop-opacity="0.2"/>
                <stop offset="100%" stop-color="#6366f1" stop-opacity="0"/>
              </radialGradient>

              <!-- 连接线渐变 -->
              <linearGradient id="connection-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#22d3ee" stop-opacity="0.8"/>
                <stop offset="100%" stop-color="#6366f1" stop-opacity="0.3"/>
              </linearGradient>

              <!-- 数据流动画 -->
              <linearGradient id="flow-gradient">
                <stop offset="0%" stop-color="transparent"/>
                <stop offset="40%" stop-color="#22d3ee"/>
                <stop offset="60%" stop-color="#22d3ee"/>
                <stop offset="100%" stop-color="transparent"/>
              </linearGradient>
            </defs>

            <!-- 背景装饰环 -->
            <circle cx="0" cy="0" r="280" class="deco-ring deco-ring-1"/>
            <circle cx="0" cy="0" r="260" class="deco-ring deco-ring-2"/>

            <!-- 外环轨道 -->
            <circle cx="0" cy="0" r="235" class="orbit-ring outer-orbit"/>
            <circle cx="0" cy="0" r="235" class="orbit-ring-glow outer-orbit"/>

            <!-- 内环轨道 -->
            <circle cx="0" cy="0" r="130" class="orbit-ring inner-orbit"/>
            <circle cx="0" cy="0" r="130" class="orbit-ring-glow inner-orbit"/>

            <!-- 核心区域 -->
            <circle cx="0" cy="0" r="55" class="core-ring"/>
            <circle cx="0" cy="0" r="50" fill="url(#core-gradient)"/>
            <circle cx="0" cy="0" r="45" class="core-inner"/>

            <!-- 核心文字 -->
            <text x="0" y="-8" class="core-title">AGENT</text>
            <text x="0" y="10" class="core-subtitle">CORE</text>
            <text x="0" y="26" class="core-version">v3.0</text>

            <!-- 连接线 - 核心到内环 -->
            <g class="connections-inner">
              <line
                v-for="(mod, i) in coreModules"
                :key="'conn-inner-' + mod.id"
                x1="50" y1="0"
                :x2="getCorePosition(i, coreModules.length).x"
                :y2="getCorePosition(i, coreModules.length).y"
                class="connection-line"
                :class="{ active: hoveredModule === mod.id || selectedModule === mod.id }"
                :style="{
                  stroke: mod.color,
                  transformOrigin: 'center',
                  transform: `rotate(${getCorePosition(i, coreModules.length).angle + 90}deg)`
                }"
              />
            </g>

            <!-- 连接线 - 内环到外环 (曲线) -->
            <g class="connections-outer">
              <path
                v-for="(mod, i) in multiAgentModules"
                :key="'conn-outer-' + mod.id"
                :d="`M ${getCorePosition(i % coreModules.length, coreModules.length).x}
                    ${getCorePosition(i % coreModules.length, coreModules.length).y}
                    Q ${getCorePosition(i % coreModules.length, coreModules.length).x * 0.5 + getMultiPosition(i, multiAgentModules.length).x * 0.5}
                    ${getCorePosition(i % coreModules.length, coreModules.length).y * 0.5 + getMultiPosition(i, multiAgentModules.length).y * 0.5}
                    ${getMultiPosition(i, multiAgentModules.length).x}
                    ${getMultiPosition(i, multiAgentModules.length).y}`"
                class="connection-curve"
                :class="{ active: hoveredModule === mod.id || selectedModule === mod.id }"
                :style="{ stroke: mod.color }"
              />
            </g>

            <!-- 脉冲波纹 -->
            <circle cx="0" cy="0" r="50" class="pulse-wave pulse-1"/>
            <circle cx="0" cy="0" r="130" class="pulse-wave pulse-2"/>
            <circle cx="0" cy="0" r="235" class="pulse-wave pulse-3"/>

            <!-- 内环：核心组件节点 -->
            <g
              v-for="(mod, i) in coreModules"
              :key="mod.id"
              class="module-node core-module"
              :class="{
                active: selectedModule === mod.id,
                hovered: hoveredModule === mod.id
              }"
              :transform="`translate(${getCorePosition(i, coreModules.length).x}, ${getCorePosition(i, coreModules.length).y})`"
              @click="selectModule(mod.id)"
              @mouseenter="hoveredModule = mod.id"
              @mouseleave="hoveredModule = null"
            >
              <!-- 外圈光晕 -->
              <circle r="38" class="node-glow" :style="{ fill: mod.color + '15' }"/>
              <!-- 主圆形 -->
              <circle r="32" class="node-bg" :style="{ stroke: mod.color }"/>
              <circle r="26" class="node-inner" :style="{ fill: mod.color + '30' }"/>
              <!-- 图标 -->
              <text y="2" class="node-icon">{{ mod.icon }}</text>
              <!-- 名称标签 -->
              <text y="52" class="node-name">{{ mod.name }}</text>
              <!-- 状态指示器 -->
              <circle cx="22" cy="-22" r="5" class="node-status" :class="mod.status"/>
            </g>

            <!-- 外环：协同模块节点 -->
            <g
              v-for="(mod, i) in multiAgentModules"
              :key="mod.id"
              class="module-node multi-module"
              :class="{
                active: selectedModule === mod.id,
                hovered: hoveredModule === mod.id
              }"
              :transform="`translate(${getMultiPosition(i, multiAgentModules.length).x}, ${getMultiPosition(i, multiAgentModules.length).y})`"
              @click="selectModule(mod.id)"
              @mouseenter="hoveredModule = mod.id"
              @mouseleave="hoveredModule = null"
            >
              <!-- 外框光晕 -->
              <rect x="-48" y="-32" width="96" height="64" rx="8" class="node-glow" :style="{ fill: mod.color + '10' }"/>
              <!-- 主矩形 -->
              <rect x="-44" y="-28" width="88" height="56" rx="6" class="node-bg" :style="{ stroke: mod.color }"/>
              <rect x="-40" y="-24" width="80" height="48" rx="4" class="node-inner" :style="{ fill: mod.color + '20' }"/>
              <!-- 图标 -->
              <text y="-4" class="node-icon" style="font-size: 18px;">{{ mod.icon }}</text>
              <!-- 名称 -->
              <text y="14" class="node-label">{{ mod.name }}</text>
              <!-- 状态指示器 -->
              <circle cx="36" cy="-20" r="4" class="node-status" :class="mod.status"/>
            </g>

            <!-- 数据流粒子 (装饰) -->
            <g class="data-particles" v-if="dataFlowActive">
              <circle r="2" class="particle p1"><animateMotion dur="3s" repeatCount="indefinite" path="M0,0 L130,0" /></circle>
              <circle r="2" class="particle p2"><animateMotion dur="2.5s" repeatCount="indefinite" path="M0,0 L-130,0" /></circle>
              <circle r="2" class="particle p3"><animateMotion dur="4s" repeatCount="indefinite" path="M0,0 L0,130" /></circle>
            </g>
          </svg>

          <!-- 图例 -->
          <div class="viz-legend">
            <div class="legend-section">
              <span class="legend-marker inner"></span>
              <span class="legend-label">Single Agent Core (5 modules)</span>
            </div>
            <div class="legend-section">
              <span class="legend-marker outer"></span>
              <span class="legend-label">Multi-Agent Framework (4 modules)</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：详情面板 -->
      <div class="detail-panel" :class="{ 'has-selection': currentModule }">
        <!-- 扫描线效果 -->
        <div class="scan-line"></div>

        <!-- 未选中状态 -->
        <div v-if="!currentModule" class="panel-empty">
          <div class="empty-visual">
            <div class="empty-rings">
              <span class="ring r1"></span>
              <span class="ring r2"></span>
              <span class="ring r3"></span>
            </div>
            <span class="empty-icon">◎</span>
          </div>
          <h3>SELECT A MODULE</h3>
          <p>Click on any node in the architecture diagram to view module details, metrics, and development options.</p>

          <div class="empty-stats">
            <div class="es-item">
              <span class="es-value">5</span>
              <span class="es-label">Core Modules</span>
            </div>
            <div class="es-item">
              <span class="es-value">4</span>
              <span class="es-label">Framework Modules</span>
            </div>
            <div class="es-item">
              <span class="es-value">47</span>
              <span class="es-label">Active Tools</span>
            </div>
          </div>

          <div class="quick-links">
            <button class="quick-link" @click="router.push('/agent-studio')">
              <span>+</span> Create New Agent
            </button>
            <button class="quick-link" @click="router.push('/monitor')">
              <span>◉</span> System Monitor
            </button>
          </div>
        </div>

        <!-- 选中模块详情 -->
        <div v-else class="panel-content">
          <!-- 模块头部 -->
          <div class="module-header">
            <div class="header-badge" :style="{ background: currentModule.gradient }">
              <span class="badge-icon">{{ currentModule.icon }}</span>
            </div>
            <div class="header-info">
              <div class="info-row">
                <h2>{{ currentModule.name }}</h2>
                <span class="module-type" :class="isCoreModule(currentModule.id) ? 'core' : 'framework'">
                  {{ isCoreModule(currentModule.id) ? 'CORE' : 'FRAMEWORK' }}
                </span>
              </div>
              <span class="module-desc">{{ currentModule.nameCn }}</span>
              <div class="info-meta">
                <span class="meta-item">
                  <span class="meta-dot" :class="currentModule.status"></span>
                  {{ currentModule.status === 'active' ? 'Running' : 'Offline' }}
                </span>
                <span class="meta-divider">|</span>
                <span class="meta-item">{{ currentModule.version }}</span>
              </div>
            </div>
          </div>

          <!-- 标签页切换 -->
          <div class="detail-tabs">
            <button
              :class="['tab', { active: activeDetailTab === 'overview' }]"
              @click="activeDetailTab = 'overview'"
            >Overview</button>
            <button
              :class="['tab', { active: activeDetailTab === 'metrics' }]"
              @click="activeDetailTab = 'metrics'"
            >Metrics</button>
            <button
              :class="['tab', { active: activeDetailTab === 'api' }]"
              @click="activeDetailTab = 'api'"
            >API</button>
            <button
              :class="['tab', { active: activeDetailTab === 'develop' }]"
              @click="activeDetailTab = 'develop'"
            >Develop</button>
          </div>

          <!-- Overview 标签页 -->
          <div v-show="activeDetailTab === 'overview'" class="tab-content">
            <div class="content-section">
              <h4>Description</h4>
              <p class="section-text">{{ currentModule.detail }}</p>
            </div>

            <div class="content-section">
              <h4>Features</h4>
              <div class="feature-tags">
                <span
                  v-for="feature in currentModule.features"
                  :key="feature"
                  class="feature-tag"
                  :style="{ borderColor: currentModule.color + '60' }"
                >
                  {{ feature }}
                </span>
              </div>
            </div>

            <div class="content-section" v-if="currentModule.dependencies.length">
              <h4>Dependencies</h4>
              <div class="dependency-list">
                <span
                  v-for="dep in currentModule.dependencies"
                  :key="dep"
                  class="dep-item"
                  @click="selectModule(dep)"
                >
                  {{ getModuleById(dep)?.icon }} {{ getModuleById(dep)?.name }}
                </span>
              </div>
            </div>
          </div>

          <!-- Metrics 标签页 -->
          <div v-show="activeDetailTab === 'metrics'" class="tab-content">
            <div class="metrics-grid">
              <div
                v-for="(value, key) in currentModule.metrics"
                :key="key"
                class="metric-card"
              >
                <div class="metric-visual">
                  <svg viewBox="0 0 36 36" class="metric-ring">
                    <circle cx="18" cy="18" r="16" class="ring-bg"/>
                    <circle cx="18" cy="18" r="16" class="ring-fill" :style="{ stroke: currentModule.color }"/>
                  </svg>
                  <span class="metric-value" :style="{ color: currentModule.color }">{{ value }}</span>
                </div>
                <span class="metric-label">{{ key }}</span>
              </div>
            </div>

            <div class="live-indicator">
              <span class="live-dot"></span>
              <span>Live Data</span>
            </div>
          </div>

          <!-- API 标签页 -->
          <div v-show="activeDetailTab === 'api'" class="tab-content">
            <div class="api-section">
              <h4>REST Endpoints</h4>
              <div class="api-list">
                <div class="api-item">
                  <span class="method get">GET</span>
                  <code>/api/modules/{{ currentModule.id }}/status</code>
                </div>
                <div class="api-item">
                  <span class="method post">POST</span>
                  <code>/api/modules/{{ currentModule.id }}/execute</code>
                </div>
                <div class="api-item">
                  <span class="method put">PUT</span>
                  <code>/api/modules/{{ currentModule.id }}/config</code>
                </div>
                <div class="api-item">
                  <span class="method get">GET</span>
                  <code>/api/modules/{{ currentModule.id }}/metrics</code>
                </div>
              </div>
            </div>

            <div class="api-section">
              <h4>Event Hooks</h4>
              <div class="api-list">
                <div class="api-item">
                  <span class="method event">EVT</span>
                  <code>on{{ currentModule.name }}Start</code>
                </div>
                <div class="api-item">
                  <span class="method event">EVT</span>
                  <code>on{{ currentModule.name }}Complete</code>
                </div>
                <div class="api-item">
                  <span class="method event">EVT</span>
                  <code>on{{ currentModule.name }}Error</code>
                </div>
              </div>
            </div>
          </div>

          <!-- Develop 标签页 -->
          <div v-show="activeDetailTab === 'develop'" class="tab-content">
            <div class="develop-info">
              <div class="dev-card">
                <span class="dev-icon">📁</span>
                <div class="dev-details">
                  <span class="dev-label">Source Location</span>
                  <code>portal/server/modules/{{ currentModule.id }}/</code>
                </div>
              </div>
              <div class="dev-card">
                <span class="dev-icon">📦</span>
                <div class="dev-details">
                  <span class="dev-label">Package</span>
                  <code>@agent-core/{{ currentModule.id }}</code>
                </div>
              </div>
              <div class="dev-card">
                <span class="dev-icon">🔧</span>
                <div class="dev-details">
                  <span class="dev-label">Test Command</span>
                  <code>npm run test:{{ currentModule.id }}</code>
                </div>
              </div>
            </div>

            <p class="dev-note">
              This module can be developed independently. Clone the repository and run the test suite to get started.
            </p>
          </div>

          <!-- 操作按钮 -->
          <div class="action-buttons">
            <button
              class="btn-primary"
              :style="{ background: currentModule.gradient }"
              @click="configureModule(currentModule.id)"
            >
              <span>⚙</span>
              Configure
            </button>
            <button class="btn-secondary" @click="viewMonitor(currentModule.id)">
              <span>◉</span>
              Monitor
            </button>
            <button class="btn-secondary" @click="viewDocs(currentModule.id)">
              <span>◷</span>
              Docs
            </button>
            <button class="btn-develop" @click="startDevelopment(currentModule.id)">
              <span>⟨/⟩</span>
              Develop
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部状态栏 -->
    <footer class="command-footer">
      <div class="footer-left">
        <span class="footer-item">
          <span class="fi-dot active"></span>
          All Systems Operational
        </span>
      </div>
      <div class="footer-center">
        <span class="footer-item">Agent Neural Core™</span>
        <span class="footer-sep">·</span>
        <span class="footer-item">Modular Architecture</span>
        <span class="footer-sep">·</span>
        <span class="footer-item">Enterprise Ready</span>
      </div>
      <div class="footer-right">
        <span class="footer-item">v3.0.0</span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Inter:wght@400;500;600&display=swap');

.neural-command-center {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #030712;
  color: #e2e8f0;
  font-family: 'Inter', sans-serif;
  overflow: hidden;
  position: relative;
}

/* 背景效果 */
.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(34, 211, 238, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(34, 211, 238, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
}

.bg-glow {
  position: absolute;
  top: 50%;
  left: 30%;
  width: 800px;
  height: 800px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 60%);
  transform: translate(-50%, -50%);
  pointer-events: none;
}

/* 顶部控制栏 */
.command-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
  background: rgba(3, 7, 18, 0.8);
  border-bottom: 1px solid rgba(34, 211, 238, 0.2);
  backdrop-filter: blur(12px);
  z-index: 10;
}

.system-logo {
  display: flex;
  align-items: center;
  gap: 14px;
}

.logo-icon {
  font-size: 32px;
  color: #22d3ee;
  text-shadow: 0 0 20px rgba(34, 211, 238, 0.5);
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { opacity: 1; text-shadow: 0 0 20px rgba(34, 211, 238, 0.5); }
  50% { opacity: 0.8; text-shadow: 0 0 30px rgba(34, 211, 238, 0.8); }
}

.logo-text h1 {
  font-family: 'Orbitron', sans-serif;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 3px;
  margin: 0;
  background: linear-gradient(90deg, #22d3ee, #a855f7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.logo-subtitle {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #64748b;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.system-stats {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 8px 24px;
  background: rgba(34, 211, 238, 0.05);
  border: 1px solid rgba(34, 211, 238, 0.15);
  border-radius: 8px;
}

.stat-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.stat-value {
  font-family: 'Orbitron', sans-serif;
  font-size: 18px;
  font-weight: 600;
  color: #22d3ee;
}

.stat-value.online {
  color: #10b981;
}

.stat-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: #64748b;
  letter-spacing: 1px;
}

.stat-divider {
  width: 1px;
  height: 28px;
  background: rgba(34, 211, 238, 0.2);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.system-clock {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.clock-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: #64748b;
  letter-spacing: 1px;
}

.clock-value {
  font-family: 'Orbitron', sans-serif;
  font-size: 16px;
  color: #22d3ee;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #10b981;
  letter-spacing: 1px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #10b981;
  border-radius: 50%;
  animation: pulse-dot 1.5s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.3); opacity: 0.7; }
}

/* 主体区域 */
.command-body {
  flex: 1;
  display: flex;
  min-height: 0;
}

/* 可视化面板 */
.visualization-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  padding: 20px;
}

.viz-container {
  position: relative;
  width: 100%;
  max-width: 700px;
}

.layer-labels {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.layer-label {
  position: absolute;
  display: flex;
  align-items: center;
  gap: 8px;
}

.inner-label {
  top: 50%;
  left: 20px;
  transform: translateY(40px);
}

.outer-label {
  top: 50%;
  right: 20px;
  transform: translateY(-120px);
  flex-direction: row-reverse;
}

.layer-line {
  width: 30px;
  height: 1px;
  background: linear-gradient(90deg, #22d3ee, transparent);
}

.outer-label .layer-line {
  background: linear-gradient(90deg, transparent, #a855f7);
}

.layer-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: #64748b;
  letter-spacing: 2px;
  white-space: nowrap;
}

.architecture-svg {
  width: 100%;
  height: auto;
  max-height: calc(100vh - 200px);
}

/* SVG 样式 */
.deco-ring {
  fill: none;
  stroke: rgba(34, 211, 238, 0.05);
  stroke-width: 1;
}

.deco-ring-2 {
  stroke-dasharray: 4 8;
  animation: rotate-slow 120s linear infinite;
}

@keyframes rotate-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.orbit-ring {
  fill: none;
  stroke: rgba(34, 211, 238, 0.15);
  stroke-width: 1;
}

.orbit-ring-glow {
  fill: none;
  stroke: rgba(34, 211, 238, 0.08);
  stroke-width: 8;
}

.inner-orbit {
  stroke-dasharray: 8 4;
  animation: rotate-cw 80s linear infinite;
}

.outer-orbit {
  stroke-dasharray: 12 6;
  animation: rotate-ccw 100s linear infinite;
}

@keyframes rotate-cw {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes rotate-ccw {
  from { transform: rotate(0deg); }
  to { transform: rotate(-360deg); }
}

.core-ring {
  fill: none;
  stroke: #22d3ee;
  stroke-width: 2;
  filter: url(#glow-strong);
}

.core-inner {
  fill: rgba(34, 211, 238, 0.1);
  stroke: rgba(34, 211, 238, 0.3);
  stroke-width: 1;
}

.core-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 14px;
  font-weight: 700;
  fill: #22d3ee;
  text-anchor: middle;
  letter-spacing: 2px;
}

.core-subtitle {
  font-family: 'Orbitron', sans-serif;
  font-size: 10px;
  fill: #94a3b8;
  text-anchor: middle;
  letter-spacing: 1px;
}

.core-version {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8px;
  fill: #64748b;
  text-anchor: middle;
}

/* 连接线 */
.connection-line {
  stroke-width: 2;
  opacity: 0.2;
  transition: opacity 0.3s, stroke-width 0.3s;
}

.connection-line.active {
  opacity: 0.8;
  stroke-width: 3;
  filter: url(#glow-soft);
}

.connection-curve {
  fill: none;
  stroke-width: 1.5;
  opacity: 0.15;
  transition: opacity 0.3s, stroke-width 0.3s;
}

.connection-curve.active {
  opacity: 0.6;
  stroke-width: 2.5;
  filter: url(#glow-soft);
}

/* 脉冲波纹 */
.pulse-wave {
  fill: none;
  stroke: rgba(34, 211, 238, 0.4);
  stroke-width: 1;
  animation: pulse-expand 4s ease-out infinite;
}

.pulse-2 { animation-delay: 1.3s; }
.pulse-3 { animation-delay: 2.6s; }

@keyframes pulse-expand {
  0% { stroke-opacity: 0.5; transform: scale(0.98); }
  100% { stroke-opacity: 0; transform: scale(1.08); }
}

/* 模块节点 */
.module-node {
  cursor: pointer;
}

.module-node:hover .node-bg,
.module-node.active .node-bg {
  filter: url(#glow-strong);
}

.module-node.active .node-inner {
  opacity: 0.9;
}

.node-glow {
  transition: opacity 0.3s, filter 0.3s;
  opacity: 0.5;
}

.module-node:hover .node-glow,
.module-node.active .node-glow {
  opacity: 1;
  filter: url(#glow-strong);
}

.node-bg {
  fill: rgba(3, 7, 18, 0.9);
  stroke-width: 2;
  transition: stroke-width 0.3s, filter 0.3s;
}

.module-node:hover .node-bg,
.module-node.active .node-bg {
  stroke-width: 3;
  filter: url(#glow-soft);
}

.node-inner {
  transition: all 0.3s;
}

.node-icon {
  font-size: 22px;
  text-anchor: middle;
  dominant-baseline: middle;
}

.node-name {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  fill: #94a3b8;
  text-anchor: middle;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.node-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  fill: #94a3b8;
  text-anchor: middle;
  letter-spacing: 0.5px;
}

.node-status {
  fill: #64748b;
}

.node-status.active {
  fill: #10b981;
  filter: drop-shadow(0 0 4px #10b981);
}

/* 数据粒子 */
.particle {
  fill: #22d3ee;
  opacity: 0.8;
}

.p1 { animation-delay: 0s; }
.p2 { animation-delay: 1s; }
.p3 { animation-delay: 2s; }

/* 图例 */
.viz-legend {
  display: flex;
  justify-content: center;
  gap: 32px;
  margin-top: 24px;
}

.legend-section {
  display: flex;
  align-items: center;
  gap: 10px;
}

.legend-marker {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-marker.inner {
  background: linear-gradient(135deg, #a855f7, #3b82f6);
  box-shadow: 0 0 8px rgba(168, 85, 247, 0.5);
}

.legend-marker.outer {
  background: linear-gradient(135deg, #ec4899, #f97316);
  border-radius: 3px;
  box-shadow: 0 0 8px rgba(236, 72, 153, 0.5);
}

.legend-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #64748b;
}

/* 详情面板 */
.detail-panel {
  width: 420px;
  background: rgba(3, 7, 18, 0.95);
  border-left: 1px solid rgba(34, 211, 238, 0.15);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.scan-line {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #22d3ee, transparent);
  opacity: 0.5;
  animation: scan 3s linear infinite;
}

@keyframes scan {
  0% { transform: translateY(0); opacity: 0; }
  10% { opacity: 0.5; }
  90% { opacity: 0.5; }
  100% { transform: translateY(calc(100vh - 120px)); opacity: 0; }
}

/* 空状态 */
.panel-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  text-align: center;
}

.empty-visual {
  position: relative;
  width: 100px;
  height: 100px;
  margin-bottom: 24px;
}

.empty-rings {
  position: absolute;
  inset: 0;
}

.ring {
  position: absolute;
  border: 1px solid rgba(34, 211, 238, 0.2);
  border-radius: 50%;
  animation: ring-pulse 3s ease-out infinite;
}

.r1 { inset: 0; animation-delay: 0s; }
.r2 { inset: 10px; animation-delay: 0.5s; }
.r3 { inset: 20px; animation-delay: 1s; }

@keyframes ring-pulse {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.05); }
}

.empty-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 32px;
  color: #22d3ee;
  opacity: 0.6;
}

.panel-empty h3 {
  font-family: 'Orbitron', sans-serif;
  font-size: 16px;
  font-weight: 600;
  color: #e2e8f0;
  margin: 0 0 12px;
  letter-spacing: 2px;
}

.panel-empty > p {
  font-size: 13px;
  color: #64748b;
  line-height: 1.6;
  margin: 0 0 32px;
  max-width: 280px;
}

.empty-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 32px;
}

.es-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.es-value {
  font-family: 'Orbitron', sans-serif;
  font-size: 24px;
  font-weight: 600;
  color: #22d3ee;
}

.es-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #64748b;
  letter-spacing: 0.5px;
}

.quick-links {
  display: flex;
  gap: 12px;
}

.quick-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(34, 211, 238, 0.1);
  border: 1px solid rgba(34, 211, 238, 0.2);
  border-radius: 6px;
  color: #22d3ee;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-link:hover {
  background: rgba(34, 211, 238, 0.15);
  border-color: rgba(34, 211, 238, 0.4);
}

.quick-link span {
  font-size: 14px;
}

/* 面板内容 */
.panel-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 24px;
  overflow-y: auto;
}

.module-header {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.header-badge {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.badge-icon {
  font-size: 28px;
}

.header-info {
  flex: 1;
  min-width: 0;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.header-info h2 {
  font-family: 'Orbitron', sans-serif;
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: #e2e8f0;
}

.module-type {
  padding: 3px 8px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  font-weight: 500;
  letter-spacing: 1px;
}

.module-type.core {
  background: rgba(168, 85, 247, 0.2);
  color: #a855f7;
}

.module-type.framework {
  background: rgba(236, 72, 153, 0.2);
  color: #ec4899;
}

.module-desc {
  font-size: 13px;
  color: #94a3b8;
  display: block;
  margin-bottom: 8px;
}

.info-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-item {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 6px;
}

.meta-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #64748b;
}

.meta-dot.active {
  background: #10b981;
  box-shadow: 0 0 6px #10b981;
}

.meta-divider {
  color: #374151;
}

/* 标签页 */
.detail-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: rgba(34, 211, 238, 0.05);
  border-radius: 8px;
  margin-bottom: 20px;
}

.tab {
  flex: 1;
  padding: 10px 12px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #64748b;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}

.tab:hover {
  color: #94a3b8;
}

.tab.active {
  background: rgba(34, 211, 238, 0.15);
  color: #22d3ee;
}

/* 标签页内容 */
.tab-content {
  flex: 1;
  overflow-y: auto;
}

.content-section {
  margin-bottom: 20px;
}

.content-section h4 {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 500;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0 0 10px;
}

.section-text {
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.7;
  margin: 0;
}

.feature-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.feature-tag {
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #94a3b8;
}

.dependency-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.dep-item {
  padding: 6px 12px;
  background: rgba(34, 211, 238, 0.1);
  border-radius: 4px;
  font-size: 12px;
  color: #22d3ee;
  cursor: pointer;
  transition: all 0.2s;
}

.dep-item:hover {
  background: rgba(34, 211, 238, 0.2);
}

/* Metrics */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.metric-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.metric-visual {
  position: relative;
  width: 60px;
  height: 60px;
  margin: 0 auto 10px;
}

.metric-ring {
  width: 100%;
  height: 100%;
}

.ring-bg {
  fill: none;
  stroke: rgba(255, 255, 255, 0.06);
  stroke-width: 3;
}

.ring-fill {
  fill: none;
  stroke-width: 3;
  stroke-dasharray: 75 100;
  stroke-linecap: round;
  transform: rotate(-90deg);
  transform-origin: center;
}

.metric-value {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-family: 'Orbitron', sans-serif;
  font-size: 12px;
  font-weight: 600;
}

.metric-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.live-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #10b981;
}

.live-dot {
  width: 6px;
  height: 6px;
  background: #10b981;
  border-radius: 50%;
  animation: pulse-dot 1s ease-in-out infinite;
}

/* API Section */
.api-section {
  margin-bottom: 20px;
}

.api-section h4 {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 500;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0 0 10px;
}

.api-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.api-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 6px;
}

.method {
  padding: 3px 8px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.method.get {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.method.post {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.method.put {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.method.event {
  background: rgba(168, 85, 247, 0.2);
  color: #a855f7;
}

.api-item code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #94a3b8;
}

/* Develop */
.develop-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.dev-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
}

.dev-icon {
  font-size: 20px;
}

.dev-details {
  flex: 1;
  min-width: 0;
}

.dev-label {
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.dev-details code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #22d3ee;
}

.dev-note {
  font-size: 12px;
  color: #64748b;
  line-height: 1.6;
  padding: 12px;
  background: rgba(34, 211, 238, 0.05);
  border-left: 2px solid rgba(34, 211, 238, 0.3);
  border-radius: 0 4px 4px 0;
  margin: 0;
}

/* 操作按钮 */
.action-buttons {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr;
  gap: 10px;
  margin-top: auto;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.btn-primary,
.btn-secondary,
.btn-develop {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  grid-column: 1 / -1;
  color: white;
  border: none;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94a3b8;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
}

.btn-develop {
  background: rgba(34, 211, 238, 0.1);
  border: 1px solid rgba(34, 211, 238, 0.3);
  color: #22d3ee;
}

.btn-develop:hover {
  background: rgba(34, 211, 238, 0.2);
}

/* 底部状态栏 */
.command-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 32px;
  background: rgba(3, 7, 18, 0.9);
  border-top: 1px solid rgba(34, 211, 238, 0.1);
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #64748b;
}

.footer-left,
.footer-center,
.footer-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.footer-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.fi-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #64748b;
}

.fi-dot.active {
  background: #10b981;
  box-shadow: 0 0 6px #10b981;
}

.footer-sep {
  color: #374151;
}

/* 滚动条样式 */
.panel-content::-webkit-scrollbar,
.tab-content::-webkit-scrollbar {
  width: 4px;
}

.panel-content::-webkit-scrollbar-track,
.tab-content::-webkit-scrollbar-track {
  background: transparent;
}

.panel-content::-webkit-scrollbar-thumb,
.tab-content::-webkit-scrollbar-thumb {
  background: rgba(34, 211, 238, 0.2);
  border-radius: 2px;
}

.panel-content::-webkit-scrollbar-thumb:hover,
.tab-content::-webkit-scrollbar-thumb:hover {
  background: rgba(34, 211, 238, 0.4);
}
</style>
