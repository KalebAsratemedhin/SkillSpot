<template>
  <AppLayout>
    <div class="w-full max-w-[1400px] mx-auto px-4 md:px-6 lg:px-10 py-6 md:py-10">
      <div class="mb-6 md:mb-8">
        <h1 class="text-2xl md:text-3xl font-bold text-midnight tracking-tight">Browse</h1>
        <p class="text-slate-500 text-sm md:text-base mt-1">Search open jobs and verified service providers</p>
      </div>

      <!-- Search bar: submit only (Enter / Search) — not on each keystroke -->
      <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-3 md:p-4 mb-6 flex flex-col md:flex-row gap-3">
        <form class="contents" @submit.prevent="runSearch">
          <div class="flex-1 flex items-center gap-3 px-3 py-2 rounded-xl bg-slate-50 border border-slate-100">
            <span class="material-symbols-outlined text-amber">search</span>
            <input
              v-model="query"
              type="search"
              class="w-full bg-transparent outline-none text-midnight placeholder:text-slate-400 font-medium"
              :placeholder="tab === 'jobs' ? 'Search jobs by title, skill, or description…' : 'Search providers by name, skill, or location…'"
            />
          </div>
          <div class="flex items-center gap-3 px-3 py-2 rounded-xl bg-slate-50 border border-slate-100 md:w-56">
            <span class="material-symbols-outlined text-slate-400">location_on</span>
            <input
              v-model="location"
              type="text"
              class="w-full bg-transparent outline-none text-midnight placeholder:text-slate-400 font-medium"
              placeholder="Location"
            />
          </div>
          <Button type="submit" variant="secondary" class="bg-midnight text-white hover:bg-slate-800 h-11 px-6">
            Search
          </Button>
        </form>
      </div>

      <!-- Tabs -->
      <div class="flex gap-6 border-b border-slate-200 mb-6">
        <button
          type="button"
          class="relative pb-3 text-sm font-bold transition-colors"
          :class="tab === 'jobs' ? 'text-amber' : 'text-slate-500 hover:text-midnight'"
          @click="setTab('jobs')"
        >
          Jobs
          <span v-if="tab === 'jobs'" class="absolute bottom-0 left-0 h-1 w-full bg-amber rounded-t-full" />
        </button>
        <button
          type="button"
          class="relative pb-3 text-sm font-bold transition-colors"
          :class="tab === 'providers' ? 'text-amber' : 'text-slate-500 hover:text-midnight'"
          @click="setTab('providers')"
        >
          Providers
          <span v-if="tab === 'providers'" class="absolute bottom-0 left-0 h-1 w-full bg-amber rounded-t-full" />
        </button>
      </div>

      <div class="flex flex-col lg:flex-row gap-8">
        <!-- Filters -->
        <aside class="w-full lg:w-64 shrink-0 space-y-6">
          <div>
            <h3 class="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">Skill</h3>
            <Select v-model="skill">
              <SelectTrigger :class="selectTriggerClass">
                <SelectValue placeholder="All skills" />
              </SelectTrigger>
              <SelectContent :class="selectContentClass">
                <SelectItem value="__all__" :class="selectItemClass">All skills</SelectItem>
                <SelectItem
                  v-for="tag in skillTags"
                  :key="tag.id"
                  :value="tag.id"
                  :class="selectItemClass"
                >
                  {{ tag.name }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <template v-if="tab === 'jobs'">
            <div>
              <h3 class="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">Budget (Br)</h3>
              <div class="grid grid-cols-2 gap-2">
                <div class="space-y-1">
                  <span class="text-xs font-semibold text-slate-500">Min</span>
                  <input
                    v-model.number="budgetMin"
                    type="number"
                    min="0"
                    placeholder="0"
                    class="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm text-midnight"
                    @change="applyFilters"
                  />
                </div>
                <div class="space-y-1">
                  <span class="text-xs font-semibold text-slate-500">Max</span>
                  <input
                    v-model.number="budgetMax"
                    type="number"
                    min="0"
                    placeholder="Any"
                    class="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm text-midnight"
                    @change="applyFilters"
                  />
                </div>
              </div>
            </div>
            <div>
              <h3 class="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">Payment</h3>
              <Select v-model="paymentSchedule">
                <SelectTrigger :class="selectTriggerClass">
                  <SelectValue placeholder="Any" />
                </SelectTrigger>
                <SelectContent :class="selectContentClass">
                  <SelectItem value="__all__" :class="selectItemClass">Any</SelectItem>
                  <SelectItem value="HOURLY" :class="selectItemClass">Hourly</SelectItem>
                  <SelectItem value="FIXED" :class="selectItemClass">Fixed</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </template>

          <template v-else>
            <div>
              <h3 class="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">Hourly rate (Br)</h3>
              <div class="grid grid-cols-2 gap-2">
                <div class="space-y-1">
                  <span class="text-xs font-semibold text-slate-500">Min</span>
                  <input
                    v-model.number="rateMin"
                    type="number"
                    min="0"
                    placeholder="0"
                    class="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm text-midnight"
                    @change="applyFilters"
                  />
                </div>
                <div class="space-y-1">
                  <span class="text-xs font-semibold text-slate-500">Max</span>
                  <input
                    v-model.number="rateMax"
                    type="number"
                    min="0"
                    placeholder="Any"
                    class="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm text-midnight"
                    @change="applyFilters"
                  />
                </div>
              </div>
            </div>
            <label class="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
              <input v-model="verifiedOnly" type="checkbox" class="rounded border-slate-300 text-amber focus:ring-amber" />
              Verified only
            </label>
          </template>

          <div>
            <h3 class="text-xs font-black uppercase tracking-widest text-slate-400 mb-3">Sort</h3>
            <Select v-model="ordering">
              <SelectTrigger :class="selectTriggerClass">
                <SelectValue placeholder="Best match" />
              </SelectTrigger>
              <SelectContent :class="selectContentClass">
                <SelectItem value="relevance" :class="selectItemClass">Best match</SelectItem>
                <SelectItem v-if="tab === 'jobs'" value="-created_at" :class="selectItemClass">Newest</SelectItem>
                <SelectItem v-if="tab === 'jobs'" value="-budget_max" :class="selectItemClass">Highest budget</SelectItem>
                <SelectItem v-if="tab === 'providers'" value="-rating" :class="selectItemClass">Top rated</SelectItem>
                <SelectItem v-if="tab === 'providers'" value="hourly_rate" :class="selectItemClass">Low to high</SelectItem>
                <SelectItem v-if="tab === 'providers'" value="-hourly_rate" :class="selectItemClass">High to low</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button variant="outline" class="w-full border-slate-200 text-slate-600" @click="clearFilters">Clear filters</Button>
        </aside>

        <!-- Results -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between mb-4">
            <p class="text-sm text-slate-500">
              <span v-if="loading">Searching…</span>
              <span v-else>{{ totalCount }} result{{ totalCount === 1 ? '' : 's' }}</span>
            </p>
          </div>

          <div v-if="loading && !hasResults" class="flex justify-center py-16">
            <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
          </div>

          <div v-else-if="!hasResults" class="text-center py-16 rounded-2xl border border-dashed border-slate-200 bg-white">
            <span class="material-symbols-outlined text-4xl text-slate-300 mb-2">search_off</span>
            <p class="text-slate-500">No results. Try a different search or filters.</p>
          </div>

          <div v-else-if="tab === 'jobs'" class="space-y-3">
            <JobCard
              v-for="job in jobs"
              :key="job.id"
              :job="job"
              :show-apply="authStore.isProvider"
            />
          </div>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <router-link
              v-for="p in providers"
              :key="p.user_id"
              :to="`/providers/${p.user_id}`"
              class="block bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-md hover:border-amber/30 transition-all no-underline text-inherit"
            >
              <div class="flex gap-4">
                <div
                  v-if="p.avatar"
                  class="size-14 rounded-xl bg-cover bg-center shrink-0 ring-2 ring-slate-100"
                  :style="{ backgroundImage: `url(${p.avatar})` }"
                />
                <div
                  v-else
                  class="size-14 rounded-xl bg-slate-100 text-amber font-black flex items-center justify-center shrink-0 text-lg"
                >
                  {{ initials(p.full_name) }}
                </div>
                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-2 flex-wrap">
                    <h3 class="font-bold text-midnight truncate">{{ p.full_name || 'Provider' }}</h3>
                    <span v-if="p.is_verified" class="material-symbols-outlined text-amber text-base">verified</span>
                  </div>
                  <p v-if="p.location" class="text-sm text-slate-500 truncate">{{ p.location }}</p>
                  <div class="flex flex-wrap gap-1.5 mt-2">
                    <span
                      v-for="s in p.headline_skills.slice(0, 3)"
                      :key="s.id"
                      class="px-2 py-0.5 text-xs font-semibold rounded-md bg-amber/10 text-amber"
                    >
                      {{ s.name }}
                    </span>
                  </div>
                  <div class="flex items-center justify-between mt-3 text-sm">
                    <span v-if="p.hourly_rate" class="font-bold text-midnight">Br {{ Number(p.hourly_rate).toLocaleString() }}/hr</span>
                    <span v-else class="text-slate-400">Rate on request</span>
                    <span v-if="p.rating.count > 0" class="text-slate-500 flex items-center gap-0.5">
                      <span class="material-symbols-outlined text-amber text-sm fill-1">star</span>
                      {{ Number(p.rating.average).toFixed(1) }}
                      <span class="text-slate-400">({{ p.rating.count }})</span>
                    </span>
                    <span v-else class="text-slate-400 text-xs">No reviews</span>
                  </div>
                </div>
              </div>
            </router-link>
          </div>

          <PaginationBar
            v-if="totalCount > 0"
            class="mt-6"
            :current-page="page"
            :total-pages="totalPages"
            :total-count="totalCount"
            :page-size="pageSize"
            :loading="loading"
            @go-to-page="goToPage"
            @update-page-size="onPageSizeChange"
          />
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { jobsService, type Job } from '@/services/jobs'
import { profilesService, type PublicProvider, type Tag } from '@/services/profiles'
import AppLayout from '@/components/AppLayout.vue'
import JobCard from '@/components/JobCard.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import Button from '@/components/ui/Button.vue'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

type BrowseTab = 'jobs' | 'providers'

/** Light overrides — Select defaults are dark (`text-white`), invisible on white triggers. */
const selectTriggerClass =
  'w-full h-11 rounded-xl border-slate-200 bg-white text-slate-900 hover:bg-slate-50 focus:ring-amber/20'
const selectContentClass = 'rounded-xl border border-slate-200 bg-white text-slate-900'
const selectItemClass =
  'focus:bg-slate-100 focus:text-slate-900 data-[highlighted]:bg-slate-100 data-[highlighted]:text-slate-900'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const tab = ref<BrowseTab>((route.query.tab as BrowseTab) === 'providers' ? 'providers' : 'jobs')
const query = ref(String(route.query.q || ''))
const location = ref(String(route.query.location || ''))
const skill = ref(String(route.query.skill || '__all__'))
const budgetMin = ref<number | undefined>(route.query.budget_min ? Number(route.query.budget_min) : undefined)
const budgetMax = ref<number | undefined>(route.query.budget_max ? Number(route.query.budget_max) : undefined)
const paymentSchedule = ref(String(route.query.payment_schedule || '__all__'))
const rateMin = ref<number | undefined>(route.query.hourly_rate_min ? Number(route.query.hourly_rate_min) : undefined)
const rateMax = ref<number | undefined>(route.query.hourly_rate_max ? Number(route.query.hourly_rate_max) : undefined)
const verifiedOnly = ref(route.query.is_verified === 'true')
const ordering = ref(String(route.query.ordering || 'relevance'))
const page = ref(Number(route.query.page) || 1)
const pageSize = ref(Number(route.query.page_size) || 12)

const loading = ref(false)
const jobs = ref<Job[]>([])
const providers = ref<PublicProvider[]>([])
const totalCount = ref(0)
const skillTags = ref<Tag[]>([])

const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize.value)))
const hasResults = computed(() => (tab.value === 'jobs' ? jobs.value.length > 0 : providers.value.length > 0))

