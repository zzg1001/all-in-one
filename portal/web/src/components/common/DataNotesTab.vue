<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { dataNotesApi } from '@/api'

const noteCount = ref(0)
const showModal = ref(false)
const isPinned = ref(false)  // 点击弹框内部后固定
let hideTimeout: number | null = null

const loadNoteCount = async () => {
  try {
    const notes = await dataNotesApi.getAll()
    noteCount.value = notes.length
  } catch (e) {
    console.error('Failed to load note count:', e)
  }
}

const clearHideTimeout = () => {
  if (hideTimeout) {
    clearTimeout(hideTimeout)
    hideTimeout = null
  }
}

const handleTabEnter = () => {
  clearHideTimeout()
  showModal.value = true
}

const handleTabLeave = () => {
  if (isPinned.value) return
  hideTimeout = window.setTimeout(() => {
    showModal.value = false
  }, 150)
}

const handleModalEnter = () => {
  clearHideTimeout()
}

const handleModalLeave = () => {
  if (isPinned.value) return
  hideTimeout = window.setTimeout(() => {
    showModal.value = false
    loadNoteCount()
  }, 150)
}

const handleTabClick = () => {
  clearHideTimeout()
  showModal.value = !showModal.value
  if (!showModal.value) {
    isPinned.value = false
  }
}

// 点击弹框内部，固定不关闭
const handleModalClick = () => {
  isPinned.value = true
}

// 点击外部关闭
const handleClickOutside = (e: MouseEvent) => {
  if (!isPinned.value || !showModal.value) return
  const target = e.target as HTMLElement
  if (!target.closest('.popup-container') && !target.closest('.data-tab')) {
    showModal.value = false
    isPinned.value = false
    loadNoteCount()
  }
}

const handleClose = () => {
  showModal.value = false
  isPinned.value = false
  loadNoteCount()
}

watch(isPinned, (val) => {
  if (val) {
    // 延迟添加，避免当前点击触发
    setTimeout(() => {
      document.addEventListener('click', handleClickOutside)
    }, 0)
  } else {
    document.removeEventListener('click', handleClickOutside)
  }
})

onMounted(() => loadNoteCount())

onBeforeUnmount(() => {
  clearHideTimeout()
  document.removeEventListener('click', handleClickOutside)
})

defineExpose({ refresh: loadNoteCount })
</script>

<template>
  <Teleport to="body">
    <!-- 侧边标签 -->
    <div
      class="data-tab"
      :class="{ active: showModal }"
      @click="handleTabClick"
      @mouseenter="handleTabEnter"
      @mouseleave="handleTabLeave"
      title="数据便签"
    >
      <span class="tab-label">data</span>
      <span v-if="noteCount > 0" class="badge">{{ noteCount > 99 ? '99+' : noteCount }}</span>
    </div>

    <!-- 弹窗 -->
    <Transition name="popup">
      <div
        v-if="showModal"
        class="popup-container"
        @mouseenter="handleModalEnter"
        @mouseleave="handleModalLeave"
        @click="handleModalClick"
      >
        <DataNotesModal @close="handleClose" />
      </div>
    </Transition>
  </Teleport>
</template>

<script lang="ts">
import DataNotesModal from './DataNotesModal.vue'
export default {
  components: { DataNotesModal }
}
</script>

<style scoped>
.data-tab {
  position: fixed;
  right: 0;
  top: calc(50% + 40px);
  transform: translateY(-50%);
  z-index: 9998;
  width: 38px;
  height: 56px;
  background: linear-gradient(135deg, #fffef5, #fff9e8);
  border: 1px solid #e8e0c8;
  border-right: none;
  border-radius: 6px 0 0 6px;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.8;
  writing-mode: vertical-rl;
}

.data-tab:hover,
.data-tab.active {
  opacity: 1;
  width: 42px;
  background: #fff9e6;
  border-color: #d4c99e;
}

.tab-label {
  font-size: 14px;
  font-weight: 600;
  color: #5a4a2a;
  letter-spacing: 1px;
}

.badge {
  position: absolute;
  top: -8px;
  left: -10px;
  background: #e6a700;
  color: white;
  font-size: 10px;
  padding: 2px 5px;
  border-radius: 8px;
  min-width: 18px;
  text-align: center;
  font-weight: 600;
  writing-mode: horizontal-tb;
}

/* Popup - 从标签冒出来 */
.popup-container {
  position: fixed;
  right: 42px;
  top: calc(50% + 40px);
  transform: translateY(-50%);
  z-index: 9999;
  width: 530px;
  height: 430px;
  background: #fff;
  border-radius: 10px 0 10px 10px;
  box-shadow: -4px 4px 20px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  border: 1px solid #e8e0c8;
}

/* 连接标签的小三角 */
.popup-container::before {
  content: '';
  position: absolute;
  right: -8px;
  top: 50%;
  transform: translateY(-50%);
  border: 8px solid transparent;
  border-left-color: #fff;
  border-right: none;
}

.popup-container::after {
  content: '';
  position: absolute;
  right: -9px;
  top: 50%;
  transform: translateY(-50%);
  border: 8px solid transparent;
  border-left-color: #e8e0c8;
  border-right: none;
  z-index: -1;
}

/* 动画 - 从右边滑出 */
.popup-enter-active,
.popup-leave-active {
  transition: all 0.2s ease;
}

.popup-enter-from,
.popup-leave-to {
  opacity: 0;
  transform: translateY(-50%) translateX(20px);
}
</style>
