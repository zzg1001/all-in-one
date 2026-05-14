<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { ccswitchApi, type CCConfig } from '@/api'

// Tab 切换
const activeTab = ref<'models' | 'proxy'>('models')

// ========== 代理配置相关 ==========
interface ProxyConfig {
  id: string
  name: string
  description: string
  target_base_url: string   // 原始API地址（如 DashScope）
  target_api_key: string
  target_model: string      // 原始模型
  proxy_port: number        // 代理端口
  proxy_url: string         // 代理地址（对外）
  proxy_model: string       // 对外模型名（如 claude-3-opus）
  max_tokens: number
  temperature: number
  is_running: boolean
}

interface ProxyStatus {
  is_running: boolean
  proxy_model: string | null  // 对外模型名
  proxy_url: string | null    // 代理地址
  running_config_name: string | null
}

// API_BASE: 生产环境是 /api，开发环境是 http://localhost:8001/api
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api'
const proxyConfigs = ref<ProxyConfig[]>([])
const proxyStatus = ref<ProxyStatus | null>(null)
const proxyLoading = ref(false)
const showProxyModal = ref(false)
const isProxyEditing = ref(false)
const showProxyApiKey = ref(false)
const showProxyViewModal = ref(false)
const viewingProxyConfig = ref<ProxyConfig | null>(null)

const proxyForm = ref({
  id: '',
  name: '',
  description: '',
  proxy_port: 4000,
  proxy_url: 'http://localhost:4000',
  proxy_model: 'claude-sonnet-4-20250514',
  target_base_url: 'https://dashscope.aliyuncs.com/apps/anthropic',
  target_api_key: '',
  target_model: 'qwen-plus',
  max_tokens: 4096,
  temperature: 0.7,
})

// Toast 提示
const toast = ref({ show: false, type: 'success' as 'success' | 'error', message: '' })
function showToast(type: 'success' | 'error', message: string) {
  toast.value = { show: true, type, message }
  setTimeout(() => { toast.value.show = false }, 3000)
}

// 测试连通性
const isTesting = ref(false)
async function testConnection() {
  if (!proxyForm.value.target_base_url || !proxyForm.value.target_api_key || !proxyForm.value.target_model) {
    showToast('error', '请先填写原始 API 地址、API Key 和模型')
    return
  }
  isTesting.value = true
  try {
    const res = await fetch(`${API_BASE}/proxy/test-connection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_base_url: proxyForm.value.target_base_url,
        target_api_key: proxyForm.value.target_api_key,
        target_model: proxyForm.value.target_model
      })
    })
    const data = await res.json()
    if (data.success) {
      showToast('success', data.message)
    } else {
      showToast('error', data.message)
    }
  } catch (e) {
    showToast('error', '测试请求失败')
  } finally {
    isTesting.value = false
  }
}


async function fetchProxyConfigs() {
  proxyLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/proxy/configs`)
    if (res.ok) proxyConfigs.value = await res.json()
  } catch (e) { console.error('获取代理配置失败:', e) }
  finally { proxyLoading.value = false }
}

async function fetchProxyStatus() {
  try {
    const res = await fetch(`${API_BASE}/proxy/status`)
    if (res.ok) {
      proxyStatus.value = await res.json()
    }
  } catch (e) { console.error('获取代理状态失败:', e) }
}

async function saveProxyConfig() {
  try {
    const url = isProxyEditing.value ? `${API_BASE}/proxy/configs/${proxyForm.value.id}` : `${API_BASE}/proxy/configs`
    const res = await fetch(url, { method: isProxyEditing.value ? 'PUT' : 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(proxyForm.value) })
    if (res.ok) {
      showProxyModal.value = false
      showToast('success', isProxyEditing.value ? '配置已更新' : '配置已创建')
      fetchProxyConfigs()
      fetchProxyStatus()
    } else {
      const err = await res.json()
      showToast('error', err.detail || '保存失败')
    }
  } catch (e) {
    showToast('error', '保存失败')
  }
}

async function deleteProxyConfig(config: ProxyConfig) {
  // 检查是否被模型配置引用
  const referencedBy = configs.value.filter(m =>
    m.base_url && (
      m.base_url === config.proxy_url ||
      m.base_url.includes(`localhost:${config.proxy_port}`) ||
      m.base_url.includes(`127.0.0.1:${config.proxy_port}`)
    )
  )

  if (referencedBy.length > 0) {
    const names = referencedBy.map(m => `"${m.name}"`).join('、')
    showToast('error', `无法删除：该代理被模型配置 ${names} 引用中`)
    return
  }

  if (!confirm(`确定删除配置 "${config.name}"？`)) return
  try {
    const res = await fetch(`${API_BASE}/proxy/configs/${config.id}`, { method: 'DELETE' })
    if (res.ok) {
      showToast('success', '配置已删除')
      fetchProxyConfigs()
      fetchProxyStatus()
    }
  } catch (e) {
    showToast('error', '删除失败')
  }
}

async function startProxy(config: ProxyConfig) {
  try {
    const res = await fetch(`${API_BASE}/proxy/configs/${config.id}/start`, { method: 'POST' })
    const data = await res.json()
    if (res.ok) {
      showToast('success', `代理已启动 - ${data.proxy_url}`)
      fetchProxyConfigs()
      fetchProxyStatus()
    } else {
      showToast('error', data.detail || '启动失败')
    }
  } catch (e) {
    showToast('error', '启动失败')
  }
}

function copyToClipboard(text: string, label: string) {
  navigator.clipboard.writeText(text)
  showToast('success', `已复制 ${label}`)
}

async function stopProxy(config: ProxyConfig) {
  try {
    const res = await fetch(`${API_BASE}/proxy/configs/${config.id}/stop`, { method: 'POST' })
    if (res.ok) {
      showToast('success', '代理已停止')
      fetchProxyConfigs()
      fetchProxyStatus()
    }
  } catch (e) {
    showToast('error', '停止失败')
  }
}

async function restartProxy(config: ProxyConfig) {
  showToast('success', '正在重启...')
  try {
    // 先停止
    await fetch(`${API_BASE}/proxy/configs/${config.id}/stop`, { method: 'POST' })
    // 等待一下
    await new Promise(resolve => setTimeout(resolve, 500))
    // 再启动
    const res = await fetch(`${API_BASE}/proxy/configs/${config.id}/start`, { method: 'POST' })
    if (res.ok) {
      showToast('success', '代理已重启')
      fetchProxyConfigs()
      fetchProxyStatus()
    } else {
      showToast('error', '重启失败')
    }
  } catch (e) {
    showToast('error', '重启失败')
  }
}

function openProxyCreateModal() {
  isProxyEditing.value = false; showProxyApiKey.value = false
  proxyForm.value = {
    id: '',
    name: '',
    description: '',
    proxy_port: 4000,
    proxy_url: 'http://localhost:4000',
    proxy_model: 'claude-sonnet-4-20250514',
    target_base_url: 'https://dashscope.aliyuncs.com/apps/anthropic',
    target_api_key: '',
    target_model: 'qwen-plus',
    max_tokens: 4096,
    temperature: 0.7
  }
  showProxyModal.value = true
}

