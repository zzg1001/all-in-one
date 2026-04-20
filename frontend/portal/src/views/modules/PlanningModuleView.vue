<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 当前活动标签
const activeTab = ref('strategies')

// 基础配置
const config = reactive({
  enabled: true,
  decompositionStyle: 'hierarchical',
  maxDepth: 3,
  autoReplan: true,
  parallelExecution: true,
  progressTracking: true,
  failureRecovery: 'retry'
})

const planningStats = ref({
  totalPlans: 324,
  avgTasks: 5.8,
  completionRate: '91%',
  avgReplans: 0.4
})

// 分解策略 - 可编辑
const decompositionStrategies = ref([
  {
    id: 'hierarchical',
    name: '层次分解',
    desc: '自顶向下分解为子任务树',
    icon: '🌲',
    enabled: true,
    maxDepth: 5,
    prompt: '请将这个任务按层次结构分解为子任务...'
  },
  {
    id: 'sequential',
    name: '顺序分解',
    desc: '线性步骤序列',
    icon: '📋',
    enabled: true,
    maxDepth: 10,
    prompt: '请将这个任务分解为顺序执行的步骤...'
  },
  {
    id: 'dag',
    name: 'DAG 分解',
    desc: '有向无环图，支持并行',
    icon: '🔀',
    enabled: true,
    maxDepth: 4,
    prompt: '请将任务分解为可并行执行的子任务图...'
  },
  {
    id: 'recursive',
    name: '递归分解',
    desc: '自相似结构，适合复杂问题',
    icon: '🔄',
    enabled: false,
    maxDepth: 6,
    prompt: '请递归地分解这个问题...'
  }
])

// 计划模板 - 可编辑
const planTemplates = ref([
  {
    id: 'data_analysis',
    name: '数据分析模板',
    description: '适用于数据处理和分析任务',
    tasks: [
      { name: '数据获取', duration: '预估 2min' },
      { name: '数据清洗', duration: '预估 5min' },
      { name: '数据分析', duration: '预估 10min' },
      { name: '结果可视化', duration: '预估 5min' },
      { name: '报告生成', duration: '预估 3min' }
    ]
  },
  {
    id: 'code_review',
    name: '代码审查模板',
    description: '适用于代码审查和重构任务',
    tasks: [
      { name: '代码阅读', duration: '预估 10min' },
      { name: '问题识别', duration: '预估 5min' },
      { name: '修改建议', duration: '预估 5min' },
      { name: '测试验证', duration: '预估 10min' }
    ]
  },
  {
    id: 'document_writing',
    name: '文档编写模板',
    description: '适用于文档创作任务',
    tasks: [
      { name: '需求理解', duration: '预估 3min' },
      { name: '大纲设计', duration: '预估 5min' },
      { name: '内容撰写', duration: '预估 15min' },
      { name: '审阅修改', duration: '预估 5min' }
    ]
  }
])

// 失败处理策略 - 可编辑
const failureStrategies = ref([
  { id: 'retry', name: '重试', desc: '失败后自动重试', maxRetries: 3, delay: 1000 },
  { id: 'skip', name: '跳过', desc: '跳过失败步骤继续', continueOnError: true },
  { id: 'abort', name: '终止', desc: '停止整个计划', cleanup: true },
  { id: 'replan', name: '重规划', desc: '重新生成计划', preserveProgress: true }
])

// 当前计划
const currentPlan = ref({
  id: 'plan-001',
  name: '数据分析报告生成',
  status: 'executing',
  progress: 65,
  tasks: [
    { id: 't1', name: '读取数据源', status: 'completed', duration: '2.1s' },
    { id: 't2', name: '数据清洗', status: 'completed', duration: '5.3s' },
    { id: 't3', name: '统计分析', status: 'running', duration: '...' },
    { id: 't4', name: '生成图表', status: 'pending', duration: '-' },
    { id: 't5', name: '输出报告', status: 'pending', duration: '-' }
  ]
})

