<template>
  <div class="flex flex-col-reverse sm:flex-row sm:justify-end sm:gap-3 pt-4" :class="resolvedClass">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed, useAttrs } from 'vue'
import type { ClassValue } from 'clsx'
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })
const attrs = useAttrs()
const resolvedClass = computed(() => cn('flex flex-col-reverse sm:flex-row sm:justify-end sm:gap-3 pt-4', (attrs.class ?? '') as ClassValue))
</script>
