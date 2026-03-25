<script setup lang="ts">
import { ref, nextTick, onMounted, computed, watch } from 'vue'
import { dataNotesApi, type DataNote } from '@/api'
import config from '@/config'

const props = defineProps<{
  departmentName?: string
}>()

const emit = defineEmits<{ close: [] }>()

const notes = ref<DataNote[]>([])

// 前16个（4列×4行）横着排，剩余的竖着排
const FIRST_SECTION_COUNT = 16
const firstNotes = computed(() => notes.value.slice(0, FIRST_SECTION_COUNT))
const restNotes = computed(() => notes.value.slice(FIRST_SECTION_COUNT))
const isLoading = ref(false)
const editingId = ref<string | null>(null)
const editingName = ref('')
const isDragging = ref(false)
const isUploading = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)

// 文件夹导航
const currentFolderId = ref<string | null>(null)
const folderPath = ref<{ id: string | null; name: string }[]>([{ id: null, name: 'root' }])
const currentLevel = computed(() => folderPath.value.length - 1)
// 是否可以创建文件夹（根目录不能创建，且最多3层）
const canCreateFolder = computed(() => {
  // 如果在部门根目录，不能创建文件夹
  if (props.departmentName && currentFolderId.value === null) {
    return false
  }
  return currentLevel.value < 3
})

// 选择模式
const selectedIds = ref<Set<string>>(new Set())
const isSelecting = computed(() => selectedIds.value.size > 0)


// 滚动导航 - 四个方向
const contentRef = ref<HTMLElement | null>(null)
const canScrollLeft = ref(false)
const canScrollRight = ref(false)
const canScrollUp = ref(false)
const canScrollDown = ref(false)

const updateScrollState = () => {
  const el = contentRef.value
  if (!el) return
  canScrollLeft.value = el.scrollLeft > 0
  canScrollRight.value = el.scrollLeft < el.scrollWidth - el.clientWidth - 1
  canScrollUp.value = el.scrollTop > 0
  canScrollDown.value = el.scrollTop < el.scrollHeight - el.clientHeight - 1
}

const scroll = (dir: 'left' | 'right' | 'up' | 'down') => {
  const el = contentRef.value
  if (!el) return
  const step = 110
  const opts: ScrollToOptions = { behavior: 'smooth' }
  if (dir === 'left') opts.left = -step
  if (dir === 'right') opts.left = step
  if (dir === 'up') opts.top = -step
  if (dir === 'down') opts.top = step
  el.scrollBy(opts)
  setTimeout(updateScrollState, 300)
}

// Toast 提示
const toastMessage = ref('')
const showToast = ref(false)
let toastTimer: number | null = null

const toast = (message: string) => {
  if (toastTimer) clearTimeout(toastTimer)
  toastMessage.value = message
  showToast.value = true
  toastTimer = window.setTimeout(() => {
    showToast.value = false
  }, 2000)
}

// 部门根文件夹ID（不能删除、不能修改）
const departmentFolderId = ref<string | null>(null)
// 防止重复初始化的锁
let isInitializing = false
let lastInitDepartment = ''

// 初始化部门文件夹（如果有部门名称，自动创建文件夹，但不自动进入）
const initDepartmentFolder = async () => {
  console.log('[initDepartmentFolder] departmentName:', props.departmentName)

  if (!props.departmentName) {
    departmentFolderId.value = null
    currentFolderId.value = null
    folderPath.value = [{ id: null, name: 'root' }]
    return
  }

  // 防止重复初始化同一个部门
  if (isInitializing && lastInitDepartment === props.departmentName) {
    console.log('[initDepartmentFolder] 跳过，正在初始化中')
    return
  }

  isInitializing = true
  lastInitDepartment = props.departmentName

  try {
    // 查找是否已有该部门的文件夹
    const allNotes = await dataNotesApi.getAll({ parentId: null })
    console.log('[initDepartmentFolder] 根目录文件夹:', allNotes.filter(n => n.file_type === 'folder').map(n => ({ id: n.id, name: n.name })))

    const existingFolder = allNotes.find(
      n => n.file_type === 'folder' && n.name === props.departmentName
    )
    console.log('[initDepartmentFolder] 找到现有文件夹:', existingFolder?.id, existingFolder?.name)

    if (existingFolder) {
      departmentFolderId.value = existingFolder.id
      console.log('[initDepartmentFolder] 使用现有文件夹')
    } else {
      console.log('[initDepartmentFolder] 未找到，准备创建...')
      // 创建部门文件夹（后端会检查重复）
      const newFolder = await dataNotesApi.createFolder({
        name: props.departmentName,
        parent_id: undefined,
        item_ids: []
      })
      console.log('[initDepartmentFolder] 创建/返回文件夹:', newFolder.id, newFolder.name)
      departmentFolderId.value = newFolder.id
    }

    // 停留在根目录，显示部门文件夹
    currentFolderId.value = null
    folderPath.value = [{ id: null, name: 'root' }]
  } catch (e) {
    console.error('Failed to init department folder:', e)
  } finally {
    isInitializing = false
  }
}

