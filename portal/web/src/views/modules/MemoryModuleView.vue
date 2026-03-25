<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 基础配置
const config = reactive({
  enabled: true,
  shortTermCapacity: 20,
  longTermEnabled: true,
  vectorStore: 'chromadb',
  embeddingModel: 'text-embedding-3-small',
  retrievalTopK: 5,
  similarityThreshold: 0.75
})

// 当前编辑的 Tab
const activeTab = ref<'rules' | 'knowledge' | 'prompts' | 'settings'>('rules')

// 记忆规则
const memoryRules = ref([
  { id: '1', name: '用户偏好', pattern: '用户喜欢|用户偏好|用户习惯', action: 'long_term', priority: 'high', enabled: true },
  { id: '2', name: '任务结果', pattern: '执行成功|执行失败|任务完成', action: 'short_term', priority: 'medium', enabled: true },
  { id: '3', name: '敏感信息', pattern: '密码|token|key|secret', action: 'never_store', priority: 'high', enabled: true },
  { id: '4', name: '临时数据', pattern: '临时|暂存|缓存', action: 'auto_expire', priority: 'low', enabled: false }
])

// 编辑规则弹窗
const showRuleEditor = ref(false)
const editingRule = reactive({
  id: '',
  name: '',
  pattern: '',
  action: 'short_term',
  priority: 'medium',
  enabled: true
})

// 知识库条目
const knowledgeEntries = ref([
  { id: 'k1', title: '项目技术栈', content: '本项目使用 Vue 3 + TypeScript + FastAPI + MySQL 技术栈', category: 'project', updatedAt: '2026-03-22' },
  { id: 'k2', title: 'API 规范', content: 'API 遵循 RESTful 设计，返回 JSON 格式，错误码统一使用 HTTP 状态码', category: 'api', updatedAt: '2026-03-21' },
  { id: 'k3', title: '用户角色定义', content: '系统有 admin、developer、analyst、viewer 四种角色', category: 'business', updatedAt: '2026-03-20' }
])

// 编辑知识条目
const showKnowledgeEditor = ref(false)
const editingKnowledge = reactive({
  id: '',
  title: '',
  content: '',
  category: 'general'
})

// 提示词模板
const promptTemplates = ref({
  summarization: `请将以下对话内容总结为简洁的记忆条目：

对话内容：
{conversation}

要求：
1. 提取关键信息和用户意图
2. 保留重要的上下文
3. 使用第三人称描述
4. 不超过 100 字`,

  extraction: `从以下文本中提取需要记忆的信息：

文本：
{text}

提取规则：
- 用户的明确偏好和习惯
- 重要的任务结果和反馈
- 需要长期记住的知识点

输出格式：JSON 数组`,

  retrieval: `根据当前查询，从记忆库中检索相关信息：

查询：{query}
上下文：{context}

请返回最相关的记忆条目 ID 列表。`
})

// 记忆统计
const memoryStats = ref({
  shortTermCount: 15,
  longTermCount: 1247,
  totalSize: '128 MB',
  lastAccess: '2 分钟前'
})

const vectorStores = [
  { id: 'chromadb', name: 'ChromaDB', desc: '轻量级本地向量库' },
  { id: 'pinecone', name: 'Pinecone', desc: '云端高性能向量库' },
  { id: 'milvus', name: 'Milvus', desc: '分布式向量数据库' },
  { id: 'qdrant', name: 'Qdrant', desc: '高效向量搜索引擎' }
]

const embeddingModels = [
  { id: 'text-embedding-3-small', name: 'OpenAI Small', dim: 1536 },
  { id: 'text-embedding-3-large', name: 'OpenAI Large', dim: 3072 },
  { id: 'bge-large-zh', name: 'BGE 中文', dim: 1024 }
]

const ruleActions = [
  { id: 'long_term', name: '存入长期记忆' },
  { id: 'short_term', name: '存入短期记忆' },
  { id: 'auto_expire', name: '自动过期' },
  { id: 'never_store', name: '永不存储' }
]

