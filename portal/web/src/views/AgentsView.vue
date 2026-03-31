<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { agentsApi } from '@/api'

const router = useRouter()

interface Agent {
  id: string
  name: string
  description: string
  icon: string
  category: string
  author: string
  version: string
  status: 'active' | 'draft' | 'deprecated'
  tools: string[]
  skills: string[]
  usage_count: number
  created_at: string
  updated_at: string
}

const searchQuery = ref('')
const selectedCategory = ref('all')
const categories = ['all', '企业服务', '市场营销', '管理决策', '自定义']

const agents = ref<Agent[]>([])
const isLoading = ref(false)
const showDeleteConfirm = ref(false)
const agentToDelete = ref<Agent | null>(null)
const isHeaderCollapsed = ref(false)

const toggleHeader = () => {
  isHeaderCollapsed.value = !isHeaderCollapsed.value
}

// 从 API 加载 Agent 列表
const loadAgents = async () => {
  isLoading.value = true
  try {
    const params: Record<string, string> = {}
    if (searchQuery.value) params.search = searchQuery.value
    if (selectedCategory.value !== 'all') params.category = selectedCategory.value

    const response = await agentsApi.getAll(params)
    agents.value = response.agents
  } catch (error) {
    console.error('Failed to load agents:', error)
  } finally {
    isLoading.value = false
  }
}

// 删除 Agent
const confirmDelete = (agent: Agent) => {
  agentToDelete.value = agent
  showDeleteConfirm.value = true
}

const deleteAgent = async () => {
  if (!agentToDelete.value) return
  try {
    await agentsApi.delete(agentToDelete.value.id)
    agents.value = agents.value.filter(a => a.id !== agentToDelete.value?.id)
    showDeleteConfirm.value = false
    agentToDelete.value = null
  } catch (error) {
    console.error('Failed to delete agent:', error)
  }
}

const cancelDelete = () => {
  showDeleteConfirm.value = false
  agentToDelete.value = null
}

onMounted(() => {
  loadAgents()
})

// 监听搜索和分类变化，重新加载数据
watch([searchQuery, selectedCategory], () => {
  loadAgents()
}, { debounce: 300 } as any)

// 前端筛选（API 已经做了筛选，这里是本地补充筛选）
const filteredAgents = computed(() => {
  return agents.value
})

const stats = computed(() => ({
  total: agents.value.length,
  active: agents.value.filter(a => a.status === 'active').length,
  totalUsage: agents.value.reduce((sum, a) => sum + (a.usage_count || 0), 0)
}))

const createAgent = () => router.push('/agent-studio')
const useAgent = (agent: Agent) => router.push({ path: '/', query: { tab: 'agent', agentId: agent.id, agent: agent.name, from: 'home' } })
const editAgent = (agent: Agent) => router.push({ path: '/agent-studio', query: { id: agent.id } })
const onCardClick = (agent: Agent) => useAgent(agent)

const getStatusClass = (status: string) => {
  switch (status) {
    case 'active': return 'status-active'
    case 'draft': return 'status-draft'
    case 'deprecated': return 'status-deprecated'
    default: return ''
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'active': return '已发布'
    case 'draft': return '草稿'
    case 'deprecated': return '已弃用'
    default: return status
  }
}
</script>

