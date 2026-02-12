<template>
    <div class="space-y-6">
        <div class="glass rounded-2xl overflow-hidden">
            <div class="p-6 border-b border-white/10">
                <h3 class="font-bold text-xl text-white">
                    <i class="fas fa-paper-plane text-orange-400 mr-2"></i>推送渠道
                </h3>
                <p class="text-gray-500 text-sm mt-2">配置推送渠道后，新热点将自动推送到对应平台</p>
            </div>
            <div class="p-6">
                <div v-if="loading" class="text-center py-10 text-gray-400">
                    <i class="fas fa-spinner animate-spin text-2xl"></i>
                    <p class="mt-2">加载中...</p>
                </div>
                <!-- 列表布局 -->
                <div v-else class="space-y-3">
                    <div
                        v-for="channel in channels"
                        :key="channel.id"
                        class="flex items-center justify-between py-3 border-b border-white/5 last:border-b-0"
                    >
                        <div class="flex items-center space-x-4">
                            <div :class="['w-12 h-12 rounded-xl flex items-center justify-center', channel.enabled ? 'bg-amber-500/20' : 'bg-white/5']">
                                <i :class="[getChannelIcon(channel.id), 'text-xl', channel.enabled ? 'text-amber-300' : 'text-gray-500']"></i>
                            </div>
                            <div>
                                <div class="font-semibold text-white">{{ channel.name }}</div>
                                <div class="text-sm mt-0.5" :class="channel.enabled ? 'text-amber-300' : 'text-gray-500'">
                                    {{ channel.enabled ? '已启用' : '未配置' }}
                                </div>
                            </div>
                        </div>
                        <div v-if="isAdmin" class="flex items-center space-x-2">
                            <button
                                @click="openConfig(channel)"
                                class="px-4 py-2 text-sm glass rounded-lg text-gray-300 hover:text-white hover:bg-white/10 transition flex items-center space-x-2"
                            >
                                <i class="fas fa-cog"></i>
                                <span>配置</span>
                            </button>
                            <button
                                v-if="channel.enabled"
                                @click="testChannelDirect(channel)"
                                :disabled="testingChannel === channel.id"
                                class="px-4 py-2 text-sm glass rounded-lg text-amber-400 hover:bg-white/10 transition flex items-center space-x-2"
                            >
                                <i :class="testingChannel === channel.id ? 'fas fa-spinner animate-spin' : 'fas fa-paper-plane'"></i>
                                <span>测试</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 推送数据源选择 -->
        <div class="glass rounded-2xl overflow-hidden">
            <div class="p-6 border-b border-white/10">
                <div class="flex items-center justify-between">
                    <div>
                        <h3 class="font-bold text-xl text-white">
                            <i class="fas fa-filter text-blue-400 mr-2"></i>推送数据源
                        </h3>
                        <p class="text-gray-500 text-sm mt-2">选择需要推送的热榜平台，未选中的平台将不会推送消息</p>
                    </div>
                    <div v-if="isAdmin && !sourcesLoading" class="flex items-center space-x-2">
                        <button
                            @click="toggleAllSources"
                            class="px-3 py-1.5 text-xs glass rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition"
                        >
                            {{ isAllSelected ? '取消全选' : '全选' }}
                        </button>
                        <button
                            v-if="sourcesChanged"
                            @click="savePushSources"
                            :disabled="savingSources"
                            class="px-4 py-1.5 text-xs bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-lg hover:opacity-90 transition disabled:opacity-50 font-medium"
                        >
                            <i v-if="savingSources" class="fas fa-spinner animate-spin mr-1"></i>
                            保存
                        </button>
                    </div>
                </div>
            </div>
            <div class="p-6">
                <div v-if="sourcesLoading" class="text-center py-8 text-gray-400">
                    <i class="fas fa-spinner animate-spin text-2xl"></i>
                    <p class="mt-2">加载中...</p>
                </div>
                <div v-else class="space-y-5">
                    <!-- 提示信息 -->
                    <div class="flex items-center space-x-2 text-sm bg-white/5 rounded-lg px-4 py-2.5"
                         :class="selectedSources.length === 0 ? 'text-amber-400' : 'text-gray-400'">
                        <i :class="selectedSources.length === 0 ? 'fas fa-exclamation-triangle text-amber-400' : 'fas fa-info-circle text-blue-400'"></i>
                        <span>{{ selectedSources.length === 0 ? '未选择任何平台，不会推送任何消息' : isAllSelected ? '已选择全部平台' : `已选择 ${selectedSources.length} / ${allSources.length} 个平台` }}</span>
                    </div>

                    <!-- 按分类分组 -->
                    <div v-for="(sourceIds, category) in categories" :key="category" class="space-y-2">
                        <div class="flex items-center space-x-2 mb-3">
                            <span class="text-sm font-medium text-gray-300">{{ category }}</span>
                            <span class="text-xs text-gray-500 bg-white/5 px-2 py-0.5 rounded-full">{{ sourceIds.length }}</span>
                        </div>
                        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                            <div
                                v-for="sourceId in sourceIds"
                                :key="sourceId"
                                @click="isAdmin && toggleSource(sourceId)"
                                :class="[
                                    'flex items-center space-x-3 p-3 rounded-xl border transition-all',
                                    isAdmin ? 'cursor-pointer' : 'cursor-default',
                                    isSourceSelected(sourceId)
                                        ? 'border-amber-500/40 bg-amber-500/10 hover:bg-amber-500/15'
                                        : 'border-white/5 bg-white/[0.02] hover:bg-white/5'
                                ]"
                            >
                                <div :class="[
                                    'w-[18px] h-[18px] rounded flex items-center justify-center flex-shrink-0 transition-all',
                                    isSourceSelected(sourceId)
                                        ? 'bg-amber-500 text-white shadow-sm shadow-amber-500/30'
                                        : 'border-2 border-gray-400/50'
                                ]">
                                    <i v-if="isSourceSelected(sourceId)" class="fas fa-check text-[10px]"></i>
                                </div>
                                <div class="flex items-center space-x-2 min-w-0">
                                    <img
                                        v-if="getSourceIcon(sourceId)"
                                        :src="getSourceIcon(sourceId)"
                                        class="w-4 h-4 rounded flex-shrink-0"
                                        @error="$event.target.style.display='none'"
                                    >
                                    <span :class="[
                                        'text-sm truncate',
                                        isSourceSelected(sourceId) ? 'text-white' : 'text-gray-400'
                                    ]">{{ getSourceName(sourceId) }}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 配置指南 -->
        <div class="glass rounded-xl overflow-hidden">
            <div class="p-4 border-b border-white/5">
                <h3 class="text-sm font-medium text-white">
                    <i class="fas fa-book-open mr-2 text-gray-500"></i>配置指南
                </h3>
            </div>
            <div class="p-4 space-y-3">
                <div class="bg-white/5 rounded-lg p-4">
                    <h4 class="text-sm text-white mb-2">
                        <i class="fab fa-telegram text-gray-400 mr-2"></i>Telegram
                    </h4>
                    <ol class="text-xs text-gray-500 space-y-1.5 list-decimal list-inside">
                        <li>找 @BotFather 创建 Bot，获取 Token</li>
                        <li>找 @userinfobot 获取你的 Chat ID</li>
                        <li>点击配置按钮填写 Bot Token 和 Chat ID</li>
                    </ol>
                </div>
                <div class="bg-white/5 rounded-lg p-4">
                    <h4 class="text-sm text-white mb-2">
                        <i class="fab fa-discord text-gray-400 mr-2"></i>Discord
                    </h4>
                    <ol class="text-xs text-gray-500 space-y-1.5 list-decimal list-inside">
                        <li>服务器设置 - 整合 - Webhook - 创建 Webhook</li>
                        <li>复制 Webhook URL</li>
                        <li>点击配置按钮填写 Webhook URL</li>
                    </ol>
                </div>
                <div class="bg-white/5 rounded-lg p-4">
                    <h4 class="text-sm text-white mb-2">
                        <i class="fab fa-weixin text-gray-400 mr-2"></i>企业微信 / 飞书 / 钉钉
                    </h4>
                    <ol class="text-xs text-gray-500 space-y-1.5 list-decimal list-inside">
                        <li>在群设置中添加机器人</li>
                        <li>复制 Webhook URL</li>
                        <li>点击配置按钮填写 Webhook URL</li>
                    </ol>
                </div>
                <div class="bg-white/5 rounded-lg p-4">
                    <h4 class="text-sm text-white mb-2">
                        <i class="fas fa-envelope text-gray-400 mr-2"></i>邮件
                    </h4>
                    <ol class="text-xs text-gray-500 space-y-1.5 list-decimal list-inside">
                        <li>Gmail 需开启两步验证并创建应用专用密码</li>
                        <li>QQ/163 邮箱需开启 SMTP 并获取授权码</li>
                        <li>填写 SMTP 服务器、端口、用户名、密码</li>
                    </ol>
                </div>
            </div>
        </div>

        <!-- 配置弹窗 -->
        <Teleport to="body">
        <div v-if="showModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[9999] p-4">
            <div class="glass rounded-2xl w-full max-w-md overflow-hidden">
                <div class="p-6 border-b border-white/10 flex items-center justify-between">
                    <h3 class="font-bold text-xl text-white">{{ editingChannel?.name }} 配置</h3>
                    <button @click="showModal = false" class="text-gray-500 hover:text-white transition w-8 h-8 rounded-lg hover:bg-white/10 flex items-center justify-center">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="p-6 space-y-5">
                    <!-- 启用开关 -->
                    <div class="flex items-center justify-between">
                        <span class="text-gray-300">启用推送</span>
                        <label class="toggle-switch" @click="channelForm.enabled = !channelForm.enabled">
                            <div :class="['toggle-slider', channelForm.enabled ? 'on' : 'off']">
                                <span class="toggle-label-on">开</span>
                                <span class="toggle-label-off">关</span>
                            </div>
                        </label>
                    </div>

                    <!-- Telegram 配置 -->
                    <template v-if="editingChannel?.id === 'telegram'">
                        <div>
                            <label class="block text-sm font-medium text-gray-400 mb-2">Bot Token</label>
                            <input
                                type="text"
                                v-model="channelForm.config.bot_token"
                                placeholder="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
                                class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white placeholder-gray-500"
                            >
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-400 mb-2">Chat ID</label>
                            <input
                                type="text"
                                v-model="channelForm.config.chat_id"
                                placeholder="-1001234567890"
                                class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white placeholder-gray-500"
                            >
                        </div>
                    </template>

                    <!-- 邮件配置 -->
                    <template v-else-if="editingChannel?.id === 'email'">
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-400 mb-2">SMTP 服务器</label>
                                <input
                                    type="text"
                                    v-model="channelForm.config.smtp_host"
                                    placeholder="smtp.gmail.com"
                                    class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white placeholder-gray-500"
                                >
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-400 mb-2">端口</label>
                                <input
                                    type="text"
                                    v-model="channelForm.config.smtp_port"
                                    placeholder="587"
                                    class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white placeholder-gray-500"
                                >
                            </div>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-400 mb-2">用户名</label>
                            <input
                                type="text"
                                v-model="channelForm.config.username"
                                placeholder="your@email.com"
                                class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white placeholder-gray-500"
                            >
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-400 mb-2">密码 / 授权码</label>
                            <input
                                type="password"
                                v-model="channelForm.config.password"
                                placeholder="应用专用密码或授权码"
                                class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white placeholder-gray-500"
                            >
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-400 mb-2">收件人邮箱</label>
                            <input
                                type="email"
                                v-model="channelForm.config.to_email"
                                placeholder="receiver@email.com"
                                class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white placeholder-gray-500"
                            >
                        </div>
                    </template>

                    <!-- 其他渠道 Webhook 配置 -->
                    <template v-else>
                        <div>
                            <label class="block text-sm font-medium text-gray-400 mb-2">Webhook URL</label>
                            <input
                                type="text"
                                v-model="channelForm.config.webhook_url"
                                placeholder="https://..."
                                class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white placeholder-gray-500"
                            >
                        </div>
                    </template>
                </div>
                <div class="p-6 border-t border-white/10 flex justify-end space-x-3">
                    <button
                        @click="showModal = false"
                        class="px-5 py-2.5 text-gray-400 hover:text-white hover:bg-white/10 rounded-xl transition"
                    >
                        取消
                    </button>
                    <button
                        @click="saveConfig"
                        :disabled="saving"
                        class="px-5 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl hover:opacity-90 transition disabled:opacity-50 font-medium"
                    >
                        <i v-if="saving" class="fas fa-spinner animate-spin mr-2"></i>
                        保存配置
                    </button>
                </div>
            </div>
        </div>
        </Teleport>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useApi } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import { useAppStore } from '../stores/app'

