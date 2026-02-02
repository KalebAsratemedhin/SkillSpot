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
        <div v-if="jobsStore.nextPage" class="mt-6 flex justify-center">
          <Button
            variant="outline"
            :loading="jobsStore.loading"
            @click="loadMore"
            class="border-2 border-slate-200"
          >
            Load more
            <span class="material-symbols-outlined ml-1">expand_more</span>
          </Button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useJobsStore } from '@/stores/jobs'
import AppLayout from '@/components/AppLayout.vue'
import Button from '@/components/ui/Button.vue'
import JobCard from '@/components/JobCard.vue'

const authStore = useAuthStore()
const jobsStore = useJobsStore()
const currentPage = ref(1)

async function loadMore() {
  if (!jobsStore.nextPage) return
  currentPage.value += 1
  await jobsStore.fetchJobs(
    { ...(authStore.isClient ? { my_jobs: true } : {}), page: currentPage.value },
    { append: true }
  )
}

onMounted(async () => {
  currentPage.value = 1
  await jobsStore.fetchJobs(
    authStore.isClient ? { my_jobs: true } : undefined
  )
})
</script>
