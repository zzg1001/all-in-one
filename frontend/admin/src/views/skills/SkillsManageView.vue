<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { skillsApi, type Skill } from '@/api'
import Toast from '@/components/Toast.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

// 组件引用
const toast = ref<InstanceType<typeof Toast> | null>(null)
const confirmDialog = ref<InstanceType<typeof ConfirmDialog> | null>(null)

// 状态
const skills = ref<Skill[]>([])
const loading = ref(false)
const searchQuery = ref('')

// 多选
const selectedIds = ref<Set<string>>(new Set())

// 版本信息缓存
const versionCache = ref<Record<string, { version: string; updated_at: string | null }>>({})

// 浮框位置
const tooltipStyle = ref({ top: '0px', left: '0px' })
const activeTooltipId = ref<string | null>(null)

// 计算浮框位置
const showTooltip = (e: MouseEvent, skillId: string) => {
  const card = (e.currentTarget as HTMLElement)
  const rect = card.getBoundingClientRect()
  tooltipStyle.value = {
    top: `${rect.top - 8}px`,
    left: `${rect.left + rect.width / 2}px`
  }
  activeTooltipId.value = skillId
}

const hideTooltip = () => {
  activeTooltipId.value = null
}

// 获取版本信息
const getVersionInfo = async (skillId: string) => {
  if (versionCache.value[skillId]) return
  try {
    const info = await skillsApi.getVersion(skillId)
    versionCache.value[skillId] = info
  } catch (e) {
    console.warn('获取版本信息失败:', e)
  }
}

// 上传弹窗
const showUploadModal = ref(false)
const uploadForm = ref({ name: '', description: '', icon: '⚡', tags: '', version: '1.0.0', entry_script: 'main.py' })
const uploadFile = ref<File | null>(null)
const uploading = ref(false)
const parsing = ref(false)
const parsed = ref(false)  // 是否已解析
const fileInputRef = ref<HTMLInputElement | null>(null)
const batchFileInputRef = ref<HTMLInputElement | null>(null)
const parsedFiles = ref<string[]>([])  // 解析出的文件列表
const isDragging = ref(false)  // 文件拖拽状态

// 弹框拖动（只改变位置，不改变窗口大小）
const modalPos = ref({ x: 0, y: 0 })
let modalDragStart: { mouseX: number; mouseY: number; posX: number; posY: number } | null = null

const onModalDrag = (e: MouseEvent) => {
  if (!modalDragStart) return
  modalPos.value = {
    x: modalDragStart.posX + (e.clientX - modalDragStart.mouseX),
    y: modalDragStart.posY + (e.clientY - modalDragStart.mouseY)
  }
}

const stopModalDrag = () => {
  modalDragStart = null
  window.removeEventListener('mousemove', onModalDrag)
  window.removeEventListener('mouseup', stopModalDrag)
}

const startModalDrag = (e: MouseEvent) => {
  modalDragStart = {
    mouseX: e.clientX,
    mouseY: e.clientY,
    posX: modalPos.value.x,
    posY: modalPos.value.y
  }
  window.addEventListener('mousemove', onModalDrag)
  window.addEventListener('mouseup', stopModalDrag)
}

// 创建弹窗
const showCreateModal = ref(false)
const createForm = ref({ name: '', description: '', icon: '⚡', tags: '', code: '' })
const creating = ref(false)

// 过滤后的技能列表
const filteredSkills = computed(() => {
  if (!searchQuery.value) return skills.value
  const q = searchQuery.value.toLowerCase()
  return skills.value.filter(s =>
    s.name.toLowerCase().includes(q) ||
    s.description?.toLowerCase().includes(q) ||
    s.tags?.some(t => t.toLowerCase().includes(q))
  )
})

// 统计
const stats = computed(() => ({
  total: skills.value.length,
  selected: selectedIds.value.size
}))

// 加载数据
const loadSkills = async (showLoading = true) => {
  // 清除选择状态
  selectedIds.value.clear()

  // 只有首次加载才显示 loading（页面为空时）
  if (showLoading && skills.value.length === 0) {
    loading.value = true
  }

  try {
    skills.value = await skillsApi.getAll()
  } catch (e) {
    console.error('加载技能失败:', e)
  } finally {
    loading.value = false
  }
}

