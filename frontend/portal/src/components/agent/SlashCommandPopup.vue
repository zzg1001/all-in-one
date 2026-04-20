<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { dataNotesApi } from '@/api'
import type { DataNote } from '@/api'

const props = defineProps<{
  notes: DataNote[]
  query: string
  visible: boolean
  position: { x: number; y: number }
}>()

const emit = defineEmits<{
  select: [note: DataNote, isFolder: boolean]
  close: []
}>()

const selectedIndex = ref(0)

// 级联菜单状态：每一级的数据和选中项
interface MenuLevel {
  items: DataNote[]
  selectedIndex: number
  loading: boolean
  parentFolder?: DataNote
}
const menuLevels = ref<MenuLevel[]>([])

// 悬停延迟 timer
let hoverTimer: number | null = null
const HOVER_DELAY = 200  // 悬停延迟时间

// 计算主弹窗位置
const popupStyle = computed(() => ({
  left: `${props.position.x}px`,
  bottom: `${globalThis.window?.innerHeight - props.position.y + 8}px`
}))

// 计算子菜单位置（确保不超出屏幕）
const getSubmenuStyle = (levelIndex: number) => {
  const menuWidth = 260
  const gap = 4
  let left = props.position.x + (menuWidth + gap) * (levelIndex + 1)

  // 如果超出右边界，显示在左边
  const windowWidth = globalThis.window?.innerWidth || 1200
  if (left + menuWidth > windowWidth - 10) {
    left = props.position.x - (menuWidth + gap) * (levelIndex + 1)
  }

  return {
    left: `${left}px`,
    bottom: `${globalThis.window?.innerHeight - props.position.y + 8}px`
  }
}

// 文件类型图标映射
const fileIconMap: Record<string, string> = {
  folder: '📁',
  xlsx: '📊', xls: '📊', csv: '📊',
  json: '{ }',
  pdf: '📄',
  docx: '📝', doc: '📝',
  pptx: '📽', ppt: '📽',
  png: '🖼', jpg: '🖼', jpeg: '🖼', gif: '🖼', svg: '🖼',
  html: '🌐',
  txt: '📃', md: '📑',
  mp4: '🎬', mp3: '🎵',
  zip: '📦',
}

const getFileIcon = (type: string) => fileIconMap[type] || '📎'

const getDisplayName = (note: { name: string; file_type: string; item_count?: number }) => {
  if (note.file_type === 'folder') {
    return `${note.name} (${note.item_count || 0})`
  }
  return note.name
}

// 过滤后的主列表
const filteredNotes = computed(() => {
  const q = props.query.toLowerCase()
  if (!q) return props.notes.slice(0, 12)
  return props.notes
    .filter(note =>
      note.name.toLowerCase().includes(q) ||
      (note.description && note.description.toLowerCase().includes(q))
    )
    .slice(0, 12)
})

// 重置状态
watch(() => props.visible, (visible) => {
  if (visible) {
    selectedIndex.value = 0
    menuLevels.value = []
  }
})

watch(() => props.query, () => {
  selectedIndex.value = 0
  menuLevels.value = []  // 搜索时关闭子菜单
})

// 清除悬停 timer
const clearHoverTimer = () => {
  if (hoverTimer) {
    clearTimeout(hoverTimer)
    hoverTimer = null
  }
}

// 鼠标进入主列表项
const handleMainItemEnter = (index: number, note: DataNote) => {
  clearHoverTimer()
  selectedIndex.value = index

  if (note.file_type === 'folder') {
    hoverTimer = window.setTimeout(() => {
      openSubMenu(note, 0)
    }, HOVER_DELAY)
  } else {
    menuLevels.value = []
  }
}

// 鼠标进入子菜单项
const handleSubItemEnter = (levelIndex: number, itemIndex: number, note: DataNote) => {
  clearHoverTimer()
  menuLevels.value[levelIndex].selectedIndex = itemIndex

  // 关闭更深层级的子菜单
  menuLevels.value = menuLevels.value.slice(0, levelIndex + 1)

  if (note.file_type === 'folder') {
    hoverTimer = window.setTimeout(() => {
      openSubMenu(note, levelIndex + 1)
    }, HOVER_DELAY)
  }
}

// 打开子菜单
const openSubMenu = async (folder: DataNote, levelIndex: number) => {
  // 确保数组长度正确
  menuLevels.value = menuLevels.value.slice(0, levelIndex)

  // 添加新的加载中层级
  menuLevels.value.push({
    items: [],
    selectedIndex: -1,
    loading: true,
    parentFolder: folder
  })

  try {
    const items = await dataNotesApi.getAll({ parentId: folder.id })
    if (menuLevels.value[levelIndex]) {
      menuLevels.value[levelIndex].items = items
      menuLevels.value[levelIndex].loading = false
    }
  } catch (e) {
    console.error('Failed to load folder:', e)
    if (menuLevels.value[levelIndex]) {
      menuLevels.value[levelIndex].loading = false
    }
  }
}

// 点击选择（主列表）
const handleMainItemClick = (note: DataNote) => {
  emit('select', note, note.file_type === 'folder')
}

// 点击选择（子菜单）
const handleSubItemClick = (note: DataNote) => {
  emit('select', note, note.file_type === 'folder')
}

// 鼠标离开整个菜单区域
const handleMenuLeave = () => {
  clearHoverTimer()
}

