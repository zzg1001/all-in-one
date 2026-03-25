<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

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

const availableTools = [
  { id: 'read', name: '读取文件', icon: '📖', desc: '读取本地文件内容' },
  { id: 'write', name: '写入文件', icon: '✏️', desc: '创建或修改文件' },
  { id: 'bash', name: '执行命令', icon: '💻', desc: '执行 Shell 命令' },
  { id: 'web_search', name: '网络搜索', icon: '🔍', desc: '搜索互联网信息' },
  { id: 'web_fetch', name: '网页抓取', icon: '🌐', desc: '获取网页内容' },
  { id: 'image_read', name: '图像识别', icon: '🖼️', desc: '分析图像内容' },
  { id: 'code_exec', name: '代码执行', icon: '▶️', desc: '执行代码片段' }
]

const availableSkills = ref([
  { id: 'excel-to-json', name: 'Excel 转 JSON', icon: '📊' },
  { id: 'json-to-excel', name: 'JSON 转 Excel', icon: '📑' },
  { id: 'pdf-reader', name: 'PDF 读取', icon: '📄' },
  { id: 'image-gen', name: '图像生成', icon: '🎨' }
])

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

const toggleTool = (toolId: string) => {
  const index = agent.tools.indexOf(toolId)
  if (index > -1) {
    agent.tools.splice(index, 1)
  } else {
    agent.tools.push(toolId)
  }
}

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

const recommendTools = async () => {
  if (!agent.description) {
    alert('请先填写 Agent 描述')
    return
  }
  isGenerating.value = true
  generatingField.value = 'tools'
  await new Promise(resolve => setTimeout(resolve, 1200))
  const desc = agent.description.toLowerCase()
  agent.tools = []
  if (desc.includes('文件') || desc.includes('文档')) agent.tools.push('read', 'write')
  if (desc.includes('代码') || desc.includes('编程')) agent.tools.push('bash', 'code_exec')
  if (desc.includes('搜索') || desc.includes('网络')) agent.tools.push('web_search', 'web_fetch')
  if (desc.includes('图像') || desc.includes('图片')) agent.tools.push('image_read')
  if (agent.tools.length === 0) agent.tools.push('read')
  isGenerating.value = false
  generatingField.value = ''
}

const saveAgent = async () => {
  if (!agent.name) {
    alert('请填写 Agent 名称')
    return
  }
  console.log('Saving agent:', agent)
  alert('Agent 保存成功！')
  router.push('/agents')
}

const goBack = () => router.push('/agents')
const testAgent = () => router.push({ path: '/', query: { tab: 'agent', testAgent: 'true' } })

onMounted(() => {
  const agentId = route.query.id as string
  if (agentId) console.log('Loading agent:', agentId)
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
          <span>工具与技能: 配置 Agent 可使用的能力扩展</span>
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
              <span class="nav-title">工具与技能</span>
              <span class="nav-desc">扩展能力配置</span>
            </div>
            <span v-if="agent.tools.length > 0" class="nav-check">✓</span>
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

        <!-- 工具与技能 -->
        <div v-show="activeTab === 'tools'" class="form-panel">
          <div class="panel-header">
            <h2>工具与技能</h2>
            <p>选择 Agent 可使用的能力</p>
            <button class="btn-ai header-ai" :disabled="isGenerating" @click="recommendTools">
              <span class="ai-icon">✨</span>
              <span v-if="generatingField === 'tools'">推荐中...</span>
              <span v-else>AI 推荐</span>
            </button>
          </div>

          <div class="tools-section">
            <h3>内置工具</h3>
            <div class="tools-grid">
              <div
                v-for="tool in availableTools"
                :key="tool.id"
                :class="['tool-card', { selected: agent.tools.includes(tool.id) }]"
                @click="toggleTool(tool.id)"
              >
                <div class="tool-header">
                  <span class="tool-icon">{{ tool.icon }}</span>
                  <span class="tool-check">
                    <svg v-if="agent.tools.includes(tool.id)" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                    </svg>
                  </span>
                </div>
                <span class="tool-name">{{ tool.name }}</span>
                <span class="tool-desc">{{ tool.desc }}</span>
              </div>
            </div>
          </div>

          <div class="skills-section">
            <h3>自定义技能</h3>
            <div class="skills-grid">
              <div
                v-for="skill in availableSkills"
                :key="skill.id"
                :class="['skill-card', { selected: agent.skills.includes(skill.id) }]"
                @click="toggleSkill(skill.id)"
              >
                <span class="skill-icon">{{ skill.icon }}</span>
                <span class="skill-name">{{ skill.name }}</span>
                <span v-if="agent.skills.includes(skill.id)" class="skill-check">✓</span>
              </div>
            </div>
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
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

.agent-studio {
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

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
}

.orb-1 {
  width: 500px;
  height: 500px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(139, 92, 246, 0.2));
  top: -100px;
  left: 50%;
}

.orb-2 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(59, 130, 246, 0.15));
  bottom: 10%;
  right: 10%;
}

