<script setup lang="ts">
import { computed } from 'vue'
import { useContextStore, type ContextType } from '@/stores/context'

const contextStore = useContextStore()

const emit = defineEmits<{
  click: []
}>()

// 徽章配置
interface BadgeConfig {
  type: ContextType
  icon: string
  label: string
  color: string
  bgColor: string
}

const badgeConfigs: BadgeConfig[] = [
  { type: 'file', icon: '📄', label: '文件', color: '#1d4ed8', bgColor: '#dbeafe' },
  { type: 'data-note', icon: '📝', label: '便签', color: '#15803d', bgColor: '#dcfce7' },
  { type: 'skill-output', icon: '🔧', label: '输出', color: '#b45309', bgColor: '#fef3c7' },
  { type: 'url', icon: '🔗', label: '链接', color: '#4338ca', bgColor: '#e0e7ff' },
  { type: 'text-snippet', icon: '📋', label: '文本', color: '#7c3aed', bgColor: '#f3e8ff' },
  { type: 'conversation', icon: '💬', label: '对话', color: '#be185d', bgColor: '#fce7f3' }
]

// 生成要显示的徽章
const visibleBadges = computed(() => {
  const counts = contextStore.countByType
  return badgeConfigs
    .filter(config => (counts[config.type] || 0) > 0)
    .map(config => ({
      ...config,
      count: counts[config.type] || 0
    }))
})

// 总 token 格式化
const formattedTokens = computed(() => {
  const tokens = contextStore.totalTokens
  if (tokens >= 1000) {
    return `${(tokens / 1000).toFixed(1)}k`
  }
  return tokens.toString()
})
</script>

<template>
  <div
    class="context-badges"
    v-if="contextStore.hasItems"
    @click="emit('click')"
  >
    <div class="badges-container">
      <div
        v-for="badge in visibleBadges"
        :key="badge.type"
        class="badge"
        :style="{
          '--badge-color': badge.color,
          '--badge-bg': badge.bgColor
        }"
      >
        <span class="badge-icon">{{ badge.icon }}</span>
        <span class="badge-label">{{ badge.label }}</span>
        <span class="badge-count" v-if="badge.count > 1">{{ badge.count }}</span>
      </div>
    </div>
    <div class="token-indicator">
      <span class="token-icon">🔢</span>
      <span class="token-value">{{ formattedTokens }}</span>
    </div>
  </div>
</template>

<style scoped>
.context-badges {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--color-background-soft, #f8fafc);
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.context-badges:hover {
  background: var(--color-background-mute, #f1f5f9);
}

.badges-container {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: var(--badge-bg);
  color: var(--badge-color);
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  transition: transform 0.15s ease;
}

.badge:hover {
  transform: scale(1.02);
}

.badge-icon {
  font-size: 12px;
}

.badge-label {
  font-size: 11px;
}

.badge-count {
  background: var(--badge-color);
  color: #fff;
  font-size: 10px;
  padding: 0 5px;
  border-radius: 10px;
  min-width: 16px;
  text-align: center;
}

.token-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--color-text-light, #64748b);
  background: var(--color-background, #fff);
  padding: 4px 8px;
  border-radius: 6px;
}

.token-icon {
  font-size: 11px;
}

.token-value {
  font-weight: 500;
}
</style>
