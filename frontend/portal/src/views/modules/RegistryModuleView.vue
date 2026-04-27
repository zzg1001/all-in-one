<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const config = reactive({
  enabled: true,
  autoDiscovery: true,
  healthCheckInterval: 30,
  heartbeatTimeout: 60,
  loadBalancing: 'round-robin',
  versionPolicy: 'latest'
})

const registryStats = ref({
  totalAgents: 24,
  activeAgents: 18,
  services: 45,
  avgLatency: '12ms'
})

const loadBalancingStrategies = [
  { id: 'round-robin', name: '轮询', desc: '依次分配请求' },
  { id: 'least-conn', name: '最少连接', desc: '分配给连接数最少的实例' },
  { id: 'weighted', name: '加权轮询', desc: '根据权重分配' },
  { id: 'random', name: '随机', desc: '随机选择实例' }
]

const registeredAgents = ref([
  { id: 'agent-001', name: '数据分析专家', version: '2.1.0', status: 'healthy', instances: 3, cpu: 45, memory: 62 },
  { id: 'agent-002', name: '代码生成器', version: '3.0.1', status: 'healthy', instances: 2, cpu: 38, memory: 55 },
  { id: 'agent-003', name: '智能写作助手', version: '1.5.2', status: 'healthy', instances: 4, cpu: 52, memory: 48 },
  { id: 'agent-004', name: 'PDF 处理专家', version: '1.0.0', status: 'warning', instances: 1, cpu: 78, memory: 85 },
  { id: 'agent-005', name: '图像分析器', version: '2.0.0', status: 'unhealthy', instances: 0, cpu: 0, memory: 0 }
])

const serviceEndpoints = ref([
  { service: 'agent-registry', endpoint: '/api/registry', method: 'GET', calls: 15420 },
  { service: 'health-check', endpoint: '/api/health', method: 'GET', calls: 89200 },
  { service: 'capability-query', endpoint: '/api/capabilities', method: 'POST', calls: 3240 },
  { service: 'version-info', endpoint: '/api/versions', method: 'GET', calls: 1890 }
])

const searchQuery = ref('')

const filteredAgents = computed(() => {
  if (!searchQuery.value) return registeredAgents.value
  return registeredAgents.value.filter(a =>
    a.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    healthy: '#4ade80',
    warning: '#fbbf24',
    unhealthy: '#f87171'
  }
  return colors[status] || '#71717a'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    healthy: '健康',
    warning: '警告',
    unhealthy: '异常'
  }
  return texts[status] || status
}

const goBack = () => router.push('/architecture')
</script>

