<script setup lang="ts">
import { ref } from 'vue'

const visible = ref(true)

function close() {
  visible.value = false
}
</script>

<template>
  <div v-if="visible" class="banner">
    <!-- 左侧：返回首页 -->
    <router-link to="/" class="back-btn">
      <svg class="back-arrow" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="15 18 9 12 15 6"/>
      </svg>
      <span>返回首页</span>
    </router-link>

    <!-- 中间：广告内容 -->
    <div class="banner-content">
      <div class="banner-logo">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
        </svg>
        <span class="mono">manus</span>
      </div>
      <span class="banner-text">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 6v6l4 2"/>
        </svg>
        Run any Skill in Manus with one click
      </span>
      <a href="#" class="banner-btn">Get Started</a>
    </div>

    <!-- 右侧：关闭按钮 -->
    <button class="banner-close" @click="close">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>
  </div>
</template>

<style scoped>
.banner {
  background: var(--text-primary);
  color: white;
  padding: 10px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  margin-left: 120px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  transition: all 0.15s;
  flex-shrink: 0;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.4);
  color: white;
}

.back-arrow {
  font-weight: 600;
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 20px;
  flex: 1;
  justify-content: center;
}

.banner-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.banner-text {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
}

.banner-btn {
  padding: 6px 16px;
  background: white;
  color: var(--text-primary);
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.15s;
}

.banner-btn:hover {
  background: rgba(255, 255, 255, 0.9);
}

.banner-close {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.banner-close:hover {
  color: white;
}

@media (max-width: 768px) {
  .banner {
    padding: 10px 16px;
  }

  .banner-logo {
    display: none;
  }

  .banner-text {
    font-size: 13px;
  }

  .back-btn span {
    display: none;
  }
}
</style>