// 判断是否可以删除（部门文件夹不能删除）
const canDelete = (noteId: string) => {
  return noteId !== departmentFolderId.value
}

// 判断是否可以编辑名字（部门文件夹不能编辑）
const canEdit = (noteId: string) => {
  return noteId !== departmentFolderId.value
}

// 是否在根目录（有部门时，根目录只能看不能上传）
const isAtDepartmentRoot = computed(() => {
  return props.departmentName && currentFolderId.value === null
})

// 是否可以上传（在部门文件夹内或子文件夹内可以上传）
const canUpload = computed(() => {
  return !isAtDepartmentRoot.value
})

// 加载便签
const loadNotes = async () => {
  isLoading.value = true
  try {
    let allNotes = await dataNotesApi.getAll({
      parentId: currentFolderId.value
    })

    // 如果在根目录且有部门名称，只显示当前部门的文件夹
    if (currentFolderId.value === null && props.departmentName) {
      allNotes = allNotes.filter(n =>
        n.file_type === 'folder' && n.name === props.departmentName
      )
    }

    notes.value = allNotes
  } catch (e) {
    console.error('Failed to load notes:', e)
  } finally {
    isLoading.value = false
    nextTick(() => updateScrollState())
  }
}

// 进入文件夹
const enterFolder = (folder: DataNote) => {
  if (folder.file_type !== 'folder') return
  currentFolderId.value = folder.id
  folderPath.value.push({ id: folder.id, name: folder.name })
  selectedIds.value.clear()
  loadNotes()
}

// 返回上级或指定层级
const navigateTo = (index: number) => {
  const target = folderPath.value[index]
  currentFolderId.value = target.id
  folderPath.value = folderPath.value.slice(0, index + 1)
  selectedIds.value.clear()
  loadNotes()
}

// 选择/取消选择（单击）
const toggleSelect = (id: string) => {
  // 部门文件夹不能选中
  if (id === departmentFolderId.value) {
    return
  }
  if (selectedIds.value.has(id)) {
    selectedIds.value.delete(id)
  } else {
    selectedIds.value.add(id)
  }
  selectedIds.value = new Set(selectedIds.value)
}

// 创建文件夹（直接创建，默认名"未知"）
const createFolder = async () => {
  try {
    const folder = await dataNotesApi.createFolder({
      name: '未知',
      parent_id: currentFolderId.value || undefined,
      item_ids: Array.from(selectedIds.value)
    })
    selectedIds.value.clear()
    selectedIds.value = new Set()
    await loadNotes()
    // 自动进入编辑名字状态
    nextTick(() => {
      editingId.value = folder.id
      editingName.value = folder.name
      nextTick(() => {
        const input = document.querySelector('.edit-input') as HTMLInputElement
        input?.focus()
        input?.select()
      })
    })
  } catch (e) {
    console.error('Failed to create folder:', e)
    toast('创建文件夹失败')
  }
}

// 取消选择
const clearSelection = () => {
  selectedIds.value.clear()
  selectedIds.value = new Set()
}

// 点击空白处取消选择
const clickEmpty = () => {
  if (selectedIds.value.size > 0) {
    clearSelection()
  }
}

// 重置状态（关闭弹框时）
const resetState = () => {
  clearSelection()
  editingId.value = null
}

// 通知数据变化（用于刷新其他组件）
const notifyDataChange = () => {
  window.dispatchEvent(new CustomEvent('data-notes-changed'))
}

// 批量删除
const batchDelete = async () => {
  // 过滤掉部门文件夹
  const ids = Array.from(selectedIds.value).filter(id => canDelete(id))
  if (ids.length === 0) {
    toast('没有可删除的文件')
    return
  }
  const count = ids.length
  try {
    // 先从列表移除
    notes.value = notes.value.filter(n => !ids.includes(n.id))
    selectedIds.value.clear()
    toast(`正在删除 ${count} 个文件...`)
    // 逐个删除
    await Promise.all(ids.map(id => dataNotesApi.delete(id)))
    toast(`已删除 ${count} 个文件`)
    notifyDataChange()
  } catch (e) {
    console.error('Failed to batch delete:', e)
    toast('部分删除失败')
    loadNotes()
  }
}

// 批量下载（文件夹下载为zip）
const batchDownload = () => {
  const selected = notes.value.filter(n => selectedIds.value.has(n.id))
  if (selected.length === 0) {
    toast('没有可下载的文件')
    return
  }

  let downloadCount = 0
  selected.forEach((item, index) => {
    setTimeout(() => {
      const a = document.createElement('a')
      if (item.file_type === 'folder') {
        // 文件夹下载为zip
        a.href = dataNotesApi.getFolderZipUrl(item.id)
        a.download = `${item.name}.zip`
      } else if (item.file_url) {
        // 普通文件
        a.href = `${config.serverBaseUrl}${item.file_url}`
        a.download = item.name
      } else {
        return
      }
      a.click()
      downloadCount++
    }, index * 300)
  })
  toast(`开始下载 ${selected.length} 个项目`)
  selectedIds.value.clear()
  selectedIds.value = new Set()
}

