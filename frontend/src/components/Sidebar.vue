<template>
    <aside class="w-60 glass border-r border-white/5 flex flex-col">
        <!-- Logo -->
        <div class="p-6">
            <div class="flex items-center space-x-3">
                <span class="text-3xl">🔥</span>
                <div>
                    <h1 class="text-lg font-bold text-white">HotPush</h1>
                    <p class="text-xs text-gray-500">热点聚合推送平台</p>
                </div>
            </div>
        </div>

        <!-- Navigation -->
        <nav class="flex-1 px-3 space-y-1">
            <RouterLink
                v-for="item in visibleMenuItems"
                :key="item.path"
                :to="item.path"
                :class="[
                    'sidebar-item w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition',
                    isActive(item.path) ? 'active' : 'hover:bg-white/5'
                ]"
            >
                <div :class="['icon-wrapper w-8 h-8 rounded-lg flex items-center justify-center', isActive(item.path) ? '' : 'bg-white/5']">
                    <i :class="[item.icon, 'text-sm', isActive(item.path) ? 'text-amber-400' : 'text-gray-500']"></i>
                </div>
                <span :class="['text-sm font-medium', isActive(item.path) ? 'text-white' : 'text-gray-400']">
                    {{ item.name }}
                </span>
            </RouterLink>
        </nav>

        <!-- Stats -->
        <div class="p-4 border-t border-white/5">
            <div class="grid grid-cols-2 gap-2 text-center">
                <div class="glass rounded-lg p-3">
                    <div class="text-lg font-bold text-white">{{ stats?.sources_count || 0 }}</div>
                    <div class="text-xs text-gray-500">数据源</div>
                </div>
                <div class="glass rounded-lg p-3">
                    <div class="text-lg font-bold text-white">{{ stats?.configured_channels || 0 }}</div>
                    <div class="text-xs text-gray-500">推送渠道</div>
                </div>
            </div>
        </div>

        <!-- User Info -->
        <div class="p-4 border-t border-white/5">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <div class="w-9 h-9 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 flex items-center justify-center text-white font-bold text-sm">
                        {{ authStore.user?.username?.[0]?.toUpperCase() || 'U' }}
                    </div>
                    <div>
                        <div class="text-sm font-medium text-white">{{ authStore.user?.username || 'User' }}</div>
                        <div class="text-xs text-gray-500">{{ authStore.isAdmin ? '管理员' : '普通用户' }}</div>
                    </div>
                </div>
                <button
                    @click="$emit('logout')"
                    class="text-gray-500 hover:text-red-400 transition"
                    title="退出登录"
                >
                    <i class="fas fa-sign-out-alt"></i>
                </button>
            </div>
        </div>

        <!-- Footer -->
        <div class="p-4 border-t border-white/5 text-center">
            <a href="https://github.com/JackyST0/hotpush" target="_blank" class="text-xs text-gray-600 hover:text-gray-400 transition">
                <i class="fab fa-github mr-1"></i>@JackyST0
            </a>
        </div>
    </aside>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useAppStore } from '../stores/app'

defineProps({
    stats: Object
})

defineEmits(['logout'])

const route = useRoute()
const authStore = useAuthStore()
const appStore = useAppStore()

// 组件挂载时获取统计信息
onMounted(() => {
    appStore.fetchStats()
})

const menuItems = [
    { path: '/hotlist', name: '热搜榜', icon: 'fas fa-fire', adminOnly: false },
    { path: '/sources', name: '数据源', icon: 'fas fa-rss', adminOnly: false },
    { path: '/push', name: '推送配置', icon: 'fas fa-paper-plane', adminOnly: true },
    { path: '/rules', name: '推送规则', icon: 'fas fa-filter', adminOnly: true },
    { path: '/history', name: '推送历史', icon: 'fas fa-history', adminOnly: true },
    { path: '/scheduler', name: '定时任务', icon: 'fas fa-clock', adminOnly: true },
    { path: '/users', name: '用户管理', icon: 'fas fa-users-cog', adminOnly: true }
]

const visibleMenuItems = computed(() => {
    return menuItems.filter(item => !item.adminOnly || authStore.isAdmin)
})

const isActive = (path) => {
    return route.path === path
}
</script>
