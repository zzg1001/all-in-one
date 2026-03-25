import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchSkills, type Skill } from '@/api/skills'

export const useSkillsStore = defineStore('skills', () => {
  const skills = ref<Skill[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const searchQuery = ref('')
  const currentCategory = ref('all')

  const categories = computed(() => {
    const map = new Map<string, { name: string; count: number }>()
    map.set('all', { name: 'All Skills', count: skills.value.length })

    skills.value.forEach(skill => {
      const cat = skill.category || 'Uncategorized'
      if (map.has(cat)) {
        map.get(cat)!.count++
      } else {
        map.set(cat, { name: cat, count: 1 })
      }
    })

    return map
  })

  const filteredSkills = computed(() => {
    return skills.value.filter(skill => {
      const matchesCategory = currentCategory.value === 'all' || skill.category === currentCategory.value
      const matchesSearch = !searchQuery.value ||
        skill.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
        (skill.description && skill.description.toLowerCase().includes(searchQuery.value.toLowerCase()))
      return matchesCategory && matchesSearch
    })
  })

  async function loadSkills() {
    loading.value = true
    error.value = null
    try {
      skills.value = await fetchSkills()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
    } finally {
      loading.value = false
    }
  }

  function setCategory(category: string) {
    currentCategory.value = category
  }

  function setSearch(query: string) {
    searchQuery.value = query
  }

  return {
    skills,
    loading,
    error,
    searchQuery,
    currentCategory,
    categories,
    filteredSkills,
    loadSkills,
    setCategory,
    setSearch
  }
})