// 切换选择
const toggleSelect = (id: string) => {
  if (selectedIds.value.has(id)) {
    selectedIds.value.delete(id)
  } else {
    selectedIds.value.add(id)
  }
}

// 打开上传弹窗
const openUploadModal = () => {
  uploadForm.value = { name: '', description: '', icon: '⚡', tags: '', version: '1.0.0', entry_script: 'main.py' }
  uploadFile.value = null
  parsed.value = false
  parsedFiles.value = []
  modalPos.value = { x: 0, y: 0 }
  showUploadModal.value = true
}

// 解析文件
const parseFile = async (file: File) => {
  if (!file.name.endsWith('.zip')) {
    toast.value?.warning('请选择 ZIP 文件')
    return
  }

  uploadFile.value = file
  parsed.value = false
  parsing.value = true

  try {
    const preview = await skillsApi.preview(file)
    uploadForm.value = {
      name: preview.name || file.name.replace('.zip', ''),
      description: preview.description || '',
      icon: preview.icon || '⚡',
      tags: preview.tags?.join(', ') || '',
      version: preview.version || '1.0.0',
      entry_script: preview.entry_script || 'main.py'
    }
    parsedFiles.value = preview.files || []
    parsed.value = true
    toast.value?.show('解析成功', 'dark')
  } catch (e) {
    toast.value?.error('解析失败: ' + e)
    uploadForm.value.name = file.name.replace('.zip', '')
    parsed.value = true
  } finally {
    parsing.value = false
  }
}

// 选择文件
const handleFileSelect = async (e: Event) => {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  await parseFile(input.files[0])
}

// 拖拽处理
const handleDragOver = (e: DragEvent) => {
  e.preventDefault()
  if (!parsing.value) isDragging.value = true
}

const handleDragLeave = () => {
  isDragging.value = false
}

const handleDrop = async (e: DragEvent) => {
  e.preventDefault()
  isDragging.value = false
  if (parsing.value) return

  const files = e.dataTransfer?.files
  if (files?.length) {
    await parseFile(files[0])
  }
}

// 批量上传文件选择
const handleBatchFileSelect = async (e: Event) => {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return

  const files = Array.from(input.files)
  uploading.value = true
  let successCount = 0

  for (const file of files) {
    try {
      await skillsApi.upload(file, {
        name: file.name.replace('.zip', ''),
        icon: '⚡'
      })
      successCount++
    } catch (e) {
      console.error(`上传 ${file.name} 失败:`, e)
    }
  }

  uploading.value = false
  toast.value?.success(`批量上传完成：${successCount}/${files.length} 个`)
  loadSkills(false)
  input.value = ''
}

// 上传技能
const handleUpload = async () => {
  if (!uploadFile.value) {
    toast.value?.warning('请选择 ZIP 文件')
    return
  }
  if (!uploadForm.value.name) {
    toast.value?.warning('请输入技能名称')
    return
  }

  uploading.value = true
  try {
    // 上传到本地
    const result = await skillsApi.upload(uploadFile.value, {
      name: uploadForm.value.name,
      description: uploadForm.value.description,
      icon: uploadForm.value.icon,
      tags: uploadForm.value.tags,
      version: uploadForm.value.version,
      entry_script: uploadForm.value.entry_script
    })

    // 直接添加到列表（不刷新页面）
    skills.value.push(result)

    // 关闭弹框
    showUploadModal.value = false

    toast.value?.success('上传成功')
  } catch (e) {
    toast.value?.error('上传失败: ' + e)
  } finally {
    uploading.value = false
  }
}

// 打开创建弹窗
const openCreateModal = () => {
  createForm.value = { name: '', description: '', icon: '⚡', tags: '', code: '' }
  showCreateModal.value = true
}

// 创建技能
const handleCreate = async () => {
  if (!createForm.value.name) {
    toast.value?.warning('请输入技能名称')
    return
  }

  creating.value = true
  try {
    const result = await skillsApi.create({
      name: createForm.value.name,
      description: createForm.value.description,
      icon: createForm.value.icon,
      tags: createForm.value.tags ? createForm.value.tags.split(',').map(t => t.trim()) : [],
      code: createForm.value.code
    })
    // 直接添加到列表
    skills.value.push(result)
    showCreateModal.value = false
    toast.value?.success('创建成功')
  } catch (e) {
    toast.value?.error('创建失败: ' + e)
  } finally {
    creating.value = false
  }
}