const priorities = [
  { id: 'high', name: '高', color: '#f87171' },
  { id: 'medium', name: '中', color: '#fbbf24' },
  { id: 'low', name: '低', color: '#4ade80' }
]

const categories = [
  { id: 'general', name: '通用' },
  { id: 'project', name: '项目' },
  { id: 'api', name: 'API' },
  { id: 'business', name: '业务' },
  { id: 'user', name: '用户' }
]

// 操作方法
const openRuleEditor = (rule?: typeof editingRule) => {
  if (rule && rule.id) {
    Object.assign(editingRule, rule)
  } else {
    editingRule.id = ''
    editingRule.name = ''
    editingRule.pattern = ''
    editingRule.action = 'short_term'
    editingRule.priority = 'medium'
    editingRule.enabled = true
  }
  showRuleEditor.value = true
}

const saveRule = () => {
  if (!editingRule.name || !editingRule.pattern) {
    alert('请填写规则名称和匹配模式')
    return
  }

  if (editingRule.id) {
    const index = memoryRules.value.findIndex(r => r.id === editingRule.id)
    if (index > -1) {
      memoryRules.value[index] = { ...editingRule }
    }
  } else {
    memoryRules.value.push({
      ...editingRule,
      id: 'rule-' + Date.now()
    })
  }
  showRuleEditor.value = false
}

const deleteRule = (id: string) => {
  if (confirm('确定删除此规则？')) {
    memoryRules.value = memoryRules.value.filter(r => r.id !== id)
  }
}

const toggleRule = (rule: typeof memoryRules.value[0]) => {
  rule.enabled = !rule.enabled
}

const openKnowledgeEditor = (entry?: typeof editingKnowledge) => {
  if (entry && entry.id) {
    Object.assign(editingKnowledge, entry)
  } else {
    editingKnowledge.id = ''
    editingKnowledge.title = ''
    editingKnowledge.content = ''
    editingKnowledge.category = 'general'
  }
  showKnowledgeEditor.value = true
}

const saveKnowledge = () => {
  if (!editingKnowledge.title || !editingKnowledge.content) {
    alert('请填写标题和内容')
    return
  }

  if (editingKnowledge.id) {
    const index = knowledgeEntries.value.findIndex(k => k.id === editingKnowledge.id)
    if (index > -1) {
      knowledgeEntries.value[index] = {
        ...editingKnowledge,
        updatedAt: new Date().toISOString().split('T')[0]
      }
    }
  } else {
    knowledgeEntries.value.push({
      ...editingKnowledge,
      id: 'k-' + Date.now(),
      updatedAt: new Date().toISOString().split('T')[0]
    })
  }
  showKnowledgeEditor.value = false
}

const deleteKnowledge = (id: string) => {
  if (confirm('确定删除此知识条目？')) {
    knowledgeEntries.value = knowledgeEntries.value.filter(k => k.id !== id)
  }
}

const getPriorityColor = (priority: string) => {
  return priorities.find(p => p.id === priority)?.color || '#71717a'
}

const getActionName = (action: string) => {
  return ruleActions.find(a => a.id === action)?.name || action
}

const getCategoryName = (category: string) => {
  return categories.find(c => c.id === category)?.name || category
}

const goBack = () => router.push('/architecture')
</script>

