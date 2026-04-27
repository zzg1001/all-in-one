<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  executionsApi,
  type ExecutionStatusResponse,
  type InteractionRequest,
  type WorkflowPreCheck,
  type CompletedStep
} from '@/api'

const props = defineProps<{
  workflowId: string
  workflowName?: string
}>()

const emit = defineEmits<{
  close: []
  completed: [result: ExecutionStatusResponse]
}>()

// 状态
const loading = ref(false)
const error = ref<string | null>(null)
const phase = ref<'precheck' | 'precollect' | 'running' | 'paused' | 'completed' | 'failed'>('precheck')

// 预检查结果
const precheck = ref<WorkflowPreCheck | null>(null)
const preInputs = ref<Record<string, any>>({})

// 执行状态
const execution = ref<ExecutionStatusResponse | null>(null)
const interactionValue = ref<any>(null)

// 计算属性
const progressPercent = computed(() => {
  if (!execution.value) return 0
  return Math.round((execution.value.current_step / execution.value.total_steps) * 100)
})

const currentInteraction = computed(() => execution.value?.pending_interaction)

const phaseLabel = computed(() => {
  const labels: Record<string, string> = {
    precheck: '检查中',
    precollect: '待配置',
    running: '执行中',
    paused: '等待输入',
    completed: '已完成',
    failed: '失败'
  }
  return labels[phase.value] || '未知'
})

// 静态文件 base URL（用于 /outputs 等静态资源）
const SERVER_BASE = import.meta.env.VITE_SERVER_BASE_URL || '/portal-api'

// 从 step.result 中提取 _output_file
const getOutputFile = (step: CompletedStep) => {
  if (!step.result) return null
  // result 可能是对象，包含 _output_file
  if (typeof step.result === 'object' && step.result._output_file) {
    return step.result._output_file
  }
  return null
}

// 获取完整的文件下载 URL
const getOutputFileUrl = (step: CompletedStep) => {
  const outputFile = getOutputFile(step)
  if (!outputFile?.url) return ''
  // 如果是相对路径，加上 Server base URL
  if (outputFile.url.startsWith('/')) {
    return `${SERVER_BASE}${outputFile.url}`
  }
  return outputFile.url
}

// 初始化：预检查工作流
const initPrecheck = async () => {
  loading.value = true
  error.value = null

  try {
    precheck.value = await executionsApi.precheck(props.workflowId)

    if (precheck.value.before_interactions.length > 0) {
      // 有需要预收集的交互
      phase.value = 'precollect'
      // 初始化默认值
      precheck.value.before_interactions.forEach(inter => {
        if (inter.type === 'confirm') {
          preInputs.value[inter.interaction_id] = false
        }
      })
    } else {
      // 无需预收集，直接开始
      await startExecution()
    }
  } catch (e: any) {
    error.value = e.message
    phase.value = 'failed'
  } finally {
    loading.value = false
  }
}

// 开始执行
const startExecution = async () => {
  loading.value = true
  error.value = null
  phase.value = 'running'

  try {
    execution.value = await executionsApi.start(props.workflowId, preInputs.value)
    updatePhaseFromStatus()
  } catch (e: any) {
    error.value = e.message
    phase.value = 'failed'
  } finally {
    loading.value = false
  }
}

