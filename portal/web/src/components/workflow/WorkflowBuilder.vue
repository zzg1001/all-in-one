<script setup lang="ts">
import { ref, computed, onMounted, watch, onBeforeUnmount } from 'vue'
import { skillsApi, workflowsApi, favoritesApi, dataNotesApi, type DataNote } from '@/api'
import config from '@/config'

interface WorkflowNode {
  id: string
  type: 'skill' | 'workflow' | 'data'
  name: string
  icon: string
  description: string
  position: { x: number; y: number }
  workflowData?: Workflow
  dataNote?: DataNote  // 数据源节点
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

const props = defineProps<{
  skills: Array<{ id: number; name: string; icon: string; description: string }>
  workflows: Workflow[]
  editingWorkflow?: Workflow | null
}>()

const emit = defineEmits<{
  save: [workflow: Workflow]
  close: []
}>()

const workflowName = ref('')
const workflowDesc = ref('')
const workflowIcon = ref('🔄')

const nodes = ref<WorkflowNode[]>([])
const edges = ref<WorkflowEdge[]>([])

// 初始化编辑数据
const initFromEditingWorkflow = () => {
  const editing = props.editingWorkflow
  console.log('initFromEditingWorkflow called, editingWorkflow:', editing)
  if (editing && editing.nodes && editing.nodes.length > 0) {
    workflowName.value = editing.name || ''
    workflowDesc.value = editing.description || ''
    workflowIcon.value = editing.icon || '🔄'
    nodes.value = JSON.parse(JSON.stringify(editing.nodes))
    edges.value = JSON.parse(JSON.stringify(editing.edges || []))
    console.log('Loaded nodes:', nodes.value.length, 'edges:', edges.value.length)
  } else if (!editing) {
    // 新建流程时清空
    workflowName.value = ''
    workflowDesc.value = ''
    workflowIcon.value = '🔄'
    nodes.value = []
    edges.value = []
  }
}

// 监听editingWorkflow变化
watch(() => props.editingWorkflow, (newVal, oldVal) => {
  console.log('editingWorkflow changed:', newVal?.name, 'from:', oldVal?.name)
  initFromEditingWorkflow()
}, { immediate: true, deep: true })

// 自动生成流程描述（根据节点和边的关系）
const autoDescription = computed(() => {
  if (nodes.value.length === 0) return ''

  // 找到起始节点（没有入边的节点）
  const nodeIds = new Set(nodes.value.map(n => n.id))
  const hasIncoming = new Set(edges.value.map(e => e.to))
  const startNodes = nodes.value.filter(n => !hasIncoming.has(n.id))

  // 构建邻接表
  const adj: Record<string, string[]> = {}
  edges.value.forEach(e => {
    if (!adj[e.from]) adj[e.from] = []
    const fromAdj = adj[e.from]
    if (fromAdj) fromAdj.push(e.to)
  })

  // 生成描述
  const parts: string[] = []
  const visited = new Set<string>()

  const traverse = (nodeId: string, depth: number): string => {
    if (visited.has(nodeId)) return ''
    visited.add(nodeId)

    const node = nodes.value.find(n => n.id === nodeId)
    if (!node) return ''

    const children = adj[nodeId] || []
    if (children.length === 0) {
      return node.name
    } else if (children.length === 1 && children[0]) {
      const childResult = traverse(children[0], depth + 1)
      return childResult ? `${node.name} → ${childResult}` : node.name
    } else if (children.length > 1) {
      // 分叉：并行执行
      const childResults = children.map(c => traverse(c, depth + 1)).filter(Boolean)
      if (childResults.length > 0) {
        return `${node.name} → [${childResults.join(' + ')}]`
      }
      return node.name
    }
    return node.name
  }

  const firstStart = startNodes[0]
  if (startNodes.length === 1 && firstStart) {
    return traverse(firstStart.id, 0)
  } else if (startNodes.length > 1) {
    return startNodes.map(n => traverse(n.id, 0)).join(' | ')
  } else if (nodes.value.length > 0) {
    // 没有明确的起始节点，按顺序列出
    return nodes.value.map(n => n.name).join(' → ')
  }
  return ''
})

// 显示的描述（用户输入优先，否则自动生成）
const displayDescription = computed(() => {
  return workflowDesc.value || autoDescription.value
})

const selectedNode = ref<string | null>(null)
const canvasRef = ref<HTMLElement | null>(null)

// 节点尺寸常量
const NODE_WIDTH = 150
const NODE_HEIGHT = 70

// 拖拽节点状态
const isDraggingNode = ref(false)
const draggedNode = ref<WorkflowNode | null>(null)
const dragOffset = ref({ x: 0, y: 0 })

// 拖拽连线状态
const isDraggingEdge = ref(false)
const edgeFromNode = ref<string | null>(null)
const tempEdge = ref({ x1: 0, y1: 0, x2: 0, y2: 0 })
const hoverTargetNode = ref<string | null>(null)

// 搜索关键词
const searchQuery = ref('')
const isSearching = ref(false)
let searchDebounceTimer: ReturnType<typeof setTimeout> | null = null

// 搜索结果（后端返回）
const searchedSkills = ref<any[]>([])
const searchedWorkflows = ref<any[]>([])

// 搜索前保存的折叠状态
let savedCollapsedSections: Set<string> | null = null

// 监听搜索关键词变化，调用后端搜索
watch(searchQuery, (newQuery) => {
  if (searchDebounceTimer) {
    clearTimeout(searchDebounceTimer)
  }

  if (!newQuery.trim()) {
    // 清空搜索时，恢复之前的折叠状态
    searchedSkills.value = []
    searchedWorkflows.value = []
    if (savedCollapsedSections) {
      collapsedSections.value = new Set(savedCollapsedSections)
      savedCollapsedSections = null
    }
    return
  }

  // 防抖 300ms
  searchDebounceTimer = setTimeout(async () => {
    isSearching.value = true
    try {
      // 保存当前折叠状态（仅第一次搜索时）
      if (!savedCollapsedSections) {
        savedCollapsedSections = new Set(collapsedSections.value)
      }

      const [skillsResult, workflowsResult] = await Promise.all([
        skillsApi.getAll(newQuery),
        workflowsApi.getAll(newQuery)
      ])
      searchedSkills.value = skillsResult
      searchedWorkflows.value = workflowsResult

      // 展开有搜索结果的分组
      const newCollapsed = new Set(collapsedSections.value)
      if (skillsResult.length > 0) {
        newCollapsed.delete('skills')
      }
      if (workflowsResult.length > 0) {
        newCollapsed.delete('workflows')
      }
      collapsedSections.value = newCollapsed
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      isSearching.value = false
    }
  }, 300)
})

// 收藏列表（从后端加载）
const favorites = ref<Set<string>>(new Set())
const favoritesLoading = ref(false)

// 从后端加载收藏列表
const loadFavorites = async () => {
  try {
    favoritesLoading.value = true
    const data = await favoritesApi.getAll()
    const favoriteIds = [
      ...data.skills.map(id => `skill-${id}`),
      ...data.workflows.map(id => `workflow-${id}`)
    ]
    favorites.value = new Set(favoriteIds)
  } catch (error) {
    console.error('Failed to load favorites:', error)
  } finally {
    favoritesLoading.value = false
  }
}

// 切换收藏状态（调用后端 API）
const toggleFavorite = async (itemId: string, event: Event) => {
  event.stopPropagation()

  // 解析 itemId: "skill-xxx" 或 "workflow-xxx"
  const [itemType, ...idParts] = itemId.split('-')
  const realId = idParts.join('-')

  if (itemType !== 'skill' && itemType !== 'workflow') {
    console.error('Invalid item type:', itemType)
    return
  }

  // 乐观更新 UI
  const wasFavorited = favorites.value.has(itemId)
  if (wasFavorited) {
    favorites.value.delete(itemId)
  } else {
    favorites.value.add(itemId)
  }
  favorites.value = new Set(favorites.value)

  // 调用后端 API
  try {
    await favoritesApi.toggle(itemType as 'skill' | 'workflow', realId)
  } catch (error) {
    console.error('Failed to toggle favorite:', error)
    // 回滚 UI
    if (wasFavorited) {
      favorites.value.add(itemId)
    } else {
      favorites.value.delete(itemId)
    }
    favorites.value = new Set(favorites.value)
  }
}

// 数据便签
const dataNotes = ref<DataNote[]>([])
const dataNotesLoading = ref(false)

// 文件类型图标
const dataFileIcons: Record<string, string> = {
  xlsx: '📊', xls: '📊', csv: '📊',
  json: '{ }', pdf: '📄',
  docx: '📝', doc: '📝',
  pptx: '📽', ppt: '📽',
  png: '🖼', jpg: '🖼', jpeg: '🖼', gif: '🖼', svg: '🖼',
  html: '🌐', txt: '📃', md: '📑',
  mp4: '🎬', mp3: '🎵', zip: '📦'
}
const getDataFileIcon = (type: string) => dataFileIcons[type] || '📎'

// 加载收藏的数据便签
const loadDataNotes = async () => {
  try {
    dataNotesLoading.value = true
    dataNotes.value = await dataNotesApi.getAll({ favoritedOnly: true })
    console.log('[WorkflowBuilder] Loaded', dataNotes.value.length, 'favorited data notes')
    dataNotes.value.forEach(n => {
      console.log(`[WorkflowBuilder] DataNote: id=${n.id}, name="${n.name}", file_url=${n.file_url?.substring(0, 50) || 'null'}`)
    })
  } catch (error) {
    console.error('Failed to load data notes:', error)
  } finally {
    dataNotesLoading.value = false
  }
}

// 过滤数据便签
const filteredDataNotes = computed(() => {
  if (!searchQuery.value) return dataNotes.value
  const q = searchQuery.value.toLowerCase()
  return dataNotes.value.filter(n =>
    n.name.toLowerCase().includes(q) ||
    (n.description && n.description.toLowerCase().includes(q))
  )
})

// 打开数据文件
const openDataNote = (note: DataNote) => {
  if (note.file_url) {
    window.open(`${config.serverBaseUrl}${note.file_url}`, '_blank')
  }
}

// 分组折叠状态
const collapsedSections = ref<Set<string>>(new Set())

// 帮助面板显示状态
const showHelpPanel = ref(false)
const showHelpTooltip = ref(false)
const helpWrapperRef = ref<HTMLElement | null>(null)

// 点击外部关闭帮助面板
const handleClickOutside = (e: MouseEvent) => {
  if (showHelpPanel.value && helpWrapperRef.value && !helpWrapperRef.value.contains(e.target as Node)) {
    showHelpPanel.value = false
  }
}

// 监听数据变化
const handleDataNotesChange = () => {
  loadDataNotes()
}

onMounted(() => {
  loadFavorites()
  loadDataNotes()
  document.addEventListener('click', handleClickOutside)
  window.addEventListener('data-notes-changed', handleDataNotesChange)
})

onBeforeUnmount(() => {
  tooltip.value.show = false
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('data-notes-changed', handleDataNotesChange)
})

const toggleSection = (section: string) => {
  if (collapsedSections.value.has(section)) {
    collapsedSections.value.delete(section)
  } else {
    collapsedSections.value.add(section)
  }
  collapsedSections.value = new Set(collapsedSections.value)
}

// 全部展开/折叠
const allSections = ['favorites', 'skills', 'workflows']
const isAllCollapsed = computed(() => {
  return allSections.every(s => collapsedSections.value.has(s))
})
const toggleAllSections = () => {
  if (isAllCollapsed.value) {
    // 全部展开
    collapsedSections.value = new Set()
  } else {
    // 全部折叠
    collapsedSections.value = new Set(allSections)
  }
}

// 大面板展开
const hoverSection = ref<string | null>(null)
const lockedSection = ref<string | null>(null)
const panelTop = ref(0)
let hoverCloseTimer: ReturnType<typeof setTimeout> | null = null

const showGridPanel = computed(() => hoverSection.value || lockedSection.value)
const activeSection = computed(() => lockedSection.value || hoverSection.value)

// 计算面板位置 - 让面板的箭头对准按钮
const updatePanelPosition = (e: MouseEvent) => {
  const btn = e.currentTarget as HTMLElement
  const body = document.querySelector('.body')
  if (btn && body) {
    const btnRect = btn.getBoundingClientRect()
    const bodyRect = body.getBoundingClientRect()
    // 面板顶部位置 = 按钮中心 - 箭头在面板中的位置(20px) - 偏移修正
    const btnCenterY = btnRect.top + btnRect.height / 2 - bodyRect.top
    panelTop.value = Math.max(0, btnCenterY - 80)
  }
}

const onGridBtnEnter = (section: string, e: MouseEvent) => {
  if (hoverCloseTimer) {
    clearTimeout(hoverCloseTimer)
    hoverCloseTimer = null
  }
  if (!lockedSection.value) {
    hoverSection.value = section
    updatePanelPosition(e)
  }
}
const onGridBtnLeave = () => {
  if (!lockedSection.value) {
    // 延迟关闭，给用户时间移动到面板
    hoverCloseTimer = setTimeout(() => {
      hoverSection.value = null
    }, 150)
  }
}
const onPanelEnter = () => {
  if (hoverCloseTimer) {
    clearTimeout(hoverCloseTimer)
    hoverCloseTimer = null
  }
}
const onPanelLeave = () => {
  if (!lockedSection.value) {
    hoverSection.value = null
  }
}
const onGridBtnClick = (section: string, e: MouseEvent) => {
  if (lockedSection.value === section) {
    // 已锁定同一个，解锁
    lockedSection.value = null
    hoverSection.value = null
  } else {
    // 锁定
    lockedSection.value = section
    hoverSection.value = null
    updatePanelPosition(e)
  }
}
const closeGridPanel = () => {
  lockedSection.value = null
  hoverSection.value = null
}

// 获取面板的项目列表
const gridPanelItems = computed(() => {
  switch (activeSection.value) {
    case 'all':
      return [...favoriteItems.value, ...filteredSkills.value, ...filteredWorkflows.value]
    case 'favorites':
      return favoriteItems.value
    case 'skills':
      return filteredSkills.value
    case 'workflows':
      return filteredWorkflows.value
    case 'data':
      return filteredDataNotes.value.map(n => ({
        id: `data-${n.id}`,
        type: 'data' as const,
        name: n.name,
        icon: getDataFileIcon(n.file_type),
        description: n.description,
        dataNote: n
      }))
    default:
      return []
  }
})

const gridPanelTitle = computed(() => {
  switch (activeSection.value) {
    case 'all': return '全部组件'
    case 'favorites': return '⭐ 收藏'
    case 'skills': return 'Skills'
    case 'workflows': return '子流程'
    case 'data': return '数据'
    default: return ''
  }
})

// 可用项目
const availableItems = computed(() => {
  const skillItems = props.skills.map(s => ({
    id: `skill-${s.id}`,
    type: 'skill' as const,
    name: s.name,
    icon: s.icon,
    description: s.description
  }))
  const workflowItems = props.workflows.map(w => ({
    id: `workflow-${w.id}`,
    type: 'workflow' as const,
    name: w.name,
    icon: w.icon,
    description: w.description,
    workflowData: w
  }))
  return [...skillItems, ...workflowItems]
})

// 过滤后的技能列表（后端搜索或 props 数据）
const filteredSkills = computed(() => {
  const query = searchQuery.value.trim()
  if (!query) {
    // 没有搜索时，使用 props 数据
    return availableItems.value.filter(i => i.type === 'skill')
  }
  // 有搜索时，使用后端返回的结果
  return searchedSkills.value.map(s => ({
    id: `skill-${s.id}`,
    type: 'skill' as const,
    name: s.name,
    icon: s.icon,
    description: s.description
  }))
})

// 过滤后的子流程列表（后端搜索或 props 数据）
const filteredWorkflows = computed(() => {
  const query = searchQuery.value.trim()
  if (!query) {
    return availableItems.value.filter(i => i.type === 'workflow')
  }
  return searchedWorkflows.value.map(w => ({
    id: `workflow-${w.id}`,
    type: 'workflow' as const,
    name: w.name,
    icon: w.icon,
    description: w.description,
    workflowData: w
  }))
})

// 收藏的项目列表（收藏使用前端过滤，因为收藏数据在本地）
const favoriteItems = computed(() => {
  // 收藏项不受搜索影响，始终显示所有收藏
  return availableItems.value.filter(i => favorites.value.has(i.id))
})

// 添加节点
const addNode = (item: any, x: number, y: number) => {
  const newNode = {
    id: `node-${Date.now()}`,
    type: item.type,
    name: item.name,
    icon: item.icon,
    description: item.description || '',
    position: { x, y },
    workflowData: item.workflowData,
    dataNote: item.dataNote
  }
  console.log('[addNode] Creating node:', {
    id: newNode.id,
    type: newNode.type,
    name: newNode.name,
    hasDataNote: !!newNode.dataNote,
    dataNote_file_url: newNode.dataNote?.file_url
  })
  nodes.value.push(newNode)
}

// 删除节点
const deleteNode = (nodeId: string) => {
  nodes.value = nodes.value.filter(n => n.id !== nodeId)
  edges.value = edges.value.filter(e => e.from !== nodeId && e.to !== nodeId)
  if (selectedNode.value === nodeId) selectedNode.value = null
}

// 删除连线
const deleteEdge = (edgeId: string) => {
  edges.value = edges.value.filter(e => e.id !== edgeId)
}

// === 节点拖拽 ===
const startDragNode = (e: MouseEvent, node: WorkflowNode) => {
  // 如果点击的是端口，不触发节点拖拽
  if ((e.target as HTMLElement).closest('.port')) return

  e.stopPropagation()
  isDraggingNode.value = true
  draggedNode.value = node
  selectedNode.value = node.id
  tooltip.value.show = false  // 拖拽时隐藏 tooltip
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  dragOffset.value = { x: e.clientX - rect.left, y: e.clientY - rect.top }
}

// === 连线拖拽 ===
const startDragEdge = (e: MouseEvent, nodeId: string) => {
  e.stopPropagation()
  e.preventDefault()
  isDraggingEdge.value = true
  edgeFromNode.value = nodeId
  tooltip.value.show = false  // 拖拽时隐藏 tooltip

  const node = nodes.value.find(n => n.id === nodeId)
  if (node && canvasRef.value) {
    const rect = canvasRef.value.getBoundingClientRect()
    // 从右侧输出端口中心开始
    const x = node.position.x + NODE_WIDTH + 6
    const y = node.position.y + NODE_HEIGHT / 2
    tempEdge.value = { x1: x, y1: y, x2: e.clientX - rect.left, y2: e.clientY - rect.top }
  }
}

// 在输入端口上松开鼠标 - 完成连线
const onInputPortMouseUp = (e: MouseEvent, nodeId: string) => {
  if (isDraggingEdge.value && edgeFromNode.value && edgeFromNode.value !== nodeId) {
    const exists = edges.value.some(e =>
      (e.from === edgeFromNode.value && e.to === nodeId) ||
      (e.from === nodeId && e.to === edgeFromNode.value)
    )
    if (!exists) {
      edges.value.push({
        id: `edge-${Date.now()}`,
        from: edgeFromNode.value,
        to: nodeId
      })
    }
  }
  resetDragState()
}

// 鼠标移动
const onMouseMove = (e: MouseEvent) => {
  if (!canvasRef.value) return
  const rect = canvasRef.value.getBoundingClientRect()
  const mx = e.clientX - rect.left
  const my = e.clientY - rect.top

  // 移动节点
  if (isDraggingNode.value && draggedNode.value) {
    draggedNode.value.position = {
      x: Math.max(0, mx - dragOffset.value.x),
      y: Math.max(0, my - dragOffset.value.y)
    }
  }

  // 拖拽连线
  if (isDraggingEdge.value) {
    tempEdge.value.x2 = mx
    tempEdge.value.y2 = my

    // 检测是否悬停在某个节点的输入端口附近
    hoverTargetNode.value = null
    for (const node of nodes.value) {
      if (node.id === edgeFromNode.value) continue
      // 输入端口位置（节点左侧）
      const portX = node.position.x - 6
      const portY = node.position.y + NODE_HEIGHT / 2
      // 检测距离（40px 范围内）
      const dist = Math.sqrt(Math.pow(mx - portX, 2) + Math.pow(my - portY, 2))
      if (dist < 40) {
        hoverTargetNode.value = node.id
        break
      }
    }
  }
}

// 重置拖拽状态
const resetDragState = () => {
  isDraggingNode.value = false
  draggedNode.value = null
  isDraggingEdge.value = false
  edgeFromNode.value = null
  hoverTargetNode.value = null
}

// 鼠标松开
const onMouseUp = () => {
  // 完成连线（如果在目标节点上松开）
  if (isDraggingEdge.value && edgeFromNode.value && hoverTargetNode.value) {
    const exists = edges.value.some(e =>
      (e.from === edgeFromNode.value && e.to === hoverTargetNode.value) ||
      (e.from === hoverTargetNode.value && e.to === edgeFromNode.value)
    )
    if (!exists) {
      edges.value.push({
        id: `edge-${Date.now()}`,
        from: edgeFromNode.value,
        to: hoverTargetNode.value
      })
    }
  }
  resetDragState()
}

// 获取连线路径（贝塞尔曲线）
const getEdgePath = (edge: WorkflowEdge) => {
  const from = nodes.value.find(n => n.id === edge.from)
  const to = nodes.value.find(n => n.id === edge.to)
  if (!from || !to) return ''

  // 起点：from 节点的右侧输出端口
  const x1 = from.position.x + NODE_WIDTH + 6
  const y1 = from.position.y + NODE_HEIGHT / 2
  // 终点：to 节点的左侧输入端口
  const x2 = to.position.x - 6
  const y2 = to.position.y + NODE_HEIGHT / 2

  // 控制点偏移量
  const dx = Math.abs(x2 - x1)
  const ctrl = Math.max(dx * 0.4, 50)

  return `M ${x1} ${y1} C ${x1 + ctrl} ${y1}, ${x2 - ctrl} ${y2}, ${x2} ${y2}`
}

// 临时连线路径
const getTempEdgePath = () => {
  const { x1, y1, x2, y2 } = tempEdge.value
  const dx = Math.abs(x2 - x1)
  const ctrl = Math.max(dx * 0.3, 30)
  return `M ${x1} ${y1} C ${x1 + ctrl} ${y1}, ${x2 - ctrl} ${y2}, ${x2} ${y2}`
}

// 从侧边栏拖入
const onDrop = (e: DragEvent) => {
  const data = e.dataTransfer?.getData('application/json')
  if (data && canvasRef.value) {
    const item = JSON.parse(data)
    const rect = canvasRef.value.getBoundingClientRect()
    addNode(item, e.clientX - rect.left - 70, e.clientY - rect.top - 35)
  }
}

// 点击添加
const quickAdd = (item: any) => {
  const last = nodes.value[nodes.value.length - 1]
  addNode(item, last ? last.position.x + 180 : 60, last ? last.position.y : 80)
}

// 点击添加数据节点
const quickAddData = (note: DataNote) => {
  console.log('[quickAddData] Adding data node:', {
    name: note.name,
    file_type: note.file_type,
    file_url: note.file_url,
    fullNote: JSON.stringify(note)
  })
  const last = nodes.value[nodes.value.length - 1]
  addNode({
    type: 'data',
    name: note.name,
    icon: getDataFileIcon(note.file_type),
    description: note.description || note.file_type,
    dataNote: note
  }, last ? last.position.x + 180 : 60, last ? last.position.y : 80)
}

// 保存对话框状态
const showSaveDialog = ref(false)
const saveDialogName = ref('')
const saveDialogDesc = ref('')
const saveDialogIcon = ref('🔄')
const saveNameError = ref('')

// 打开保存对话框
const openSaveDialog = () => {
  // 预填充当前值
  saveDialogName.value = workflowName.value.trim()
  saveDialogDesc.value = workflowDesc.value.trim() || autoDescription.value
  saveDialogIcon.value = workflowIcon.value
  saveNameError.value = ''
  showSaveDialog.value = true
}

// 确认保存
const confirmSave = () => {
  // 验证名字
  if (!saveDialogName.value.trim()) {
    saveNameError.value = '请输入工作流名称'
    return
  }

  // 调试：打印保存的节点数据
  console.log('[WorkflowBuilder] Saving nodes:', JSON.stringify(nodes.value, null, 2))
  const dataNodes = nodes.value.filter(n => n.type === 'data')
  console.log('[WorkflowBuilder] Data nodes:', dataNodes.map(n => ({ id: n.id, name: n.name, type: n.type, hasDataNote: !!n.dataNote, file_url: n.dataNote?.file_url })))

  emit('save', {
    id: props.editingWorkflow?.id || `wf-${Date.now()}`,
    name: saveDialogName.value.trim(),
    description: saveDialogDesc.value.trim(),
    icon: saveDialogIcon.value,
    nodes: nodes.value,
    edges: edges.value,
    createdAt: props.editingWorkflow?.createdAt || new Date().toISOString(),
    updatedAt: new Date().toISOString()
  })

  showSaveDialog.value = false
}

// 取消保存
const cancelSave = () => {
  showSaveDialog.value = false
}

// 重新创建（清空当前内容）
const resetWorkflow = () => {
  if (nodes.value.length > 0) {
    if (confirm('确定要放弃当前内容并重新创建吗？')) {
      nodes.value = []
      edges.value = []
      workflowName.value = ''
      workflowDesc.value = ''
      workflowIcon.value = '🔄'
    }
  }
}

// 加载示例
const loadExample = () => {
  nodes.value = [
    { id: 'n1', type: 'skill', name: 'sql-helper', icon: '🗃️', description: '构建SQL查询', position: { x: 50, y: 80 } },
    { id: 'n2', type: 'skill', name: 'data-visualizer', icon: '📊', description: '数据可视化', position: { x: 230, y: 40 } },
    { id: 'n3', type: 'skill', name: 'doc-parser', icon: '📑', description: '解析文档', position: { x: 230, y: 130 } },
    { id: 'n4', type: 'skill', name: 'email-composer', icon: '📧', description: '生成邮件', position: { x: 410, y: 80 } },
  ]
  edges.value = [
    { id: 'e1', from: 'n1', to: 'n2' },
    { id: 'e2', from: 'n1', to: 'n3' },
    { id: 'e3', from: 'n2', to: 'n4' },
    { id: 'e4', from: 'n3', to: 'n4' },
  ]
  workflowName.value = '数据分析报告'
  workflowDesc.value = 'SQL查询 → 可视化+解析 → 邮件发送'
}

const icons = ['🔄', '📊', '🗃️', '📋', '⚡', '🔗', '🤖', '📦', '🎯', '🚀']

// Tooltip 状态
const tooltip = ref<{
  show: boolean
  item: { name: string; icon: string; description: string; type: string } | null
  style: { top: string; left: string }
}>({
  show: false,
  item: null,
  style: { top: '0px', left: '0px' }
})

const handleItemMouseEnter = (e: MouseEvent, item: any) => {
  const target = e.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const tooltipWidth = 200
  const tooltipHeight = 80

  // 固定显示在卡片右侧，不跟随鼠标
  let left = rect.right + 8
  let top = rect.top

  // 如果右侧空间不够，显示在左侧
  if (left + tooltipWidth > window.innerWidth - 10) {
    left = rect.left - tooltipWidth - 8
  }
  // 如果下方空间不够，往上调整
  if (top + tooltipHeight > window.innerHeight - 10) {
    top = window.innerHeight - tooltipHeight - 10
  }

  tooltip.value = {
    show: true,
    item,
    style: { top: `${top}px`, left: `${left}px` }
  }
}

const handleItemMouseLeave = () => {
  tooltip.value.show = false
}

// 关闭所有浮动元素（标签页切换时调用）
const closeAllPopups = () => {
  tooltip.value.show = false
  showGridPanel.value = false
  lockedSection.value = null
  hoverSection.value = null
  showHelpPanel.value = false
  showHelpTooltip.value = false
}

// 暴露方法给父组件
defineExpose({ closeAllPopups })

// 工作区节点的 tooltip（位置固定在节点上方）
const handleNodeMouseEnter = (e: MouseEvent, node: WorkflowNode) => {
  // 拖拽时不显示 tooltip
  if (isDraggingNode.value || isDraggingEdge.value) return

  const target = e.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const tooltipWidth = 220
  const tooltipHeight = 80

  let left = rect.left + rect.width / 2 - tooltipWidth / 2
  let top = rect.top - tooltipHeight - 8

  // 边界检查
  if (left < 10) left = 10
  if (left + tooltipWidth > window.innerWidth - 10) {
    left = window.innerWidth - tooltipWidth - 10
  }
  if (top < 10) {
    top = rect.bottom + 8
  }

  tooltip.value = {
    show: true,
    item: {
      name: node.name,
      icon: node.icon,
      description: node.description,
      type: node.type
    },
    style: { top: `${top}px`, left: `${left}px` }
  }
}

</script>

<template>
  <div class="builder">
    <!-- Header -->
    <header class="header">
      <div class="header-left">
        <button class="back-btn" @click="emit('close')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
        </button>
        <div class="header-title">
          <span class="header-icon">{{ workflowIcon }}</span>
          <span class="header-text">{{ props.editingWorkflow ? '编辑工作流' : '创建工作流' }}</span>
        </div>
      </div>
      <div class="header-right">
        <button class="btn text" @click="loadExample">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
          </svg>
          示例
        </button>
        <button v-if="nodes.length > 0" class="btn text danger" @click="resetWorkflow">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
            <path d="M3 3v5h5"/>
          </svg>
          重新创建
        </button>
        <button class="btn save" @click="openSaveDialog" :disabled="nodes.length === 0">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          保存工作流
        </button>
      </div>
    </header>

