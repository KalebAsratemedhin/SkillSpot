<template>
  <div class="flex flex-col-reverse sm:flex-row sm:justify-end sm:gap-3 pt-4" :class="cn($attrs.class)">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })
</script>
