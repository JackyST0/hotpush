<template>
    <div class="glass rounded-xl p-4 flex items-center justify-between mb-6">
        <div>
            <h2 class="text-2xl font-bold text-white">{{ viewTitle }}</h2>
            <p class="text-gray-500 text-sm mt-1">{{ viewSubtitle }}</p>
        </div>
        <div class="flex items-center space-x-4">
            <span v-if="lastUpdate" class="text-sm text-gray-500">
                <i class="far fa-clock mr-1"></i>{{ lastUpdate }}
            </span>
            <button
                @click="toggleDarkMode"
                class="mode-toggle"
                :title="isDarkMode ? '切换到白天模式' : '切换到黑夜模式'"
            >
                <i :class="isDarkMode ? 'fas fa-sun text-amber-400' : 'fas fa-moon text-amber-600'" class="text-sm"></i>
            </button>
            <button
                @click="$emit('refresh')"
                class="action-btn flex items-center space-x-2"
            >
                <i class="fas fa-sync-alt"></i>
                <span>刷新</span>
            </button>
        </div>
    </div>
</template>

<script setup>
import { useTheme } from '../composables/useTheme'

defineProps({
    viewTitle: String,
    viewSubtitle: String,
    lastUpdate: String
})

defineEmits(['refresh'])

const { isDarkMode, toggleDarkMode } = useTheme()
</script>