const { apiCall, currentUser } = useApi()
const { showToast } = useToast()
const appStore = useAppStore()

const channels = ref([])
const loading = ref(false)
const showModal = ref(false)
const editingChannel = ref(null)
const channelForm = ref({ enabled: false, config: {} })
const saving = ref(false)
const testing = ref(false)
const testingChannel = ref(null)

// 推送数据源选择
const sourcesLoading = ref(false)
const savingSources = ref(false)
const allSources = ref([])             // 所有可用数据源
const categories = ref({})             // 分类信息
const selectedSources = ref([])        // UI 中选中的数据源（始终使用显式列表）
const originalSelectedSources = ref([])  // 保存前的原始值，用于检测变更

const isAdmin = computed(() => currentUser.value?.role === 'admin')

// 检查是否有未保存的变更
const sourcesChanged = computed(() => {
    const current = [...selectedSources.value].sort()
    const original = [...originalSelectedSources.value].sort()
    return JSON.stringify(current) !== JSON.stringify(original)
})

// 检查是否全选
const isAllSelected = computed(() => {
    if (allSources.value.length === 0) return false
    return selectedSources.value.length === allSources.value.length
})

const getChannelIcon = (id) => {
    const icons = {
        telegram: 'fab fa-telegram',
        discord: 'fab fa-discord',
        wecom: 'fas fa-comments',
        feishu: 'fas fa-feather',
        dingtalk: 'fas fa-comment-dots',
        email: 'fas fa-envelope',
        webhook: 'fas fa-link'
    }
    return icons[id] || 'fas fa-bell'
}