// 切换收藏
const toggleFavorite = async (id: string, e: Event) => {
  e.stopPropagation()
  try {
    const result = await dataNotesApi.toggleFavorite(id)
    const note = notes.value.find(n => n.id === id)
    if (note) note.is_favorited = result.is_favorited
    notifyDataChange()
  } catch (e) {
    console.error('Failed to toggle favorite:', e)
  }
}

// 删除便签
const deleteNote = async (id: string, e: Event) => {
  e.stopPropagation()
  // 部门文件夹不能删除
  if (!canDelete(id)) {
    toast('部门文件夹不能删除')
    return
  }
  const note = notes.value.find(n => n.id === id)
  const fileName = note?.name || '文件'
  try {
    // 先从列表移除（立即反馈）
    notes.value = notes.value.filter(n => n.id !== id)
    toast(`已删除 ${fileName}`)
    // 再调用 API
    await dataNotesApi.delete(id)
    notifyDataChange()
  } catch (err) {
    console.error('Failed to delete note:', err)
    // 删除失败，恢复
    if (note) notes.value.push(note)
    toast('删除失败')
  }
}

// 单击选中
const clickCard = (note: DataNote) => {
  if (editingId.value) return
  // 部门文件夹单击直接进入
  if (note.id === departmentFolderId.value) {
    enterFolder(note)
    return
  }
  toggleSelect(note.id)
}

// 双击打开
const dblClickCard = (note: DataNote) => {
  if (editingId.value) return
  if (note.file_type === 'folder') {
    enterFolder(note)
  } else if (note.file_url) {
    window.open(`${config.serverBaseUrl}${note.file_url}`, '_blank')
  }
}

// 拖拽开始 - 用于拖到输入框
const handleDragStart = (e: DragEvent, note: DataNote) => {
  if (note.file_type === 'folder' || !note.file_url) {
    e.preventDefault()
    return
  }
  e.dataTransfer?.setData('application/data-note', JSON.stringify({
    id: note.id,
    name: note.name,
    file_url: note.file_url,
    file_type: note.file_type,
    file_size: note.file_size
  }))
  e.dataTransfer!.effectAllowed = 'copy'
}

// 开始编辑名字
const startEdit = (note: DataNote, e: Event) => {
  e.stopPropagation()
  // 部门文件夹不能编辑
  if (!canEdit(note.id)) {
    return
  }
  editingId.value = note.id
  editingName.value = note.name
  nextTick(() => {
    const input = document.querySelector('.edit-input') as HTMLInputElement
    input?.focus()
    input?.select()
  })
}

// 保存名字
const saveName = async (note: DataNote) => {
  if (!editingName.value.trim()) {
    editingId.value = null
    return
  }
  const newName = editingName.value.trim()
  if (newName !== note.name) {
    try {
      await dataNotesApi.update(note.id, { name: newName })
      note.name = newName
    } catch (e) {
      console.error('Failed to update name:', e)
    }
  }
  editingId.value = null
}

// 取消编辑
const cancelEdit = () => {
  editingId.value = null
}

// 获取显示名称（不含扩展名）
const getDisplayName = (name: string) => {
  const parts = name.split('.')
  if (parts.length > 1) {
    parts.pop()
    return parts.join('.')
  }
  return name
}

// 获取图标类型
const getIconType = (type: string) => {
  if (type === 'folder') return 'folder'
  if (['xlsx', 'xls'].includes(type)) return 'excel'
  if (type === 'csv') return 'csv'
  if (['docx', 'doc'].includes(type)) return 'word'
  if (['pptx', 'ppt'].includes(type)) return 'ppt'
  if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'bmp'].includes(type)) return 'image'
  if (['mp4', 'avi', 'mov', 'mkv', 'webm'].includes(type)) return 'video'
  if (['mp3', 'wav', 'flac', 'aac', 'ogg'].includes(type)) return 'audio'
  if (['zip', 'rar', '7z', 'tar', 'gz'].includes(type)) return 'zip'
  if (['txt', 'md', 'log'].includes(type)) return 'txt'
  return type
}

// 获取图标标签
const getIconLabel = (type: string) => {
  const labels: Record<string, string> = {
    xlsx: 'XLS', xls: 'XLS', csv: 'CSV',
    docx: 'DOC', doc: 'DOC',
    pptx: 'PPT', ppt: 'PPT',
    pdf: 'PDF', json: 'JSON',
    png: 'PNG', jpg: 'JPG', jpeg: 'JPG', gif: 'GIF', svg: 'SVG', webp: 'IMG',
    mp4: 'MP4', avi: 'AVI', mov: 'MOV', mkv: 'MKV',
    mp3: 'MP3', wav: 'WAV', flac: 'FLAC',
    zip: 'ZIP', rar: 'RAR', '7z': '7Z',
    txt: 'TXT', md: 'MD', html: 'HTML'
  }
  return labels[type] || type.toUpperCase()
}

// 点击上传
const triggerUpload = () => {
  fileInputRef.value?.click()
}

