<script setup lang="ts">
import { ref, onMounted } from 'vue'

const chartData = ref([30, 45, 35, 55, 40, 65, 50, 75, 60, 85, 70, 95])
const labels = ['12/29', '1/5', '1/12', '1/19', '1/26', '2/2', '2/9', '2/16', '2/23', '3/2', '3/9', '3/16']

const animatedData = ref<number[]>(chartData.value.map(() => 0))

onMounted(() => {
  setTimeout(() => {
    animatedData.value = [...chartData.value]
  }, 300)
})
</script>

<template>
  <div class="chart-window">
    <!-- Window Header -->
    <div class="chart-header">
      <div class="chart-dots">
        <span class="dot red"></span>
        <span class="dot yellow"></span>
        <span class="dot green"></span>
      </div>
      <span class="chart-title mono">trend-analytics.tsx</span>
    </div>

    <!-- Chart Area -->
    <div class="chart-body">
      <!-- Y Axis -->
      <div class="y-axis mono">
        <span>30000</span>
        <span>20000</span>
        <span>10000</span>
        <span>0</span>
      </div>

      <!-- Chart -->
      <div class="chart-area">
        <svg class="chart-svg" viewBox="0 0 400 180" preserveAspectRatio="none">
          <!-- Grid lines -->
          <line x1="0" y1="45" x2="400" y2="45" stroke="#e8e8e8" stroke-width="1" />
          <line x1="0" y1="90" x2="400" y2="90" stroke="#e8e8e8" stroke-width="1" />
          <line x1="0" y1="135" x2="400" y2="135" stroke="#e8e8e8" stroke-width="1" />

          <!-- Area fill -->
          <path
            :d="getAreaPath(animatedData)"
            fill="url(#areaGradient)"
            class="area-path"
          />

          <!-- Line -->
          <path
            :d="getLinePath(animatedData)"
            fill="none"
            stroke="#fb923c"
            stroke-width="2"
            class="line-path"
          />

          <!-- Gradient definition -->
          <defs>
            <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="rgba(251, 146, 60, 0.3)" />
              <stop offset="100%" stop-color="rgba(251, 146, 60, 0.05)" />
            </linearGradient>
          </defs>
        </svg>

        <!-- X Axis Labels -->
        <div class="x-axis mono">
          <span v-for="(label, i) in labels" :key="i">{{ label }}</span>
        </div>
      </div>
    </div>

    <!-- Chart Footer -->
    <div class="chart-footer mono">
      Based on skill last push time, not same-day commit count
    </div>
  </div>
</template>

<script lang="ts">
function getLinePath(data: number[]): string {
  if (!data.length) return ''
  const width = 400
  const height = 180
  const padding = 10
  const max = 100

  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * (width - padding * 2) + padding
    const y = height - (value / max) * (height - padding * 2) - padding
    return `${x},${y}`
  })

  return `M ${points.join(' L ')}`
}

function getAreaPath(data: number[]): string {
  if (!data.length) return ''
  const width = 400
  const height = 180
  const padding = 10
  const max = 100

  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * (width - padding * 2) + padding
    const y = height - (value / max) * (height - padding * 2) - padding
    return `${x},${y}`
  })

  const firstX = padding
  const lastX = width - padding

  return `M ${firstX},${height - padding} L ${points.join(' L ')} L ${lastX},${height - padding} Z`
}

export default {
  methods: {
    getLinePath,
    getAreaPath
  }
}
</script>

<style scoped>
.chart-window {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.chart-header {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  background: var(--bg-terminal);
  border-bottom: 1px solid var(--border-light);
}

.chart-dots {
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

.chart-title {
  flex: 1;
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
  margin-right: 30px;
}

.chart-body {
  display: flex;
  padding: 20px;
  gap: 12px;
}

.y-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-muted);
  text-align: right;
  padding: 5px 0;
  min-width: 45px;
}

.chart-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chart-svg {
  width: 100%;
  height: 180px;
}

.area-path,
.line-path {
  transition: d 0.8s ease-out;
}

.x-axis {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 8px;
  padding: 0 5px;
}

.chart-footer {
  padding: 12px 16px;
  background: var(--bg-terminal);
  border-top: 1px solid var(--border-light);
  font-size: 11px;
  color: var(--text-muted);
  text-align: center;
}
</style>
