<template>
    <div>
        <!-- Scheduler Status -->
        <div class="glass rounded-2xl overflow-hidden mb-8">
            <div class="p-6 border-b border-white/10">
                <h3 class="font-bold text-xl text-white">调度器状态</h3>
            </div>
            <div class="p-6">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Status -->
                    <div class="glass rounded-xl p-5">
                        <div class="flex items-center justify-between mb-4">
                            <span class="text-gray-400">运行状态</span>
                            <span :class="['px-3 py-1.5 rounded-full text-sm font-semibold border', schedulerStatus.running ? 'bg-green-500/20 text-green-400 border-green-500/30' : 'bg-red-500/25 text-red-300 border-red-500/40']">
                                {{ schedulerStatus.running ? '运行中' : (schedulerStatus.paused ? '已暂停' : '已停止') }}
                            </span>
                        </div>
                        <div v-if="isAdmin" class="flex items-center space-x-3">
                            <button
                                v-if="schedulerStatus.paused"
                                @click="resumeScheduler"
                                class="flex-1 px-4 py-2.5 bg-amber-500/25 text-amber-300 rounded-xl hover:bg-amber-500/40 transition font-medium"
                            >
                                <i class="fas fa-play mr-2"></i>恢复
                            </button>
                            <button
                                v-else
                                @click="pauseScheduler"
                                class="flex-1 px-4 py-2.5 bg-amber-500/25 text-amber-300 rounded-xl hover:bg-amber-500/40 transition font-medium"
                            >
                                <i class="fas fa-pause mr-2"></i>暂停
                            </button>
                            <button
                                @click="triggerFetch"
                                :disabled="triggeringFetch"
                                class="flex-1 px-4 py-2.5 bg-amber-500/25 text-amber-300 rounded-xl hover:bg-amber-500/40 transition font-medium disabled:opacity-50"
                            >
                                <i v-if="triggeringFetch" class="fas fa-spinner animate-spin mr-2"></i>
                                <i v-else class="fas fa-bolt mr-2"></i>
                                {{ triggeringFetch ? '执行中' : '立即执行' }}
                            </button>
                        </div>
                        <div v-else class="text-center text-gray-500 text-sm py-2">
                            <i class="fas fa-lock mr-1"></i>仅管理员可控制
                        </div>
                    </div>

                    <!-- Interval Config -->
                    <div class="glass rounded-xl p-5">
                        <div class="flex items-center justify-between mb-4">
                            <span class="text-gray-400">抓取间隔</span>
                            <span class="text-white font-medium">{{ schedulerStatus.interval_minutes || '-' }} 分钟</span>
                        </div>
                        <div v-if="isAdmin" class="flex items-center space-x-3">
                            <input
                                type="number"
                                v-model.number="newInterval"
                                min="1"
                                max="1440"
                                class="flex-1 px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white"
                            >
                            <button
                                @click="updateInterval"
                                class="px-4 py-2.5 bg-amber-500/25 text-amber-300 rounded-xl hover:bg-amber-500/40 transition font-medium"
                            >
                                更新
                            </button>
                        </div>
                        <div v-else class="text-center text-gray-500 text-sm py-2">
                            <i class="fas fa-lock mr-1"></i>仅管理员可修改
                        </div>
                    </div>
                </div>

                <!-- Next Run & Last Run -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                    <div class="glass rounded-xl p-5">
                        <div class="text-gray-400 mb-2">下次执行时间</div>
                        <div class="text-xl font-medium text-white">
                            {{ schedulerStatus.next_run ? formatDateTime(schedulerStatus.next_run) : '-' }}
                        </div>
                    </div>
                    <div class="glass rounded-xl p-5">
                        <div class="text-gray-400 mb-2">上次执行时间</div>
                        <div class="text-xl font-medium text-white">
                            {{ schedulerStatus.last_run ? formatDateTime(schedulerStatus.last_run) : '-' }}
                        </div>
                    </div>
                </div>

                <!-- Last Run Result -->
                <div v-if="schedulerStatus.last_run_result" class="mt-6 glass rounded-xl p-5">
                    <div class="text-gray-400 mb-3">上次执行结果</div>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="text-center">
                            <div :class="['text-2xl font-bold', schedulerStatus.last_run_result.success ? 'text-green-400' : 'text-red-400']">
                                {{ schedulerStatus.last_run_result.success ? '成功' : '失败' }}
                            </div>
                            <div class="text-xs text-gray-500 mt-1">状态</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-blue-400">{{ schedulerStatus.last_run_result.sources_count || 0 }}</div>
                            <div class="text-xs text-gray-500 mt-1">数据源</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-amber-400">{{ schedulerStatus.last_run_result.new_items || 0 }}</div>
                            <div class="text-xs text-gray-500 mt-1">新内容</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-green-400">{{ schedulerStatus.last_run_result.pushed_count || 0 }}</div>
                            <div class="text-xs text-gray-500 mt-1">已推送</div>
                        </div>
                    </div>
                    <div v-if="schedulerStatus.last_run_result.error" class="mt-4 text-sm text-red-400 bg-red-500/10 px-4 py-2 rounded-lg">
                        <i class="fas fa-exclamation-circle mr-2"></i>{{ schedulerStatus.last_run_result.error }}
                    </div>
                </div>
            </div>
        </div>

        <!-- Daily Digest Config -->
        <div class="glass rounded-2xl overflow-hidden">
            <div class="p-6 border-b border-white/10">
                <div class="flex items-center justify-between">
                    <div>
                        <h3 class="font-bold text-xl text-white">
                            <i class="fas fa-newspaper text-orange-400 mr-2"></i>定时摘要
                        </h3>
                        <p class="text-gray-500 text-sm mt-1">每天定时推送热榜汇总</p>
                    </div>
                    <div v-if="isAdmin" class="flex items-center space-x-3">
                        <label class="toggle-switch" @click="toggleDigest">
                            <div :class="['toggle-slider', digestStatus.enabled ? 'on' : 'off']">
                                <span class="toggle-label-on">开</span>
                                <span class="toggle-label-off">关</span>
                            </div>
                        </label>
                    </div>
                </div>
            </div>
            <div class="p-6">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Time Config -->
                    <div class="glass rounded-xl p-5">
                        <div class="flex items-center justify-between mb-4">
                            <span class="text-gray-400"><i class="fas fa-clock mr-2"></i>推送时间</span>
                            <span class="text-white font-medium">{{ digestStatus.time || '08:00' }}</span>
                        </div>
                        <div v-if="isAdmin" class="flex items-center space-x-3">
                            <input
                                type="time"
                                v-model="digestForm.time"
                                class="flex-1 px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white"
                            >
                            <button
                                @click="updateDigestTime"
                                class="px-4 py-2.5 bg-amber-500/25 text-amber-300 rounded-xl hover:bg-amber-500/40 transition font-medium"
                            >
                                保存
                            </button>
                        </div>
                    </div>

                    <!-- Top N Config -->
                    <div class="glass rounded-xl p-5">
                        <div class="flex items-center justify-between mb-4">
                            <span class="text-gray-400"><i class="fas fa-list-ol mr-2"></i>每源条数</span>
                            <span class="text-white font-medium">{{ digestStatus.top_n || 10 }} 条</span>
                        </div>
                        <div v-if="isAdmin" class="flex items-center space-x-3">
                            <input
                                type="number"
                                v-model.number="digestForm.top_n"
                                min="1"
                                max="50"
                                class="flex-1 px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white"
                            >
                            <button
                                @click="updateDigestTopN"
                                class="px-4 py-2.5 bg-amber-500/25 text-amber-300 rounded-xl hover:bg-amber-500/40 transition font-medium"
                            >
                                保存
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Weekdays Config -->
                <div class="mt-6 glass rounded-xl p-5">
                    <div class="text-gray-400 mb-4"><i class="fas fa-calendar-week mr-2"></i>推送日期</div>
                    <div class="flex flex-wrap gap-2">
                        <button
                            v-for="(day, index) in ['一', '二', '三', '四', '五', '六', '日']"
                            :key="index"
                            @click="toggleDigestWeekday(index + 1)"
                            :class="['px-4 py-2 rounded-lg font-medium transition', digestStatus.weekdays?.includes(index + 1) ? 'bg-amber-500/30 text-amber-300' : 'bg-white/5 text-gray-400 hover:bg-white/10']"
                            :disabled="!isAdmin"
                        >
                            周{{ day }}
                        </button>
                    </div>
                </div>

                <!-- Digest Status -->
                <div class="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="glass rounded-xl p-5">
                        <div class="text-gray-400 mb-2">下次推送时间</div>
                        <div class="text-xl font-medium text-white">
                            {{ digestStatus.next_run ? formatDateTime(digestStatus.next_run) : (digestStatus.enabled ? '计算中...' : '未启用') }}
                        </div>
                    </div>
                    <div class="glass rounded-xl p-5">
                        <div class="text-gray-400 mb-2">上次推送时间</div>
                        <div class="text-xl font-medium text-white">
                            {{ digestStatus.last_run ? formatDateTime(digestStatus.last_run) : '从未执行' }}
                        </div>
                    </div>
                </div>

                <!-- Manual Trigger -->
                <div v-if="isAdmin" class="mt-6 flex justify-end">
                    <button
                        @click="triggerDigest"
                        :disabled="triggeringDigest"
                        class="px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl hover:opacity-90 transition font-medium disabled:opacity-50"
                    >
                        <i :class="['fas mr-2', triggeringDigest ? 'fa-spinner fa-spin' : 'fa-paper-plane']"></i>
                        {{ triggeringDigest ? '推送中...' : '立即推送摘要' }}
                    </button>
                </div>

                <!-- Last Digest Result -->
                <div v-if="digestStatus.last_run_result" class="mt-6 glass rounded-xl p-5">
                    <div class="text-gray-400 mb-3">上次推送结果</div>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="text-center">
                            <div :class="['text-2xl font-bold', digestStatus.last_run_result.success ? 'text-green-400' : 'text-red-400']">
                                {{ digestStatus.last_run_result.success ? '成功' : '失败' }}
                            </div>
                            <div class="text-xs text-gray-500 mt-1">状态</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-blue-400">{{ digestStatus.last_run_result.sources_count || 0 }}</div>
                            <div class="text-xs text-gray-500 mt-1">数据源</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-amber-400">{{ digestStatus.last_run_result.items_count || 0 }}</div>
                            <div class="text-xs text-gray-500 mt-1">内容条数</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-green-400">{{ digestStatus.last_run_result.channels_success || 0 }}</div>
                            <div class="text-xs text-gray-500 mt-1">推送渠道</div>
                        </div>
                    </div>
                    <div v-if="digestStatus.last_run_result.ai_summary" class="mt-4 text-sm text-amber-400 bg-amber-500/10 px-4 py-2 rounded-lg">
                        <i class="fas fa-robot mr-2"></i>本次摘要使用了 AI 生成
                    </div>
                    <div v-if="digestStatus.last_run_result.error" class="mt-4 text-sm text-red-400 bg-red-500/10 px-4 py-2 rounded-lg">
                        <i class="fas fa-exclamation-circle mr-2"></i>{{ digestStatus.last_run_result.error }}
                    </div>
                </div>
            </div>
        </div>

        <!-- AI Summary Config -->
        <div class="glass rounded-2xl overflow-hidden mt-8">
            <div class="p-6 border-b border-white/10">
                <div class="flex items-center justify-between">
                    <div>
                        <h3 class="font-bold text-xl text-white">
                            <i class="fas fa-robot text-orange-400 mr-2"></i>AI 摘要
                        </h3>
                        <p class="text-gray-500 text-sm mt-1">使用 AI 生成智能热点摘要，支持 OpenAI、Claude、DeepSeek、Ollama 等</p>
                    </div>
                    <div v-if="isAdmin" class="flex items-center space-x-3">
                        <label class="toggle-switch" @click="toggleAI">
                            <div :class="['toggle-slider', aiConfig.enabled ? 'on' : 'off']">
                                <span class="toggle-label-on">开</span>
                                <span class="toggle-label-off">关</span>
                            </div>
                        </label>
                    </div>
                </div>
            </div>
            <div class="p-6">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Model Config -->
                    <div class="glass rounded-xl p-5">
                        <div class="text-gray-400 mb-3"><i class="fas fa-cube mr-2"></i>模型</div>
                        <div v-if="isAdmin">
                            <input
                                type="text"
                                v-model="aiForm.model"
                                placeholder="gpt-4o-mini / claude-sonnet-4-20250514 / deepseek/deepseek-chat"
                                class="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white placeholder-gray-600 text-sm"
                            >
                            <p class="text-xs text-gray-600 mt-2">
                                支持 <a href="https://docs.litellm.ai/docs/providers" target="_blank" class="text-orange-400 hover:underline">litellm 所有模型</a>
                            </p>
                        </div>
                        <div v-else class="text-white font-medium">{{ aiConfig.model || '未配置' }}</div>
                    </div>

                    <!-- API Key Config -->
                    <div class="glass rounded-xl p-5">
                        <div class="text-gray-400 mb-3"><i class="fas fa-key mr-2"></i>API Key</div>
                        <div v-if="isAdmin" class="relative">
                            <input
                                :type="showApiKey ? 'text' : 'password'"
                                v-model="aiForm.api_key"
                                placeholder="sk-..."
                                class="w-full px-4 py-2.5 pr-10 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white placeholder-gray-600 text-sm"
                            >
                            <button
                                type="button"
                                @click="showApiKey = !showApiKey"
                                class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition"
                            >
                                <i :class="['fas', showApiKey ? 'fa-eye-slash' : 'fa-eye']"></i>
                            </button>
                        </div>
                        <div v-else class="text-white font-medium">{{ aiConfig.api_key ? '已配置' : '未配置' }}</div>
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                    <!-- Base URL Config -->
                    <div class="glass rounded-xl p-5">
                        <div class="text-gray-400 mb-3"><i class="fas fa-link mr-2"></i>API 地址（可选）</div>
                        <div v-if="isAdmin">
                            <input
                                type="text"
                                v-model="aiForm.base_url"
                                placeholder="留空使用默认地址，本地 Ollama: http://localhost:11434"
                                class="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white placeholder-gray-600 text-sm"
                            >
                        </div>
                        <div v-else class="text-white font-medium">{{ aiConfig.base_url || '默认' }}</div>
                    </div>

                    <!-- Summary Style -->
                    <div class="glass rounded-xl p-5">
                        <div class="text-gray-400 mb-3"><i class="fas fa-palette mr-2"></i>摘要风格</div>
                        <div v-if="isAdmin" class="flex flex-wrap gap-2">
                            <button
                                v-for="style in summaryStyles"
                                :key="style.value"
                                @click="aiForm.summary_style = style.value"
                                :class="['px-4 py-2 rounded-lg font-medium transition text-sm', aiForm.summary_style === style.value ? 'bg-amber-500/30 text-amber-300' : 'bg-white/5 text-gray-400 hover:bg-white/10']"
                            >
                                {{ style.label }}
                            </button>
                        </div>
                        <div v-else class="text-white font-medium">{{ currentStyleLabel }}</div>
                    </div>
                </div>

                <!-- Save Button -->
                <div v-if="isAdmin" class="mt-6 flex justify-end">
                    <button
                        @click="saveAIConfig"
                        :disabled="savingAI"
                        class="px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl hover:opacity-90 transition font-medium disabled:opacity-50"
                    >
                        <i :class="['fas mr-2', savingAI ? 'fa-spinner fa-spin' : 'fa-save']"></i>
                        {{ savingAI ? '保存中...' : '保存配置' }}
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

