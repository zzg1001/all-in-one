<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import config from '@/config'
import { setLocale, getLocale } from '@/locales'
import { useAuthStore } from '@/stores/auth'
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

// Agent 配置（8个入口）
const allAgents = [
  { name: 'HR部门 Agent', department: 'HR', theme: 'blue', desc: '人事数据分析 · 入离职流程自动化 · 招聘文案生成' },
  { name: '销售部门 Agent', department: '销售', theme: 'purple', desc: '销售数据分析 · 客户管理自动化 · 销售物料生成' },
  { name: '采购部门 Agent', department: '采购', theme: 'cyan', desc: '采购成本分析 · 采购流程自动化 · 供应商管理' },
  { name: '行政部门 Agent', department: '行政', theme: 'orange', desc: '行政数据分析 · 会议室/车辆预约自动化 · 会议纪要生成' },
  { name: '财务部门 Agent', department: '财务', theme: 'green', desc: '财务数据分析 · 费用报销审核 · 财务文书生成' },
  { name: '智能体自定义', department: null, theme: 'magenta', desc: '自然语言指令训练 · 个性化流程自动化 · 适配专属需求' },
  { name: '商业线索 Agent', department: null, theme: 'red', desc: '智能分级推送 · 全网智能抓取 · 全流程转化管理' },
  { name: '老板视角', department: null, theme: 'indigo', desc: '现金流与财务健康 · 增长与战略方向 · 人才与团队' },
]

// 所有 Agent 都显示（无论是否登录）
const visibleAgents = computed(() => allAgents)

// 处理 Agent 点击
function handleAgentClick(agentName: string, theme: string) {
  const targetUrl = `/app?from=home&agent=${encodeURIComponent(agentName)}&theme=${theme}`

  // 未登录 -> 跳转登录页
  if (!authStore.isAuthenticated) {
    router.push({ name: 'login', query: { redirect: targetUrl } })
    return
  }

  // 已登录但无权限
  if (!authStore.canAccessAgent(agentName)) {
    alert(`您没有权限访问「${agentName}」，请联系管理员`)
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

// 检查认证状态
onMounted(async () => {
  await authStore.checkAuth()
})
</script>

<template>
  <div class="home-page">
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
              <li><a href="#products" class="active">{{ $t('header.products') }}</a></li>
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

    <!-- Products Section -->
    <section id="products" class="products-section">
      <div class="container">
        <div class="section-header">
          <h2 class="section-title">全栈 AI 产品矩阵</h2>
          <p class="section-desc">基于大模型和行业知识，构建面向OA场景的智能产品生态</p>
        </div>
        <div class="products-grid">
          <!-- 部门 Agent 列表 -->
          <div
            v-for="agent in visibleAgents"
            :key="agent.name"
            class="product-card"
            :class="`card-${agent.theme}`"
            @click="handleAgentClick(agent.name, agent.theme)"
          >
            <div class="card-icon">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
              </svg>
            </div>
            <h3>{{ agent.name }}</h3>
            <p>{{ agent.desc }}</p>
            <span class="card-link">了解更多 →</span>
          </div>


        </div>
      </div>
    </section>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body {
  overflow: hidden;
  height: 100%;
  margin: 0;
  padding: 0;
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
  overflow: hidden;
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
  overflow: hidden;
  box-sizing: border-box;
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

/* Card Colors - Icon with multi-color gradients */
.card-blue .card-icon { background: linear-gradient(135deg, #60a5fa 0%, #93c5fd 50%, #c4b5fd 100%); }
.card-purple .card-icon { background: linear-gradient(135deg, #a78bfa 0%, #c4b5fd 50%, #f9a8d4 100%); }
.card-cyan .card-icon { background: linear-gradient(135deg, #0891b2 0%, #22d3ee 50%, #a5f3fc 100%); }
.card-orange .card-icon { background: linear-gradient(135deg, #f97316 0%, #fbbf24 50%, #fde68a 100%); }
.card-green .card-icon { background: linear-gradient(135deg, #22c55e 0%, #4ade80 50%, #86efac 100%); }
.card-magenta .card-icon { background: linear-gradient(135deg, #ec4899 0%, #f472b6 50%, #fce7f3 100%); }
.card-red .card-icon { background: linear-gradient(135deg, #ef4444 0%, #fca5a5 50%, #fef3c7 100%); }
.card-indigo .card-icon { background: linear-gradient(135deg, #6366f1 0%, #a5b4fc 50%, #e0e7ff 100%); }

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
</style>
