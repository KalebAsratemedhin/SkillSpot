<template>
  <AppLayout>
    <div class="w-full max-w-[1100px] mx-auto px-4 md:px-6 lg:px-10 py-6 md:py-10">
      <div v-if="loading && !provider" class="space-y-8">
        <div class="flex flex-col md:flex-row gap-8 items-start animate-pulse">
          <div class="size-28 md:size-36 rounded-2xl bg-slate-200 shrink-0" />
          <div class="flex-1 space-y-3 w-full">
            <div class="h-9 bg-slate-200 rounded-lg w-2/3" />
            <div class="h-4 bg-slate-200 rounded w-1/3" />
            <SectionLoader :lines="3" compact />
          </div>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div v-for="i in 4" :key="i" class="h-20 rounded-2xl bg-slate-200 animate-pulse" />
        </div>
        <div class="rounded-2xl border border-gray-100 bg-white px-6">
          <SectionLoader :lines="5" />
        </div>
      </div>
      <div v-else-if="!provider" class="text-center py-16">
        <p class="text-slate-500 mb-4">Provider not found.</p>
        <router-link to="/browse">
          <Button variant="default">Browse</Button>
        </router-link>
      </div>
      <div v-else class="space-y-8">
        <div class="flex flex-col md:flex-row gap-8 items-start">
          <div
            v-if="provider.avatar"
            class="size-28 md:size-36 rounded-2xl bg-cover bg-center shrink-0 ring-4 ring-amber/20 shadow-lg"
            :style="{ backgroundImage: `url(${provider.avatar})` }"
          />
          <div
            v-else
            class="size-28 md:size-36 rounded-2xl bg-slate-100 text-amber font-black flex items-center justify-center shrink-0 text-4xl ring-4 ring-amber/20"
          >
            {{ initials }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex flex-wrap items-center gap-3">
              <h1 class="text-3xl md:text-4xl font-extrabold text-midnight tracking-tight">
                {{ provider.full_name || 'Service provider' }}
              </h1>
              <span
                v-if="provider.is_verified"
                class="inline-flex items-center gap-1 rounded-lg bg-amber/10 px-3 py-1 text-sm font-bold text-amber border border-amber/20"
              >
                <span class="material-symbols-outlined text-base">verified</span>
                Verified
              </span>
            </div>
            <p v-if="provider.location" class="mt-2 text-slate-500 flex items-center gap-1">
              <span class="material-symbols-outlined text-amber text-lg">location_on</span>
              {{ provider.location }}
            </p>
            <div class="mt-4 flex flex-wrap gap-4 text-sm">
              <div v-if="provider.hourly_rate" class="font-bold text-midnight text-lg">
                ${{ Number(provider.hourly_rate).toLocaleString() }}<span class="text-slate-500 font-medium text-sm">/hr</span>
              </div>
              <div v-if="provider.rating.count > 0" class="flex items-center gap-1 text-slate-600">
                <span class="material-symbols-outlined text-amber fill-1">star</span>
                <span class="font-bold text-midnight">{{ Number(provider.rating.average).toFixed(1) }}</span>
                <span>({{ provider.rating.count }} reviews)</span>
              </div>
              <div v-else class="text-slate-400">No reviews yet</div>
              <div v-if="provider.years_of_experience" class="text-slate-600">
                {{ provider.years_of_experience }}+ years experience
              </div>
              <div v-if="provider.availability" class="text-slate-600 capitalize">
                {{ provider.availability.replace(/_/g, ' ').toLowerCase() }}
              </div>
            </div>
            <p v-if="provider.member_since" class="mt-2 text-xs text-slate-400">
              Member since {{ formatMemberSince(provider.member_since) }}
            </p>
          </div>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
          <div class="rounded-2xl border border-gray-100 bg-white p-4 md:p-5 shadow-sm">
            <p class="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Earned</p>
            <p class="text-xl md:text-2xl font-extrabold text-midnight tracking-tight">{{ formatMoney(provider.total_earnings) }}</p>
          </div>
          <div class="rounded-2xl border border-gray-100 bg-white p-4 md:p-5 shadow-sm">
            <p class="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">In progress</p>
            <p class="text-xl md:text-2xl font-extrabold text-midnight tracking-tight">{{ provider.jobs_in_progress_count ?? inProgressJobs.length }}</p>
          </div>
          <div class="rounded-2xl border border-gray-100 bg-white p-4 md:p-5 shadow-sm">
            <p class="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Closed jobs</p>
            <p class="text-xl md:text-2xl font-extrabold text-midnight tracking-tight">{{ provider.jobs_closed_count ?? closedJobs.length }}</p>
          </div>
          <div class="rounded-2xl border border-gray-100 bg-white p-4 md:p-5 shadow-sm">
            <p class="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Rating</p>
            <p class="text-xl md:text-2xl font-extrabold text-midnight tracking-tight">
              <template v-if="provider.rating.count > 0">{{ Number(provider.rating.average).toFixed(1) }}</template>
              <template v-else>—</template>
            </p>
          </div>
        </div>

        <section v-if="provider.bio" class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 md:p-8">
          <h2 class="text-lg font-bold text-midnight mb-3">About</h2>
          <p class="text-slate-600 leading-relaxed whitespace-pre-wrap">{{ provider.bio }}</p>
        </section>

        <section class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 md:p-8">
          <h2 class="text-lg font-bold text-midnight mb-4">Skills</h2>
          <div v-if="displaySkills.length" class="flex flex-wrap gap-2">
            <span
              v-for="s in displaySkills"
              :key="s.id"
              class="px-4 py-2 rounded-xl bg-amber/10 border border-amber/20 text-sm font-bold text-amber"
            >
              {{ s.name }}
            </span>
          </div>
          <p v-else class="text-slate-400 text-sm">No skills listed.</p>
        </section>

        <section
          v-if="provider.certifications?.length"
          class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 md:p-8"
        >
          <h2 class="text-lg font-bold text-midnight mb-4">Certifications</h2>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="c in provider.certifications"
              :key="c.id"
              class="px-4 py-2 rounded-xl bg-slate-100 text-sm font-semibold text-midnight"
            >
              {{ c.name }}
            </span>
          </div>
        </section>

        <section class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 md:p-8">
          <div class="flex items-center justify-between gap-3 mb-4">
            <h2 class="text-lg font-bold text-midnight">In progress</h2>
            <span class="text-xs font-bold uppercase tracking-wider text-amber bg-amber/10 border border-amber/20 px-2.5 py-1 rounded-lg">
              {{ provider.jobs_in_progress_count ?? inProgressJobs.length }}
            </span>
          </div>
          <ul v-if="inProgressJobs.length" class="space-y-3">
            <li
              v-for="job in inProgressJobs"
              :key="job.contract_id"
              class="rounded-xl border border-amber/20 bg-amber/5 p-4"
            >
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div class="min-w-0">
                  <h3 class="font-bold text-midnight">{{ job.job_title || 'Contract' }}</h3>
                  <p class="text-xs text-slate-500 mt-1">
                    Started {{ formatWorkDate(job.started_at) }}
                  </p>
                </div>
                <div class="text-right shrink-0">
                  <span class="inline-block text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded border bg-amber/10 text-amber border-amber/20">
                    Active
                  </span>
                  <p v-if="job.amount != null" class="text-sm font-bold text-midnight mt-2">
                    {{ formatMoney(job.amount) }}
                  </p>
                </div>
              </div>
            </li>
          </ul>
          <p v-else class="text-slate-400 text-sm">No jobs in progress.</p>
        </section>

        <section class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 md:p-8">
          <div class="flex items-center justify-between gap-3 mb-4">
            <h2 class="text-lg font-bold text-midnight">Closed jobs</h2>
            <span class="text-xs font-bold uppercase tracking-wider text-slate-500 bg-slate-100 border border-slate-200 px-2.5 py-1 rounded-lg">
              {{ provider.jobs_closed_count ?? closedJobs.length }}
            </span>
          </div>
          <ul v-if="closedJobs.length" class="space-y-4">
            <li
              v-for="job in closedJobs"
              :key="job.contract_id"
              class="rounded-xl border border-slate-200 bg-slate-50 p-4"
            >
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div class="min-w-0 flex-1">
                  <h3 class="font-bold text-midnight">{{ job.job_title || 'Contract' }}</h3>
                  <p class="text-xs text-slate-500 mt-1">
                    <template v-if="job.completed_at">Closed {{ formatWorkDate(job.completed_at) }}</template>
                    <template v-else-if="job.started_at">Started {{ formatWorkDate(job.started_at) }}</template>
                  </p>
                </div>
                <div class="text-right shrink-0">
                  <span
                    :class="[
                      'inline-block text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded border',
                      job.status === 'TERMINATED'
                        ? 'bg-slate-200/80 text-slate-600 border-slate-300'
                        : 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20',
                    ]"
                  >
                    {{ job.status === 'TERMINATED' ? 'Terminated' : 'Completed' }}
                  </span>
                  <p v-if="job.amount != null" class="text-sm font-bold text-midnight mt-2">
                    {{ formatMoney(job.amount) }}
                  </p>
                </div>
              </div>
              <div
                v-if="job.review"
                class="mt-3 pt-3 border-t border-slate-200/80"
              >
                <div class="flex items-center gap-1 text-amber mb-1">
                  <span
                    v-for="i in 5"
                    :key="i"
                    class="material-symbols-outlined text-base"
                    :class="i <= job.review.score ? 'text-amber' : 'text-slate-300'"
                  >star</span>
                  <span class="text-xs font-bold text-slate-500 ml-1">{{ job.review.score }}/5</span>
                </div>
                <p v-if="job.review.comment" class="text-sm text-slate-600 leading-relaxed">
                  “{{ job.review.comment }}”
                </p>
                <p v-if="job.review.rater_name" class="text-xs text-slate-400 mt-1">
                  — {{ job.review.rater_name }}
                </p>
              </div>
              <p v-else class="mt-3 text-xs text-slate-400">No review for this job.</p>
            </li>
          </ul>
          <p v-else class="text-slate-400 text-sm">No closed jobs yet.</p>
        </section>

        <section class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 md:p-8">
          <h2 class="text-lg font-bold text-midnight mb-4">Experience</h2>
          <ul v-if="experiences.length" class="space-y-4">
            <li
              v-for="exp in experiences"
              :key="exp.id"
              class="border-l-2 border-amber/30 pl-4"
            >
              <div class="flex flex-wrap items-center gap-2">
                <h3 class="font-bold text-midnight">{{ exp.title }}</h3>
                <span
                  v-if="exp.is_current"
                  class="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded bg-amber/10 text-amber border border-amber/20"
                >
                  Current
                </span>
              </div>
              <p v-if="exp.company_name" class="text-sm text-slate-500">{{ exp.company_name }}</p>
              <p v-if="exp.location" class="text-xs text-slate-400">{{ exp.location }}</p>
              <p v-if="exp.description" class="text-sm text-slate-600 mt-1">{{ exp.description }}</p>
              <p class="text-xs text-slate-400 mt-1">
                {{ formatExpDate(exp.start_date) }} –
                {{ exp.is_current ? 'Present' : formatExpDate(exp.end_date || '') }}
              </p>
            </li>
          </ul>
          <p v-else class="text-slate-400 text-sm">No experience listed yet.</p>
        </section>

        <div class="flex flex-wrap gap-3">
          <router-link to="/browse">
            <Button variant="outline" class="border-slate-200 text-slate-700">Back to browse</Button>
          </router-link>
          <router-link v-if="!authStore.isAuthenticated" :to="{ name: 'login', query: { redirect: route.fullPath } }">
            <Button variant="default">Sign in to hire</Button>
          </router-link>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { formatMoney } from '@/lib/utils'
