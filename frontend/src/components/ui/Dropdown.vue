<template>
    <div class="relative" ref="dropdownRef">
        <div
            @click="toggle"
            class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl cursor-pointer text-white flex items-center justify-between hover:border-orange-500/50 transition"
        >
            <span>{{ displayValue }}</span>
            <i :class="['fas fa-chevron-down text-gray-500 text-xs transition-transform', isOpen ? 'rotate-180' : '']"></i>
        </div>
        <Transition name="dropdown">
            <div
                v-if="isOpen"
                class="absolute top-full left-0 right-0 mt-1 glass rounded-lg z-20 py-1 shadow-xl max-h-60 overflow-auto"
            >
                <div
                    v-for="option in options"
                    :key="option.value"
                    @click="select(option)"
                    class="px-4 py-2 cursor-pointer transition flex items-center justify-between text-sm hover:bg-amber-500/10"
                    :class="modelValue === option.value ? 'bg-amber-500/20 text-amber-400' : 'text-gray-300'"
                >
                    <span>
                        <i v-if="option.icon" :class="[option.icon, 'mr-2 text-gray-500']"></i>
                        {{ option.label }}
                    </span>
                    <i v-if="modelValue === option.value" class="fas fa-check text-xs"></i>
                </div>
            </div>
        </Transition>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
    modelValue: [String, Number],
    options: {
        type: Array,
        required: true
        // Each option: { value, label, icon? }
    },
    placeholder: {
        type: String,
        default: '请选择'
    }
})

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)
const dropdownRef = ref(null)

const displayValue = computed(() => {
    const selected = props.options.find(o => o.value === props.modelValue)
    return selected ? selected.label : props.placeholder
})

const toggle = () => {
    isOpen.value = !isOpen.value
}

const select = (option) => {
    emit('update:modelValue', option.value)
    isOpen.value = false
}

const handleClickOutside = (e) => {
    if (dropdownRef.value && !dropdownRef.value.contains(e.target)) {
        isOpen.value = false
    }
}

onMounted(() => {
    document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
    document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
    transition: all 0.15s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
    opacity: 0;
    transform: translateY(-4px);
}
</style>
