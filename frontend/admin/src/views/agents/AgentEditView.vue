<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { agentsApi, skillsApi, type Agent, type Skill } from '@/api'
import Toast from '@/components/Toast.vue'

const route = useRoute()
const router = useRouter()
const toast = ref<InstanceType<typeof Toast> | null>(null)

const loading = ref(false)
const saving = ref(false)
const allSkills = ref<Skill[]>([])
const selectedSkillIds = ref<Set<string>>(new Set())
const skillSearchQuery = ref('')
const hoveredSkill = ref<Skill | null>(null)
const tooltipPos = ref({ x: 0, y: 0 })

const isCreating = computed(() => route.params.id === 'new')

const agent = ref<Partial<Agent>>({
  name: '',
  description: '',
  icon: '🤖',
  category: '通用助手',
  system_prompt: '',
  model: 'claude-opus-4-5',
  temperature: 0.7,
  max_tokens: 4096,
  status: 'draft',
  skills: []
})

const filteredSkills = computed(() => {
  if (!skillSearchQuery.value) return allSkills.value
  const q = skillSearchQuery.value.toLowerCase()
  return allSkills.value.filter(s =>
    s.name.toLowerCase().includes(q) ||
    s.description?.toLowerCase().includes(q)
  )
})

const icons = ['🤖', '🧠', '💡', '🎯', '🚀', '⚡', '🔧', '📊', '📝', '💻', '🌐', '🔍']
const categories = ['通用助手', 'HR', '销售', '采购', '行政', '财务', '技术', '自定义']

const loadData = async () => {
  loading.value = true
  try {
    allSkills.value = await skillsApi.getAll()
    if (!isCreating.value) {
      const data = await agentsApi.getById(route.params.id as string)
      agent.value = { ...data }
      selectedSkillIds.value = new Set(data.skills || [])
    }
  } catch (e) {
    toast.value?.error('加载失败')
  } finally {
    loading.value = false
  }
}

const toggleSkill = (skillId: string) => {
  if (selectedSkillIds.value.has(skillId)) {
    selectedSkillIds.value.delete(skillId)
  } else {
    selectedSkillIds.value.add(skillId)
  }
  selectedSkillIds.value = new Set(selectedSkillIds.value)
}

const showTooltip = (skill: Skill, e: MouseEvent) => {
  hoveredSkill.value = skill
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  tooltipPos.value = {
    x: Math.min(rect.left + rect.width / 2, window.innerWidth - 100),
    y: rect.top - 10
  }
}

const hideTooltip = () => { hoveredSkill.value = null }

