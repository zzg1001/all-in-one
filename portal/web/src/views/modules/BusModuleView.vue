<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const config = reactive({
  enabled: true,
  protocol: 'grpc',
  messageQueueSize: 10000,
  batchSize: 100,
  compressionEnabled: true,
  encryptionEnabled: true,
  retentionHours: 24
})

const busStats = ref({
  messagesPerSec: 1247,
  totalMessages: '2.4M',
  activeChannels: 32,
  avgLatency: '3.2ms'
})

const protocols = [
  { id: 'grpc', name: 'gRPC', desc: '高性能二进制协议', badge: 'FAST' },
  { id: 'rest', name: 'REST', desc: 'HTTP/JSON 通用协议', badge: '' },
  { id: 'websocket', name: 'WebSocket', desc: '双向实时通信', badge: 'REALTIME' },
  { id: 'mqtt', name: 'MQTT', desc: '轻量级消息队列', badge: 'IOT' }
]

const channels = ref([
  { id: 'ch-001', name: 'agent-commands', type: 'broadcast', subscribers: 18, messages: 4520, status: 'active' },
  { id: 'ch-002', name: 'task-updates', type: 'pubsub', subscribers: 24, messages: 12840, status: 'active' },
  { id: 'ch-003', name: 'state-sync', type: 'multicast', subscribers: 8, messages: 89200, status: 'active' },
  { id: 'ch-004', name: 'error-alerts', type: 'broadcast', subscribers: 32, messages: 156, status: 'active' },
  { id: 'ch-005', name: 'metrics-stream', type: 'stream', subscribers: 12, messages: 245000, status: 'busy' }
])

const recentMessages = ref([
  { id: 'm1', channel: 'task-updates', type: 'TASK_COMPLETED', from: 'agent-001', to: 'orchestrator', time: '10:30:15.234' },
  { id: 'm2', channel: 'state-sync', type: 'STATE_UPDATE', from: 'agent-003', to: '*', time: '10:30:15.128' },
  { id: 'm3', channel: 'agent-commands', type: 'START_TASK', from: 'orchestrator', to: 'agent-002', time: '10:30:14.892' },
  { id: 'm4', channel: 'metrics-stream', type: 'METRICS', from: 'agent-004', to: 'monitor', time: '10:30:14.567' }
])

const getChannelTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    broadcast: '#f472b6',
    pubsub: '#60a5fa',
    multicast: '#4ade80',
    stream: '#fbbf24'
  }
  return colors[type] || '#71717a'
}

const goBack = () => router.push('/architecture')
</script>

