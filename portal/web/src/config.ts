// Application configuration

export const config = {
  // API base URL - 统一后端服务
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api',

  // Server base URL (without /api)
  serverBaseUrl: import.meta.env.VITE_SERVER_BASE_URL || 'http://localhost:8001',

  // WebSocket URL
  wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8001',

  // 首页 URL（现在是同一个应用内的路由）
  homeUrl: '/',

  // Portal URL (当前应用)
  portalUrl: '',
}

export default config
