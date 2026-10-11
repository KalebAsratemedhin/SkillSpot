<template>
  <div
    v-if="totalCount > 0"
    class="flex flex-col sm:flex-row items-center justify-between gap-4 pt-6"
  >
    <div class="flex items-center gap-2">
      <span :class="labelClass">Per page</span>
      <Select
        :model-value="String(pageSize)"
        @update:model-value="onPageSizeSelect"
      >
        <SelectTrigger
          :class="[
            'w-[5.5rem] h-9 rounded-lg text-sm font-medium',
            triggerClass,
          ]"
        >
          <SelectValue :placeholder="String(pageSize)" />
        </SelectTrigger>
        <SelectContent :class="contentClass">
          <SelectItem
            v-for="size in resolvedPageSizeOptions"
            :key="size"
            :value="String(size)"
            :class="['rounded-lg cursor-pointer', itemClass]"
          >
            {{ size }}
          </SelectItem>
        </SelectContent>
      </Select>
    </div>
    <div class="flex items-center gap-2">
      <Button
        variant="outline"
        size="sm"
        :disabled="currentPage === 1 || loading"
        :class="buttonClass"
        @click="$emit('goToPage', currentPage - 1)"
      >
        <span class="material-symbols-outlined text-lg">chevron_left</span>
      </Button>
      <span :class="[labelClass, 'text-sm px-3']">
        Page {{ currentPage }} of {{ totalPages }}
      </span>
      <Button
        variant="outline"
        size="sm"
        :disabled="currentPage === totalPages || loading"
        :class="buttonClass"
        @click="$emit('goToPage', currentPage + 1)"
      >
        <span class="material-symbols-outlined text-lg">chevron_right</span>
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import Button from '@/components/ui/Button.vue'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

const props = withDefaults(
  defineProps<{
    currentPage: number
    totalPages: number
    totalCount: number
    pageSize: number
    loading?: boolean
    /** 'default' = light (slate) for light backgrounds; 'dark' = light text for dark backgrounds */
    variant?: 'default' | 'dark'
  }>(),
  { loading: false, variant: 'default' }
)

const emit = defineEmits<{
  goToPage: [page: number]
  updatePageSize: [size: number]
}>()

const basePageSizeOptions = [5, 10, 15, 20] as const

/** Include current pageSize even if a view uses a non-standard default (e.g. 12). */
const resolvedPageSizeOptions = computed(() => {
  const set = new Set<number>([...basePageSizeOptions])
  if (props.pageSize > 0) set.add(props.pageSize)
  return [...set].sort((a, b) => a - b)
})

const isDark = computed(() => props.variant === 'dark')

const labelClass = computed(() =>
  isDark.value ? 'text-slate-400' : 'text-slate-600'
)

/** `!text-*` wins over SelectTrigger’s default `text-white` (invisible on white). */
const triggerClass = computed(() =>
  isDark.value
    ? 'border-white/10 bg-white/5 !text-slate-200 hover:!text-slate-200 focus:ring-amber/40'
    : 'border-slate-200 bg-white !text-slate-900 hover:!text-slate-900 hover:bg-slate-50 focus:ring-amber/20'
)

const contentClass = computed(() =>
  isDark.value
    ? 'rounded-xl border border-white/10 bg-midnight text-slate-200'
    : 'rounded-xl border border-slate-200 bg-white text-slate-900'
)

const itemClass = computed(() =>
  isDark.value
    ? 'focus:bg-white/10 focus:text-white data-[highlighted]:bg-white/10 data-[highlighted]:text-white'
    : 'focus:bg-slate-100 focus:text-slate-900 data-[highlighted]:bg-slate-100 data-[highlighted]:text-slate-900'
)

const buttonClass = computed(() =>
  isDark.value
    ? 'border-white/10 text-slate-400 hover:text-white hover:border-white/20 disabled:opacity-50'
    : 'border-slate-200 text-slate-600 hover:text-slate-900'
)

function onPageSizeSelect(value: string) {
  const size = Number(value)
  if (size === props.pageSize || Number.isNaN(size)) return
  emit('updatePageSize', size)
}
</script>
