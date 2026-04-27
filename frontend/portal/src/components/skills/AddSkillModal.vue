<script setup lang="ts">
import { ref, watch, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { skillsApi, agentApi } from '@/api'
import type { Skill } from '@/api'

// ============================================================
// Props & Emits
// ============================================================

const props = defineProps<{
  show: boolean
  mode: 'create' | 'upload'  // create=AI对话创建/编辑, upload=上传ZIP
  prefillName?: string | null
  isFromAgent?: boolean
  editSkill?: Skill | null  // 传入则为编辑现有技能
}>()

const emit = defineEmits<{
  close: []
  submit: [data: any]
  'return-to-agent': [skillName: string]
}>()

// ============================================================
// skill-creator 技能
// ============================================================

const skillCreatorId = ref<string | null>(null)
const existingSkillNames = ref<Set<string>>(new Set())

const loadSkillCreator = async () => {
  try {
    const skill = await skillsApi.getByName('skill-creator')
    skillCreatorId.value = skill.id
    console.log('[AddSkillModal] Loaded skill-creator:', skill.id)
  } catch (e) {
    console.warn('[AddSkillModal] skill-creator not found')
    skillCreatorId.value = null
  }
}

// 加载已有技能名称（用于避免重复）
const loadExistingSkillNames = async () => {
  try {
    const skills = await skillsApi.getAll()
    existingSkillNames.value = new Set(skills.map(s => s.name.toLowerCase()))
    console.log('[AddSkillModal] Loaded existing skill names:', existingSkillNames.value.size)
  } catch (e) {
    console.warn('[AddSkillModal] Failed to load existing skills')
  }
}

// 生成唯一的技能名称
const generateUniqueName = (baseName: string): string => {
  // 清理名称：转小写，用横线替换空格和特殊字符
  let name = baseName
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '-')
    .replace(/^-|-$/g, '')

  if (!name) name = 'custom-skill'

  // 如果名称不存在，直接返回
  if (!existingSkillNames.value.has(name)) {
    return name
  }

  // 否则添加数字后缀
  let counter = 2
  while (existingSkillNames.value.has(`${name}-${counter}`)) {
    counter++
  }
  return `${name}-${counter}`
}

// 根据用户需求生成技能名称
const generateSkillName = (userRequest: string): string => {
  // 从用户描述中提取关键词
  const keywords = userRequest
    .replace(/[，。！？、\s]+/g, ' ')
    .split(' ')
    .filter(w => w.length >= 2)
    .slice(0, 3)

  if (keywords.length === 0) {
    return generateUniqueName('custom-skill')
  }

  // 尝试生成有意义的名称
  const baseName = keywords.join('-')
  return generateUniqueName(baseName)
}

onMounted(() => {
  loadSkillCreator()
  loadExistingSkillNames()
})

// ============================================================
// 代码编辑器状态（手动编辑）
// ============================================================

const showCodeEditor = ref(false)
const codeEditorContent = ref('')
const editingSkillInfo = ref<{
  id?: string
  name: string
  description: string
  icon: string
  tags: string[]
} | null>(null)

// ============================================================
// 更新模式选择（覆盖/新版本）
// ============================================================

const showUpdateModeDialog = ref(false)
const selectedUpdateMode = ref<'overwrite' | 'new_version'>('new_version')
const pendingUpdateData = ref<{
  skillId: string
  code: string
  skillName: string
  description: string
  icon: string
} | null>(null)

// 执行保存（根据选择的模式）
const executeUpdate = async () => {
  if (!pendingUpdateData.value) return

  const { skillId, code, skillName, description, icon } = pendingUpdateData.value

  try {
    await skillsApi.update(skillId, {
      code: code,
      update_mode: selectedUpdateMode.value
    })

    showUpdateModeDialog.value = false
    pendingUpdateData.value = null

    const modeText = selectedUpdateMode.value === 'overwrite' ? '已覆盖更新' : '已创建新版本'

    // 更新当前消息显示结果
    if (currentGeneratingMsgId.value) {
      const msgIndex = aiMessages.value.findIndex(m => m.id === currentGeneratingMsgId.value)
      if (msgIndex !== -1) {
        aiMessages.value[msgIndex] = {
          ...aiMessages.value[msgIndex],
          content: `✅ 技能「${skillName}」${modeText}`,
          generating: false,
          skillCard: {
            type: 'saved',
            name: skillName,
            icon: icon,
            description: description,
            status: 'success',
            details: [{ label: '状态', value: modeText }],
            actions: []
          }
        }
      }
    }

    // 关闭代码编辑器
    showCodeEditor.value = false

    // 通知父组件刷新
    emit('submit', { updated: true, skillId })

  } catch (error: any) {
    console.error('[UpdateSkill] Error:', error)
    showUpdateModeDialog.value = false

    if (currentGeneratingMsgId.value) {
      const msgIndex = aiMessages.value.findIndex(m => m.id === currentGeneratingMsgId.value)
      if (msgIndex !== -1) {
        aiMessages.value[msgIndex] = {
          ...aiMessages.value[msgIndex],
          content: `❌ 保存失败: ${error.message}`,
          generating: false
        }
      }
    }
  }
}

// 取消更新
const cancelUpdate = () => {
  showUpdateModeDialog.value = false
  pendingUpdateData.value = null
}

// 加载编辑模式下的技能代码
const loadEditSkillCode = async () => {
  if (!props.editSkill) return

  editingSkillInfo.value = {
    id: props.editSkill.id,
    name: props.editSkill.name,
    description: props.editSkill.description || '',
    icon: props.editSkill.icon || '⚡',
    tags: props.editSkill.tags || []
  }

  // 加载技能代码文件
  try {
    const entryScript = props.editSkill.entry_script || 'main.py'
    const fileContent = await skillsApi.getFileContent(props.editSkill.id, entryScript)
    if (fileContent.content) {
      codeEditorContent.value = fileContent.content
    }
  } catch (e) {
    console.warn('[AddSkillModal] Failed to load skill code:', e)
    codeEditorContent.value = '# 无法加载代码\n'
  }
}

// 切换代码编辑器
const toggleCodeEditor = () => {
  showCodeEditor.value = !showCodeEditor.value
  if (showCodeEditor.value) {
    // 初始化 editingSkillInfo（如果还没有）
    if (!editingSkillInfo.value) {
      editingSkillInfo.value = {
        name: tempSkillName.value || props.editSkill?.name || generateSkillName('custom'),
        description: props.editSkill?.description || '',
        icon: props.editSkill?.icon || '⚡',
        tags: props.editSkill?.tags || []
      }
    }

    // 如果代码为空，加载
    if (!codeEditorContent.value) {
      if (tempSkillId.value) {
        loadTempSkillCode()
      } else if (props.editSkill) {
        loadEditSkillCode()
      } else {
        codeEditorContent.value = generateDefaultCode({ name: editingSkillInfo.value.name, description: editingSkillInfo.value.description })
      }
    }
  }
}

// 加载临时技能代码
const loadTempSkillCode = async () => {
  if (!tempSkillId.value) return
  try {
    const tempSkill = await skillsApi.getTemp(tempSkillId.value)
    const fileContent = await skillsApi.getFileContent(tempSkill.temp_id, 'main.py')
    if (fileContent.content) {
      codeEditorContent.value = fileContent.content
    }
  } catch (e) {
    console.warn('[AddSkillModal] Failed to load temp skill code:', e)
  }
}

// 保存手动编辑的代码
const saveManualCodeEdit = async (): Promise<ActionResult> => {
  if (!codeEditorContent.value.trim()) {
    return {
      response: '',
      skillCard: {
        type: 'created',
        name: '保存失败',
        status: 'error',
        description: '代码不能为空',
        actions: [{ label: '继续编辑', action: 'edit' }]
      }
    }
  }

  try {
    const skillName = editingSkillInfo.value?.name || tempSkillName.value || generateSkillName('custom')
    const description = editingSkillInfo.value?.description || ''
    const icon = editingSkillInfo.value?.icon || '⚡'

    // 如果是编辑现有技能（传入了 editSkill）
    if (props.editSkill) {
      // 显示更新模式选择对话框
      pendingUpdateData.value = {
        skillId: props.editSkill.id,
        code: codeEditorContent.value,
        skillName: skillName,
        description: description,
        icon: icon
      }
      selectedUpdateMode.value = 'new_version'  // 默认新版本
      showUpdateModeDialog.value = true

      // 返回空结果，等用户选择后再执行
      return {
        response: '请选择保存方式...',
        pendingModeSelection: true
      }
    }

    // 如果有临时技能，删除旧的重新创建
    if (tempSkillId.value) {
      await skillsApi.deleteTemp(tempSkillId.value)
    }

    // 创建新的临时技能
    const tempSkill = await skillsApi.createTemp({
      name: skillName,
      description: description,
      icon: icon,
      code: codeEditorContent.value,
      tags: editingSkillInfo.value?.tags || ['手动编辑']
    })

    tempSkillId.value = tempSkill.temp_id
    tempSkillName.value = skillName

    const createdCard: SkillSummaryCard = {
      type: 'created',
      name: skillName,
      icon: icon,
      description: description || '手动编辑的代码',
      status: 'success',
      details: [{ label: '来源', value: '手动编辑' }],
      actions: [
        { label: '测试', action: 'test' },
        { label: '保存', action: 'save' }
      ]
    }

    showCodeEditor.value = false
    return {
      response: '',
      skillCreated: true,
      skillId: tempSkill.temp_id,
      skillName: skillName,
      skillCard: createdCard
    }

  } catch (error: any) {
    return {
      response: '',
      skillCard: {
        type: 'created',
        name: '保存失败',
        status: 'error',
        description: error.message || '保存代码时出错',
        actions: [{ label: '重试', action: 'edit' }]
      }
    }
  }
}

// ============================================================
// 上传模式状态（上传外部 ZIP 技能包）
// ============================================================

const uploadZipFile = ref<File | null>(null)
const uploadFolderName = ref<string>('')
const uploadIsDragging = ref(false)
const uploadParsedData = ref<{
  name: string
  description: string
  icon: string
  tags: string[]
  files: string[]
  aiAnalysis?: {
    description?: string
    capabilities?: string[]
    input_types?: string[]
    output_types?: string[]
    tags?: string[]
    icon?: string
    complexity?: string
  }
} | null>(null)
const uploadError = ref<string | null>(null)
const isUploading = ref(false)
const isAnalyzing = ref(false)  // AI 正在分析中
const uploadEntryScript = ref<string>('')
const uploadAuthor = ref<string>('')
const uploadVersion = ref<string>('1.0.0')

// 根据描述推断图标
const inferIcon = (description: string): string => {
  const desc = description.toLowerCase()
  if (desc.includes('data') || desc.includes('数据') || desc.includes('分析')) return '📊'
  if (desc.includes('api') || desc.includes('接口')) return '🔗'
  if (desc.includes('doc') || desc.includes('文档')) return '📑'
  if (desc.includes('翻译') || desc.includes('translate')) return '🌍'
  if (desc.includes('图') || desc.includes('image')) return '🖼️'
  if (desc.includes('代码') || desc.includes('code')) return '💻'
  if (desc.includes('测试') || desc.includes('test')) return '🧪'
  return '⚡'
}

// 处理 ZIP 文件选择 - 自动解析配置
const handleUploadZipSelect = async (file: File) => {
  uploadError.value = null
  uploadParsedData.value = null

  if (!file.name.toUpperCase().endsWith('.ZIP')) {
    uploadError.value = '请上传 ZIP 压缩包文件'
    return
  }

  uploadZipFile.value = file
  uploadFolderName.value = file.name.replace(/\.zip$/i, '')

  // 先显示默认值（正在分析中）
  isAnalyzing.value = true
  uploadParsedData.value = {
    name: uploadFolderName.value,
    description: '🤖 AI 正在分析技能代码...',
    icon: '📦',
    tags: [],
    files: []
  }

  // 调用 API 解析 ZIP 内容（包含 AI 分析）
  try {
    const preview = await skillsApi.previewUpload(file)
    uploadParsedData.value = {
      name: preview.name || uploadFolderName.value,
      description: preview.description || '从 ZIP 包导入的技能',
      icon: preview.icon || '📦',
      tags: preview.tags || ['导入'],
      files: preview.files || [],
      aiAnalysis: preview.ai_analysis || undefined
    }
    // 保存额外信息
    if (preview.entry_script) {
      uploadEntryScript.value = preview.entry_script
    }
    if (preview.author) {
      uploadAuthor.value = preview.author
    }
    if (preview.version) {
      uploadVersion.value = preview.version
    }
  } catch (error: any) {
    console.warn('Failed to preview ZIP:', error)
    // 解析失败时使用默认值
    uploadParsedData.value = {
      name: uploadFolderName.value,
      description: '从 ZIP 包导入的技能',
      icon: '📦',
      tags: ['导入'],
      files: []
    }
  } finally {
    isAnalyzing.value = false
  }
}

// 处理拖放
const handleUploadDrop = async (e: DragEvent) => {
  uploadIsDragging.value = false
  const files = e.dataTransfer?.files
  if (files && files.length > 0 && files[0]) {
    await handleUploadZipSelect(files[0])
  }
}

// 处理文件选择
const handleUploadFileSelect = async (e: Event) => {
  const target = e.target as HTMLInputElement
  const files = target.files
  if (files && files.length > 0 && files[0]) {
    await handleUploadZipSelect(files[0])
  }
  target.value = ''
}

// 清除上传
const clearUpload = () => {
  uploadZipFile.value = null
  uploadFolderName.value = ''
  uploadParsedData.value = null
  uploadError.value = null
  uploadEntryScript.value = ''
  uploadAuthor.value = ''
  uploadVersion.value = '1.0.0'
  isAnalyzing.value = false
}

// 提交上传
const handleUploadSubmit = async () => {
  if (!uploadZipFile.value || !uploadParsedData.value) return

  isUploading.value = true
  uploadError.value = null

  try {
    // 注意：上传的 skill 始终标记为 'uploaded'，确保不可编辑
    const newSkill = await skillsApi.upload({
      file: uploadZipFile.value,
      name: uploadParsedData.value.name,
      description: uploadParsedData.value.description,
      icon: uploadParsedData.value.icon,
      tags: uploadParsedData.value.tags,
      entry_script: uploadEntryScript.value || undefined,
      author: 'uploaded',  // 始终使用 'uploaded'，确保上传的 skill 不可编辑
      version: uploadVersion.value || '1.0.0'
    })

    emit('submit', {
      id: newSkill.id,
      name: newSkill.name,
      description: newSkill.description,
      icon: newSkill.icon
    })

    clearUpload()
    emit('close')
  } catch (e: any) {
    console.error('Upload failed:', e)
    uploadError.value = '上传失败: ' + (e.message || '未知错误')
  } finally {
    isUploading.value = false
  }
}

// ============================================================
// 对话状态
// ============================================================

interface OutputFileInfo {
  name: string
  type: string
  url: string
  size?: string
}

// 技能摘要卡片数据
interface SkillSummaryCard {
  type: 'created' | 'tested' | 'saved'
  name: string
  icon?: string
  description?: string
  status: 'success' | 'error'
  details?: { label: string; value: string }[]
  actions?: { label: string; action: string }[]
  outputFile?: OutputFileInfo
}

