<template>
  <SelectItem
    :class="cn(
      'relative flex w-full cursor-default select-none items-center rounded-lg py-2 pl-3 pr-8 text-sm outline-none focus:bg-white/10 focus:text-white data-[disabled]:pointer-events-none data-[disabled]:opacity-50',
      $attrs.class
    )"
    v-bind="$attrs"
  >
    <span class="absolute right-2 flex h-3.5 w-3.5 items-center justify-center">
      <SelectItemIndicator>
        <span class="material-symbols-outlined text-amber text-sm">check</span>
      </SelectItemIndicator>
    </span>
    <SelectItemText>
      <slot />
    </SelectItemText>
  </SelectItem>
</template>

<script setup lang="ts">
import { SelectItem, SelectItemIndicator, SelectItemText } from 'radix-vue'
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })
</script>
