<template>
    <div>
        <!-- Add Custom Source Button (Admin Only) -->
        <div v-if="isAdmin" class="mb-4 flex justify-end">
            <div class="action-container inline-flex p-1.5 rounded-xl">
                <button @click="openAddSourceModal" class="action-chip">
                    <i class="fas fa-plus mr-2"></i>添加自定义源
                </button>
            </div>
        </div>

        <!-- Custom Sources -->
        <div v-if="customSources.length > 0" class="glass rounded-2xl overflow-hidden mb-6">
            <div class="p-6 border-b border-white/10 flex items-center justify-between">
                <div>
                    <h3 class="font-bold text-xl text-white">自定义数据源</h3>
                    <p class="text-gray-500 text-sm mt-2">您添加的自定义 RSS 数据源</p>
                </div>
            </div>
            <div class="divide-y divide-white/5">
                <div v-for="source in customSources" :key="source.id" class="p-5 flex items-center justify-between hover:bg-white/5 transition">
                    <div class="flex items-center space-x-4">
                        <div :class="['w-10 h-10 rounded-xl flex items-center justify-center', source.enabled ? 'bg-amber-500/20' : 'bg-white/5']">
                            <i class="fas fa-rss" :class="source.enabled ? 'text-amber-300' : 'text-gray-500'"></i>
                        </div>
                        <div>
                            <div class="font-medium text-white">{{ source.name }}</div>
                            <div class="text-xs text-gray-500 font-mono truncate max-w-xs">{{ source.url }}</div>
                        </div>
                    </div>
                    <div class="flex items-center space-x-3">
                        <span :class="['text-xs px-3 py-1.5 rounded-full font-medium border', source.enabled ? 'bg-amber-500/25 text-amber-300 border-amber-500/40' : 'bg-gray-500/20 text-gray-400 border-gray-500/30']">
                            {{ source.enabled ? '已启用' : '已禁用' }}
                        </span>
                        <template v-if="isAdmin">
                            <button
                                @click="editCustomSource(source)"
                                class="px-3 py-1.5 text-sm glass rounded-lg text-gray-300 hover:text-white transition"
                            >
                                <i class="fas fa-edit"></i>
                            </button>
                            <button
                                @click="deleteCustomSource(source.id)"
                                class="px-3 py-1.5 text-sm glass rounded-lg text-red-400 hover:bg-red-500/20 transition"
                            >
                                <i class="fas fa-trash"></i>
                            </button>
                        </template>
                    </div>
                </div>
            </div>
        </div>

        <!-- Builtin Sources -->
        <div class="glass rounded-2xl overflow-hidden">
            <div class="p-6 border-b border-white/10">
                <h3 class="font-bold text-xl text-white">内置数据源</h3>
                <p class="text-gray-500 text-sm mt-2">当前已配置 {{ builtinSources.length }} 个内置数据源</p>
            </div>
            <div v-if="loading" class="p-12 text-center">
                <i class="fas fa-spinner animate-spin text-2xl text-amber-400"></i>
                <p class="mt-2 text-gray-400">加载中...</p>
            </div>
            <div v-else class="divide-y divide-white/5">
                <div v-for="(sourceList, category) in sourcesByCategory" :key="category">
                    <div class="px-6 py-3 bg-white/5 font-medium text-gray-400 text-sm flex items-center">
                        <i class="fas fa-folder-open mr-2 text-orange-400"></i>{{ category }}
                    </div>
                    <div v-for="source in sourceList" :key="source.id" class="p-5 flex items-center justify-between hover:bg-white/5 transition">
                        <div class="flex items-center space-x-4">
                            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500/10 to-red-500/10 flex items-center justify-center">
                                <img
                                    v-if="source.icon"
                                    :src="source.icon"
                                    class="w-6 h-6 rounded"
                                    @error="handleIconError"
                                >
                                <i v-else class="fas fa-rss text-gray-500"></i>
                            </div>
                            <div>
                                <div class="font-medium text-white">{{ source.name }}</div>
                                <div class="text-xs text-gray-500 font-mono">{{ source.id }}</div>
                            </div>
                        </div>
                        <span class="text-xs px-3 py-1 bg-white/5 text-gray-400 rounded-full">{{ source.category }}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Add/Edit Source Modal -->
        <div v-if="showSourceModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div class="glass rounded-2xl w-full max-w-md overflow-hidden">
                <div class="p-6 border-b border-white/10 flex items-center justify-between">
                    <h3 class="font-bold text-xl text-white">{{ editingSource ? '编辑数据源' : '添加自定义源' }}</h3>
                    <button @click="closeSourceModal" class="text-gray-500 hover:text-white transition w-8 h-8 rounded-lg hover:bg-white/10 flex items-center justify-center">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <form @submit.prevent="saveSource" class="p-6 space-y-5">
                    <div>
                        <label class="block text-sm font-medium text-gray-400 mb-2">源 ID</label>
                        <input
                            type="text"
                            v-model="sourceForm.id"
                            placeholder="my_custom_source"
                            :disabled="editingSource"
                            class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white placeholder-gray-500 disabled:opacity-50"
                        >
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-400 mb-2">名称</label>
                        <input
                            type="text"
                            v-model="sourceForm.name"
                            placeholder="我的自定义源"
                            class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white placeholder-gray-500"
                        >
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-400 mb-2">RSS URL</label>
                        <input
                            type="url"
                            v-model="sourceForm.url"
                            placeholder="https://example.com/rss"
                            class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white placeholder-gray-500"
                        >
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-400 mb-2">分类</label>
                        <input
                            type="text"
                            v-model="sourceForm.category"
                            placeholder="自定义"
                            class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white placeholder-gray-500"
                        >
                    </div>
                    <div class="flex items-center justify-between">
                        <span class="text-gray-400">启用</span>
                        <label class="toggle-switch" @click.prevent="sourceForm.enabled = !sourceForm.enabled">
                            <div :class="['toggle-slider', sourceForm.enabled ? 'on' : 'off']">
                                <span class="toggle-label-on">开</span>
                                <span class="toggle-label-off">关</span>
                            </div>
                        </label>
                    </div>
                </form>
                <div class="p-6 border-t border-white/10 flex justify-end space-x-3">
                    <button
                        @click="closeSourceModal"
                        class="px-5 py-2.5 text-gray-400 hover:text-white hover:bg-white/10 rounded-xl transition"
                    >
                        取消
                    </button>
                    <button
                        @click="saveSource"
                        :disabled="saving"
                        class="px-5 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl hover:opacity-90 transition disabled:opacity-50 font-medium"
                    >
                        <i v-if="saving" class="fas fa-spinner animate-spin mr-2"></i>
                        保存
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
import { useConfirm } from '../composables/useConfirm'

