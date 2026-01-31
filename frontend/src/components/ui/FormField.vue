<template>
  <div class="space-y-2">
    <slot />
    <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
interface Props {
  error?: string
}

defineProps<Props>()
</script>
