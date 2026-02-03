<template>
  <div class="min-h-screen bg-[#020617]">
    <Header />
    <main class="flex-1 flex flex-col items-center">
      <div class="w-full max-w-[1280px] px-8 py-10 flex flex-col gap-10">
        <div class="flex flex-col gap-4">
          <div class="flex items-center gap-3">
            <span class="bg-amber/10 text-amber text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest border border-amber/20">
              {{ authStore.isProvider ? 'Received' : 'Sent' }}
            </span>
          </div>
          <h1 class="text-white text-5xl font-extrabold tracking-tight leading-none">Job Invitations</h1>
          <p class="text-slate-400 text-lg">
            {{ authStore.isProvider ? 'Review and respond to job invitations' : 'Manage invitations you\'ve sent to providers' }}
          </p>
        </div>

        <div v-if="jobsStore.loading" class="flex justify-center py-12">
          <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
        </div>
        
        <div v-else-if="validInvitations.length === 0" class="text-center py-16">
          <div class="inline-flex items-center justify-center size-20 rounded-full bg-white/5 mb-4">
            <span class="material-symbols-outlined text-4xl text-slate-500">mail</span>
          </div>
          <p class="text-slate-500 mb-2">No invitations found</p>
          <p class="text-slate-600 text-sm">{{ authStore.isProvider ? 'Job invitations will appear here' : 'Send invitations to providers from job listings' }}</p>
        </div>

        <div v-else class="space-y-4">
          <Card
            v-for="invitation in validInvitations"
            :key="invitation.id"
            class="bg-midnight rounded-2xl border border-white/5 hover:border-white/10 transition-all p-6"
          >
            <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
              <div class="flex-1 space-y-3">
                <div class="flex items-center gap-3">
                  <span
                    :class="[
                      'px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider border',
                      invitation.status === 'PENDING' ? 'bg-amber/10 text-amber border-amber/20' : '',
                      invitation.status === 'ACCEPTED' ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20' : '',
                      invitation.status === 'DECLINED' ? 'bg-red-500/10 text-red-600 border-red-500/20' : '',
                    ]"
                  >
                    {{ invitation.status }}
                  </span>
                  <span class="text-slate-500 text-sm">{{ formatDate(invitation.invited_at || invitation.created_at) }}</span>
                </div>
                <h3 class="text-white text-2xl font-bold">
                  {{ getJobTitle(invitation.job) }}
                </h3>
                <p v-if="invitation.message" class="text-slate-400 text-sm leading-relaxed">
                  {{ invitation.message }}
                </p>
              </div>
              <div class="flex gap-3">
                <Button
                  v-if="invitation.status === 'PENDING' && authStore.isProvider"
                  variant="default"
                  size="default"
                  class="bg-emerald-600 text-white hover:bg-emerald-700"
                  @click="handleAccept(invitation.id)"
                >
                  <span class="material-symbols-outlined mr-2 text-lg">check</span>
                  Accept
                </Button>
                <Button
                  v-if="invitation.status === 'PENDING' && authStore.isProvider"
                  variant="outline"
                  size="default"
                  class="border-red-500/50 text-red-400 hover:bg-red-500/10 hover:text-red-300"
                  @click="handleDecline(invitation.id)"
                >
                  <span class="material-symbols-outlined mr-2 text-lg">close</span>
                  Decline
                </Button>
                <router-link
                  v-if="invitation.status === 'ACCEPTED' && authStore.isClient && getJobId(invitation.job) && getProviderId(invitation.provider)"
                  :to="`/contracts/create?job=${getJobId(invitation.job)}&provider=${getProviderId(invitation.provider)}`"
                >
                  <Button variant="default" size="default" class="bg-amber text-midnight hover:bg-amber-dark">
                    <span class="material-symbols-outlined mr-2 text-lg">description</span>
                    Create Contract
                  </Button>
                </router-link>
                <router-link v-if="getJobId(invitation.job)" :to="`/jobs/${getJobId(invitation.job)}`">
                  <Button variant="outline" size="default" class="border-white/10 text-slate-400 hover:text-white hover:border-white/20">
                    <span class="material-symbols-outlined mr-2 text-lg">visibility</span>
                    View Job
                  </Button>
                </router-link>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useJobsStore } from '@/stores/jobs'
import type { JobInvitation } from '@/services/jobs'
import Header from '@/components/Header.vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import { toast } from 'vue-sonner'

const authStore = useAuthStore()
const jobsStore = useJobsStore()

const validInvitations = computed(() => {
  const list = Array.isArray(jobsStore.invitations) ? jobsStore.invitations : []
  return list.filter((inv): inv is JobInvitation => inv != null && inv.id != null)
})

function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function getJobTitle(job: string | { title?: string } | any) {
  if (typeof job === 'object' && job?.title) return job.title
  return 'Job Invitation'
}

function getJobId(job: string | { id?: string } | any) {
  if (job == null) return null
  if (typeof job === 'string') return job
  return job?.id ?? null
}

function getProviderId(provider: string | { id?: string } | any) {
  if (provider == null) return null
  if (typeof provider === 'string') return provider
  return provider?.id ?? null
}

async function handleAccept(id: string) {
  try {
    await jobsStore.updateInvitation(id, { status: 'ACCEPTED' })
    await jobsStore.fetchInvitations()
    toast.success('Invitation accepted successfully')
  } catch (err) {
    console.error('Failed to accept invitation:', err)
    toast.error('Failed to accept invitation')
  }
}

async function handleDecline(id: string) {
  try {
    await jobsStore.updateInvitation(id, { status: 'DECLINED' })
    await jobsStore.fetchInvitations()
    toast.success('Invitation declined')
  } catch (err) {
    console.error('Failed to decline invitation:', err)
    toast.error('Failed to decline invitation')
  }
}

onMounted(async () => {
  await jobsStore.fetchInvitations()
})
</script>
