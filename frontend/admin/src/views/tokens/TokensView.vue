<script setup lang="ts">
// Tokens - Token 用量统计
</script>

<template>
  <div class="tokens">
    <h1>Token 用量</h1>
    <p class="description">按用户、技能、时间统计 Token 消耗，管理配额</p>

    <div class="summary-cards">
      <div class="card">
        <div class="card-title">本月消耗</div>
        <div class="card-value">-- tokens</div>
      </div>
      <div class="card">
        <div class="card-title">预估成本</div>
        <div class="card-value">$ --</div>
      </div>
      <div class="card">
        <div class="card-title">配额使用</div>
        <div class="card-value">-- %</div>
      </div>
    </div>

    <div class="usage-table">
      <h3>使用明细</h3>
      <p>Token 使用明细功能开发中...</p>
    </div>
  </div>
</template>

<style scoped>
.tokens {
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

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.card-title {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.card-value {
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.usage-table {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.usage-table h3 {
  margin-bottom: 16px;
}
</style>
