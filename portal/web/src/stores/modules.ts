import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import {
  modulesApi,
  type ModuleDefinition,
  type ModuleStatusResponse,
  type ModuleMetricsResponse,
  type AgentModulesResponse,
} from '@/api'

// 模块类别
export type ModuleCategory = 'core' | 'multi'

// 模块运行状态
export type ModuleRunStatus = 'active' | 'inactive' | 'error' | 'idle'

// 模块详情（合并定义和状态）
export interface ModuleDetail extends ModuleDefinition {
  status: ModuleRunStatus
  enabled: boolean
  config: Record<string, any>
  metrics?: ModuleMetricsResponse
}

export const useModulesStore = defineStore('modules', () => {
  // State
  const definitions = ref<ModuleDefinition[]>([])
  const agentModules = ref<Map<string, Record<string, ModuleStatusResponse>>>(new Map())
  const moduleMetrics = ref<Map<string, Record<string, ModuleMetricsResponse>>>(new Map())
  const loading = ref(false)
  const error = ref<string | null>(null)
  const selectedModuleType = ref<string | null>(null)
  const selectedAgentId = ref<string | null>(null)

  // Getters
  const coreModules = computed(() =>
    definitions.value.filter(m => m.category === 'core')
  )

  const multiModules = computed(() =>
    definitions.value.filter(m => m.category === 'multi')
  )

  const getModuleByType = computed(() => (type: string) =>
    definitions.value.find(m => m.type === type)
  )

  // 获取 Agent 的模块详情列表
  const getAgentModuleDetails = computed(() => (agentId: string): ModuleDetail[] => {
    const agentConfig = agentModules.value.get(agentId) || {}
    const agentMetrics = moduleMetrics.value.get(agentId) || {}

    return definitions.value.map(def => {
      const status = agentConfig[def.type]
      const metrics = agentMetrics[def.type]

      return {
        ...def,
        status: status?.status as ModuleRunStatus || 'inactive',
        enabled: status?.enabled ?? true,
        config: status?.config || def.default_config,
        metrics,
      }
    })
  })

  // 获取选中的模块详情
  const selectedModuleDetail = computed((): ModuleDetail | null => {
    if (!selectedModuleType.value || !selectedAgentId.value) return null

    const details = getAgentModuleDetails.value(selectedAgentId.value)
    return details.find(d => d.type === selectedModuleType.value) || null
  })

  // Actions

  // 加载所有模块定义
  async function loadDefinitions() {
    loading.value = true
    error.value = null

    try {
      definitions.value = await modulesApi.getAll()
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载模块定义失败'
      console.error('Failed to load module definitions:', e)
    } finally {
      loading.value = false
    }
  }

  // 加载 Agent 的模块配置
  async function loadAgentModules(agentId: string) {
    loading.value = true
    error.value = null

    try {
      const response = await modulesApi.getAgentModules(agentId)
      agentModules.value.set(agentId, response.modules)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载 Agent 模块配置失败'
      console.error('Failed to load agent modules:', e)
    } finally {
      loading.value = false
    }
  }

  // 更新模块配置
  async function updateModuleConfig(
    agentId: string,
    moduleType: string,
    config: { enabled?: boolean; settings?: Record<string, any> }
  ) {
    try {
      const response = await modulesApi.updateAgentModule(agentId, moduleType, config)

      // 更新本地状态
      const agentConfig = agentModules.value.get(agentId) || {}
      agentConfig[moduleType] = response
      agentModules.value.set(agentId, { ...agentConfig })

      return response
    } catch (e) {
      error.value = e instanceof Error ? e.message : '更新模块配置失败'
      throw e
    }
  }

  // 启用模块
  async function enableModule(agentId: string, moduleType: string) {
    try {
      await modulesApi.enableModule(agentId, moduleType)
      await loadAgentModules(agentId)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '启用模块失败'
      throw e
    }
  }

  // 禁用模块
  async function disableModule(agentId: string, moduleType: string) {
    try {
      await modulesApi.disableModule(agentId, moduleType)
      await loadAgentModules(agentId)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '禁用模块失败'
      throw e
    }
  }

  // 重置模块配置
  async function resetModule(agentId: string, moduleType: string) {
    try {
      await modulesApi.resetModule(agentId, moduleType)
      await loadAgentModules(agentId)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '重置模块配置失败'
      throw e
    }
  }

  // 加载模块指标
  async function loadModuleMetrics(agentId: string, moduleType: string) {
    try {
      const metrics = await modulesApi.getAgentModuleMetrics(agentId, moduleType)

      const agentMetrics = moduleMetrics.value.get(agentId) || {}
      agentMetrics[moduleType] = metrics
      moduleMetrics.value.set(agentId, { ...agentMetrics })

      return metrics
    } catch (e) {
      console.error('Failed to load module metrics:', e)
      return null
    }
  }

  // 加载 Agent 所有模块的指标
  async function loadAllModuleMetrics(agentId: string) {
    const promises = definitions.value.map(def =>
      loadModuleMetrics(agentId, def.type)
    )
    await Promise.all(promises)
  }

  // 选择模块
  function selectModule(agentId: string, moduleType: string) {
    selectedAgentId.value = agentId
    selectedModuleType.value = moduleType
  }

  // 清除选择
  function clearSelection() {
    selectedAgentId.value = null
    selectedModuleType.value = null
  }

  // 初始化（加载定义）
  async function init() {
    if (definitions.value.length === 0) {
      await loadDefinitions()
    }
  }

  return {
    // State
    definitions,
    agentModules,
    moduleMetrics,
    loading,
    error,
    selectedModuleType,
    selectedAgentId,

    // Getters
    coreModules,
    multiModules,
    getModuleByType,
    getAgentModuleDetails,
    selectedModuleDetail,

    // Actions
    loadDefinitions,
    loadAgentModules,
    updateModuleConfig,
    enableModule,
    disableModule,
    resetModule,
    loadModuleMetrics,
    loadAllModuleMetrics,
    selectModule,
    clearSelection,
    init,
  }
})
