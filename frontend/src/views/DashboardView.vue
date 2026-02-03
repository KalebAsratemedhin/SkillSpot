<template>
  <AppLayout>
    <div>
      <section class="w-full bg-midnight py-20 px-6 lg:px-20 relative overflow-hidden">
        <div class="absolute inset-0 opacity-10 pointer-events-none" style="background-image: radial-gradient(circle at 2px 2px, rgba(255,255,255,0.15) 1px, transparent 0); background-size: 50px 50px;"></div>
        <div class="max-w-[1400px] mx-auto flex flex-col items-center text-center gap-10 relative z-10">
          <div class="max-w-3xl">
            <h1 class="text-white text-5xl md:text-6xl font-display font-bold leading-[1.1] tracking-tight mb-6">
              Connect with Local <span class="text-amber">Service Experts</span>
            </h1>
            <p class="text-slate-400 text-xl font-medium max-w-2xl mx-auto">
              The premium marketplace for certified electricians, master plumbers, and healthcare specialists.
            </p>
          </div>
          <div class="w-full max-w-5xl bg-white p-3 rounded-2xl shadow-2xl flex flex-col md:flex-row gap-3">
            <div class="flex-[1.5] flex items-center border-b md:border-b-0 md:border-r border-slate-100 px-5 py-3">
              <span class="material-symbols-outlined text-amber mr-3">search</span>
              <input
                v-model="searchForm.service"
                class="w-full border-none outline-none focus:ring-0 focus:outline-none bg-transparent text-slate-900 placeholder:text-slate-400 text-lg font-medium"
                placeholder="What service do you need?"
                type="text"
                @keydown.enter="handleSearch"
              />
            </div>
            <div class="flex-1 flex items-center border-b md:border-b-0 md:border-r border-slate-100 px-5 py-3">
              <span class="material-symbols-outlined text-slate-400 mr-3">location_on</span>
              <input
                v-model="searchForm.location"
                class="w-full border-none outline-none focus:ring-0 focus:outline-none bg-transparent text-slate-900 placeholder:text-slate-400 text-lg font-medium"
                placeholder="City or Zip"
                type="text"
                @keydown.enter="handleSearch"
              />
            </div>
            <Button variant="secondary" size="lg" @click="handleSearch" class="bg-midnight hover:bg-slate-800 text-white font-bold py-4 px-10 rounded-xl shadow-lg flex items-center justify-center gap-2">
              <span class="font-display">Search Now</span>
              <span class="material-symbols-outlined group-hover:translate-x-1 transition-transform">arrow_forward</span>
            </Button>
          </div>
        </div>
      </section>
      <div class="max-w-[1400px] mx-auto px-6 lg:px-20 py-12 flex flex-col lg:flex-row gap-12">
        <aside class="w-full lg:w-72 flex-shrink-0">
          <div class="sticky top-32 flex flex-col gap-8">
            <div>
              <h3 class="text-midnight text-xl font-display font-bold mb-2">Filters</h3>
              <div class="h-1 w-12 bg-amber rounded-full"></div>
            </div>
            <div v-if="skillTags.length" class="space-y-2">
              <h4 class="text-[11px] font-black text-slate-400 uppercase tracking-[0.2em] mb-2">Skill</h4>
              <Select v-model="searchForm.skill" @update:model-value="applySearch">
                <SelectTrigger class="w-full h-11 rounded-xl border border-slate-200 bg-white text-slate-900 font-medium focus:ring-2 focus:ring-amber/20 [&>span]:line-clamp-1">
                  <SelectValue placeholder="All skills" />
                </SelectTrigger>
                <SelectContent class="rounded-xl border border-slate-200 bg-white text-slate-900">
                  <SelectItem value="__all__" class="rounded-lg focus:bg-slate-100 focus:text-slate-900 data-[highlighted]:bg-slate-100 data-[highlighted]:text-slate-900">All skills</SelectItem>
                  <SelectItem
                    v-for="tag in skillTags"
                    :key="tag.id"
                    :value="tag.id"
                    class="rounded-lg focus:bg-slate-100 focus:text-slate-900 data-[highlighted]:bg-slate-100 data-[highlighted]:text-slate-900"
                  >
                    {{ tag.name }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="space-y-2">
              <h4 class="text-[11px] font-black text-slate-400 uppercase tracking-[0.2em] mb-2">Budget (Br)</h4>
              <div class="flex gap-2 items-center">
                <input
                  v-model.number="searchForm.budget_min"
                  type="number"
                  min="0"
                  placeholder="Min"
                  class="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white text-slate-900 text-sm focus:ring-2 focus:ring-amber/20 outline-none focus:outline-none"
                />
                <span class="text-slate-400">–</span>
                <input
                  v-model.number="searchForm.budget_max"
                  type="number"
                  min="0"
                  placeholder="Max"
                  class="w-full px-3 py-2 rounded-lg border border-slate-200 bg-white text-slate-900 text-sm focus:ring-2 focus:ring-amber/20 outline-none focus:outline-none"
                />
              </div>
            </div>
            <div class="pt-8 border-t border-slate-200">
              <h4 class="text-[11px] font-black text-slate-400 uppercase tracking-[0.2em] mb-5">Service Radius</h4>
              <input class="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-midnight" type="range"/>
              <div class="flex justify-between mt-3 text-xs font-bold text-slate-500">
                <span>5 miles</span>
                <span>50+ miles</span>
              </div>
            </div>
          </div>
        </aside>
        <div class="flex-1">
          <div class="flex items-center justify-between mb-8">
            <div>
              <h2 class="text-3xl font-display font-bold text-midnight">Available Jobs</h2>
              <p class="text-slate-500 text-sm mt-1">Found {{ jobsStore.totalCount }} physical service requests in your area</p>
            </div>
            <div class="flex items-center gap-2 text-sm text-slate-500">
              <span>Sort by:</span>
              <Select v-model="sortBy" @update:model-value="applySearch">
                <SelectTrigger class="w-auto min-w-[10rem] h-9 bg-transparent border-none focus:ring-0 text-slate-900 font-semibold cursor-pointer [&>span]:line-clamp-1">
                  <SelectValue placeholder="Sort" />
                </SelectTrigger>
                <SelectContent class="rounded-xl border border-slate-200 bg-white text-slate-900">
                  <SelectItem value="-created_at" class="rounded-lg focus:bg-slate-100 focus:text-slate-900 data-[highlighted]:bg-slate-100 data-[highlighted]:text-slate-900">Newest first</SelectItem>
                  <SelectItem value="created_at" class="rounded-lg focus:bg-slate-100 focus:text-slate-900 data-[highlighted]:bg-slate-100 data-[highlighted]:text-slate-900">Oldest first</SelectItem>
                  <SelectItem value="-budget_max" class="rounded-lg focus:bg-slate-100 focus:text-slate-900 data-[highlighted]:bg-slate-100 data-[highlighted]:text-slate-900">Highest budget</SelectItem>
                  <SelectItem value="budget_min" class="rounded-lg focus:bg-slate-100 focus:text-slate-900 data-[highlighted]:bg-slate-100 data-[highlighted]:text-slate-900">Lowest budget</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div v-if="jobsStore.loading && jobsStore.jobs.length === 0" class="flex justify-center py-12">
            <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
          </div>
          <div v-else-if="jobsStore.jobs.length === 0" class="text-center py-12">
            <p class="text-slate-500">No jobs found. Try adjusting your search or filters.</p>
          </div>
          <div v-else class="flex flex-col gap-4">
            <JobCard
              v-for="job in jobsStore.jobs"
              :key="job.id"
              :job="job"
              :show-apply="authStore.isProvider"
            />
            <PaginationBar
              v-if="jobsStore.totalCount > 0"
              :current-page="currentPage"
              :total-pages="jobsTotalPages"
              :total-count="jobsStore.totalCount"
              :page-size="pageSize"
              :loading="jobsStore.loading"
              @go-to-page="goToPage"
              @update-page-size="onPageSizeChange"
            />
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useJobsStore } from '@/stores/jobs'
import AppLayout from '@/components/AppLayout.vue'
import JobCard from '@/components/JobCard.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

