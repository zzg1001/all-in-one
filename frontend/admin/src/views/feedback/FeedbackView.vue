<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { feedbackApi, type Feedback } from '@/api'

// 状态
const feedbacks = ref<Feedback[]>([])
const loading = ref(false)
const total = ref(0)

// 搜索和筛选
const searchKeyword = ref('')
const filterStatus = ref<string>('')
const filterType = ref<string>('')

// 分页
const currentPage = ref(1)
const pageSize = ref(20)

// 选中项（批量操作）
const selectedIds = ref<Set<string>>(new Set())
const selectAll = ref(false)

// 状态选项
const statusOptions = [
  { value: 'pending', label: '待处理', color: '#f59e0b' },
  { value: 'processing', label: '处理中', color: '#3b82f6' },
  { value: 'resolved', label: '已解决', color: '#10b981' },
  { value: 'closed', label: '已关闭', color: '#6b7280' },
]

// 类型选项
const typeOptions = [
  { value: 'bug', label: 'Bug', icon: '🐛' },
  { value: 'suggestion', label: '建议', icon: '💡' },
  { value: 'other', label: '其他', icon: '💬' },
]

// 总页数
const totalPages = computed(() => Math.ceil(total.value / pageSize.value) || 1)

// 是否全选
const isAllSelected = computed(() => {
  return feedbacks.value.length > 0 && feedbacks.value.every(f => selectedIds.value.has(f.id))
})

// 监听筛选条件变化
watch([filterStatus, filterType, pageSize], () => {
  currentPage.value = 1
  loadFeedbacks()
})

// 搜索防抖
let searchTimer: number
watch(searchKeyword, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    loadFeedbacks()
  }, 300)
})

// 加载数据
const loadFeedbacks = async () => {
  loading.value = true
  try {
    const response = await feedbackApi.getAll({
      status: filterStatus.value || undefined,
      feedback_type: filterType.value || undefined,
      keyword: searchKeyword.value || undefined,
      page: currentPage.value,
      page_size: pageSize.value,
    })
    feedbacks.value = response.items
    total.value = response.total
    selectedIds.value.clear()
  } catch (e) {
    console.error('加载反馈失败:', e)
  } finally {
    loading.value = false
  }
}

// 切换全选
const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedIds.value.clear()
  } else {
    feedbacks.value.forEach(f => selectedIds.value.add(f.id))
  }
}

// 切换单选
const toggleSelect = (id: string) => {
  if (selectedIds.value.has(id)) {
    selectedIds.value.delete(id)
  } else {
    selectedIds.value.add(id)
  }
}

// 跳转页码
const goToPage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    loadFeedbacks()
  }
}

// 快速修改状态
const updateStatus = async (feedback: Feedback, newStatus: string) => {
  try {
    const updated = await feedbackApi.update(feedback.id, {
      status: newStatus as 'pending' | 'processing' | 'resolved' | 'closed',
    })
    feedback.status = updated.status
    feedback.updated_at = updated.updated_at
  } catch (e) {
    console.error('更新状态失败:', e)
    alert('更新失败')
  }
}

// 删除单个
const deleteFeedback = async (feedback: Feedback) => {
  if (!confirm('确定删除这条反馈？')) return
  try {
    await feedbackApi.delete(feedback.id)
    await loadFeedbacks()
  } catch (e) {
    console.error('删除失败:', e)
    alert('删除失败')
  }
}

// 批量删除
const batchDelete = async () => {
  if (selectedIds.value.size === 0) return
  if (!confirm(`确定删除选中的 ${selectedIds.value.size} 条反馈？`)) return

  try {
    const ids = Array.from(selectedIds.value)
    await Promise.all(ids.map(id => feedbackApi.delete(id)))
    await loadFeedbacks()
  } catch (e) {
    console.error('批量删除失败:', e)
    alert('部分删除失败')
    await loadFeedbacks()
  }
}

// 格式化时间
const formatDate = (dateStr: string | null) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const h = String(date.getHours()).padStart(2, '0')
  const min = String(date.getMinutes()).padStart(2, '0')
  return `${m}-${d} ${h}:${min}`
}

// 获取状态信息
const getStatusInfo = (status: string) => {
  return statusOptions.find(s => s.value === status) || { value: status, label: status, color: '#6b7280' }
}

// 获取类型信息
const getTypeInfo = (type: string) => {
  return typeOptions.find(t => t.value === type) || { value: type, label: type, icon: '📝' }
}

onMounted(() => {
  loadFeedbacks()
})
</script>

