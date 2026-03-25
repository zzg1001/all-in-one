<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const config = reactive({
  enabled: true,
  schedulingMode: 'dag',
  maxParallelTasks: 5,
  taskTimeout: 300,
  retryPolicy: 'exponential',
  maxRetries: 3,
  failoverEnabled: true
})

const orchestratorStats = ref({
  activeWorkflows: 12,
  pendingTasks: 28,
  completedToday: 156,
  avgLatency: '2.4s'
})

const schedulingModes = [
  { id: 'sequential', name: '顺序执行', desc: '任务按顺序依次执行', icon: '📋' },
  { id: 'parallel', name: '并行执行', desc: '独立任务同时执行', icon: '⚡' },
  { id: 'dag', name: 'DAG 编排', desc: '有向无环图依赖调度', icon: '🔀' },
  { id: 'priority', name: '优先级调度', desc: '按优先级动态调度', icon: '🎯' }
]

const retryPolicies = [
  { id: 'none', name: '不重试' },
  { id: 'fixed', name: '固定间隔' },
  { id: 'exponential', name: '指数退避' },
  { id: 'linear', name: '线性增长' }
]

const activeWorkflows = ref([
  {
    id: 'wf-001',
    name: '数据处理流水线',
    status: 'running',
    progress: 65,
    tasks: [
      { name: '数据采集', status: 'completed' },
      { name: '数据清洗', status: 'completed' },
      { name: '特征提取', status: 'running' },
      { name: '模型训练', status: 'pending' },
      { name: '结果输出', status: 'pending' }
    ],
    startTime: '10:15:00',
    estimatedEnd: '10:45:00'
  },
  {
    id: 'wf-002',
    name: '报告生成任务',
    status: 'running',
    progress: 40,
    tasks: [
      { name: '数据查询', status: 'completed' },
      { name: '图表生成', status: 'running' },
      { name: '文档组装', status: 'pending' }
    ],
    startTime: '10:20:00',
    estimatedEnd: '10:35:00'
  }
])

const taskQueue = ref([
  { id: 't1', name: '用户分析任务', priority: 'high', agent: 'agent-001', wait: '0s' },
  { id: 't2', name: '日志处理', priority: 'medium', agent: 'agent-003', wait: '12s' },
  { id: 't3', name: '缓存更新', priority: 'low', agent: 'agent-002', wait: '45s' },
  { id: 't4', name: '通知发送', priority: 'medium', agent: 'agent-004', wait: '23s' }
])

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    completed: '#4ade80',
    running: '#fbbf24',
    pending: '#71717a',
    failed: '#f87171'
  }
  return colors[status] || '#71717a'
}

const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = {
    high: '#f87171',
    medium: '#fbbf24',
    low: '#4ade80'
  }
  return colors[priority] || '#71717a'
}

const goBack = () => router.push('/architecture')
</script>

