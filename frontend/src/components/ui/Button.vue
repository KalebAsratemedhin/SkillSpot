<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="cn(buttonVariants({ variant, size }), props.class)"
    @click="$emit('click', $event)"
  >
    <span v-if="loading" class="material-symbols-outlined animate-spin">refresh</span>
    <slot />
  </button>
</template>

<script setup lang="ts">
import { buttonVariants, type ButtonProps } from './button'
import { cn } from '@/lib/utils'

const props = withDefaults(defineProps<ButtonProps>(), {
  variant: 'default',
  size: 'default',
  type: 'button',
  disabled: false,
  loading: false,
  class: '',
})

defineEmits<{
  click: [event: MouseEvent]
}>()
</script>
