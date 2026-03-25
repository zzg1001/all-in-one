<script setup lang="ts">
import { ref } from 'vue'

const isDark = ref(false)

function toggleTheme() {
  isDark.value = !isDark.value
}
</script>

<template>
  <header class="header">
    <div class="header-content">
      <!-- Left: Status + Logo -->
      <div class="header-left">
        <div class="status-badge mono">
          <span class="status-dot"></span>
          <span>ready</span>
        </div>
        <a href="/skills" class="logo mono">
          <span class="logo-prefix">~/</span>skillsmp<span class="cursor"></span>
        </a>
      </div>

      <!-- Center: Navigation -->
      <nav class="header-nav">
        <a href="#search" class="nav-btn mono">
          <span class="cmd">$</span> ai --search
        </a>
        <a href="#categories" class="nav-btn mono">
          <span class="cmd">$</span> cd /categories
        </a>
        <a href="#stats" class="nav-btn mono">
          <span class="cmd">$</span> watch stats
        </a>
        <a href="/docs" class="nav-btn mono">
          <span class="cmd">$</span> man docs
        </a>
        <a href="/api" class="nav-btn mono">
          <span class="cmd">$</span> api --docs
        </a>
      </nav>

      <!-- Right: Actions -->
      <div class="header-right">
        <button class="icon-btn" @click="toggleTheme" title="Toggle theme">
          <svg v-if="!isDark" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="5"/>
            <line x1="12" y1="1" x2="12" y2="3"/>
            <line x1="12" y1="21" x2="12" y2="23"/>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
            <line x1="1" y1="12" x2="3" y2="12"/>
            <line x1="21" y1="12" x2="23" y2="12"/>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
          </svg>
          <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
          </svg>
        </button>
        <button class="lang-btn mono">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="2" y1="12" x2="22" y2="12"/>
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
          </svg>
          EN
        </button>
        <a href="/login" class="signin-btn mono">
          <span class="cmd">$</span> Sign In <span class="arrow">-></span>
        </a>
      </div>
    </div>
  </header>
</template>

<style scoped>
.header {
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: var(--container-width);
  margin: 0 auto;
  padding: 0 24px;
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  font-size: 13px;
  color: var(--text-secondary);
}

.status-dot {
  width: 8px;
  height: 8px;
  background: var(--accent-green);
  border-radius: 50%;
}

.logo {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  text-decoration: none;
}

.logo-prefix {
  color: var(--text-muted);
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
  text-decoration: none;
}

.nav-btn:hover {
  border-color: var(--text-muted);
  color: var(--text-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.icon-btn:hover {
  border-color: var(--text-muted);
  color: var(--text-primary);
}

.lang-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.lang-btn:hover {
  border-color: var(--text-muted);
  color: var(--text-primary);
}

.signin-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--bg-primary);
  border: 1px solid var(--accent-orange);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--accent-orange);
  cursor: pointer;
  transition: all 0.15s;
  text-decoration: none;
}

.signin-btn:hover {
  background: var(--accent-orange);
  color: white;
}

.signin-btn .arrow {
  font-family: sans-serif;
}

@media (max-width: 1024px) {
  .header-nav {
    display: none;
  }
}

@media (max-width: 768px) {
  .header-content {
    padding: 0 16px;
  }

  .lang-btn,
  .icon-btn {
    display: none;
  }
}
</style>