interface QuickAction {
  label: string
  action: string
  data?: any  // 附带数据，用于 save-extracted-skill 等需要数据的操作
}

interface AiMessage {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  generating?: boolean
  outputFile?: OutputFileInfo
  htmlPreview?: string
  showProgress?: boolean       // 是否显示创建进度卡片
  showTestProgress?: boolean   // 是否显示测试进度卡片
  skillCard?: SkillSummaryCard // 技能摘要卡片
  quickActions?: QuickAction[] // 快捷操作按钮
}

const aiMessages = ref<AiMessage[]>([])
const aiInput = ref('')
const aiGenerating = ref(false)
const aiChatContainer = ref<HTMLElement | null>(null)
const currentGeneratingMsgId = ref<number | null>(null)
const abortController = ref<AbortController | null>(null)

// 取消/撤回正在生成的消息
const cancelGeneration = () => {
  if (abortController.value) {
    abortController.value.abort()
    abortController.value = null
  }

  // 删除正在生成的消息和对应的用户消息
  if (currentGeneratingMsgId.value) {
    const genMsgIndex = aiMessages.value.findIndex(m => m.id === currentGeneratingMsgId.value)
    if (genMsgIndex !== -1) {
      // 删除AI消息
      aiMessages.value.splice(genMsgIndex, 1)
      // 删除前面的用户消息
      if (genMsgIndex > 0 && aiMessages.value[genMsgIndex - 1]?.role === 'user') {
        aiMessages.value.splice(genMsgIndex - 1, 1)
      }
    }
    currentGeneratingMsgId.value = null
  }

  // 重置状态
  aiGenerating.value = false
  isCreatingSkill.value = false
  isTestingSkill.value = false

  if (creationTimer) {
    clearInterval(creationTimer)
    creationTimer = null
  }
  if (testTimer) {
    clearInterval(testTimer)
    testTimer = null
  }
}

// 进度状态
interface ProgressStep {
  id: string
  label: string
  icon: string
  status: 'pending' | 'active' | 'done' | 'error'
}

// 创建进度
const isCreatingSkill = ref(false)
const creationProgress = ref<ProgressStep[]>([])
const creationStartTime = ref<number>(0)
const creationElapsedTime = ref(0)
const creationEncouragement = ref('')
let creationTimer: number | null = null

// 测试进度
const isTestingSkill = ref(false)
const testProgress = ref<ProgressStep[]>([])
const testStartTime = ref<number>(0)
const testElapsedTime = ref(0)
const testEncouragement = ref('')
let testTimer: number | null = null

const encouragements = [
  '正在认真思考中...',
  '好技能需要耐心打磨...',
  '快好了，再等一下...',
  '正在写代码，马上就好...',
  '细节决定成败，稍等片刻...',
]

const testEncouragements = [
  '正在执行技能...',
  '处理数据中...',
  '即将完成...',
  '正在生成输出...',
]

const startCreationProgress = () => {
  isCreatingSkill.value = true
  creationStartTime.value = Date.now()
  creationElapsedTime.value = 0
  creationEncouragement.value = ''

  creationProgress.value = [
    { id: 'analyze', label: '分析需求', icon: '🔍', status: 'active' },
    { id: 'design', label: '设计方案', icon: '💡', status: 'pending' },
    { id: 'generate', label: '生成代码', icon: '📝', status: 'pending' },
    { id: 'create', label: '创建技能', icon: '🔧', status: 'pending' },
  ]

  // 定时更新进度和鼓励语
  creationTimer = window.setInterval(() => {
    creationElapsedTime.value = Math.floor((Date.now() - creationStartTime.value) / 1000)

    // 根据时间更新鼓励语
    if (creationElapsedTime.value > 3 && creationElapsedTime.value <= 6) {
      creationEncouragement.value = encouragements[0]!
    } else if (creationElapsedTime.value > 6 && creationElapsedTime.value <= 10) {
      creationEncouragement.value = encouragements[1]!
    } else if (creationElapsedTime.value > 10 && creationElapsedTime.value <= 15) {
      creationEncouragement.value = encouragements[2]!
    } else if (creationElapsedTime.value > 15 && creationElapsedTime.value <= 20) {
      creationEncouragement.value = encouragements[3]!
    } else if (creationElapsedTime.value > 20) {
      creationEncouragement.value = encouragements[4]!
    }
  }, 1000)
}

const updateCreationStep = (stepId: string) => {
  const stepIndex = creationProgress.value.findIndex(s => s.id === stepId)
  if (stepIndex !== -1) {
    // 将之前的步骤标记为完成
    for (let i = 0; i < stepIndex; i++) {
      const step = creationProgress.value[i]
      if (step) step.status = 'done'
    }
    // 当前步骤标记为活动
    const currentStep = creationProgress.value[stepIndex]
    if (currentStep) currentStep.status = 'active'
  }
}

const finishCreationProgress = (success: boolean) => {
  if (creationTimer) {
    clearInterval(creationTimer)
    creationTimer = null
  }

  if (success) {
    creationProgress.value.forEach(s => s.status = 'done')
  } else {
    // 标记当前活动步骤为错误
    const activeStep = creationProgress.value.find(s => s.status === 'active')
    if (activeStep) activeStep.status = 'error'
  }

  setTimeout(() => {
    isCreatingSkill.value = false
  }, success ? 1000 : 500)
}

// 测试进度控制
const startTestProgress = () => {
  isTestingSkill.value = true
  testStartTime.value = Date.now()
  testElapsedTime.value = 0
  testEncouragement.value = ''

  testProgress.value = [
    { id: 'prepare', label: '准备环境', icon: '🔧', status: 'active' },
    { id: 'execute', label: '执行技能', icon: '▶️', status: 'pending' },
    { id: 'process', label: '处理结果', icon: '📊', status: 'pending' },
    { id: 'output', label: '生成输出', icon: '📄', status: 'pending' },
  ]

  testTimer = window.setInterval(() => {
    testElapsedTime.value = Math.floor((Date.now() - testStartTime.value) / 1000)

    if (testElapsedTime.value > 2 && testElapsedTime.value <= 5) {
      testEncouragement.value = testEncouragements[0]!
    } else if (testElapsedTime.value > 5 && testElapsedTime.value <= 10) {
      testEncouragement.value = testEncouragements[1]!
    } else if (testElapsedTime.value > 10 && testElapsedTime.value <= 15) {
      testEncouragement.value = testEncouragements[2]!
    } else if (testElapsedTime.value > 15) {
      testEncouragement.value = testEncouragements[3]!
    }
  }, 1000)
}

const updateTestStep = (stepId: string) => {
  const stepIndex = testProgress.value.findIndex(s => s.id === stepId)
  if (stepIndex !== -1) {
    for (let i = 0; i < stepIndex; i++) {
      const step = testProgress.value[i]
      if (step) step.status = 'done'
    }
    const currentStep = testProgress.value[stepIndex]
    if (currentStep) currentStep.status = 'active'
  }
}

const finishTestProgress = (success: boolean) => {
  if (testTimer) {
    clearInterval(testTimer)
    testTimer = null
  }

  if (success) {
    testProgress.value.forEach(s => s.status = 'done')
  } else {
    const activeStep = testProgress.value.find(s => s.status === 'active')
    if (activeStep) activeStep.status = 'error'
  }

  setTimeout(() => {
    isTestingSkill.value = false
  }, success ? 800 : 500)
}

// 测试进度百分比
const testProgressPercentage = computed(() => {
  if (!testProgress.value.length) return 0
  const doneCount = testProgress.value.filter(s => s.status === 'done').length
  const activeCount = testProgress.value.filter(s => s.status === 'active').length
  return Math.round(((doneCount + activeCount * 0.5) / testProgress.value.length) * 100)
})

