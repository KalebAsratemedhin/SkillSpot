<template>
  <RadixDialogTitle :class="resolvedClass">
    <slot />
  </RadixDialogTitle>
</template>

<script setup lang="ts">
import { computed, useAttrs } from 'vue'
import type { ClassValue } from 'clsx'
import { DialogTitle as RadixDialogTitle } from 'radix-vue'
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })
const attrs = useAttrs()
const resolvedClass = computed(() => cn('text-xl font-bold text-white', (attrs.class ?? '') as ClassValue))
</script>
