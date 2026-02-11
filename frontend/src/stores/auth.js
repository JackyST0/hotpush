import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const API_BASE = '/api'

export const useAuthStore = defineStore('auth', () => {
    // State
    const token = ref(localStorage.getItem('hotpush_token') || '')
    const user = ref(null)
    const isAuthenticated = ref(false)

    // Getters
    const isAdmin = computed(() => user.value?.role === 'admin')

    const authHeaders = computed(() => {
        if (!token.value) return { 'Content-Type': 'application/json' }
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token.value}`
        }
    })

    // Actions
    const setToken = (newToken) => {
        token.value = newToken
        if (newToken) {
            localStorage.setItem('hotpush_token', newToken)
        } else {
            localStorage.removeItem('hotpush_token')
        }
    }

    const setUser = (userData) => {
        user.value = userData
        isAuthenticated.value = !!userData
    }

    const login = async (username, password) => {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        })
        const data = await response.json()

        if (data.success) {
            setToken(data.token)
            setUser(data.user)
            return { success: true }
        }
        return { success: false, message: data.detail || data.message || '登录失败' }
    }

    const checkAuth = async () => {
        if (!token.value) {
            isAuthenticated.value = false
            return false
        }

        try {
            const response = await fetch(`${API_BASE}/auth/check`, {
                headers: authHeaders.value
            })
            const data = await response.json()

            if (data.authenticated) {
                setUser(data.user)
                return true
            }
        } catch (e) {
            console.error('Auth check failed:', e)
        }

        isAuthenticated.value = false
        return false
    }

    const logout = () => {
        setToken('')
        setUser(null)
    }

    return {
        // State
        token,
        user,
        isAuthenticated,
        // Getters
        isAdmin,
        authHeaders,
        // Actions
        setToken,
        setUser,
        login,
        checkAuth,
        logout
    }
})
