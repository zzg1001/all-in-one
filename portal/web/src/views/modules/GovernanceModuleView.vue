<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const config = reactive({
  enabled: true,
  authMode: 'rbac',
  auditEnabled: true,
  auditRetention: 90,
  quotaEnabled: true,
  defaultQuota: 1000,
  rateLimitEnabled: true,
  rateLimit: 100
})

const governanceStats = ref({
  activeRoles: 8,
  totalPolicies: 24,
  auditEvents: '156K',
  violations: 12
})

const authModes = [
  { id: 'rbac', name: 'RBAC', desc: '基于角色的访问控制', icon: '👥' },
  { id: 'abac', name: 'ABAC', desc: '基于属性的访问控制', icon: '🏷️' },
  { id: 'pbac', name: 'PBAC', desc: '基于策略的访问控制', icon: '📜' }
]

const roles = ref([
  { id: 'admin', name: '管理员', agents: 2, permissions: ['*'], color: '#f87171' },
  { id: 'developer', name: '开发者', agents: 8, permissions: ['read', 'write', 'execute'], color: '#60a5fa' },
  { id: 'analyst', name: '分析师', agents: 12, permissions: ['read', 'analyze'], color: '#4ade80' },
  { id: 'viewer', name: '观察者', agents: 6, permissions: ['read'], color: '#a1a1aa' }
])

const recentAudits = ref([
  { id: 'a1', event: 'AGENT_CREATED', actor: 'admin-001', target: 'agent-015', result: 'success', time: '10:30:15' },
  { id: 'a2', event: 'PERMISSION_DENIED', actor: 'agent-003', target: '/api/admin', result: 'blocked', time: '10:28:42' },
  { id: 'a3', event: 'QUOTA_EXCEEDED', actor: 'agent-007', target: 'tokens', result: 'warning', time: '10:25:00' },
  { id: 'a4', event: 'CONFIG_CHANGED', actor: 'admin-002', target: 'security-policy', result: 'success', time: '10:20:30' },
  { id: 'a5', event: 'RATE_LIMIT_HIT', actor: 'agent-012', target: 'api-calls', result: 'throttled', time: '10:15:00' }
])

const securityPolicies = ref([
  { id: 'p1', name: '敏感数据访问', status: 'active', rules: 5, enforced: true },
  { id: 'p2', name: 'API 调用限制', status: 'active', rules: 3, enforced: true },
  { id: 'p3', name: '资源配额管理', status: 'active', rules: 8, enforced: true },
  { id: 'p4', name: '跨域通信策略', status: 'draft', rules: 4, enforced: false }
])

const getResultColor = (result: string) => {
  const colors: Record<string, string> = {
    success: '#4ade80',
    blocked: '#f87171',
    warning: '#fbbf24',
    throttled: '#fb923c'
  }
  return colors[result] || '#71717a'
}

const goBack = () => router.push('/architecture')
</script>