const schedulerStatus = ref({})
const digestStatus = ref({})
const newInterval = ref(30)
const triggeringFetch = ref(false)
const triggeringDigest = ref(false)
const digestForm = ref({ time: '08:00', top_n: 10 })
const aiConfig = ref({})
const aiForm = ref({ model: 'gpt-4o-mini', api_key: '', base_url: '', summary_style: 'brief' })
const savingAI = ref(false)
const showApiKey = ref(false)

const summaryStyles = [
    { value: 'brief', label: '简洁速递' },
    { value: 'detailed', label: '详细分析' },
    { value: 'morning_briefing', label: '晨间简报' },
]

const isAdmin = computed(() => currentUser.value?.role === 'admin')
const currentStyleLabel = computed(() => {
    const style = summaryStyles.find(s => s.value === aiConfig.value.summary_style)
    return style ? style.label : '简洁速递'
})

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

const fetchSchedulerStatus = async () => {
    try {
        const data = await apiCall('/scheduler/status')
        schedulerStatus.value = data
        newInterval.value = data.interval_minutes || 30
    } catch (e) {
        showToast(e.message || '获取调度器状态失败', 'error')
    }
}

const fetchDigestStatus = async () => {
    try {
        const data = await apiCall('/scheduler/digest')
        digestStatus.value = data
        digestForm.value.time = data.time || '08:00'
        digestForm.value.top_n = data.top_n || 10
    } catch (e) {
        showToast(e.message || '获取摘要配置失败', 'error')
    }
}

