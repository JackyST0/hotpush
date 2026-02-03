<template>
    <div class="fixed top-5 left-1/2 -translate-x-1/2 z-[99999] space-y-2 flex flex-col items-center">
        <div
            v-for="toast in toasts"
            :key="toast.id"
            :class="[
                'toast px-4 py-2.5 rounded-lg shadow-lg backdrop-blur-md flex items-center space-x-2 text-sm border',
                toast.type === 'success' ? 'bg-amber-950/80 text-amber-200 border-amber-800/50' :
                toast.type === 'error' ? 'bg-red-950/80 text-red-200 border-red-800/50' :
                'bg-amber-900/80 text-amber-100 border-amber-700/50'
            ]"
        >
            <i :class="[
                'text-xs',
                toast.type === 'success' ? 'fas fa-check-circle' :
                toast.type === 'error' ? 'fas fa-exclamation-circle' :
                'fas fa-info-circle'
            ]"></i>
            <span>{{ toast.message }}</span>
        </div>
    </div>
</template>

<script setup>
import { useToast } from '../composables/useToast'
const { toasts } = useToast()
</script>
