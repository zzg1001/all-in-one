<script setup lang="ts">
defineProps<{
  folder: string
  name: string
  count: number
}>()

defineEmits<{
  (e: 'click'): void
}>()
</script>

<template>
  <div class="category-card" @click="$emit('click')">
    <!-- Card Header -->
    <div class="card-header">
      <div class="folder-info mono">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" class="folder-icon">
          <path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/>
        </svg>
        <span>{{ folder }}/</span>
      </div>
      <div class="module-badge mono">
        <span class="module-dot"></span>
        module
      </div>
    </div>

    <!-- Card Body -->
    <div class="card-body mono">
      <div class="json-line">
        <span class="str">"name"</span><span class="op"> : </span><span class="str">"{{ name }}"</span>
      </div>
      <div class="json-line">
        <span class="str">"exports"</span><span class="op"> : </span><span class="num">{{ count }}</span><span class="cmt"> // skills</span>
      </div>

      <div class="card-command">
        <span class="cmd">$</span> cd {{ folder }} && ls
      </div>
    </div>
  </div>
</template>

<style scoped>
.category-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
}

.category-card:hover {
  border-color: var(--accent-orange);
  box-shadow: var(--shadow-md);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-light);
}

.folder-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-muted);
}

.folder-icon {
  color: var(--accent-orange);
}

.module-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--accent-green);
}

.module-dot {
  width: 6px;
  height: 6px;
  background: var(--accent-green);
  border-radius: 50%;
}

.card-body {
  padding: 16px;
}

.json-line {
  font-size: 13px;
  line-height: 1.6;
}

.json-line + .json-line {
  margin-top: 4px;
}

.card-command {
  margin-top: 12px;
  font-size: 12px;
  color: var(--text-muted);
}
</style>
