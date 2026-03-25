<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { chatSessionsApi, type ChatSession } from '@/api'

const props = defineProps<{
  currentSessionId: string | null
}>()

const emit = defineEmits<{
  selectSession: [session: ChatSession]
  deleteSession: [sessionId: string]
}>()

// 状态
const sessions = ref<ChatSession[]>([])
const total = ref(0)

// 编辑状态
const editingId = ref<string | null>(null)
const editingTitle = ref('')

// 按日期分组
const groupedSessions = computed(() => {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)
  const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)

  const groups: { label: string; sessions: ChatSession[] }[] = [
    { label: '今天', sessions: [] },
    { label: '昨天', sessions: [] },
    { label: '最近7天', sessions: [] },
    { label: '更早', sessions: [] },
  ]

  sessions.value.forEach(session => {
    const date = session.last_message_at ? new Date(session.last_message_at) : new Date(session.created_at || '')

    if (date >= today) {
      groups[0].sessions.push(session)
    } else if (date >= yesterday) {
      groups[1].sessions.push(session)
    } else if (date >= weekAgo) {
      groups[2].sessions.push(session)
    } else {
      groups[3].sessions.push(session)
    }
  })

  return groups.filter(g => g.sessions.length > 0)
})

// 加载会话列表（静默加载）
const loadSessions = async () => {
  try {
    const res = await chatSessionsApi.list(1, 50)
    sessions.value = res.sessions
    total.value = res.total
  } catch (e) {
    console.error('Failed to load sessions:', e)
  }
}

// 选择会话
const selectSession = (session: ChatSession) => {
  if (editingId.value) return
  emit('selectSession', session)
}

// 开始编辑
const startEdit = (session: ChatSession, e: Event) => {
  e.stopPropagation()
  editingId.value = session.id
  editingTitle.value = session.title || ''
}

// 保存编辑
const saveEdit = async () => {
  if (!editingId.value) return

  try {
    await chatSessionsApi.update(editingId.value, editingTitle.value)
    const session = sessions.value.find(s => s.id === editingId.value)
    if (session) {
      session.title = editingTitle.value
    }
  } catch (e) {
    console.error('Failed to update session:', e)
  } finally {
    editingId.value = null
  }
}

// 取消编辑
const cancelEdit = () => {
  editingId.value = null
}

// 删除会话
const deleteSession = async (session: ChatSession, e: Event) => {
  e.stopPropagation()

  try {
    await chatSessionsApi.delete(session.id)
    sessions.value = sessions.value.filter(s => s.id !== session.id)
    emit('deleteSession', session.id)
    showToast('已删除')
  } catch (err) {
    console.error('Failed to delete session:', err)
    showToast('删除失败', 'error')
  }
}

// Toast 提示
const toastMessage = ref('')
const toastType = ref<'success' | 'error'>('success')
const toastVisible = ref(false)

const showToast = (message: string, type: 'success' | 'error' = 'success') => {
  toastMessage.value = message
  toastType.value = type
  toastVisible.value = true
  setTimeout(() => {
    toastVisible.value = false
  }, 1200)
}

// 格式化时间
const formatTime = (dateStr: string | null) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 暴露方法
defineExpose({
  refresh: loadSessions,
  addSession: (session: ChatSession) => {
    sessions.value.unshift(session)
  }
})

onMounted(() => {
  loadSessions()
})
</script>

<template>
  <div class="chat-history">
    <!-- Toast -->
    <Transition name="toast">
      <div v-if="toastVisible" class="toast" :class="toastType">
        {{ toastMessage }}
      </div>
    </Transition>
    <!-- 头部 -->
    <div class="history-header">
      <span class="header-title">历史记录</span>
    </div>


    <!-- 会话列表 -->
    <div class="session-list">
      <!-- 空状态 -->
      <div v-if="sessions.length === 0" class="empty">
        <span class="empty-icon">💬</span>
        <p>暂无历史记录</p>
      </div>

      <!-- 分组列表 -->
      <div v-else>
        <div v-for="group in groupedSessions" :key="group.label" class="session-group">
          <div class="group-label">{{ group.label }}</div>
          <div
            v-for="session in group.sessions"
            :key="session.id"
            class="session-item"
            :class="{ active: session.id === currentSessionId }"
            @click="selectSession(session)"
          >
            <!-- 编辑模式 -->
            <template v-if="editingId === session.id">
              <input
                v-model="editingTitle"
                class="edit-input"
                @keydown.enter="saveEdit"
                @keydown.escape="cancelEdit"
                @blur="saveEdit"
                autofocus
              />
            </template>

            <!-- 正常显示 -->
            <template v-else>
              <div class="session-content">
                <span class="session-title">{{ session.title || '新对话' }}</span>
                <span class="session-meta">
                  {{ session.message_count }} 条 · {{ formatTime(session.last_message_at) }}
                </span>
                <span v-if="session.skill_names?.length" class="session-skills">
                  {{ session.skill_names.slice(0, 3).join(', ') }}{{ session.skill_names.length > 3 ? '...' : '' }}
                </span>
              </div>
              <div class="session-actions">
                <button class="action-btn" @click="startEdit(session, $event)" title="重命名">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                </button>
                <button class="action-btn delete" @click="deleteSession(session, $event)" title="删除">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                  </svg>
                </button>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-history {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-background, #fff);
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 12px 8px;
  border-bottom: 1px solid var(--color-border, #e2e8f0);
}

.header-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text, #1e293b);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.empty {
  text-align: center;
  padding: 32px 16px;
  color: var(--color-text-light, #94a3b8);
}

.empty-icon {
  font-size: 32px;
  display: block;
  margin-bottom: 8px;
}

.empty p {
  font-size: 13px;
  margin: 0;
}

.session-group {
  margin-bottom: 12px;
}

.group-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-light, #64748b);
  padding: 4px 8px;
  margin-bottom: 4px;
}

.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.session-item:hover {
  background: var(--color-background-soft, #f1f5f9);
}

.session-item.active {
  background: var(--color-primary-light, #eff6ff);
}

.session-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.session-title {
  font-size: 13px;
  color: var(--color-text, #1e293b);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-meta {
  font-size: 11px;
  color: var(--color-text-light, #94a3b8);
}

.session-skills {
  font-size: 10px;
  color: var(--color-primary, #3b82f6);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.session-item:hover .session-actions {
  opacity: 1;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  color: var(--color-text-light, #64748b);
  transition: all 0.15s ease;
}

.action-btn:hover {
  background: var(--color-background, #fff);
  color: var(--color-text, #1e293b);
}

.action-btn.delete:hover {
  color: #ef4444;
}

.action-btn svg {
  width: 12px;
  height: 12px;
}

.edit-input {
  flex: 1;
  padding: 4px 8px;
  border: 1px solid var(--color-primary, #3b82f6);
  border-radius: 4px;
  font-size: 13px;
  outline: none;
}

/* Toast */
.toast {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  padding: 5px 14px;
  border-radius: 4px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.9);
  background: rgba(0, 0, 0, 0.75);
  white-space: nowrap;
  z-index: 100;
}

.toast.error {
  color: #fca5a5;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.15s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(4px);
}
</style>