// 模态框状态
const showStrategyModal = ref(false)
const showTemplateModal = ref(false)
const showAddTemplateModal = ref(false)
const editingStrategy = ref<string | null>(null)
const editingTemplate = ref<string | null>(null)

// 表单数据
const strategyForm = reactive({
  id: '',
  name: '',
  desc: '',
  icon: '',
  enabled: true,
  maxDepth: 5,
  prompt: ''
})

const templateForm = reactive({
  id: '',
  name: '',
  description: '',
  tasks: [] as { name: string; duration: string }[]
})

// 方法
const getStatusIcon = (status: string) => {
  const icons: Record<string, string> = {
    completed: '✅',
    running: '⏳',
    pending: '⏸️',
    failed: '❌'
  }
  return icons[status] || '📝'
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    completed: '#4ade80',
    running: '#fbbf24',
    pending: '#71717a',
    failed: '#f87171'
  }
  return colors[status] || '#71717a'
}

const selectStrategy = (strategyId: string) => {
  config.decompositionStyle = strategyId
}

const editStrategy = (strategy: typeof decompositionStrategies.value[0]) => {
  Object.assign(strategyForm, strategy)
  editingStrategy.value = strategy.id
  showStrategyModal.value = true
}

const saveStrategy = () => {
  const index = decompositionStrategies.value.findIndex(s => s.id === editingStrategy.value)
  if (index !== -1) {
    decompositionStrategies.value[index] = { ...strategyForm }
  }
  showStrategyModal.value = false
  editingStrategy.value = null
}

const toggleStrategy = (strategyId: string) => {
  const strategy = decompositionStrategies.value.find(s => s.id === strategyId)
  if (strategy) {
    strategy.enabled = !strategy.enabled
  }
}

const editTemplate = (template: typeof planTemplates.value[0]) => {
  Object.assign(templateForm, {
    ...template,
    tasks: [...template.tasks.map(t => ({ ...t }))]
  })
  editingTemplate.value = template.id
  showTemplateModal.value = true
}

const saveTemplate = () => {
  const index = planTemplates.value.findIndex(t => t.id === editingTemplate.value)
  if (index !== -1) {
    planTemplates.value[index] = { ...templateForm, tasks: [...templateForm.tasks] }
  }
  showTemplateModal.value = false
  editingTemplate.value = null
}

const addNewTemplate = () => {
  Object.assign(templateForm, {
    id: `template-${Date.now()}`,
    name: '',
    description: '',
    tasks: [{ name: '', duration: '' }]
  })
  showAddTemplateModal.value = true
}

const saveNewTemplate = () => {
  planTemplates.value.push({ ...templateForm, tasks: [...templateForm.tasks] })
  showAddTemplateModal.value = false
}

const deleteTemplate = (templateId: string) => {
  const index = planTemplates.value.findIndex(t => t.id === templateId)
  if (index !== -1) {
    planTemplates.value.splice(index, 1)
  }
}

const addTaskToTemplate = () => {
  templateForm.tasks.push({ name: '', duration: '' })
}

const removeTaskFromTemplate = (index: number) => {
  templateForm.tasks.splice(index, 1)
}

const goBack = () => router.push('/architecture')
</script>

