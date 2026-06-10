<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import config from '@/config'
import { setLocale, getLocale } from '@/locales'
import { useAuthStore } from '@/stores/auth'
import { agentsApi, extractHistoryApi } from '@/api'
import EnterpriseInfoForm from '@/components/extract/EnterpriseInfoForm.vue'
import { base64ToBlob, triggerDownload, WORD_MIME } from '@/utils/download'
import '@/assets/home.css'
import './HomePage.css'

const router = useRouter()
const authStore = useAuthStore()

// 语言切换
const currentLocale = ref(getLocale())
const toggleLocale = () => {
  const newLocale = currentLocale.value === 'zh' ? 'en' : 'zh'
  setLocale(newLocale)
  currentLocale.value = newLocale
}

// 用户菜单
const showUserMenu = ref(false)

// 预设 Agent 配置（用于提供默认的 theme 和样式）
const presetAgentConfig: Record<string, { department: string | null; theme: string }> = {
  'HR部门 Agent': { department: 'HR', theme: 'blue' },
  '销售部门 Agent': { department: '销售', theme: 'purple' },
  '采购部门 Agent': { department: '采购', theme: 'cyan' },
  '行政部门 Agent': { department: '行政', theme: 'orange' },
  '财务部门 Agent': { department: '财务', theme: 'green' },
  '智能体自定义': { department: null, theme: 'magenta' },
  '商业线索 Agent': { department: null, theme: 'red' },
  '老板视角': { department: null, theme: 'indigo' },
}

// 可用的颜色主题（用于非预设 Agent）
const themeColors = ['teal', 'amber', 'rose', 'lime', 'sky', 'violet', 'emerald', 'pink']

// Agent 类型定义
interface VisibleAgent {
  name: string
  department: string | null
  theme: string
  desc: string
  status: 'active' | 'inactive'  // active=可用, inactive=展示但不可用
}

// 所有可展示的 Agent（从后端加载，包括 active 和 inactive）
const visibleAgents = ref<VisibleAgent[]>([])

// 加载中状态
const loadingAgents = ref(true)

// Toast 提示
const toastVisible = ref(false)
const toastMessage = ref('')
let toastTimer: ReturnType<typeof setTimeout> | null = null

function showToast(message: string, duration = 2500) {
  toastMessage.value = message
  toastVisible.value = true
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toastVisible.value = false
  }, duration)
}

// 处理 Agent 点击
function handleAgentClick(agent: VisibleAgent) {
  // 检查 Agent 状态
  if (agent.status === 'inactive') {
    showToast(`「${agent.name}」当前不可用，敬请期待`)
    return
  }

  const targetUrl = `/app?from=home&agent=${encodeURIComponent(agent.name)}&theme=${agent.theme}`

  // 未登录 -> 跳转登录页
  if (!authStore.isAuthenticated) {
    router.push({ name: 'login', query: { redirect: targetUrl } })
    return
  }

  // 已登录但无权限
  if (!authStore.canAccessAgent(agent.name)) {
    showToast(`您没有权限访问「${agent.name}」，请联系管理员`)
    return
  }

  // 有权限 -> 直接进入
  router.push(targetUrl)
}

// 登录
function goToLogin() {
  router.push({ name: 'login' })
}

// 登出
async function handleLogout() {
  await authStore.logout()
  showUserMenu.value = false
}

// 加载 Agent 列表（获取所有可展示的: active + inactive）
async function loadAgents() {
  loadingAgents.value = true
  try {
    const res = await agentsApi.getAll({ visible: true })
    if (res.agents) {
      let nonPresetIndex = 0
      visibleAgents.value = res.agents.map(agent => {
        // 检查是否是预设 Agent，使用预设的 theme
        const preset = presetAgentConfig[agent.name]
        if (preset) {
          return {
            name: agent.name,
            department: preset.department,
            theme: preset.theme,
            desc: agent.description || '自定义智能体',
            status: agent.status as 'active' | 'inactive'
          }
        } else {
          // 非预设 Agent，使用动态颜色
          const theme = themeColors[nonPresetIndex % themeColors.length]
          nonPresetIndex++
          return {
            name: agent.name,
            department: null,
            theme,
            desc: agent.description || '自定义智能体',
            status: agent.status as 'active' | 'inactive'
          }
        }
      })
    }
  } catch (err) {
    console.error('加载 Agent 失败:', err)
  } finally {
    loadingAgents.value = false
  }
}

// ========== 企业信息提取相关 ==========
const licenseInputRef = ref<HTMLInputElement | null>(null)
const introInputRef = ref<HTMLInputElement | null>(null)

const extractStep = ref<'form' | 'loading' | 'result'>('form')
const extractLoading = ref(false)
const extractError = ref('')
const extractProgress = ref('准备中...')
const extractProgressPercent = ref(0)

const extractForm = ref({
  companyName: '',
  creditCode: '',
  website: '',
  licenseFile: null as File | null,
  introFile: null as File | null
})

const extractResultData = ref<any>(null)
const extractWordBase64 = ref('')
const extractRawOcrText = ref('')

// 可编辑企业信息表单组件引用（基础信息/产品等编辑表单已抽成 EnterpriseInfoForm）
const infoFormRef = ref<InstanceType<typeof EnterpriseInfoForm> | null>(null)

// 取表单当前（编辑后）数据；无表单时回退原始数据
function buildEditedData(): Record<string, any> {
  return infoFormRef.value?.buildEditedData() ?? { ...(extractResultData.value || {}) }
}

// 是否可以提交
const canSubmitExtract = computed(() => {
  return extractForm.value.companyName.trim() ||
         extractForm.value.creditCode.trim() ||
         extractForm.value.licenseFile
})

