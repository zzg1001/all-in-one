// Frontend Home application configuration

export const config = {
  // API base URL
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',

  // Server base URL (without /api)
  serverBaseUrl: import.meta.env.VITE_SERVER_BASE_URL || 'http://localhost:8000',

  // Portal URL (AI Agent / Skills)
  portalUrl: import.meta.env.VITE_PORTAL_URL || 'http://localhost:5173',

  // Admin URL (模型管理等)
  adminUrl: import.meta.env.VITE_ADMIN_URL || 'http://localhost:5174',
}

export default config