// 提交交互响应
const submitInteraction = async () => {
  if (!execution.value || !currentInteraction.value) return

  loading.value = true
  error.value = null

  try {
    execution.value = await executionsApi.submitInteraction(execution.value.execution_id, {
      interaction_id: currentInteraction.value.interaction_id,
      value: interactionValue.value
    })
    interactionValue.value = null
    updatePhaseFromStatus()
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

// 取消执行
const cancelExecution = async () => {
  if (!execution.value) return

  try {
    await executionsApi.cancel(execution.value.execution_id)
    phase.value = 'failed'
    error.value = '用户取消'
  } catch (e: any) {
    error.value = e.message
  }
}

// 根据执行状态更新阶段
const updatePhaseFromStatus = () => {
  if (!execution.value) return

  switch (execution.value.status) {
    case 'running':
      phase.value = 'running'
      // 轮询状态
      pollStatus()
      break
    case 'paused':
      phase.value = 'paused'
      break
    case 'completed':
      phase.value = 'completed'
      emit('completed', execution.value)
      break
    case 'failed':
      phase.value = 'failed'
      error.value = execution.value.error || '执行失败'
      break
  }
}

// 轮询执行状态
let pollTimer: number | null = null
const pollStatus = async () => {
  if (pollTimer) clearTimeout(pollTimer)

  if (!execution.value || phase.value !== 'running') return

  try {
    execution.value = await executionsApi.getStatus(execution.value.execution_id)
    updatePhaseFromStatus()

    // 继续轮询
    if (phase.value === 'running') {
      pollTimer = window.setTimeout(pollStatus, 1000)
    }
  } catch (e: any) {
    error.value = e.message
  }
}

// 重试
const retry = () => {
  error.value = null
  preInputs.value = {}
  execution.value = null
  initPrecheck()
}

// 组件挂载时开始预检查
initPrecheck()

// 清理
watch(() => props.workflowId, () => {
  if (pollTimer) clearTimeout(pollTimer)
  retry()
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="true" class="runner-backdrop" @click.self="emit('close')">
        <div class="workflow-runner" :class="[`phase-${phase}`]">
          <!-- 顶部光晕 -->
          <div class="runner-glow"></div>

          <!-- 流动粒子背景 -->
          <div class="particle-field">
            <div class="particle" v-for="n in 6" :key="n"></div>
          </div>

          <!-- 头部 -->
          <header class="runner-header">
            <div class="header-left">
              <div class="workflow-icon">
                <svg viewBox="0 0 24 24" fill="none">
                  <path d="M12 2L2 7l10 5 10-5-10-5z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M2 17l10 5 10-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M2 12l10 5 10-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <div class="icon-ring"></div>
              </div>
              <div class="header-info">
                <h3>{{ workflowName || precheck?.workflow_name || '工作流执行' }}</h3>
                <span class="phase-badge" :class="`badge-${phase}`">
                  <span class="badge-dot"></span>
                  {{ phaseLabel }}
                </span>
              </div>
            </div>
            <button class="close-btn" @click="emit('close')" aria-label="关闭">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M18 6L6 18M6 6l12 12"/>
              </svg>
            </button>
          </header>

          <!-- 进度条 -->
          <div v-if="execution" class="progress-section">
            <div class="progress-track">
              <div class="progress-fill" :style="{ width: progressPercent + '%' }">
                <div class="progress-glow"></div>
              </div>
            </div>
            <div class="progress-meta">
              <span class="step-counter">
                <span class="current">{{ execution.current_step }}</span>
                <span class="divider">/</span>
                <span class="total">{{ execution.total_steps }}</span>
              </span>
              <span class="percent">{{ progressPercent }}%</span>
            </div>
          </div>

          <!-- 主体内容区 -->
          <main class="runner-body">
            <TransitionGroup name="phase-transition">
              <!-- 预收集交互 -->
              <div v-if="phase === 'precollect' && precheck" key="precollect" class="phase-content precollect-phase">
                <div class="phase-header">
                  <div class="phase-icon">
                    <svg viewBox="0 0 24 24" fill="none">
                      <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                  <div class="phase-title">
                    <h4>配置参数</h4>
                    <p>请填写以下信息以开始执行</p>
                  </div>
                </div>

                <div class="interactions-form">
                  <div
                    v-for="(inter, index) in precheck.before_interactions"
                    :key="inter.interaction_id"
                    class="form-item"
                    :style="{ '--delay': index * 0.08 + 's' }"
                  >
                    <label class="form-label">
                      {{ inter.label }}
                      <span v-if="inter.required" class="required-mark">必填</span>
                    </label>
                    <p v-if="inter.description" class="form-desc">{{ inter.description }}</p>

                    <!-- 文本输入 -->
                    <div v-if="inter.type === 'input'" class="input-wrapper">
                      <input
                        v-model="preInputs[inter.interaction_id]"
                        type="text"
                        :placeholder="inter.label"
                        class="text-input"
                      />
                      <div class="input-border"></div>
                    </div>

                    <!-- 单选 -->
                    <div v-else-if="inter.type === 'select'" class="select-wrapper">
                      <select v-model="preInputs[inter.interaction_id]" class="select-input">
                        <option value="" disabled>请选择...</option>
                        <option v-for="opt in inter.options" :key="opt.value" :value="opt.value">
                          {{ opt.label }}
                        </option>
                      </select>
                      <svg class="select-arrow" viewBox="0 0 24 24" fill="none">
                        <path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </div>

                    <!-- 确认框 -->
                    <label v-else-if="inter.type === 'confirm'" class="checkbox-wrapper">
                      <input type="checkbox" v-model="preInputs[inter.interaction_id]" class="checkbox-input" />
                      <span class="checkbox-box">
                        <svg viewBox="0 0 12 12" fill="none">
                          <path d="M2 6l3 3 5-6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                      </span>
                      <span class="checkbox-text">{{ inter.label }}</span>
                    </label>
                  </div>
                </div>

                <div class="actions">
                  <button class="btn btn-ghost" @click="emit('close')">
                    <span>取消</span>
                  </button>
                  <button class="btn btn-primary" @click="startExecution" :disabled="loading">
                    <svg v-if="loading" class="btn-spinner" viewBox="0 0 24 24">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none" stroke-dasharray="60 40"/>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="none">
                      <path d="M5 3l14 9-14 9V3z" fill="currentColor"/>
                    </svg>
                    <span>{{ loading ? '启动中' : '开始执行' }}</span>
                  </button>
                </div>
              </div>

              <!-- 运行中 -->
              <div v-else-if="phase === 'running'" key="running" class="phase-content running-phase">
                <div class="running-visual">
                  <div class="orbit-container">
                    <div class="orbit orbit-1"></div>
                    <div class="orbit orbit-2"></div>
                    <div class="orbit orbit-3"></div>
                    <div class="core-pulse"></div>
                  </div>
                  <p class="running-text">正在执行第 <strong>{{ (execution?.current_step || 0) + 1 }}</strong> 步</p>
                </div>

                <!-- 步骤时间线 -->
                <div v-if="execution?.completed_steps.length" class="steps-timeline">
                  <div
                    v-for="step in execution.completed_steps"
                    :key="step.step_index"
                    class="timeline-item completed"
                  >
                    <div class="timeline-marker">
                      <svg viewBox="0 0 16 16" fill="none">
                        <path d="M13.5 4.5L6 12L2.5 8.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </div>
                    <div class="timeline-content">
                      <span class="step-icon">{{ step.icon || '⚡' }}</span>
                      <span class="step-name">{{ step.skill_name }}</span>
                    </div>
                  </div>
                </div>

                <button class="btn btn-ghost btn-cancel" @click="cancelExecution">
                  <svg viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.5"/>
                    <path d="M15 9l-6 6M9 9l6 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                  </svg>
                  <span>取消执行</span>
                </button>
              </div>

              <!-- 暂停中（等待交互） -->
              <div v-else-if="phase === 'paused' && currentInteraction" key="paused" class="phase-content paused-phase">
                <div class="interaction-card">
                  <div class="card-header">
                    <span class="skill-tag">
                      <svg viewBox="0 0 16 16" fill="none">
                        <path d="M8 1l2 4 4.5.5-3.25 3.25.75 4.25L8 11l-4 2 .75-4.25L1.5 5.5 6 5l2-4z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                      {{ currentInteraction.skill_name }}
                    </span>
                    <span class="step-tag">步骤 {{ currentInteraction.step_index + 1 }}</span>
                  </div>

                  <h4 class="interaction-title">{{ currentInteraction.label }}</h4>
                  <p v-if="currentInteraction.description" class="interaction-desc">
                    {{ currentInteraction.description }}
                  </p>

                  <!-- 上下文参考 -->
                  <details v-if="currentInteraction.context" class="context-details">
                    <summary>
                      <svg viewBox="0 0 16 16" fill="none">
                        <path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                      查看前序步骤输出
                    </summary>
                    <pre class="context-code">{{ JSON.stringify(currentInteraction.context, null, 2) }}</pre>
                  </details>

                  <!-- 交互控件 -->
                  <div class="interaction-input">
                    <div v-if="currentInteraction.type === 'input'" class="input-wrapper">
                      <input
                        v-model="interactionValue"
                        type="text"
                        :placeholder="currentInteraction.label"
                        class="text-input"
                      />
                      <div class="input-border"></div>
                    </div>

                    <div v-else-if="currentInteraction.type === 'select'" class="select-wrapper">
                      <select v-model="interactionValue" class="select-input">
                        <option value="" disabled>请选择...</option>
                        <option v-for="opt in currentInteraction.options" :key="opt.value" :value="opt.value">
                          {{ opt.label }}
                        </option>
                      </select>
                      <svg class="select-arrow" viewBox="0 0 24 24" fill="none">
                        <path d="M6 9l6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </div>

                    <div v-else-if="currentInteraction.type === 'confirm'" class="confirm-actions">
                      <button class="btn btn-ghost" @click="interactionValue = false; submitInteraction()">
                        <span>取消</span>
                      </button>
                      <button class="btn btn-primary" @click="interactionValue = true; submitInteraction()">
                        <span>确认</span>
                      </button>
                    </div>
                  </div>

                  <div v-if="currentInteraction.type !== 'confirm'" class="actions">
                    <button class="btn btn-ghost" @click="cancelExecution">取消执行</button>
                    <button
                      class="btn btn-primary"
                      @click="submitInteraction"
                      :disabled="loading || (currentInteraction.required && !interactionValue)"
                    >
                      <svg v-if="loading" class="btn-spinner" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none" stroke-dasharray="60 40"/>
                      </svg>
                      <span>{{ loading ? '处理中' : '继续执行' }}</span>
                    </button>
                  </div>
                </div>

                <!-- 已完成步骤 -->
                <div v-if="execution?.completed_steps.length" class="steps-timeline">
                  <div
                    v-for="step in execution.completed_steps"
                    :key="step.step_index"
                    class="timeline-item completed"
                  >
                    <div class="timeline-marker">
                      <svg viewBox="0 0 16 16" fill="none">
                        <path d="M13.5 4.5L6 12L2.5 8.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </div>
                    <div class="timeline-content">
                      <span class="step-icon">{{ step.icon || '⚡' }}</span>
                      <span class="step-name">{{ step.skill_name }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 完成 -->
              <div v-else-if="phase === 'completed'" key="completed" class="phase-content completed-phase">
                <div class="success-visual">
                  <div class="success-ring">
                    <svg viewBox="0 0 80 80" fill="none">
                      <circle cx="40" cy="40" r="36" stroke="currentColor" stroke-width="2" stroke-dasharray="226" stroke-dashoffset="0" class="ring-progress"/>
                    </svg>
                  </div>
                  <div class="success-icon">
                    <svg viewBox="0 0 32 32" fill="none">
                      <path d="M8 16l6 6 10-12" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                </div>
                <h4 class="success-title">执行完成</h4>
                <p class="success-subtitle">所有步骤已成功执行</p>

                <div class="completed-results">
                  <div
                    v-for="step in execution?.completed_steps"
                    :key="step.step_index"
                    class="result-item"
                  >
                    <div class="result-icon">{{ step.icon || '✓' }}</div>
                    <div class="result-info">
                      <span class="result-name">{{ step.skill_name }}</span>
                      <span v-if="step.output" class="result-output">{{ step.output }}</span>
                    </div>
                    <a
                      v-if="getOutputFile(step)"
                      :href="getOutputFileUrl(step)"
                      target="_blank"
                      class="download-link"
                    >
                      <svg viewBox="0 0 16 16" fill="none">
                        <path d="M14 10v3a1 1 0 01-1 1H3a1 1 0 01-1-1v-3M11 7l-3 3-3-3M8 2v8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                      {{ getOutputFile(step)?.name || '下载' }}
                    </a>
                  </div>
                </div>

                <div class="actions">
                  <button class="btn btn-ghost" @click="emit('close')">关闭</button>
                  <button class="btn btn-primary" @click="retry">
                    <svg viewBox="0 0 24 24" fill="none">
                      <path d="M1 4v6h6M23 20v-6h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span>再次执行</span>
                  </button>
                </div>
              </div>

              <!-- 失败 -->
              <div v-else-if="phase === 'failed'" key="failed" class="phase-content failed-phase">
                <div class="error-visual">
                  <div class="error-ring"></div>
                  <div class="error-icon">
                    <svg viewBox="0 0 32 32" fill="none">
                      <path d="M20 12l-8 8M12 12l8 8" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
                    </svg>
                  </div>
                </div>
                <h4 class="error-title">执行失败</h4>
                <div class="error-message">
                  <svg viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.2"/>
                    <path d="M8 5v3M8 10v.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                  </svg>
                  <span>{{ error }}</span>
                </div>

                <div class="actions">
                  <button class="btn btn-ghost" @click="emit('close')">关闭</button>
                  <button class="btn btn-primary" @click="retry">
                    <svg viewBox="0 0 24 24" fill="none">
                      <path d="M1 4v6h6M23 20v-6h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span>重试</span>
                  </button>
                </div>
              </div>

              <!-- 加载中 -->
              <div v-else-if="loading" key="loading" class="phase-content loading-phase">
                <div class="loading-visual">
                  <div class="loading-ring"></div>
                  <div class="loading-ring delay-1"></div>
                  <div class="loading-ring delay-2"></div>
                </div>
                <p class="loading-text">加载中...</p>
              </div>
            </TransitionGroup>
          </main>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

/* === 背景遮罩 === */
.runner-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

/* === 主容器 === */
.workflow-runner {
  --accent: #6366f1;
  --accent-light: #818cf8;
  --accent-dark: #4f46e5;
  --success: #10b981;
  --error: #ef4444;
  --warning: #f59e0b;

  position: relative;
  width: 100%;
  max-width: 520px;
  max-height: 85vh;
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.95) 100%);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow:
    0 0 0 1px rgba(0, 0, 0, 0.03),
    0 4px 6px rgba(0, 0, 0, 0.02),
    0 12px 24px rgba(0, 0, 0, 0.04),
    0 32px 64px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* 状态变化 */
.workflow-runner.phase-completed {
  --accent: #10b981;
  border-color: rgba(16, 185, 129, 0.2);
}

.workflow-runner.phase-failed {
  --accent: #ef4444;
  border-color: rgba(239, 68, 68, 0.2);
}

/* === 顶部光晕 === */
.runner-glow {
  position: absolute;
  top: -100px;
  left: 50%;
  transform: translateX(-50%);
  width: 300%;
  height: 200px;
  background: radial-gradient(
    ellipse at center,
    rgba(99, 102, 241, 0.12) 0%,
    rgba(139, 92, 246, 0.06) 30%,
    transparent 60%
  );
  pointer-events: none;
  animation: glowPulse 4s ease-in-out infinite;
}

.phase-completed .runner-glow {
  background: radial-gradient(
    ellipse at center,
    rgba(16, 185, 129, 0.15) 0%,
    rgba(52, 211, 153, 0.08) 30%,
    transparent 60%
  );
}

.phase-failed .runner-glow {
  background: radial-gradient(
    ellipse at center,
    rgba(239, 68, 68, 0.12) 0%,
    rgba(248, 113, 113, 0.06) 30%,
    transparent 60%
  );
}

@keyframes glowPulse {
  0%, 100% { opacity: 1; transform: translateX(-50%) scale(1); }
  50% { opacity: 0.7; transform: translateX(-50%) scale(1.05); }
}

/* === 流动粒子 === */
.particle-field {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: var(--accent);
  border-radius: 50%;
  opacity: 0.15;
  animation: particleFloat 12s infinite ease-in-out;
}

.particle:nth-child(1) { top: 20%; left: 10%; animation-delay: 0s; }
.particle:nth-child(2) { top: 60%; left: 85%; animation-delay: -2s; }
.particle:nth-child(3) { top: 80%; left: 25%; animation-delay: -4s; }
.particle:nth-child(4) { top: 15%; left: 70%; animation-delay: -6s; }
.particle:nth-child(5) { top: 45%; left: 5%; animation-delay: -8s; }
.particle:nth-child(6) { top: 75%; left: 60%; animation-delay: -10s; }

@keyframes particleFloat {
  0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.15; }
  25% { transform: translate(20px, -30px) scale(1.5); opacity: 0.25; }
  50% { transform: translate(-10px, -50px) scale(1); opacity: 0.15; }
  75% { transform: translate(30px, -20px) scale(1.3); opacity: 0.2; }
}

/* === 头部 === */
.runner-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px 8px;
  position: relative;
  z-index: 1;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.workflow-icon {
  position: relative;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, var(--accent) 0%, #8b5cf6 100%);
  border-radius: 8px;
  color: white;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.25);
}

.workflow-icon svg {
  width: 14px;
  height: 14px;
}

.icon-ring {
  position: absolute;
  inset: -2px;
  border-radius: 10px;
  border: 1.5px solid transparent;
  background: linear-gradient(145deg, rgba(99, 102, 241, 0.3), rgba(139, 92, 246, 0.2)) border-box;
  mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  animation: ringPulse 3s ease-in-out infinite;
}

@keyframes ringPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.header-info h3 {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
  letter-spacing: -0.01em;
}

.phase-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 500;
  color: #64748b;
}

.badge-dot {
  width: 4px;
  height: 4px;
  background: currentColor;
  border-radius: 50%;
}

.badge-running .badge-dot,
.badge-precheck .badge-dot {
  background: var(--accent);
  animation: dotPulse 1.2s ease-in-out infinite;
}

.badge-completed {
  color: var(--success);
}

.badge-failed {
  color: var(--error);
}

.badge-paused {
  color: var(--warning);
}

@keyframes dotPulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.4); opacity: 0.6; }
}

