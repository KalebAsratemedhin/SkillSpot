<template>
  <AppLayout>
    <div class="max-w-[1280px] mx-auto w-full px-4 md:px-6 lg:px-10 py-6 md:py-10">
      <div v-if="jobsStore.loading" class="flex justify-center py-12">
        <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
      </div>
      <div v-else-if="!jobsStore.currentJob" class="text-center py-16">
        <p class="text-slate-500 mb-4">Job not found or you don't have access.</p>
        <Button variant="default" @click="router.push('/jobs')">Back to Jobs</Button>
      </div>
      <div v-else-if="jobsStore.currentJob" class="space-y-6 md:space-y-8">
        <div class="flex items-center gap-2 mb-4 md:mb-8 text-xs font-bold uppercase tracking-widest text-gray-400">
          <router-link to="/dashboard" class="hover:text-midnight">Home</router-link>
          <span class="material-symbols-outlined text-[10px]">chevron_right</span>
          <span class="hover:text-midnight">Job</span>
          <span class="material-symbols-outlined text-[10px]">chevron_right</span>
          <span class="text-midnight">Job Details</span>
        </div>
        <div class="flex flex-col lg:flex-row gap-6 lg:gap-10">
          <div class="flex-1 space-y-6 lg:space-y-8">
            <Card class="bg-white rounded-xl md:rounded-2xl p-6 md:p-8 lg:p-10 shadow-sm border border-gray-100">
              <CardContent class="p-0">
                <div class="flex flex-col gap-3 md:gap-4">
                  <div class="flex items-center gap-2 md:gap-3 flex-wrap">
                    <span class="px-2 md:px-3 py-1 bg-amber/10 text-amber text-[9px] md:text-[10px] font-black uppercase tracking-widest rounded-full">Urgent Hire</span>
                    <span class="text-gray-400 text-xs md:text-sm">Posted {{ formatDate(jobsStore.currentJob.created_at) }}</span>
                    <div v-if="isJobOwner" class="flex items-center gap-2 md:gap-3 flex-wrap ml-auto">
                      <span class="text-sm text-gray-500 font-medium">Status:</span>
                      <Select v-model="jobStatusValue">
                        <SelectTrigger
                          class="!h-10 !w-auto min-w-[10rem] !border-slate-200 !bg-white !text-midnight !placeholder:text-slate-500 focus:!ring-amber/20"
                        >
                          <SelectValue placeholder="Select status" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="DRAFT">Draft</SelectItem>
                          <SelectItem value="OPEN">Open</SelectItem>
                          <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
                          <SelectItem value="COMPLETED">Completed</SelectItem>
                          <SelectItem value="CANCELLED">Cancelled</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <h1 class="text-midnight text-4xl font-extrabold leading-tight tracking-tight">
                    {{ jobsStore.currentJob.title }}
                  </h1>
                  <div class="flex flex-wrap gap-6 pt-2">
                    <div class="flex items-center gap-2 text-gray-600">
                      <span class="material-symbols-outlined text-amber text-xl">location_on</span>
                      <span class="text-sm font-medium">{{ jobsStore.currentJob.location }} (On-Site)</span>
                    </div>
                    <div class="flex items-center gap-2 text-gray-600">
                      <span class="material-symbols-outlined text-amber text-xl">payments</span>
                      <span class="text-sm font-medium">${{ jobsStore.currentJob.budget_min }} - ${{ jobsStore.currentJob.budget_max }} Budget</span>
                    </div>
                  </div>
                </div>
                <div class="mt-12 space-y-8">
                  <section>
                    <h3 class="text-lg font-bold text-midnight mb-4 flex items-center gap-2">
                      <span class="w-1 h-6 bg-amber rounded-full"></span>
                      Project Description
                    </h3>
                    <div class="text-gray-600 space-y-4 leading-relaxed text-lg">
                      <p>{{ jobsStore.currentJob.description }}</p>
                    </div>
                  </section>
                  <section v-if="jobTags.length" class="pt-8 border-t border-gray-100">
                    <h3 class="text-lg font-bold text-midnight mb-6">Required Skills & Expertise</h3>
                    <div class="flex flex-wrap gap-3">
                      <span
                        v-for="tag in jobTags"
                        :key="tag"
                        class="px-5 py-2.5 bg-gray-100 text-midnight text-sm font-bold rounded-xl hover:bg-midnight hover:text-white transition-all cursor-default"
                      >
                        {{ tag }}
                      </span>
                    </div>
                  </section>
                </div>
              </CardContent>
            </Card>

            <Card v-if="isJobOwner && applicationsForThisJob.length" class="bg-white rounded-2xl p-10 shadow-sm border border-gray-100">
              <CardHeader>
                <CardTitle class="text-lg font-bold text-midnight">Applications ({{ applicationsForThisJob.length }})</CardTitle>
              </CardHeader>
              <CardContent class="p-0">
                <ul class="divide-y divide-gray-100">
                  <li v-for="app in applicationsForThisJob" :key="app.id" class="py-6 first:pt-0">
                    <div class="flex flex-col gap-2">
                      <div class="flex items-center justify-between flex-wrap gap-2">
                        <span class="font-semibold text-midnight">{{ (app as any).provider_name ?? app.provider }}</span>
                        <span
                          class="text-xs font-medium px-2 py-1 rounded-full"
                          :class="app.status === 'ACCEPTED' ? 'bg-green-100 text-green-800' : app.status === 'REJECTED' ? 'bg-red-100 text-red-800' : 'bg-slate-100 text-slate-700'"
                        >
                          {{ app.status }}
                        </span>
                      </div>
                      <p v-if="app.cover_letter" class="text-gray-600 text-sm">{{ app.cover_letter }}</p>
                      <p v-if="app.proposed_rate != null" class="text-sm text-gray-500">Proposed rate: ${{ app.proposed_rate }}</p>
                      <div class="flex gap-2 mt-2 flex-wrap">
                        <Button v-if="app.status === 'PENDING'" size="sm" @click="handleApplicationStatus(app.id, 'ACCEPTED')">Accept</Button>
                        <Button v-if="app.status === 'PENDING'" size="sm" variant="outline" @click="handleApplicationStatus(app.id, 'REJECTED')">Reject</Button>
                        <Button size="sm" variant="outline" :disabled="messageLoading === app.id" @click="startConversation(app)">
                          <span v-if="messageLoading === app.id" class="material-symbols-outlined animate-spin text-sm">refresh</span>
                          <span v-else class="material-symbols-outlined text-sm">chat</span>
                          Message
                        </Button>
                        <Button v-if="app.status === 'ACCEPTED'" size="sm" :disabled="contractLoading === app.id" @click="createContractFromApplication(app)">
                          <span v-if="contractLoading === app.id" class="material-symbols-outlined animate-spin text-sm">refresh</span>
                          <span v-else class="material-symbols-outlined text-sm">description</span>
                          Create Contract
                        </Button>
                      </div>
                    </div>
                  </li>
                </ul>
              </CardContent>
            </Card>
            <Card v-else-if="isJobOwner && !applicationsForThisJob.length" class="bg-white rounded-2xl p-10 shadow-sm border border-gray-100">
              <CardHeader>
                <CardTitle class="text-lg font-bold text-midnight">Applications</CardTitle>
              </CardHeader>
              <CardContent>
                <p class="text-gray-500 text-sm">No applications yet.</p>
              </CardContent>
            </Card>

            <Card v-if="authStore.isProvider && !isJobOwner" class="bg-white rounded-2xl p-10 shadow-sm border border-gray-100">
              <CardHeader>
                <CardTitle class="text-lg font-bold text-midnight mb-8">Apply for this Job</CardTitle>
              </CardHeader>
              <CardContent>
                <form @submit.prevent="handleApply" class="space-y-4">
                  <FormField :error="applicationErrors.message">
                    <Label>Message</Label>
                    <textarea
                      v-model="applicationForm.message"
                      class="w-full rounded-xl border border-slate-200 bg-white text-midnight focus:ring-2 focus:ring-amber/20 focus:border-amber p-4 min-h-[120px]"
                      placeholder="Tell the client why you're the right fit..."
                    ></textarea>
                  </FormField>
                  <FormField :error="applicationErrors.proposed_rate">
                    <Label>Proposed Rate (optional)</Label>
                    <Input
                      v-model="applicationForm.proposed_rate"
                      type="number"
                      placeholder="Your rate"
                      :error="applicationErrors.proposed_rate"
                    />
                  </FormField>
                  <Button type="submit" :loading="jobsStore.loading" variant="default" size="lg" class="w-full">
                    Submit Application
                  </Button>
                </form>
              </CardContent>
            </Card>
            <Card v-if="(clientName || clientEmail) && !isJobOwner" class="bg-white rounded-2xl p-10 shadow-sm border border-gray-100">
              <CardHeader>
                <CardTitle class="text-lg font-bold text-midnight mb-8">Client Profile</CardTitle>
              </CardHeader>
              <CardContent class="p-0">
                <div class="flex flex-col md:flex-row items-start gap-8">
                  <div class="relative">
                    <div class="bg-center bg-no-repeat aspect-square bg-cover rounded-2xl size-24 ring-4 ring-gray-50 shadow-inner bg-slate-300"></div>
                    <div class="absolute -bottom-2 -right-2 bg-white rounded-full p-1 shadow-md">
                      <span class="material-symbols-outlined text-amber text-xl">verified</span>
                    </div>
                  </div>
                  <div class="flex-1">
                    <div class="flex items-center gap-3 mb-1">
                      <h4 class="text-xl font-extrabold text-midnight">{{ clientName || clientEmail }}</h4>
                      <span class="text-xs font-bold text-amber bg-amber/10 px-2 py-0.5 rounded uppercase tracking-tighter">Gold Client</span>
                    </div>
                    <p class="text-gray-500 font-medium mb-6">Residential Homeowner • Member since {{ formatYear(jobsStore.currentJob.created_at) }}</p>
                    <div class="grid grid-cols-2 lg:grid-cols-4 gap-6">
                      <div class="space-y-1">
                        <p class="text-xs text-gray-400 font-bold uppercase tracking-wider">Rating</p>
                        <div class="flex items-center gap-1">
                          <span class="text-midnight font-bold">5.0</span>
                          <span class="material-symbols-outlined text-amber text-sm fill-1">star</span>
                        </div>
                      </div>
                      <div class="space-y-1">
                        <p class="text-xs text-gray-400 font-bold uppercase tracking-wider">Total Spend</p>
                        <p class="text-midnight font-bold">$45,000+</p>
                      </div>
                      <div class="space-y-1">
                        <p class="text-xs text-gray-400 font-bold uppercase tracking-wider">Hires</p>
                        <p class="text-midnight font-bold">4 Projects</p>
                      </div>
                      <div class="space-y-1">
                        <p class="text-xs text-gray-400 font-bold uppercase tracking-wider">Location</p>
                        <p class="text-midnight font-bold">{{ jobsStore.currentJob.location }}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
          <div class="lg:w-[380px] space-y-4 md:space-y-6">
            <Card class="bg-midnight rounded-2xl md:rounded-3xl p-6 md:p-8 shadow-2xl lg:sticky lg:top-28 overflow-hidden">
              <div class="absolute top-0 right-0 -mr-16 -mt-16 w-32 h-32 bg-amber/10 blur-3xl rounded-full"></div>
              <div class="relative z-10 space-y-8">
                <div>
                  <p class="text-amber text-xs font-black uppercase tracking-[0.2em] mb-2">Investment Range</p>
                  <div class="flex items-baseline gap-2">
                    <span class="text-white text-4xl font-black tracking-tight">${{ formatBudgetMax(jobsStore.currentJob.budget_max) }}</span>
                    <span class="text-gray-400 text-sm font-medium">max budget</span>
                  </div>
                </div>
                <div class="space-y-4">
                  <Button
                    v-if="authStore.isProvider && !isJobOwner"
                    variant="default"
                    size="lg"
                    @click="handleApply"
                    class="w-full h-16 bg-amber text-midnight text-lg font-black shadow-lg shadow-amber/30 hover:shadow-amber/40 hover:scale-[1.02] transition-all"
                  >
                    Apply Now
                  </Button>
                  <Button variant="outline" size="lg" class="w-full h-14 border-2 border-midnight-light bg-midnight-light/50 text-white hover:bg-midnight-light">
                    <span class="material-symbols-outlined text-xl">bookmark</span>
                    Save Project
                  </Button>
                </div>
                <div class="pt-8 border-t border-white/10 space-y-6">
                  <h4 class="text-xs font-black uppercase tracking-[0.2em] text-gray-400">Market Insight</h4>
                  <div class="grid grid-cols-1 gap-4">
                    <div class="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/10">
                      <div class="flex items-center gap-3">
                        <div class="p-2 rounded-lg bg-amber/10">
                          <span class="material-symbols-outlined text-amber">groups</span>
                        </div>
                        <span class="text-sm text-gray-300 font-medium">Proposals</span>
                      </div>
                      <span class="text-white font-bold">5 - 10</span>
                    </div>
                    <div class="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/10">
                      <div class="flex items-center gap-3">
                        <div class="p-2 rounded-lg bg-amber/10">
                          <span class="material-symbols-outlined text-amber">analytics</span>
                        </div>
                        <span class="text-sm text-gray-300 font-medium">Interest</span>
                      </div>
                      <span class="text-white font-bold">High</span>
                    </div>
                    <div class="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/10">
                      <div class="flex items-center gap-3">
                        <div class="p-2 rounded-lg bg-amber/10">
                          <span class="material-symbols-outlined text-amber">verified</span>
                        </div>
                        <span class="text-sm text-gray-300 font-medium">Site Visits</span>
                      </div>
                      <span class="text-white font-bold">3 Booked</span>
                    </div>
                  </div>
                </div>
                <div class="bg-amber/5 border border-amber/20 rounded-2xl p-4">
                  <div class="flex gap-3">
                    <span class="material-symbols-outlined text-amber text-lg">lightbulb</span>
                    <p class="text-xs text-gray-300 leading-relaxed">
                      <span class="text-amber font-bold">Expert Tip:</span> Highlighting your portfolio of similar <span class="italic">residential kitchen projects</span> can increase your selection chance by 45%.
                    </p>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useJobsStore } from '@/stores/jobs'
