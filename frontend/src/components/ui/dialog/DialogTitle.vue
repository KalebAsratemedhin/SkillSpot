<template>
  <RadixDialogTitle :class="cn('text-xl font-bold text-white', $attrs.class)">
    <slot />
  </RadixDialogTitle>
</template>

<script setup lang="ts">
import { DialogTitle as RadixDialogTitle } from 'radix-vue'
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })
</script>
