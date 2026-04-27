<script setup lang="ts">
import { ref, computed, onBeforeUnmount } from 'vue'

interface SkillInteraction {
  id: string
  type: string
  label: string
}

interface OutputConfig {
  enabled: boolean
  preferred_type?: string
}

interface Skill {
  id: number
  name: string
  description: string
  tags: string[]
  icon: string
  author: string
  version: string
  created_at?: string
  interactions?: SkillInteraction[]
  output_config?: OutputConfig
}

const props = defineProps<{
  skill: Skill
  hideActions?: boolean
}>()

const emit = defineEmits<{
  delete: []
  edit: []
}>()

const isEditable = computed(() => props.skill.author !== 'uploaded')

// 是否显示作者（排除uploaded和unknown）
const showAuthor = computed(() => {
  const author = props.skill.author
  return author && author !== 'uploaded' && author !== 'unknown'
})

// 输出类型
const outputType = computed(() => {
  const type = props.skill.output_config?.preferred_type
  if (!type) return null
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
  return typeMap[type] || type
})

// 输入数量
const inputCount = computed(() => {
  return props.skill.interactions?.length || 0
})

// 显示的标签（最多显示3个）
const displayTags = computed(() => {
  const tags = props.skill.tags || []
  return tags.slice(0, 3)
})

// 图标颜色 - 柔和的色调，不会太跳跃
const iconColors = ['#8b5cf6', '#6366f1', '#8b5cf6', '#7c3aed', '#6d28d9']

const iconColor = computed(() => {
  const id = props.skill.id || 0
  const index = (typeof id === 'number' ? id : id.charCodeAt(0)) % iconColors.length
  return iconColors[index]
})

const handleEdit = (e: Event) => {
  e.stopPropagation()
  emit('edit')
}

const handleDelete = (e: Event) => {
  e.stopPropagation()
  emit('delete')
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }).replace(/\//g, '.')
}

const showTooltip = ref(false)
const tooltipStyle = ref({ top: '0px', left: '0px' })

const handleMouseMove = (e: MouseEvent) => {
  let left = e.clientX + 10
  let top = e.clientY + 10
  if (left + 200 > window.innerWidth) left = e.clientX - 210
  if (top + 60 > window.innerHeight) top = e.clientY - 70
  tooltipStyle.value = { top: `${top}px`, left: `${left}px` }
}

const handleMouseEnter = (e: MouseEvent) => {
  handleMouseMove(e)
  showTooltip.value = true
}

const handleMouseLeave = () => {
  showTooltip.value = false
}

// 组件卸载时确保关闭tooltip
onBeforeUnmount(() => {
  showTooltip.value = false
})
</script>

<template>
  <article
    class="card"
    :class="{ 'is-uploaded': !isEditable }"
    @mouseenter="handleMouseEnter"
    @mousemove="handleMouseMove"
    @mouseleave="handleMouseLeave"
  >
    <!-- 顶部栏：紧凑型 -->
    <div class="header">
      <span class="type-badge" :class="isEditable ? 'self' : 'uploaded'">
        {{ isEditable ? 'SELF' : 'UPLOAD' }}
      </span>
      <span class="title">{{ skill.name }}</span>
      <div v-if="!hideActions" class="actions">
        <span v-if="isEditable" class="action edit" @click="handleEdit">✎</span>
        <span class="action del" @click="handleDelete">×</span>
      </div>
    </div>

    <!-- 中间：主体内容区 -->
    <div class="body">
      <span class="icon" :style="{ background: iconColor }">{{ skill.icon }}</span>
      <div class="info">
        <div class="desc">{{ skill.description || '暂无描述' }}</div>
        <span class="version">v{{ skill.version || '1.0' }}</span>
      </div>
    </div>

    <!-- 底部栏：一行 -->
    <div class="footer">
      <div class="capability-tags">
        <span v-if="inputCount > 0" class="cap-tag input">{{ inputCount }}个输入</span>
        <span v-if="outputType" class="cap-tag output">{{ outputType }}</span>
        <span v-for="(tag, idx) in displayTags" :key="tag" class="cap-tag" :class="'color-' + (idx % 4)">{{ tag }}</span>
      </div>
      <div class="footer-right">
        <template v-if="showAuthor">
          <span class="author">{{ skill.author }}</span>
          <span class="sep">·</span>
        </template>
        <span class="date">{{ formatDate(skill.created_at) }}</span>
      </div>
    </div>

    <!-- Tooltip - 完整信息 -->
    <Teleport to="body">
      <div v-if="showTooltip" class="skill-tip" :style="tooltipStyle">
        <div class="tip-title">{{ skill.name }}</div>
        <div class="tip-desc">{{ skill.description || '暂无描述' }}</div>
        <div class="tip-meta">
          <span>版本: v{{ skill.version || '1.0' }}</span>
          <span>作者: {{ skill.author || '-' }}</span>
        </div>
        <div v-if="skill.tags?.length" class="tip-tags">
          标签: {{ skill.tags.join(', ') }}
        </div>
      </div>
    </Teleport>
  </article>
