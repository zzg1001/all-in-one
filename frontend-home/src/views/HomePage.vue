<script setup lang="ts">
import { ref } from 'vue'
import config from '@/config'
import { setLocale, getLocale } from '@/locales'

// 语言切换
const currentLocale = ref(getLocale())
const toggleLocale = () => {
  const newLocale = currentLocale.value === 'zh' ? 'en' : 'zh'
  setLocale(newLocale)
  currentLocale.value = newLocale
}
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
              <li><a :href="`${config.portalUrl}/agents`" target="_blank">{{ $t('header.manage') }}</a></li>
            </ul>
          </nav>

          <div class="header-actions">
            <button class="btn btn-text btn-lang" @click="toggleLocale">{{ currentLocale === 'zh' ? 'EN' : '中' }}</button>
            <button class="btn btn-text">{{ $t('header.login') }}</button>
            <button class="btn btn-primary">{{ $t('header.freeTrial') }}</button>
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
          <!-- HR部门 Agent -->
          <a :href="`${config.portalUrl}?from=home&agent=${encodeURIComponent('HR部门 Agent')}&theme=blue`" target="_blank" class="product-card card-blue">
            <div class="card-icon">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
              </svg>
            </div>
            <h3>HR部门 Agent</h3>
            <p>人事数据分析 · 入离职流程自动化 · 招聘文案生成</p>
            <span class="card-link">了解更多 →</span>
          </a>

          <!-- 销售部门 Agent -->
          <a :href="`${config.portalUrl}?from=home&agent=${encodeURIComponent('销售部门 Agent')}&theme=purple`" target="_blank" class="product-card card-purple">
            <div class="card-icon">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
              </svg>
            </div>
            <h3>销售部门 Agent</h3>
            <p>销售数据分析 · 客户管理自动化 · 销售物料生成</p>
            <span class="card-link">了解更多 →</span>
          </a>

          <!-- 采购部门 Agent -->
          <a :href="`${config.portalUrl}?from=home&agent=${encodeURIComponent('采购部门 Agent')}&theme=cyan`" target="_blank" class="product-card card-cyan">
            <div class="card-icon">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
              </svg>
            </div>
            <h3>采购部门 Agent</h3>
            <p>采购成本分析 · 采购流程自动化 · 供应商管理</p>
            <span class="card-link">了解更多 →</span>
          </a>

          <!-- 行政部门 Agent -->
          <a :href="`${config.portalUrl}?from=home&agent=${encodeURIComponent('行政部门 Agent')}&theme=orange`" target="_blank" class="product-card card-orange">
            <div class="card-icon">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
              </svg>
            </div>
            <h3>行政部门 Agent</h3>
            <p>行政数据分析 · 会议室/车辆预约自动化 · 会议纪要生成</p>
            <span class="card-link">了解更多 →</span>
          </a>

          <!-- 财务部门 Agent -->
          <a :href="`${config.portalUrl}?from=home&agent=${encodeURIComponent('财务部门 Agent')}&theme=green`" target="_blank" class="product-card card-green">
            <div class="card-icon">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <h3>财务部门 Agent</h3>
            <p>财务数据分析 · 费用报销审核 · 财务文书生成</p>
            <span class="card-link">了解更多 →</span>
          </a>

          <!-- 智能体自定义 -->
          <a :href="`${config.portalUrl}?from=home&agent=${encodeURIComponent('智能体自定义')}&theme=magenta`" target="_blank" class="product-card card-magenta">
            <div class="card-icon">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z"/>
              </svg>
            </div>
            <h3>智能体自定义</h3>
            <p>自然语言指令训练 · 个性化流程自动化 · 适配专属需求</p>
            <span class="card-link">了解更多 →</span>
          </a>

          <!-- 商业线索 Agent -->
          <a :href="`${config.portalUrl}?from=home&agent=${encodeURIComponent('商业线索 Agent')}&theme=red`" target="_blank" class="product-card card-red">
            <div class="card-icon">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7"/>
              </svg>
            </div>
            <h3>商业线索 Agent</h3>
            <p>智能分级推送 · 全网智能抓取 · 全流程转化管理</p>
            <span class="card-link">了解更多 →</span>
          </a>

          <!-- 老板视角 -->
          <a :href="`${config.portalUrl}?from=home&agent=${encodeURIComponent('老板视角')}&theme=indigo`" target="_blank" class="product-card card-indigo">
            <div class="card-icon">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
              </svg>
            </div>
            <h3>老板视角</h3>
            <p>现金流与财务健康 · 增长与战略方向 · 人才与团队</p>
            <span class="card-link">了解更多 →</span>
          </a>
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
