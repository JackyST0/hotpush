<template>
    <div>
        <!-- Add Rule Button (Admin Only) -->
        <div v-if="isAdmin" class="mb-4 flex justify-end">
            <div class="action-container inline-flex p-1.5 rounded-xl">
                <button @click="openAddRuleModal" class="action-chip">
                    <i class="fas fa-plus mr-2"></i>添加规则
                </button>
            </div>
        </div>

        <!-- Rules List -->
        <div class="glass rounded-2xl overflow-hidden mb-8">
            <div class="p-6 border-b border-white/10">
                <h3 class="font-bold text-xl text-white">推送规则</h3>
                <p class="text-gray-500 text-sm mt-2">配置规则过滤推送内容</p>
            </div>
            <div v-if="loading" class="p-12 text-center">
                <i class="fas fa-spinner animate-spin text-2xl text-amber-400"></i>
                <p class="mt-2 text-gray-400">加载中...</p>
            </div>
            <div v-else-if="pushRules.length === 0" class="p-12 text-center">
                <div class="text-6xl mb-4">📋</div>
                <p class="text-gray-500">暂无推送规则</p>
            </div>
            <div v-else class="divide-y divide-white/5">
                <div v-for="rule in pushRules" :key="rule.id" class="p-5 hover:bg-white/5 transition">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-4">
                            <div :class="['w-10 h-10 rounded-xl flex items-center justify-center', rule.enabled ? 'bg-amber-500/20' : 'bg-white/5']">
                                <i :class="[getRuleIcon(rule.rule_type), rule.enabled ? 'text-amber-300' : 'text-gray-500']"></i>
                            </div>
                            <div>
                                <div class="font-medium text-white">{{ rule.name }}</div>
                                <div class="text-sm text-gray-500">{{ getRuleTypeName(rule.rule_type) }}</div>
                            </div>
                        </div>
                        <div class="flex items-center space-x-3">
                            <span :class="['text-xs px-3 py-1.5 rounded-full font-medium border', rule.enabled ? 'bg-amber-500/25 text-amber-300 border-amber-500/40' : 'bg-gray-500/20 text-gray-400 border-gray-500/30']">
                                {{ rule.enabled ? '已启用' : '已禁用' }}
                            </span>
                            <template v-if="isAdmin">
                                <button
                                    @click="editRule(rule)"
                                    class="px-3 py-1.5 text-sm glass rounded-lg text-gray-300 hover:text-white transition"
                                >
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button
                                    @click="deleteRule(rule.id)"
                                    class="px-3 py-1.5 text-sm glass rounded-lg text-red-400 hover:bg-red-500/20 transition"
                                >
                                    <i class="fas fa-trash"></i>
                                </button>
                            </template>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Rule Types Guide -->
        <div class="glass rounded-2xl overflow-hidden">
            <div class="p-6 border-b border-white/10">
                <h3 class="font-bold text-xl text-white">
                    <i class="fas fa-info-circle mr-2 text-amber-400"></i>规则类型说明
                </h3>
            </div>
            <div class="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="glass rounded-xl p-5">
                    <h4 class="font-semibold text-white mb-2">
                        <i class="fas fa-search text-amber-400 mr-2"></i>关键词包含
                    </h4>
                    <p class="text-sm text-gray-400">只有标题包含指定关键词的内容才会推送</p>
                </div>
                <div class="glass rounded-xl p-5">
                    <h4 class="font-semibold text-white mb-2">
                        <i class="fas fa-ban text-red-400 mr-2"></i>关键词排除
                    </h4>
                    <p class="text-sm text-gray-400">标题包含指定关键词的内容不会推送</p>
                </div>
                <div class="glass rounded-xl p-5">
                    <h4 class="font-semibold text-white mb-2">
                        <i class="fas fa-clock text-yellow-400 mr-2"></i>时间段限制
                    </h4>
                    <p class="text-sm text-gray-400">只在指定时间段内推送</p>
                </div>
                <div class="glass rounded-xl p-5">
                    <h4 class="font-semibold text-white mb-2">
                        <i class="fas fa-filter text-orange-400 mr-2"></i>来源过滤
                    </h4>
                    <p class="text-sm text-gray-400">只推送或排除指定来源的内容</p>
                </div>
            </div>
        </div>

        <!-- Add/Edit Rule Modal -->
        <div v-if="showRuleModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div class="glass rounded-2xl w-full max-w-lg">
                <div class="p-6 border-b border-white/10 flex items-center justify-between">
                    <h3 class="font-bold text-xl text-white">{{ editingRule ? '编辑规则' : '添加推送规则' }}</h3>
                    <button @click="closeRuleModal" class="text-gray-500 hover:text-white transition w-8 h-8 rounded-lg hover:bg-white/10 flex items-center justify-center">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="p-6 space-y-5">
                    <div>
                        <label class="block text-sm font-medium text-gray-400 mb-2">规则名称</label>
                        <input
                            type="text"
                            v-model="ruleForm.name"
                            placeholder="我的规则"
                            class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white placeholder-gray-500"
                        >
                    </div>
                    <div class="relative">
                        <label class="block text-sm font-medium text-gray-400 mb-2">规则类型</label>
                        <div 
                            @click="showRuleTypeDropdown = !showRuleTypeDropdown"
                            class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl cursor-pointer text-white flex items-center justify-between hover:border-orange-500/50 transition"
                        >
                            <span>{{ getRuleTypeName(ruleForm.rule_type) }}</span>
                            <i :class="['fas fa-chevron-down text-gray-500 text-xs transition-transform', showRuleTypeDropdown ? 'rotate-180' : '']"></i>
                        </div>
                        <div 
                            v-if="showRuleTypeDropdown" 
                            class="absolute top-full left-0 right-0 mt-1 glass rounded-lg overflow-hidden z-10 py-1 shadow-xl"
                        >
                            <div 
                                v-for="option in ruleTypeOptions" 
                                :key="option.value"
                                @click="selectRuleType(option.value)"
                                class="px-4 py-2 cursor-pointer transition flex items-center justify-between text-sm hover:bg-amber-500/10"
                                :class="ruleForm.rule_type === option.value ? 'bg-amber-500/20 text-amber-400' : 'text-gray-300'"
                            >
                                <span>
                                    <i :class="[getRuleIcon(option.value), 'mr-2']"></i>
                                    {{ option.label }}
                                </span>
                                <i v-if="ruleForm.rule_type === option.value" class="fas fa-check text-xs"></i>
                            </div>
                        </div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-400 mb-2">规则值</label>
                        <input
                            type="text"
                            v-model="ruleForm.value"
                            :placeholder="getValuePlaceholder(ruleForm.rule_type)"
                            class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white placeholder-gray-500"
                        >
                    </div>
                    <div class="flex items-center justify-between">
                        <span class="text-gray-400">启用</span>
                        <label class="toggle-switch" @click.prevent="ruleForm.enabled = !ruleForm.enabled">
                            <div :class="['toggle-slider', ruleForm.enabled ? 'on' : 'off']">
                                <span class="toggle-label-on">开</span>
                                <span class="toggle-label-off">关</span>
                            </div>
                        </label>
                    </div>
                </div>
                <div class="p-6 border-t border-white/10 flex justify-end space-x-3">
                    <button
                        @click="closeRuleModal"
                        class="px-5 py-2.5 text-gray-400 hover:text-white hover:bg-white/10 rounded-xl transition"
                    >
                        取消
                    </button>
                    <button
                        @click="saveRule"
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
const pushRules = ref([])
const showRuleModal = ref(false)
const editingRule = ref(null)
const ruleForm = ref({ name: '', rule_type: 'keyword_include', value: '', enabled: false })
const showRuleTypeDropdown = ref(false)

