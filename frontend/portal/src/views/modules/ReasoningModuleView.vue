<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 当前活动标签
const activeTab = ref('modes')

// 基础配置
const config = reactive({
  enabled: true,
  style: 'chain-of-thought',
  showThinking: true,
  reflectionEnabled: true,
  maxReflections: 3,
  hypothesisValidation: true,
  confidenceThreshold: 0.8
})

const reasoningStats = ref({
  totalReasoning: 856,
  avgSteps: 4.2,
  reflectionRate: '23%',
  accuracy: '94.5%'
})

// 推理模式 - 可编辑
const reasoningModes = ref([
  { id: 'chain-of-thought', name: '链式思考', desc: '逐步推理，展示完整思考过程', icon: '🔗', enabled: true, prompt: '请一步一步思考这个问题...' },
  { id: 'tree-of-thought', name: '树形思考', desc: '探索多个分支，选择最优路径', icon: '🌳', enabled: true, prompt: '让我们探索多个可能的方向...' },
  { id: 'react', name: 'ReAct 模式', desc: '推理-行动交替，动态调整', icon: '⚡', enabled: true, prompt: '思考 -> 行动 -> 观察 -> 思考...' },
  { id: 'reflexion', name: '反思模式', desc: '自我评估，持续改进', icon: '🔄', enabled: false, prompt: '让我反思之前的回答是否正确...' }
])

// 思考步骤类型 - 可编辑
const stepTypes = ref([
  { id: 'understand', name: '理解', icon: '🎯', color: '#3b82f6', description: '理解问题和需求' },
  { id: 'analyze', name: '分析', icon: '🔍', color: '#10b981', description: '分析数据和信息' },
  { id: 'hypothesize', name: '假设', icon: '🤔', color: '#f59e0b', description: '提出可能的假设' },
  { id: 'decide', name: '决策', icon: '💡', color: '#8b5cf6', description: '做出判断和决策' },
  { id: 'validate', name: '验证', icon: '✅', color: '#22c55e', description: '验证结论的正确性' },
  { id: 'reflect', name: '反思', icon: '🔄', color: '#ec4899', description: '反思和改进' }
])

// 提示词模板 - 可编辑
const promptTemplates = ref([
  {
    id: 'reasoning_start',
    name: '推理开始',
    description: '开始推理时的系统提示',
    content: `让我仔细思考这个问题。

首先，我需要理解问题的核心：
1. 问题是什么？
2. 有哪些已知条件？
3. 期望的输出是什么？

然后，我会逐步分析和推导...`
  },
  {
    id: 'reflection',
    name: '反思提示',
    description: '触发反思机制的提示',
    content: `让我回顾一下刚才的推理过程：

1. 我的结论是否正确？
2. 推理逻辑是否有漏洞？
3. 是否考虑了所有可能的情况？

如果发现问题，我需要...`
  },
  {
    id: 'hypothesis',
    name: '假设验证',
    description: '验证假设时的提示',
    content: `基于以上分析，我提出以下假设：

假设：{hypothesis}

验证方法：
1. 检查逻辑一致性
2. 寻找反例
3. 验证边界条件

验证结果：...`
  }
])

// 最近推理记录
const recentThoughts = ref([
  {
    id: '1',
    task: '分析用户需求并生成解决方案',
    steps: [
      { step: 1, content: '理解用户问题：需要将 Excel 数据转换为特定格式', type: 'understand' },
      { step: 2, content: '分析数据结构：包含日期、数值、文本三种类型', type: 'analyze' },
      { step: 3, content: '选择转换策略：使用 pandas 库进行批量处理', type: 'decide' },
      { step: 4, content: '验证结果：检查输出格式是否符合要求', type: 'validate' }
    ],
    status: 'completed',
    confidence: 0.92
  },
  {
    id: '2',
    task: '代码错误诊断',
    steps: [
      { step: 1, content: '定位错误：TypeError at line 42', type: 'understand' },
      { step: 2, content: '分析原因：变量类型不匹配', type: 'analyze' },
      { step: 3, content: '提出假设：可能是异步返回值未处理', type: 'hypothesize' }
    ],
    status: 'thinking',
    confidence: 0.78
  }
])