<template>
  <div class="module-view planning-module">
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
        <div class="module-badge planning">
          <span>📋</span>
        </div>
        <div class="header-title">
          <h1>Planning 规划模块</h1>
          <p>任务分解、执行计划、动态调整，支持层次化目标管理</p>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn-secondary">导入模板</button>
        <button class="btn-primary">保存配置</button>
      </div>
    </header>

    <!-- 标签导航 -->
    <nav class="tab-nav">
      <button
        :class="['tab-btn', { active: activeTab === 'strategies' }]"
        @click="activeTab = 'strategies'"
      >
        分解策略
      </button>
      <button
        :class="['tab-btn', { active: activeTab === 'templates' }]"
        @click="activeTab = 'templates'"
      >
        计划模板
      </button>
      <button
        :class="['tab-btn', { active: activeTab === 'execution' }]"
        @click="activeTab = 'execution'"
      >
        执行监控
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
      <!-- 分解策略 Tab -->
      <div v-if="activeTab === 'strategies'" class="tab-content">
        <div class="content-header">
          <h3>任务分解策略</h3>
          <p class="content-desc">选择和配置任务分解方式</p>
        </div>

        <div class="strategies-grid">
          <div
            v-for="strategy in decompositionStrategies"
            :key="strategy.id"
            :class="['strategy-card', { selected: config.decompositionStyle === strategy.id, disabled: !strategy.enabled }]"
          >
            <div class="strategy-header">
              <div class="strategy-icon-wrapper" @click="selectStrategy(strategy.id)">
                <span class="strategy-icon">{{ strategy.icon }}</span>
              </div>
              <div class="strategy-controls">
                <label class="toggle-mini">
                  <input type="checkbox" :checked="strategy.enabled" @change="toggleStrategy(strategy.id)" />
                  <span class="toggle-track-mini"></span>
                </label>
                <button class="btn-edit" @click="editStrategy(strategy)">编辑</button>
              </div>
            </div>
            <div class="strategy-body" @click="selectStrategy(strategy.id)">
              <h4>{{ strategy.name }}</h4>
              <p>{{ strategy.desc }}</p>
            </div>
            <div class="strategy-meta">
              <span class="meta-item">
                <span class="meta-label">最大深度</span>
                <span class="meta-value">{{ strategy.maxDepth }}</span>
              </span>
            </div>
            <div v-if="config.decompositionStyle === strategy.id" class="strategy-selected-badge">当前使用</div>
          </div>
        </div>

        <!-- 统计信息 -->
        <div class="stats-row">
          <div class="stat-item">
            <span class="stat-icon">📊</span>
            <span class="stat-value">{{ planningStats.totalPlans }}</span>
            <span class="stat-label">计划总数</span>
          </div>
          <div class="stat-item">
            <span class="stat-icon">📝</span>
            <span class="stat-value">{{ planningStats.avgTasks }}</span>
            <span class="stat-label">平均任务数</span>
          </div>
          <div class="stat-item">
            <span class="stat-icon">✅</span>
            <span class="stat-value">{{ planningStats.completionRate }}</span>
            <span class="stat-label">完成率</span>
          </div>
          <div class="stat-item">
            <span class="stat-icon">🔄</span>
            <span class="stat-value">{{ planningStats.avgReplans }}</span>
            <span class="stat-label">平均重规划</span>
          </div>
        </div>
      </div>

      <!-- 计划模板 Tab -->
      <div v-if="activeTab === 'templates'" class="tab-content">
        <div class="content-header">
          <h3>计划模板管理</h3>
          <button class="btn-add" @click="addNewTemplate">+ 添加模板</button>
        </div>

        <div class="templates-list">
          <div v-for="template in planTemplates" :key="template.id" class="template-card">
            <div class="template-header">
              <div class="template-info">
                <h4>{{ template.name }}</h4>
                <span class="template-id">{{ template.id }}</span>
              </div>
              <div class="template-actions">
                <button class="btn-edit" @click="editTemplate(template)">编辑</button>
                <button class="btn-delete" @click="deleteTemplate(template.id)">删除</button>
              </div>
            </div>
            <p class="template-desc">{{ template.description }}</p>
            <div class="template-tasks">
              <div v-for="(task, index) in template.tasks" :key="index" class="template-task">
                <span class="task-number">{{ index + 1 }}</span>
                <span class="task-name">{{ task.name }}</span>
                <span class="task-duration">{{ task.duration }}</span>
              </div>
            </div>
            <div class="template-footer">
              <span class="task-count">{{ template.tasks.length }} 个步骤</span>
              <button class="btn-use">使用此模板</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 执行监控 Tab -->
      <div v-if="activeTab === 'execution'" class="tab-content">
        <div class="content-header">
          <h3>当前执行计划</h3>
          <div class="execution-controls">
            <button class="btn-secondary-sm">暂停</button>
            <button class="btn-danger-sm">取消</button>
          </div>
        </div>

        <div class="execution-panel">
          <div class="plan-info">
            <div class="plan-header">
              <h4>{{ currentPlan.name }}</h4>
              <span :class="['plan-status', currentPlan.status]">
                {{ currentPlan.status === 'executing' ? '执行中' : '已完成' }}
              </span>
            </div>
            <div class="plan-progress">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: currentPlan.progress + '%' }"></div>
              </div>
              <span class="progress-text">{{ currentPlan.progress }}%</span>
            </div>
          </div>

          <div class="task-timeline">
            <div
              v-for="(task, index) in currentPlan.tasks"
              :key="task.id"
              :class="['timeline-item', task.status]"
            >
              <div class="timeline-connector">
                <div class="connector-line" v-if="index < currentPlan.tasks.length - 1"></div>
              </div>
              <div class="timeline-node">
                <span class="node-icon">{{ getStatusIcon(task.status) }}</span>
              </div>
              <div class="timeline-content">
                <span class="task-name">{{ task.name }}</span>
                <span class="task-duration">{{ task.duration }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 失败处理策略 -->
        <div class="failure-section">
          <h3>失败处理策略</h3>
          <div class="failure-strategies">
            <div
              v-for="strategy in failureStrategies"
              :key="strategy.id"
              :class="['failure-card', { selected: config.failureRecovery === strategy.id }]"
              @click="config.failureRecovery = strategy.id"
            >
              <div class="failure-info">
                <span class="failure-name">{{ strategy.name }}</span>
                <span class="failure-desc">{{ strategy.desc }}</span>
              </div>
              <span v-if="config.failureRecovery === strategy.id" class="check-mark">✓</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 基础设置 Tab -->
      <div v-if="activeTab === 'settings'" class="tab-content">
        <div class="settings-grid">
          <div class="settings-section">
            <h3>执行配置</h3>

            <div class="setting-item">
              <div class="setting-label">
                <span>最大分解深度</span>
                <span class="setting-value">{{ config.maxDepth }} 层</span>
              </div>
              <input v-model.number="config.maxDepth" type="range" min="1" max="5" class="setting-slider" />
            </div>

            <div class="setting-item">
              <div class="setting-label">
                <span>并行执行</span>
                <span class="setting-desc">允许无依赖任务同时执行</span>
              </div>
              <label class="toggle-switch">
                <input v-model="config.parallelExecution" type="checkbox" />
                <span class="toggle-track"></span>
              </label>
            </div>

            <div class="setting-item">
              <div class="setting-label">
                <span>进度追踪</span>
                <span class="setting-desc">实时更新任务执行状态</span>
              </div>
              <label class="toggle-switch">
                <input v-model="config.progressTracking" type="checkbox" />
                <span class="toggle-track"></span>
              </label>
            </div>
          </div>

          <div class="settings-section">
            <h3>自动化</h3>

            <div class="setting-item">
              <div class="setting-label">
                <span>自动重规划</span>
                <span class="setting-desc">失败时自动调整计划</span>
              </div>
              <label class="toggle-switch">
                <input v-model="config.autoReplan" type="checkbox" />
                <span class="toggle-track"></span>
              </label>
            </div>
          </div>

          <div class="settings-section full-width">
            <h3>规划流程说明</h3>
            <div class="flow-diagram">
              <div class="flow-step">
                <span class="flow-icon">🎯</span>
                <span class="flow-label">目标定义</span>
              </div>
              <div class="flow-arrow">→</div>
              <div class="flow-step">
                <span class="flow-icon">🔀</span>
                <span class="flow-label">任务分解</span>
              </div>
              <div class="flow-arrow">→</div>
              <div class="flow-step">
                <span class="flow-icon">🔗</span>
                <span class="flow-label">依赖分析</span>
              </div>
              <div class="flow-arrow">→</div>
              <div class="flow-step">
                <span class="flow-icon">▶️</span>
                <span class="flow-label">调度执行</span>
              </div>
              <div class="flow-arrow">→</div>
              <div class="flow-step">
                <span class="flow-icon">📊</span>
                <span class="flow-label">监控反馈</span>
              </div>
            </div>
            <p class="flow-desc">支持动态调整和失败恢复，确保计划顺利完成</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑策略弹窗 -->
    <div v-if="showStrategyModal" class="modal-overlay" @click.self="showStrategyModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>编辑分解策略</h3>
          <button class="modal-close" @click="showStrategyModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>策略名称</label>
            <input v-model="strategyForm.name" type="text" class="form-input" />
          </div>
          <div class="form-group">
            <label>图标</label>
            <input v-model="strategyForm.icon" type="text" class="form-input icon-input" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <input v-model="strategyForm.desc" type="text" class="form-input" />
          </div>
          <div class="form-group">
            <label>最大分解深度</label>
            <input v-model.number="strategyForm.maxDepth" type="number" min="1" max="10" class="form-input" />
          </div>
          <div class="form-group">
            <label>分解提示词</label>
            <textarea v-model="strategyForm.prompt" class="form-textarea" rows="4"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showStrategyModal = false">取消</button>
          <button class="btn-save" @click="saveStrategy">保存</button>
        </div>
      </div>
    </div>

    <!-- 编辑模板弹窗 -->
    <div v-if="showTemplateModal" class="modal-overlay" @click.self="showTemplateModal = false">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h3>编辑计划模板</h3>
          <button class="modal-close" @click="showTemplateModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>模板名称</label>
            <input v-model="templateForm.name" type="text" class="form-input" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <input v-model="templateForm.description" type="text" class="form-input" />
          </div>
          <div class="form-group">
            <label>任务步骤</label>
            <div class="task-editor">
              <div v-for="(task, index) in templateForm.tasks" :key="index" class="task-row">
                <span class="task-index">{{ index + 1 }}</span>
                <input v-model="task.name" type="text" class="form-input" placeholder="任务名称" />
                <input v-model="task.duration" type="text" class="form-input duration-input" placeholder="预估时间" />
                <button class="btn-remove" @click="removeTaskFromTemplate(index)">×</button>
              </div>
              <button class="btn-add-task" @click="addTaskToTemplate">+ 添加步骤</button>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showTemplateModal = false">取消</button>
          <button class="btn-save" @click="saveTemplate">保存</button>
        </div>
      </div>
    </div>

    <!-- 添加模板弹窗 -->
    <div v-if="showAddTemplateModal" class="modal-overlay" @click.self="showAddTemplateModal = false">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h3>添加计划模板</h3>
          <button class="modal-close" @click="showAddTemplateModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>模板名称</label>
            <input v-model="templateForm.name" type="text" class="form-input" placeholder="例如：项目开发流程" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <input v-model="templateForm.description" type="text" class="form-input" placeholder="简要描述此模板的用途" />
          </div>
          <div class="form-group">
            <label>任务步骤</label>
            <div class="task-editor">
              <div v-for="(task, index) in templateForm.tasks" :key="index" class="task-row">
                <span class="task-index">{{ index + 1 }}</span>
                <input v-model="task.name" type="text" class="form-input" placeholder="任务名称" />
                <input v-model="task.duration" type="text" class="form-input duration-input" placeholder="预估时间" />
                <button class="btn-remove" @click="removeTaskFromTemplate(index)">×</button>
              </div>
              <button class="btn-add-task" @click="addTaskToTemplate">+ 添加步骤</button>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showAddTemplateModal = false">取消</button>
          <button class="btn-save" @click="saveNewTemplate">添加</button>
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

.planning-module .orb-1 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.25), rgba(16, 185, 129, 0.15));
  top: -100px;
  right: 20%;
}

