<template>
    <div>
        <!-- Users List -->
        <div class="glass rounded-2xl overflow-hidden">
            <div class="p-6 border-b border-white/10">
                <h3 class="font-bold text-xl text-white">用户管理</h3>
                <p class="text-gray-500 text-sm mt-2">管理系统用户和权限</p>
            </div>
            <div v-if="loading" class="p-12 text-center">
                <i class="fas fa-spinner animate-spin text-2xl text-amber-400"></i>
                <p class="mt-2 text-gray-400">加载中...</p>
            </div>
            <div v-else-if="usersList.length === 0" class="p-12 text-center">
                <div class="text-6xl mb-4">👥</div>
                <p class="text-gray-500">暂无用户</p>
            </div>
            <div v-else class="divide-y divide-white/5">
                <div v-for="user in usersList" :key="user.id" class="p-5 hover:bg-white/5 transition">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-4">
                            <div :class="['w-12 h-12 rounded-xl flex items-center justify-center font-bold text-white', user.role === 'admin' ? 'bg-gradient-to-r from-amber-500 to-orange-500' : 'bg-white/10']">
                                {{ user.username.charAt(0).toUpperCase() }}
                            </div>
                            <div>
                                <div class="font-medium text-white">{{ user.username }}</div>
                                <div class="text-sm text-gray-500">
                                    <span :class="user.role === 'admin' ? 'text-orange-400' : 'text-gray-400'">
                                        {{ user.role === 'admin' ? '管理员' : '普通用户' }}
                                    </span>
                                    <span class="mx-2">·</span>
                                    <span>注册于 {{ formatDateTime(user.created_at) }}</span>
                                </div>
                            </div>
                        </div>
                        <div class="flex items-center space-x-3">
                            <button
                                @click="openEditUserModal(user)"
                                class="px-3 py-1.5 text-sm glass rounded-lg text-gray-300 hover:text-white transition"
                            >
                                <i class="fas fa-edit"></i>
                            </button>
                            <button
                                v-if="user.id !== currentUser?.id"
                                @click="deleteUser(user)"
                                class="px-3 py-1.5 text-sm glass rounded-lg text-red-400 hover:bg-red-500/20 transition"
                            >
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Edit User Modal -->
        <div v-if="showEditModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div class="glass rounded-2xl w-full max-w-md">
                <div class="p-6 border-b border-white/10 flex items-center justify-between">
                    <h3 class="font-bold text-xl text-white">编辑用户</h3>
                    <button @click="closeEditModal" class="text-gray-500 hover:text-white transition w-8 h-8 rounded-lg hover:bg-white/10 flex items-center justify-center">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="p-6 space-y-5">
                    <div>
                        <label class="block text-sm font-medium text-gray-400 mb-2">用户名</label>
                        <input
                            type="text"
                            v-model="editForm.username"
                            class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white placeholder-gray-500"
                            disabled
                        >
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-400 mb-2">新密码（留空则不修改）</label>
                        <input
                            type="password"
                            v-model="editForm.password"
                            placeholder="输入新密码"
                            class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 outline-none text-white placeholder-gray-500"
                        >
                    </div>
                    <div class="relative">
                        <label class="block text-sm font-medium text-gray-400 mb-2">角色</label>
                        <div 
                            @click="showRoleDropdown = !showRoleDropdown"
                            class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl cursor-pointer text-white flex items-center justify-between hover:border-orange-500/50 transition"
                        >
                            <span>{{ editForm.role === 'admin' ? '管理员' : '普通用户' }}</span>
                            <i :class="['fas fa-chevron-down text-gray-500 text-xs transition-transform', showRoleDropdown ? 'rotate-180' : '']"></i>
                        </div>
                        <div 
                            v-if="showRoleDropdown" 
                            class="absolute top-full left-0 right-0 mt-1 glass rounded-lg z-20 py-1 shadow-xl"
                        >
                            <div
                                @click="editForm.role = 'user'; showRoleDropdown = false"
                                class="px-4 py-2 cursor-pointer transition flex items-center justify-between text-sm hover:bg-amber-500/10"
                                :class="editForm.role === 'user' ? 'bg-amber-500/20 text-amber-400' : 'text-gray-300'"
                            >
                                <span><i class="fas fa-user mr-2 text-gray-500"></i>普通用户</span>
                                <i v-if="editForm.role === 'user'" class="fas fa-check text-xs"></i>
                            </div>
                            <div
                                @click="editForm.role = 'admin'; showRoleDropdown = false"
                                class="px-4 py-2 cursor-pointer transition flex items-center justify-between text-sm hover:bg-amber-500/10"
                                :class="editForm.role === 'admin' ? 'bg-amber-500/20 text-amber-400' : 'text-gray-300'"
                            >
                                <span><i class="fas fa-user-shield mr-2 text-gray-500"></i>管理员</span>
                                <i v-if="editForm.role === 'admin'" class="fas fa-check text-xs"></i>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="px-6 pb-6 border-t border-white/10 pt-5 flex justify-end space-x-3">
                    <button
                        @click="closeEditModal"
                        class="px-5 py-2.5 text-gray-400 hover:text-white hover:bg-white/10 rounded-xl transition"
                    >
                        取消
                    </button>
                    <button
                        @click="saveUser"
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
import { ref, onMounted } from 'vue'
import { useApi } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'

const { apiCall, currentUser } = useApi()
const { showToast } = useToast()
const { confirm } = useConfirm()

const loading = ref(false)
const saving = ref(false)
const usersList = ref([])
const showEditModal = ref(false)
const editingUser = ref(null)
const editForm = ref({ username: '', password: '', role: 'user' })
const showRoleDropdown = ref(false)

const formatDateTime = (dateStr) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    })
}

const fetchUsers = async () => {
    loading.value = true
    try {
        const data = await apiCall('/users')
        usersList.value = data.users || []
    } catch (e) {
        showToast('加载用户列表失败', 'error')
    } finally {
        loading.value = false
    }
}

const openEditUserModal = (user) => {
    editingUser.value = user
    editForm.value = {
        username: user.username,
        password: '',
        role: user.role
    }
    showRoleDropdown.value = false
    showEditModal.value = true
}

const closeEditModal = () => {
    showEditModal.value = false
    editingUser.value = null
}

const saveUser = async () => {
    saving.value = true
    try {
        const payload = { role: editForm.value.role }
        if (editForm.value.password) {
            payload.password = editForm.value.password
        }
        await apiCall(`/users/${editingUser.value.id}`, {
            method: 'PUT',
            body: JSON.stringify(payload)
        })
        showToast('用户已更新', 'success')
        closeEditModal()
        fetchUsers()
    } catch (e) {
        showToast('保存失败', 'error')
    } finally {
        saving.value = false
    }
}

const deleteUser = async (user) => {
    const confirmed = await confirm(`确定要删除用户 "${user.username}" 吗？`, { title: '删除用户', type: 'danger', confirmText: '删除' })
    if (!confirmed) return
    try {
        await apiCall(`/users/${user.id}`, { method: 'DELETE' })
        showToast('用户已删除', 'success')
        fetchUsers()
    } catch (e) {
        showToast('删除失败', 'error')
    }
}

onMounted(() => {
    fetchUsers()
})
</script>
