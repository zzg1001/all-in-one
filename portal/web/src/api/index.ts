// API Configuration and Services
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

  // 204 No Content 没有响应体
  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

// ============ Common Types ============

export interface InteractionOption {
  value: string
  label: string
}

export interface SkillInteraction {
  id: string
  type: 'input' | 'select' | 'multiselect' | 'confirm' | 'upload' | 'form'
  label: string
  description?: string
  required: boolean
  timing: 'before' | 'during'
  depends_on?: string
  options?: InteractionOption[]
}

// 技能输出配置
export interface OutputConfig {
  enabled: boolean  // 是否生成输出文件
  preferred_type?: string  // 优先文件类型: png, pdf, xlsx, docx, txt, json, html, md 等
  filename_template?: string  // 文件名模板，支持 {skill_name}, {timestamp}, {uuid}
  description?: string  // 输出说明
}

// ============ Skills API ============

export interface Skill {
  id: string  // UUID
  group_id: string  // 版本组ID
  name: string
  description: string | null
  icon: string | null
  tags: string[] | null
  folder_path: string | null  // 技能文件夹路径
  entry_script: string | null  // 入口脚本
  interactions: SkillInteraction[] | null
  output_config: OutputConfig | null  // 输出文件配置
  author: string | null
  version: string | null
  skill_md: string | null  // 技能 Markdown 文档
  status: 'active' | 'deprecated'  // 版本状态
  original_created_at: string  // 原始创建时间（用于排序）
  created_at: string
  updated_at: string
}

export interface SkillVersion {
  id: string
  version: string | null
  status: string
  created_at: string
}

export interface SkillCreate {
  name: string
  description?: string
  icon?: string
  tags?: string[]
  entry_script?: string
  interactions?: SkillInteraction[]
  output_config?: OutputConfig  // 输出文件配置
  author?: string
  version?: string
  code?: string  // 脚本代码，提供后自动创建文件夹
}

export interface SkillUpdate {
  name?: string
  description?: string
  icon?: string
  tags?: string[]
  entry_script?: string
  interactions?: SkillInteraction[]
  output_config?: OutputConfig  // 输出文件配置
  author?: string
  version?: string
  skill_md?: string  // 技能 Markdown 文档
  code?: string  // 更新脚本代码
  // 更新模式: overwrite=覆盖当前版本, new_version=创建新版本
  update_mode?: 'overwrite' | 'new_version'
}

export interface SkillUploadData {
  file: File  // ZIP 文件
  name: string
  description?: string
  icon?: string
  tags?: string[]
  entry_script?: string
  author?: string
  version?: string
}