// 处理文件选择
const handleFileSelect = (e: Event) => {
  const input = e.target as HTMLInputElement
  if (input.files?.length) {
    uploadFiles(Array.from(input.files))
    input.value = ''
  }
}

// 拖拽事件
let dragCounter = 0

const handleDragEnter = (e: DragEvent) => {
  e.preventDefault()
  e.stopPropagation()
  dragCounter++
  // 根目录不允许上传，不显示拖拽效果
  if (e.dataTransfer?.types.includes('Files') && canUpload.value) {
    isDragging.value = true
  }
}

const handleDragOver = (e: DragEvent) => {
  e.preventDefault()
  e.stopPropagation()
}

const handleDragLeave = (e: DragEvent) => {
  e.preventDefault()
  e.stopPropagation()
  dragCounter--
  if (dragCounter === 0) {
    isDragging.value = false
  }
}

const handleDrop = (e: DragEvent) => {
  e.preventDefault()
  e.stopPropagation()
  dragCounter = 0
  isDragging.value = false
  // 根目录不允许上传
  if (!canUpload.value) {
    toast('请进入文件夹后上传')
    return
  }
  if (e.dataTransfer?.files.length) {
    uploadFiles(Array.from(e.dataTransfer.files))
  }
}

// 上传文件（多文件直接铺开，不创建文件夹）
const uploadFiles = async (files: File[]) => {
  isUploading.value = true
  let successCount = 0

  try {
    for (const file of files) {
      try {
        // 上传文件到服务器
        const formData = new FormData()
        formData.append('file', file)
        const res = await fetch(`${config.serverBaseUrl}/api/upload`, {
          method: 'POST',
          body: formData
        })
        const data = await res.json()

        if (data.url) {
          // 创建便签
          const ext = file.name.split('.').pop()?.toLowerCase() || ''
          const newNote = await dataNotesApi.create({
            name: file.name,
            file_type: ext,
            file_url: data.url,
            file_size: formatFileSize(file.size),
            parent_id: currentFolderId.value || undefined
          })
          notes.value.unshift(newNote)
          successCount++
        }
      } catch (e) {
        console.error('Failed to upload file:', e)
        toast(`上传 ${file.name} 失败`)
      }
    }
  } finally {
    isUploading.value = false
  }

  if (successCount > 0) {
    toast(`已上传 ${successCount} 个文件`)
    notifyDataChange()
  }
}

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

onMounted(async () => {
  await initDepartmentFolder()
  await loadNotes()
  nextTick(() => updateScrollState())
})

// 监听部门变化，重新初始化（只在值真正变化时触发）
watch(() => props.departmentName, async (newVal, oldVal) => {
  if (newVal === oldVal) return
  await initDepartmentFolder()
  await loadNotes()
})
</script>

