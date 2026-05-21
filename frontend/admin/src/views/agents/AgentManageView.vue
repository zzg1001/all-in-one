<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { agentsApi, type Agent } from '@/api'
import Toast from '@/components/Toast.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const router = useRouter()
const toast = ref<InstanceType<typeof Toast> | null>(null)
const confirmDialog = ref<InstanceType<typeof ConfirmDialog> | null>(null)

const agents = ref<Agent[]>([])
const loading = ref(false)
const searchQuery = ref('')

const filteredAgents = computed(() => {
  if (!searchQuery.value) return agents.value
  const q = searchQuery.value.toLowerCase()
  return agents.value.filter(a =>
    a.name.toLowerCase().includes(q) ||
    a.description?.toLowerCase().includes(q) ||
    a.category?.toLowerCase().includes(q)
  )
})

const stats = computed(() => ({
  total: agents.value.length,
  active: agents.value.filter(a => a.status === 'active').length,
  inactive: agents.value.filter(a => a.status === 'inactive').length,
  draft: agents.value.filter(a => a.status === 'draft').length,
}))

const loadAgents = async () => {
  loading.value = true
  try {
    const response = await agentsApi.getAll()
    agents.value = response.agents || []
  } catch (e) {
    console.error('加载失败:', e)
  } finally {
    loading.value = false
  }
}

const openCreate = () => router.push('/agent-manage/new')
const openEdit = (agent: Agent) => router.push(`/agent-manage/${agent.id}`)

const deleteAgent = async (agent: Agent) => {
  const confirmed = await confirmDialog.value?.confirm(
    `确定要删除「${agent.name}」吗？`,
    { title: '删除 Agent', type: 'danger' }
  )
  if (!confirmed) return
  try {
    await agentsApi.delete(agent.id)
    agents.value = agents.value.filter(a => a.id !== agent.id)
    toast.value?.show('已删除', 'dark')
  } catch (e) {
    toast.value?.error('删除失败')
  }
}

// 状态切换菜单
const showStatusMenu = ref<string | null>(null)

const toggleStatusMenu = (agentId: string, event: Event) => {
  event.stopPropagation()
  showStatusMenu.value = showStatusMenu.value === agentId ? null : agentId
}

const setStatus = async (agent: Agent, newStatus: string) => {
  showStatusMenu.value = null
  if (agent.status === newStatus) return

  try {
    await agentsApi.update(agent.id, { status: newStatus })
    const idx = agents.value.findIndex(a => a.id === agent.id)
    if (idx >= 0) agents.value[idx] = { ...agents.value[idx], status: newStatus }

    const statusLabels: Record<string, string> = {
      active: '已发布',
      inactive: '已设为不可用',
      draft: '已设为草稿'
    }
    toast.value?.show(statusLabels[newStatus] || '已更新', 'dark')
  } catch (e) {
    toast.value?.error('更新失败')
  }
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    active: '已发布',
    inactive: '不可用',
    draft: '草稿'
  }
  return labels[status] || status
}

// 点击页面其他地方关闭状态菜单
const closeStatusMenu = () => {
  showStatusMenu.value = null
}

onMounted(() => {
  loadAgents()
  document.addEventListener('click', closeStatusMenu)
})

onUnmounted(() => {
  document.removeEventListener('click', closeStatusMenu)
})
</script>

<template>
  <Toast ref="toast" />
  <ConfirmDialog ref="confirmDialog" />

  <div class="page">
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="search-box">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
        <input v-model="searchQuery" placeholder="搜索" />
      </div>

      <div class="toolbar-stats">
        <span class="stat-item">
          <span class="stat-dot total"></span>
          {{ stats.total }} 个
        </span>
        <span class="stat-item">
          <span class="stat-dot active"></span>
          {{ stats.active }} 已发布
        </span>
        <span class="stat-item">
          <span class="stat-dot inactive"></span>
          {{ stats.inactive }} 不可用
        </span>
        <span class="stat-item">
          <span class="stat-dot draft"></span>
          {{ stats.draft }} 草稿
        </span>
      </div>

      <button class="btn-add" @click="openCreate">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M12 5v14M5 12h14"/>
        </svg>
        新建
      </button>
    </div>

    <!-- 内容区 -->
    <div class="content">
      <!-- 加载中 -->
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!filteredAgents.length" class="empty">
        <div class="empty-icon">🤖</div>
        <div class="empty-text">暂无 Agent</div>
        <button class="empty-btn" @click="openCreate">创建第一个</button>
      </div>

      <!-- Agent 列表 -->
      <div v-else class="agent-grid">
        <div
          v-for="agent in filteredAgents"
          :key="agent.id"
          class="agent-card"
          @click="openEdit(agent)"
        >
          <div class="card-header">
            <span class="card-icon">{{ agent.icon || '🤖' }}</span>
            <div class="status-wrapper">
              <div class="card-status" :class="agent.status" @click.stop="toggleStatusMenu(agent.id, $event)">
                {{ getStatusLabel(agent.status) }}
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <path d="m6 9 6 6 6-6"/>
                </svg>
              </div>
              <!-- 状态下拉菜单 -->
              <div v-if="showStatusMenu === agent.id" class="status-menu" @click.stop>
                <div class="status-option active" @click="setStatus(agent, 'active')">
                  <span class="status-dot"></span>
                  已发布
                  <span class="status-desc">展示且可用</span>
                </div>
                <div class="status-option inactive" @click="setStatus(agent, 'inactive')">
                  <span class="status-dot"></span>
                  不可用
                  <span class="status-desc">展示但不可点击</span>
                </div>
                <div class="status-option draft" @click="setStatus(agent, 'draft')">
                  <span class="status-dot"></span>
                  草稿
                  <span class="status-desc">不展示</span>
                </div>
              </div>
            </div>
          </div>

          <div class="card-body">
            <div class="card-name">{{ agent.name }}</div>
            <div class="card-desc">{{ agent.description || '暂无描述' }}</div>
          </div>

          <div class="card-footer">
            <span class="card-tag">{{ agent.category || '通用' }}</span>
            <span class="card-skills" v-if="agent.skills?.length">
              {{ agent.skills.length }} 个技能
            </span>
            <button class="card-delete" @click.stop="deleteAgent(agent)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  height: 100%;
  min-height: 100vh;
  background: linear-gradient(180deg, #f5f5f7 0%, #e8e8ed 100%);
  display: flex;
  flex-direction: column;
  position: relative;
}

