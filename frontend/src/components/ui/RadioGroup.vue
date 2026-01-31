<template>
  <div :class="cn('grid gap-2', props.class)" role="radiogroup">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { cn } from '@/lib/utils'

interface Props {
  modelValue?: string
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  class: '',
})

defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>
