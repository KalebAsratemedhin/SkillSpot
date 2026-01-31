<template>
  <RadixDialogClose as-child>
    <slot />
  </RadixDialogClose>
</template>

<script setup lang="ts">
import { DialogClose as RadixDialogClose } from 'radix-vue'
</script>
