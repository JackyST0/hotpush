<template>
    <div class="min-h-screen flex items-center justify-center relative overflow-hidden">
        <!-- Mode Toggle -->
        <button
            @click="toggleDarkMode"
            class="mode-toggle absolute top-5 right-5 z-20"
            :title="isDarkMode ? '切换到白天模式' : '切换到黑夜模式'"
        >
            <i :class="isDarkMode ? 'fas fa-sun text-amber-400' : 'fas fa-moon text-amber-600'" class="text-sm"></i>
        </button>

        <div class="glass rounded-2xl p-8 w-full max-w-sm mx-4 relative z-10">
            <div class="text-center mb-8">
                <div class="inline-block animate-float">
                    <span class="text-5xl">🔥</span>
                </div>
                <h1 class="text-3xl font-semibold mt-4 text-white tracking-tight">HotPush</h1>
                <p class="text-gray-400 mt-2 text-sm font-light">热点聚合推送平台</p>
            </div>

            <form @submit.prevent="handleLogin" class="space-y-4">
                <div class="relative">
                    <input
                        type="text"
                        v-model="username"
                        placeholder="用户名"
                        class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none transition text-white placeholder-gray-500 text-sm"
                        :disabled="loading"
                    >
                    <i class="fas fa-user absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 text-sm"></i>
                </div>
                <div class="relative">
                    <input
                        type="password"
                        v-model="password"
                        placeholder="密码"
                        class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none transition text-white placeholder-gray-500 text-sm"
                        :disabled="loading"
                    >
                    <i class="fas fa-lock absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 text-sm"></i>
                </div>

                <!-- 记住我 -->
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2">
                        <label class="toggle-switch" style="transform: scale(0.7); transform-origin: left center;" @click="rememberMe = !rememberMe">
                            <div :class="['toggle-slider', rememberMe ? 'on' : 'off']">
                                <span class="toggle-label-on">开</span>
                                <span class="toggle-label-off">关</span>
                            </div>
                        </label>
                        <span class="text-xs text-gray-500">记住我</span>
                    </div>
                    <a href="#" @click.prevent="showForgotTip = true" class="text-xs text-gray-500 hover:text-white transition">忘记密码?</a>
                </div>

                <div v-if="error" class="text-red-400 text-xs text-center bg-red-500/10 py-2 px-3 rounded-lg">
                    <i class="fas fa-exclamation-circle mr-2"></i>{{ error }}
                </div>

                <div v-if="showForgotTip" class="text-amber-300 text-xs text-center bg-amber-500/10 py-2 px-3 rounded-lg">
                    <i class="fas fa-info-circle mr-2"></i>请联系管理员重置密码
                </div>

                <button
                    type="submit"
                    :disabled="loading"
                    class="w-full py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl font-semibold hover:opacity-90 transition disabled:opacity-50"
                >
                    <i v-if="loading" class="fas fa-spinner animate-spin mr-2"></i>
                    {{ loading ? '登录中...' : '进入系统' }}
                </button>
            </form>

            <!-- 注册链接 -->
            <div class="text-center mt-6">
                <span class="text-xs text-gray-500">没有账号? </span>
                <a href="#" @click.prevent="showRegister = true" class="text-xs text-amber-400 hover:text-amber-300 transition">点击注册</a>
            </div>
        </div>

        <!-- 注册模态框 -->
        <div v-if="showRegister" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50" @click.self="showRegister = false">
            <div class="glass rounded-2xl p-8 w-full max-w-sm mx-4">
                <div class="flex items-center justify-between mb-6">
                    <h2 class="text-xl font-semibold text-white">注册新账号</h2>
                    <button @click="showRegister = false" class="text-gray-500 hover:text-white transition">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <form @submit.prevent="handleRegister" class="space-y-4">
                    <div class="relative">
                        <input
                            type="text"
                            v-model="registerForm.username"
                            placeholder="用户名"
                            class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none transition text-white placeholder-gray-500 text-sm"
                        >
                    </div>
                    <div class="relative">
                        <input
                            type="password"
                            v-model="registerForm.password"
                            placeholder="密码"
                            class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none transition text-white placeholder-gray-500 text-sm"
                        >
                    </div>
                    <div class="relative">
                        <input
                            type="password"
                            v-model="registerForm.confirmPassword"
                            placeholder="确认密码"
                            class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none transition text-white placeholder-gray-500 text-sm"
                        >
                    </div>
                    <div v-if="registerError" class="text-red-400 text-xs text-center bg-red-500/10 py-2 px-3 rounded-lg">
                        <i class="fas fa-exclamation-circle mr-2"></i>{{ registerError }}
                    </div>
                    <button
                        type="submit"
                        :disabled="registerLoading"
                        class="w-full py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl font-semibold hover:opacity-90 transition disabled:opacity-50"
                    >
                        <i v-if="registerLoading" class="fas fa-spinner animate-spin mr-2"></i>
                        {{ registerLoading ? '注册中...' : '注册' }}
                    </button>
                </form>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useTheme } from '../composables/useTheme'
import { useAuthStore } from '../stores/auth'

const emit = defineEmits(['login-success'])

const { isDarkMode, toggleDarkMode } = useTheme()
const authStore = useAuthStore()

// 登录表单
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const rememberMe = ref(false)
const showForgotTip = ref(false)

// 注册表单
const showRegister = ref(false)
const registerForm = ref({ username: '', password: '', confirmPassword: '' })
const registerLoading = ref(false)
const registerError = ref('')

// 初始化时检查是否记住了用户名
onMounted(() => {
    const remembered = localStorage.getItem('hotpush_remember_me')
    if (remembered === 'true') {
        rememberMe.value = true
        username.value = localStorage.getItem('hotpush_remember_username') || ''
    }
})

const handleLogin = async () => {
    if (!username.value || !password.value) {
        error.value = '请输入用户名和密码'
        return
    }

    loading.value = true
    error.value = ''

    try {
        const result = await authStore.login(username.value, password.value)

        if (result.success) {
            // 处理"记住我"
            if (rememberMe.value) {
                localStorage.setItem('hotpush_remember_me', 'true')
                localStorage.setItem('hotpush_remember_username', username.value)
            } else {
                localStorage.removeItem('hotpush_remember_me')
                localStorage.removeItem('hotpush_remember_username')
            }
            emit('login-success')
        } else {
            error.value = result.message || '登录失败'
        }
    } catch (e) {
        error.value = e.message || '网络错误，请稍后重试'
    } finally {
        loading.value = false
    }
}

const handleRegister = async () => {
    if (!registerForm.value.username || !registerForm.value.password) {
        registerError.value = '请填写用户名和密码'
        return
    }
    if (registerForm.value.password !== registerForm.value.confirmPassword) {
        registerError.value = '两次密码输入不一致'
        return
    }
    if (registerForm.value.password.length < 6) {
        registerError.value = '密码长度至少6位'
        return
    }

    registerLoading.value = true
    registerError.value = ''

    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: registerForm.value.username,
                password: registerForm.value.password
            })
        })

        const data = await response.json()

        if (response.ok && data.success) {
            // 注册成功，自动登录
            authStore.setToken(data.token)
            authStore.setUser(data.user)
            showRegister.value = false
            registerForm.value = { username: '', password: '', confirmPassword: '' }
            emit('login-success')
        } else {
            registerError.value = data.detail || data.message || '注册失败'
        }
    } catch (e) {
        registerError.value = e.message || '网络错误，请稍后重试'
    } finally {
        registerLoading.value = false
    }
}
</script>

<style scoped>
@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-6px); }
}
.animate-float {
    animation: float 8s ease-in-out infinite;
}
</style>
