<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const config = reactive({
  enabled: true,
  autoDiscovery: true,
  safeMode: true,
  maxConcurrent: 3,
  timeout: 30,
  retryOnFailure: true
})

const toolStats = ref({
  totalTools: 12,
  activeTools: 8,
  totalCalls: 3456,
  successRate: '97.2%'
})

const tools = ref([
  { id: 'read', name: '文件读取', icon: '📖', category: '文件系统', status: 'active', calls: 1245, avgTime: '0.3s' },
  { id: 'write', name: '文件写入', icon: '✏️', category: '文件系统', status: 'active', calls: 892, avgTime: '0.5s' },
  { id: 'bash', name: '命令执行', icon: '💻', category: '系统', status: 'active', calls: 456, avgTime: '2.1s' },
  { id: 'web_search', name: '网络搜索', icon: '🔍', category: '网络', status: 'active', calls: 234, avgTime: '1.8s' },
  { id: 'web_fetch', name: '网页抓取', icon: '🌐', category: '网络', status: 'active', calls: 178, avgTime: '2.5s' },
  { id: 'image_read', name: '图像识别', icon: '🖼️', category: '多媒体', status: 'active', calls: 89, avgTime: '3.2s' },
  { id: 'code_exec', name: '代码执行', icon: '▶️', category: '开发', status: 'inactive', calls: 0, avgTime: '-' },
  { id: 'database', name: '数据库查询', icon: '🗄️', category: '数据', status: 'inactive', calls: 0, avgTime: '-' }
])

const searchQuery = ref('')
const selectedCategory = ref('all')

const categories = computed(() => {
  const cats = new Set(tools.value.map(t => t.category))
  return ['all', ...Array.from(cats)]
})

const filteredTools = computed(() => {
  return tools.value.filter(tool => {
    const matchSearch = !searchQuery.value ||
      tool.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchCategory = selectedCategory.value === 'all' || tool.category === selectedCategory.value
    return matchSearch && matchCategory
  })
})

const recentCalls = ref([
  { id: '1', tool: 'read', input: '/data/report.xlsx', output: '成功读取 1.2MB', time: '10:30:15', duration: '0.3s', status: 'success' },
  { id: '2', tool: 'web_search', input: 'Python pandas tutorial', output: '返回 10 条结果', time: '10:28:42', duration: '1.5s', status: 'success' },
  { id: '3', tool: 'bash', input: 'pip install requests', output: '安装成功', time: '10:25:00', duration: '8.2s', status: 'success' },
  { id: '4', tool: 'web_fetch', input: 'https://api.example.com', output: '超时', time: '10:20:00', duration: '30s', status: 'failed' }
])

const toggleTool = (toolId: string) => {
  const tool = tools.value.find(t => t.id === toolId)
  if (tool) {
    tool.status = tool.status === 'active' ? 'inactive' : 'active'
  }
}

const getToolIcon = (toolId: string) => {
  const tool = tools.value.find(t => t.id === toolId)
  return tool?.icon || '🔧'
}

const goBack = () => router.push('/architecture')
</script>

