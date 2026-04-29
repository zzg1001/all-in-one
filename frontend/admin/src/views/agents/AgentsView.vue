<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { agentsApi, type Agent } from '@/api'

// 状态
const agents = ref<Agent[]>([])
const loading = ref(false)
const searchQuery = ref('')

// 编辑弹框
const showEditModal = ref(false)
const editingAgent = ref<Agent | null>(null)
const selectedPermissions = ref<string[]>([])
const accessAllData = ref(false)

// 过滤后的 Agent 列表
const filteredAgents = computed(() => {
  if (!searchQuery.value) return agents.value
  const q = searchQuery.value.toLowerCase()
  return agents.value.filter(a =>
    a.name.toLowerCase().includes(q) ||
    a.description?.toLowerCase().includes(q) ||
    a.category?.toLowerCase().includes(q)
  )
})

// 统计
const stats = computed(() => ({
  total: agents.value.length,
  active: agents.value.filter(a => a.status === 'active').length,
  withAllAccess: agents.value.filter(a => a.accessible_agent_ids?.includes('*')).length,
}))

// 加载数据
const loadAgents = async () => {
  loading.value = true
  try {
    const response = await agentsApi.getAll()
    agents.value = response.agents || []
  } catch (e) {
    console.error('加载 Agent 失败:', e)
  } finally {
    loading.value = false
  }
}

// 获取 Agent 的数据权限描述
const getPermissionDesc = (agent: Agent) => {
  const ids = agent.accessible_agent_ids || []
  if (ids.length === 0) return '仅自己的数据'
  if (ids.includes('*')) return '全部 Agent 数据'
  return `自己 + ${ids.length} 个 Agent`
}

// 获取 Agent 可访问的 Agent 名称列表
const getAccessibleAgentNames = (agent: Agent) => {
  const ids = agent.accessible_agent_ids || []
  if (ids.length === 0 || ids.includes('*')) return []
  return ids.map(id => {
    const a = agents.value.find(x => x.id === id)
    return a ? a.name : id
  })
}

// 打开编辑弹框
const openEdit = (agent: Agent) => {
  editingAgent.value = agent
  const ids = agent.accessible_agent_ids || []
  accessAllData.value = ids.includes('*')
  selectedPermissions.value = accessAllData.value ? [] : [...ids]
  showEditModal.value = true
}

// 保存权限
const savePermissions = async () => {
  if (!editingAgent.value) return

  try {
    const newIds = accessAllData.value ? ['*'] : selectedPermissions.value
    await agentsApi.update(editingAgent.value.id, {
      accessible_agent_ids: newIds
    })

    // 更新本地数据
    const idx = agents.value.findIndex(a => a.id === editingAgent.value!.id)
    if (idx >= 0) {
      agents.value[idx] = { ...agents.value[idx], accessible_agent_ids: newIds }
    }

    showEditModal.value = false
    alert('保存成功')
  } catch (e) {
    alert('保存失败: ' + e)
  }
}

// 可选的其他 Agent（排除自己）
const otherAgents = computed(() => {
  if (!editingAgent.value) return []
  return agents.value.filter(a => a.id !== editingAgent.value!.id)
})

// 切换选择
const toggleAgent = (agentId: string) => {
  const idx = selectedPermissions.value.indexOf(agentId)
  if (idx >= 0) {
    selectedPermissions.value.splice(idx, 1)
  } else {
    selectedPermissions.value.push(agentId)
  }
}

// 全选/取消全选
const selectAll = () => {
  if (selectedPermissions.value.length === otherAgents.value.length) {
    selectedPermissions.value = []
  } else {
    selectedPermissions.value = otherAgents.value.map(a => a.id)
  }
}

onMounted(() => {
  loadAgents()
})
</script>

