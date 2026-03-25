<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useContextStore, type ContextItem as ContextItemType } from '@/stores/context'
import ContextItem from './ContextItem.vue'

const contextStore = useContextStore()

const emit = defineEmits<{
  addContext: []
}>()

// 预览相关
const previewItem = ref<ContextItemType | null>(null)
const showPreview = ref(false)

// 格式化总 token 数
const formattedTotalTokens = computed(() => {
  const tokens = contextStore.totalTokens
  if (tokens >= 1000) {
    return `~${(tokens / 1000).toFixed(1)}k`
  }
  return `~${tokens}`
})

// token 使用百分比
const tokenPercentage = computed(() => {
  return Math.min((contextStore.totalTokens / contextStore.maxTokens) * 100, 100)
})

// 处理移除
const handleRemove = (id: string) => {
  contextStore.removeItem(id)
}

// 处理预览
const handlePreview = (item: ContextItemType) => {
  previewItem.value = item
  showPreview.value = true
}

// 关闭预览
const closePreview = () => {
  showPreview.value = false
  previewItem.value = null
}

// 清空所有
const handleClearAll = () => {
  if (confirm('确定要清空所有上下文吗？')) {
    contextStore.clearAll()
  }
}

// 点击外部关闭预览
const handleOverlayClick = (e: MouseEvent) => {
  if ((e.target as HTMLElement).classList.contains('preview-overlay')) {
    closePreview()
  }
}
</script>

<template>
  <div class="context-panel" :class="{ expanded: contextStore.isExpanded }">
    <!-- 头部 -->
    <div class="panel-header" @click="contextStore.toggleExpanded">
      <div class="header-left">
        <span class="header-icon">📎</span>
        <span class="header-title">上下文</span>
        <span class="item-count" v-if="contextStore.itemCount > 0">
          ({{ contextStore.itemCount }})
        </span>
      </div>
      <div class="header-right">
        <span
          class="token-count"
          :class="{ warning: contextStore.isOverLimit }"
          v-if="contextStore.hasItems"
        >
          🔢 {{ formattedTotalTokens }} tokens
        </span>
        <span class="expand-icon">
          {{ contextStore.isExpanded ? '▼' : '▶' }}
        </span>
      </div>
    </div>

    <!-- 展开的内容 -->
    <div class="panel-content" v-show="contextStore.isExpanded">
      <!-- Token 进度条 -->
      <div class="token-progress" v-if="contextStore.hasItems">
        <div
          class="progress-bar"
          :style="{ width: `${tokenPercentage}%` }"
          :class="{ warning: tokenPercentage > 80, danger: tokenPercentage > 95 }"
        />
      </div>

      <!-- 空状态 -->
      <div class="empty-state" v-if="!contextStore.hasItems">
        <span class="empty-icon">📭</span>
        <p>暂无上下文</p>
        <p class="empty-hint">使用 @ 引用文件或数据便签</p>
      </div>

      <!-- 上下文列表 -->
      <div class="context-list" v-else>
        <ContextItem
          v-for="item in contextStore.items"
          :key="item.id"
          :item="item"
          @remove="handleRemove"
          @preview="handlePreview"
        />
      </div>

      <!-- 底部操作 -->
      <div class="panel-footer" v-if="contextStore.hasItems">
        <button class="footer-btn add-btn" @click="emit('addContext')">
          <span>+ 添加</span>
        </button>
        <button class="footer-btn clear-btn" @click="handleClearAll">
          <span>清空全部</span>
        </button>
      </div>
    </div>

    <!-- 预览弹窗 -->
    <Teleport to="body">
      <div
        class="preview-overlay"
        v-if="showPreview && previewItem"
        @click="handleOverlayClick"
      >
        <div class="preview-modal">
          <div class="preview-header">
            <h3>{{ previewItem.name }}</h3>
            <button class="close-btn" @click="closePreview">✕</button>
          </div>
          <div class="preview-meta">
            <span>类型: {{ previewItem.type }}</span>
            <span>Tokens: ~{{ previewItem.tokenCount }}</span>
          </div>
          <div class="preview-content">
            <pre>{{ previewItem.content }}</pre>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.context-panel {
  background: var(--color-background, #fff);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  user-select: none;
  background: var(--color-background-soft, #f8fafc);
  transition: background 0.2s ease;
}

.panel-header:hover {
  background: var(--color-background-mute, #f1f5f9);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  font-size: 16px;
}

.header-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--color-text, #1e293b);
}

.item-count {
  font-size: 13px;
  color: var(--color-text-light, #64748b);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.token-count {
  font-size: 12px;
  color: var(--color-text-light, #64748b);
  background: var(--color-background, #fff);
  padding: 4px 8px;
  border-radius: 6px;
}

.token-count.warning {
  background: #fef3c7;
  color: #b45309;
}

.expand-icon {
  font-size: 10px;
  color: var(--color-text-light, #94a3b8);
  transition: transform 0.2s ease;
}

.panel-content {
  border-top: 1px solid var(--color-border, #e2e8f0);
}

.token-progress {
  height: 3px;
  background: var(--color-background-mute, #e2e8f0);
}

.progress-bar {
  height: 100%;
  background: var(--color-primary, #3b82f6);
  transition: width 0.3s ease, background 0.3s ease;
}

.progress-bar.warning {
  background: #f59e0b;
}

.progress-bar.danger {
  background: #ef4444;
}

.empty-state {
  padding: 24px 16px;
  text-align: center;
  color: var(--color-text-light, #94a3b8);
}

.empty-icon {
  font-size: 32px;
  display: block;
  margin-bottom: 8px;
}

.empty-state p {
  margin: 4px 0;
  font-size: 13px;
}

.empty-hint {
  font-size: 12px !important;
  opacity: 0.7;
}

.context-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  max-height: 280px;
  overflow-y: auto;
}

.panel-footer {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid var(--color-border, #e2e8f0);
  background: var(--color-background-soft, #f8fafc);
}

.footer-btn {
  flex: 1;
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.add-btn {
  background: var(--color-primary, #3b82f6);
  color: #fff;
}

.add-btn:hover {
  background: var(--color-primary-dark, #2563eb);
}

.clear-btn {
  background: var(--color-background, #fff);
  color: var(--color-text-light, #64748b);
  border: 1px solid var(--color-border, #e2e8f0);
}

.clear-btn:hover {
  background: #fee2e2;
  color: #dc2626;
  border-color: #fecaca;
}

/* 预览弹窗 */
.preview-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.preview-modal {
  background: var(--color-background, #fff);
  border-radius: 12px;
  width: 100%;
  max-width: 640px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border, #e2e8f0);
}

.preview-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text, #1e293b);
}

.close-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: var(--color-background-soft, #f1f5f9);
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  color: var(--color-text-light, #64748b);
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: var(--color-background-mute, #e2e8f0);
  color: var(--color-text, #1e293b);
}

.preview-meta {
  display: flex;
  gap: 16px;
  padding: 12px 20px;
  font-size: 12px;
  color: var(--color-text-light, #64748b);
  background: var(--color-background-soft, #f8fafc);
}

.preview-content {
  flex: 1;
  overflow: auto;
  padding: 16px 20px;
}

.preview-content pre {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--color-text, #334155);
  font-family: 'SF Mono', Monaco, 'Courier New', monospace;
}
</style>