const formatTime = (seconds: number): string => {
  if (seconds < 60) return `${seconds}秒`
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}分${secs}秒`
}

// ============================================================
// 技能状态
// ============================================================

// 临时技能（测试用）
const tempSkillId = ref<string | null>(null)
const tempSkillName = ref<string | null>(null)

// 编辑现有技能（永久技能）
const editingSkillId = ref<string | null>(null)

// 最终创建的技能
const finalSkillId = ref<string | null>(null)
const finalSkillName = ref<string | null>(null)

// 是否等待测试决定（保存后）
const awaitingTestDecision = ref(false)

// 是否等待修改输入（用户点击了"修改"按钮）
const awaitingModification = ref(false)

// ============================================================
// 新流程状态（简化版）
// ============================================================

// 流程阶段: idle -> creating -> preview -> testing -> saved
type FlowPhase = 'idle' | 'creating' | 'preview' | 'testing' | 'saved'
const flowPhase = ref<FlowPhase>('idle')

// 当前技能信息（用于卡片展示）
const currentSkillInfo = ref<{
  name: string
  description: string
  icon: string
  tags: string[]
  code?: string
  inputType?: string
  outputType?: string
} | null>(null)

// 是否已有可测试的技能
const hasTestableSkill = computed(() => !!tempSkillId.value || !!editingSkillId.value)

// 创建进度百分比
const progressPercentage = computed(() => {
  if (!creationProgress.value.length) return 0
  const doneCount = creationProgress.value.filter(s => s.status === 'done').length
  const activeCount = creationProgress.value.filter(s => s.status === 'active').length
  return Math.round(((doneCount + activeCount * 0.5) / creationProgress.value.length) * 100)
})

// ============================================================
// 文件上传
// ============================================================

interface UploadedFile {
  id: string
  name: string
  type: string
  size: number
  file: File
  serverPath?: string
  uploading?: boolean
  uploadError?: string
}

const uploadedFiles = ref<UploadedFile[]>([])
const fileInputRef = ref<HTMLInputElement | null>(null)
const isDraggingFile = ref(false)

// ============================================================
// 工具函数
// ============================================================

const scrollToBottom = () => {
  nextTick(() => {
    if (aiChatContainer.value) {
      aiChatContainer.value.scrollTop = aiChatContainer.value.scrollHeight
    }
  })
}

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// 获取执行结果的友好文本
const getFriendlyResultText = (error?: string): string => {
  if (!error) return '执行未能产生预期的结果'

  if (error.includes('SyntaxError')) {
    return '技能代码在解析时遇到了问题，可能需要调整代码格式'
  }
  if (error.includes('TypeError')) {
    return '数据类型不匹配，输入的内容格式可能需要调整'
  }
  if (error.includes('KeyError')) {
    return '找不到需要的数据字段，输入数据的结构可能不符合预期'
  }
  if (error.includes('FileNotFoundError') || error.includes('No such file')) {
    return '找不到需要处理的文件'
  }
  if (error.includes('ValueError')) {
    return '输入的值格式不正确'
  }
  if (error.includes('ImportError') || error.includes('ModuleNotFoundError')) {
    return '技能需要的某些依赖还没有安装'
  }

  return '执行过程中遇到了一些问题'
}

// 获取执行分析/建议
const getFriendlyThinking = (error?: string): string => {
  if (!error) return '建议检查输入内容是否正确，或者尝试修改技能代码'

  if (error.includes('SyntaxError')) {
    return '这通常是代码格式问题，比如引号、括号不匹配等。可以尝试修改技能代码。'
  }
  if (error.includes('TypeError')) {
    return '输入的数据类型和技能期望的不一致。比如期望数字却收到了文字，可以检查输入格式。'
  }
  if (error.includes('KeyError')) {
    return '输入的 JSON 数据缺少必要的字段。请确认输入数据包含技能需要的所有字段。'
  }
  if (error.includes('FileNotFoundError')) {
    return '需要先上传文件，或者检查文件路径是否正确。'
  }
  if (error.includes('ValueError')) {
    return '输入值的格式不对，比如日期格式、数字格式等。请检查并调整输入内容。'
  }
  if (error.includes('ImportError') || error.includes('ModuleNotFoundError')) {
    return '技能代码使用了未安装的库，需要在服务器上安装相应的依赖。'
  }

  return '可以尝试重新输入，或者修改技能代码来适应当前的输入。'
}

const getFileIcon = (type: string): string => {
  if (type.startsWith('image/')) return '🖼️'
  if (type.includes('pdf')) return '📄'
  if (type.includes('word') || type.includes('document')) return '📝'
  if (type.includes('excel') || type.includes('spreadsheet') || type.includes('csv')) return '📊'
  if (type.includes('powerpoint') || type.includes('presentation')) return '📽️'
  if (type.includes('zip') || type.includes('rar') || type.includes('tar')) return '📦'
  if (type.includes('json')) return '📋'
  if (type.includes('text')) return '📄'
  return '📎'
}

// ============================================================
// 初始化对话
// ============================================================

const initConversation = () => {
  // 统一的简洁开场白
  let greeting: string

  // 重置状态
  tempSkillId.value = null
  tempSkillName.value = null
  editingSkillId.value = null
  finalSkillId.value = null
  awaitingModification.value = false
  finalSkillName.value = null
  awaitingTestDecision.value = false
  uploadedFiles.value = []
  showCodeEditor.value = false
  codeEditorContent.value = ''

  if (props.editSkill) {
    // 编辑现有技能 - 设置编辑状态
    editingSkillId.value = props.editSkill.id
    tempSkillName.value = props.editSkill.name
    loadEditSkillCode()
    greeting = `正在编辑「${props.editSkill.name}」\n\n当前功能：${props.editSkill.description || '暂无描述'}\n\n描述你想修改的内容，或直接上传文件测试。`
  } else if (props.prefillName) {
    greeting = `「${props.prefillName}」- 描述一下它要做什么。`
  } else {
    greeting = '描述你想创建的技能，我来帮你实现。'
  }

  aiMessages.value = [{
    id: 1,
    role: 'assistant',
    content: greeting
  }]
}

// 存储待保存的提取技能数据
const pendingExtractedSkill = ref<any>(null)

// 处理卡片按钮点击
const handleCardAction = async (action: string, data?: any) => {
  switch (action) {
    case 'test':
      // 添加提示消息并聚焦输入框
      aiMessages.value.push({
        id: Date.now(),
        role: 'assistant',
        content: '请上传文件或输入内容来测试技能。'
      })
      scrollToBottom()
      aiInput.value = ''
      nextTick(() => {
        const textarea = document.querySelector('.input-wrapper textarea') as HTMLTextAreaElement
        textarea?.focus()
      })
      break
    case 'save':
      // 保存技能
      aiInput.value = '保存'
      handleUserInput('保存')
      break
    case 'modify':
      // 修改技能 - 设置等待修改状态
      awaitingModification.value = true
      aiMessages.value.push({
        id: Date.now(),
        role: 'assistant',
        content: '请告诉我需要修改什么？（描述问题或直接说明需要的改动）'
      })
      scrollToBottom()
      break
    case 'retry':
      // 重试测试
      aiMessages.value.push({
        id: Date.now(),
        role: 'assistant',
        content: '请上传文件或输入内容重新测试。'
      })
      scrollToBottom()
      break
    case 'recreate':
      // 重新创建
      aiInput.value = '重新创建'
      handleUserInput('重新创建')
      break
    case 'edit':
      // 打开代码编辑器
      toggleCodeEditor()
      break
    case 'test-skill':
      // 测试已保存的技能
      awaitingTestDecision.value = false
      aiMessages.value.push({
        id: Date.now(),
        role: 'assistant',
        content: '请上传文件或输入内容来测试技能。'
      })
      scrollToBottom()
      nextTick(() => {
        const textarea = document.querySelector('.input-wrapper textarea') as HTMLTextAreaElement
        textarea?.focus()
      })
      break
    case 'skip-test':
      // 跳过测试
      awaitingTestDecision.value = false
      if (props.isFromAgent && finalSkillName.value) {
        // 显示返回选项
        aiMessages.value.push({
          id: Date.now(),
          role: 'assistant',
          content: '好的，技能已保存。接下来？',
          quickActions: [
            { label: '返回继续执行', action: 'return-to-agent' },
            { label: '留在这里', action: 'stay-here' }
          ]
        })
        scrollToBottom()
      } else {
        // 直接关闭
        handleClose()
      }
      break
    case 'return-to-agent':
      // 返回 Agent 继续执行
      if (finalSkillName.value) {
        emit('return-to-agent', finalSkillName.value)
      }
      break
    case 'stay-here':
      // 留在当前对话
      aiMessages.value.push({
        id: Date.now(),
        role: 'assistant',
        content: '好的，可以继续测试或修改技能。'
      })
      scrollToBottom()
      break

    case 'save-extracted-skill':
      // 保存从 skill-creator 输出中提取的技能
      await saveExtractedSkill(data || pendingExtractedSkill.value)
      break

    case 'continue':
      // 继续优化，不需要特殊处理，用户可以继续输入
      aiMessages.value.push({
        id: Date.now(),
        role: 'assistant',
        content: '好的，请告诉我需要如何优化？'
      })
      scrollToBottom()
      break
  }
}

// 保存从 skill-creator 输出中提取的技能
const saveExtractedSkill = async (skillData: any) => {
  if (!skillData || !skillData.code) {
    aiMessages.value.push({
      id: Date.now(),
      role: 'assistant',
      content: '抱歉，没有找到可保存的技能代码。'
    })
    return
  }

  try {
    const skillName = generateUniqueName(skillData.name || '新技能')

    // 创建临时技能
    const tempSkill = await skillsApi.createTemp({
      name: skillName,
      description: skillData.description || '',
      icon: skillData.icon || '⚡',
      code: skillData.code,
      tags: skillData.tags || ['自动创建'],
      output_config: skillData.output_type ? { preferred_type: skillData.output_type } : undefined
    })

    tempSkillId.value = tempSkill.temp_id
    tempSkillName.value = skillName

    // 显示成功卡片
    aiMessages.value.push({
      id: Date.now(),
      role: 'assistant',
      content: '',
      skillCard: {
        type: 'created',
        name: skillName,
        icon: skillData.icon || '⚡',
        description: skillData.description || '',
        status: 'success',
        details: skillData.output_type ? [{ label: '输出', value: skillData.output_type }] : [],
        actions: [
          { label: '测试', action: 'test' },
          { label: '保存', action: 'save' }
        ]
      }
    })
    scrollToBottom()
  } catch (error: any) {
    aiMessages.value.push({
      id: Date.now(),
      role: 'assistant',
      content: `创建技能失败：${error.message}`
    })
    scrollToBottom()
  }
}

// ============================================================
// 文件上传处理
// ============================================================

const handleFileSelect = (e: Event) => {
  const input = e.target as HTMLInputElement
  if (input.files) {
    addFiles(Array.from(input.files))
  }
  input.value = ''
}

const addFiles = async (files: File[]) => {
  const newFiles: UploadedFile[] = files.map(file => ({
    id: `file-${Date.now()}-${Math.random().toString(36).slice(2)}`,
    name: file.name,
    type: file.type,
    size: file.size,
    file,
    uploading: true
  }))

  uploadedFiles.value.push(...newFiles)

  // 上传每个文件
  for (const uf of newFiles) {
    try {
      const response = await agentApi.upload(uf.file)
      const idx = uploadedFiles.value.findIndex(f => f.id === uf.id)
      if (idx !== -1) {
        uploadedFiles.value[idx] = {
          ...uploadedFiles.value[idx],
          serverPath: response.path,
          uploading: false
        }
      }
    } catch (error: any) {
      const idx = uploadedFiles.value.findIndex(f => f.id === uf.id)
      if (idx !== -1) {
        uploadedFiles.value[idx] = {
          ...uploadedFiles.value[idx],
          uploading: false,
          uploadError: error.message || '上传失败'
        }
      }
    }
  }
}

const removeFile = (fileId: string) => {
  uploadedFiles.value = uploadedFiles.value.filter(f => f.id !== fileId)
}

const triggerFileUpload = () => {
  fileInputRef.value?.click()
}

// 拖拽处理
const handleDragOver = (e: DragEvent) => {
  e.preventDefault()
  isDraggingFile.value = true
}

const handleDragLeave = (e: DragEvent) => {
  e.preventDefault()
  isDraggingFile.value = false
}

const handleFileDrop = (e: DragEvent) => {
  e.preventDefault()
  isDraggingFile.value = false
  if (e.dataTransfer?.files) {
    addFiles(Array.from(e.dataTransfer.files))
  }
}

// ============================================================
// 核心：处理用户输入
// ============================================================

const handleUserInput = async (input: string) => {
  const readyFiles = uploadedFiles.value.filter(f => f.serverPath && !f.uploading)
  const hasFiles = readyFiles.length > 0

  if (!input.trim() && !hasFiles) return
  if (aiGenerating.value) return

  // 构建用户消息
  const fileNames = readyFiles.map(f => f.name)
  const filePaths = readyFiles.map(f => f.serverPath!)
  const displayContent = hasFiles
    ? (input.trim() ? `${input}\n\n📎 附件: ${fileNames.join(', ')}` : `📎 附件: ${fileNames.join(', ')}`)
    : input

  // 添加用户消息
  aiMessages.value.push({
    id: Date.now(),
    role: 'user',
    content: displayContent
  })

  // 清空输入
  aiInput.value = ''
  const currentFiles = [...readyFiles]
  uploadedFiles.value = []

  aiGenerating.value = true
  abortController.value = new AbortController()
  scrollToBottom()

  // 添加 AI 回复占位
  const aiMsgId = Date.now() + 1
  currentGeneratingMsgId.value = aiMsgId
  aiMessages.value.push({
    id: aiMsgId,
    role: 'assistant',
    content: '正在思考...',
    generating: true
  })
  scrollToBottom()

  try {
    // 构建对话历史
    const history = aiMessages.value
      .filter(m => m.role !== 'system' && m.id !== aiMsgId && !m.generating)
      .map(m => ({ role: m.role as 'user' | 'assistant', content: m.content }))

    // 分析用户意图并决定行动
    const action = await analyzeAndAct(input, currentFiles, filePaths, history)

    // 更新 AI 消息
    const msgIndex = aiMessages.value.findIndex(m => m.id === aiMsgId)
    if (msgIndex !== -1) {
      aiMessages.value[msgIndex] = {
        ...aiMessages.value[msgIndex],
        content: action.response,
        generating: false,
        outputFile: action.outputFile,
        htmlPreview: action.htmlPreview,
        skillCard: action.skillCard,
        quickActions: action.quickActions
      }
    }

    // 处理特殊动作
    if (action.skillCreated) {
      tempSkillId.value = action.skillId!
      tempSkillName.value = action.skillName!
    }

    if (action.finalized) {
      finalSkillId.value = action.skillId!
      finalSkillName.value = action.skillName!
      // 通知父组件
      emit('submit', { id: action.skillId, name: action.skillName })

      // 添加测试提示消息
      await nextTick()
      awaitingTestDecision.value = true
      aiMessages.value.push({
        id: Date.now(),
        role: 'assistant',
        content: '技能已保存！要测试一下吗？',
        generating: false,
        quickActions: [
          { label: '试一下', action: 'test-skill' },
          { label: '不用了', action: 'skip-test' }
        ]
      })
      scrollToBottom()
    }

    // 测试完成后显示返回选项
    if (action.showReturnOptions && props.isFromAgent) {
      await nextTick()
      aiMessages.value.push({
        id: Date.now(),
        role: 'assistant',
        content: '测试完成。接下来？',
        generating: false,
        quickActions: [
          { label: '返回继续执行', action: 'return-to-agent' },
          { label: '留在这里', action: 'stay-here' }
        ]
      })
      scrollToBottom()
    }

  } catch (error: any) {
    const msgIndex = aiMessages.value.findIndex(m => m.id === aiMsgId)
    if (msgIndex !== -1) {
      aiMessages.value[msgIndex] = {
        ...aiMessages.value[msgIndex],
        content: `抱歉，出现了错误：${error.message || '未知错误'}\n\n请重试或换一种方式描述。`,
        generating: false
      }
    }
  } finally {
    currentGeneratingMsgId.value = null
    abortController.value = null
  }

  aiGenerating.value = false
  scrollToBottom()
}

// ============================================================
// 核心：分析意图并执行动作
// ============================================================

interface ActionResult {
  response: string
  outputFile?: OutputFileInfo
  htmlPreview?: string
  skillCreated?: boolean
  skillId?: string
  skillName?: string
  finalized?: boolean
  skillCard?: SkillSummaryCard
  showReturnOptions?: boolean
  pendingModeSelection?: boolean  // 等待用户选择更新模式
  quickActions?: QuickAction[]    // 快捷操作按钮
}

const analyzeAndAct = async (
  input: string,
  files: UploadedFile[],
  filePaths: string[],
  history: Array<{ role: 'user' | 'assistant', content: string }>
): Promise<ActionResult> => {

  const inputLower = input.toLowerCase().trim()
  const hasFiles = files.length > 0

  console.log('[AnalyzeAction] 流程阶段:', flowPhase.value, '输入:', inputLower)

  // ============================================================
  // 简化流程：减少确认，直接行动
  // ============================================================

  // 0. 等待修改输入
  if (awaitingModification.value && (tempSkillId.value || editingSkillId.value)) {
    awaitingModification.value = false
    flowPhase.value = 'creating'
    return await modifyExistingSkill(input, history)
  }

  // 意图检测
  const wantsToSave = /保存|确认|提交|没问题|满意/.test(inputLower)
  const wantsToRecreate = /重新创建|从头开始|重做|重新来/.test(inputLower)
  const wantsToModify = /修改|改一下|不对|调整|更改|换一下|改改|有问题|错了|bug|优化/.test(inputLower) && !wantsToRecreate
  const wantsToCancel = /取消|算了|不要了|关闭/.test(inputLower)
  const wantsToTest = hasFiles || /测试|试试|运行|执行|试一下/.test(inputLower)

  // 1. 取消
  if (wantsToCancel) {
    await cleanupTempSkill()
    flowPhase.value = 'idle'
    return { response: '好的，已取消。' }
  }

  // 2. 保存（已有临时技能）
  if (wantsToSave && tempSkillId.value) {
    flowPhase.value = 'saved'
    return await finalizeSkill()
  }

  // 3. 重新创建
  if (wantsToRecreate) {
    await cleanupTempSkill()
    flowPhase.value = 'idle'
    return { response: '好的，请描述你想创建的技能。' }
  }

  // 4. 修改（有技能时）
  if ((tempSkillId.value || editingSkillId.value) && wantsToModify) {
    flowPhase.value = 'creating'
    return await modifyExistingSkill(input, history)
  }

  // 5. 测试（有技能且有文件/输入）
  const hasTestableSkillNow = tempSkillId.value || finalSkillId.value || editingSkillId.value
  if (hasTestableSkillNow && (hasFiles || (wantsToTest && input.trim()))) {
    flowPhase.value = 'testing'
    return await executeSkillTest(input, filePaths)
  }

  // 6. 有文件但没有技能 - 提示
  if (hasFiles && !tempSkillId.value && !editingSkillId.value) {
    return {
      response: `收到文件：${files.map(f => f.name).join(', ')}\n\n请描述你想创建什么技能来处理这些文件？`
    }
  }

  // 7. 首次输入或继续对话 - 直接开始创建
  // 关键改动：不再反复确认，直接开始
  if (!tempSkillId.value && !editingSkillId.value && history.length <= 2) {
    // 首次输入需求，直接开始创建
    flowPhase.value = 'creating'
    return await directCreateSkill(input, filePaths, history)
  }

  // 8. 其他情况：继续对话
  return await callAIForSkillCreation(input, filePaths, history, false)
}

// 显示进度卡片到当前消息
const showProgressInCurrentMessage = () => {
  if (currentGeneratingMsgId.value) {
    const msgIndex = aiMessages.value.findIndex(m => m.id === currentGeneratingMsgId.value)
    if (msgIndex !== -1) {
      aiMessages.value[msgIndex] = {
        ...aiMessages.value[msgIndex],
        showProgress: true,
        generating: true,
        content: ''
      }
      scrollToBottom()
    }
  }
}

// 隐藏进度卡片
const hideProgressInCurrentMessage = () => {
  if (currentGeneratingMsgId.value) {
    const msgIndex = aiMessages.value.findIndex(m => m.id === currentGeneratingMsgId.value)
    if (msgIndex !== -1) {
      aiMessages.value[msgIndex] = {
        ...aiMessages.value[msgIndex],
        showProgress: false
      }
    }
  }
}

// ============================================================
// 调用 AI 进行技能创建对话
// ============================================================

const callAIForSkillCreation = async (
  input: string,
  filePaths: string[],
  history: Array<{ role: 'user' | 'assistant', content: string }>,
  isModification: boolean
): Promise<ActionResult> => {

  const fileInfo = filePaths.length > 0
    ? `[上传了文件：${filePaths.join(', ')}]`
    : ''

  // 检测用户是否在确认创建 - 更严格的条件
  const inputLower = input.toLowerCase().trim()
  const confirmWords = ['好的', '好', '可以', '行', '确认', '创建', '生成', '开始', 'ok', 'yes', '是', '对', '嗯', '没问题', '创建吧']
  const simpleConfirm = confirmWords.some(word => inputLower.includes(word))

  // 检查 AI 是否明确询问过是否创建
  const lastAiMsg = history.filter(m => m.role === 'assistant').slice(-1)[0]
  const aiAskingToCreate = lastAiMsg?.content && /开始创建|确认创建|需求已明确/.test(lastAiMsg.content)

  // 只有当：1.用户确认 2.AI明确询问过 3.还没有临时技能 4.有足够对话历史
  const isConfirmingCreation = simpleConfirm && aiAskingToCreate &&
    !tempSkillId.value && history.length >= 2

  // 如果用户确认创建，立即显示进度卡片并创建技能
  if (isConfirmingCreation) {
    return await createSkillFromHistory(history, input)
  }

  // ============================================================
  // 透传模式 + 环境适配
  // 首次对话时添加环境上下文，后续保持纯透传
  // ============================================================

  let fullContent = ''

  try {
    let message = input
    if (fileInfo) {
      message = `${input}\n\n${fileInfo}`
    }

    // 首次对话时，添加 Web 环境上下文和代码格式要求
    if (history.length === 0) {
      message = `${message}