// 触发文件选择
function triggerExtractFileInput(type: 'license' | 'intro') {
  if (type === 'license') {
    licenseInputRef.value?.click()
  } else {
    introInputRef.value?.click()
  }
}

// 处理文件拖放
function handleExtractFileDrop(e: DragEvent, type: 'license' | 'intro') {
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    setExtractFile(files[0], type)
  }
}

// 处理文件选择
function handleExtractFileSelect(e: Event, type: 'license' | 'intro') {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    setExtractFile(input.files[0], type)
  }
}

// 设置文件
function setExtractFile(file: File, type: 'license' | 'intro') {
  if (file.size > 20 * 1024 * 1024) {
    showToast('文件大小不能超过 20MB')
    return
  }
  if (type === 'license') {
    extractForm.value.licenseFile = file
  } else {
    extractForm.value.introFile = file
  }
}

// 重置表单
function resetExtractForm() {
  extractForm.value = {
    companyName: '',
    creditCode: '',
    website: '',
    licenseFile: null,
    introFile: null
  }
  extractStep.value = 'form'
  extractError.value = ''
  extractResultData.value = null
  extractWordBase64.value = ''
  actionsPos.value = null  // 复位浮框位置
}

// ========== 浮框拖动 ==========
const actionsRef = ref<HTMLElement | null>(null)
const actionsPos = ref<{ x: number; y: number } | null>(null)
const isDraggingActions = ref(false)
let dragOffset = { x: 0, y: 0 }

// 滚动惯性跟随：用「跟随者平滑逼近真实滚动位置」产生惯性，
// 关键：在 rAF 里【直接改 DOM 的 transform】，不走 Vue 响应式，避免整组件每帧重渲染导致卡顿/抖动。
let realScroll = 0                 // 最新真实滚动位置
let followScroll = 0               // 平滑跟随者（落后于 realScroll → 产生惯性）
let followRaf: number | null = null
let scrollContainer: HTMLElement | Window | null = null

const LAG_MAX = 50                 // 最大偏移幅度
const FOLLOW_EASE = 0.12           // 跟随者每帧逼近真实位置的比例（越小越“肉”、惯性越强）
const LAG_FACTOR = 0.6             // 偏移 = 落后距离 × 此系数（越大位移越明显）

function getScrollTop(): number {
  if (scrollContainer && scrollContainer !== window) {
    return (scrollContainer as HTMLElement).scrollTop
  }
  return window.scrollY
}

// 直接操作 DOM，避免响应式重渲染
function applyActionsTransform(y: number) {
  const el = actionsRef.value
  if (!el) return
  el.style.transform = y === 0 ? '' : `translate3d(0, ${y}px, 0)`
}

function followStep() {
  // 跟随者指数缓动逼近真实滚动位置（平滑、无噪声）
  followScroll += (realScroll - followScroll) * FOLLOW_EASE
  const gap = realScroll - followScroll
  let offset = Math.max(-LAG_MAX, Math.min(LAG_MAX, gap * LAG_FACTOR))
  if (!actionsPos.value) applyActionsTransform(offset)
  // 跟随者追上 → 收敛归位
  if (Math.abs(gap) < 0.3) {
    followScroll = realScroll
    if (!actionsPos.value) applyActionsTransform(0)
    followRaf = null
    return
  }
  followRaf = requestAnimationFrame(followStep)
}

function onPageScroll() {
  // 仅在结果页、且未拖动时生效
  if (extractStep.value !== 'result' || actionsPos.value) return
  realScroll = getScrollTop()
  if (followRaf == null) followRaf = requestAnimationFrame(followStep)
}

// 拖动后切换为 fixed 定位（滚动惯性的 transform 由 rAF 直接管理，不在此处）
const actionsStyle = computed(() => {
  if (actionsPos.value) {
    return {
      position: 'fixed',
      left: actionsPos.value.x + 'px',
      top: actionsPos.value.y + 'px',
      right: 'auto',
      bottom: 'auto',
      margin: '0',
    } as Record<string, string>
  }
  return {}
})

function onDragMove(e: PointerEvent) {
  if (!actionsPos.value) return
  const el = actionsRef.value
  const w = el?.offsetWidth || 116
  const h = el?.offsetHeight || 140
  let x = e.clientX - dragOffset.x
  let y = e.clientY - dragOffset.y
  // 限制在视口内
  x = Math.min(Math.max(8, x), window.innerWidth - w - 8)
  y = Math.min(Math.max(8, y), window.innerHeight - h - 8)
  actionsPos.value = { x, y }
}

function onDragEnd() {
  isDraggingActions.value = false
  window.removeEventListener('pointermove', onDragMove)
  window.removeEventListener('pointerup', onDragEnd)
}

function startDragActions(e: PointerEvent) {
  const el = actionsRef.value
  if (!el) return
  // 清掉滚动惯性的 transform，避免拖动定位被偏移
  if (followRaf != null) { cancelAnimationFrame(followRaf); followRaf = null }
  el.style.transform = ''
  followScroll = realScroll = getScrollTop()
  const rect = el.getBoundingClientRect()
  actionsPos.value = { x: rect.left, y: rect.top }
  dragOffset = { x: e.clientX - rect.left, y: e.clientY - rect.top }
  isDraggingActions.value = true
  window.addEventListener('pointermove', onDragMove)
  window.addEventListener('pointerup', onDragEnd)
  e.preventDefault()
}