<template>
  <div class="module-view orchestrator-module">
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
        <div class="module-badge">
          <span>🎭</span>
        </div>
        <div class="header-title">
          <h1>Orchestrator 编排器</h1>
          <p>任务分配、负载均衡、故障转移、流程编排</p>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn-secondary">暂停调度</button>
        <button class="btn-primary">保存配置</button>
      </div>
    </header>

    <!-- 主内容 -->
    <div class="module-content">
      <!-- 左侧配置 -->
      <div class="config-panel">
        <div class="panel-section">
          <h3>调度模式</h3>
          <div class="mode-cards">
            <div
              v-for="mode in schedulingModes"
              :key="mode.id"
              :class="['mode-card', { selected: config.schedulingMode === mode.id }]"
              @click="config.schedulingMode = mode.id"
            >
              <span class="mode-icon">{{ mode.icon }}</span>
              <div class="mode-info">
                <span class="mode-name">{{ mode.name }}</span>
                <span class="mode-desc">{{ mode.desc }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="panel-section">
          <h3>执行配置</h3>

          <div class="config-item">
            <div class="config-label">
              <span>最大并行任务</span>
              <span class="config-value">{{ config.maxParallelTasks }}</span>
            </div>
            <input v-model.number="config.maxParallelTasks" type="range" min="1" max="20" class="config-slider" />
          </div>

          <div class="config-item">
            <div class="config-label">
              <span>任务超时 (秒)</span>
              <span class="config-value">{{ config.taskTimeout }}s</span>
            </div>
            <input v-model.number="config.taskTimeout" type="range" min="60" max="600" step="30" class="config-slider" />
          </div>

          <div class="config-item">
            <div class="config-label">
              <span>故障转移</span>
              <span class="config-desc">任务失败时自动转移</span>
            </div>
            <label class="toggle-switch">
              <input v-model="config.failoverEnabled" type="checkbox" />
              <span class="toggle-track"></span>
            </label>
          </div>
        </div>

        <div class="panel-section">
          <h3>重试策略</h3>

          <div class="retry-options">
            <button
              v-for="policy in retryPolicies"
              :key="policy.id"
              :class="['retry-btn', { selected: config.retryPolicy === policy.id }]"
              @click="config.retryPolicy = policy.id"
            >
              {{ policy.name }}
            </button>
          </div>

          <div class="config-item">
            <div class="config-label">
              <span>最大重试次数</span>
              <span class="config-value">{{ config.maxRetries }}</span>
            </div>
            <input v-model.number="config.maxRetries" type="range" min="0" max="10" class="config-slider" />
          </div>
        </div>

        <!-- 任务队列 -->
        <div class="panel-section">
          <h3>待处理队列</h3>
          <div class="task-queue">
            <div v-for="task in taskQueue" :key="task.id" class="queue-item">
              <span class="task-priority" :style="{ background: getPriorityColor(task.priority) }"></span>
              <div class="task-info">
                <span class="task-name">{{ task.name }}</span>
                <span class="task-agent">{{ task.agent }}</span>
              </div>
              <span class="task-wait">等待 {{ task.wait }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧状态 -->
      <div class="status-panel">
        <div class="stats-grid">
          <div class="stat-card">
            <span class="stat-icon">🔄</span>
            <div class="stat-info">
              <span class="stat-value">{{ orchestratorStats.activeWorkflows }}</span>
              <span class="stat-label">活跃工作流</span>
            </div>
          </div>
          <div class="stat-card">
            <span class="stat-icon">⏳</span>
            <div class="stat-info">
              <span class="stat-value">{{ orchestratorStats.pendingTasks }}</span>
              <span class="stat-label">待处理任务</span>
            </div>
          </div>
          <div class="stat-card">
            <span class="stat-icon">✅</span>
            <div class="stat-info">
              <span class="stat-value">{{ orchestratorStats.completedToday }}</span>
              <span class="stat-label">今日完成</span>
            </div>
          </div>
          <div class="stat-card">
            <span class="stat-icon">⚡</span>
            <div class="stat-info">
              <span class="stat-value">{{ orchestratorStats.avgLatency }}</span>
              <span class="stat-label">平均延迟</span>
            </div>
          </div>
        </div>

        <div class="workflows-panel">
          <div class="list-header">
            <h3>活跃工作流</h3>
            <button class="btn-text">查看全部</button>
          </div>
          <div class="workflow-items">
            <div v-for="workflow in activeWorkflows" :key="workflow.id" class="workflow-card">
              <div class="workflow-header">
                <div class="workflow-info">
                  <span class="workflow-name">{{ workflow.name }}</span>
                  <span class="workflow-id">{{ workflow.id }}</span>
                </div>
                <span class="workflow-progress">{{ workflow.progress }}%</span>
              </div>

              <div class="workflow-progress-bar">
                <div class="progress-fill" :style="{ width: workflow.progress + '%' }"></div>
              </div>

              <div class="workflow-tasks">
                <div
                  v-for="(task, index) in workflow.tasks"
                  :key="index"
                  class="task-node"
                >
                  <span class="node-dot" :style="{ background: getStatusColor(task.status) }"></span>
                  <span class="node-name">{{ task.name }}</span>
                  <span v-if="index < workflow.tasks.length - 1" class="node-connector"></span>
                </div>
              </div>

              <div class="workflow-time">
                <span>开始: {{ workflow.startTime }}</span>
                <span>预计: {{ workflow.estimatedEnd }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="architecture-hint">
          <div class="hint-icon">🎯</div>
          <div class="hint-content">
            <h4>编排流程</h4>
            <p>任务提交 → 依赖分析 → 调度分配 → 执行监控 → 结果聚合</p>
            <p>支持 DAG 工作流和动态故障转移</p>
          </div>
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

.orchestrator-module .orb-1 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.25), rgba(139, 92, 246, 0.15));
  top: -100px;
  right: 20%;
}

.orchestrator-module .orb-2 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, rgba(192, 132, 252, 0.2), rgba(168, 85, 247, 0.1));
  bottom: 10%;
  left: 10%;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(168, 85, 247, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(168, 85, 247, 0.03) 1px, transparent 1px);
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
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.2), rgba(139, 92, 246, 0.2));
  border: 1px solid rgba(168, 85, 247, 0.4);
  box-shadow: 0 0 20px rgba(168, 85, 247, 0.2);
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
  background: linear-gradient(135deg, #a855f7, #8b5cf6);
  border: none;
  color: white;
}

.btn-primary:hover {
  box-shadow: 0 4px 20px rgba(168, 85, 247, 0.4);
  transform: translateY(-1px);
}