<template>
  <div class="module-view memory-module">
    <!-- 装饰背景 -->
    <div class="bg-decoration">
      <div class="bg-orb orb-1"></div>
      <div class="bg-orb orb-2"></div>
      <div class="bg-grid"></div>
    </div>

    <!-- 顶部 -->
    <header class="module-header">
      <div class="header-left">
        <button class="btn-back" @click="goBack">
          <svg viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd"/>
          </svg>
        </button>
        <div class="module-badge memory">
          <span>🧠</span>
        </div>
        <div class="header-title">
          <h1>Memory 记忆模块</h1>
          <p>自定义记忆规则、知识库、提示词模板</p>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn-primary">保存所有配置</button>
      </div>
    </header>

    <!-- Tab 导航 -->
    <div class="tab-nav">
      <button :class="['tab-btn', { active: activeTab === 'rules' }]" @click="activeTab = 'rules'">
        📜 记忆规则
      </button>
      <button :class="['tab-btn', { active: activeTab === 'knowledge' }]" @click="activeTab = 'knowledge'">
        📚 知识库
      </button>
      <button :class="['tab-btn', { active: activeTab === 'prompts' }]" @click="activeTab = 'prompts'">
        ✨ 提示词模板
      </button>
      <button :class="['tab-btn', { active: activeTab === 'settings' }]" @click="activeTab = 'settings'">
        ⚙️ 基础设置
      </button>
    </div>

    <!-- 主内容 -->
    <div class="module-content">
      <!-- 记忆规则 Tab -->
      <div v-show="activeTab === 'rules'" class="tab-content">
        <div class="content-header">
          <div class="header-info">
            <h2>记忆规则</h2>
            <p>定义什么信息需要记住、如何存储、何时过期</p>
          </div>
          <button class="btn-add" @click="openRuleEditor()">
            <span>+</span> 添加规则
          </button>
        </div>

        <div class="rules-list">
          <div v-for="rule in memoryRules" :key="rule.id" :class="['rule-card', { disabled: !rule.enabled }]">
            <div class="rule-header">
              <div class="rule-title">
                <span class="rule-priority" :style="{ background: getPriorityColor(rule.priority) }"></span>
                <span class="rule-name">{{ rule.name }}</span>
              </div>
              <div class="rule-actions">
                <button class="action-btn" @click="openRuleEditor(rule)" title="编辑">✏️</button>
                <button class="action-btn" @click="toggleRule(rule)" :title="rule.enabled ? '禁用' : '启用'">
                  {{ rule.enabled ? '🟢' : '⚫' }}
                </button>
                <button class="action-btn danger" @click="deleteRule(rule.id)" title="删除">🗑️</button>
              </div>
            </div>
            <div class="rule-body">
              <div class="rule-pattern">
                <span class="label">匹配模式:</span>
                <code>{{ rule.pattern }}</code>
              </div>
              <div class="rule-meta">
                <span class="rule-action">{{ getActionName(rule.action) }}</span>
                <span class="rule-priority-text">优先级: {{ priorities.find(p => p.id === rule.priority)?.name }}</span>
              </div>
            </div>
          </div>

          <div v-if="memoryRules.length === 0" class="empty-state">
            <span>📭</span>
            <p>暂无记忆规则，点击上方按钮添加</p>
          </div>
        </div>
      </div>

      <!-- 知识库 Tab -->
      <div v-show="activeTab === 'knowledge'" class="tab-content">
        <div class="content-header">
          <div class="header-info">
            <h2>知识库</h2>
            <p>预置的知识条目，Agent 可以直接检索使用</p>
          </div>
          <button class="btn-add" @click="openKnowledgeEditor()">
            <span>+</span> 添加知识
          </button>
        </div>

        <div class="knowledge-list">
          <div v-for="entry in knowledgeEntries" :key="entry.id" class="knowledge-card">
            <div class="knowledge-header">
              <span class="knowledge-category">{{ getCategoryName(entry.category) }}</span>
              <span class="knowledge-date">{{ entry.updatedAt }}</span>
            </div>
            <h3 class="knowledge-title">{{ entry.title }}</h3>
            <p class="knowledge-content">{{ entry.content }}</p>
            <div class="knowledge-actions">
              <button class="action-btn" @click="openKnowledgeEditor(entry)">编辑</button>
              <button class="action-btn danger" @click="deleteKnowledge(entry.id)">删除</button>
            </div>
          </div>

          <div v-if="knowledgeEntries.length === 0" class="empty-state">
            <span>📭</span>
            <p>暂无知识条目，点击上方按钮添加</p>
          </div>
        </div>
      </div>

      <!-- 提示词模板 Tab -->
      <div v-show="activeTab === 'prompts'" class="tab-content">
        <div class="content-header">
          <div class="header-info">
            <h2>提示词模板</h2>
            <p>自定义记忆相关的 AI 提示词</p>
          </div>
        </div>

        <div class="prompts-list">
          <div class="prompt-card">
            <div class="prompt-header">
              <h3>📝 记忆总结提示词</h3>
              <p>用于将对话内容总结为记忆条目</p>
            </div>
            <textarea
              v-model="promptTemplates.summarization"
              class="prompt-editor"
              rows="10"
              placeholder="输入记忆总结提示词..."
            ></textarea>
            <div class="prompt-hints">
              <span class="hint">可用变量: <code>{conversation}</code></span>
            </div>
          </div>

          <div class="prompt-card">
            <div class="prompt-header">
              <h3>🔍 信息提取提示词</h3>
              <p>用于从文本中提取需要记忆的信息</p>
            </div>
            <textarea
              v-model="promptTemplates.extraction"
              class="prompt-editor"
              rows="10"
              placeholder="输入信息提取提示词..."
            ></textarea>
            <div class="prompt-hints">
              <span class="hint">可用变量: <code>{text}</code></span>
            </div>
          </div>

          <div class="prompt-card">
            <div class="prompt-header">
              <h3>🎯 记忆检索提示词</h3>
              <p>用于从记忆库检索相关信息</p>
            </div>
            <textarea
              v-model="promptTemplates.retrieval"
              class="prompt-editor"
              rows="8"
              placeholder="输入记忆检索提示词..."
            ></textarea>
            <div class="prompt-hints">
              <span class="hint">可用变量: <code>{query}</code> <code>{context}</code></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 基础设置 Tab -->
      <div v-show="activeTab === 'settings'" class="tab-content">
        <div class="settings-grid">
          <div class="settings-section">
            <h3>存储配置</h3>

            <div class="setting-item">
              <div class="setting-label">
                <span>启用记忆</span>
                <span class="setting-desc">开启后 Agent 将记住历史对话</span>
              </div>
              <label class="toggle-switch">
                <input v-model="config.enabled" type="checkbox" />
                <span class="toggle-track"></span>
              </label>
            </div>

            <div class="setting-item">
              <div class="setting-label">
                <span>短期记忆容量</span>
                <span class="setting-value">{{ config.shortTermCapacity }} 轮对话</span>
              </div>
              <input v-model.number="config.shortTermCapacity" type="range" min="5" max="50" class="setting-slider" />
            </div>

            <div class="setting-item">
              <div class="setting-label">
                <span>长期记忆</span>
                <span class="setting-desc">持久化存储重要信息</span>
              </div>
              <label class="toggle-switch">
                <input v-model="config.longTermEnabled" type="checkbox" />
                <span class="toggle-track"></span>
              </label>
            </div>
          </div>

          <div class="settings-section">
            <h3>向量存储</h3>

            <div class="setting-item vertical">
              <div class="setting-label">
                <span>存储后端</span>
              </div>
              <div class="option-cards">
                <div
                  v-for="store in vectorStores"
                  :key="store.id"
                  :class="['option-card', { selected: config.vectorStore === store.id }]"
                  @click="config.vectorStore = store.id"
                >
                  <span class="option-name">{{ store.name }}</span>
                  <span class="option-desc">{{ store.desc }}</span>
                </div>
              </div>
            </div>

            <div class="setting-item vertical">
              <div class="setting-label">
                <span>Embedding 模型</span>
              </div>
              <select v-model="config.embeddingModel" class="setting-select">
                <option v-for="model in embeddingModels" :key="model.id" :value="model.id">
                  {{ model.name }} ({{ model.dim }}维)
                </option>
              </select>
            </div>
          </div>

          <div class="settings-section">
            <h3>检索配置</h3>

            <div class="setting-item">
              <div class="setting-label">
                <span>检索数量 (Top-K)</span>
                <span class="setting-value">{{ config.retrievalTopK }}</span>
              </div>
              <input v-model.number="config.retrievalTopK" type="range" min="1" max="20" class="setting-slider" />
            </div>

            <div class="setting-item">
              <div class="setting-label">
                <span>相似度阈值</span>
                <span class="setting-value">{{ config.similarityThreshold }}</span>
              </div>
              <input v-model.number="config.similarityThreshold" type="range" min="0.5" max="1" step="0.05" class="setting-slider" />
            </div>
          </div>

          <div class="settings-section stats">
            <h3>统计信息</h3>
            <div class="stats-grid">
              <div class="stat-item">
                <span class="stat-value">{{ memoryStats.shortTermCount }}</span>
                <span class="stat-label">短期记忆</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ memoryStats.longTermCount }}</span>
                <span class="stat-label">长期记忆</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ memoryStats.totalSize }}</span>
                <span class="stat-label">存储占用</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ memoryStats.lastAccess }}</span>
                <span class="stat-label">最近访问</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 规则编辑弹窗 -->
    <div v-if="showRuleEditor" class="modal-overlay" @click.self="showRuleEditor = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ editingRule.id ? '编辑规则' : '添加规则' }}</h3>
          <button class="modal-close" @click="showRuleEditor = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>规则名称</label>
            <input v-model="editingRule.name" type="text" placeholder="例如：用户偏好" />
          </div>
          <div class="form-group">
            <label>匹配模式 (正则表达式)</label>
            <input v-model="editingRule.pattern" type="text" placeholder="例如：用户喜欢|用户偏好" />
            <span class="form-hint">使用 | 分隔多个关键词</span>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>存储行为</label>
              <select v-model="editingRule.action">
                <option v-for="action in ruleActions" :key="action.id" :value="action.id">
                  {{ action.name }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>优先级</label>
              <select v-model="editingRule.priority">
                <option v-for="p in priorities" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
          </div>
          <div class="form-group checkbox">
            <label>
              <input v-model="editingRule.enabled" type="checkbox" />
              启用此规则
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showRuleEditor = false">取消</button>
          <button class="btn-save" @click="saveRule">保存</button>
        </div>
      </div>
    </div>

    <!-- 知识编辑弹窗 -->
    <div v-if="showKnowledgeEditor" class="modal-overlay" @click.self="showKnowledgeEditor = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ editingKnowledge.id ? '编辑知识' : '添加知识' }}</h3>
          <button class="modal-close" @click="showKnowledgeEditor = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>标题</label>
            <input v-model="editingKnowledge.title" type="text" placeholder="知识条目标题" />
          </div>
          <div class="form-group">
            <label>分类</label>
            <select v-model="editingKnowledge.category">
              <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>内容</label>
            <textarea v-model="editingKnowledge.content" rows="6" placeholder="详细内容..."></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showKnowledgeEditor = false">取消</button>
          <button class="btn-save" @click="saveKnowledge">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

.module-view {
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

.bg-decoration {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
}

.memory-module .orb-1 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.25), rgba(99, 102, 241, 0.15));
  top: -100px;
  right: 20%;
}

