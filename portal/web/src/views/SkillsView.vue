<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import SkillCard from '@/components/skills/SkillCard.vue'
import AddSkillModal from '@/components/skills/AddSkillModal.vue'
import AgentChat from '@/components/agent/AgentChat.vue'
import WorkflowBuilder from '@/components/workflow/WorkflowBuilder.vue'
import WorkflowRunner from '@/components/workflow/WorkflowRunner.vue'
import { skillsApi, workflowsApi, agentApi, type Skill as ApiSkill, type Workflow as ApiWorkflow, type ExecutionStatusResponse } from '@/api'

// Workflow 类型定义
interface WorkflowNode {
  id: string
  type: 'skill' | 'workflow'
  name: string
  icon: string
  description: string
  config?: Record<string, any>
  position: { x: number; y: number }
}

interface WorkflowEdge {
  id: string
  from: string
  to: string
}

interface Workflow {
  id: string
  name: string
  description: string
  icon: string
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  createdAt: string
  updatedAt: string
}

const route = useRoute()
const activeTab = ref<'skills' | 'agent' | 'workflows' | 'agents' | 'monitor'>('agent')

// 从首页跳转时隐藏侧边栏
const hideSidebar = computed(() => route.query.from === 'home')


// 根据 URL 参数初始化 tab
const initTabFromQuery = () => {
  const tab = route.query.tab as string
  if (tab === 'skills' || tab === 'agent' || tab === 'workflows') {
    activeTab.value = tab
  }
}
initTabFromQuery()

const showModal = ref(false)
const modalMode = ref<'create' | 'upload'>('create')
const pendingSkillName = ref<string | null>(null)
const agentChatRef = ref<InstanceType<typeof AgentChat> | null>(null)
const workflowBuilderRef = ref<InstanceType<typeof WorkflowBuilder> | null>(null)
const gridWrapperRef = ref<HTMLElement | null>(null)

// 是否可以向上滚动
const canScrollUp = ref(false)

// 检查滚动状态
const checkScrollPosition = () => {
  const wrapper = gridWrapperRef.value
  if (!wrapper) return
  canScrollUp.value = wrapper.scrollTop > 10
}

// 获取滚动单位
const getScrollUnit = () => {
  const wrapper = gridWrapperRef.value
  if (!wrapper) return { rowHeight: 0, gap: 8 }
  const firstCell = wrapper.querySelector('.grid-cell') as HTMLElement
  if (!firstCell) return { rowHeight: 120, gap: 8 }
  return { rowHeight: firstCell.offsetHeight, gap: 8 }
}

// 单击：向下滚动一行
const scrollDownOne = () => {
  totalSlots.value += COLS
  nextTick(() => {
    const wrapper = gridWrapperRef.value
    if (!wrapper) return
    const { rowHeight, gap } = getScrollUnit()
    wrapper.scrollBy({ top: rowHeight + gap, behavior: 'smooth' })
  })
}

// 双击：向下滚动一屏（4行）
const scrollDownPage = () => {
  totalSlots.value += COLS * 4
  nextTick(() => {
    const wrapper = gridWrapperRef.value
    if (!wrapper) return
    const { rowHeight, gap } = getScrollUnit()
    wrapper.scrollBy({ top: (rowHeight + gap) * 4, behavior: 'smooth' })
  })
}

// 单击：向上滚动一行
const scrollUpOne = () => {
  const wrapper = gridWrapperRef.value
  if (!wrapper) return
  const { rowHeight, gap } = getScrollUnit()
  wrapper.scrollBy({ top: -(rowHeight + gap), behavior: 'smooth' })
}

// 双击：向上滚动一屏（4行）
const scrollUpPage = () => {
  const wrapper = gridWrapperRef.value
  if (!wrapper) return
  const { rowHeight, gap } = getScrollUnit()
  wrapper.scrollBy({ top: -(rowHeight + gap) * 4, behavior: 'smooth' })
}

// 监听标签切换，关闭浮动元素
watch(activeTab, () => {
  workflowBuilderRef.value?.closeAllPopups()
})

// 工作流运行对话框状态
const showRunWorkflowDialog = ref(false)
const pendingRunWorkflow = ref<Workflow | null>(null)
const workflowRunContext = ref('')
const workflowRunFiles = ref<{ id: string; name: string; type: string; size: number; file: File; url?: string; uploading?: boolean; serverPath?: string }[]>([])
const workflowFileInputRef = ref<HTMLInputElement | null>(null)
const isWorkflowDragging = ref(false)

// 总格子数（5列x4行=20个）
const COLS = 5
const totalSlots = ref(20)  // 可动态增加

// Loading state
const isLoadingSkills = ref(false)
const skillsError = ref<string | null>(null)

// 技能交互配置
interface SkillInteraction {
  id: string
  type: string
  label: string
}

// 输出配置
interface OutputConfig {
  enabled: boolean
  preferred_type?: string
}

// Skill 类型定义
interface Skill {
  id: string  // UUID
  group_id?: string  // 版本组ID
  name: string
  description: string
  tags: string[]
  icon: string
  author: string
  version: string
  status?: string  // active/deprecated
  original_created_at?: string  // 原始创建时间
  created_at?: string
  folder_path?: string
  entry_script?: string
  interactions?: SkillInteraction[]
  output_config?: OutputConfig
}

// Skills数据（从API获取）
const skills = ref<Skill[]>([])

// 加载技能数据
const loadSkills = async () => {
  isLoadingSkills.value = true
  skillsError.value = null
  try {
    const apiSkills = await skillsApi.getAll()
    // 按原始创建时间升序排序（最早的在前面，版本更新不影响位置）
    const sortedSkills = [...apiSkills].sort((a, b) => {
      const timeA = new Date(a.original_created_at || a.created_at).getTime()
      const timeB = new Date(b.original_created_at || b.created_at).getTime()
      return timeA - timeB
    })
    skills.value = sortedSkills.map(s => ({
      id: s.id,
      group_id: s.group_id,
      name: s.name,
      description: s.description || '',
      tags: s.tags || [],
      icon: s.icon || '⚡',
      author: s.author || 'unknown',
      version: s.version || '1.0.0',
      status: s.status || 'active',
      original_created_at: s.original_created_at,
      created_at: s.created_at,
      interactions: s.interactions || [],
      output_config: s.output_config || null
    }))
  } catch (error: any) {
    console.error('Failed to load skills:', error)
    skillsError.value = error.message || '加载技能失败'
    // 使用默认数据作为 fallback
    skills.value = [
      { id: 'fallback-1', name: 'expert-feishu-doc', description: 'Expert-level documentation generation for Feishu/Lark platform.', tags: ['Expert', 'Public'], icon: '📄', author: 'system', version: '1.2.0', created_at: new Date().toISOString() },
      { id: 'fallback-2', name: 'data-visualizer', description: 'Data visualization and chart generation with real-time updates.', tags: ['Expert', 'Public'], icon: '📊', author: 'community', version: '2.0.1', created_at: new Date().toISOString() },
      { id: 'fallback-3', name: 'code-reviewer', description: 'Advanced code review and optimization for 20+ languages.', tags: ['Expert', 'Public'], icon: '🔍', author: 'system', version: '1.5.3', created_at: new Date().toISOString() },
    ]
  } finally {
    isLoadingSkills.value = false
  }
}

// Workflows 数据（从 API 加载）
const workflows = ref<Workflow[]>([])
const isLoadingWorkflows = ref(false)

// ============ Agents 数据 ============
const sampleAgents = ref([
  { id: '1', name: '智能写作助手', description: '帮助撰写各类文档、邮件、报告', icon: '✍️', status: 'active', capabilities: ['文档撰写', '内容优化', '格式转换'] },
  { id: '2', name: '数据分析专家', description: '分析 Excel、CSV 数据，生成图表', icon: '📊', status: 'active', capabilities: ['数据清洗', '统计分析', '图表生成'] },
  { id: '3', name: '代码生成器', description: '根据需求描述生成代码', icon: '💻', status: 'active', capabilities: ['代码生成', '代码审查', '单元测试'] },
  { id: '4', name: 'PDF 处理专家', description: '提取 PDF 内容、转换格式', icon: '📄', status: 'draft', capabilities: ['PDF提取', '格式转换'] },
])

const openAgentStudio = () => {
  // TODO: 打开 Agent 编辑器
  alert('Agent Studio 开发中...')
}

const useAgent = (agent: any) => {
  activeTab.value = 'agent'
  // TODO: 设置当前使用的 Agent
}

const editAgent = (agent: any) => {
  // TODO: 编辑 Agent
  alert(`编辑 Agent: ${agent.name}`)
}

// ============ Monitor 数据 ============
const monitorStats = ref({
  totalExecutions: 1247,
  successRate: 94.5,
  avgDuration: 3.2
})

const executionLogs = ref([
  { id: '1', icon: '📊', name: '数据分析专家', task: 'Excel 数据转换', status: 'success', statusText: '成功', time: '10:30' },
  { id: '2', icon: '💻', name: '代码生成器', task: '生成 Python 脚本', status: 'running', statusText: '运行中', time: '10:32' },
  { id: '3', icon: '✍️', name: '智能写作助手', task: '撰写产品文档', status: 'success', statusText: '成功', time: '10:25' },
  { id: '4', icon: '📄', name: 'PDF 处理专家', task: '提取 PDF 表格', status: 'failed', statusText: '失败', time: '10:20' },
])

// Workflow tooltip 状态
const wfTooltip = ref<{
  show: boolean
  workflow: Workflow | null
  style: { top: string; left: string }
}>({
  show: false,
  workflow: null,
  style: { top: '0px', left: '0px' }
})

const handleWfMouseMove = (e: MouseEvent, workflow: Workflow) => {
  const tooltipWidth = 160
  const tooltipHeight = 100

  let left = e.clientX + 12
  let top = e.clientY + 12

  if (left + tooltipWidth > window.innerWidth - 10) {
    left = e.clientX - tooltipWidth - 8
  }
  if (top + tooltipHeight > window.innerHeight - 10) {
    top = e.clientY - tooltipHeight - 8
  }

  wfTooltip.value = {
    show: true,
    workflow,
    style: { top: `${top}px`, left: `${left}px` }
  }
}

const handleWfMouseLeave = () => {
  wfTooltip.value.show = false
}

// 加载工作流数据
const loadWorkflows = async () => {
  isLoadingWorkflows.value = true
  try {
    const apiWorkflows = await workflowsApi.getAll()
    // 调试：检查API返回的节点数据
    apiWorkflows.forEach(w => {
      const dataNodes = (w.nodes || []).filter((n: any) => n.type === 'data' || n.dataNote)
      if (dataNodes.length > 0) {
        console.log(`[loadWorkflows] Workflow "${w.name}" data nodes from API:`, dataNodes.map((n: any) => ({
          id: n.id,
          type: n.type,
          name: n.name,
          hasDataNote: !!n.dataNote,
          file_url: n.dataNote?.file_url
        })))
      }
    })
    workflows.value = apiWorkflows.map(w => ({
      id: w.id,
      name: w.name,
      description: w.description || '',
      icon: w.icon || '🔄',
      nodes: w.nodes || [],
      edges: w.edges || [],
      createdAt: w.created_at,
      updatedAt: w.updated_at
    }))
  } catch (error: any) {
    console.error('Failed to load workflows:', error)
    // 加载失败时使用空数组
    workflows.value = []
  } finally {
    isLoadingWorkflows.value = false
  }
}

