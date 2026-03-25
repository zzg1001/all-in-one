// Admin API Configuration and Services
import config from '@/config'

const API_BASE_URL = config.apiBaseUrl

// Generic fetch wrapper
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
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
  today_calls: number
  today_tokens: number
  active_users: number
  success_rate: number
  trends: {
    calls: number[]
    tokens: number[]
    dates: string[]
  }
}

export const dashboardApi = {
  getStats: () => request<DashboardStats>('/dashboard/stats'),
  getTrends: (days: number = 7) => request<DashboardStats['trends']>(`/dashboard/trends?days=${days}`),
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

// Export all APIs
export default {
  dashboard: dashboardApi,
  models: modelsApi,
  tokens: tokensApi,
  users: usersApi,
  logs: logsApi,
  ccswitch: ccswitchApi,
}
