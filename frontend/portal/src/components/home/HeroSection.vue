<script setup lang="ts">
import TrendChart from './TrendChart.vue'

defineProps<{
  skillCount: number
}>()
</script>

<template>
  <section class="hero">
    <div class="terminal-window">
      <!-- Window Header -->
      <div class="window-header">
        <div class="window-dots">
          <span class="dot red"></span>
          <span class="dot yellow"></span>
          <span class="dot green"></span>
        </div>
        <span class="window-title mono">skills.marketplace</span>
      </div>

      <!-- Window Body -->
      <div class="window-body">
        <div class="hero-grid">
          <!-- Left: Content -->
          <div class="hero-content">
            <div class="file-comment mono">// main.ts</div>

            <h1 class="hero-title serif">
              <span class="prompt">&gt;</span> Agent Skills<br>
              Marketplace<span class="cursor cursor-lg"></span>
            </h1>

            <p class="hero-subtitle mono">
              <span class="prompt">&gt;</span> for the open SKILL.md ecosystem
            </p>

            <!-- Stats Code Block -->
            <div class="stats-block">
              <div class="code-line mono">
                <span class="kw">const</span>
                <span class="var"> skills</span>
                <span class="op"> = </span>
                <span class="num">{{ skillCount.toLocaleString() }}</span>
                <span class="op">;</span>
              </div>
              <div class="code-line mono">
                <span class="cmt">// Discover open-source agent skills from GitHub</span>
              </div>
            </div>

            <!-- JSDoc Description -->
            <div class="desc-block mono">
              <div class="jsdoc-start">/**</div>
              <div class="jsdoc-line">* Search with AI semantics or keywords, browse by category, sort</div>
              <div class="jsdoc-line">by popularity. All skills use the open SKILL.md standard and are</div>
              <div class="jsdoc-line">ready to install</div>
              <div class="jsdoc-end">*/</div>
            </div>
          </div>

          <!-- Right: Chart -->
          <div class="hero-chart">
            <TrendChart />
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero {
  padding: 40px 24px;
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

.window-body {
  padding: 40px 48px;
}

.hero-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 60px;
  align-items: start;
}

.file-comment {
  font-size: 13px;
  color: var(--syntax-comment);
  margin-bottom: 16px;
}

.hero-title {
  font-size: 48px;
  font-weight: 700;
  line-height: 1.15;
  color: var(--text-primary);
  margin-bottom: 16px;
  letter-spacing: -0.02em;
}

.hero-subtitle {
  font-size: 15px;
  color: var(--text-secondary);
  margin-bottom: 32px;
}

.stats-block {
  background: var(--bg-terminal);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 20px 24px;
  margin-bottom: 24px;
}

.code-line {
  font-size: 15px;
  line-height: 1.6;
}

.code-line + .code-line {
  margin-top: 4px;
}

.desc-block {
  border-left: 3px solid var(--accent-orange);
  padding-left: 16px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.jsdoc-start,
.jsdoc-end {
  color: var(--accent-orange);
}

.jsdoc-line {
  color: var(--text-secondary);
}

.jsdoc-line::before {
  content: '* ';
  color: var(--accent-orange);
}

@media (max-width: 1024px) {
  .hero-grid {
    grid-template-columns: 1fr;
    gap: 40px;
  }

  .hero-chart {
    order: -1;
  }
}

@media (max-width: 768px) {
  .hero {
    padding: 24px 16px;
  }

  .window-body {
    padding: 24px;
  }

  .hero-title {
    font-size: 32px;
  }
}
</style>