import { useMessagingStore } from '@/stores/messaging'
import AppLayout from '@/components/AppLayout.vue'
import Card from '@/components/ui/Card.vue'
import CardHeader from '@/components/ui/CardHeader.vue'
import CardTitle from '@/components/ui/CardTitle.vue'
import CardContent from '@/components/ui/CardContent.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Label from '@/components/ui/Label.vue'
import FormField from '@/components/ui/FormField.vue'
import { toast } from 'vue-sonner'
import type { JobApplication } from '@/services/jobs'

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const jobsStore = useJobsStore()
const messagingStore = useMessagingStore()
const messageLoading = ref<string | null>(null)
const contractLoading = ref<string | null>(null)

const jobStatusValue = computed({
  get: () => jobsStore.currentJob?.status ?? '',
  set: (value: string) => {
    if (value && jobsStore.currentJob) handleStatusChange(value)
  },
})

const applicationForm = ref({
  message: '',
  proposed_rate: '',
})

const applicationErrors = ref({
  message: '',
  proposed_rate: '',
})

const jobTags = computed(() => {
  const job = jobsStore.currentJob
  if (!job) return []
  if (job.tags?.length) return job.tags
  if (job.required_skills?.length) return job.required_skills.map((s: { name: string }) => s.name)
  return []
})
const clientName = computed(() => jobsStore.currentJob?.client_name || null)
const clientEmail = computed(() => jobsStore.currentJob?.client_email || null)
const isJobOwner = computed(() => {
  const job = jobsStore.currentJob
  const user = authStore.user
  if (!job || !user) return false
  return job.client === user.id
})

