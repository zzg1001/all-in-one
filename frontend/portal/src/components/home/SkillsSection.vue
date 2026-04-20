<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import SkillCard from './SkillCard.vue'
import type { Skill } from '@/api/skills'

const props = defineProps<{
  skills: Skill[]
  categories: Map<string, { name: string; count: number }>
  loading: boolean
  error: string | null
  currentCategory: string
  searchQuery: string
}>()

const emit = defineEmits<{
  (e: 'update:currentCategory', value: string): void
  (e: 'update:searchQuery', value: string): void
  (e: 'select', skill: Skill): void
  (e: 'retry'): void
}>()

const localSearch = ref(props.searchQuery)

watch(() => props.searchQuery, (val) => {
  localSearch.value = val
})

function onSearchInput(e: Event) {
  const value = (e.target as HTMLInputElement).value
  localSearch.value = value
  emit('update:searchQuery', value)
}

function selectCategory(cat: string) {
  emit('update:currentCategory', cat)
}

const categoryList = computed(() => {
  return Array.from(props.categories.entries())
})
</script>

<template>
  <section class="skills-section">
    <div class="terminal-window">
      <!-- Window Header -->
      <div class="window-header">
        <div class="window-dots">
          <span class="dot red"></span>
          <span class="dot yellow"></span>
          <span class="dot green"></span>
        </div>
        <span class="window-title mono">skills --list</span>
        <span class="window-status mono">ready</span>
      </div>

      <!-- Window Body -->
      <div class="window-body">
        <!-- Section Title -->
        <h2 class="section-title serif">
          <span class="prompt">&gt;</span> Browse Agent Skills
        </h2>

        <!-- Filter Row -->
        <div class="filter-row">
          <span class="filter-label mono">Sort by:</span>

          <div class="filter-tabs">
            <button
              v-for="[key, data] in categoryList"
              :key="key"
              class="filter-tab mono"
              :class="{ active: currentCategory === key }"
              @click="selectCategory(key)"
            >
              <span v-if="currentCategory === key" class="check">✓</span>
              {{ key === 'all' ? 'Stars' : data.name }}
            </button>
            <button class="filter-tab mono enhance">Enhance</button>
          </div>

          <!-- Search -->
          <div class="search-box">
            <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/>
              <path d="M21 21l-4.35-4.35"/>
            </svg>
            <input
              type="text"
              class="search-input mono"
              placeholder="$ grep skill..."
              :value="localSearch"
              @input="onSearchInput"
            >
          </div>
        </div>

        <!-- Skills Grid -->
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner"></div>
          <span class="mono">Loading skills...</span>
        </div>

        <div v-else-if="error" class="error-state">
          <span class="error-icon">⚠️</span>
          <span class="mono">// Error: {{ error }}</span>
          <span class="mono hint">// Make sure backend is running at localhost:8000</span>
          <button class="retry-btn mono" @click="$emit('retry')">
            <span class="cmd">$</span> retry --fetch
          </button>
        </div>

        <div v-else-if="skills.length === 0" class="empty-state">
          <span class="mono">// No skills found matching your criteria</span>
        </div>

        <div v-else class="skills-grid">
          <SkillCard
            v-for="skill in skills"
            :key="skill.id"
            :skill="skill"
            @click="$emit('select', skill)"
          />
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.skills-section {
  padding: 0 24px 40px;
  max-width: var(--container-width);
  margin: 0 auto;
}

.terminal-window {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-md);
}

.window-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-terminal);
  border-bottom: 1px solid var(--border-light);
}

.window-dots {
  display: flex;
  gap: 8px;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.dot.red { background: var(--dot-red); }
.dot.yellow { background: var(--dot-yellow); }
.dot.green { background: var(--dot-green); }

.window-title {
  flex: 1;
  text-align: center;
  font-size: 13px;
  color: var(--text-muted);
}

.window-status {
  font-size: 12px;
  color: var(--text-muted);
}

.window-body {
  padding: 32px 40px;
}

.section-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 24px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.filter-label {
  font-size: 13px;
  color: var(--text-muted);
}

.filter-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.filter-tab:hover {
  border-color: var(--accent-orange);
  color: var(--accent-orange);
}

.filter-tab.active {
  background: var(--accent-orange);
  border-color: var(--accent-orange);
  color: white;
}

.filter-tab .check {
  font-size: 12px;
}

.filter-tab.enhance {
  color: var(--text-muted);
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  margin-left: auto;
}

.search-box:focus-within {
  border-color: var(--accent-orange);
}

.search-icon {
  color: var(--text-muted);
  flex-shrink: 0;
}

.search-input {
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  width: 180px;
  color: var(--text-primary);
}

.search-input::placeholder {
  color: var(--text-muted);
}

.skills-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
}

/* States */
.loading-state,
.error-state,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.error-icon {
  font-size: 40px;
  margin-bottom: 8px;
}

.hint {
  color: var(--text-muted);
  font-size: 13px;
}

.retry-btn {
  margin-top: 16px;
  padding: 10px 20px;
  background: var(--accent-orange);
  border: none;
  border-radius: var(--radius-sm);
  color: white;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.retry-btn:hover {
  background: #ea580c;
}

@media (max-width: 768px) {
  .skills-section {
    padding: 0 16px 24px;
  }

  .window-body {
    padding: 24px;
  }

  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }

  .search-box {
    margin-left: 0;
  }

  .skills-grid {
    grid-template-columns: 1fr;
  }
}
</style>
