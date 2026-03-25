<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useContextStore } from '@/stores/context'
import { dataNotesApi, type DataNote } from '@/api'

const props = defineProps<{
  visible: boolean
  query: string
  position: { x: number; y: number }
}>()

const emit = defineEmits<{
  close: []
  select: [item: { type: string; name: string; content: string; filePath?: string }]
}>()

const contextStore = useContextStore()
const pickerRef = ref<HTMLElement | null>(null)
const activeIndex = ref(0)

// 数据便签
const dataNotes = ref<DataNote[]>([])
const loadingNotes = ref(false)

// 选项类型
interface PickerOption {
  id: string
  type: 'data-note' | 'skill-output' | 'file' | 'text'
  icon: string
  name: string
  description?: string
  content?: string
  filePath?: string
}

// 加载数据便签
const loadDataNotes = async () => {
  loadingNotes.value = true
  try {
    dataNotes.value = await dataNotesApi.getAll({ parentId: null })
  } catch (e) {
    console.error('Failed to load data notes:', e)
  } finally {
    loadingNotes.value = false
  }
}

// 生成选项列表
const options = computed((): PickerOption[] => {
  const query = props.query.toLowerCase()
  const result: PickerOption[] = []

  // 数据便签
  dataNotes.value.forEach(note => {
    if (!note.file_url) return // 跳过文件夹
    if (query && !note.name.toLowerCase().includes(query)) return
    result.push({
      id: `note-${note.id}`,
      type: 'data-note',
      icon: '📝',
      name: note.name,
      description: note.description || note.file_type,
      filePath: note.file_url
    })
  })

  // 已有的技能输出
  contextStore.items
    .filter(item => item.type === 'skill-output')
    .forEach(item => {
      if (query && !item.name.toLowerCase().includes(query)) return
      result.push({
        id: `output-${item.id}`,
        type: 'skill-output',
        icon: '🔧',
        name: item.name,
        description: `${item.tokenCount} tokens`,
        content: item.content
      })
    })

  // 快捷操作
  if (!query || '添加文本'.includes(query) || 'add text'.includes(query)) {
    result.push({
      id: 'action-text',
      type: 'text',
      icon: '📋',
      name: '添加文本片段',
      description: '手动输入文本作为上下文'
    })
  }

  return result
})

// 监听 visible 变化
watch(() => props.visible, (visible) => {
  if (visible) {
    activeIndex.value = 0
    loadDataNotes()
  }
})

// 监听 query 变化重置选中
watch(() => props.query, () => {
  activeIndex.value = 0
})

// 处理键盘导航
const handleKeydown = (e: KeyboardEvent) => {
  if (!props.visible) return

  switch (e.key) {
    case 'ArrowUp':
      e.preventDefault()
      activeIndex.value = Math.max(0, activeIndex.value - 1)
      break
    case 'ArrowDown':
      e.preventDefault()
      activeIndex.value = Math.min(options.value.length - 1, activeIndex.value + 1)
      break
    case 'Enter':
      e.preventDefault()
      selectOption(options.value[activeIndex.value])
      break
    case 'Escape':
      e.preventDefault()
      emit('close')
      break
  }
}

// 选择选项
const selectOption = (option: PickerOption) => {
  if (!option) return

  if (option.type === 'text') {
    // 添加文本片段（弹出输入框）
    const text = prompt('请输入文本内容:')
    if (text) {
      emit('select', {
        type: 'text-snippet',
        name: text.slice(0, 20) + (text.length > 20 ? '...' : ''),
        content: text
      })
    }
  } else {
    emit('select', {
      type: option.type,
      name: option.name,
      content: option.content || '',
      filePath: option.filePath
    })
  }
  emit('close')
}

// 挂载/卸载键盘监听
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

// 滚动到可见
watch(activeIndex, () => {
  nextTick(() => {
    const activeEl = pickerRef.value?.querySelector('.option.active')
    activeEl?.scrollIntoView({ block: 'nearest' })
  })
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="visible"
      ref="pickerRef"
      class="context-picker"
      :style="{
        left: `${position.x}px`,
        bottom: `${position.y}px`
      }"
    >
      <div class="picker-header">
        <span class="header-icon">@</span>
        <span class="header-title">引用上下文</span>
        <span class="header-hint" v-if="query">搜索: {{ query }}</span>
      </div>

      <div class="picker-content">
        <!-- 加载中 -->
        <div class="loading" v-if="loadingNotes">
          <span class="spinner"></span>
          <span>加载中...</span>
        </div>

        <!-- 空状态 -->
        <div class="empty" v-else-if="options.length === 0">
          <span>没有匹配的内容</span>
        </div>

        <!-- 选项列表 -->
        <div class="options" v-else>
          <div
            v-for="(option, index) in options"
            :key="option.id"
            class="option"
            :class="{ active: index === activeIndex }"
            @click="selectOption(option)"
            @mouseenter="activeIndex = index"
          >
            <span class="option-icon">{{ option.icon }}</span>
            <div class="option-info">
              <span class="option-name">{{ option.name }}</span>
              <span class="option-desc" v-if="option.description">
                {{ option.description }}
              </span>
            </div>
            <span class="option-type">{{ option.type === 'data-note' ? '便签' : option.type === 'skill-output' ? '输出' : '操作' }}</span>
          </div>
        </div>
      </div>

      <div class="picker-footer">
        <span><kbd>↑</kbd><kbd>↓</kbd> 导航</span>
        <span><kbd>Enter</kbd> 选择</span>
        <span><kbd>Esc</kbd> 关闭</span>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.context-picker {
  position: fixed;
  width: 320px;
  max-height: 360px;
  background: var(--color-background, #fff);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 12px;
  box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.2);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.picker-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border, #e2e8f0);
  background: var(--color-background-soft, #f8fafc);
}

.header-icon {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-primary, #3b82f6);
}

.header-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text, #1e293b);
}

.header-hint {
  margin-left: auto;
  font-size: 11px;
  color: var(--color-text-light, #64748b);
  background: var(--color-background, #fff);
  padding: 2px 8px;
  border-radius: 4px;
}

.picker-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.loading, .empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  color: var(--color-text-light, #94a3b8);
  font-size: 13px;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--color-border, #e2e8f0);
  border-top-color: var(--color-primary, #3b82f6);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.options {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.option:hover, .option.active {
  background: var(--color-background-soft, #f1f5f9);
}

.option.active {
  background: var(--color-primary-light, #eff6ff);
}

.option-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.option-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.option-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text, #1e293b);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.option-desc {
  font-size: 11px;
  color: var(--color-text-light, #64748b);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.option-type {
  font-size: 10px;
  color: var(--color-text-light, #94a3b8);
  background: var(--color-background-mute, #e2e8f0);
  padding: 2px 6px;
  border-radius: 4px;
  flex-shrink: 0;
}

.picker-footer {
  display: flex;
  gap: 16px;
  padding: 10px 16px;
  border-top: 1px solid var(--color-border, #e2e8f0);
  background: var(--color-background-soft, #f8fafc);
  font-size: 11px;
  color: var(--color-text-light, #64748b);
}

.picker-footer kbd {
  display: inline-block;
  padding: 2px 5px;
  font-size: 10px;
  font-family: inherit;
  background: var(--color-background, #fff);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 4px;
  margin-right: 4px;
}
</style>