// 下载技能
const downloadSkill = async (skill: Skill) => {
  const filename = `${skill.name.replace(/\s+/g, '_')}_v${skill.version || '1.0.0'}.zip`
  try {
    await skillsApi.download(skill.id, filename)
    toast.value?.success(`下载成功: ${skill.name}`)
  } catch (e: any) {
    console.error('下载失败:', e)
    toast.value?.error(`下载失败: ${e.message || '未知错误'}`)
  }
}

// 批量下载
const batchDownload = () => {
  if (selectedIds.value.size === 0) {
    toast.value?.warning('请先选择要下载的技能')
    return
  }
  selectedIds.value.forEach(id => {
    const skill = skills.value.find(s => s.id === id)
    if (skill) downloadSkill(skill)
  })
  toast.value?.success(`开始下载 ${selectedIds.value.size} 个技能`)
}

// 删除技能（软删除，后台异步清理文件）
const deleteSkill = async (skill: Skill) => {
  try {
    await skillsApi.delete(skill.id)
    skills.value = skills.value.filter(s => s.id !== skill.id)
    selectedIds.value.delete(skill.id)
    toast.value?.show(`已删除「${skill.name}」`, 'dark')
  } catch (e) {
    toast.value?.error('删除失败')
  }
}

// 批量删除（软删除，后台异步清理文件）
const batchDelete = async () => {
  if (selectedIds.value.size === 0) {
    toast.value?.warning('请先选择要删除的技能')
    return
  }

  const idsToDelete = Array.from(selectedIds.value)
  let successCount = 0
  for (const id of idsToDelete) {
    try {
      await skillsApi.delete(id)
      skills.value = skills.value.filter(s => s.id !== id)
      successCount++
    } catch (e) {
      console.error(`删除失败:`, e)
    }
  }
  selectedIds.value.clear()
  toast.value?.show(`已删除 ${successCount} 个技能`, 'dark')
}

// 截断文本
const truncate = (text: string | undefined, maxLen: number) => {
  if (!text) return ''
  return text.length > maxLen ? text.slice(0, maxLen) + '...' : text
}

// 图标
const icons = ['⚡', '🔧', '📊', '📝', '💻', '🌐', '🔍', '✨', '🎨', '📚', '💼', '📈', '🎯', '🚀']

onMounted(() => {
  loadSkills()
})
</script>

