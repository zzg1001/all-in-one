<script setup lang="ts">
import { ref } from 'vue'

const visible = ref(false)
const title = ref('')
const message = ref('')
const type = ref<'danger' | 'warning' | 'info'>('warning')
let resolvePromise: ((value: boolean) => void) | null = null

const confirm = (msg: string, options?: { title?: string; type?: 'danger' | 'warning' | 'info' }): Promise<boolean> => {
  message.value = msg
  title.value = options?.title || '确认操作'
  type.value = options?.type || 'warning'
  visible.value = true

  return new Promise((resolve) => {
    resolvePromise = resolve
  })
}

const handleConfirm = () => {
  visible.value = false
  resolvePromise?.(true)
}

const handleCancel = () => {
  visible.value = false
  resolvePromise?.(false)
}

defineExpose({ confirm })
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="visible" class="confirm-overlay" @click.self="handleCancel">
        <Transition name="scale">
          <div v-if="visible" class="confirm-dialog" :class="type">
            <div class="confirm-icon">
              <svg v-if="type === 'danger'" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
              </svg>
              <svg v-else viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
              </svg>
            </div>
            <div class="confirm-content">
              <h3 class="confirm-title">{{ title }}</h3>
              <p class="confirm-message">{{ message }}</p>
            </div>
            <div class="confirm-actions">
              <button class="btn-cancel" @click="handleCancel">取消</button>
              <button class="btn-confirm" :class="type" @click="handleConfirm">确定</button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.confirm-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(2px);
}

.confirm-dialog {
  background: white;
  border-radius: 16px;
  padding: 24px;
  width: 380px;
  max-width: 90vw;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  text-align: center;
}

.confirm-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.confirm-icon svg {
  width: 28px;
  height: 28px;
}

.confirm-dialog.warning .confirm-icon {
  background: #fef3c7;
  color: #f59e0b;
}

.confirm-dialog.danger .confirm-icon {
  background: #fee2e2;
  color: #ef4444;
}

.confirm-dialog.info .confirm-icon {
  background: #dbeafe;
  color: #3b82f6;
}

.confirm-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px;
}

.confirm-message {
  font-size: 14px;
  color: #6b7280;
  margin: 0 0 24px;
  line-height: 1.5;
}

.confirm-actions {
  display: flex;
  gap: 12px;
}

.btn-cancel, .btn-confirm {
  flex: 1;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  color: #374151;
}

.btn-cancel:hover {
  background: #e5e7eb;
}

.btn-confirm {
  border: none;
  color: white;
}

.btn-confirm.warning {
  background: #f59e0b;
}

.btn-confirm.warning:hover {
  background: #d97706;
}

.btn-confirm.danger {
  background: #ef4444;
}

.btn-confirm.danger:hover {
  background: #dc2626;
}

.btn-confirm.info {
  background: #3b82f6;
}

.btn-confirm.info:hover {
  background: #2563eb;
}

/* 动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.scale-enter-active {
  transition: all 0.2s ease;
}

.scale-leave-active {
  transition: all 0.15s ease;
}

.scale-enter-from {
  opacity: 0;
  transform: scale(0.9);
}

.scale-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