// 获取workflow的输入输出信息
const getWorkflowIO = (workflow: Workflow) => {
  let totalInputs = 0
  let outputType: string | null = null

  // 遍历nodes，从skills中查找对应的skill信息
  for (const node of workflow.nodes) {
    const skill = skills.value.find(s => s.name === node.name)
    if (skill) {
      // 累计输入数量
      totalInputs += skill.interactions?.length || 0
      // 获取输出类型（取最后一个有输出配置的节点）
      if (skill.output_config?.preferred_type) {
        outputType = skill.output_config.preferred_type
      }
    }
  }

  // 输出类型映射
  const typeMap: Record<string, string> = {
    'html': '网页',
    'pdf': 'PDF',
    'xlsx': 'Excel',
    'docx': 'Word',
    'png': '图片',
    'json': 'JSON',
    'txt': '文本',
    'md': 'Markdown'
  }

  return {
    inputCount: totalInputs,
    outputType: outputType ? (typeMap[outputType] || outputType) : null
  }
}

// 是否显示 WorkflowBuilder
const showWorkflowBuilder = ref(false)
const editingWorkflow = ref<Workflow | null>(null)

// 工作流运行器
const showWorkflowRunner = ref(false)
const runningWorkflowId = ref<string | null>(null)
const runningWorkflowName = ref<string | null>(null)

// Toast 提示
const showToast = ref(false)
const toastMessage = ref('')
const showToastMessage = (message: string) => {
  toastMessage.value = message
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 3000)
}

// 打开创建新工作流
const openCreateWorkflow = () => {
  editingWorkflow.value = null
  showWorkflowBuilder.value = true
}

// 编辑已有工作流
const openEditWorkflow = (workflow: Workflow) => {
  // 关闭浮框
  wfTooltip.value.show = false
  // 深拷贝以避免直接修改原数据
  editingWorkflow.value = JSON.parse(JSON.stringify(workflow))
  nextTick(() => {
    showWorkflowBuilder.value = true
  })
}

// 保存工作流
const handleSaveWorkflow = async (workflow: Workflow) => {
  try {
    if (editingWorkflow.value) {
      // 更新已有的
      const updated = await workflowsApi.update(editingWorkflow.value.id, {
        name: workflow.name,
        description: workflow.description,
        icon: workflow.icon,
        nodes: workflow.nodes,
        edges: workflow.edges
      })
      const idx = workflows.value.findIndex(w => w.id === editingWorkflow.value!.id)
      if (idx !== -1) {
        workflows.value[idx] = {
          ...workflow,
          id: editingWorkflow.value.id,
          updatedAt: updated.updated_at
        }
      }
    } else {
      // 添加新的
      const created = await workflowsApi.create({
        id: workflow.id,
        name: workflow.name,
        description: workflow.description,
        icon: workflow.icon,
        nodes: workflow.nodes,
        edges: workflow.edges
      })
      workflows.value.push({
        ...workflow,
        id: created.id,
        createdAt: created.created_at,
        updatedAt: created.updated_at
      })
    }
    showToastMessage('工作流保存成功')
  } catch (error: any) {
    console.error('Failed to save workflow:', error)
    showToastMessage('保存失败: ' + (error.message || '未知错误'))
  }
  showWorkflowBuilder.value = false
  editingWorkflow.value = null
}

// 删除工作流
const deleteWorkflow = async (workflowId: string) => {
  wfTooltip.value.show = false
  try {
    await workflowsApi.delete(workflowId)
    workflows.value = workflows.value.filter(w => w.id !== workflowId)
    showToastMessage('工作流已删除')
  } catch (error: any) {
    console.error('Failed to delete workflow:', error)
    // 即使 API 失败也从本地删除
    workflows.value = workflows.value.filter(w => w.id !== workflowId)
  }
}

// 运行工作流 - 打开对话框
const runWorkflow = (workflow: Workflow) => {
  wfTooltip.value.show = false
  pendingRunWorkflow.value = workflow
  workflowRunContext.value = ''
  workflowRunFiles.value = []
  showRunWorkflowDialog.value = true
}

// 确认运行工作流
const confirmRunWorkflow = async () => {
  if (!pendingRunWorkflow.value) return

  // 检查是否有文件还在上传中
  const uploadingFiles = workflowRunFiles.value.filter(f => f.uploading)
  if (uploadingFiles.length > 0) {
    alert('请等待文件上传完成')
    return
  }

  const workflow = pendingRunWorkflow.value
  const context = workflowRunContext.value.trim()

  // 获取文件路径（在关闭对话框前获取）
  const filePaths = workflowRunFiles.value
    .filter(f => f.serverPath)
    .map(f => f.serverPath!)

  console.log('[Workflow Run] Files:', workflowRunFiles.value)
  console.log('[Workflow Run] File paths:', filePaths)

  // 调试：打印 workflow 节点详情
  console.log('[Workflow Run] Workflow nodes:', workflow.nodes)
  const dataNodesDebug = workflow.nodes.filter((n: any) => n.type === 'data' || n.dataNote)
  if (dataNodesDebug.length > 0) {
    console.log('[Workflow Run] Data nodes in workflow:', dataNodesDebug.map((n: any) => ({
      id: n.id,
      name: n.name,
      type: n.type,
      hasDataNote: !!n.dataNote,
      file_url: n.dataNote?.file_url
    })))
  }

  // 关闭对话框
  showRunWorkflowDialog.value = false

  // 切换到 Agent tab
  activeTab.value = 'agent'

  // 等待 DOM 更新后调用 AgentChat 的 runWorkflow
  nextTick(() => {

    agentChatRef.value?.runWorkflow({
      id: workflow.id,
      name: workflow.name,
      description: context || workflow.description,
      icon: workflow.icon,
      nodes: workflow.nodes,
      edges: workflow.edges || [],
      // 标记从 SkillsView 传入，不需要再弹对话框
      fromSkillsView: true,
      userContext: context,
      filePaths
    })
  })

  // 清理状态
  pendingRunWorkflow.value = null
  workflowRunContext.value = ''
  workflowRunFiles.value = []
}

// 取消运行工作流
const cancelRunWorkflow = () => {
  showRunWorkflowDialog.value = false
  pendingRunWorkflow.value = null
  workflowRunContext.value = ''
  workflowRunFiles.value = []
}

// 工作流对话框 - 文件上传处理
const handleWorkflowFileSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files) {
    addWorkflowFiles(Array.from(input.files))
  }
  input.value = ''
}

const addWorkflowFiles = async (files: File[]) => {
  const newFiles = files.map(file => ({
    id: `file-${Date.now()}-${Math.random().toString(36).slice(2)}`,
    name: file.name,
    type: file.type,
    size: file.size,
    file,
    url: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined,
    uploading: true,
    serverPath: undefined as string | undefined
  }))
  workflowRunFiles.value.push(...newFiles)

  // 上传文件
  for (const uploadedFile of newFiles) {
    try {
      const response = await agentApi.upload(uploadedFile.file)
      const idx = workflowRunFiles.value.findIndex(f => f.id === uploadedFile.id)
      if (idx !== -1) {
        workflowRunFiles.value[idx] = {
          ...workflowRunFiles.value[idx],
          uploading: false,
          serverPath: response.path
        }
      }
    } catch (error: any) {
      console.error('Upload failed:', error)
      const idx = workflowRunFiles.value.findIndex(f => f.id === uploadedFile.id)
      if (idx !== -1) {
        workflowRunFiles.value[idx] = {
          ...workflowRunFiles.value[idx],
          uploading: false
        }
      }
    }
  }
}

const removeWorkflowFile = (fileId: string) => {
  workflowRunFiles.value = workflowRunFiles.value.filter(f => f.id !== fileId)
}

const handleWorkflowDragOver = (e: DragEvent) => {
  e.preventDefault()
  isWorkflowDragging.value = true
}

const handleWorkflowDragLeave = () => {
  isWorkflowDragging.value = false
}

const handleWorkflowDrop = (e: DragEvent) => {
  e.preventDefault()
  isWorkflowDragging.value = false
  if (e.dataTransfer?.files) {
    addWorkflowFiles(Array.from(e.dataTransfer.files))
  }
}

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const getFileIcon = (type: string): string => {
  if (type.startsWith('image/')) return '🖼️'
  if (type.includes('pdf')) return '📄'
  if (type.includes('word') || type.includes('document')) return '📝'
  if (type.includes('excel') || type.includes('spreadsheet')) return '📊'
  if (type.includes('json')) return '📋'
  if (type.includes('text')) return '📃'
  return '📎'
}

// 关闭运行器
const closeWorkflowRunner = () => {
  showWorkflowRunner.value = false
  runningWorkflowId.value = null
  runningWorkflowName.value = null
}

// 运行完成
const handleWorkflowCompleted = (result: ExecutionStatusResponse) => {
  showToastMessage(`工作流「${runningWorkflowName.value}」执行完成`)
}

// 从 Agent 保存工作流
const handleSaveWorkflowFromAgent = async (workflowData: { name: string; description: string; nodes: any[]; edges: any[] }) => {
  const workflowId = `wf-${Date.now()}`
  try {
    const created = await workflowsApi.create({
      id: workflowId,
      name: workflowData.name,
      description: workflowData.description,
      icon: '💾',
      nodes: workflowData.nodes,
      edges: workflowData.edges
    })
    workflows.value.push({
      id: created.id,
      name: created.name,
      description: created.description || '',
      icon: created.icon || '💾',
      nodes: created.nodes || [],
      edges: created.edges || [],
      createdAt: created.created_at,
      updatedAt: created.updated_at
    })
  } catch (error: any) {
    console.error('Failed to save workflow from agent:', error)
    // 降级：仍然添加到本地
    workflows.value.push({
      id: workflowId,
      name: workflowData.name,
      description: workflowData.description,
      icon: '💾',
      nodes: workflowData.nodes,
      edges: workflowData.edges,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    })
  }

  // 显示保存成功提示
  showToastMessage(`工作流「${workflowData.name}」已保存`)
}

// 计算显示列表：skills在前，空位在后
const displayList = computed(() => {
  const list: (any | null)[] = [...skills.value]
  // 补齐空位到总数
  while (list.length < totalSlots.value) {
    list.push(null)
  }
  return list
})

// 空位数量
const emptyCount = computed(() => totalSlots.value - skills.value.length)

// 是否已满
const isFull = computed(() => skills.value.length >= totalSlots.value)

const openCreateModal = () => {
  modalMode.value = 'create'
  showModal.value = true
}

const openUploadModal = () => {
  modalMode.value = 'upload'
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  // 如果是从 Agent 来的但取消了，清除状态
  if (pendingSkillName.value) {
    pendingSkillName.value = null
  }
}