const { apiCall, currentUser } = useApi()
const { showToast } = useToast()
const { confirm } = useConfirm()

const loading = ref(false)
const saving = ref(false)
const builtinSources = ref([])
const customSources = ref([])
const showSourceModal = ref(false)
const editingSource = ref(null)
const sourceForm = ref({ id: '', name: '', url: '', category: '自定义', enabled: false })

const isAdmin = computed(() => currentUser.value?.role === 'admin')

const sourcesByCategory = computed(() => {
    const groups = {}
    for (const source of builtinSources.value) {
        const cat = source.category || '其他'
        if (!groups[cat]) groups[cat] = []
        groups[cat].push(source)
    }
    return groups
})

const fetchSources = async () => {
    loading.value = true
    try {
        // 获取内置数据源
        const sourcesData = await apiCall('/sources')
        builtinSources.value = sourcesData.sources || []
        
        // 获取自定义数据源
        try {
            const customData = await apiCall('/sources/custom')
            customSources.value = customData.sources || []
        } catch (e) {
            customSources.value = []
        }
    } catch (e) {
        showToast(e.message || '加载数据源失败', 'error')
    } finally {
        loading.value = false
    }
}

const handleIconError = (e) => {
    e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23666"><rect width="24" height="24" rx="4"/></svg>'
}

const openAddSourceModal = () => {
    editingSource.value = null
    sourceForm.value = { id: '', name: '', url: '', category: '自定义', enabled: false }
    showSourceModal.value = true
}

const editCustomSource = (source) => {
    editingSource.value = source
    sourceForm.value = { ...source }
    showSourceModal.value = true
}

const closeSourceModal = () => {
    showSourceModal.value = false
    editingSource.value = null
}

const saveSource = async () => {
    if (!sourceForm.value.name || !sourceForm.value.url) {
        showToast('请填写完整信息', 'error')
        return
    }
    saving.value = true
    try {
        if (editingSource.value) {
            await apiCall(`/sources/custom/${editingSource.value.id}`, {
                method: 'PUT',
                body: JSON.stringify(sourceForm.value)
            })
            showToast('数据源已更新', 'success')
        } else {
            await apiCall('/sources/custom', {
                method: 'POST',
                body: JSON.stringify(sourceForm.value)
            })
            showToast('数据源已添加', 'success')
        }
        closeSourceModal()
        fetchSources()
    } catch (e) {
        showToast(e.message || '保存失败', 'error')
    } finally {
        saving.value = false
    }
}

const deleteCustomSource = async (id) => {
    const confirmed = await confirm('确定要删除此数据源吗？', { title: '删除数据源', type: 'danger', confirmText: '删除' })
    if (!confirmed) return
    try {
        await apiCall(`/sources/custom/${id}`, { method: 'DELETE' })
        showToast('数据源已删除', 'success')
        fetchSources()
    } catch (e) {
        showToast(e.message || '删除失败', 'error')
    }
}

onMounted(() => {
    fetchSources()
})
</script>
