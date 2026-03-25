<script setup lang="ts">
// Models - 模型配置管理
</script>

<template>
  <div class="models">
    <h1>模型配置</h1>
    <p class="description">管理 AI 模型的 API Key、Base URL 和参数配置</p>

    <div class="model-list">
      <div class="model-card">
        <div class="model-header">
          <span class="model-name">Claude</span>
          <span class="model-status active">启用</span>
        </div>
        <div class="model-info">
          <div class="info-item">
            <span class="label">模型:</span>
            <span class="value">claude-opus-4-5</span>
          </div>
          <div class="info-item">
            <span class="label">Base URL:</span>
            <span class="value">--</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.models {
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

.model-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.model-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.model-name {
  font-size: 18px;
  font-weight: 600;
}

.model-status {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
}

.model-status.active {
  background: #e6f7e6;
  color: #52c41a;
}

.model-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  gap: 8px;
}

.label {
  color: #666;
  min-width: 80px;
}

.value {
  color: #333;
}
</style>
