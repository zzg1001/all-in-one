/**
 * Auth Store - Admin 认证状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import config from '@/config'

const API_BASE_URL = config.apiBaseUrl

// 用户信息类型
export interface User {
  id: string
  username: string
  display_name: string | null
  department: string | null
  role: 'user' | 'boss' | 'admin'
  is_active: boolean
  created_at: string | null
  last_login: string | null
}

// 登录响应类型
interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

// Token 存储 key
const TOKEN_KEY = 'auth_token'
const USER_KEY = 'auth_user'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 初始化时从 localStorage 恢复用户信息
  const savedUser = localStorage.getItem(USER_KEY)
  if (savedUser) {
    try {
      user.value = JSON.parse(savedUser)
    } catch (e) {
      localStorage.removeItem(USER_KEY)
    }
  }

  // 计算属性
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const displayName = computed(() => user.value?.display_name || user.value?.username || '')

  // 登录
  async function login(username: string, password: string): Promise<boolean> {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '登录失败' }))
        throw new Error(errorData.detail || '登录失败')
      }

      const data: LoginResponse = await response.json()

      // 检查是否是管理员
      if (data.user.role !== 'admin') {
        throw new Error('您没有管理后台访问权限')
      }

      // 保存 token 和用户信息
      token.value = data.access_token
      user.value = data.user
      localStorage.setItem(TOKEN_KEY, data.access_token)
      localStorage.setItem(USER_KEY, JSON.stringify(data.user))

      return true
    } catch (e: any) {
      error.value = e.message || '登录失败'
      return false
    } finally {
      loading.value = false
    }
  }

  // 登出
  async function logout() {
    try {
      if (token.value) {
        await fetch(`${API_BASE_URL}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token.value}`,
          },
        }).catch(() => {})
      }
    } finally {
      token.value = null
      user.value = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    }
  }

  // 检查认证状态
  async function checkAuth(): Promise<boolean> {
    if (!token.value) {
      return false
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token.value}`,
        },
      })

      if (!response.ok) {
        await logout()
        return false
      }

      const userData: User = await response.json()

      // 检查是否是管理员
      if (userData.role !== 'admin') {
        await logout()
        return false
      }

      user.value = userData
      localStorage.setItem(USER_KEY, JSON.stringify(userData))
      return true
    } catch (e) {
      await logout()
      return false
    }
  }

  // 获取 Authorization header
  function getAuthHeader(): Record<string, string> {
    if (token.value) {
      return { 'Authorization': `Bearer ${token.value}` }
    }
    return {}
  }

  return {
    token,
    user,
    loading,
    error,
    isAuthenticated,
    isAdmin,
    displayName,
    login,
    logout,
    checkAuth,
    getAuthHeader,
  }
})