    <!-- 保存确认对话框 -->
    <Transition name="dialog">
      <div v-if="showSaveDialog" class="save-dialog-overlay" @click.self="cancelSave">
        <div class="save-dialog">
          <div class="save-dialog-header">
            <h3>保存工作流</h3>
            <button class="close-btn" @click="cancelSave">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <div class="save-dialog-body">
            <!-- 图标选择 -->
            <div class="form-group">
              <label>图标</label>
              <div class="icon-select">
                <button
                  v-for="ic in icons"
                  :key="ic"
                  class="icon-option"
                  :class="{ active: saveDialogIcon === ic }"
                  @click="saveDialogIcon = ic"
                >{{ ic }}</button>
              </div>
            </div>

            <!-- 名称输入 -->
            <div class="form-group">
              <label>名称 <span class="required">*</span></label>
              <input
                v-model="saveDialogName"
                class="form-input"
                :class="{ error: saveNameError }"
                placeholder="请输入工作流名称"
                @input="saveNameError = ''"
              />
              <span v-if="saveNameError" class="error-msg">{{ saveNameError }}</span>
            </div>

            <!-- 描述输入 -->
            <div class="form-group">
              <label>描述 <span class="optional">(可选)</span></label>
              <textarea
                v-model="saveDialogDesc"
                class="form-textarea"
                placeholder="添加工作流描述..."
                rows="3"
              ></textarea>
            </div>

