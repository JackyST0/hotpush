import { ref, createApp, h } from 'vue'
import ConfirmDialog from '../components/ui/ConfirmDialog.vue'

// 全局确认对话框状态
const confirmState = ref({
    visible: false,
    title: '确认操作',
    message: '确定要执行此操作吗？',
    type: 'warning',
    confirmText: '确定',
    cancelText: '取消',
    resolve: null
})

export function useConfirm() {
    const confirm = (message, options = {}) => {
        return new Promise((resolve) => {
            confirmState.value = {
                visible: true,
                title: options.title || '确认操作',
                message: message,
                type: options.type || 'warning',
                confirmText: options.confirmText || '确定',
                cancelText: options.cancelText || '取消',
                resolve
            }
        })
    }

    const handleConfirm = () => {
        if (confirmState.value.resolve) {
            confirmState.value.resolve(true)
        }
        confirmState.value.visible = false
    }

    const handleCancel = () => {
        if (confirmState.value.resolve) {
            confirmState.value.resolve(false)
        }
        confirmState.value.visible = false
    }

    return {
        confirmState,
        confirm,
        handleConfirm,
        handleCancel
    }
}