// 提交提取
async function submitExtract() {
  if (!canSubmitExtract.value || extractLoading.value) return

  extractLoading.value = true
  extractError.value = ''
  extractStep.value = 'loading'
  extractProgress.value = '正在上传文件...'
  extractProgressPercent.value = 10

  try {
    const formData = new FormData()
    if (extractForm.value.companyName) formData.append('company_name', extractForm.value.companyName)
    if (extractForm.value.creditCode) formData.append('credit_code', extractForm.value.creditCode)
    if (extractForm.value.website) formData.append('website', extractForm.value.website)
    if (extractForm.value.licenseFile) formData.append('license_file', extractForm.value.licenseFile)
    if (extractForm.value.introFile) formData.append('intro_file', extractForm.value.introFile)

    extractProgress.value = '正在识别文件内容...'
    extractProgressPercent.value = 30

    const response = await fetch('/api/extract/company', {
      method: 'POST',
      body: formData
    })

    extractProgress.value = '正在提取企业信息...'
    extractProgressPercent.value = 60

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.detail || '提取失败，请稍后重试')
    }

    extractProgress.value = '正在生成企业档案...'
    extractProgressPercent.value = 90

    const data = await response.json()

    if (data.success) {
      extractResultData.value = data.data
      extractWordBase64.value = data.word_file_base64 || ''
      extractRawOcrText.value = data.raw_ocr_text || ''
      extractStep.value = 'result'
      // 表单初始化与文本域撑高由 EnterpriseInfoForm 组件内部处理
    } else {
      throw new Error(data.error || '提取失败')
    }
  } catch (err: any) {
    extractError.value = err.message || '提取失败，请稍后重试'
    extractStep.value = 'form'
  } finally {
    extractLoading.value = false
  }
}

// 下载 Word 文档（用编辑后的内容重新生成）
const downloadingWord = ref(false)
async function downloadWord() {
  if (downloadingWord.value) return
  downloadingWord.value = true
  try {
    const edited = buildEditedData()
    const response = await fetch('/api/extract/word', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(edited)
    })
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.detail || 'Word 生成失败')
    }
    const data = await response.json()
    if (!data.success || !data.word_file_base64) throw new Error('Word 生成失败')

    const blob = base64ToBlob(data.word_file_base64, WORD_MIME)
    triggerDownload(blob, (edited['企业名称'] || '企业') + '_企业档案.docx')
  } catch (err: any) {
    showToast(err.message || 'Word 生成失败，请稍后重试')
  } finally {
    downloadingWord.value = false
  }
}

// 下载 JSON（编辑后的内容）
function downloadJSON() {
  if (!extractResultData.value) return
  const edited = buildEditedData()
  const jsonStr = JSON.stringify(edited, null, 2)
  const blob = new Blob([jsonStr], { type: 'application/json' })
  triggerDownload(blob, (edited['企业名称'] || '企业') + '_data.json')
}

// 保存当前（编辑后）企业信息到历史
const savingRecord = ref(false)
async function saveExtractRecord() {
  if (savingRecord.value || !extractResultData.value) return
  savingRecord.value = true
  try {
    const edited = buildEditedData()
    await extractHistoryApi.create({
      company_name: edited['企业名称'] || '',
      credit_code: edited['统一社会信用代码'] || edited['统一社会信用码'] || '',
      data: edited,
    })
    showToast('保存成功')
  } catch (err: any) {
    showToast(err?.message || '保存失败，请稍后重试')
  } finally {
    savingRecord.value = false
  }
}

// 跳转到历史记录页面
function goToHistory() {
  router.push('/extract-history')
}

// 产品下拉菜单
const showProductMenu = ref(false)
const toggleProductMenu = () => {
  showProductMenu.value = !showProductMenu.value
}

// 滚动到指定区域
function scrollToSection(sectionId: string) {
  showProductMenu.value = false
  const el = document.getElementById(sectionId)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth' })
  }
}

// 检查认证状态
onMounted(async () => {
  await authStore.checkAuth()
  // 加载 Agent 列表
  loadAgents()

  // 点击外部关闭产品菜单
  document.addEventListener('click', (e: MouseEvent) => {
    const target = e.target as HTMLElement
    if (!target.closest('.nav-dropdown')) {
      showProductMenu.value = false
    }
  })

  // 监听滚动，驱动浮框的滚动惯性跟随（.home-page 是实际滚动容器）
  await nextTick()
  scrollContainer = document.querySelector('.home-page') || window
  realScroll = followScroll = getScrollTop()
  scrollContainer.addEventListener('scroll', onPageScroll, { passive: true })
})

onUnmounted(() => {
  if (scrollContainer) scrollContainer.removeEventListener('scroll', onPageScroll)
  if (followRaf != null) cancelAnimationFrame(followRaf)
})
</script>