<template>
  <div class="notes-modal">
    <!-- Toast 提示 -->
    <Transition name="toast">
      <div v-if="showToast" class="toast">{{ toastMessage }}</div>
    </Transition>

    <!-- 头部 -->
    <header class="modal-header">
      <span class="header-title">{{ props.departmentName ? props.departmentName + ' File Manage' : 'File Manage' }}</span>
      <span class="header-count">{{ notes.length }}</span>
      <!-- 面包屑导航 -->
      <div class="breadcrumb">
        <span
          v-for="(folder, idx) in folderPath"
          :key="folder.id || 'root'"
          class="breadcrumb-item"
          :class="{ active: idx === folderPath.length - 1 }"
          @click="idx < folderPath.length - 1 && navigateTo(idx)"
        >
          {{ folder.name }}
          <span v-if="idx < folderPath.length - 1" class="sep">/</span>
        </span>
      </div>
      <button class="close-btn" @click="emit('close')" title="关闭">×</button>
    </header>
    <input
      ref="fileInputRef"
      type="file"
      multiple
      style="display: none"
      @change="handleFileSelect"
    />

    <!-- 内容区域 -->
    <div class="content-area">
      <!-- 左箭头 - 始终显示 -->
      <button class="nav-btn nav-left" :class="{ disabled: !canScrollLeft }" @click="scroll('left')">《</button>

      <!-- 主内容 -->
      <div
        ref="contentRef"
        class="modal-content"
        :class="{ dragging: isDragging }"
        @dragenter="handleDragEnter"
        @dragover="handleDragOver"
        @dragleave="handleDragLeave"
        @drop="handleDrop"
        @scroll="updateScrollState"
        @click.self="clickEmpty"
      >
        <!-- 拖拽提示 -->
        <div v-if="isDragging" class="drop-hint">
          <span class="drop-icon">📥</span>
          <span>释放文件以上传</span>
        </div>

        <!-- 加载中 -->
        <div v-if="isLoading" class="loading">加载中...</div>

        <!-- 便签网格 -->
        <div v-else class="grid-wrapper" @click.self="clickEmpty">
        <!-- 前16个：横向排列（4列×4行） -->
        <div class="grid grid-horizontal" @click.self="clickEmpty">
          <div
            v-for="note in firstNotes"
            :key="note.id"
            class="card"
            :class="{ favorited: note.is_favorited, selected: selectedIds.has(note.id), folder: note.file_type === 'folder' }"
            :draggable="note.file_type !== 'folder' && !!note.file_url"
            @dragstart="handleDragStart($event, note)"
            @click="clickCard(note)"
            @dblclick="dblClickCard(note)"
          >
            <div class="card-icon" :class="'icon-' + getIconType(note.file_type)"></div>
            <span class="card-type">{{ note.file_type === 'folder' ? `${note.item_count || 0}项` : note.file_type }}</span>
            <div class="card-actions">
              <button
                class="action-btn fav"
                :class="{ active: note.is_favorited }"
                @click="toggleFavorite(note.id, $event)"
                :title="note.is_favorited ? '取消收藏' : '收藏'"
              >{{ note.is_favorited ? '★' : '☆' }}</button>
              <button v-if="canDelete(note.id)" class="action-btn del" @click="deleteNote(note.id, $event)" title="删除">×</button>
            </div>
            <input
              v-if="editingId === note.id"
              v-model="editingName"
              class="edit-input"
              @blur="saveName(note)"
              @keydown.enter="saveName(note)"
              @keydown.escape="cancelEdit"
              @click.stop
            />
            <div
              v-else
              class="card-name"
              :title="note.name"
              @click.stop="startEdit(note, $event)"
              :class="{ 'no-edit': !canEdit(note.id) }"
            >{{ note.file_type === 'folder' ? note.name : getDisplayName(note.name) }}</div>
          </div>
          <!-- 上传卡片（前16个未满时显示在这里，根目录不显示） -->
          <div v-if="firstNotes.length < 16 && canUpload" class="card upload-card" @click="triggerUpload">
            <span class="upload-icon">+</span>
            <span class="upload-text">{{ isUploading ? '上传中...' : '上传' }}</span>
          </div>
        </div>

        <!-- 超出16个：竖向排列 -->
        <div v-if="restNotes.length > 0 || firstNotes.length >= 16" class="grid grid-vertical" @click.self="clickEmpty">
          <div
            v-for="note in restNotes"
            :key="note.id"
            class="card"
            :class="{ favorited: note.is_favorited, selected: selectedIds.has(note.id), folder: note.file_type === 'folder' }"
            :draggable="note.file_type !== 'folder' && !!note.file_url"
            @dragstart="handleDragStart($event, note)"
            @click="clickCard(note)"
            @dblclick="dblClickCard(note)"
          >
            <div class="card-icon" :class="'icon-' + getIconType(note.file_type)"></div>
            <span class="card-type">{{ note.file_type === 'folder' ? `${note.item_count || 0}项` : note.file_type }}</span>
            <div class="card-actions">
              <button
                class="action-btn fav"
                :class="{ active: note.is_favorited }"
                @click="toggleFavorite(note.id, $event)"
                :title="note.is_favorited ? '取消收藏' : '收藏'"
              >{{ note.is_favorited ? '★' : '☆' }}</button>
              <button v-if="canDelete(note.id)" class="action-btn del" @click="deleteNote(note.id, $event)" title="删除">×</button>
            </div>
            <input
              v-if="editingId === note.id"
              v-model="editingName"
              class="edit-input"
              @blur="saveName(note)"
              @keydown.enter="saveName(note)"
              @keydown.escape="cancelEdit"
              @click.stop
            />
            <div
              v-else
              class="card-name"
              :title="note.name"
              @click.stop="startEdit(note, $event)"
              :class="{ 'no-edit': !canEdit(note.id) }"
            >{{ note.file_type === 'folder' ? note.name : getDisplayName(note.name) }}</div>
          </div>
          <!-- 上传卡片（前16个满了显示在这里，根目录不显示） -->
          <div v-if="firstNotes.length >= 16 && canUpload" class="card upload-card" @click="triggerUpload">
            <span class="upload-icon">+</span>
            <span class="upload-text">{{ isUploading ? '上传中...' : '上传' }}</span>
          </div>
        </div>
        </div>
      </div>

      <!-- 右箭头 - 始终显示 -->
      <button class="nav-btn nav-right" :class="{ disabled: !canScrollRight }" @click="scroll('right')">》</button>

      <!-- 选中操作工具栏 -->
      <Transition name="toolbar">
        <div v-if="selectedIds.size > 0" class="selection-toolbar">
          <span class="toolbar-count">{{ selectedIds.size }}</span>
          <button class="toolbar-btn" @click="batchDownload">下载</button>
          <button v-if="canCreateFolder" class="toolbar-btn" @click="createFolder">文件夹</button>
          <button class="toolbar-btn danger" @click="batchDelete">删除</button>
          <button class="toolbar-btn cancel" @click="clearSelection">×</button>
        </div>
      </Transition>
    </div>

  </div>
</template>

<style scoped>
.notes-modal {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* 头部 */
.modal-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  background: #fff;
  border-bottom: 1px solid #eee;
}

.header-title {
  font-size: 12px;
  font-weight: 600;
  color: #333;
}

.header-count {
  font-size: 9px;
  color: #888;
  background: rgba(0,0,0,0.05);
  padding: 1px 5px;
  border-radius: 6px;
}

