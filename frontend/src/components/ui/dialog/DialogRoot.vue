<template>
  <DialogRoot
    :open="open"
    @update:open="(v: boolean) => $emit('update:open', v)"
  >
    <slot />
  </DialogRoot>
</template>

<script setup lang="ts">
import { DialogRoot } from 'radix-vue'

defineProps<{
  open?: boolean
}>()
defineEmits<{
  'update:open': [value: boolean]
}>()
</script>