// 编辑状态
const editingMode = ref<string | null>(null)
const editingStepType = ref<string | null>(null)
const editingPrompt = ref<string | null>(null)

// 模态框状态
const showModeModal = ref(false)
const showStepTypeModal = ref(false)
const showAddModeModal = ref(false)

// 表单数据
const modeForm = reactive({
  id: '',
  name: '',
  desc: '',
  icon: '',
  enabled: true,
  prompt: ''
})

const stepTypeForm = reactive({
  id: '',
  name: '',
  icon: '',
  color: '#3b82f6',
  description: ''
})

// 方法
const getStepIcon = (type: string) => {
  const step = stepTypes.value.find(s => s.id === type)
  return step?.icon || '📝'
}

const getStepColor = (type: string) => {
  const step = stepTypes.value.find(s => s.id === type)
  return step?.color || '#71717a'
}

const editMode = (mode: typeof reasoningModes.value[0]) => {
  Object.assign(modeForm, mode)
  editingMode.value = mode.id
  showModeModal.value = true
}

const saveMode = () => {
  const index = reasoningModes.value.findIndex(m => m.id === editingMode.value)
  if (index !== -1) {
    reasoningModes.value[index] = { ...modeForm }
  }
  showModeModal.value = false
  editingMode.value = null
}

const addNewMode = () => {
  Object.assign(modeForm, {
    id: `mode-${Date.now()}`,
    name: '',
    desc: '',
    icon: '🧠',
    enabled: true,
    prompt: ''
  })
  showAddModeModal.value = true
}

const saveNewMode = () => {
  reasoningModes.value.push({ ...modeForm })
  showAddModeModal.value = false
}

const deleteMode = (modeId: string) => {
  const index = reasoningModes.value.findIndex(m => m.id === modeId)
  if (index !== -1) {
    reasoningModes.value.splice(index, 1)
  }
}

const toggleMode = (modeId: string) => {
  const mode = reasoningModes.value.find(m => m.id === modeId)
  if (mode) {
    mode.enabled = !mode.enabled
  }
}

const editStepType = (step: typeof stepTypes.value[0]) => {
  Object.assign(stepTypeForm, step)
  editingStepType.value = step.id
  showStepTypeModal.value = true
}

const saveStepType = () => {
  const index = stepTypes.value.findIndex(s => s.id === editingStepType.value)
  if (index !== -1) {
    stepTypes.value[index] = { ...stepTypeForm }
  }
  showStepTypeModal.value = false
  editingStepType.value = null
}

const selectMode = (modeId: string) => {
  config.style = modeId
}

const goBack = () => router.push('/architecture')
</script>

