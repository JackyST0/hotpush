import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'

const API_BASE = '/api'

export const useAppStore = defineStore('app', () => {
    // State
    const stats = ref({ sources_count: 0, configured_channels: 0 })
    const lastUpdate = ref('')
    const refreshTrigger = ref(0)

    // Actions
    const fetchStats = async () => {
        const authStore = useAuthStore()
        try {
            const response = await fetch(`${API_BASE}/stats`, {
                headers: authStore.authHeaders
            })
            if (response.ok) {
                stats.value = await response.json()
            }
        } catch (e) {
            console.error('Failed to fetch stats:', e)
        }
    }

    const updateLastRefresh = () => {
        lastUpdate.value = new Date().toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    const triggerRefresh = () => {
        refreshTrigger.value++
        updateLastRefresh()
    }

    return {
        stats,
        lastUpdate,
        refreshTrigger,
        fetchStats,
        updateLastRefresh,
        triggerRefresh
    }
})