<template>
  <div class="agents-view">
    <!-- 装饰背景 -->
    <div class="bg-decoration">
      <div class="bg-blob blob-1"></div>
      <div class="bg-blob blob-2"></div>
      <div class="bg-grid"></div>
    </div>

    <!-- 顶部区域 -->
    <header class="page-header">
      <div class="header-top">
        <div class="header-info">
          <div class="title-row">
            <span class="title-icon">🤖</span>
            <h1>Agent 市场</h1>
            <button class="btn-collapse" @click="toggleHeader" :class="{ collapsed: isHeaderCollapsed }">
              <svg viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd"/>
              </svg>
            </button>
          </div>
          <p class="subtitle">发现、使用和管理各种智能 Agent</p>
        </div>
        <button class="btn-create" @click="createAgent">
          <span class="btn-icon">+</span>
          <span>创建 Agent</span>
        </button>
      </div>

      <!-- 可收缩区域 -->
      <div class="collapsible-section" :class="{ collapsed: isHeaderCollapsed }">
        <!-- 功能说明卡片 -->
        <div class="intro-cards">
          <div class="intro-card">
            <span class="intro-icon">💡</span>
            <div class="intro-content">
              <h4>什么是 Agent?</h4>
              <p>具有特定能力的 AI 助手，可使用工具、记忆对话</p>
            </div>
          </div>
          <div class="intro-card">
            <span class="intro-icon">🔧</span>
            <div class="intro-content">
              <h4>如何使用?</h4>
              <p>选择 Agent 点击「使用」进入对话，或编辑自定义配置</p>
            </div>
          </div>
          <div class="intro-card">
            <span class="intro-icon">⚡</span>
            <div class="intro-content">
              <h4>创建自己的</h4>
              <p>点击「创建 Agent」定制专属助手，配置工具和提示词</p>
            </div>
          </div>
        </div>

        <!-- 统计卡片 -->
        <div class="stats-cards">
          <div class="stat-card">
            <div class="stat-icon">📦</div>
            <div class="stat-content">
              <span class="stat-value">{{ stats.total }}</span>
              <span class="stat-label">总 Agents</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon pulse">🟢</div>
            <div class="stat-content">
              <span class="stat-value">{{ stats.active }}</span>
              <span class="stat-label">已发布</span>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">⚡</div>
            <div class="stat-content">
              <span class="stat-value">{{ stats.totalUsage.toLocaleString() }}</span>
              <span class="stat-label">总调用</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 筛选栏 -->
      <div class="filter-section">
        <div class="search-wrapper">
          <svg class="search-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
          </svg>
          <input v-model="searchQuery" type="text" placeholder="搜索 Agent 名称或描述..." class="search-input" />
        </div>
        <div class="category-pills">
          <button
            v-for="cat in categories"
            :key="cat"
            :class="['pill', { active: selectedCategory === cat }]"
            @click="selectedCategory = cat"
          >
            {{ cat === 'all' ? '全部' : cat }}
          </button>
        </div>
      </div>
    </header>

    <!-- 主内容 -->
    <div class="page-content">
      <!-- Agent 网格 -->
      <div class="agents-grid">
        <div
          v-for="(agent, index) in filteredAgents"
          :key="agent.id"
          class="agent-card"
          :style="{ '--delay': index * 0.05 + 's' }"
          @click="onCardClick(agent)"
        >
          <div class="card-content">
            <div class="card-header">
              <div class="agent-avatar">
                <span class="avatar-icon">{{ agent.icon }}</span>
              </div>
              <span :class="['status-badge', getStatusClass(agent.status)]">
                {{ getStatusText(agent.status) }}
              </span>
            </div>

            <h3 class="agent-name">{{ agent.name }}</h3>
            <p class="agent-desc">{{ agent.description }}</p>

            <div class="agent-meta">
              <div class="meta-item">
                <svg viewBox="0 0 16 16" fill="currentColor">
                  <path d="M8 8a3 3 0 100-6 3 3 0 000 6zm2-3a2 2 0 11-4 0 2 2 0 014 0zm4 8c0 1-1 1-1 1H3s-1 0-1-1 1-4 6-4 6 3 6 4zm-1-.004c-.001-.246-.154-.986-.832-1.664C11.516 10.68 10.289 10 8 10c-2.29 0-3.516.68-4.168 1.332-.678.678-.83 1.418-.832 1.664h10z"/>
                </svg>
                <span>{{ agent.author }}</span>
              </div>
              <div class="meta-item">
                <svg viewBox="0 0 16 16" fill="currentColor">
                  <path d="M11.251.068a.5.5 0 0 1 .227.58L9.677 6.5H13a.5.5 0 0 1 .364.843l-8 8.5a.5.5 0 0 1-.842-.49L6.323 9.5H3a.5.5 0 0 1-.364-.843l8-8.5a.5.5 0 0 1 .615-.09z"/>
                </svg>
                <span>{{ agent.usage_count || 0 }}</span>
              </div>
            </div>

            <div class="capabilities">
              <span v-for="tool in (agent.tools || []).slice(0, 3)" :key="tool" class="cap-tag">
                {{ tool }}
              </span>
            </div>

            <div class="card-actions" @click.stop>
              <button class="btn-use" @click="useAgent(agent)">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/>
                </svg>
                使用
              </button>
              <button class="btn-edit" @click="editAgent(agent)" title="编辑">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"/>
                </svg>
              </button>
              <button class="btn-delete" @click="confirmDelete(agent)" title="删除">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="filteredAgents.length === 0" class="empty-state">
          <div class="empty-visual">
            <span class="empty-icon">🔍</span>
            <div class="empty-rings">
              <span class="ring"></span>
              <span class="ring"></span>
            </div>
          </div>
          <h3>没有找到匹配的 Agent</h3>
          <p>尝试调整搜索条件，或创建一个新的 Agent</p>
          <button class="btn-create-empty" @click="createAgent">
            <span>+</span> 创建新 Agent
          </button>
        </div>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click="cancelDelete">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <span class="modal-icon">⚠️</span>
          <h3>确认删除</h3>
        </div>
        <p class="modal-body">
          确定要删除 Agent「<strong>{{ agentToDelete?.name }}</strong>」吗？此操作不可恢复。
        </p>
        <div class="modal-actions">
          <button class="btn-cancel" @click="cancelDelete">取消</button>
          <button class="btn-confirm-delete" @click="deleteAgent">确认删除</button>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-spinner"></div>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