            <!-- 预览 -->
            <div class="save-preview">
              <div class="preview-icon">{{ saveDialogIcon }}</div>
              <div class="preview-info">
                <div class="preview-name">{{ saveDialogName || '未命名工作流' }}</div>
                <div class="preview-meta">{{ nodes.length }} 个步骤</div>
              </div>
            </div>
          </div>

          <div class="save-dialog-footer">
            <button class="btn secondary" @click="cancelSave">取消</button>
            <button class="btn primary" @click="confirmSave">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              确认保存
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 拖拽连线提示 -->
    <div v-if="isDraggingEdge" class="drag-hint" :class="{ 'ready': hoverTargetNode }">
      <template v-if="hoverTargetNode">✓ 松开鼠标完成连接！</template>
      <template v-else>拖到目标节点的左侧端口 ● 建立连接</template>
    </div>

    <div class="body">
      <!-- Sidebar -->
      <aside class="sidebar">
        <!-- 搜索框 -->
        <div class="search-box">
          <svg v-if="!isSearching" class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <path d="m21 21-4.35-4.35"/>
          </svg>
          <div v-else class="search-spinner"></div>
          <input
            v-model="searchQuery"
            type="text"
            class="search-input"
            placeholder="搜索..."
          />
          <button v-if="searchQuery" class="search-clear" @click="searchQuery = ''">×</button>
        </div>

