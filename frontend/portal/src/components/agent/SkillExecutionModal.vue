<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { agentApi } from '@/api'

interface Message {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  isExecuting?: boolean
}

const props = defineProps<{
  show: boolean
  skill: {
    name: string
    icon: string
    description: string
  }
  context?: string
}>()

const emit = defineEmits<{
  close: []
  complete: [result: { success: boolean; output?: string; params?: Record<string, any> }]
}>()

// 状态
const messages = ref<Message[]>([])
const inputText = ref('')
const isProcessing = ref(false)
const isComplete = ref(false)
const collectedParams = ref<Record<string, any>>({})
const chatContainer = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)

// 初始化
const initConversation = () => {
  messages.value = []
  isComplete.value = false
  collectedParams.value = {}
  inputText.value = ''

  // AI主动发起对话
  const greeting = generateGreeting()
  messages.value.push({
    id: 1,
    role: 'assistant',
    content: greeting,
    timestamp: new Date()
  })

  // 聚焦输入框
  nextTick(() => {
    inputRef.value?.focus()
  })
}

// 生成友好的问候语
const generateGreeting = () => {
  const context = props.context
  const skillName = props.skill.name

  if (context) {
    // 根据上下文生成具体问题
    if (context.includes('画') || context.includes('设计') || context.includes('图')) {
      return `收到！我来帮你「${context}」\n\n请告诉我：\n• 风格偏好（写实/卡通/抽象...）\n• 配色要求\n• 其他细节`
    }
    return `好的，关于「${context}」\n\n我需要了解更多细节，请补充说明：`
  }

  return `Hi! 我是 ${skillName}\n\n${props.skill.description}\n\n请告诉我你的具体需求：`
}

// 发送消息
const sendMessage = async () => {
  if (!inputText.value.trim() || isProcessing.value) return

  const userMessage = inputText.value.trim()
  inputText.value = ''

  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: userMessage,
    timestamp: new Date()
  })

  scrollToBottom()
  isProcessing.value = true

  // AI 回复占位
  const aiMsgId = Date.now() + 1
  messages.value.push({
    id: aiMsgId,
    role: 'assistant',
    content: '',
    timestamp: new Date()
  })

  try {
    const history = messages.value
      .filter(m => m.role !== 'system' && m.id !== aiMsgId)
      .map(m => ({ role: m.role as 'user' | 'assistant', content: m.content }))

    let fullContent = ''
    for await (const event of agentApi.chatStream({
      message: userMessage,
      history: history
    })) {
      // chatStream 返回的是 ChatStreamEvent 对象，需要提取 content
      if (event.type === 'text' && event.content) {
        fullContent += event.content
      }
      const msgIndex = messages.value.findIndex(m => m.id === aiMsgId)
      if (msgIndex !== -1) {
        messages.value[msgIndex] = {
          ...messages.value[msgIndex],
          content: fullContent.replace(/<!--SKILL_EXECUTE:.*?-->/g, '')
        }
      }
      scrollToBottom()
    }

    // 检查是否可以执行
    const executeMatch = fullContent.match(/<!--SKILL_EXECUTE:(\{.*?\})-->/)
    if (executeMatch) {
      try {
        const execData = JSON.parse(executeMatch[1])
        if (execData.ready) {
          collectedParams.value = execData.params || {}
          await executeSkill()
        }
      } catch (e) {
        console.error('Parse execute data failed:', e)
      }
    }

  } catch (error: any) {
    const msgIndex = messages.value.findIndex(m => m.id === aiMsgId)
    if (msgIndex !== -1) {
      messages.value[msgIndex] = {
        ...messages.value[msgIndex],
        content: `出现问题：${error.message}`
      }
    }
  } finally {
    isProcessing.value = false
  }
}

// 执行技能
const executeSkill = async () => {
  isProcessing.value = true

  // 显示执行状态
  messages.value.push({
    id: Date.now(),
    role: 'system',
    content: '正在执行...',
    timestamp: new Date(),
    isExecuting: true
  })
  scrollToBottom()

  // 模拟执行
  await new Promise(resolve => setTimeout(resolve, 1500))

  // 完成
  isComplete.value = true

  // 移除执行中消息
  messages.value = messages.value.filter(m => !m.isExecuting)

  isProcessing.value = false
  scrollToBottom()

  // 自动关闭并返回结果
  setTimeout(() => {
    emit('complete', {
      success: true,
      params: collectedParams.value
    })
    emit('close')
  }, 800)
}

