<template>
  <RadixDialogDescription :class="resolvedClass">
    <slot />
  </RadixDialogDescription>
</template>

<script setup lang="ts">
import { computed, useAttrs } from 'vue'
import type { ClassValue } from 'clsx'
import { DialogDescription as RadixDialogDescription } from 'radix-vue'
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })
const attrs = useAttrs()
const resolvedClass = computed(() => cn('text-sm text-slate-400', (attrs.class ?? '') as ClassValue))
</script>
