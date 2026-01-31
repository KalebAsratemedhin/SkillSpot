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
                class="w-full border-none focus:ring-0 bg-transparent text-slate-900 placeholder:text-slate-400 text-lg font-medium"
                placeholder="What service do you need?"
                type="text"
              />
            </div>
            <div class="flex-1 flex items-center border-b md:border-b-0 md:border-r border-slate-100 px-5 py-3">
              <span class="material-symbols-outlined text-slate-400 mr-3">location_on</span>
              <input
                v-model="searchForm.location"
                class="w-full border-none focus:ring-0 bg-transparent text-slate-900 placeholder:text-slate-400 text-lg font-medium"
                placeholder="City or Zip"
                type="text"
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
            <div class="space-y-2">
              <div
                v-for="filter in filters"
                :key="filter.name"
                :class="activeFilter === filter.name
                  ? 'flex items-center justify-between px-4 py-3 rounded-xl bg-midnight text-white cursor-pointer shadow-md'
                  : 'flex items-center gap-3 px-4 py-3 rounded-xl text-slate-600 hover:bg-white hover:shadow-sm border border-transparent hover:border-slate-100 cursor-pointer transition-all'"
                @click="activeFilter = filter.name"
              >
                <div class="flex items-center gap-3">
                  <span class="material-symbols-outlined text-[20px]" :class="activeFilter === filter.name ? 'text-amber' : ''">{{ filter.icon }}</span>
                  <span class="text-sm font-semibold">{{ filter.name }}</span>
                </div>
                <span v-if="activeFilter === filter.name" class="text-[10px] bg-amber text-midnight px-1.5 py-0.5 rounded font-black">{{ filter.count }}</span>
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
              <p class="text-slate-500 text-sm mt-1">Found {{ jobsStore.totalCount || 128 }} physical service requests in your area</p>
            </div>
            <div class="flex items-center gap-2 text-sm text-slate-500">
              <span>Sort by:</span>
              <select
                v-model="sortBy"
                class="bg-transparent border-none focus:ring-0 text-slate-900 font-semibold pr-8"
              >
                <option>Distance (Closest)</option>
                <option>Newest first</option>
                <option>Highest budget</option>
              </select>
            </div>
          </div>
          <div v-if="jobsStore.loading" class="flex justify-center py-12">
            <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
          </div>
          <div v-else-if="jobsStore.jobs.length === 0" class="text-center py-12">
            <p class="text-slate-500">No jobs found</p>
          </div>
          <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-2 gap-6">
            <JobCard
              v-for="job in jobsStore.jobs"
              :key="job.id"
              :job="job"
              :show-apply="authStore.isProvider"
            />
          </div>
          <div v-if="jobsStore.nextPage" class="mt-12 flex justify-center">
            <Button variant="outline" @click="loadMore" class="border-2 border-slate-200">
              Load more requests
              <span class="material-symbols-outlined text-[20px]">expand_more</span>
            </Button>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useJobsStore } from '@/stores/jobs'
import AppLayout from '@/components/AppLayout.vue'
import Button from '@/components/ui/Button.vue'
import JobCard from '@/components/JobCard.vue'

const router = useRouter()
const authStore = useAuthStore()
const jobsStore = useJobsStore()

const searchForm = ref({
  service: '',
  location: '',
  budget: '',
})

const activeFilter = ref('Electrical')
const sortBy = ref('Distance (Closest)')

const filters = [
  { name: 'Electrical', icon: 'bolt', count: 24 },
  { name: 'Plumbing', icon: 'water_drop', count: 18 },
  { name: 'Nursing & Care', icon: 'medical_services', count: 32 },
  { name: 'HVAC', icon: 'ac_unit', count: 15 },
]

async function handleSearch() {
  await jobsStore.fetchJobs({
    search: searchForm.value.service,
    location: searchForm.value.location,
  })
}

async function loadMore() {
  if (jobsStore.nextPage) {
    const page = parseInt(new URL(jobsStore.nextPage).searchParams.get('page') || '1')
    await jobsStore.fetchJobs({ page })
  }
}

onMounted(async () => {
  await jobsStore.fetchJobs()
})
</script>
