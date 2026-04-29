<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { dashboardApi } from '@/api'

// 统计数据
const stats = ref({
  today_sessions: 0,
  today_messages: 0,
  today_executions: 0,
  today_tokens: 0,
  total_sessions: 0,
  total_messages: 0,
  total_tokens: 0,
  active_users: 0,
  success_rate: 100,
  avg_latency: 0,
  skill_count: 0,
  agent_count: 0,
  pending_feedbacks: 0,
  total_feedbacks: 0,
  session_growth: 0,
})

// 趋势数据
const trends = ref({
  dates: [] as string[],
  sessions: [] as number[],
  messages: [] as number[],
  executions: [] as number[],
  tokens: [] as number[],
})

// 最近反馈
const recentFeedbacks = ref<any[]>([])

// 热门 Agent
const topAgents = ref<any[]>([])

// 加载状态
const loading = ref(true)

// 格式化数字
const formatNumber = (num: number): string => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

// 计算趋势图最大值
const maxTrendValue = computed(() => {
  const allValues = [...trends.value.sessions, ...trends.value.messages]
  return Math.max(...allValues, 1)
})

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const [statsData, trendsData, feedbacksData, agentsData] = await Promise.all([
      dashboardApi.getStats(),
      dashboardApi.getTrends(7),
      fetch('/api/dashboard/recent-feedbacks').then(r => r.json()),
      fetch('/api/dashboard/top-agents').then(r => r.json()),
    ])
    stats.value = statsData
    trends.value = trendsData
    recentFeedbacks.value = feedbacksData
    topAgents.value = agentsData
  } catch (e) {
    console.error('加载驾驶舱数据失败:', e)
  } finally {
    loading.value = false
  }
}

// 获取反馈类型图标
const getFeedbackIcon = (type: string) => {
  const icons: Record<string, string> = { bug: '🐛', suggestion: '💡', other: '💬' }
  return icons[type] || '📝'
}

// 获取状态颜色
const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: '#f59e0b',
    processing: '#3b82f6',
    resolved: '#10b981',
    closed: '#6b7280',
  }
  return colors[status] || '#6b7280'
}

