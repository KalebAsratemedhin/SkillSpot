<template>
  <div
    :class="[
      'shrink-0 overflow-hidden flex items-center justify-center font-semibold',
      roundedClass,
      sizeClass,
      src ? 'bg-slate-200' : fallbackClass,
    ]"
    :aria-label="name || 'User avatar'"
  >
    <img
      v-if="src && !imgFailed"
      :src="src"
      alt=""
      class="h-full w-full object-cover"
      @error="imgFailed = true"
    />
    <span v-else :class="textClass">{{ initials }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    src?: string | null
    name?: string | null
    /** Tailwind size classes, e.g. size-10 or size-11 */
    sizeClass?: string
    roundedClass?: string
    fallbackClass?: string
    textClass?: string
  }>(),
  {
    src: null,
    name: null,
    sizeClass: 'size-10',
    roundedClass: 'rounded-full',
    fallbackClass: 'bg-gradient-to-br from-midnight to-slate-700 text-white',
    textClass: 'text-sm',
  }
)

const imgFailed = ref(false)
watch(
  () => props.src,
  () => {
    imgFailed.value = false
  }
)

const initials = computed(() => {
  const raw = (props.name || '').trim()
  if (!raw) return '?'
  const parts = raw.split(/\s+/).filter(Boolean)
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  }
  // email-like
  if (raw.includes('@')) return raw[0].toUpperCase()
  return raw[0].toUpperCase()
})
</script>