.module-content {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 20px;
  padding: 20px 24px;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.config-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  padding-right: 10px;
}

.panel-section {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 16px;
}

.panel-section h3 {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 13px;
  font-weight: 600;
  color: #a1a1aa;
  margin: 0 0 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.mode-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.mode-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-card:hover {
  background: rgba(255, 255, 255, 0.04);
}

.mode-card.selected {
  background: rgba(168, 85, 247, 0.1);
  border-color: rgba(168, 85, 247, 0.4);
}

.mode-icon {
  font-size: 18px;
}

.mode-info {
  flex: 1;
  min-width: 0;
}

.mode-name {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #e4e4e7;
}

.mode-desc {
  display: block;
  font-size: 10px;
  color: #52525b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.config-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.config-item:last-child {
  border-bottom: none;
}

.config-label {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.config-label > span:first-child {
  font-size: 13px;
  font-weight: 500;
  color: #e4e4e7;
}

.config-desc {
  font-size: 11px;
  color: #52525b;
}

.config-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #c084fc;
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
  background: linear-gradient(135deg, #a855f7, #8b5cf6);
}

.toggle-switch input:checked + .toggle-track::after {
  transform: translateX(20px);
}

.config-slider {
  width: 120px;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  appearance: none;
  cursor: pointer;
}

.config-slider::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  background: linear-gradient(135deg, #a855f7, #8b5cf6);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(168, 85, 247, 0.4);
}

.retry-options {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.retry-btn {
  flex: 1;
  padding: 8px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  color: #a1a1aa;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-btn:hover {
  background: rgba(255, 255, 255, 0.06);
}

.retry-btn.selected {
  background: rgba(168, 85, 247, 0.15);
  border-color: rgba(168, 85, 247, 0.4);
  color: #c084fc;
}

.task-queue {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 6px;
}

.task-priority {
  width: 4px;
  height: 24px;
  border-radius: 2px;
}

.task-info {
  flex: 1;
}

.task-name {
  display: block;
  font-size: 11px;
  font-weight: 500;
  color: #e4e4e7;
}

.task-agent {
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: #52525b;
}

.task-wait {
  font-size: 10px;
  color: #71717a;
}

.status-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  padding-right: 10px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
}

.stat-icon {
  font-size: 20px;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
}

.stat-label {
  font-size: 10px;
  color: #71717a;
}

.workflows-panel {
  flex: 1;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.list-header h3 {
  font-size: 13px;
  font-weight: 600;
  color: #e4e4e7;
  margin: 0;
}

.btn-text {
  background: none;
  border: none;
  color: #c084fc;
  font-size: 12px;
  cursor: pointer;
}

.btn-text:hover {
  text-decoration: underline;
}

.workflow-items {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.workflow-card {
  padding: 14px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 10px;
  margin-bottom: 10px;
}

.workflow-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.workflow-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.workflow-name {
  font-size: 13px;
  font-weight: 500;
  color: #e4e4e7;
}

.workflow-id {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #52525b;
}

.workflow-progress {
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  font-weight: 600;
  color: #c084fc;
}

.workflow-progress-bar {
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 12px;
}

.workflow-progress-bar .progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #a855f7, #c084fc);
  border-radius: 2px;
  transition: width 0.5s ease;
}

.workflow-tasks {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 10px;
  overflow-x: auto;
}

.task-node {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.node-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.node-name {
  font-size: 10px;
  color: #a1a1aa;
  white-space: nowrap;
}

.node-connector {
  width: 16px;
  height: 1px;
  background: rgba(255, 255, 255, 0.2);
  margin: 0 2px;
}

.workflow-time {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: #52525b;
}

.architecture-hint {
  display: flex;
  gap: 12px;
  padding: 14px;
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.08), rgba(139, 92, 246, 0.05));
  border: 1px solid rgba(168, 85, 247, 0.2);
  border-radius: 10px;
}

.hint-icon {
  font-size: 24px;
}

.hint-content h4 {
  font-size: 12px;
  font-weight: 600;
  color: #d8b4fe;
  margin: 0 0 6px;
}

.hint-content p {
  font-size: 11px;
  color: #71717a;
  margin: 0 0 4px;
}

.config-panel::-webkit-scrollbar,
.status-panel::-webkit-scrollbar,
.workflow-items::-webkit-scrollbar {
  width: 4px;
}

.config-panel::-webkit-scrollbar-track,
.status-panel::-webkit-scrollbar-track,
.workflow-items::-webkit-scrollbar-track {
  background: transparent;
}

.config-panel::-webkit-scrollbar-thumb,
.status-panel::-webkit-scrollbar-thumb,
.workflow-items::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}
</style>