export const skillsApi = {
  // Get all skills (with optional search and department filter)
  getAll: (options?: { search?: string; dept?: string }) => {
    const params = new URLSearchParams()
    if (options?.search) params.append('q', options.search)
    if (options?.dept) params.append('dept', options.dept)
    const queryString = params.toString()
    return request<Skill[]>(`/skills${queryString ? `?${queryString}` : ''}`)
  },

  // Get single skill
  getById: (id: string) => request<Skill>(`/skills/${id}`),

  // Get skill by name
  getByName: (name: string) => request<Skill>(`/skills/by-name/${encodeURIComponent(name)}`),

  // Create skill (without folder)
  create: (data: SkillCreate) =>
    request<Skill>('/skills', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Preview ZIP content before upload (with AI analysis)
  previewUpload: async (file: File): Promise<{
    name: string
    description: string
    icon: string
    tags: string[]
    author: string
    version: string
    entry_script: string | null
    files: string[]
    ai_analysis?: {
      description?: string
      capabilities?: string[]
      input_types?: string[]
      output_types?: string[]
      tags?: string[]
      icon?: string
      complexity?: string
      error?: string
    }
  }> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE_URL}/skills/upload/preview`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Preview failed' }))
      throw new Error(error.detail || `HTTP error! status: ${response.status}`)
    }

    return response.json()
  },

  // Upload skill (with folder ZIP)
  upload: async (data: SkillUploadData): Promise<Skill> => {
    const formData = new FormData()
    formData.append('file', data.file)
    formData.append('name', data.name)
    if (data.description) formData.append('description', data.description)
    if (data.icon) formData.append('icon', data.icon)
    if (data.tags) formData.append('tags', JSON.stringify(data.tags))
    if (data.entry_script) formData.append('entry_script', data.entry_script)
    if (data.author) formData.append('author', data.author)
    if (data.version) formData.append('version', data.version)

    const response = await fetch(`${API_BASE_URL}/skills/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
      throw new Error(error.detail || `HTTP error! status: ${response.status}`)
    }

    return response.json()
  },

  // Update skill info
  update: (id: string, data: SkillUpdate) =>
    request<Skill>(`/skills/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  // Update skill folder
  updateFolder: async (id: string, file: File): Promise<Skill> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE_URL}/skills/${id}/folder`, {
      method: 'PUT',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
      throw new Error(error.detail || `HTTP error! status: ${response.status}`)
    }

    return response.json()
  },

  // Delete skill
  delete: (id: string) =>
    request<void>(`/skills/${id}`, {
      method: 'DELETE',
    }),

  // Get skill files
  getFiles: (id: string) =>
    request<{ files: { name: string; path: string; size: number }[] }>(`/skills/${id}/files`),

  // Get skill file content
  getFileContent: (id: string, filePath: string) =>
    request<{ content: string | null; binary?: boolean; size?: number }>(`/skills/${id}/file/${filePath}`),

  // ============ 临时技能 API ============

  // Create temporary skill (for testing)
  createTemp: (data: SkillCreate) =>
    request<TempSkillResponse>('/skills/temp', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Get temporary skill
  getTemp: (tempId: string) =>
    request<TempSkillResponse>(`/skills/temp/${tempId}`),

  // Finalize temporary skill (move to permanent)
  finalizeTemp: (tempId: string) =>
    request<Skill>(`/skills/temp/${tempId}/finalize`, {
      method: 'POST',
    }),

  // Delete temporary skill
  deleteTemp: (tempId: string) =>
    request<void>(`/skills/temp/${tempId}`, {
      method: 'DELETE',
    }),

  // ============ 版本管理 API ============

  // Get all versions of a skill
  getVersions: (id: string) =>
    request<SkillVersion[]>(`/skills/${id}/versions`),

  // Rollback to a specific version
  rollback: (id: string, targetVersionId: string) =>
    request<Skill>(`/skills/${id}/rollback/${targetVersionId}`, {
      method: 'POST',
    }),
}

// Temporary skill response
export interface TempSkillResponse {
  temp_id: string
  name: string
  description: string | null
  icon: string | null
  tags: string[] | null
  folder_path: string
  entry_script: string | null
  is_temp?: boolean
}

// ============ Agent API ============

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

// 上下文项
export interface ContextItem {
  type: string
  name: string
  content: string
}

export interface ChatRequest {
  message: string
  history?: ChatMessage[]
  skill_ids?: string[]  // UUID array
  context?: ContextItem[]  // 上下文项列表
  agent_id?: string  // Agent ID for RAG data isolation
  enable_rag?: boolean  // Enable RAG retrieval (default: true)
}

export interface ChatResponse {
  message: string
  skill_suggestions?: any[]
}

export interface PlanRequest {
  user_input: string
  available_skills?: string[]
}

export interface SkillPlanItem {
  skill_id: string
  skill_name: string
  reason: string
  params?: Record<string, any>
}

export interface PlanResponse {
  plan: SkillPlanItem[]
  explanation: string
}

export interface ExecuteRequest {
  skill_id: string  // UUID
  script_name?: string
  params?: Record<string, any>
  agent_id?: string  // Agent ID for RAG data isolation
}

export interface OutputFile {
  name: string
  type: string
  url: string
  size?: string
}

export interface ExecuteResponse {
  success: boolean
  result?: any
  error?: string
  output?: string
  output_file?: OutputFile
}

export interface UploadResponse {
  success: boolean
  filename: string
  original_name: string
  path: string
  url: string
  size: number
  type: string
}

// ============ Analyze API Types ============

export interface AnalyzeRequest {
  file_paths: string[]
  context?: string
  skill_id?: string
  max_iterations?: number
}

export interface AnalyzeCodeResult {
  code: string
  success: boolean
  stdout: string
  stderr?: string
  generated_files?: Array<{
    path: string
    name: string
    url: string
    size: number
  }>
}

export interface AnalyzeResponse {
  success: boolean
  iterations: AnalyzeCodeResult[]
  final_report?: string
  generated_files?: Array<{
    path: string
    name: string
    url: string
    size: number
  }>
  error?: string
}