.close-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.04);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: #94a3b8;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  color: #64748b;
}

.close-btn svg {
  width: 14px;
  height: 14px;
}

/* === 进度条 === */
.progress-section {
  padding: 0 20px 12px;
  position: relative;
  z-index: 1;
}

.progress-track {
  height: 6px;
  background: rgba(0, 0, 0, 0.06);
  border-radius: 3px;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), #8b5cf6, var(--accent-light));
  background-size: 200% 100%;
  border-radius: 4px;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  animation: progressShine 2s linear infinite;
}

@keyframes progressShine {
  from { background-position: 200% 0; }
  to { background-position: -200% 0; }
}

.progress-glow {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 30px;
  height: 20px;
  background: radial-gradient(ellipse at right, rgba(255, 255, 255, 0.6), transparent);
  filter: blur(4px);
}

.progress-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  font-size: 12px;
}

.step-counter {
  display: flex;
  align-items: baseline;
  gap: 2px;
  font-weight: 600;
}

.step-counter .current {
  color: var(--accent);
  font-size: 14px;
}

.step-counter .divider {
  color: #cbd5e1;
  margin: 0 2px;
}

.step-counter .total {
  color: #94a3b8;
}

.percent {
  color: #64748b;
  font-weight: 500;
}

/* === 主体区域 === */
.runner-body {
  flex: 1;
  overflow-y: auto;
  position: relative;
  z-index: 1;
}