function openProxyViewModal(config: ProxyConfig) {
  viewingProxyConfig.value = config
  showProxyViewModal.value = true
}

function openProxyEditModal(config: ProxyConfig) {
  isProxyEditing.value = true; showProxyApiKey.value = false
  const port = config.proxy_port || 4000
  proxyForm.value = {
    id: config.id,
    name: config.name,
    description: config.description || '',
    target_base_url: config.target_base_url || '',
    target_api_key: config.target_api_key || '',
    target_model: config.target_model || '',
    proxy_port: port,
    proxy_url: config.proxy_url || `http://localhost:${port}`,
    proxy_model: config.proxy_model || 'claude-sonnet-4-20250514',
    max_tokens: config.max_tokens || 4096,
    temperature: config.temperature ?? 0.7
  }
  showProxyModal.value = true
}

function copyProxyUrl() {
  if (proxyStatus.value?.proxy_url) {
    navigator.clipboard.writeText(proxyStatus.value.proxy_url)
    showToast('success', '已复制代理地址')
  }
}

// 应用代理配置到模型配置
function applyProxyToModel(config: ProxyConfig) {
  // 切换到模型配置 tab
  activeTab.value = 'models'

  // 打开新建模型配置弹框，并自动填充代理信息
  testingDirect.value = false
  testDirectResult.value = null
  testDirectPassed.value = false
  showApiKey.value = false
  useCustomModel.value = true  // 使用自定义模型

  editingConfig.value = {
    name: `${config.name} - 模型配置`,
    description: `通过代理 ${config.name} 连接`,
    api_type: 'claude_sdk',
    model_id: config.proxy_model,  // 代理对外模型名
    api_key: 'proxy-no-key-needed',  // 代理不需要真实 key
    base_url: config.proxy_url,  // 代理地址
    max_tokens: config.max_tokens || 4096,
    temperature: config.temperature ?? 0.7,
    top_p: 1.0,
    system_prompt: '',
  }
  showEditModal.value = true

  showToast('success', '已填充代理配置，请确认后保存')
}

// ========== 模型配置相关 ==========
// 状态
const configs = ref<CCConfig[]>([])
const loading = ref(false)
const showEditModal = ref(false)
const showImportModal = ref(false)
const editingConfig = ref<Partial<CCConfig> | null>(null)
const testingId = ref<string | null>(null)
const testResult = ref<{ success: boolean; message: string; latency_ms?: number } | null>(null)
const importJson = ref('')
const searchQuery = ref('')

// 弹框内直接测试
const testingDirect = ref(false)
const testDirectResult = ref<{ success: boolean; message: string; latency_ms?: number } | null>(null)
const testDirectPassed = ref(false)

// 自定义模型输入
const useCustomModel = ref(false)

// API Key 显示/隐藏
const showApiKey = ref(false)

// API 类型选项 - 只使用 Claude Agent SDK
const apiTypeOptions = [
  { value: 'claude_sdk', label: 'Claude Agent SDK', description: '完整 Agent 能力，支持 Bash/Read/Write/Edit 等工具' },
]

// 模型选项（根据 API 类型动态调整）
const modelOptions = [
  { value: 'claude-opus-4-5', label: 'Claude Opus 4.5' },
  { value: 'claude-sonnet-4', label: 'Claude Sonnet 4' },
  { value: 'claude-haiku-3', label: 'Claude Haiku 3' },
]

// 过滤后的配置列表
const filteredConfigs = computed(() => {
  if (!searchQuery.value) return configs.value
  const q = searchQuery.value.toLowerCase()
  return configs.value.filter(c =>
    c.name.toLowerCase().includes(q) ||
    c.model_id.toLowerCase().includes(q) ||
    c.description?.toLowerCase().includes(q)
  )
})

// 统计数据
const stats = computed(() => ({
  total: configs.value.length,
  active: configs.value.filter(c => c.is_active).length,
}))

// 当前激活的配置
const activeConfig = computed(() => configs.value.find(c => c.is_active))

// 加载配置列表
const loadConfigs = async () => {
  loading.value = true
  try {
    configs.value = await ccswitchApi.getAll()
  } catch (e) {
    console.error('加载失败:', e)
  } finally {
    loading.value = false
  }
}

// 打开编辑弹框
const openEdit = (config?: CCConfig) => {
  // 重置测试状态
  testingDirect.value = false
  testDirectResult.value = null
  testDirectPassed.value = !!config  // 编辑现有配置时默认允许保存
  showApiKey.value = false  // 重置 API Key 显示状态

  if (config) {
    editingConfig.value = { ...config }
    // 判断是否是自定义模型
    const claudeModels = ['claude-opus-4-5', 'claude-sonnet-4', 'claude-haiku-3']
    useCustomModel.value = !claudeModels.includes(config.model_id)
  } else {
    editingConfig.value = {
      name: '',
      description: '',
      api_type: 'claude_sdk',
      model_id: 'claude-opus-4-5',
      api_key: '',
      base_url: '',
      max_tokens: 4096,
      temperature: 0.7,
      top_p: 1.0,
      system_prompt: '',
    }
    useCustomModel.value = false
  }
  showEditModal.value = true
}

// 弹框内直接测试配置
const testConfigDirect = async () => {
  if (!editingConfig.value) return
  testingDirect.value = true
  testDirectResult.value = null
  testDirectPassed.value = false

  try {
    const result = await ccswitchApi.testDirect(editingConfig.value as any)
    testDirectResult.value = result
    testDirectPassed.value = result.success
  } catch (e: any) {
    testDirectResult.value = { success: false, message: e.message || '测试失败' }
    testDirectPassed.value = false
  } finally {
    testingDirect.value = false
  }
}


// 监听模型选择，处理自定义选项
watch(() => editingConfig.value?.model_id, (newVal) => {
  if (newVal === '__custom__') {
    useCustomModel.value = true
    if (editingConfig.value) {
      editingConfig.value.model_id = ''
    }
  }
})

// 保存配置
const saveConfig = async () => {
  if (!editingConfig.value) return
  try {
    if (editingConfig.value.id) {
      await ccswitchApi.update(editingConfig.value.id, editingConfig.value)
    } else {
      await ccswitchApi.create(editingConfig.value as any)
    }
    showEditModal.value = false
    await loadConfigs()
  } catch (e) {
    alert('保存失败')
  }
}

// 删除配置
const deleteConfig = async (id: string) => {
  if (!confirm('确定删除此配置？')) return
  try {
    await ccswitchApi.delete(id)
    await loadConfigs()
  } catch (e) {
    alert('删除失败')
  }
}

// 测试配置
const testConfig = async (id: string) => {
  testingId.value = id
  testResult.value = null
  try {
    const result = await ccswitchApi.test(id)
    testResult.value = result
    setTimeout(() => {
      if (testingId.value === id) {
        testResult.value = null
        testingId.value = null
      }
    }, 5000)
  } catch (e) {
    testResult.value = { success: false, message: '测试失败' }
  }
}

