<script setup lang="ts">
// Permissions - 权限管理
</script>

<template>
  <div class="permissions">
    <h1>权限管理</h1>
    <p class="description">管理角色、用户权限和 API 访问控制</p>

    <div class="tabs">
      <button class="tab active">角色管理</button>
      <button class="tab">用户权限</button>
      <button class="tab">API 权限</button>
    </div>

    <div class="content">
      <p>权限管理功能开发中...</p>
    </div>
  </div>
</template>

<style scoped>
.permissions {
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

.content {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
</style>