.planning-module .orb-2 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, rgba(52, 211, 153, 0.2), rgba(34, 197, 94, 0.1));
  bottom: 10%;
  left: 10%;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(34, 197, 94, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(34, 197, 94, 0.03) 1px, transparent 1px);
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

.module-badge.planning {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(16, 185, 129, 0.2));
  border: 1px solid rgba(34, 197, 94, 0.4);
  box-shadow: 0 0 20px rgba(34, 197, 94, 0.2);
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
  background: linear-gradient(135deg, #22c55e, #10b981);
  border: none;
  color: white;
}

.btn-primary:hover {
  box-shadow: 0 4px 20px rgba(34, 197, 94, 0.4);
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
  color: #4ade80;
  background: rgba(34, 197, 94, 0.1);
  border-color: rgba(34, 197, 94, 0.3);
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
  background: rgba(34, 197, 94, 0.15);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 6px;
  color: #4ade80;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-add:hover {
  background: rgba(34, 197, 94, 0.25);
}

/* 策略卡片 */
.strategies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.strategy-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 16px;
  position: relative;
  transition: all 0.2s;
}

.strategy-card:hover {
  background: rgba(255, 255, 255, 0.04);
}

.strategy-card.selected {
  border-color: rgba(34, 197, 94, 0.5);
  background: rgba(34, 197, 94, 0.08);
}

