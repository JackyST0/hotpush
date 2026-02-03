<template>
    <div class="animate-pulse">
        <!-- Card Skeleton -->
        <template v-if="type === 'card'">
            <div v-for="i in count" :key="i" class="glass rounded-xl p-4 mb-4">
                <div class="flex items-center space-x-3 mb-4">
                    <div class="w-10 h-10 rounded-lg skeleton"></div>
                    <div class="flex-1">
                        <div class="h-4 w-24 skeleton rounded mb-2"></div>
                        <div class="h-3 w-16 skeleton rounded"></div>
                    </div>
                </div>
                <div class="space-y-3">
                    <div v-for="j in lines" :key="j" class="h-3 skeleton rounded" :style="{ width: randomWidth() }"></div>
                </div>
            </div>
        </template>

        <!-- List Skeleton -->
        <template v-else-if="type === 'list'">
            <div v-for="i in count" :key="i" class="p-5 flex items-center space-x-4 border-b border-white/5">
                <div class="w-10 h-10 rounded-xl skeleton"></div>
                <div class="flex-1">
                    <div class="h-4 skeleton rounded mb-2" :style="{ width: randomWidth() }"></div>
                    <div class="h-3 w-32 skeleton rounded"></div>
                </div>
                <div class="h-6 w-16 skeleton rounded-full"></div>
            </div>
        </template>

        <!-- Stats Skeleton -->
        <template v-else-if="type === 'stats'">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div v-for="i in 4" :key="i" class="glass rounded-xl p-5 text-center">
                    <div class="h-8 w-16 skeleton rounded mx-auto mb-2"></div>
                    <div class="h-3 w-12 skeleton rounded mx-auto"></div>
                </div>
            </div>
        </template>

        <!-- Grid Skeleton -->
        <template v-else-if="type === 'grid'">
            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
                <div v-for="i in count" :key="i" class="glass rounded-xl p-4">
                    <div class="flex items-center space-x-3 mb-4">
                        <div class="w-10 h-10 rounded-lg skeleton"></div>
                        <div class="flex-1">
                            <div class="h-4 w-24 skeleton rounded mb-2"></div>
                            <div class="h-3 w-16 skeleton rounded"></div>
                        </div>
                    </div>
                    <div class="space-y-3">
                        <div v-for="j in 5" :key="j" class="h-3 skeleton rounded" :style="{ width: randomWidth() }"></div>
                    </div>
                </div>
            </div>
        </template>

        <!-- Text Skeleton -->
        <template v-else>
            <div v-for="i in lines" :key="i" class="h-4 skeleton rounded mb-3" :style="{ width: randomWidth() }"></div>
        </template>
    </div>
</template>

<script setup>
defineProps({
    type: {
        type: String,
        default: 'text',
        validator: (v) => ['text', 'card', 'list', 'stats', 'grid'].includes(v)
    },
    count: {
        type: Number,
        default: 3
    },
    lines: {
        type: Number,
        default: 5
    }
})

const randomWidth = () => {
    return `${60 + Math.random() * 40}%`
}
</script>