const handleSkillSubmit = async (skillData: any) => {
  // 先保存 pending 状态
  const isFromAgent = !!pendingSkillName.value
  const addedName = pendingSkillName.value || skillData.name || 'new-skill'

  // 如果 skillData 已经有 id，说明已经在 AddSkillModal 中通过 API 创建了
  // 直接添加到本地列表，不需要再次调用 API
  if (skillData.id) {
    skills.value.push({
      id: skillData.id,
      name: skillData.name,
      description: skillData.description || '',
      tags: skillData.tags || [],
      icon: skillData.icon || '⚡',
      author: skillData.author || 'user',
      version: skillData.version || '1.0.0',
      created_at: skillData.created_at || new Date().toISOString()
    })
  } else {
    // 没有 id，需要调用 API 创建
    try {
      // 调用 API 创建技能
      const newSkill = await skillsApi.create({
        name: skillData.name || addedName,
        description: skillData.description || '用户添加的技能',
        tags: skillData.tags || ['Custom'],
        icon: skillData.icon || '⚡',
        author: 'user',
        version: '1.0.0'
      })

      // 添加到本地列表
      skills.value.push({
        id: newSkill.id,
        name: newSkill.name,
        description: newSkill.description || '',
        tags: newSkill.tags || [],
        icon: newSkill.icon || '⚡',
        author: newSkill.author || 'user',
        version: newSkill.version || '1.0.0',
        created_at: newSkill.created_at
      })
    } catch (error: any) {
      console.error('Failed to create skill:', error)
      // 如果 API 失败，仍然添加到本地（降级处理）
      skills.value.push({
        id: `local-${Date.now()}`,
        name: skillData.name || addedName,
        description: skillData.description || '用户添加的技能',
        tags: skillData.tags || ['Custom'],
        icon: skillData.icon || '⚡',
        author: 'user',
        version: '1.0.0',
        created_at: new Date().toISOString()
      })
    }
  }

  // 如果是从 Agent 来的，不自动关闭弹窗（由 AddSkillModal 内部控制测试和返回流程）
  if (!isFromAgent) {
    pendingSkillName.value = null
    showModal.value = false
  }
  // 从 Agent 来的情况：弹窗保持打开，等待用户在对话中选择"返回继续执行"或"留在这里"
}

// 处理从 AddSkillModal 返回 Agent 的事件
const handleReturnToAgent = (skillName: string) => {
  showModal.value = false
  pendingSkillName.value = null
  loadSkills()  // 刷新技能列表
  activeTab.value = 'agent'
  // 等待 DOM 更新后调用 onSkillAdded 显示确认对话框
  nextTick(() => {
    agentChatRef.value?.onSkillAdded(skillName)
  })
}

const deleteSkill = async (index: number) => {
  const skill = skills.value[index]
  if (!skill) return

  try {
    // 调用 API 删除技能
    await skillsApi.delete(skill.id)
  } catch (error: any) {
    console.error('Failed to delete skill:', error)
    // 即使 API 失败也继续删除本地数据（降级处理）
  }

  // 从本地列表移除
  skills.value.splice(index, 1)
}

// 编辑技能（只有创建的可以编辑，上传的不可以）
const editingSkillData = ref<Skill | null>(null)
const showEditModal = ref(false)
const editMode = ref<'ai' | 'manual'>('ai')  // 默认 AI 模式
const editTab = ref<'basic' | 'content'>('basic')
const isLoadingSkillDetail = ref(false)
const editTagsString = ref('')  // 用于标签输入

// AI 编辑相关状态
interface EditMessage {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  generating?: boolean
}
const editMessages = ref<EditMessage[]>([])
const editInput = ref('')
const isEditAiThinking = ref(false)
const editWaitingConfirm = ref(false)
const editModifiedSkill = ref<Partial<Skill> | null>(null)

const editSkill = async (skill: Skill) => {
  // 上传的技能不可编辑
  if (skill.author === 'uploaded') {
    return
  }

  // 初始化状态
  editingSkillData.value = { ...skill }
  editTagsString.value = (skill.tags || []).join(', ')
  editMode.value = 'ai'  // 默认 AI 模式
  editTab.value = 'basic'
  editMessages.value = []
  editInput.value = ''
  editWaitingConfirm.value = false
  editModifiedSkill.value = null
  showEditModal.value = true

  // 异步加载完整数据（包括 skill_md）
  isLoadingSkillDetail.value = true
  try {
    const fullSkill = await skillsApi.getById(skill.id)
    if (editingSkillData.value && editingSkillData.value.id === skill.id) {
      editingSkillData.value.skill_md = fullSkill.skill_md || ''

      // AI 模式下，自动分析技能
      if (editMode.value === 'ai') {
        await analyzeSkillWithAI(fullSkill)
      }
    }
  } catch (error) {
    console.error('Failed to load skill detail:', error)
  } finally {
    isLoadingSkillDetail.value = false
  }
}

// AI 分析技能
const analyzeSkillWithAI = async (skill: any) => {
  isEditAiThinking.value = true

  // 添加系统消息
  const analysisMsg: EditMessage = {
    id: Date.now(),
    role: 'assistant',
    content: '',
    generating: true
  }
  editMessages.value.push(analysisMsg)

  const prompt = `请分析以下技能并简要说明它的功能，然后询问用户想要如何修改：

技能名称: ${skill.name}
描述: ${skill.description || '无'}
标签: ${(skill.tags || []).join(', ') || '无'}
技能内容:
\`\`\`
${skill.skill_md || '暂无内容'}
\`\`\`

请用简洁的语言概述这个技能的功能，然后友好地询问用户想要修改什么。`

  try {
    // 尝试流式调用
    const stream = agentApi.chatStream({
      message: prompt,
      history: []
    })

    for await (const chunk of stream) {
      const idx = editMessages.value.findIndex(m => m.id === analysisMsg.id)
      if (idx !== -1) {
        editMessages.value[idx].content += chunk
      }
    }

    // 完成生成
    const idx = editMessages.value.findIndex(m => m.id === analysisMsg.id)
    if (idx !== -1) {
      editMessages.value[idx].generating = false
    }
  } catch (streamError) {
    console.warn('Stream failed, trying non-stream:', streamError)

    // 流式失败，尝试非流式
    try {
      const response = await agentApi.chat({
        message: prompt,
        history: []
      })

      const idx = editMessages.value.findIndex(m => m.id === analysisMsg.id)
      if (idx !== -1) {
        editMessages.value[idx].content = response.message
        editMessages.value[idx].generating = false
      }
    } catch (error) {
      console.error('Failed to analyze skill:', error)
      const idx = editMessages.value.findIndex(m => m.id === analysisMsg.id)
      if (idx !== -1) {
        // 如果 API 完全失败，显示欢迎消息
        editMessages.value[idx].content = `📋 **当前技能：${skill.name}**\n\n` +
          `${skill.description || '暂无描述'}\n\n` +
          `请告诉我您想如何修改这个技能？例如：\n` +
          `- 修改技能描述\n` +
          `- 添加新的标签\n` +
          `- 更新技能内容\n\n` +
          `或者您可以切换到「手动编辑」模式直接修改。`
        editMessages.value[idx].generating = false
      }
    }
  } finally {
    isEditAiThinking.value = false
  }
}

// 发送编辑请求给 AI
const sendEditMessage = async () => {
  if (!editInput.value.trim() || isEditAiThinking.value || !editingSkillData.value) return

  const userMessage = editInput.value.trim()
  editInput.value = ''

  // 添加用户消息
  editMessages.value.push({
    id: Date.now(),
    role: 'user',
    content: userMessage
  })

  isEditAiThinking.value = true

  // AI 回复
  const aiMsg: EditMessage = {
    id: Date.now() + 1,
    role: 'assistant',
    content: '',
    generating: true
  }
  editMessages.value.push(aiMsg)

  try {
    const currentSkill = editingSkillData.value
    const prompt = `你是一个技能编辑助手。用户想要修改以下技能：

当前技能信息：
- 名称: ${currentSkill.name}
- 描述: ${currentSkill.description || '无'}
- 图标: ${currentSkill.icon}
- 标签: ${(currentSkill.tags || []).join(', ')}
- 技能内容 (SKILL.md):
\`\`\`
${currentSkill.skill_md || '暂无'}
\`\`\`

用户的修改请求: "${userMessage}"

请根据用户的请求，生成修改后的技能。回复格式要求：
1. 先简要说明你将进行的修改
2. 然后输出修改后的完整信息，使用以下 JSON 格式（必须包含在 \`\`\`json 代码块中）：
\`\`\`json
{
  "name": "技能名称",
  "description": "技能描述",
  "icon": "图标emoji",
  "tags": ["标签1", "标签2"],
  "skill_md": "完整的 SKILL.md 内容"
}
\`\`\`
3. 最后询问用户是否确认这些修改`

    // 构建历史
    const history = editMessages.value.slice(0, -1).map(m => ({
      role: m.role as 'user' | 'assistant',
      content: m.content
    }))

    let responseContent = ''

    try {
      // 尝试流式调用
      const stream = agentApi.chatStream({
        message: prompt,
        history
      })

      for await (const chunk of stream) {
        const idx = editMessages.value.findIndex(m => m.id === aiMsg.id)
        if (idx !== -1) {
          editMessages.value[idx].content += chunk
        }
      }

      const idx = editMessages.value.findIndex(m => m.id === aiMsg.id)
      if (idx !== -1) {
        responseContent = editMessages.value[idx].content
      }
    } catch (streamError) {
      console.warn('Stream failed, trying non-stream:', streamError)

      // 流式失败，尝试非流式
      const response = await agentApi.chat({
        message: prompt,
        history
      })

      responseContent = response.message
      const idx = editMessages.value.findIndex(m => m.id === aiMsg.id)
      if (idx !== -1) {
        editMessages.value[idx].content = responseContent
      }
    }

    // 完成生成
    const idx = editMessages.value.findIndex(m => m.id === aiMsg.id)
    if (idx !== -1) {
      editMessages.value[idx].generating = false

      // 尝试提取 JSON 修改内容
      const jsonMatch = responseContent.match(/```json\s*([\s\S]*?)\s*```/)
      if (jsonMatch) {
        try {
          const parsed = JSON.parse(jsonMatch[1])
          editModifiedSkill.value = parsed
          editWaitingConfirm.value = true
        } catch (e) {
          console.error('Failed to parse skill JSON:', e)
        }
      }
    }
  } catch (error) {
    console.error('Failed to get AI response:', error)
    const idx = editMessages.value.findIndex(m => m.id === aiMsg.id)
    if (idx !== -1) {
      editMessages.value[idx].content = '抱歉，AI 服务暂时不可用。您可以：\n\n' +
        '1. 重试发送消息\n' +
        '2. 切换到「手动编辑」模式直接修改'
      editMessages.value[idx].generating = false
    }
  } finally {
    isEditAiThinking.value = false
  }
}