<template>
  <div class="module-view registry-module">
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
          <span>📋</span>
        </div>
        <div class="header-title">
          <h1>Registry 注册中心</h1>
          <p>Agent 注册、发现、能力描述、版本管理</p>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn-secondary">刷新注册表</button>
        <button class="btn-primary">保存配置</button>
      </div>
    </header>

    <!-- 主内容 -->
    <div class="module-content">
      <!-- 左侧配置 -->
      <div class="config-panel">
        <div class="panel-section">
          <h3>发现配置</h3>

          <div class="config-item">
            <div class="config-label">
              <span>启用注册中心</span>
              <span class="config-desc">允许 Agent 注册和发现</span>
            </div>
            <label class="toggle-switch">
              <input v-model="config.enabled" type="checkbox" />
              <span class="toggle-track"></span>
            </label>
          </div>

          <div class="config-item">
            <div class="config-label">
              <span>自动发现</span>
              <span class="config-desc">自动检测新的 Agent 实例</span>
            </div>
            <label class="toggle-switch">
              <input v-model="config.autoDiscovery" type="checkbox" />
              <span class="toggle-track"></span>
            </label>
          </div>

          <div class="config-item">
            <div class="config-label">
              <span>健康检查间隔</span>
              <span class="config-value">{{ config.healthCheckInterval }}s</span>
            </div>
            <input v-model.number="config.healthCheckInterval" type="range" min="10" max="120" step="10" class="config-slider" />
          </div>

          <div class="config-item">
            <div class="config-label">
              <span>心跳超时</span>
              <span class="config-value">{{ config.heartbeatTimeout }}s</span>
            </div>
            <input v-model.number="config.heartbeatTimeout" type="range" min="30" max="180" step="10" class="config-slider" />
          </div>
        </div>

        <div class="panel-section">
          <h3>负载均衡</h3>
          <div class="strategy-cards">
            <div
              v-for="strategy in loadBalancingStrategies"
              :key="strategy.id"
              :class="['strategy-card', { selected: config.loadBalancing === strategy.id }]"
              @click="config.loadBalancing = strategy.id"
            >
              <span class="strategy-name">{{ strategy.name }}</span>
              <span class="strategy-desc">{{ strategy.desc }}</span>
            </div>
          </div>
        </div>

        <div class="panel-section">
          <h3>服务端点</h3>
          <div class="endpoints-list">
            <div v-for="ep in serviceEndpoints" :key="ep.service" class="endpoint-item">
              <div class="endpoint-info">
                <span class="endpoint-name">{{ ep.service }}</span>
                <code class="endpoint-path">{{ ep.method }} {{ ep.endpoint }}</code>
              </div>
              <span class="endpoint-calls">{{ ep.calls.toLocaleString() }} 次</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧状态 -->
      <div class="status-panel">
        <div class="stats-grid">
          <div class="stat-card">
            <span class="stat-icon">🤖</span>
            <div class="stat-info">
              <span class="stat-value">{{ registryStats.totalAgents }}</span>
              <span class="stat-label">注册 Agent</span>
            </div>
          </div>
          <div class="stat-card">
            <span class="stat-icon">✅</span>
            <div class="stat-info">
              <span class="stat-value">{{ registryStats.activeAgents }}</span>
              <span class="stat-label">活跃实例</span>
            </div>
          </div>
          <div class="stat-card">
            <span class="stat-icon">🔗</span>
            <div class="stat-info">
              <span class="stat-value">{{ registryStats.services }}</span>
              <span class="stat-label">服务端点</span>
            </div>
          </div>
          <div class="stat-card">
            <span class="stat-icon">⚡</span>
            <div class="stat-info">
              <span class="stat-value">{{ registryStats.avgLatency }}</span>
              <span class="stat-label">平均延迟</span>
            </div>
          </div>
        </div>

        <div class="agents-registry">
          <div class="list-header">
            <h3>已注册 Agent</h3>
            <input v-model="searchQuery" type="text" placeholder="搜索..." class="search-input" />
          </div>
          <div class="agents-table">
            <div class="table-header">
              <span class="col-name">名称</span>
              <span class="col-version">版本</span>
              <span class="col-status">状态</span>
              <span class="col-instances">实例</span>
              <span class="col-resources">资源</span>
            </div>
            <div class="table-body">
              <div v-for="agent in filteredAgents" :key="agent.id" class="table-row">
                <span class="col-name">
                  <span class="agent-id">{{ agent.id }}</span>
                  <span class="agent-name">{{ agent.name }}</span>
                </span>
                <span class="col-version">
                  <code>v{{ agent.version }}</code>
                </span>
                <span class="col-status">
                  <span class="status-badge" :style="{ '--status-color': getStatusColor(agent.status) }">
                    <span class="status-dot"></span>
                    {{ getStatusText(agent.status) }}
                  </span>
                </span>
                <span class="col-instances">{{ agent.instances }}</span>
                <span class="col-resources">
                  <div class="resource-bars">
                    <div class="resource-bar">
                      <span class="resource-label">CPU</span>
                      <div class="bar-track">
                        <div class="bar-fill cpu" :style="{ width: agent.cpu + '%' }"></div>
                      </div>
                      <span class="resource-value">{{ agent.cpu }}%</span>
                    </div>
                    <div class="resource-bar">
                      <span class="resource-label">MEM</span>
                      <div class="bar-track">
                        <div class="bar-fill mem" :style="{ width: agent.memory + '%' }"></div>
                      </div>
                      <span class="resource-value">{{ agent.memory }}%</span>
                    </div>
                  </div>
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="architecture-hint">
          <div class="hint-icon">🌐</div>
          <div class="hint-content">
            <h4>注册流程</h4>
            <p>Agent 启动 → 注册服务 → 健康检查 → 能力发布</p>
            <p>支持服务发现和动态负载均衡</p>
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

.registry-module .orb-1 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.25), rgba(20, 184, 166, 0.15));
  top: -100px;
  right: 20%;
}