// 快速执行
const quickExecute = () => {
  collectedParams.value = { quickMode: true, context: props.context }
  executeSkill()
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

// 关闭
const handleClose = () => {
  emit('close')
}

// 监听显示
watch(() => props.show, (newVal) => {
  if (newVal) {
    initConversation()
  }
})

// Markdown 渲染
const renderMarkdown = (text: string): string => {
  return text
    .replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre class="code-block"><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
    .replace(/• /g, '<span class="bullet">•</span> ')
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="show" class="modal-backdrop" @click.self="handleClose">
        <div class="skill-dialog" :class="{ 'is-complete': isComplete }">
          <!-- 顶部光晕 -->
          <div class="dialog-glow"></div>

          <!-- 头部 -->
          <header class="dialog-header">
            <div class="skill-identity">
              <div class="skill-avatar">
                <span class="avatar-icon">{{ skill.icon }}</span>
                <div class="avatar-ring"></div>
              </div>
              <div class="skill-meta">
                <h3 class="skill-title">{{ skill.name }}</h3>
                <Transition name="badge">
                  <span v-if="isComplete" class="status-complete">
                    <svg viewBox="0 0 16 16" fill="none">
                      <path d="M13.5 4.5L6 12L2.5 8.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    已完成
                  </span>
                  <span v-else-if="isProcessing" class="status-processing">
                    <span class="pulse-dot"></span>
                    处理中
                  </span>
                </Transition>
              </div>
            </div>
            <button class="close-button" @click="handleClose" aria-label="关闭">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M18 6L6 18M6 6l12 12"/>
              </svg>
            </button>
          </header>

          <!-- 对话区 -->
          <main class="dialog-body" ref="chatContainer">
            <TransitionGroup name="message" tag="div" class="message-list">
              <div
                v-for="msg in messages"
                :key="msg.id"
                class="message-item"
                :class="[
                  `is-${msg.role}`,
                  { 'is-executing': msg.isExecuting }
                ]"
              >
                <!-- AI 消息 -->
                <template v-if="msg.role === 'assistant'">
                  <div class="message-avatar">
                    <span>{{ skill.icon }}</span>
                  </div>
                  <div class="message-bubble">
                    <div v-if="msg.content" class="bubble-text" v-html="renderMarkdown(msg.content)"></div>
                    <div v-else class="typing-indicator">
                      <span></span><span></span><span></span>
                    </div>
                  </div>
                </template>

                <!-- 用户消息 -->
                <template v-else-if="msg.role === 'user'">
                  <div class="message-bubble">
                    <div class="bubble-text">{{ msg.content }}</div>
                  </div>
                </template>

                <!-- 系统消息 -->
                <template v-else>
                  <div class="system-message">
                    <div v-if="msg.isExecuting" class="executing-indicator">
                      <svg class="spinner-ring" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none" stroke-dasharray="60 40"/>
                      </svg>
                      <span>{{ msg.content }}</span>
                    </div>
                    <span v-else>{{ msg.content }}</span>
                  </div>
                </template>
              </div>
            </TransitionGroup>
          </main>

          <!-- 底部 -->
          <footer class="dialog-footer">
            <Transition name="fade" mode="out-in">
              <!-- 完成状态 -->
              <div v-if="isComplete" class="complete-state">
                <div class="complete-check">
                  <svg viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.5"/>
                    <path d="M8 12l3 3 5-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
                <span class="complete-text">配置完成，即将返回...</span>
              </div>

              <!-- 输入状态 -->
              <div v-else class="input-state">
                <div class="input-container">
                  <textarea
                    ref="inputRef"
                    v-model="inputText"
                    placeholder="输入你的需求..."
                    @keydown.enter.exact.prevent="sendMessage"
                    :disabled="isProcessing"
                    rows="1"
                  ></textarea>
                  <button
                    class="send-button"
                    @click="sendMessage"
                    :disabled="!inputText.trim() || isProcessing"
                  >
                    <svg viewBox="0 0 24 24" fill="none">
                      <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                </div>
                <button
                  v-if="!isProcessing"
                  class="quick-action"
                  @click="quickExecute"
                >
                  <svg viewBox="0 0 16 16" fill="none">
                    <path d="M8.5 1L3 9h4.5l-.5 6 5.5-8H8l.5-6z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  跳过配置，直接执行
                </button>
              </div>
            </Transition>
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* 背景遮罩 */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

/* 对话框主体 */
.skill-dialog {
  position: relative;
  width: 100%;
  max-width: 440px;
  max-height: 80vh;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow:
    0 0 0 1px rgba(0, 0, 0, 0.03),
    0 2px 4px rgba(0, 0, 0, 0.02),
    0 8px 16px rgba(0, 0, 0, 0.04),
    0 24px 48px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transform-origin: center;
}

.skill-dialog.is-complete {
  border-color: rgba(16, 185, 129, 0.3);
}

/* 顶部光晕 */
.dialog-glow {
  position: absolute;
  top: -60%;
  left: 50%;
  transform: translateX(-50%);
  width: 200%;
  height: 200px;
  background: radial-gradient(
    ellipse at center,
    rgba(99, 102, 241, 0.08) 0%,
    transparent 60%
  );
  pointer-events: none;
}

.skill-dialog.is-complete .dialog-glow {
  background: radial-gradient(
    ellipse at center,
    rgba(16, 185, 129, 0.1) 0%,
    transparent 60%
  );
}

/* 头部 */
.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  position: relative;
  z-index: 1;
}

