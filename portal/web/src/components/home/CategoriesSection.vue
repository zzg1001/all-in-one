<script setup lang="ts">
import CategoryCard from './CategoryCard.vue'

defineProps<{
  categories: Map<string, { name: string; count: number }>
}>()

defineEmits<{
  (e: 'select', category: string): void
}>()

// Predefined categories with proper display info
const categoryConfig: Record<string, { folder: string; displayName: string }> = {
  'Tools': { folder: 'tools', displayName: 'Tools' },
  'Business': { folder: 'business', displayName: 'Business' },
  'Development': { folder: 'development', displayName: 'Development' },
  'Data & AI': { folder: 'data-ai', displayName: 'Data & AI' },
  'Testing & Security': { folder: 'testing-security', displayName: 'Testing & Security' },
  'DevOps': { folder: 'devops', displayName: 'DevOps' },
  'Documentation': { folder: 'documentation', displayName: 'Documentation' },
  'Content & Media': { folder: 'content-media', displayName: 'Content & Media' },
  'Research': { folder: 'research', displayName: 'Research' },
  'Lifestyle': { folder: 'lifestyle', displayName: 'Lifestyle' },
  'Databases': { folder: 'databases', displayName: 'Databases' },
  'Blockchain': { folder: 'blockchain', displayName: 'Blockchain' },
}

function getConfig(name: string) {
  return categoryConfig[name] || {
    folder: name.toLowerCase().replace(/\s+/g, '-').replace(/[&]/g, ''),
    displayName: name
  }
}
</script>

<template>
  <section id="categories" class="categories-section">
    <div class="terminal-window">
      <!-- Window Header -->
      <div class="window-header">
        <div class="window-dots">
          <span class="dot red"></span>
          <span class="dot yellow"></span>
          <span class="dot green"></span>
        </div>
        <span class="window-title mono">categories.json</span>
        <span class="window-status mono">ready</span>
      </div>

      <!-- Window Body -->
      <div class="window-body">
        <!-- Section Title -->
        <h2 class="section-title serif">
          <span class="prompt">&gt;</span> Browse by Category
        </h2>

        <p class="section-subtitle mono">
          <span class="cmd">$</span> Explore agent skills organized by their primary use case
        </p>

        <!-- Categories Grid -->
        <div class="categories-grid">
          <CategoryCard
            v-for="[key, data] in categories"
            :key="key"
            v-show="key !== 'all'"
            :folder="getConfig(data.name).folder"
            :name="getConfig(data.name).displayName"
            :count="data.count"
            @click="$emit('select', key)"
          />
        </div>

        <!-- Bottom Navigation -->
        <div class="bottom-nav">
          <div class="nav-hint mono">
            <span class="cmd">$</span> cd /ca<span class="cursor-inline">|</span>
          </div>
          <button class="nav-btn mono">
            <span class="cmd">$</span> cd <span class="arrow-up">⬆</span> top
          </button>
          <div class="nav-hint mono">
            ...s -la <span class="arrow-right">→</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.categories-section {
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
  margin-bottom: 12px;
}

.section-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 32px;
}

.categories-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 40px;
}

.bottom-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.nav-hint {
  font-size: 13px;
  color: var(--text-muted);
}

.cursor-inline {
  color: var(--accent-orange);
  animation: blink 1s infinite;
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--bg-primary);
  border: 1px solid var(--accent-orange);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--accent-orange);
  cursor: pointer;
  transition: all 0.15s;
}

.nav-btn:hover {
  background: var(--accent-orange);
  color: white;
}

.arrow-up {
  font-size: 11px;
}

.arrow-right {
  color: var(--accent-orange);
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

@media (max-width: 1200px) {
  .categories-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 900px) {
  .categories-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .categories-section {
    padding: 0 16px 24px;
  }

  .window-body {
    padding: 24px;
  }

  .categories-grid {
    grid-template-columns: 1fr;
  }

  .bottom-nav {
    flex-wrap: wrap;
  }
}
</style>