const pauseScheduler = async () => {
    try {
        await apiCall('/scheduler/pause', { method: 'POST' })
        showToast('调度器已暂停', 'success')
        fetchSchedulerStatus()
    } catch (e) {
        showToast(e.message || '操作失败', 'error')
    }
}

const resumeScheduler = async () => {
    try {
        await apiCall('/scheduler/resume', { method: 'POST' })
        showToast('调度器已恢复', 'success')
        fetchSchedulerStatus()
    } catch (e) {
        showToast(e.message || '操作失败', 'error')
    }
}

const triggerFetch = async () => {
    triggeringFetch.value = true
    try {
        await apiCall('/scheduler/trigger', { method: 'POST' })
        showToast('已触发抓取任务', 'success')
        fetchSchedulerStatus()
    } catch (e) {
        showToast(e.message || '触发失败', 'error')
    } finally {
        triggeringFetch.value = false
    }
}

const updateInterval = async () => {
    try {
        await apiCall('/scheduler/config', {
            method: 'PUT',
            body: JSON.stringify({ fetch_interval: newInterval.value })
        })
        showToast('间隔已更新', 'success')
        fetchSchedulerStatus()
    } catch (e) {
        showToast(e.message || '更新失败', 'error')
    }
}

const toggleDigest = async () => {
    try {
        await apiCall('/scheduler/digest', {
            method: 'PUT',
            body: JSON.stringify({ enabled: !digestStatus.value.enabled })
        })
        showToast(digestStatus.value.enabled ? '摘要已禁用' : '摘要已启用', 'success')
        fetchDigestStatus()
    } catch (e) {
        showToast(e.message || '操作失败', 'error')
    }
}