export interface AnalyzeStreamEvent {
  type: 'code' | 'result' | 'thinking' | 'error' | 'done'
  data: {
    // For 'code' event
    code?: string
    iteration?: number
    // For 'result' event
    success?: boolean
    stdout?: string
    stderr?: string
    generated_files?: Array<{ path: string; name: string; url: string; size: number }>
    // For 'thinking' event
    content?: string
    // For 'error' event
    error?: string
    // For 'done' event
    final_report?: string
    iterations?: number
  }
}

// ========== Claude Code 风格：步骤化技能执行 ==========

export interface SkillChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface SkillChatAction {
  type: 'write' | 'run' | 'generate'
  data: Record<string, any>
}

export interface SkillChatRequest {
  skill_id: string
  context: string
  conversation?: SkillChatMessage[]
  file_paths?: string[]
  user_choice?: 'execute' | 'skip' | null
  pending_actions?: SkillChatAction[]
  current_action_index?: number
  agent_id?: string  // Agent ID for RAG data isolation
}

export interface SkillChatEvent {
  type: 'content' | 'actions_planned' | 'action_pending' | 'action_executing' | 'action_result' | 'action_skipped' | 'all_actions_done' | 'done' | 'error'
  // For 'content' event - streaming text
  text?: string
  // For 'actions_planned' event
  actions?: SkillChatAction[]
  total?: number
  // For 'action_pending', 'action_executing', 'action_result', 'action_skipped' events
  index?: number
  action?: SkillChatAction
  // For 'action_result' event
  success?: boolean
  output?: string
  output_file?: {
    path: string
    type: string
    name: string
    url: string
    size: number
  }
  // For 'error' event
  message?: string
  // For 'done' event
  full_response?: string
}

// Claude Code 风格：系统级工具调用确认
export interface SkillExecuteInteractiveRequest {
  skill_id: string
  context: string
  file_paths?: string[]
  confirmed_step?: number  // -1 表示还没开始
  auto_confirm?: boolean   // 全部执行
  skip_current?: boolean   // 跳过当前步骤
}

export interface ExecutionStep {
  type: 'generate' | 'write' | 'run'
  name: string
  description: string
  command?: string
}

export interface SkillExecuteInteractiveEvent {
  type: 'step_start' | 'step_done' | 'step_error' | 'all_done' | 'error'
  // Common
  message?: string
  step?: ExecutionStep | string
  index?: number
  // For 'steps_planned'
  steps?: ExecutionStep[]
  total?: number
  // For 'step_confirm', 'step_executing', 'step_result'
  // index?: number  // 已在上面定义
  // step?: ExecutionStep  // 已在上面定义
  // For 'step_result'
  success?: boolean
  output?: string
  output_file?: {
    path: string
    type: string
    name: string
    url: string
    size: number
  }
}