// 切换启用状态
const toggleConfig = async (id: string) => {
  try {
    await ccswitchApi.toggle(id)
    await loadConfigs()
  } catch (e) {
    alert('操作失败')
  }
}

// 复制配置
const copyConfig = async (id: string) => {
  try {
    await ccswitchApi.copy(id)
    await loadConfigs()
  } catch (e) {
    alert('复制失败')
  }
}

// 导出
const exportConfig = async (id: string) => {
  try {
    const config = await ccswitchApi.export(id)
    downloadJson(config, `model-config-${id}.json`)
  } catch (e) {
    alert('导出失败')
  }
}

const exportAll = async () => {
  try {
    const data = await ccswitchApi.exportAll()
    downloadJson(data, 'model-configs-all.json')
  } catch (e) {
    alert('导出失败')
  }
}

const downloadJson = (data: any, filename: string) => {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

// 导入
const openImport = () => {
  importJson.value = ''
  showImportModal.value = true
}

const doImport = async () => {
  try {
    const data = JSON.parse(importJson.value)
    const result = await ccswitchApi.import(data)
    alert(result.message)
    showImportModal.value = false
    await loadConfigs()
  } catch (e) {
    alert('导入失败，请检查 JSON 格式')
  }
}

const handleFileImport = (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (e) => {
    importJson.value = e.target?.result as string
  }
  reader.readAsText(file)
}

onMounted(() => {
  loadConfigs()
  fetchProxyConfigs()
  fetchProxyStatus()
})
</script>

<template>
  <div class="models-page">
    <!-- Tab 切换 -->
    <div class="tabs-header">
      <button class="tab-btn" :class="{ active: activeTab === 'models' }" @click="activeTab = 'models'">
        <svg viewBox="0 0 20 20" fill="currentColor"><path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3z"/></svg>
        模型配置
      </button>
      <button class="tab-btn" :class="{ active: activeTab === 'proxy' }" @click="activeTab = 'proxy'">
        <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"/></svg>
        API 代理
        <span v-if="proxyStatus?.is_running" class="status-dot running"></span>
      </button>
    </div>

    <!-- ========== 模型配置 Tab ========== -->
    <div v-show="activeTab === 'models'" class="tab-content">
      <!-- 内容卡片 -->
      <div class="content-card">
        <!-- 顶部操作栏 -->
        <div class="card-section header-section">
          <div class="header-info">
            <h2 class="section-title">模型配置管理</h2>
            <p class="page-desc">管理 AI 模型的 API 配置，支持多配置快速切换</p>
            <div class="active-badge" v-if="activeConfig">
              <span class="dot"></span>
              当前启用: {{ activeConfig.name }}
            </div>
          </div>
          <div class="header-actions">
            <div class="search-box">
              <svg class="search-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
              </svg>
              <input v-model="searchQuery" type="text" placeholder="搜索配置..." />
            </div>
            <button class="btn-secondary" @click="openImport">
              <svg viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"/>
              </svg>
              导入
            </button>
            <button class="btn-secondary" @click="exportAll">
              <svg viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
              </svg>
              导出全部
            </button>
            <button class="btn-primary" @click="openEdit()">
              <svg viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"/>
              </svg>
              新建配置
            </button>
          </div>
        </div>

        <!-- 统计卡片 -->
        <div class="card-section stats-section">
          <div class="stats-row">
            <div class="stat-card">
              <div class="stat-icon blue">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z"/>
                </svg>
              </div>
              <div class="stat-content">
                <span class="stat-value">{{ stats.total }}</span>
                <span class="stat-label">总配置数</span>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon green">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                </svg>
              </div>
              <div class="stat-content">
                <span class="stat-value">{{ stats.active }}</span>
                <span class="stat-label">已启用</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 配置列表 -->
        <div class="card-section list-section">
          <h3 class="list-title">配置列表</h3>
          <div class="config-list">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <span>加载中...</span>
      </div>

      <div v-else-if="filteredConfigs.length === 0" class="empty-state">
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z"/>
        </svg>
        <p>暂无模型配置</p>
        <button class="btn-primary" @click="openEdit()">创建第一个配置</button>
      </div>

      <div v-else class="config-grid">
        <div
          v-for="config in filteredConfigs"
          :key="config.id"
          class="config-card"
          :class="{ active: config.is_active, inactive: !config.is_active }"
        >
          <!-- 卡片头部 -->
          <div class="card-header">
            <div class="card-title">
              <h3>{{ config.name }}</h3>
              <span class="status-badge" :class="config.is_active ? 'active' : 'inactive'">
                {{ config.is_active ? '启用中' : '未启用' }}
              </span>
            </div>
            <div class="card-actions">
              <button class="icon-btn" @click="openEdit(config)" title="编辑">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"/>
                </svg>
              </button>
              <button class="icon-btn" @click="copyConfig(config.id)" title="复制">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z"/>
                  <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z"/>
                </svg>
              </button>
              <button class="icon-btn" @click="exportConfig(config.id)" title="导出">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
                </svg>
              </button>
              <button class="icon-btn danger" @click="deleteConfig(config.id)" title="删除">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- 卡片内容 -->
          <div class="card-body">
            <p class="config-desc">{{ config.description || '暂无描述' }}</p>

            <div class="config-info">
              <div class="info-row">
                <span class="info-label">API 类型</span>
                <span class="info-value api-type-tag" :class="config.api_type || 'anthropic'">
                  {{ apiTypeOptions.find(o => o.value === (config.api_type || 'anthropic'))?.label }}
                </span>
              </div>
              <div class="info-row">
                <span class="info-label">模型</span>
                <span class="info-value model-tag">{{ config.model_id }}</span>
              </div>
              <div class="info-row" v-if="config.api_type === 'openai' && config.base_url">
                <span class="info-label">Base URL</span>
                <span class="info-value url-value" :title="config.base_url">{{ config.base_url }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">Max Tokens</span>
                <span class="info-value">{{ config.max_tokens }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">Temperature</span>
                <span class="info-value">{{ config.temperature }}</span>
              </div>
            </div>
          </div>

          <!-- 卡片底部 -->
          <div class="card-footer">
            <button
              class="btn-test"
              @click="testConfig(config.id)"
              :disabled="testingId === config.id"
            >
              <svg v-if="testingId === config.id" class="spinning" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"/>
              </svg>
              <svg v-else viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clip-rule="evenodd"/>
              </svg>
              测试连接
            </button>

            <button
              class="btn-toggle"
              :class="config.is_active ? 'active' : ''"
              @click="toggleConfig(config.id)"
            >
              {{ config.is_active ? '禁用' : '启用' }}
            </button>
          </div>

          <!-- 测试结果 -->
          <div v-if="testingId === config.id && testResult" class="test-result" :class="testResult.success ? 'success' : 'error'">
            <svg v-if="testResult.success" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
            <svg v-else viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
            </svg>
            <span>{{ testResult.message }}</span>
            <span v-if="testResult.latency_ms" class="latency">{{ testResult.latency_ms }}ms</span>
          </div>
        </div>
      </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑弹框 -->
    <Teleport to="body">
      <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
        <div class="modal">
          <div class="modal-header">
            <h2>{{ editingConfig?.id ? '编辑配置' : '新建配置' }}</h2>
            <button class="modal-close" @click="showEditModal = false">&times;</button>
          </div>
          <div class="modal-body">
            <div class="form-grid">
              <!-- 通用配置 -->
              <div class="form-group full">
                <label>配置名称 <span class="required">*</span></label>
                <input v-model="editingConfig!.name" type="text" placeholder="例如：生产环境配置" />
              </div>
              <div class="form-group full">
                <label>描述</label>
                <input v-model="editingConfig!.description" type="text" placeholder="配置用途说明" />
              </div>

              <!-- API 类型选择 -->
              <div class="form-group full">
                <label>API 类型 <span class="required">*</span></label>
                <div class="api-type-cards">
                  <div
                    v-for="opt in apiTypeOptions"
                    :key="opt.value"
                    class="api-type-card"
                    :class="{ active: editingConfig!.api_type === opt.value }"
                    @click="editingConfig!.api_type = opt.value"
                  >
                    <div class="api-type-label">{{ opt.label }}</div>
                    <div class="api-type-desc">{{ opt.description }}</div>
                  </div>
                </div>
              </div>

              <!-- 模型配置 -->
                <div class="form-group">
                  <label>模型 <span class="required">*</span></label>
                  <select v-model="editingConfig!.model_id" v-if="!useCustomModel">
                    <option value="claude-opus-4-5">Claude Opus 4.5</option>
                    <option value="claude-sonnet-4">Claude Sonnet 4</option>
                    <option value="claude-haiku-3">Claude Haiku 3</option>
                    <option value="__custom__">自定义模型...</option>
                  </select>
                  <input v-else v-model="editingConfig!.model_id" type="text" placeholder="ollama/qwen3.5:9b" />
                  <span class="form-hint">
                    <a v-if="!useCustomModel" href="#" @click.prevent="useCustomModel = true">切换到手动输入</a>
                    <a v-else href="#" @click.prevent="useCustomModel = false; editingConfig!.model_id = 'claude-opus-4-5'">切换到下拉选择</a>
                  </span>
                </div>
                <div class="form-group">
                  <label>Base URL</label>
                  <input v-model="editingConfig!.base_url" type="text" placeholder="留空使用默认 Anthropic API" />
                  <span class="form-hint">SDK 会自动添加 /v1/messages，如用代理填 http://localhost:4000</span>
                </div>
                <div class="form-group full">
                  <label>API Key <span class="required">*</span></label>
                  <div class="input-with-toggle">
                    <input
                      v-model="editingConfig!.api_key"
                      :type="showApiKey ? 'text' : 'password'"
                      placeholder="sk-ant-..."
                    />
                    <button type="button" class="toggle-btn" @click="showApiKey = !showApiKey">
                      <svg v-if="showApiKey" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                        <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
                      </svg>
                      <svg v-else viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z" clip-rule="evenodd"/>
                        <path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z"/>
                      </svg>
                    </button>
                  </div>
                </div>
                <div class="form-group">
                  <label>Max Tokens</label>
                  <input v-model.number="editingConfig!.max_tokens" type="number" placeholder="4096" />
                </div>
                <div class="form-group">
                  <label>Temperature</label>
                  <input v-model.number="editingConfig!.temperature" type="number" step="0.1" min="0" max="2" placeholder="0.7" />
                </div>
                <div class="form-group">
                  <label>Top P</label>
                  <input v-model.number="editingConfig!.top_p" type="number" step="0.1" min="0" max="1" placeholder="1.0" />
                </div>

              <!-- 通用：System Prompt -->
              <div class="form-group full">
                <label>System Prompt</label>
                <textarea v-model="editingConfig!.system_prompt" rows="3" placeholder="系统提示词（可选）"></textarea>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="showEditModal = false">取消</button>
            <button class="btn-test-modal" @click="testConfigDirect" :disabled="testingDirect">
              <svg v-if="testingDirect" class="spinning" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"/>
              </svg>
              {{ testingDirect ? '测试中...' : '测试连接' }}
            </button>
            <button class="btn-primary" @click="saveConfig">保存</button>
          </div>
          <div v-if="testDirectResult" class="test-direct-result" :class="testDirectResult.success ? 'success' : 'error'">
            {{ testDirectResult.message }}
            <span v-if="testDirectResult.latency_ms" class="latency">{{ testDirectResult.latency_ms }}ms</span>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 导入弹框 -->
    <Teleport to="body">
      <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal = false">
        <div class="modal">
          <div class="modal-header">
            <h2>导入配置</h2>
            <button class="modal-close" @click="showImportModal = false">&times;</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>选择文件</label>
              <input type="file" accept=".json" @change="handleFileImport" class="file-input" />
            </div>
            <div class="form-group">
              <label>或粘贴 JSON</label>
              <textarea v-model="importJson" rows="10" placeholder='{"name": "配置名", "model_id": "claude-opus-4-5", ...}'></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="showImportModal = false">取消</button>
            <button class="btn-primary" @click="doImport" :disabled="!importJson">导入</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ========== API 代理 Tab ========== -->
    <div v-show="activeTab === 'proxy'" class="tab-content">
      <div class="content-card">
        <!-- 状态区域 -->
        <div class="card-section header-section">
          <h2 class="section-title">API 代理管理</h2>
          <p class="page-desc">将其他大模型 API 转换为 Anthropic 格式，支持 Claude Code 等工具使用</p>
          <!-- 运行状态 -->
          <div class="proxy-status-inline" :class="{ running: proxyStatus?.is_running }">
            <span class="dot" :class="proxyStatus?.is_running ? 'running' : 'stopped'"></span>
            <span class="status-text">{{ proxyStatus?.is_running ? '运行中' : '已停止' }}</span>
            <template v-if="proxyStatus?.is_running">
              <span class="divider">|</span>
              <span class="status-detail">{{ proxyStatus.running_config_name }}</span>
              <span class="status-detail clickable" @click="copyToClipboard(proxyStatus.proxy_model || '', '代理模型')">
                {{ proxyStatus.proxy_model }}
                <svg viewBox="0 0 20 20" fill="currentColor"><path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z"/><path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z"/></svg>
              </span>
              <span class="status-detail clickable" @click="copyToClipboard(proxyStatus.proxy_url || '', '代理地址')">
                {{ proxyStatus.proxy_url }}
                <svg viewBox="0 0 20 20" fill="currentColor"><path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z"/><path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z"/></svg>
              </span>
            </template>
          </div>
        </div>

        <!-- 工具栏和列表 -->
        <div class="card-section list-section">
          <div class="proxy-toolbar">
            <h3 class="list-title">代理配置列表</h3>
            <div class="toolbar-actions">
              <button class="btn-secondary" @click="fetchProxyConfigs">
                <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1z" clip-rule="evenodd"/></svg>
                刷新
              </button>
              <button class="btn-primary" @click="openProxyCreateModal">
                <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"/></svg>
                新建配置
              </button>
            </div>
          </div>

          <!-- 配置列表 -->
          <div class="proxy-list">
        <div v-if="proxyLoading" class="loading-state"><div class="spinner"></div><span>加载中...</span></div>
        <div v-else-if="proxyConfigs.length === 0" class="empty-state">
          <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4z" clip-rule="evenodd"/></svg>
          <p>暂无代理配置</p>
          <button class="btn-primary" @click="openProxyCreateModal">创建代理配置</button>
        </div>
        <div v-else class="proxy-grid">
          <div v-for="config in proxyConfigs" :key="config.id" class="proxy-card" :class="{ active: config.is_running }">
            <div class="card-header">
              <div class="card-title">
                <h3>{{ config.name }}</h3>
                <span class="status-badge" :class="config.is_running ? 'running' : 'stopped'">{{ config.is_running ? '运行中' : '已停止' }}</span>
              </div>
              <div class="card-actions">
                <button class="icon-btn" @click="openProxyViewModal(config)" title="查看详情"><svg viewBox="0 0 20 20" fill="currentColor"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/></svg></button>
                <button v-if="config.is_running" class="icon-btn" @click="restartProxy(config)" title="重启"><svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"/></svg></button>
                <button class="icon-btn" :class="{ disabled: config.is_running }" :disabled="config.is_running" @click="openProxyEditModal(config)" :title="config.is_running ? '运行中无法编辑，请先停止' : '编辑'"><svg viewBox="0 0 20 20" fill="currentColor"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"/></svg></button>
                <button class="icon-btn danger" :class="{ disabled: config.is_running }" :disabled="config.is_running" @click="deleteProxyConfig(config)" :title="config.is_running ? '运行中无法删除，请先停止' : '删除'"><svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/></svg></button>
              </div>
            </div>
            <div class="card-body">
              <p class="config-desc">{{ config.description || '暂无描述' }}</p>
              <div class="config-info">
                <div class="info-row"><span class="info-label">目标模型</span><span class="info-value model-tag">{{ config.target_model }}</span></div>
                <div class="info-row"><span class="info-label">Base URL</span><span class="info-value url-value" :title="config.target_base_url">{{ config.target_base_url }}</span></div>
              </div>
            </div>
            <div class="card-footer">
              <button v-if="!config.is_running" class="btn-start" @click="startProxy(config)">启动代理</button>
              <button v-else class="btn-stop" @click="stopProxy(config)">停止代理</button>
            </div>
            <!-- 悬浮时显示的应用按钮 -->
            <div class="card-hover-action" @click.stop="applyProxyToModel(config)">
              <span>应用到模型配置</span>
              <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>
            </div>
          </div>
        </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 代理配置弹框 -->
    <Teleport to="body">
        <div v-if="showProxyModal" class="modal-overlay" @click.self="showProxyModal = false">
          <div class="modal">
            <div class="modal-header">
              <h2>{{ isProxyEditing ? '编辑代理配置' : '新建代理配置' }}</h2>
              <button class="modal-close" @click="showProxyModal = false">&times;</button>
            </div>
            <div class="modal-body">
              <div class="compact-form">
                <div class="form-row">
                  <div class="form-field">
                    <label>配置名称 <span class="required">*</span></label>
                    <input v-model="proxyForm.name" type="text" placeholder="如：Qwen 代理" autocomplete="off" />
                  </div>
                  <div class="form-field">
                    <label>描述</label>
                    <input v-model="proxyForm.description" type="text" placeholder="配置用途说明" autocomplete="off" />
                  </div>
                </div>
                <div class="form-section">代理配置（对外 - 客户端使用）</div>
                <div class="form-row">
                  <div class="form-field">
                    <label>代理端口 <span class="required">*</span></label>
                    <input v-model.number="proxyForm.proxy_port" type="number" placeholder="4000" autocomplete="off" />
                  </div>
                  <div class="form-field flex-2">
                    <label>对外模型名</label>
                    <input v-model="proxyForm.proxy_model" type="text" placeholder="claude-sonnet-4-20250514" autocomplete="off" />
                  </div>
                </div>
                <div class="form-section">原始 API 配置（后端实际调用）</div>
                <div class="form-row">
                  <div class="form-field flex-2">
                    <label>原始 API 地址 <span class="required">*</span></label>
                    <input v-model="proxyForm.target_base_url" type="text" placeholder="https://dashscope.aliyuncs.com/apps/anthropic" autocomplete="off" />
                  </div>
                  <div class="form-field">
                    <label>原始模型 <span class="required">*</span></label>
                    <input v-model="proxyForm.target_model" type="text" placeholder="qwen-plus" autocomplete="off" />
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-field flex-2">
                    <label>API Key <span class="required">*</span></label>
                    <div class="input-with-toggle">
                      <input v-model="proxyForm.target_api_key" :type="showProxyApiKey ? 'text' : 'password'" placeholder="sk-..." autocomplete="new-password" />
                      <button type="button" class="toggle-btn" @click="showProxyApiKey = !showProxyApiKey">
                        <svg v-if="showProxyApiKey" viewBox="0 0 20 20" fill="currentColor"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/></svg>
                        <svg v-else viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z" clip-rule="evenodd"/><path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z"/></svg>
                      </button>
                    </div>
                  </div>
                  <div class="form-field">
                    <label>Max Tokens</label>
                    <input v-model.number="proxyForm.max_tokens" type="number" autocomplete="off" />
                  </div>
                  <div class="form-field">
                    <label>Temperature</label>
                    <input v-model.number="proxyForm.temperature" type="number" step="0.1" min="0" max="2" autocomplete="off" />
                  </div>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn-test" @click="testConnection" :disabled="isTesting">
                <svg v-if="isTesting" class="spin" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1z" clip-rule="evenodd"/></svg>
                <svg v-else viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clip-rule="evenodd"/></svg>
                {{ isTesting ? '测试中...' : '测试连接' }}
              </button>
              <div class="footer-spacer"></div>
              <button class="btn-secondary" @click="showProxyModal = false">取消</button>
              <button class="btn-primary" @click="saveProxyConfig">{{ isProxyEditing ? '保存' : '创建' }}</button>
            </div>
          </div>
        </div>
      </Teleport>

      <!-- 代理配置查看弹窗 -->
      <Teleport to="body">
        <div v-if="showProxyViewModal" class="modal-overlay" @click.self="showProxyViewModal = false">
          <div class="modal view-modal">
            <div class="modal-header">
              <h3>查看代理配置</h3>
              <button class="close-btn" @click="showProxyViewModal = false">
                <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>
              </button>
            </div>
            <div class="modal-body" v-if="viewingProxyConfig">
              <div class="view-sections">
                <!-- 基本信息 -->
                <div class="view-section">
                  <div class="view-section-title">基本信息</div>
                  <div class="view-grid">
                    <div class="view-item">
                      <span class="view-label">配置名称</span>
                      <span class="view-value">{{ viewingProxyConfig.name }}</span>
                    </div>
                    <div class="view-item">
                      <span class="view-label">描述</span>
                      <span class="view-value">{{ viewingProxyConfig.description || '-' }}</span>
                    </div>
                    <div class="view-item">
                      <span class="view-label">状态</span>
                      <span class="view-value">
                        <span :class="['status-tag', viewingProxyConfig.is_running ? 'running' : 'stopped']">
                          {{ viewingProxyConfig.is_running ? '运行中' : '已停止' }}
                        </span>
                      </span>
                    </div>
                  </div>
                </div>

                <!-- 代理配置（对外） -->
                <div class="view-section">
                  <div class="view-section-title">代理配置（对外 - 客户端使用）</div>
                  <div class="view-grid">
                    <div class="view-item">
                      <span class="view-label">代理端口</span>
                      <span class="view-value">{{ viewingProxyConfig.proxy_port }}</span>
                    </div>
                    <div class="view-item">
                      <span class="view-label">对外模型名</span>
                      <span class="view-value copy-value" @click="copyToClipboard(viewingProxyConfig.proxy_model, '代理模型名')" title="点击复制">
                        {{ viewingProxyConfig.proxy_model }}
                        <svg viewBox="0 0 20 20" fill="currentColor" class="copy-icon"><path d="M8 2a1 1 0 000 2h2a1 1 0 100-2H8z"/><path d="M3 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v6h-4.586l1.293-1.293a1 1 0 00-1.414-1.414l-3 3a1 1 0 000 1.414l3 3a1 1 0 001.414-1.414L10.414 13H15v3a2 2 0 01-2 2H5a2 2 0 01-2-2V5z"/></svg>
                      </span>
                    </div>
                    <div class="view-item full-width">
                      <span class="view-label">代理地址</span>
                      <span class="view-value copy-value" @click="copyToClipboard(`http://localhost:${viewingProxyConfig.proxy_port}`, '代理地址')" title="点击复制">
                        http://localhost:{{ viewingProxyConfig.proxy_port }}
                        <svg viewBox="0 0 20 20" fill="currentColor" class="copy-icon"><path d="M8 2a1 1 0 000 2h2a1 1 0 100-2H8z"/><path d="M3 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v6h-4.586l1.293-1.293a1 1 0 00-1.414-1.414l-3 3a1 1 0 000 1.414l3 3a1 1 0 001.414-1.414L10.414 13H15v3a2 2 0 01-2 2H5a2 2 0 01-2-2V5z"/></svg>
                      </span>
                    </div>
                  </div>
                </div>

                <!-- 原始 API 配置 -->
                <div class="view-section">
                  <div class="view-section-title">原始 API 配置（后端实际调用）</div>
                  <div class="view-grid">
                    <div class="view-item full-width">
                      <span class="view-label">原始 API 地址</span>
                      <span class="view-value copy-value" @click="copyToClipboard(viewingProxyConfig.target_base_url, 'API 地址')" title="点击复制">
                        {{ viewingProxyConfig.target_base_url }}
                        <svg viewBox="0 0 20 20" fill="currentColor" class="copy-icon"><path d="M8 2a1 1 0 000 2h2a1 1 0 100-2H8z"/><path d="M3 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v6h-4.586l1.293-1.293a1 1 0 00-1.414-1.414l-3 3a1 1 0 000 1.414l3 3a1 1 0 001.414-1.414L10.414 13H15v3a2 2 0 01-2 2H5a2 2 0 01-2-2V5z"/></svg>
                      </span>
                    </div>
                    <div class="view-item">
                      <span class="view-label">原始模型</span>
                      <span class="view-value">{{ viewingProxyConfig.target_model }}</span>
                    </div>
                    <div class="view-item">
                      <span class="view-label">API Key</span>
                      <span class="view-value masked">{{ viewingProxyConfig.target_api_key ? '••••••••••••' + viewingProxyConfig.target_api_key.slice(-4) : '-' }}</span>
                    </div>
                    <div class="view-item">
                      <span class="view-label">Max Tokens</span>
                      <span class="view-value">{{ viewingProxyConfig.max_tokens || '默认' }}</span>
                    </div>
                    <div class="view-item">
                      <span class="view-label">Temperature</span>
                      <span class="view-value">{{ viewingProxyConfig.temperature ?? '默认' }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn-primary" @click="showProxyViewModal = false">关闭</button>
            </div>
          </div>
        </div>
      </Teleport>

    <!-- Toast 提示 -->
    <Teleport to="body">
      <Transition name="toast">
        <div v-if="toast.show" class="toast" :class="toast.type">
          <svg v-if="toast.type === 'success'" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
          <svg v-else viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>
          <span>{{ toast.message }}</span>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.models-page {
  padding: 24px;
  max-width: 1400px;
  background: #f5f7fa;
  min-height: calc(100vh - 64px);
}

/* Tab 内容区域 */
.tab-content {
  animation: fadeIn 0.2s ease;
}

/* 内容卡片容器 */
.content-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

/* 卡片区域 */
.card-section {
  padding: 20px 24px;
}

.card-section + .card-section {
  border-top: 1px solid #e5e7eb;
}

/* 头部区域 */
.header-section {
  background: linear-gradient(135deg, #fafbfc 0%, #f5f7fa 100%);
  border-bottom: 1px solid #e5e7eb;
}

.section-title {
  margin: 0 0 4px;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

/* 统计区域 */
.stats-section {
  background: #fafbfc;
}

/* 列表区域 */
.list-section {
  padding-top: 16px;
}

.list-title {
  margin: 0 0 16px;
  font-size: 14px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  flex-wrap: wrap;
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.page-desc {
  color: #6b7280;
  font-size: 14px;
  margin: 0;
}

.active-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: #ecfdf5;
  color: #059669;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
}

.active-badge .dot {
  width: 6px;
  height: 6px;
  background: #10b981;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.search-box {
  position: relative;
}

.search-box .search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: #9ca3af;
}

.search-box input {
  padding: 8px 12px 8px 36px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 13px;
  width: 200px;
  transition: all 0.2s;
}

.search-box input:focus {
  outline: none;
  border-color: #1677ff;
  box-shadow: 0 0 0 3px rgba(22, 119, 255, 0.1);
}

/* 按钮 */
.btn-primary, .btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-primary {
  background: #1677ff;
  color: white;
}

.btn-primary:hover {
  background: #4096ff;
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.btn-secondary {
  background: white;
  color: #374151;
  border: 1px solid #e5e7eb;
}

.btn-secondary:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.btn-primary svg, .btn-secondary svg {
  width: 16px;
  height: 16px;
}

/* 统计卡片 */
.stats-row {
  display: flex;
  gap: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  min-width: 160px;
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon svg {
  width: 22px;
  height: 22px;
}

.stat-icon.blue {
  background: #eff6ff;
  color: #1677ff;
}

.stat-icon.green {
  background: #ecfdf5;
  color: #10b981;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
}

.stat-label {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}

/* 配置列表 */
.config-list {
  min-height: 200px;
}

.loading-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #9ca3af;
}

.loading-state .spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #1677ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state svg {
  width: 48px;
  height: 48px;
  margin-bottom: 12px;
}

.empty-state p {
  margin: 0 0 16px;
  font-size: 14px;
}

/* 配置网格 */
.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 20px;
}

.config-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  position: relative;
  transition: all 0.2s;
}

.config-card:hover {
  border-color: #d1d5db;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.config-card.active {
  border: 2px solid #1677ff;
  box-shadow: 0 0 0 3px rgba(22, 119, 255, 0.1);
}

.config-card.inactive {
  opacity: 0.75;
  background: #fafbfc;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px 16px 12px;
  border-bottom: 1px solid #f3f4f6;
}

.card-title {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.card-title h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.status-badge {
  display: inline-flex;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.status-badge.active {
  background: #ecfdf5;
  color: #059669;
}

.status-badge.inactive {
  background: #f3f4f6;
  color: #6b7280;
}

.card-actions {
  display: flex;
  gap: 4px;
}

.icon-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #9ca3af;
  cursor: pointer;
  transition: all 0.15s;
}

.icon-btn:hover {
  background: #f3f4f6;
  color: #1677ff;
}

.icon-btn.danger:hover {
  background: #fef2f2;
  color: #ef4444;
}

.icon-btn.disabled,
.icon-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  pointer-events: none;
}

.icon-btn svg {
  width: 16px;
  height: 16px;
}

.card-body {
  padding: 16px;
}

.config-desc {
  margin: 0 0 16px;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
}

.config-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  font-size: 12px;
  color: #9ca3af;
}

.info-value {
  font-size: 13px;
  color: #374151;
  font-weight: 500;
}

.info-value.model-tag {
  padding: 2px 8px;
  background: #eff6ff;
  color: #1677ff;
  border-radius: 4px;
  font-family: 'SF Mono', monospace;
  font-size: 11px;
}

.info-value.url-value {
  font-size: 11px;
  color: #6b7280;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.info-value.api-type-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.info-value.api-type-tag.anthropic {
  background: #fef3c7;
  color: #d97706;
}

.info-value.api-type-tag.openai {
  background: #ecfdf5;
  color: #059669;
}

.info-value.api-type-tag.litellm {
  background: #ede9fe;
  color: #7c3aed;
}

.form-hint {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 4px;
  line-height: 1.5;
}

/* API 类型选择卡片 */
.api-type-cards {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.api-type-card {
  flex: 1;
  min-width: 150px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.api-type-card:hover {
  border-color: #d1d5db;
  background: #f9fafb;
}

.api-type-card.active {
  border-color: #1677ff;
  background: #eff6ff;
}

.api-type-card .card-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 18px;
  flex-shrink: 0;
}

.api-type-card .card-icon.anthropic {
  background: #fef3c7;
  color: #d97706;
}

.api-type-card .card-icon.openai {
  background: #ecfdf5;
  color: #059669;
}

.api-type-card .card-icon.litellm {
  background: #ede9fe;
  color: #7c3aed;
}

.api-type-card .card-info {
  flex: 1;
  min-width: 0;
}

.api-type-label {
  font-weight: 600;
  font-size: 14px;
  color: #1f2937;
}

.api-type-desc {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.api-type-card .card-label {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 2px;
}

.api-type-card .card-desc {
  font-size: 11px;
  color: #6b7280;
  line-height: 1.3;
}

/* 表单分组标题 */
.form-section {
  margin-top: 8px;
  padding-top: 16px;
  border-top: 1px solid #f3f4f6;
}

.form-section .section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.form-section .section-desc {
  font-size: 12px;
  color: #6b7280;
}

.card-footer {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  background: #f9fafb;
  border-top: 1px solid #f3f4f6;
}

.btn-test, .btn-toggle {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  border: none;
}

.btn-test {
  background: white;
  color: #374151;
  border: 1px solid #e5e7eb;
}

.btn-test:hover:not(:disabled) {
  background: #f9fafb;
  border-color: #1677ff;
  color: #1677ff;
}

.btn-test:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-test svg {
  width: 14px;
  height: 14px;
}

.btn-test svg.spinning {
  animation: spin 1s linear infinite;
}

.btn-toggle {
  background: #f3f4f6;
  color: #374151;
}

.btn-toggle:hover {
  background: #e5e7eb;
}

.btn-toggle.active {
  background: #fef2f2;
  color: #ef4444;
}

.btn-toggle.active:hover {
  background: #fee2e2;
}

/* 测试结果 */
.test-result {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 500;
}

.test-result.success {
  background: #ecfdf5;
  color: #059669;
}

.test-result.error {
  background: #fef2f2;
  color: #ef4444;
}

.test-result svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.test-result .latency {
  margin-left: auto;
  opacity: 0.7;
}

/* 弹框 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 800px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.modal-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 8px;
  font-size: 24px;
  color: #9ca3af;
  cursor: pointer;
  transition: all 0.15s;
}

.modal-close:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.modal-body {
  padding: 12px 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 8px 20px;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

.footer-spacer {
  flex: 1;
}

.btn-test {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-test:hover:not(:disabled) {
  border-color: #1677ff;
  color: #1677ff;
}

.btn-test:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-test svg {
  width: 16px;
  height: 16px;
}

.btn-test svg.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 表单 */
/* 紧凑表单布局 */
.compact-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-row {
  display: flex;
  gap: 12px;
}

.form-field {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-field.flex-2 {
  flex: 2;
}

.form-field label {
  font-size: 12px;
  font-weight: 500;
  color: #374151;
}

.form-field label .required {
  color: #ef4444;
}

.form-field input {
  padding: 8px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
}

.form-field input:focus {
  outline: none;
  border-color: #1677ff;
  box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.1);
}

.form-section {
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 8px 0 4px;
  border-top: 1px solid #f3f4f6;
  margin-top: 4px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.form-group.full {
  grid-column: 1 / -1;
}

.form-group.section-header {
  margin-top: 6px;
  margin-bottom: -6px;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.form-group label .required {
  color: #ef4444;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 6px 8px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  transition: all 0.15s;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #1677ff;
  box-shadow: 0 0 0 3px rgba(22, 119, 255, 0.1);
}

.form-group textarea {
  resize: vertical;
  min-height: 50px;
  font-family: inherit;
}

.file-input {
  padding: 8px !important;
  background: #f9fafb;
}

/* 响应式 */
@media (max-width: 768px) {
  .models-page {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions {
    justify-content: flex-start;
  }

  .stats-row {
    flex-direction: column;
  }

  .config-grid {
    grid-template-columns: 1fr;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .form-group.full {
    grid-column: 1;
  }
}

/* 弹框内测试按钮 */
.btn-test-modal {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #10b981;
  background: white;
  color: #10b981;
}

.btn-test-modal:hover:not(:disabled) {
  background: #ecfdf5;
}

.btn-test-modal:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-test-modal svg {
  width: 14px;
  height: 14px;
}

.btn-test-modal svg.spinning {
  animation: spin 1s linear infinite;
}

/* 弹框内测试结果 */
.test-direct-result {
  margin-top: 12px;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.test-direct-result.success {
  background: #ecfdf5;
  color: #059669;
}

.test-direct-result.error {
  background: #fef2f2;
  color: #ef4444;
}

.test-direct-result .latency {
  margin-left: auto;
  opacity: 0.7;
}

/* API Key 输入框带切换按钮 */
.input-with-toggle {
  position: relative;
  display: flex;
  align-items: center;
}

.input-with-toggle input {
  flex: 1;
  padding-right: 40px;
}

.input-with-toggle .toggle-btn {
  position: absolute;
  right: 8px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: #9ca3af;
  cursor: pointer;
  transition: all 0.15s;
}

.input-with-toggle .toggle-btn:hover {
  background: #f3f4f6;
  color: #1677ff;
}

.input-with-toggle .toggle-btn svg {
  width: 18px;
  height: 18px;
}

/* ========== Tab 切换样式 ========== */
.tabs-header {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  background: white;
  padding: 4px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  border: 1px solid #e5e7eb;
  width: fit-content;
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  background: transparent;
  color: #6b7280;
  position: relative;
}

.tab-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

.tab-btn.active {
  background: #1677ff;
  color: white;
  box-shadow: 0 2px 4px rgba(22, 119, 255, 0.3);
}

.tab-btn svg {
  width: 18px;
  height: 18px;
}

.tab-btn .status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10b981;
  animation: pulse 2s infinite;
}

.tab-btn .status-dot.running {
  background: #10b981;
}

/* ========== 代理 Tab 样式 ========== */
/* 代理状态行内显示 */
.proxy-status-inline {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 8px 16px;
  background: #f3f4f6;
  border-radius: 8px;
  font-size: 13px;
}

.proxy-status-inline.running {
  background: #ecfdf5;
}

.proxy-status-inline .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #9ca3af;
}

.proxy-status-inline .dot.running {
  background: #10b981;
  animation: pulse 2s infinite;
}

.proxy-status-inline .dot.stopped {
  background: #9ca3af;
}

.proxy-status-inline .status-text {
  font-weight: 500;
  color: #374151;
}

.proxy-status-inline .divider {
  color: #d1d5db;
}

.proxy-status-inline .status-detail {
  color: #6b7280;
}

.proxy-status-inline .status-detail.clickable {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  color: #1677ff;
}

.proxy-status-inline .status-detail.clickable:hover {
  text-decoration: underline;
}

.proxy-status-inline .status-detail svg {
  width: 14px;
  height: 14px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.proxy-status-card {
  background: white;
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  border-left: 4px solid #e5e7eb;
}

.proxy-status-card.running {
  border-left-color: #10b981;
  background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
}

.status-content {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-indicator .dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-indicator .dot.running {
  background: #10b981;
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.2);
  animation: pulse 2s infinite;
}

.status-indicator .dot.stopped {
  background: #9ca3af;
}

.status-indicator .status-label {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.status-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 6px;
}

.status-info .info-label {
  font-size: 12px;
  color: #6b7280;
}

.status-info .info-value {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.status-info .info-value.proxy-url {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  color: #1677ff;
}

.status-info.clickable {
  cursor: pointer;
  transition: all 0.2s;
}

.status-info.clickable:hover {
  background: rgba(22, 119, 255, 0.1);
}

.status-info.clickable svg {
  width: 14px;
  height: 14px;
  color: #9ca3af;
}

/* 代理工具栏 */
.proxy-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.proxy-toolbar .list-title {
  margin: 0;
}

.toolbar-actions {
  display: flex;
  gap: 12px;
}

/* 代理列表 */
.proxy-list {
  min-height: 200px;
}

.proxy-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 20px;
}

.proxy-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  position: relative;
  transition: all 0.2s;
}

.proxy-card:hover {
  border-color: #d1d5db;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.proxy-card.active {
  border: 2px solid #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}

.proxy-card .status-badge.running {
  background: #ecfdf5;
  color: #059669;
}

.proxy-card .status-badge.stopped {
  background: #f3f4f6;
  color: #6b7280;
}

/* 启动/停止按钮 */
.btn-start, .btn-stop {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  border: none;
}

.btn-start {
  background: #10b981;
  color: white;
}

.btn-start:hover {
  background: #059669;
}

.btn-stop {
  background: #fee2e2;
  color: #ef4444;
  border: 1px solid #fecaca;
}

.btn-stop:hover {
  background: #fecaca;
}

/* 卡片悬浮时显示的应用按钮 */
.card-hover-action {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) scale(0.9);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.95);
  color: #3b82f6;
  font-size: 14px;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  z-index: 10;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border: 1px solid #e5e7eb;
}

.card-hover-action svg {
  width: 18px;
  height: 18px;
}

.card-hover-action:hover {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.proxy-card:hover .card-hover-action {
  opacity: 1;
  visibility: visible;
  transform: translate(-50%, -50%) scale(1);
}

.proxy-card:hover::before {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.03);
  z-index: 5;
  pointer-events: none;
}

/* 表单提示 */
.form-group label .hint {
  font-size: 11px;
  color: #9ca3af;
  font-weight: 400;
  margin-left: 4px;
}

/* ========== Toast 提示 ========== */
.toast {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 24px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 10000;
}

.toast svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.toast.success {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  color: #059669;
  border: 1px solid #a7f3d0;
}

.toast.error {
  background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%);
  color: #dc2626;
  border: 1px solid #fca5a5;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(-30px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}

/* 状态栏样式 */
.status-info.editing {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
}

.url-action-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: #9ca3af;
  cursor: pointer;
  transition: all 0.15s;
  flex-shrink: 0;
}

.url-action-btn:hover {
  background: rgba(22, 119, 255, 0.1);
  color: #1677ff;
}

.url-action-btn.confirm {
  color: #10b981;
}

.url-action-btn.confirm:hover {
  background: rgba(16, 185, 129, 0.1);
}

.url-action-btn svg {
  width: 14px;
  height: 14px;
}

.url-input {
  padding: 4px 8px;
  border: 1px solid #1677ff;
  border-radius: 4px;
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  color: #1677ff;
  background: white;
  min-width: 280px;
}

.url-input:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.2);
}

/* 查看弹窗样式 */
.view-modal {
  max-width: 600px;
}

.view-sections {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.view-section {
  background: #fafbfc;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e5e7eb;
}

.view-section-title {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.view-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.view-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.view-item.full-width {
  grid-column: 1 / -1;
}

.view-label {
  font-size: 11px;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.view-value {
  font-size: 14px;
  color: #1f2937;
  word-break: break-all;
}

.view-value.masked {
  font-family: 'SF Mono', monospace;
  color: #9ca3af;
}

.view-value.copy-value {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: #f3f4f6;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
  font-family: 'SF Mono', monospace;
  font-size: 13px;
}

.view-value.copy-value:hover {
  background: #e5e7eb;
  color: #1677ff;
}

.view-value .copy-icon {
  width: 14px;
  height: 14px;
  opacity: 0.5;
  flex-shrink: 0;
}

.view-value.copy-value:hover .copy-icon {
  opacity: 1;
}

.view-value .status-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.view-value .status-tag.running {
  background: #ecfdf5;
  color: #059669;
}

.view-value .status-tag.stopped {
  background: #f3f4f6;
  color: #6b7280;
}
</style>
