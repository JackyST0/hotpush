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
            // detail 可能是字符串或数组（Pydantic 验证错误）
            let message = 'Request failed'
            if (typeof error.detail === 'string') {
                message = error.detail
            } else if (Array.isArray(error.detail)) {
                message = error.detail
                    .map(e => {
                        let msg = e.msg || e.message || ''
                        // 去掉 Pydantic 的技术前缀
                        msg = msg.replace(/^Value error,\s*/i, '')
                        // 常见英文错误翻译为中文
                        msg = msg.replace(/^Field required$/i, '缺少必填字段')
                        msg = msg.replace(/^String should have at least \d+ characters?$/i, '内容长度不足')
                        return msg
                    })
                    .filter(Boolean)
                    .join('; ')
            } else if (error.message) {
                message = error.message
            }
            throw new Error(message)
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
