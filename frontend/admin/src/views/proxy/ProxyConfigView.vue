<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface ProxyConfig {
  id: string
  name: string
  description: string
  proxy_type: string
  target_base_url: string
  target_api_key: string
  target_model: string
  proxy_port: number
  max_tokens: number
  temperature: number
  is_enabled: boolean
  is_running: boolean
  created_at: string
  updated_at: string
}

interface ProxyStatus {
  is_running: boolean
  target_model: string
  target_base_url: string
  proxy_url: string | null
  running_config_id: string | null
  running_config_name: string | null
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

// 状态
const configs = ref<ProxyConfig[]>([])
const status = ref<ProxyStatus | null>(null)
const loading = ref(false)
const showModal = ref(false)
const isEditing = ref(false)
const showApiKey = ref(false)

const form = ref({
  id: '',
  name: '',
  description: '',
  target_base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  target_api_key: '',
  target_model: 'qwen-plus',
  max_tokens: 4096,
  temperature: 0.7,
})

// 模型选项
const modelOptions = [
  { value: 'qwen-plus', label: 'Qwen Plus' },
  { value: 'qwen-turbo', label: 'Qwen Turbo' },
  { value: 'qwen-max', label: 'Qwen Max' },
  { value: 'qwen-long', label: 'Qwen Long' },
]

// API 请求
async function fetchConfigs() {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/proxy/configs`)
    if (res.ok) {
      configs.value = await res.json()
    }
  } catch (e) {
    console.error('获取配置失败:', e)
  } finally {
    loading.value = false
  }
}

async function fetchStatus() {
  try {
    const res = await fetch(`${API_BASE}/proxy/status`)
    if (res.ok) {
      status.value = await res.json()
    }
  } catch (e) {
    console.error('获取状态失败:', e)
  }
}

async function saveConfig() {
  try {
    const url = isEditing.value
      ? `${API_BASE}/proxy/configs/${form.value.id}`
      : `${API_BASE}/proxy/configs`
    const method = isEditing.value ? 'PUT' : 'POST'

    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value),
    })

    if (res.ok) {
      showModal.value = false
      fetchConfigs()
      fetchStatus()
    } else {
      const err = await res.json()
      alert(err.detail || '保存失败')
    }
  } catch (e) {
    alert('保存失败')
  }
}

async function deleteConfig(config: ProxyConfig) {
  if (!confirm(`确定删除配置 "${config.name}"？`)) return
  try {
    const res = await fetch(`${API_BASE}/proxy/configs/${config.id}`, {
      method: 'DELETE',
    })
    if (res.ok) {
      fetchConfigs()
      fetchStatus()
    }
  } catch (e) {
    alert('删除失败')
  }
}

async function startProxy(config: ProxyConfig) {
  try {
    const res = await fetch(`${API_BASE}/proxy/configs/${config.id}/start`, {
      method: 'POST',
    })
    const data = await res.json()
    if (res.ok) {
      alert(`代理已启动\n代理地址: ${data.proxy_url}`)
      fetchConfigs()
      fetchStatus()
    } else {
      alert(data.detail || '启动失败')
    }
  } catch (e) {
    alert('启动失败')
  }
}

async function stopProxy(config: ProxyConfig) {
  try {
    const res = await fetch(`${API_BASE}/proxy/configs/${config.id}/stop`, {
      method: 'POST',
    })
    if (res.ok) {
      fetchConfigs()
      fetchStatus()
    }
  } catch (e) {
    alert('停止失败')
  }
}

function openCreateModal() {
  isEditing.value = false
  showApiKey.value = false
  form.value = {
    id: '',
    name: '',
    description: '',
    target_base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    target_api_key: '',
    target_model: 'qwen-plus',
    max_tokens: 4096,
    temperature: 0.7,
  }
  showModal.value = true
}

function openEditModal(config: ProxyConfig) {
  isEditing.value = true
  showApiKey.value = false
  form.value = {
    id: config.id,
    name: config.name,
    description: config.description || '',
    target_base_url: config.target_base_url,
    target_api_key: '',
    target_model: config.target_model,
    max_tokens: config.max_tokens,
    temperature: config.temperature,
  }
  showModal.value = true
}

function copyProxyUrl() {
  if (status.value?.proxy_url) {
    navigator.clipboard.writeText(status.value.proxy_url)
    alert('已复制代理地址')
  }
}

onMounted(() => {
  fetchConfigs()
  fetchStatus()
})
</script>

<template>
  <div class="p-6">
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-2xl font-semibold text-gray-900">API 代理配置</h1>
      <p class="mt-1 text-sm text-gray-500">配置 Anthropic API 到其他模型（如通义千问）的代理转换</p>
    </div>

    <!-- 运行状态卡片 -->
    <div
      class="mb-6 p-4 rounded-lg border-l-4"
      :class="status?.is_running ? 'bg-green-50 border-green-500' : 'bg-gray-50 border-gray-300'"
    >
      <div class="flex items-center gap-6">
        <div class="flex items-center gap-2">
          <span
            class="w-3 h-3 rounded-full"
            :class="status?.is_running ? 'bg-green-500 animate-pulse' : 'bg-gray-400'"
          ></span>
          <span class="font-semibold" :class="status?.is_running ? 'text-green-700' : 'text-gray-600'">
            {{ status?.is_running ? '运行中' : '已停止' }}
          </span>
        </div>
        <template v-if="status?.is_running">
          <div class="text-sm">
            <span class="text-gray-500">配置:</span>
            <span class="ml-1 font-medium">{{ status.running_config_name }}</span>
          </div>
          <div class="text-sm">
            <span class="text-gray-500">模型:</span>
            <span class="ml-1 font-medium">{{ status.target_model }}</span>
          </div>
          <div class="text-sm flex items-center gap-1 cursor-pointer hover:text-blue-600" @click="copyProxyUrl">
            <span class="text-gray-500">代理地址:</span>
            <span class="ml-1 font-mono text-blue-600">{{ status.proxy_url }}</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </div>
        </template>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="mb-4 flex gap-3">
      <button
        @click="openCreateModal"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        新建配置
      </button>
      <button
        @click="fetchConfigs"
        class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        刷新
      </button>
    </div>

    <!-- 配置列表 -->
    <div class="bg-white rounded-lg border overflow-hidden">
      <table class="w-full">
        <thead class="bg-gray-50 border-b">
          <tr>
            <th class="px-4 py-3 text-left text-sm font-medium text-gray-600">名称</th>
            <th class="px-4 py-3 text-left text-sm font-medium text-gray-600">描述</th>
            <th class="px-4 py-3 text-left text-sm font-medium text-gray-600">目标模型</th>
            <th class="px-4 py-3 text-left text-sm font-medium text-gray-600">目标 URL</th>
            <th class="px-4 py-3 text-center text-sm font-medium text-gray-600">状态</th>
            <th class="px-4 py-3 text-center text-sm font-medium text-gray-600">操作</th>
          </tr>
        </thead>
        <tbody v-if="loading">
          <tr>
            <td colspan="6" class="px-4 py-8 text-center text-gray-500">加载中...</td>
          </tr>
        </tbody>
        <tbody v-else-if="configs.length === 0">
          <tr>
            <td colspan="6" class="px-4 py-8 text-center text-gray-500">暂无配置，点击"新建配置"创建</td>
          </tr>
        </tbody>
        <tbody v-else>
          <tr v-for="config in configs" :key="config.id" class="border-b last:border-b-0 hover:bg-gray-50">
            <td class="px-4 py-3 font-medium">{{ config.name }}</td>
            <td class="px-4 py-3 text-sm text-gray-600">{{ config.description || '-' }}</td>
            <td class="px-4 py-3">
              <span class="px-2 py-1 bg-purple-100 text-purple-700 text-sm rounded">{{ config.target_model }}</span>
            </td>
            <td class="px-4 py-3 text-xs text-gray-500 font-mono max-w-xs truncate">{{ config.target_base_url }}</td>
            <td class="px-4 py-3 text-center">
              <span
                class="px-2 py-1 text-xs rounded-full"
                :class="config.is_running ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'"
              >
                {{ config.is_running ? '运行中' : '已停止' }}
              </span>
            </td>
            <td class="px-4 py-3 text-center">
              <div class="flex items-center justify-center gap-2">
                <button
                  v-if="!config.is_running"
                  @click="startProxy(config)"
                  class="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                >
                  启动
                </button>
                <button
                  v-else
                  @click="stopProxy(config)"
                  class="px-3 py-1 bg-yellow-500 text-white text-sm rounded hover:bg-yellow-600"
                >
                  停止
                </button>
                <button
                  @click="openEditModal(config)"
                  class="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded hover:bg-gray-200"
                >
                  编辑
                </button>
                <button
                  @click="deleteConfig(config)"
                  class="px-3 py-1 bg-red-100 text-red-600 text-sm rounded hover:bg-red-200"
                >
                  删除
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 创建/编辑弹框 -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4">
        <div class="px-6 py-4 border-b flex items-center justify-between">
          <h3 class="text-lg font-semibold">{{ isEditing ? '编辑代理配置' : '新建代理配置' }}</h3>
          <button @click="showModal = false" class="text-gray-400 hover:text-gray-600">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="px-6 py-4 space-y-4 max-h-[70vh] overflow-y-auto">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">配置名称 <span class="text-red-500">*</span></label>
            <input
              v-model="form.name"
              type="text"
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="如：Qwen 代理"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
            <textarea
              v-model="form.description"
              rows="2"
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            ></textarea>
          </div>

          <div class="border-t pt-4">
            <h4 class="text-sm font-medium text-gray-500 mb-3">目标 API 配置</h4>

            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Base URL <span class="text-red-500">*</span></label>
                <input
                  v-model="form.target_base_url"
                  type="text"
                  class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                  placeholder="https://dashscope.aliyuncs.com/compatible-mode/v1"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  API Key
                  <span v-if="!isEditing" class="text-red-500">*</span>
                  <span v-else class="text-gray-400 text-xs ml-1">(留空表示不修改)</span>
                </label>
                <div class="relative">
                  <input
                    v-model="form.target_api_key"
                    :type="showApiKey ? 'text' : 'password'"
                    class="w-full px-3 py-2 pr-10 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="sk-..."
                  />
                  <button
                    type="button"
                    @click="showApiKey = !showApiKey"
                    class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    <svg v-if="showApiKey" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                    <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">模型 ID <span class="text-red-500">*</span></label>
                <select
                  v-model="form.target_model"
                  class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option v-for="opt in modelOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
              </div>
            </div>
          </div>

          <div class="border-t pt-4">
            <h4 class="text-sm font-medium text-gray-500 mb-3">参数配置</h4>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Max Tokens</label>
                <input
                  v-model.number="form.max_tokens"
                  type="number"
                  min="1"
                  max="32000"
                  class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Temperature</label>
                <input
                  v-model.number="form.temperature"
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </div>
        </div>

        <div class="px-6 py-4 border-t flex justify-end gap-3">
          <button
            @click="showModal = false"
            class="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            取消
          </button>
          <button
            @click="saveConfig"
            class="px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700"
          >
            {{ isEditing ? '保存' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