<template>
  <div class="agents-page">
    <!-- 头部 -->
    <div class="page-header">
      <div class="header-info">
        <h2>Agent 数据权限</h2>
        <p class="page-desc">配置每个 Agent 可以访问哪些数据</p>
      </div>
      <div class="header-actions">
        <div class="search-box">
          <svg class="search-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
          </svg>
          <input v-model="searchQuery" type="text" placeholder="搜索 Agent..." />
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon blue">
          <span>🤖</span>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ stats.total }}</span>
          <span class="stat-label">Agent 总数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green">
          <span>✓</span>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ stats.active }}</span>
          <span class="stat-label">已发布</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon orange">
          <span>👑</span>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ stats.withAllAccess }}</span>
          <span class="stat-label">全数据权限</span>
        </div>
      </div>
    </div>

    <!-- 表格 -->
    <div class="table-container">
      <div class="table-header">
        <div class="th-cell th-agent">Agent</div>
        <div class="th-cell th-category">分类</div>
        <div class="th-cell th-status">状态</div>
        <div class="th-cell th-permission">数据权限</div>
        <div class="th-cell th-details">可访问的 Agent</div>
        <div class="th-cell th-actions">操作</div>
      </div>

      <div class="table-body-wrapper">
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          加载中...
        </div>
        <div v-else-if="filteredAgents.length === 0" class="empty-state">暂无 Agent 数据</div>
        <template v-else>
          <div v-for="agent in filteredAgents" :key="agent.id" class="table-row">
            <div class="td-cell td-agent">
              <div class="agent-info">
                <span class="agent-icon">{{ agent.icon || '🤖' }}</span>
                <div class="agent-details">
                  <span class="agent-name">{{ agent.name }}</span>
                  <span class="agent-desc">{{ agent.description?.slice(0, 30) }}{{ agent.description?.length > 30 ? '...' : '' }}</span>
                </div>
              </div>
            </div>
            <div class="td-cell td-category">
              <span class="category-tag">{{ agent.category || '通用' }}</span>
            </div>
            <div class="td-cell td-status">
              <span class="status-badge" :class="agent.status">
                {{ agent.status === 'active' ? '已发布' : agent.status === 'draft' ? '草稿' : agent.status }}
              </span>
            </div>
            <div class="td-cell td-permission">
              <span class="permission-badge" :class="{
                'all': agent.accessible_agent_ids?.includes('*'),
                'custom': agent.accessible_agent_ids?.length && !agent.accessible_agent_ids?.includes('*'),
                'self': !agent.accessible_agent_ids?.length
              }">
                {{ getPermissionDesc(agent) }}
              </span>
            </div>
            <div class="td-cell td-details">
              <div class="access-list" v-if="getAccessibleAgentNames(agent).length">
                <span v-for="name in getAccessibleAgentNames(agent).slice(0, 3)" :key="name" class="access-tag">
                  {{ name }}
                </span>
                <span v-if="getAccessibleAgentNames(agent).length > 3" class="access-more">
                  +{{ getAccessibleAgentNames(agent).length - 3 }}
                </span>
              </div>
              <span v-else class="no-access">-</span>
            </div>
            <div class="td-cell td-actions">
              <button class="btn-edit" @click="openEdit(agent)">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"/>
                </svg>
                配置权限
              </button>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- 编辑弹框 -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>配置数据权限</h3>
          <button class="close-btn" @click="showEditModal = false">&times;</button>
        </div>

        <div class="modal-body" v-if="editingAgent">
          <div class="current-agent">
            <span class="agent-icon">{{ editingAgent.icon || '🤖' }}</span>
            <div>
              <strong>{{ editingAgent.name }}</strong>
              <p>{{ editingAgent.description }}</p>
            </div>
          </div>

          <div class="permission-section">
            <label class="checkbox-label all-access">
              <input type="checkbox" v-model="accessAllData" />
              <span class="checkbox-mark"></span>
              <span class="checkbox-text">
                <strong>访问全部 Agent 数据</strong>
                <small>勾选后可以查看所有 Agent 的数据（Boss 权限）</small>
              </span>
            </label>
          </div>

          <div class="permission-section" v-if="!accessAllData">
            <div class="section-header">
              <span>选择可访问的 Agent 数据：</span>
              <button class="select-all-btn" @click="selectAll">
                {{ selectedPermissions.length === otherAgents.length ? '取消全选' : '全选' }}
              </button>
            </div>
            <div class="agent-list">
              <label v-for="agent in otherAgents" :key="agent.id" class="checkbox-label">
                <input
                  type="checkbox"
                  :checked="selectedPermissions.includes(agent.id)"
                  @change="toggleAgent(agent.id)"
                />
                <span class="checkbox-mark"></span>
                <span class="agent-icon-small">{{ agent.icon || '🤖' }}</span>
                <span class="checkbox-text">
                  {{ agent.name }}
                  <small>{{ agent.category }}</small>
                </span>
              </label>
            </div>
            <div class="selected-info" v-if="selectedPermissions.length">
              已选择 {{ selectedPermissions.length }} 个 Agent
            </div>
          </div>

          <div class="tip-box">
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
            </svg>
            <span>Agent 始终可以访问自己的数据，此处配置额外的数据访问权限</span>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-cancel" @click="showEditModal = false">取消</button>
          <button class="btn-save" @click="savePermissions">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.agents-page {
  padding: 24px;
  background: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-info h2 {
  margin: 0 0 4px 0;
  font-size: 24px;
  color: #1a1a2e;
}

.page-desc {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.search-box {
  position: relative;
  width: 240px;
}

.search-box input {
  width: 100%;
  padding: 8px 12px 8px 36px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  background: white;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  color: #999;
}

/* 统计卡片 */
.stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  flex: 1;
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.stat-icon.blue { background: #e0f2fe; color: #0284c7; }
.stat-icon.green { background: #dcfce7; color: #16a34a; }
.stat-icon.orange { background: #fef3c7; color: #d97706; }

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #1a1a2e;
}

.stat-label {
  font-size: 13px;
  color: #666;
}

/* 表格 */
.table-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  overflow: hidden;
}

.table-header {
  display: flex;
  background: #f8fafc;
  border-bottom: 1px solid #e5e7eb;
  padding: 12px 20px;
  font-weight: 500;
  color: #64748b;
  font-size: 13px;
}

.th-cell { padding: 0 8px; }
.th-agent { flex: 2; }
.th-category { flex: 1; }
.th-status { flex: 0.8; }
.th-permission { flex: 1.2; }
.th-details { flex: 1.5; }
.th-actions { flex: 1; text-align: right; }

.table-body-wrapper {
  max-height: calc(100vh - 400px);
  overflow-y: auto;
}

.table-row {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f1f5f9;
  transition: background 0.2s;
}

.table-row:hover {
  background: #f8fafc;
}

.td-cell { padding: 0 8px; }
.td-agent { flex: 2; }
.td-category { flex: 1; }
.td-status { flex: 0.8; }
.td-permission { flex: 1.2; }
.td-details { flex: 1.5; }
.td-actions { flex: 1; text-align: right; }

.agent-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.agent-icon {
  font-size: 28px;
}

.agent-details {
  display: flex;
  flex-direction: column;
}

.agent-name {
  font-weight: 500;
  color: #1a1a2e;
}

.agent-desc {
  font-size: 12px;
  color: #999;
}

.category-tag {
  padding: 4px 10px;
  background: #f1f5f9;
  border-radius: 4px;
  font-size: 12px;
  color: #475569;
}

.status-badge {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
}

.status-badge.active {
  background: #dcfce7;
  color: #16a34a;
}

.status-badge.draft {
  background: #fef3c7;
  color: #d97706;
}

.permission-badge {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
}

.permission-badge.all {
  background: #fef3c7;
  color: #b45309;
}

.permission-badge.custom {
  background: #dbeafe;
  color: #1d4ed8;
}

.permission-badge.self {
  background: #f1f5f9;
  color: #64748b;
}

.access-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.access-tag {
  padding: 2px 8px;
  background: #e0f2fe;
  color: #0284c7;
  border-radius: 4px;
  font-size: 11px;
}

.access-more {
  padding: 2px 8px;
  background: #e5e7eb;
  color: #6b7280;
  border-radius: 4px;
  font-size: 11px;
}

.no-access {
  color: #999;
}

.btn-edit {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-edit:hover {
  background: #2563eb;
}

.btn-edit svg {
  width: 14px;
  height: 14px;
}

.loading-state, .empty-state {
  padding: 60px;
  text-align: center;
  color: #999;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 弹框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 16px;
  width: 560px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: #f1f5f9;
  border-radius: 8px;
  font-size: 20px;
  cursor: pointer;
  color: #64748b;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.current-agent {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  margin-bottom: 24px;
}

.current-agent .agent-icon {
  font-size: 40px;
}

.current-agent strong {
  display: block;
  font-size: 16px;
  margin-bottom: 4px;
}

.current-agent p {
  margin: 0;
  font-size: 13px;
  color: #666;
}

.permission-section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  color: #374151;
}

.select-all-btn {
  padding: 4px 10px;
  background: #f1f5f9;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  color: #3b82f6;
  cursor: pointer;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.checkbox-label:hover {
  border-color: #3b82f6;
  background: #f8fafc;
}

.checkbox-label.all-access {
  background: #fef3c7;
  border-color: #f59e0b;
}

.checkbox-label input {
  display: none;
}

.checkbox-mark {
  width: 20px;
  height: 20px;
  border: 2px solid #d1d5db;
  border-radius: 4px;
  position: relative;
  flex-shrink: 0;
}

.checkbox-label input:checked + .checkbox-mark {
  background: #3b82f6;
  border-color: #3b82f6;
}

.checkbox-label input:checked + .checkbox-mark::after {
  content: '';
  position: absolute;
  left: 6px;
  top: 2px;
  width: 5px;
  height: 10px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.checkbox-text {
  flex: 1;
}

.checkbox-text strong {
  display: block;
}

.checkbox-text small {
  color: #666;
  font-size: 12px;
}

.agent-icon-small {
  font-size: 20px;
}

.agent-list {
  max-height: 280px;
  overflow-y: auto;
}

.selected-info {
  margin-top: 12px;
  padding: 8px 12px;
  background: #dbeafe;
  color: #1d4ed8;
  border-radius: 6px;
  font-size: 13px;
}

.tip-box {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  background: #f0f9ff;
  border-radius: 8px;
  color: #0369a1;
  font-size: 13px;
}

.tip-box svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  margin-top: 2px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
}

.btn-cancel {
  padding: 10px 20px;
  background: #f1f5f9;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  color: #64748b;
}

.btn-save {
  padding: 10px 24px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.btn-save:hover {
  background: #2563eb;
}
</style>
