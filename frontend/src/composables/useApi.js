import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'

const API_BASE = '/api'

export function useApi() {
    const authStore = useAuthStore()

    // Generic API call
    const apiCall = async (endpoint, options = {}) => {
        const url = `${API_BASE}${endpoint}`
        const config = {
            ...options,
            headers: {
                ...authStore.authHeaders,
                ...options.headers
            }
        }

        const response = await fetch(url, config)

        if (response.status === 401) {
            authStore.logout()
            throw new Error('Unauthorized')
        }

        if (!response.ok) {
            const error = await response.json().catch(() => ({}))
            throw new Error(error.detail || error.message || 'Request failed')
        }

        return response.json()
    }

    // 兼容旧代码
    const currentUser = computed(() => authStore.user)
    const isAdmin = computed(() => authStore.isAdmin)

    return {
        API_BASE,
        apiCall,
        currentUser,
        isAdmin,
        // 兼容旧接口
        authToken: computed(() => authStore.token),
        getHeaders: () => authStore.authHeaders,
        setToken: (token) => authStore.setToken(token),
        setUser: (user) => authStore.setUser(user)
    }
}