const authStore = useAuthStore()
const jobsStore = useJobsStore()

const searchForm = ref({
  service: '',
  location: '',
  skill: '__all__' as string,
  budget_min: undefined as number | undefined,
  budget_max: undefined as number | undefined,
})

const sortBy = ref('-created_at')
const skillTags = ref<{ id: string; name: string }[]>([])
const currentPage = ref(1)
const pageSize = ref(10)

const jobsTotalPages = computed(() => Math.max(1, Math.ceil(jobsStore.totalCount / pageSize.value)))

function buildParams(append = false) {
  const page = append ? currentPage.value : 1
  const skillParam = searchForm.value.skill === '__all__' ? undefined : searchForm.value.skill
  const params: Record<string, string | number | undefined> = {
    search: searchForm.value.service.trim() || undefined,
    location: searchForm.value.location.trim() || undefined,
    skill: skillParam || undefined,
    budget_min: searchForm.value.budget_min,
    budget_max: searchForm.value.budget_max,
    ordering: sortBy.value,
    page,
    page_size: pageSize.value,
  }
  return params
}

async function handleSearch() {
  currentPage.value = 1
  await jobsStore.fetchJobs(buildParams())
}

function applySearch() {
  currentPage.value = 1
  jobsStore.fetchJobs(buildParams())
}

async function goToPage(page: number) {
  if (page < 1 || page > jobsTotalPages.value) return
  currentPage.value = page
  await jobsStore.fetchJobs(buildParams(true), { append: false })
}

function onPageSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  jobsStore.fetchJobs(buildParams())
}


onMounted(async () => {
  try {
    const { useProfilesStore } = await import('@/stores/profiles')
    const profilesStore = useProfilesStore()
    await profilesStore.fetchTags({ category: 'SKILL' })
    skillTags.value = (profilesStore.tags || []).map((t: { id: string; name: string }) => ({ id: t.id, name: t.name }))
  } catch {
    skillTags.value = []
  }
  await jobsStore.fetchJobs(buildParams())
})
</script>