        <!-- 分组容器 -->
        <div class="sections-container">
          <div class="sections-header">
            <span class="sections-label">组件列表</span>
            <button class="toggle-all-btn" @click="toggleAllSections">
              {{ isAllCollapsed ? '展开' : '折叠' }}
            </button>
            <button
              class="grid-btn grid-btn-all"
              :class="{ active: lockedSection === 'all' }"
              @mouseenter="onGridBtnEnter('all', $event)"
              @mouseleave="onGridBtnLeave"
              @click="onGridBtnClick('all', $event)"
              title="查看全部"
            >
              <svg viewBox="0 0 24 24" fill="currentColor">
                <rect x="3" y="3" width="8" height="8" rx="1"/>
                <rect x="13" y="3" width="8" height="8" rx="1"/>
                <rect x="3" y="13" width="8" height="8" rx="1"/>
                <rect x="13" y="13" width="8" height="8" rx="1"/>
              </svg>
            </button>
          </div>
          <div class="sections-body">
        <!-- 收藏分组 -->
        <div v-if="favoriteItems.length > 0" class="section section-favorites">
          <div class="section-title">
            <div class="section-title-left clickable" @click="toggleSection('favorites')">
              <span class="section-toggle" :class="{ collapsed: collapsedSections.has('favorites') }">▼</span>
              <span class="section-label">⭐ 收藏</span>
            </div>
            <span class="section-count">{{ favoriteItems.length }}</span>
            <button
              class="grid-btn"
              :class="{ active: lockedSection === 'favorites' }"
              @mouseenter="onGridBtnEnter('favorites', $event)"
              @mouseleave="onGridBtnLeave"
              @click="onGridBtnClick('favorites', $event)"
            >
              <svg viewBox="0 0 24 24" fill="currentColor">
                <rect x="3" y="3" width="8" height="8" rx="1"/>
                <rect x="13" y="3" width="8" height="8" rx="1"/>
                <rect x="3" y="13" width="8" height="8" rx="1"/>
                <rect x="13" y="13" width="8" height="8" rx="1"/>
              </svg>
            </button>
          </div>
          <Transition name="collapse">
            <div v-show="!collapsedSections.has('favorites')" class="item-list">
              <div
                v-for="item in favoriteItems"
                :key="'fav-' + item.id"
                class="item"
                :class="{ workflow: item.type === 'workflow' }"
                draggable="true"
                @dragstart="e => e.dataTransfer?.setData('application/json', JSON.stringify(item))"
                @click="quickAdd(item)"
                @mouseenter="handleItemMouseEnter($event, item)"
                @mouseleave="handleItemMouseLeave"
              >
                <span class="item-icon">{{ item.icon }}</span>
                <span class="item-name">{{ item.name }}</span>
                <span class="item-fav active" @click="toggleFavorite(item.id, $event)" title="取消收藏">★</span>
                <span class="item-add">+</span>
              </div>
            </div>
          </Transition>
        </div>

        <!-- Skills 分组 -->
        <div class="section section-skills">
          <div class="section-title">
            <div class="section-title-left clickable" @click="toggleSection('skills')">
              <span class="section-toggle" :class="{ collapsed: collapsedSections.has('skills') }">▼</span>
              <span class="section-label">Skills</span>
            </div>
            <span class="section-count">{{ filteredSkills.length }}<template v-if="searchQuery">/{{ skills.length }}</template></span>
            <button
              class="grid-btn"
              :class="{ active: lockedSection === 'skills' }"
              @mouseenter="onGridBtnEnter('skills', $event)"
              @mouseleave="onGridBtnLeave"
              @click="onGridBtnClick('skills', $event)"
            >
              <svg viewBox="0 0 24 24" fill="currentColor">
                <rect x="3" y="3" width="8" height="8" rx="1"/>
                <rect x="13" y="3" width="8" height="8" rx="1"/>
                <rect x="3" y="13" width="8" height="8" rx="1"/>
                <rect x="13" y="13" width="8" height="8" rx="1"/>
              </svg>
            </button>
          </div>
          <Transition name="collapse">
            <div v-show="!collapsedSections.has('skills')" class="item-list">
              <div
                v-for="item in filteredSkills"
                :key="item.id"
                class="item"
                draggable="true"
                @dragstart="e => e.dataTransfer?.setData('application/json', JSON.stringify(item))"
                @click="quickAdd(item)"
                @mouseenter="handleItemMouseEnter($event, item)"
                @mouseleave="handleItemMouseLeave"
              >
                <span class="item-icon">{{ item.icon }}</span>
                <span class="item-name">{{ item.name }}</span>
                <span
                  class="item-fav"
                  :class="{ active: favorites.has(item.id) }"
                  @click="toggleFavorite(item.id, $event)"
                  :title="favorites.has(item.id) ? '取消收藏' : '添加收藏'"
                >{{ favorites.has(item.id) ? '★' : '☆' }}</span>
                <span class="item-add">+</span>
              </div>
              <div v-if="filteredSkills.length === 0 && searchQuery" class="no-results">
                未找到匹配的技能
              </div>
            </div>
          </Transition>
        </div>