.bg-lines {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(99, 102, 241, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(99, 102, 241, 0.02) 1px, transparent 1px);
  background-size: 50px 50px;
}

/* 顶部 Header */
.studio-header {
  flex-shrink: 0;
  position: relative;
  padding: 14px 24px;
  background: rgba(10, 10, 15, 0.95);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(12px);
  z-index: 10;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

/* 功能说明条 */
.intro-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 10px 14px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.06), rgba(139, 92, 246, 0.04));
  border: 1px solid rgba(99, 102, 241, 0.15);
  border-radius: 8px;
}

.intro-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #a1a1aa;
}

.intro-number {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(139, 92, 246, 0.3));
  border-radius: 50%;
  font-size: 10px;
  font-weight: 600;
  color: #c4b5fd;
  flex-shrink: 0;
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

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-badge {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2));
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 10px;
  font-size: 18px;
}

.title-text h1 {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: #fff;
}

.title-text p {
  font-size: 11px;
  color: #71717a;
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
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #a1a1aa;
}

.btn-test:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.btn-save {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  color: white;
}

.btn-save:hover {
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
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
  width: 220px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.02);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
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
  color: #52525b;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 12px;
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
  margin-bottom: 6px;
  text-align: left;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.03);
}

.nav-item.active {
  background: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.3);
}

.nav-number {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  color: #71717a;
  flex-shrink: 0;
}

.nav-item.active .nav-number {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
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
  color: #e4e4e7;
}

.nav-desc {
  font-size: 10px;
  color: #52525b;
  margin-top: 2px;
}

.nav-check {
  color: #4ade80;
  font-size: 12px;
}

/* 预览卡片 */
.nav-preview {
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.preview-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
}

.preview-icon {
  font-size: 28px;
}

.preview-name {
  font-size: 12px;
  font-weight: 500;
  color: #e4e4e7;
  text-align: center;
}

.preview-model {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: #52525b;
}

/* 右侧表单 */
.studio-form {
  flex: 1;
  padding: 20px 32px;
  overflow-y: auto;
}

.form-panel {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.panel-header {
  margin-bottom: 20px;
  position: relative;
}

.panel-header h2 {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 6px;
  color: #fff;
}

.panel-header p {
  font-size: 12px;
  color: #71717a;
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
  gap: 16px;
  margin-bottom: 16px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  font-weight: 500;
  color: #a1a1aa;
  margin-bottom: 8px;
}

.required {
  color: #f87171;
}

.form-input, .form-textarea {
  width: 100%;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  color: #e4e4e7;
  font-size: 13px;
  outline: none;
  transition: all 0.2s;
}

.form-input:focus, .form-textarea:focus {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(99, 102, 241, 0.5);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
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
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.15));
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 12px;
  color: #a5b4fc;
  font-size: 10px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-ai:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(139, 92, 246, 0.25));
  box-shadow: 0 0 12px rgba(99, 102, 241, 0.2);
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
  width: 56px;
  height: 56px;
  font-size: 28px;
  background: rgba(255, 255, 255, 0.03);
  border: 2px dashed rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.current-icon:hover {
  border-color: rgba(99, 102, 241, 0.5);
  background: rgba(99, 102, 241, 0.1);
}

.icon-edit {
  position: absolute;
  bottom: 4px;
  right: 4px;
  font-size: 12px;
  color: #71717a;
}

.icon-picker {
  position: absolute;
  top: 64px;
  left: 0;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 6px;
  padding: 12px;
  background: #18181b;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 16px 32px rgba(0, 0, 0, 0.5);
  z-index: 20;
}

