<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { agentsApi, skillsApi, type Skill } from '@/api'
import SkillCard from '@/components/skills/SkillCard.vue'
import AddSkillModal from '@/components/skills/AddSkillModal.vue'

const router = useRouter()
const route = useRoute()

const agent = reactive({
  id: '',
  name: '',
  description: '',
  icon: '🤖',
  category: '通用助手',
  systemPrompt: '',
  model: 'claude-opus-4-5',
  temperature: 0.7,
  maxTokens: 4096,
  tools: [] as string[],
  skills: [] as string[],
  memory: { enabled: true, type: 'conversation', maxHistory: 20 },
  reasoning: { enabled: true, style: 'step-by-step' }
})

const isLoading = ref(false)
const loadError = ref('')

// 从 API 加载的技能列表
const availableSkillsFromApi = ref<Skill[]>([])
const skillsLoading = ref(false)

// 技能管理相关状态
const showSkillModal = ref(false)
const skillModalMode = ref<'create' | 'upload'>('create')
const editingSkill = ref<Skill | null>(null)  // 编辑时传入的技能

// Toast 提示
const showToast = ref(false)
const toastMessage = ref('')
const showToastMessage = (message: string) => {
  toastMessage.value = message
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 3000)
}

// 加载技能列表
const loadSkills = async () => {
  skillsLoading.value = true
  try {
    const skills = await skillsApi.getAll()
    availableSkillsFromApi.value = skills
  } catch (error) {
    console.error('Failed to load skills:', error)
  } finally {
    skillsLoading.value = false
  }
}

// 打开创建技能弹窗
const openCreateModal = () => {
  editingSkill.value = null
  skillModalMode.value = 'create'
  showSkillModal.value = true
}

// 打开上传技能弹窗
const openUploadModal = () => {
  editingSkill.value = null
  skillModalMode.value = 'upload'
  showSkillModal.value = true
}

// 打开编辑技能弹窗
const openEditModal = (skill: Skill) => {
  editingSkill.value = skill
  skillModalMode.value = 'create'  // 编辑也用create模式（AI对话模式）
  showSkillModal.value = true
}

// 关闭技能弹窗
const closeSkillModal = () => {
  showSkillModal.value = false
  editingSkill.value = null
}

// 技能创建/编辑成功
const handleSkillSubmit = (data: any) => {
  const isEdit = !!editingSkill.value
  showSkillModal.value = false
  editingSkill.value = null
  loadSkills()
  showToastMessage(isEdit ? '技能修改成功' : '技能创建成功')
}

// 删除技能
const deleteSkill = async (index: number) => {
  const skill = availableSkillsFromApi.value[index]
  if (!skill) return

  if (!confirm(`确定要删除技能 "${skill.name}" 吗？`)) return

  try {
    await skillsApi.delete(skill.id)
    availableSkillsFromApi.value.splice(index, 1)
    showToastMessage('技能已删除')
  } catch (error: any) {
    console.error('Failed to delete skill:', error)
    showToastMessage('删除失败: ' + (error.message || '未知错误'))
  }
}

// 编辑技能（使用AddSkillModal）
const editSkill = (skill: Skill) => {
  // 上传的技能不可编辑
  if (skill.author === 'uploaded') {
    showToastMessage('上传的技能不可编辑')
    return
  }
  openEditModal(skill)
}

const icons = ['🤖', '🧠', '💡', '🎯', '🚀', '⚡', '🔧', '📊', '📝', '💻', '🌐', '🔍', '✨', '🎨', '📚']
const showIconPicker = ref(false)
const categories = ['通用助手', '数据处理', '代码生成', '文档处理', '图像处理', '自定义']

const models = [
  { id: 'claude-opus-4-5', name: 'Claude Opus 4.5', desc: '最强大，适合复杂任务', badge: 'PRO' },
  { id: 'claude-sonnet-4', name: 'Claude Sonnet 4', desc: '平衡性能与速度', badge: '' },
  { id: 'claude-haiku', name: 'Claude Haiku', desc: '快速响应，适合简单任务', badge: 'FAST' }
]