        <!-- 子流程分组 -->
        <div v-if="workflows.length" class="section section-workflows">
          <div class="section-title">
            <div class="section-title-left clickable" @click="toggleSection('workflows')">
              <span class="section-toggle" :class="{ collapsed: collapsedSections.has('workflows') }">▼</span>
              <span class="section-label">子流程</span>
            </div>
            <span class="section-count">{{ filteredWorkflows.length }}<template v-if="searchQuery">/{{ workflows.length }}</template></span>
            <button
              class="grid-btn"
              :class="{ active: lockedSection === 'workflows' }"
              @mouseenter="onGridBtnEnter('workflows', $event)"
              @mouseleave="onGridBtnLeave"
              @click="onGridBtnClick('workflows', $event)"
            >
              <svg viewBox="0 0 24 24" fill="currentColor">
                <rect x="3" y="3" width="8" height="8" rx="1"/>
                <rect x="13" y="3" width="8" height="8" rx="1"/>
                <rect x="3" y="13" width="8" height="8" rx="1"/>
                <rect x="13" y="13" width="8" height="8" rx="1"/>
              </svg>
            </button>
          </div>
          <Transition name="collapse">
            <div v-show="!collapsedSections.has('workflows')" class="item-list">
              <div
                v-for="item in filteredWorkflows"
                :key="item.id"
                class="item workflow"
                draggable="true"
                @dragstart="e => e.dataTransfer?.setData('application/json', JSON.stringify(item))"
                @click="quickAdd(item)"
                @mouseenter="handleItemMouseEnter($event, item)"
                @mouseleave="handleItemMouseLeave"
              >
                <span class="item-icon">{{ item.icon }}</span>
                <span class="item-name">{{ item.name }}</span>
                <span
                  class="item-fav"
                  :class="{ active: favorites.has(item.id) }"
                  @click="toggleFavorite(item.id, $event)"
                  :title="favorites.has(item.id) ? '取消收藏' : '添加收藏'"
                >{{ favorites.has(item.id) ? '★' : '☆' }}</span>
                <span class="item-add">+</span>
              </div>
              <div v-if="filteredWorkflows.length === 0 && searchQuery" class="no-results">
                未找到匹配的子流程
              </div>
            </div>
          </Transition>
        </div>

        <!-- 数据分组 -->
        <div v-if="dataNotes.length > 0" class="section section-data">
          <div class="section-title">
            <div class="section-title-left clickable" @click="toggleSection('data')">
              <span class="section-toggle" :class="{ collapsed: collapsedSections.has('data') }">▼</span>
              <span class="section-label">数据</span>
            </div>
            <span class="section-count">{{ filteredDataNotes.length }}<template v-if="searchQuery">/{{ dataNotes.length }}</template></span>
            <button
              class="grid-btn"
              :class="{ active: lockedSection === 'data' }"
              @mouseenter="onGridBtnEnter('data', $event)"
              @mouseleave="onGridBtnLeave"
              @click="onGridBtnClick('data', $event)"
            >
              <svg viewBox="0 0 24 24" fill="currentColor">
                <rect x="3" y="3" width="8" height="8" rx="1"/>
                <rect x="13" y="3" width="8" height="8" rx="1"/>
                <rect x="3" y="13" width="8" height="8" rx="1"/>
                <rect x="13" y="13" width="8" height="8" rx="1"/>
              </svg>
            </button>
          </div>
          <Transition name="collapse">
            <div v-show="!collapsedSections.has('data')" class="item-list">
              <div
                v-for="note in filteredDataNotes"
                :key="note.id"
                class="item data-item"
                draggable="true"
                @dragstart="e => e.dataTransfer?.setData('application/json', JSON.stringify({ type: 'data', name: note.name, icon: getDataFileIcon(note.file_type), description: note.description || note.file_type, dataNote: note }))"
                @click="quickAddData(note)"
              >
                <span class="item-icon">{{ getDataFileIcon(note.file_type) }}</span>
                <span class="item-name">{{ note.name }}</span>
                <span class="item-add">+</span>
              </div>
              <div v-if="filteredDataNotes.length === 0 && searchQuery" class="no-results">
                未找到匹配的数据
              </div>
            </div>
          </Transition>
        </div>
        </div>
      </div>
      </aside>

      <!-- 大网格面板 - 覆盖在画布上 -->
      <Transition name="grid-panel">
        <div
          v-if="showGridPanel"
          class="grid-panel"
          :style="{ top: panelTop + 'px' }"
          @mouseenter="onPanelEnter"
          @mouseleave="onPanelLeave"
        >
          <div class="grid-panel-arrow"></div>
          <!-- 单个分组 -->
          <template v-if="activeSection !== 'all'">
            <div class="grid-panel-grid">
              <div
                v-for="item in gridPanelItems"
                :key="'grid-' + item.id"
                class="grid-item"
                :class="{ workflow: item.type === 'workflow', data: item.type === 'data' }"
                draggable="true"
                @dragstart="e => { e.dataTransfer?.setData('application/json', JSON.stringify(item)); closeGridPanel() }"
                @click="item.type === 'data' ? (quickAddData(item.dataNote), closeGridPanel()) : (quickAdd(item), closeGridPanel())"
                @mouseenter="handleItemMouseEnter($event, item)"
                @mouseleave="handleItemMouseLeave"
              >
                <span
                  v-if="activeSection !== 'favorites' && activeSection !== 'data'"
                  class="grid-item-fav"
                  :class="{ active: favorites.has(item.id) }"
                  @click.stop="toggleFavorite(item.id, $event)"
                >{{ favorites.has(item.id) ? '★' : '☆' }}</span>
                <span class="grid-item-icon">{{ item.icon }}</span>
                <span class="grid-item-name">{{ item.name }}</span>
              </div>
            </div>
            <div v-if="gridPanelItems.length === 0" class="grid-panel-empty">暂无内容</div>
          </template>

          <!-- 全部分组 -->
          <template v-else>
            <!-- 收藏 -->
            <div v-if="favoriteItems.length > 0" class="grid-section">
              <div class="grid-section-title">⭐ 收藏</div>
              <div class="grid-panel-grid">
                <div
                  v-for="item in favoriteItems"
                  :key="'grid-fav-' + item.id"
                  class="grid-item"
                  :class="{ workflow: item.type === 'workflow' }"
                  draggable="true"
                  @dragstart="e => { e.dataTransfer?.setData('application/json', JSON.stringify(item)); closeGridPanel() }"
                  @click="quickAdd(item); closeGridPanel()"
                  @mouseenter="handleItemMouseEnter($event, item)"
                  @mouseleave="handleItemMouseLeave"
                >
                  <span class="grid-item-icon">{{ item.icon }}</span>
                  <span class="grid-item-name">{{ item.name }}</span>
                </div>
              </div>
            </div>

            <!-- Skills -->
            <div v-if="filteredSkills.length > 0" class="grid-section">
              <div class="grid-section-title">Skills</div>
              <div class="grid-panel-grid">
                <div
                  v-for="item in filteredSkills"
                  :key="'grid-skill-' + item.id"
                  class="grid-item"
                  draggable="true"
                  @dragstart="e => { e.dataTransfer?.setData('application/json', JSON.stringify(item)); closeGridPanel() }"
                  @click="quickAdd(item); closeGridPanel()"
                  @mouseenter="handleItemMouseEnter($event, item)"
                  @mouseleave="handleItemMouseLeave"
                >
                  <span
                    class="grid-item-fav"
                    :class="{ active: favorites.has(item.id) }"
                    @click.stop="toggleFavorite(item.id, $event)"
                  >{{ favorites.has(item.id) ? '★' : '☆' }}</span>
                  <span class="grid-item-icon">{{ item.icon }}</span>
                  <span class="grid-item-name">{{ item.name }}</span>
                </div>
              </div>
            </div>

            <!-- 子流程 -->
            <div v-if="filteredWorkflows.length > 0" class="grid-section">
              <div class="grid-section-title">子流程</div>
              <div class="grid-panel-grid">
                <div
                  v-for="item in filteredWorkflows"
                  :key="'grid-wf-' + item.id"
                  class="grid-item workflow"
                  draggable="true"
                  @dragstart="e => { e.dataTransfer?.setData('application/json', JSON.stringify(item)); closeGridPanel() }"
                  @click="quickAdd(item); closeGridPanel()"
                  @mouseenter="handleItemMouseEnter($event, item)"
                  @mouseleave="handleItemMouseLeave"
                >
                  <span
                    class="grid-item-fav"
                    :class="{ active: favorites.has(item.id) }"
                    @click.stop="toggleFavorite(item.id, $event)"
                  >{{ favorites.has(item.id) ? '★' : '☆' }}</span>
                  <span class="grid-item-icon">{{ item.icon }}</span>
                  <span class="grid-item-name">{{ item.name }}</span>
                </div>
              </div>
            </div>

            <!-- 数据 -->
            <div v-if="filteredDataNotes.length > 0" class="grid-section">
              <div class="grid-section-title">数据</div>
              <div class="grid-panel-grid">
                <div
                  v-for="note in filteredDataNotes"
                  :key="'grid-data-' + note.id"
                  class="grid-item data"
                  draggable="true"
                  @dragstart="e => { e.dataTransfer?.setData('application/json', JSON.stringify({ type: 'data', name: note.name, icon: getDataFileIcon(note.file_type), description: note.description || note.file_type, dataNote: note })); closeGridPanel() }"
                  @click="quickAddData(note); closeGridPanel()"
                >
                  <span class="grid-item-icon">{{ getDataFileIcon(note.file_type) }}</span>
                  <span class="grid-item-name">{{ note.name }}</span>
                </div>
              </div>
            </div>
          </template>

          <button v-if="lockedSection" class="grid-panel-close" @click="closeGridPanel">×</button>
        </div>
      </Transition>

      <!-- Canvas -->
      <div
        ref="canvasRef"
        class="canvas"
        :class="{ 'dragging-edge': isDraggingEdge }"
        @mousemove="onMouseMove"
        @mouseup="onMouseUp"
        @mouseleave="onMouseUp"
        @dragover.prevent
        @drop="onDrop"
        @click="selectedNode = null"
      >
        <div class="grid"></div>

