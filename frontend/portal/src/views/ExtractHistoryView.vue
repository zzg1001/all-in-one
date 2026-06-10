<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { extractHistoryApi, type ExtractRecord } from '@/api'
import EnterpriseInfoForm from '@/components/extract/EnterpriseInfoForm.vue'
import { base64ToBlob, triggerDownload, WORD_MIME } from '@/utils/download'

const router = useRouter()

const records = ref<ExtractRecord[]>([])
const loading = ref(false)
const selectedIds = ref<string[]>([])
const searchQuery = ref('')

// 编辑弹窗
const editing = ref<ExtractRecord | null>(null)
const editFormRef = ref<InstanceType<typeof EnterpriseInfoForm> | null>(null)
const savingEdit = ref(false)

// Toast
const toastVisible = ref(false)
const toastMessage = ref('')
const toastType = ref<'success' | 'error'>('success')
let toastTimer: ReturnType<typeof setTimeout> | null = null
function showToast(message: string, type: 'success' | 'error' = 'success') {
  toastMessage.value = message
  toastType.value = type
  toastVisible.value = true
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 1600)
}

// 搜索过滤（企业名称 / 信用代码）
const filteredRecords = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return records.value
  return records.value.filter((r) =>
    (r.company_name || '').toLowerCase().includes(q) ||
    (r.credit_code || '').toLowerCase().includes(q)
  )
})

const allSelected = computed(() =>
  filteredRecords.value.length > 0 &&
  filteredRecords.value.every((r) => selectedIds.value.includes(r.id))
)

function toggleAll() {
  if (allSelected.value) {
    const ids = new Set(filteredRecords.value.map((r) => r.id))
    selectedIds.value = selectedIds.value.filter((id) => !ids.has(id))
  } else {
    const set = new Set(selectedIds.value)
    filteredRecords.value.forEach((r) => set.add(r.id))
    selectedIds.value = [...set]
  }
}

async function load() {
  loading.value = true
  try {
    records.value = (await extractHistoryApi.list()) || []
    selectedIds.value = []
  } catch (e: any) {
    showToast(e?.message || '加载失败', 'error')
  } finally {
    loading.value = false
  }
}