const isGenerating = ref(false)
const generatingField = ref('')
const activeTab = ref<'basic' | 'prompt' | 'tools' | 'advanced'>('basic')

const toggleSkill = (skillId: string) => {
  const index = agent.skills.indexOf(skillId)
  if (index > -1) {
    agent.skills.splice(index, 1)
  } else {
    agent.skills.push(skillId)
  }
}

const generatePrompt = async () => {
  if (!agent.name || !agent.description) {
    alert('请先填写 Agent 名称和描述')
    return
  }
  isGenerating.value = true
  generatingField.value = 'systemPrompt'
  await new Promise(resolve => setTimeout(resolve, 1500))
  agent.systemPrompt = `你是${agent.name}，一个专业的 AI 助手。

## 角色定位
${agent.description}

## 工作原则
1. 始终保持专业、友好的态度
2. 给出清晰、结构化的回答
3. 在不确定时主动询问澄清
4. 注重用户隐私和数据安全

## 输出格式
- 使用清晰的标题和列表
- 代码使用合适的语法高亮
- 复杂内容分步骤说明`
  isGenerating.value = false
  generatingField.value = ''
}

const generateDescription = async () => {
  if (!agent.name) {
    alert('请先填写 Agent 名称')
    return
  }
  isGenerating.value = true
  generatingField.value = 'description'
  await new Promise(resolve => setTimeout(resolve, 1000))
  agent.description = `一个基于 ${agent.name} 的智能助手，能够帮助用户高效完成相关任务，提供专业的建议和解决方案。`
  isGenerating.value = false
  generatingField.value = ''
}


const saveAgent = async () => {
  if (!agent.name) {
    alert('请填写 Agent 名称')
    return
  }

  try {
    const data = {
      name: agent.name,
      description: agent.description,
      icon: agent.icon,
      category: agent.category,
      system_prompt: agent.systemPrompt,
      model: agent.model,
      temperature: agent.temperature,
      max_tokens: agent.maxTokens,
      tools: agent.tools,
      skills: agent.skills,
      memory: {
        enabled: agent.memory.enabled,
        type: agent.memory.type,
        max_history: agent.memory.maxHistory
      },
      reasoning: agent.reasoning
    }

    if (agent.id) {
      // 更新
      await agentsApi.update(agent.id, data)
    } else {
      // 创建
      await agentsApi.create(data)
    }
    alert('Agent 保存成功！')
    router.push('/agents')
  } catch (error: any) {
    alert('保存失败: ' + (error.message || '未知错误'))
  }
}

const goBack = () => router.push('/agents')
const testAgent = () => router.push({ path: '/', query: { tab: 'agent', agentId: agent.id, agent: agent.name } })

// 加载 Agent 数据
const loadAgent = async (id: string) => {
  isLoading.value = true
  loadError.value = ''
  try {
    const data = await agentsApi.getById(id)
    agent.id = data.id
    agent.name = data.name
    agent.description = data.description || ''
    agent.icon = data.icon || '🤖'
    agent.category = data.category || '通用助手'
    agent.systemPrompt = data.system_prompt || ''
    agent.model = data.model || 'claude-opus-4-5'
    agent.temperature = data.temperature ?? 0.7
    agent.maxTokens = data.max_tokens || 4096
    agent.tools = data.tools || []
    agent.skills = data.skills || []
    agent.memory = {
      enabled: data.memory?.enabled ?? true,
      type: data.memory?.type || 'conversation',
      maxHistory: data.memory?.max_history || 20
    }
    agent.reasoning = {
      enabled: data.reasoning?.enabled ?? true,
      style: data.reasoning?.style || 'step-by-step'
    }
  } catch (error: any) {
    loadError.value = error.message || '加载失败'
    console.error('Failed to load agent:', error)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  // 加载技能列表
  loadSkills()

  // 如果有 ID，加载 Agent 数据
  const agentId = route.query.id as string
  if (agentId) {
    loadAgent(agentId)
  }
})
</script>

