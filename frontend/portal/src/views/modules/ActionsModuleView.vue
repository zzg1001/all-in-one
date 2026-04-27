<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const config = reactive({
  enabled: true,
  executionMode: 'async',
  outputFormat: 'structured',
  feedbackCollection: true,
  streamOutput: true,
  maxQueueSize: 100
})

const actionStats = ref({
  totalActions: 2847,
  pendingActions: 3,
  avgExecTime: '1.8s',
  feedbackRate: '68%'
})

const executionModes = [
  { id: 'sync', name: '同步执行', desc: '等待完成后返回', icon: '⏳' },
  { id: 'async', name: '异步执行', desc: '立即返回，后台处理', icon: '⚡' },
  { id: 'stream', name: '流式输出', desc: '实时返回部分结果', icon: '🌊' }
]

const outputFormats = [
  { id: 'text', name: '纯文本', desc: '简单文本输出' },
  { id: 'structured', name: '结构化', desc: 'JSON/Markdown 格式' },
  { id: 'multimodal', name: '多模态', desc: '支持图像/音频' }
]

const actionQueue = ref([
  { id: 'a1', type: 'response', content: '正在生成回复...', status: 'executing', progress: 75 },
  { id: 'a2', type: 'file_write', content: '写入 report.xlsx', status: 'pending', progress: 0 },
  { id: 'a3', type: 'notification', content: '发送完成通知', status: 'pending', progress: 0 }
])

const recentActions = ref([
  { id: '1', type: 'response', content: '已完成数据分析并生成报告', time: '10:30:15', duration: '2.1s', feedback: 'positive' },
  { id: '2', type: 'file_write', content: '成功保存 output.json', time: '10:28:42', duration: '0.3s', feedback: 'none' },
  { id: '3', type: 'api_call', content: '调用外部 API 获取数据', time: '10:25:00', duration: '1.5s', feedback: 'positive' },
  { id: '4', type: 'response', content: '生成代码并解释实现思路', time: '10:20:00', duration: '4.2s', feedback: 'negative' }
])

const getTypeIcon = (type: string) => {
  const icons: Record<string, string> = {
    response: '💬',
    file_write: '📝',
    api_call: '🌐',
    notification: '🔔'
  }
  return icons[type] || '⚡'
}

const getFeedbackIcon = (feedback: string) => {
  const icons: Record<string, string> = {
    positive: '👍',
    negative: '👎',
    none: '—'
  }
  return icons[feedback] || '—'
}

const goBack = () => router.push('/architecture')
</script>