.strategy-card.disabled {
  opacity: 0.5;
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.strategy-icon-wrapper {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(34, 197, 94, 0.15);
  border-radius: 10px;
  cursor: pointer;
}

.strategy-icon {
  font-size: 22px;
}

.strategy-controls {
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
  background: linear-gradient(135deg, #22c55e, #10b981);
}

.toggle-mini input:checked + .toggle-track-mini::after {
  transform: translateX(14px);
}

.btn-edit {
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
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
}

.strategy-body {
  cursor: pointer;
}

.strategy-body h4 {
  font-size: 14px;
  font-weight: 600;
  color: #e4e4e7;
  margin: 0 0 4px;
}

.strategy-body p {
  font-size: 12px;
  color: #71717a;
  margin: 0;
}

.strategy-meta {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-label {
  font-size: 11px;
  color: #52525b;
}

.meta-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #4ade80;
}

.strategy-selected-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 2px 8px;
  background: rgba(34, 197, 94, 0.2);
  border-radius: 4px;
  font-size: 10px;
  color: #4ade80;
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

/* 模板列表 */
.templates-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.template-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 16px;
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.template-info h4 {
  font-size: 14px;
  font-weight: 600;
  color: #e4e4e7;
  margin: 0 0 4px;
}

.template-id {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #52525b;
}

.template-actions {
  display: flex;
  gap: 8px;
}

.btn-delete {
  padding: 4px 8px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 4px;
  color: #f87171;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-delete:hover {
  background: rgba(239, 68, 68, 0.2);
}

.template-desc {
  font-size: 12px;
  color: #71717a;
  margin: 0 0 12px;
}

.template-tasks {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}

.template-task {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.template-task:last-child {
  border-bottom: none;
}

.task-number {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(34, 197, 94, 0.2);
  border-radius: 50%;
  font-size: 10px;
  font-weight: 600;
  color: #4ade80;
}

.task-name {
  flex: 1;
  font-size: 12px;
  color: #a1a1aa;
}

.task-duration {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #52525b;
}

.template-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-count {
  font-size: 11px;
  color: #52525b;
}

.btn-use {
  padding: 6px 12px;
  background: rgba(34, 197, 94, 0.15);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 6px;
  color: #4ade80;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-use:hover {
  background: rgba(34, 197, 94, 0.25);
}

/* 执行监控 */
.execution-controls {
  display: flex;
  gap: 8px;
}

.btn-secondary-sm {
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: #a1a1aa;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary-sm:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.btn-danger-sm {
  padding: 6px 12px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 6px;
  color: #f87171;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-danger-sm:hover {
  background: rgba(239, 68, 68, 0.2);
}

.execution-panel {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

.plan-info {
  margin-bottom: 20px;
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.plan-header h4 {
  font-size: 16px;
  font-weight: 600;
  color: #e4e4e7;
  margin: 0;
}

.plan-status {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.plan-status.executing {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
}

.plan-status.completed {
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
}

.plan-progress {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #22c55e, #4ade80);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.progress-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  font-weight: 600;
  color: #4ade80;
  min-width: 40px;
}

/* 时间线 */
.task-timeline {
  display: flex;
  flex-direction: column;
}

.timeline-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  position: relative;
}

.timeline-connector {
  width: 24px;
  position: relative;
  display: flex;
  justify-content: center;
}

.connector-line {
  position: absolute;
  top: 28px;
  width: 2px;
  height: calc(100% + 12px);
  background: rgba(255, 255, 255, 0.1);
}

.timeline-item.completed .connector-line {
  background: rgba(34, 197, 94, 0.4);
}

.timeline-node {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 50%;
  font-size: 12px;
  flex-shrink: 0;
}

.timeline-item.completed .timeline-node {
  background: rgba(34, 197, 94, 0.2);
}

.timeline-item.running .timeline-node {
  background: rgba(251, 191, 36, 0.2);
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.timeline-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0 20px;
}

.timeline-content .task-name {
  font-size: 13px;
  color: #a1a1aa;
}

.timeline-item.completed .timeline-content .task-name {
  color: #e4e4e7;
}

.timeline-item.running .timeline-content .task-name {
  color: #fbbf24;
}

.timeline-content .task-duration {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #52525b;
}

/* 失败处理 */
.failure-section {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 16px;
}

.failure-section h3 {
  font-size: 14px;
  font-weight: 600;
  color: #e4e4e7;
  margin: 0 0 14px;
}

.failure-strategies {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.failure-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.failure-card:hover {
  background: rgba(255, 255, 255, 0.04);
}

.failure-card.selected {
  background: rgba(34, 197, 94, 0.1);
  border-color: rgba(34, 197, 94, 0.4);
}

.failure-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.failure-name {
  font-size: 13px;
  font-weight: 500;
  color: #e4e4e7;
}

.failure-desc {
  font-size: 11px;
  color: #52525b;
}

.check-mark {
  color: #4ade80;
  font-size: 14px;
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
  color: #4ade80;
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
  background: linear-gradient(135deg, #22c55e, #10b981);
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
  background: linear-gradient(135deg, #22c55e, #10b981);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(34, 197, 94, 0.4);
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

.modal.modal-lg {
  width: 600px;
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
  max-height: 60vh;
  overflow-y: auto;
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
  border-color: rgba(34, 197, 94, 0.5);
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
  border-color: rgba(34, 197, 94, 0.5);
}

/* 任务编辑器 */
.task-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.task-index {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(34, 197, 94, 0.2);
  border-radius: 50%;
  font-size: 11px;
  font-weight: 600;
  color: #4ade80;
  flex-shrink: 0;
}

.duration-input {
  width: 120px;
  flex-shrink: 0;
}

.btn-remove {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 6px;
  color: #f87171;
  font-size: 16px;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s;
}

.btn-remove:hover {
  background: rgba(239, 68, 68, 0.2);
}

.btn-add-task {
  padding: 8px 12px;
  background: transparent;
  border: 1px dashed rgba(34, 197, 94, 0.3);
  border-radius: 6px;
  color: #4ade80;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 4px;
}

.btn-add-task:hover {
  background: rgba(34, 197, 94, 0.1);
  border-style: solid;
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
  background: linear-gradient(135deg, #22c55e, #10b981);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-save:hover {
  box-shadow: 0 4px 15px rgba(34, 197, 94, 0.4);
}

/* 滚动条 */
.module-content::-webkit-scrollbar,
.modal-body::-webkit-scrollbar {
  width: 6px;
}

.module-content::-webkit-scrollbar-track,
.modal-body::-webkit-scrollbar-track {
  background: transparent;
}

.module-content::-webkit-scrollbar-thumb,
.modal-body::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}
</style>