const fetchChannels = async () => {
    loading.value = true
    try {
        const data = await apiCall('/config/push')
        channels.value = data.channels || []
    } catch (e) {
        showToast(e.message || '加载推送渠道失败', 'error')
    } finally {
        loading.value = false
    }
}

const openConfig = (channel) => {
    editingChannel.value = channel
    channelForm.value = { 
        enabled: channel.enabled || false, 
        config: { ...(channel.config || {}) } 
    }
    showModal.value = true
}

// 验证配置是否完整
const validateConfig = () => {
    const channelId = editingChannel.value?.id
    const config = channelForm.value.config

    // 如果未启用，不需要验证
    if (!channelForm.value.enabled) {
        return { valid: true }
    }

    if (channelId === 'telegram') {
        if (!config.bot_token?.trim()) {
            return { valid: false, message: '请填写 Bot Token' }
        }
        if (!config.chat_id?.trim()) {
            return { valid: false, message: '请填写 Chat ID' }
        }
    } else if (channelId === 'email') {
        if (!config.smtp_host?.trim()) {
            return { valid: false, message: '请填写 SMTP 服务器' }
        }
        if (!config.smtp_port) {
            return { valid: false, message: '请填写端口' }
        }
        if (!config.username?.trim()) {
            return { valid: false, message: '请填写邮箱用户名' }
        }
        if (!config.password?.trim()) {
            return { valid: false, message: '请填写密码/授权码' }
        }
        if (!config.to_email?.trim()) {
            return { valid: false, message: '请填写收件人邮箱' }
        }
    } else {
        // Webhook 类型的渠道
        if (!config.webhook_url?.trim()) {
            return { valid: false, message: '请填写 Webhook URL' }
        }
    }

    return { valid: true }
}

