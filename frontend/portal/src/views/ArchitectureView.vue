<script setup lang="ts">
import AgentArchitecture from '@/components/agent/AgentArchitecture.vue'
</script>

<template>
  <div class="architecture-page">
    <AgentArchitecture />
  </div>
</template>

<style scoped>
.architecture-page {
  position: fixed;
  top: 0;
  left: 60px;
  right: 0;
  bottom: 0;
  width: calc(100vw - 60px);
  height: 100vh;
  overflow: hidden;
}
</style>
