<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

interface ExecutionLog {
  id: string
  agentName: string
  agentIcon: string
  taskName: string
  status: 'running' | 'success' | 'failed' | 'cancelled'
  startTime: string
  endTime?: string
  duration?: number
  tokensUsed: number
  toolCalls: number
  errorMessage?: string
}

interface Stats {
  totalExecutions: number
  successRate: number
  avgDuration: number
  totalTokens: number
  activeAgents: number
}

const timeRange = ref<'1h' | '24h' | '7d' | '30d'>('24h')
const statusFilter = ref<'all' | 'running' | 'success' | 'failed'>('all')
const searchQuery = ref('')
const isLive = ref(true)

const stats = ref<Stats>({
  totalExecutions: 1247,
  successRate: 94.5,
  avgDuration: 3.2,
  totalTokens: 2450000,
  activeAgents: 8
})

const logs = ref<ExecutionLog[]>([
  {
    id: '1',
    agentName: '数据分析专家',
    agentIcon: '📊',
    taskName: 'Excel 数据转换',
    status: 'success',
    startTime: '2026-03-22 10:30:15',
    endTime: '2026-03-22 10:30:18',
    duration: 3.2,
    tokensUsed: 1520,
    toolCalls: 2
  },
  {
    id: '2',
    agentName: '代码生成器',
    agentIcon: '💻',
    taskName: '生成 Python 脚本',
    status: 'running',
    startTime: '2026-03-22 10:32:00',
    tokensUsed: 890,
    toolCalls: 1
  },
  {
    id: '3',
    agentName: '智能写作助手',
    agentIcon: '✍️',
    taskName: '撰写产品文档',
    status: 'success',
    startTime: '2026-03-22 10:25:00',
    endTime: '2026-03-22 10:27:30',
    duration: 150,
    tokensUsed: 4200,
    toolCalls: 5
  },
  {
    id: '4',
    agentName: 'PDF 处理专家',
    agentIcon: '📄',
    taskName: '提取 PDF 表格',
    status: 'failed',
    startTime: '2026-03-22 10:20:00',
    endTime: '2026-03-22 10:20:05',
    duration: 5,
    tokensUsed: 320,
    toolCalls: 1,
    errorMessage: 'PDF 文件格式不支持'
  },
  {
    id: '5',
    agentName: '图像描述生成',
    agentIcon: '🖼️',
    taskName: '分析产品图片',
    status: 'success',
    startTime: '2026-03-22 10:15:00',
    endTime: '2026-03-22 10:15:12',
    duration: 12,
    tokensUsed: 2100,
    toolCalls: 3
  }
])

const filteredLogs = computed(() => {
  return logs.value.filter(log => {
    const matchStatus = statusFilter.value === 'all' || log.status === statusFilter.value
    const matchSearch = !searchQuery.value ||
      log.agentName.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      log.taskName.toLowerCase().includes(searchQuery.value.toLowerCase())
    return matchStatus && matchSearch
  })
})

const chartData = ref({
  labels: ['10:00', '10:10', '10:20', '10:30', '10:40', '10:50'],
  executions: [12, 18, 15, 22, 19, 25],
  tokens: [15000, 22000, 18000, 28000, 24000, 32000]
})

const formatDuration = (seconds?: number) => {
  if (!seconds) return '-'
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}m ${secs.toFixed(0)}s`
}

const formatTokens = (tokens: number) => {
  if (tokens >= 1000000) return `${(tokens / 1000000).toFixed(1)}M`
  if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}K`
  return tokens.toString()
}

const getSparkLine = (data: number[], max: number) => {
  const width = 200
  const height = 50
  const padding = 2
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width
    const y = height - padding - ((v / max) * (height - padding * 2))
    return `${x},${y}`
  })
  return `M${points.join(' L')}`
}

const getSparkArea = (data: number[], max: number) => {
  const width = 200
  const height = 50
  const padding = 2
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width
    const y = height - padding - ((v / max) * (height - padding * 2))
    return `${x},${y}`
  })
  return `M0,${height} L${points.join(' L')} L${width},${height} Z`
}

const getStatusClass = (status: string) => {
  switch (status) {
    case 'running': return 'status-running'
    case 'success': return 'status-success'
    case 'failed': return 'status-failed'
    case 'cancelled': return 'status-cancelled'
    default: return ''
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'running': return '运行中'
    case 'success': return '成功'
    case 'failed': return '失败'
    case 'cancelled': return '已取消'
    default: return status
  }
}

