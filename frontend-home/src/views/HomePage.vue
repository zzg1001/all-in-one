<script setup lang="ts">
import { ref, onMounted } from 'vue'
import config from '@/config'
import { setLocale, getLocale } from '@/locales'

const currentTab = ref('manufacturing')
const tabs = ['manufacturing', 'healthcare', 'retail', 'energy']

// 语言切换
const currentLocale = ref(getLocale())
const toggleLocale = () => {
  const newLocale = currentLocale.value === 'zh' ? 'en' : 'zh'
  setLocale(newLocale)
  currentLocale.value = newLocale
}

function selectTab(tab: string) {
  currentTab.value = tab
}

onMounted(() => {
  // Header scroll effect
  const header = document.querySelector('.header') as HTMLElement
  if (header) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 50) {
        header.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)'
      } else {
        header.style.boxShadow = 'none'
      }
    })
  }
})

function scrollTo(id: string) {
  const target = document.querySelector(id)
  if (target) {
    const headerHeight = 64
    const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - headerHeight
    window.scrollTo({
      top: targetPosition,
      behavior: 'smooth'
    })
  }
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
              <li><a href="#products" @click.prevent="scrollTo('#products')" class="active">{{ $t('header.products') }}</a></li>
              <li><a href="#solutions" @click.prevent="scrollTo('#solutions')">{{ $t('header.solutions') }}</a></li>
              <li><a href="#customers" @click.prevent="scrollTo('#customers')">{{ $t('header.customers') }}</a></li>
              <li><a href="#projects" @click.prevent="scrollTo('#projects')">{{ $t('header.quickEntry') }}</a></li>
              <li><a href="#contact" @click.prevent="scrollTo('#contact')">{{ $t('header.about') }}</a></li>
            </ul>
          </nav>

          <div class="header-actions">
            <button class="btn btn-text btn-lang" @click="toggleLocale">{{ currentLocale === 'zh' ? 'EN' : '中' }}</button>
            <button class="btn btn-text">{{ $t('header.login') }}</button>
            <button class="btn btn-primary" @click="scrollTo('#projects')">{{ $t('header.freeTrial') }}</button>
          </div>
        </div>
      </div>
    </header>

    <!-- Hero Section -->
    <section class="hero">
      <div class="container">
        <div class="hero-inner">
          <div class="hero-content">
            <div class="hero-badge">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
              </svg>
              {{ $t('hero.badge') }}
            </div>

            <h1 class="hero-title">
              {{ $t('hero.title1') }}<span class="highlight">{{ $t('hero.titleHighlight') }}</span><br>
              {{ $t('hero.title2') }}
            </h1>

            <p class="hero-desc">
              {{ $t('hero.desc') }}
            </p>

            <div class="hero-buttons">
              <a href="#products" @click.prevent="scrollTo('#products')" class="btn btn-primary btn-lg btn-icon">
                <span>{{ $t('hero.exploreProducts') }}</span>
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/>
                </svg>
              </a>
              <a href="#contact" @click.prevent="scrollTo('#contact')" class="btn btn-outline btn-lg">{{ $t('hero.contactUs') }}</a>
            </div>

            <div class="hero-stats">
              <div class="hero-stat">
                <div class="hero-stat-value">500<span>+</span></div>
                <div class="hero-stat-label">{{ $t('hero.stats.enterprises') }}</div>
              </div>
              <div class="hero-stat">
                <div class="hero-stat-value">50<span>+</span></div>
                <div class="hero-stat-label">{{ $t('hero.stats.fortune500') }}</div>
              </div>
              <div class="hero-stat">
                <div class="hero-stat-value">30<span>%</span></div>
                <div class="hero-stat-label">{{ $t('hero.stats.efficiency') }}</div>
              </div>
            </div>
          </div>

          <div class="hero-visual">
            <div class="hero-image">
              <div class="hero-dashboard">
                <div class="dashboard-header">
                  <div class="dashboard-dot red"></div>
                  <div class="dashboard-dot yellow"></div>
                  <div class="dashboard-dot green"></div>
                  <span class="dashboard-title">{{ $t('dashboard.title') }}</span>
                </div>
                <div class="dashboard-grid">
                  <div class="dashboard-card">
                    <div class="dashboard-card-label">{{ $t('dashboard.deviceRate') }}</div>
                    <div class="dashboard-card-value up">96.8%</div>
                  </div>
                  <div class="dashboard-card">
                    <div class="dashboard-card-label">{{ $t('dashboard.capacity') }}</div>
                    <div class="dashboard-card-value">87.2%</div>
                  </div>
                  <div class="dashboard-card">
                    <div class="dashboard-card-label">{{ $t('dashboard.alerts') }}</div>
                    <div class="dashboard-card-value accent">3</div>
                  </div>
                  <div class="dashboard-chart">
                    <div class="chart-bar" style="height: 60%"></div>
                    <div class="chart-bar" style="height: 80%"></div>
                    <div class="chart-bar" style="height: 45%"></div>
                    <div class="chart-bar" style="height: 90%"></div>
                    <div class="chart-bar" style="height: 70%"></div>
                    <div class="chart-bar" style="height: 85%"></div>
                    <div class="chart-bar" style="height: 55%"></div>
                    <div class="chart-bar" style="height: 95%"></div>
                  </div>
                </div>
              </div>

              <div class="floating-card card-1">
                <div class="floating-icon blue">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                </div>
                <div class="floating-text">
                  <strong>{{ $t('dashboard.realtime') }}</strong>
                  <span class="status-ok">{{ $t('dashboard.deviceNormal') }}</span>
                </div>
              </div>

              <div class="floating-card card-2">
                <div class="floating-icon orange">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
                  </svg>
                </div>
                <div class="floating-text">
                  <strong>{{ $t('dashboard.aiPredict') }}</strong>
                  <span>{{ $t('dashboard.efficiencyUp') }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Products Section -->
    <section id="products" class="products">
      <div class="container">
        <div class="section-header">
          <div class="section-tag">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
            </svg>
            {{ $t('products.tag') }}
          </div>
          <h2 class="section-title">{{ $t('products.title') }}</h2>
          <p class="section-desc">{{ $t('products.desc') }}</p>
        </div>

        <div class="products-grid">
          <a :href="`${config.portalUrl}?from=home`" target="_blank" class="product-card clickable">
            <div class="product-icon blue">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
              </svg>
            </div>
            <h3>{{ $t('products.aiAgent.name') }}</h3>
            <p>{{ $t('products.aiAgent.desc') }}</p>
            <div class="arrow">{{ $t('products.learnMore') }} <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg></div>
          </a>

          <router-link to="/skills" class="product-card clickable">
            <div class="product-icon purple">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
              </svg>
            </div>
            <h3>{{ $t('products.aiSkills.name') }}</h3>
            <p>{{ $t('products.aiSkills.desc') }}</p>
            <div class="arrow">{{ $t('products.learnMore') }} <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg></div>
          </router-link>

          <a :href="`${config.adminUrl}/ccswitch?from=home`" target="_blank" class="product-card clickable">
            <div class="product-icon cyan">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
              </svg>
            </div>
            <h3>{{ $t('products.modelMgmt.name') }}</h3>
            <p>{{ $t('products.modelMgmt.desc') }}</p>
            <div class="arrow">{{ $t('products.learnMore') }} <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg></div>
          </a>

          <div class="product-card">
            <div class="product-icon orange">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"/>
              </svg>
            </div>
            <h3>{{ $t('products.dataPlatform.name') }}</h3>
            <p>{{ $t('products.dataPlatform.desc') }}</p>
            <div class="arrow">{{ $t('products.learnMore') }} <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg></div>
          </div>

          <div class="product-card">
            <div class="product-icon green">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
              </svg>
            </div>
            <h3>{{ $t('products.dataWarehouse.name') }}</h3>
            <p>{{ $t('products.dataWarehouse.desc') }}</p>
            <div class="arrow">{{ $t('products.learnMore') }} <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg></div>
          </div>

          <div class="product-card">
            <div class="product-icon magenta">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <h3>{{ $t('products.taskScheduler.name') }}</h3>
            <p>{{ $t('products.taskScheduler.desc') }}</p>
            <div class="arrow">{{ $t('products.learnMore') }} <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg></div>
          </div>

          <div class="product-card">
            <div class="product-icon red">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
              </svg>
            </div>
            <h3>{{ $t('products.predictiveMaint.name') }}</h3>
            <p>{{ $t('products.predictiveMaint.desc') }}</p>
            <div class="arrow">{{ $t('products.learnMore') }} <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg></div>
          </div>

          <div class="product-card">
            <div class="product-icon geek">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/>
              </svg>
            </div>
            <h3>{{ $t('products.smartConfig.name') }}</h3>
            <p>{{ $t('products.smartConfig.desc') }}</p>
            <div class="arrow">{{ $t('products.learnMore') }} <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg></div>
          </div>
        </div>
      </div>
    </section>

    <!-- Solutions Section -->
    <section id="solutions" class="solutions">
      <div class="container">
        <div class="section-header">
          <div class="section-tag">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"/>
            </svg>
            {{ $t('solutions.tag') }}
          </div>
          <h2 class="section-title">{{ $t('solutions.title') }}</h2>
          <p class="section-desc">{{ $t('solutions.desc') }}</p>
        </div>

        <div class="solutions-tabs">
          <button
            v-for="tab in tabs"
            :key="tab"
            class="solution-tab"
            :class="{ active: currentTab === tab }"
            @click="selectTab(tab)"
          >{{ $t(`solutions.tabs.${tab}`) }}</button>
        </div>

        <div class="solution-content">
          <div class="solution-info">
            <h3>{{ $t(`solutions.tabs.${currentTab}`) }}{{ $t('solutions.solutionFor') }}</h3>
            <p>{{ $t('solutions.content') }}</p>

            <div class="solution-features">
              <div class="solution-feature">
                <div class="solution-feature-icon">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                </div>
                <span>{{ $t('solutions.features.monitoring') }}</span>
              </div>
              <div class="solution-feature">
                <div class="solution-feature-icon">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                </div>
                <span>{{ $t('solutions.features.scheduling') }}</span>
              </div>
              <div class="solution-feature">
                <div class="solution-feature-icon">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                </div>
                <span>{{ $t('solutions.features.quality') }}</span>
              </div>
              <div class="solution-feature">
                <div class="solution-feature-icon">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                </div>
                <span>{{ $t('solutions.features.energy') }}</span>
              </div>
            </div>

            <a href="#" class="btn btn-primary btn-icon">
              {{ $t('solutions.viewDetails') }}
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
            </a>
          </div>

          <div class="solution-visual">
            <div class="solution-diagram">
              <div class="diagram-node">
                <div class="diagram-node-icon">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"/></svg>
                </div>
                <span>{{ $t('solutions.diagram.device') }}</span>
              </div>
              <div class="diagram-node">
                <div class="diagram-node-icon">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7"/></svg>
                </div>
                <span>{{ $t('solutions.diagram.data') }}</span>
              </div>
              <div class="diagram-node">
                <div class="diagram-node-icon">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2z"/></svg>
                </div>
                <span>{{ $t('solutions.diagram.analysis') }}</span>
              </div>
              <div class="diagram-node diagram-center">
                <div class="diagram-node-icon">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                </div>
                <span>{{ $t('solutions.diagram.aiEngine') }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Customers Section -->
    <section id="customers" class="customers">
      <div class="container">
        <div class="section-header">
          <div class="section-tag">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
            </svg>
            {{ $t('customers.tag') }}
          </div>
          <h2 class="section-title">{{ $t('customers.title') }}</h2>
          <p class="section-desc">{{ $t('customers.desc') }}</p>
        </div>

        <div class="customers-logos">
          <span class="customer-logo">{{ $t('customers.logos.exxon') }}</span>
          <span class="customer-logo">{{ $t('customers.logos.saintGobain') }}</span>
          <span class="customer-logo">{{ $t('customers.logos.lvmh') }}</span>
          <span class="customer-logo">{{ $t('customers.logos.chinaTobacco') }}</span>
          <span class="customer-logo">{{ $t('customers.logos.huawei') }}</span>
          <span class="customer-logo">{{ $t('customers.logos.microsoft') }}</span>
        </div>

      </div>
    </section>

    <!-- Projects Section -->
    <section id="projects" class="projects">
      <div class="container">
        <div class="section-header">
          <div class="section-tag">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
            </svg>
            {{ $t('projects.tag') }}
          </div>
          <h2 class="section-title">{{ $t('projects.title') }}</h2>
          <p class="section-desc">{{ $t('projects.desc') }}</p>
        </div>

        <div class="projects-grid">
          <router-link to="/skills" class="project-card">
            <div class="project-card-header">
              <div class="project-card-icon blue">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
              </div>
              <h3>{{ $t('projects.aiSkills.name') }}</h3>
            </div>
            <p>{{ $t('projects.aiSkills.desc') }}</p>
            <div class="project-card-footer">
              <span class="project-card-tag">{{ $t('projects.aiSkills.tag') }}</span>
              <div class="project-card-arrow">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
              </div>
            </div>
          </router-link>

          <a :href="config.adminUrl" target="_blank" class="project-card">
            <div class="project-card-header">
              <div class="project-card-icon purple">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                </svg>
              </div>
              <h3>{{ $t('projects.admin.name') }}</h3>
            </div>
            <p>{{ $t('projects.admin.desc') }}</p>
            <div class="project-card-footer">
              <span class="project-card-tag">{{ $t('projects.admin.tag') }}</span>
              <div class="project-card-arrow">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
              </div>
            </div>
          </a>

          <div class="project-card" style="cursor: pointer;">
            <div class="project-card-header">
              <div class="project-card-icon green">
                <svg fill="currentColor" viewBox="0 0 24 24"><path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 01.213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 00.167-.054l1.903-1.114a.864.864 0 01.717-.098 10.16 10.16 0 002.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348z"/></svg>
              </div>
              <h3>{{ $t('projects.wechat.name') }}</h3>
            </div>
            <p>{{ $t('projects.wechat.desc') }}</p>
            <div class="project-card-footer">
              <span class="project-card-tag">{{ $t('projects.wechat.tag') }}</span>
              <div class="project-card-arrow">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
              </div>
            </div>
          </div>

          <a href="#" class="project-card">
            <div class="project-card-header">
              <div class="project-card-icon orange">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
              </div>
              <h3>{{ $t('projects.oa.name') }}</h3>
            </div>
            <p>{{ $t('projects.oa.desc') }}</p>
            <div class="project-card-footer">
              <span class="project-card-tag">{{ $t('projects.oa.tag') }}</span>
              <div class="project-card-arrow">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
              </div>
            </div>
          </a>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section id="contact" class="cta">
      <div class="container">
        <div class="cta-content">
          <h2>{{ $t('contact.title') }}</h2>
          <p>{{ $t('contact.desc') }}</p>
          <div class="cta-buttons">
            <a href="mailto:contact@ikedata.com" class="btn btn-white btn-lg btn-icon">
              {{ $t('contact.form.submit') }}
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
            </a>
            <a href="tel:021-12345678" class="btn btn-ghost btn-lg">{{ $t('contact.info.phoneValue') }}</a>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
      <div class="container">
        <div class="footer-grid">
          <div class="footer-brand">
            <a href="/" class="logo">
              <div class="logo-icon">IK</div>
              <div class="logo-text">{{ $t('logo.text') }}</div>
            </a>
            <p>{{ $t('footer.desc') }}</p>
          </div>
          <div class="footer-col">
            <h4>{{ $t('footer.products') }}</h4>
            <ul>
              <li><a href="#products" @click.prevent="scrollTo('#products')">{{ $t('products.aiAgent.name') }}</a></li>
              <li><router-link to="/skills">{{ $t('products.aiSkills.name') }}</router-link></li>
              <li><a href="#products" @click.prevent="scrollTo('#products')">{{ $t('products.modelMgmt.name') }}</a></li>
              <li><a href="#products" @click.prevent="scrollTo('#products')">{{ $t('products.dataPlatform.name') }}</a></li>
            </ul>
          </div>
          <div class="footer-col">
            <h4>{{ $t('header.solutions') }}</h4>
            <ul>
              <li><a href="#solutions" @click.prevent="scrollTo('#solutions')">{{ $t('solutions.tabs.manufacturing') }}</a></li>
              <li><a href="#solutions" @click.prevent="scrollTo('#solutions')">{{ $t('solutions.tabs.healthcare') }}</a></li>
              <li><a href="#solutions" @click.prevent="scrollTo('#solutions')">{{ $t('solutions.tabs.retail') }}</a></li>
              <li><a href="#solutions" @click.prevent="scrollTo('#solutions')">{{ $t('solutions.tabs.energy') }}</a></li>
            </ul>
          </div>
          <div class="footer-col">
            <h4>{{ $t('footer.resources') }}</h4>
            <ul>
              <li><a href="#">{{ $t('footer.docCenter') }}</a></li>
              <li><a href="#">{{ $t('footer.apiRef') }}</a></li>
              <li><a href="#">{{ $t('footer.bestPractice') }}</a></li>
              <li><a href="#">{{ $t('footer.devCommunity') }}</a></li>
            </ul>
          </div>
          <div class="footer-col">
            <h4>{{ $t('footer.contactUs') }}</h4>
            <ul>
              <li><a href="#">{{ $t('contact.info.addressValue') }}</a></li>
              <li><a href="mailto:contact@ikedata.com">{{ $t('contact.info.emailValue') }}</a></li>
              <li><a href="tel:021-12345678">{{ $t('contact.info.phoneValue') }}</a></li>
            </ul>
          </div>
        </div>
        <div class="footer-bottom">
          <p>{{ $t('footer.copyright') }}</p>
          <div class="footer-links">
            <a href="#">{{ $t('footer.privacy') }}</a>
            <a href="#">{{ $t('footer.terms') }}</a>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<style>
@import './HomePage.css';
</style>