/* 面包屑 */
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 2px;
  margin-left: 8px;
  margin-right: auto;
  font-size: 10px;
  color: #666;
}

.breadcrumb-item {
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 3px;
}

.breadcrumb-item:hover:not(.active) {
  background: rgba(0,0,0,0.05);
}

.breadcrumb-item.active {
  color: #333;
  font-weight: 500;
  cursor: default;
}

.breadcrumb .sep {
  color: #ccc;
  margin: 0 2px;
}

.close-btn {
  width: 18px;
  height: 18px;
  border: none;
  background: transparent;
  font-size: 14px;
  color: #666;
  cursor: pointer;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: rgba(0,0,0,0.06);
  color: #333;
}

/* 选中操作工具栏 - 简洁版 */
.selection-toolbar {
  position: absolute;
  bottom: 6px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 4px 8px;
  background: rgba(0,0,0,0.75);
  border-radius: 14px;
  z-index: 30;
}

.toolbar-count {
  font-size: 11px;
  color: #90caf9;
  font-weight: 500;
  padding: 0 6px;
  min-width: 16px;
  text-align: center;
}

.toolbar-btn {
  padding: 3px 8px;
  border: none;
  background: transparent;
  color: rgba(255,255,255,0.8);
  font-size: 11px;
  cursor: pointer;
  border-radius: 10px;
  transition: all 0.15s;
}

.toolbar-btn:hover {
  background: rgba(255,255,255,0.15);
  color: #fff;
}

.toolbar-btn.danger:hover {
  background: rgba(231,76,60,0.8);
}

.toolbar-btn.cancel {
  color: rgba(255,255,255,0.5);
  padding: 3px 6px;
}

.toolbar-btn.cancel:hover {
  color: #fff;
}

/* 工具栏动画 */
.toolbar-enter-active,
.toolbar-leave-active {
  transition: all 0.15s ease;
}

.toolbar-enter-from,
.toolbar-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(10px);
}

/* 内容区域 - 包含导航箭头 */
.content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

/* 导航箭头 */
.nav-btn {
  position: absolute;
  z-index: 20;
  border: none;
  background: transparent;
  color: #555;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 90px;
  font-size: 24px;
  font-weight: bold;
  border-radius: 8px;
}

.nav-btn:hover {
  color: #1565c0;
  background: rgba(33,150,243,0.25);
  box-shadow: 0 0 30px rgba(33,150,243,0.6);
  transform: translateY(-50%) scale(1.25);
}

.nav-btn:active {
  color: #0d47a1;
  background: rgba(33,150,243,0.4);
  box-shadow: 0 0 40px rgba(33,150,243,0.8);
}

.nav-left { left: -16px; }
.nav-right { right: -16px; }