<template>
  <Toast ref="toast" />
  <ConfirmDialog ref="confirmDialog" />
  <div class="skills-page">
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-stats">
        <span class="stat-item">
          <span class="stat-dot"></span>
          {{ stats.total }} 个技能
        </span>
      </div>
      <div class="toolbar-actions">
        <div class="search-box">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
          <input v-model="searchQuery" type="text" placeholder="搜索" />
        </div>
        <button class="btn-add" @click="openCreateModal">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M12 5v14M5 12h14"/>
          </svg>
          创建
        </button>
      </div>
    </div>

    <!-- 技能卡片网格 -->
    <div class="skills-grid">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
      </div>
      <template v-else>
        <!-- 技能卡片 -->
        <div
          v-for="skill in filteredSkills"
          :key="skill.id"
          class="skill-card"
          :class="{ selected: selectedIds.has(skill.id) }"
          @click="toggleSelect(skill.id)"
          @mouseenter="(e) => { getVersionInfo(skill.id); showTooltip(e, skill.id) }"
          @mouseleave="hideTooltip"
        >
          <div class="card-main">
            <div class="card-icon">{{ skill.icon || '⚡' }}</div>
            <div class="card-info">
              <div class="card-name">{{ skill.name }}</div>
              <div class="card-desc">{{ skill.description || '暂无描述' }}</div>
            </div>
          </div>
          <div class="card-footer">
            <div class="card-left">
              <div class="card-tags" v-if="skill.tags?.length">
                <span v-for="tag in skill.tags.slice(0, 2)" :key="tag">{{ tag }}</span>
              </div>
            </div>
            <div class="card-right">
              <span class="card-version">v{{ skill.version || '1.0' }}</span>
            </div>
          </div>

          <!-- 悬浮操作 -->
          <div class="card-actions">
            <button class="action-btn" title="下载技能包" @click.stop="downloadSkill(skill)">
              <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>
            </button>
            <button class="action-btn danger" title="删除技能" @click.stop="deleteSkill(skill)">
              <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>
            </button>
          </div>

        </div>

        <!-- 上传占位卡片 -->
        <div class="skill-card add-card" @click="openUploadModal">
          <input
            ref="batchFileInputRef"
            type="file"
            accept=".zip"
            multiple
            style="display:none"
            @change="handleBatchFileSelect"
          />
          <div class="add-content">
            <div class="add-icon">+</div>
            <div class="add-text">上传技能</div>
          </div>
        </div>
      </template>
    </div>

    <!-- 全局版本浮框 -->
    <Teleport to="body">
      <div
        v-if="activeTooltipId"
        class="skill-tooltip-fixed"
        :style="{ top: tooltipStyle.top, left: tooltipStyle.left }"
      >
        <template v-for="skill in filteredSkills" :key="skill.id">
          <template v-if="skill.id === activeTooltipId">
            <div class="tooltip-name">{{ skill.name }}</div>
            <div class="tooltip-desc">{{ skill.description || '暂无描述' }}</div>
            <div class="tooltip-version">
              <span>版本: v{{ versionCache[skill.id]?.version || skill.version || '1.0.0' }}</span>
              <span v-if="versionCache[skill.id]?.updated_at">更新: {{ versionCache[skill.id].updated_at }}</span>
            </div>
          </template>
        </template>
      </div>
    </Teleport>

    <!-- 上传弹窗 -->
    <div v-if="showUploadModal" class="modal-overlay" @click.self="showUploadModal = false">
      <div
        class="modal-content apple-modal"
        :style="{ transform: `translate(${modalPos.x}px, ${modalPos.y}px)` }"
      >
        <div class="modal-header-mini drag-handle" @mousedown.prevent="startModalDrag">
          <span>上传技能</span>
          <button class="close-x" @mousedown.stop @click="showUploadModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <!-- 步骤 1: 选择文件 -->
          <div
            class="upload-area"
            :class="{ parsing: parsing, dragging: isDragging }"
            @click="!parsing && fileInputRef?.click()"
            @dragover="handleDragOver"
            @dragleave="handleDragLeave"
            @drop="handleDrop"
          >
            <input ref="fileInputRef" type="file" accept=".zip" style="display:none" @change="handleFileSelect" />
            <div v-if="!uploadFile && !parsing" class="upload-placeholder">
              <span class="upload-icon">📦</span>
              <p>{{ isDragging ? '松开即可上传' : '点击或拖拽 ZIP 文件' }}</p>
            </div>
            <div v-else-if="parsing" class="parsing-animation">
              <div class="parse-spinner"></div>
              <div class="parse-text">正在解析技能包...</div>
              <div class="parse-dots"><span></span><span></span><span></span></div>
            </div>
            <div v-else class="upload-file-info">
              <span class="file-icon">✓</span>
              <span class="file-name">{{ uploadFile?.name }}</span>
            </div>
          </div>

          <!-- 步骤 2: 编辑信息（解析后显示） -->
          <template v-if="parsed">
            <div class="form-section">
              <div class="form-row">
                <label>图标</label>
                <div class="icon-picker-sm">
                  <button v-for="icon in icons" :key="icon" :class="{ active: uploadForm.icon === icon }" @click="uploadForm.icon = icon">{{ icon }}</button>
                </div>
              </div>
              <div class="form-row-grid">
                <div class="form-row">
                  <label>名称 *</label>
                  <input v-model="uploadForm.name" type="text" placeholder="技能名称" />
                </div>
                <div class="form-row">
                  <label>版本</label>
                  <input v-model="uploadForm.version" type="text" placeholder="1.0.0" />
                </div>
              </div>
              <div class="form-row">
                <label>描述</label>
                <textarea v-model="uploadForm.description" rows="3" placeholder="技能描述"></textarea>
              </div>
              <div class="form-row-grid">
                <div class="form-row">
                  <label>标签</label>
                  <input v-model="uploadForm.tags" type="text" placeholder="逗号分隔" />
                </div>
                <div class="form-row">
                  <label>入口脚本</label>
                  <input v-model="uploadForm.entry_script" type="text" placeholder="main.py" />
                </div>
              </div>
            </div>

            <!-- 文件列表预览 -->
            <div v-if="parsedFiles.length" class="files-preview">
              <div class="files-header">包含文件 ({{ parsedFiles.length }})</div>
              <div class="files-list">
                <span v-for="f in parsedFiles.slice(0, 8)" :key="f" class="file-tag">{{ f }}</span>
                <span v-if="parsedFiles.length > 8" class="file-tag more">+{{ parsedFiles.length - 8 }}</span>
              </div>
            </div>
          </template>

          <div class="tip-box">提交后保存到本地</div>
        </div>
        <div class="modal-footer-apple">
          <button class="apple-btn primary" :disabled="uploading || parsing || !parsed" @click="handleUpload">
            {{ uploading ? '提交中...' : parsing ? '解析中...' : '提交' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 创建弹窗 -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>创建技能</h3>
          <button class="close-btn" @click="showCreateModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <label>图标</label>
            <div class="icon-picker-sm">
              <button v-for="icon in icons" :key="icon" :class="{ active: createForm.icon === icon }" @click="createForm.icon = icon">{{ icon }}</button>
            </div>
          </div>
          <div class="form-row">
            <label>名称 *</label>
            <input v-model="createForm.name" type="text" placeholder="技能名称" />
          </div>
          <div class="form-row">
            <label>描述</label>
            <input v-model="createForm.description" type="text" placeholder="简短描述" />
          </div>
          <div class="form-row">
            <label>标签</label>
            <input v-model="createForm.tags" type="text" placeholder="逗号分隔" />
          </div>
          <div class="form-row">
            <label>代码</label>
            <textarea v-model="createForm.code" rows="8" placeholder="# 技能入口代码&#10;def main():&#10;    pass"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showCreateModal = false">取消</button>
          <button class="btn-primary" :disabled="creating" @click="handleCreate">
            {{ creating ? '创建中...' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.skills-page {
  height: 100%;
  min-height: 100vh;
  background: linear-gradient(180deg, #f5f5f7 0%, #e8e8ed 100%);
  display: flex;
  flex-direction: column;
}

/* 工具栏 - 固定在顶部 */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 20px;
  background: white;
  border-bottom: 1px solid rgba(0,0,0,0.08);
  position: sticky;
  top: 0;
  z-index: 100;
}

.toolbar-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #86868b;
}

.stat-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #007aff;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: rgba(0,0,0,0.04);
  border-radius: 8px;
  width: 160px;
}

.search-box svg {
  width: 14px;
  height: 14px;
  color: #86868b;
  flex-shrink: 0;
}

.search-box input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 13px;
  outline: none;
  color: #1d1d1f;
}

.search-box input::placeholder {
  color: #86868b;
}

.btn-icon {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(0,0,0,0.04);
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #86868b;
  transition: all 0.15s;
}

.btn-icon:hover {
  background: rgba(0,0,0,0.08);
  color: #007aff;
}

.btn-icon svg {
  width: 16px;
  height: 16px;
}

.btn-add {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  background: #007aff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-add:hover {
  background: #0066d6;
}

.btn-add:active {
  transform: scale(0.96);
}

.btn-add svg {
  width: 12px;
  height: 12px;
}

.btn-icon:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-push {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  background: #34c759;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-push:hover {
  background: #2db84d;
}

.btn-push:active {
  transform: scale(0.96);
}

.btn-push:disabled {
  background: #a8e6b8;
  cursor: not-allowed;
}

.btn-push svg {
  width: 12px;
  height: 12px;
}

.push-badge {
  background: rgba(255,255,255,0.3);
  font-size: 10px;
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 8px;
  margin-left: 2px;
}

.btn-text {
  padding: 6px 12px;
  border: 1px solid #e2e8f0;
  background: white;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  color: #64748b;
}

.btn-text:hover, .btn-text.active {
  background: #f1f5f9;
  color: #3b82f6;
}

.btn-primary {
  padding: 6px 14px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-primary:disabled {
  background: #93c5fd;
  cursor: not-allowed;
}

/* 内容区 - 可滚动 */
.skills-grid {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  align-content: start;
}

.skill-card {
  background: white;
  border-radius: 12px;
  padding: 14px;
  cursor: pointer;
  position: relative;
  border: 1px solid #e2e8f0;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  min-height: 100px;
}

.skill-card:hover {
  border-color: #c7d2fe;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.12);
  transform: translateY(-2px);
}

.skill-card.selected {
  border-color: #007aff;
  background: linear-gradient(135deg, #e0f2ff 0%, #f0f9ff 100%);
  box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.2);
}

/* 卡片主体 */
.card-main {
  display: flex;
  gap: 12px;
  flex: 1;
}

.card-icon {
  font-size: 20px;
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.card-info {
  flex: 1;
  min-width: 0;
}

.card-name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-desc {
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 卡片底部 */
.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #f1f5f9;
}

.card-left {
  flex: 1;
  min-width: 0;
}

.card-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.card-tags {
  display: flex;
  gap: 4px;
}

.card-tags span {
  padding: 2px 8px;
  background: #f1f5f9;
  border-radius: 4px;
  font-size: 10px;
  color: #64748b;
}

.sync-badge {
  font-size: 10px;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.sync-badge.synced {
  background: #dcfce7;
  color: #16a34a;
}

.sync-badge.not-synced {
  background: #fef3c7;
  color: #d97706;
}

.card-version {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 500;
}

/* 悬浮操作按钮 */
.card-actions {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  gap: 6px;
  opacity: 0;
  transition: opacity 0.2s;
}

.skill-card:hover .card-actions {
  opacity: 1;
}

.action-btn {
  width: 30px;
  height: 30px;
  border: none;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: all 0.15s;
}

.action-btn:hover {
  background: #e0f2fe;
  color: #0284c7;
  transform: scale(1.1);
}

.action-btn.sync:hover {
  background: #dcfce7;
  color: #16a34a;
}

.action-btn.danger:hover {
  background: #fee2e2;
  color: #dc2626;
}

.action-btn svg {
  width: 14px;
  height: 14px;
}

/* 版本浮框 - fixed 定位，显示在卡片上方 */
.skill-tooltip-fixed {
  position: fixed;
  transform: translate(-50%, -100%);
  background: rgba(30, 41, 59, 0.95);
  color: white;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 12px;
  z-index: 9999;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  max-width: 280px;
  pointer-events: none;
}

.skill-tooltip-fixed::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: rgba(30, 41, 59, 0.95);
}

.tooltip-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.tooltip-desc {
  opacity: 0.85;
  margin-bottom: 6px;
  line-height: 1.4;
}

.tooltip-version {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-top: 6px;
  border-top: 1px solid rgba(255,255,255,0.2);
  font-size: 11px;
  opacity: 0.75;
}

/* 上传占位卡片 */
.add-card {
  border: 2px dashed #d1d5db;
  background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.add-card:hover {
  border-color: #6366f1;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
}

.add-content {
  text-align: center;
}

.add-icon {
  font-size: 28px;
  color: #9ca3af;
  font-weight: 300;
  line-height: 1;
}

.add-text {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 6px;
}

.add-card:hover .add-icon,
.add-card:hover .add-text {
  color: #6366f1;
}

/* Loading */
.loading-state {
  grid-column: 1 / -1;
  padding: 60px;
  text-align: center;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 440px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}

.modal-sm {
  width: 360px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
}

.close-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: #f1f5f9;
  border-radius: 6px;
  font-size: 18px;
  cursor: pointer;
  color: #64748b;
}

/* Apple 风格弹框 */
.apple-modal {
  border-radius: 14px;
  overflow: hidden;
}

.modal-header-mini {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header-mini span {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

/* 弹框表头可拖动 */
.drag-handle {
  cursor: move;
  user-select: none;
}

.close-x {
  width: 20px;
  height: 20px;
  border: none;
  background: transparent;
  font-size: 16px;
  cursor: pointer;
  color: #9ca3af;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.close-x:hover {
  background: #e5e7eb;
  color: #374151;
}

.modal-footer-apple {
  padding: 12px 16px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
}

.apple-btn {
  padding: 6px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.apple-btn.primary {
  background: #007aff;
  color: white;
}

.apple-btn.primary:hover {
  background: #0066d6;
}

.apple-btn.primary:disabled {
  background: #a8d4ff;
  cursor: not-allowed;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.apple-modal .modal-body {
  padding: 14px 16px;
}

.upload-area {
  border: 2px dashed #e2e8f0;
  border-radius: 10px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  margin-bottom: 16px;
}

.apple-modal .upload-area {
  padding: 16px;
  margin-bottom: 12px;
}

.upload-area.parsing {
  border-color: #6366f1;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  cursor: default;
}

.upload-area.dragging {
  border-color: #22c55e;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  transform: scale(1.02);
}

.upload-area.dragging .upload-icon {
  animation: pulse 0.5s ease-in-out infinite alternate;
}

@keyframes pulse {
  from { transform: scale(1); }
  to { transform: scale(1.1); }
}

/* 解析动画 */
.parsing-animation {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
}

.parse-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e0e7ff;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.parse-text {
  font-size: 13px;
  color: #4f46e5;
  font-weight: 500;
}

.parse-dots {
  display: flex;
  gap: 4px;
}

.parse-dots span {
  width: 6px;
  height: 6px;
  background: #6366f1;
  border-radius: 50%;
  animation: bounce 1.4s ease-in-out infinite;
}

.parse-dots span:nth-child(1) { animation-delay: 0s; }
.parse-dots span:nth-child(2) { animation-delay: 0.2s; }
.parse-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.4;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.upload-area:hover {
  border-color: #3b82f6;
  background: #f8fafc;
}

.upload-icon {
  font-size: 32px;
}

.upload-placeholder p {
  margin: 8px 0 4px;
  font-size: 13px;
  color: #475569;
}

.upload-file-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-icon {
  font-size: 16px;
  width: 24px;
  height: 24px;
  background: #dcfce7;
  color: #16a34a;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.file-name {
  font-size: 14px;
  color: #334155;
  font-weight: 500;
}

.parsing-badge {
  padding: 3px 8px;
  background: #fef3c7;
  color: #d97706;
  border-radius: 4px;
  font-size: 11px;
}

.parsed-badge {
  padding: 3px 8px;
  background: #dcfce7;
  color: #16a34a;
  border-radius: 4px;
  font-size: 11px;
}

.form-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.form-row-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.files-preview {
  margin-top: 12px;
  padding: 10px;
  background: #f8fafc;
  border-radius: 8px;
}

.files-header {
  font-size: 11px;
  color: #64748b;
  margin-bottom: 8px;
}

.files-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.file-tag {
  padding: 2px 8px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  font-size: 11px;
  color: #475569;
}

.file-tag.more {
  background: #e0e7ff;
  border-color: #c7d2fe;
  color: #4f46e5;
}

.form-row {
  margin-bottom: 14px;
}

.form-row label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #475569;
  margin-bottom: 6px;
}

.form-row input,
.form-row textarea {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
}

.form-row input:focus,
.form-row textarea:focus {
  outline: none;
  border-color: #3b82f6;
}

.form-row textarea {
  resize: vertical;
  font-family: monospace;
}

.icon-picker-sm {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.icon-picker-sm button {
  width: 30px;
  height: 30px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: white;
  font-size: 16px;
  cursor: pointer;
}

.icon-picker-sm button:hover {
  border-color: #3b82f6;
}

.icon-picker-sm button.active {
  border-color: #3b82f6;
  background: #eff6ff;
}

.tip-box {
  padding: 10px;
  background: #f0fdf4;
  border-radius: 6px;
  font-size: 11px;
  color: #16a34a;
  text-align: center;
}

.apple-modal .tip-box {
  padding: 8px;
  margin-top: 12px;
}

.apple-modal .form-section {
  margin-top: 12px;
  padding-top: 12px;
}

.apple-modal .form-row {
  margin-bottom: 10px;
}

.apple-modal .form-row label {
  font-size: 11px;
  margin-bottom: 4px;
}

.apple-modal .form-row input,
.apple-modal .form-row textarea {
  padding: 6px 8px;
  font-size: 12px;
}

.apple-modal .icon-picker-sm button {
  width: 26px;
  height: 26px;
  font-size: 14px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid #e2e8f0;
}

.btn-cancel {
  padding: 8px 16px;
  background: #f1f5f9;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  color: #64748b;
}

/* 响应式 */
@media (max-width: 640px) {
  .skills-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    padding: 12px;
  }

  .skill-card {
    min-height: auto;
  }

  .toolbar {
    padding: 8px 12px;
  }

  .search-box {
    width: 120px;
  }
}
</style>
