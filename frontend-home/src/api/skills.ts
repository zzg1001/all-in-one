const API_BASE = '/api'

export interface Skill {
  id: number
  name: string
  description?: string
  category?: string
  system_prompt?: string
  created_at?: string
  updated_at?: string
}

export async function fetchSkills(): Promise<Skill[]> {
  const response = await fetch(`${API_BASE}/skills`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

export async function fetchSkillById(id: number): Promise<Skill> {
  const response = await fetch(`${API_BASE}/skills/${id}`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}
