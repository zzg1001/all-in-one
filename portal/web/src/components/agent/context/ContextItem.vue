<script setup lang="ts">
import { computed } from 'vue'
import type { ContextItem, ContextType } from '@/stores/context'

const props = defineProps<{
  item: ContextItem
}>()

const emit = defineEmits<{
  remove: [id: string]
  preview: [item: ContextItem]
}>()

// 类型图标映射
const typeIcons: Record<ContextType, string> = {
  'file': '📄',
  'data-note': '📝',
  'skill-output': '🔧',
  'url': '🔗',
  'text-snippet': '📋',
  'conversation': '💬'
}

// 类型标签映射
const typeLabels: Record<ContextType, string> = {
  'file': '文件',
  'data-note': '便签',
  'skill-output': '技能输出',
  'url': '链接',
  'text-snippet': '文本',
  'conversation': '对话'
}

const icon = computed(() => typeIcons[props.item.type] || '📎')
const typeLabel = computed(() => typeLabels[props.item.type] || '其他')

// 格式化 token 数
const formattedTokens = computed(() => {
  const tokens = props.item.tokenCount
  if (tokens >= 1000) {
    return `${(tokens / 1000).toFixed(1)}k`
  }
  return tokens.toString()
})

// 截断显示名称
const displayName = computed(() => {
  const name = props.item.name
  if (name.length > 24) {
    return name.slice(0, 22) + '...'
  }
  return name
})
</script>

<template>
  <div class="context-item" :class="`type-${item.type}`">
    <div class="item-icon">{{ icon }}</div>
    <div class="item-info">
      <div class="item-name" :title="item.name">{{ displayName }}</div>
      <div class="item-meta">
        <span class="item-type">{{ typeLabel }}</span>
        <span class="item-tokens">{{ formattedTokens }} tokens</span>
      </div>
    </div>
    <div class="item-actions">
      <button
        class="action-btn preview-btn"
        @click="emit('preview', item)"
        title="预览内容"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
          <circle cx="12" cy="12" r="3"/>
        </svg>
      </button>
      <button
        class="action-btn remove-btn"
        @click="emit('remove', item.id)"
        title="移除"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.context-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: var(--color-background-soft, #f8f9fa);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.context-item:hover {
  background: var(--color-background-mute, #f0f0f0);
}

.item-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text, #333);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: var(--color-text-light, #888);
  margin-top: 2px;
}

.item-type {
  background: var(--color-background-mute, #e9ecef);
  padding: 1px 6px;
  border-radius: 4px;
}

.item-tokens {
  opacity: 0.8;
}

.item-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.context-item:hover .item-actions {
  opacity: 1;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  color: var(--color-text-light, #666);
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: var(--color-background, #fff);
}

.remove-btn:hover {
  color: #e53e3e;
}

.preview-btn:hover {
  color: var(--color-primary, #3b82f6);
}

/* 类型颜色 */
.type-file .item-type { background: #dbeafe; color: #1d4ed8; }
.type-data-note .item-type { background: #dcfce7; color: #15803d; }
.type-skill-output .item-type { background: #fef3c7; color: #b45309; }
.type-url .item-type { background: #e0e7ff; color: #4338ca; }
.type-text-snippet .item-type { background: #f3e8ff; color: #7c3aed; }
.type-conversation .item-type { background: #fce7f3; color: #be185d; }
</style>
