<template>
  <AppLayout>
    <div class="max-w-[1400px] mx-auto px-4 md:px-6 lg:px-20 py-6 md:py-10">
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6 md:mb-8">
        <h1 class="text-2xl md:text-3xl font-bold text-midnight">My Jobs</h1>
        <router-link v-if="authStore.isClient" to="/jobs/create">
          <Button variant="default" size="default" class="w-full sm:w-auto">Post a Job</Button>
        </router-link>
      </div>
      <div v-if="jobsStore.loading" class="flex justify-center py-12">
        <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
      </div>
      <div v-else-if="jobsStore.jobs.length === 0" class="text-center py-12">
        <p class="text-slate-500 mb-4">No jobs found</p>
        <router-link v-if="authStore.isClient" to="/jobs/create">
          <Button variant="default">Create Your First Job</Button>
        </router-link>
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
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useJobsStore } from '@/stores/jobs'
import AppLayout from '@/components/AppLayout.vue'
import JobCard from '@/components/JobCard.vue'
import PaginationBar from '@/components/PaginationBar.vue'

const authStore = useAuthStore()
const jobsStore = useJobsStore()
const currentPage = ref(1)
const pageSize = ref(10)

const jobsTotalPages = computed(() => Math.max(1, Math.ceil(jobsStore.totalCount / pageSize.value)))

async function goToPage(page: number) {
  if (page < 1 || page > jobsTotalPages.value) return
  currentPage.value = page
  await jobsStore.fetchJobs(
    { ...(authStore.isClient ? { my_jobs: true } : {}), page: currentPage.value, page_size: pageSize.value },
    { append: false }
  )
}

function onPageSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  jobsStore.fetchJobs(
    { ...(authStore.isClient ? { my_jobs: true } : {}), page: 1, page_size: pageSize.value },
    { append: false }
  )
}

onMounted(async () => {
  currentPage.value = 1
  await jobsStore.fetchJobs(
    { ...(authStore.isClient ? { my_jobs: true } : {}), page: 1, page_size: pageSize.value }
  )
})
</script>