<template>
  <div class="module-view reasoning-module">
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
        <div class="module-badge reasoning">
          <span>💭</span>
        </div>
        <div class="header-title">
          <h1>Reasoning 推理模块</h1>
          <p>链式思考、反思机制、假设验证，支持多种推理模式</p>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn-secondary">导入配置</button>
        <button class="btn-primary">保存配置</button>
      </div>
    </header>

    <!-- 标签导航 -->
    <nav class="tab-nav">
      <button
        :class="['tab-btn', { active: activeTab === 'modes' }]"
        @click="activeTab = 'modes'"
      >
        推理模式
      </button>
      <button
        :class="['tab-btn', { active: activeTab === 'steps' }]"
        @click="activeTab = 'steps'"
      >
        思考步骤
      </button>
      <button
        :class="['tab-btn', { active: activeTab === 'prompts' }]"
        @click="activeTab = 'prompts'"
      >
        提示词模板
      </button>
      <button
        :class="['tab-btn', { active: activeTab === 'settings' }]"
        @click="activeTab = 'settings'"
      >
        基础设置
      </button>
    </nav>

    <!-- 主内容 -->
    <div class="module-content">
      <!-- 推理模式 Tab -->
      <div v-if="activeTab === 'modes'" class="tab-content">
        <div class="content-header">
          <h3>推理模式管理</h3>
          <button class="btn-add" @click="addNewMode">+ 添加模式</button>
        </div>

        <div class="modes-grid">
          <div
            v-for="mode in reasoningModes"
            :key="mode.id"
            :class="['mode-card', { selected: config.style === mode.id, disabled: !mode.enabled }]"
          >
            <div class="mode-header">
              <div class="mode-icon-wrapper" @click="selectMode(mode.id)">
                <span class="mode-icon">{{ mode.icon }}</span>
              </div>
              <div class="mode-controls">
                <label class="toggle-mini">
                  <input type="checkbox" :checked="mode.enabled" @change="toggleMode(mode.id)" />
                  <span class="toggle-track-mini"></span>
                </label>
                <button class="btn-edit" @click="editMode(mode)">编辑</button>
                <button class="btn-delete" @click="deleteMode(mode.id)">×</button>
              </div>
            </div>
            <div class="mode-body" @click="selectMode(mode.id)">
              <h4>{{ mode.name }}</h4>
              <p>{{ mode.desc }}</p>
            </div>
            <div class="mode-prompt">
              <span class="prompt-label">提示词:</span>
              <p>{{ mode.prompt.slice(0, 50) }}...</p>
            </div>
            <div v-if="config.style === mode.id" class="mode-selected-badge">当前使用</div>
          </div>
        </div>

        <!-- 统计信息 -->
        <div class="stats-row">
          <div class="stat-item">
            <span class="stat-icon">🧠</span>
            <span class="stat-value">{{ reasoningStats.totalReasoning }}</span>
            <span class="stat-label">推理次数</span>
          </div>
          <div class="stat-item">
            <span class="stat-icon">📊</span>
            <span class="stat-value">{{ reasoningStats.avgSteps }}</span>
            <span class="stat-label">平均步骤</span>
          </div>
          <div class="stat-item">
            <span class="stat-icon">🔄</span>
            <span class="stat-value">{{ reasoningStats.reflectionRate }}</span>
            <span class="stat-label">反思率</span>
          </div>
          <div class="stat-item">
            <span class="stat-icon">🎯</span>
            <span class="stat-value">{{ reasoningStats.accuracy }}</span>
            <span class="stat-label">准确率</span>
          </div>
        </div>
      </div>

      <!-- 思考步骤 Tab -->
      <div v-if="activeTab === 'steps'" class="tab-content">
        <div class="content-header">
          <h3>思考步骤类型</h3>
          <p class="content-desc">定义推理过程中的步骤类型，用于结构化展示思考过程</p>
        </div>

        <div class="steps-grid">
          <div
            v-for="step in stepTypes"
            :key="step.id"
            class="step-card"
            :style="{ '--step-color': step.color }"
          >
            <div class="step-header">
              <span class="step-icon">{{ step.icon }}</span>
              <button class="btn-edit-small" @click="editStepType(step)">编辑</button>
            </div>
            <h4>{{ step.name }}</h4>
            <p>{{ step.description }}</p>
            <div class="step-color-preview" :style="{ background: step.color }"></div>
          </div>
        </div>

        <!-- 推理示例 -->
        <div class="example-section">
          <h3>推理过程示例</h3>
          <div class="thoughts-list">
            <div v-for="thought in recentThoughts" :key="thought.id" class="thought-item">
              <div class="thought-header">
                <span class="thought-task">{{ thought.task }}</span>
                <span :class="['thought-status', thought.status]">
                  {{ thought.status === 'completed' ? '已完成' : '思考中...' }}
                </span>
              </div>
              <div class="thought-steps">
                <div
                  v-for="step in thought.steps"
                  :key="step.step"
                  class="step-item"
                  :style="{ '--step-color': getStepColor(step.type) }"
                >
                  <span class="step-number">{{ step.step }}</span>
                  <span class="step-icon-small">{{ getStepIcon(step.type) }}</span>
                  <span class="step-content">{{ step.content }}</span>
                </div>
              </div>
              <div class="thought-footer">
                <span class="confidence-label">置信度</span>
                <div class="confidence-bar">
                  <div class="confidence-fill" :style="{ width: (thought.confidence * 100) + '%' }"></div>
                </div>
                <span class="confidence-value">{{ (thought.confidence * 100).toFixed(0) }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 提示词模板 Tab -->
      <div v-if="activeTab === 'prompts'" class="tab-content">
        <div class="content-header">
          <h3>提示词模板</h3>
          <p class="content-desc">自定义推理过程中使用的提示词模板</p>
        </div>

        <div class="prompts-list">
          <div v-for="prompt in promptTemplates" :key="prompt.id" class="prompt-card">
            <div class="prompt-header">
              <div class="prompt-info">
                <h4>{{ prompt.name }}</h4>
                <span class="prompt-id">{{ prompt.id }}</span>
              </div>
              <p class="prompt-desc">{{ prompt.description }}</p>
            </div>
            <div class="prompt-content">
              <textarea
                v-model="prompt.content"
                class="prompt-textarea"
                rows="6"
              ></textarea>
            </div>
            <div class="prompt-actions">
              <button class="btn-text">重置默认</button>
              <button class="btn-small">测试</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 基础设置 Tab -->
      <div v-if="activeTab === 'settings'" class="tab-content">
        <div class="settings-grid">
          <div class="settings-section">
            <h3>显示设置</h3>

            <div class="setting-item">
              <div class="setting-label">
                <span>显示思考过程</span>
                <span class="setting-desc">在回答中展示推理步骤</span>
              </div>
              <label class="toggle-switch">
                <input v-model="config.showThinking" type="checkbox" />
                <span class="toggle-track"></span>
              </label>
            </div>
          </div>

          <div class="settings-section">
            <h3>反思机制</h3>

            <div class="setting-item">
              <div class="setting-label">
                <span>启用反思</span>
                <span class="setting-desc">自动检查和改进推理结果</span>
              </div>
              <label class="toggle-switch">
                <input v-model="config.reflectionEnabled" type="checkbox" />
                <span class="toggle-track"></span>
              </label>
            </div>

            <div class="setting-item">
              <div class="setting-label">
                <span>最大反思轮数</span>
                <span class="setting-value">{{ config.maxReflections }}</span>
              </div>
              <input v-model.number="config.maxReflections" type="range" min="1" max="5" class="setting-slider" />
            </div>

            <div class="setting-item">
              <div class="setting-label">
                <span>假设验证</span>
                <span class="setting-desc">验证推理假设的正确性</span>
              </div>
              <label class="toggle-switch">
                <input v-model="config.hypothesisValidation" type="checkbox" />
                <span class="toggle-track"></span>
              </label>
            </div>

            <div class="setting-item">
              <div class="setting-label">
                <span>置信度阈值</span>
                <span class="setting-value">{{ config.confidenceThreshold }}</span>
              </div>
              <input v-model.number="config.confidenceThreshold" type="range" min="0.5" max="1" step="0.05" class="setting-slider" />
            </div>
          </div>

          <div class="settings-section full-width">
            <h3>推理流程说明</h3>
            <div class="flow-diagram">
              <div class="flow-step">
                <span class="flow-icon">🎯</span>
                <span class="flow-label">理解</span>
              </div>
              <div class="flow-arrow">→</div>
              <div class="flow-step">
                <span class="flow-icon">🔍</span>
                <span class="flow-label">分析</span>
              </div>
              <div class="flow-arrow">→</div>
              <div class="flow-step">
                <span class="flow-icon">🤔</span>
                <span class="flow-label">假设</span>
              </div>
              <div class="flow-arrow">→</div>
              <div class="flow-step">
                <span class="flow-icon">✅</span>
                <span class="flow-label">验证</span>
              </div>
              <div class="flow-arrow">→</div>
              <div class="flow-step">
                <span class="flow-icon">🔄</span>
                <span class="flow-label">反思</span>
              </div>
            </div>
            <p class="flow-desc">通过多轮反思持续提升推理质量，直到达到置信度阈值</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑模式弹窗 -->
    <div v-if="showModeModal" class="modal-overlay" @click.self="showModeModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>编辑推理模式</h3>
          <button class="modal-close" @click="showModeModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>模式名称</label>
            <input v-model="modeForm.name" type="text" class="form-input" />
          </div>
          <div class="form-group">
            <label>图标</label>
            <input v-model="modeForm.icon" type="text" class="form-input icon-input" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <input v-model="modeForm.desc" type="text" class="form-input" />
          </div>
          <div class="form-group">
            <label>提示词</label>
            <textarea v-model="modeForm.prompt" class="form-textarea" rows="4"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showModeModal = false">取消</button>
          <button class="btn-save" @click="saveMode">保存</button>
        </div>
      </div>
    </div>

    <!-- 添加模式弹窗 -->
    <div v-if="showAddModeModal" class="modal-overlay" @click.self="showAddModeModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>添加推理模式</h3>
          <button class="modal-close" @click="showAddModeModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>模式名称</label>
            <input v-model="modeForm.name" type="text" class="form-input" placeholder="例如：深度思考" />
          </div>
          <div class="form-group">
            <label>图标</label>
            <input v-model="modeForm.icon" type="text" class="form-input icon-input" placeholder="选择一个 emoji" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <input v-model="modeForm.desc" type="text" class="form-input" placeholder="简要描述此模式" />
          </div>
          <div class="form-group">
            <label>提示词</label>
            <textarea v-model="modeForm.prompt" class="form-textarea" rows="4" placeholder="输入此模式使用的提示词..."></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showAddModeModal = false">取消</button>
          <button class="btn-save" @click="saveNewMode">添加</button>
        </div>
      </div>
    </div>

    <!-- 编辑步骤类型弹窗 -->
    <div v-if="showStepTypeModal" class="modal-overlay" @click.self="showStepTypeModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>编辑步骤类型</h3>
          <button class="modal-close" @click="showStepTypeModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>名称</label>
            <input v-model="stepTypeForm.name" type="text" class="form-input" />
          </div>
          <div class="form-group">
            <label>图标</label>
            <input v-model="stepTypeForm.icon" type="text" class="form-input icon-input" />
          </div>
          <div class="form-group">
            <label>颜色</label>
            <div class="color-picker-row">
              <input v-model="stepTypeForm.color" type="color" class="color-picker" />
              <input v-model="stepTypeForm.color" type="text" class="form-input color-text" />
            </div>
          </div>
          <div class="form-group">
            <label>描述</label>
            <input v-model="stepTypeForm.description" type="text" class="form-input" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showStepTypeModal = false">取消</button>
          <button class="btn-save" @click="saveStepType">保存</button>
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

.reasoning-module .orb-1 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.25), rgba(99, 102, 241, 0.15));
  top: -100px;
  right: 20%;
}

