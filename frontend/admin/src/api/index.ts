// Admin API Configuration and Services
import config from '@/config'

const API_BASE_URL = config.apiBaseUrl

// 获取 token
function getAuthToken(): string | null {
  return localStorage.getItem('auth_token')
}

// Generic fetch wrapper
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  const token = getAuthToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers as Record<string, string>,
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  const response = await fetch(url, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || `HTTP error! status: ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

// ============ Dashboard API ============

export interface DashboardStats {
  today_sessions: number
  today_messages: number
  today_executions: number
  today_tokens: number
  total_sessions: number
  total_messages: number
  total_tokens: number
  active_users: number
  success_rate: number
  avg_latency: number
  skill_count: number
  agent_count: number
  pending_feedbacks: number
  total_feedbacks: number
  session_growth: number
}

export interface DashboardTrends {
  dates: string[]
  sessions: number[]
  messages: number[]
  executions: number[]
  tokens: number[]
}

export const dashboardApi = {
  getStats: () => request<DashboardStats>('/dashboard/stats'),
  getTrends: (days: number = 7) => request<DashboardTrends>(`/dashboard/trends?days=${days}`),
}

// ============ Models API ============

export interface ModelConfig {
  id: string
  name: string
  provider: string  // anthropic, openai, azure
  model_id: string
  api_key: string
  base_url?: string
  max_tokens?: number
  temperature?: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ModelConfigCreate {
  name: string
  provider: string
  model_id: string
  api_key: string
  base_url?: string
  max_tokens?: number
  temperature?: number
}

export const modelsApi = {
  getAll: () => request<ModelConfig[]>('/models'),
  getById: (id: string) => request<ModelConfig>(`/models/${id}`),
  create: (data: ModelConfigCreate) => request<ModelConfig>('/models', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  update: (id: string, data: Partial<ModelConfigCreate>) => request<ModelConfig>(`/models/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  delete: (id: string) => request<void>(`/models/${id}`, { method: 'DELETE' }),
  test: (id: string) => request<{ success: boolean; message: string }>(`/models/${id}/test`, { method: 'POST' }),
}

// ============ Tokens API ============

export interface TokenUsage {
  id: string
  user_id: string
  skill_id?: string
  skill_name?: string
  input_tokens: number
  output_tokens: number
  total_tokens: number
  cost: number
  created_at: string
}

export interface TokenSummary {
  total_tokens: number
  total_cost: number
  by_user: { user_id: string; tokens: number; cost: number }[]
  by_skill: { skill_name: string; tokens: number; cost: number }[]
  by_date: { date: string; tokens: number; cost: number }[]
}

export const tokensApi = {
  getSummary: (startDate?: string, endDate?: string) => {
    const params = new URLSearchParams()
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)
    return request<TokenSummary>(`/tokens/summary?${params}`)
  },
  getUsage: (page: number = 1, limit: number = 50) =>
    request<{ items: TokenUsage[]; total: number }>(`/tokens/usage?page=${page}&limit=${limit}`),
}

// ============ Users API ============

export interface User {
  id: string
  username: string
  email?: string
  role: string
  is_active: boolean
  created_at: string
  last_login?: string
}

