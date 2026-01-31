<template>
  <AppLayout>
    <div class="max-w-[1400px] mx-auto px-6 lg:px-20 py-10">
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-3xl font-display font-bold text-midnight">Job Invitations</h1>
          <p class="text-slate-500 text-sm mt-1">Manage your job invitations and applications</p>
        </div>
      </div>
      <div v-if="jobsStore.loading" class="flex justify-center py-12">
        <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
      </div>
      <div v-else-if="validInvitations.length === 0" class="text-center py-12">
        <p class="text-slate-500">No invitations found</p>
      </div>
      <div v-else class="space-y-4">
        <Card
          v-for="invitation in validInvitations"
          :key="invitation.id"
          class="bg-white rounded-2xl p-7 shadow-sm border border-slate-200 hover:shadow-md transition-all"
        >
          <CardContent class="p-0">
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div class="flex-1">
                <div class="flex items-center gap-3 mb-3">
                  <span
                    :class="[
                      'px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider',
                      invitation.status === 'PENDING' ? 'bg-amber/10 text-amber border border-amber/20' : '',
                      invitation.status === 'ACCEPTED' ? 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20' : '',
                      invitation.status === 'DECLINED' ? 'bg-red-500/10 text-red-600 border border-red-500/20' : '',
                    ]"
                  >
                    {{ invitation.status }}
                  </span>
                  <span class="text-slate-400 text-sm">{{ formatDate(invitation.invited_at || invitation.created_at) }}</span>
                </div>
                <h3 class="text-xl font-display font-bold text-midnight mb-2">
                  {{ getJobTitle(invitation.job) }}
                </h3>
                <p v-if="invitation.message" class="text-slate-600 text-sm leading-relaxed">
                  {{ invitation.message }}
                </p>
              </div>
              <div class="flex gap-3">
                <Button
                  v-if="invitation.status === 'PENDING' && authStore.isProvider"
                  variant="default"
                  @click="handleAccept(invitation.id)"
                >
                  Accept
                </Button>
                <Button
                  v-if="invitation.status === 'PENDING' && authStore.isProvider"
                  variant="outline"
                  @click="handleDecline(invitation.id)"
                  class="border-2 border-slate-200"
                >
                  Decline
                </Button>
                <router-link v-if="getJobId(invitation.job)" :to="`/jobs/${getJobId(invitation.job)}`">
                  <Button variant="secondary" class="bg-midnight text-white hover:bg-midnight-light">
                    View Job
                  </Button>
                </router-link>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useJobsStore } from '@/stores/jobs'
import type { JobInvitation } from '@/services/jobs'
import AppLayout from '@/components/AppLayout.vue'
import Card from '@/components/ui/Card.vue'
import CardContent from '@/components/ui/CardContent.vue'
import Button from '@/components/ui/Button.vue'

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

async function handleAccept(id: string) {
  try {
    await jobsStore.updateInvitation(id, { status: 'ACCEPTED' })
    await jobsStore.fetchInvitations()
  } catch (err) {
    console.error('Failed to accept invitation:', err)
  }
}

async function handleDecline(id: string) {
  try {
    await jobsStore.updateInvitation(id, { status: 'DECLINED' })
    await jobsStore.fetchInvitations()
  } catch (err) {
    console.error('Failed to decline invitation:', err)
  }
}

onMounted(async () => {
  await jobsStore.fetchInvitations()
})
</script>
