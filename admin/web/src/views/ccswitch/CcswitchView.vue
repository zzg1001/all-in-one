<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ccswitchApi, type CCConfig } from '@/api'
import config from '@/config'

// 路由 - 返回首页功能
const route = useRoute()
const showBackHome = computed(() => route.query.from === 'home')
const homeUrl = config.homeUrl

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

// 模型选项
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
  inactive: configs.value.filter(c => !c.is_active).length,
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
  if (config) {
    editingConfig.value = { ...config }
  } else {
    editingConfig.value = {
      name: '',
      description: '',
      model_id: 'claude-opus-4-5',
      api_key: '',
      base_url: '',
      max_tokens: 4096,
      temperature: 0.7,
      top_p: 1.0,
      system_prompt: '',
    }
  }
  showEditModal.value = true
}

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
    downloadJson(config, `ccswitch-${id}.json`)
  } catch (e) {
    alert('导出失败')
  }
}

const exportAll = async () => {
  try {
    const data = await ccswitchApi.exportAll()
    downloadJson(data, 'ccswitch-all.json')
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

// 初始化默认配置
const initDefaultConfig = async () => {
  try {
    await ccswitchApi.create({
      name: 'Claude Opus 4.5 (Azure)',
      description: '默认配置 - Azure 代理的 Claude Opus 4.5 模型',
      model_id: 'claude-opus-4-5',
      api_key: '',  // API Key 应通过后端环境变量配置
      base_url: 'https://yunqinghu-3344-resource.services.ai.azure.com/anthropic/',
      max_tokens: 4096,
      temperature: 0.7,
      top_p: 1.0,
    })
    // 重新加载配置
    await loadConfigs()
    // 激活第一个配置
    if (configs.value.length > 0 && !activeConfig.value) {
      const firstConfig = configs.value[0]
      await ccswitchApi.toggle(firstConfig.id)
      await loadConfigs()
    }
  } catch (e) {
    console.error('初始化配置失败:', e)
    alert('初始化配置失败')
  }
}

onMounted(loadConfigs)
</script>

<template>
  <div class="h-screen bg-[#f7f9fb] text-[#2a3439] font-sans flex flex-col overflow-hidden">
    <!-- 紧凑头部 - 固定 -->
    <div class="bg-gradient-to-r from-[#1e3a5f] to-[#27609d] text-white flex-shrink-0">
      <div class="px-8 py-4 flex items-center justify-between">
        <!-- 左侧：返回 + 标题 -->
        <div class="flex items-center gap-4">
          <a v-if="showBackHome" :href="homeUrl" class="back-home-link" title="返回首页">
            <span class="cmd">$</span> cd ~/home
          </a>
          <div>
            <h1 class="text-xl font-bold">Ike Switch</h1>
            <p class="text-white/60 text-xs">Claude 模型配置管理</p>
          </div>
        </div>

        <!-- 右侧：当前配置状态 -->
        <div class="flex items-center gap-6">
          <div v-if="activeConfig" class="flex items-center gap-4">
            <div class="flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded-lg">
              <span class="w-2 h-2 bg-green-400 rounded-full"></span>
              <span class="text-sm font-medium">{{ activeConfig.name }}</span>
            </div>
            <span class="text-white/50 text-xs">{{ activeConfig.model_id }}</span>
            <span class="text-white/40 text-xs">T:{{ activeConfig.temperature }} | {{ activeConfig.max_tokens }}tk</span>
            <button @click="openEdit(activeConfig)" class="text-white/70 hover:text-white text-xs underline">编辑</button>
          </div>
          <div v-else class="flex items-center gap-3">
            <span class="text-white/50 text-sm">未激活配置</span>
            <button
              @click="initDefaultConfig"
              class="px-3 py-1.5 bg-white/20 hover:bg-white/30 rounded text-xs font-medium transition-colors"
            >
              + 初始化
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Compact Controls - 固定 -->
      <div class="flex items-center justify-between px-6 py-2 bg-[#eef2f5] flex-shrink-0">
        <!-- 左侧：全部配置 -->
        <button class="px-5 py-2 bg-white text-[#27609d] font-semibold rounded-lg shadow-sm text-sm">
          全部配置
        </button>
        <!-- 右侧：搜索 + 操作 -->
        <div class="flex items-center gap-3">
          <div class="relative">
            <span class="absolute left-3 top-1/2 -translate-y-1/2 text-[#8899a8]">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
              </svg>
            </span>
            <input
              v-model="searchQuery"
              class="bg-[#c8d5de] border-none pl-9 pr-4 py-2 text-sm w-56 rounded-lg focus:ring-2 focus:ring-[#27609d] focus:outline-none placeholder-[#6b7c8a]"
              placeholder="搜索配置..."
              type="text"
            />
          </div>
          <button @click="exportAll" class="px-3 py-2 text-[#4a5568] hover:bg-[#dde4ea] rounded-lg text-sm flex items-center gap-1.5 transition-colors">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
            </svg>
            导出全部
          </button>
          <button @click="openImport" class="px-3 py-2 text-[#4a5568] hover:bg-[#dde4ea] rounded-lg text-sm flex items-center gap-1.5 transition-colors">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
            </svg>
            导入
          </button>
          <button @click="openEdit()" class="bg-[#27609d] text-white px-4 py-2 rounded-lg text-sm flex items-center gap-1.5 font-medium hover:bg-[#1e4f7a] transition-all">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            新建配置
          </button>
        </div>
      </div>

      <!-- Table - 可滚动区域 -->
      <div class="flex-1 overflow-auto px-8 py-4">
        <div class="bg-white rounded-lg overflow-hidden shadow-sm">
          <table class="w-full text-left border-collapse">
            <thead class="bg-[#e1e9ee] text-[#566166] sticky top-0">
              <tr>
                <th class="px-6 py-3 font-semibold text-xs uppercase tracking-widest">配置名称</th>
                <th class="px-6 py-3 font-semibold text-xs uppercase tracking-widest">模型</th>
                <th class="px-6 py-3 font-semibold text-xs uppercase tracking-widest">描述</th>
                <th class="px-6 py-3 font-semibold text-xs uppercase tracking-widest">参数</th>
                <th class="px-6 py-3 font-semibold text-xs uppercase tracking-widest">状态</th>
                <th class="px-6 py-3 font-semibold text-xs uppercase tracking-widest text-right">操作</th>
              </tr>
            </thead>
            <tbody class="text-sm">
              <tr v-if="loading">
                <td colspan="6" class="px-6 py-12 text-center text-[#566166]">加载中...</td>
              </tr>
              <tr v-else-if="filteredConfigs.length === 0">
                <td colspan="6" class="px-6 py-12 text-center text-[#566166]">暂无配置</td>
              </tr>
              <tr
                v-for="config in filteredConfigs"
                :key="config.id"
                class="hover:bg-[#f0f4f7] transition-colors group border-b border-[#e1e9ee] last:border-b-0"
                :class="{ 'opacity-60': !config.is_active }"
              >
                <td class="px-6 py-5">
                  <div class="font-semibold text-[#2a3439]" :class="{ 'line-through': !config.is_active }">
                    {{ config.name }}
                  </div>
                  <div class="text-xs text-[#717c82] font-mono mt-1">ID: {{ config.id }}</div>
                </td>
                <td class="px-6 py-5">
                  <span class="font-mono text-[#27609d] font-semibold bg-[#d3e4ff] px-2 py-1 rounded text-xs">
                    {{ config.model_id }}
                  </span>
                </td>
                <td class="px-6 py-5 text-[#566166] max-w-xs truncate">
                  {{ config.description || '-' }}
                </td>
                <td class="px-6 py-5 text-[#566166] text-xs">
                  <div>Tokens: {{ config.max_tokens }}</div>
                  <div>Temp: {{ config.temperature }}</div>
                </td>
                <td class="px-6 py-5">
                  <span v-if="config.is_active" class="bg-[#d5e3fc] text-[#324053] px-3 py-1 rounded-full text-xs font-medium">
                    Active
                  </span>
                  <span v-else class="bg-[#e1e9ee] text-[#566166] px-3 py-1 rounded-full text-xs font-medium uppercase tracking-tight">
                    Disabled
                  </span>
                  <!-- Test Result -->
                  <div v-if="testingId === config.id && testResult" class="mt-2">
                    <span
                      class="text-xs px-2 py-1 rounded"
                      :class="testResult.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
                    >
                      {{ testResult.message }}
                      <span v-if="testResult.latency_ms">({{ testResult.latency_ms }}ms)</span>
                    </span>
                  </div>
                </td>
                <td class="px-6 py-5 text-right">
                  <div class="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      @click="testConfig(config.id)"
                      :disabled="testingId === config.id"
                      class="p-2 hover:bg-[#e1e9ee] rounded-full text-[#717c82] hover:text-[#27609d] transition-colors"
                      title="测试连接"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                      </svg>
                    </button>
                    <button
                      @click="openEdit(config)"
                      class="p-2 hover:bg-[#e1e9ee] rounded-full text-[#717c82] hover:text-[#27609d] transition-colors"
                      title="编辑"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                      </svg>
                    </button>
                    <button
                      @click="toggleConfig(config.id)"
                      class="p-2 hover:bg-[#e1e9ee] rounded-full text-[#717c82] hover:text-[#27609d] transition-colors"
                      :title="config.is_active ? '禁用' : '启用'"
                    >
                      <svg v-if="config.is_active" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"/>
                      </svg>
                      <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                    </button>
                    <button
                      @click="copyConfig(config.id)"
                      class="p-2 hover:bg-[#e1e9ee] rounded-full text-[#717c82] hover:text-[#27609d] transition-colors"
                      title="复制"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                      </svg>
                    </button>
                    <button
                      @click="exportConfig(config.id)"
                      class="p-2 hover:bg-[#e1e9ee] rounded-full text-[#717c82] hover:text-[#27609d] transition-colors"
                      title="导出"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
                      </svg>
                    </button>
                    <button
                      @click="deleteConfig(config.id)"
                      class="p-2 hover:bg-[#e1e9ee] rounded-full text-[#717c82] hover:text-[#9f403d] transition-colors"
                      title="删除"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Footer -->
          <div class="flex items-center justify-between px-4 py-2 bg-[#f7f9fb] border-t border-[#e1e9ee] text-xs text-[#566166]">
            <span>共 <b class="text-[#2a3439]">{{ stats.total }}</b> 个配置，<b class="text-[#27609d]">{{ stats.active }}</b> 个启用</span>
          </div>
        </div>

        <!-- Info Panel -->
        <div class="mt-6 grid grid-cols-12 gap-6 pb-6">
          <div class="col-span-12 lg:col-span-8">
            <div class="bg-[#d3e4ff]/20 rounded-lg p-5 border-l-4 border-[#27609d]">
              <div class="flex items-start gap-3">
                <svg class="w-5 h-5 text-[#27609d] flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <div>
                  <h3 class="font-semibold text-[#27609d] mb-1 text-sm">配置同步说明</h3>
                  <p class="text-[#135390] text-xs leading-relaxed">
                    Portal 系统会自动使用当前启用的配置。同一时间只能有一个配置处于启用状态。
                    修改配置后会即时生效，无需重启服务。建议在启用前先进行连接测试。
                  </p>
                </div>
              </div>
            </div>
          </div>
          <div class="col-span-12 lg:col-span-4">
            <div class="bg-[#f0f4f7] rounded-lg p-4 h-full">
              <h3 class="font-semibold text-[#2a3439] mb-2 text-sm">快速统计</h3>
              <div class="space-y-2">
                <div class="flex justify-between items-center py-1.5 border-b border-[#e1e9ee]">
                  <span class="text-xs text-[#566166]">总配置数</span>
                  <span class="font-bold text-sm">{{ stats.total }}</span>
                </div>
                <div class="flex justify-between items-center py-1.5 border-b border-[#e1e9ee]">
                  <span class="text-xs text-[#566166]">已启用</span>
                  <span class="font-bold text-sm text-[#27609d]">{{ stats.active }}</span>
                </div>
                <div class="flex justify-between items-center py-1.5">
                  <span class="text-xs text-[#566166]">未启用</span>
                  <span class="font-bold text-sm">{{ stats.inactive }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Modal -->
    <div v-if="showEditModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showEditModal = false">
      <div class="bg-white rounded-xl w-full max-w-2xl max-h-[90vh] overflow-hidden shadow-2xl">
        <div class="flex justify-between items-center px-6 py-4 border-b border-[#e1e9ee]">
          <h2 class="text-lg font-semibold text-[#2a3439]">{{ editingConfig?.id ? '编辑配置' : '新建配置' }}</h2>
          <button @click="showEditModal = false" class="text-[#717c82] hover:text-[#2a3439] text-2xl">&times;</button>
        </div>
        <div class="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          <div class="grid grid-cols-2 gap-4">
            <div class="col-span-2">
              <label class="block text-sm font-medium text-[#566166] mb-1">配置名称 *</label>
              <input v-model="editingConfig!.name" class="w-full px-4 py-2 border border-[#a9b4b9] rounded-lg focus:ring-2 focus:ring-[#27609d] focus:border-transparent" placeholder="例如：生产环境配置" />
            </div>
            <div class="col-span-2">
              <label class="block text-sm font-medium text-[#566166] mb-1">描述</label>
              <input v-model="editingConfig!.description" class="w-full px-4 py-2 border border-[#a9b4b9] rounded-lg focus:ring-2 focus:ring-[#27609d] focus:border-transparent" placeholder="配置用途说明" />
            </div>
            <div>
              <label class="block text-sm font-medium text-[#566166] mb-1">模型 *</label>
              <select v-model="editingConfig!.model_id" class="w-full px-4 py-2 border border-[#a9b4b9] rounded-lg focus:ring-2 focus:ring-[#27609d] focus:border-transparent">
                <option v-for="opt in modelOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-[#566166] mb-1">Base URL</label>
              <input v-model="editingConfig!.base_url" class="w-full px-4 py-2 border border-[#a9b4b9] rounded-lg focus:ring-2 focus:ring-[#27609d] focus:border-transparent" placeholder="留空使用默认" />
            </div>
            <div class="col-span-2">
              <label class="block text-sm font-medium text-[#566166] mb-1">API Key *</label>
              <input v-model="editingConfig!.api_key" type="password" class="w-full px-4 py-2 border border-[#a9b4b9] rounded-lg focus:ring-2 focus:ring-[#27609d] focus:border-transparent font-mono" placeholder="sk-ant-..." />
            </div>
            <div>
              <label class="block text-sm font-medium text-[#566166] mb-1">Max Tokens</label>
              <input v-model.number="editingConfig!.max_tokens" type="number" class="w-full px-4 py-2 border border-[#a9b4b9] rounded-lg focus:ring-2 focus:ring-[#27609d] focus:border-transparent" />
            </div>
            <div>
              <label class="block text-sm font-medium text-[#566166] mb-1">Temperature</label>
              <input v-model.number="editingConfig!.temperature" type="number" step="0.1" min="0" max="2" class="w-full px-4 py-2 border border-[#a9b4b9] rounded-lg focus:ring-2 focus:ring-[#27609d] focus:border-transparent" />
            </div>
            <div class="col-span-2">
              <label class="block text-sm font-medium text-[#566166] mb-1">System Prompt</label>
              <textarea v-model="editingConfig!.system_prompt" rows="3" class="w-full px-4 py-2 border border-[#a9b4b9] rounded-lg focus:ring-2 focus:ring-[#27609d] focus:border-transparent" placeholder="系统提示词（可选）"></textarea>
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-3 px-6 py-4 border-t border-[#e1e9ee] bg-[#f7f9fb]">
          <button @click="showEditModal = false" class="px-6 py-2 text-[#566166] hover:bg-[#e1e9ee] rounded-lg transition-colors">取消</button>
          <button @click="saveConfig" class="px-6 py-2 bg-[#27609d] text-white rounded-lg hover:bg-[#145490] transition-colors">保存</button>
        </div>
      </div>
    </div>

    <!-- Import Modal -->
    <div v-if="showImportModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showImportModal = false">
      <div class="bg-white rounded-xl w-full max-w-xl max-h-[90vh] overflow-hidden shadow-2xl">
        <div class="flex justify-between items-center px-6 py-4 border-b border-[#e1e9ee]">
          <h2 class="text-lg font-semibold text-[#2a3439]">导入配置</h2>
          <button @click="showImportModal = false" class="text-[#717c82] hover:text-[#2a3439] text-2xl">&times;</button>
        </div>
        <div class="p-6">
          <div class="mb-4">
            <label class="block text-sm font-medium text-[#566166] mb-2">选择文件</label>
            <input type="file" accept=".json" @change="handleFileImport" class="w-full text-sm text-[#566166] file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-[#27609d] file:text-white hover:file:bg-[#145490]" />
          </div>
          <div>
            <label class="block text-sm font-medium text-[#566166] mb-2">或粘贴 JSON</label>
            <textarea v-model="importJson" rows="10" class="w-full px-4 py-2 border border-[#a9b4b9] rounded-lg focus:ring-2 focus:ring-[#27609d] focus:border-transparent font-mono text-sm" placeholder='{"name": "配置名", "model_id": "claude-opus-4-5", ...}'></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-3 px-6 py-4 border-t border-[#e1e9ee] bg-[#f7f9fb]">
          <button @click="showImportModal = false" class="px-6 py-2 text-[#566166] hover:bg-[#e1e9ee] rounded-lg transition-colors">取消</button>
          <button @click="doImport" :disabled="!importJson" class="px-6 py-2 bg-[#27609d] text-white rounded-lg hover:bg-[#145490] transition-colors disabled:opacity-50 disabled:cursor-not-allowed">导入</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.back-home-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #1a1a2e;
  border: 1px solid #2d2d44;
  border-radius: 6px;
  font-family: 'JetBrains Mono', 'Consolas', monospace;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.85);
  text-decoration: none;
  transition: all 0.15s;
}

.back-home-link:hover {
  background: #252540;
  border-color: #3d3d5c;
  color: white;
}

.back-home-link .cmd {
  color: rgba(255, 255, 255, 0.5);
}
</style>