// 键盘导航
const handleKeydown = (e: KeyboardEvent) => {
  if (!props.visible) return

  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault()
      if (menuLevels.value.length === 0) {
        selectedIndex.value = Math.min(selectedIndex.value + 1, filteredNotes.value.length - 1)
      }
      break
    case 'ArrowUp':
      e.preventDefault()
      if (menuLevels.value.length === 0) {
        selectedIndex.value = Math.max(selectedIndex.value - 1, 0)
      }
      break
    case 'ArrowRight':
      e.preventDefault()
      // 进入文件夹
      if (menuLevels.value.length === 0) {
        const note = filteredNotes.value[selectedIndex.value]
        if (note?.file_type === 'folder') {
          openSubMenu(note, 0)
        }
      }
      break
    case 'ArrowLeft':
      e.preventDefault()
      // 返回上一级
      if (menuLevels.value.length > 0) {
        menuLevels.value.pop()
      }
      break
    case 'Enter':
      e.preventDefault()
      const selected = filteredNotes.value[selectedIndex.value]
      if (selected) {
        emit('select', selected, selected.file_type === 'folder')
      }
      break
    case 'Escape':
      e.preventDefault()
      if (menuLevels.value.length > 0) {
        menuLevels.value = []
      } else {
        emit('close')
      }
      break
  }
}

defineExpose({ handleKeydown })
</script>

<template>
  <Teleport to="body">
    <div v-if="visible && filteredNotes.length > 0" class="slash-menu-wrapper" @mousedown.prevent>
      <!-- 主菜单 -->
      <div class="slash-menu" :style="popupStyle">
        <div class="menu-header">
          <span class="menu-title">reference</span>
        </div>
        <div class="menu-list">
          <div
            v-for="(note, index) in filteredNotes"
            :key="note.id"
            class="menu-item"
            :class="{
              selected: index === selectedIndex,
              folder: note.file_type === 'folder',
              expanded: menuLevels.length > 0 && index === selectedIndex && note.file_type === 'folder'
            }"
            @click="handleMainItemClick(note)"
            @mouseenter="handleMainItemEnter(index, note)"
          >
            <span class="item-icon">{{ getFileIcon(note.file_type) }}</span>
            <span class="item-name">{{ getDisplayName(note) }}</span>
            <span v-if="note.is_favorited" class="item-star">★</span>
            <span v-if="note.file_type === 'folder'" class="item-arrow">›</span>
          </div>
        </div>
        <div class="menu-footer">
          <span class="hint">↑↓ 导航</span>
          <span class="hint">↵ 选择</span>
          <span class="hint">Esc 取消</span>
        </div>
      </div>

      <!-- 级联子菜单 -->
      <template v-for="(level, levelIndex) in menuLevels" :key="levelIndex">
        <div
          class="slash-submenu"
          :style="getSubmenuStyle(levelIndex)"
        >
          <div class="menu-header">
            <span class="menu-title">{{ level.parentFolder?.name }}</span>
          </div>

          <!-- 加载中 -->
          <div v-if="level.loading" class="menu-loading">
            <span class="loading-spinner"></span>
            <span>加载中...</span>
          </div>

          <!-- 空文件夹 -->
          <div v-else-if="level.items.length === 0" class="menu-empty">
            <span>📭 文件夹为空</span>
          </div>

          <!-- 文件列表 -->
          <div v-else class="menu-list">
            <div
              v-for="(note, itemIndex) in level.items"
              :key="note.id"
              class="menu-item"
              :class="{
                selected: itemIndex === level.selectedIndex,
                folder: note.file_type === 'folder'
              }"
              @click="handleSubItemClick(note)"
              @mouseenter="handleSubItemEnter(levelIndex, itemIndex, note)"
            >
              <span class="item-icon">{{ getFileIcon(note.file_type) }}</span>
              <span class="item-name">{{ getDisplayName(note) }}</span>
              <span v-if="note.is_favorited" class="item-star">★</span>
              <span v-if="note.file_type === 'folder'" class="item-arrow">›</span>
            </div>
          </div>
        </div>
      </template>
    </div>
  </Teleport>
</template>

<style scoped>
.slash-menu-wrapper {
  position: fixed;
  z-index: 10001;
}

.slash-menu {
  position: fixed;
  width: 260px;
  max-height: 400px;
  background: #fff;
  border: 1px solid #e0d8c0;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  z-index: 10002;
}

.slash-submenu {
  position: fixed;
  width: 260px;
  max-height: 400px;
  background: #fff;
  border: 1px solid #e0d8c0;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  z-index: 10003;
}

.menu-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: #fffef8;
  border-bottom: 1px solid #f0e8d0;
}

.menu-title {
  font-size: 11px;
  font-weight: 600;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.menu-loading,
.menu-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: #888;
  font-size: 12px;
}

.loading-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid #e0d8c0;
  border-top-color: #d4a700;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.menu-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  cursor: pointer;
  transition: background 0.1s;
}

.menu-item:hover,
.menu-item.selected {
  background: #fff9e6;
}

.menu-item.expanded {
  background: #fff3cc;
}

.item-icon {
  flex-shrink: 0;
  font-size: 14px;
  width: 20px;
  text-align: center;
}

.item-name {
  flex: 1;
  font-size: 13px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-star {
  flex-shrink: 0;
  color: #e6a700;
  font-size: 11px;
}

.item-arrow {
  flex-shrink: 0;
  color: #999;
  font-size: 12px;
  margin-left: 4px;
}

.menu-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  background: #fafafa;
  border-top: 1px solid #f0e8d0;
}

.hint {
  font-size: 10px;
  color: #999;
}
</style>
