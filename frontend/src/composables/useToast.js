import { ref } from 'vue'

const toasts = ref([])

export function useToast() {
    const showToast = (message, type = 'info') => {
        const id = Date.now()
        toasts.value.push({ id, message, type })
        setTimeout(() => {
            const index = toasts.value.findIndex(t => t.id === id)
            if (index > -1) {
                toasts.value.splice(index, 1)
            }
        }, 3000)
    }

    return {
        toasts,
        showToast
    }
}