function initials(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  return (name.charAt(0) || 'P').toUpperCase()
}

function syncUrl() {
  const q: Record<string, string> = { tab: tab.value }
  if (query.value.trim()) q.q = query.value.trim()
  if (location.value.trim()) q.location = location.value.trim()
  if (skill.value && skill.value !== '__all__') q.skill = skill.value
  if (ordering.value && ordering.value !== 'relevance') q.ordering = ordering.value
  if (page.value > 1) q.page = String(page.value)
  if (pageSize.value !== 12) q.page_size = String(pageSize.value)
  if (tab.value === 'jobs') {
    if (budgetMin.value != null && !Number.isNaN(budgetMin.value)) q.budget_min = String(budgetMin.value)
    if (budgetMax.value != null && !Number.isNaN(budgetMax.value)) q.budget_max = String(budgetMax.value)
    if (paymentSchedule.value && paymentSchedule.value !== '__all__') q.payment_schedule = paymentSchedule.value
  } else {
    if (rateMin.value != null && !Number.isNaN(rateMin.value)) q.hourly_rate_min = String(rateMin.value)
    if (rateMax.value != null && !Number.isNaN(rateMax.value)) q.hourly_rate_max = String(rateMax.value)
    if (verifiedOnly.value) q.is_verified = 'true'
  }
  router.replace({ query: q })
}