<template>
  <div class="agent-studio">
    <!-- 装饰背景 -->
    <div class="bg-decoration">
      <div class="bg-orb orb-1"></div>
      <div class="bg-orb orb-2"></div>
      <div class="bg-lines"></div>
    </div>

    <!-- 顶部导航 -->
    <header class="studio-header">
      <div class="header-row">
        <div class="header-left">
          <button class="btn-back" @click="goBack">
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd"/>
            </svg>
          </button>
          <div class="header-title">
            <div class="title-badge">
              <span>{{ agent.icon }}</span>
            </div>
            <div class="title-text">
              <h1>{{ agent.id ? '编辑 Agent' : '创建新 Agent' }}</h1>
              <p>配置你的智能助手</p>
            </div>
          </div>
        </div>
        <div class="header-right">
          <button class="btn-test" @click="testAgent">
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/>
            </svg>
            测试
          </button>
          <button class="btn-save" @click="saveAgent">
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
            </svg>
            保存
          </button>
        </div>
      </div>

      <!-- 功能说明 -->
      <div class="intro-bar">
        <div class="intro-item">
          <span class="intro-number">1</span>
          <span>基本信息: 设置 Agent 的名称、图标和描述</span>
        </div>
        <div class="intro-item">
          <span class="intro-number">2</span>
          <span>系统提示词: 定义 Agent 的角色和行为准则</span>
        </div>
        <div class="intro-item">
          <span class="intro-number">3</span>
          <span>技能管理: 创建、编辑、删除可用技能</span>
        </div>
        <div class="intro-item">
          <span class="intro-number">4</span>
          <span>高级设置: 调整模型参数和行为配置</span>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <div class="studio-content">
      <!-- 左侧导航 -->
      <nav class="studio-nav">
        <div class="nav-section">
          <span class="nav-label">配置步骤</span>
          <button :class="['nav-item', { active: activeTab === 'basic' }]" @click="activeTab = 'basic'">
            <span class="nav-number">1</span>
            <div class="nav-text">
              <span class="nav-title">基本信息</span>
              <span class="nav-desc">名称、描述、分类</span>
            </div>
            <span v-if="agent.name" class="nav-check">✓</span>
          </button>
          <button :class="['nav-item', { active: activeTab === 'prompt' }]" @click="activeTab = 'prompt'">
            <span class="nav-number">2</span>
            <div class="nav-text">
              <span class="nav-title">系统提示词</span>
              <span class="nav-desc">角色定义和行为</span>
            </div>
            <span v-if="agent.systemPrompt" class="nav-check">✓</span>
          </button>
          <button :class="['nav-item', { active: activeTab === 'tools' }]" @click="activeTab = 'tools'">
            <span class="nav-number">3</span>
            <div class="nav-text">
              <span class="nav-title">技能管理</span>
              <span class="nav-desc">管理可用技能</span>
            </div>
            <span v-if="agent.skills.length > 0" class="nav-check">✓</span>
          </button>
          <button :class="['nav-item', { active: activeTab === 'advanced' }]" @click="activeTab = 'advanced'">
            <span class="nav-number">4</span>
            <div class="nav-text">
              <span class="nav-title">高级设置</span>
              <span class="nav-desc">模型和参数</span>
            </div>
          </button>
        </div>

        <div class="nav-preview">
          <div class="preview-card">
            <span class="preview-icon">{{ agent.icon }}</span>
            <span class="preview-name">{{ agent.name || '未命名 Agent' }}</span>
            <span class="preview-model">{{ agent.model }}</span>
          </div>
        </div>
      </nav>

      <!-- 右侧表单 -->
      <div class="studio-form">
        <!-- 基本信息 -->
        <div v-show="activeTab === 'basic'" class="form-panel">
          <div class="panel-header">
            <h2>基本信息</h2>
            <p>设置 Agent 的基础属性</p>
          </div>

          <div class="form-grid">
            <div class="form-group icon-group">
              <label>图标</label>
              <div class="icon-selector">
                <button class="current-icon" @click="showIconPicker = !showIconPicker">
                  {{ agent.icon }}
                  <span class="icon-edit">✎</span>
                </button>
                <div v-if="showIconPicker" class="icon-picker">
                  <button
                    v-for="icon in icons"
                    :key="icon"
                    :class="['icon-option', { selected: agent.icon === icon }]"
                    @click="agent.icon = icon; showIconPicker = false"
                  >{{ icon }}</button>
                </div>
              </div>
            </div>

            <div class="form-group name-group">
              <label>名称 <span class="required">*</span></label>
              <input v-model="agent.name" type="text" placeholder="给你的 Agent 起个名字" class="form-input" />
            </div>
          </div>

          <div class="form-group">
            <label>
              描述
              <button class="btn-ai" :disabled="isGenerating" @click="generateDescription">
                <span class="ai-icon">✨</span>
                <span v-if="generatingField === 'description'">生成中...</span>
                <span v-else>AI 生成</span>
              </button>
            </label>
            <textarea v-model="agent.description" placeholder="描述这个 Agent 的功能和用途" class="form-textarea" rows="3"></textarea>
          </div>

          <div class="form-group">
            <label>分类</label>
            <div class="category-grid">
              <button
                v-for="cat in categories"
                :key="cat"
                :class="['category-btn', { selected: agent.category === cat }]"
                @click="agent.category = cat"
              >
                {{ cat }}
              </button>
            </div>
          </div>
        </div>

        <!-- 系统提示词 -->
        <div v-show="activeTab === 'prompt'" class="form-panel">
          <div class="panel-header">
            <h2>系统提示词</h2>
            <p>定义 Agent 的角色和行为准则</p>
            <button class="btn-ai header-ai" :disabled="isGenerating" @click="generatePrompt">
              <span class="ai-icon">✨</span>
              <span v-if="generatingField === 'systemPrompt'">生成中...</span>
              <span v-else>AI 智能生成</span>
            </button>
          </div>

          <div class="form-group">
            <div class="prompt-editor-wrapper">
              <textarea
                v-model="agent.systemPrompt"
                placeholder="输入系统提示词，定义 Agent 的角色、能力范围和行为准则..."
                class="prompt-editor"
                rows="18"
              ></textarea>
              <div class="editor-footer">
                <span class="char-count">{{ agent.systemPrompt.length }} 字符</span>
              </div>
            </div>
          </div>

          <div class="prompt-tips">
            <div class="tip-header">
              <span class="tip-icon">💡</span>
              <span>提示词建议</span>
            </div>
            <ul class="tip-list">
              <li>明确定义角色身份和专业领域</li>
              <li>设定清晰的输出格式要求</li>
              <li>规定行为边界和安全限制</li>
              <li>添加常见场景的处理指南</li>
            </ul>
          </div>
        </div>

        <!-- 技能管理 -->
        <div v-show="activeTab === 'tools'" class="form-panel form-panel-wide">
          <div class="panel-header">
            <div class="panel-header-left">
              <h2>技能管理</h2>
              <p>管理 Agent 可使用的技能，支持创建、编辑和删除</p>
            </div>
            <div class="panel-header-right">
              <button class="btn-create-skill" @click="openCreateModal">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"/>
                </svg>
                创建技能
              </button>
              <button class="btn-upload-skill" @click="openUploadModal">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
                </svg>
                上传技能
              </button>
            </div>
          </div>

          <!-- 技能网格 -->
          <div class="skills-grid-wrapper">
            <div v-if="skillsLoading" class="skills-loading">
              <div class="loading-spinner-small"></div>
              <span>加载技能中...</span>
            </div>
            <div v-else-if="availableSkillsFromApi.length === 0" class="empty-skills-large">
              <div class="empty-icon">⚡</div>
              <h3>暂无技能</h3>
              <p>创建或上传你的第一个技能</p>
              <div class="empty-actions">
                <button class="btn-create-skill" @click="openCreateModal">创建技能</button>
                <button class="btn-upload-skill" @click="openUploadModal">上传技能</button>
              </div>
            </div>
            <div v-else class="skills-grid">
              <div
              v-for="(skill, index) in availableSkillsFromApi"
              :key="skill.id"
              :class="['skill-grid-item', { selected: agent.skills.includes(skill.id) }]"
              @click="toggleSkill(skill.id)"
            >
                <SkillCard
                  :skill="skill"
                  @delete="deleteSkill(index)"
                  @edit="editSkill(skill)"
                />
              </div>
            </div>
          </div>

          <!-- 已选技能提示 -->
          <div v-if="agent.skills.length > 0" class="selected-skills-hint">
            <span class="hint-icon">✓</span>
            <span>已选择 {{ agent.skills.length }} 个技能</span>
          </div>
        </div>

        <!-- 高级设置 -->
        <div v-show="activeTab === 'advanced'" class="form-panel">
          <div class="panel-header">
            <h2>高级设置</h2>
            <p>调整模型参数和行为配置</p>
          </div>

          <div class="form-group">
            <label>模型选择</label>
            <div class="model-cards">
              <div
                v-for="model in models"
                :key="model.id"
                :class="['model-card', { selected: agent.model === model.id }]"
                @click="agent.model = model.id"
              >
                <div class="model-radio">
                  <span class="radio-dot"></span>
                </div>
                <div class="model-info">
                  <div class="model-header">
                    <span class="model-name">{{ model.name }}</span>
                    <span v-if="model.badge" :class="['model-badge', model.badge.toLowerCase()]">
                      {{ model.badge }}
                    </span>
                  </div>
                  <span class="model-desc">{{ model.desc }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label>
              温度 (Temperature)
              <span class="value-badge">{{ agent.temperature }}</span>
            </label>
            <div class="slider-wrapper">
              <input v-model.number="agent.temperature" type="range" min="0" max="1" step="0.1" class="form-slider" />
              <div class="slider-labels">
                <span>精确</span>
                <span>平衡</span>
                <span>创意</span>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label>最大 Token 数</label>
            <div class="token-input">
              <input v-model.number="agent.maxTokens" type="number" min="256" max="32000" class="form-input" />
              <span class="token-unit">tokens</span>
            </div>
          </div>

          <div class="toggle-group">
            <div class="toggle-item">
              <div class="toggle-info">
                <span class="toggle-title">记忆功能</span>
                <span class="toggle-desc">记住历史对话，提供连贯体验</span>
              </div>
              <label class="toggle-switch">
                <input v-model="agent.memory.enabled" type="checkbox" />
                <span class="toggle-track"></span>
              </label>
            </div>

            <div class="toggle-item">
              <div class="toggle-info">
                <span class="toggle-title">推理模式</span>
                <span class="toggle-desc">显示思考过程，提高可解释性</span>
              </div>
              <label class="toggle-switch">
                <input v-model="agent.reasoning.enabled" type="checkbox" />
                <span class="toggle-track"></span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <span class="loading-text">加载中...</span>
    </div>

    <!-- 加载错误 -->
    <div v-if="loadError" class="error-overlay">
      <div class="error-content">
        <span class="error-icon">⚠️</span>
        <p>{{ loadError }}</p>
        <button @click="goBack">返回</button>
      </div>
    </div>

    <!-- 技能创建/编辑/上传弹窗 -->
    <AddSkillModal
      :show="showSkillModal"
      :mode="skillModalMode"
      :edit-skill="editingSkill"
      @close="closeSkillModal"
      @submit="handleSkillSubmit"
    />

    <!-- Toast 提示 -->
    <Transition name="toast">
      <div v-if="showToast" class="toast-message">
        {{ toastMessage }}
      </div>
    </Transition>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

.agent-studio {
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

.bg-orb, .orb-1, .orb-2, .bg-lines {
  display: none;
}

/* 顶部 Header */
.studio-header {
  flex-shrink: 0;
  position: relative;
  padding: 12px 24px;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  z-index: 10;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

/* 功能说明条 */
.intro-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 8px 12px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.intro-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #6b7280;
}

.intro-number {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1677ff, #4096ff);
  border-radius: 50%;
  font-size: 10px;
  font-weight: 600;
  color: #fff;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-back {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-back:hover {
  background: #e5e7eb;
  color: #1f2937;
}

.btn-back svg {
  width: 16px;
  height: 16px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-badge {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #60a5fa 0%, #93c5fd 50%, #c4b5fd 100%);
  border-radius: 10px;
  font-size: 18px;
}

.title-text h1 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: #1f2937;
}

.title-text p {
  font-size: 11px;
  color: #9ca3af;
  margin: 2px 0 0;
}

.header-right {
  display: flex;
  gap: 8px;
}

.btn-test, .btn-save {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-test {
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  color: #6b7280;
}

.btn-test:hover {
  background: #e5e7eb;
  color: #1f2937;
}

.btn-save {
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
  border: none;
  color: white;
  box-shadow: 0 2px 8px rgba(22, 119, 255, 0.3);
}

.btn-save:hover {
  box-shadow: 0 4px 12px rgba(22, 119, 255, 0.4);
  transform: translateY(-1px);
}

.btn-test svg, .btn-save svg {
  width: 14px;
  height: 14px;
}

/* 主内容 */
.studio-content {
  display: flex;
  flex: 1;
  position: relative;
  z-index: 1;
  overflow: hidden;
}

/* 左侧导航 */
.studio-nav {
  width: 200px;
  padding: 14px;
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
}

.nav-section {
  flex: 1;
}

.nav-label {
  display: block;
  font-size: 10px;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 10px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
  text-align: left;
}

.nav-item:hover {
  background: #f3f4f6;
}

.nav-item.active {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.nav-number {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  color: #9ca3af;
  flex-shrink: 0;
}

.nav-item.active .nav-number {
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
  color: white;
}

.nav-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.nav-title {
  font-size: 12px;
  font-weight: 500;
  color: #1f2937;
}

.nav-desc {
  font-size: 10px;
  color: #9ca3af;
  margin-top: 2px;
}

.nav-check {
  color: #22c55e;
  font-size: 12px;
}

/* 预览卡片 */
.nav-preview {
  margin-top: auto;
  padding-top: 14px;
  border-top: 1px solid #e5e7eb;
}

.preview-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
}

.preview-icon {
  font-size: 28px;
}

.preview-name {
  font-size: 12px;
  font-weight: 500;
  color: #1f2937;
  text-align: center;
}

.preview-model {
  font-size: 9px;
  color: #9ca3af;
}

/* 右侧表单 */
.studio-form {
  flex: 1;
  padding: 16px 28px;
  overflow-y: auto;
  background: #f5f7fa;
}

.form-panel {
  animation: fadeIn 0.3s ease;
  max-width: 720px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.panel-header {
  margin-bottom: 16px;
  position: relative;
}

.panel-header h2 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px;
  color: #1f2937;
}

.panel-header p {
  font-size: 12px;
  color: #9ca3af;
  margin: 0;
}

.header-ai {
  position: absolute;
  top: 0;
  right: 0;
}

/* 表单组件 */
.form-grid {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 14px;
  margin-bottom: 14px;
}

.form-group {
  margin-bottom: 14px;
}

.form-group label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  margin-bottom: 6px;
}

.required {
  color: #ef4444;
}

.form-input, .form-textarea {
  width: 100%;
  padding: 10px 14px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  color: #1f2937;
  font-size: 13px;
  outline: none;
  transition: all 0.2s;
}

.form-input:focus, .form-textarea:focus {
  border-color: #1677ff;
  box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.1);
}

.form-textarea {
  resize: vertical;
  line-height: 1.6;
}

/* AI 生成按钮 */
.btn-ai {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: linear-gradient(135deg, rgba(22, 119, 255, 0.1), rgba(64, 150, 255, 0.1));
  border: 1px solid rgba(22, 119, 255, 0.3);
  border-radius: 12px;
  color: #1677ff;
  font-size: 10px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-ai:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(22, 119, 255, 0.15), rgba(64, 150, 255, 0.15));
  box-shadow: 0 0 8px rgba(22, 119, 255, 0.15);
}