// 确认 AI 修改
const confirmAiEdit = async () => {
  if (!editModifiedSkill.value || !editingSkillData.value) return

  try {
    const updateData = {
      name: editModifiedSkill.value.name || editingSkillData.value.name,
      description: editModifiedSkill.value.description || editingSkillData.value.description,
      icon: editModifiedSkill.value.icon || editingSkillData.value.icon,
      tags: editModifiedSkill.value.tags || editingSkillData.value.tags,
      skill_md: editModifiedSkill.value.skill_md || editingSkillData.value.skill_md
    }

    await skillsApi.update(editingSkillData.value.id, updateData)

    // 更新本地列表
    const index = skills.value.findIndex(s => s.id === editingSkillData.value!.id)
    if (index !== -1) {
      skills.value[index] = {
        ...skills.value[index],
        ...updateData
      }
    }

    showToastMessage('技能修改成功')
    closeEditModal()
  } catch (error: any) {
    console.error('Failed to update skill:', error)
    showToastMessage('保存失败: ' + (error.message || '未知错误'))
  }
}

// 继续修改
const continueEdit = () => {
  editWaitingConfirm.value = false
  editModifiedSkill.value = null
}

const closeEditModal = () => {
  showEditModal.value = false
  editingSkillData.value = null
  editMode.value = 'ai'
  editTab.value = 'basic'
  editTagsString.value = ''
  editMessages.value = []
  editInput.value = ''
  editWaitingConfirm.value = false
  editModifiedSkill.value = null
}

// 手动保存（手动模式）
const saveSkillEdit = async () => {
  if (!editingSkillData.value) return

  // 将标签字符串转换为数组
  const tagsArray = editTagsString.value
    .split(/[,，]/)  // 支持中英文逗号
    .map(t => t.trim())
    .filter(t => t.length > 0)

  try {
    // 调用 API 更新技能（包括 skill_md）
    await skillsApi.update(editingSkillData.value.id, {
      name: editingSkillData.value.name,
      description: editingSkillData.value.description,
      icon: editingSkillData.value.icon,
      tags: tagsArray,
      skill_md: editingSkillData.value.skill_md
    })

    // 更新本地列表
    const index = skills.value.findIndex(s => s.id === editingSkillData.value!.id)
    if (index !== -1) {
      skills.value[index] = { ...editingSkillData.value, tags: tagsArray }
    }

    showToastMessage('技能保存成功')
    closeEditModal()
  } catch (error: any) {
    console.error('Failed to update skill:', error)
    showToastMessage('保存失败: ' + (error.message || '未知错误'))
  }
}

// 从 Agent 页面跳转过来添加技能
const handleGotoSkills = (skillName: string, mode: 'create' | 'upload') => {
  pendingSkillName.value = skillName
  activeTab.value = 'skills'
  // 自动打开对应弹窗
  nextTick(() => {
    modalMode.value = mode
    showModal.value = true
  })
}

// 下拉菜单状态
const activeDropdown = ref<number | null>(null)
const dropdownPos = ref({ x: 0, y: 0 })

const dropdownStyle = computed(() => ({
  left: `${dropdownPos.value.x}px`,
  top: `${dropdownPos.value.y}px`
}))

const handleSlotClick = (e: MouseEvent, index: number) => {
  const target = e.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  dropdownPos.value = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top
  }
  activeDropdown.value = index
}

const closeDropdown = () => {
  activeDropdown.value = null
}

// 点击外部关闭
const handleClickOutside = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (!target.closest('.slot-dropdown') && !target.closest('.empty-slot')) {
    closeDropdown()
  }
}

// 监听全局点击和加载数据
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  // 加载技能数据
  loadSkills()
  // 加载工作流数据
  loadWorkflows()
})
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  // 清理 tooltip 状态，避免页面切换后浮框残留
  wfTooltip.value.show = false
  // 清理 WorkflowBuilder 的浮框
  workflowBuilderRef.value?.closeAllPopups()
})
</script>