[环境说明]
这是 Web API 环境，不是命令行。生成代码时必须使用以下格式：

\`\`\`python
def main(params):
    """
    技能入口函数

    params 包含:
    - params.get('input', '') - 用户输入的文本
    - params.get('files', []) - 上传的文件路径列表
    - params.get('file_path', '') - 单个文件路径

    可用工具:
    - pd (pandas) - 数据处理
    - Path - 路径操作
    - OUTPUTS_DIR - 输出目录
    - generate_unique_filename(ext) - 生成唯一文件名
    """
    files = params.get('files', [])

    # 处理逻辑...

    # 返回格式
    return {
        'status': 'success',  # 或 'error'
        'message': '处理完成',
        'output_file': {  # 可选，如果生成了文件
            'path': str(output_path),
            'type': 'json'  # json/xlsx/csv/html 等
        }
    }
\`\`\`

重要：
- 不要用 argparse 或 if __name__ == "__main__"
- 必须有 main(params) 函数作为入口
- 文件路径从 params['files'] 获取，不是命令行参数`
    }

    for await (const chunk of agentApi.chatStream({
      message: message,
      history: history,
      skill_ids: skillCreatorId.value ? [skillCreatorId.value] : undefined
    }, abortController.value?.signal)) {
      fullContent += chunk

      // 流式更新消息内容
      if (currentGeneratingMsgId.value) {
        const msgIndex = aiMessages.value.findIndex(m => m.id === currentGeneratingMsgId.value)
        if (msgIndex !== -1) {
          aiMessages.value[msgIndex] = {
            ...aiMessages.value[msgIndex],
            content: fullContent || '正在思考...'
          }
          scrollToBottom()
        }
      }
    }
  } catch (error: any) {
    throw new Error(`AI 服务出错: ${error.message}`)
  }

  // UI 增强：检测是否输出了完整技能，显示保存按钮
  const extractedSkill = tryExtractSkillFromResponse(fullContent, history)
  if (extractedSkill && extractedSkill.code && !tempSkillId.value) {
    // skill-creator 输出了代码，但我们还没有创建临时技能
    // 返回响应并附带快速操作按钮
    return {
      response: fullContent,
      quickActions: [
        { label: '保存此技能', action: 'save-extracted-skill', data: extractedSkill },
        { label: '继续优化', action: 'continue' }
      ]
    }
  }

  return { response: fullContent }
}

// ============================================================
// 调用 skill-creator 创建技能
// ============================================================
// 简化流程：直接创建技能（不反复确认）
// ============================================================

const directCreateSkill = async (
  input: string,
  filePaths: string[],
  history: Array<{ role: 'user' | 'assistant', content: string }>
): Promise<ActionResult> => {
  console.log('[DirectCreate] 开始直接创建，输入:', input)

  // 显示进度
  showProgressInCurrentMessage()
  startCreationProgress()
  updateCreationStep('design')

  try {
    // 构建消息：直接告诉 AI 开始创建
    const createMessage = history.length === 0
      ? `${input}\n\n[环境说明]\n这是 Web API 环境。请直接开始创建技能，生成完整的代码。\n代码格式要求：def main(params): ...\n不需要反复确认，直接给出可用的代码。`
      : input

    let fullResponse = ''

    for await (const chunk of agentApi.chatStream({
      message: createMessage,
      history: history,
      skill_ids: skillCreatorId.value ? [skillCreatorId.value] : undefined
    }, abortController.value?.signal)) {
      fullResponse += chunk

      // 流式更新
      if (currentGeneratingMsgId.value) {
        const msgIndex = aiMessages.value.findIndex(m => m.id === currentGeneratingMsgId.value)
        if (msgIndex !== -1) {
          aiMessages.value[msgIndex] = {
            ...aiMessages.value[msgIndex],
            content: fullResponse || '正在创建...'
          }
          scrollToBottom()
        }
      }
    }

    console.log('[DirectCreate] AI 返回，长度:', fullResponse.length)
    updateCreationStep('generate')

    // 尝试提取技能
    const extractedConfig = tryExtractSkillFromResponse(fullResponse, history)

    if (extractedConfig && extractedConfig.code) {
      // 成功提取代码，创建临时技能
      updateCreationStep('create')

      const skillName = generateUniqueName(extractedConfig.name || generateSkillName(input))
      const tempSkill = await skillsApi.createTemp({
        name: skillName,
        description: extractedConfig.description || input,
        icon: extractedConfig.icon || '⚡',
        code: extractedConfig.code,
        tags: extractedConfig.tags || ['自动创建'],
        output_config: extractedConfig.output_type ? { preferred_type: extractedConfig.output_type } : undefined
      })

      tempSkillId.value = tempSkill.temp_id
      tempSkillName.value = skillName
      flowPhase.value = 'preview'

      // 保存当前技能信息
      currentSkillInfo.value = {
        name: skillName,
        description: extractedConfig.description || input,
        icon: extractedConfig.icon || '⚡',
        tags: extractedConfig.tags || ['自动创建'],
        code: extractedConfig.code,
        inputType: extractedConfig.input_type,
        outputType: extractedConfig.output_type
      }

      finishCreationProgress(true)
      hideProgressInCurrentMessage()

      // 返回预览卡片（简洁版）
      return {
        response: `✅ 技能创建完成！`,
        skillCreated: true,
        skillId: tempSkill.temp_id,
        skillName: skillName,
        skillCard: {
          type: 'created',
          name: skillName,
          icon: extractedConfig.icon || '⚡',
          description: extractedConfig.description || input,
          status: 'success',
          details: [
            ...(extractedConfig.input_type ? [{ label: '输入', value: extractedConfig.input_type }] : []),
            ...(extractedConfig.output_type ? [{ label: '输出', value: extractedConfig.output_type }] : [])
          ],
          actions: [
            { label: '🧪 测试一下', action: 'test' },
            { label: '💾 保存技能', action: 'save' },
            { label: '✏️ 调整', action: 'modify' }
          ]
        }
      }
    }

    // 未提取到代码，继续对话
    finishCreationProgress(true)
    hideProgressInCurrentMessage()
    flowPhase.value = 'idle'

    return { response: fullResponse }

  } catch (error: any) {
    console.error('[DirectCreate] 创建失败:', error)
    finishCreationProgress(false)
    hideProgressInCurrentMessage()
    flowPhase.value = 'idle'

    return {
      response: `创建失败: ${error.message || '未知错误'}`,
      skillCard: {
        type: 'created',
        name: '创建失败',
        status: 'error',
        description: error.message || '创建过程中出错',
        actions: [{ label: '重试', action: 'recreate' }]
      }
    }
  }
}

// ============================================================
// 纯透传模式：前端只做 UI 展示，skill-creator 负责所有创建逻辑
// ============================================================

const createSkillFromHistory = async (
  history: Array<{ role: 'user' | 'assistant', content: string }>,
  confirmInput: string
): Promise<ActionResult> => {
  // 显示进度（UI 增强）
  showProgressInCurrentMessage()
  startCreationProgress()
  updateCreationStep('design')

  try {
    // 纯透传：直接把确认消息发给 skill-creator
    // skill-creator 会根据对话历史和用户确认来创建技能
    console.log('[CreateSkill] 纯透传模式，发送确认消息到 skill-creator')

    let fullResponse = ''
    for await (const chunk of agentApi.chatStream({
      message: confirmInput,
      history: history,
      skill_ids: skillCreatorId.value ? [skillCreatorId.value] : undefined
    }, abortController.value?.signal)) {
      fullResponse += chunk

      // 流式更新当前消息
      if (currentGeneratingMsgId.value) {
        const msgIndex = aiMessages.value.findIndex(m => m.id === currentGeneratingMsgId.value)
        if (msgIndex !== -1) {
          aiMessages.value[msgIndex] = {
            ...aiMessages.value[msgIndex],
            content: fullResponse || '正在创建...'
          }
          scrollToBottom()
        }
      }
    }

    console.log('[CreateSkill] skill-creator 返回，长度:', fullResponse.length)

    // UI 增强：尝试从响应中提取技能信息，用于显示卡片
    updateCreationStep('generate')
    const extractedConfig = tryExtractSkillFromResponse(fullResponse, history)

    if (extractedConfig && extractedConfig.code) {
      // 成功提取到技能代码，创建临时技能
      updateCreationStep('create')

      const skillName = generateUniqueName(extractedConfig.name || '新技能')
      const tempSkill = await skillsApi.createTemp({
        name: skillName,
        description: extractedConfig.description || '',
        icon: extractedConfig.icon || '⚡',
        code: extractedConfig.code,
        tags: extractedConfig.tags || ['自动创建'],
        output_config: extractedConfig.output_type ? { preferred_type: extractedConfig.output_type } : undefined
      })

      tempSkillId.value = tempSkill.temp_id
      tempSkillName.value = skillName

      finishCreationProgress(true)
      hideProgressInCurrentMessage()

      // 显示成功卡片
      return {
        response: fullResponse,
        skillCreated: true,
        skillId: tempSkill.temp_id,
        skillName: skillName,
        skillCard: {
          type: 'created',
          name: skillName,
          icon: extractedConfig.icon || '⚡',
          description: extractedConfig.description || '',
          status: 'success',
          details: extractedConfig.output_type ? [{ label: '输出', value: extractedConfig.output_type }] : [],
          actions: [
            { label: '测试', action: 'test' },
            { label: '保存', action: 'save' }
          ]
        }
      }
    }

    // 未提取到代码，直接返回 skill-creator 的响应
    // 用户可以继续对话，让 skill-creator 生成代码
    finishCreationProgress(true)
    hideProgressInCurrentMessage()

    return { response: fullResponse }

  } catch (error: any) {
    console.error('[CreateSkill] 创建失败:', error)
    finishCreationProgress(false)
    hideProgressInCurrentMessage()

    return {
      response: '',
      skillCard: {
        type: 'created',
        name: '创建失败',
        status: 'error',
        description: error.message || '请重新描述需求',
        actions: [{ label: '重试', action: 'retry' }]
      }
    }
  }
}

// UI 增强：尝试从 skill-creator 响应中提取技能信息
// 这是纯粹的 UI 辅助，不影响 skill-creator 的核心功能
const tryExtractSkillFromResponse = (
  response: string,
  history: Array<{ role: 'user' | 'assistant', content: string }>
): any => {
  // 尝试提取 JSON 配置
  const jsonMatch = response.match(/```json\s*([\s\S]*?)\s*```/)
  if (jsonMatch) {
    try {
      const config = JSON.parse(jsonMatch[1])
      if (config.name && config.code) {
        console.log('[Extract] 从 JSON 提取技能:', config.name)
        return config
      }
    } catch (e) {
      // JSON 解析失败，继续尝试其他方式
    }
  }

  // 尝试提取 Python 代码块
  const codeMatch = response.match(/```python\s*([\s\S]*?)\s*```/)
  if (codeMatch?.[1]) {
    const nameMatch = response.match(/"name"\s*:\s*"([^"]+)"/) ||
                      response.match(/技能名称[：:]\s*(.+?)[\n\r]/) ||
                      response.match(/名称[：:]\s*(.+?)[\n\r]/)
    const descMatch = response.match(/"description"\s*:\s*"([^"]+)"/) ||
                      response.match(/描述[：:]\s*(.+?)[\n\r]/)

    // 从对话历史中提取用户需求作为备用描述
    const userMessages = history.filter(m => m.role === 'user').map(m => m.content).join(' ')
    const fallbackName = generateSkillName(userMessages)
    const fallbackDesc = userMessages.slice(0, 100)

    console.log('[Extract] 从 Python 代码块提取技能')
    return {
      name: nameMatch?.[1]?.trim() || fallbackName,
      description: descMatch?.[1]?.trim() || fallbackDesc,
      icon: '⚡',
      tags: ['自动创建'],
      code: codeMatch[1]
    }
  }

  return null
}

// 解析 skill-creator 返回的技能配置
const parseSkillConfig = (result: string, fallbackDesc: string): any => {
  // 尝试提取 JSON
  const jsonMatch = result.match(/```json\s*([\s\S]*?)\s*```/) ||
                    result.match(/\{[\s\S]*"name"[\s\S]*"code"[\s\S]*\}/)

  if (jsonMatch) {
    const jsonStr = jsonMatch[1] || jsonMatch[0]
    try {
      const config = JSON.parse(jsonStr)
      if (config.name && config.code) {
        console.log('[CreateSkill] 成功解析技能配置:', config.name)
        return config
      }
    } catch (e) {
      console.error('[CreateSkill] JSON 解析失败:', e)
      // 尝试修复常见问题
      try {
        const fixedJson = jsonStr.replace(/[\x00-\x1F\x7F]/g, '')
        const config = JSON.parse(fixedJson)
        if (config.name && config.code) return config
      } catch (e2) {
        // 继续尝试其他方式
      }
    }
  }

  // 尝试从文本中提取关键信息
  const nameMatch = result.match(/"name"\s*:\s*"([^"]+)"/)
  const descMatch = result.match(/"description"\s*:\s*"([^"]+)"/)
  const codeMatch = result.match(/```python\s*([\s\S]*?)\s*```/)
  const outputTypeMatch = result.match(/"output_type"\s*:\s*"([^"]+)"/)

  if (codeMatch?.[1]) {
    return {
      name: nameMatch?.[1] || generateSkillName(fallbackDesc),
      description: descMatch?.[1] || fallbackDesc.slice(0, 50),
      icon: '⚡',
      tags: ['自动创建'],
      output_type: outputTypeMatch?.[1],
      code: codeMatch[1]
    }
  }

  return null
}