async function fetchResults() {
  loading.value = true
  syncUrl()
  try {
    if (tab.value === 'jobs') {
      const res = await jobsService.list({
        q: query.value.trim() || undefined,
        location: location.value.trim() || undefined,
        skill: skill.value !== '__all__' ? skill.value : undefined,
        budget_min: budgetMin.value,
        budget_max: budgetMax.value,
        payment_schedule: paymentSchedule.value !== '__all__' ? paymentSchedule.value : undefined,
        ordering: ordering.value === 'relevance' && !query.value.trim() ? '-created_at' : ordering.value,
        page: page.value,
        page_size: pageSize.value,
      })
      jobs.value = res.data.results || []
      totalCount.value = res.data.count ?? jobs.value.length
      providers.value = []
    } else {
      const res = await profilesService.listPublicProviders({
        q: query.value.trim() || undefined,
        location: location.value.trim() || undefined,
        skill: skill.value !== '__all__' ? skill.value : undefined,
        hourly_rate_min: rateMin.value,
        hourly_rate_max: rateMax.value,
        is_verified: verifiedOnly.value || undefined,
        ordering: ordering.value === 'relevance' && !query.value.trim() ? '-rating' : ordering.value,
        page: page.value,
        page_size: pageSize.value,
      })
      const data = res.data
      if (Array.isArray(data)) {
        providers.value = data
        totalCount.value = data.length
      } else {
        providers.value = data.results || []
        totalCount.value = data.count ?? providers.value.length
      }
      jobs.value = []
    }
  } catch (err) {
    console.error('Browse search failed', err)
    jobs.value = []
    providers.value = []
    totalCount.value = 0
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  page.value = 1
  scheduleFetch()
}

function runSearch() {
  page.value = 1
  void fetchResults()
}

/** Coalesce rapid filter updates (e.g. clearFilters touching several refs) into one request. */
let fetchScheduled = false
function scheduleFetch() {
  if (fetchScheduled) return
  fetchScheduled = true
  queueMicrotask(() => {
    fetchScheduled = false
    void fetchResults()
  })
}

const jobOrderings = new Set(['-created_at', '-budget_max'])
const providerOrderings = new Set(['-rating', 'hourly_rate', '-hourly_rate'])

function setTab(next: BrowseTab) {
  if (tab.value === next) return
  tab.value = next
  if (next === 'jobs' && providerOrderings.has(ordering.value)) ordering.value = 'relevance'
  if (next === 'providers' && jobOrderings.has(ordering.value)) ordering.value = 'relevance'
  applyFilters()
}

function clearFilters() {
  skill.value = '__all__'
  budgetMin.value = undefined
  budgetMax.value = undefined
  paymentSchedule.value = '__all__'
  rateMin.value = undefined
  rateMax.value = undefined
  verifiedOnly.value = false
  ordering.value = 'relevance'
  applyFilters()
}

function goToPage(p: number) {
  page.value = p
  void fetchResults()
}

function onPageSizeChange(size: number) {
  pageSize.value = size
  page.value = 1
  void fetchResults()
}

watch([skill, paymentSchedule, ordering, verifiedOnly], () => {
  applyFilters()
})

onMounted(async () => {
  try {
    skillTags.value = await profilesService.listAllTags({ category: 'SKILL', page_size: 50 })
  } catch {
    skillTags.value = []
  }
  await fetchResults()
})
</script>
