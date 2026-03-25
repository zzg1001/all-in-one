<script setup lang="ts">
import { ref, computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import LogPanel from '@/components/common/LogPanel.vue'
import DataNotesTab from '@/components/common/DataNotesTab.vue'
import GlobalNav from '@/components/common/GlobalNav.vue'

const route = useRoute()
const showLogPanel = ref(false)

// 从 URL 获取 agent 名称，提取部门名（去掉 " Agent" 后缀）
const departmentName = computed(() => {
  const agentName = route.query.agent as string
  if (agentName) {
    const decoded = decodeURIComponent(agentName)
    // 去掉 " Agent" 后缀
    return decoded.replace(/ Agent$/, '')
  }
  return ''
})
</script>

<template>
  <GlobalNav />
  <RouterView />
  <LogPanel v-model:show="showLogPanel" />
  <DataNotesTab :department-name="departmentName" />
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html,
body {
  height: 100%;
}

body {
  background: #f8fafc;
  color: #0f172a;
  font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  height: 100%;
  width: 100%;
  overflow-x: hidden;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f5f9;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 选中文本颜色 */
::selection {
  background: rgba(99, 102, 241, 0.2);
  color: #0f172a;
}
</style>