.btn-ai:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ai-icon {
  font-size: 12px;
}

/* 图标选择器 */
.icon-selector {
  position: relative;
}

.current-icon {
  width: 52px;
  height: 52px;
  font-size: 26px;
  background: #ffffff;
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.current-icon:hover {
  border-color: #1677ff;
  background: #f0f7ff;
}

.icon-edit {
  position: absolute;
  bottom: 4px;
  right: 4px;
  font-size: 12px;
  color: #9ca3af;
}

.icon-picker {
  position: absolute;
  top: 60px;
  left: 0;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 6px;
  padding: 12px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  z-index: 20;
}

.icon-option {
  width: 36px;
  height: 36px;
  font-size: 18px;
  background: #f3f4f6;
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.icon-option:hover {
  background: #e0f2fe;
  transform: scale(1.1);
}

.icon-option.selected {
  background: #dbeafe;
  border-color: #1677ff;
}

/* 分类选择 */
.category-grid {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.category-btn {
  padding: 6px 12px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  color: #6b7280;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.category-btn:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.category-btn.selected {
  background: #eff6ff;
  border-color: #1677ff;
  color: #1677ff;
}

/* 提示词编辑器 */
.prompt-editor-wrapper {
  position: relative;
}

.prompt-editor {
  width: 100%;
  padding: 14px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  color: #1f2937;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
  font-size: 12px;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  transition: all 0.2s;
}

.prompt-editor:focus {
  border-color: #1677ff;
  box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.1);
}

.editor-footer {
  display: flex;
  justify-content: flex-end;
  padding: 6px 0;
}

.char-count {
  font-size: 11px;
  color: #9ca3af;
}

/* 提示建议 */
.prompt-tips {
  background: #f0f7ff;
  border: 1px solid #bfdbfe;
  border-radius: 10px;
  padding: 12px;
}

.tip-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 500;
  color: #1677ff;
}

.tip-icon {
  font-size: 14px;
}

.tip-list {
  margin: 0;
  padding-left: 16px;
}

.tip-list li {
  color: #6b7280;
  font-size: 11px;
  margin-bottom: 4px;
  line-height: 1.4;
}

/* 技能管理面板 */
.form-panel-wide {
  max-width: 100%;
}

.form-panel-wide .panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.panel-header-left h2 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px;
  color: #1f2937;
}

