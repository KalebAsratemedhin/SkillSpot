<template>
  <div
    class="animate-pulse"
    :class="compact ? 'space-y-2 py-4' : 'space-y-3 py-6'"
    role="status"
    aria-live="polite"
    aria-label="Loading"
  >
    <div
      v-for="(w, i) in bars"
      :key="i"
      class="h-3 rounded-lg bg-slate-200/90"
      :style="{ width: w }"
    />
    <span class="sr-only">Loading…</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    /** Number of skeleton lines */
    lines?: number
    compact?: boolean
  }>(),
  { lines: 4, compact: false }
)

const widths = ['92%', '78%', '85%', '64%', '70%', '88%']

const bars = computed(() =>
  Array.from({ length: Math.max(1, props.lines) }, (_, i) => widths[i % widths.length])
)
</script>
