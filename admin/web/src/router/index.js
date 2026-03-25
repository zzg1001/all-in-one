import { createRouter, createWebHistory } from 'vue-router';
const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            redirect: '/dashboard'
        },
        {
            path: '/dashboard',
            name: 'dashboard',
            component: () => import('@/views/dashboard/DashboardView.vue'),
            meta: { title: '驾驶舱' }
        },
        {
            path: '/models',
            name: 'models',
            component: () => import('@/views/models/ModelsView.vue'),
            meta: { title: '模型配置' }
        },
        {
            path: '/permissions',
            name: 'permissions',
            component: () => import('@/views/permissions/PermissionsView.vue'),
            meta: { title: '权限管理' }
        },
        {
            path: '/tokens',
            name: 'tokens',
            component: () => import('@/views/tokens/TokensView.vue'),
            meta: { title: 'Token 用量' }
        },
        {
            path: '/apis',
            name: 'apis',
            component: () => import('@/views/apis/ApisView.vue'),
            meta: { title: '接口配置' }
        },
        {
            path: '/users',
            name: 'users',
            component: () => import('@/views/users/UsersView.vue'),
            meta: { title: '用户管理' }
        },
        {
            path: '/logs',
            name: 'logs',
            component: () => import('@/views/logs/LogsView.vue'),
            meta: { title: '日志审计' }
        },
        {
            path: '/ccswitch',
            name: 'ccswitch',
            component: () => import('@/views/ccswitch/CcswitchView.vue'),
            meta: { title: 'Ike Switch' }
        }
    ]
});
export default router;
//# sourceMappingURL=index.js.map