<template>
  <div class="module-view tools-module">
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
        <div class="module-badge tools">
          <span>🔧</span>
        </div>
        <div class="header-title">
          <h1>Tool Use 工具模块</h1>
          <p>工具发现、参数构造、结果解析，支持动态工具注册</p>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn-secondary">注册新工具</button>
        <button class="btn-primary">保存配置</button>
      </div>
    </header>

    <!-- 主内容 -->
    <div class="module-content">
      <!-- 左侧配置 -->
      <div class="config-panel">
        <div class="panel-section">
          <h3>全局配置</h3>

          <div class="config-item">
            <div class="config-label">
              <span>启用工具</span>
              <span class="config-desc">允许 Agent 使用外部工具</span>
            </div>
            <label class="toggle-switch">
              <input v-model="config.enabled" type="checkbox" />
              <span class="toggle-track"></span>
            </label>
          </div>

          <div class="config-item">
            <div class="config-label">
              <span>自动发现</span>
              <span class="config-desc">自动检测可用工具</span>
            </div>
            <label class="toggle-switch">
              <input v-model="config.autoDiscovery" type="checkbox" />
              <span class="toggle-track"></span>
            </label>
          </div>

          <div class="config-item">
            <div class="config-label">
              <span>安全模式</span>
              <span class="config-desc">限制危险操作</span>
            </div>
            <label class="toggle-switch">
              <input v-model="config.safeMode" type="checkbox" />
              <span class="toggle-track"></span>
            </label>
          </div>
        </div>

        <div class="panel-section">
          <h3>执行配置</h3>

          <div class="config-item">
            <div class="config-label">
              <span>最大并发数</span>
              <span class="config-value">{{ config.maxConcurrent }}</span>
            </div>
            <input v-model.number="config.maxConcurrent" type="range" min="1" max="10" class="config-slider" />
          </div>

          <div class="config-item">
            <div class="config-label">
              <span>超时时间</span>
              <span class="config-value">{{ config.timeout }}s</span>
            </div>
            <input v-model.number="config.timeout" type="range" min="10" max="120" step="10" class="config-slider" />
          </div>

          <div class="config-item">
            <div class="config-label">
              <span>失败重试</span>
              <span class="config-desc">工具调用失败时自动重试</span>
            </div>
            <label class="toggle-switch">
              <input v-model="config.retryOnFailure" type="checkbox" />
              <span class="toggle-track"></span>
            </label>
          </div>
        </div>

        <div class="panel-section">
          <h3>可用工具</h3>
          <div class="tool-filters">
            <input v-model="searchQuery" type="text" placeholder="搜索工具..." class="search-input" />
            <select v-model="selectedCategory" class="category-select">
              <option v-for="cat in categories" :key="cat" :value="cat">
                {{ cat === 'all' ? '全部分类' : cat }}
              </option>
            </select>
          </div>
          <div class="tools-list">
            <div
              v-for="tool in filteredTools"
              :key="tool.id"
              :class="['tool-item', { inactive: tool.status === 'inactive' }]"
            >
              <span class="tool-icon">{{ tool.icon }}</span>
              <div class="tool-info">
                <span class="tool-name">{{ tool.name }}</span>
                <span class="tool-category">{{ tool.category }}</span>
              </div>
              <div class="tool-stats">
                <span class="tool-calls">{{ tool.calls }} 次</span>
                <span class="tool-time">{{ tool.avgTime }}</span>
              </div>
              <label class="toggle-mini">
                <input type="checkbox" :checked="tool.status === 'active'" @change="toggleTool(tool.id)" />
                <span class="toggle-track-mini"></span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧状态 -->
      <div class="status-panel">
        <div class="stats-grid">
          <div class="stat-card">
            <span class="stat-icon">🔧</span>
            <div class="stat-info">
              <span class="stat-value">{{ toolStats.totalTools }}</span>
              <span class="stat-label">总工具数</span>
            </div>
          </div>
          <div class="stat-card">
            <span class="stat-icon">✅</span>
            <div class="stat-info">
              <span class="stat-value">{{ toolStats.activeTools }}</span>
              <span class="stat-label">已启用</span>
            </div>
          </div>
          <div class="stat-card">
            <span class="stat-icon">📊</span>
            <div class="stat-info">
              <span class="stat-value">{{ toolStats.totalCalls }}</span>
              <span class="stat-label">总调用</span>
            </div>
          </div>
          <div class="stat-card">
            <span class="stat-icon">🎯</span>
            <div class="stat-info">
              <span class="stat-value">{{ toolStats.successRate }}</span>
              <span class="stat-label">成功率</span>
            </div>
          </div>
        </div>

        <div class="calls-list">
          <div class="list-header">
            <h3>最近调用</h3>
            <button class="btn-text">查看全部</button>
          </div>
          <div class="call-items">
            <div v-for="call in recentCalls" :key="call.id" :class="['call-item', call.status]">
              <div class="call-tool">
                <span class="call-icon">{{ getToolIcon(call.tool) }}</span>
                <span class="call-name">{{ call.tool }}</span>
              </div>
              <div class="call-details">
                <span class="call-input">{{ call.input }}</span>
                <span class="call-output">→ {{ call.output }}</span>
              </div>
              <div class="call-meta">
                <span class="call-time">{{ call.time }}</span>
                <span class="call-duration">{{ call.duration }}</span>
                <span :class="['call-status', call.status]">
                  {{ call.status === 'success' ? '成功' : '失败' }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="architecture-hint">
          <div class="hint-icon">⚙️</div>
          <div class="hint-content">
            <h4>工具流程</h4>
            <p>工具发现 → 参数构造 → 执行调用 → 结果解析</p>
            <p>支持同步/异步调用和并行执行</p>
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

.tools-module .orb-1 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.25), rgba(234, 88, 12, 0.15));
  top: -100px;
  right: 20%;
}