<template>
  <div class="page">
    <!-- 主体 -->
    <div class="body">
      <!-- 左侧导航 - 从首页跳转时隐藏 -->
      <nav v-if="!hideSidebar" class="sidebar">
        <div class="sidebar-logo">
          <div class="logo-icon">
            <svg viewBox="0 0 36 36" fill="none">
              <circle cx="18" cy="18" r="16" fill="url(#logo-grad)" />
              <circle cx="18" cy="18" r="12" fill="rgba(255,255,255,0.15)" />
              <path d="M18 10L18 26M12 14L18 10L24 14M12 22L18 26L24 22" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <defs>
                <linearGradient id="logo-grad" x1="0" y1="0" x2="36" y2="36">
                  <stop stop-color="#818cf8"/>
                  <stop offset="1" stop-color="#c084fc"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
        </div>
        <div class="nav-tabs">
          <button class="nav-btn" :class="{ active: activeTab === 'agent' }" @click="activeTab = 'agent'">
            <span class="nav-icon">💬</span>
            <span class="nav-label">对话</span>
          </button>
          <button class="nav-btn" :class="{ active: activeTab === 'skills' }" @click="activeTab = 'skills'">
            <span class="nav-icon">⚡</span>
            <span class="nav-label">技能</span>
          </button>
          <button class="nav-btn" :class="{ active: activeTab === 'workflows' }" @click="activeTab = 'workflows'">
            <span class="nav-icon">🔄</span>
            <span class="nav-label">流程</span>
          </button>
        </div>
        <div class="nav-spacer"></div>
      </nav>

      <!-- 内容区 -->
      <main class="content">
        <div v-show="activeTab === 'skills'" class="skills-area">
          <!-- 顶部预留区域 - 2倍高度 -->
          <div class="top-section">
            <div class="showcase-box">
              <div class="showcase-bg"></div>
              <div class="showcase-content">
                <div class="showcase-left">
                  <div class="showcase-badge">✨ AI-Powered</div>
                  <h2 class="showcase-title">Skill Studio</h2>
                  <p class="showcase-desc">Create, manage and deploy intelligent skills for your AI agents</p>
                </div>
                <div class="showcase-stats">
                  <div class="stat-item">
                    <span class="stat-value">{{ skills.length }}</span>
                    <span class="stat-label">Active Skills</span>
                  </div>
                  <div class="stat-divider"></div>
                  <div class="stat-item">
                    <span class="stat-value">{{ emptyCount }}</span>
                    <span class="stat-label">Available Slots</span>
                  </div>
                  <div class="stat-divider"></div>
                  <div class="stat-item">
                    <span class="stat-value">∞</span>
                    <span class="stat-label">Possibilities</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <!-- Grid 滚动容器 -->
          <div class="grid-wrapper" ref="gridWrapperRef" @scroll="checkScrollPosition">
            <!-- 卡片网格 -->
            <div class="grid">
            <template v-for="(item, index) in displayList" :key="index">
              <!-- 有内容的卡片 -->
              <div v-if="item" class="grid-cell">
                <SkillCard :skill="item" @delete="deleteSkill(index)" @edit="editSkill(item)" />
              </div>
              <!-- 空位占位符 -->
              <div v-else class="grid-cell">
                <div class="empty-slot" @click.stop="handleSlotClick($event, index)">
                  <div class="empty-slot-bg"></div>
                  <div class="empty-slot-content">
                    <div class="empty-slot-icon">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <line x1="12" y1="5" x2="12" y2="19"/>
                        <line x1="5" y1="12" x2="19" y2="12"/>
                      </svg>
                    </div>
                  </div>
                  <!-- 点击弹出下拉菜单 -->
                  <div
                    v-if="activeDropdown === index"
                    class="slot-dropdown"
                    :style="dropdownStyle"
                    @click.stop
                  >
                    <button class="dropdown-item" @click="openCreateModal(); closeDropdown()">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="12" y1="5" x2="12" y2="19"/>
                        <line x1="5" y1="12" x2="19" y2="12"/>
                      </svg>
                      <span>创建</span>
                    </button>
                    <button class="dropdown-item" @click="openUploadModal(); closeDropdown()">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="17 8 12 3 7 8"/>
                        <line x1="12" y1="3" x2="12" y2="15"/>
                      </svg>
                      <span>上传</span>
                    </button>
                  </div>
                </div>
              </div>
            </template>
            </div>
          </div>
          <!-- 向上滚动按钮 -->
          <button v-show="canScrollUp" class="scroll-btn scroll-up-btn" @click="scrollUpOne" @dblclick="scrollUpPage">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M5 15l7-7 7 7"/>
            </svg>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M5 15l7-7 7 7"/>
            </svg>
          </button>
          <!-- 向下滚动按钮 -->
          <button class="scroll-btn scroll-down-btn" @click="scrollDownOne" @dblclick="scrollDownPage">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M19 9l-7 7-7-7"/>
            </svg>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M19 9l-7 7-7-7"/>
            </svg>
          </button>
        </div>
        <div v-show="activeTab === 'agent'" class="agent-area">
          <AgentChat
            ref="agentChatRef"
            :skills="skills"
            @goto-skills="handleGotoSkills"
            @save-workflow="handleSaveWorkflowFromAgent"
          />
        </div>
        <!-- Workflows 区域 -->
        <div v-show="activeTab === 'workflows'" class="workflows-area">
          <!-- 如果正在编辑/创建工作流 -->
          <WorkflowBuilder
            ref="workflowBuilderRef"
            v-if="showWorkflowBuilder"
            :skills="skills"
            :workflows="workflows"
            :editing-workflow="editingWorkflow"
            @save="handleSaveWorkflow"
            @close="showWorkflowBuilder = false"
          />
          <!-- 工作流列表 -->
          <div v-else class="workflows-list">
            <!-- 顶部信息栏 - 类似 Agent 头部 -->
            <header class="workflows-topbar">
              <div class="topbar-left">
                <div class="topbar-icon">
                  <span class="icon-emoji">⚡</span>
                  <span class="icon-pulse"></span>
                </div>
                <div class="topbar-info">
                  <h3>Workflow Studio</h3>
                  <span class="topbar-status">自动化流程编排</span>
                </div>
              </div>
              <div class="topbar-right">
                <div class="topbar-stats">
                  <div class="stat-box">
                    <span class="stat-num">{{ workflows.length }}</span>
                    <span class="stat-label">工作流</span>
                  </div>
                  <div class="stat-divider"></div>
                  <div class="stat-box">
                    <span class="stat-num">{{ skills.length }}</span>
                    <span class="stat-label">可用技能</span>
                  </div>
                </div>
                <button class="topbar-btn" @click="openCreateWorkflow">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="12" y1="5" x2="12" y2="19"/>
                    <line x1="5" y1="12" x2="19" y2="12"/>
                  </svg>
                  新建工作流
                </button>
              </div>
            </header>
            <!-- 空状态 -->
            <div v-if="workflows.length === 0" class="workflows-empty">
              <div class="empty-illustration">
                <div class="flow-icon">🔄</div>
                <div class="flow-dots">
                  <span></span><span></span><span></span>
                </div>
              </div>
              <h3>还没有工作流</h3>
              <p>创建你的第一个工作流，将多个 Skill 组合成可复用的自动化流程</p>
              <button class="start-btn" @click="openCreateWorkflow">
                开始创建
              </button>
            </div>
            <!-- 工作流卡片网格 -->
            <div v-else class="workflows-grid">
              <!-- 工作流卡片 - 类似SkillCard样式 -->
              <article
                v-for="workflow in workflows"
                :key="workflow.id"
                class="wf-card"
                @click="runWorkflow(workflow)"
                @mouseenter="(e) => handleWfMouseMove(e, workflow)"
                @mousemove="(e) => handleWfMouseMove(e, workflow)"
                @mouseleave="handleWfMouseLeave"
              >
                <!-- 顶部栏 -->
                <div class="wf-header">
                  <span class="wf-title">{{ workflow.name }}</span>
                  <div class="wf-actions">
                    <span class="wf-action run" title="运行" @click.stop="runWorkflow(workflow)">▶</span>
                    <span class="wf-action edit" @click.stop="openEditWorkflow(workflow)" title="编辑">✎</span>
                    <span class="wf-action del" @click.stop="deleteWorkflow(workflow.id)" title="删除">×</span>
                  </div>
                </div>

                <!-- 中间主体 -->
                <div class="wf-body">
                  <span class="wf-icon">{{ workflow.icon || '🔄' }}</span>
                  <div class="wf-info">
                    <div class="wf-desc">{{ workflow.description || '点击运行工作流' }}</div>
                    <span class="wf-steps">{{ workflow.nodes.length }} 步骤</span>
                  </div>
                </div>

                <!-- 底部栏 -->
                <div class="wf-footer">
                  <div class="wf-tags">
                    <span class="wf-tag">{{ workflow.nodes.length }}步骤</span>
                    <span v-if="getWorkflowIO(workflow).inputCount > 0" class="wf-tag input">
                      {{ getWorkflowIO(workflow).inputCount }}个输入
                    </span>
                    <span v-if="getWorkflowIO(workflow).outputType" class="wf-tag output">
                      {{ getWorkflowIO(workflow).outputType }}
                    </span>
                  </div>
                </div>
              </article>

              <!-- 添加新工作流 -->
              <div class="wf-card wf-card-add" @click="openCreateWorkflow">
                <div class="wf-add-content">
                  <span class="wf-add-icon">+</span>
                  <span class="wf-add-text">新建工作流</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Agents 管理区域 -->
        <div v-show="activeTab === 'agents'" class="agents-area">
          <div class="agents-header">
            <div class="agents-title-row">
              <h2>Agent 市场</h2>
              <button class="btn-create-agent" @click="openAgentStudio()">
                <span>+</span> 创建 Agent
              </button>
            </div>
            <p class="agents-desc">发现和管理智能 Agent</p>
          </div>
          <div class="agents-grid">
            <div v-for="agent in sampleAgents" :key="agent.id" class="agent-card">
              <div class="agent-card-header">
                <span class="agent-icon">{{ agent.icon }}</span>
                <span :class="['agent-status', agent.status]">{{ agent.status === 'active' ? '已发布' : '草稿' }}</span>
              </div>
              <h3 class="agent-name">{{ agent.name }}</h3>
              <p class="agent-desc">{{ agent.description }}</p>
              <div class="agent-tags">
                <span v-for="cap in agent.capabilities.slice(0, 3)" :key="cap" class="agent-tag">{{ cap }}</span>
              </div>
              <div class="agent-card-actions">
                <button class="btn-use-agent" @click="useAgent(agent)">使用</button>
                <button class="btn-edit-agent" @click="editAgent(agent)">编辑</button>
              </div>
            </div>
          </div>
        </div>

        <!-- 监控区域 -->
        <div v-show="activeTab === 'monitor'" class="monitor-area">
          <div class="monitor-header">
            <h2>执行监控</h2>
            <p class="monitor-desc">实时监控 Agent 执行状态</p>
          </div>
          <div class="monitor-stats">
            <div class="monitor-stat">
              <span class="stat-value">{{ monitorStats.totalExecutions }}</span>
              <span class="stat-label">总执行</span>
            </div>
            <div class="monitor-stat">
              <span class="stat-value">{{ monitorStats.successRate }}%</span>
              <span class="stat-label">成功率</span>
            </div>
            <div class="monitor-stat">
              <span class="stat-value">{{ monitorStats.avgDuration }}s</span>
              <span class="stat-label">平均耗时</span>
            </div>
          </div>
          <div class="monitor-logs">
            <h3>执行日志</h3>
            <div class="logs-list">
              <div v-for="log in executionLogs" :key="log.id" class="log-item">
                <span class="log-icon">{{ log.icon }}</span>
                <div class="log-info">
                  <span class="log-name">{{ log.name }}</span>
                  <span class="log-task">{{ log.task }}</span>
                </div>
                <span :class="['log-status', log.status]">{{ log.statusText }}</span>
                <span class="log-time">{{ log.time }}</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>

    <AddSkillModal :show="showModal" :mode="modalMode" :prefill-name="pendingSkillName" :is-from-agent="!!pendingSkillName" @close="closeModal" @submit="handleSkillSubmit" @return-to-agent="handleReturnToAgent" />

    <!-- 工作流运行对话框 -->
    <Teleport to="body">
      <Transition name="workflow-dialog">
        <div v-if="showRunWorkflowDialog" class="workflow-run-overlay" @click.self="cancelRunWorkflow">
          <div class="workflow-run-dialog">
            <!-- 对话框头部 -->
            <div class="wrd-header">
              <div class="wrd-workflow-info">
                <span class="wrd-icon">{{ pendingRunWorkflow?.icon || '🚀' }}</span>
                <div class="wrd-titles">
                  <h3 class="wrd-title">{{ pendingRunWorkflow?.name }}</h3>
                  <p class="wrd-subtitle">{{ pendingRunWorkflow?.nodes?.length || 0 }} 个步骤</p>
                </div>
              </div>
              <button class="wrd-close" @click="cancelRunWorkflow">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
              </button>
            </div>

            <!-- 对话框内容 -->
            <div class="wrd-content">
              <!-- 提示信息 -->
              <div class="wrd-hint">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 16v-4M12 8h.01"/>
                </svg>
                <span>告诉 AI 你想要完成什么任务，它会根据工作流中的技能来帮你处理</span>
              </div>

              <!-- 输入区域 -->
              <div
                class="wrd-input-area"
                :class="{ 'is-dragging': isWorkflowDragging }"
                @dragover="handleWorkflowDragOver"
                @dragleave="handleWorkflowDragLeave"
                @drop="handleWorkflowDrop"
              >
                <!-- 已上传文件 -->
                <div v-if="workflowRunFiles.length > 0" class="wrd-files">
                  <div
                    v-for="file in workflowRunFiles"
                    :key="file.id"
                    class="wrd-file"
                    :class="{ uploading: file.uploading }"
                  >
                    <span class="wrd-file-icon">{{ getFileIcon(file.type) }}</span>
                    <div class="wrd-file-info">
                      <span class="wrd-file-name">{{ file.name }}</span>
                      <span v-if="file.uploading" class="wrd-file-status">上传中...</span>
                      <span v-else class="wrd-file-size">{{ formatFileSize(file.size) }}</span>
                    </div>
                    <button class="wrd-file-remove" @click="removeWorkflowFile(file.id)">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 6L6 18M6 6l12 12"/>
                      </svg>
                    </button>
                  </div>
                </div>

                <!-- 文本输入 -->
                <textarea
                  v-model="workflowRunContext"
                  class="wrd-textarea"
                  placeholder="描述你的需求，例如：&#10;• 帮我分析这份销售报告，重点关注华东地区&#10;• 生成一个关于产品发布的演示文稿&#10;• 处理这些数据并生成可视化图表"
                  rows="5"
                  @keydown.ctrl.enter="confirmRunWorkflow"
                ></textarea>

                <!-- 底部操作栏 -->
                <div class="wrd-input-actions">
                  <div class="wrd-input-left">
                    <input
                      ref="workflowFileInputRef"
                      type="file"
                      multiple
                      hidden
                      @change="handleWorkflowFileSelect"
                    />
                    <button class="wrd-action-btn" @click="workflowFileInputRef?.click()" title="上传文件">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
                      </svg>
                      <span>添加文件</span>
                    </button>
                    <span class="wrd-tip">支持拖拽上传</span>
                  </div>
                  <span class="wrd-shortcut">Ctrl + Enter 快速执行</span>
                </div>
              </div>

              <!-- 工作流步骤预览 -->
              <div class="wrd-steps-preview">
                <div class="wrd-steps-title">执行步骤</div>
                <div class="wrd-steps-list">
                  <div
                    v-for="(node, index) in pendingRunWorkflow?.nodes || []"
                    :key="node.id"
                    class="wrd-step"
                  >
                    <div class="wrd-step-number">{{ index + 1 }}</div>
                    <span class="wrd-step-icon">{{ node.icon || '⚡' }}</span>
                    <span class="wrd-step-name">{{ node.name }}</span>
                    <span v-if="index < (pendingRunWorkflow?.nodes?.length || 0) - 1" class="wrd-step-arrow">→</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 对话框底部 -->
            <div class="wrd-footer">
              <button class="wrd-btn wrd-btn-secondary" @click="cancelRunWorkflow">
                取消
              </button>
              <button class="wrd-btn wrd-btn-primary" @click="confirmRunWorkflow">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
                开始执行
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 编辑技能弹窗 -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showEditModal && editingSkillData" class="edit-modal-overlay" @click.self="closeEditModal">
          <div class="edit-modal edit-modal-wide">
            <div class="edit-modal-header">
              <h3>编辑技能</h3>
              <div class="edit-mode-switch">
                <button
                  class="mode-btn"
                  :class="{ active: editMode === 'ai' }"
                  @click="editMode = 'ai'"
                >
                  <span class="mode-icon">🤖</span>
                  AI 辅助
                </button>
                <button
                  class="mode-btn"
                  :class="{ active: editMode === 'manual' }"
                  @click="editMode = 'manual'"
                >
                  <span class="mode-icon">✏️</span>
                  手动编辑
                </button>
              </div>
              <button class="close-btn" @click="closeEditModal">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
              </button>
            </div>

            <!-- AI 辅助模式 -->
            <div v-if="editMode === 'ai'" class="edit-ai-mode">
              <!-- 技能信息卡片 -->
              <div class="skill-info-card">
                <div class="skill-info-icon">{{ editingSkillData.icon }}</div>
                <div class="skill-info-body">
                  <div class="skill-info-name">{{ editingSkillData.name }}</div>
                  <div class="skill-info-desc">{{ editingSkillData.description || '暂无描述' }}</div>
                </div>
                <div class="skill-info-tags">
                  <span v-for="tag in editingSkillData.tags" :key="tag" class="skill-tag">{{ tag }}</span>
                </div>
              </div>

              <!-- AI 对话区域 -->
              <div class="edit-chat-area">
                <div class="edit-messages">
                  <div v-if="isLoadingSkillDetail" class="edit-loading">
                    <div class="loading-spinner"></div>
                    <span>正在加载技能...</span>
                  </div>
                  <template v-else>
                    <div
                      v-for="msg in editMessages"
                      :key="msg.id"
                      class="edit-message"
                      :class="msg.role"
                    >
                      <div class="message-avatar">
                        {{ msg.role === 'user' ? '👤' : '🤖' }}
                      </div>
                      <div class="message-content">
                        <div class="message-text" v-html="msg.content.replace(/\n/g, '<br>')"></div>
                        <div v-if="msg.generating" class="message-typing">
                          <span></span><span></span><span></span>
                        </div>
                      </div>
                    </div>
                  </template>
                </div>

                <!-- 确认修改按钮组 -->
                <div v-if="editWaitingConfirm" class="edit-confirm-bar">
                  <span class="confirm-hint">AI 已生成修改建议，是否应用？</span>
                  <div class="confirm-buttons">
                    <button class="confirm-btn secondary" @click="continueEdit">继续修改</button>
                    <button class="confirm-btn primary" @click="confirmAiEdit">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                      确认应用
                    </button>
                  </div>
                </div>

                <!-- 输入区域 -->
                <div v-else class="edit-input-bar">
                  <input
                    v-model="editInput"
                    type="text"
                    placeholder="告诉 AI 你想如何修改这个技能..."
                    :disabled="isEditAiThinking"
                    @keyup.enter="sendEditMessage"
                  />
                  <button
                    class="send-btn"
                    :disabled="!editInput.trim() || isEditAiThinking"
                    @click="sendEditMessage"
                  >
                    <svg v-if="!isEditAiThinking" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <line x1="22" y1="2" x2="11" y2="13"/>
                      <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                    </svg>
                    <div v-else class="btn-spinner"></div>
                  </button>
                </div>
              </div>
            </div>

            <!-- 手动编辑模式 -->
            <div v-else class="edit-manual-mode">
              <div class="edit-tabs">
                <button
                  class="edit-tab"
                  :class="{ active: editTab === 'basic' }"
                  @click="editTab = 'basic'"
                >
                  基本信息
                </button>
                <button
                  class="edit-tab"
                  :class="{ active: editTab === 'content' }"
                  @click="editTab = 'content'"
                >
                  技能内容
                </button>
              </div>

              <!-- 基本信息 Tab -->
              <div v-show="editTab === 'basic'" class="edit-modal-body">
                <div class="edit-field">
                  <label>图标</label>
                  <div class="icon-selector">
                    <button
                      v-for="icon in ['⚡', '📊', '🔗', '📑', '🌍', '🖼️', '💻', '🧪', '🗃️', '📧', '🔍', '🎨']"
                      :key="icon"
                      class="icon-option"
                      :class="{ active: editingSkillData.icon === icon }"
                      @click="editingSkillData.icon = icon"
                    >
                      {{ icon }}
                    </button>
                  </div>
                </div>
                <div class="edit-field">
                  <label>名称</label>
                  <input v-model="editingSkillData.name" type="text" placeholder="技能名称" />
                </div>
                <div class="edit-field">
                  <label>描述</label>
                  <textarea v-model="editingSkillData.description" placeholder="技能描述" rows="3"></textarea>
                </div>
                <div class="edit-field">
                  <label>标签</label>
                  <input v-model="editTagsString" type="text" placeholder="用逗号分隔标签，如：Expert, Public" />
                </div>
              </div>
              <!-- 技能内容 Tab -->
              <div v-show="editTab === 'content'" class="edit-modal-body edit-modal-body-content">
                <div class="skill-content-header">
                  <div class="skill-content-label">
                    <span class="label-icon">📄</span>
                    <span>SKILL.md</span>
                  </div>
                  <span class="skill-content-hint">定义技能的详细说明和执行逻辑</span>
                </div>
                <div v-if="isLoadingSkillDetail" class="skill-content-loading">
                  <div class="loading-spinner"></div>
                  <span>加载中...</span>
                </div>
                <textarea
                  v-else
                  v-model="editingSkillData.skill_md"
                  class="skill-md-editor"
                  placeholder="# 技能名称

