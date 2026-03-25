<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

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
  capabilities: string[]
  tools: string[]
  createdAt: string
  usageCount: number
}

const searchQuery = ref('')
const selectedCategory = ref('all')
const categories = ['all', '通用助手', '数据处理', '代码生成', '文档处理', '图像处理', '自定义']

const agents = ref<Agent[]>([
  {
    id: '1',
    name: '智能写作助手',
    description: '帮助撰写各类文档、邮件、报告，支持多种风格和格式',
    icon: '✍️',
    category: '通用助手',
    author: 'System',
    version: '1.0.0',
    status: 'active',
    capabilities: ['文档撰写', '内容优化', '格式转换'],
    tools: ['write', 'read', 'format'],
    createdAt: '2026-03-01',
    usageCount: 1520
  },
  {
    id: '2',
    name: '数据分析专家',
    description: '分析 Excel、CSV 数据，生成可视化图表和分析报告',
    icon: '📊',
    category: '数据处理',
    author: 'System',
    version: '1.2.0',
    status: 'active',
    capabilities: ['数据清洗', '统计分析', '图表生成'],
    tools: ['excel-to-json', 'json-to-excel', 'chart'],
    createdAt: '2026-02-15',
    usageCount: 892
  },
  {
    id: '3',
    name: '代码生成器',
    description: '根据需求描述生成代码，支持多种编程语言',
    icon: '💻',
    category: '代码生成',
    author: 'System',
    version: '2.0.0',
    status: 'active',
    capabilities: ['代码生成', '代码审查', '单元测试'],
    tools: ['code', 'bash', 'test'],
    createdAt: '2026-01-20',
    usageCount: 2341
  },
  {
    id: '4',
    name: 'PDF 处理专家',
    description: '提取 PDF 内容、转换格式、合并拆分文档',
    icon: '📄',
    category: '文档处理',
    author: 'Community',
    version: '1.0.0',
    status: 'active',
    capabilities: ['PDF提取', '格式转换', '文档合并'],
    tools: ['pdf-reader', 'pdf-writer'],
    createdAt: '2026-03-10',
    usageCount: 456
  },
  {
    id: '5',
    name: '图像描述生成',
    description: '分析图像内容，生成详细的文字描述',
    icon: '🖼️',
    category: '图像处理',
    author: 'Community',
    version: '1.1.0',
    status: 'active',
    capabilities: ['图像识别', '内容描述', '标签生成'],
    tools: ['image-read', 'vision'],
    createdAt: '2026-02-28',
    usageCount: 678
  },
  {
    id: '6',
    name: '邮件助手',
    description: '智能撰写、回复邮件，支持多语言翻译',
    icon: '📧',
    category: '通用助手',
    author: 'System',
    version: '1.0.0',
    status: 'draft',
    capabilities: ['邮件撰写', '自动回复', '翻译'],
    tools: ['write', 'translate'],
    createdAt: '2026-03-18',
    usageCount: 0
  }
])

const filteredAgents = computed(() => {
  return agents.value.filter(agent => {
    const matchSearch = !searchQuery.value ||
      agent.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      agent.description.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchCategory = selectedCategory.value === 'all' || agent.category === selectedCategory.value
    return matchSearch && matchCategory
  })
})

const stats = computed(() => ({
  total: agents.value.length,
  active: agents.value.filter(a => a.status === 'active').length,
  totalUsage: agents.value.reduce((sum, a) => sum + a.usageCount, 0)
}))

const createAgent = () => router.push('/agent-studio')
const useAgent = (agent: Agent) => router.push({ path: '/', query: { tab: 'agent', agentId: agent.id } })
const editAgent = (agent: Agent) => router.push({ path: '/agent-studio', query: { id: agent.id } })

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
          </div>
          <p class="subtitle">发现、使用和管理各种智能 Agent</p>
        </div>
        <button class="btn-create" @click="createAgent">
          <span class="btn-icon">+</span>
          <span>创建 Agent</span>
          <span class="btn-glow"></span>
        </button>
      </div>

      <!-- 功能说明卡片 -->
      <div class="intro-cards">
        <div class="intro-card">
          <span class="intro-icon">💡</span>
          <div class="intro-content">
            <h4>什么是 Agent?</h4>
            <p>Agent 是具有特定能力的 AI 助手，可以使用工具、记忆对话、执行复杂任务</p>
          </div>
        </div>
        <div class="intro-card">
          <span class="intro-icon">🔧</span>
          <div class="intro-content">
            <h4>如何使用?</h4>
            <p>选择一个 Agent 点击「使用」进入对话，或点击编辑自定义配置</p>
          </div>
        </div>
        <div class="intro-card">
          <span class="intro-icon">⚡</span>
          <div class="intro-content">
            <h4>创建自己的</h4>
            <p>点击「创建 Agent」定制专属助手，配置工具和系统提示词</p>
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
        >
          <div class="card-glow"></div>
          <div class="card-content">
            <div class="card-header">
              <div class="agent-avatar">
                <span class="avatar-icon">{{ agent.icon }}</span>
                <span class="avatar-ring"></span>
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
                <span>{{ agent.usageCount }}</span>
              </div>
            </div>

            <div class="capabilities">
              <span v-for="cap in agent.capabilities.slice(0, 3)" :key="cap" class="cap-tag">
                {{ cap }}
              </span>
            </div>

            <div class="card-actions">
              <button class="btn-use" @click="useAgent(agent)">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/>
                </svg>
                使用
              </button>
              <button class="btn-edit" @click="editAgent(agent)">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"/>
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
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

