import { createI18n } from 'vue-i18n'
import zh from './zh'
import en from './en'

// 获取浏览器语言或本地存储的语言偏好
function getDefaultLocale(): string {
  const stored = localStorage.getItem('locale')
  if (stored && ['zh', 'en'].includes(stored)) {
    return stored
  }
  const browserLang = navigator.language.toLowerCase()
  if (browserLang.startsWith('zh')) {
    return 'zh'
  }
  return 'en'
}

const i18n = createI18n({
  legacy: false, // 使用 Composition API
  locale: getDefaultLocale(),
  fallbackLocale: 'zh',
  messages: {
    zh,
    en
  }
})

export default i18n

// 切换语言
export function setLocale(locale: 'zh' | 'en') {
  i18n.global.locale.value = locale
  localStorage.setItem('locale', locale)
  document.documentElement.lang = locale
}

// 获取当前语言
export function getLocale(): string {
  return i18n.global.locale.value
}
