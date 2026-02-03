import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

// 视图组件懒加载
const HotListView = () => import('../views/HotListView.vue')
const PushConfigView = () => import('../views/PushConfigView.vue')
const DataSourcesView = () => import('../views/DataSourcesView.vue')
const PushRulesView = () => import('../views/PushRulesView.vue')
const PushHistoryView = () => import('../views/PushHistoryView.vue')
const SchedulerView = () => import('../views/SchedulerView.vue')
const UserManagementView = () => import('../views/UserManagementView.vue')

const routes = [
    {
        path: '/',
        redirect: '/hotlist'
    },
    {
        path: '/hotlist',
        name: 'hotlist',
        component: HotListView,
        meta: { title: '热搜榜', subtitle: '实时聚合全网热点资讯', icon: 'fas fa-fire' }
    },
    {
        path: '/sources',
        name: 'sources',
        component: DataSourcesView,
        meta: { title: '数据源', subtitle: '查看数据源', icon: 'fas fa-rss' }
    },
    {
        path: '/push',
        name: 'push',
        component: PushConfigView,
        meta: { title: '推送配置', subtitle: '配置推送渠道', icon: 'fas fa-paper-plane', adminOnly: true }
    },
    {
        path: '/rules',
        name: 'rules',
        component: PushRulesView,
        meta: { title: '推送规则', subtitle: '配置推送规则', icon: 'fas fa-filter', adminOnly: true }
    },
    {
        path: '/history',
        name: 'history',
        component: PushHistoryView,
        meta: { title: '推送历史', subtitle: '查看推送记录', icon: 'fas fa-history', adminOnly: true }
    },
    {
        path: '/scheduler',
        name: 'scheduler',
        component: SchedulerView,
        meta: { title: '定时任务', subtitle: '管理定时任务', icon: 'fas fa-clock', adminOnly: true }
    },
    {
        path: '/users',
        name: 'users',
        component: UserManagementView,
        meta: { title: '用户管理', subtitle: '管理系统用户', icon: 'fas fa-users-cog', adminOnly: true }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
    const authStore = useAuthStore()

    // 检查是否需要管理员权限
    if (to.meta.adminOnly && !authStore.isAdmin) {
        next('/hotlist')
        return
    }

    next()
})

export default router
