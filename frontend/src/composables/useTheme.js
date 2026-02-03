import { ref, watchEffect } from 'vue'

// 获取默认主题：优先使用用户保存的设置，否则默认白天模式
const getDefaultTheme = () => {
    const saved = localStorage.getItem('hotpush_dark_mode')
    if (saved !== null) {
        return saved === 'true'
    }
    // 默认白天模式
    return false
}

const isDarkMode = ref(getDefaultTheme())

export function useTheme() {
    const toggleDarkMode = () => {
        isDarkMode.value = !isDarkMode.value
        localStorage.setItem('hotpush_dark_mode', isDarkMode.value)
    }

    // Apply theme class to document
    watchEffect(() => {
        if (isDarkMode.value) {
            document.documentElement.classList.remove('light-mode')
        } else {
            document.documentElement.classList.add('light-mode')
        }
    })

    return {
        isDarkMode,
        toggleDarkMode
    }
}