.reasoning-module .orb-2 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(59, 130, 246, 0.1));
  bottom: 10%;
  left: 10%;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(59, 130, 246, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(59, 130, 246, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
}

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

.module-badge.reasoning {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(99, 102, 241, 0.2));
  border: 1px solid rgba(59, 130, 246, 0.4);
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);
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

.header-actions {
  display: flex;
  gap: 10px;
}

.btn-secondary, .btn-primary {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #a1a1aa;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.btn-primary {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  border: none;
  color: white;
}

.btn-primary:hover {
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4);
  transform: translateY(-1px);
}

/* Tab 导航 */
.tab-nav {
  display: flex;
  gap: 4px;
  padding: 12px 24px;
  background: rgba(10, 10, 15, 0.8);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.tab-btn {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
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
  color: #60a5fa;
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.3);
}

/* 主内容 */
.module-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  position: relative;
  z-index: 1;
}

.tab-content {
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.content-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #e4e4e7;
  margin: 0;
}

.content-desc {
  font-size: 12px;
  color: #71717a;
  margin: 0;
}

.btn-add {
  padding: 8px 16px;
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 6px;
  color: #60a5fa;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-add:hover {
  background: rgba(59, 130, 246, 0.25);
}

/* 模式卡片 */
.modes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.mode-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 16px;
  position: relative;
  transition: all 0.2s;
}

