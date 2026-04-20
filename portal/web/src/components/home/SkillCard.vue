<script setup lang="ts">
import { computed } from 'vue'
import type { Skill } from '@/api/skills'

const props = defineProps<{
  skill: Skill
}>()

defineEmits<{
  (e: 'click'): void
}>()

// Generate stable pseudo-random values based on skill id
function seededRandom(seed: number): number {
  const x = Math.sin(seed) * 10000
  return x - Math.floor(x)
}

const repoName = computed(() => {
  const authors = ['cursor', 'anthropic', 'openai', 'meta', 'google', 'vercel', 'stripe']
  const seed = props.skill.id || 1
  const authorIndex = Math.floor(seededRandom(seed) * authors.length)
  const fileName = props.skill.name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')
  return `${authors[authorIndex]}/${fileName}`
})

const stars = computed(() => {
  const seed = (props.skill.id || 1) * 137
  const count = Math.floor(seededRandom(seed) * 900) + 100
  return count >= 1000 ? `${(count / 1000).toFixed(1)}k` : String(count)
})
</script>

<template>
  <div class="skill-card" @click="$emit('click')">
    <!-- Card Header -->
    <div class="card-header">
      <div class="card-dots">
        <span class="dot red"></span>
        <span class="dot yellow"></span>
        <span class="dot green"></span>
      </div>
      <span class="card-title mono">
        <span class="repo-dot"></span>
        {{ repoName }}
      </span>
      <span class="card-stars mono">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
        </svg>
        {{ stars }}
      </span>
    </div>

    <!-- Card Body -->
    <div class="card-body">
      <p class="skill-desc">{{ skill.description || 'No description available' }}</p>

      <div class="skill-command mono">
        <span class="cmd">$</span> run skill open {{ skill.name.toLowerCase().replace(/\s+/g, '-') }} && execute
      </div>
    </div>
  </div>
</template>

<style scoped>
.skill-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
}

.skill-card:hover {
  border-color: var(--accent-orange);
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  background: var(--bg-terminal);
  border-bottom: 1px solid var(--border-light);
  gap: 12px;
}

.card-dots {
  display: flex;
  gap: 6px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.dot.red { background: var(--dot-red); }
.dot.yellow { background: var(--dot-yellow); }
.dot.green { background: var(--dot-green); }

.card-title {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.repo-dot {
  width: 8px;
  height: 8px;
  background: var(--accent-red);
  border-radius: 50%;
  flex-shrink: 0;
}

.card-stars {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-muted);
}

.card-body {
  padding: 16px;
}

.skill-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.skill-command {
  font-size: 12px;
  color: var(--text-muted);
  padding: 8px 12px;
  background: var(--bg-terminal);
  border-radius: var(--radius-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