.phase-content {
  padding: 6px 20px 20px;
}

/* === 预收集阶段 === */
.phase-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.phase-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1));
  border-radius: 12px;
  color: var(--accent);
}

.phase-icon svg {
  width: 20px;
  height: 20px;
}

.phase-title h4 {
  margin: 0 0 4px;
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.phase-title p {
  margin: 0;
  font-size: 13px;
  color: #64748b;
}

/* 表单 */
.interactions-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.form-item {
  animation: formItemIn 0.4s ease-out backwards;
  animation-delay: var(--delay, 0s);
}

@keyframes formItemIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
}

.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 8px;
}

.required-mark {
  font-size: 10px;
  font-weight: 500;
  padding: 2px 6px;
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
  border-radius: 4px;
}

.form-desc {
  margin: 0 0 8px;
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.5;
}

/* 输入框 */
.input-wrapper {
  position: relative;
}

.text-input {
  width: 100%;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  font-size: 14px;
  font-family: inherit;
  color: #0f172a;
  outline: none;
  transition: all 0.2s ease;
}

.text-input::placeholder {
  color: #94a3b8;
}

.text-input:focus {
  background: white;
  border-color: var(--accent);
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
}

.input-border {
  position: absolute;
  inset: 0;
  border-radius: 12px;
  pointer-events: none;
  opacity: 0;
  border: 2px solid var(--accent);
  transition: opacity 0.2s;
}