.mode-card:hover {
  background: rgba(255, 255, 255, 0.04);
}

.mode-card.selected {
  border-color: rgba(59, 130, 246, 0.5);
  background: rgba(59, 130, 246, 0.08);
}

.mode-card.disabled {
  opacity: 0.5;
}

.mode-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.mode-icon-wrapper {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(59, 130, 246, 0.15);
  border-radius: 12px;
  cursor: pointer;
}

.mode-icon {
  font-size: 24px;
}

.mode-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toggle-mini {
  position: relative;
  width: 32px;
  height: 18px;
  cursor: pointer;
}

.toggle-mini input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-track-mini {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 9px;
  transition: all 0.3s;
}

.toggle-track-mini::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 14px;
  height: 14px;
  background: white;
  border-radius: 50%;
  transition: all 0.3s;
}

.toggle-mini input:checked + .toggle-track-mini {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
}

.toggle-mini input:checked + .toggle-track-mini::after {
  transform: translateX(14px);
}

.btn-edit, .btn-delete {
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  color: #a1a1aa;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-edit:hover {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

.btn-delete {
  color: #f87171;
  font-size: 14px;
  padding: 2px 6px;
}

.btn-delete:hover {
  background: rgba(239, 68, 68, 0.2);
}

.mode-body {
  cursor: pointer;
}

.mode-body h4 {
  font-size: 14px;
  font-weight: 600;
  color: #e4e4e7;
  margin: 0 0 4px;
}

.mode-body p {
  font-size: 12px;
  color: #71717a;
  margin: 0;
}

.mode-prompt {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.prompt-label {
  font-size: 10px;
  color: #52525b;
  display: block;
  margin-bottom: 4px;
}

.mode-prompt p {
  font-size: 11px;
  color: #a1a1aa;
  margin: 0;
  font-style: italic;
}

.mode-selected-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 2px 8px;
  background: rgba(59, 130, 246, 0.2);
  border-radius: 4px;
  font-size: 10px;
  color: #60a5fa;
}

/* 统计行 */
.stats-row {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
}

.stat-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-item .stat-icon {
  font-size: 24px;
}

.stat-item .stat-value {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 20px;
  font-weight: 700;
  color: #fff;
}

.stat-item .stat-label {
  font-size: 11px;
  color: #71717a;
  margin-left: -8px;
}

/* 步骤类型 */
.steps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}