// 修改现有技能（临时技能或编辑中的永久技能）
// 纯透传模式：直接把修改请求发给 skill-creator
const modifyExistingSkill = async (
  modifyRequest: string,
  history: Array<{ role: 'user' | 'assistant', content: string }>
): Promise<ActionResult> => {
  const skillId = tempSkillId.value || editingSkillId.value
  const isEditingPermanent = !!editingSkillId.value && !tempSkillId.value

  if (!skillId) {
    return { response: '没有可修改的技能。' }
  }

  // 显示进度（UI 增强）
  showProgressInCurrentMessage()
  startCreationProgress()
  creationProgress.value = [
    { id: 'analyze', label: '分析修改', icon: '🔍', status: 'active' },
    { id: 'generate', label: '更新代码', icon: '📝', status: 'pending' },
    { id: 'update', label: '保存更新', icon: '💾', status: 'pending' },
  ]

  try {
    updateCreationStep('generate')
    console.log('[ModifySkill] 纯透传模式，发送修改请求到 skill-creator')

    // 纯透传：直接发送修改请求，带上对话历史
    let fullResponse = ''
    for await (const chunk of agentApi.chatStream({
      message: modifyRequest,
      history: history,
      skill_ids: skillCreatorId.value ? [skillCreatorId.value] : undefined
    }, abortController.value?.signal)) {
      fullResponse += chunk

      // 流式更新当前消息
      if (currentGeneratingMsgId.value) {
        const msgIndex = aiMessages.value.findIndex(m => m.id === currentGeneratingMsgId.value)
        if (msgIndex !== -1) {
          aiMessages.value[msgIndex] = {
            ...aiMessages.value[msgIndex],
            content: fullResponse || '正在修改...'
          }
          scrollToBottom()
        }
      }
    }

    console.log('[ModifySkill] skill-creator 返回，长度:', fullResponse.length)

    // UI 增强：尝试从响应中提取更新后的代码
    const extractedConfig = tryExtractSkillFromResponse(fullResponse, history)

    if (extractedConfig && extractedConfig.code) {
      updateCreationStep('update')

      const updatedName = extractedConfig.name || tempSkillName.value || 'skill'

      if (isEditingPermanent) {
        // 更新永久技能 - 显示模式选择对话框
        finishCreationProgress(true)
        hideProgressInCurrentMessage()

        pendingUpdateData.value = {
          skillId: editingSkillId.value!,
          code: extractedConfig.code,
          skillName: updatedName,
          description: extractedConfig.description || '',
          icon: extractedConfig.icon || '⚡'
        }
        selectedUpdateMode.value = 'new_version'
        showUpdateModeDialog.value = true

        return {
          response: fullResponse,
          pendingModeSelection: true
        }
      } else {
        // 删除旧的临时技能，创建新的
        await skillsApi.deleteTemp(tempSkillId.value!)

        const newTempSkill = await skillsApi.createTemp({
          name: updatedName,
          description: extractedConfig.description,
          code: extractedConfig.code,
          tags: ['自动创建', '已修改']
        })

        tempSkillId.value = newTempSkill.temp_id
        tempSkillName.value = updatedName

        finishCreationProgress(true)
        hideProgressInCurrentMessage()

        return {
          response: fullResponse,
          skillCreated: true,
          skillId: newTempSkill.temp_id,
          skillName: updatedName,
          skillCard: {
            type: 'created',
            name: updatedName,
            icon: extractedConfig.icon || '⚡',
            description: extractedConfig.description || '已更新',
            status: 'success',
            details: [{ label: '版本', value: '已更新' }],
            actions: [
              { label: '测试', action: 'test' },
              { label: '保存', action: 'save' }
            ]
          }
        }
      }
    }

    // 未提取到代码，直接返回 skill-creator 的响应
    finishCreationProgress(true)
    hideProgressInCurrentMessage()

    return { response: fullResponse }

  } catch (error: any) {
    console.error('[ModifySkill] 修改失败:', error)
    finishCreationProgress(false)
    hideProgressInCurrentMessage()

    return {
      response: '',
      skillCard: {
        type: 'created',
        name: tempSkillName.value || '技能',
        status: 'error',
        description: error.message || '修改失败',
        actions: [{ label: '重试', action: 'retry' }]
      }
    }
  }
}

// 生成增强版代码模板
const generateEnhancedCode = (config: any, userRequest: string): string => {
  const name = config.name || 'custom-skill'
  const description = config.description || userRequest.slice(0, 100)

  return `# ${name}
# ${description}

def main(params):
    """
    技能入口函数

    Args:
        params: 参数字典
            - input: 用户输入的文本
            - files: 上传的文件路径列表
            - context: 额外上下文信息

    Returns:
        dict: 执行结果
    """
    user_input = params.get('input', '')
    files = params.get('files', [])
    context = params.get('context', '')

    try:
        # 1. 验证输入
        if not files and not user_input:
            return {
                "status": "error",
                "message": "请提供输入内容或上传文件"
            }

        # 2. 处理文件
        results = []
        if files:
            for file_path in files:
                try:
                    # 根据文件类型处理
                    if file_path.endswith(('.xlsx', '.xls')):
                        df = pd.read_excel(file_path)
                        results.append({
                            "file": file_path,
                            "rows": len(df),
                            "columns": list(df.columns)
                        })
                    elif file_path.endswith('.csv'):
                        df = pd.read_csv(file_path)
                        results.append({
                            "file": file_path,
                            "rows": len(df),
                            "columns": list(df.columns)
                        })
                    else:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        results.append({
                            "file": file_path,
                            "size": len(content)
                        })
                except Exception as e:
                    results.append({
                        "file": file_path,
                        "error": str(e)
                    })

        # 3. 处理文本输入
        if user_input:
            results.append({
                "input_text": user_input[:200] + "..." if len(user_input) > 200 else user_input
            })

        # 4. 返回结果
        return {
            "status": "success",
            "message": f"处理完成，共处理 {len(files)} 个文件",
            "data": results
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"处理失败: {str(e)}"
        }

if __name__ == "__main__":
    # 本地测试
    test_params = {
        "input": "测试输入",
        "files": []
    }
    print(main(test_params))
`
}

// 生成默认代码模板
const generateDefaultCode = (config: any): string => {
  return `# ${config.name}
# ${config.description || ''}

def main(params):
    """
    技能入口函数

    Args:
        params: 包含以下字段的字典
            - input: 用户输入的文本
            - files: 上传的文件路径列表
            - context: 额外上下文

    Returns:
        字典格式的结果
    """
    user_input = params.get('input', '')
    files = params.get('files', [])

    # TODO: 实现技能逻辑
    result = {
        "status": "success",
        "message": f"处理完成: {user_input}",
        "files_processed": len(files)
    }

    return result

if __name__ == "__main__":
    # 测试
    test_params = {"input": "测试", "files": []}
    print(main(test_params))
`
}

// ============================================================
// 执行技能测试 - 使用进度卡片
// ============================================================

const executeSkillTest = async (
  input: string,
  filePaths: string[]
): Promise<ActionResult> => {

  // 支持测试临时技能、编辑中的永久技能、或已保存的技能
  const skillId = tempSkillId.value || editingSkillId.value || finalSkillId.value
  const skillName = tempSkillName.value || finalSkillName.value
  const isTemp = !!tempSkillId.value  // 只有临时技能使用 executeTemp API

  if (!skillId) {
    return {
      response: '还没有创建技能，请先描述你想要的技能功能。'
    }
  }

  // 显示测试进度卡片
  showTestProgressInCurrentMessage()
  startTestProgress()

  try {
    console.log('[SkillTest] 开始测试技能:', skillName, isTemp ? '(临时)' : '(已保存)')
    console.log('[SkillTest] 输入:', input)
    console.log('[SkillTest] 文件:', filePaths)

    // 准备环境
    updateTestStep('prepare')
    await new Promise(r => setTimeout(r, 300))

    // 执行技能
    updateTestStep('execute')

    // 根据技能类型调用不同的 API
    const result = isTemp
      ? await agentApi.executeTemp({
          skill_id: skillId,
          params: {
            input: input,
            files: filePaths,
            context: `测试技能: ${skillName}`
          }
        })
      : await agentApi.execute({
          skill_id: skillId,
          params: {
            input: input,
            files: filePaths,
            context: `测试技能: ${skillName}`
          }
        })

    console.log('[SkillTest] 执行结果:', result)

    // 处理结果
    updateTestStep('process')
    await new Promise(r => setTimeout(r, 200))

    // 生成输出
    updateTestStep('output')
    await new Promise(r => setTimeout(r, 200))

    if (result.success) {
      finishTestProgress(true)
      await new Promise(r => setTimeout(r, 400))
      hideTestProgressInCurrentMessage()

      let outputFile: OutputFileInfo | undefined
      let htmlPreview: string | undefined
      const details: { label: string; value: string }[] = []

      // 处理输出文件
      if (result.output_file) {
        outputFile = {
          name: result.output_file.name,
          type: result.output_file.type,
          url: result.output_file.url,
          size: result.output_file.size
        }
        details.push({ label: '输出文件', value: result.output_file.name })
      }

      // 处理返回结果摘要
      if (result.result && typeof result.result === 'object') {
        if (result.result.status === 'error') {
          // 技能返回错误
          const errorCard: SkillSummaryCard = {
            type: 'tested',
            name: skillName || '技能',
            status: 'error',
            description: result.result.message || '技能执行返回错误',
            actions: isTemp
              ? [{ label: '修改', action: 'modify' }, { label: '重试', action: 'retry' }]
              : [{ label: '重试', action: 'retry' }]
          }
          return { response: '', skillCard: errorCard }
        }
        if (result.result.message) {
          details.push({ label: '结果', value: result.result.message })
        }
      }

      // 检查 HTML 预览
      if (result.output) {
        if (result.output.trim().toLowerCase().startsWith('<!doctype') ||
            result.output.trim().toLowerCase().startsWith('<html')) {
          htmlPreview = result.output
          details.push({ label: '预览', value: 'HTML 页面' })
        }
      }

      // 构建测试成功卡片
      const testCard: SkillSummaryCard = {
        type: 'tested',
        name: skillName || '技能',
        status: 'success',
        description: '测试通过',
        details,
        outputFile,
        actions: isTemp
          ? [{ label: '继续测试', action: 'test' }, { label: '保存', action: 'save' }]
          : [{ label: '继续测试', action: 'test' }]
      }

      // 如果是测试已保存的技能，测试完成后显示返回选项
      if (!isTemp && props.isFromAgent) {
        return {
          response: '',
          outputFile,
          htmlPreview,
          skillCard: testCard,
          showReturnOptions: true
        }
      }

      return { response: '', outputFile, htmlPreview, skillCard: testCard }

    } else {
      finishTestProgress(false)
      await new Promise(r => setTimeout(r, 300))
      hideTestProgressInCurrentMessage()

      // 构建友好的结果卡片
      const details: { label: string; value: string }[] = [
        { label: '📋 执行结果', value: getFriendlyResultText(result.error) },
        { label: '💭 分析', value: getFriendlyThinking(result.error) }
      ]

      // 如果有日志，添加可展开的详情
      if (result.output) {
        details.push({ label: '📝 执行日志', value: result.output })
      }

      const resultCard: SkillSummaryCard = {
        type: 'tested',
        name: skillName || '技能',
        status: 'error',
        description: '结果可能不符合预期',
        details,
        actions: isTemp
          ? [{ label: '重试', action: 'retry' }, { label: '修改代码', action: 'modify' }]
          : [{ label: '重试', action: 'retry' }]
      }

      return { response: '', skillCard: resultCard }
    }

  } catch (error: any) {
    console.error('[SkillTest] 执行异常:', error)
    finishTestProgress(false)
    await new Promise(r => setTimeout(r, 300))
    hideTestProgressInCurrentMessage()

    // 构建友好的结果卡片
    const resultCard: SkillSummaryCard = {
      type: 'tested',
      name: skillName || '技能',
      status: 'error',
      description: '结果可能不符合预期',
      details: [
        { label: '📋 执行结果', value: getFriendlyResultText(error.message) },
        { label: '💭 分析', value: getFriendlyThinking(error.message) }
      ],
      actions: isTemp
        ? [{ label: '重试', action: 'retry' }, { label: '修改代码', action: 'modify' }]
        : [{ label: '重试', action: 'retry' }]
    }

    return { response: '', skillCard: resultCard }
  }
}

// 显示测试进度卡片
const showTestProgressInCurrentMessage = () => {
  if (currentGeneratingMsgId.value) {
    const msgIndex = aiMessages.value.findIndex(m => m.id === currentGeneratingMsgId.value)
    if (msgIndex !== -1) {
      aiMessages.value[msgIndex] = {
        ...aiMessages.value[msgIndex],
        showTestProgress: true,
        generating: true,
        content: ''
      }
      scrollToBottom()
    }
  }
}

// 隐藏测试进度卡片
const hideTestProgressInCurrentMessage = () => {
  if (currentGeneratingMsgId.value) {
    const msgIndex = aiMessages.value.findIndex(m => m.id === currentGeneratingMsgId.value)
    if (msgIndex !== -1) {
      aiMessages.value[msgIndex] = {
        ...aiMessages.value[msgIndex],
        showTestProgress: false
      }
    }
  }
}

// ============================================================
// 正式创建技能 - 将临时技能保存为正式技能
// ============================================================

const finalizeSkill = async (): Promise<ActionResult> => {
  if (!tempSkillId.value) {
    return {
      response: '还没有可以保存的技能。请先创建并测试技能。'
    }
  }

  console.log('[FinalizeSkill] 开始正式保存技能:', tempSkillName.value)

  try {
    // 更新当前消息显示保存状态
    if (currentGeneratingMsgId.value) {
      const msgIndex = aiMessages.value.findIndex(m => m.id === currentGeneratingMsgId.value)
      if (msgIndex !== -1) {
        aiMessages.value[msgIndex] = {
          ...aiMessages.value[msgIndex],
          content: '💾 正在保存技能到技能库...',
          generating: false
        }
        scrollToBottom()
      }
    }

    const skill = await skillsApi.finalizeTemp(tempSkillId.value)
    console.log('[FinalizeSkill] 技能已保存:', skill.id, skill.name)

    const name = tempSkillName.value || skill.name
    const icon = skill.icon || '⚡'
    tempSkillId.value = null
    tempSkillName.value = null

    // 构建保存成功卡片
    const savedCard: SkillSummaryCard = {
      type: 'saved',
      name: name,
      icon: icon,
      description: skill.description || undefined,
      status: 'success',
      details: [
        { label: '状态', value: '已保存到技能库' }
      ],
      actions: []  // 保存后不需要更多操作
    }

    return {
      response: '',
      finalized: true,
      skillId: skill.id,
      skillName: name,
      skillCard: savedCard
    }

  } catch (error: any) {
    console.error('[FinalizeSkill] 保存失败:', error)

    // 构建保存失败卡片
    const errorCard: SkillSummaryCard = {
      type: 'saved',
      name: tempSkillName.value || '技能',
      status: 'error',
      description: error.message || '保存失败',
      actions: [
        { label: '重试', action: 'save' },
        { label: '重建', action: 'recreate' }
      ]
    }
    return { response: '', skillCard: errorCard }
  }
}

// ============================================================
// 清理临时技能
// ============================================================

const cleanupTempSkill = async () => {
  if (tempSkillId.value) {
    try {
      await skillsApi.deleteTemp(tempSkillId.value)
    } catch (e) {
      console.error('Failed to cleanup temp skill:', e)
    }
    tempSkillId.value = null
    tempSkillName.value = null
  }
}

// ============================================================
// 代码编辑器操作
// ============================================================

// 处理技能信息变化
const handleSkillInfoChange = () => {
  // 当用户编辑技能信息时，自动初始化 editingSkillInfo
  if (!editingSkillInfo.value) {
    editingSkillInfo.value = {
      name: tempSkillName.value || 'new-skill',
      description: '',
      icon: '⚡',
      tags: []
    }
  }
}