const saveConfig = async () => {
    // 验证必填字段
    const validation = validateConfig()
    if (!validation.valid) {
        showToast(validation.message, 'error')
        return
    }

    saving.value = true
    try {
        await apiCall(`/config/push/${editingChannel.value.id}`, {
            method: 'PUT',
            body: JSON.stringify(channelForm.value)
        })
        showToast('保存成功', 'success')
        showModal.value = false
        fetchChannels()
        // 刷新统计信息（更新侧边栏推送渠道数量）
        appStore.fetchStats()
    } catch (e) {
        showToast(e.message || '保存失败', 'error')
    } finally {
        saving.value = false
    }
}

const testChannel = async () => {
    testing.value = true
    try {
        const result = await apiCall(`/config/push/${editingChannel.value.id}/test`, {
            method: 'POST',
            body: JSON.stringify(channelForm.value.config)
        })
        if (result.success) {
            showToast('测试成功', 'success')
        } else {
            showToast(result.message || '测试失败', 'error')
        }
    } catch (e) {
        showToast(e.message || '测试失败', 'error')
    } finally {
        testing.value = false
    }
}

const testChannelDirect = async (channel) => {
    testingChannel.value = channel.id
    try {
        const result = await apiCall(`/config/push/${channel.id}/test`, {
            method: 'POST',
            body: JSON.stringify(channel.config || {})
        })
        if (result.success) {
            showToast('测试成功', 'success')
        } else {
            showToast(result.message || '测试失败', 'error')
        }
    } catch (e) {
        showToast(e.message || '测试失败', 'error')
    } finally {
        testingChannel.value = null
    }
}

