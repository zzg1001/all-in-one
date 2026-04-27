<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

// 上下缩放状态：true=展开显示导航项，false=收起只显示手柄
const isExpanded = ref(false)

// 拖拽移动位置（默认左下角）
const navPosition = ref({ x: 0, y: window.innerHeight - 80 })
const isDragging = ref(false)
const dragOffset = ref({ x: 0, y: 0 })
const dragStartPos = ref({ x: 0, y: 0 })
const hasMoved = ref(false)

const startDrag = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (!target.closest('.nav-drag-handle')) return
  e.preventDefault()
  isDragging.value = true
  hasMoved.value = false
  dragStartPos.value = { x: e.clientX, y: e.clientY }
  dragOffset.value = {
    x: e.clientX - navPosition.value.x,
    y: e.clientY - navPosition.value.y
  }
  document.addEventListener('mousemove', handleDrag)
  document.addEventListener('mouseup', stopDrag)
  document.body.style.userSelect = 'none'
}

const handleDrag = (e: MouseEvent) => {
  if (!isDragging.value) return
  const dx = Math.abs(e.clientX - dragStartPos.value.x)
  const dy = Math.abs(e.clientY - dragStartPos.value.y)
  if (dx > 5 || dy > 5) {
    hasMoved.value = true
    document.body.style.cursor = 'grabbing'
  }
  if (!hasMoved.value) return
  const newX = e.clientX - dragOffset.value.x
  const newY = e.clientY - dragOffset.value.y
  navPosition.value = {
    x: Math.max(0, Math.min(window.innerWidth - 60, newX)),
    y: Math.max(20, Math.min(window.innerHeight - 60, newY))
  }
}

const stopDrag = () => {
  // 没移动则视为点击，切换上下缩放
  if (!hasMoved.value) {
    isExpanded.value = !isExpanded.value
  }
  isDragging.value = false
  hasMoved.value = false
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

onUnmounted(() => {
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', stopDrag)
})

interface NavItem {
  path: string
  query?: { tab: string }
  icon: string
  label: string
  name: string
}

const navItems: NavItem[] = [
  { path: '/', query: { tab: 'agent' }, icon: '💬', label: '对话', name: 'home' },
  { path: '/', query: { tab: 'skills' }, icon: '⚡', label: 'Skills', name: 'skills' },
  { path: '/', query: { tab: 'workflows' }, icon: '🔗', label: '工作流', name: 'workflows' },
  { path: '/architecture', icon: '◈', label: '架构', name: 'architecture' },
  { path: '/monitor', icon: '📡', label: '监控', name: 'monitor' },
  { path: '/admin', icon: '⚙️', label: '管理', name: 'admin' }
]

const isActive = (item: NavItem) => {
  if (item.query?.tab) {
    return route.path === item.path && route.query.tab === item.query.tab
  }
  if (item.path === '/' && !item.query) {
    return route.path === '/' && !route.query.tab
  }
  return route.path === item.path
}

const navigate = (item: NavItem) => {
  if (item.query) {
    router.push({ path: item.path, query: item.query })
  } else {
    router.push(item.path)
  }
}
</script>

<template>
  <nav
    :class="['global-nav', { expanded: isExpanded, dragging: isDragging }]"
    :style="{ left: navPosition.x + 'px', top: navPosition.y + 'px' }"
    @mousedown="startDrag"
  >
    <!-- 拖拽手柄（点击上下缩放，拖拽移动） -->
    <div class="nav-drag-handle" :title="isExpanded ? '点击收起 / 拖拽移动' : '点击展开 / 拖拽移动'">
      <span></span><span></span><span></span>
    </div>

    <!-- 导航项（展开时显示） -->
    <div v-show="isExpanded" class="nav-items">
      <button
        v-for="item in navItems"
        :key="item.name"
        :class="['nav-item', { active: isActive(item) }]"
        @click="navigate(item)"
        :title="item.label"
      >
        <span class="nav-icon">{{ item.icon }}</span>
      </button>
    </div>
  </nav>
</template>

<style scoped>
.global-nav {
  position: fixed;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.2s ease;
}

.global-nav.dragging {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  opacity: 0.9;
}

/* 拖拽手柄 */
.nav-drag-handle {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  padding: 8px 10px;
  cursor: grab;
  transition: background 0.2s;
  border-radius: 8px;
}

.global-nav.expanded .nav-drag-handle {
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 6px;
  border-radius: 8px 8px 0 0;
}

.nav-drag-handle:hover {
  background: #f1f5f9;
}

.nav-drag-handle:active {
  cursor: grabbing;
}

.nav-drag-handle span {
  width: 18px;
  height: 2px;
  background: #cbd5e1;
  border-radius: 1px;
  transition: background 0.2s;
}

.nav-drag-handle:hover span {
  background: #94a3b8;
}

.nav-items {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 10px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-item:hover {
  background: #f1f5f9;
  color: #475569;
}

.nav-item.active {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  color: #667eea;
}

.nav-icon {
  font-size: 18px;
}
</style>
