<template>
  <RadixDialogDescription :class="cn('text-sm text-slate-400', $attrs.class)">
    <slot />
  </RadixDialogDescription>
</template>

<script setup lang="ts">
import { DialogDescription as RadixDialogDescription } from 'radix-vue'
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })
</script>
