<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useSkillsStore } from '@/stores/skills'
import type { Skill } from '@/api/skills'
import config from '@/config'

import HeaderNav from '@/components/HeaderNav.vue'
import ManusBanner from '@/components/ManusBanner.vue'
import HeroSection from '@/components/HeroSection.vue'
import SkillsSection from '@/components/SkillsSection.vue'
import CategoriesSection from '@/components/CategoriesSection.vue'
import FloatingButton from '@/components/FloatingButton.vue'
import SkillModal from '@/components/SkillModal.vue'

const store = useSkillsStore()

// Modal state
const selectedSkill = ref<Skill | null>(null)
const modalVisible = ref(false)

// Computed
const skillCount = computed(() => store.skills.length)

// Methods
function openSkillModal(skill: Skill) {
  selectedSkill.value = skill
  modalVisible.value = true
}

function closeModal() {
  modalVisible.value = false
  setTimeout(() => {
    selectedSkill.value = null
  }, 300)
}

function executeSkill(skill: Skill) {
  window.open(`${config.portalUrl}/?tab=skills&skillId=${skill.id}`, '_blank')
  closeModal()
}

function selectCategory(category: string) {
  store.setCategory(category)
  // Scroll to skills section
  document.querySelector('.skills-section-wrapper')?.scrollIntoView({ behavior: 'smooth' })
}

// Load data
onMounted(() => {
  store.loadSkills()
})
</script>

<template>
  <div class="marketplace">
    <!-- Manus Banner -->
    <ManusBanner />

    <!-- Header -->
    <HeaderNav />

    <!-- Main Content -->
    <main class="main-content">
      <!-- Hero Section -->
      <HeroSection :skill-count="skillCount" />

      <!-- Skills Section -->
      <div class="skills-section-wrapper">
        <SkillsSection
          :skills="store.filteredSkills"
          :categories="store.categories"
          :loading="store.loading"
          :error="store.error"
          :current-category="store.currentCategory"
          :search-query="store.searchQuery"
          @update:current-category="store.setCategory"
          @update:search-query="store.setSearch"
          @select="openSkillModal"
          @retry="store.loadSkills"
        />
      </div>

      <!-- Categories Section -->
      <CategoriesSection
        :categories="store.categories"
        @select="selectCategory"
      />
    </main>

    <!-- Floating Button -->
    <FloatingButton :href="config.portalUrl" />

    <!-- Skill Modal -->
    <SkillModal
      :skill="selectedSkill"
      :visible="modalVisible"
      @close="closeModal"
      @execute="executeSkill"
    />
  </div>
</template>

<style scoped>
.marketplace {
  min-height: 100vh;
  background: var(--bg-secondary);
}

.main-content {
  padding-bottom: 80px;
}

.skills-section-wrapper {
  scroll-margin-top: 80px;
}
</style>
