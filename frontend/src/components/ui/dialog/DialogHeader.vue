<template>
  <div class="flex flex-col space-y-1.5 text-center sm:text-left" :class="resolvedClass">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed, useAttrs } from 'vue'
import type { ClassValue } from 'clsx'
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })
const attrs = useAttrs()
const resolvedClass = computed(() => cn('flex flex-col space-y-1.5 text-center sm:text-left', (attrs.class ?? '') as ClassValue))
</script>