// 保存代码
const handleSaveCode = async () => {
  if (aiGenerating.value) return

  aiGenerating.value = true

  // 添加用户消息
  aiMessages.value.push({
    id: Date.now(),
    role: 'user',
    content: '💾 保存代码'
  })
  scrollToBottom()

  // 添加 AI 回复占位
  const aiMsgId = Date.now() + 1
  currentGeneratingMsgId.value = aiMsgId
  aiMessages.value.push({
    id: aiMsgId,
    role: 'assistant',
    content: '正在保存...',
    generating: true
  })
  scrollToBottom()

  try {
    const result = await saveManualCodeEdit()

    // 更新 AI 消息
    const msgIndex = aiMessages.value.findIndex(m => m.id === aiMsgId)
    if (msgIndex !== -1) {
      aiMessages.value[msgIndex] = {
        ...aiMessages.value[msgIndex],
        content: result.response,
        generating: false,
        skillCard: result.skillCard
      }
    }

    // 处理特殊动作
    if (result.skillCreated) {
      tempSkillId.value = result.skillId!
      tempSkillName.value = result.skillName!
    }

    if (result.finalized) {
      finalSkillId.value = result.skillId!
      finalSkillName.value = result.skillName!
      emit('submit', { id: result.skillId, name: result.skillName })

      // 添加测试提示消息
      await nextTick()
      awaitingTestDecision.value = true
      aiMessages.value.push({
        id: Date.now(),
        role: 'assistant',
        content: '技能已保存！要测试一下吗？',
        generating: false,
        quickActions: [
          { label: '试一下', action: 'test-skill' },
          { label: '不用了', action: 'skip-test' }
        ]
      })
      scrollToBottom()
    }

  } catch (error: any) {
    const msgIndex = aiMessages.value.findIndex(m => m.id === aiMsgId)
    if (msgIndex !== -1) {
      aiMessages.value[msgIndex] = {
        ...aiMessages.value[msgIndex],
        content: `保存失败：${error.message || '未知错误'}`,
        generating: false
      }
    }
  } finally {
    currentGeneratingMsgId.value = null
    aiGenerating.value = false
    scrollToBottom()
  }
}

// ============================================================
// 关闭处理
// ============================================================

const handleClose = async () => {
  // 清理定时器
  if (creationTimer) {
    clearInterval(creationTimer)
    creationTimer = null
  }
  if (testTimer) {
    clearInterval(testTimer)
    testTimer = null
  }
  isCreatingSkill.value = false
  isTestingSkill.value = false
  awaitingTestDecision.value = false
  finalSkillId.value = null
  finalSkillName.value = null
  await cleanupTempSkill()
  // 清空上传状态
  clearUpload()
  emit('close')
}

// ============================================================
// 监听器
// ============================================================

watch(() => props.show, (newVal) => {
  if (newVal) {
    initConversation()

    // 如果有预填名称，自动开始
    if (props.prefillName) {
      nextTick(() => {
        aiInput.value = `我想创建一个 ${props.prefillName} 技能`
      })
    }
  }
})

// 组件卸载时清理
onUnmounted(() => {
  cleanupTempSkill()
  if (creationTimer) {
    clearInterval(creationTimer)
    creationTimer = null
  }
  if (testTimer) {
    clearInterval(testTimer)
    testTimer = null
  }
})
</script>