.text-input:focus + .input-border {
  opacity: 1;
}

/* 下拉选择 */
.select-wrapper {
  position: relative;
}

.select-input {
  width: 100%;
  padding: 14px 44px 14px 16px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  font-size: 14px;
  font-family: inherit;
  color: #0f172a;
  outline: none;
  cursor: pointer;
  appearance: none;
  transition: all 0.2s ease;
}

.select-input:focus {
  background: white;
  border-color: var(--accent);
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
}

.select-arrow {
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  color: #64748b;
  pointer-events: none;
}

/* 复选框 */
.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.checkbox-wrapper:hover {
  background: rgba(255, 255, 255, 0.9);
  border-color: rgba(99, 102, 241, 0.2);
}

.checkbox-input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.checkbox-box {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border: 2px solid #cbd5e1;
  border-radius: 6px;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.checkbox-box svg {
  width: 12px;
  height: 12px;
  color: white;
  opacity: 0;
  transform: scale(0.5);
  transition: all 0.15s ease;
}

.checkbox-input:checked + .checkbox-box {
  background: var(--accent);
  border-color: var(--accent);
}

.checkbox-input:checked + .checkbox-box svg {
  opacity: 1;
  transform: scale(1);
}

.checkbox-text {
  font-size: 14px;
  color: #334155;
  font-weight: 500;
}

/* === 按钮 === */
.actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.btn svg {
  width: 12px;
  height: 12px;
}

.btn-primary {
  background: linear-gradient(145deg, var(--accent) 0%, var(--accent-dark) 100%);
  color: white;
  box-shadow: 0 3px 10px rgba(99, 102, 241, 0.3);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
}

.btn-primary:active:not(:disabled) {
  transform: translateY(0);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-ghost {
  background: transparent;
  color: #64748b;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.btn-ghost:hover {
  background: rgba(0, 0, 0, 0.04);
  border-color: rgba(0, 0, 0, 0.15);
  color: #475569;
}

.btn-spinner {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* === 运行中 === */
.running-phase {
  text-align: center;
  padding-top: 20px;
}

.running-visual {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}

.orbit-container {
  position: relative;
  width: 100px;
  height: 100px;
}

.orbit {
  position: absolute;
  inset: 0;
  border: 2px solid transparent;
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: orbitSpin 2s linear infinite;
}

.orbit-1 {
  border-top-color: rgba(99, 102, 241, 0.8);
}

.orbit-2 {
  inset: 10px;
  animation-duration: 1.5s;
  animation-direction: reverse;
  border-top-color: rgba(139, 92, 246, 0.6);
}

.orbit-3 {
  inset: 20px;
  animation-duration: 1s;
  border-top-color: rgba(167, 139, 250, 0.4);
}

@keyframes orbitSpin {
  to { transform: rotate(360deg); }
}

.core-pulse {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 24px;
  height: 24px;
  background: linear-gradient(145deg, var(--accent), #8b5cf6);
  border-radius: 50%;
  box-shadow: 0 0 30px rgba(99, 102, 241, 0.5);
  animation: corePulse 1.5s ease-in-out infinite;
}

@keyframes corePulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
  50% { transform: translate(-50%, -50%) scale(0.85); opacity: 0.7; }
}

.running-text {
  font-size: 15px;
  color: #475569;
  margin: 0;
}

.running-text strong {
  color: var(--accent);
  font-weight: 700;
}

/* 步骤时间线 */
.steps-timeline {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin: 20px 0;
  padding: 16px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 14px;
}

.timeline-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  transition: all 0.2s ease;
}

.timeline-item.completed {
  background: rgba(16, 185, 129, 0.08);
}

.timeline-marker {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--success);
  border-radius: 8px;
  color: white;
  flex-shrink: 0;
}

.timeline-marker svg {
  width: 14px;
  height: 14px;
}

.timeline-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.step-icon {
  font-size: 16px;
}

.step-name {
  font-size: 13px;
  font-weight: 500;
  color: #334155;
}

.btn-cancel {
  margin: 0 auto;
}

/* === 暂停阶段 === */
.interaction-card {
  background: linear-gradient(165deg, rgba(255, 255, 255, 0.95), rgba(248, 250, 252, 0.9));
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 18px;
  padding: 20px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
}

.card-header {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}

.skill-tag,
.step-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 600;
  padding: 5px 10px;
  border-radius: 8px;
}

