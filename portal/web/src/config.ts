// Application configuration

export const config = {
  // API base URL - change this to your backend server address
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',

  // Server base URL (without /api)
  serverBaseUrl: import.meta.env.VITE_SERVER_BASE_URL || 'http://localhost:8000',

  // WebSocket URL
  wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',

  // Home page URL
  homeUrl: import.meta.env.VITE_HOME_URL || 'http://localhost:5175',

  // Admin URL
  adminUrl: import.meta.env.VITE_ADMIN_URL || 'http://localhost:5174',
}

export default config