<template>
  <div class="module-view bus-module">
    <!-- 装饰背景 -->
    <div class="bg-decoration">
      <div class="bg-orb orb-1"></div>
      <div class="bg-orb orb-2"></div>
      <div class="bg-grid"></div>
      <!-- 数据流动画 -->
      <div class="data-flow">
        <div class="flow-line line-1"></div>
        <div class="flow-line line-2"></div>
        <div class="flow-line line-3"></div>
      </div>
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
          <span>🔀</span>
        </div>
        <div class="header-title">
          <h1>Agent Bus 通信总线</h1>
          <p>消息路由、事件广播、状态同步、协议适配</p>
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
          <h3>通信协议</h3>
          <div class="protocol-cards">
            <div
              v-for="proto in protocols"
              :key="proto.id"
              :class="['protocol-card', { selected: config.protocol === proto.id }]"
              @click="config.protocol = proto.id"
            >
              <div class="protocol-info">
                <span class="protocol-name">{{ proto.name }}</span>
                <span class="protocol-desc">{{ proto.desc }}</span>
              </div>
              <span v-if="proto.badge" :class="['protocol-badge', proto.badge.toLowerCase()]">
                {{ proto.badge }}
              </span>
            </div>
          </div>
        </div>

        <div class="panel-section">
          <h3>队列配置</h3>

          <div class="config-item">
            <div class="config-label">
              <span>消息队列大小</span>
              <span class="config-value">{{ config.messageQueueSize.toLocaleString() }}</span>
            </div>
            <input v-model.number="config.messageQueueSize" type="range" min="1000" max="100000" step="1000" class="config-slider" />
          </div>

          <div class="config-item">
            <div class="config-label">
              <span>批处理大小</span>
              <span class="config-value">{{ config.batchSize }}</span>
            </div>
            <input v-model.number="config.batchSize" type="range" min="10" max="500" step="10" class="config-slider" />
          </div>

          <div class="config-item">
            <div class="config-label">
              <span>消息保留时间</span>
              <span class="config-value">{{ config.retentionHours }}h</span>
            </div>
            <input v-model.number="config.retentionHours" type="range" min="1" max="168" class="config-slider" />
          </div>
        </div>

        <div class="panel-section">
          <h3>安全设置</h3>

          <div class="config-item">
            <div class="config-label">
              <span>消息压缩</span>
              <span class="config-desc">减少带宽占用</span>
            </div>
            <label class="toggle-switch">
              <input v-model="config.compressionEnabled" type="checkbox" />
              <span class="toggle-track"></span>
            </label>
          </div>

          <div class="config-item">
            <div class="config-label">
              <span>端到端加密</span>
              <span class="config-desc">保护消息内容</span>
            </div>
            <label class="toggle-switch">
              <input v-model="config.encryptionEnabled" type="checkbox" />
              <span class="toggle-track"></span>
            </label>
          </div>
        </div>

        <!-- 消息日志 -->
        <div class="panel-section">
          <h3>最近消息</h3>
          <div class="messages-log">
            <div v-for="msg in recentMessages" :key="msg.id" class="message-item">
              <span class="msg-type">{{ msg.type }}</span>
              <div class="msg-route">
                <span class="msg-from">{{ msg.from }}</span>
                <span class="msg-arrow">→</span>
                <span class="msg-to">{{ msg.to }}</span>
              </div>
              <span class="msg-time">{{ msg.time }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧状态 -->
      <div class="status-panel">
        <div class="stats-grid">
          <div class="stat-card pulse">
            <span class="stat-icon">⚡</span>
            <div class="stat-info">
              <span class="stat-value">{{ busStats.messagesPerSec }}</span>
              <span class="stat-label">消息/秒</span>
            </div>
          </div>
          <div class="stat-card">
            <span class="stat-icon">📨</span>
            <div class="stat-info">
              <span class="stat-value">{{ busStats.totalMessages }}</span>
              <span class="stat-label">总消息</span>
            </div>
          </div>
          <div class="stat-card">
            <span class="stat-icon">📡</span>
            <div class="stat-info">
              <span class="stat-value">{{ busStats.activeChannels }}</span>
              <span class="stat-label">活跃频道</span>
            </div>
          </div>
          <div class="stat-card">
            <span class="stat-icon">🕐</span>
            <div class="stat-info">
              <span class="stat-value">{{ busStats.avgLatency }}</span>
              <span class="stat-label">平均延迟</span>
            </div>
          </div>
        </div>

        <div class="channels-panel">
          <div class="list-header">
            <h3>通信频道</h3>
            <button class="btn-text">+ 创建频道</button>
          </div>
          <div class="channels-list">
            <div v-for="channel in channels" :key="channel.id" class="channel-card">
              <div class="channel-header">
                <div class="channel-name-row">
                  <span class="channel-type-dot" :style="{ background: getChannelTypeColor(channel.type) }"></span>
                  <span class="channel-name">{{ channel.name }}</span>
                </div>
                <span :class="['channel-status', channel.status]">{{ channel.status }}</span>
              </div>
              <div class="channel-stats">
                <div class="channel-stat">
                  <span class="stat-num">{{ channel.subscribers }}</span>
                  <span class="stat-desc">订阅者</span>
                </div>
                <div class="channel-stat">
                  <span class="stat-num">{{ channel.messages.toLocaleString() }}</span>
                  <span class="stat-desc">消息数</span>
                </div>
                <span class="channel-type-badge">{{ channel.type }}</span>
              </div>
              <div class="channel-activity">
                <div class="activity-bar">
                  <div class="activity-pulse" :class="channel.status"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="architecture-hint">
          <div class="hint-icon">🌐</div>
          <div class="hint-content">
            <h4>消息流转</h4>
            <p>发布消息 → 路由分发 → 队列缓冲 → 订阅消费</p>
            <p>支持广播、组播、点对点多种模式</p>
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

.bus-module .orb-1 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, rgba(251, 146, 60, 0.25), rgba(245, 158, 11, 0.15));
  top: -100px;
  right: 20%;
}