.panel-header-left p {
  font-size: 12px;
  color: #9ca3af;
  margin: 0;
}

.panel-header-right {
  display: flex;
  gap: 8px;
}

.btn-create-skill, .btn-upload-skill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-create-skill {
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
  border: none;
  color: white;
}

.btn-create-skill:hover {
  box-shadow: 0 2px 8px rgba(22, 119, 255, 0.3);
}

.btn-upload-skill {
  background: #fff;
  border: 1px solid #e5e7eb;
  color: #6b7280;
}

.btn-upload-skill:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.btn-create-skill svg, .btn-upload-skill svg {
  width: 14px;
  height: 14px;
}

/* 技能网格容器 */
.skills-grid-wrapper {
  min-height: 300px;
}

.skills-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 20px;
  color: #9ca3af;
  font-size: 13px;
}

.loading-spinner-small {
  width: 24px;
  height: 24px;
  border: 2px solid rgba(22, 119, 255, 0.2);
  border-top-color: #1677ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.empty-skills-large {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-skills-large h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px;
}

.empty-skills-large p {
  font-size: 13px;
  color: #9ca3af;
  margin: 0 0 20px;
}

.empty-actions {
  display: flex;
  gap: 12px;
}

/* 技能网格 */
.skills-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.skill-grid-item {
  position: relative;
}