.skill-tag {
  background: linear-gradient(145deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1));
  color: var(--accent);
}

.skill-tag svg {
  width: 12px;
  height: 12px;
}

.step-tag {
  background: rgba(245, 158, 11, 0.1);
  color: #d97706;
}

.interaction-title {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.interaction-desc {
  margin: 0 0 16px;
  font-size: 13px;
  color: #64748b;
  line-height: 1.6;
}

.context-details {
  margin-bottom: 16px;
}

.context-details summary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--accent);
  cursor: pointer;
  padding: 8px 12px;
  background: rgba(99, 102, 241, 0.08);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.context-details summary:hover {
  background: rgba(99, 102, 241, 0.12);
}

.context-details summary svg {
  width: 12px;
  height: 12px;
  transition: transform 0.2s ease;
}

.context-details[open] summary svg {
  transform: rotate(90deg);
}

.context-code {
  margin: 10px 0 0;
  padding: 14px;
  background: #1e293b;
  color: #e2e8f0;
  border-radius: 10px;
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  overflow-x: auto;
  line-height: 1.5;
}

.interaction-input {
  margin-top: 16px;
}

.confirm-actions {
  display: flex;
  gap: 12px;
}

.confirm-actions .btn {
  flex: 1;
}

/* === 完成阶段 === */
.completed-phase {
  text-align: center;
  padding-top: 20px;
}