const updateDigestTime = async () => {
    try {
        await apiCall('/scheduler/digest', {
            method: 'PUT',
            body: JSON.stringify({ time: digestForm.value.time })
        })
        showToast('推送时间已更新', 'success')
        fetchDigestStatus()
    } catch (e) {
        showToast(e.message || '更新失败', 'error')
    }
}

const updateDigestTopN = async () => {
    try {
        await apiCall('/scheduler/digest', {
            method: 'PUT',
            body: JSON.stringify({ top_n: digestForm.value.top_n })
        })
        showToast('每源条数已更新', 'success')
        fetchDigestStatus()
    } catch (e) {
        showToast(e.message || '更新失败', 'error')
    }
}

const toggleDigestWeekday = async (day) => {
    if (!isAdmin.value) return
    try {
        // 获取当前的 weekdays，切换指定的 day
        const currentWeekdays = digestStatus.value.weekdays || [1, 2, 3, 4, 5]
        let newWeekdays
        if (currentWeekdays.includes(day)) {
            newWeekdays = currentWeekdays.filter(d => d !== day)
        } else {
            newWeekdays = [...currentWeekdays, day].sort()
        }
        await apiCall('/scheduler/digest', {
            method: 'PUT',
            body: JSON.stringify({ weekdays: newWeekdays })
        })
        fetchDigestStatus()
    } catch (e) {
        showToast(e.message || '更新失败', 'error')
    }
}

