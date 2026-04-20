<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authApi } from '@/api'

const route = useRoute()
const router = useRouter()

// Tab 切换
const tabs = [
  { id: 'users', label: '用户管理', path: '/admin/users' },
  { id: 'permissions', label: '权限配置', path: '/admin/permissions' },
]
const activeTab = computed(() => route.path === '/admin/permissions' ? 'permissions' : 'users')
const switchTab = (tab: typeof tabs[0]) => {
  router.push(tab.path)
}

// 用户类型
interface User {
  id: string
  username: string
  display_name: string | null
  department: string | null
  role: 'user' | 'boss' | 'admin'
  is_active: boolean
  created_at: string | null
  last_login: string | null
}

// 状态
const users = ref<User[]>([])
const loading = ref(false)
const searchQuery = ref('')
const filterRole = ref<string>('')
const filterDepartment = ref<string>('')

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const pageSizeOptions = [10, 20, 50, 100]

// 弹框
const showEditModal = ref(false)
const showPasswordModal = ref(false)
const editingUser = ref<Partial<User> & { password?: string } | null>(null)
const newPassword = ref('')

// 选项数据
const departments = ref<string[]>([])
const roles = [
  { value: 'user', label: '普通用户', color: '#6b7280' },
  { value: 'boss', label: '部门管理员', color: '#f59e0b' },
  { value: 'admin', label: '系统管理员', color: '#ef4444' },
]

// 过滤后的用户列表
const filteredUsers = computed(() => {
  let result = users.value

  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(u =>
      u.username.toLowerCase().includes(q) ||
      u.display_name?.toLowerCase().includes(q) ||
      u.department?.toLowerCase().includes(q)
    )
  }

  if (filterRole.value) {
    result = result.filter(u => u.role === filterRole.value)
  }

  if (filterDepartment.value) {
    result = result.filter(u => u.department === filterDepartment.value)
  }

  return result
})

// 分页后的用户列表
const paginatedUsers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredUsers.value.slice(start, end)
})

// 总页数
const totalPages = computed(() => {
  return Math.ceil(filteredUsers.value.length / pageSize.value) || 1
})

// 显示的页码
const displayedPages = computed(() => {
  const pages: (number | string)[] = []
  const total = totalPages.value
  const current = currentPage.value

  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i)
  } else {
    pages.push(1)
    if (current > 3) pages.push('...')

    const start = Math.max(2, current - 1)
    const end = Math.min(total - 1, current + 1)

    for (let i = start; i <= end; i++) pages.push(i)

    if (current < total - 2) pages.push('...')
    pages.push(total)
  }

  return pages
})

// 监听筛选条件变化，重置到第一页
watch([searchQuery, filterRole, filterDepartment, pageSize], () => {
  currentPage.value = 1
})

// 跳转页码
const goToPage = (page: number | string) => {
  if (typeof page === 'number' && page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

// 统计
const stats = computed(() => ({
  total: users.value.length,
  active: users.value.filter(u => u.is_active).length,
  admins: users.value.filter(u => u.role === 'admin').length,
}))

// 加载数据
const loadUsers = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/users?limit=100', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
      },
    })
    if (response.ok) {
      const data = await response.json()
      // API 返回 { total, items } 格式
      users.value = data.items || data
    }
  } catch (e) {
    console.error('加载用户失败:', e)
  } finally {
    loading.value = false
  }
}

const loadDepartments = async () => {
  try {
    departments.value = await authApi.getDepartments()
  } catch (e) {
    console.error('加载部门失败:', e)
  }
}

// 打开编辑弹框
const openEdit = (user?: User) => {
  if (user) {
    editingUser.value = { ...user }
  } else {
    editingUser.value = {
      username: '',
      display_name: '',
      department: '',
      role: 'user',
      is_active: true,
      password: '',
    }
  }
  showEditModal.value = true
}