const applicationsForThisJob = computed(() => {
  const jobId = jobsStore.currentJob?.id
  if (!jobId) return []
  const apps = jobsStore.applications
  if (!Array.isArray(apps)) return []
  return apps.filter((a: JobApplication) => a.job === jobId)
})

function formatDate(dateString: string) {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))
  if (hours < 1) return 'just now'
  if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`
  const days = Math.floor(hours / 24)
  return `${days} day${days > 1 ? 's' : ''} ago`
}

function formatYear(dateString: string) {
  return new Date(dateString).getFullYear()
}

function formatBudgetMax(max?: number) {
  if (!max) return '0'
  if (max >= 1000) {
    return `${(max / 1000).toFixed(1)}k`
  }
  return max.toString()
}

async function handleApply() {
  if (!jobsStore.currentJob) return
  const rawRate = applicationForm.value.proposed_rate
  const proposedRate =
    rawRate !== '' && rawRate != null ? parseFloat(String(rawRate).trim()) : undefined
  try {
    await jobsStore.createApplication(jobsStore.currentJob.id, {
      cover_letter: (applicationForm.value.message ?? '').trim(),
      proposed_rate: proposedRate != null && !Number.isNaN(proposedRate) && proposedRate >= 0 ? proposedRate : undefined,
    })
    router.push('/applications')
  } catch (err: any) {
    const message = err.response?.data.error || 'Failed to apply for this job. Please try again.'
    toast.error(message)
  }
}

async function handleStatusChange(newStatus: string) {
  if (!jobsStore.currentJob) return
  try {
    await jobsStore.updateJob(jobsStore.currentJob.id, { status: newStatus })
    toast.success('Job status updated.')
  } catch (err: any) {
    const msg = err.response?.data?.error ?? 'Failed to update status.'
    toast.error(msg)
  }
}

async function handleApplicationStatus(applicationId: string, newStatus: 'ACCEPTED' | 'REJECTED') {
  if (!jobsStore.currentJob) return
  try {
    await jobsStore.updateApplication(applicationId, { status: newStatus })
    await jobsStore.fetchApplications(jobsStore.currentJob.id)
    toast.success(newStatus === 'ACCEPTED' ? 'Application accepted.' : 'Application rejected.')
  } catch (err: any) {
    const msg = err.response?.data?.error ?? 'Failed to update application.'
    toast.error(msg)
  }
}

async function startConversation(app: JobApplication) {
  if (!app.job || !jobsStore.currentJob) return
  const otherId = isJobOwner.value ? app.provider : app.job_client
  if (!otherId) return
  messageLoading.value = app.id
  try {
    const conv = await messagingStore.createConversation({
      participant2_id: otherId,
      job_id: app.job,
      initial_message: '',
    })
    if (conv?.id && conv.id !== 'undefined') {
      router.push(`/messages/${conv.id}`)
    } else {
      console.log('Conversation created but could not open it.', conv)
      toast.error('Conversation created but could not open it.')
    }
  } catch (err: any) {
    const msg = err.response?.data?.participant2_id?.[0] ?? err.response?.data?.detail ?? 'Failed to start conversation'
    toast.error(msg)
  } finally {
    messageLoading.value = null
  }
}

function createContractFromApplication(app: JobApplication) {
  if (!app.job || !app.provider) return
  contractLoading.value = app.id
  router.push({
    path: '/contracts/create',
    query: { job: app.job, application: app.id, provider: app.provider },
  })
  contractLoading.value = null
}

async function loadJob() {
  const jobId = route.params.id as string
  if (!jobId) return
  jobsStore.currentJob = null
  await jobsStore.fetchJob(jobId)
  if (isJobOwner.value) {
    await jobsStore.fetchApplications(jobId)
  }
}

onMounted(loadJob)

watch(() => route.params.id, () => {
  if (route.name === 'job-detail') loadJob()
})
</script>