<template>
  <div class="home-page" :class="{ 'snap-off': extractStep === 'result' }">
    <!-- Header -->
    <header class="header">
      <div class="container">
        <div class="header-inner">
          <a href="/" class="logo">
            <div class="logo-icon">IK</div>
            <div class="logo-text">{{ $t('logo.text') }}<span>{{ $t('logo.slogan') }}</span></div>
          </a>

          <nav class="nav">
            <ul class="nav-links">
              <li class="nav-dropdown">
                <a href="#" class="dropdown-trigger" :class="{ active: showProductMenu }" @click.prevent="toggleProductMenu">
                  {{ $t('header.products') }}
                  <svg class="dropdown-arrow" :class="{ rotated: showProductMenu }" width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </a>
                <Transition name="dropdown">
                  <div v-if="showProductMenu" class="dropdown-menu">
                    <a href="#ai-agents" @click.prevent="scrollToSection('ai-agents')">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
                      </svg>
                      AI 智能体
                    </a>
                    <a href="#smart-ocr" @click.prevent="scrollToSection('smart-ocr')">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
                      </svg>
                      企业信息提取
                    </a>
                  </div>
                </Transition>
              </li>
            </ul>
          </nav>

          <div class="header-actions">
            <button class="btn btn-text btn-lang" @click="toggleLocale">{{ currentLocale === 'zh' ? 'EN' : '中' }}</button>

            <!-- 未登录 -->
            <template v-if="!authStore.isAuthenticated">
              <button class="btn btn-text" @click="goToLogin">{{ $t('header.login') }}</button>
              <button class="btn btn-primary" @click="goToLogin">{{ $t('header.freeTrial') }}</button>
            </template>

            <!-- 已登录 -->
            <template v-else>
              <div class="user-menu-wrapper">
                <button class="btn btn-user" @click="showUserMenu = !showUserMenu">
                  <span class="user-avatar">{{ authStore.displayName?.charAt(0) || 'U' }}</span>
                  <span class="user-name">{{ authStore.displayName }}</span>
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
                <div v-if="showUserMenu" class="user-menu">
                  <div class="user-info">
                    <div class="info-name">{{ authStore.displayName }}</div>
                    <div class="info-role">
                      <span v-if="authStore.isAdmin">管理员</span>
                      <span v-else-if="authStore.isBoss">老板</span>
                      <span v-else>{{ authStore.userDepartment }}部门</span>
                    </div>
                  </div>
                  <div class="menu-divider"></div>
                  <a v-if="authStore.canAccessAdmin" href="/admin" class="menu-item">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path d="M8 10a2 2 0 100-4 2 2 0 000 4z" stroke="currentColor" stroke-width="1.2"/>
                      <path d="M13.54 10.28a1 1 0 00.2 1.1l.04.04a1.21 1.21 0 11-1.71 1.71l-.04-.04a1.01 1.01 0 00-1.1-.2 1 1 0 00-.61.92v.11a1.21 1.21 0 01-2.42 0v-.06a1 1 0 00-.66-.91 1 1 0 00-1.1.2l-.04.04a1.21 1.21 0 11-1.71-1.71l.04-.04a1.01 1.01 0 00.2-1.1 1 1 0 00-.92-.61h-.11a1.21 1.21 0 010-2.42h.06a1 1 0 00.91-.66 1 1 0 00-.2-1.1l-.04-.04a1.21 1.21 0 111.71-1.71l.04.04a1 1 0 001.1.2h.05a1 1 0 00.61-.92v-.11a1.21 1.21 0 012.42 0v.06a1.01 1.01 0 00.61.91 1 1 0 001.1-.2l.04-.04a1.21 1.21 0 111.71 1.71l-.04.04a1 1 0 00-.2 1.1v.05a1 1 0 00.92.61h.11a1.21 1.21 0 010 2.42h-.06a1.01 1.01 0 00-.91.61z" stroke="currentColor" stroke-width="1.2"/>
                    </svg>
                    管理后台
                  </a>
                  <button class="menu-item" @click="handleLogout">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path d="M6 14H3.33a1.33 1.33 0 01-1.33-1.33V3.33A1.33 1.33 0 013.33 2H6M10.67 11.33L14 8l-3.33-3.33M14 8H6" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    退出登录
                  </button>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </header>

    <!-- AI 智能体 Section -->
    <section id="ai-agents" class="products-section">
      <div class="container">
        <div class="section-header">
          <h2 class="section-title">全栈 AI 产品矩阵</h2>
          <p class="section-desc">基于大模型和行业知识，构建面向OA场景的智能产品生态</p>
        </div>
        <div class="products-grid">
          <!-- 加载中状态 -->
          <div v-if="loadingAgents" class="loading-placeholder">
            <div class="loading-spinner"></div>
            <span>加载中...</span>
          </div>

          <!-- 空状态 -->
          <div v-else-if="visibleAgents.length === 0" class="empty-state">
            <span>暂无可用的 Agent</span>
          </div>

          <!-- 部门 Agent 列表 -->
          <template v-else>
            <div
              v-for="agent in visibleAgents"
              :key="agent.name"
              class="product-card"
              :class="[`card-${agent.theme}`, { 'card-inactive': agent.status === 'inactive' }]"
              @click="handleAgentClick(agent)"
            >
              <!-- 不可用标签 -->
              <span v-if="agent.status === 'inactive'" class="card-badge-inactive">暂不可用</span>
              <div class="card-icon">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
                </svg>
              </div>
              <h3>{{ agent.name }}</h3>
              <p>{{ agent.desc }}</p>
              <span class="card-link">{{ agent.status === 'inactive' ? '敬请期待' : '了解更多 →' }}</span>
            </div>
          </template>
        </div>
      </div>
    </section>

    <!-- 企业信息提取 Section -->
    <section id="smart-ocr" class="smart-ocr-section">
      <div class="container">
        <div class="section-header">
          <h2 class="section-title">企业信息提取</h2>
          <p class="section-desc">智能识别营业执照与企业介绍，自动生成结构化企业档案</p>
        </div>

        <!-- 表单输入区域 -->
        <div class="extract-content" v-if="extractStep === 'form'">
          <div class="extract-form">
            <p class="form-hint">请至少填写企业名称、统一社会信用代码或上传营业执照其中之一</p>

            <div class="form-row">
              <div class="form-group">
                <label>企业名称</label>
                <input type="text" v-model="extractForm.companyName" placeholder="请输入企业全称" />
              </div>
              <div class="form-group">
                <label>统一社会信用代码</label>
                <input type="text" v-model="extractForm.creditCode" placeholder="18位统一社会信用代码" />
              </div>
            </div>

            <div class="form-group">
              <label>官网URL（可选）</label>
              <input type="text" v-model="extractForm.website" placeholder="https://example.com" />
            </div>

            <div class="upload-row">
              <!-- 营业执照上传 -->
              <div
                class="upload-box"
                :class="{ 'has-file': extractForm.licenseFile }"
                @dragover.prevent
                @drop.prevent="(e) => handleExtractFileDrop(e, 'license')"
                @click="() => triggerExtractFileInput('license')"
              >
                <input ref="licenseInputRef" type="file" accept=".jpg,.jpeg,.png,.pdf,.bmp,.tiff" @change="(e) => handleExtractFileSelect(e, 'license')" style="display:none" />
                <div class="box-icon">📄</div>
                <div class="box-title">营业执照</div>
                <div class="box-hint">拖拽或点击上传</div>
                <div class="box-formats">PDF / JPG / PNG</div>
                <div v-if="extractForm.licenseFile" class="box-filename">✓ {{ extractForm.licenseFile.name }}</div>
              </div>

              <!-- 企业介绍上传 -->
              <div
                class="upload-box"
                :class="{ 'has-file': extractForm.introFile }"
                @dragover.prevent
                @drop.prevent="(e) => handleExtractFileDrop(e, 'intro')"
                @click="() => triggerExtractFileInput('intro')"
              >
                <input ref="introInputRef" type="file" accept=".pptx,.ppt,.docx,.doc,.pdf" @change="(e) => handleExtractFileSelect(e, 'intro')" style="display:none" />
                <div class="box-icon">📊</div>
                <div class="box-title">企业介绍（可选）</div>
                <div class="box-hint">拖拽或点击上传</div>
                <div class="box-formats">PPT / Word / PDF</div>
                <div v-if="extractForm.introFile" class="box-filename">✓ {{ extractForm.introFile.name }}</div>
              </div>
            </div>

            <div class="form-actions">
              <button class="btn btn-primary" :disabled="!canSubmitExtract || extractLoading" @click="submitExtract">
                <svg v-if="extractLoading" class="loading-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 2v4m0 12v4m-7-10H2m20 0h-3" stroke-linecap="round"/>
                </svg>
                {{ extractLoading ? '提取中...' : '开始提取' }}
              </button>
              <button class="btn btn-secondary" @click="resetExtractForm">重置</button>
              <button class="btn btn-history" @click="goToHistory">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 3v5h5" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M3.05 13A9 9 0 106 5.3L3 8" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M12 7v5l3 2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                历史记录
              </button>
            </div>

            <div v-if="extractError" class="form-error">{{ extractError }}</div>
          </div>
        </div>

        <!-- 加载状态 -->
        <div class="extract-loading" v-else-if="extractStep === 'loading'">
          <div class="loading-spinner-large"></div>
          <p class="loading-text">{{ extractProgress }}</p>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: extractProgressPercent + '%' }"></div>
          </div>
        </div>

        <!-- 结果展示 -->
        <div class="extract-result" v-else-if="extractStep === 'result'">
          <div class="result-main">
            <EnterpriseInfoForm
              ref="infoFormRef"
              :source="extractResultData"
              :raw-ocr-text="extractRawOcrText"
            />
          </div>

          <!-- 操作按钮（浮框，可拖动） -->
          <div
            class="result-actions"
            :class="{ dragging: isDraggingActions }"
            ref="actionsRef"
            :style="actionsStyle"
          >
            <div class="drag-handle" @pointerdown="startDragActions" title="拖动">
              <span class="drag-dots">⠿</span> 拖动
            </div>
            <button class="btn btn-primary" :disabled="savingRecord" @click="saveExtractRecord">
              {{ savingRecord ? '保存中...' : '保存' }}
            </button>
            <button class="btn btn-secondary" @click="goToHistory">历史</button>
            <button class="btn btn-secondary" @click="downloadWord">下载 Word</button>
            <button class="btn btn-secondary" @click="downloadJSON">下载 JSON</button>
            <button class="btn btn-text" @click="resetExtractForm">返回</button>
          </div>
        </div>
      </div>
    </section>

    <!-- Toast 提示 -->
    <Transition name="toast">
      <div v-if="toastVisible" class="toast-container">
        <div class="toast-content">
          <svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 8v4M12 16h.01"/>
          </svg>
          <span>{{ toastMessage }}</span>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  overflow: hidden;
}