/* 技能卡片 */
.skill-grid-item {
  position: relative;
  cursor: pointer;
  border-radius: 10px;
  transition: all 0.2s;
}

.skill-grid-item:hover {
  transform: translateY(-2px);
}

/* 选中状态 - 用伪元素覆盖蓝色蒙层 */
.skill-grid-item.selected {
  box-shadow: 0 0 0 2px #1677ff;
}

.skill-grid-item.selected::before {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(22, 119, 255, 0.08);
  border-radius: 10px;
  pointer-events: none;
  z-index: 1;
}

/* 已选技能提示 */
.selected-skills-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 10px 14px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  font-size: 12px;
  color: #15803d;
}

.hint-icon {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #22c55e;
  border-radius: 50%;
  color: white;
  font-size: 10px;
}

/* Toast 提示 */
.toast-message {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  background: #1f2937;
  color: white;
  border-radius: 8px;
  font-size: 13px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
}

.toast-enter-active, .toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from, .toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}


/* 模型选择 */
.model-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.model-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.model-card:hover {
  background: #f8fafc;
}

.model-card.selected {
  background: #eff6ff;
  border-color: #1677ff;
}

.model-radio {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #d1d5db;
  border-radius: 50%;
  flex-shrink: 0;
}

.model-card.selected .model-radio {
  border-color: #1677ff;
}