## 描述
这个技能的功能描述...

## 使用方法
如何使用这个技能...

## 示例
使用示例..."
                ></textarea>
              </div>

              <div class="edit-modal-footer">
                <button class="cancel-btn" @click="closeEditModal">取消</button>
                <button class="save-btn" @click="saveSkillEdit">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  保存
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 工作流运行器弹窗 -->
    <Teleport to="body">
      <div v-if="showWorkflowRunner && runningWorkflowId" class="runner-overlay" @click.self="closeWorkflowRunner">
        <WorkflowRunner
          :workflow-id="runningWorkflowId"
          :workflow-name="runningWorkflowName || undefined"
          @close="closeWorkflowRunner"
          @completed="handleWorkflowCompleted"
        />
      </div>
    </Teleport>

    <!-- Toast 提示 -->
    <Transition name="toast">
      <div v-if="showToast" class="toast">
        <span class="toast-icon">✅</span>
        <span class="toast-message">{{ toastMessage }}</span>
      </div>
    </Transition>

    <!-- Workflow Tooltip (Teleport 到 body) -->
    <Teleport to="body">
      <Transition name="wf-tooltip">
        <div v-if="wfTooltip.show && wfTooltip.workflow" class="wf-tooltip" :style="wfTooltip.style">
          <div class="wf-tooltip-header">
            <span class="wf-tooltip-icon">{{ wfTooltip.workflow.icon || '⚡' }}</span>
            <span class="wf-tooltip-name">{{ wfTooltip.workflow.name }}</span>
          </div>
          <p class="wf-tooltip-desc">{{ wfTooltip.workflow.description || '点击运行' }}</p>
          <div class="wf-tooltip-meta">
            <span>{{ wfTooltip.workflow.nodes.length }} 步骤</span>
            <span>{{ wfTooltip.workflow.edges?.length || 0 }} 连接</span>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.page {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f4f6f8;
}

/* Body */
.body {
  flex: 1;
  display: flex;
  overflow: hidden;
  gap: 0;
}

/* Sidebar */
.sidebar {
  width: 72px;
  background: linear-gradient(180deg, #ffffff 0%, #fafbfc 100%);
  margin: 8px 0 8px 8px;
  border-radius: 12px;
  border: 1px solid #e0e4e8;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  box-shadow:
    0 2px 4px rgba(0,0,0,0.04),
    0 4px 8px rgba(0,0,0,0.04),
    inset 0 1px 0 rgba(255,255,255,0.8),
    inset 0 -1px 0 rgba(0,0,0,0.03);
}

.sidebar-logo {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 4px;
  flex: 1;
}

.logo-icon {
  width: 40px;
  height: 40px;
  filter: drop-shadow(0 2px 4px rgba(129, 140, 248, 0.3));
  transition: transform 0.2s ease;
}

.logo-icon:hover {
  transform: scale(1.05);
}

.logo-icon svg {
  width: 100%;
  height: 100%;
}

.nav-spacer {
  flex: 1;
}

.nav-tabs {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-btn {
  width: 100%;
  height: 48px;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  transition: all 0.15s;
}

.nav-btn:hover {
  background: #f3f4f6;
}

.nav-btn.active {
  background: #eef2ff;
}

.nav-icon {
  font-size: 18px;
}

.nav-label {
  font-size: 9px;
  font-weight: 600;
  color: #9ca3af;
}

.nav-btn.active .nav-label {
  color: #6366f1;
}

/* Content */
.content {
  flex: 1;
  padding: 12px 16px;
  overflow: visible;
  display: flex;
}

/* Skills区域 */
.skills-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  height: 100%;
  min-width: 0;
  overflow: hidden;
  position: relative;
  /* 每行高度：基于视口计算，一屏正好4行 */
  /* 100vh - 顶部区域(120px) - 外边距(16px) - 4个gap(32px) 再除以4 */
  --row-height: calc((100vh - 168px) / 4);
}

/* 顶部预留区域 - 2倍高度 */
.top-section {
  flex-shrink: 0;
  height: 120px;
}

/* Showcase Box */
.showcase-box {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  position: relative;
  overflow: hidden;
}

.showcase-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 50%, rgba(255,255,255,0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255,255,255,0.08) 0%, transparent 40%),
    radial-gradient(circle at 60% 80%, rgba(255,255,255,0.05) 0%, transparent 30%);
}

.showcase-content {
  position: relative;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.showcase-left {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.showcase-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(255,255,255,0.2);
  backdrop-filter: blur(4px);
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 10px;
  font-weight: 600;
  color: #fff;
  width: fit-content;
}

.showcase-title {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  margin: 0;
  letter-spacing: -0.5px;
}

.showcase-desc {
  font-size: 11px;
  color: rgba(255,255,255,0.85);
  margin: 0;
  max-width: 280px;
}

.showcase-stats {
  display: flex;
  align-items: center;
  gap: 16px;
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(8px);
  padding: 12px 20px;
  border-radius: 10px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
}

.stat-label {
  font-size: 9px;
  color: rgba(255,255,255,0.8);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-divider {
  width: 1px;
  height: 32px;
  background: rgba(255,255,255,0.25);
}

/* 滚动按钮通用样式 */
.scroll-btn {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  width: 70px;
  height: 50px;
  border-radius: 25px;
  border: none;
  background: radial-gradient(circle, rgba(102, 126, 234, 0.35) 0%, rgba(102, 126, 234, 0.15) 50%, transparent 75%);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0;
  z-index: 10;
  transition: all 0.2s ease;
}

.scroll-btn:hover {
  transform: translateX(-50%) scale(1.1);
  background: radial-gradient(circle, rgba(102, 126, 234, 0.5) 0%, rgba(102, 126, 234, 0.2) 50%, transparent 75%);
}

.scroll-btn svg {
  width: 28px;
  height: 16px;
  stroke: #667eea;
  transition: all 0.3s ease;
}

/* 第一个箭头更透明 */
.scroll-btn svg:first-child {
  opacity: 0.35;
  margin-bottom: -6px;
}

/* 第二个箭头更实 */
.scroll-btn svg:last-child {
  opacity: 0.8;
}

.scroll-btn:hover svg:first-child {
  opacity: 0.6;
}

.scroll-btn:hover svg:last-child {
  opacity: 1;
}

/* 向上按钮 */
.scroll-up-btn {
  top: 130px;
}

.scroll-up-btn svg:first-child {
  margin-bottom: 0;
  margin-top: -8px;
  order: 2;
}

.scroll-up-btn svg:last-child {
  order: 1;
}

.scroll-up-btn svg {
  animation: bounceUp 1.5s ease-in-out infinite;
}

.scroll-up-btn svg:first-child {
  animation-delay: 0.15s;
}

/* 向下按钮 */
.scroll-down-btn {
  bottom: 16px;
}

.scroll-down-btn svg {
  animation: bounceDown 1.5s ease-in-out infinite;
}

.scroll-down-btn svg:last-child {
  animation-delay: 0.15s;
}

@keyframes bounceDown {
  0%, 100% { transform: translateY(0); opacity: inherit; }
  50% { transform: translateY(2px); opacity: 1; }
}

@keyframes bounceUp {
  0%, 100% { transform: translateY(0); opacity: inherit; }
  50% { transform: translateY(-2px); opacity: 1; }
}

/* Grid 滚动容器 */
.grid-wrapper {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  /* 隐藏滚动条 */
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.grid-wrapper::-webkit-scrollbar {
  display: none;
}

/* Grid */
.grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  grid-auto-rows: var(--row-height);
  gap: 8px;
}

.grid-cell {
  min-width: 0;
  min-height: 0;
  display: flex;
  padding: 3px;
  overflow: visible;
}

/* 空位占位符 */
.empty-slot {
  flex: 1;
  position: relative;
  border-radius: 6px;
  cursor: pointer;
  overflow: visible;
}

.empty-slot-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #f8f9fb 0%, #f0f2f5 100%);
  border: 1px dashed #dde1e6;
  border-radius: 6px;
  transition: all 0.25s ease;
}

.empty-slot-content {
  position: relative;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
  transition: opacity 0.25s ease;
}

.empty-slot-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  transition: all 0.25s ease;
}