.home-page {
  --primary: #1677FF;
  --primary-dark: #0958d9;
  --primary-light: #e6f4ff;
  --secondary: #0f1419;
  --accent: #FF6A00;
  --bg: #ffffff;
  --bg-dark: #030712;
  --text: #1f2937;
  --text-secondary: #6b7280;
  --text-light: #9ca3af;
  --border: #e5e7eb;
  --shadow: 0 1px 3px rgba(0,0,0,0.08);
  --shadow-lg: 0 10px 40px rgba(0,0,0,0.1);
  --radius: 8px;
  --radius-lg: 16px;

  font-family: 'Plus Jakarta Sans', 'Noto Sans SC', -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  font-size: 15px;
  height: 100vh;
  overflow-y: auto;
  scroll-snap-type: y mandatory;
  scroll-behavior: smooth;
  scroll-padding-top: 72px;
}

/* 查看解析结果时关闭整屏吸附：结果内容远高于一屏，强制吸附会与下拉较劲导致抖动 */
.home-page.snap-off {
  scroll-snap-type: none;
}

.home-page a {
  text-decoration: none;
  color: inherit;
}

.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 32px;
}

/* Header */
.header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 72px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #1677ff, #4096ff);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 800;
  font-size: 15px;
  letter-spacing: -0.5px;
}

.logo-text {
  font-weight: 700;
  font-size: 19px;
  color: var(--secondary);
}