<template>
  <div class="module-view actions-module">
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
        <div class="module-badge actions">
          <span>⚡</span>
        </div>
        <div class="header-title">
          <h1>Actions 行动模块</h1>
          <p>执行引擎、输出格式化、反馈收集，支持多模态输出</p>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn-secondary">清空队列</button>
        <button class="btn-primary">保存配置</button>
      </div>
    </header>

    <!-- 主内容 -->
    <div class="module-content">
      <!-- 左侧配置 -->
      <div class="config-panel">
        <div class="panel-section">
          <h3>执行模式</h3>
          <div class="mode-cards">
            <div
              v-for="mode in executionModes"
              :key="mode.id"
              :class="['mode-card', { selected: config.executionMode === mode.id }]"
              @click="config.executionMode = mode.id"
            >
              <span class="mode-icon">{{ mode.icon }}</span>
              <div class="mode-info">
                <span class="mode-name">{{ mode.name }}</span>
                <span class="mode-desc">{{ mode.desc }}</span>
              </div>
              <span v-if="config.executionMode === mode.id" class="mode-check">✓</span>
            </div>
          </div>
        </div>

        <div class="panel-section">
          <h3>输出配置</h3>

          <div class="config-item vertical">
            <div class="config-label">
              <span>输出格式</span>
            </div>
            <div class="format-options">
              <button
                v-for="format in outputFormats"
                :key="format.id"
                :class="['format-btn', { selected: config.outputFormat === format.id }]"
                @click="config.outputFormat = format.id"
              >
                {{ format.name }}
              </button>
            </div>
          </div>

          <div class="config-item">
            <div class="config-label">
              <span>流式输出</span>
              <span class="config-desc">实时返回生成内容</span>
            </div>
            <label class="toggle-switch">
              <input v-model="config.streamOutput" type="checkbox" />
              <span class="toggle-track"></span>
            </label>
          </div>
        </div>

        <div class="panel-section">
          <h3>队列配置</h3>

          <div class="config-item">
            <div class="config-label">
              <span>最大队列大小</span>
              <span class="config-value">{{ config.maxQueueSize }}</span>
            </div>
            <input v-model.number="config.maxQueueSize" type="range" min="10" max="500" step="10" class="config-slider" />
          </div>

          <div class="config-item">
            <div class="config-label">
              <span>收集反馈</span>
              <span class="config-desc">允许用户对输出评分</span>
            </div>
            <label class="toggle-switch">
              <input v-model="config.feedbackCollection" type="checkbox" />
              <span class="toggle-track"></span>
            </label>
          </div>
        </div>

        <!-- 当前队列 -->
        <div class="panel-section">
          <h3>执行队列</h3>
          <div class="queue-list">
            <div v-for="action in actionQueue" :key="action.id" :class="['queue-item', action.status]">
              <div class="queue-icon">{{ getTypeIcon(action.type) }}</div>
              <div class="queue-content">
                <span class="queue-text">{{ action.content }}</span>
                <div class="queue-progress" v-if="action.status === 'executing'">
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: action.progress + '%' }"></div>
                  </div>
                  <span class="progress-text">{{ action.progress }}%</span>
                </div>
              </div>
              <span :class="['queue-status', action.status]">
                {{ action.status === 'executing' ? '执行中' : '等待中' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧状态 -->
      <div class="status-panel">
        <div class="stats-grid">
          <div class="stat-card">
            <span class="stat-icon">⚡</span>
            <div class="stat-info">
              <span class="stat-value">{{ actionStats.totalActions }}</span>
              <span class="stat-label">总行动</span>
            </div>
          </div>
          <div class="stat-card">
            <span class="stat-icon">⏳</span>
            <div class="stat-info">
              <span class="stat-value">{{ actionStats.pendingActions }}</span>
              <span class="stat-label">等待中</span>
            </div>
          </div>
          <div class="stat-card">
            <span class="stat-icon">⏱️</span>
            <div class="stat-info">
              <span class="stat-value">{{ actionStats.avgExecTime }}</span>
              <span class="stat-label">平均耗时</span>
            </div>
          </div>
          <div class="stat-card">
            <span class="stat-icon">📊</span>
            <div class="stat-info">
              <span class="stat-value">{{ actionStats.feedbackRate }}</span>
              <span class="stat-label">反馈率</span>
            </div>
          </div>
        </div>

        <div class="actions-list">
          <div class="list-header">
            <h3>最近行动</h3>
            <button class="btn-text">查看全部</button>
          </div>
          <div class="action-items">
            <div v-for="action in recentActions" :key="action.id" class="action-item">
              <div class="action-icon">{{ getTypeIcon(action.type) }}</div>
              <div class="action-content">
                <span class="action-text">{{ action.content }}</span>
                <div class="action-meta">
                  <span class="action-time">{{ action.time }}</span>
                  <span class="action-duration">{{ action.duration }}</span>
                </div>
              </div>
              <div class="action-feedback">
                <span :class="['feedback-icon', action.feedback]">
                  {{ getFeedbackIcon(action.feedback) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 输出预览 -->
        <div class="output-preview">
          <div class="preview-header">
            <h3>输出预览</h3>
            <span class="preview-format">{{ config.outputFormat }}</span>
          </div>
          <div class="preview-content">
            <div class="output-line typing">
              <span class="output-text">正在生成数据分析报告...</span>
              <span class="cursor"></span>
            </div>
          </div>
        </div>

        <div class="architecture-hint">
          <div class="hint-icon">🎬</div>
          <div class="hint-content">
            <h4>行动流程</h4>
            <p>任务入队 → 执行引擎 → 格式化输出 → 反馈收集</p>
            <p>支持流式输出和多模态响应</p>
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

.actions-module .orb-1 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, rgba(236, 72, 153, 0.25), rgba(219, 39, 119, 0.15));
  top: -100px;
  right: 20%;
}

.actions-module .orb-2 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, rgba(244, 114, 182, 0.2), rgba(236, 72, 153, 0.1));
  bottom: 10%;
  left: 10%;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(236, 72, 153, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(236, 72, 153, 0.03) 1px, transparent 1px);
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

.module-badge.actions {
  background: linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(219, 39, 119, 0.2));
  border: 1px solid rgba(236, 72, 153, 0.4);
  box-shadow: 0 0 20px rgba(236, 72, 153, 0.2);
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
  background: linear-gradient(135deg, #ec4899, #db2777);
  border: none;
  color: white;
}

.btn-primary:hover {
  box-shadow: 0 4px 20px rgba(236, 72, 153, 0.4);
  transform: translateY(-1px);
}

.module-content {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
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

/* 模式卡片 */
.mode-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mode-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-card:hover {
  background: rgba(255, 255, 255, 0.04);
}

.mode-card.selected {
  background: rgba(236, 72, 153, 0.1);
  border-color: rgba(236, 72, 153, 0.4);
}

.mode-icon {
  font-size: 22px;
  flex-shrink: 0;
}

.mode-info {
  flex: 1;
}

.mode-name {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #e4e4e7;
  margin-bottom: 2px;
}

.mode-desc {
  display: block;
  font-size: 11px;
  color: #52525b;
}

.mode-check {
  color: #f472b6;
  font-size: 14px;
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

.config-item.vertical {
  flex-direction: column;
  align-items: stretch;
  gap: 10px;
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
  color: #f472b6;
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
  background: linear-gradient(135deg, #ec4899, #db2777);
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
  background: linear-gradient(135deg, #ec4899, #db2777);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(236, 72, 153, 0.4);
}

.format-options {
  display: flex;
  gap: 8px;
}

.format-btn {
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  color: #a1a1aa;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.format-btn:hover {
  background: rgba(255, 255, 255, 0.06);
}

.format-btn.selected {
  background: rgba(236, 72, 153, 0.15);
  border-color: rgba(236, 72, 153, 0.4);
  color: #f472b6;
}

/* 队列列表 */
.queue-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 8px;
}

.queue-item.executing {
  border-color: rgba(236, 72, 153, 0.3);
}

.queue-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.queue-content {
  flex: 1;
  min-width: 0;
}

.queue-text {
  display: block;
  font-size: 12px;
  color: #a1a1aa;
  margin-bottom: 4px;
}

.queue-progress {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-bar {
  flex: 1;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #ec4899, #f472b6);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.progress-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #f472b6;
}

.queue-status {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
}

.queue-status.executing {
  background: rgba(236, 72, 153, 0.15);
  color: #f472b6;
}

.queue-status.pending {
  background: rgba(113, 113, 122, 0.15);
  color: #a1a1aa;
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
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
}

.stat-icon {
  font-size: 24px;
}

.stat-info {
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
}

/* 行动列表 */
.actions-list {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  overflow: hidden;
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
  color: #f472b6;
  font-size: 12px;
  cursor: pointer;
}

.btn-text:hover {
  text-decoration: underline;
}

.action-items {
  max-height: 180px;
  overflow-y: auto;
  padding: 8px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 8px;
  transition: background 0.2s;
}

.action-item:hover {
  background: rgba(255, 255, 255, 0.02);
}

.action-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.action-content {
  flex: 1;
  min-width: 0;
}

.action-text {
  display: block;
  font-size: 12px;
  color: #a1a1aa;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-meta {
  display: flex;
  gap: 10px;
}

.action-time {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #52525b;
}

.action-duration {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #71717a;
}

.action-feedback {
  flex-shrink: 0;
}

.feedback-icon {
  font-size: 16px;
}

.feedback-icon.positive {
  filter: drop-shadow(0 0 4px rgba(74, 222, 128, 0.5));
}

.feedback-icon.negative {
  filter: drop-shadow(0 0 4px rgba(248, 113, 113, 0.5));
}

/* 输出预览 */
.output-preview {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.preview-header h3 {
  font-size: 12px;
  font-weight: 600;
  color: #e4e4e7;
  margin: 0;
}

.preview-format {
  padding: 2px 8px;
  background: rgba(236, 72, 153, 0.15);
  border-radius: 4px;
  font-size: 10px;
  color: #f472b6;
}

.preview-content {
  padding: 14px;
  background: rgba(0, 0, 0, 0.2);
  font-family: 'JetBrains Mono', monospace;
}

.output-line {
  display: flex;
  align-items: center;
}

.output-text {
  font-size: 12px;
  color: #a1a1aa;
}

.cursor {
  width: 8px;
  height: 16px;
  background: #f472b6;
  margin-left: 2px;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.architecture-hint {
  display: flex;
  gap: 12px;
  padding: 14px;
  background: linear-gradient(135deg, rgba(236, 72, 153, 0.08), rgba(219, 39, 119, 0.05));
  border: 1px solid rgba(236, 72, 153, 0.2);
  border-radius: 10px;
}

.hint-icon {
  font-size: 24px;
}

.hint-content h4 {
  font-size: 12px;
  font-weight: 600;
  color: #f9a8d4;
  margin: 0 0 6px;
}

.hint-content p {
  font-size: 11px;
  color: #71717a;
  margin: 0 0 4px;
}

.config-panel::-webkit-scrollbar,
.status-panel::-webkit-scrollbar,
.action-items::-webkit-scrollbar {
  width: 4px;
}

.config-panel::-webkit-scrollbar-track,
.status-panel::-webkit-scrollbar-track,
.action-items::-webkit-scrollbar-track {
  background: transparent;
}

.config-panel::-webkit-scrollbar-thumb,
.status-panel::-webkit-scrollbar-thumb,
.action-items::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}
</style>