        <!-- Edges SVG -->
        <svg class="edges">
          <defs>
            <!-- 渐变 -->
            <linearGradient id="edgeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#6366f1" />
              <stop offset="100%" stop-color="#8b5cf6" />
            </linearGradient>
            <linearGradient id="edgeGradientHover" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#ef4444" />
              <stop offset="100%" stop-color="#f97316" />
            </linearGradient>
            <!-- 箭头 -->
            <marker id="arrow" markerWidth="12" markerHeight="10" refX="10" refY="5" orient="auto">
              <path d="M0 0 L12 5 L0 10 L3 5 Z" fill="#6366f1" />
            </marker>
            <marker id="arrow-hover" markerWidth="12" markerHeight="10" refX="10" refY="5" orient="auto">
              <path d="M0 0 L12 5 L0 10 L3 5 Z" fill="#ef4444" />
            </marker>
            <marker id="arrow-temp" markerWidth="10" markerHeight="8" refX="8" refY="4" orient="auto">
              <path d="M0 0 L10 4 L0 8 L2 4 Z" fill="#10b981" />
            </marker>
            <!-- 发光效果 -->
            <filter id="glow">
              <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>

          <!-- 已有连线（底层阴影） -->
          <path
            v-for="edge in edges"
            :key="edge.id + '-shadow'"
            :d="getEdgePath(edge)"
            class="edge-shadow"
          />

          <!-- 已有连线 -->
          <g v-for="edge in edges" :key="edge.id" class="edge-group" @click.stop="deleteEdge(edge.id)">
            <path :d="getEdgePath(edge)" class="edge-hitarea" />
            <path :d="getEdgePath(edge)" class="edge" />
          </g>

          <!-- 临时连线 -->
          <g v-if="isDraggingEdge">
            <path :d="getTempEdgePath()" class="edge temp-shadow" />
            <path :d="getTempEdgePath()" class="edge temp" />
          </g>
        </svg>

        <!-- Nodes -->
        <div
          v-for="node in nodes"
          :key="node.id"
          class="node"
          :class="{
            selected: selectedNode === node.id,
            'is-workflow': node.type === 'workflow',
            'is-data': node.type === 'data',
            'drop-target': hoverTargetNode === node.id,
            'is-source': edgeFromNode === node.id
          }"
          :style="{ left: node.position.x + 'px', top: node.position.y + 'px' }"
          @mousedown="startDragNode($event, node)"
          @click.stop="selectedNode = node.id"
          @mouseenter="handleNodeMouseEnter($event, node)"
          @mouseleave="handleItemMouseLeave"
        >
          <!-- 输入端口（左侧）- 数据节点不需要输入端口 -->
          <div
            v-if="node.type !== 'data'"
            class="port input"
            :class="{ 'port-active': isDraggingEdge && edgeFromNode !== node.id }"
            @mouseup="onInputPortMouseUp($event, node.id)"
          >
            <div class="port-ring"></div>
          </div>

          <div class="node-icon">{{ node.icon }}</div>
          <div class="node-info">
            <div class="node-name">{{ node.name }}</div>
            <div class="node-type">{{ node.type === 'workflow' ? '子流程' : node.type === 'data' ? '数据源' : 'Skill' }}</div>
          </div>

          <!-- 输出端口（右侧）- 拖拽建立连线 -->
          <div
            class="port output"
            @mousedown="startDragEdge($event, node.id)"
            title="从这里拖出连线"
          >
            <div class="port-ring"></div>
            <svg class="port-arrow" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8 5v14l11-7z"/>
            </svg>
          </div>

          <!-- 删除按钮 -->
          <button class="delete-btn" @click.stop="deleteNode(node.id)">×</button>
        </div>

        <!-- 帮助按钮 - 右下角悬浮 -->
        <div class="help-fab" ref="helpWrapperRef">
          <button
            class="help-fab-btn"
            @click.stop="showHelpPanel = !showHelpPanel"
            :class="{ active: showHelpPanel }"
            @mouseenter="showHelpTooltip = true"
            @mouseleave="showHelpTooltip = false"
          >
            <span class="help-fab-icon">?</span>
          </button>
          <!-- 悬停提示 -->
          <Transition name="help-tip">
            <div v-if="showHelpTooltip && !showHelpPanel" class="help-fab-tooltip">
              操作指南
            </div>
          </Transition>
          <!-- 展开的帮助面板 -->
          <Transition name="help-panel">
            <div v-if="showHelpPanel" class="help-fab-panel">
              <div class="help-fab-panel-header">
                <span>操作指南</span>
                <button class="help-fab-close" @click="showHelpPanel = false">×</button>
              </div>
              <ul>
                <li>
                  <span class="help-step">1</span>
                  <div class="help-content">
                    <strong>添加节点</strong>
                    <p>点击左侧列表或拖拽到画布</p>
                  </div>
                </li>
                <li>
                  <span class="help-step">2</span>
                  <div class="help-content">
                    <strong>连接节点</strong>
                    <p>从右侧 <b class="port-out">●→</b> 拖到左侧 <b class="port-in">●</b></p>
                  </div>
                </li>
                <li>
                  <span class="help-step">3</span>
                  <div class="help-content">
                    <strong>删除连线</strong>
                    <p>点击连线即可删除</p>
                  </div>
                </li>
              </ul>
            </div>
          </Transition>
        </div>

        <!-- Empty -->
        <div v-if="nodes.length === 0" class="empty">
          <div class="empty-icon">🔄</div>
          <h3>开始构建流程</h3>
          <p>点击左侧添加节点</p>
          <p class="sub-hint">从右侧 <span class="port-demo">●→</span> 拖拽到左侧 <span class="port-demo in">●</span> 建立连接</p>
          <button @click="loadExample">加载示例</button>
        </div>
      </div>
    </div>

    <!-- Footer - 显示自动生成的流程描述 -->
    <footer class="footer">
      <div class="footer-flow">
        <span class="flow-label">流程：</span>
        <span class="flow-desc">{{ autoDescription || '添加节点开始构建流程...' }}</span>
      </div>
      <div class="stats">{{ nodes.length }} 节点 · {{ edges.length }} 连接</div>
    </footer>

    <!-- Skill/Workflow Tooltip -->
    <Teleport to="body">
      <Transition name="tooltip">
        <div v-if="tooltip.show && tooltip.item" class="builder-tooltip" :style="tooltip.style">
          <div class="builder-tooltip-header">
            <span class="builder-tooltip-icon">{{ tooltip.item.icon }}</span>
            <span class="builder-tooltip-name">{{ tooltip.item.name }}</span>
            <span class="builder-tooltip-type">{{ tooltip.item.type === 'workflow' ? '子流程' : 'Skill' }}</span>
          </div>
          <p class="builder-tooltip-desc">{{ tooltip.item.description || '暂无描述' }}</p>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.builder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
  border-radius: 12px;
  overflow: hidden;
}

/* Header */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
}
.header-left, .header-right { display: flex; align-items: center; gap: 6px; }

.back-btn {
  width: 26px; height: 26px;
  background: #f1f5f9; border: none; border-radius: 6px;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  color: #64748b; transition: all 0.15s;
}
.back-btn:hover { background: #e2e8f0; color: #1e293b; }
.back-btn svg { width: 14px; height: 14px; }

/* Header 标题 */
.header-title {
  display: flex;
  align-items: center;
  gap: 6px;
}

.header-icon {
  width: 26px;
  height: 26px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  box-shadow: 0 2px 6px rgba(99, 102, 241, 0.25);
}

.header-text {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}

.btn {
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  gap: 4px;
  border: none;
}

.btn svg {
  width: 12px;
  height: 12px;
}

.btn.text {
  background: transparent;
  color: #64748b;
}

.btn.text:hover {
  background: #f1f5f9;
  color: #475569;
}

.btn.text.danger {
  color: #94a3b8;
}

.btn.text.danger:hover {
  background: #fef2f2;
  color: #ef4444;
}

.btn.secondary {
  background: #f1f5f9;
  color: #64748b;
}

.btn.secondary:hover {
  background: #e2e8f0;
  color: #475569;
}

.btn.save {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

.btn.save:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.4);
}

.btn.save:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
}

.btn.primary {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
}

.btn.primary:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

/* Drag hint */
.drag-hint {
  padding: 10px 16px;
  text-align: center;
  background: linear-gradient(90deg, #e0e7ff, #dbeafe);
  border-bottom: 2px solid #6366f1;
  font-size: 12px;
  font-weight: 600;
  color: #4338ca;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  animation: hintPulse 1.5s ease infinite;
}
.drag-hint::before {
  content: '🔗';
  font-size: 14px;
}
.drag-hint.ready {
  background: linear-gradient(90deg, #dcfce7, #bbf7d0);
  border-bottom-color: #10b981;
  color: #047857;
  animation: none;
}
.drag-hint.ready::before {
  content: '✨';
}

@keyframes hintPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.85; }
}

/* Body */
.body { flex: 1; display: flex; overflow: hidden; position: relative; }

/* Sidebar */
.sidebar {
  width: 180px;
  background: #fff;
  border-right: 1px solid #e5e7eb;
  padding: 10px 10px 10px 8px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0;
  position: relative;
}

/* 搜索框 */
.search-box {
  position: relative;
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

/* 分组容器 */
.sections-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
  min-height: 0;
}

.sections-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.sections-label {
  flex: 1;
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
}

.toggle-all-btn {
  padding: 2px 8px;
  border: none;
  background: transparent;
  border-radius: 3px;
  cursor: pointer;
  font-size: 10px;
  color: #6366f1;
  transition: all 0.15s;
}
.toggle-all-btn:hover {
  background: #eef2ff;
}