export const usersApi = {
  getAll: () => request<User[]>('/users'),
  getById: (id: string) => request<User>(`/users/${id}`),
  create: (data: Partial<User>) => request<User>('/users', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  update: (id: string, data: Partial<User>) => request<User>(`/users/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  delete: (id: string) => request<void>(`/users/${id}`, { method: 'DELETE' }),
}

// ============ Logs API ============

export interface LogEntry {
  id: string
  type: 'operation' | 'api_call' | 'error'
  user_id?: string
  action: string
  details?: Record<string, any>
  ip_address?: string
  created_at: string
}

export const logsApi = {
  getAll: (type?: string, page: number = 1, limit: number = 50) => {
    const params = new URLSearchParams()
    if (type) params.append('type', type)
    params.append('page', page.toString())
    params.append('limit', limit.toString())
    return request<{ items: LogEntry[]; total: number }>(`/logs?${params}`)
  },
}

// ============ Auth API ============

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: {
    id: string
    username: string
    display_name: string | null
    department: string | null
    role: 'user' | 'boss' | 'admin'
    is_active: boolean
    created_at: string | null
    last_login: string | null
  }
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

export const authApi = {
  login: (data: LoginRequest) =>
    request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  logout: () =>
    request<{ message: string }>('/auth/logout', {
      method: 'POST',
    }),
  me: () => request<LoginResponse['user']>('/auth/me'),
  changePassword: (data: ChangePasswordRequest) =>
    request<{ message: string }>('/auth/password', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  getDepartments: () => request<string[]>('/users/departments'),
  getRoles: () => request<string[]>('/users/roles'),
}

// ============ CCSwitch API ============

export interface CCConfig {
  id: string
  name: string
  description?: string
  model_id: string
  api_key: string
  base_url?: string
  max_tokens?: number
  temperature?: number
  top_p?: number
  system_prompt?: string
  extra_params?: Record<string, any>
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CCConfigCreate {
  name: string
  description?: string
  model_id: string
  api_key: string
  base_url?: string
  max_tokens?: number
  temperature?: number
  top_p?: number
  system_prompt?: string
  extra_params?: Record<string, any>
}

export interface TestResult {
  success: boolean
  message: string
  latency_ms?: number
  response_preview?: string
}

export const ccswitchApi = {
  getAll: (isActive?: boolean) => {
    const params = isActive !== undefined ? `?is_active=${isActive}` : ''
    return request<CCConfig[]>(`/ccswitch${params}`)
  },
  getById: (id: string) => request<CCConfig>(`/ccswitch/${id}`),
  create: (data: CCConfigCreate) => request<CCConfig>('/ccswitch', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  update: (id: string, data: Partial<CCConfigCreate>) => request<CCConfig>(`/ccswitch/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  delete: (id: string) => request<void>(`/ccswitch/${id}`, { method: 'DELETE' }),
  test: (id: string) => request<TestResult>(`/ccswitch/${id}/test`, { method: 'POST' }),
  toggle: (id: string) => request<{ id: string; is_active: boolean; message: string }>(`/ccswitch/${id}/toggle`, { method: 'POST' }),
  copy: (id: string) => request<CCConfig>(`/ccswitch/${id}/copy`, { method: 'POST' }),
  export: (id: string) => request<CCConfig>(`/ccswitch/${id}/export`),
  exportAll: () => request<{ configs: CCConfig[]; exported_at: string }>('/ccswitch/export/all'),
  import: (data: any) => request<{ imported: string[]; errors: string[]; message: string }>('/ccswitch/import', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
}

// ============ Feedback API ============

export interface Feedback {
  id: string
  user_id: string
  session_id: string | null
  agent_id: string | null
  agent_name: string | null
  feedback_type: string
  title: string
  description: string | null
  status: string
  admin_notes: string | null
  created_at: string | null
  updated_at: string | null
}

export interface FeedbackListResponse {
  items: Feedback[]
  total: number
}

export interface FeedbackUpdate {
  status?: 'pending' | 'processing' | 'resolved' | 'closed'
  admin_notes?: string
}

export const feedbackApi = {
  // 获取反馈列表
  getAll: (params?: { status?: string; feedback_type?: string; keyword?: string; page?: number; page_size?: number }) => {
    const searchParams = new URLSearchParams()
    if (params?.status) searchParams.append('status', params.status)
    if (params?.feedback_type) searchParams.append('feedback_type', params.feedback_type)
    if (params?.keyword) searchParams.append('keyword', params.keyword)
    if (params?.page) searchParams.append('page', params.page.toString())
    if (params?.page_size) searchParams.append('page_size', params.page_size.toString())
    const query = searchParams.toString()
    return request<FeedbackListResponse>(`/feedback${query ? `?${query}` : ''}`)
  },

  // 获取反馈详情
  getById: (id: string) => request<Feedback>(`/feedback/${id}`),

  // 更新反馈
  update: (id: string, data: FeedbackUpdate) =>
    request<Feedback>(`/feedback/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  // 删除反馈
  delete: (id: string) =>
    request<void>(`/feedback/${id}`, { method: 'DELETE' }),
}

// ============ Agents API ============

export interface Agent {
  id: string
  name: string
  description: string
  icon: string
  category: string
  system_prompt: string
  model: string
  temperature: number
  max_tokens: number
  tools: string[]
  skills: string[]
  accessible_agent_ids: string[]  // 可访问的其他 Agent 数据
  status: string
  author: string
  version: string
  usage_count: number
  created_at: string
  updated_at: string
}

export interface AgentListResponse {
  agents: Agent[]
  total: number
}

export interface AgentUpdate {
  name?: string
  description?: string
  icon?: string
  category?: string
  system_prompt?: string
  model?: string
  temperature?: number
  max_tokens?: number
  tools?: string[]
  skills?: string[]
  accessible_agent_ids?: string[]
  status?: string
}

export const agentsApi = {
  // 获取 Agent 列表
  getAll: (params?: { category?: string; status?: string; search?: string }) => {
    const searchParams = new URLSearchParams()
    if (params?.category) searchParams.append('category', params.category)
    if (params?.status) searchParams.append('status', params.status)
    if (params?.search) searchParams.append('search', params.search)
    const query = searchParams.toString()
    return request<AgentListResponse>(`/agents${query ? `?${query}` : ''}`)
  },

  // 获取单个 Agent
  getById: (id: string) => request<Agent>(`/agents/${id}`),

  // 创建 Agent
  create: (data: AgentUpdate) =>
    request<Agent>('/agents', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // 更新 Agent
  update: (id: string, data: AgentUpdate) =>
    request<Agent>(`/agents/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  // 删除 Agent
  delete: (id: string) =>
    request<{ status: string; message: string }>(`/agents/${id}`, {
      method: 'DELETE',
    }),
}

// ============ Skills API ============

export interface Skill {
  id: string
  group_id: string
  name: string
  description: string
  icon: string
  tags: string[]
  folder_path: string
  entry_script: string
  author: string
  version: string
  status: string
  minio_synced: boolean  // 是否已同步到 MinIO
  created_at: string
  updated_at: string
}

export interface SkillCreate {
  name: string
  description?: string
  icon?: string
  tags?: string[]
  entry_script?: string
  code?: string
}

export interface SkillPreview {
  name: string
  description: string
  icon: string
  tags: string[]
  author: string
  version: string
  entry_script: string
  files: string[]
  ai_analysis?: {
    description?: string
    capabilities?: string[]
    tags?: string[]
    icon?: string
  }
}

export const skillsApi = {
  // 获取技能列表
  getAll: () => request<Skill[]>('/skills'),

  // 获取单个技能
  getById: (id: string) => request<Skill>(`/skills/${id}`),

  // 创建技能
  create: (data: SkillCreate) => request<Skill>('/skills', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  // 预览上传的 ZIP 包内容
  preview: async (file: File): Promise<SkillPreview> => {
    const formData = new FormData()
    formData.append('file', file)

    const token = localStorage.getItem('auth_token')
    const response = await fetch(`${config.apiBaseUrl}/skills/upload/preview`, {
      method: 'POST',
      headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: '解析失败' }))
      throw new Error(error.detail || '解析失败')
    }

    return response.json()
  },

  // 上传技能 ZIP
  upload: async (file: File, data: { name: string; description?: string; icon?: string; tags?: string; version?: string; entry_script?: string }) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('name', data.name)
    if (data.description) formData.append('description', data.description)
    if (data.icon) formData.append('icon', data.icon)
    if (data.tags) formData.append('tags', data.tags)
    if (data.version) formData.append('version', data.version)
    if (data.entry_script) formData.append('entry_script', data.entry_script)

    const token = localStorage.getItem('auth_token')
    const response = await fetch(`${config.apiBaseUrl}/skills/upload`, {
      method: 'POST',
      headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: '上传失败' }))
      throw new Error(error.detail || '上传失败')
    }

    return response.json()
  },

  // 下载技能
  download: (id: string, filename: string) => {
    const token = localStorage.getItem('auth_token')
    const url = `${config.apiBaseUrl}/skills/${id}/download`

    // 使用隐藏的 a 标签触发下载
    fetch(url, {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {},
    })
      .then(res => res.blob())
      .then(blob => {
        const a = document.createElement('a')
        a.href = URL.createObjectURL(blob)
        a.download = filename
        a.click()
        URL.revokeObjectURL(a.href)
      })
  },

  // 删除技能
  delete: (id: string) => request<void>(`/skills/${id}`, { method: 'DELETE' }),

  // 推送到 MinIO
  push: (id: string) => request<any>(`/skills/${id}/push`, { method: 'POST' }),

  // 推送全部
  pushAll: () => request<any>('/skills/push-all', { method: 'POST' }),

  // 从 MinIO 同步
  sync: (id: string) => request<any>(`/skills/${id}/sync`, { method: 'POST' }),

  // 同步全部
  syncAll: () => request<any>('/skills/sync-all', { method: 'POST' }),
}

// Export all APIs
export default {
  dashboard: dashboardApi,
  users: usersApi,
  logs: logsApi,
  auth: authApi,
  feedback: feedbackApi,
  agents: agentsApi,
}
