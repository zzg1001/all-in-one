/**
 * Skills Store - 技能状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { skillsApi, type Skill } from '@/api/index'

export const useSkillsStore = defineStore('skills', () => {
  // 状态
  const skills = ref<Skill[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const currentCategory = ref<string>('全部')
  const searchQuery = ref<string>('')

  // 计算属性 - 分类列表
  const categories = computed(() => {
    const tagSet = new Set<string>()
    tagSet.add('全部')
    skills.value.forEach(skill => {
      if (skill.tags) {
        skill.tags.forEach(tag => tagSet.add(tag))
      }
    })
    return Array.from(tagSet)
  })

  // 计算属性 - 过滤后的技能
  const filteredSkills = computed(() => {
    let result = skills.value

    // 分类过滤
    if (currentCategory.value && currentCategory.value !== '全部') {
      result = result.filter(skill =>
        skill.tags?.includes(currentCategory.value)
      )
    }

    // 搜索过滤
    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      result = result.filter(skill =>
        skill.name.toLowerCase().includes(query) ||
        (skill.description?.toLowerCase().includes(query))
      )
    }

    return result
  })

  // 加载技能列表
  async function loadSkills() {
    loading.value = true
    error.value = null

    try {
      skills.value = await skillsApi.getAll()
    } catch (e: any) {
      error.value = e.message || '加载技能失败'
    } finally {
      loading.value = false
    }
  }

  // 设置当前分类
  function setCategory(category: string) {
    currentCategory.value = category
  }

  // 设置搜索词
  function setSearch(query: string) {
    searchQuery.value = query
  }

  return {
    // 状态
    skills,
    loading,
    error,
    currentCategory,
    searchQuery,
    // 计算属性
    categories,
    filteredSkills,
    // 方法
    loadSkills,
    setCategory,
    setSearch,
  }
})
