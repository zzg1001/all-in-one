<script setup lang="ts">
// Logs - 日志审计
</script>

<template>
  <div class="logs">
    <h1>日志审计</h1>
    <p class="description">查看操作日志、API 调用日志和错误追踪</p>

    <div class="tabs">
      <button class="tab active">操作日志</button>
      <button class="tab">调用日志</button>
      <button class="tab">错误日志</button>
    </div>

    <div class="log-list">
      <p>日志审计功能开发中...</p>
    </div>
  </div>
</template>

<style scoped>
.logs {
  padding: 24px;
}

h1 {
  margin-bottom: 8px;
  color: #333;
}

.description {
  color: #666;
  margin-bottom: 24px;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
}

.tab {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
}

.tab.active {
  background: #1890ff;
  color: white;
  border-color: #1890ff;
}

.log-list {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
</style>