const refreshData = () => console.log('Refreshing data...')
const viewDetail = (log: ExecutionLog) => console.log('View detail:', log)
const stopExecution = (log: ExecutionLog) => console.log('Stopping:', log)

let refreshInterval: number | null = null
onMounted(() => { refreshInterval = window.setInterval(refreshData, 30000) })
onUnmounted(() => { if (refreshInterval) clearInterval(refreshInterval) })
</script>

<template>
  <div class="monitor-view">
    <!-- 装饰背景 -->
    <div class="bg-decoration">
      <div class="bg-orb orb-1"></div>
      <div class="bg-orb orb-2"></div>
      <div class="bg-grid"></div>
    </div>

    <!-- 顶部区域 -->
    <header class="page-header">
        <div class="header-top">
          <div class="header-info">
            <div class="title-row">
              <span class="title-icon">📡</span>
              <h1>监控中心</h1>
              <span class="live-badge" v-if="isLive">
                <span class="live-dot"></span>
                LIVE
              </span>
            </div>
            <p class="subtitle">实时监控 Agent 执行状态和系统性能</p>
          </div>
          <div class="header-actions">
            <select v-model="timeRange" class="time-select">
              <option value="1h">最近 1 小时</option>
              <option value="24h">最近 24 小时</option>
              <option value="7d">最近 7 天</option>
              <option value="30d">最近 30 天</option>
            </select>
            <button class="btn-refresh" @click="refreshData">
              <svg viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"/>
              </svg>
              刷新
            </button>
          </div>
        </div>

        <!-- 功能说明 -->
        <div class="intro-bar">
          <div class="intro-item">
            <span class="intro-dot"></span>
            <span>实时监控所有 Agent 的运行状态和性能指标</span>
          </div>
          <div class="intro-item">
            <span class="intro-dot"></span>
            <span>查看执行日志、Token 消耗和成功率统计</span>
          </div>
          <div class="intro-item">
            <span class="intro-dot"></span>
            <span>支持按状态筛选和搜索历史记录</span>
          </div>
        </div>

        <!-- 统计卡片 -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-visual">
              <svg viewBox="0 0 36 36" class="stat-ring">
                <circle cx="18" cy="18" r="14" class="ring-bg"/>
                <circle cx="18" cy="18" r="14" class="ring-fill exec"/>
              </svg>
              <span class="stat-icon">⚡</span>
            </div>
            <div class="stat-content">
              <span class="stat-value">{{ stats.totalExecutions.toLocaleString() }}</span>
              <span class="stat-label">总执行</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-visual">
              <svg viewBox="0 0 36 36" class="stat-ring">
                <circle cx="18" cy="18" r="14" class="ring-bg"/>
                <circle cx="18" cy="18" r="14" class="ring-fill success" :style="{ strokeDasharray: `${stats.successRate * 0.88} 88` }"/>
              </svg>
              <span class="stat-icon">✓</span>
            </div>
            <div class="stat-content">
              <span class="stat-value">{{ stats.successRate }}<small>%</small></span>
              <span class="stat-label">成功率</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-visual">
              <svg viewBox="0 0 36 36" class="stat-ring">
                <circle cx="18" cy="18" r="14" class="ring-bg"/>
                <circle cx="18" cy="18" r="14" class="ring-fill time"/>
              </svg>
              <span class="stat-icon">⏱</span>
            </div>
            <div class="stat-content">
              <span class="stat-value">{{ stats.avgDuration }}<small>s</small></span>
              <span class="stat-label">平均耗时</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-visual">
              <svg viewBox="0 0 36 36" class="stat-ring">
                <circle cx="18" cy="18" r="14" class="ring-bg"/>
                <circle cx="18" cy="18" r="14" class="ring-fill tokens"/>
              </svg>
              <span class="stat-icon">🔤</span>
            </div>
            <div class="stat-content">
              <span class="stat-value">{{ formatTokens(stats.totalTokens) }}</span>
              <span class="stat-label">Token 消耗</span>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-visual">
              <svg viewBox="0 0 36 36" class="stat-ring">
                <circle cx="18" cy="18" r="14" class="ring-bg"/>
                <circle cx="18" cy="18" r="14" class="ring-fill agents"/>
              </svg>
              <span class="stat-icon">🤖</span>
            </div>
            <div class="stat-content">
              <span class="stat-value">{{ stats.activeAgents }}</span>
              <span class="stat-label">活跃 Agent</span>
            </div>
          </div>
        </div>
      </header>

      <!-- 主内容 -->
      <div class="page-content">
        <!-- 图表区域 -->
      <div class="charts-section">
        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-info">
              <h3>执行趋势</h3>
              <span class="chart-total">{{ chartData.executions.reduce((a, b) => a + b, 0) }} 次</span>
            </div>
            <span class="chart-badge up">↑ 15%</span>
          </div>
          <div class="chart-body">
            <svg class="sparkline" viewBox="0 0 200 50" preserveAspectRatio="none">
              <defs>
                <linearGradient id="sparkGradient1" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" style="stop-color:#6366f1;stop-opacity:0.3"/>
                  <stop offset="100%" style="stop-color:#6366f1;stop-opacity:0"/>
                </linearGradient>
              </defs>
              <path class="spark-area" :d="getSparkArea(chartData.executions, 30)" fill="url(#sparkGradient1)"/>
              <path class="spark-line exec" :d="getSparkLine(chartData.executions, 30)" fill="none"/>
            </svg>
            <div class="chart-labels">
              <span v-for="(label, i) in chartData.labels" :key="i">{{ label }}</span>
            </div>
          </div>
        </div>

        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-info">
              <h3>Token 消耗</h3>
              <span class="chart-total">{{ formatTokens(stats.totalTokens) }}</span>
            </div>
            <span class="chart-badge purple">今日</span>
          </div>
          <div class="chart-body">
            <svg class="sparkline" viewBox="0 0 200 50" preserveAspectRatio="none">
              <defs>
                <linearGradient id="sparkGradient2" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" style="stop-color:#8b5cf6;stop-opacity:0.3"/>
                  <stop offset="100%" style="stop-color:#8b5cf6;stop-opacity:0"/>
                </linearGradient>
              </defs>
              <path class="spark-area" :d="getSparkArea(chartData.tokens, 35000)" fill="url(#sparkGradient2)"/>
              <path class="spark-line token" :d="getSparkLine(chartData.tokens, 35000)" fill="none"/>
            </svg>
            <div class="chart-labels">
              <span v-for="(label, i) in chartData.labels" :key="i">{{ label }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 执行日志 -->
      <div class="logs-section">
        <div class="logs-header">
          <h2>执行日志</h2>
          <div class="logs-controls">
            <div class="search-box">
              <svg viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
              </svg>
              <input v-model="searchQuery" type="text" placeholder="搜索日志..." />
            </div>
            <div class="status-filters">
              <button
                :class="['filter-btn', { active: statusFilter === 'all' }]"
                @click="statusFilter = 'all'"
              >全部</button>
              <button
                :class="['filter-btn', { active: statusFilter === 'running' }]"
                @click="statusFilter = 'running'"
              >
                <span class="status-dot running"></span>
                运行中
              </button>
              <button
                :class="['filter-btn', { active: statusFilter === 'success' }]"
                @click="statusFilter = 'success'"
              >
                <span class="status-dot success"></span>
                成功
              </button>
              <button
                :class="['filter-btn', { active: statusFilter === 'failed' }]"
                @click="statusFilter = 'failed'"
              >
                <span class="status-dot failed"></span>
                失败
              </button>
            </div>
          </div>
        </div>

        <div class="logs-table">
          <div class="table-header">
            <div class="col col-agent">Agent</div>
            <div class="col col-task">任务</div>
            <div class="col col-status">状态</div>
            <div class="col col-time">时间</div>
            <div class="col col-duration">耗时</div>
            <div class="col col-tokens">Tokens</div>
            <div class="col col-actions">操作</div>
          </div>

          <div class="table-body">
            <div
              v-for="(log, index) in filteredLogs"
              :key="log.id"
              class="table-row"
              :style="{ '--delay': index * 0.05 + 's' }"
            >
              <div class="col col-agent">
                <span class="agent-icon">{{ log.agentIcon }}</span>
                <span class="agent-name">{{ log.agentName }}</span>
              </div>
              <div class="col col-task">
                <span class="task-name">{{ log.taskName }}</span>
                <span v-if="log.errorMessage" class="task-error">{{ log.errorMessage }}</span>
              </div>
              <div class="col col-status">
                <span :class="['status-badge', getStatusClass(log.status)]">
                  <span class="status-indicator"></span>
                  {{ getStatusText(log.status) }}
                </span>
              </div>
              <div class="col col-time">{{ log.startTime.split(' ')[1] }}</div>
              <div class="col col-duration">{{ formatDuration(log.duration) }}</div>
              <div class="col col-tokens">{{ formatTokens(log.tokensUsed) }}</div>
              <div class="col col-actions">
                <button class="action-btn" @click="viewDetail(log)" title="查看详情">
                  <svg viewBox="0 0 20 20" fill="currentColor">
                    <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                    <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
                  </svg>
                </button>
                <button
                  v-if="log.status === 'running'"
                  class="action-btn stop"
                  @click="stopExecution(log)"
                  title="停止执行"
                >
                  <svg viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clip-rule="evenodd"/>
                  </svg>
                </button>
              </div>
            </div>

            <div v-if="filteredLogs.length === 0" class="empty-state">
              <span class="empty-icon">📭</span>
              <p>暂无执行记录</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

.monitor-view {
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
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(6, 182, 212, 0.15));
  top: -150px;
  right: 10%;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.15));
  bottom: 10%;
  left: 20%;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(16, 185, 129, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(16, 185, 129, 0.02) 1px, transparent 1px);
  background-size: 50px 50px;
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
  padding: 20px 28px 16px;
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

