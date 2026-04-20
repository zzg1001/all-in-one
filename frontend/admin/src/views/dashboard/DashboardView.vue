<script setup lang="ts">
// Dashboard - 驾驶舱
</script>

<template>
  <div class="dashboard">
    <h1>驾驶舱</h1>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-title">今日调用量</div>
        <div class="stat-value">--</div>
      </div>
      <div class="stat-card">
        <div class="stat-title">Token 消耗</div>
        <div class="stat-value">--</div>
      </div>
      <div class="stat-card">
        <div class="stat-title">活跃用户</div>
        <div class="stat-value">--</div>
      </div>
      <div class="stat-card">
        <div class="stat-title">成功率</div>
        <div class="stat-value">--</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 24px;
}

h1 {
  margin-bottom: 24px;
  color: #333;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.stat-title {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #333;
}
</style>