.registry-module .orb-2 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.2), rgba(6, 182, 212, 0.1));
  bottom: 10%;
  left: 10%;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(6, 182, 212, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(6, 182, 212, 0.03) 1px, transparent 1px);
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
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(20, 184, 166, 0.2));
  border: 1px solid rgba(6, 182, 212, 0.4);
  box-shadow: 0 0 20px rgba(6, 182, 212, 0.2);
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
  background: linear-gradient(135deg, #06b6d4, #14b8a6);
  border: none;
  color: white;
}

.btn-primary:hover {
  box-shadow: 0 4px 20px rgba(6, 182, 212, 0.4);
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
  color: #22d3ee;
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
  background: linear-gradient(135deg, #06b6d4, #14b8a6);
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
  background: linear-gradient(135deg, #06b6d4, #14b8a6);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(6, 182, 212, 0.4);
}

.strategy-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.strategy-card {
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.strategy-card:hover {
  background: rgba(255, 255, 255, 0.04);
}

.strategy-card.selected {
  background: rgba(6, 182, 212, 0.1);
  border-color: rgba(6, 182, 212, 0.4);
}

.strategy-name {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #e4e4e7;
  margin-bottom: 2px;
}

.strategy-desc {
  display: block;
  font-size: 10px;
  color: #52525b;
}

.endpoints-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.endpoint-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
}

.endpoint-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.endpoint-name {
  font-size: 11px;
  font-weight: 500;
  color: #a1a1aa;
}

.endpoint-path {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #22d3ee;
  background: none;
  padding: 0;
}

.endpoint-calls {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
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

.agents-registry {
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

.search-input {
  width: 150px;
  padding: 6px 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  color: #e4e4e7;
  font-size: 11px;
  outline: none;
}

.search-input::placeholder {
  color: #52525b;
}

.agents-table {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.table-header {
  display: grid;
  grid-template-columns: 1.5fr 0.8fr 0.8fr 0.5fr 1.2fr;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.02);
  font-size: 10px;
  font-weight: 600;
  color: #52525b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.table-body {
  flex: 1;
  overflow-y: auto;
}

.table-row {
  display: grid;
  grid-template-columns: 1.5fr 0.8fr 0.8fr 0.5fr 1.2fr;
  padding: 10px 14px;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  transition: background 0.2s;
}

.table-row:hover {
  background: rgba(255, 255, 255, 0.02);
}

.col-name {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.agent-id {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #52525b;
}

.agent-name {
  font-size: 12px;
  font-weight: 500;
  color: #e4e4e7;
}

.col-version code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #a1a1aa;
  background: rgba(255, 255, 255, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  font-size: 10px;
  color: var(--status-color);
}

.status-dot {
  width: 6px;
  height: 6px;
  background: var(--status-color);
  border-radius: 50%;
}

.col-instances {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #a1a1aa;
  text-align: center;
}

.resource-bars {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.resource-bar {
  display: flex;
  align-items: center;
  gap: 6px;
}

.resource-label {
  font-size: 9px;
  color: #52525b;
  width: 24px;
}

.bar-track {
  flex: 1;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s;
}

.bar-fill.cpu {
  background: linear-gradient(90deg, #06b6d4, #22d3ee);
}

.bar-fill.mem {
  background: linear-gradient(90deg, #8b5cf6, #a78bfa);
}

.resource-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: #71717a;
  width: 28px;
  text-align: right;
}

.architecture-hint {
  display: flex;
  gap: 12px;
  padding: 14px;
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.08), rgba(20, 184, 166, 0.05));
  border: 1px solid rgba(6, 182, 212, 0.2);
  border-radius: 10px;
}

.hint-icon {
  font-size: 24px;
}

.hint-content h4 {
  font-size: 12px;
  font-weight: 600;
  color: #67e8f9;
  margin: 0 0 6px;
}

.hint-content p {
  font-size: 11px;
  color: #71717a;
  margin: 0 0 4px;
}

.config-panel::-webkit-scrollbar,
.status-panel::-webkit-scrollbar,
.table-body::-webkit-scrollbar {
  width: 4px;
}

.config-panel::-webkit-scrollbar-track,
.status-panel::-webkit-scrollbar-track,
.table-body::-webkit-scrollbar-track {
  background: transparent;
}

.config-panel::-webkit-scrollbar-thumb,
.status-panel::-webkit-scrollbar-thumb,
.table-body::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}
</style>
