<template>
  <router-link :to="`/jobs/${job.id}`" class="block no-underline text-inherit">
    <Card class="group hover:shadow-xl transition-all duration-300 border border-slate-200 hover:border-amber/30 cursor-pointer h-full">
      <CardContent class="p-6">
        <div class="flex justify-between items-start mb-4">
          <div class="flex items-center gap-1 text-amber">
            <span class="material-symbols-outlined text-[18px] fill-1">star</span>
            <span class="text-sm font-bold text-midnight">{{ rating || '4.9' }}</span>
            <span class="text-xs text-slate-400 font-normal">({{ reviewCount || '124' }} reviews)</span>
          </div>
          <span v-if="badge" :class="badgeClassString">
            {{ badge }}
          </span>
        </div>
        <h3 class="text-xl font-bold text-midnight mb-3 group-hover:text-amber transition-colors">
          {{ job.title }}
        </h3>
        <div class="flex flex-wrap gap-4 mb-4">
          <div class="flex items-center gap-1.5 text-slate-600 text-sm">
            <span class="material-symbols-outlined text-[18px] text-amber">payments</span>
            <span>{{ formatBudget }}</span>
          </div>
          <div class="flex items-center gap-1.5 text-slate-600 text-sm">
            <span class="material-symbols-outlined text-[18px] text-amber">location_on</span>
            <span>{{ job.location }}</span>
          </div>
        </div>
        <div v-if="jobTags.length" class="flex flex-wrap gap-2 mb-6">
          <span
            v-for="tag in jobTags.slice(0, 3)"
            :key="tag"
            class="px-3 py-1 bg-slate-100 text-midnight text-xs font-semibold rounded-lg"
          >
            {{ tag }}
          </span>
        </div>
        <span
          v-if="showApply"
          class="inline-flex items-center justify-center rounded-md text-sm font-medium bg-midnight hover:bg-midnight-light text-white h-10 px-4 py-2 w-full"
        >
          Apply for Job
        </span>
      </CardContent>
    </Card>
  </router-link>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { type Job } from '@/services/jobs'
import Card from './ui/Card.vue'
import CardContent from './ui/CardContent.vue'

interface Props {
  job: Job
  rating?: number
  reviewCount?: number
  badge?: string
  /** Show "Apply for Job" button (hide for clients viewing job cards) */
  showApply?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showApply: true,
})

const jobTags = computed(() => {
  if (props.job.tags && props.job.tags.length) return props.job.tags
  if (props.job.required_skills?.length) return props.job.required_skills.map(s => s.name)
  return []
})

const formatBudget = computed(() => {
  if (props.job.budget_type === 'hourly') {
    return `$${props.job.budget_min || 0} - $${props.job.budget_max || 0} / hr`
  } else if (props.job.budget_type === 'fixed') {
    return `$${props.job.budget_max || props.job.budget_min || 0}`
  }
  return `$${props.job.budget_min || 0} - $${props.job.budget_max || 0}`
})

const badgeClassString = computed(() => {
  const badges: Record<string, string> = {
    'Insured': 'bg-emerald-100 text-emerald-700',
    'Emergency': 'bg-blue-100 text-blue-700',
    'Verified RN': 'bg-emerald-100 text-emerald-700',
  }
  const badgeClass = badges[props.badge || ''] || 'bg-slate-100 text-slate-700'
  return `text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded ${badgeClass}`
})
</script>