.memory-module .orb-2 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.2), rgba(139, 92, 246, 0.1));
  bottom: 10%;
  left: 10%;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(139, 92, 246, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(139, 92, 246, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
}

/* 头部 */
.module-header {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: rgba(10, 10, 15, 0.95);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(12px);
  position: relative;
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.btn-back {
  width: 32px;
  height: 32px;
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

.btn-back:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.btn-back svg {
  width: 16px;
  height: 16px;
}

.module-badge {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  font-size: 20px;
}

.module-badge.memory {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(168, 85, 247, 0.2));
  border: 1px solid rgba(139, 92, 246, 0.4);
  box-shadow: 0 0 20px rgba(139, 92, 246, 0.2);
}

.header-title h1 {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: #fff;
}

.header-title p {
  font-size: 12px;
  color: #71717a;
  margin: 4px 0 0;
}

.btn-primary {
  padding: 8px 16px;
  background: linear-gradient(135deg, #8b5cf6, #a855f7);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4);
  transform: translateY(-1px);
}

/* Tab 导航 */
.tab-nav {
  flex-shrink: 0;
  display: flex;
  gap: 4px;
  padding: 12px 24px;
  background: rgba(10, 10, 15, 0.8);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  position: relative;
  z-index: 5;
}

.tab-btn {
  padding: 10px 20px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  color: #71717a;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: #a1a1aa;
  background: rgba(255, 255, 255, 0.03);
}

.tab-btn.active {
  background: rgba(139, 92, 246, 0.15);
  border-color: rgba(139, 92, 246, 0.3);
  color: #c4b5fd;
}

/* 主内容 */
.module-content {
  flex: 1;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.tab-content {
  height: 100%;
  overflow-y: auto;
  padding: 20px 24px;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header-info h2 {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 4px;
  color: #fff;
}

.header-info p {
  font-size: 12px;
  color: #71717a;
  margin: 0;
}

.btn-add {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  background: linear-gradient(135deg, #8b5cf6, #a855f7);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-add:hover {
  box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4);
}

.btn-add span {
  font-size: 16px;
}

/* 规则列表 */
.rules-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rule-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s;
}

.rule-card:hover {
  border-color: rgba(139, 92, 246, 0.3);
}

.rule-card.disabled {
  opacity: 0.5;
}

.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.rule-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.rule-priority {
  width: 4px;
  height: 20px;
  border-radius: 2px;
}

.rule-name {
  font-size: 14px;
  font-weight: 600;
  color: #e4e4e7;
}

.rule-actions {
  display: flex;
  gap: 6px;
}

.action-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.action-btn.danger:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.4);
}

.rule-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rule-pattern {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rule-pattern .label {
  font-size: 11px;
  color: #71717a;
}

.rule-pattern code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #c4b5fd;
  background: rgba(139, 92, 246, 0.1);
  padding: 4px 10px;
  border-radius: 4px;
}

.rule-meta {
  display: flex;
  gap: 16px;
}

.rule-action {
  font-size: 11px;
  color: #a1a1aa;
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.rule-priority-text {
  font-size: 11px;
  color: #71717a;
}

/* 知识库列表 */
.knowledge-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.knowledge-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s;
}

.knowledge-card:hover {
  border-color: rgba(139, 92, 246, 0.3);
}

.knowledge-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.knowledge-category {
  font-size: 10px;
  padding: 3px 10px;
  background: rgba(139, 92, 246, 0.15);
  color: #c4b5fd;
  border-radius: 4px;
}

.knowledge-date {
  font-size: 11px;
  color: #52525b;
}

.knowledge-title {
  font-size: 14px;
  font-weight: 600;
  color: #e4e4e7;
  margin: 0 0 8px;
}

.knowledge-content {
  font-size: 12px;
  color: #a1a1aa;
  line-height: 1.6;
  margin: 0 0 12px;
}

.knowledge-actions {
  display: flex;
  gap: 8px;
}

.knowledge-actions .action-btn {
  width: auto;
  padding: 6px 12px;
  font-size: 11px;
  color: #a1a1aa;
}

/* 提示词列表 */
.prompts-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.prompt-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 18px;
}

.prompt-header {
  margin-bottom: 14px;
}

.prompt-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: #e4e4e7;
  margin: 0 0 4px;
}

