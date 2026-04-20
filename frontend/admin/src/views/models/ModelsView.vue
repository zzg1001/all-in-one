<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ccswitchApi, type CCConfig } from '@/api'

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

onMounted(loadConfigs)
</script>

<template>
  <div class="models-page">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <div class="header-info">
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

    <!-- 配置列表 -->
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
                <span class="info-label">模型</span>
                <span class="info-value model-tag">{{ config.model_id }}</span>
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
              <div class="form-group full">
                <label>配置名称 <span class="required">*</span></label>
                <input v-model="editingConfig!.name" type="text" placeholder="例如：生产环境配置" />
              </div>
              <div class="form-group full">
                <label>描述</label>
                <input v-model="editingConfig!.description" type="text" placeholder="配置用途说明" />
              </div>
              <div class="form-group">
                <label>模型 <span class="required">*</span></label>
                <select v-model="editingConfig!.model_id">
                  <option v-for="opt in modelOptions" :key="opt.value" :value="opt.value">
                    {{ opt.label }}
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label>Base URL</label>
                <input v-model="editingConfig!.base_url" type="text" placeholder="留空使用默认" />
              </div>
              <div class="form-group full">
                <label>API Key <span class="required">*</span></label>
                <input v-model="editingConfig!.api_key" type="password" placeholder="sk-ant-..." />
              </div>
              <div class="form-group">
                <label>Max Tokens</label>
                <input v-model.number="editingConfig!.max_tokens" type="number" />
              </div>
              <div class="form-group">
                <label>Temperature</label>
                <input v-model.number="editingConfig!.temperature" type="number" step="0.1" min="0" max="2" />
              </div>
              <div class="form-group full">
                <label>System Prompt</label>
                <textarea v-model="editingConfig!.system_prompt" rows="3" placeholder="系统提示词（可选）"></textarea>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="showEditModal = false">取消</button>
            <button class="btn-primary" @click="saveConfig">保存</button>
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
  </div>
</template>

<style scoped>
.models-page {
  padding: 24px;
  max-width: 1400px;
}

/* 头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
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
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
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
  min-height: 300px;
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
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  position: relative;
  transition: all 0.2s;
}

.config-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.config-card.active {
  border: 2px solid #1677ff;
}

.config-card.inactive {
  opacity: 0.7;
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
  border-radius: 16px;
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  margin: 0;
  font-size: 18px;
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
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

/* 表单 */
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group.full {
  grid-column: 1 / -1;
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
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
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
  min-height: 80px;
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
</style>
