<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { agentsApi, skillsApi, ccswitchApi, type Agent, type Skill, type CCConfig } from '@/api'
import Toast from '@/components/Toast.vue'

const route = useRoute()
const router = useRouter()
const toast = ref<InstanceType<typeof Toast> | null>(null)

const loading = ref(false)
const saving = ref(false)
const activeTab = ref<'basic' | 'model' | 'prompt' | 'skills'>('basic')
const allSkills = ref<Skill[]>([])
const availableModels = ref<CCConfig[]>([])
const selectedSkillIds = ref<Set<string>>(new Set())
const skillSearchQuery = ref('')

const isCreating = computed(() => route.params.id === 'new')

const agent = ref<Partial<Agent>>({
  name: '',
  description: '',
  icon: '🤖',
  category: '通用助手',
  system_prompt: '',
  model: '',
  temperature: 0.7,
  max_tokens: 4096,
  status: 'draft',
  skills: []
})

const filteredSkills = computed(() => {
  if (!skillSearchQuery.value) return allSkills.value
  const q = skillSearchQuery.value.toLowerCase()
  return allSkills.value.filter(s =>
    s.name.toLowerCase().includes(q) || s.description?.toLowerCase().includes(q)
  )
})

const icons = ['🤖', '🧠', '💡', '🎯', '🚀', '⚡', '🔧', '📊', '📝', '💻', '🌐', '🔍']
const categories = ['通用助手', 'HR', '销售', '采购', '行政', '财务', '技术', '自定义']

const currentModel = computed(() => {
  const m = availableModels.value.find(m => m.model_id === agent.value.model)
  return m?.name || '未选择'
})