.empty-slot-icon svg {
  width: 14px;
  height: 14px;
  color: #c4c9d1;
  transition: all 0.25s ease;
}

.empty-slot:hover .empty-slot-bg {
  border-color: #c0c6ce;
  background: linear-gradient(135deg, #f5f7fa 0%, #ebeef2 100%);
}

.empty-slot:hover .empty-slot-icon {
  transform: scale(1.05);
}

.empty-slot:hover .empty-slot-icon svg {
  color: #a0a5ad;
}

/* 点击弹出下拉菜单 */
.slot-dropdown {
  position: absolute;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  z-index: 100;
  border-radius: 6px;
  overflow: visible;
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
  animation: dropdownFadeIn 0.15s ease;
}

@keyframes dropdownFadeIn {
  from {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #fff;
  border: none;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  color: #374151;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.dropdown-item:first-child {
  border-radius: 6px 6px 0 0;
  border-bottom: 1px solid #f0f0f0;
}

.dropdown-item:last-child {
  border-radius: 0 0 6px 6px;
}

.dropdown-item:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.dropdown-item svg {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

/* Agent 区域 */
.agent-area {
  flex: 1;
  width: 100%;
  display: flex;
  min-height: 0;
  overflow: hidden;
}

/* Workflows 区域 */
.workflows-area {
  flex: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: visible;
}

.workflows-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0 20px;
  overflow-x: visible;
  overflow-y: auto;
}

/* 顶部信息栏 */
.workflows-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  margin-bottom: 20px;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.topbar-icon {
  position: relative;
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-emoji {
  font-size: 20px;
}

.icon-pulse {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 10px;
  height: 10px;
  background: #10b981;
  border: 2px solid #667eea;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.8; }
}

.topbar-info h3 {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 2px 0;
}

.topbar-status {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.8);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.topbar-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 14px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 8px;
}

.stat-box {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-num {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
}

.stat-label {
  font-size: 9px;
  color: rgba(255, 255, 255, 0.8);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-divider {
  width: 1px;
  height: 24px;
  background: rgba(255, 255, 255, 0.2);
}

.topbar-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.topbar-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.topbar-btn svg {
  width: 14px;
  height: 14px;
}

/* 兼容旧按钮样式 */
.create-workflow-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.create-workflow-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

.create-workflow-btn svg {
  width: 16px;
  height: 16px;
}

/* Workflows Empty */
.workflows-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px;
}

.empty-illustration {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24px;
}

.flow-icon {
  font-size: 56px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.flow-dots {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.flow-dots span {
  width: 8px;
  height: 8px;
  background: #cbd5e1;
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

.flow-dots span:nth-child(2) { animation-delay: 0.2s; }
.flow-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes pulse {
  0%, 100% { opacity: 0.4; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); }
}

.workflows-empty h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 8px;
}

.workflows-empty p {
  font-size: 14px;
  color: #64748b;
  margin: 0 0 24px;
  max-width: 360px;
}

.start-btn {
  padding: 12px 28px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 10px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.start-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
}

/* 工作流网格容器 - 允许 tooltip 溢出 */
.workflows-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 16px;
  padding: 10px 0 120px 0;  /* 底部留空间给 tooltip */
  overflow: visible;
  position: relative;
}

/* 工作流方块 */
/* Workflow 卡片 - 类似 SkillCard 样式 */
.wf-card {
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 10px;
  cursor: pointer;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.2s, transform 0.15s;
}

.wf-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  transform: translateY(-1px);
}

/* 顶部栏 */
.wf-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: linear-gradient(135deg, #fef5f5 0%, #fdf8f8 100%);
  border-bottom: 1px solid #f5e8e8;
  flex-shrink: 0;
}

.wf-type-badge {
  font-size: 8px;
  padding: 1px 5px;
  border-radius: 3px;
  font-weight: 700;
  letter-spacing: 0.5px;
  background: #9b59b6;
  color: #fff;
  flex-shrink: 0;
}

.wf-title {
  flex: 1;
  font-size: 11px;
  font-weight: 600;
  color: #8e44ad;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wf-actions {
  display: flex;
  gap: 4px;
}

.wf-action {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  cursor: pointer;
  border-radius: 3px;
  transition: background 0.15s;
}

.wf-action.run {
  color: #9b59b6;
}

.wf-action.run:hover {
  background: rgba(155, 89, 182, 0.1);
}

.wf-action.edit {
  color: #3498db;
}

.wf-action.edit:hover {
  background: rgba(52, 152, 219, 0.1);
}

.wf-action.del {
  color: #bdc3c7;
  font-size: 14px;
  font-weight: 300;
}

.wf-action.del:hover {
  color: #e74c3c;
  background: rgba(231, 76, 60, 0.1);
}

/* 中间主体 */
.wf-body {
  flex: 1;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  overflow: hidden;
  min-height: 0;
}

.wf-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  background: linear-gradient(135deg, #9b59b6, #8e44ad);
  box-shadow: 0 2px 6px rgba(155, 89, 182, 0.3);
}

.wf-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  overflow: hidden;
}

.wf-desc {
  font-size: 11px;
  color: #555;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wf-steps {
  font-size: 9px;
  color: #aaa;
}

/* 底部栏 */
.wf-footer {
  padding: 6px 10px;
  background: #fafafa;
  border-top: 1px solid #f0f0f0;
  flex-shrink: 0;
}

.wf-tags {
  display: flex;
  align-items: center;
  gap: 6px;
}

.wf-tag {
  font-size: 9px;
  padding: 2px 8px;
  background: #f5e6f5;
  color: #8e44ad;
  border-radius: 4px;
  white-space: nowrap;
  font-weight: 500;
}

.wf-tag.input {
  background: #dbeafe;
  color: #1d4ed8;
}

.wf-tag.output {
  background: #fef3c7;
  color: #b45309;
}

/* 添加卡片 */
.wf-card.wf-card-add {
  background: #fafbfc;
  border: 2px dashed #d0d5dd;
  justify-content: center;
  align-items: center;
  min-height: 120px;
}

.wf-card.wf-card-add:hover {
  border-color: #9b59b6;
  background: #fef5f5;
}

.wf-add-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.wf-add-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #f5e6f5, #e8d4e8);
  color: #9b59b6;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 300;
}

.wf-add-text {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

/* Toast */
.toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 24px;
  background: #1e293b;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  z-index: 1000;
}

.toast-icon {
  font-size: 18px;
}

.toast-message {
  font-size: 14px;
  font-weight: 500;
  color: #fff;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}

/* 工作流运行器遮罩 */
.runner-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 响应式 */
@media (max-width: 1400px) {
  .grid { grid-template-columns: repeat(4, 1fr); }
}

@media (max-width: 1100px) {
  .grid { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 800px) {
  .grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 500px) {
  .grid { grid-template-columns: 1fr; }
  .sidebar { width: 56px; margin: 4px 0 4px 4px; padding: 8px 4px; }
  .sidebar-logo { padding-top: 4px; }
  .logo-icon { width: 32px; height: 32px; }
  .content { padding: 8px 10px; }
  .showcase-content { flex-direction: column; padding: 12px; gap: 8px; }
  .showcase-stats { padding: 8px 12px; gap: 10px; }
  .stat-value { font-size: 16px; }
  .showcase-title { font-size: 18px; }
  .header-add-btn span { display: none; }
}

/* 编辑技能弹窗 */
.edit-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.edit-modal {
  background: #fff;
  border-radius: 16px;
  width: 400px;
  max-width: 90vw;
  max-height: 85vh;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease;
}

.edit-modal.edit-modal-wide {
  width: 600px;
  height: 520px;
}

/* 模式切换 */
.edit-mode-switch {
  display: flex;
  gap: 4px;
  background: #f1f5f9;
  padding: 3px;
  border-radius: 8px;
  margin-left: auto;
  margin-right: 12px;
}

.mode-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
}

.mode-btn:hover {
  color: #475569;
}

.mode-btn.active {
  background: #fff;
  color: #6366f1;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.mode-icon {
  font-size: 13px;
}

/* AI 辅助模式 */
.edit-ai-mode {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.skill-info-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.skill-info-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.skill-info-body {
  flex: 1;
  min-width: 0;
}

.skill-info-name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.skill-info-desc {
  font-size: 11px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.skill-info-tags {
  display: flex;
  gap: 4px;
}

.skill-tag {
  padding: 2px 6px;
  background: #e0e7ff;
  color: #4f46e5;
  font-size: 9px;
  font-weight: 600;
  border-radius: 4px;
  text-transform: uppercase;
}

/* AI 对话区域 */
.edit-chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.edit-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.edit-loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #94a3b8;
  font-size: 13px;
}

.edit-message {
  display: flex;
  gap: 10px;
  max-width: 90%;
}

.edit-message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.edit-message.assistant {
  align-self: flex-start;
}

.message-avatar {
  width: 28px;
  height: 28px;
  background: #f1f5f9;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
}

.edit-message.assistant .message-avatar {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-text {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
}

.edit-message.user .message-text {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.edit-message.assistant .message-text {
  background: #f1f5f9;
  color: #334155;
  border-bottom-left-radius: 4px;
}

.message-typing {
  display: flex;
  gap: 3px;
  padding: 0 4px;
}

.message-typing span {
  width: 5px;
  height: 5px;
  background: #94a3b8;
  border-radius: 50%;
  animation: typing 1.2s infinite;
}

.message-typing span:nth-child(2) { animation-delay: 0.2s; }
.message-typing span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-4px); opacity: 1; }
}

/* 确认栏 */
.edit-confirm-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  border-top: 1px solid #a7f3d0;
}

.confirm-hint {
  font-size: 13px;
  color: #047857;
  font-weight: 500;
}

.confirm-buttons {
  display: flex;
  gap: 8px;
}

.confirm-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
}

.confirm-btn.secondary {
  background: #fff;
  color: #64748b;
  border: 1px solid #e2e8f0;
}

.confirm-btn.secondary:hover {
  background: #f8fafc;
}

.confirm-btn.primary {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #fff;
}

.confirm-btn.primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.confirm-btn svg {
  width: 14px;
  height: 14px;
}

/* 输入栏 */
.edit-input-bar {
  display: flex;
  gap: 10px;
  padding: 12px 16px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
}

.edit-input-bar input {
  flex: 1;
  padding: 10px 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 13px;
  color: #1e293b;
  transition: all 0.15s;
}

.edit-input-bar input:focus {
  outline: none;
  border-color: #6366f1;
  background: #fff;
}

.edit-input-bar input:disabled {
  opacity: 0.6;
}