.radio-dot {
  width: 8px;
  height: 8px;
  background: #1677ff;
  border-radius: 50%;
  opacity: 0;
  transform: scale(0);
  transition: all 0.2s;
}

.model-card.selected .radio-dot {
  opacity: 1;
  transform: scale(1);
}

.model-info {
  flex: 1;
}

.model-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}

.model-name {
  font-size: 12px;
  font-weight: 500;
  color: #1f2937;
}

.model-badge {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.model-badge.pro {
  background: #fef3c7;
  color: #d97706;
}

.model-badge.fast {
  background: #dcfce7;
  color: #16a34a;
}

.model-desc {
  font-size: 10px;
  color: #9ca3af;
}

/* 滑块 */
.slider-wrapper {
  padding: 8px 0;
}

.form-slider {
  width: 100%;
  height: 6px;
  background: #e5e7eb;
  border-radius: 3px;
  appearance: none;
  cursor: pointer;
}

.form-slider::-webkit-slider-thumb {
  appearance: none;
  width: 18px;
  height: 18px;
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(22, 119, 255, 0.35);
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #9ca3af;
  margin-top: 8px;
}

.value-badge {
  padding: 2px 10px;
  background: #eff6ff;
  border-radius: 10px;
  font-size: 12px;
  color: #1677ff;
}

/* Token 输入 */
.token-input {
  position: relative;
  display: flex;
  align-items: center;
}

.token-input .form-input {
  padding-right: 70px;
}

.token-unit {
  position: absolute;
  right: 16px;
  font-size: 13px;
  color: #9ca3af;
}

/* 开关组 */
.toggle-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
}