// 保存用户
const saveUser = async () => {
  if (!editingUser.value) return

  try {
    const url = editingUser.value.id ? `/api/users/${editingUser.value.id}` : '/api/users'
    const method = editingUser.value.id ? 'PUT' : 'POST'

    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
      },
      body: JSON.stringify(editingUser.value),
    })

    if (response.ok) {
      showEditModal.value = false
      await loadUsers()
    } else {
      const error = await response.json()
      alert(error.detail || '保存失败')
    }
  } catch (e) {
    alert('保存失败')
  }
}

// 删除用户
const deleteUser = async (user: User) => {
  if (!confirm(`确定删除用户 "${user.username}" 吗？`)) return

  try {
    const response = await fetch(`/api/users/${user.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
      },
    })

    if (response.ok) {
      await loadUsers()
    } else {
      alert('删除失败')
    }
  } catch (e) {
    alert('删除失败')
  }
}

// 切换用户状态
const toggleStatus = async (user: User) => {
  try {
    const response = await fetch(`/api/users/${user.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
      },
      body: JSON.stringify({ is_active: !user.is_active }),
    })

    if (response.ok) {
      await loadUsers()
    }
  } catch (e) {
    console.error('更新状态失败:', e)
  }
}

// 重置密码
const openPasswordModal = (user: User) => {
  editingUser.value = user
  newPassword.value = ''
  showPasswordModal.value = true
}

const resetPassword = async () => {
  if (!editingUser.value || !newPassword.value) return

  try {
    const response = await fetch(`/api/users/${editingUser.value.id}/password`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
      },
      body: JSON.stringify({ new_password: newPassword.value }),
    })

    if (response.ok) {
      showPasswordModal.value = false
      alert('密码重置成功')
    } else {
      alert('重置失败')
    }
  } catch (e) {
    alert('重置失败')
  }
}

// 格式化时间
const formatDate = (dateStr: string | null) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 获取角色信息
const getRoleInfo = (role: string) => {
  return roles.find(r => r.value === role) || { value: role, label: role, color: '#6b7280' }
}

onMounted(() => {
  loadUsers()
  loadDepartments()
})
</script>