.send-btn {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 10px;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-btn svg {
  width: 18px;
  height: 18px;
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* 手动编辑模式 */
.edit-manual-mode {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.edit-manual-mode .edit-tabs {
  display: flex;
  gap: 4px;
  padding: 0 20px;
  border-bottom: 1px solid #f1f5f9;
  margin: 0;
  background: transparent;
}

.edit-modal-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid #f1f5f9;
  flex-shrink: 0;
}

.edit-modal-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.edit-tabs {
  display: flex;
  gap: 0;
  background: transparent;
  padding: 0;
  border-radius: 0;
}

.edit-tab {
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all 0.15s;
}

.edit-tab:hover {
  color: #475569;
}

.edit-tab.active {
  color: #6366f1;
  border-bottom-color: #6366f1;
}

.edit-modal-header .close-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: #94a3b8;
  transition: all 0.15s;
}

.edit-modal-header .close-btn:hover {
  background: #f1f5f9;
  color: #64748b;
}

.edit-modal-header .close-btn svg {
  width: 16px;
  height: 16px;
}

.edit-modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.edit-modal-body-content {
  gap: 12px;
}

.skill-content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.skill-content-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}

.label-icon {
  font-size: 14px;
}

.skill-content-hint {
  font-size: 11px;
  color: #94a3b8;
}

.skill-content-loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #94a3b8;
  font-size: 13px;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid #e2e8f0;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.skill-md-editor {
  flex: 1;
  min-height: 300px;
  padding: 14px;
  background: #1e293b;
  border: none;
  border-radius: 10px;
  font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #e2e8f0;
  resize: none;
  overflow-y: auto;
}

.skill-md-editor::placeholder {
  color: #64748b;
}

.skill-md-editor:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3);
}

.edit-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.edit-field label {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.edit-field input,
.edit-field textarea {
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  color: #1e293b;
  transition: all 0.15s;
  font-family: inherit;
}

.edit-field input:focus,
.edit-field textarea:focus {
  outline: none;
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

.edit-field textarea {
  resize: vertical;
  min-height: 60px;
}

.icon-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.icon-option {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
  border: 2px solid transparent;
  border-radius: 8px;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.15s;
}

.icon-option:hover {
  background: #f1f5f9;
}

.icon-option.active {
  background: #ede9fe;
  border-color: #8b5cf6;
}

.edit-modal-footer {
  display: flex;
  gap: 10px;
  padding: 16px 20px;
  background: #f8fafc;
  border-top: 1px solid #f1f5f9;
}

.edit-modal-footer .cancel-btn {
  flex: 1;
  padding: 10px 16px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s;
}

.edit-modal-footer .cancel-btn:hover {
  background: #f1f5f9;
}

.edit-modal-footer .save-btn {
  flex: 1.5;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  cursor: pointer;
  transition: all 0.15s;
}

.edit-modal-footer .save-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
}

.edit-modal-footer .save-btn svg {
  width: 14px;
  height: 14px;
}

/* modal 动画 */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.25s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .edit-modal,
.modal-leave-to .edit-modal {
  transform: scale(0.95) translateY(10px);
}

/* ========================================
   工作流运行对话框样式
   ======================================== */

.workflow-run-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.workflow-run-dialog {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 20px;
  box-shadow:
    0 25px 50px -12px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  width: 100%;
  max-width: 580px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 对话框头部 */
.wrd-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
}

.wrd-workflow-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.wrd-icon {
  width: 24px;
  height: 24px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

.wrd-titles {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.wrd-title {
  font-size: 13px;
  font-weight: 600;
  margin: 0;
}

.wrd-subtitle {
  font-size: 10px;
  opacity: 0.85;
  margin: 0;
}

.wrd-close {
  width: 22px;
  height: 22px;
  border: none;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 5px;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.wrd-close:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: scale(1.05);
}

.wrd-close svg {
  width: 12px;
  height: 12px;
}

/* 对话框内容 */
.wrd-content {
  padding: 14px;
  overflow-y: auto;
  flex: 1;
}

.wrd-hint {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  background: linear-gradient(135deg, #eff6ff 0%, #f0f9ff 100%);
  border-radius: 10px;
  margin-bottom: 14px;
  font-size: 12px;
  color: #3b82f6;
  line-height: 1.5;
}

.wrd-hint svg {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  margin-top: 1px;
}

/* 输入区域 */
.wrd-input-area {
  background: #f8fafc;
  border: 2px dashed #e2e8f0;
  border-radius: 12px;
  padding: 12px;
  transition: all 0.2s ease;
  margin-bottom: 14px;
}

.wrd-input-area.is-dragging {
  border-color: #6366f1;
  background: #f5f3ff;
}

/* 已上传文件 */
.wrd-files {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.wrd-file {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 12px;
  transition: all 0.2s ease;
}

.wrd-file.uploading {
  opacity: 0.7;
}

.wrd-file-icon {
  font-size: 16px;
}

.wrd-file-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.wrd-file-name {
  color: #334155;
  font-weight: 500;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wrd-file-size {
  color: #94a3b8;
  font-size: 11px;
}

.wrd-file-status {
  color: #6366f1;
  font-size: 11px;
}

.wrd-file-remove {
  width: 20px;
  height: 20px;
  border: none;
  background: transparent;
  border-radius: 5px;
  color: #94a3b8;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.wrd-file-remove:hover {
  background: #fee2e2;
  color: #ef4444;
}

.wrd-file-remove svg {
  width: 14px;
  height: 14px;
}

/* 文本输入 */
.wrd-textarea {
  width: 100%;
  padding: 14px 16px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  font-size: 14px;
  color: #1e293b;
  font-family: inherit;
  resize: none;
  transition: all 0.2s ease;
  line-height: 1.6;
}

.wrd-textarea:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.wrd-textarea::placeholder {
  color: #94a3b8;
}

/* 底部操作栏 */
.wrd-input-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
}

.wrd-input-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.wrd-action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s ease;
}

.wrd-action-btn:hover {
  background: #f8fafc;
  border-color: #6366f1;
  color: #6366f1;
}

.wrd-action-btn svg {
  width: 16px;
  height: 16px;
}

.wrd-tip {
  font-size: 12px;
  color: #94a3b8;
}

.wrd-shortcut {
  font-size: 12px;
  color: #94a3b8;
  background: #f1f5f9;
  padding: 4px 10px;
  border-radius: 6px;
}

/* 步骤预览 */
.wrd-steps-preview {
  background: #f8fafc;
  border-radius: 10px;
  padding: 10px;
}

.wrd-steps-title {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.wrd-steps-list {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.wrd-step {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 8px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.wrd-step-number {
  width: 16px;
  height: 16px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 600;
  color: white;
}

.wrd-step-icon {
  font-size: 12px;
}

.wrd-step-name {
  font-size: 11px;
  color: #334155;
  font-weight: 500;
}

.wrd-step-arrow {
  color: #cbd5e1;
  margin-left: 4px;
}

/* 对话框底部 */
.wrd-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 10px 14px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

.wrd-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 7px 14px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.wrd-btn svg {
  width: 14px;
  height: 14px;
}

.wrd-btn-secondary {
  background: white;
  border: 1px solid #e2e8f0;
  color: #64748b;
}

.wrd-btn-secondary:hover {
  background: #f8fafc;
  color: #334155;
}

.wrd-btn-primary {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}

.wrd-btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
}

/* 对话框动画 */
.workflow-dialog-enter-active,
.workflow-dialog-leave-active {
  transition: all 0.3s ease;
}

.workflow-dialog-enter-from,
.workflow-dialog-leave-to {
  opacity: 0;
}

.workflow-dialog-enter-from .workflow-run-dialog,
.workflow-dialog-leave-to .workflow-run-dialog {
  transform: scale(0.95) translateY(20px);
}

/* Workflow Tooltip - 紧凑跟随鼠标 */
.wf-tooltip {
  position: fixed;
  padding: 8px 10px;
  background: rgba(15, 23, 42, 0.95);
  color: #f1f5f9;
  border-radius: 6px;
  min-width: 120px;
  max-width: 160px;
  z-index: 99999;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  pointer-events: none;
  backdrop-filter: blur(8px);
}

.wf-tooltip-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.wf-tooltip-icon {
  font-size: 12px;
}

.wf-tooltip-name {
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wf-tooltip-desc {
  font-size: 10px;
  line-height: 1.3;
  color: #94a3b8;
  margin: 0 0 4px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.wf-tooltip-meta {
  display: flex;
  gap: 8px;
  font-size: 9px;
  color: #64748b;
}

/* Tooltip 动画 */
.wf-tooltip-enter-active {
  transition: all 0.12s ease-out;
}

.wf-tooltip-leave-active {
  transition: all 0.08s ease-in;
}

.wf-tooltip-enter-from,
.wf-tooltip-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* ============ Agents 区域样式 ============ */
.agents-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
  overflow-y: auto;
}

.agents-header {
  margin-bottom: 24px;
}

.agents-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.agents-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.agents-desc {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.btn-create-agent {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-create-agent:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.agent-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s;
}

.agent-card:hover {
  border-color: #c7d2fe;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

.agent-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.agent-icon {
  font-size: 28px;
}

.agent-status {
  padding: 3px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}

.agent-status.active {
  background: #dcfce7;
  color: #15803d;
}

.agent-status.draft {
  background: #fef3c7;
  color: #b45309;
}

.agent-name {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 6px;
}

.agent-desc {
  font-size: 13px;
  color: #64748b;
  margin: 0 0 12px;
  line-height: 1.4;
}

.agent-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.agent-tag {
  padding: 3px 8px;
  background: #f1f5f9;
  border-radius: 10px;
  font-size: 11px;
  color: #64748b;
}

.agent-card-actions {
  display: flex;
  gap: 8px;
}

.btn-use-agent {
  flex: 1;
  padding: 8px 12px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
}

.btn-edit-agent {
  padding: 8px 12px;
  background: #fff;
  color: #64748b;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
}

.btn-edit-agent:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

/* ============ Monitor 区域样式 ============ */
.monitor-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
  overflow-y: auto;
}

.monitor-header {
  margin-bottom: 20px;
}

.monitor-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 6px;
}

.monitor-desc {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.monitor-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.monitor-stat {
  flex: 1;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 12px;
  padding: 16px;
  text-align: center;
  color: white;
}

.monitor-stat .stat-value {
  font-size: 28px;
  font-weight: 700;
  display: block;
}

.monitor-stat .stat-label {
  font-size: 12px;
  opacity: 0.85;
}

.monitor-logs {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
}

.monitor-logs h3 {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 16px;
}

.logs-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.log-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.log-icon {
  font-size: 20px;
}

.log-info {
  flex: 1;
}

.log-name {
  font-size: 13px;
  font-weight: 500;
  color: #1e293b;
  display: block;
}

.log-task {
  font-size: 12px;
  color: #64748b;
}

.log-status {
  padding: 4px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}

.log-status.success {
  background: #dcfce7;
  color: #15803d;
}

.log-status.running {
  background: #fef3c7;
  color: #b45309;
}

.log-status.failed {
  background: #fee2e2;
  color: #b91c1c;
}

.log-time {
  font-size: 12px;
  color: #94a3b8;
}
</style>