.title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}

.title-icon {
  font-size: 24px;
  filter: drop-shadow(0 0 12px rgba(16, 185, 129, 0.5));
}

.header-info h1 {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 22px;
  font-weight: 700;
  margin: 0;
  background: linear-gradient(135deg, #fff, #6ee7b7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.live-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 12px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  font-weight: 600;
  color: #f87171;
  letter-spacing: 1px;
}

.live-dot {
  width: 6px;
  height: 6px;
  background: #ef4444;
  border-radius: 50%;
  animation: pulse-live 1.5s ease-in-out infinite;
}

@keyframes pulse-live {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.2); }
}

.subtitle {
  font-size: 12px;
  color: #71717a;
  margin: 0;
}

/* 功能说明条 */
.intro-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 10px 14px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.06), rgba(6, 182, 212, 0.04));
  border: 1px solid rgba(16, 185, 129, 0.15);
  border-radius: 8px;
  margin-bottom: 16px;
}

.intro-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #a1a1aa;
}

.intro-dot {
  width: 5px;
  height: 5px;
  background: linear-gradient(135deg, #10b981, #06b6d4);
  border-radius: 50%;
  flex-shrink: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.time-select {
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #e4e4e7;
  font-size: 12px;
  cursor: pointer;
  outline: none;
}

.time-select option {
  background: #18181b;
  color: #e4e4e7;
}

.btn-refresh {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 8px;
  color: #6ee7b7;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-refresh:hover {
  background: rgba(16, 185, 129, 0.25);
  box-shadow: 0 0 16px rgba(16, 185, 129, 0.2);
}

.btn-refresh svg {
  width: 14px;
  height: 14px;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
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
  transition: all 0.3s;
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.1);
  transform: translateY(-1px);
}

.stat-visual {
  position: relative;
  width: 36px;
  height: 36px;
}

.stat-ring {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring-bg {
  fill: none;
  stroke: rgba(255, 255, 255, 0.06);
  stroke-width: 4;
}

.ring-fill {
  fill: none;
  stroke-width: 4;
  stroke-linecap: round;
  stroke-dasharray: 70 88;
  transition: stroke-dasharray 1s ease;
}

.ring-fill.exec { stroke: #6366f1; }
.ring-fill.success { stroke: #10b981; }
.ring-fill.time { stroke: #f59e0b; }
.ring-fill.tokens { stroke: #8b5cf6; }
.ring-fill.agents { stroke: #06b6d4; }

.stat-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 14px;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
}

.stat-value small {
  font-size: 11px;
  color: #71717a;
  margin-left: 2px;
}

.stat-label {
  font-size: 10px;
  color: #71717a;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 图表区域 */
.charts-section {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.chart-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  padding: 14px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.chart-info h3 {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 11px;
  font-weight: 500;
  color: #71717a;
  margin: 0 0 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.chart-total {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 18px;
  font-weight: 700;
  color: #fff;
}

.chart-badge {
  padding: 3px 8px;
  border-radius: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 600;
}

.chart-badge.up {
  background: rgba(16, 185, 129, 0.15);
  color: #6ee7b7;
}

.chart-badge.purple {
  background: rgba(139, 92, 246, 0.15);
  color: #c4b5fd;
}

.chart-body {
  position: relative;
}

.sparkline {
  width: 100%;
  height: 50px;
  display: block;
}

.spark-line {
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.spark-line.exec {
  stroke: #6366f1;
}

.spark-line.token {
  stroke: #8b5cf6;
}

.spark-area {
  opacity: 0.8;
}

.chart-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
}

.chart-labels span {
  font-size: 9px;
  color: #52525b;
}

/* 日志区域 */
.logs-section {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  overflow: hidden;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.logs-header h2 {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  color: #e4e4e7;
}

.logs-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
}

.search-box svg {
  width: 14px;
  height: 14px;
  color: #52525b;
}

.search-box input {
  width: 120px;
  padding: 6px 0;
  background: transparent;
  border: none;
  color: #e4e4e7;
  font-size: 12px;
  outline: none;
}

.search-box input::placeholder {
  color: #52525b;
}

.status-filters {
  display: flex;
  gap: 6px;
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  color: #a1a1aa;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-btn:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #e4e4e7;
}

.filter-btn.active {
  background: rgba(99, 102, 241, 0.15);
  border-color: rgba(99, 102, 241, 0.3);
  color: #a5b4fc;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-dot.running {
  background: #f59e0b;
  animation: pulse-live 1.5s infinite;
}

.status-dot.success {
  background: #10b981;
}

.status-dot.failed {
  background: #ef4444;
}

/* 表格 */
.logs-table {
  overflow-x: auto;
}

.table-header {
  display: grid;
  grid-template-columns: 140px 1fr 80px 70px 60px 60px 60px;
  padding: 10px 18px;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.col {
  font-size: 10px;
  font-weight: 600;
  color: #52525b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.table-body {
  max-height: 300px;
  overflow-y: auto;
}

.table-row {
  display: grid;
  grid-template-columns: 140px 1fr 80px 70px 60px 60px 60px;
  padding: 10px 18px;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  animation: row-in 0.3s ease backwards;
  animation-delay: var(--delay);
  transition: background 0.2s;
}

@keyframes row-in {
  from { opacity: 0; transform: translateX(-10px); }
  to { opacity: 1; transform: translateX(0); }
}

.table-row:hover {
  background: rgba(255, 255, 255, 0.02);
}

.col-agent {
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-icon {
  font-size: 16px;
}

.agent-name {
  font-size: 12px;
  font-weight: 500;
  color: #e4e4e7;
}

.col-task {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.task-name {
  font-size: 12px;
  color: #a1a1aa;
}

.task-error {
  font-size: 10px;
  color: #f87171;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 500;
}

.status-indicator {
  width: 5px;
  height: 5px;
  border-radius: 50%;
}

.status-running {
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
}

.status-running .status-indicator {
  background: #f59e0b;
  animation: pulse-live 1.5s infinite;
}

.status-success {
  background: rgba(16, 185, 129, 0.15);
  color: #6ee7b7;
}

.status-success .status-indicator {
  background: #10b981;
}

.status-failed {
  background: rgba(239, 68, 68, 0.15);
  color: #fca5a5;
}

.status-failed .status-indicator {
  background: #ef4444;
}

.status-cancelled {
  background: rgba(113, 113, 122, 0.15);
  color: #a1a1aa;
}

.status-cancelled .status-indicator {
  background: #71717a;
}

.col-time, .col-duration, .col-tokens {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #71717a;
}

.col-actions {
  display: flex;
  gap: 6px;
}

.action-btn {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: #a1a1aa;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #e4e4e7;
}

.action-btn.stop:hover {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.3);
  color: #f87171;
}

.action-btn svg {
  width: 12px;
  height: 12px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 40px 20px;
}

.empty-icon {
  font-size: 36px;
  margin-bottom: 12px;
  display: block;
}

.empty-state p {
  color: #71717a;
  margin: 0;
}

/* 滚动条 */
.table-body::-webkit-scrollbar {
  width: 6px;
}

.table-body::-webkit-scrollbar-track {
  background: transparent;
}

.table-body::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.table-body::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>