const triggerDigest = async () => {
    triggeringDigest.value = true
    try {
        await apiCall('/scheduler/digest/trigger', { method: 'POST' })
        showToast('摘要推送已触发', 'success')
        fetchDigestStatus()
    } catch (e) {
        showToast(e.message || '触发失败', 'error')
    } finally {
        triggeringDigest.value = false
    }
}

const fetchAIConfig = async () => {
    try {
        const data = await apiCall('/scheduler/ai-config')
        aiConfig.value = data
        aiForm.value = {
            model: data.model || 'gpt-4o-mini',
            api_key: data.api_key || '',
            base_url: data.base_url || '',
            summary_style: data.summary_style || 'brief',
        }
    } catch (e) {
        showToast(e.message || '获取 AI 配置失败', 'error')
    }
}

const toggleAI = async () => {
    if (!aiConfig.value.enabled) {
        const key = aiForm.value.api_key
        if (!key || !aiForm.value.model) {
            showToast('请先配置模型和 API Key 后再启用', 'error')
            return
        }
    }
    try {
        await apiCall('/scheduler/ai-config', {
            method: 'PUT',
            body: JSON.stringify({ enabled: !aiConfig.value.enabled })
        })
        showToast(aiConfig.value.enabled ? 'AI 摘要已禁用' : 'AI 摘要已启用', 'success')
        fetchAIConfig()
    } catch (e) {
        showToast(e.message || '操作失败', 'error')
    }
}

const saveAIConfig = async () => {
    savingAI.value = true
    try {
        const payload = { ...aiForm.value }
        if (!payload.api_key) {
            delete payload.api_key
        }
        await apiCall('/scheduler/ai-config', {
            method: 'PUT',
            body: JSON.stringify(payload)
        })
        showToast('AI 配置已保存', 'success')
        showApiKey.value = false
        fetchAIConfig()
    } catch (e) {
        showToast(e.message || '保存失败', 'error')
    } finally {
        savingAI.value = false
    }
}

onMounted(() => {
    fetchSchedulerStatus()
    fetchDigestStatus()
    fetchAIConfig()
})
</script>