.skill-identity {
  display: flex;
  align-items: center;
  gap: 14px;
}

.skill-avatar {
  position: relative;
  width: 44px;
  height: 44px;
}

.avatar-icon {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  background: linear-gradient(145deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 14px;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
}

.avatar-ring {
  position: absolute;
  inset: -3px;
  border-radius: 17px;
  border: 2px solid transparent;
  background: linear-gradient(145deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2)) border-box;
  -webkit-mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
  mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
}

.skill-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.skill-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
  letter-spacing: -0.01em;
}

.status-complete,
.status-processing {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 500;
}

.status-complete {
  color: #10b981;
}

.status-complete svg {
  width: 14px;
  height: 14px;
}

.status-processing {
  color: #6366f1;
}

.pulse-dot {
  width: 6px;
  height: 6px;
  background: currentColor;
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.close-button {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  color: #94a3b8;
  transition: all 0.2s ease;
}

.close-button:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #64748b;
}

.close-button svg {
  width: 20px;
  height: 20px;
}

/* 对话区 */
.dialog-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px 24px 20px;
  min-height: 200px;
  max-height: 400px;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-item {
  display: flex;
  gap: 10px;
  animation: messageIn 0.3s ease-out;
}

@keyframes messageIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-item.is-user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: linear-gradient(145deg, #6366f1 0%, #8b5cf6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(99, 102, 241, 0.2);
}

.message-bubble {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 18px;
  font-size: 14px;
  line-height: 1.55;
}

.is-assistant .message-bubble {
  background: #f1f5f9;
  color: #334155;
  border-bottom-left-radius: 6px;
}

.is-user .message-bubble {
  background: linear-gradient(145deg, #6366f1 0%, #8b5cf6 100%);
  color: #fff;
  border-bottom-right-radius: 6px;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.25);
}

.bubble-text :deep(strong) {
  font-weight: 600;
}

.bubble-text :deep(.bullet) {
  color: #6366f1;
  font-weight: bold;
}

.is-user .bubble-text :deep(.bullet) {
  color: rgba(255, 255, 255, 0.8);
}

/* 打字指示器 */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: #94a3b8;
  border-radius: 50%;
  animation: typingBounce 1.4s ease-in-out infinite;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.15s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.3s; }

@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-6px); }
}

/* 系统消息 */
.system-message {
  width: 100%;
  display: flex;
  justify-content: center;
}

.executing-indicator {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(99, 102, 241, 0.08);
  border-radius: 20px;
  font-size: 13px;
  color: #6366f1;
  font-weight: 500;
}

.spinner-ring {
  width: 16px;
  height: 16px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 底部 */
.dialog-footer {
  padding: 16px 24px 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  background: rgba(248, 250, 252, 0.5);
}

.input-state {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-container {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.input-container textarea {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 14px;
  font-size: 14px;
  font-family: inherit;
  resize: none;
  outline: none;
  background: #fff;
  transition: all 0.2s ease;
  min-height: 44px;
  max-height: 100px;
}

.input-container textarea:focus {
  border-color: rgba(99, 102, 241, 0.5);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.input-container textarea::placeholder {
  color: #94a3b8;
}

.send-button {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #6366f1 0%, #8b5cf6 100%);
  border: none;
  border-radius: 14px;
  cursor: pointer;
  color: #fff;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.send-button svg {
  width: 20px;
  height: 20px;
}

.send-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}

.send-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.quick-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  background: transparent;
  border: 1px dashed rgba(0, 0, 0, 0.1);
  border-radius: 10px;
  font-size: 13px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-action:hover {
  background: rgba(0, 0, 0, 0.02);
  border-color: rgba(0, 0, 0, 0.15);
  color: #475569;
}

.quick-action svg {
  width: 14px;
  height: 14px;
}

/* 完成状态 */
.complete-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
}

.complete-check {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #10b981;
  animation: checkPop 0.4s ease;
}

.complete-check svg {
  width: 48px;
  height: 48px;
}

@keyframes checkPop {
  0% { transform: scale(0); opacity: 0; }
  50% { transform: scale(1.2); }
  100% { transform: scale(1); opacity: 1; }
}

.complete-text {
  font-size: 14px;
  color: #64748b;
}

/* 动画 */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.25s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .skill-dialog,
.modal-leave-to .skill-dialog {
  transform: scale(0.95) translateY(10px);
  opacity: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: all 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.badge-enter-active {
  transition: all 0.3s ease;
}

.badge-enter-from {
  opacity: 0;
  transform: translateX(-10px);
}

.message-enter-active {
  transition: all 0.3s ease;
}

.message-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

/* 滚动条 */
.dialog-body::-webkit-scrollbar {
  width: 4px;
}

.dialog-body::-webkit-scrollbar-track {
  background: transparent;
}

.dialog-body::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 2px;
}

.dialog-body::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.15);
}
</style>