.agents-view {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #f5f7fa;
  color: #1f2937;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  font-family: 'Plus Jakarta Sans', 'Noto Sans SC', -apple-system, sans-serif;
}

/* 装饰背景 - 隐藏 */
.bg-decoration {
  display: none;
}

.bg-blob, .blob-1, .blob-2, .bg-grid {
  display: none;
}

/* 主内容 */
.page-content {
  position: relative;
  z-index: 1;
  flex: 1;
  overflow-y: auto;
  padding: 0 32px 40px;
  max-width: 1280px;
  margin: 0 auto;
  width: 100%;
}

/* 头部 */
.page-header {
  flex-shrink: 0;
  padding: 16px 32px 0;
  background: #f5f7fa;
  position: relative;
  z-index: 10;
  max-width: 1280px;
  margin: 0 auto;
  width: 100%;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 24px;
}

.header-info h1 {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
  color: #1f2937;
}

.subtitle {
  font-size: 13px;
  color: #9ca3af;
  margin: 0;
  padding-left: 16px;
  border-left: 1px solid #e5e7eb;
}

.btn-collapse {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: transparent;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  transition: all 0.2s;
  border-radius: 4px;
}

.btn-collapse:hover {
  background: #e5e7eb;
  color: #6b7280;
}

.btn-collapse svg {
  width: 16px;
  height: 16px;
  transition: transform 0.3s ease;
}

.btn-collapse.collapsed svg {
  transform: rotate(-90deg);
}

.btn-create {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(22, 119, 255, 0.3);
}

.btn-create:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(22, 119, 255, 0.4);
}

.btn-icon {
  font-size: 14px;
  font-weight: 400;
}

/* 可收缩区域 */
.collapsible-section {
  max-height: 200px;
  overflow: hidden;
  transition: max-height 0.3s ease, opacity 0.3s ease, margin 0.3s ease;
  opacity: 1;
  margin-bottom: 12px;
}

.collapsible-section.collapsed {
  max-height: 0;
  opacity: 0;
  margin-bottom: 0;
}

/* 功能说明卡片 */
.intro-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.intro-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.intro-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.intro-content h4 {
  font-size: 12px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 2px;
}

.intro-content p {
  font-size: 11px;
  color: #9ca3af;
  margin: 0;
  line-height: 1.4;
}

/* 统计卡片 */
.stats-cards {
  display: flex;
  gap: 12px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  transition: all 0.2s;
}

.stat-card:hover {
  border-color: #1677ff;
  box-shadow: 0 2px 8px rgba(22, 119, 255, 0.12);
}

.stat-icon {
  font-size: 18px;
}

.stat-icon.pulse {
  animation: pulse-icon 2s ease-in-out infinite;
}

@keyframes pulse-icon {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 16px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.2;
}

.stat-label {
  font-size: 11px;
  color: #9ca3af;
}

/* 筛选区 */
.filter-section {
  display: flex;
  gap: 12px;
  align-items: center;
  padding-bottom: 16px;
  flex-wrap: wrap;
}

.search-wrapper {
  position: relative;
  flex: 1;
  max-width: 280px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 14px;
  height: 14px;
  color: #9ca3af;
}

.search-input {
  width: 100%;
  padding: 8px 12px 8px 34px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  color: #1f2937;
  font-size: 13px;
  outline: none;
  transition: all 0.2s;
}

.search-input::placeholder {
  color: #9ca3af;
}

.search-input:focus {
  border-color: #1677ff;
  box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.1);
}

.category-pills {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.pill {
  padding: 6px 14px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  color: #6b7280;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.pill:hover {
  border-color: #1677ff;
  color: #1677ff;
}

.pill.active {
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
  border-color: transparent;
  color: #ffffff;
}

/* Agent 网格 - 与首页一致 4 列 */
.agents-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  grid-auto-rows: 1fr;
}

.agent-card {
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  animation: card-in 0.3s ease-out backwards;
  animation-delay: var(--delay);
  cursor: pointer;
  height: 100%;
}