.sections-body {
  flex: 1;
  overflow-y: auto;
  padding: 6px 0 6px 6px; /* 右边无padding，让grid-btn与header对齐 */
}

/* 大网格面板 - 覆盖画布 */
.grid-panel {
  position: absolute;
  top: 0;
  left: 182px;
  background: #fff;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  box-shadow: 4px 4px 24px rgba(0,0,0,0.18);
  z-index: 50;
  padding: 14px;
  display: inline-block;
}

/* 箭头指向 */
.grid-panel-arrow {
  position: absolute;
  left: -7px;
  top: 12px;
  width: 0;
  height: 0;
  border-top: 8px solid transparent;
  border-bottom: 8px solid transparent;
  border-right: 7px solid #d1d5db;
}
.grid-panel-arrow::after {
  content: '';
  position: absolute;
  left: 2px;
  top: -7px;
  width: 0;
  height: 0;
  border-top: 7px solid transparent;
  border-bottom: 7px solid transparent;
  border-right: 6px solid #fff;
}

.grid-panel-close {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 16px;
  height: 16px;
  border: none;
  background: #ef4444;
  border-radius: 50%;
  color: #fff;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(239,68,68,0.3);
  transition: transform 0.15s;
}
.grid-panel-close:hover {
  transform: scale(1.1);
}

.grid-panel-grid {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 8px;
  max-width: calc(100px * 5 + 8px * 4); /* 最多5列，更扁平 */
}

.grid-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  width: 100px;
  height: 60px;
  flex-shrink: 0;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.15s;
}
.grid-item:hover {
  background: #fff;
  border-color: #6366f1;
  box-shadow: 0 2px 8px rgba(99,102,241,0.15);
}
.grid-item.workflow {
  background: #faf5ff;
  border-color: #e9d5ff;
}
.grid-item.workflow:hover {
  border-color: #a78bfa;
}
.grid-item.data {
  background: #fffbeb;
  border-color: #fde68a;
}
.grid-item.data:hover {
  border-color: #f59e0b;
}
.grid-item-fav {
  position: absolute;
  top: 3px;
  left: 3px;
  font-size: 14px;
  color: #9ca3af;
  cursor: pointer;
  transition: all 0.15s;
  line-height: 1;
  z-index: 1;
}
.grid-item-fav:hover {
  color: #f59e0b;
  transform: scale(1.15);
}
.grid-item-fav.active {
  color: #d97706;
}

.grid-item-icon {
  font-size: 22px;
  line-height: 1;
}

.grid-item-name {
  font-size: 11px;
  font-weight: 500;
  color: #374151;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
  padding: 0 6px;
  line-height: 1.1;
}

.grid-panel-empty {
  text-align: center;
  padding: 15px;
  color: #9ca3af;
  font-size: 10px;
}

/* 分组分隔 */
.grid-section {
  padding-bottom: 8px;
  margin-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}
.grid-section:last-child {
  padding-bottom: 0;
  margin-bottom: 0;
  border-bottom: none;
}

.grid-section-title {
  font-size: 10px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

/* 网格面板动画 */
.grid-panel-enter-active,
.grid-panel-leave-active {
  transition: all 0.15s ease;
}
.grid-panel-enter-from,
.grid-panel-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
.search-icon {
  position: absolute;
  left: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 12px;
  height: 12px;
  color: #9ca3af;
  pointer-events: none;
}
.search-spinner {
  position: absolute;
  left: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 12px;
  height: 12px;
  border: 1.5px solid #e5e7eb;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.search-input {
  width: 100%;
  padding: 6px 22px 6px 26px;
  border: 1px solid #e5e7eb;
  border-radius: 5px;
  font-size: 11px;
  outline: none;
  background: #f9fafb;
  transition: border-color 0.15s, background 0.15s;
  height: 28px;
  box-sizing: border-box;
}
.search-input:focus {
  border-color: #a5b4fc;
  background: #fff;
}
.search-input::placeholder {
  color: #9ca3af;
}
.search-clear {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  border: none;
  background: #e5e7eb;
  border-radius: 50%;
  font-size: 11px;
  line-height: 1;
  color: #6b7280;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.search-clear:hover {
  background: #d1d5db;
  color: #374151;
}
.no-results {
  padding: 8px;
  text-align: center;
  font-size: 11px;
  color: #9ca3af;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.section + .section {
  margin-top: 6px;
}
.section-title {
  font-size: 11px;
  font-weight: 600;
  color: #374151;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 8px;
  border-radius: 4px;
  background: #e5e7eb;
}
.section-title-left {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}
.section-title-left.clickable {
  cursor: pointer;
  user-select: none;
  padding: 2px 4px;
  margin: -2px -4px;
  border-radius: 3px;
  transition: background 0.15s;
}
.section-title-left.clickable:hover { background: rgba(0,0,0,0.08); }

.section-count {
  font-size: 10px;
  color: #4b5563;
  font-weight: 600;
  background: #fff;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 20px;
  text-align: center;
}

/* 四格按钮 */
.grid-btn {
  width: 22px;
  height: 22px;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  transition: all 0.15s;
  flex-shrink: 0;
}
.grid-btn:hover {
  color: #6366f1;
  background: #eef2ff;
}
.grid-btn.active {
  color: #6366f1;
  background: #e0e7ff;
}
.grid-btn svg {
  width: 14px;
  height: 14px;
}
.section-label { flex: 1; }

.section-toggle {
  font-size: 8px;
  margin-right: 6px;
  transition: transform 0.2s;
  display: inline-block;
  color: #9ca3af;
}
.section-toggle.collapsed { transform: rotate(-90deg); }

/* 折叠动画 */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.15s ease;
  overflow: hidden;
}
.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
}
.collapse-enter-to,
.collapse-leave-from {
  opacity: 1;
  max-height: 400px;
}