const save = async () => {
  if (!agent.value.name) {
    toast.value?.warning('请输入名称')
    return
  }
  saving.value = true
  try {
    const data = { ...agent.value, skills: Array.from(selectedSkillIds.value) }
    if (isCreating.value) {
      await agentsApi.create(data as any)
    } else {
      await agentsApi.update(agent.value.id!, data as any)
    }
    toast.value?.show('保存成功', 'dark')
    setTimeout(() => router.push('/agent-manage'), 400)
  } catch (e) {
    toast.value?.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => loadData())
</script>

<template>
  <Toast ref="toast" />

  <!-- Tooltip -->
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="hoveredSkill" class="tooltip" :style="{ left: tooltipPos.x + 'px', top: tooltipPos.y + 'px' }">
        <div class="tooltip-name">{{ hoveredSkill.name }}</div>
        <div class="tooltip-desc">{{ hoveredSkill.description || '暂无描述' }}</div>
      </div>
    </Transition>
  </Teleport>

  <!-- 主容器 -->
  <div class="page">
    <!-- 顶部栏 -->
    <header class="header">
      <button class="header-btn back" @click="router.push('/agent-manage')">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M15 18l-6-6 6-6"/>
        </svg>
      </button>
      <div class="header-title">
        <span class="header-icon">{{ agent.icon }}</span>
        {{ isCreating ? '新建 Agent' : '编辑 Agent' }}
      </div>
      <button class="header-btn save" :disabled="saving" @click="save">
        {{ saving ? '保存中' : '保存' }}
      </button>
    </header>

    <!-- 内容区 -->
    <main class="content" v-if="!loading">
      <!-- 左侧：基本信息 -->
      <section class="panel main-panel">
        <div class="panel-title">基本信息</div>

        <div class="form-section">
          <!-- 图标选择 -->
          <div class="icon-select">
            <button
              v-for="ic in icons"
              :key="ic"
              class="icon-item"
              :class="{ active: agent.icon === ic }"
              @click="agent.icon = ic"
            >{{ ic }}</button>
          </div>

          <!-- 名称 & 分类 -->
          <div class="form-row">
            <div class="form-field flex2">
              <label>名称</label>
              <input v-model="agent.name" placeholder="输入 Agent 名称" />
            </div>
            <div class="form-field flex1">
              <label>分类</label>
              <select v-model="agent.category">
                <option v-for="c in categories" :key="c">{{ c }}</option>
              </select>
            </div>
          </div>

          <!-- 描述 -->
          <div class="form-field">
            <label>描述</label>
            <input v-model="agent.description" placeholder="简短描述这个 Agent" />
          </div>
        </div>

        <div class="divider"></div>

        <div class="panel-title">模型配置</div>
        <div class="form-section">
          <div class="form-row">
            <div class="form-field flex1">
              <label>模型</label>
              <select v-model="agent.model">
                <option value="claude-opus-4-5">Claude Opus 4.5</option>
                <option value="claude-sonnet-4">Claude Sonnet 4</option>
                <option value="claude-haiku">Claude Haiku</option>
              </select>
            </div>
            <div class="form-field flex1">
              <label>温度 <span class="label-value">{{ agent.temperature }}</span></label>
              <input type="range" v-model.number="agent.temperature" min="0" max="1" step="0.1" class="range" />
            </div>
            <div class="form-field flex1">
              <label>最大 Token</label>
              <input type="number" v-model.number="agent.max_tokens" min="256" max="8192" />
            </div>
          </div>

          <!-- 系统提示词 -->
          <div class="form-field">
            <label>系统提示词</label>
            <textarea v-model="agent.system_prompt" rows="4" placeholder="定义 Agent 的角色和行为规则..."></textarea>
          </div>

          <!-- 状态 -->
          <div class="form-field">
            <label>状态</label>
            <div class="status-toggle">
              <button :class="{ active: agent.status === 'draft' }" @click="agent.status = 'draft'">
                <span class="dot draft"></span> 草稿
              </button>
              <button :class="{ active: agent.status === 'active' }" @click="agent.status = 'active'">
                <span class="dot active"></span> 已发布
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- 右侧：技能绑定 -->
      <section class="panel skill-panel">
        <div class="panel-header">
          <div class="panel-title">绑定技能</div>
          <span class="skill-badge">{{ selectedSkillIds.size }} 已选</span>
        </div>

        <div class="skill-search">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
          <input v-model="skillSearchQuery" placeholder="搜索技能..." />
        </div>

        <div class="skill-grid">
          <div
            v-for="skill in filteredSkills"
            :key="skill.id"
            class="skill-card"
            :class="{ selected: selectedSkillIds.has(skill.id) }"
            @click="toggleSkill(skill.id)"
            @mouseenter="showTooltip(skill, $event)"
            @mouseleave="hideTooltip"
          >
            <span class="skill-icon">{{ skill.icon || '⚡' }}</span>
            <span class="skill-name">{{ skill.name }}</span>
            <div class="skill-check" v-if="selectedSkillIds.has(skill.id)">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </div>
          </div>
          <div v-if="!filteredSkills.length" class="skill-empty">暂无技能</div>
        </div>
      </section>
    </main>

    <!-- Loading -->
    <div v-else class="loading">
      <div class="spinner"></div>
    </div>
  </div>
</template>

<style scoped>
/* 页面容器 */
.page {
  height: 100%;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
  display: flex;
  flex-direction: column;
  position: relative;
}

/* 顶部栏 - 固定在顶部 */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  background: white;
  border-bottom: 1px solid rgba(0,0,0,0.08);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.header-btn:active {
  transform: scale(0.96);
}

.header-btn.back {
  background: transparent;
  color: #007aff;
  padding: 6px;
}
.header-btn.back:hover { background: rgba(0,122,255,0.08); }

.header-btn.back svg {
  width: 16px;
  height: 16px;
}

.header-btn.save {
  background: #007aff;
  color: white;
}
.header-btn.save:hover { background: #0066d6; }
.header-btn.save:disabled { opacity: 0.5; cursor: not-allowed; }

.header-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #1d1d1f;
}

.header-icon {
  font-size: 18px;
}

/* 内容区 */
.content {
  flex: 1;
  display: flex;
  gap: 20px;
  padding: 20px 24px;
  overflow: hidden;
  min-height: 0;
}

/* 面板 */
.panel {
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  overflow: hidden;
}

.main-panel {
  flex: 0 0 55%;
  padding: 24px;
  overflow-y: auto;
}

.skill-panel {
  flex: 1;
  min-width: 360px;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: #86868b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 16px;
}

.panel-header .panel-title {
  margin-bottom: 0;
}

.skill-badge {
  font-size: 12px;
  color: #007aff;
  background: rgba(0,122,255,0.1);
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: 500;
}

.divider {
  height: 1px;
  background: #f0f0f0;
  margin: 24px 0;
}

/* 表单 */
.form-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.form-field.flex1 { flex: 1; }
.form-field.flex2 { flex: 2; }

.form-field label {
  font-size: 13px;
  font-weight: 500;
  color: #1d1d1f;
}

.label-value {
  color: #007aff;
  margin-left: 4px;
}

.form-field input[type="text"],
.form-field input[type="number"],
.form-field select,
.form-field textarea {
  padding: 10px 14px;
  border: 1px solid #d2d2d7;
  border-radius: 10px;
  font-size: 15px;
  background: #fafafa;
  transition: all 0.2s;
}

.form-field input:focus,
.form-field select:focus,
.form-field textarea:focus {
  outline: none;
  border-color: #007aff;
  background: white;
  box-shadow: 0 0 0 3px rgba(0,122,255,0.1);
}

.form-field textarea {
  resize: none;
  line-height: 1.5;
}

/* Range 滑块 */
.range {
  -webkit-appearance: none;
  height: 6px;
  border-radius: 3px;
  background: #e5e5ea;
  margin-top: 4px;
}
.range::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: white;
  border: 1px solid #d2d2d7;
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
  cursor: pointer;
}