.success-visual {
  position: relative;
  width: 88px;
  height: 88px;
  margin: 0 auto 20px;
}

.success-ring {
  position: absolute;
  inset: 0;
  color: var(--success);
  animation: ringDraw 0.6s ease-out forwards;
}

.success-ring svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring-progress {
  stroke-dashoffset: 226;
  animation: ringProgress 0.8s ease-out 0.2s forwards;
}

@keyframes ringProgress {
  to { stroke-dashoffset: 0; }
}

.success-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #10b981, #059669);
  border-radius: 50%;
  color: white;
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.35);
  animation: iconPop 0.4s ease-out 0.4s backwards;
}

.success-icon svg {
  width: 28px;
  height: 28px;
}

@keyframes iconPop {
  from {
    transform: translate(-50%, -50%) scale(0);
    opacity: 0;
  }
  to {
    transform: translate(-50%, -50%) scale(1);
    opacity: 1;
  }
}

.success-title {
  margin: 0 0 6px;
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
}

.success-subtitle {
  margin: 0 0 24px;
  font-size: 14px;
  color: #64748b;
}

.completed-results {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: left;
  margin-bottom: 4px;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background: rgba(16, 185, 129, 0.06);
  border-radius: 12px;
  animation: resultIn 0.3s ease-out backwards;
}