.item-list { display: flex; flex-direction: column; gap: 1px; margin-top: 4px; }
.item {
  display: flex; align-items: center; gap: 6px;
  padding: 5px 6px; background: transparent;
  border-radius: 3px; cursor: pointer; transition: all 0.15s;
}
.item:hover { background: #f3f4f6; }
.item:hover .item-add { opacity: 1; }
.item-icon { font-size: 12px; }
.item-name { flex: 1; font-size: 11px; font-weight: 500; color: #374151; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.item-fav {
  font-size: 11px;
  color: #9ca3af;
  cursor: pointer;
  transition: color 0.15s;
}
.item-fav:hover { color: #fbbf24; }
.item-fav.active { color: #f59e0b; }
.item-add { font-size: 10px; font-weight: 500; color: #9ca3af; opacity: 0; transition: opacity 0.15s; }
.item-meta { font-size: 9px; color: #9ca3af; margin-left: 4px; }
.data-item { background: #fffef8; border-color: #e8e4d0; }
.data-item:hover { background: #fff9e6; border-color: #d4c99e; }

/* 帮助悬浮按钮 - 右下角 */
.help-fab {
  position: absolute;
  right: 16px;
  bottom: 16px;
  z-index: 100;
}

.help-fab-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #fff;
  border: 1px solid #e5e7eb;
  color: #6b7280;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease;
}

.help-fab-btn:hover {
  background: #f9fafb;
  border-color: #6366f1;
  color: #6366f1;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
}

.help-fab-btn.active {
  background: #6366f1;
  border-color: #6366f1;
  color: #fff;
}

.help-fab-icon {
  transition: transform 0.2s ease;
}

.help-fab-btn.active .help-fab-icon {
  transform: rotate(45deg);
}

/* 悬停提示 */
.help-fab-tooltip {
  position: absolute;
  right: 40px;
  top: 50%;
  transform: translateY(-50%);
  background: #374151;
  color: #fff;
  font-size: 11px;
  padding: 5px 8px;
  border-radius: 4px;
  white-space: nowrap;
  pointer-events: none;
}

.help-fab-tooltip::after {
  content: '';
  position: absolute;
  left: 100%;
  top: 50%;
  transform: translateY(-50%);
  border: 4px solid transparent;
  border-left-color: #374151;
}

/* 帮助面板 */
.help-fab-panel {
  position: absolute;
  right: 0;
  bottom: 40px;
  width: 220px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.help-fab-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  color: #374151;
  font-size: 12px;
  font-weight: 600;
}

.help-fab-close {
  width: 18px;
  height: 18px;
  border: none;
  background: transparent;
  border-radius: 3px;
  color: #9ca3af;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.help-fab-close:hover {
  background: #e5e7eb;
  color: #374151;
}

.help-fab-panel ul {
  list-style: none;
  padding: 6px 0;
  margin: 0;
}

.help-fab-panel li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 6px 10px;
}

.help-step {
  width: 18px;
  height: 18px;
  background: #f3f4f6;
  color: #6b7280;
  border-radius: 50%;
  font-size: 10px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.help-content {
  flex: 1;
}

.help-content strong {
  display: block;
  font-size: 11px;
  color: #374151;
  font-weight: 600;
}

.help-content p {
  margin: 2px 0 0;
  font-size: 10px;
  color: #6b7280;
  line-height: 1.3;
}

.help-content .port-out {
  color: #6366f1;
  font-weight: 600;
}

.help-content .port-in {
  color: #10b981;
  font-weight: 600;
}

/* 帮助面板动画 */
.help-panel-enter-active,
.help-panel-leave-active {
  transition: all 0.15s ease;
}
.help-panel-enter-from,
.help-panel-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

/* tooltip 动画 */
.help-tip-enter-active,
.help-tip-leave-active {
  transition: all 0.1s ease;
}
.help-tip-enter-from,
.help-tip-leave-to {
  opacity: 0;
}

/* Canvas */
.canvas {
  flex: 1; position: relative; overflow: hidden;
}
.canvas.dragging-edge { cursor: crosshair; }

.grid {
  position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(0,0,0,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,0,0,0.03) 1px, transparent 1px);
  background-size: 20px 20px;
}

/* Edges */
.edges { position: absolute; inset: 0; pointer-events: none; overflow: visible; }

.edge-shadow {
  fill: none;
  stroke: rgba(99, 102, 241, 0.15);
  stroke-width: 8;
  stroke-linecap: round;
}

.edge-group { cursor: pointer; }
.edge-hitarea {
  fill: none;
  stroke: transparent;
  stroke-width: 20;
  pointer-events: stroke;
}

.edge {
  fill: none;
  stroke: url(#edgeGradient);
  stroke-width: 3;
  stroke-linecap: round;
  marker-end: url(#arrow);
  transition: all 0.2s ease;
  pointer-events: none;
}

.edge-group:hover .edge {
  stroke: url(#edgeGradientHover);
  stroke-width: 4;
  marker-end: url(#arrow-hover);
  filter: url(#glow);
}

.edge-group:hover .edge-shadow {
  stroke: rgba(239, 68, 68, 0.2);
}

.edge.temp-shadow {
  stroke: rgba(16, 185, 129, 0.2);
  stroke-width: 10;
  stroke-dasharray: none;
  marker-end: none;
}

.edge.temp {
  stroke: #10b981;
  stroke-width: 3;
  stroke-dasharray: 8 4;
  marker-end: url(#arrow-temp);
  animation: dashMove 0.5s linear infinite;
}

@keyframes dashMove {
  to { stroke-dashoffset: -12; }
}

/* Nodes */
.node {
  position: absolute; width: 150px; height: 70px;
  background: #fff; border: 2px solid #e2e8f0; border-radius: 12px;
  display: flex; align-items: center; gap: 8px; padding: 0 12px;
  cursor: grab; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  transition: all 0.2s ease; user-select: none;
}
.node:hover { border-color: #cbd5e1; box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
.node.selected { border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99,102,241,0.2); }
.node.is-workflow { background: rgba(99,102,241,0.04); border-color: rgba(99,102,241,0.4); }
.node.is-data { background: rgba(245,158,11,0.06); border-color: rgba(245,158,11,0.5); }
.node.drop-target {
  border-color: #10b981;
  box-shadow: 0 0 0 4px rgba(16,185,129,0.25), 0 4px 20px rgba(16,185,129,0.2);
  transform: scale(1.02);
}
.node.is-source {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.2);
}

.node-icon {
  width: 36px; height: 36px;
  background: #f8fafc; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; flex-shrink: 0;
}
.node.is-workflow .node-icon { background: linear-gradient(135deg, #6366f1, #8b5cf6); }
.node.is-data .node-icon { background: linear-gradient(135deg, #f59e0b, #d97706); }

.node-info { flex: 1; overflow: hidden; }
.node-name { font-size: 12px; font-weight: 600; color: #1e293b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.node-type { font-size: 9px; color: #94a3b8; margin-top: 2px; }

/* Ports */
.port {
  position: absolute;
  width: 16px; height: 16px;
  display: flex; align-items: center; justify-content: center;
  z-index: 10;
  transition: all 0.2s ease;
}

.port-ring {
  width: 12px; height: 12px;
  background: #fff;
  border: 2px solid #cbd5e1;
  border-radius: 50%;
  transition: all 0.2s ease;
}

/* 输入端口（左侧） */
.port.input {
  left: -8px; top: 50%; transform: translateY(-50%);
  cursor: default;
}

.port.input .port-ring {
  width: 10px; height: 10px;
  background: #f1f5f9;
  border-color: #94a3b8;
}

.port.input.port-active .port-ring {
  width: 18px; height: 18px;
  background: #dcfce7;
  border-color: #10b981;
  border-width: 3px;
  animation: portPulse 1s ease infinite;
}

.node.drop-target .port.input .port-ring {
  width: 20px; height: 20px;
  background: #10b981;
  border-color: #10b981;
}

/* 输出端口（右侧） */
.port.output {
  right: -8px; top: 50%; transform: translateY(-50%);
  width: 28px; height: 28px;
  cursor: crosshair;
}

.port.output .port-ring {
  width: 20px; height: 20px;
  background: linear-gradient(135deg, #f8fafc, #fff);
  border: 2px solid #6366f1;
  box-shadow: 0 2px 6px rgba(99, 102, 241, 0.2);
}

.port.output .port-arrow {
  position: absolute;
  width: 10px; height: 10px;
  color: #6366f1;
  transition: all 0.2s ease;
}

.port.output:hover {
  transform: translateY(-50%) scale(1.15);
}

.port.output:hover .port-ring {
  background: #6366f1;
  border-color: #6366f1;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

.port.output:hover .port-arrow {
  color: #fff;
  transform: scale(1.2);
}

@keyframes portPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
}

/* Delete button */
.delete-btn {
  position: absolute; top: -8px; right: -8px;
  width: 18px; height: 18px;
  background: #ef4444; border: 2px solid #fff; border-radius: 50%;
  color: #fff; font-size: 12px; font-weight: 700;
  cursor: pointer; opacity: 0; transition: opacity 0.15s;
  display: flex; align-items: center; justify-content: center; line-height: 1;
}
.node:hover .delete-btn { opacity: 1; }

/* Empty state */
.empty {
  position: absolute; inset: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-align: center;
}
.empty-icon { font-size: 40px; margin-bottom: 12px; opacity: 0.6; }
.empty h3 { font-size: 16px; font-weight: 600; color: #475569; margin: 0 0 6px; }
.empty p { font-size: 12px; color: #94a3b8; margin: 0 0 6px; }
.empty .sub-hint {
  font-size: 11px;
  color: #64748b;
  background: #f8fafc;
  padding: 8px 14px;
  border-radius: 8px;
  margin-bottom: 16px;
  border: 1px dashed #e2e8f0;
}
.empty .port-demo {
  display: inline-flex;
  align-items: center;
  gap: 1px;
  font-weight: 700;
  color: #6366f1;
}
.empty .port-demo.in { color: #10b981; }
.empty button {
  padding: 10px 20px; background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none; border-radius: 8px;
  color: #fff; font-size: 12px; font-weight: 600; cursor: pointer;
  transition: all 0.2s ease;
}
.empty button:hover {
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
  transform: translateY(-1px);
}

/* Footer - 流程描述 */
.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
}

.footer-flow {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.flow-label {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  flex-shrink: 0;
}

.flow-desc {
  font-size: 12px;
  color: #475569;
  font-family: monospace;
  background: #f8fafc;
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stats {
  font-size: 11px;
  color: #94a3b8;
  background: #f1f5f9;
  padding: 4px 10px;
  border-radius: 12px;
  flex-shrink: 0;
  margin-left: 12px;
}

/* 保存对话框 */
.save-dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.save-dialog {
  background: #fff;
  border-radius: 16px;
  width: 400px;
  max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.save-dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
}

.save-dialog-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.close-btn {
  width: 28px;
  height: 28px;
  background: #f1f5f9;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  transition: all 0.15s ease;
}

.close-btn:hover {
  background: #fee2e2;
  color: #ef4444;
}

.close-btn svg {
  width: 14px;
  height: 14px;
}

.save-dialog-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
}

.form-group .required {
  color: #ef4444;
}

.form-group .optional {
  font-weight: 400;
  color: #94a3b8;
}

.icon-select {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.icon-option {
  width: 36px;
  height: 36px;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.icon-option:hover {
  border-color: #c7d2fe;
  background: #eef2ff;
  transform: scale(1.05);
}

.icon-option.active {
  border-color: #6366f1;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

.form-input,
.form-textarea {
  padding: 10px 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  color: #1e293b;
  outline: none;
  transition: all 0.15s ease;
  font-family: inherit;
}

.form-input:focus,
.form-textarea:focus {
  border-color: #6366f1;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.form-input.error {
  border-color: #ef4444;
  background: #fef2f2;
}

.form-textarea {
  resize: none;
}

.error-msg {
  font-size: 11px;
  color: #ef4444;
}

.save-preview {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}

.preview-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.25);
}

.preview-info {
  flex: 1;
}

.preview-name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.preview-meta {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 2px;
}

.save-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

/* 对话框动画 */
.dialog-enter-active,
.dialog-leave-active {
  transition: all 0.2s ease;
}

.dialog-enter-from,
.dialog-leave-to {
  opacity: 0;
}

.dialog-enter-from .save-dialog,
.dialog-leave-to .save-dialog {
  transform: scale(0.95) translateY(-10px);
}
</style>

<style>
/* Tooltip 样式 (Teleport 到 body，不能用 scoped) */
.builder-tooltip {
  position: fixed;
  max-width: 220px;
  padding: 10px 12px;
  background: rgba(15, 23, 42, 0.95);
  color: #fff;
  font-size: 12px;
  line-height: 1.4;
  border-radius: 8px;
  z-index: 99999;
  pointer-events: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
}

.builder-tooltip-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.builder-tooltip-icon {
  font-size: 16px;
}

.builder-tooltip-name {
  font-weight: 600;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.builder-tooltip-type {
  font-size: 10px;
  padding: 2px 6px;
  background: rgba(99, 102, 241, 0.3);
  border-radius: 4px;
  color: #a5b4fc;
}

.builder-tooltip-desc {
  margin: 0;
  color: #cbd5e1;
  font-size: 11px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Tooltip 动画 */
.tooltip-enter-active,
.tooltip-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.tooltip-enter-from,
.tooltip-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>
