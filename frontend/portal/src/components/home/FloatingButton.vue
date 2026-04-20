<script setup lang="ts">
defineProps<{
  href?: string
}>()
</script>

<template>
  <a :href="href || '#'" class="fab" target="_blank">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <circle cx="12" cy="12" r="10"/>
      <path d="M12 6v6l4 2"/>
    </svg>
    <span class="mono">Run any Skill with one click</span>
  </a>
</template>

<style scoped>
.fab {
  position: fixed;
  bottom: 32px;
  right: 32px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 24px;
  background: var(--text-primary);
  color: white;
  border-radius: 50px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: var(--shadow-lg);
  transition: all 0.3s;
  z-index: 90;
}

.fab:hover {
  transform: translateY(-3px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25);
}

.fab svg {
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .fab {
    bottom: 20px;
    right: 20px;
    padding: 12px 20px;
    font-size: 13px;
  }

  .fab span {
    display: none;
  }

  .fab svg {
    width: 24px;
    height: 24px;
  }
}
</style>