// 格式化时间
const formatTime = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="dashboard">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <span>加载中...</span>
    </div>

    <!-- 主要指标卡片 -->
    <div class="stats-grid">
      <div class="stat-card primary">
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ formatNumber(stats.today_sessions) }}</div>
          <div class="stat-label">今日会话</div>
          <div class="stat-sub" v-if="stats.session_growth !== 0">
            <span :class="stats.session_growth > 0 ? 'up' : 'down'">
              {{ stats.session_growth > 0 ? '↑' : '↓' }} {{ Math.abs(stats.session_growth) }}%
            </span>
            较昨日
          </div>
        </div>
        <div class="stat-total">累计 {{ formatNumber(stats.total_sessions) }}</div>
      </div>

      <div class="stat-card blue">
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
          </svg>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ formatNumber(stats.today_messages) }}</div>
          <div class="stat-label">今日消息</div>
        </div>
        <div class="stat-total">累计 {{ formatNumber(stats.total_messages) }}</div>
      </div>

      <div class="stat-card purple">
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/>
          </svg>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ formatNumber(stats.today_tokens) }}</div>
          <div class="stat-label">今日 Token</div>
        </div>
        <div class="stat-total">累计 {{ formatNumber(stats.total_tokens) }}</div>
      </div>

      <div class="stat-card green">
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.active_users }}</div>
          <div class="stat-label">活跃用户</div>
          <div class="stat-sub">近7天</div>
        </div>
      </div>
    </div>

    <!-- 第二行指标 -->
    <div class="metrics-row">
      <div class="metric-card">
        <div class="metric-icon orange">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ stats.avg_latency }}<span class="unit">ms</span></div>
          <div class="metric-label">平均延迟</div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-icon green">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ stats.success_rate }}<span class="unit">%</span></div>
          <div class="metric-label">成功率</div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-icon blue">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
          </svg>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ stats.skill_count }}</div>
          <div class="metric-label">可用技能</div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-icon purple">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            <circle cx="8.5" cy="8.5" r="1.5"/>
            <polyline points="21 15 16 10 5 21"/>
          </svg>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ stats.agent_count }}</div>
          <div class="metric-label">活跃 Agent</div>
        </div>
      </div>

      <div class="metric-card clickable" @click="$router.push('/feedback')">
        <div class="metric-icon red">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
          </svg>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ stats.pending_feedbacks }}</div>
          <div class="metric-label">待处理反馈</div>
        </div>
        <div class="metric-badge" v-if="stats.pending_feedbacks > 0">!</div>
      </div>
    </div>

    <!-- 图表和列表区 -->
    <div class="charts-row">
      <!-- 趋势图 -->
      <div class="chart-card">
        <div class="card-header">
          <h3>近7天趋势</h3>
        </div>
        <div class="chart-container">
          <div class="chart-legend">
            <span class="legend-item"><i class="dot sessions"></i>会话</span>
            <span class="legend-item"><i class="dot messages"></i>消息</span>
          </div>
          <div class="bar-chart">
            <div class="chart-bars">
              <div v-for="(date, idx) in trends.dates" :key="date" class="bar-group">
                <div class="bars">
                  <div
                    class="bar sessions"
                    :style="{ height: (trends.sessions[idx] / maxTrendValue * 100) + '%' }"
                    :title="`会话: ${trends.sessions[idx]}`"
                  ></div>
                  <div
                    class="bar messages"
                    :style="{ height: (trends.messages[idx] / maxTrendValue * 100) + '%' }"
                    :title="`消息: ${trends.messages[idx]}`"
                  ></div>
                </div>
                <span class="bar-label">{{ date }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 最近反馈 -->
      <div class="list-card">
        <div class="card-header">
          <h3>最近反馈</h3>
          <router-link to="/feedback" class="view-all">查看全部 →</router-link>
        </div>
        <div class="feedback-list">
          <div v-if="recentFeedbacks.length === 0" class="empty-list">暂无反馈</div>
          <div v-else v-for="fb in recentFeedbacks" :key="fb.id" class="feedback-item">
            <span class="fb-icon">{{ getFeedbackIcon(fb.feedback_type) }}</span>
            <div class="fb-content">
              <div class="fb-title">{{ fb.title }}</div>
              <div class="fb-meta">
                <span v-if="fb.agent_name" class="fb-agent">{{ fb.agent_name }}</span>
                <span class="fb-time">{{ formatTime(fb.created_at) }}</span>
              </div>
            </div>
            <span class="fb-status" :style="{ background: getStatusColor(fb.status) }"></span>
          </div>
        </div>
      </div>

      <!-- 热门 Agent -->
      <div class="list-card">
        <div class="card-header">
          <h3>热门 Agent</h3>
        </div>
        <div class="agent-list">
          <div v-if="topAgents.length === 0" class="empty-list">暂无数据</div>
          <div v-else v-for="(agent, idx) in topAgents" :key="agent.id" class="agent-item">
            <span class="agent-rank">{{ idx + 1 }}</span>
            <span class="agent-icon">{{ agent.icon }}</span>
            <div class="agent-info">
              <div class="agent-name">{{ agent.name }}</div>
              <div class="agent-category">{{ agent.category }}</div>
            </div>
            <span class="agent-count">{{ formatNumber(agent.usage_count) }} 次</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100%;
}

/* 加载状态 */
.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: #9ca3af;
  gap: 12px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #1677ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 主要统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.stat-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
}