/* 图标选择 */
.icon-select {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.icon-item {
  width: 40px;
  height: 40px;
  border: 2px solid #e5e5ea;
  border-radius: 12px;
  background: white;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.2s;
}
.icon-item:hover {
  border-color: #007aff;
  transform: scale(1.05);
}
.icon-item.active {
  border-color: #007aff;
  background: rgba(0,122,255,0.08);
}

/* 状态切换 */
.status-toggle {
  display: flex;
  gap: 12px;
}

.status-toggle button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: 1px solid #d2d2d7;
  border-radius: 10px;
  background: white;
  font-size: 14px;
  color: #86868b;
  cursor: pointer;
  transition: all 0.2s;
}
.status-toggle button:hover {
  border-color: #007aff;
}
.status-toggle button.active {
  border-color: #007aff;
  color: #007aff;
  background: rgba(0,122,255,0.05);
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.dot.draft { background: #ff9500; }
.dot.active { background: #34c759; }

/* 技能搜索 */
.skill-search {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 12px 16px;
  padding: 8px 12px;
  background: #f5f5f7;
  border-radius: 10px;
}

.skill-search svg {
  color: #86868b;
  flex-shrink: 0;
}

.skill-search input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 14px;
  outline: none;
}

/* 技能网格 */
.skill-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  padding: 12px 16px;
  overflow-y: auto;
  align-content: start;
}

.skill-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 16px 8px;
  background: #f5f5f7;
  border: 2px solid transparent;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.skill-card:hover {
  background: #e8e8ed;
  transform: translateY(-2px);
}

.skill-card.selected {
  background: rgba(0,122,255,0.08);
  border-color: #007aff;
}

.skill-icon {
  font-size: 24px;
}

.skill-name {
  font-size: 11px;
  font-weight: 500;
  color: #1d1d1f;
  text-align: center;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.skill-check {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 18px;
  height: 18px;
  background: #007aff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.skill-empty {
  grid-column: 1 / -1;
  padding: 40px;
  text-align: center;
  color: #86868b;
  font-size: 14px;
}

/* Tooltip */
.tooltip {
  position: fixed;
  transform: translateX(-50%) translateY(-100%);
  max-width: 200px;
  padding: 10px 14px;
  background: #1d1d1f;
  border-radius: 10px;
  z-index: 9999;
  pointer-events: none;
}

.tooltip-name {
  font-size: 13px;
  font-weight: 600;
  color: white;
  margin-bottom: 4px;
}

.tooltip-desc {
  font-size: 12px;
  color: #a1a1a6;
  line-height: 1.4;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Loading */
.loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e5ea;
  border-top-color: #007aff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