/* 主内容 */
.modal-content {
  flex: 1;
  overflow: auto;
  padding: 8px;
  margin: 4px 2px;
  background: #fafafa;
  position: relative;
  transition: background 0.15s;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.modal-content::-webkit-scrollbar {
  display: none;
}

.modal-content.dragging {
  background: #e8f5e9;
}

.drop-hint {
  position: absolute;
  inset: 10px;
  border: 2px dashed #4caf50;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: rgba(232, 245, 233, 0.9);
  color: #2e7d32;
  font-size: 14px;
  font-weight: 500;
  z-index: 10;
}

.drop-icon {
  font-size: 32px;
}

/* 网格容器 */
.grid-wrapper {
  display: flex;
  gap: 10px;
  width: max-content;
  min-width: 100%;
}

/* 网格基础 */
.grid {
  display: grid;
  gap: 10px;
}

/* 前16个：横向排列（4列×4行，按行填充） */
.grid-horizontal {
  grid-template-columns: repeat(4, 100px);
  grid-template-rows: repeat(4, 95px);
  grid-auto-flow: row;
}

/* 超出部分：竖向排列（按列填充） */
.grid-vertical {
  grid-auto-flow: column;
  grid-template-rows: repeat(4, 95px);
  grid-auto-columns: 100px;
}

/* 卡片 - 正方形 */
.card {
  background: #fff;
  border: 1px solid #e8e4d0;
  border-radius: 8px;
  padding: 18px 6px 6px;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  min-height: 76px;
}

.card:hover {
  background: #fffef5;
  border-color: #d4c99e;
  box-shadow: 0 2px 8px rgba(180, 160, 100, 0.2);
}

.card[draggable="true"] {
  cursor: grab;
}

.card[draggable="true"]:active {
  cursor: grabbing;
}

.card.favorited {
  background: #fffbeb;
  border-color: #e6c84a;
}

/* 上传卡片 */
.upload-card {
  border: 2px dashed #ccc;
  background: #fafafa;
  justify-content: center;
  gap: 4px;
}

.upload-card:hover {
  border-color: #4caf50;
  background: #f1f8e9;
}

.upload-icon {
  font-size: 28px;
  color: #999;
  font-weight: 300;
  line-height: 1;
}

.upload-card:hover .upload-icon {
  color: #4caf50;
}

.upload-text {
  font-size: 10px;
  color: #999;
}

.upload-card:hover .upload-text {
  color: #4caf50;
}

/* 文件图标 - 背景图 */
.card-icon {
  width: 50px;
  height: 50px;
  flex-shrink: 0;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Cpath d='M28 4H12a4 4 0 00-4 4v32a4 4 0 004 4h24a4 4 0 004-4V16L28 4z' fill='%2390a4ae'/%3E%3Cpath d='M28 4v12h12L28 4z' fill='%23b0bec5'/%3E%3C/svg%3E");
}

/* Excel - 绿色表格图标 */
.card-icon.icon-excel {
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 96 96' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='96' height='96' rx='8' fill='%23107c41'/%3E%3Crect x='50' y='12' width='34' height='72' rx='2' fill='white' fill-opacity='0.9'/%3E%3Cpath d='M56 24h22M56 36h22M56 48h22M56 60h22M56 72h22' stroke='%23107c41' stroke-width='2'/%3E%3Cpath d='M67 24v48' stroke='%23107c41' stroke-width='1.5'/%3E%3Crect x='12' y='24' width='32' height='48' rx='2' fill='%230d5c31'/%3E%3Cpath d='M20 36l8 12-8 12M36 36l-8 12 8 12' stroke='white' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
}

/* Word - 蓝色文档图标 */
.card-icon.icon-word {
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 96 96' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='96' height='96' rx='8' fill='%232b7cd3'/%3E%3Crect x='50' y='12' width='34' height='72' rx='2' fill='white' fill-opacity='0.9'/%3E%3Cpath d='M56 28h22M56 40h22M56 52h22M56 64h16' stroke='%232b7cd3' stroke-width='2.5' stroke-linecap='round'/%3E%3Crect x='12' y='24' width='32' height='48' rx='2' fill='%23185abd'/%3E%3Cpath d='M18 36l4 24 6-18 6 18 4-24' stroke='white' stroke-width='3' stroke-linecap='round' stroke-linejoin='round' fill='none'/%3E%3C/svg%3E");
}

/* PPT - 橙红色演示图标 */
.card-icon.icon-ppt {
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 96 96' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='96' height='96' rx='8' fill='%23d35230'/%3E%3Crect x='50' y='12' width='34' height='72' rx='2' fill='white' fill-opacity='0.9'/%3E%3Crect x='56' y='24' width='22' height='16' rx='2' fill='%23d35230'/%3E%3Cpath d='M56 52h22M56 64h16' stroke='%23d35230' stroke-width='2.5' stroke-linecap='round'/%3E%3Crect x='12' y='24' width='32' height='48' rx='2' fill='%23b7472a'/%3E%3Cpath d='M20 36h10a6 6 0 010 12H20z' fill='white'/%3E%3Cpath d='M20 36v24' stroke='white' stroke-width='4' stroke-linecap='round'/%3E%3C/svg%3E");
}

/* PDF - 红色PDF图标 */
.card-icon.icon-pdf {
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 96 96' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='96' height='96' rx='8' fill='%23f44336'/%3E%3Crect x='16' y='16' width='64' height='64' rx='4' fill='white' fill-opacity='0.95'/%3E%3Ctext x='48' y='58' font-family='Arial,sans-serif' font-size='24' font-weight='bold' fill='%23f44336' text-anchor='middle'%3EPDF%3C/text%3E%3C/svg%3E");
}

/* JSON - 橙色代码图标 */
.card-icon.icon-json {
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 96 96' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='96' height='96' rx='8' fill='%23f7931e'/%3E%3Crect x='16' y='16' width='64' height='64' rx='4' fill='white' fill-opacity='0.95'/%3E%3Ctext x='48' y='42' font-family='monospace' font-size='20' font-weight='bold' fill='%23f7931e' text-anchor='middle'%3E%7B%7D%3C/text%3E%3Ctext x='48' y='66' font-family='Arial,sans-serif' font-size='16' font-weight='bold' fill='%23f7931e' text-anchor='middle'%3EJSON%3C/text%3E%3C/svg%3E");
}

/* Image - 绿色图片图标 */
.card-icon.icon-image {
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 96 96' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='96' height='96' rx='8' fill='%234caf50'/%3E%3Crect x='16' y='20' width='64' height='56' rx='4' fill='white' fill-opacity='0.95'/%3E%3Ccircle cx='34' cy='38' r='8' fill='%23ffeb3b'/%3E%3Cpath d='M20 68l18-22 14 16 10-12 18 18H20z' fill='%234caf50'/%3E%3C/svg%3E");
}

/* Video - 紫色视频图标 */
.card-icon.icon-video {
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 96 96' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='96' height='96' rx='8' fill='%239c27b0'/%3E%3Crect x='12' y='24' width='72' height='48' rx='4' fill='white' fill-opacity='0.95'/%3E%3Cpath d='M40 36v24l20-12z' fill='%239c27b0'/%3E%3C/svg%3E");
}

/* Audio - 青色音频图标 */
.card-icon.icon-audio {
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 96 96' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='96' height='96' rx='8' fill='%2300bcd4'/%3E%3Ccircle cx='48' cy='48' r='32' fill='white' fill-opacity='0.95'/%3E%3Ccircle cx='48' cy='48' r='20' fill='%2300bcd4'/%3E%3Ccircle cx='48' cy='48' r='6' fill='white'/%3E%3C/svg%3E");
}

/* ZIP - 棕色压缩图标 */
.card-icon.icon-zip {
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 96 96' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='96' height='96' rx='8' fill='%23795548'/%3E%3Crect x='20' y='12' width='56' height='72' rx='4' fill='white' fill-opacity='0.95'/%3E%3Crect x='42' y='12' width='12' height='72' fill='%23795548'/%3E%3Crect x='38' y='20' width='8' height='6' fill='white'/%3E%3Crect x='50' y='30' width='8' height='6' fill='white'/%3E%3Crect x='38' y='40' width='8' height='6' fill='white'/%3E%3Crect x='50' y='50' width='8' height='6' fill='white'/%3E%3Crect x='40' y='62' width='16' height='14' rx='2' fill='%23ffc107'/%3E%3C/svg%3E");
}

/* TXT - 灰色文本图标 */
.card-icon.icon-txt {
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 96 96' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='96' height='96' rx='8' fill='%23607d8b'/%3E%3Crect x='16' y='12' width='64' height='72' rx='4' fill='white' fill-opacity='0.95'/%3E%3Cpath d='M28 32h40M28 46h40M28 60h28' stroke='%23607d8b' stroke-width='4' stroke-linecap='round'/%3E%3C/svg%3E");
}

/* HTML - 橙色网页图标 */
.card-icon.icon-html {
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 96 96' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='96' height='96' rx='8' fill='%23e44d26'/%3E%3Crect x='16' y='16' width='64' height='64' rx='4' fill='white' fill-opacity='0.95'/%3E%3Ctext x='48' y='58' font-family='monospace' font-size='22' font-weight='bold' fill='%23e44d26' text-anchor='middle'%3E%26lt;/%26gt;%3C/text%3E%3C/svg%3E");
}

/* CSV */
.card-icon.icon-csv {
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 96 96' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='96' height='96' rx='8' fill='%23107c41'/%3E%3Crect x='16' y='16' width='64' height='64' rx='4' fill='white' fill-opacity='0.95'/%3E%3Ctext x='48' y='58' font-family='Arial,sans-serif' font-size='22' font-weight='bold' fill='%23107c41' text-anchor='middle'%3ECSV%3C/text%3E%3C/svg%3E");
}

.card-type {
  position: absolute;
  top: 3px;
  left: 4px;
  font-size: 8px;
  color: #999;
  text-transform: uppercase;
}

.card-name {
  font-size: 10px;
  font-weight: 500;
  color: #333;
  text-align: center;
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-top: 4px;
  padding: 1px 3px;
  border-radius: 2px;
  cursor: text;
}

.card-name:hover {
  background: rgba(0,0,0,0.04);
}

.card-name.no-edit {
  cursor: default;
  pointer-events: none;
}

.edit-input {
  width: 100%;
  font-size: 10px;
  color: #333;
  text-align: center;
  border: 1px solid #d4b84a;
  border-radius: 2px;
  padding: 2px 4px;
  outline: none;
  background: #fff;
  margin-top: 4px;
}

.card-actions {
  position: absolute;
  top: 2px;
  right: 2px;
  display: flex;
  align-items: center;
  gap: 1px;
}

.action-btn {
  width: 16px;
  height: 16px;
  border: none;
  background: transparent;
  border-radius: 3px;
  cursor: pointer;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.action-btn.fav {
  color: #ccc;
}

.action-btn.fav:hover {
  color: #b8860b;
}

.action-btn.fav.active {
  color: #b8860b;
}

.action-btn.del {
  color: #ccc;
  font-size: 13px;
}

.action-btn.del:hover {
  color: #e74c3c;
}

/* 状态 */
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #888;
  font-size: 12px;
}

/* Toast 提示 */
.toast {
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.75);
  color: #fff;
  padding: 6px 14px;
  border-radius: 4px;
  font-size: 11px;
  z-index: 100;
  white-space: nowrap;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.2s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(10px);
}

/* 选中状态 */
.card.selected {
  background: #e3f2fd;
  border-color: #2196f3;
}

/* 文件夹图标 */
.card-icon.icon-folder {
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 96 96' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M8 24c0-4.4 3.6-8 8-8h24l8 8h32c4.4 0 8 3.6 8 8v40c0 4.4-3.6 8-8 8H16c-4.4 0-8-3.6-8-8V24z' fill='%23ffc107'/%3E%3Cpath d='M8 36h80v36c0 4.4-3.6 8-8 8H16c-4.4 0-8-3.6-8-8V36z' fill='%23ffca28'/%3E%3C/svg%3E");
}

.card.folder {
  background: #fffde7;
  border-color: #ffe082;
}

.card.folder:hover {
  background: #fff9c4;
  border-color: #ffc107;
}
</style>