<template>
  <div class="module-view governance-module">
    <!-- 装饰背景 -->
    <div class="bg-decoration">
      <div class="bg-orb orb-1"></div>
      <div class="bg-orb orb-2"></div>
      <div class="bg-grid"></div>
      <!-- 安全网格 -->
      <div class="security-grid">
        <div class="grid-line horizontal"></div>
        <div class="grid-line vertical"></div>
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
          <span>🛡️</span>
        </div>
        <div class="header-title">
          <h1>Governance 治理模块</h1>
          <p>权限控制、审计日志、资源配额、安全策略</p>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn-secondary">导出审计日志</button>
        <button class="btn-primary">保存配置</button>
      </div>
    </header>

    <!-- 主内容 -->
    <div class="module-content">
      <!-- 左侧配置 -->
      <div class="config-panel">
        <div class="panel-section">
          <h3>访问控制</h3>
          <div class="auth-modes">
            <div
              v-for="mode in authModes"
              :key="mode.id"
              :class="['auth-card', { selected: config.authMode === mode.id }]"
              @click="config.authMode = mode.id"
            >
              <span class="auth-icon">{{ mode.icon }}</span>
              <div class="auth-info">
                <span class="auth-name">{{ mode.name }}</span>
                <span class="auth-desc">{{ mode.desc }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="panel-section">
          <h3>审计配置</h3>

          <div class="config-item">
            <div class="config-label">
              <span>启用审计日志</span>
              <span class="config-desc">记录所有操作事件</span>
            </div>
            <label class="toggle-switch">
              <input v-model="config.auditEnabled" type="checkbox" />
              <span class="toggle-track"></span>
            </label>
          </div>

          <div class="config-item">
            <div class="config-label">
              <span>日志保留天数</span>
              <span class="config-value">{{ config.auditRetention }} 天</span>
            </div>
            <input v-model.number="config.auditRetention" type="range" min="7" max="365" class="config-slider" />
          </div>
        </div>

        <div class="panel-section">
          <h3>资源配额</h3>

          <div class="config-item">
            <div class="config-label">
              <span>启用配额限制</span>
              <span class="config-desc">限制资源使用量</span>
            </div>
            <label class="toggle-switch">
              <input v-model="config.quotaEnabled" type="checkbox" />
              <span class="toggle-track"></span>
            </label>
          </div>

          <div class="config-item">
            <div class="config-label">
              <span>默认 Token 配额</span>
              <span class="config-value">{{ config.defaultQuota.toLocaleString() }}/天</span>
            </div>
            <input v-model.number="config.defaultQuota" type="range" min="100" max="10000" step="100" class="config-slider" />
          </div>

          <div class="config-item">
            <div class="config-label">
              <span>启用速率限制</span>
              <span class="config-desc">限制 API 调用频率</span>
            </div>
            <label class="toggle-switch">
              <input v-model="config.rateLimitEnabled" type="checkbox" />
              <span class="toggle-track"></span>
            </label>
          </div>

          <div class="config-item">
            <div class="config-label">
              <span>请求限制</span>
              <span class="config-value">{{ config.rateLimit }}/分钟</span>
            </div>
            <input v-model.number="config.rateLimit" type="range" min="10" max="1000" step="10" class="config-slider" />
          </div>
        </div>

        <!-- 角色列表 -->
        <div class="panel-section">
          <h3>角色管理</h3>
          <div class="roles-list">
            <div v-for="role in roles" :key="role.id" class="role-item">
              <span class="role-indicator" :style="{ background: role.color }"></span>
              <div class="role-info">
                <span class="role-name">{{ role.name }}</span>
                <span class="role-agents">{{ role.agents }} Agents</span>
              </div>
              <div class="role-permissions">
                <span v-for="perm in role.permissions.slice(0, 2)" :key="perm" class="perm-badge">
                  {{ perm }}
                </span>
                <span v-if="role.permissions.length > 2" class="perm-more">
                  +{{ role.permissions.length - 2 }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧状态 -->
      <div class="status-panel">
        <div class="stats-grid">
          <div class="stat-card">
            <span class="stat-icon">👥</span>
            <div class="stat-info">
              <span class="stat-value">{{ governanceStats.activeRoles }}</span>
              <span class="stat-label">活跃角色</span>
            </div>
          </div>
          <div class="stat-card">
            <span class="stat-icon">📜</span>
            <div class="stat-info">
              <span class="stat-value">{{ governanceStats.totalPolicies }}</span>
              <span class="stat-label">安全策略</span>
            </div>
          </div>
          <div class="stat-card">
            <span class="stat-icon">📋</span>
            <div class="stat-info">
              <span class="stat-value">{{ governanceStats.auditEvents }}</span>
              <span class="stat-label">审计事件</span>
            </div>
          </div>
          <div class="stat-card warning">
            <span class="stat-icon">⚠️</span>
            <div class="stat-info">
              <span class="stat-value">{{ governanceStats.violations }}</span>
              <span class="stat-label">违规警告</span>
            </div>
          </div>
        </div>

        <!-- 安全策略 -->
        <div class="policies-panel">
          <div class="list-header">
            <h3>安全策略</h3>
            <button class="btn-text">+ 新建策略</button>
          </div>
          <div class="policies-list">
            <div v-for="policy in securityPolicies" :key="policy.id" class="policy-card">
              <div class="policy-header">
                <span class="policy-name">{{ policy.name }}</span>
                <span :class="['policy-status', policy.status]">{{ policy.status }}</span>
              </div>
              <div class="policy-stats">
                <span class="policy-rules">{{ policy.rules }} 条规则</span>
                <span :class="['policy-enforced', { active: policy.enforced }]">
                  {{ policy.enforced ? '已启用' : '未启用' }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 审计日志 -->
        <div class="audit-panel">
          <div class="list-header">
            <h3>审计日志</h3>
            <button class="btn-text">查看全部</button>
          </div>
          <div class="audit-list">
            <div v-for="audit in recentAudits" :key="audit.id" class="audit-item">
              <span class="audit-result" :style="{ background: getResultColor(audit.result) }"></span>
              <div class="audit-content">
                <div class="audit-event">
                  <span class="event-type">{{ audit.event }}</span>
                  <span class="event-time">{{ audit.time }}</span>
                </div>
                <div class="audit-details">
                  <span class="audit-actor">{{ audit.actor }}</span>
                  <span class="audit-arrow">→</span>
                  <span class="audit-target">{{ audit.target }}</span>
                </div>
              </div>
              <span :class="['audit-badge', audit.result]">{{ audit.result }}</span>
            </div>
          </div>
        </div>

        <div class="architecture-hint">
          <div class="hint-icon">🔐</div>
          <div class="hint-content">
            <h4>治理流程</h4>
            <p>身份认证 → 权限验证 → 操作审计 → 合规检查</p>
            <p>确保系统安全和操作可追溯</p>
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

.governance-module .orb-1 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(220, 38, 38, 0.1));
  top: -100px;
  right: 20%;
}

.governance-module .orb-2 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, rgba(248, 113, 113, 0.15), rgba(239, 68, 68, 0.08));
  bottom: 10%;
  left: 10%;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(239, 68, 68, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(239, 68, 68, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
}

.security-grid {
  position: absolute;
  inset: 0;
}

.grid-line {
  position: absolute;
  background: rgba(239, 68, 68, 0.1);
}

.grid-line.horizontal {
  width: 100%;
  height: 1px;
  top: 50%;
  animation: scan-h 4s linear infinite;
}

.grid-line.vertical {
  width: 1px;
  height: 100%;
  left: 50%;
  animation: scan-v 4s linear infinite;
  animation-delay: 2s;
}

@keyframes scan-h {
  0% { top: 0; opacity: 0; }
  10% { opacity: 0.5; }
  90% { opacity: 0.5; }
  100% { top: 100%; opacity: 0; }
}

@keyframes scan-v {
  0% { left: 0; opacity: 0; }
  10% { opacity: 0.5; }
  90% { opacity: 0.5; }
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
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(220, 38, 38, 0.2));
  border: 1px solid rgba(239, 68, 68, 0.4);
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.2);
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
  background: linear-gradient(135deg, #ef4444, #dc2626);
  border: none;
  color: white;
}