</template>

<style scoped>
.card {
  width: 100%;
  height: 100%;
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 10px;
  cursor: pointer;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  transition: box-shadow 0.2s, transform 0.15s;
}

.card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  transform: translateY(-1px);
}

.card.is-uploaded {
  border-style: dashed;
  border-color: #c9b8e0;
}

/* 顶部栏 - 紧凑 */
.header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: linear-gradient(135deg, #fef5f5 0%, #fdf8f8 100%);
  border-bottom: 1px solid #f5e8e8;
  flex-shrink: 0;
}

.type-badge {
  font-size: 8px;
  padding: 1px 5px;
  border-radius: 3px;
  font-weight: 700;
  letter-spacing: 0.5px;
  flex-shrink: 0;
}

.type-badge.self {
  background: #e74c3c;
  color: #fff;
}

.type-badge.uploaded {
  background: #9b59b6;
  color: #fff;
}

.title {
  flex: 1;
  font-size: 11px;
  font-weight: 600;
  color: #8e44ad;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.actions {
  display: flex;
  gap: 4px;
}

.action {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  cursor: pointer;
  border-radius: 3px;
  transition: background 0.15s;
}

.action.edit {
  color: #3498db;
}

.action.edit:hover {
  background: rgba(52, 152, 219, 0.1);
}

.action.del {
  color: #bdc3c7;
  font-size: 14px;
  font-weight: 300;
}

.action.del:hover {
  color: #e74c3c;
  background: rgba(231, 76, 60, 0.1);
}

/* 中间：主体内容区 */
.body {
  flex: 1;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  overflow: hidden;
  min-height: 0;
}

.icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
}

.info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  overflow: hidden;
}

.desc {
  font-size: 11px;
  color: #555;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.version {
  font-size: 9px;
  color: #aaa;
}

/* 底部栏 - 一行 */
.footer {
  padding: 6px 10px;
  background: #fafafa;
  border-top: 1px solid #f0f0f0;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.capability-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  overflow: hidden;
}

.cap-tag {
  font-size: 9px;
  padding: 2px 8px;
  border-radius: 4px;
  white-space: nowrap;
  font-weight: 500;
}

/* 输出类型 - 橙色系 */
.cap-tag.output {
  background: #fef3c7;
  color: #b45309;
}

/* 输入数 - 蓝色系 */
.cap-tag.input {
  background: #dbeafe;
  color: #1d4ed8;
}

/* 和谐配色 - 柔和色调 */
.cap-tag.color-0 {
  background: #f3e8ff;
  color: #7c3aed;
}

.cap-tag.color-1 {
  background: #e0f2fe;
  color: #0369a1;
}

.cap-tag.color-2 {
  background: #dcfce7;
  color: #15803d;
}

.cap-tag.color-3 {
  background: #fce7f3;
  color: #be185d;
}

.footer-right {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 4px;
}

.author {
  font-size: 9px;
  color: #888;
  white-space: nowrap;
}

.sep {
  font-size: 9px;
  color: #ccc;
}

.date {
  font-size: 9px;
  color: #aaa;
  white-space: nowrap;
}
</style>

<style>
.skill-tip {
  position: fixed;
  max-width: 200px;
  padding: 8px 10px;
  background: rgba(0,0,0,0.85);
  color: #fff;
  font-size: 11px;
  line-height: 1.4;
  border-radius: 6px;
  z-index: 99999;
  pointer-events: none;
}
</style>