<template>
  <Transition name="modal">
    <div v-if="show" class="modal-overlay" @click.self="handleClose">
      <div class="modal-container skill-creator-modal">
        <!-- 头部 -->
        <div class="modal-header">
          <div class="header-left">
            <span class="header-icon">{{ mode === 'upload' ? '📦' : (editSkill ? '✏️' : '🛠️') }}</span>
            <h2>{{ mode === 'upload' ? '上传技能' : (editSkill ? '编辑技能' : '技能工坊') }}</h2>
            <span v-if="mode === 'create' && (tempSkillName || editSkill)" class="skill-badge">
              {{ tempSkillName || editSkill?.name }}
            </span>
          </div>
          <div class="header-right">
            <!-- 代码编辑切换按钮（仅创建/编辑模式） -->
            <button
              v-if="mode === 'create'"
              class="code-toggle-btn"
              :class="{ active: showCodeEditor }"
              @click="toggleCodeEditor"
              title="手动编辑代码"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="16 18 22 12 16 6"/>
                <polyline points="8 6 2 12 8 18"/>
              </svg>
              <span>代码</span>
            </button>
            <button class="close-btn" @click="handleClose">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- 上传模式 -->
        <template v-if="mode === 'upload'">
          <div class="upload-mode">
            <div class="upload-header">
              <div class="upload-icon-big">📦</div>
              <h3>上传技能包</h3>
              <p>上传 ZIP 压缩包导入外部技能</p>
            </div>

            <div
              class="upload-zone"
              :class="{ dragging: uploadIsDragging, 'has-file': uploadZipFile }"
              @dragover.prevent="uploadIsDragging = true"
              @dragleave="uploadIsDragging = false"
              @drop.prevent="handleUploadDrop"
            >
              <input
                type="file"
                accept=".zip"
                @change="handleUploadFileSelect"
              />
              <template v-if="!uploadZipFile">
                <div class="upload-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="17 8 12 3 7 8"/>
                    <line x1="12" y1="3" x2="12" y2="15"/>
                  </svg>
                </div>
                <span class="upload-text">拖放 ZIP 文件到这里</span>
                <span class="upload-hint">或点击选择技能压缩包</span>
              </template>
              <template v-else>
                <div class="folder-preview">
                  <span class="folder-icon">📦</span>
                  <div class="folder-details">
                    <span class="folder-name">{{ uploadFolderName }}</span>
                    <span class="folder-size">{{ (uploadZipFile.size / 1024).toFixed(1) }} KB</span>
                  </div>
                  <button
                    class="remove-btn"
                    :disabled="isAnalyzing"
                    :class="{ disabled: isAnalyzing }"
                    @click.stop="clearUpload"
                  >✕</button>
                </div>
              </template>
            </div>

            <div v-if="uploadError" class="upload-error">
              <span>⚠️</span> {{ uploadError }}
            </div>

            <!-- 解析结果预览卡片 -->
            <div v-if="uploadParsedData" class="upload-preview-card">
              <div class="preview-header">
                <span class="preview-icon">{{ uploadParsedData.icon }}</span>
                <div class="preview-title">
                  <span class="preview-name">{{ uploadParsedData.name }}</span>
                  <span class="preview-version">v{{ uploadVersion }}</span>
                </div>
                <span v-if="uploadParsedData.aiAnalysis?.complexity" class="complexity-badge" :class="uploadParsedData.aiAnalysis.complexity">
                  {{ uploadParsedData.aiAnalysis.complexity }}
                </span>
              </div>

              <div class="preview-desc">{{ uploadParsedData.description }}</div>

              <!-- AI 分析结果 -->
              <div v-if="uploadParsedData.aiAnalysis && !uploadParsedData.aiAnalysis.error" class="ai-analysis">
                <div class="ai-header">
                  <span>🤖</span>
                  <span>AI 智能分析</span>
                </div>

                <div v-if="uploadParsedData.aiAnalysis.capabilities?.length" class="ai-section">
                  <div class="ai-label">功能特性</div>
                  <div class="ai-capabilities">
                    <span v-for="cap in uploadParsedData.aiAnalysis.capabilities" :key="cap" class="capability-item">✓ {{ cap }}</span>
                  </div>
                </div>

                <div class="ai-io-row">
                  <div v-if="uploadParsedData.aiAnalysis.input_types?.length" class="ai-io">
                    <span class="io-label">📥 输入</span>
                    <span class="io-value">{{ uploadParsedData.aiAnalysis.input_types.join('、') }}</span>
                  </div>
                  <div v-if="uploadParsedData.aiAnalysis.output_types?.length" class="ai-io">
                    <span class="io-label">📤 输出</span>
                    <span class="io-value">{{ uploadParsedData.aiAnalysis.output_types.join('、') }}</span>
                  </div>
                </div>
              </div>

              <div class="preview-meta">
                <div class="meta-item">
                  <span class="meta-label">作者</span>
                  <span class="meta-value">{{ uploadAuthor || '未知' }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">入口</span>
                  <span class="meta-value">{{ uploadEntryScript || '自动检测' }}</span>
                </div>
              </div>

              <div v-if="uploadParsedData.tags.length" class="preview-tags">
                <span v-for="tag in uploadParsedData.tags" :key="tag" class="preview-tag">{{ tag }}</span>
              </div>

              <div v-if="uploadParsedData.files.length" class="preview-files">
                <div class="files-header">
                  <span>📁 包含文件 ({{ uploadParsedData.files.length }})</span>
                </div>
                <div class="files-list">
                  <span v-for="f in uploadParsedData.files.slice(0, 5)" :key="f" class="file-item">{{ f }}</span>
                  <span v-if="uploadParsedData.files.length > 5" class="file-more">+{{ uploadParsedData.files.length - 5 }} 更多</span>
                </div>
              </div>

              <div class="preview-note">
                <span>📦</span>
                <span>上传后此技能将标记为"已上传"，不可编辑</span>
              </div>
            </div>

            <div class="upload-actions">
              <button class="btn-cancel" @click="handleClose">取消</button>
              <button class="btn-submit" :disabled="!uploadZipFile || isUploading || isAnalyzing" @click="handleUploadSubmit">
                <template v-if="isAnalyzing">
                  <span class="btn-spinner"></span>
                  分析中...
                </template>
                <template v-else-if="isUploading">
                  <span class="btn-spinner"></span>
                  上传中...
                </template>
                <template v-else>
                  上传并导入
                </template>
              </button>
            </div>
          </div>
        </template>

        <!-- 创建/编辑模式 -->
        <template v-else>
          <!-- 来自 Agent 提示 -->
          <div v-if="isFromAgent" class="agent-hint">
            <span>🤖</span>
            <span>来自 Agent 任务，创建后自动返回</span>
          </div>

          <!-- 对话区域 -->
          <div class="chat-area" ref="aiChatContainer">
          <div v-for="msg in aiMessages" :key="msg.id" class="chat-msg" :class="msg.role">
            <div class="msg-bubble" :class="{ 'with-progress': (msg.showProgress && isCreatingSkill) || (msg.showTestProgress && isTestingSkill) }">
              <!-- 测试进度卡片 -->
              <div v-if="msg.showTestProgress && isTestingSkill" class="test-progress-card">
                <div class="progress-header">
                  <div class="progress-icon test">
                    <svg class="play-icon" viewBox="0 0 24 24" fill="currentColor">
                      <polygon points="5 3 19 12 5 21 5 3"/>
                    </svg>
                  </div>
                  <div class="progress-title">
                    <span>正在测试技能</span>
                    <span class="elapsed-time">{{ formatTime(testElapsedTime) }}</span>
                  </div>
                </div>

                <div class="progress-steps">
                  <div
                    v-for="(step, index) in testProgress"
                    :key="step.id"
                    class="progress-step"
                    :class="step.status"
                  >
                    <div class="step-indicator">
                      <span v-if="step.status === 'done'" class="check">✓</span>
                      <span v-else-if="step.status === 'active'" class="step-spinner"></span>
                      <span v-else-if="step.status === 'error'" class="error-mark">!</span>
                      <span v-else class="step-number">{{ index + 1 }}</span>
                    </div>
                    <span class="step-icon">{{ step.icon }}</span>
                    <span class="step-label">{{ step.label }}</span>
                  </div>
                </div>

                <div class="progress-bar-container">
                  <div class="progress-bar test">
                    <div class="progress-bar-fill" :style="{ width: testProgressPercentage + '%' }"></div>
                    <div class="progress-bar-glow"></div>
                  </div>
                </div>

                <div v-if="testEncouragement" class="progress-encouragement">
                  {{ testEncouragement }}
                </div>
              </div>
              <!-- 创建进度卡片 -->
              <div v-else-if="msg.showProgress && isCreatingSkill" class="creation-progress-card">
                <div class="progress-header">
                  <div class="progress-icon">
                    <svg class="gear-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="3"/>
                      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                    </svg>
                  </div>
                  <div class="progress-title">
                    <span>正在创建技能</span>
                    <span class="elapsed-time">{{ formatTime(creationElapsedTime) }}</span>
                  </div>
                </div>

                <div class="progress-steps">
                  <div
                    v-for="(step, index) in creationProgress"
                    :key="step.id"
                    class="progress-step"
                    :class="step.status"
                  >
                    <div class="step-indicator">
                      <span v-if="step.status === 'done'" class="check">✓</span>
                      <span v-else-if="step.status === 'active'" class="step-spinner"></span>
                      <span v-else-if="step.status === 'error'" class="error-mark">!</span>
                      <span v-else class="step-number">{{ index + 1 }}</span>
                    </div>
                    <span class="step-icon">{{ step.icon }}</span>
                    <span class="step-label">{{ step.label }}</span>
                  </div>
                </div>

                <div class="progress-bar-container">
                  <div class="progress-bar">
                    <div class="progress-bar-fill" :style="{ width: progressPercentage + '%' }"></div>
                    <div class="progress-bar-glow"></div>
                  </div>
                </div>

                <div v-if="creationEncouragement" class="progress-encouragement">
                  {{ creationEncouragement }}
                </div>
              </div>
              <!-- 加载动画（普通对话）- 点击可取消 -->
              <div v-else-if="msg.generating" class="generating-bubble" @click="cancelGeneration" title="点击取消">
                <div class="typing">
                  <span></span><span></span><span></span>
                </div>
              </div>
              <!-- 技能摘要卡片 -->
              <div v-else-if="msg.skillCard" class="skill-summary-card" :class="[msg.skillCard.type, msg.skillCard.status]">
                <div class="card-header">
                  <span class="card-icon">{{ msg.skillCard.icon || (msg.skillCard.status === 'success' ? '✅' : '💡') }}</span>
                  <div class="card-title">
                    <span class="skill-name">{{ msg.skillCard.name }}</span>
                    <span class="card-status" :class="msg.skillCard.status">
                      {{ msg.skillCard.type === 'created' ? '已创建' : msg.skillCard.type === 'tested' ? (msg.skillCard.status === 'success' ? '测试通过' : '需要调整') : '已保存' }}
                    </span>
                  </div>
                </div>
                <p v-if="msg.skillCard.description" class="card-description">{{ msg.skillCard.description }}</p>
                <div v-if="msg.skillCard.details?.length" class="card-details">
                  <div v-for="(detail, idx) in msg.skillCard.details" :key="idx" class="detail-item">
                    <span class="detail-label">{{ detail.label }}</span>
                    <span class="detail-value">{{ detail.value }}</span>
                  </div>
                </div>
                <!-- 输出文件（如果有） -->
                <div v-if="msg.skillCard.outputFile" class="card-output-file">
                  <span class="file-icon">{{ getFileIcon(msg.skillCard.outputFile.type) }}</span>
                  <span class="file-name">{{ msg.skillCard.outputFile.name }}</span>
                  <a :href="msg.skillCard.outputFile.url" target="_blank" class="download-link" download>下载</a>
                </div>
                <div v-if="msg.skillCard.actions?.length" class="card-actions">
                  <button
                    v-for="(action, idx) in msg.skillCard.actions"
                    :key="idx"
                    class="action-btn"
                    :class="action.action"
                    @click="handleCardAction(action.action)"
                  >
                    {{ action.label }}
                  </button>
                </div>
              </div>
              <!-- 消息内容 -->
              <template v-else>
                <div v-if="msg.content" class="msg-text" v-html="formatMessage(msg.content)"></div>

                <!-- 输出文件 -->
                <div v-if="msg.outputFile" class="output-file">
                  <div class="file-card">
                    <span class="file-icon">{{ getFileIcon(msg.outputFile.type) }}</span>
                    <div class="file-info">
                      <span class="file-name">{{ msg.outputFile.name }}</span>
                      <span class="file-size">{{ msg.outputFile.size || '' }}</span>
                    </div>
                    <a :href="msg.outputFile.url" target="_blank" class="download-btn" download>
                      下载
                    </a>
                  </div>
                </div>

                <!-- HTML 预览 -->
                <div v-if="msg.htmlPreview" class="html-preview">
                  <details>
                    <summary>查看预览</summary>
                    <iframe :srcdoc="msg.htmlPreview" sandbox="allow-scripts"></iframe>
                  </details>
                </div>

                <!-- 快捷操作按钮 -->
                <div v-if="msg.quickActions?.length" class="quick-actions">
                  <button
                    v-for="(qa, idx) in msg.quickActions"
                    :key="idx"
                    class="quick-action-btn"
                    :class="qa.action"
                    @click="handleCardAction(qa.action, qa.data)"
                  >
                    {{ qa.label }}
                  </button>
                </div>
              </template>
            </div>
          </div>
        </div>

        <!-- 代码编辑器面板 -->
        <Transition name="slide">
          <div v-if="showCodeEditor" class="code-editor-panel">
            <div class="code-editor-header">
              <span class="code-editor-title">📝 代码编辑器</span>
              <div class="code-editor-actions">
                <button class="save-code-btn" @click="handleSaveCode" :disabled="aiGenerating">
                  💾 保存代码
                </button>
              </div>
            </div>
            <div v-if="editingSkillInfo" class="code-editor-info">
              <input
                v-model="editingSkillInfo.name"
                class="skill-name-input"
                placeholder="技能名称"
              />
              <input
                v-model="editingSkillInfo.description"
                class="skill-desc-input"
                placeholder="技能描述"
              />
            </div>
            <textarea
              v-model="codeEditorContent"
              class="code-editor-textarea"
              placeholder="# 在这里编写 Python 代码&#10;&#10;def main(params):&#10;    user_input = params.get('input', '')&#10;    files = params.get('files', [])&#10;    &#10;    return {'status': 'success', 'message': '完成'}"
              spellcheck="false"
            ></textarea>
          </div>
        </Transition>

        <!-- 输入区域 -->
        <div
          class="input-area"
          :class="{ 'drag-over': isDraggingFile }"
          @dragover="handleDragOver"
          @dragleave="handleDragLeave"
          @drop="handleFileDrop"
        >
          <!-- 拖拽提示 -->
          <div v-if="isDraggingFile" class="drag-overlay">
            <span>📂 释放以上传文件</span>
          </div>

          <!-- 已上传文件 -->
          <div v-if="uploadedFiles.length > 0" class="uploaded-files">
            <div
              v-for="file in uploadedFiles"
              :key="file.id"
              class="uploaded-file"
              :class="{ 'uploading': file.uploading, 'error': file.uploadError }"
            >
              <span class="file-icon">{{ getFileIcon(file.type) }}</span>
              <div class="file-details">
                <span class="file-name">{{ file.name }}</span>
                <span v-if="file.uploading" class="status uploading">上传中...</span>
                <span v-else-if="file.uploadError" class="status error">{{ file.uploadError }}</span>
                <span v-else-if="file.serverPath" class="status success">✓</span>
                <span v-else class="status">{{ formatFileSize(file.size) }}</span>
              </div>
              <button class="remove-btn" @click="removeFile(file.id)">×</button>
            </div>
          </div>

          <!-- 输入框 -->
          <div class="input-wrapper" :class="{ disabled: aiGenerating }">
            <input
              ref="fileInputRef"
              type="file"
              multiple
              accept="*/*"
              style="display: none"
              @change="handleFileSelect"
            />
            <button class="upload-btn" @click="triggerFileUpload" :disabled="aiGenerating">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
              </svg>
            </button>
            <textarea
              v-model="aiInput"
              :placeholder="aiGenerating ? 'AI 正在处理中...' : (hasTestableSkill ? '输入测试内容、上传文件，或说明需要修改什么...' : '描述你想创建的技能...')"
              @keydown.enter.exact.prevent="handleUserInput(aiInput)"
              :disabled="aiGenerating"
              :readonly="aiGenerating"
              rows="1"
            ></textarea>
            <button
              class="send-btn"
              @click="handleUserInput(aiInput)"
              :disabled="(!aiInput.trim() && !uploadedFiles.some(f => f.serverPath)) || aiGenerating"
            >
              <template v-if="aiGenerating">
                <span class="loading-spinner"></span>
              </template>
              <template v-else>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="22" y1="2" x2="11" y2="13"/>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
              </template>
            </button>
          </div>

          <!-- 状态提示 -->
          <div class="status-hint">
            <template v-if="aiGenerating">
              <span class="dot generating"></span>
              AI 正在处理，请稍候...
            </template>
            <template v-else-if="hasTestableSkill">
              <span class="dot active"></span>
              技能已就绪，可以测试
            </template>
            <template v-else>
              <span class="dot"></span>
              描述你的需求来创建技能
            </template>
          </div>
        </div>
        </template>
      </div>
    </div>
  </Transition>

  <!-- 更新模式选择对话框 -->
  <Transition name="modal">
    <div v-if="showUpdateModeDialog" class="modal-overlay update-mode-overlay" @click.self="cancelUpdate">
      <div class="update-mode-dialog">
        <div class="dialog-header">
          <span class="dialog-icon">💾</span>
          <h3>选择保存方式</h3>
        </div>

        <div class="dialog-body">
          <p class="dialog-hint">修改技能「{{ pendingUpdateData?.skillName }}」，请选择保存方式：</p>

          <div class="mode-options">
            <label
              class="mode-option"
              :class="{ selected: selectedUpdateMode === 'overwrite' }"
            >
              <input
                type="radio"
                v-model="selectedUpdateMode"
                value="overwrite"
              />
              <div class="option-content">
                <div class="option-title">
                  <span class="option-icon">🔄</span>
                  覆盖当前版本
                </div>
                <div class="option-desc">
                  直接修改当前版本，不保留历史记录。
                  <br/>适合小修改、bug修复。
                </div>
              </div>
            </label>

            <label
              class="mode-option"
              :class="{ selected: selectedUpdateMode === 'new_version' }"
            >
              <input
                type="radio"
                v-model="selectedUpdateMode"
                value="new_version"
              />
              <div class="option-content">
                <div class="option-title">
                  <span class="option-icon">📦</span>
                  创建新版本
                </div>
                <div class="option-desc">
                  保留当前版本，创建新版本。
                  <br/>适合重大改动，可随时回退。
                </div>
              </div>
            </label>
          </div>
        </div>

        <div class="dialog-footer">
          <button class="btn-cancel" @click="cancelUpdate">取消</button>
          <button class="btn-confirm" @click="executeUpdate">
            {{ selectedUpdateMode === 'overwrite' ? '覆盖保存' : '创建新版本' }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script lang="ts">
// 格式化消息（Markdown 简单处理）
function formatMessage(content: string): string {
  return content
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
}
</script>

<style scoped>
/* ============================================================ */
/* Modal 基础样式 */
/* ============================================================ */

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.skill-creator-modal {
  position: relative;
  width: 90%;
  max-width: 800px;
  height: 85vh;
  background: #fff;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

/* ============================================================ */
/* 头部 */
/* ============================================================ */

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
  color: white;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  font-size: 24px;
}

.modal-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.skill-badge {
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.code-toggle-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  color: white;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.code-toggle-btn:hover {
  background: rgba(255, 255, 255, 0.25);
}

.code-toggle-btn.active {
  background: white;
  color: #8e44ad;
  border-color: white;
}

.code-toggle-btn svg {
  width: 16px;
  height: 16px;
}

.close-btn {
  width: 32px;
  height: 32px;
  padding: 0;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.close-btn svg {
  width: 18px;
  height: 18px;
}

/* Agent 提示 */
.agent-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #f3e8ff;
  color: #6b21a8;
  font-size: 13px;
}

/* ============================================================ */
/* 对话区域 */
/* ============================================================ */

.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-msg {
  display: flex;
  max-width: 85%;
}

.chat-msg.user {
  align-self: flex-end;
}

.chat-msg.assistant {
  align-self: flex-start;
}

.msg-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  line-height: 1.6;
  font-size: 14px;
}

.chat-msg.user .msg-bubble {
  background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.chat-msg.assistant .msg-bubble {
  background: #f3f4f6;
  color: #1f2937;
  border-bottom-left-radius: 4px;
}

.msg-text {
  word-break: break-word;
}

.msg-text :deep(code) {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 13px;
}

.msg-text :deep(pre) {
  background: #1e293b;
  color: #e2e8f0;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 10px 0;
}

.msg-text :deep(pre code) {
  background: transparent;
  padding: 0;
  color: inherit;
}

.msg-text :deep(strong) {
  font-weight: 600;
}

/* ============================================================ */
/* 创建进度卡片 */
/* ============================================================ */

.msg-bubble.with-progress {
  background: transparent !important;
  padding: 0 !important;
}

.creation-progress-card {
  background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%);
  border: 1px solid #9b59b6;
  border-radius: 16px;
  padding: 20px;
  min-width: 320px;
  box-shadow: 0 4px 20px rgba(155, 89, 182, 0.2);
}

.progress-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.progress-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.gear-icon {
  width: 24px;
  height: 24px;
  color: white;
  animation: rotate 3s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.progress-title {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.progress-title span:first-child {
  font-size: 16px;
  font-weight: 600;
  color: #6b21a8;
}

.elapsed-time {
  font-size: 13px;
  color: #7c3aed;
  font-weight: 500;
}

.progress-steps {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.progress-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  flex: 1;
  opacity: 0.4;
  transition: all 0.3s ease;
}

.progress-step.active {
  opacity: 1;
}

.progress-step.done {
  opacity: 1;
}

.step-indicator {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  background: #f3e8ff;
  border: 2px solid #9b59b6;
  color: #6b21a8;
  transition: all 0.3s ease;
}

.progress-step.active .step-indicator {
  background: #9b59b6;
  border-color: #9b59b6;
  color: white;
  box-shadow: 0 0 12px rgba(155, 89, 182, 0.5);
}

.progress-step.done .step-indicator {
  background: #10b981;
  border-color: #10b981;
  color: white;
}

.step-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.check {
  font-size: 14px;
}

.step-icon {
  font-size: 18px;
}

.step-label {
  font-size: 11px;
  color: #6b21a8;
  font-weight: 500;
  text-align: center;
}

.progress-step.active .step-label {
  font-weight: 600;
}

.progress-bar-container {
  margin-bottom: 12px;
}

.progress-bar {
  height: 6px;
  background: rgba(155, 89, 182, 0.2);
  border-radius: 3px;
  overflow: hidden;
  position: relative;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #9b59b6 0%, #8e44ad 100%);
  border-radius: 3px;
  transition: width 0.5s ease;
  position: relative;
}

.progress-bar-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.4) 50%,
    transparent 100%
  );
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.progress-encouragement {
  text-align: center;
  font-size: 13px;
  color: #7c3aed;
  font-style: italic;
  animation: fadeInOut 2s ease-in-out infinite;
}

@keyframes fadeInOut {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

/* 测试进度卡片 */
.test-progress-card {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border: 1px solid #3b82f6;
  border-radius: 16px;
  padding: 20px;
  min-width: 320px;
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.2);
}

.test-progress-card .progress-header .progress-icon.test {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}

.test-progress-card .progress-title span:first-child {
  color: #1e40af;
}

.test-progress-card .elapsed-time {
  color: #3b82f6;
}

.test-progress-card .step-indicator {
  background: #dbeafe;
  border-color: #3b82f6;
  color: #1e40af;
}

.test-progress-card .progress-step.active .step-indicator {
  background: #3b82f6;
  border-color: #3b82f6;
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.5);
}

.test-progress-card .step-label {
  color: #1e40af;
}

.test-progress-card .progress-bar.test {
  background: rgba(59, 130, 246, 0.2);
}

.test-progress-card .progress-bar-fill {
  background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
}

.test-progress-card .progress-encouragement {
  color: #3b82f6;
}

.play-icon {
  width: 20px;
  height: 20px;
  color: white;
  animation: pulse-play 1.5s ease-in-out infinite;
}

@keyframes pulse-play {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.error-mark {
  color: #ef4444;
  font-weight: bold;
}

.progress-step.error .step-indicator {
  background: #fee2e2 !important;
  border-color: #ef4444 !important;
  color: #ef4444 !important;
}

/* ============================================================ */
/* 技能摘要卡片 */
/* ============================================================ */

.skill-summary-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  min-width: 300px;
  max-width: 400px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border: 2px solid #e5e7eb;
}

.skill-summary-card.created.success {
  border-color: #10b981;
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
}

.skill-summary-card.tested.success {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
}

.skill-summary-card.tested.error,
.skill-summary-card.created.error {
  border-color: #eab308;
  background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
}

.skill-summary-card.saved.success {
  border-color: #8b5cf6;
  background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
}

.skill-summary-card.saved.error {
  border-color: #eab308;
  background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
}

.skill-summary-card .card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.skill-summary-card .card-icon {
  font-size: 32px;
  line-height: 1;
}

.skill-summary-card .card-title {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.skill-summary-card .skill-name {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.skill-summary-card .card-status {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 10px;
  display: inline-block;
  width: fit-content;
}

.skill-summary-card .card-status.success {
  background: #d1fae5;
  color: #059669;
}

.skill-summary-card .card-status.error {
  background: #f3e8ff;
  color: #6b21a8;
}

.skill-summary-card .card-description {
  color: #4b5563;
  font-size: 14px;
  margin: 0 0 12px 0;
  line-height: 1.5;
}

.skill-summary-card .card-details {
  background: rgba(255, 255, 255, 0.5);
  border-radius: 10px;
  padding: 10px 12px;
  margin-bottom: 12px;
}

.skill-summary-card.error .card-details {
  background: rgba(254, 226, 226, 0.5);
}

.skill-summary-card.error .detail-label {
  color: #dc2626;
  font-weight: 500;
}

.skill-summary-card .detail-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 6px 0;
  gap: 12px;
}

.skill-summary-card .detail-item:not(:last-child) {
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.skill-summary-card .detail-label {
  color: #6b7280;
  font-size: 12px;
  flex-shrink: 0;
  min-width: 40px;
}

.skill-summary-card .detail-value {
  color: #1f2937;
  font-size: 13px;
  font-weight: 500;
  word-break: break-word;
  text-align: right;
  flex: 1;
}

/* 结果卡片的详情样式（友好展示） */
.skill-summary-card.error .card-details {
  background: rgba(254, 243, 199, 0.5);
}

.skill-summary-card.error .detail-item {
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  padding: 8px 0;
}

.skill-summary-card.error .detail-label {
  color: #6b21a8;
  font-weight: 600;
  font-size: 13px;
}

.skill-summary-card.error .detail-value {
  text-align: left;
  font-size: 13px;
  font-weight: 400;
  color: #78350f;
  padding: 0;
  width: 100%;
  line-height: 1.5;
  background: none;
  border: none;
}

/* 执行日志（第三项）使用特殊样式 */
.skill-summary-card.error .detail-item:nth-child(3) .detail-value {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 11px;
  background: rgba(255, 255, 255, 0.6);
  padding: 8px 10px;
  border-radius: 6px;
  white-space: pre-wrap;
  max-height: 120px;
  overflow-y: auto;
}

.skill-summary-card .card-output-file {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  margin-bottom: 12px;
}

.skill-summary-card .card-output-file .file-icon {
  font-size: 20px;
}

.skill-summary-card .card-output-file .file-name {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.skill-summary-card .card-output-file .download-link {
  color: #3b82f6;
  font-size: 12px;
  font-weight: 500;
  text-decoration: none;
}

.skill-summary-card .card-output-file .download-link:hover {
  text-decoration: underline;
}

.skill-summary-card .card-actions {
  display: flex;
  gap: 10px;
}

.skill-summary-card .action-btn {
  flex: 1;
  padding: 10px 16px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.skill-summary-card .action-btn.test,
.skill-summary-card .action-btn.retry {
  background: #f3f4f6;
  color: #4b5563;
}

.skill-summary-card .action-btn.test:hover,
.skill-summary-card .action-btn.retry:hover {
  background: #e5e7eb;
}

.skill-summary-card .action-btn.save {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.skill-summary-card .action-btn.save:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.skill-summary-card .action-btn.modify {
  background: #9b59b6;
  color: white;
}

.skill-summary-card .action-btn.modify:hover {
  background: #8e44ad;
}

.skill-summary-card .action-btn.recreate {
  background: #ef4444;
  color: white;
}

.skill-summary-card .action-btn.recreate:hover {
  background: #dc2626;
}

/* 快捷操作按钮 */
.quick-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.quick-action-btn {
  padding: 8px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #fff;
  font-size: 13px;
  color: #333;
  cursor: pointer;
  transition: all 0.15s;
}

.quick-action-btn:hover {
  background: #f5f5f5;
  border-color: #ccc;
}

.quick-action-btn.test-skill,
.quick-action-btn.return-to-agent {
  background: #1a73e8;
  border-color: #1a73e8;
  color: #fff;
}

.quick-action-btn.test-skill:hover,
.quick-action-btn.return-to-agent:hover {
  background: #1557b0;
  border-color: #1557b0;
}

.quick-action-btn.skip-test,
.quick-action-btn.stay-here,
.quick-action-btn.continue {
  background: #f5f5f5;
  border-color: #ddd;
  color: #666;
}

.quick-action-btn.skip-test:hover,
.quick-action-btn.stay-here:hover,
.quick-action-btn.continue:hover {
  background: #eee;
}

.quick-action-btn.save-extracted-skill {
  background: #10b981;
  border-color: #10b981;
  color: #fff;
}

.quick-action-btn.save-extracted-skill:hover {
  background: #059669;
  border-color: #059669;
}

/* 生成中气泡 - 点击可取消 */
.generating-bubble {
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.2s;
}

.generating-bubble:hover {
  background: #fee2e2;
}

.generating-bubble:hover .typing span {
  background: #ef4444;
}

/* 加载动画 */
.typing {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing span {
  width: 8px;
  height: 8px;
  background: #9ca3af;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.typing span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 输出文件 */
.output-file {
  margin-top: 12px;
}

.file-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
}

.file-card .file-icon {
  font-size: 24px;
}

.file-card .file-info {
  flex: 1;
  min-width: 0;
}

.file-card .file-name {
  display: block;
  font-weight: 500;
  font-size: 13px;
  color: #1f2937;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-card .file-size {
  font-size: 11px;
  color: #6b7280;
}

.file-card .download-btn {
  padding: 6px 12px;
  background: #9b59b6;
  color: white;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  text-decoration: none;
  transition: background 0.2s;
}

.file-card .download-btn:hover {
  background: #8e44ad;
}

/* HTML 预览 */
.html-preview {
  margin-top: 12px;
}

.html-preview details {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.html-preview summary {
  padding: 8px 12px;
  cursor: pointer;
  font-size: 12px;
  color: #6b7280;
  background: #f9fafb;
}

.html-preview iframe {
  width: 100%;
  height: 300px;
  border: none;
  border-top: 1px solid #e5e7eb;
}

/* ============================================================ */
/* 输入区域 */
/* ============================================================ */

.input-area {
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
  background: #fafafa;
  position: relative;
}

.input-area.drag-over {
  background: #f3e8ff;
}

.drag-overlay {
  position: absolute;
  inset: 0;
  background: rgba(245, 158, 11, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: #8e44ad;
  border: 2px dashed #9b59b6;
  border-radius: 12px;
  z-index: 10;
}

/* 已上传文件 */
.uploaded-files {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.uploaded-file {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  max-width: 200px;
}

.uploaded-file.uploading {
  border-color: #9b59b6;
  background: #fffbeb;
}

.uploaded-file.error {
  border-color: #ef4444;
  background: #fef2f2;
}

.uploaded-file .file-icon {
  font-size: 16px;
}

.uploaded-file .file-details {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.uploaded-file .file-name {
  font-size: 11px;
  font-weight: 500;
  color: #374151;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.uploaded-file .status {
  font-size: 10px;
  color: #6b7280;
}

.uploaded-file .status.uploading {
  color: #8e44ad;
}

.uploaded-file .status.success {
  color: #10b981;
}

.uploaded-file .status.error {
  color: #ef4444;
}

.uploaded-file .remove-btn {
  width: 18px;
  height: 18px;
  padding: 0;
  background: transparent;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
}

.uploaded-file .remove-btn:hover {
  color: #ef4444;
}

/* 输入框 */
.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 4px 4px 4px 14px;
  transition: all 0.2s;
}

.input-wrapper:focus-within {
  border-color: #9b59b6;
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.1);
}

.input-wrapper.disabled {
  background: #f3f4f6;
  border-color: #e5e7eb;
}

.input-wrapper.disabled textarea {
  color: #9ca3af;
  cursor: not-allowed;
}

.input-wrapper textarea {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 14px;
  color: #1f2937;
  resize: none;
  min-height: 36px;
  max-height: 120px;
  line-height: 1.5;
  padding: 8px 0;
  font-family: inherit;
}

.input-wrapper textarea::placeholder {
  color: #9ca3af;
}

.upload-btn,
.send-btn {
  width: 36px;
  height: 36px;
  padding: 0;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.upload-btn {
  background: transparent;
  color: #9ca3af;
}

.upload-btn:hover:not(:disabled) {
  background: #f3f4f6;
  color: #6b7280;
}

.send-btn {
  background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
  color: white;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
}

.send-btn:disabled,
.upload-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.upload-btn svg,
.send-btn svg {
  width: 18px;
  height: 18px;
}

/* 状态提示 */
.status-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  font-size: 12px;
  color: #6b7280;
}

.status-hint .dot {
  width: 6px;
  height: 6px;
  background: #d1d5db;
  border-radius: 50%;
}

.status-hint .dot.active {
  background: #10b981;
}

.status-hint .dot.generating {
  background: #9b59b6;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.2);
  }
}

/* 发送按钮加载动画 */
.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ============================================================ */
/* 上传模式 */
/* ============================================================ */

.upload-mode {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 40px;
  overflow: auto;
}

.upload-header {
  text-align: center;
  margin-bottom: 30px;
}

.upload-icon-big {
  font-size: 48px;
  margin-bottom: 12px;
}

.upload-header h3 {
  margin: 0 0 8px 0;
  font-size: 22px;
  font-weight: 600;
  color: #1f2937;
}

.upload-header p {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.upload-zone {
  position: relative;
  border: 2px dashed #d1d5db;
  border-radius: 16px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #fafafa;
}

.upload-zone:hover {
  border-color: #9b59b6;
  background: #fffbeb;
}

.upload-zone.dragging {
  border-color: #9b59b6;
  background: #f3e8ff;
  transform: scale(1.02);
}

.upload-zone.has-file {
  border-style: solid;
  border-color: #10b981;
  background: #ecfdf5;
}

.upload-zone input[type="file"] {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.upload-icon {
  margin-bottom: 16px;
}

.upload-icon svg {
  width: 48px;
  height: 48px;
  color: #9ca3af;
}

.upload-text {
  display: block;
  font-size: 16px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.upload-hint {
  display: block;
  font-size: 13px;
  color: #9ca3af;
}

.folder-preview {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.folder-icon {
  font-size: 32px;
}

.folder-details {
  flex: 1;
  text-align: left;
}

.folder-name {
  display: block;
  font-weight: 500;
  color: #1f2937;
}

.folder-size {
  font-size: 12px;
  color: #6b7280;
}

.folder-preview .remove-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: #fee2e2;
  color: #ef4444;
  border-radius: 50%;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.folder-preview .remove-btn:hover:not(:disabled) {
  background: #ef4444;
  color: white;
}

.folder-preview .remove-btn.disabled,
.folder-preview .remove-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.upload-error {
  margin-top: 16px;
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
}

/* 上传预览卡片 */
.upload-preview-card {
  margin-top: 20px;
  padding: 16px;
  background: linear-gradient(135deg, #faf5ff 0%, #fef9c3 100%);
  border: 1px solid #fde047;
  border-radius: 12px;
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.preview-icon {
  width: 40px;
  height: 40px;
  background: #fff;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.preview-title {
  flex: 1;
}

.preview-name {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.preview-version {
  font-size: 12px;
  color: #6b7280;
}

.preview-desc {
  font-size: 14px;
  color: #4b5563;
  line-height: 1.5;
  margin-bottom: 12px;
  padding: 10px;
  background: rgba(255,255,255,0.6);
  border-radius: 8px;
}

.preview-meta {
  display: flex;
  gap: 20px;
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.meta-label {
  color: #9ca3af;
}

.meta-value {
  color: #374151;
  font-weight: 500;
}

.preview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.preview-tag {
  padding: 3px 10px;
  background: #fff;
  border-radius: 12px;
  font-size: 12px;
  color: #6366f1;
  border: 1px solid #c7d2fe;
}

.preview-files {
  background: rgba(255,255,255,0.7);
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 12px;
}

.files-header {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 8px;
}

.files-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.file-item {
  padding: 2px 8px;
  background: #f3f4f6;
  border-radius: 4px;
  font-size: 11px;
  color: #4b5563;
  font-family: monospace;
}

.file-more {
  padding: 2px 8px;
  background: #e5e7eb;
  border-radius: 4px;
  font-size: 11px;
  color: #6b7280;
}

.preview-note {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: rgba(245, 158, 11, 0.1);
  border-radius: 6px;
  font-size: 12px;
  color: #6b21a8;
}

/* 复杂度徽章 */
.complexity-badge {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}

.complexity-badge.简单 {
  background: #d1fae5;
  color: #047857;
}

.complexity-badge.中等 {
  background: #f3e8ff;
  color: #7c3aed;
}

.complexity-badge.复杂 {
  background: #fee2e2;
  color: #b91c1c;
}

/* AI 分析区域 */
.ai-analysis {
  margin: 12px 0;
  padding: 12px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border: 1px solid #93c5fd;
  border-radius: 10px;
}

.ai-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #1e40af;
  margin-bottom: 10px;
}

.ai-section {
  margin-bottom: 10px;
}

.ai-label {
  font-size: 11px;
  color: #6b7280;
  margin-bottom: 6px;
}

.ai-capabilities {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.capability-item {
  font-size: 13px;
  color: #1f2937;
  padding-left: 4px;
}

.ai-io-row {
  display: flex;
  gap: 16px;
}

.ai-io {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.io-label {
  font-size: 11px;
  color: #6b7280;
}

.io-value {
  font-size: 12px;
  color: #374151;
  font-weight: 500;
}

.upload-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 30px;
}

.upload-actions .btn-cancel {
  padding: 10px 24px;
  background: #f3f4f6;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #4b5563;
  cursor: pointer;
  transition: background 0.2s;
}

.upload-actions .btn-cancel:hover {
  background: #e5e7eb;
}

.upload-actions .btn-submit {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-actions .btn-submit:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
}

.upload-actions .btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.upload-actions .btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* ============================================================ */
/* 动画 */
/* ============================================================ */

.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .skill-creator-modal,
.modal-leave-to .skill-creator-modal {
  transform: scale(0.95) translateY(20px);
}

/* ============================================================ */
/* 代码编辑器面板 */
/* ============================================================ */

.code-editor-panel {
  position: absolute;
  top: 60px;
  right: 0;
  bottom: 0;
  width: 50%;
  background: #1e1e1e;
  border-left: 1px solid #333;
  display: flex;
  flex-direction: column;
  z-index: 10;
}

.code-editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #252525;
  border-bottom: 1px solid #333;
}

.code-editor-title {
  color: #e0e0e0;
  font-size: 14px;
  font-weight: 500;
}

.code-editor-actions {
  display: flex;
  gap: 8px;
}

.save-code-btn {
  padding: 6px 14px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 6px;
  color: white;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.save-code-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.save-code-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.code-editor-info {
  display: flex;
  gap: 8px;
  padding: 10px 16px;
  background: #2a2a2a;
  border-bottom: 1px solid #333;
}

.skill-name-input,
.skill-desc-input {
  flex: 1;
  padding: 8px 12px;
  background: #1e1e1e;
  border: 1px solid #444;
  border-radius: 6px;
  color: #e0e0e0;
  font-size: 13px;
}

.skill-name-input {
  max-width: 180px;
}

.skill-name-input:focus,
.skill-desc-input:focus {
  outline: none;
  border-color: #8e44ad;
}

.code-editor-textarea {
  flex: 1;
  width: 100%;
  padding: 16px;
  background: #1e1e1e;
  border: none;
  color: #d4d4d4;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 14px;
  line-height: 1.6;
  resize: none;
  tab-size: 4;
}

.code-editor-textarea:focus {
  outline: none;
}

.code-editor-textarea::placeholder {
  color: #666;
}

/* Slide transition for code editor */
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

/* ========== 更新模式选择对话框 ========== */
.update-mode-overlay {
  z-index: 1100;  /* 高于主模态框 */
}

.update-mode-dialog {
  background: #1e1e2e;
  border-radius: 16px;
  width: 420px;
  max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  overflow: hidden;
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.dialog-icon {
  font-size: 24px;
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #e2e8f0;
}

.dialog-body {
  padding: 20px 24px;
}

.dialog-hint {
  margin: 0 0 16px;
  font-size: 14px;
  color: #94a3b8;
}

.mode-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mode-option {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 2px solid transparent;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mode-option:hover {
  background: rgba(255, 255, 255, 0.06);
}

.mode-option.selected {
  background: rgba(99, 102, 241, 0.1);
  border-color: #6366f1;
}

.mode-option input[type="radio"] {
  margin-top: 4px;
  accent-color: #6366f1;
  transform: scale(1.2);
}

.option-content {
  flex: 1;
}

.option-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 6px;
}

.option-icon {
  font-size: 16px;
}

.option-desc {
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.5;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.btn-cancel {
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 500;
  color: #94a3b8;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #e2e8f0;
}

.btn-confirm {
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-confirm:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}
</style>
