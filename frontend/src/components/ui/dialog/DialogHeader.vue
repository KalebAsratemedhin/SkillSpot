<template>
  <div class="flex flex-col space-y-1.5 text-center sm:text-left" :class="cn($attrs.class)">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })
</script>