.logo-text span {
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 13px;
  margin-left: 10px;
  padding-left: 10px;
  border-left: 1px solid var(--border);
}

.nav {
  display: flex;
  align-items: center;
  gap: 32px;
}

.nav-links {
  display: flex;
  gap: 28px;
  list-style: none;
}

.nav-links a {
  font-size: 14px;
  color: var(--text);
  font-weight: 500;
  transition: color 0.2s;
  position: relative;
}

.nav-links a:hover {
  color: var(--primary);
}

.nav-links a.active {
  color: var(--primary);
}

/* 产品下拉菜单 */
.nav-dropdown {
  position: relative;
}

.dropdown-trigger {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.dropdown-arrow {
  transition: transform 0.2s ease;
}

.dropdown-arrow.rotated {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 12px);
  left: 50%;
  transform: translateX(-50%);
  min-width: 160px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  border: 1px solid var(--border);
  padding: 8px 0;
  z-index: 1001;
}

.dropdown-menu::before {
  content: '';
  position: absolute;
  top: -6px;
  left: 50%;
  transform: translateX(-50%) rotate(45deg);
  width: 12px;
  height: 12px;
  background: white;
  border-left: 1px solid var(--border);
  border-top: 1px solid var(--border);
}

.dropdown-menu a {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  font-size: 14px;
  color: var(--text);
  transition: all 0.2s ease;
}

.dropdown-menu a:hover {
  background: var(--primary-light);
  color: var(--primary);
}

.dropdown-menu a svg {
  flex-shrink: 0;
  color: var(--text-secondary);
}

.dropdown-menu a:hover svg {
  color: var(--primary);
}

/* 下拉菜单动画 */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-8px);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 22px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.btn-text {
  background: transparent;
  color: var(--text);
}

.btn-text:hover {
  color: var(--primary);
}

.btn-lang {
  font-weight: 600;
  min-width: 40px;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 12px;
  background: var(--bg);
}

.btn-lang:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--primary-light);
}

.btn-primary {
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
  color: white;
  box-shadow: 0 4px 14px rgba(22, 119, 255, 0.35);
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(22, 119, 255, 0.45);
}

/* User Menu */
.user-menu-wrapper {
  position: relative;
}

.btn-user {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px 6px 6px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 100px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-user:hover {
  border-color: var(--primary);
  background: var(--primary-light);
}

.user-avatar {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  font-weight: 600;
}

.user-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 200px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  border: 1px solid var(--border);
  overflow: hidden;
  z-index: 1001;
}

.user-info {
  padding: 14px 16px;
  background: #f8fafc;
}

.info-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

.info-role {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.menu-divider {
  height: 1px;
  background: var(--border);
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  font-size: 13px;
  color: var(--text);
  cursor: pointer;
  transition: background 0.2s ease;
  border: none;
  background: none;
  width: 100%;
  text-align: left;
}

.menu-item:hover {
  background: #f1f5f9;
}

.menu-item svg {
  color: var(--text-secondary);
}


/* Products Section */
.products-section {
  height: calc(100vh - 72px);
  margin-top: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 0;
  position: relative;
  background: #f5f7fa;
  box-sizing: border-box;
  scroll-snap-align: start;
  scroll-snap-stop: always;
  overflow: hidden;
}

.products-section .container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.section-header {
  text-align: center;
  margin-bottom: 40px;
}

.section-title {
  font-size: 32px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 12px;
  letter-spacing: -0.5px;
}

.section-desc {
  font-size: 16px;
  color: #6b7280;
  margin: 0;
}

/* Products Grid */
.products-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  position: relative;
  z-index: 1;
  width: 100%;
}

/* Loading and Empty States */
.loading-placeholder,
.empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 20px;
  color: #64748b;
  font-size: 15px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e2e8f0;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Product Card */
.product-card {
  position: relative;
  background: #ffffff;
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: block;
  border: 1px solid transparent;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
  border-color: #e5e7eb;
}

/* Inactive Card - 展示但不可用 */
.product-card.card-inactive {
  cursor: not-allowed;
  opacity: 0.6;
  filter: grayscale(30%);
}