const loadData = async () => {
  loading.value = true
  try {
    const [skills, models] = await Promise.all([
      skillsApi.getAll(),
      ccswitchApi.getAll(true)
    ])
    allSkills.value = skills
    availableModels.value = models

    if (isCreating.value && models.length > 0) {
      agent.value.model = models[0].model_id
    }

    if (!isCreating.value) {
      const data = await agentsApi.getById(route.params.id as string)
      agent.value = { ...data }
      // 只保留存在的技能ID
      const existingSkillIds = new Set(skills.map(s => s.id))
      const validSkillIds = (data.skills || []).filter((id: string) => existingSkillIds.has(id))
      selectedSkillIds.value = new Set(validSkillIds)
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

const save = async () => {
  if (!agent.value.name) {
    toast.value?.warning('请输入 Agent 名称')
    activeTab.value = 'basic'
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

  <div class="page" v-if="!loading">
    <!-- 顶部操作栏 -->
    <header class="page-header">
      <div class="header-left">
        <button class="btn-back" @click="router.push('/agent-manage')">
          <svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd"/></svg>
          返回
        </button>
        <div class="header-title">
          <span class="title-icon">{{ agent.icon }}</span>
          <span class="title-text">{{ agent.name || '新建 Agent' }}</span>
          <span class="title-status" :class="agent.status">{{ agent.status === 'active' ? '已发布' : '草稿' }}</span>
        </div>
      </div>
      <div class="header-right">
        <button class="btn-draft" v-if="agent.status === 'active'" @click="agent.status = 'draft'; save()">
          转为草稿
        </button>
        <button class="btn-publish" v-if="agent.status === 'draft'" :disabled="saving" @click="agent.status = 'active'; save()">
          发布
        </button>
        <button class="btn-save" :disabled="saving" @click="save">
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </div>
    </header>

    <div class="page-body">
      <!-- 左侧导航 -->
      <aside class="sidebar">
        <nav class="nav-menu">
          <div class="nav-item" :class="{ active: activeTab === 'basic' }" @click="activeTab = 'basic'">
            <span class="nav-icon">📋</span>
            <span class="nav-text">基本信息</span>
          </div>
          <div class="nav-item" :class="{ active: activeTab === 'model' }" @click="activeTab = 'model'">
            <span class="nav-icon">🤖</span>
            <span class="nav-text">模型配置</span>
          </div>
          <div class="nav-item" :class="{ active: activeTab === 'prompt' }" @click="activeTab = 'prompt'">
            <span class="nav-icon">📝</span>
            <span class="nav-text">系统提示词</span>
            <span class="nav-badge" v-if="agent.system_prompt">已配置</span>
          </div>
          <div class="nav-item" :class="{ active: activeTab === 'skills' }" @click="activeTab = 'skills'">
            <span class="nav-icon">⚡</span>
            <span class="nav-text">绑定技能</span>
            <span class="nav-badge">{{ selectedSkillIds.size }}</span>
          </div>
        </nav>
      </aside>

    <!-- 右侧内容 -->
    <main class="content">
      <!-- 基本信息 -->
      <div v-show="activeTab === 'basic'" class="panel">
        <div class="form-section">
          <div class="section-title">图标</div>
          <div class="icon-picker">
            <button v-for="ic in icons" :key="ic" :class="{ active: agent.icon === ic }" @click="agent.icon = ic">{{ ic }}</button>
          </div>
        </div>
        <div class="form-section">
          <div class="section-title">名称 <span class="required">*</span></div>
          <input v-model="agent.name" placeholder="给 Agent 起个名字" class="apple-input" />
        </div>
        <div class="form-section">
          <div class="section-title">分类</div>
          <div class="apple-select-group">
            <button v-for="c in categories" :key="c" :class="{ active: agent.category === c }" @click="agent.category = c">{{ c }}</button>
          </div>
        </div>
        <div class="form-section">
          <div class="section-title">描述</div>
          <input v-model="agent.description" placeholder="简单描述 Agent 的功能" class="apple-input" />
        </div>
      </div>

      <!-- 模型配置 -->
      <div v-show="activeTab === 'model'" class="panel">
        <div class="form-section">
          <div class="section-title">选择模型</div>
          <div class="model-cards">
            <div
              v-for="m in availableModels"
              :key="m.id"
              class="model-card"
              :class="{ active: agent.model === m.model_id }"
              @click="agent.model = m.model_id"
            >
              <div class="model-icon">🤖</div>
              <div class="model-name">{{ m.name }}</div>
              <div class="model-check" v-if="agent.model === m.model_id">✓</div>
            </div>
          </div>
          <div v-if="!availableModels.length" class="empty-hint">请先在模型配置中添加模型</div>
        </div>
        <div class="form-section">
          <div class="section-row">
            <div class="section-title">温度</div>
            <div class="section-value">{{ agent.temperature }}</div>
          </div>
          <input type="range" v-model.number="agent.temperature" min="0" max="1" step="0.1" class="apple-range" />
          <div class="range-hints"><span>精确</span><span>创意</span></div>
        </div>
        <div class="form-section">
          <div class="section-row">
            <div class="section-title">最大 Token</div>
            <input type="number" v-model.number="agent.max_tokens" min="256" max="8192" class="apple-input-small" />
          </div>
        </div>
      </div>

      <!-- 系统提示词 -->
      <div v-show="activeTab === 'prompt'" class="panel full-height">
        <div class="form-section full">
          <div class="section-title">系统提示词</div>
          <div class="section-hint">定义 Agent 的角色、能力和行为规范</div>
          <textarea v-model="agent.system_prompt" class="apple-textarea" placeholder="例如：你是一个专业的人力资源助手..."></textarea>
        </div>
      </div>

      <!-- 绑定技能 -->
      <div v-show="activeTab === 'skills'" class="panel full-height">
        <div class="form-section full">
          <div class="section-row">
            <div>
              <div class="section-title">绑定技能</div>
              <div class="section-hint">共 {{ filteredSkills.length }} 个技能</div>
            </div>
            <div class="search-box">
              <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="2" fill="none"/><path d="m21 21-4.35-4.35" stroke="currentColor" stroke-width="2"/></svg>
              <input v-model="skillSearchQuery" placeholder="搜索" />
            </div>
          </div>
          <div class="skills-cards">
            <div
              v-for="skill in filteredSkills"
              :key="skill.id"
              class="skill-card"
              :class="{ selected: selectedSkillIds.has(skill.id) }"
              @click="toggleSkill(skill.id)"
            >
              <div class="skill-header">
                <div class="skill-icon">{{ skill.icon || '⚡' }}</div>
                <div class="skill-name">{{ skill.name }}</div>
                <div class="skill-check" v-if="selectedSkillIds.has(skill.id)">✓</div>
              </div>
              <div class="skill-desc">{{ skill.description || '暂无描述' }}</div>
              <div class="skill-tooltip">
                <div class="tooltip-name">{{ skill.name }}</div>
                <div class="tooltip-desc">{{ skill.description || '暂无描述' }}</div>
              </div>
            </div>
            <div v-if="!filteredSkills.length" class="empty-hint">暂无技能</div>
          </div>
        </div>
      </div>
    </main>
    </div>
  </div>

  <!-- Loading -->
  <div v-else class="loading-page">
    <div class="spinner"></div>
  </div>
</template>

<style scoped>
.page {
  height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
  background: #f5f5f7;
  overflow: hidden;
}

/* 顶部操作栏 - Apple 风格 */
.page-header {
  height: 52px;
  background: rgba(255,255,255,0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0,0,0,0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
}
.title-icon { font-size: 22px; }
.title-text {
  font-size: 16px;
  font-weight: 600;
  color: #1d1d1f;
}
.title-status {
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}
.title-status.draft { background: #fff3cd; color: #856404; }
.title-status.active { background: #d4edda; color: #155724; }

.btn-back {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 7px 14px;
  border: none;
  border-radius: 8px;
  background: #f5f5f7;
  color: #1d1d1f;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-back:hover { background: #e8e8ed; }
.btn-back svg { width: 16px; height: 16px; }

.btn-draft {
  padding: 7px 16px;
  border: none;
  border-radius: 8px;
  background: #f5f5f7;
  color: #1d1d1f;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-draft:hover { background: #e8e8ed; }

.btn-publish {
  padding: 7px 16px;
  border: none;
  border-radius: 8px;
  background: #34c759;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-publish:hover { background: #2db84d; }
.btn-publish:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-save {
  padding: 7px 16px;
  border: none;
  border-radius: 8px;
  background: #007aff;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-save:hover { background: #0066d6; }
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }

/* 页面主体 */
.page-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 左侧边栏 - Apple 风格 */
.sidebar {
  width: 200px;
  background: rgba(255,255,255,0.8);
  backdrop-filter: blur(20px);
  border-right: 1px solid rgba(0,0,0,0.06);
  flex-shrink: 0;
  overflow: hidden;
}

/* 导航菜单 */
.nav-menu {
  padding: 12px 8px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  margin-bottom: 4px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.nav-item:hover { background: rgba(0,0,0,0.04); }
.nav-item.active {
  background: #007aff;
  color: #fff;
}
.nav-icon { font-size: 18px; flex-shrink: 0; }
.nav-text {
  font-size: 14px;
  font-weight: 500;
  flex-shrink: 0;
}
.nav-badge {
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(0,0,0,0.06);
  border-radius: 10px;
  color: #86868b;
  margin-left: auto;
}
.nav-item.active .nav-badge {
  background: rgba(255,255,255,0.25);
  color: #fff;
}

/* 右侧内容 - Apple 风格 */
.content {
  flex: 1;
  padding: 24px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f5f5f7;
}

.panel {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 0 0 1px rgba(0,0,0,0.04), 0 2px 8px rgba(0,0,0,0.04);
}
.panel.full-height {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

/* 表单区块 */
.form-section {
  margin-bottom: 24px;
}
.form-section:last-child { margin-bottom: 0; }
.form-section.full {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #1d1d1f;
  margin-bottom: 10px;
}
.section-hint {
  font-size: 12px;
  color: #86868b;
  margin-top: -6px;
  margin-bottom: 12px;
}
.section-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.section-value {
  font-size: 15px;
  font-weight: 500;
  color: #1d1d1f;
}
.required { color: #ff3b30; }

/* Apple 输入框 */
.apple-input {
  width: 100%;
  padding: 12px 16px;
  border: none;
  border-radius: 12px;
  background: #f5f5f7;
  font-size: 15px;
  color: #1d1d1f;
  box-sizing: border-box;
  transition: all 0.2s;
}
.apple-input:focus {
  outline: none;
  background: #fff;
  box-shadow: 0 0 0 4px rgba(0,125,250,0.15);
}
.apple-input::placeholder { color: #86868b; }

.apple-input-small {
  width: 100px;
  padding: 8px 12px;
  border: none;
  border-radius: 8px;
  background: #f5f5f7;
  font-size: 15px;
  color: #1d1d1f;
  text-align: right;
}
.apple-input-small:focus {
  outline: none;
  box-shadow: 0 0 0 4px rgba(0,125,250,0.15);
}

/* Apple 选择器组 */
.apple-select-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.apple-select-group button {
  padding: 8px 16px;
  border: none;
  border-radius: 20px;
  background: #f5f5f7;
  font-size: 13px;
  color: #1d1d1f;
  cursor: pointer;
  transition: all 0.2s;
}
.apple-select-group button:hover {
  background: #e8e8ed;
}
.apple-select-group button.active {
  background: #007aff;
  color: #fff;
}

/* 图标选择器 */
.icon-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.icon-picker button {
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 12px;
  background: #f5f5f7;
  font-size: 22px;
  cursor: pointer;
  transition: all 0.2s;
}
.icon-picker button:hover {
  background: #e8e8ed;
  transform: scale(1.05);
}
.icon-picker button.active {
  background: #007aff;
  box-shadow: 0 2px 8px rgba(0,122,255,0.3);
}

/* 模型卡片 */
.model-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.model-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: #f5f5f7;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}
.model-card:hover { background: #e8e8ed; }
.model-card.active {
  background: #e8f4ff;
  box-shadow: inset 0 0 0 2px #007aff;
}
.model-icon { font-size: 20px; }
.model-name { font-size: 14px; font-weight: 500; color: #1d1d1f; }
.model-check {
  position: absolute;
  right: 12px;
  color: #007aff;
  font-weight: 600;
}

/* Apple Range */
.apple-range {
  width: 100%;
  height: 4px;
  border: none;
  border-radius: 2px;
  -webkit-appearance: none;
  background: #e5e5ea;
}
.apple-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.2), 0 0 0 1px rgba(0,0,0,0.04);
  cursor: pointer;
}
.range-hints {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #86868b;
  margin-top: 8px;
}

/* Apple Textarea */
.apple-textarea {
  flex: 1;
  width: 100%;
  padding: 16px;
  border: none;
  border-radius: 12px;
  background: #f5f5f7;
  font-size: 15px;
  line-height: 1.6;
  color: #1d1d1f;
  resize: none;
  box-sizing: border-box;
}
.apple-textarea:focus {
  outline: none;
  background: #fff;
  box-shadow: 0 0 0 4px rgba(0,125,250,0.15);
}
.apple-textarea::placeholder { color: #86868b; }

/* 搜索框 */
.search-box {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #f5f5f7;
  border-radius: 10px;
  width: 160px;
}
.search-box svg {
  width: 14px;
  height: 14px;
  color: #86868b;
}
.search-box input {
  flex: 1;
  border: none;
  background: none;
  font-size: 13px;
  color: #1d1d1f;
  outline: none;
}
.search-box input::placeholder { color: #86868b; }

/* 技能卡片 - Apple 风格 */
.skills-cards {
  flex: 1;
  margin-top: 16px;
  padding-top: 80px;
  margin-top: -64px;
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  align-content: flex-start;
  overflow-y: auto;
  overflow-x: hidden;
}
.skill-card {
  width: 210px;
  padding: 16px;
  background: #fff;
  border: 1px solid #e5e5ea;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  box-sizing: border-box;
}
.skill-card:hover {
  border-color: #c5c5ca;
  background: #fafafa;
}
.skill-card.selected {
  border-color: #007aff;
  background: #f5f9ff;
}
.skill-card .skill-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.skill-card .skill-icon {
  width: 36px;
  height: 36px;
  background: #f5f5f7;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}
.skill-card.selected .skill-icon {
  background: #007aff;
}
.skill-card .skill-name {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: #1d1d1f;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.skill-card .skill-check {
  width: 20px;
  height: 20px;
  background: #007aff;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
}
.skill-card .skill-desc {
  font-size: 12px;
  color: #86868b;
  line-height: 1.5;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.skill-card .skill-tooltip {
  position: absolute;
  left: 50%;
  bottom: calc(100% + 8px);
  transform: translateX(-50%);
  width: 220px;
  padding: 12px 14px;
  background: #1d1d1f;
  color: #fff;
  font-size: 13px;
  line-height: 1.5;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.25);
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  z-index: 100;
  pointer-events: none;
}
.skill-card .skill-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 8px solid transparent;
  border-top-color: #1d1d1f;
}
.skill-card:hover .skill-tooltip {
  opacity: 1;
  visibility: visible;
}
.skill-tooltip .tooltip-name {
  font-weight: 600;
  margin-bottom: 6px;
  font-size: 14px;
}
.skill-tooltip .tooltip-desc {
  font-size: 13px;
  opacity: 0.9;
}

.empty-hint {
  text-align: center;
  padding: 32px;
  color: #86868b;
  font-size: 14px;
}

/* Loading */
.loading-page {
  height: calc(100vh - 64px);
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f7;
}
.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e5ea;
  border-top-color: #007aff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