const ruleTypeOptions = [
    { value: 'keyword_include', label: '关键词包含' },
    { value: 'keyword_exclude', label: '关键词排除' },
    { value: 'time_range', label: '时间段限制' },
    { value: 'source_filter', label: '来源过滤' }
]

const selectRuleType = (value) => {
    ruleForm.value.rule_type = value
    showRuleTypeDropdown.value = false
}

const isAdmin = computed(() => currentUser.value?.role === 'admin')

const getRuleIcon = (type) => {
    const icons = {
        keyword_include: 'fas fa-search',
        keyword_exclude: 'fas fa-ban',
        time_range: 'fas fa-clock',
        source_filter: 'fas fa-filter'
    }
    return icons[type] || 'fas fa-cog'
}

const getRuleTypeName = (type) => {
    const names = {
        keyword_include: '关键词包含',
        keyword_exclude: '关键词排除',
        time_range: '时间段限制',
        source_filter: '来源过滤'
    }
    return names[type] || type
}

const getValuePlaceholder = (type) => {
    const placeholders = {
        keyword_include: '输入关键词，多个用逗号分隔',
        keyword_exclude: '输入排除关键词，多个用逗号分隔',
        time_range: '格式：08:00-22:00',
        source_filter: '输入来源ID，多个用逗号分隔'
    }
    return placeholders[type] || '输入规则值'
}

const fetchRules = async () => {
    loading.value = true
    try {
        const data = await apiCall('/rules')
        pushRules.value = data.rules || []
    } catch (e) {
        showToast(e.message || '加载规则失败', 'error')
    } finally {
        loading.value = false
    }
}

const openAddRuleModal = () => {
    editingRule.value = null
    ruleForm.value = { name: '', rule_type: 'keyword_include', value: '', enabled: false }
    showRuleTypeDropdown.value = false
    showRuleModal.value = true
}

const editRule = (rule) => {
    editingRule.value = rule
    ruleForm.value = { ...rule }
    showRuleModal.value = true
}

const closeRuleModal = () => {
    showRuleModal.value = false
    editingRule.value = null
}

const saveRule = async () => {
    if (!ruleForm.value.name || !ruleForm.value.value) {
        showToast('请填写完整信息', 'error')
        return
    }
    saving.value = true
    try {
        if (editingRule.value) {
            await apiCall(`/rules/${editingRule.value.id}`, {
                method: 'PUT',
                body: JSON.stringify(ruleForm.value)
            })
            showToast('规则已更新', 'success')
        } else {
            await apiCall('/rules', {
                method: 'POST',
                body: JSON.stringify(ruleForm.value)
            })
            showToast('规则已添加', 'success')
        }
        closeRuleModal()
        fetchRules()
    } catch (e) {
        showToast(e.message || '保存失败', 'error')
    } finally {
        saving.value = false
    }
}

const deleteRule = async (id) => {
    const confirmed = await confirm('确定要删除此规则吗？', { title: '删除规则', type: 'danger', confirmText: '删除' })
    if (!confirmed) return
    try {
        await apiCall(`/rules/${id}`, { method: 'DELETE' })
        showToast('规则已删除', 'success')
        fetchRules()
    } catch (e) {
        showToast(e.message || '删除失败', 'error')
    }
}

onMounted(() => {
    fetchRules()
})
</script>