.agents-view {
  position: fixed;
  top: 0;
  left: 60px;
  right: 0;
  bottom: 0;
  background: #0a0a0f;
  color: #e4e4e7;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 装饰背景 */
.bg-decoration {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.bg-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
}

.blob-1 {
  width: 600px;
  height: 600px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  top: -200px;
  right: -100px;
}

.blob-2 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #06b6d4, #3b82f6);
  bottom: -100px;
  left: 20%;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(99, 102, 241, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(99, 102, 241, 0.03) 1px, transparent 1px);
  background-size: 60px 60px;
}

/* 主内容 */
.page-content {
  position: relative;
  z-index: 1;
  flex: 1;
  overflow-y: auto;
  padding: 0 28px 40px;
}

/* 头部 */
.page-header {
  flex-shrink: 0;
  padding: 20px 28px 0;
  background: #0a0a0f;
  position: relative;
  z-index: 10;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

/* 功能说明卡片 */
.intro-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.intro-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(139, 92, 246, 0.05));
  border: 1px solid rgba(99, 102, 241, 0.15);
  border-radius: 10px;
}

.intro-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.intro-content h4 {
  font-size: 12px;
  font-weight: 600;
  color: #e4e4e7;
  margin: 0 0 4px;
}

.intro-content p {
  font-size: 11px;
  color: #71717a;
  margin: 0;
  line-height: 1.4;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}

.title-icon {
  font-size: 28px;
  filter: drop-shadow(0 0 15px rgba(99, 102, 241, 0.5));
}

.header-info h1 {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 24px;
  font-weight: 700;
  margin: 0;
  background: linear-gradient(135deg, #fff, #a5b4fc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  font-size: 13px;
  color: #71717a;
  margin: 0;
}

.btn-create {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 10px;
  color: white;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn-create:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(99, 102, 241, 0.4);
}

.btn-icon {
  font-size: 16px;
  font-weight: 400;
}

.btn-glow {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, transparent, rgba(255,255,255,0.1), transparent);
  transform: translateX(-100%);
  transition: transform 0.5s;
}

.btn-create:hover .btn-glow {
  transform: translateX(100%);
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
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  backdrop-filter: blur(12px);
  transition: all 0.3s;
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(99, 102, 241, 0.3);
  transform: translateY(-2px);
}

.stat-icon {
  font-size: 20px;
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
  font-family: 'Space Grotesk', sans-serif;
  font-size: 18px;
  font-weight: 700;
  color: #fff;
}

.stat-label {
  font-size: 11px;
  color: #71717a;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 筛选区 */
.filter-section {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-top: 16px;
  padding-bottom: 16px;
  flex-wrap: wrap;
}

.search-wrapper {
  position: relative;
  flex: 1;
  max-width: 300px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: #52525b;
}

.search-input {
  width: 100%;
  padding: 10px 12px 10px 36px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  color: #e4e4e7;
  font-size: 13px;
  outline: none;
  transition: all 0.2s;
}

.search-input::placeholder {
  color: #52525b;
}

.search-input:focus {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(99, 102, 241, 0.5);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.category-pills {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.pill {
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  color: #a1a1aa;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.pill:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #e4e4e7;
}

.pill.active {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2));
  border-color: rgba(99, 102, 241, 0.5);
  color: #a5b4fc;
}

/* Agent 网格 */
.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

.agent-card {
  position: relative;
  border-radius: 14px;
  overflow: hidden;
  animation: card-in 0.5s ease-out backwards;
  animation-delay: var(--delay);
}

@keyframes card-in {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.card-glow {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), transparent);
  opacity: 0;
  transition: opacity 0.3s;
}

.agent-card:hover .card-glow {
  opacity: 1;
}

.card-content {
  position: relative;
  padding: 16px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  transition: all 0.3s;
}

.agent-card:hover .card-content {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(99, 102, 241, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.3);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.agent-avatar {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-icon {
  font-size: 22px;
  position: relative;
  z-index: 1;
}

.avatar-ring {
  position: absolute;
  inset: 0;
  border: 2px solid rgba(99, 102, 241, 0.3);
  border-radius: 12px;
  animation: ring-pulse 3s ease-in-out infinite;
}

@keyframes ring-pulse {
  0%, 100% { transform: scale(1); opacity: 0.5; }
  50% { transform: scale(1.1); opacity: 0.8; }
}

.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-active {
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.status-draft {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.status-deprecated {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.agent-name {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 6px;
}

.agent-desc {
  font-size: 12px;
  color: #71717a;
  margin: 0 0 12px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.agent-meta {
  display: flex;
  gap: 14px;
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #52525b;
}

.meta-item svg {
  width: 12px;
  height: 12px;
}

.capabilities {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.cap-tag {
  padding: 4px 8px;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 6px;
  font-size: 10px;
  color: #a5b4fc;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.btn-use {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 14px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-use:hover {
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.4);
  transform: translateY(-1px);
}

.btn-use svg {
  width: 14px;
  height: 14px;
}

.btn-edit {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #a1a1aa;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-edit:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.btn-edit svg {
  width: 14px;
  height: 14px;
}

/* 空状态 */
.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 80px 20px;
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
  border: 2px solid rgba(99, 102, 241, 0.2);
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
  font-family: 'Space Grotesk', sans-serif;
  font-size: 20px;
  color: #e4e4e7;
  margin: 0 0 8px;
}

.empty-state p {
  color: #71717a;
  margin: 0 0 24px;
}

.btn-create-empty {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 10px;
  color: white;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-create-empty:hover {
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
}
</style>