.prompt-header p {
  font-size: 12px;
  color: #71717a;
  margin: 0;
}

.prompt-editor {
  width: 100%;
  padding: 14px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  color: #e4e4e7;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  line-height: 1.6;
  resize: vertical;
  outline: none;
}

.prompt-editor:focus {
  border-color: rgba(139, 92, 246, 0.5);
}

.prompt-hints {
  margin-top: 10px;
}

.hint {
  font-size: 11px;
  color: #71717a;
}

.hint code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #c4b5fd;
  background: rgba(139, 92, 246, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
  margin: 0 4px;
}

/* 设置 */
.settings-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.settings-section {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 18px;
}

.settings-section h3 {
  font-size: 13px;
  font-weight: 600;
  color: #a1a1aa;
  margin: 0 0 16px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-item.vertical {
  flex-direction: column;
  align-items: stretch;
  gap: 12px;
}

.setting-label {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.setting-label > span:first-child {
  font-size: 13px;
  font-weight: 500;
  color: #e4e4e7;
}

.setting-desc {
  font-size: 11px;
  color: #52525b;
}

.setting-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #c4b5fd;
}

.toggle-switch {
  position: relative;
  width: 44px;
  height: 24px;
  cursor: pointer;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-track {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  transition: all 0.3s;
}

.toggle-track::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  transition: all 0.3s;
}

.toggle-switch input:checked + .toggle-track {
  background: linear-gradient(135deg, #8b5cf6, #a855f7);
}

.toggle-switch input:checked + .toggle-track::after {
  transform: translateX(20px);
}

.setting-slider {
  width: 140px;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  appearance: none;
  cursor: pointer;
}

.setting-slider::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  background: linear-gradient(135deg, #8b5cf6, #a855f7);
  border-radius: 50%;
  cursor: pointer;
}

.option-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.option-card {
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.option-card:hover {
  background: rgba(255, 255, 255, 0.04);
}

.option-card.selected {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.4);
}

.option-name {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #e4e4e7;
  margin-bottom: 2px;
}

.option-desc {
  display: block;
  font-size: 10px;
  color: #52525b;
}

.setting-select {
  width: 100%;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  color: #e4e4e7;
  font-size: 13px;
  cursor: pointer;
  outline: none;
}

.setting-select option {
  background: #18181b;
}

.settings-section.stats {
  grid-column: span 2;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 10px;
}

.stat-item .stat-value {
  display: block;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 4px;
}

.stat-item .stat-label {
  font-size: 11px;
  color: #71717a;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #71717a;
}

.empty-state span {
  font-size: 48px;
  display: block;
  margin-bottom: 12px;
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-content {
  width: 480px;
  max-width: 90%;
  background: #18181b;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #e4e4e7;
  margin: 0;
}

.modal-close {
  width: 28px;
  height: 28px;
  background: rgba(255, 255, 255, 0.05);
  border: none;
  border-radius: 6px;
  color: #a1a1aa;
  font-size: 18px;
  cursor: pointer;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #a1a1aa;
  margin-bottom: 8px;
}

.form-group input[type="text"],
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #e4e4e7;
  font-size: 13px;
  outline: none;
}

.form-group textarea {
  resize: vertical;
  font-family: inherit;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  border-color: rgba(139, 92, 246, 0.5);
}

.form-hint {
  display: block;
  font-size: 11px;
  color: #52525b;
  margin-top: 6px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.form-group.checkbox label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.form-group.checkbox input {
  width: 16px;
  height: 16px;
  accent-color: #8b5cf6;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.btn-cancel,
.btn-save {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #a1a1aa;
}

.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn-save {
  background: linear-gradient(135deg, #8b5cf6, #a855f7);
  border: none;
  color: white;
}

.btn-save:hover {
  box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4);
}

/* 滚动条 */
.tab-content::-webkit-scrollbar {
  width: 6px;
}

.tab-content::-webkit-scrollbar-track {
  background: transparent;
}

.tab-content::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}
</style>
