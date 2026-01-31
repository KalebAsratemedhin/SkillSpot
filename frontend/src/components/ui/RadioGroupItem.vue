<template>
  <div class="flex items-center space-x-2">
    <input
      :id="id"
      :value="value"
      :checked="modelValue === value"
      type="radio"
      :class="cn(
        'h-4 w-4 border-primary text-primary focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
        props.class
      )"
      @change="$emit('update:modelValue', value)"
    />
    <label
      v-if="label"
      :for="id"
      class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
    >
      {{ label }}
    </label>
    <slot />
  </div>
</template>

<script setup lang="ts">
import { cn } from '@/lib/utils'

interface Props {
  id?: string
  value: string
  modelValue?: string
  label?: string
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  id: () => `radio-${Math.random().toString(36).substr(2, 9)}`,
  class: '',
})

defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>
