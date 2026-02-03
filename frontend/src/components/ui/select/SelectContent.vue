<template>
  <SelectPortal>
    <SelectContent
      :class="resolvedClass"
      :position="position"
    >
      <SelectViewport class="p-1">
        <slot />
      </SelectViewport>
    </SelectContent>
  </SelectPortal>
</template>

<script setup lang="ts">
import { computed, useAttrs } from 'vue'
import type { ClassValue } from 'clsx'
import { SelectPortal, SelectContent, SelectViewport } from 'radix-vue'
import { cn } from '@/lib/utils'

defineProps<{ position?: 'item-aligned' | 'popper' }>()
defineOptions({ inheritAttrs: false })
const attrs = useAttrs()
const baseClass = 'relative z-50 max-h-96 min-w-[8rem] overflow-hidden rounded-xl border border-white/10 bg-midnight-light text-white shadow-xl data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2'
const resolvedClass = computed(() => cn(baseClass, (attrs.class ?? '') as ClassValue))
</script>
