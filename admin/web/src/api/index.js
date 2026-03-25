// Admin API Configuration and Services
import config from '@/config';
const API_BASE_URL = config.apiBaseUrl;
// Generic fetch wrapper
async function request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }
    if (response.status === 204) {
        return undefined;
    }
    return response.json();
}
export const dashboardApi = {
    getStats: () => request('/dashboard/stats'),
    getTrends: (days = 7) => request(`/dashboard/trends?days=${days}`),
};
export const modelsApi = {
    getAll: () => request('/models'),
    getById: (id) => request(`/models/${id}`),
    create: (data) => request('/models', {
        method: 'POST',
        body: JSON.stringify(data),
    }),
    update: (id, data) => request(`/models/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
    }),
    delete: (id) => request(`/models/${id}`, { method: 'DELETE' }),
    test: (id) => request(`/models/${id}/test`, { method: 'POST' }),
};
export const tokensApi = {
    getSummary: (startDate, endDate) => {
        const params = new URLSearchParams();
        if (startDate)
            params.append('start_date', startDate);
        if (endDate)
            params.append('end_date', endDate);
        return request(`/tokens/summary?${params}`);
    },
    getUsage: (page = 1, limit = 50) => request(`/tokens/usage?page=${page}&limit=${limit}`),
};
export const usersApi = {
    getAll: () => request('/users'),
    getById: (id) => request(`/users/${id}`),
    create: (data) => request('/users', {
        method: 'POST',
        body: JSON.stringify(data),
    }),
    update: (id, data) => request(`/users/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
    }),
    delete: (id) => request(`/users/${id}`, { method: 'DELETE' }),
};
export const logsApi = {
    getAll: (type, page = 1, limit = 50) => {
        const params = new URLSearchParams();
        if (type)
            params.append('type', type);
        params.append('page', page.toString());
        params.append('limit', limit.toString());
        return request(`/logs?${params}`);
    },
};
export const ccswitchApi = {
    getAll: (isActive) => {
        const params = isActive !== undefined ? `?is_active=${isActive}` : '';
        return request(`/ccswitch${params}`);
    },
    getById: (id) => request(`/ccswitch/${id}`),
    create: (data) => request('/ccswitch', {
        method: 'POST',
        body: JSON.stringify(data),
    }),
    update: (id, data) => request(`/ccswitch/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
    }),
    delete: (id) => request(`/ccswitch/${id}`, { method: 'DELETE' }),
    test: (id) => request(`/ccswitch/${id}/test`, { method: 'POST' }),
    toggle: (id) => request(`/ccswitch/${id}/toggle`, { method: 'POST' }),
    copy: (id) => request(`/ccswitch/${id}/copy`, { method: 'POST' }),
    export: (id) => request(`/ccswitch/${id}/export`),
    exportAll: () => request('/ccswitch/export/all'),
    import: (data) => request('/ccswitch/import', {
        method: 'POST',
        body: JSON.stringify(data),
    }),
};
// Export all APIs
export default {
    dashboard: dashboardApi,
    models: modelsApi,
    tokens: tokensApi,
    users: usersApi,
    logs: logsApi,
    ccswitch: ccswitchApi,
};
//# sourceMappingURL=index.js.map