<template>
  <div class="users-page">
    <!-- Tab 切换 -->
    <div class="page-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="tab-btn"
        :class="{ active: activeTab === tab.id }"
        @click="switchTab(tab)"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 固定头部区域 -->
    <div class="fixed-header">
      <!-- 头部 -->
      <div class="page-header">
        <div class="header-info">
          <p class="page-desc">管理系统用户、角色分配和账号状态</p>
        </div>
        <div class="header-actions">
          <div class="search-box">
            <svg class="search-icon" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
            </svg>
            <input v-model="searchQuery" type="text" placeholder="搜索用户..." />
          </div>
          <select v-model="filterRole" class="filter-select">
            <option value="">全部角色</option>
            <option v-for="r in roles" :key="r.value" :value="r.value">{{ r.label }}</option>
          </select>
          <select v-model="filterDepartment" class="filter-select">
            <option value="">全部部门</option>
            <option v-for="d in departments" :key="d" :value="d">{{ d }}</option>
          </select>
          <button class="btn-primary" @click="openEdit()">
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"/>
            </svg>
            新建用户
          </button>
        </div>
      </div>

      <!-- 统计卡片 -->
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-icon blue">
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/>
            </svg>
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ stats.total }}</span>
            <span class="stat-label">总用户数</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon green">
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ stats.active }}</span>
            <span class="stat-label">活跃用户</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon orange">
            <svg viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M18 8a6 6 0 01-7.743 5.743L10 14l-1 1-1 1H6v2H2v-4l4.257-4.257A6 6 0 1118 8zm-6-4a1 1 0 100 2 2 2 0 012 2 1 1 0 102 0 4 4 0 00-4-4z" clip-rule="evenodd"/>
            </svg>
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ stats.admins }}</span>
            <span class="stat-label">管理员</span>
          </div>
        </div>
      </div>

    </div>

    <!-- 表格容器 -->
    <div class="table-container">
      <!-- 表头 -->
      <div class="table-header">
        <div class="th-cell th-user">用户</div>
        <div class="th-cell th-dept">部门</div>
        <div class="th-cell th-role">角色</div>
        <div class="th-cell th-status">状态</div>
        <div class="th-cell th-login">最后登录</div>
        <div class="th-cell th-created">创建时间</div>
        <div class="th-cell th-actions">操作</div>
      </div>

      <!-- 表格内容 -->
      <div class="table-body-wrapper">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        加载中...
      </div>
      <div v-else-if="filteredUsers.length === 0" class="empty-state">暂无用户数据</div>
      <template v-else>
        <div v-for="user in paginatedUsers" :key="user.id" class="table-row">
          <div class="td-cell td-user">
            <div class="user-info">
              <div class="user-avatar">{{ (user.display_name || user.username).charAt(0).toUpperCase() }}</div>
              <div class="user-details">
                <span class="user-name">{{ user.display_name || user.username }}</span>
                <span class="user-username">@{{ user.username }}</span>
              </div>
            </div>
          </div>
          <div class="td-cell td-dept">
            <span class="dept-tag" v-if="user.department">{{ user.department }}</span>
            <span class="no-dept" v-else>-</span>
          </div>
          <div class="td-cell td-role">
            <span class="role-badge" :style="{ background: getRoleInfo(user.role).color + '20', color: getRoleInfo(user.role).color }">
              {{ getRoleInfo(user.role).label }}
            </span>
          </div>
          <div class="td-cell td-status">
            <button class="status-toggle" :class="{ active: user.is_active }" @click="toggleStatus(user)">
              <span class="toggle-dot"></span>
              {{ user.is_active ? '启用' : '禁用' }}
            </button>
          </div>
          <div class="td-cell td-login">{{ formatDate(user.last_login) }}</div>
          <div class="td-cell td-created">{{ formatDate(user.created_at) }}</div>
          <div class="td-cell td-actions">
            <div class="action-btns">
              <button class="icon-btn" @click="openEdit(user)" title="编辑">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"/>
                </svg>
              </button>
              <button class="icon-btn" @click="openPasswordModal(user)" title="重置密码">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M18 8a6 6 0 01-7.743 5.743L10 14l-1 1-1 1H6v2H2v-4l4.257-4.257A6 6 0 1118 8zm-6-4a1 1 0 100 2 2 2 0 012 2 1 1 0 102 0 4 4 0 00-4-4z" clip-rule="evenodd"/>
                </svg>
              </button>
              <button class="icon-btn danger" @click="deleteUser(user)" title="删除">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </template>
      </div>

      <!-- 分页 -->
      <div class="table-pagination" v-if="filteredUsers.length > 0">
        <div class="pagination-info">
          共 <strong>{{ filteredUsers.length }}</strong> 条，
          显示第 {{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, filteredUsers.length) }} 条
        </div>
        <div class="pagination-controls">
          <select v-model="pageSize" class="page-size-select">
            <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }} 条/页</option>
          </select>
          <div class="pagination-btns">
            <button class="page-btn" :disabled="currentPage === 1" @click="goToPage(currentPage - 1)">
              <svg viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd"/>
              </svg>
            </button>
            <template v-for="(page, idx) in displayedPages" :key="idx">
              <span v-if="page === '...'" class="page-ellipsis">...</span>
              <button v-else class="page-btn" :class="{ active: page === currentPage }" @click="goToPage(page)">
                {{ page }}
              </button>
            </template>
            <button class="page-btn" :disabled="currentPage === totalPages" @click="goToPage(currentPage + 1)">
              <svg viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑弹框 -->
    <Teleport to="body">
      <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
        <div class="modal">
          <div class="modal-header">
            <h2>{{ editingUser?.id ? '编辑用户' : '新建用户' }}</h2>
            <button class="modal-close" @click="showEditModal = false">&times;</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>用户名 <span class="required">*</span></label>
              <input v-model="editingUser!.username" type="text" placeholder="登录用户名" :disabled="!!editingUser?.id" />
            </div>
            <div class="form-group">
              <label>显示名称</label>
              <input v-model="editingUser!.display_name" type="text" placeholder="用户昵称" />
            </div>
            <div class="form-group" v-if="!editingUser?.id">
              <label>密码 <span class="required">*</span></label>
              <input v-model="editingUser!.password" type="password" placeholder="登录密码" />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>部门</label>
                <select v-model="editingUser!.department">
                  <option value="">无部门</option>
                  <option v-for="d in departments" :key="d" :value="d">{{ d }}</option>
                </select>
              </div>
              <div class="form-group">
                <label>角色 <span class="required">*</span></label>
                <select v-model="editingUser!.role">
                  <option v-for="r in roles" :key="r.value" :value="r.value">{{ r.label }}</option>
                </select>
              </div>
            </div>
            <div class="form-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="editingUser!.is_active" />
                <span>账号启用</span>
              </label>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="showEditModal = false">取消</button>
            <button class="btn-primary" @click="saveUser">保存</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 重置密码弹框 -->
    <Teleport to="body">
      <div v-if="showPasswordModal" class="modal-overlay" @click.self="showPasswordModal = false">
        <div class="modal modal-sm">
          <div class="modal-header">
            <h2>重置密码</h2>
            <button class="modal-close" @click="showPasswordModal = false">&times;</button>
          </div>
          <div class="modal-body">
            <p class="modal-hint">为用户 <strong>{{ editingUser?.username }}</strong> 设置新密码</p>
            <div class="form-group">
              <label>新密码 <span class="required">*</span></label>
              <input v-model="newPassword" type="password" placeholder="输入新密码" />
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="showPasswordModal = false">取消</button>
            <button class="btn-primary" @click="resetPassword" :disabled="!newPassword">确认重置</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.users-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* Tab 切换 */