// ===== 推送数据源选择方法 =====

const fetchPushSources = async () => {
    sourcesLoading.value = true
    try {
        const data = await apiCall('/config/push-sources')
        allSources.value = data.all_sources || []
        categories.value = data.categories || {}
        const apiSources = data.selected_sources || []
        const isConfigured = data.is_configured || false
        
        if (!isConfigured) {
            // 未配置过 → 默认全选
            selectedSources.value = allSources.value.map(s => s.id)
        } else {
            // 已配置 → 使用保存的选择
            selectedSources.value = [...apiSources]
        }
        originalSelectedSources.value = [...selectedSources.value]
    } catch (e) {
        showToast(e.message || '加载推送数据源配置失败', 'error')
    } finally {
        sourcesLoading.value = false
    }
}

const getSourceName = (sourceId) => {
    const source = allSources.value.find(s => s.id === sourceId)
    return source ? source.name : sourceId
}

const getSourceIcon = (sourceId) => {
    const source = allSources.value.find(s => s.id === sourceId)
    return source ? source.icon : ''
}

const isSourceSelected = (sourceId) => {
    return selectedSources.value.includes(sourceId)
}

const toggleSource = (sourceId) => {
    const index = selectedSources.value.indexOf(sourceId)
    if (index > -1) {
        selectedSources.value.splice(index, 1)
    } else {
        selectedSources.value.push(sourceId)
    }
}

const toggleAllSources = () => {
    if (isAllSelected.value) {
        // 取消全选：清空所有
        selectedSources.value = []
    } else {
        // 全选：选中所有源
        selectedSources.value = allSources.value.map(s => s.id)
    }
}

const savePushSources = async () => {
    savingSources.value = true
    try {
        // 始终发送显式的数据源列表
        await apiCall('/config/push-sources', {
            method: 'PUT',
            body: JSON.stringify({ sources: selectedSources.value })
        })
        originalSelectedSources.value = [...selectedSources.value]
        showToast('推送数据源设置已保存', 'success')
    } catch (e) {
        showToast(e.message || '保存推送数据源失败', 'error')
    } finally {
        savingSources.value = false
    }
}

onMounted(() => {
    fetchChannels()
    fetchPushSources()
})
</script>
