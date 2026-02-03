<template>
    <label class="toggle-switch" :style="scaleStyle" @click.prevent="toggle">
        <div :class="['toggle-slider', modelValue ? 'on' : 'off']">
            <span class="toggle-label-on">开</span>
            <span class="toggle-label-off">关</span>
        </div>
    </label>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    modelValue: Boolean,
    scale: {
        type: Number,
        default: 1
    },
    disabled: Boolean
})

const emit = defineEmits(['update:modelValue'])

const scaleStyle = computed(() => {
    if (props.scale === 1) return {}
    return {
        transform: `scale(${props.scale})`,
        transformOrigin: 'left center'
    }
})

const toggle = () => {
    if (!props.disabled) {
        emit('update:modelValue', !props.modelValue)
    }
}
</script>
