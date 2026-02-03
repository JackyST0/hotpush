<template>
    <Teleport to="body">
        <Transition name="modal">
            <div
                v-if="modelValue"
                class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
                @click.self="closeOnBackdrop && $emit('update:modelValue', false)"
            >
                <div :class="['glass rounded-2xl w-full overflow-hidden', sizeClass]">
                    <!-- Header -->
                    <div v-if="title || $slots.header" class="p-6 border-b border-white/10 flex items-center justify-between">
                        <slot name="header">
                            <h3 class="font-bold text-xl text-white">{{ title }}</h3>
                        </slot>
                        <button
                            v-if="showClose"
                            @click="$emit('update:modelValue', false)"
                            class="text-gray-500 hover:text-white transition w-8 h-8 rounded-lg hover:bg-white/10 flex items-center justify-center"
                        >
                            <i class="fas fa-times"></i>
                        </button>
                    </div>

                    <!-- Body -->
                    <div :class="['p-6', bodyClass]">
                        <slot></slot>
                    </div>

                    <!-- Footer -->
                    <div v-if="$slots.footer" class="px-6 pb-6 border-t border-white/10 pt-5 flex justify-end space-x-3">
                        <slot name="footer"></slot>
                    </div>
                </div>
            </div>
        </Transition>
    </Teleport>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    modelValue: Boolean,
    title: String,
    size: {
        type: String,
        default: 'md',
        validator: (v) => ['sm', 'md', 'lg', 'xl'].includes(v)
    },
    showClose: {
        type: Boolean,
        default: true
    },
    closeOnBackdrop: {
        type: Boolean,
        default: true
    },
    bodyClass: String
})

defineEmits(['update:modelValue'])

const sizeClass = computed(() => {
    const sizes = {
        sm: 'max-w-sm',
        md: 'max-w-md',
        lg: 'max-w-lg',
        xl: 'max-w-xl'
    }
    return sizes[props.size]
})
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
    transition: opacity 0.2s ease;
}
.modal-enter-active > div,
.modal-leave-active > div {
    transition: transform 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
    opacity: 0;
}
.modal-enter-from > div {
    transform: scale(0.95);
}
.modal-leave-to > div {
    transform: scale(0.95);
}
</style>