.step-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  padding: 14px;
  position: relative;
  border-left: 3px solid var(--step-color);
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.step-icon {
  font-size: 24px;
}

.btn-edit-small {
  padding: 2px 6px;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  color: #71717a;
  font-size: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-edit-small:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #a1a1aa;
}

.step-card h4 {
  font-size: 13px;
  font-weight: 600;
  color: #e4e4e7;
  margin: 0 0 4px;
}

.step-card p {
  font-size: 11px;
  color: #71717a;
  margin: 0;
}

.step-color-preview {
  width: 100%;
  height: 3px;
  border-radius: 2px;
  margin-top: 12px;
}

/* 示例部分 */
.example-section {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 16px;
}

.example-section h3 {
  font-size: 14px;
  font-weight: 600;
  color: #e4e4e7;
  margin: 0 0 16px;
}

.thoughts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.thought-item {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  padding: 14px;
}

.thought-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.thought-task {
  font-size: 13px;
  font-weight: 500;
  color: #e4e4e7;
}

.thought-status {
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 500;
}

.thought-status.completed {
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
}

.thought-status.thinking {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.thought-steps {
  margin-bottom: 12px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-left: 2px solid var(--step-color, rgba(59, 130, 246, 0.3));
  padding-left: 10px;
  margin-left: 8px;
}

.step-number {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(59, 130, 246, 0.2);
  border-radius: 50%;
  font-size: 10px;
  font-weight: 600;
  color: #60a5fa;
}

.step-icon-small {
  font-size: 14px;
}

.step-content {
  font-size: 12px;
  color: #a1a1aa;
}

.thought-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.confidence-label {
  font-size: 10px;
  color: #52525b;
}

.confidence-bar {
  flex: 1;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
  border-radius: 2px;
}

.confidence-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #60a5fa;
}