.product-card.card-inactive:hover {
  transform: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.card-badge-inactive {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
  border-radius: 12px;
  z-index: 1;
}

/* Card Colors - Icon with multi-color gradients */
.card-blue .card-icon { background: linear-gradient(135deg, #60a5fa 0%, #93c5fd 50%, #c4b5fd 100%); }
.card-purple .card-icon { background: linear-gradient(135deg, #a78bfa 0%, #c4b5fd 50%, #f9a8d4 100%); }
.card-cyan .card-icon { background: linear-gradient(135deg, #0891b2 0%, #22d3ee 50%, #a5f3fc 100%); }
.card-orange .card-icon { background: linear-gradient(135deg, #f97316 0%, #fbbf24 50%, #fde68a 100%); }
.card-green .card-icon { background: linear-gradient(135deg, #22c55e 0%, #4ade80 50%, #86efac 100%); }
.card-magenta .card-icon { background: linear-gradient(135deg, #ec4899 0%, #f472b6 50%, #fce7f3 100%); }
.card-red .card-icon { background: linear-gradient(135deg, #ef4444 0%, #fca5a5 50%, #fef3c7 100%); }
.card-indigo .card-icon { background: linear-gradient(135deg, #6366f1 0%, #a5b4fc 50%, #e0e7ff 100%); }
/* 动态 Agent 使用的额外颜色 */
.card-teal .card-icon { background: linear-gradient(135deg, #14b8a6 0%, #5eead4 50%, #99f6e4 100%); }
.card-amber .card-icon { background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 50%, #fde68a 100%); }
.card-rose .card-icon { background: linear-gradient(135deg, #f43f5e 0%, #fb7185 50%, #fecdd3 100%); }
.card-lime .card-icon { background: linear-gradient(135deg, #84cc16 0%, #a3e635 50%, #d9f99d 100%); }
.card-sky .card-icon { background: linear-gradient(135deg, #0ea5e9 0%, #38bdf8 50%, #bae6fd 100%); }
.card-violet .card-icon { background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 50%, #ddd6fe 100%); }
.card-emerald .card-icon { background: linear-gradient(135deg, #10b981 0%, #34d399 50%, #a7f3d0 100%); }
.card-pink .card-icon { background: linear-gradient(135deg, #ec4899 0%, #f472b6 50%, #fbcfe8 100%); }

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  transition: transform 0.3s ease;
}

.product-card:hover .card-icon {
  transform: scale(1.05);
}

.card-icon svg {
  width: 24px;
  height: 24px;
  color: white;
}

.product-card h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

.product-card p {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.6;
  margin-bottom: 0;
}

.card-link {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #06b6d4;
  margin-top: 12px;
  opacity: 0;
  transform: translateY(4px);
  transition: all 0.3s ease;
}

.product-card:hover .card-link {
  opacity: 1;
  transform: translateY(0);
}

/* Coming Soon Cards */
.card-coming {
  opacity: 0.6;
}

.card-coming:hover {
  opacity: 0.85;
}

/* 企业信息提取 Section */
.smart-ocr-section {
  min-height: calc(100vh - 72px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 40px 0 60px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  box-sizing: border-box;
  scroll-snap-align: start;
  scroll-snap-stop: always;
}

.smart-ocr-section .container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 800px;
}

.smart-ocr-section .section-header {
  margin-bottom: 32px;
}

/* 历史记录按钮（与开始提取/重置同排） */
.btn-history {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid #e5e7eb;
  background: #fff;
  color: #4b5563;
  transition: border-color 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
}
.btn-history:hover {
  border-color: #6366f1;
  color: #6366f1;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.16);
}

/* 提取表单 */
.extract-content {
  width: 100%;
}

.extract-form {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--border);
}

.form-hint {
  font-size: 14px;
  color: #3b82f6;
  background: #eff6ff;
  padding: 12px 16px;
  border-radius: 8px;
  border-left: 4px solid #3b82f6;
  margin-bottom: 24px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
  margin-bottom: 8px;
}

.form-group input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  background: #f9fafb;
  font-size: 15px;
  font-family: inherit;
  transition: all 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #8b5cf6;
  background: white;
  box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.1);
}

.form-group input::placeholder {
  color: #9ca3af;
}

/* 上传区域 */
.upload-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

.upload-box {
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  background: #f9fafb;
  padding: 24px 16px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  min-height: 160px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.upload-box:hover {
  border-color: #8b5cf6;
  background: #faf5ff;
  transform: translateY(-2px);
}

.upload-box.has-file {
  border-style: solid;
  border-color: #22c55e;
  background: #f0fdf4;
}

.box-icon {
  font-size: 36px;
  margin-bottom: 10px;
}

.box-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 6px;
}

.box-hint {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 4px;
}

.box-formats {
  font-size: 12px;
  color: #9ca3af;
  background: #e5e7eb;
  padding: 4px 10px;
  border-radius: 20px;
  margin-top: 6px;
}

.box-filename {
  font-size: 13px;
  color: #22c55e;
  font-weight: 500;
  margin-top: 10px;
  word-break: break-all;
}

/* 表单按钮 */
.form-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 8px;
}

.btn-secondary {
  background: #f3f4f6;
  color: #4b5563;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

.form-error {
  color: #ef4444;
  font-size: 14px;
  margin-top: 16px;
  padding: 12px 16px;
  background: #fef2f2;
  border-radius: 8px;
  text-align: center;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

/* 加载状态 */
.extract-loading {
  text-align: center;
  padding: 80px 20px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  width: 100%;
}

.loading-spinner-large {
  width: 48px;
  height: 48px;
  border: 4px solid #e2e8f0;
  border-top-color: #6366f1;
  border-radius: 50%;
  margin: 0 auto 24px;
  animation: spin 0.8s linear infinite;
}

.loading-text {
  font-size: 18px;
  color: var(--text);
  margin-bottom: 24px;
}

.progress-bar {
  width: 100%;
  max-width: 400px;
  height: 8px;
  background: #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
  margin: 0 auto;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 10px;
  transition: width 0.3s;
}

/* 结果展示 */
.extract-result {
  width: 100%;
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.result-main {
  /* 固定宽度（预留浮框 116px + 间距 16px），拖动浮框时内容窗口宽度不变 */
  flex: 0 0 auto;
  width: calc(100% - 132px);
  min-width: 0;
}

.result-card {
  background: white;
  border-radius: 12px;
  margin-bottom: 16px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid var(--border);
}

.card-header {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  padding: 12px 16px;
  font-size: 15px;
  font-weight: 600;
}

.card-body {
  padding: 16px;
}

.info-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 0;
  font-size: 14px;
  border-bottom: 1px solid #f3f4f6;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  width: 120px;
  color: #6b7280;
  flex-shrink: 0;
  font-weight: 500;
  padding-top: 7px;
  line-height: 1.5;
}

.info-value {
  flex: 1;
  color: var(--text);
  word-break: break-all;
}

/* 可编辑输入框（textarea，自动撑高、自动换行、不截断） */
.info-input {
  flex: 1;
  min-width: 0;
  width: 100%;
  box-sizing: border-box;
  font-size: 14px;
  font-family: inherit;
  line-height: 1.5;
  color: var(--text);
  background: #f8fafc;
  border: 1px solid transparent;
  border-radius: 6px;
  padding: 6px 8px;
  resize: none;            /* 由 v-auto-grow 控制高度 */
  overflow: hidden;        /* 无滚动条，内容靠撑高显示 */
  white-space: pre-wrap;   /* 保留换行并自动折行 */
  word-break: break-word;  /* 长串也能换行，不会被截断 */
  transition: border-color 0.18s ease, background 0.18s ease;
}
.info-input:hover {
  background: #f1f5f9;
}
.info-input:focus {
  outline: none;
  background: #fff;
  border-color: var(--primary, #1677FF);
}

/* 区块级输入框（核心产品/解决方案等，整行铺满） */
.block-input {
  display: block;
  width: 100%;
}

.card-header-hint {
  margin-left: 8px;
  font-size: 12px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.85);
}

.info-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.info-list li {
  padding: 10px 0;
  font-size: 14px;
  color: var(--text);
  border-bottom: 1px solid #f3f4f6;
}

.info-list li:last-child {
  border-bottom: none;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

/* 浮框：贴着结果窗口右侧，随滚动停靠在视口中间，仅在结果区内出现 */
.result-actions {
  position: sticky;
  top: calc(50vh - 70px);
  flex-shrink: 0;
  width: 116px;
  z-index: 20;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
  margin: 0;
  padding: 10px;
  background: #fff;
  border: 1px solid var(--border, #e2e8f0);
  border-radius: 10px;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.12);
  animation: floatPanelIn 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
  /* 滚动惯性的 transform 由 JS 逐帧直接写在 style 上（GPU 合成），不加过渡 */
  transition: box-shadow 0.25s ease;
  will-change: transform;
}

/* 悬停阴影加深（位移交给 JS 惯性，避免与之冲突） */
.result-actions:hover {
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.18);
}

/* 拖动手柄 */
.drag-handle {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 11px;
  color: #94a3b8;
  cursor: grab;
  user-select: none;
  padding: 2px 0 4px;
  margin-bottom: 2px;
  border-bottom: 1px dashed #e2e8f0;
  touch-action: none;
}
.drag-handle .drag-dots {
  font-size: 14px;
  line-height: 1;
}

/* 拖动中：关闭动效，固定停靠位置，光标变抓握 */
.result-actions.dragging {
  animation: none;
  transition: none;
  transform: none !important;
  cursor: grabbing;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.22);
}
.result-actions.dragging .drag-handle {
  cursor: grabbing;
}

/* 入场：从右侧淡入滑入 */
@keyframes floatPanelIn {
  from {
    opacity: 0;
    transform: translateX(20px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
}

.result-actions .btn {
  width: 100%;
  padding: 7px 8px;
  font-size: 12px;
  line-height: 1.2;
  justify-content: center;
  white-space: nowrap;
  transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
}

.result-actions .btn:hover {
  transform: translateY(-1px);
  filter: brightness(1.03);
}

.result-actions .btn:active {
  transform: translateY(0) scale(0.97);
}

@media (prefers-reduced-motion: reduce) {
  .result-actions,
  .result-actions .btn {
    animation: none;
    transition: none;
  }
}

@media (max-width: 640px) {
  .extract-result {
    flex-direction: column;
  }
  .result-main {
    width: 100%;
  }
  .result-actions {
    position: static;
    width: 100%;
    flex-direction: row;
  }
  .result-actions .btn {
    flex: 1;
  }
}

.raw-ocr-text {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text);
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
  background: #f8fafc;
  padding: 12px;
  border-radius: 8px;
  font-family: 'Noto Sans SC', monospace;
}

/* 响应式 */
@media (max-width: 700px) {
  .form-row,
  .upload-row {
    grid-template-columns: 1fr;
  }

  .info-row {
    flex-direction: column;
  }

  .info-label {
    width: 100%;
    margin-bottom: 4px;
  }
}

/* Responsive */
@media (max-width: 1400px) {
  .container {
    max-width: 1100px;
  }

  .section-header {
    margin-bottom: 32px;
  }

  .section-title {
    font-size: 28px;
  }

  .section-desc {
    font-size: 15px;
  }

  .products-grid {
    gap: 16px;
  }

  .product-card {
    padding: 20px;
  }

  .card-icon {
    width: 44px;
    height: 44px;
  }

  .card-icon svg {
    width: 22px;
    height: 22px;
  }

  .product-card h3 {
    font-size: 15px;
  }

  .product-card p {
    font-size: 12px;
  }
}

@media (max-width: 1200px) {
  .section-header {
    margin-bottom: 24px;
  }

  .section-title {
    font-size: 24px;
  }

  .section-desc {
    font-size: 14px;
  }

  .products-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
  }

  .product-card {
    padding: 16px;
  }

  .card-icon {
    width: 40px;
    height: 40px;
    margin-bottom: 12px;
  }

  .card-icon svg {
    width: 20px;
    height: 20px;
  }

  .product-card h3 {
    font-size: 14px;
    margin-bottom: 6px;
  }

  .product-card p {
    font-size: 11px;
    line-height: 1.5;
  }

  .card-link {
    font-size: 12px;
    margin-top: 8px;
  }
}

@media (max-width: 900px) {
  .products-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .nav-links {
    display: none;
  }
}

@media (max-width: 640px) {
  .products-section {
    padding: 20px 0;
  }

  .products-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .product-card {
    padding: 14px;
  }
}

/* Toast 提示 */
.toast-container {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
}

.toast-content {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 24px;
  background: rgba(30, 30, 30, 0.92);
  backdrop-filter: blur(12px);
  border-radius: 12px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.toast-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: #fbbf24;
}

/* Toast 动画 */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-10px);
}
</style>