function formatTime(s?: string): string {
  if (!s) return '-'
  const d = new Date(s)
  if (isNaN(d.getTime())) return s
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

function initials(name?: string): string {
  const n = (name || '').trim()
  return n ? n.slice(0, 1) : '企'
}

// ===== 删除 =====
async function deleteOne(rec: ExtractRecord) {
  if (!confirm(`确认删除「${rec.company_name || '该记录'}」？`)) return
  try {
    await extractHistoryApi.delete(rec.id)
    records.value = records.value.filter((r) => r.id !== rec.id)
    selectedIds.value = selectedIds.value.filter((id) => id !== rec.id)
    showToast('已删除')
  } catch (e: any) {
    showToast(e?.message || '删除失败', 'error')
  }
}

async function batchDelete() {
  if (selectedIds.value.length === 0) return
  if (!confirm(`确认删除选中的 ${selectedIds.value.length} 条记录？`)) return
  try {
    const ids = [...selectedIds.value]
    await extractHistoryApi.batchDelete(ids)
    records.value = records.value.filter((r) => !ids.includes(r.id))
    selectedIds.value = []
    showToast('已批量删除')
  } catch (e: any) {
    showToast(e?.message || '批量删除失败', 'error')
  }
}

// ===== 编辑 =====
async function openEdit(rec: ExtractRecord) {
  try {
    const full = await extractHistoryApi.get(rec.id)
    editing.value = full
  } catch (e: any) {
    showToast(e?.message || '加载详情失败', 'error')
  }
}

function closeEdit() {
  editing.value = null
}

async function saveEdit() {
  if (!editing.value || savingEdit.value) return
  savingEdit.value = true
  try {
    const data = editFormRef.value?.buildEditedData() || editing.value.data || {}
    const updated = await extractHistoryApi.update(editing.value.id, {
      company_name: (data as any)['企业名称'] || '',
      credit_code: (data as any)['统一社会信用代码'] || (data as any)['统一社会信用码'] || '',
      data,
    })
    const idx = records.value.findIndex((r) => r.id === updated.id)
    if (idx >= 0) records.value[idx] = { ...records.value[idx], ...updated }
    showToast('已保存')
    editing.value = null
  } catch (e: any) {
    showToast(e?.message || '保存失败', 'error')
  } finally {
    savingEdit.value = false
  }
}

// ===== 下载 =====
const downloadingId = ref<string | null>(null)
async function downloadWord(rec: ExtractRecord) {
  if (downloadingId.value) return
  downloadingId.value = rec.id
  try {
    const res = await extractHistoryApi.word(rec.id)
    if (!res?.success || !res.word_file_base64) throw new Error('生成失败')
    const blob = base64ToBlob(res.word_file_base64, WORD_MIME)
    triggerDownload(blob, (rec.company_name || '企业') + '_企业档案.docx')
  } catch (e: any) {
    showToast(e?.message || 'Word 生成失败', 'error')
  } finally {
    downloadingId.value = null
  }
}

async function downloadJSON(rec: ExtractRecord) {
  try {
    const full = rec.data ? rec : await extractHistoryApi.get(rec.id)
    const blob = new Blob([JSON.stringify(full.data || {}, null, 2)], { type: 'application/json' })
    triggerDownload(blob, (rec.company_name || '企业') + '_data.json')
  } catch (e: any) {
    showToast(e?.message || '下载失败', 'error')
  }
}

onMounted(load)
</script>

<template>
  <div class="history-page">
    <div class="history-container">
      <!-- 顶部横幅 -->
      <div class="page-banner">
        <button class="btn-back" @click="router.push('/')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M15 18l-6-6 6-6" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          返回
        </button>
        <div class="banner-title">
          <div>
            <h1>历史记录</h1>
            <p>已保存 <b>{{ records.length }}</b> 条<span v-if="searchQuery.trim()">，匹配 <b>{{ filteredRecords.length }}</b> 条</span></p>
          </div>
        </div>
      </div>

      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="search-box">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="7"/>
            <path d="M21 21l-4.3-4.3" stroke-linecap="round"/>
          </svg>
          <input v-model="searchQuery" type="text" placeholder="搜索企业名称 / 统一社会信用代码" />
          <button v-if="searchQuery" class="clear" @click="searchQuery = ''" title="清除">✕</button>
        </div>
        <div class="toolbar-actions">
          <span v-if="selectedIds.length" class="sel-count">已选 {{ selectedIds.length }}</span>
          <button
            class="btn btn-danger"
            :disabled="selectedIds.length === 0"
            @click="batchDelete"
          >批量删除</button>
          <button class="btn btn-light" @click="load" :disabled="loading">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12a9 9 0 11-3-6.7L21 8" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M21 3v5h-5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            刷新
          </button>
        </div>
      </div>

      <!-- 列表 -->
      <div class="card">
        <div v-if="loading" class="state">
          <div class="spinner"></div>
          <span>加载中...</span>
        </div>
        <div v-else-if="records.length === 0" class="state">
          <div class="state-icon">📭</div>
          <span>还没有保存的记录</span>
          <button class="btn btn-primary" @click="router.push('/')">去首页解析</button>
        </div>
        <div v-else-if="filteredRecords.length === 0" class="state">
          <div class="state-icon">🔍</div>
          <span>没有匹配「{{ searchQuery }}」的记录</span>
        </div>

        <table v-else class="history-table">
          <thead>
            <tr>
              <th class="col-check">
                <label class="checkbox">
                  <input type="checkbox" :checked="allSelected" @change="toggleAll" />
                  <span></span>
                </label>
              </th>
              <th>企业名称</th>
              <th class="col-code">统一社会信用代码</th>
              <th class="col-time">保存时间</th>
              <th class="col-actions">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="rec in filteredRecords" :key="rec.id" :class="{ checked: selectedIds.includes(rec.id) }">
              <td class="col-check">
                <label class="checkbox">
                  <input type="checkbox" :value="rec.id" v-model="selectedIds" />
                  <span></span>
                </label>
              </td>
              <td>
                <div class="company-cell">
                  <span class="avatar">{{ initials(rec.company_name) }}</span>
                  <span class="company-name">{{ rec.company_name || '（未命名）' }}</span>
                </div>
              </td>
              <td class="col-code mono">{{ rec.credit_code || '-' }}</td>
              <td class="col-time">{{ formatTime(rec.created_at) }}</td>
              <td class="col-actions">
                <button class="pill" @click="openEdit(rec)">编辑</button>
                <button class="pill" :disabled="downloadingId === rec.id" @click="downloadWord(rec)">
                  {{ downloadingId === rec.id ? '生成中' : 'Word' }}
                </button>
                <button class="pill" @click="downloadJSON(rec)">JSON</button>
                <button class="pill danger" @click="deleteOne(rec)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <Transition name="modal">
      <div v-if="editing" class="modal-mask" @click.self="closeEdit">
        <div class="modal-panel">
          <div class="modal-head">
            <span>编辑：{{ editing.company_name || '企业信息' }}</span>
            <button class="modal-close" @click="closeEdit">✕</button>
          </div>
          <div class="modal-body">
            <EnterpriseInfoForm ref="editFormRef" :source="editing.data" />
          </div>
          <div class="modal-foot">
            <button class="btn btn-light" @click="closeEdit">取消</button>
            <button class="btn btn-primary" :disabled="savingEdit" @click="saveEdit">
              {{ savingEdit ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Toast -->
    <Transition name="toast">
      <div v-if="toastVisible" class="toast" :class="{ error: toastType === 'error' }">
        {{ toastMessage }}
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.history-page {
  min-height: 100vh;
  background:
    radial-gradient(1200px 400px at 100% -10%, rgba(139, 92, 246, 0.10), transparent 60%),
    radial-gradient(1000px 380px at -10% 0%, rgba(99, 102, 241, 0.10), transparent 55%),
    #f5f6fb;
  padding: 28px 16px 72px;
  font-family: 'Plus Jakarta Sans', 'Noto Sans SC', -apple-system, sans-serif;
  color: #1f2937;
}
.history-container { max-width: 1100px; margin: 0 auto; }

/* 横幅 */
.page-banner { margin-bottom: 18px; }
.btn-back {
  display: inline-flex; align-items: center; gap: 4px;
  border: 1px solid #e5e7eb; background: rgba(255, 255, 255, 0.8);
  border-radius: 9px; padding: 7px 12px; cursor: pointer;
  font-size: 13px; color: #4b5563; margin-bottom: 16px;
  transition: background 0.15s ease;
}
.btn-back:hover { background: #fff; }
.banner-title { display: flex; align-items: center; gap: 14px; }
.banner-title h1 { font-size: 22px; font-weight: 700; margin: 0; }
.banner-title p { margin: 3px 0 0; font-size: 13px; color: #6b7280; }
.banner-title b { color: #6366f1; }

/* 工具栏 */
.toolbar {
  display: flex; align-items: center; justify-content: space-between;
  gap: 14px; margin-bottom: 16px; flex-wrap: wrap;
}
.search-box {
  display: flex; align-items: center; gap: 8px;
  background: #fff; border: 1px solid #e7e9f0; border-radius: 11px;
  padding: 9px 13px; flex: 1; min-width: 260px; max-width: 460px;
  color: #9ca3af; transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.search-box:focus-within {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
}
.search-box input {
  border: none; outline: none; flex: 1; font-size: 14px;
  color: #1f2937; background: transparent;
}
.search-box .clear {
  border: none; background: #eef0f5; color: #6b7280; cursor: pointer;
  width: 18px; height: 18px; border-radius: 50%; font-size: 11px; line-height: 1;
}
.search-box .clear:hover { background: #e2e5ee; }
.toolbar-actions { display: flex; align-items: center; gap: 10px; }
.sel-count { font-size: 13px; color: #6366f1; font-weight: 600; }

.btn {
  display: inline-flex; align-items: center; gap: 5px;
  border: none; border-radius: 9px; padding: 9px 15px;
  font-size: 14px; cursor: pointer;
  transition: filter 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}
.btn:disabled { opacity: 0.45; cursor: not-allowed; }
.btn-primary {
  background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #fff;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.28);
}
.btn-primary:hover:not(:disabled) { filter: brightness(1.05); }
.btn-light { background: #fff; border: 1px solid #e5e7eb; color: #4b5563; }
.btn-light:hover:not(:disabled) { background: #f3f4f6; }
.btn-danger { background: #fff; border: 1px solid #fecaca; color: #ef4444; }
.btn-danger:hover:not(:disabled) { background: #fef2f2; }

/* 卡片表格 */
.card {
  background: #fff;
  border: 1px solid #edeff4;
  border-radius: 16px;
  box-shadow: 0 8px 28px rgba(17, 24, 39, 0.05);
  overflow: hidden;
}
.state {
  padding: 60px 20px; text-align: center; color: #9ca3af;
  display: flex; flex-direction: column; align-items: center; gap: 14px;
  font-size: 14px;
}
.state-icon { font-size: 40px; }
.spinner {
  width: 28px; height: 28px; border-radius: 50%;
  border: 3px solid #e5e7eb; border-top-color: #6366f1;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.history-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.history-table th {
  background: #fafbfd; color: #8b91a0; font-weight: 600;
  text-align: left; padding: 13px 16px; font-size: 12.5px;
  letter-spacing: 0.02em; text-transform: uppercase;
  border-bottom: 1px solid #eef0f4;
}
.history-table td {
  padding: 13px 16px; border-bottom: 1px solid #f4f5f9;
  vertical-align: middle;
}
.history-table tbody tr { transition: background 0.12s ease; }
.history-table tbody tr:hover { background: #f9faff; }
.history-table tbody tr.checked { background: #f3f4ff; }
.history-table tbody tr:last-child td { border-bottom: none; }

.col-check { width: 48px; text-align: center; }
.col-time { width: 170px; color: #6b7280; white-space: nowrap; }
.col-code { width: 210px; color: #6b7280; }
.col-actions { width: 230px; white-space: nowrap; }
.mono { font-family: ui-monospace, 'SFMono-Regular', Menlo, monospace; font-size: 13px; }

.company-cell { display: flex; align-items: center; gap: 10px; }
.avatar {
  width: 30px; height: 30px; flex-shrink: 0; border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 700; color: #fff;
  background: linear-gradient(135deg, #818cf8, #a78bfa);
}
.company-name { font-weight: 600; color: #111827; }

/* 自定义勾选框 */
.checkbox { display: inline-flex; cursor: pointer; position: relative; }
.checkbox input { position: absolute; opacity: 0; width: 0; height: 0; }
.checkbox span {
  width: 17px; height: 17px; border-radius: 5px;
  border: 1.5px solid #cbd0dc; background: #fff;
  display: inline-block; transition: all 0.15s ease;
}
.checkbox input:checked + span {
  background: linear-gradient(135deg, #6366f1, #8b5cf6); border-color: #6366f1;
}
.checkbox input:checked + span::after {
  content: ''; position: absolute; left: 6px; top: 2.5px;
  width: 4px; height: 8px; border: solid #fff; border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.pill {
  border: 1px solid #e7e9f0; background: #fff; color: #4b5563;
  cursor: pointer; font-size: 12.5px; padding: 5px 11px;
  border-radius: 7px; margin-right: 6px;
  transition: all 0.13s ease;
}
.pill:hover { border-color: #6366f1; color: #6366f1; background: #f5f6ff; }
.pill.danger:hover { border-color: #ef4444; color: #ef4444; background: #fef2f2; }
.pill:disabled { opacity: 0.5; cursor: not-allowed; }

/* 编辑弹窗 */
.modal-mask {
  position: fixed; inset: 0; background: rgba(15, 23, 42, 0.5);
  backdrop-filter: blur(2px);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000; padding: 24px;
}
.modal-panel {
  background: #f6f7fb; width: 100%; max-width: 780px; max-height: 90vh;
  border-radius: 16px; display: flex; flex-direction: column; overflow: hidden;
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.28);
}
.modal-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; background: #fff; border-bottom: 1px solid #eef0f4;
  font-weight: 700; font-size: 15px;
}
.modal-close {
  border: none; background: #f1f3f8; cursor: pointer; color: #9ca3af;
  width: 28px; height: 28px; border-radius: 8px; font-size: 14px;
}
.modal-close:hover { background: #e7e9f0; color: #374151; }
.modal-body { padding: 18px 20px; overflow-y: auto; }
.modal-foot {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 14px 20px; background: #fff; border-top: 1px solid #eef0f4;
}
.modal-enter-active, .modal-leave-active { transition: opacity 0.2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }

/* Toast */
.toast {
  position: fixed; left: 50%; bottom: 40px; transform: translateX(-50%);
  background: #1f2937; color: #fff; padding: 11px 22px; border-radius: 999px;
  font-size: 14px; z-index: 1100; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.22);
}
.toast.error { background: #ef4444; }
.toast-enter-active, .toast-leave-active { transition: opacity 0.22s ease, transform 0.22s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, 10px); }

@media (max-width: 720px) {
  .col-code { display: none; }
  .toolbar { flex-direction: column; align-items: stretch; }
  .search-box { max-width: none; }
  .toolbar-actions { justify-content: flex-end; }
}
</style>
