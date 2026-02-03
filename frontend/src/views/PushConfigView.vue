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
        <div v-if="showModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
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
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useApi } from '../composables/useApi'
import { useToast } from '../composables/useToast'

const { apiCall, currentUser } = useApi()
const { showToast } = useToast()

const channels = ref([])
const loading = ref(false)
const showModal = ref(false)
const editingChannel = ref(null)
const channelForm = ref({ enabled: false, config: {} })
const saving = ref(false)
const testing = ref(false)
const testingChannel = ref(null)

const isAdmin = computed(() => currentUser.value?.role === 'admin')

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
        showToast('加载推送渠道失败', 'error')
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

const saveConfig = async () => {
    saving.value = true
    try {
        await apiCall(`/config/push/${editingChannel.value.id}`, {
            method: 'PUT',
            body: JSON.stringify(channelForm.value)
        })
        showToast('保存成功', 'success')
        showModal.value = false
        fetchChannels()
    } catch (e) {
        showToast('保存失败', 'error')
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
        showToast('测试失败', 'error')
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
        showToast('测试失败', 'error')
    } finally {
        testingChannel.value = null
    }
}

onMounted(() => {
    fetchChannels()
})
</script>