.result-item:nth-child(1) { animation-delay: 0.5s; }
.result-item:nth-child(2) { animation-delay: 0.6s; }
.result-item:nth-child(3) { animation-delay: 0.7s; }

@keyframes resultIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
}

.result-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 8px;
  font-size: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.result-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.result-name {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.result-output {
  font-size: 11px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.download-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  background: linear-gradient(145deg, var(--accent), #8b5cf6);
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.download-link:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

.download-link svg {
  width: 14px;
  height: 14px;
}

/* === 失败阶段 === */
.failed-phase {
  text-align: center;
  padding-top: 20px;
}

.error-visual {
  position: relative;
  width: 88px;
  height: 88px;
  margin: 0 auto 20px;
}

.error-ring {
  position: absolute;
  inset: 0;
  border: 3px solid rgba(239, 68, 68, 0.2);
  border-radius: 50%;
  animation: errorShake 0.5s ease-out;
}

@keyframes errorShake {
  0%, 100% { transform: translateX(0); }
  20%, 60% { transform: translateX(-4px); }
  40%, 80% { transform: translateX(4px); }
}

.error-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #ef4444, #dc2626);
  border-radius: 50%;
  color: white;
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.35);
}

.error-icon svg {
  width: 24px;
  height: 24px;
}

.error-title {
  margin: 0 0 16px;
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
}

.error-message {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 18px;
  background: rgba(239, 68, 68, 0.08);
  border-radius: 12px;
  font-size: 13px;
  color: #dc2626;
  margin-bottom: 8px;
}

.error-message svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

/* === 加载中 === */
.loading-phase {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
}

.loading-visual {
  position: relative;
  width: 60px;
  height: 60px;
  margin-bottom: 20px;
}

.loading-ring {
  position: absolute;
  inset: 0;
  border: 3px solid rgba(99, 102, 241, 0.15);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-ring.delay-1 {
  inset: 8px;
  animation-delay: -0.3s;
  border-top-color: #8b5cf6;
}

.loading-ring.delay-2 {
  inset: 16px;
  animation-delay: -0.6s;
  border-top-color: #a78bfa;
}

.loading-text {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

/* === 过渡动画 === */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .workflow-runner,
.modal-leave-to .workflow-runner {
  transform: scale(0.95) translateY(20px);
  opacity: 0;
}

.phase-transition-enter-active,
.phase-transition-leave-active {
  transition: all 0.3s ease;
}

.phase-transition-enter-from {
  opacity: 0;
  transform: translateY(15px);
}

.phase-transition-leave-to {
  opacity: 0;
  transform: translateY(-15px);
}

/* === 滚动条 === */
.runner-body::-webkit-scrollbar {
  width: 6px;
}

.runner-body::-webkit-scrollbar-track {
  background: transparent;
}

.runner-body::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.runner-body::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.15);
}
</style>