.bus-module .orb-2 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, rgba(253, 186, 116, 0.2), rgba(251, 146, 60, 0.1));
  bottom: 10%;
  left: 10%;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(251, 146, 60, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(251, 146, 60, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
}

/* 数据流动画 */
.data-flow {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.flow-line {
  position: absolute;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(251, 146, 60, 0.4), transparent);
  animation: flow 3s linear infinite;
}

.line-1 {
  top: 20%;
  width: 200px;
  animation-delay: 0s;
}

.line-2 {
  top: 50%;
  width: 150px;
  animation-delay: 1s;
}

.line-3 {
  top: 80%;
  width: 180px;
  animation-delay: 2s;
}

@keyframes flow {
  0% { left: -200px; opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { left: 100%; opacity: 0; }
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
  background: linear-gradient(135deg, rgba(251, 146, 60, 0.2), rgba(245, 158, 11, 0.2));
  border: 1px solid rgba(251, 146, 60, 0.4);
  box-shadow: 0 0 20px rgba(251, 146, 60, 0.2);
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
  background: linear-gradient(135deg, #fb923c, #f59e0b);
  border: none;
  color: white;
}

.btn-primary:hover {
  box-shadow: 0 4px 20px rgba(251, 146, 60, 0.4);
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

.protocol-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.protocol-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.protocol-card:hover {
  background: rgba(255, 255, 255, 0.04);
}

.protocol-card.selected {
  background: rgba(251, 146, 60, 0.1);
  border-color: rgba(251, 146, 60, 0.4);
}

.protocol-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.protocol-name {
  font-size: 13px;
  font-weight: 500;
  color: #e4e4e7;
}

.protocol-desc {
  font-size: 10px;
  color: #52525b;
}

.protocol-badge {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.protocol-badge.fast {
  background: rgba(74, 222, 128, 0.15);
  color: #4ade80;
}

.protocol-badge.realtime {
  background: rgba(96, 165, 250, 0.15);
  color: #60a5fa;
}

.protocol-badge.iot {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
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
  color: #fdba74;
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
  background: linear-gradient(135deg, #fb923c, #f59e0b);
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
  background: linear-gradient(135deg, #fb923c, #f59e0b);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(251, 146, 60, 0.4);
}

.messages-log {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 150px;
  overflow-y: auto;
}

.message-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  font-size: 10px;
}

.msg-type {
  padding: 2px 6px;
  background: rgba(251, 146, 60, 0.15);
  border-radius: 4px;
  color: #fdba74;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 500;
}

.msg-route {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
}

.msg-from, .msg-to {
  font-family: 'JetBrains Mono', monospace;
  color: #a1a1aa;
}

.msg-arrow {
  color: #52525b;
}

.msg-time {
  font-family: 'JetBrains Mono', monospace;
  color: #52525b;
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

.stat-card.pulse {
  animation: stat-pulse 2s ease-in-out infinite;
}

@keyframes stat-pulse {
  0%, 100% { border-color: rgba(255, 255, 255, 0.06); }
  50% { border-color: rgba(251, 146, 60, 0.4); }
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

.channels-panel {
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
  color: #fdba74;
  font-size: 12px;
  cursor: pointer;
}

.btn-text:hover {
  text-decoration: underline;
}

.channels-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.channel-card {
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 8px;
  margin-bottom: 8px;
}

.channel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.channel-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.channel-type-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.channel-name {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 500;
  color: #e4e4e7;
}

.channel-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
}

.channel-status.active {
  background: rgba(74, 222, 128, 0.15);
  color: #4ade80;
}

.channel-status.busy {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
}

.channel-stats {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
}

.channel-stat {
  display: flex;
  flex-direction: column;
}

.stat-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
}

.stat-desc {
  font-size: 9px;
  color: #52525b;
}

.channel-type-badge {
  margin-left: auto;
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  font-size: 9px;
  color: #71717a;
  text-transform: uppercase;
}

.channel-activity {
  margin-top: 8px;
}

.activity-bar {
  height: 3px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.activity-pulse {
  height: 100%;
  background: linear-gradient(90deg, transparent, #fb923c, transparent);
  animation: activity-flow 1.5s linear infinite;
}

.activity-pulse.busy {
  animation-duration: 0.8s;
}

@keyframes activity-flow {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.architecture-hint {
  display: flex;
  gap: 12px;
  padding: 14px;
  background: linear-gradient(135deg, rgba(251, 146, 60, 0.08), rgba(245, 158, 11, 0.05));
  border: 1px solid rgba(251, 146, 60, 0.2);
  border-radius: 10px;
}

.hint-icon {
  font-size: 24px;
}

.hint-content h4 {
  font-size: 12px;
  font-weight: 600;
  color: #fed7aa;
  margin: 0 0 6px;
}

.hint-content p {
  font-size: 11px;
  color: #71717a;
  margin: 0 0 4px;
}

.config-panel::-webkit-scrollbar,
.status-panel::-webkit-scrollbar,
.channels-list::-webkit-scrollbar,
.messages-log::-webkit-scrollbar {
  width: 4px;
}

.config-panel::-webkit-scrollbar-track,
.status-panel::-webkit-scrollbar-track,
.channels-list::-webkit-scrollbar-track,
.messages-log::-webkit-scrollbar-track {
  background: transparent;
}

.config-panel::-webkit-scrollbar-thumb,
.status-panel::-webkit-scrollbar-thumb,
.channels-list::-webkit-scrollbar-thumb,
.messages-log::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}
</style>
