import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

// 上下文项类型
export type ContextType =
  | 'file'           // 上传的文件
  | 'data-note'      // 数据便签引用
  | 'skill-output'   // 技能执行结果
  | 'skill-execution'// 技能执行记录（轻量摘要）
  | 'url'            // 网页链接
  | 'text-snippet'   // 文本片段
  | 'conversation'   // 历史对话片段

// 技能执行记录
export interface SkillExecutionRecord {
  skillName: string
  status: 'success' | 'error'
  outputFile?: { name: string; type: string; size?: string }
  errorMessage?: string
  timestamp: Date
}

export interface ContextItem {
  id: string
  type: ContextType
  name: string           // 显示名称
  content: string        // 实际内容
  tokenCount: number     // token 估算
  createdAt: Date
  source?: string        // 来源标识
  metadata?: {
    fileType?: string
    filePath?: string
    skillName?: string
    url?: string
    messageIds?: number[]
  }
}

// API 请求格式
export interface ApiContextItem {
  type: ContextType
  name: string
  content: string
}

export const useContextStore = defineStore('context', () => {
  // State
  const items = ref<ContextItem[]>([])
  const maxTokens = ref(100000)
  const isExpanded = ref(false)
  const skillExecutions = ref<SkillExecutionRecord[]>([])

  // Getters
  const totalTokens = computed(() =>
    items.value.reduce((sum, item) => sum + item.tokenCount, 0)
  )

  const itemsByType = computed(() => (type: ContextType) =>
    items.value.filter(item => item.type === type)
  )

  const isOverLimit = computed(() =>
    totalTokens.value > maxTokens.value
  )

  const itemCount = computed(() => items.value.length)

  const hasItems = computed(() => items.value.length > 0)

  // 按类型分组统计
  const countByType = computed(() => {
    const counts: Partial<Record<ContextType, number>> = {}
    items.value.forEach(item => {
      counts[item.type] = (counts[item.type] || 0) + 1
    })
    return counts
  })

  // 序列化为 API 请求格式
  const toApiContext = computed((): ApiContextItem[] =>
    items.value.map(item => ({
      type: item.type,
      name: item.name,
      content: item.content
    }))
  )

  // Actions
  function estimateTokens(text: string): number {
    // 简单估算: 中文约 1.5 字符/token，英文约 4 字符/token
    // 取平均值约 2 字符/token
    return Math.ceil(text.length / 2)
  }

  function addItem(item: Omit<ContextItem, 'id' | 'createdAt' | 'tokenCount'> & { tokenCount?: number }) {
    // 自动去重（同类型同名）
    const exists = items.value.find(i =>
      i.type === item.type && i.name === item.name
    )
    if (exists) return exists.id

    const newItem: ContextItem = {
      ...item,
      id: crypto.randomUUID(),
      createdAt: new Date(),
      tokenCount: item.tokenCount ?? estimateTokens(item.content)
    }

    items.value.push(newItem)
    return newItem.id
  }

  function removeItem(id: string) {
    items.value = items.value.filter(i => i.id !== id)
  }

  function clearAll() {
    items.value = []
    skillExecutions.value = []
  }

  function clearByType(type: ContextType) {
    items.value = items.value.filter(i => i.type !== type)
  }

  // 添加文件上下文
  function addFile(name: string, content: string, filePath?: string, fileType?: string) {
    return addItem({
      type: 'file',
      name,
      content,
      source: 'upload',
      metadata: { filePath, fileType }
    })
  }

  // 添加数据便签上下文
  function addDataNote(name: string, content: string, filePath?: string) {
    return addItem({
      type: 'data-note',
      name,
      content,
      source: 'data-notes',
      metadata: { filePath }
    })
  }

  // 添加技能输出上下文（完整输出）
  function addSkillOutput(skillName: string, output: string) {
    // 获取当前技能执行序号
    const execIndex = skillExecutions.value.length
    return addItem({
      type: 'skill-output',
      name: `[${execIndex}] ${skillName}`,
      content: `[技能: ${skillName}]\n${output}`,
      source: 'skill-execution',
      metadata: { skillName }
    })
  }

  // 记录技能执行（轻量摘要）
  function recordSkillExecution(
    skillName: string,
    status: 'success' | 'error',
    options?: {
      outputFile?: { name: string; type: string; size?: string }
      errorMessage?: string
      output?: string  // 执行输出内容
    }
  ) {
    const record: SkillExecutionRecord = {
      skillName,
      status,
      outputFile: options?.outputFile,
      errorMessage: options?.errorMessage,
      timestamp: new Date()
    }
    skillExecutions.value.push(record)

    // 如果有输出内容，添加到上下文
    if (status === 'success' && options?.output) {
      // 截断过长的输出（最多 2000 字符）
      const truncatedOutput = options.output.length > 2000
        ? options.output.slice(0, 2000) + '\n...(输出已截断)'
        : options.output
      addSkillOutput(skillName, truncatedOutput)
    }

    // 同步更新上下文项（作为摘要）
    updateExecutionSummary()
  }

  // 更新执行摘要到上下文
  function updateExecutionSummary() {
    // 移除旧的执行摘要
    items.value = items.value.filter(i => i.type !== 'skill-execution')

    if (skillExecutions.value.length === 0) return

    // 生成摘要内容
    const summary = skillExecutions.value.map((exec, idx) => {
      const status = exec.status === 'success' ? '✓' : '✗'
      let line = `${idx + 1}. ${exec.skillName} ${status}`
      if (exec.outputFile) {
        line += ` → 输出: ${exec.outputFile.name}`
        if (exec.outputFile.size) line += ` (${exec.outputFile.size})`
      }
      if (exec.errorMessage) {
        line += ` → 错误: ${exec.errorMessage}`
      }
      return line
    }).join('\n')

    addItem({
      type: 'skill-execution',
      name: '技能执行记录',
      content: `[本次会话技能执行记录]\n${summary}`,
      source: 'auto'
    })
  }

  // 清空执行记录
  function clearExecutions() {
    skillExecutions.value = []
    items.value = items.value.filter(i => i.type !== 'skill-execution')
  }

  // 获取执行记录
  const executionRecords = computed(() => skillExecutions.value)

  // 添加 URL 上下文
  function addUrl(url: string, content: string, title?: string) {
    return addItem({
      type: 'url',
      name: title || url,
      content,
      source: 'web',
      metadata: { url }
    })
  }

  // 添加文本片段
  function addTextSnippet(name: string, content: string) {
    return addItem({
      type: 'text-snippet',
      name,
      content,
      source: 'manual'
    })
  }

  // 添加对话片段
  function addConversation(name: string, content: string, messageIds: number[]) {
    return addItem({
      type: 'conversation',
      name,
      content,
      source: 'conversation',
      metadata: { messageIds }
    })
  }

  // 切换面板展开状态
  function toggleExpanded() {
    isExpanded.value = !isExpanded.value
  }

  // 更新上下文内容
  function updateItem(id: string, updates: Partial<Pick<ContextItem, 'name' | 'content'>>) {
    const item = items.value.find(i => i.id === id)
    if (item) {
      if (updates.name) item.name = updates.name
      if (updates.content) {
        item.content = updates.content
        item.tokenCount = estimateTokens(updates.content)
      }
    }
  }

  // 获取单个上下文项
  function getItem(id: string) {
    return items.value.find(i => i.id === id)
  }

  return {
    // State
    items,
    maxTokens,
    isExpanded,
    skillExecutions,

    // Getters
    totalTokens,
    itemsByType,
    isOverLimit,
    itemCount,
    hasItems,
    countByType,
    toApiContext,
    executionRecords,

    // Actions
    estimateTokens,
    addItem,
    removeItem,
    clearAll,
    clearByType,
    addFile,
    addDataNote,
    addSkillOutput,
    recordSkillExecution,
    clearExecutions,
    addUrl,
    addTextSnippet,
    addConversation,
    toggleExpanded,
    updateItem,
    getItem
  }
})
