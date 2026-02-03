<template>
    <Modal v-model="visible" size="sm" :show-close="false" :close-on-backdrop="false">
        <div class="flex items-start space-x-4">
            <div :class="['w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0', iconBgClass]">
                <i :class="[iconClass, iconColorClass]"></i>
            </div>
            <div class="flex-1">
                <h3 class="font-semibold text-white">{{ title }}</h3>
                <p class="text-gray-400 text-sm mt-1">{{ message }}</p>
            </div>
        </div>

        <template #footer>
            <button
                @click="handleCancel"
                class="px-4 py-2 text-sm text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition"
            >
                {{ cancelText }}
            </button>
            <button
                @click="handleConfirm"
                :disabled="loading"
                :class="confirmButtonClass"
            >
                <i v-if="loading" class="fas fa-spinner animate-spin mr-2"></i>
                {{ confirmText }}
            </button>
        </template>
    </Modal>
</template>

<script setup>
import { ref, computed } from 'vue'
import Modal from './Modal.vue'

const props = defineProps({
    title: {
        type: String,
        default: '确认操作'
    },
    message: {
        type: String,
        default: '确定要执行此操作吗？'
    },
    type: {
        type: String,
        default: 'warning',
        validator: (v) => ['warning', 'danger', 'info'].includes(v)
    },
    confirmText: {
        type: String,
        default: '确定'
    },
    cancelText: {
        type: String,
        default: '取消'
    }
})

const emit = defineEmits(['confirm', 'cancel'])

const visible = ref(false)
const loading = ref(false)
let resolvePromise = null

const iconClass = computed(() => {
    const icons = {
        warning: 'fas fa-exclamation-triangle',
        danger: 'fas fa-trash-alt',
        info: 'fas fa-info-circle'
    }
    return icons[props.type]
})

const iconBgClass = computed(() => {
    const classes = {
        warning: 'bg-amber-500/20',
        danger: 'bg-red-500/20',
        info: 'bg-blue-500/20'
    }
    return classes[props.type]
})

const iconColorClass = computed(() => {
    const classes = {
        warning: 'text-amber-400',
        danger: 'text-red-400',
        info: 'text-blue-400'
    }
    return classes[props.type]
})

const confirmButtonClass = computed(() => {
    const base = 'px-4 py-2 text-sm rounded-lg transition font-medium disabled:opacity-50'
    if (props.type === 'danger') {
        return `${base} bg-red-500/20 text-red-400 hover:bg-red-500/30`
    }
    return `${base} bg-gradient-to-r from-amber-500 to-orange-500 text-white hover:opacity-90`
})

const show = () => {
    visible.value = true
    return new Promise((resolve) => {
        resolvePromise = resolve
    })
}

const handleConfirm = async () => {
    loading.value = true
    emit('confirm')
    if (resolvePromise) {
        resolvePromise(true)
    }
    loading.value = false
    visible.value = false
}

const handleCancel = () => {
    emit('cancel')
    if (resolvePromise) {
        resolvePromise(false)
    }
    visible.value = false
}

defineExpose({ show })
</script>