.stat-card.primary::before { background: linear-gradient(90deg, #1677ff, #4096ff); }
.stat-card.blue::before { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
.stat-card.purple::before { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
.stat-card.green::before { background: linear-gradient(90deg, #10b981, #34d399); }

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-card.primary .stat-icon { background: #eff6ff; color: #1677ff; }
.stat-card.blue .stat-icon { background: #eff6ff; color: #3b82f6; }
.stat-card.purple .stat-icon { background: #f5f3ff; color: #8b5cf6; }
.stat-card.green .stat-icon { background: #ecfdf5; color: #10b981; }

.stat-icon svg {
  width: 24px;
  height: 24px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #6b7280;
  margin-top: 4px;
}

.stat-sub {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}

.stat-sub .up { color: #10b981; }
.stat-sub .down { color: #ef4444; }

.stat-total {
  position: absolute;
  bottom: 12px;
  right: 16px;
  font-size: 11px;
  color: #9ca3af;
}

/* 第二行指标 */
.metrics-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.metric-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.metric-card.clickable {
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}

.metric-card.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.metric-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.metric-icon svg {
  width: 20px;
  height: 20px;
}

.metric-icon.orange { background: #fff7ed; color: #f59e0b; }
.metric-icon.green { background: #ecfdf5; color: #10b981; }
.metric-icon.blue { background: #eff6ff; color: #3b82f6; }
.metric-icon.purple { background: #f5f3ff; color: #8b5cf6; }
.metric-icon.red { background: #fef2f2; color: #ef4444; }

.metric-content {
  flex: 1;
}

.metric-value {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}

.metric-value .unit {
  font-size: 12px;
  font-weight: 500;
  color: #9ca3af;
  margin-left: 2px;
}

.metric-label {
  font-size: 12px;
  color: #6b7280;
}

.metric-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 18px;
  height: 18px;
  background: #ef4444;
  color: white;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 图表区 */
.charts-row {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr;
  gap: 16px;
}

.chart-card,
.list-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.view-all {
  font-size: 12px;
  color: #1677ff;
  text-decoration: none;
}

.view-all:hover {
  text-decoration: underline;
}

/* 柱状图 */
.chart-container {
  height: 200px;
}

.chart-legend {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6b7280;
}

.legend-item .dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

.dot.sessions { background: #1677ff; }
.dot.messages { background: #10b981; }

.bar-chart {
  height: calc(100% - 30px);
}

.chart-bars {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  height: 100%;
  padding-bottom: 24px;
}

.bar-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.bars {
  flex: 1;
  display: flex;
  align-items: flex-end;
  gap: 4px;
  width: 100%;
  justify-content: center;
}

.bar {
  width: 16px;
  border-radius: 4px 4px 0 0;
  min-height: 4px;
  transition: height 0.3s ease;
}

.bar.sessions { background: #1677ff; }
.bar.messages { background: #10b981; }

.bar-label {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 8px;
}

/* 反馈列表 */
.feedback-list,
.agent-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.empty-list {
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
  padding: 20px;
}

.feedback-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #f9fafb;
  border-radius: 8px;
}

.fb-icon {
  font-size: 16px;
}

.fb-content {
  flex: 1;
  min-width: 0;
}

.fb-title {
  font-size: 13px;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.fb-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
}

.fb-agent {
  color: #1677ff;
}

.fb-status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* Agent 列表 */
.agent-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #f9fafb;
  border-radius: 8px;
}

.agent-rank {
  width: 20px;
  height: 20px;
  background: #e5e7eb;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
}

.agent-item:nth-child(1) .agent-rank { background: #fef3c7; color: #d97706; }
.agent-item:nth-child(2) .agent-rank { background: #e5e7eb; color: #4b5563; }
.agent-item:nth-child(3) .agent-rank { background: #fed7aa; color: #c2410c; }

.agent-icon {
  font-size: 20px;
}

.agent-info {
  flex: 1;
  min-width: 0;
}

.agent-name {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.agent-category {
  font-size: 11px;
  color: #9ca3af;
}

.agent-count {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

/* 响应式 */
@media (max-width: 1400px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .metrics-row {
    grid-template-columns: repeat(3, 1fr);
  }

  .charts-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .metrics-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