import {
  profilesService,
  type PublicProviderDetail,
  type ProviderWorkItem,
} from '@/services/profiles'
import AppLayout from '@/components/AppLayout.vue'
import SectionLoader from '@/components/SectionLoader.vue'
import Button from '@/components/ui/Button.vue'

const route = useRoute()
const authStore = useAuthStore()
const loading = ref(true)
const provider = ref<PublicProviderDetail | null>(null)

const initials = computed(() => {
  const name = provider.value?.full_name || 'P'
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  return name.charAt(0).toUpperCase()
})

const displaySkills = computed(() => {
  if (!provider.value) return []
  if (provider.value.skills?.length) return provider.value.skills
  return provider.value.headline_skills || []
})

const experiences = computed(() => provider.value?.experiences ?? [])

const inProgressJobs = computed((): ProviderWorkItem[] =>
  provider.value?.work_history?.in_progress ?? []
)

const closedJobs = computed((): ProviderWorkItem[] =>
  provider.value?.work_history?.closed ?? []
)

function formatMemberSince(raw: string) {
  return new Date(raw).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
}

function formatExpDate(raw: string) {
  if (!raw) return ''
  return new Date(raw).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
}

function formatWorkDate(raw?: string | null) {
  if (!raw) return '—'
  return new Date(raw).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

async function load() {
  const userId = route.params.userId as string
  if (!userId) return
  loading.value = true
  provider.value = null
  try {
    const res = await profilesService.getPublicProvider(userId)
    provider.value = res.data
  } catch {
    provider.value = null
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => route.params.userId, load)
</script>