<template>
  <div class="feedback-page">
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <div class="search-box">
          <svg class="search-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
          </svg>
          <input v-model="searchKeyword" type="text" placeholder="搜索标题、描述..." />
        </div>
        <select v-model="filterType" class="filter-select">
          <option value="">全部类型</option>
          <option v-for="t in typeOptions" :key="t.value" :value="t.value">{{ t.icon }} {{ t.label }}</option>
        </select>
        <select v-model="filterStatus" class="filter-select">
          <option value="">全部状态</option>
          <option v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>
      </div>
      <div class="toolbar-right">
        <button v-if="selectedIds.size > 0" class="btn-danger" @click="batchDelete">
          删除选中 ({{ selectedIds.size }})
        </button>
        <span class="total-count">共 {{ total }} 条</span>
      </div>
    </div>

    <!-- 表格 -->
    <div class="table-wrapper">
      <table class="feedback-table">
        <thead>
          <tr>
            <th class="col-check">
              <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll" />
            </th>
            <th class="col-type">类型</th>
            <th class="col-content">内容</th>
            <th class="col-user">用户</th>
            <th class="col-agent">Agent</th>
            <th class="col-status">状态</th>
            <th class="col-time">创建时间</th>
            <th class="col-time">更新时间</th>
            <th class="col-actions">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="9" class="loading-cell">
              <span class="spinner"></span> 加载中...
            </td>
          </tr>
          <tr v-else-if="feedbacks.length === 0">
            <td colspan="9" class="empty-cell">暂无数据</td>
          </tr>
          <tr v-else v-for="item in feedbacks" :key="item.id" :class="{ selected: selectedIds.has(item.id) }">
            <td class="col-check">
              <input type="checkbox" :checked="selectedIds.has(item.id)" @change="toggleSelect(item.id)" />
            </td>
            <td class="col-type">
              <span class="type-tag" :title="getTypeInfo(item.feedback_type).label">
                {{ getTypeInfo(item.feedback_type).icon }}
              </span>
            </td>
            <td class="col-content">
              <div class="content-cell" :title="item.title + (item.description ? '\n' + item.description : '')">
                <span class="content-title">{{ item.title }}</span>
                <span v-if="item.description" class="content-desc">{{ item.description }}</span>
              </div>
            </td>
            <td class="col-user">
              <span class="user-tag" :title="item.user_id">{{ item.user_id.slice(0, 8) }}</span>
            </td>
            <td class="col-agent">
              <span v-if="item.agent_name" class="agent-tag" :title="item.agent_name">{{ item.agent_name }}</span>
              <span v-else class="no-data">-</span>
            </td>
            <td class="col-status">
              <select
                class="status-select"
                :value="item.status"
                :style="{ borderColor: getStatusInfo(item.status).color, color: getStatusInfo(item.status).color }"
                @change="updateStatus(item, ($event.target as HTMLSelectElement).value)"
              >
                <option v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
              </select>
            </td>
            <td class="col-time">{{ formatDate(item.created_at) }}</td>
            <td class="col-time">{{ formatDate(item.updated_at) }}</td>
            <td class="col-actions">
              <button class="btn-icon delete" @click="deleteFeedback(item)" title="删除">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"/>
                </svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="totalPages > 1">
      <button class="page-btn" :disabled="currentPage === 1" @click="goToPage(currentPage - 1)">上一页</button>
      <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
      <button class="page-btn" :disabled="currentPage === totalPages" @click="goToPage(currentPage + 1)">下一页</button>
    </div>
  </div>
</template>

<style scoped>
.feedback-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px;
  gap: 12px;
}

/* 工具栏 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 10px;
  width: 16px;
  height: 16px;
  color: #9ca3af;
}

.search-box input {
  padding: 8px 12px 8px 32px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  width: 200px;
}

.search-box input:focus {
  outline: none;
  border-color: #1677ff;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  background: white;
  cursor: pointer;
}

.filter-select:focus {
  outline: none;
  border-color: #1677ff;
}

.btn-danger {
  padding: 8px 16px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-danger:hover {
  background: #dc2626;
}

.total-count {
  font-size: 13px;
  color: #6b7280;
}

/* 表格 */
.table-wrapper {
  flex: 1;
  overflow: auto;
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.feedback-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  table-layout: fixed;
}

.feedback-table th,
.feedback-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #f3f4f6;
  white-space: nowrap;
}

.feedback-table th {
  background: #f9fafb;
  font-weight: 600;
  color: #374151;
  font-size: 12px;
  position: sticky;
  top: 0;
  z-index: 1;
}

.feedback-table tbody tr:hover {
  background: #f9fafb;
}

.feedback-table tbody tr.selected {
  background: #eff6ff;
}

/* 列宽 - 均匀分布 */
.col-check { width: 36px; text-align: center; }
.col-type { width: 48px; text-align: center; }
.col-content { width: 25%; min-width: 160px; }
.col-user { width: 10%; min-width: 80px; }
.col-agent { width: 12%; min-width: 90px; }
.col-status { width: 10%; min-width: 85px; }
.col-time { width: 11%; min-width: 85px; }
.col-actions { width: 48px; text-align: center; }

/* 复选框 */
.col-check input {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

/* 类型标签 */
.type-tag {
  font-size: 16px;
}

/* 内容 */
.content-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
}

.content-title {
  font-weight: 500;
  color: #1f2937;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.content-desc {
  font-size: 12px;
  color: #9ca3af;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 时间列 */
.col-time {
  font-size: 12px;
  color: #6b7280;
}

/* 用户标签 */
.user-tag {
  font-family: monospace;
  font-size: 11px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
}

/* Agent标签 */
.agent-tag {
  font-size: 12px;
  color: #1d4ed8;
  background: #eff6ff;
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.no-data {
  color: #d1d5db;
}

/* 状态下拉 */
.status-select {
  padding: 4px 8px;
  border: 1px solid;
  border-radius: 4px;
  font-size: 12px;
  background: white;
  cursor: pointer;
  font-weight: 500;
}

.status-select:focus {
  outline: none;
}

/* 操作按钮 */
.btn-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  color: #9ca3af;
  transition: all 0.15s;
}

.btn-icon:hover {
  background: #f3f4f6;
}

.btn-icon.delete:hover {
  background: #fef2f2;
  color: #ef4444;
}

.btn-icon svg {
  width: 16px;
  height: 16px;
}

/* 加载和空状态 */
.loading-cell,
.empty-cell {
  text-align: center;
  padding: 40px !important;
  color: #9ca3af;
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid #e5e7eb;
  border-top-color: #1677ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 8px;
  vertical-align: middle;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.page-btn {
  padding: 6px 14px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.page-btn:hover:not(:disabled) {
  border-color: #1677ff;
  color: #1677ff;
}

.page-btn:disabled {
  color: #d1d5db;
  cursor: not-allowed;
}

.page-info {
  font-size: 13px;
  color: #6b7280;
}
</style>