export const agentApi = {
  // Chat (non-streaming)
  chat: (data: ChatRequest) =>
    request<ChatResponse>('/agent/chat', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Chat (streaming via SSE) - with RAG support
  chatStream: async function* (
    data: ChatRequest,
    signal?: AbortSignal
  ): AsyncGenerator<string> {
    const url = `${API_BASE_URL}/agent/chat/stream`
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': getUserId(),  // For RAG data retrieval
      },
      body: JSON.stringify({
        ...data,
        enable_rag: data.enable_rag !== false  // Default to true
      }),
      signal,
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No response body')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonData = line.slice(6)
            if (jsonData === '[DONE]') {
              return
            }
            try {
              const parsed = JSON.parse(jsonData)
              if (parsed.content) {
                yield parsed.content
              }
              if (parsed.error) {
                throw new Error(parsed.error)
              }
            } catch (e) {
              // Ignore parse errors for malformed chunks
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  },

  // Plan skills
  plan: (data: PlanRequest) =>
    request<PlanResponse>('/agent/plan', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Execute skill
  execute: (data: ExecuteRequest) =>
    request<ExecuteResponse>('/agent/execute', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Execute temporary skill (for testing)
  executeTemp: (data: ExecuteRequest) =>
    request<ExecuteResponse>('/agent/execute-temp', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Upload file for skill processing
  upload: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE_URL}/agent/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
      throw new Error(error.detail || `HTTP error! status: ${response.status}`)
    }

    return response.json()
  },

  // Preview file content (table, json, markdown, etc.)
  preview: async (filePath: string, maxRows: number = 100): Promise<FilePreviewResponse> => {
    // 移除开头的斜杠
    const cleanPath = filePath.startsWith('/') ? filePath.slice(1) : filePath
    const response = await fetch(`${API_BASE_URL}/agent/preview/${cleanPath}?max_rows=${maxRows}`)

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Preview failed' }))
      throw new Error(error.detail || `HTTP error! status: ${response.status}`)
    }

    return response.json()
  },

  // Analyze data (streaming via SSE) - iterative analysis with code execution
  analyzeStream: async function* (
    data: AnalyzeRequest,
    signal?: AbortSignal
  ): AsyncGenerator<AnalyzeStreamEvent> {
    const url = `${API_BASE_URL}/agent/analyze`
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
      signal,
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No response body')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEvent = 'message'
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            const jsonData = line.slice(6)
            try {
              const parsed = JSON.parse(jsonData)
              yield { type: currentEvent as AnalyzeStreamEvent['type'], data: parsed }
            } catch (e) {
              // Ignore parse errors for malformed chunks
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  },

  // Analyze data (sync) - wait for all iterations to complete
  analyzeSync: (data: AnalyzeRequest) =>
    request<AnalyzeResponse>('/agent/analyze/sync', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // ========== Claude Code 风格：步骤化技能执行 ==========

  // Skill chat (streaming via SSE) - Claude Code style interactive execution
  skillChatStream: async function* (
    data: SkillChatRequest,
    signal?: AbortSignal
  ): AsyncGenerator<SkillChatEvent> {
    const url = `${API_BASE_URL}/agent/skill-chat`
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
      signal,
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No response body')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonData = line.slice(6)
            try {
              const parsed = JSON.parse(jsonData)
              yield parsed as SkillChatEvent
            } catch (e) {
              // Ignore parse errors for malformed chunks
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  },

  // Claude Code 风格：系统级工具调用确认
  executeInteractive: async function* (
    data: SkillExecuteInteractiveRequest,
    signal?: AbortSignal
  ): AsyncGenerator<SkillExecuteInteractiveEvent> {
    const url = `${API_BASE_URL}/agent/execute-interactive`
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
      signal,
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No response body')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonData = line.slice(6)
            try {
              const parsed = JSON.parse(jsonData)
              yield parsed as SkillExecuteInteractiveEvent
            } catch (e) {
              // Ignore parse errors for malformed chunks
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  },
}

// ========== 真正的 Claude Code 风格：多轮 AI 交互 ==========

export interface ToolCall {
  tool: string  // write, bash, read
  params: Record<string, any>
  display_name?: string
  preview?: string
}

export interface AgentLoopMessage {
  role: 'user' | 'assistant' | 'tool_result'
  content: string
  tool_call?: ToolCall
  tool_result?: Record<string, any>
}

export interface AgentLoopRequest {
  skill_id: string
  context: string
  file_paths?: string[]
  conversation: AgentLoopMessage[]
  // 工具确认
  pending_tool_call?: ToolCall
  tool_confirmed?: boolean
  tool_rejected?: boolean
  user_edit?: string
}

export interface AgentLoopEvent {
  type: 'thinking' | 'message' | 'tool_call' | 'tool_executing' | 'tool_result' | 'done' | 'error'
  message?: string
  content?: string
  // For tool_call
  tool?: string
  params?: Record<string, any>
  display_name?: string
  preview?: string
  // For tool_result
  success?: boolean
  output?: string
  output_file?: {
    path: string
    type: string
    name: string
    url: string
    size: number
  }
}

export const agentLoopApi = {
  /**
   * 真正的 Claude Code 风格 Agent 循环
   * 多轮 AI 交互，每个工具调用都等待用户确认
   */
  loop: async function* (
    data: AgentLoopRequest,
    signal?: AbortSignal
  ): AsyncGenerator<AgentLoopEvent> {
    const url = `${API_BASE_URL}/agent/loop`
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
      signal,
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No response body')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonData = line.slice(6)
            try {
              const parsed = JSON.parse(jsonData)
              yield parsed as AgentLoopEvent
            } catch (e) {
              // Ignore parse errors
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  },
}

// File preview response types
export interface FilePreviewResponse {
  type: 'table' | 'json' | 'markdown' | 'html' | 'image' | 'code' | 'file'
  format: string
  file_name: string
  file_size: number
  // For table type
  columns?: string[]
  data?: string[][]
  total_rows?: number
  displayed_rows?: number
  // For json/markdown/html/code type
  content?: any
  // For image type
  url?: string
  // For file type
  download_url?: string
}

// ============ Workflows API ============

export interface WorkflowNode {
  id: string
  type: 'skill' | 'workflow'
  name: string
  icon: string
  description: string
  config?: Record<string, any>
  position: { x: number; y: number }
}

export interface WorkflowEdge {
  id: string
  from: string
  to: string
}

export interface Workflow {
  id: string
  name: string
  description: string | null
  icon: string | null
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  created_at: string
  updated_at: string
}

export interface WorkflowCreate {
  id: string
  name: string
  description?: string
  icon?: string
  nodes?: WorkflowNode[]
  edges?: WorkflowEdge[]
}

export interface WorkflowUpdate {
  name?: string
  description?: string
  icon?: string
  nodes?: WorkflowNode[]
  edges?: WorkflowEdge[]
}

export const workflowsApi = {
  // Get all workflows (with optional search)
  getAll: (search?: string) => {
    const params = search ? `?q=${encodeURIComponent(search)}` : ''
    return request<Workflow[]>(`/workflows${params}`)
  },

  // Get single workflow
  getById: (id: string) => request<Workflow>(`/workflows/${id}`),

  // Create workflow
  create: (data: WorkflowCreate) =>
    request<Workflow>('/workflows', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Update workflow
  update: (id: string, data: WorkflowUpdate) =>
    request<Workflow>(`/workflows/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  // Delete workflow
  delete: (id: string) =>
    request<void>(`/workflows/${id}`, {
      method: 'DELETE',
    }),
}

// ============ Favorites API ============

export interface FavoriteListResponse {
  skills: string[]  // 收藏的技能ID列表
  workflows: string[]  // 收藏的子流程ID列表
}

// 获取或生成用户ID（匿名用户使用本地存储的ID）
const getUserId = (): string => {
  const key = 'user-anonymous-id'
  let userId = localStorage.getItem(key)
  if (!userId) {
    userId = `anon-${Date.now()}-${Math.random().toString(36).slice(2)}`
    localStorage.setItem(key, userId)
  }
  return userId
}

export const favoritesApi = {
  // 获取收藏列表
  getAll: () =>
    request<FavoriteListResponse>('/favorites', {
      headers: { 'X-User-ID': getUserId() }
    }),

  // 切换收藏状态
  toggle: (itemType: 'skill' | 'workflow', itemId: string) =>
    request<{ favorited: boolean; item_id: string }>('/favorites/toggle', {
      method: 'POST',
      headers: { 'X-User-ID': getUserId() },
      body: JSON.stringify({ item_type: itemType, item_id: itemId })
    }),

  // 添加收藏
  add: (itemType: 'skill' | 'workflow', itemId: string) =>
    request<any>('/favorites', {
      method: 'POST',
      headers: { 'X-User-ID': getUserId() },
      body: JSON.stringify({ item_type: itemType, item_id: itemId })
    }),

  // 取消收藏
  remove: (itemType: 'skill' | 'workflow', itemId: string) =>
    request<any>('/favorites', {
      method: 'DELETE',
      headers: { 'X-User-ID': getUserId() },
      body: JSON.stringify({ item_type: itemType, item_id: itemId })
    }),
}

// ============ Executions API ============

export interface InteractionRequest {
  interaction_id: string
  skill_id?: string
  skill_name: string
  step_index: number
  type: string
  label: string
  description?: string
  required: boolean
  options?: InteractionOption[]
  context?: Record<string, any>
}

export interface CompletedStep {
  step_index: number
  skill_name: string
  icon?: string
  status: 'completed' | 'skipped'
  result?: any
  output?: string
}

export interface ExecutionStatusResponse {
  execution_id: string
  workflow_id: string
  workflow_name?: string
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed'
  current_step: number
  total_steps: number
  completed_steps: CompletedStep[]
  pending_interaction?: InteractionRequest
  error?: string
  created_at?: string
  updated_at?: string
}

export interface WorkflowStepInfo {
  step_index: number
  skill_name: string
  icon?: string
  interactions: SkillInteraction[]
}

export interface WorkflowPreCheck {
  workflow_id: string
  workflow_name: string
  total_steps: number
  steps: WorkflowStepInfo[]
  before_interactions: InteractionRequest[]
  has_during_interactions: boolean
}

export interface StartExecutionRequest {
  pre_inputs?: Record<string, any>
}

export interface InteractionResponseData {
  interaction_id: string
  value: any
}

export const executionsApi = {
  // 预检查工作流
  precheck: (workflowId: string) =>
    request<WorkflowPreCheck>(`/executions/workflow/${workflowId}/precheck`),

  // 启动工作流执行
  start: (workflowId: string, preInputs?: Record<string, any>) =>
    request<ExecutionStatusResponse>(`/executions/workflow/${workflowId}/start`, {
      method: 'POST',
      body: JSON.stringify({ pre_inputs: preInputs }),
    }),

  // 获取执行状态
  getStatus: (executionId: string) =>
    request<ExecutionStatusResponse>(`/executions/${executionId}`),

  // 提交交互响应
  submitInteraction: (executionId: string, response: InteractionResponseData) =>
    request<ExecutionStatusResponse>(`/executions/${executionId}/interact`, {
      method: 'POST',
      body: JSON.stringify(response),
    }),

  // 取消执行
  cancel: (executionId: string) =>
    request<{ message: string }>(`/executions/${executionId}/cancel`, {
      method: 'POST',
    }),

  // 列出执行记录
  list: (workflowId?: string, limit: number = 50) => {
    const params = new URLSearchParams()
    if (workflowId) params.append('workflow_id', workflowId)
    params.append('limit', limit.toString())
    return request<ExecutionStatusResponse[]>(`/executions?${params}`)
  },
}

// ============ Data Notes API ============

export interface DataNote {
  id: string
  user_id: string
  agent_id: string | null  // 关联的 Agent ID
  name: string
  description: string | null
  file_type: string  // 'folder' 表示文件夹
  file_url: string | null
  file_size?: string
  source_skill?: string
  is_favorited: boolean
  parent_id: string | null
  level: number
  item_count?: number  // 文件夹内项目数
  created_at?: string
  updated_at?: string
}

export interface DataNoteCreate {
  name: string
  description?: string
  file_type: string
  file_url?: string
  file_size?: string
  source_skill?: string
  parent_id?: string
  agent_id?: string  // 关联的 Agent ID
}

export interface DataNoteUpdate {
  name?: string
  description?: string
  is_favorited?: boolean
  parent_id?: string
}

export interface FolderCreate {
  name: string
  parent_id?: string
  item_ids: string[]
  agent_id?: string  // 关联的 Agent ID
}

export const dataNotesApi = {
  // 获取便签列表
  getAll: (options?: { search?: string; favoritedOnly?: boolean; parentId?: string | null; agentId?: string }) => {
    const params = new URLSearchParams()
    if (options?.search) params.append('q', options.search)
    if (options?.favoritedOnly) params.append('favorited_only', 'true')
    if (options?.parentId !== undefined) {
      params.append('parent_id', options.parentId || '')
    }
    if (options?.agentId) params.append('agent_id', options.agentId)
    const query = params.toString()
    return request<DataNote[]>(`/data-notes${query ? '?' + query : ''}`, {
      headers: { 'X-User-ID': getUserId() }
    })
  },

  // 获取单个便签
  getById: (id: string) =>
    request<DataNote>(`/data-notes/${id}`, {
      headers: { 'X-User-ID': getUserId() }
    }),

  // 创建便签
  create: (data: DataNoteCreate) =>
    request<DataNote>('/data-notes', {
      method: 'POST',
      headers: { 'X-User-ID': getUserId() },
      body: JSON.stringify(data),
    }),

  // 创建文件夹
  createFolder: (data: FolderCreate) =>
    request<DataNote>('/data-notes/folder', {
      method: 'POST',
      headers: { 'X-User-ID': getUserId() },
      body: JSON.stringify(data),
    }),

  // 移动到文件夹
  move: (id: string, targetFolderId: string | null) =>
    request<DataNote>(`/data-notes/${id}/move`, {
      method: 'POST',
      headers: { 'X-User-ID': getUserId() },
      body: JSON.stringify({ target_folder_id: targetFolderId }),
    }),

  // 更新便签
  update: (id: string, data: DataNoteUpdate) =>
    request<DataNote>(`/data-notes/${id}`, {
      method: 'PUT',
      headers: { 'X-User-ID': getUserId() },
      body: JSON.stringify(data),
    }),

  // 删除便签
  delete: (id: string) =>
    request<void>(`/data-notes/${id}`, {
      method: 'DELETE',
      headers: { 'X-User-ID': getUserId() },
    }),

  // 切换收藏状态
  toggleFavorite: (id: string) =>
    request<{ id: string; is_favorited: boolean }>(`/data-notes/${id}/toggle-favorite`, {
      method: 'POST',
      headers: { 'X-User-ID': getUserId() },
    }),

  // 下载文件夹为zip的URL
  getFolderZipUrl: (id: string) =>
    `${API_BASE_URL}/data-notes/${id}/download-zip?x_user_id=${getUserId()}`,

  // 获取文件夹内所有文件
  getFolderFiles: (id: string) =>
    request<{ id: string; name: string; file_type: string; file_url: string; file_size: string }[]>(
      `/data-notes/${id}/files`,
      { headers: { 'X-User-ID': getUserId() } }
    ),

  // 上传文件到 File Manage（独立存储，与输入框上传分开）
  upload: async (file: File, agentId?: string): Promise<{ url: string; name: string; size: number; agent_id?: string }> => {
    const formData = new FormData()
    formData.append('file', file)
    if (agentId) {
      formData.append('agent_id', agentId)
    }
    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
      throw new Error(error.detail || 'Upload failed')
    }
    return response.json()
  },
}

// ============ Chat Sessions API ============

export interface ChatSessionMessage {
  id: string
  session_id: string
  role: 'user' | 'agent'
  content: string
  metadata?: {
    skill_plan?: any[]
    pipeline_edges?: any[]
    attachments?: any[]
  }
  created_at?: string
}

export interface ChatSession {
  id: string
  user_id: string
  title: string | null
  message_count: number
  skill_names?: string[] | null  // 涉及的技能名称
  last_message_at: string | null
  created_at?: string
  updated_at?: string
}

export interface ChatSessionWithMessages extends ChatSession {
  messages: ChatSessionMessage[]
}

export interface ChatSessionListResponse {
  sessions: ChatSession[]
  total: number
}

export interface CreateMessageRequest {
  role: 'user' | 'agent'
  content: string
  metadata?: {
    skill_plan?: any[]
    pipeline_edges?: any[]
    attachments?: any[]
  }
  created_at?: string  // ISO 时间戳
}

export const chatSessionsApi = {
  // 获取会话列表
  list: (page: number = 1, pageSize: number = 20, q?: string) => {
    const params = new URLSearchParams()
    params.append('page', page.toString())
    params.append('page_size', pageSize.toString())
    if (q) params.append('q', q)
    return request<ChatSessionListResponse>(`/sessions?${params}`, {
      headers: { 'X-User-ID': getUserId() }
    })
  },

  // 创建新会话
  create: (title?: string) =>
    request<ChatSession>('/sessions', {
      method: 'POST',
      headers: { 'X-User-ID': getUserId() },
      body: JSON.stringify({ title }),
    }),

  // 获取会话详情（含消息）
  get: (id: string) =>
    request<ChatSessionWithMessages>(`/sessions/${id}`, {
      headers: { 'X-User-ID': getUserId() }
    }),

  // 更新会话（重命名）
  update: (id: string, title: string) =>
    request<ChatSession>(`/sessions/${id}`, {
      method: 'PUT',
      headers: { 'X-User-ID': getUserId() },
      body: JSON.stringify({ title }),
    }),

  // 删除会话
  delete: (id: string) =>
    request<{ message: string }>(`/sessions/${id}`, {
      method: 'DELETE',
      headers: { 'X-User-ID': getUserId() },
    }),

  // 添加消息
  addMessage: (sessionId: string, data: CreateMessageRequest) =>
    request<ChatSessionMessage>(`/sessions/${sessionId}/messages`, {
      method: 'POST',
      headers: { 'X-User-ID': getUserId() },
      body: JSON.stringify(data),
    }),

  // 获取消息列表
  getMessages: (sessionId: string, limit: number = 100) =>
    request<ChatSessionMessage[]>(`/sessions/${sessionId}/messages?limit=${limit}`, {
      headers: { 'X-User-ID': getUserId() }
    }),
}

// ============ Agents API (Agent 配置管理) ============

export interface MemoryConfig {
  enabled: boolean
  type: string
  max_history: number
}

export interface ReasoningConfig {
  enabled: boolean
  style: string
}

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
  memory: MemoryConfig
  reasoning: ReasoningConfig
  status: string
  author: string
  version: string
  usage_count: number
  created_at: string
  updated_at: string
}

export interface AgentCreate {
  name: string
  description?: string
  icon?: string
  category?: string
  system_prompt?: string
  model?: string
  temperature?: number
  max_tokens?: number
  tools?: string[]
  skills?: string[]
  memory?: Partial<MemoryConfig>
  reasoning?: Partial<ReasoningConfig>
}

export interface AgentUpdate extends Partial<AgentCreate> {
  status?: string
}

export interface AgentListResponse {
  agents: Agent[]
  total: number
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

  // 根据名称获取 Agent
  getByName: (name: string) => request<Agent>(`/agents/by-name/${encodeURIComponent(name)}`),

  // 创建 Agent
  create: (data: AgentCreate) =>
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

  // 发布 Agent
  publish: (id: string) =>
    request<{ status: string; message: string }>(`/agents/${id}/publish`, {
      method: 'POST',
    }),

  // 弃用 Agent
  deprecate: (id: string) =>
    request<{ status: string; message: string }>(`/agents/${id}/deprecate`, {
      method: 'POST',
    }),

  // AI 生成提示词
  generatePrompt: (name: string, description: string, category?: string) =>
    request<{ status: string; prompt: string }>('/agents/generate/prompt', {
      method: 'POST',
      body: JSON.stringify({ name, description, category }),
    }),

  // AI 推荐工具
  recommendTools: (description: string, category?: string) =>
    request<{ status: string; tools: string[] }>('/agents/generate/tools', {
      method: 'POST',
      body: JSON.stringify({ description, category }),
    }),

  // AI 生成描述
  generateDescription: (name: string) =>
    request<{ status: string; description: string }>(`/agents/generate/description?name=${encodeURIComponent(name)}`, {
      method: 'POST',
    }),
}

// ============ Modules API (模块管理) ============

export interface ModuleDefinition {
  type: string
  name: string
  description: string
  category: 'core' | 'multi'
  icon: string
  color: string
  config_schema?: Record<string, any>
  default_config: Record<string, any>
}

export interface ModuleStatusResponse {
  module_type: string
  status: string
  enabled: boolean
  config: Record<string, any>
}

export interface ModuleConfigUpdate {
  enabled?: boolean
  settings?: Record<string, any>
}

export interface ModuleMetricsResponse {
  module_type: string
  status: string
  total_calls: number
  success_count: number
  error_count: number
  avg_latency_ms: number
  max_latency_ms: number
  last_activity: string | null
  started_at: string | null
  extra: Record<string, any>
}

export interface AgentModulesResponse {
  agent_id: string
  modules: Record<string, ModuleStatusResponse>
}

export const modulesApi = {
  // 获取所有模块定义
  getAll: () => request<ModuleDefinition[]>('/modules'),

  // 获取核心模块定义
  getCoreModules: () => request<ModuleDefinition[]>('/modules/core'),

  // 获取多 Agent 模块定义
  getMultiModules: () => request<ModuleDefinition[]>('/modules/multi'),

  // 获取单个模块定义
  getById: (moduleType: string) => request<ModuleDefinition>(`/modules/${moduleType}`),

  // 获取模块配置 Schema
  getConfigSchema: (moduleType: string) => request<any>(`/modules/${moduleType}/schema`),

  // 获取 Agent 的所有模块配置
  getAgentModules: (agentId: string) =>
    request<AgentModulesResponse>(`/modules/agents/${agentId}`),

  // 获取 Agent 的单个模块配置
  getAgentModule: (agentId: string, moduleType: string) =>
    request<ModuleStatusResponse>(`/modules/agents/${agentId}/${moduleType}`),

  // 更新 Agent 的模块配置
  updateAgentModule: (agentId: string, moduleType: string, data: ModuleConfigUpdate) =>
    request<ModuleStatusResponse>(`/modules/agents/${agentId}/${moduleType}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  // 获取模块运行指标
  getAgentModuleMetrics: (agentId: string, moduleType: string) =>
    request<ModuleMetricsResponse>(`/modules/agents/${agentId}/${moduleType}/metrics`),

  // 启用模块
  enableModule: (agentId: string, moduleType: string) =>
    request<{ status: string; message: string }>(`/modules/agents/${agentId}/${moduleType}/enable`, {
      method: 'POST',
    }),

  // 禁用模块
  disableModule: (agentId: string, moduleType: string) =>
    request<{ status: string; message: string }>(`/modules/agents/${agentId}/${moduleType}/disable`, {
      method: 'POST',
    }),

  // 重置模块配置
  resetModule: (agentId: string, moduleType: string) =>
    request<{ status: string; message: string }>(`/modules/agents/${agentId}/${moduleType}/reset`, {
      method: 'POST',
    }),
}

// Export all APIs
export default {
  skills: skillsApi,
  agent: agentApi,
  agents: agentsApi,
  workflows: workflowsApi,
  executions: executionsApi,
  favorites: favoritesApi,
  dataNotes: dataNotesApi,
  chatSessions: chatSessionsApi,
  modules: modulesApi,
}
