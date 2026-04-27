<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

// 顶部导航 Tab
const navTabs = [
  { id: 'users', label: '用户管理', path: '/users' },
  { id: 'permissions', label: '权限配置', path: '/permissions' },
]
const activeNavTab = computed(() => route.path === '/permissions' ? 'permissions' : 'users')
const switchNavTab = (tab: typeof navTabs[0]) => {
  router.push(tab.path)
}

// 当前内容标签页
const activeTab = ref<'roles' | 'permissions' | 'api'>('roles')

// 角色定义
const roles = ref([
  {
    id: 'admin',
    name: '系统管理员',
    description: '拥有系统所有权限，可管理用户、配置和所有资源',
    color: '#ef4444',
    userCount: 2,
    permissions: ['*'],
  },
  {
    id: 'boss',
    name: '部门管理员',
    description: '可管理本部门的 Agent 和查看相关数据',
    color: '#f59e0b',
    userCount: 5,
    permissions: ['agent:read', 'agent:write', 'skill:read', 'skill:execute', 'data:read', 'data:write'],
  },
  {
    id: 'user',
    name: '普通用户',
    description: '可使用分配的 Agent 和技能，查看个人数据',
    color: '#6b7280',
    userCount: 28,
    permissions: ['agent:read', 'skill:read', 'skill:execute', 'data:read'],
  },
])

// 权限定义
const permissionGroups = ref([
  {
    name: 'Agent 管理',
    icon: 'robot',
    permissions: [
      { id: 'agent:read', name: '查看 Agent', description: '查看 Agent 列表和详情' },
      { id: 'agent:write', name: '编辑 Agent', description: '创建、修改和删除 Agent' },
      { id: 'agent:publish', name: '发布 Agent', description: '发布和下架 Agent' },
    ],
  },
  {
    name: '技能管理',
    icon: 'skill',
    permissions: [
      { id: 'skill:read', name: '查看技能', description: '查看技能列表和详情' },
      { id: 'skill:write', name: '编辑技能', description: '创建、修改和删除技能' },
      { id: 'skill:execute', name: '执行技能', description: '运行技能并获取结果' },
    ],
  },
  {
    name: '数据管理',
    icon: 'data',
    permissions: [
      { id: 'data:read', name: '查看数据', description: '查看数据便签和文件' },
      { id: 'data:write', name: '编辑数据', description: '上传、修改和删除数据' },
      { id: 'data:export', name: '导出数据', description: '导出数据和报告' },
    ],
  },
  {
    name: '系统管理',
    icon: 'system',
    permissions: [
      { id: 'user:read', name: '查看用户', description: '查看用户列表' },
      { id: 'user:write', name: '管理用户', description: '创建、修改和删除用户' },
      { id: 'config:read', name: '查看配置', description: '查看系统配置' },
      { id: 'config:write', name: '修改配置', description: '修改系统配置' },
      { id: 'log:read', name: '查看日志', description: '查看操作日志' },
    ],
  },
])

// API 权限
const apiPermissions = ref([
  { path: '/api/agent/*', methods: ['GET', 'POST', 'PUT', 'DELETE'], roles: ['admin', 'boss'], description: 'Agent 相关接口' },
  { path: '/api/skills/*', methods: ['GET', 'POST', 'PUT', 'DELETE'], roles: ['admin', 'boss'], description: '技能相关接口' },
  { path: '/api/execute', methods: ['POST'], roles: ['admin', 'boss', 'user'], description: '技能执行接口' },
  { path: '/api/users/*', methods: ['GET', 'POST', 'PUT', 'DELETE'], roles: ['admin'], description: '用户管理接口' },
  { path: '/api/config/*', methods: ['GET', 'PUT'], roles: ['admin'], description: '系统配置接口' },
  { path: '/api/logs/*', methods: ['GET'], roles: ['admin'], description: '日志查询接口' },
])

// 选中的角色（用于查看权限）
const selectedRole = ref<string | null>(null)

// 检查角色是否有某个权限
const roleHasPermission = (roleId: string, permissionId: string) => {
  const role = roles.value.find(r => r.id === roleId)
  if (!role) return false
  if (role.permissions.includes('*')) return true
  return role.permissions.includes(permissionId)
}

// 统计
const stats = computed(() => ({
  totalRoles: roles.value.length,
  totalPermissions: permissionGroups.value.reduce((acc, g) => acc + g.permissions.length, 0),
  totalUsers: roles.value.reduce((acc, r) => acc + r.userCount, 0),
}))
</script>