/* 提示词卡片 */
.prompts-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.prompt-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  overflow: hidden;
}

.prompt-header {
  padding: 14px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.prompt-info {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.prompt-info h4 {
  font-size: 14px;
  font-weight: 600;
  color: #e4e4e7;
  margin: 0;
}

.prompt-id {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #52525b;
  padding: 2px 6px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.prompt-desc {
  font-size: 12px;
  color: #71717a;
  margin: 0;
}

.prompt-content {
  padding: 16px;
  background: rgba(0, 0, 0, 0.2);
}

.prompt-textarea {
  width: 100%;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px;
  color: #e4e4e7;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  line-height: 1.6;
  resize: vertical;
  outline: none;
}

.prompt-textarea:focus {
  border-color: rgba(59, 130, 246, 0.5);
}

.prompt-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.btn-text {
  background: none;
  border: none;
  color: #71717a;
  font-size: 12px;
  cursor: pointer;
}

.btn-text:hover {
  color: #a1a1aa;
}

.btn-small {
  padding: 6px 14px;
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 6px;
  color: #60a5fa;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-small:hover {
  background: rgba(59, 130, 246, 0.25);
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
  padding: 16px;
}

.settings-section.full-width {
  grid-column: span 2;
}

.settings-section h3 {
  font-size: 13px;
  font-weight: 600;
  color: #a1a1aa;
  margin: 0 0 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.setting-item:last-child {
  border-bottom: none;
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
  color: #60a5fa;
  margin-left: auto;
  padding-left: 10px;
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
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.toggle-switch input:checked + .toggle-track {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
}

.toggle-switch input:checked + .toggle-track::after {
  transform: translateX(20px);
}

.setting-slider {
  width: 120px;
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
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.4);
}

/* 流程图 */
.flow-diagram {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  margin-bottom: 12px;
}

.flow-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.flow-icon {
  font-size: 28px;
}

.flow-label {
  font-size: 11px;
  color: #a1a1aa;
}

.flow-arrow {
  font-size: 20px;
  color: #52525b;
}

.flow-desc {
  font-size: 12px;
  color: #71717a;
  text-align: center;
  margin: 0;
}

/* 模态框 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  backdrop-filter: blur(4px);
}

.modal {
  width: 480px;
  background: #18181b;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
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
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border: none;
  border-radius: 6px;
  color: #a1a1aa;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.2s;
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

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #a1a1aa;
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #e4e4e7;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

.form-input:focus {
  border-color: rgba(59, 130, 246, 0.5);
}

.form-input.icon-input {
  width: 60px;
  text-align: center;
  font-size: 20px;
}

.form-textarea {
  width: 100%;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #e4e4e7;
  font-size: 13px;
  line-height: 1.5;
  resize: vertical;
  outline: none;
  transition: border-color 0.2s;
}

.form-textarea:focus {
  border-color: rgba(59, 130, 246, 0.5);
}

.color-picker-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.color-picker {
  width: 40px;
  height: 40px;
  padding: 0;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.color-text {
  flex: 1;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.btn-cancel {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #a1a1aa;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.btn-save {
  padding: 8px 20px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-save:hover {
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
}

/* 滚动条 */
.module-content::-webkit-scrollbar {
  width: 6px;
}

.module-content::-webkit-scrollbar-track {
  background: transparent;
}

.module-content::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}
</style>