.icon-option {
  width: 36px;
  height: 36px;
  font-size: 18px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.icon-option:hover {
  background: rgba(99, 102, 241, 0.2);
  transform: scale(1.1);
}

.icon-option.selected {
  background: rgba(99, 102, 241, 0.3);
  border-color: rgba(99, 102, 241, 0.5);
}

/* 分类选择 */
.category-grid {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.category-btn {
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  color: #a1a1aa;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.category-btn:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #e4e4e7;
}

.category-btn.selected {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2));
  border-color: rgba(99, 102, 241, 0.5);
  color: #a5b4fc;
}

/* 提示词编辑器 */
.prompt-editor-wrapper {
  position: relative;
}

.prompt-editor {
  width: 100%;
  padding: 14px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  color: #e4e4e7;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  transition: all 0.2s;
}

.prompt-editor:focus {
  border-color: rgba(99, 102, 241, 0.5);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.editor-footer {
  display: flex;
  justify-content: flex-end;
  padding: 8px 0;
}

.char-count {
  font-size: 12px;
  color: #52525b;
}

/* 提示建议 */
.prompt-tips {
  background: rgba(99, 102, 241, 0.05);
  border: 1px solid rgba(99, 102, 241, 0.15);
  border-radius: 10px;
  padding: 14px;
}

.tip-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 12px;
  font-weight: 500;
  color: #a5b4fc;
}

.tip-icon {
  font-size: 14px;
}

.tip-list {
  margin: 0;
  padding-left: 16px;
}

.tip-list li {
  color: #71717a;
  font-size: 11px;
  margin-bottom: 6px;
  line-height: 1.4;
}

/* 工具网格 */
.tools-section, .skills-section {
  margin-bottom: 20px;
}

.tools-section h3, .skills-section h3 {
  font-size: 13px;
  font-weight: 500;
  color: #e4e4e7;
  margin: 0 0 12px;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 10px;
}

.tool-card {
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.tool-card:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.1);
}

.tool-card.selected {
  background: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.4);
}

.tool-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.tool-icon {
  font-size: 20px;
}

.tool-check {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(99, 102, 241, 0.2);
  border-radius: 4px;
}

.tool-check svg {
  width: 12px;
  height: 12px;
  color: #a5b4fc;
}

.tool-name {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #e4e4e7;
  margin-bottom: 2px;
}

.tool-desc {
  display: block;
  font-size: 10px;
  color: #52525b;
}

/* 技能网格 */
.skills-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
}

.skill-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.skill-card:hover {
  background: rgba(255, 255, 255, 0.04);
}

.skill-card.selected {
  background: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.4);
}

.skill-icon {
  font-size: 22px;
}

.skill-name {
  font-size: 11px;
  color: #a1a1aa;
  text-align: center;
}

.skill-check {
  position: absolute;
  top: 8px;
  right: 8px;
  color: #4ade80;
  font-size: 10px;
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
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.model-card:hover {
  background: rgba(255, 255, 255, 0.04);
}

.model-card.selected {
  background: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.4);
}

.model-radio {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  flex-shrink: 0;
}

.model-card.selected .model-radio {
  border-color: #6366f1;
}

.radio-dot {
  width: 8px;
  height: 8px;
  background: #6366f1;
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
  color: #e4e4e7;
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
  background: rgba(234, 179, 8, 0.2);
  color: #fbbf24;
}

.model-badge.fast {
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
}

.model-desc {
  font-size: 10px;
  color: #52525b;
}

/* 滑块 */
.slider-wrapper {
  padding: 10px 0;
}

.form-slider {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  appearance: none;
  cursor: pointer;
}

.form-slider::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(99, 102, 241, 0.4);
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #52525b;
  margin-top: 10px;
}

.value-badge {
  padding: 2px 10px;
  background: rgba(99, 102, 241, 0.15);
  border-radius: 10px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #a5b4fc;
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
  color: #52525b;
}

/* 开关组 */
.toggle-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
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
  color: #e4e4e7;
}

.toggle-desc {
  font-size: 10px;
  color: #52525b;
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
  background: rgba(255, 255, 255, 0.1);
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
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.toggle-switch input:checked + .toggle-track {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
}

.toggle-switch input:checked + .toggle-track::after {
  transform: translateX(18px);
}
</style>