<template>
  <div class="permissions-page">
    <!-- 顶部 Tab 切换 -->
    <div class="page-tabs">
      <button
        v-for="tab in navTabs"
        :key="tab.id"
        class="tab-btn"
        :class="{ active: activeNavTab === tab.id }"
        @click="switchNavTab(tab)"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 头部 -->
    <div class="page-header">
      <p class="page-desc">管理系统角色、权限分配和 API 访问控制</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon purple">
          <svg viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ stats.totalRoles }}</span>
          <span class="stat-label">角色数量</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon blue">
          <svg viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ stats.totalPermissions }}</span>
          <span class="stat-label">权限项目</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green">
          <svg viewBox="0 0 20 20" fill="currentColor">
            <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-value">{{ stats.totalUsers }}</span>
          <span class="stat-label">分配用户</span>
        </div>
      </div>
    </div>

    <!-- 标签页 -->
    <div class="tabs">
      <button
        class="tab"
        :class="{ active: activeTab === 'roles' }"
        @click="activeTab = 'roles'"
      >
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/>
        </svg>
        角色管理
      </button>
      <button
        class="tab"
        :class="{ active: activeTab === 'permissions' }"
        @click="activeTab = 'permissions'"
      >
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd"/>
        </svg>
        权限矩阵
      </button>
      <button
        class="tab"
        :class="{ active: activeTab === 'api' }"
        @click="activeTab = 'api'"
      >
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd"/>
        </svg>
        API 权限
      </button>
    </div>

    <!-- 角色管理 -->
    <div v-if="activeTab === 'roles'" class="tab-content">
      <div class="roles-grid">
        <div v-for="role in roles" :key="role.id" class="role-card">
          <div class="role-header">
            <div class="role-icon" :style="{ background: role.color + '20', color: role.color }">
              <svg viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/>
              </svg>
            </div>
            <div class="role-info">
              <h3>{{ role.name }}</h3>
              <span class="role-id">{{ role.id }}</span>
            </div>
            <span class="user-count">{{ role.userCount }} 人</span>
          </div>
          <p class="role-desc">{{ role.description }}</p>
          <div class="role-permissions">
            <span class="permission-label">权限：</span>
            <div class="permission-tags">
              <span v-if="role.permissions.includes('*')" class="perm-tag all">全部权限</span>
              <template v-else>
                <span v-for="perm in role.permissions.slice(0, 4)" :key="perm" class="perm-tag">
                  {{ perm }}
                </span>
                <span v-if="role.permissions.length > 4" class="perm-tag more">
                  +{{ role.permissions.length - 4 }}
                </span>
              </template>
            </div>
          </div>
        </div>
      </div>

      <div class="info-box">
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
        </svg>
        <div>
          <strong>角色说明</strong>
          <p>系统预设了三种角色：系统管理员拥有全部权限，部门管理员可管理部门内的资源，普通用户仅可使用分配的功能。角色定义暂不支持自定义修改。</p>
        </div>
      </div>
    </div>

    <!-- 权限矩阵 -->
    <div v-if="activeTab === 'permissions'" class="tab-content">
      <div class="matrix-card">
        <table class="matrix-table">
          <thead>
            <tr>
              <th class="perm-col">权限</th>
              <th v-for="role in roles" :key="role.id" class="role-col">
                <div class="role-header-cell">
                  <span class="role-dot" :style="{ background: role.color }"></span>
                  {{ role.name }}
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            <template v-for="group in permissionGroups" :key="group.name">
              <tr class="group-row">
                <td colspan="4" class="group-cell">{{ group.name }}</td>
              </tr>
              <tr v-for="perm in group.permissions" :key="perm.id" class="perm-row">
                <td class="perm-cell">
                  <span class="perm-name">{{ perm.name }}</span>
                  <span class="perm-desc">{{ perm.description }}</span>
                </td>
                <td v-for="role in roles" :key="role.id" class="check-cell">
                  <span v-if="roleHasPermission(role.id, perm.id)" class="check-icon granted">
                    <svg viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                    </svg>
                  </span>
                  <span v-else class="check-icon denied">
                    <svg viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                    </svg>
                  </span>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- API 权限 -->
    <div v-if="activeTab === 'api'" class="tab-content">
      <div class="api-table-card">
        <table class="api-table">
          <thead>
            <tr>
              <th>API 路径</th>
              <th>允许方法</th>
              <th>允许角色</th>
              <th>说明</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(api, idx) in apiPermissions" :key="idx">
              <td class="api-path">{{ api.path }}</td>
              <td>
                <div class="method-tags">
                  <span v-for="method in api.methods" :key="method" class="method-tag" :class="method.toLowerCase()">
                    {{ method }}
                  </span>
                </div>
              </td>
              <td>
                <div class="role-tags">
                  <span
                    v-for="roleId in api.roles"
                    :key="roleId"
                    class="role-tag"
                    :style="{ background: roles.find(r => r.id === roleId)?.color + '20', color: roles.find(r => r.id === roleId)?.color }"
                  >
                    {{ roles.find(r => r.id === roleId)?.name }}
                  </span>
                </div>
              </td>
              <td class="api-desc">{{ api.description }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="info-box">
        <svg viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
        </svg>
        <div>
          <strong>API 访问控制</strong>
          <p>所有 API 请求都需要携带有效的 JWT Token。系统会根据 Token 中的角色信息验证访问权限。未授权的请求将返回 403 错误。</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.permissions-page {
  padding: 0 24px 24px;
  max-width: 1400px;
}

/* 顶部 Tab 切换 */
.page-tabs {
  display: flex;
  gap: 4px;
  padding: 16px 0 0;
  margin-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.tab-btn {
  padding: 10px 20px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: -1px;
}

.tab-btn:hover {
  color: #1f2937;
}

.tab-btn.active {
  color: #1677ff;
  border-bottom-color: #1677ff;
}

.page-header {
  margin-bottom: 24px;
}

.page-desc {
  color: #6b7280;
  font-size: 14px;
  margin: 0;
}

/* 统计卡片 */
.stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  min-width: 160px;
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon svg {
  width: 22px;
  height: 22px;
}

.stat-icon.purple { background: #f3e8ff; color: #9333ea; }
.stat-icon.blue { background: #eff6ff; color: #1677ff; }
.stat-icon.green { background: #ecfdf5; color: #10b981; }

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
}

.stat-label {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}

/* 标签页 */
.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 0;
}

.tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}

.tab:hover {
  color: #1677ff;
}

.tab.active {
  color: #1677ff;
  border-bottom-color: #1677ff;
}

.tab svg {
  width: 18px;
  height: 18px;
}

.tab-content {
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 角色卡片 */
.roles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.role-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.role-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.role-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.role-icon svg {
  width: 20px;
  height: 20px;
}

.role-info {
  flex: 1;
}

.role-info h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.role-id {
  font-size: 12px;
  color: #9ca3af;
}

.user-count {
  padding: 4px 10px;
  background: #f3f4f6;
  border-radius: 16px;
  font-size: 12px;
  color: #6b7280;
}

.role-desc {
  margin: 0 0 16px;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
}

.role-permissions {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.permission-label {
  font-size: 12px;
  color: #9ca3af;
  flex-shrink: 0;
  padding-top: 2px;
}

.permission-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.perm-tag {
  padding: 2px 8px;
  background: #f3f4f6;
  border-radius: 4px;
  font-size: 11px;
  color: #6b7280;
  font-family: 'SF Mono', monospace;
}

.perm-tag.all {
  background: #ecfdf5;
  color: #059669;
}

.perm-tag.more {
  background: #eff6ff;
  color: #1677ff;
}

/* 权限矩阵 */
.matrix-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.matrix-table {
  width: 100%;
  border-collapse: collapse;
}

.matrix-table th {
  padding: 14px 16px;
  background: #f9fafb;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

.matrix-table .perm-col {
  width: 40%;
}

.matrix-table .role-col {
  width: 20%;
  text-align: center;
}

.role-header-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.role-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.group-row .group-cell {
  padding: 10px 16px;
  background: #f3f4f6;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.perm-row td {
  padding: 12px 16px;
  border-bottom: 1px solid #f3f4f6;
}

.perm-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.perm-name {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
}

.perm-desc {
  font-size: 12px;
  color: #9ca3af;
}

.check-cell {
  text-align: center;
}

.check-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
}

.check-icon svg {
  width: 14px;
  height: 14px;
}

.check-icon.granted {
  background: #ecfdf5;
  color: #10b981;
}

.check-icon.denied {
  background: #f3f4f6;
  color: #d1d5db;
}

/* API 表格 */
.api-table-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  margin-bottom: 24px;
}

.api-table {
  width: 100%;
  border-collapse: collapse;
}

.api-table th {
  padding: 14px 16px;
  background: #f9fafb;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-align: left;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid #e5e7eb;
}

.api-table td {
  padding: 14px 16px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 13px;
}

.api-path {
  font-family: 'SF Mono', monospace;
  color: #1f2937;
}

.method-tags {
  display: flex;
  gap: 6px;
}

.method-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  font-family: 'SF Mono', monospace;
}

.method-tag.get { background: #ecfdf5; color: #059669; }
.method-tag.post { background: #eff6ff; color: #1677ff; }
.method-tag.put { background: #fff7ed; color: #f59e0b; }
.method-tag.delete { background: #fef2f2; color: #ef4444; }

.role-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.role-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.api-desc {
  color: #6b7280;
}

/* 信息框 */
.info-box {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: #eff6ff;
  border-radius: 10px;
  border-left: 4px solid #1677ff;
}

.info-box > svg {
  width: 20px;
  height: 20px;
  color: #1677ff;
  flex-shrink: 0;
  margin-top: 2px;
}

.info-box strong {
  display: block;
  font-size: 13px;
  color: #1f2937;
  margin-bottom: 4px;
}

.info-box p {
  margin: 0;
  font-size: 13px;
  color: #4b5563;
  line-height: 1.5;
}

/* 响应式 */
@media (max-width: 1024px) {
  .matrix-card {
    overflow-x: auto;
  }

  .matrix-table {
    min-width: 600px;
  }

  .api-table-card {
    overflow-x: auto;
  }

  .api-table {
    min-width: 700px;
  }
}

@media (max-width: 768px) {
  .permissions-page {
    padding: 16px;
  }

  .stats-row {
    flex-direction: column;
  }

  .tabs {
    overflow-x: auto;
    flex-wrap: nowrap;
  }

  .tab {
    white-space: nowrap;
  }

  .roles-grid {
    grid-template-columns: 1fr;
  }
}
</style>
