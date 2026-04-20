<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 侧边栏状态 (持久化到 localStorage)
const SIDEBAR_KEY = 'admin_sidebar_collapsed'
const sidebarCollapsed = ref(localStorage.getItem(SIDEBAR_KEY) === 'true')

watch(sidebarCollapsed, (val) => {
  localStorage.setItem(SIDEBAR_KEY, String(val))
})

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// AI 菜单（独立区块）
const aiMenuItems = [
  { path: '/admin/agents', icon: 'robot', label: 'Agent 管理' },
  { path: '/admin/models', icon: 'model', label: '模型配置' },
  { path: '/admin/tokens', icon: 'token', label: 'Token 用量' },
]

// 系统管理菜单
const systemMenuItems = [
  { path: '/admin/dashboard', icon: 'dashboard', label: '驾驶舱' },
  { path: '/admin/users', icon: 'users', label: '用户权限' },
  { path: '/admin/logs', icon: 'log', label: '操作日志' },
  { path: '/admin/apis', icon: 'api', label: 'API 管理' },
]

// 当前页面标题
const currentPageTitle = computed(() => route.meta.title as string || '管理后台')

// 用户信息
const userInitial = computed(() => authStore.displayName?.charAt(0) || 'A')
const displayName = computed(() => authStore.displayName || 'Admin')

// 退出登录
const handleLogout = async () => {
  await authStore.logout()
  router.push('/login')
}

// 检查菜单激活
const isActive = (path: string) => {
  if (path === '/admin/agents') {
    return route.path === '/admin/agents' || route.path === '/admin/agent-studio'
  }
  if (path === '/admin/users') {
    // 用户权限页面合并了用户管理和权限管理
    return route.path === '/admin/users' || route.path === '/admin/permissions'
  }
  return route.path === path || route.path.startsWith(path + '/')
}
</script>

<template>
  <div class="admin-layout">
    <!-- 侧边栏 -->
    <aside class="admin-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <router-link to="/" class="logo">
          <div class="logo-icon">IK</div>
          <span v-if="!sidebarCollapsed" class="logo-text">Admin</span>
        </router-link>
        <button class="collapse-btn" @click="toggleSidebar" :title="sidebarCollapsed ? '展开' : '收起'">
          <svg viewBox="0 0 20 20" fill="currentColor" :class="{ rotated: sidebarCollapsed }">
            <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd"/>
          </svg>
        </button>
      </div>

      <nav class="sidebar-menu">
        <!-- AI 能力区块 -->
        <div class="ai-section">
          <div v-if="!sidebarCollapsed" class="section-header">
            <span class="section-icon">✨</span>
            <span class="section-title">AI 能力</span>
          </div>
          <router-link
            v-for="item in aiMenuItems"
            :key="item.path"
            :to="item.path"
            class="menu-item ai-item"
            :class="{ active: isActive(item.path) }"
            :title="sidebarCollapsed ? item.label : ''"
          >
            <span class="menu-icon">
              <svg v-if="item.icon === 'robot'" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.715-5.349L10 6.477V16h2a1 1 0 110 2H8a1 1 0 110-2h2V6.477L6.237 7.582l1.715 5.349a1 1 0 01-.285 1.05A3.989 3.989 0 015 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L9 4.323V3a1 1 0 011-1z" clip-rule="evenodd"/>
              </svg>
              <svg v-else-if="item.icon === 'model'" viewBox="0 0 20 20" fill="currentColor">
                <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z"/>
              </svg>
              <svg v-else-if="item.icon === 'token'" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clip-rule="evenodd"/>
              </svg>
            </span>
            <span v-if="!sidebarCollapsed" class="menu-label">{{ item.label }}</span>
          </router-link>
        </div>

        <!-- 系统管理区块 -->
        <div class="system-section">
          <div v-if="!sidebarCollapsed" class="section-header">
            <span class="section-title">系统管理</span>
          </div>
          <router-link
            v-for="item in systemMenuItems"
            :key="item.path"
            :to="item.path"
            class="menu-item"
            :class="{ active: isActive(item.path) }"
            :title="sidebarCollapsed ? item.label : ''"
          >
            <span class="menu-icon">
              <svg v-if="item.icon === 'dashboard'" viewBox="0 0 20 20" fill="currentColor">
                <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"/>
              </svg>
              <svg v-else-if="item.icon === 'users'" viewBox="0 0 20 20" fill="currentColor">
                <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/>
              </svg>
              <svg v-else-if="item.icon === 'log'" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"/>
              </svg>
              <svg v-else-if="item.icon === 'api'" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd"/>
              </svg>
            </span>
            <span v-if="!sidebarCollapsed" class="menu-label">{{ item.label }}</span>
          </router-link>
        </div>
      </nav>

      <div class="sidebar-footer">
        <router-link to="/" class="back-home" :title="sidebarCollapsed ? '返回首页' : ''">
          <span class="menu-icon">
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z"/>
            </svg>
          </span>
          <span v-if="!sidebarCollapsed" class="menu-label">返回首页</span>
        </router-link>
      </div>
    </aside>

    <!-- 主内容区 -->
    <div class="admin-main">
      <!-- 顶部导航栏 -->
      <header class="admin-header">
        <div class="header-left">
          <h1 class="page-title">{{ currentPageTitle }}</h1>
        </div>
        <div class="header-right">
          <div class="user-info">
            <span class="user-avatar">{{ userInitial }}</span>
            <span class="user-name">{{ displayName }}</span>
          </div>
          <button class="btn-logout" @click="handleLogout">
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z" clip-rule="evenodd"/>
            </svg>
            退出
          </button>
        </div>
      </header>

      <!-- 内容区域 -->
      <main class="admin-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.admin-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: #f5f7fa;
}

