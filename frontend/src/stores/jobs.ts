import { defineStore } from 'pinia'
import { ref } from 'vue'
import { jobsService, type Job, type JobApplication, type JobInvitation, type JobListParams } from '@/services/jobs'

export const useJobsStore = defineStore('jobs', () => {
  const jobs = ref<Job[]>([])
  const currentJob = ref<Job | null>(null)
  const applications = ref<JobApplication[]>([])
  const invitations = ref<JobInvitation[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const totalCount = ref(0)
  const nextPage = ref<string | null>(null)
  const previousPage = ref<string | null>(null)

  async function fetchJobs(params?: JobListParams, options?: { append?: boolean }) {
    try {
      loading.value = true
      error.value = null
      const response = await jobsService.list(params)
      const newResults = response.data.results
      if (options?.append && params?.page && params.page > 1) {
        jobs.value = [...jobs.value, ...newResults]
      } else {
        jobs.value = newResults
      }
      totalCount.value = response.data.count
      nextPage.value = response.data.next || null
      previousPage.value = response.data.previous || null
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch jobs'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchJob(id: string) {
    try {
      loading.value = true
      error.value = null
      currentJob.value = null
      const response = await jobsService.get(id)
      currentJob.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch job'
      currentJob.value = null
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createJob(data: Partial<Job>) {
    try {
      loading.value = true
      error.value = null
      const response = await jobsService.create(data)
      jobs.value.unshift(response.data)
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to create job'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateJob(id: string, data: Partial<Job>) {
    try {
      loading.value = true
      error.value = null
      const response = await jobsService.update(id, data)
      const index = jobs.value.findIndex(j => j.id === id)
      if (index !== -1) {
        jobs.value[index] = response.data
      }
      if (currentJob.value?.id === id) {
        currentJob.value = response.data
      }
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.error ?? 'Failed to update job'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function closeJob(id: string) {
    try {
      loading.value = true
      error.value = null
      const response = await jobsService.close(id)
      const index = jobs.value.findIndex(j => j.id === id)
      if (index !== -1) {
        jobs.value[index] = response.data
      }
      if (currentJob.value?.id === id) {
        currentJob.value = response.data
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to close job'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchApplications(jobId: string) {
    try {
      loading.value = true
      error.value = null
      const response = await jobsService.getApplications(jobId)

      applications.value = Array.isArray(response.data?.results) ? response.data.results : []
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch applications'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createApplication(
    jobId: string,
    data: { cover_letter?: string; proposed_rate?: number }
  ) {
    try {
      loading.value = true
      error.value = null
      const response = await jobsService.createApplication(jobId, data)
      applications.value.push(response.data)
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to create application'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchMyApplications() {
    try {
      loading.value = true
      error.value = null
      const response = await jobsService.getMyApplications()
      applications.value = Array.isArray(response.data?.results) ? response.data.results : []
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch applications'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateApplication(id: string, data: Partial<JobApplication>) {
    try {
      loading.value = true
      error.value = null
      const response = await jobsService.updateApplication(id, data)
      const index = applications.value.findIndex(a => a.id === id)
      if (index !== -1) {
        applications.value[index] = response.data
      }
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.error ?? 'Failed to update application'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchInvitations() {
    try {
      loading.value = true
      error.value = null
      const response = await jobsService.listInvitations()
      const data = response.data as { results?: JobInvitation[] } | JobInvitation[]
      invitations.value = Array.isArray(data) ? data : (data?.results ?? [])
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch invitations'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createInvitation(data: { job: string; provider?: string; provider_email?: string; message?: string }) {
    try {
      loading.value = true
      error.value = null
      const response = await jobsService.createInvitation(data)
      invitations.value = [response.data, ...invitations.value]
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.provider_email?.[0] ?? err.response?.data?.provider?.[0] ?? err.response?.data?.detail ?? 'Failed to send invitation'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateInvitation(id: string, data: Partial<JobInvitation>) {
    try {
      loading.value = true
      error.value = null
      const response = await jobsService.updateInvitation(id, data)
      const index = invitations.value.findIndex(i => i.id === id)
      if (index !== -1) {
        invitations.value[index] = response.data
      }
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to update invitation'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    jobs,
    currentJob,
    applications,
    invitations,
    loading,
    error,
    totalCount,
    nextPage,
    previousPage,
    fetchJobs,
    fetchJob,
    createJob,
    updateJob,
    closeJob,
    fetchApplications,
    fetchMyApplications,
    updateApplication,
    createApplication,
    fetchInvitations,
    createInvitation,
    updateInvitation,
  }
})