.toggle-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toggle-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.toggle-title {
  font-size: 12px;
  font-weight: 500;
  color: #1f2937;
}

.toggle-desc {
  font-size: 10px;
  color: #9ca3af;
}

.toggle-switch {
  position: relative;
  width: 40px;
  height: 22px;
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
  background: #d1d5db;
  border-radius: 11px;
  transition: all 0.3s;
}

.toggle-track::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  background: white;
  border-radius: 50%;
  transition: all 0.3s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}

.toggle-switch input:checked + .toggle-track {
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
}

.toggle-switch input:checked + .toggle-track::after {
  transform: translateX(18px);
}

/* 加载状态 */
.loading-overlay {
  position: fixed;
  inset: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  z-index: 100;
}

.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(22, 119, 255, 0.2);
  border-top-color: #1677ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 14px;
  color: #6b7280;
}

/* 错误状态 */
.error-overlay {
  position: fixed;
  inset: 0;
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.error-content {
  text-align: center;
  padding: 32px;
  background: #ffffff;
  border: 1px solid #fecaca;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.error-icon {
  font-size: 48px;
}

.error-content p {
  color: #ef4444;
  font-size: 14px;
  margin: 12px 0 20px;
}

.error-content button {
  padding: 8px 20px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  color: #6b7280;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.error-content button:hover {
  background: #e5e7eb;
  color: #1f2937;
}
</style>
