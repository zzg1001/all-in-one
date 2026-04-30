<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { agentsApi, type Agent } from '@/api'
import Toast from '@/components/Toast.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

// 组件引用
const toast = ref<InstanceType<typeof Toast> | null>(null)
const confirmDialog = ref<InstanceType<typeof ConfirmDialog> | null>(null)

// 状态
const agents = ref<Agent[]>([])
const loading = ref(false)
const searchQuery = ref('')

// 编辑弹窗
const showEditModal = ref(false)
const editingAgent = ref<Partial<Agent> | null>(null)
const isCreating = ref(false)

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
  draft: agents.value.filter(a => a.status === 'draft').length,
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

// 打开创建弹窗
const openCreate = () => {
  isCreating.value = true
  editingAgent.value = {
    name: '',
    description: '',
    icon: '🤖',
    category: '通用助手',
    system_prompt: '',
    model: 'claude-opus-4-5',
    temperature: 0.7,
    max_tokens: 4096,
    status: 'draft'
  }
  showEditModal.value = true
}

// 打开编辑弹窗
const openEdit = (agent: Agent) => {
  isCreating.value = false
  editingAgent.value = { ...agent }
  showEditModal.value = true
}

// 保存 Agent
const saveAgent = async () => {
  if (!editingAgent.value || !editingAgent.value.name) {
    toast.value?.warning('请输入 Agent 名称')
    return
  }

  try {
    if (isCreating.value) {
      await agentsApi.create(editingAgent.value as any)
      toast.value?.success('创建成功')
    } else {
      await agentsApi.update(editingAgent.value.id!, editingAgent.value as any)
      toast.value?.success('保存成功')
    }
    showEditModal.value = false
    loadAgents()
  } catch (e) {
    toast.value?.error('保存失败: ' + e)
  }
}

// 删除 Agent
const deleteAgent = async (agent: Agent) => {
  const confirmed = await confirmDialog.value?.confirm(
    `确定要删除 Agent「${agent.name}」吗？此操作不可恢复`,
    { title: '删除 Agent', type: 'danger' }
  )
  if (!confirmed) return

  try {
    await agentsApi.delete(agent.id)
    agents.value = agents.value.filter(a => a.id !== agent.id)
    toast.value?.success('删除成功')
  } catch (e) {
    toast.value?.error('删除失败: ' + e)
  }
}

// 切换状态
const toggleStatus = async (agent: Agent) => {
  const newStatus = agent.status === 'active' ? 'draft' : 'active'
  try {
    await agentsApi.update(agent.id, { status: newStatus })
    const idx = agents.value.findIndex(a => a.id === agent.id)
    if (idx >= 0) {
      agents.value[idx] = { ...agents.value[idx], status: newStatus }
    }
    toast.value?.success(newStatus === 'active' ? '已发布' : '已设为草稿')
  } catch (e) {
    toast.value?.error('更新状态失败: ' + e)
  }
}

// 图标选择
const icons = ['🤖', '🧠', '💡', '🎯', '🚀', '⚡', '🔧', '📊', '📝', '💻', '🌐', '🔍', '✨', '🎨', '📚', '💼', '🏢', '👔', '📈', '🛒']
const categories = ['通用助手', 'HR', '销售', '采购', '行政', '财务', '技术', '自定义']

onMounted(() => {
  loadAgents()
})
</script>