/* 工具栏 - 固定在顶部 */
.toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 20px;
  background: white;
  border-bottom: 1px solid rgba(0,0,0,0.08);
  position: sticky;
  top: 0;
  z-index: 100;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: rgba(0,0,0,0.04);
  border-radius: 8px;
  width: 180px;
}

.search-box svg {
  width: 14px;
  height: 14px;
  color: #86868b;
  flex-shrink: 0;
}

.search-box input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 13px;
  outline: none;
  color: #1d1d1f;
}

.search-box input::placeholder {
  color: #86868b;
}

.toolbar-stats {
  display: flex;
  gap: 16px;
  flex: 1;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #86868b;
}

.stat-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.stat-dot.total { background: #007aff; }
.stat-dot.active { background: #34c759; }
.stat-dot.inactive { background: #8e8e93; }
.stat-dot.draft { background: #ff9500; }

.btn-add {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  background: #007aff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-add:hover {
  background: #0066d6;
}

.btn-add:active {
  transform: scale(0.96);
}

.btn-add svg {
  width: 12px;
  height: 12px;
}

/* 内容区 - 卡片滚动 */
.content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  min-height: 0;
}

/* 加载 */
.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e5ea;
  border-top-color: #007aff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 空状态 */
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  gap: 12px;
}

.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.empty-text {
  font-size: 15px;
  color: #86868b;
}

.empty-btn {
  margin-top: 8px;
  padding: 8px 20px;
  background: #007aff;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.empty-btn:hover {
  background: #0066d6;
}

/* Agent 网格 */
.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.agent-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.agent-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}

.card-icon {
  font-size: 40px;
}

.card-status {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.card-status {
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-status svg {
  opacity: 0.6;
}

.card-status.active {
  background: rgba(52, 199, 89, 0.12);
  color: #248a3d;
}

.card-status.inactive {
  background: rgba(142, 142, 147, 0.15);
  color: #636366;
}

.card-status.draft {
  background: rgba(255, 149, 0, 0.12);
  color: #c93400;
}

.card-status:hover {
  transform: scale(1.05);
}

/* 状态包装器 */
.status-wrapper {
  position: relative;
}

/* 状态下拉菜单 */
.status-menu {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  padding: 6px;
  min-width: 180px;
  z-index: 100;
}

.status-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #1d1d1f;
  position: relative;
  white-space: nowrap;
}

.status-option:hover {
  background: #f5f5f7;
}

.status-option .status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-option.active .status-dot { background: #34c759; }
.status-option.inactive .status-dot { background: #8e8e93; }
.status-option.draft .status-dot { background: #ff9500; }

.status-option .status-desc {
  font-size: 11px;
  color: #86868b;
  margin-left: auto;
}

.card-body {
  margin-bottom: 16px;
}

.card-name {
  font-size: 17px;
  font-weight: 600;
  color: #1d1d1f;
  margin-bottom: 6px;
}

.card-desc {
  font-size: 13px;
  color: #86868b;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-tag {
  padding: 4px 10px;
  background: #f5f5f7;
  border-radius: 6px;
  font-size: 12px;
  color: #86868b;
}

.card-skills {
  font-size: 12px;
  color: #007aff;
}

.card-delete {
  margin-left: auto;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #86868b;
  transition: all 0.2s;
  opacity: 0;
}

.agent-card:hover .card-delete {
  opacity: 1;
}

.card-delete:hover {
  background: rgba(255, 59, 48, 0.1);
  color: #ff3b30;
}
</style>
