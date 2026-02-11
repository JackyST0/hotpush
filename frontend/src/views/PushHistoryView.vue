<template>
    <div>
        <!-- Stats Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div class="glass rounded-xl p-5 text-center">
                <div class="text-3xl font-bold text-white">{{ historyStats.total || 0 }}</div>
                <div class="text-sm text-gray-500 mt-1">总推送次数</div>
            </div>
            <div class="glass rounded-xl p-5 text-center">
                <div class="text-3xl font-bold text-green-400">{{ historyStats.success || 0 }}</div>
                <div class="text-sm text-gray-500 mt-1">成功</div>
            </div>
            <div class="glass rounded-xl p-5 text-center">
                <div class="text-3xl font-bold text-red-400">{{ historyStats.failed || 0 }}</div>
                <div class="text-sm text-gray-500 mt-1">失败</div>
            </div>
            <div class="glass rounded-xl p-5 text-center">
                <div class="text-3xl font-bold text-amber-300">{{ historyStats.success_rate || 0 }}%</div>
                <div class="text-sm text-gray-500 mt-1">成功率</div>
            </div>
        </div>

        <!-- History List -->
        <div class="glass rounded-2xl overflow-hidden">
            <div class="p-6 border-b border-white/10 flex items-center justify-between">
                <div>
                    <h3 class="font-bold text-xl text-white">推送历史</h3>
                    <p class="text-gray-500 text-sm mt-2">最近的推送记录</p>
                </div>
                <button
                    v-if="isAdmin"
                    @click="cleanupHistory"
                    class="px-4 py-2 text-sm glass rounded-lg text-gray-300 hover:text-white hover:bg-white/10 transition"
                >
                    <i class="fas fa-broom mr-2"></i>清理旧记录
                </button>
            </div>
            <div v-if="loading" class="p-12 text-center">
                <i class="fas fa-spinner animate-spin text-2xl text-amber-400"></i>
                <p class="mt-2 text-gray-400">加载中...</p>
            </div>
            <div v-else-if="pushHistory.length === 0" class="p-12 text-center">
                <div class="text-6xl mb-4">📭</div>
                <p class="text-gray-500">暂无推送记录</p>
            </div>
            <div v-else class="divide-y divide-white/5">
                <div v-for="item in pushHistory" :key="item.id" class="p-5 hover:bg-white/5 transition">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-4">
                            <div :class="['w-10 h-10 rounded-xl flex items-center justify-center', item.status === 'success' ? 'bg-amber-500/20' : 'bg-red-500/20']">
                                <i :class="['text-lg', item.status === 'success' ? 'fas fa-check text-amber-300' : 'fas fa-times text-red-400']"></i>
                            </div>
                            <div>
                                <div class="font-medium text-white">{{ item.title }}</div>
                                <div class="text-sm text-gray-500">
                                    <span class="mr-3"><i class="fas fa-bell mr-1"></i>{{ item.channel }}</span>
                                    <span class="mr-3"><i class="fas fa-rss mr-1"></i>{{ item.source }}</span>
                                    <span><i class="fas fa-list mr-1"></i>{{ item.item_count }} 条</span>
                                </div>
                            </div>
                        </div>
                        <div class="text-sm text-gray-500">
                            {{ formatDateTime(item.pushed_at) }}
                        </div>
                    </div>
                    <div v-if="item.error_message" class="mt-2 text-sm text-red-400 bg-red-500/10 px-4 py-2 rounded-lg">
                        <i class="fas fa-exclamation-circle mr-2"></i>{{ item.error_message }}
                    </div>
                </div>
            </div>
            <!-- Pagination -->
            <div v-if="historyTotal > historyLimit" class="p-4 border-t border-white/10 flex items-center justify-between">
                <div class="text-sm text-gray-500">共 {{ historyTotal }} 条记录</div>
                <div class="flex items-center space-x-2">
                    <button
                        @click="prevPage"
                        :disabled="historyOffset === 0"
                        class="px-3 py-1.5 text-sm glass rounded-lg text-gray-300 hover:text-white transition disabled:opacity-50"
                    >
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    <span class="text-sm text-gray-400">{{ currentPage }} / {{ totalPages }}</span>
                    <button
                        @click="nextPage"
                        :disabled="historyOffset + historyLimit >= historyTotal"
                        class="px-3 py-1.5 text-sm glass rounded-lg text-gray-300 hover:text-white transition disabled:opacity-50"
                    >
                        <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
            </div>
        </div>
        <!-- 确认模态框 -->
        <div v-if="showConfirmModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div class="glass rounded-2xl w-full max-w-sm overflow-hidden">
                <div class="p-6">
                    <div class="flex items-start space-x-4">
                        <div class="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center flex-shrink-0">
                            <i class="fas fa-exclamation-triangle text-amber-400"></i>
                        </div>
                        <div class="flex-1">
                            <h3 class="font-semibold text-white">清理旧记录</h3>
                            <p class="text-gray-400 text-sm mt-1">确定要清理7天前的推送历史吗？</p>
                        </div>
                    </div>
                </div>
                <div class="px-6 pb-5 flex justify-end space-x-3">
                    <button
                        @click="showConfirmModal = false"
                        class="px-4 py-2 text-sm text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition"
                    >
                        取消
                    </button>
                    <button
                        @click="doCleanup"
                        class="px-4 py-2 text-sm bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-lg hover:opacity-90 transition font-medium"
                    >
                        确定
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useApi } from '../composables/useApi'
import { useToast } from '../composables/useToast'

const { apiCall, currentUser } = useApi()
const { showToast } = useToast()

const loading = ref(false)
const pushHistory = ref([])
const historyStats = ref({})
const historyOffset = ref(0)
const historyLimit = ref(20)
const historyTotal = ref(0)
const showConfirmModal = ref(false)

const isAdmin = computed(() => currentUser.value?.role === 'admin')
const currentPage = computed(() => Math.floor(historyOffset.value / historyLimit.value) + 1)
const totalPages = computed(() => Math.ceil(historyTotal.value / historyLimit.value))

const formatDateTime = (dateStr) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    })
}

const fetchHistory = async () => {
    loading.value = true
    try {
        const data = await apiCall(`/history?offset=${historyOffset.value}&limit=${historyLimit.value}`)
        pushHistory.value = data.history || []
        historyTotal.value = data.total || 0
        historyStats.value = data.stats || {}
    } catch (e) {
        showToast(e.message || '加载历史记录失败', 'error')
    } finally {
        loading.value = false
    }
}

const prevPage = () => {
    historyOffset.value = Math.max(0, historyOffset.value - historyLimit.value)
    fetchHistory()
}

const nextPage = () => {
    historyOffset.value += historyLimit.value
    fetchHistory()
}

const cleanupHistory = () => {
    showConfirmModal.value = true
}

const doCleanup = async () => {
    showConfirmModal.value = false
    try {
        await apiCall('/history/cleanup?days=7', { method: 'DELETE' })
        showToast('历史记录已清理', 'success')
        fetchHistory()
    } catch (e) {
        showToast(e.message || '清理失败', 'error')
    }
}

onMounted(() => {
    fetchHistory()
})
</script>