@keyframes card-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.card-content {
  position: relative;
  padding: 20px;
  background: #ffffff;
  border: 1px solid transparent;
  border-radius: 16px;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.agent-card:hover .card-content {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
  border-color: #1677ff;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.agent-avatar {
  position: relative;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: linear-gradient(135deg, #60a5fa 0%, #93c5fd 50%, #c4b5fd 100%);
}

/* 不同颜色的头像 */
.agent-card:nth-child(1) .agent-avatar { background: linear-gradient(135deg, #60a5fa 0%, #93c5fd 50%, #c4b5fd 100%); }
.agent-card:nth-child(2) .agent-avatar { background: linear-gradient(135deg, #a78bfa 0%, #c4b5fd 50%, #f9a8d4 100%); }
.agent-card:nth-child(3) .agent-avatar { background: linear-gradient(135deg, #0891b2 0%, #22d3ee 50%, #a5f3fc 100%); }
.agent-card:nth-child(4) .agent-avatar { background: linear-gradient(135deg, #f97316 0%, #fbbf24 50%, #fde68a 100%); }
.agent-card:nth-child(5) .agent-avatar { background: linear-gradient(135deg, #22c55e 0%, #4ade80 50%, #86efac 100%); }
.agent-card:nth-child(6) .agent-avatar { background: linear-gradient(135deg, #ec4899 0%, #f472b6 50%, #fce7f3 100%); }
.agent-card:nth-child(7) .agent-avatar { background: linear-gradient(135deg, #ef4444 0%, #fca5a5 50%, #fef3c7 100%); }
.agent-card:nth-child(8) .agent-avatar { background: linear-gradient(135deg, #6366f1 0%, #a5b4fc 50%, #e0e7ff 100%); }

.avatar-icon {
  font-size: 22px;
  position: relative;
  z-index: 1;
}

.status-badge {
  padding: 3px 8px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 600;
}

.status-active {
  background: #ecfdf5;
  color: #059669;
}

.status-draft {
  background: #fef9c3;
  color: #ca8a04;
}

.status-deprecated {
  background: #fee2e2;
  color: #dc2626;
}

.agent-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 6px;
}

.agent-desc {
  font-size: 12px;
  color: #6b7280;
  margin: 0 0 10px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
  min-height: 36px;
}

.agent-meta {
  display: flex;
  gap: 12px;
  margin-bottom: 10px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  color: #9ca3af;
}

.meta-item svg {
  width: 11px;
  height: 11px;
}

.capabilities {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.cap-tag {
  padding: 3px 8px;
  background: #f3f4f6;
  border-radius: 4px;
  font-size: 10px;
  color: #6b7280;
}

.card-actions {
  display: flex;
  gap: 6px;
}

.btn-use {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
  border: none;
  border-radius: 6px;
  color: white;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-use:hover {
  box-shadow: 0 2px 8px rgba(22, 119, 255, 0.4);
}

.btn-use svg {
  width: 12px;
  height: 12px;
}

.btn-edit {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-edit:hover {
  background: #e5e7eb;
  color: #1f2937;
}

.btn-edit svg {
  width: 12px;
  height: 12px;
}

/* 空状态 */
.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 80px 20px;
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
}

.empty-visual {
  position: relative;
  width: 100px;
  height: 100px;
  margin: 0 auto 24px;
}

.empty-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 48px;
}

.empty-rings .ring {
  position: absolute;
  inset: 0;
  border: 2px solid rgba(22, 119, 255, 0.2);
  border-radius: 50%;
  animation: ring-expand 2s ease-out infinite;
}

.empty-rings .ring:nth-child(2) {
  animation-delay: 1s;
}

@keyframes ring-expand {
  0% { transform: scale(0.8); opacity: 1; }
  100% { transform: scale(1.5); opacity: 0; }
}

.empty-state h3 {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px;
}

.empty-state p {
  color: #6b7280;
  margin: 0 0 24px;
}

.btn-create-empty {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
  border: none;
  border-radius: 10px;
  color: white;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 14px rgba(22, 119, 255, 0.35);
}

.btn-create-empty:hover {
  box-shadow: 0 6px 20px rgba(22, 119, 255, 0.45);
  transform: translateY(-1px);
}

/* 删除按钮 */
.btn-delete {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  color: #ef4444;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-delete:hover {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #dc2626;
}

.btn-delete svg {
  width: 12px;
  height: 12px;
}

/* 删除确认对话框 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 24px;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.modal-icon {
  font-size: 24px;
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.modal-body {
  color: #6b7280;
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 24px;
}

.modal-body strong {
  color: #1f2937;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn-cancel {
  padding: 10px 20px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  color: #6b7280;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: #e5e7eb;
  color: #1f2937;
}

.btn-confirm-delete {
  padding: 10px 20px;
  background: linear-gradient(135deg, #ef4444, #dc2626);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-confirm-delete:hover {
  box-shadow: 0 4px 16px rgba(239, 68, 68, 0.4);
  transform: translateY(-1px);
}

/* 加载状态 */
.loading-overlay {
  position: fixed;
  inset: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(22, 119, 255, 0.2);
  border-top-color: #1677ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 响应式 */
@media (max-width: 1200px) {
  .agents-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 900px) {
  .agents-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .intro-cards {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .agents-grid {
    grid-template-columns: 1fr;
  }

  .page-header {
    padding: 16px;
  }

  .page-content {
    padding: 0 16px 24px;
  }
}
</style>