.tools-module .orb-2 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, rgba(251, 146, 60, 0.2), rgba(249, 115, 22, 0.1));
  bottom: 10%;
  left: 10%;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(249, 115, 22, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(249, 115, 22, 0.03) 1px, transparent 1px);
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

.module-badge.tools {
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.2), rgba(234, 88, 12, 0.2));
  border: 1px solid rgba(249, 115, 22, 0.4);
  box-shadow: 0 0 20px rgba(249, 115, 22, 0.2);
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
  background: linear-gradient(135deg, #f97316, #ea580c);
  border: none;
  color: white;
}

.btn-primary:hover {
  box-shadow: 0 4px 20px rgba(249, 115, 22, 0.4);
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
  color: #fb923c;
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
  background: linear-gradient(135deg, #f97316, #ea580c);
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
  background: linear-gradient(135deg, #f97316, #ea580c);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(249, 115, 22, 0.4);
}

/* 工具过滤 */
.tool-filters {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.search-input {
  flex: 1;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  color: #e4e4e7;
  font-size: 12px;
  outline: none;
}

.search-input::placeholder {
  color: #52525b;
}

.category-select {
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  color: #e4e4e7;
  font-size: 12px;
  cursor: pointer;
  outline: none;
}

.category-select option {
  background: #18181b;
}

/* 工具列表 */
.tools-list {
  max-height: 200px;
  overflow-y: auto;
}

.tool-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 8px;
  transition: background 0.2s;
}

.tool-item:hover {
  background: rgba(255, 255, 255, 0.02);
}

.tool-item.inactive {
  opacity: 0.5;
}

.tool-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.tool-info {
  flex: 1;
  min-width: 0;
}

.tool-name {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #e4e4e7;
}

.tool-category {
  display: block;
  font-size: 10px;
  color: #52525b;
}

.tool-stats {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.tool-calls {
  font-size: 10px;
  color: #a1a1aa;
}

.tool-time {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #52525b;
}

/* 迷你开关 */
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
  background: linear-gradient(135deg, #f97316, #ea580c);
}

.toggle-mini input:checked + .toggle-track-mini::after {
  transform: translateX(14px);
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

/* 调用列表 */
.calls-list {
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
  color: #fb923c;
  font-size: 12px;
  cursor: pointer;
}

.btn-text:hover {
  text-decoration: underline;
}

.call-items {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.call-item {
  padding: 10px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 8px;
  margin-bottom: 8px;
}

.call-item.failed {
  border-color: rgba(239, 68, 68, 0.2);
}

.call-tool {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.call-icon {
  font-size: 14px;
}

.call-name {
  font-size: 12px;
  font-weight: 500;
  color: #e4e4e7;
}

.call-details {
  font-size: 11px;
  color: #71717a;
  margin-bottom: 6px;
}

.call-input {
  display: block;
  margin-bottom: 2px;
}

.call-output {
  display: block;
  color: #a1a1aa;
}

.call-meta {
  display: flex;
  gap: 12px;
  align-items: center;
}

.call-time {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #52525b;
}

.call-duration {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #71717a;
}

.call-status {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
}

.call-status.success {
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
}

.call-status.failed {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
}

.architecture-hint {
  display: flex;
  gap: 12px;
  padding: 14px;
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.08), rgba(234, 88, 12, 0.05));
  border: 1px solid rgba(249, 115, 22, 0.2);
  border-radius: 10px;
}

.hint-icon {
  font-size: 24px;
}

.hint-content h4 {
  font-size: 12px;
  font-weight: 600;
  color: #fdba74;
  margin: 0 0 6px;
}

.hint-content p {
  font-size: 11px;
  color: #71717a;
  margin: 0 0 4px;
}

.config-panel::-webkit-scrollbar,
.status-panel::-webkit-scrollbar,
.tools-list::-webkit-scrollbar,
.call-items::-webkit-scrollbar {
  width: 4px;
}

.config-panel::-webkit-scrollbar-track,
.status-panel::-webkit-scrollbar-track,
.tools-list::-webkit-scrollbar-track,
.call-items::-webkit-scrollbar-track {
  background: transparent;
}

.config-panel::-webkit-scrollbar-thumb,
.status-panel::-webkit-scrollbar-thumb,
.tools-list::-webkit-scrollbar-thumb,
.call-items::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}
</style>