/* 侧边栏 */
.admin-sidebar {
  width: 240px;
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  flex-shrink: 0;
}

.admin-sidebar.collapsed {
  width: 64px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
  min-height: 64px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
}

.logo-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #1677ff, #4096ff);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 13px;
  flex-shrink: 0;
}

.logo-text {
  font-weight: 600;
  font-size: 16px;
  color: #1f2937;
}

.collapse-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #9ca3af;
  cursor: pointer;
  transition: all 0.2s;
}

.collapse-btn:hover {
  background: #f3f4f6;
  color: #6b7280;
}

.collapse-btn svg {
  width: 16px;
  height: 16px;
  transition: transform 0.3s;
}

.collapse-btn svg.rotated {
  transform: rotate(180deg);
}

.admin-sidebar.collapsed .sidebar-header {
  justify-content: center;
  padding: 16px 8px;
}

.admin-sidebar.collapsed .collapse-btn {
  display: none;
}

/* 菜单 */
.sidebar-menu {
  flex: 1;
  padding: 8px 0;
  overflow-y: auto;
}

/* 收起状态下的 AI 区块 */
.admin-sidebar.collapsed .ai-section {
  margin: 0 4px 8px;
  padding: 4px;
}

.admin-sidebar.collapsed .system-section {
  padding: 0 4px;
}

/* AI 能力区块 - 突出显示 */
.ai-section {
  margin: 0 8px 12px;
  padding: 8px;
  background: linear-gradient(135deg, #f0f9ff 0%, #faf5ff 100%);
  border-radius: 12px;
  border: 1px solid #e0e7ff;
}

.ai-section .section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px 8px;
}

.ai-section .section-icon {
  font-size: 14px;
}

.ai-section .section-title {
  font-size: 12px;
  font-weight: 600;
  color: #6366f1;
}

.ai-section .menu-item {
  margin-bottom: 2px;
}

.ai-section .menu-item.active {
  background: white;
  color: #6366f1;
  box-shadow: 0 1px 3px rgba(99, 102, 241, 0.1);
}

.ai-section .menu-item:hover:not(.active) {
  background: rgba(255, 255, 255, 0.6);
}

/* 系统管理区块 */
.system-section {
  padding: 0 8px;
}

.system-section .section-header {
  padding: 8px 8px 6px;
}

.system-section .section-title {
  font-size: 11px;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  color: #6b7280;
  text-decoration: none;
  transition: all 0.2s;
  margin-bottom: 4px;
}

.menu-item:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.menu-item.active {
  background: #eff6ff;
  color: #1677ff;
}

.menu-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.menu-icon svg {
  width: 18px;
  height: 18px;
}

.menu-label {
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
}

.admin-sidebar.collapsed .menu-item {
  justify-content: center;
  padding: 10px;
}

.admin-sidebar.collapsed .ai-section .menu-item {
  padding: 8px;
}

/* 侧边栏底部 */
.sidebar-footer {
  padding: 12px 8px;
  border-top: 1px solid #e5e7eb;
}

.back-home {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  color: #6b7280;
  text-decoration: none;
  transition: all 0.2s;
}

.back-home:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.admin-sidebar.collapsed .back-home {
  justify-content: center;
  padding: 10px;
}

/* 主内容区 */
.admin-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

/* 顶部导航栏 */
.admin-header {
  height: 64px;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-avatar {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 13px;
  font-weight: 600;
}

.user-name {
  font-size: 13px;
  color: #6b7280;
}

.btn-logout {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  color: #6b7280;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-logout:hover {
  background: #fee2e2;
  border-color: #fecaca;
  color: #ef4444;
}

.btn-logout svg {
  width: 16px;
  height: 16px;
}

/* 内容区域 */
.admin-content {
  flex: 1;
  overflow: auto;
}

/* 响应式 */
@media (max-width: 1024px) {
  .admin-sidebar {
    width: 64px;
  }

  .admin-sidebar .logo-text,
  .admin-sidebar .menu-label,
  .admin-sidebar .sidebar-footer .menu-label {
    display: none;
  }

  .admin-sidebar .menu-item,
  .admin-sidebar .back-home {
    justify-content: center;
    padding: 10px;
  }

  .admin-sidebar .sidebar-header {
    justify-content: center;
    padding: 16px 8px;
  }

  .admin-sidebar .collapse-btn {
    display: none;
  }
}

@media (max-width: 768px) {
  .admin-header {
    padding: 0 16px;
  }

  .user-name {
    display: none;
  }
}
</style>
