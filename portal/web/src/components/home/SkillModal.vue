<script setup lang="ts">
import { watch } from 'vue'
import type { Skill } from '@/api/skills'

const props = defineProps<{
  skill: Skill | null
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'execute', skill: Skill): void
}>()

watch(() => props.visible, (val) => {
  if (val) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

function getFileName(name: string): string {
  return name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '') + '.skill.json'
}

function handleBackdropClick(e: MouseEvent) {
  if ((e.target as HTMLElement).classList.contains('modal-overlay')) {
    emit('close')
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    emit('close')
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="visible && skill"
        class="modal-overlay"
        @click="handleBackdropClick"
        @keydown="handleKeydown"
        tabindex="-1"
      >
        <div class="modal">
          <!-- Modal Header -->
          <div class="modal-header">
            <div class="modal-dots">
              <span class="dot red"></span>
              <span class="dot yellow"></span>
              <span class="dot green"></span>
            </div>
            <span class="modal-title mono">{{ getFileName(skill.name) }}</span>
            <button class="close-btn" @click="$emit('close')">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>

          <!-- Modal Body -->
          <div class="modal-body">
            <!-- Description -->
            <div class="modal-section">
              <h4 class="section-label mono">// Description</h4>
              <div class="code-block mono">
                {{ skill.description || 'No description available' }}
              </div>
            </div>

            <!-- System Prompt -->
            <div class="modal-section">
              <h4 class="section-label mono">// System Prompt</h4>
              <div class="code-block mono">
                {{ skill.system_prompt || 'No system prompt defined' }}
              </div>
            </div>
          </div>

          <!-- Modal Footer -->
          <div class="modal-footer">
            <button class="btn btn-secondary mono" @click="$emit('close')">
              Close
            </button>
            <button class="btn btn-primary mono" @click="$emit('execute', skill)">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
              Execute Skill
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 640px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-terminal);
  border-bottom: 1px solid var(--border-light);
}

.modal-dots {
  display: flex;
  gap: 8px;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.dot.red { background: var(--dot-red); }
.dot.yellow { background: var(--dot-yellow); }
.dot.green { background: var(--dot-green); }

.modal-title {
  flex: 1;
  text-align: center;
  font-size: 13px;
  color: var(--text-muted);
}

.close-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all 0.15s;
}

.close-btn:hover {
  background: var(--bg-code);
  color: var(--text-primary);
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.modal-section {
  margin-bottom: 24px;
}

.modal-section:last-child {
  margin-bottom: 0;
}

.section-label {
  font-size: 12px;
  color: var(--syntax-comment);
  text-transform: uppercase;
  margin-bottom: 12px;
  letter-spacing: 0.5px;
}

.code-block {
  background: var(--bg-terminal);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 16px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--border-light);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-secondary {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.btn-secondary:hover {
  border-color: var(--text-muted);
  color: var(--text-primary);
}

.btn-primary {
  background: var(--accent-orange);
  border: 1px solid var(--accent-orange);
  color: white;
}

.btn-primary:hover {
  background: #ea580c;
}

/* Transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s;
}

.modal-enter-active .modal,
.modal-leave-active .modal {
  transition: transform 0.3s;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal,
.modal-leave-to .modal {
  transform: translateY(20px);
}
</style>
