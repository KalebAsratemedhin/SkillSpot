<template>
  <div
    class="group flex flex-col sm:flex-row sm:items-center gap-4 py-5 px-4 sm:px-6 rounded-xl border transition-all"
    :class="dark
      ? 'bg-midnight-light border-white/10 shadow-sm hover:shadow-md hover:border-amber/30'
      : 'bg-white border-slate-200 shadow-sm hover:shadow-md hover:border-slate-300'"
  >
    <router-link :to="`/jobs/${job.id}`" class="flex-1 min-w-0 no-underline text-inherit">
      <div class="flex flex-wrap items-center gap-2 mb-1">
        <span v-if="badge" :class="badgeClassString">{{ badge }}</span>
      </div>
      <h3
        class="text-lg font-bold mb-2 group-hover:text-amber transition-colors line-clamp-1"
        :class="dark ? 'text-white' : 'text-midnight'"
      >
        {{ job.title }}
      </h3>
      <div
        class="flex flex-wrap gap-x-4 gap-y-1 text-sm mb-2"
        :class="dark ? 'text-slate-400' : 'text-slate-600'"
      >
        <span class="flex items-center gap-1">
          <span class="material-symbols-outlined text-amber text-base">payments</span>
          {{ formatBudget }}
        </span>
        <span class="flex items-center gap-1">
          <span class="material-symbols-outlined text-amber text-base">location_on</span>
          {{ job.location }}
        </span>
      </div>
      <p
        v-if="truncatedDescription"
        class="text-sm mb-2 line-clamp-2"
        :class="dark ? 'text-slate-400' : 'text-slate-600'"
      >
        {{ truncatedDescription }}
      </p>
      <div v-if="jobTags.length" class="flex flex-wrap gap-1.5">
        <span
          v-for="tag in jobTags"
          :key="tag"
          class="px-2 py-0.5 text-xs font-medium rounded"
          :class="dark ? 'bg-white/10 text-slate-300' : 'bg-slate-100 text-midnight'"
        >
          {{ tag }}
        </span>
      </div>
    </router-link>
    <router-link
      v-if="showApply"
      :to="`/jobs/${job.id}`"
      class="flex-shrink-0 inline-flex items-center justify-center rounded-lg text-xs font-semibold bg-midnight hover:bg-midnight-light text-white h-8 px-3 py-1.5 sm:self-center"
      @click.prevent.stop="$router.push(`/jobs/${job.id}`)"
    >
      Apply
    </router-link>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { type Job } from '@/services/jobs'

interface Props {
  job: Job
  rating?: number
  reviewCount?: number
  badge?: string
  /** Show "Apply for Job" button (hide for clients viewing job cards) */
  showApply?: boolean
  /** Dark variant for use on dark backgrounds (e.g. profile Jobs tab) */
  dark?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showApply: true,
  dark: false,
})

const DESCRIPTION_MAX_LENGTH = 120

const truncatedDescription = computed(() => {
  const d = props.job.description?.trim()
  if (!d) return ''
  if (d.length <= DESCRIPTION_MAX_LENGTH) return d
  return d.slice(0, DESCRIPTION_MAX_LENGTH).trim() + '…'
})

const jobTags = computed(() => {
  if (props.job.tags && props.job.tags.length) return props.job.tags
  if (props.job.required_skills?.length) return props.job.required_skills.map(s => s.name)
  return []
})

const isHourly = computed(() => props.job.payment_schedule === 'HOURLY' || props.job.budget_type === 'hourly')

const formatBudget = computed(() => {
  if (isHourly.value) {
    const min = props.job.budget_min ?? 0
    const max = props.job.budget_max ?? min
    return min === max ? `Br ${(min).toLocaleString()}/hr` : `Br ${(min).toLocaleString()} – ${(max).toLocaleString()} Br/hr`
  }
  if (props.job.budget_type === 'fixed' || props.job.payment_schedule === 'FIXED') {
    return `Br ${(props.job.budget_max ?? props.job.budget_min ?? 0).toLocaleString()} fixed`
  }
  return `Br ${(props.job.budget_min ?? 0).toLocaleString()} – ${(props.job.budget_max ?? 0).toLocaleString()}`
})

const badgeClassString = computed(() => {
  const badges: Record<string, string> = {
    'Insured': 'bg-emerald-100 text-emerald-700',
    'Emergency': 'bg-blue-100 text-blue-700',
    'Verified RN': 'bg-emerald-100 text-emerald-700',
  }
  const base = props.dark ? 'bg-white/10 text-slate-300' : 'bg-slate-100 text-slate-700'
  const badgeClass = badges[props.badge || ''] || base
  return `text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded ${badgeClass}`
})
</script>