.btn-primary:hover {
  box-shadow: 0 4px 20px rgba(239, 68, 68, 0.4);
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

.auth-modes {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.auth-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.auth-card:hover {
  background: rgba(255, 255, 255, 0.04);
}

.auth-card.selected {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.4);
}

.auth-icon {
  font-size: 20px;
}

.auth-info {
  flex: 1;
}

.auth-name {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #e4e4e7;
}

.auth-desc {
  display: block;
  font-size: 10px;
  color: #52525b;
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
  color: #fca5a5;
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
  background: linear-gradient(135deg, #ef4444, #dc2626);
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
  background: linear-gradient(135deg, #ef4444, #dc2626);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.4);
}

.roles-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.role-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
}

.role-indicator {
  width: 4px;
  height: 28px;
  border-radius: 2px;
}

.role-info {
  flex: 1;
}

.role-name {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #e4e4e7;
}

.role-agents {
  display: block;
  font-size: 10px;
  color: #52525b;
}

.role-permissions {
  display: flex;
  gap: 4px;
}

.perm-badge {
  padding: 2px 6px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  font-size: 9px;
  color: #71717a;
}

.perm-more {
  padding: 2px 6px;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 4px;
  font-size: 9px;
  color: #fca5a5;
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

.stat-card.warning {
  border-color: rgba(239, 68, 68, 0.3);
  background: rgba(239, 68, 68, 0.05);
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

.policies-panel, .audit-panel {
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
  color: #fca5a5;
  font-size: 12px;
  cursor: pointer;
}

.btn-text:hover {
  text-decoration: underline;
}

.policies-list {
  padding: 10px;
}

.policy-card {
  padding: 10px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 8px;
  margin-bottom: 8px;
}

.policy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.policy-name {
  font-size: 12px;
  font-weight: 500;
  color: #e4e4e7;
}

.policy-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
}

.policy-status.active {
  background: rgba(74, 222, 128, 0.15);
  color: #4ade80;
}

.policy-status.draft {
  background: rgba(113, 113, 122, 0.15);
  color: #a1a1aa;
}

.policy-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.policy-rules {
  font-size: 10px;
  color: #52525b;
}

.policy-enforced {
  font-size: 10px;
  color: #71717a;
}

.policy-enforced.active {
  color: #4ade80;
}

.audit-list {
  max-height: 200px;
  overflow-y: auto;
  padding: 10px;
}

.audit-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 6px;
  margin-bottom: 6px;
  background: rgba(255, 255, 255, 0.01);
}

.audit-result {
  width: 4px;
  height: 32px;
  border-radius: 2px;
}

.audit-content {
  flex: 1;
}

.audit-event {
  display: flex;
  justify-content: space-between;
  margin-bottom: 2px;
}

.event-type {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 500;
  color: #e4e4e7;
}

.event-time {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: #52525b;
}

.audit-details {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  color: #71717a;
}

.audit-arrow {
  color: #52525b;
}

.audit-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 9px;
  font-weight: 500;
}

.audit-badge.success {
  background: rgba(74, 222, 128, 0.15);
  color: #4ade80;
}

.audit-badge.blocked {
  background: rgba(248, 113, 113, 0.15);
  color: #f87171;
}

.audit-badge.warning {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
}

.audit-badge.throttled {
  background: rgba(251, 146, 60, 0.15);
  color: #fb923c;
}

.architecture-hint {
  display: flex;
  gap: 12px;
  padding: 14px;
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.08), rgba(220, 38, 38, 0.05));
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 10px;
}

.hint-icon {
  font-size: 24px;
}

.hint-content h4 {
  font-size: 12px;
  font-weight: 600;
  color: #fecaca;
  margin: 0 0 6px;
}

.hint-content p {
  font-size: 11px;
  color: #71717a;
  margin: 0 0 4px;
}

.config-panel::-webkit-scrollbar,
.status-panel::-webkit-scrollbar,
.audit-list::-webkit-scrollbar {
  width: 4px;
}

.config-panel::-webkit-scrollbar-track,
.status-panel::-webkit-scrollbar-track,
.audit-list::-webkit-scrollbar-track {
  background: transparent;
}

.config-panel::-webkit-scrollbar-thumb,
.status-panel::-webkit-scrollbar-thumb,
.audit-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}
</style>