<template>
  <Toast ref="toast" />
  <ConfirmDialog ref="confirmDialog" />
  <div class="agents-page">
    <!-- 头部 -->
    <div class="page-header">
      <div class="header-info">
        <h2>Agent 管理</h2>
        <p class="page-desc">创建和管理智能体</p>
      </div>
      <div class="header-actions">
        <div class="search-box">
          <svg class="search-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
          </svg>
          <input v-model="searchQuery" type="text" placeholder="搜索 Agent..." />
        </div>
        <button class="btn-primary" @click="openCreate">
          <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"/></svg>
          新建 Agent
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon blue"><span>🤖</span></div>
        <div class="stat-content">
          <span class="stat-value">{{ stats.total }}</span>
          <span class="stat-label">Agent 总数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green"><span>✓</span></div>
        <div class="stat-content">
          <span class="stat-value">{{ stats.active }}</span>
          <span class="stat-label">已发布</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon orange"><span>📝</span></div>
        <div class="stat-content">
          <span class="stat-value">{{ stats.draft }}</span>
          <span class="stat-label">草稿</span>
        </div>
      </div>
    </div>

    <!-- 表格 -->
    <div class="table-container">
      <div class="table-header">
        <div class="th-cell th-name">Agent</div>
        <div class="th-cell th-category">分类</div>
        <div class="th-cell th-model">模型</div>
        <div class="th-cell th-status">状态</div>
        <div class="th-cell th-usage">使用次数</div>
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
            <div class="td-cell td-name">
              <div class="agent-info">
                <span class="agent-icon">{{ agent.icon || '🤖' }}</span>
                <div class="agent-details">
                  <span class="agent-name">{{ agent.name }}</span>
                  <span class="agent-desc">{{ agent.description?.slice(0, 40) }}{{ agent.description?.length > 40 ? '...' : '' }}</span>
                </div>
              </div>
            </div>
            <div class="td-cell td-category">
              <span class="category-tag">{{ agent.category || '通用' }}</span>
            </div>
            <div class="td-cell td-model">
              <span class="model-tag">{{ agent.model?.split('-').slice(-2).join('-') || 'opus' }}</span>
            </div>
            <div class="td-cell td-status">
              <button class="status-toggle" :class="agent.status" @click="toggleStatus(agent)">
                {{ agent.status === 'active' ? '已发布' : '草稿' }}
              </button>
            </div>
            <div class="td-cell td-usage">
              <span class="usage-count">{{ agent.usage_count || 0 }}</span>
            </div>
            <div class="td-cell td-actions">
              <button class="btn-icon" title="编辑" @click="openEdit(agent)">
                <svg viewBox="0 0 20 20" fill="currentColor"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"/></svg>
              </button>
              <button class="btn-icon danger" title="删除" @click="deleteAgent(agent)">
                <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
              </button>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ isCreating ? '新建 Agent' : '编辑 Agent' }}</h3>
          <button class="close-btn" @click="showEditModal = false">&times;</button>
        </div>

        <div class="modal-body" v-if="editingAgent">
          <div class="form-group">
            <label>图标</label>
            <div class="icon-picker">
              <button
                v-for="icon in icons"
                :key="icon"
                class="icon-btn"
                :class="{ active: editingAgent.icon === icon }"
                @click="editingAgent.icon = icon"
              >
                {{ icon }}
              </button>
            </div>
          </div>

          <div class="form-group">
            <label>名称 *</label>
            <input v-model="editingAgent.name" type="text" placeholder="例如：HR 助手" />
          </div>

          <div class="form-group">
            <label>描述</label>
            <textarea v-model="editingAgent.description" rows="2" placeholder="简短描述这个 Agent 的功能"></textarea>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>分类</label>
              <select v-model="editingAgent.category">
                <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>模型</label>
              <select v-model="editingAgent.model">
                <option value="claude-opus-4-5">Claude Opus 4.5</option>
                <option value="claude-sonnet-4">Claude Sonnet 4</option>
                <option value="claude-haiku">Claude Haiku</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label>系统提示词</label>
            <textarea v-model="editingAgent.system_prompt" rows="4" placeholder="定义 Agent 的角色和行为..."></textarea>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>温度 ({{ editingAgent.temperature }})</label>
              <input type="range" v-model.number="editingAgent.temperature" min="0" max="1" step="0.1" />
            </div>
            <div class="form-group">
              <label>最大 Token</label>
              <input v-model.number="editingAgent.max_tokens" type="number" min="256" max="8192" />
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-cancel" @click="showEditModal = false">取消</button>
          <button class="btn-save" @click="saveAgent">保存</button>
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

.btn-primary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-primary svg {
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

.stat-icon.blue { background: #e0f2fe; }
.stat-icon.green { background: #dcfce7; }
.stat-icon.orange { background: #fef3c7; }

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
.th-name { flex: 2.5; }
.th-category { flex: 1; }
.th-model { flex: 1; }
.th-status { flex: 0.8; }
.th-usage { flex: 0.8; }
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
.td-name { flex: 2.5; }
.td-category { flex: 1; }
.td-model { flex: 1; }
.td-status { flex: 0.8; }
.td-usage { flex: 0.8; }
.td-actions { flex: 1; text-align: right; display: flex; justify-content: flex-end; gap: 8px; }

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

.category-tag, .model-tag {
  padding: 4px 10px;
  background: #f1f5f9;
  border-radius: 4px;
  font-size: 12px;
  color: #475569;
}

.status-toggle {
  padding: 4px 10px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.status-toggle.active {
  background: #dcfce7;
  color: #16a34a;
}

.status-toggle.draft {
  background: #fef3c7;
  color: #d97706;
}

.usage-count {
  font-size: 14px;
  color: #64748b;
}

.btn-icon {
  width: 32px;
  height: 32px;
  border: none;
  background: #f1f5f9;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  transition: all 0.2s;
}

.btn-icon:hover {
  background: #e2e8f0;
  color: #3b82f6;
}

.btn-icon.danger:hover {
  background: #fee2e2;
  color: #dc2626;
}

.btn-icon svg {
  width: 16px;
  height: 16px;
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

/* 弹窗 */
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
  width: 600px;
  max-height: 85vh;
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

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.form-group input[type="text"],
.form-group input[type="number"],
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: #3b82f6;
}

.form-group textarea {
  resize: vertical;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-row .form-group {
  flex: 1;
}

.icon-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.icon-btn {
  width: 40px;
  height: 40px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  background: white;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.2s;
}

.icon-btn:hover {
  border-color: #3b82f6;
}

.icon-btn.active {
  border-color: #3b82f6;
  background: #eff6ff;
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
