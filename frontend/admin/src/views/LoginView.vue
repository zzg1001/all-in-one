<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')

onMounted(async () => {
  if (authStore.isAuthenticated) {
    const redirect = route.query.redirect as string || '/dashboard'
    router.replace(redirect)
  }
})

async function handleLogin() {
  if (!username.value || !password.value) {
    errorMessage.value = '请输入用户名和密码'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  const success = await authStore.login(username.value, password.value)

  if (success) {
    const redirect = route.query.redirect as string || '/dashboard'
    router.replace(redirect)
  } else {
    errorMessage.value = authStore.error || '登录失败'
  }

  isLoading.value = false
}

function handleKeyup(event: KeyboardEvent) {
  if (event.key === 'Enter') {
    handleLogin()
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-container">
      <!-- Logo 和标题 -->
      <div class="login-header">
        <div class="logo">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <rect width="48" height="48" rx="12" fill="url(#admin-logo-gradient)" />
            <path d="M16 32V20L24 16L32 20V32L24 36L16 32Z" stroke="white" stroke-width="2" stroke-linejoin="round"/>
            <circle cx="24" cy="26" r="4" fill="white"/>
            <defs>
              <linearGradient id="admin-logo-gradient" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
                <stop stop-color="#0891b2"/>
                <stop offset="1" stop-color="#0d9488"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h1 class="title">Admin Console</h1>
        <p class="subtitle">管理员登录</p>
      </div>

      <!-- 登录表单 -->
      <form class="login-form" @submit.prevent="handleLogin">
        <div v-if="errorMessage" class="error-alert">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
            <path d="M8 4.5V8.5M8 11.5V11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span>{{ errorMessage }}</span>
        </div>

        <div class="form-group">
          <label for="username">用户名</label>
          <div class="input-wrapper">
            <svg class="input-icon" width="18" height="18" viewBox="0 0 18 18" fill="none">
              <circle cx="9" cy="5" r="3" stroke="currentColor" stroke-width="1.5"/>
              <path d="M3 15.5C3 12.462 5.686 10 9 10C12.314 10 15 12.462 15 15.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
            <input
              id="username"
              v-model="username"
              type="text"
              placeholder="请输入管理员账号"
              autocomplete="username"
              @keyup="handleKeyup"
            />
          </div>
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <div class="input-wrapper">
            <svg class="input-icon" width="18" height="18" viewBox="0 0 18 18" fill="none">
              <rect x="3" y="7" width="12" height="9" rx="2" stroke="currentColor" stroke-width="1.5"/>
              <path d="M6 7V5C6 3.343 7.343 2 9 2C10.657 2 12 3.343 12 5V7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              <circle cx="9" cy="11.5" r="1.5" fill="currentColor"/>
            </svg>
            <input
              id="password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="请输入密码"
              autocomplete="current-password"
              @keyup="handleKeyup"
            />
            <button
              type="button"
              class="toggle-password"
              @click="showPassword = !showPassword"
            >
              <svg v-if="showPassword" width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M2 9C2 9 4.5 4 9 4C13.5 4 16 9 16 9C16 9 13.5 14 9 14C4.5 14 2 9 2 9Z" stroke="currentColor" stroke-width="1.5"/>
                <circle cx="9" cy="9" r="2.5" stroke="currentColor" stroke-width="1.5"/>
              </svg>
              <svg v-else width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M2 9C2 9 4.5 4 9 4C13.5 4 16 9 16 9" stroke="currentColor" stroke-width="1.5"/>
                <path d="M3 15L15 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
        </div>

        <button type="submit" class="login-button" :disabled="isLoading">
          <span v-if="isLoading" class="loading-spinner"></span>
          <span v-else>登录</span>
        </button>
      </form>

      <div class="login-footer">
        <p class="help-text">
          仅限管理员访问
        </p>
      </div>
    </div>

    <div class="bg-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0fdfa 0%, #ccfbf1 100%);
  position: relative;
  overflow: hidden;
  padding: 20px;
}

.login-container {
  width: 100%;
  max-width: 400px;
  background: white;
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo {
  display: inline-flex;
  margin-bottom: 16px;
}

.title {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 8px 0;
}

.subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.error-alert {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 10px;
  color: #dc2626;
  font-size: 14px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 14px;
  color: #94a3b8;
  pointer-events: none;
}

.input-wrapper input {
  width: 100%;
  padding: 12px 14px 12px 44px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 15px;
  color: #0f172a;
  background: #f8fafc;
  transition: all 0.2s ease;
}

.input-wrapper input:focus {
  outline: none;
  border-color: #0891b2;
  background: white;
  box-shadow: 0 0 0 3px rgba(8, 145, 178, 0.1);
}

.input-wrapper input::placeholder {
  color: #94a3b8;
}

.toggle-password {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s ease;
}

.toggle-password:hover {
  color: #64748b;
}

.login-button {
  width: 100%;
  padding: 14px 24px;
  background: linear-gradient(135deg, #0891b2 0%, #0d9488 100%);
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 8px;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(8, 145, 178, 0.3);
}

.login-button:active:not(:disabled) {
  transform: translateY(0);
}

.login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.login-footer {
  margin-top: 24px;
  text-align: center;
}

.help-text {
  font-size: 13px;
  color: #94a3b8;
  margin: 0;
}

.bg-decoration {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.5;
}

.circle-1 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, rgba(8, 145, 178, 0.1) 0%, rgba(13, 148, 136, 0.1) 100%);
  top: -100px;
  right: -100px;
}

.circle-2 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(8, 145, 178, 0.1) 100%);
  bottom: -50px;
  left: -50px;
}

.circle-3 {
  width: 200px;
  height: 200px;
  background: linear-gradient(135deg, rgba(20, 184, 166, 0.1) 0%, rgba(34, 197, 94, 0.1) 100%);
  top: 50%;
  left: 10%;
  transform: translateY(-50%);
}
</style>
