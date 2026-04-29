<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  visible: boolean
  sessionId?: string
}>()

const emit = defineEmits<{
  close: []
  submit: [data: { feedback_type: string; title: string; description: string; session_id?: string }]
}>()

// 表单数据
const feedbackType = ref<'bug' | 'suggestion' | 'other'>('bug')
const title = ref('')
const description = ref('')
const isSubmitting = ref(false)

// 类型选项
const typeOptions = [
  { value: 'bug', label: 'Bug 报告', icon: '🐛', color: '#ef4444' },
  { value: 'suggestion', label: '功能建议', icon: '💡', color: '#f59e0b' },
  { value: 'other', label: '其他反馈', icon: '💬', color: '#6b7280' },
]

// 验证
const isValid = computed(() => {
  return title.value.trim().length > 0
})

// 重置表单
const resetForm = () => {
  feedbackType.value = 'bug'
  title.value = ''
  description.value = ''
}

// 关闭
const handleClose = () => {
  resetForm()
  emit('close')
}

// 提交
const handleSubmit = async () => {
  if (!isValid.value || isSubmitting.value) return

  isSubmitting.value = true
  try {
    emit('submit', {
      feedback_type: feedbackType.value,
      title: title.value.trim(),
      description: description.value.trim(),
      session_id: props.sessionId
    })
    resetForm()
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay" @click.self="handleClose">
      <div class="feedback-modal">
        <!-- 头部 -->
        <div class="modal-header">
          <h2>问题反馈</h2>
          <button class="close-btn" @click="handleClose">&times;</button>
        </div>

        <!-- 内容 -->
        <div class="modal-body">
          <!-- 反馈类型 -->
          <div class="form-group">
            <label>反馈类型</label>
            <div class="type-options">
              <button
                v-for="opt in typeOptions"
                :key="opt.value"
                class="type-option"
                :class="{ active: feedbackType === opt.value }"
                :style="{ '--active-color': opt.color }"
                @click="feedbackType = opt.value as 'bug' | 'suggestion' | 'other'"
              >
                <span class="type-icon">{{ opt.icon }}</span>
                <span class="type-label">{{ opt.label }}</span>
              </button>
            </div>
          </div>

          <!-- 标题 -->
          <div class="form-group">
            <label>标题 <span class="required">*</span></label>
            <input
              v-model="title"
              type="text"
              placeholder="简要描述问题或建议"
              maxlength="200"
            />
          </div>

          <!-- 详细描述 -->
          <div class="form-group">
            <label>详细描述</label>
            <textarea
              v-model="description"
              placeholder="请详细描述问题的复现步骤、期望行为，或您的建议内容..."
              rows="5"
            ></textarea>
          </div>

          <!-- 提示 -->
          <div class="tips">
            <p>感谢您的反馈！我们会尽快处理。</p>
          </div>
        </div>

        <!-- 底部 -->
        <div class="modal-footer">
          <button class="btn-secondary" @click="handleClose">取消</button>
          <button
            class="btn-primary"
            :disabled="!isValid || isSubmitting"
            @click="handleSubmit"
          >
            {{ isSubmitting ? '提交中...' : '提交反馈' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.feedback-modal {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 8px;
  font-size: 24px;
  color: #9ca3af;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 20px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.form-group label .required {
  color: #ef4444;
}

.type-options {
  display: flex;
  gap: 10px;
}

.type-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px 10px;
  background: #f9fafb;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.type-option:hover {
  border-color: var(--active-color, #1677ff);
  background: white;
}

.type-option.active {
  border-color: var(--active-color, #1677ff);
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.type-icon {
  font-size: 24px;
}

.type-label {
  font-size: 12px;
  font-weight: 500;
  color: #374151;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s;
  resize: none;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #1677ff;
  box-shadow: 0 0 0 3px rgba(22, 119, 255, 0.1);
}

.tips {
  padding: 12px;
  background: #f0f9ff;
  border-radius: 8px;
  margin-top: 16px;
}

.tips p {
  margin: 0;
  font-size: 12px;
  color: #0369a1;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

.btn-primary,
.btn-secondary {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-primary {
  background: #1677ff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #4096ff;
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.btn-secondary {
  background: white;
  color: #374151;
  border: 1px solid #e5e7eb;
}

.btn-secondary:hover {
  background: #f9fafb;
}
</style>