.page-tabs {
  display: flex;
  gap: 4px;
  padding: 16px 24px 0;
  background: #f5f7fa;
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

/* 固定头部区域 */
.fixed-header {
  flex-shrink: 0;
  padding: 16px 24px 0;
  background: #f5f7fa;
}

/* 头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  gap: 16px;
  flex-wrap: wrap;
}

.page-desc {
  color: #6b7280;
  font-size: 14px;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.search-box {
  position: relative;
}

.search-box .search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: #9ca3af;
}

.search-box input {
  padding: 8px 12px 8px 36px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 13px;
  width: 200px;
}

.search-box input:focus {
  outline: none;
  border-color: #1677ff;
  box-shadow: 0 0 0 3px rgba(22, 119, 255, 0.1);
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 13px;
  background: white;
  min-width: 120px;
}

.filter-select:focus {
  outline: none;
  border-color: #1677ff;
}

/* 按钮 */
.btn-primary, .btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-primary {
  background: #1677ff;
  color: white;
}

.btn-primary:hover {
  background: #4096ff;
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.btn-secondary {
  background: white;
  color: #374151;
  border: 1px solid #e5e7eb;
}

.btn-secondary:hover {
  background: #f9fafb;
}

.btn-primary svg, .btn-secondary svg {
  width: 16px;
  height: 16px;
}

/* 统计卡片 */
.stats-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
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

.stat-icon.blue { background: #eff6ff; color: #1677ff; }
.stat-icon.green { background: #ecfdf5; color: #10b981; }
.stat-icon.orange { background: #fff7ed; color: #f59e0b; }

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

/* 表格容器 */
.table-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin: 0 24px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

/* 表头 */
.table-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1.2fr 1.2fr 120px;
  background: #f9fafb;
  flex-shrink: 0;
}

.th-cell {
  padding: 12px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 表格内容区域 */
.table-body-wrapper {
  flex: 1;
  overflow-y: auto;
}

.table-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1.2fr 1.2fr 120px;
  border-top: 1px solid #f3f4f6;
  transition: background 0.15s;
}

.table-row:hover {
  background: #f9fafb;
}

.table-row:last-child {
  border-bottom: none;
}

.td-cell {
  padding: 14px 16px;
  font-size: 13px;
  color: #374151;
  display: flex;
  align-items: center;
}

.td-login, .td-created {
  color: #9ca3af;
  font-size: 12px;
}

/* 加载和空状态 */
.loading-state, .empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 16px;
  color: #9ca3af;
  gap: 12px;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #e5e7eb;
  border-top-color: #1677ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 用户信息 */
.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.user-details {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-weight: 500;
  color: #1f2937;
}

.user-username {
  font-size: 12px;
  color: #9ca3af;
}

/* 部门标签 */
.dept-tag {
  display: inline-block;
  padding: 2px 8px;
  background: #f3f4f6;
  border-radius: 4px;
  font-size: 12px;
  color: #4b5563;
}

.no-dept {
  color: #d1d5db;
}

/* 角色标签 */
.role-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

/* 状态切换 */
.status-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: #f3f4f6;
  border: none;
  border-radius: 16px;
  font-size: 12px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}

.status-toggle.active {
  background: #ecfdf5;
  color: #059669;
}

.toggle-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

/* 操作按钮 */
.action-btns {
  display: flex;
  gap: 4px;
}

.icon-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #9ca3af;
  cursor: pointer;
  transition: all 0.15s;
}

.icon-btn:hover {
  background: #f3f4f6;
  color: #1677ff;
}

.icon-btn.danger:hover {
  background: #fef2f2;
  color: #ef4444;
}

.icon-btn svg {
  width: 16px;
  height: 16px;
}

/* 弹框 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.modal.modal-sm {
  max-width: 400px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.modal-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 8px;
  font-size: 24px;
  color: #9ca3af;
  cursor: pointer;
}

.modal-close:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
}

.modal-hint {
  margin: 0 0 16px;
  color: #6b7280;
  font-size: 14px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

/* 表单 */
.form-group {
  margin-bottom: 16px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 6px;
}

.form-group label .required {
  color: #ef4444;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 13px;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #1677ff;
  box-shadow: 0 0 0 3px rgba(22, 119, 255, 0.1);
}

.form-group input:disabled {
  background: #f3f4f6;
  color: #9ca3af;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.checkbox-label {
  display: flex !important;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-label input {
  width: auto !important;
}

/* 分页 */
.table-pagination {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

.pagination-info {
  font-size: 13px;
  color: #6b7280;
}

.pagination-info strong {
  color: #1f2937;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-size-select {
  padding: 6px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  background: white;
}

.page-size-select:focus {
  outline: none;
  border-color: #1677ff;
}

.pagination-btns {
  display: flex;
  align-items: center;
  gap: 4px;
}

.page-btn {
  min-width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
  transition: all 0.15s;
  padding: 0 8px;
}

.page-btn:hover:not(:disabled) {
  border-color: #1677ff;
  color: #1677ff;
}

.page-btn.active {
  background: #1677ff;
  border-color: #1677ff;
  color: white;
}

.page-btn:disabled {
  color: #d1d5db;
  cursor: not-allowed;
  background: #f9fafb;
}

.page-btn svg {
  width: 16px;
  height: 16px;
}

.page-ellipsis {
  padding: 0 4px;
  color: #9ca3af;
}

/* 响应式 */
@media (max-width: 1200px) {
  .table-header,
  .table-row {
    grid-template-columns: 1.5fr 1fr 1fr 1fr 1fr 1fr 100px;
  }
}

@media (max-width: 1024px) {
  .table-header,
  .table-row {
    grid-template-columns: 1.5fr 0.8fr 0.8fr 0.8fr 1fr 1fr 90px;
  }

  .th-cell,
  .td-cell {
    padding: 10px 12px;
    font-size: 12px;
  }
}

@media (max-width: 768px) {
  .fixed-header {
    padding: 16px 16px 0;
  }

  .table-container {
    margin: 0 16px 16px;
  }

  .page-header {
    flex-direction: column;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .stats-row {
    flex-wrap: wrap;
  }

  .stat-card {
    min-width: calc(50% - 6px);
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .table-pagination {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .pagination-controls {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
