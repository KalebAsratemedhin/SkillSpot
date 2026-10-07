<template>
  <AppLayout>
    <div class="px-4 md:px-6 lg:px-20 py-6 md:py-10">
      <div class="mb-6 md:mb-8">
        <h1 class="text-2xl md:text-3xl font-display font-bold text-midnight">Requests</h1>
        <p class="text-slate-500 text-xs md:text-sm mt-1">
          {{
            authStore.isProvider
              ? 'Track your applications and job invitations'
              : 'Manage applications to your jobs and invitations you’ve sent'
          }}
        </p>
      </div>

      <div class="flex gap-8 border-b border-slate-200 mb-6 md:mb-8">
        <button
          type="button"
          class="relative pb-3 text-sm font-semibold transition-colors"
          :class="activeTab === 'applications' ? 'text-amber' : 'text-slate-500 hover:text-midnight'"
          @click="setTab('applications')"
        >
          Applications
          <span
            v-if="activeTab === 'applications'"
            class="absolute bottom-0 left-0 h-1 w-full bg-amber rounded-t-full"
          />
        </button>
        <button
          type="button"
          class="relative pb-3 text-sm font-semibold transition-colors"
          :class="activeTab === 'invitations' ? 'text-amber' : 'text-slate-500 hover:text-midnight'"
          @click="setTab('invitations')"
        >
          Invitations
          <span
            v-if="activeTab === 'invitations'"
            class="absolute bottom-0 left-0 h-1 w-full bg-amber rounded-t-full"
          />
        </button>
      </div>

      <!-- Applications -->
      <template v-if="activeTab === 'applications'">
        <div v-if="appsLoading" class="flex justify-center py-12">
          <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
        </div>
        <div v-else-if="validApplications.length === 0" class="text-center py-12">
          <p class="text-slate-500">No applications yet</p>
          <p class="text-slate-400 text-sm mt-1">
            {{
              authStore.isProvider
                ? 'Apply to jobs from Browse.'
                : 'Applications to your posted jobs will appear here.'
            }}
          </p>
        </div>
        <div v-else class="space-y-4 max-w-3xl">
          <Card
            v-for="app in validApplications"
            :key="app.id"
            class="bg-white rounded-xl p-5 shadow-sm border border-slate-200 hover:shadow-md transition-all cursor-pointer"
            :class="expandedId === app.id ? 'ring-2 ring-amber/30 border-amber/40' : ''"
            @click="toggleExpanded(app.id)"
          >
            <CardContent class="p-0">
              <div class="flex flex-col md:flex-row md:items-start justify-between gap-3">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 flex-wrap mb-1.5">
                    <span
                      :class="[
                        'px-2.5 py-1 rounded-full text-xs font-black uppercase tracking-wider',
                        app.status === 'PENDING' ? 'bg-amber/10 text-amber border border-amber/20' : '',
                        app.status === 'ACCEPTED' ? 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20' : '',
                        app.status === 'REJECTED' ? 'bg-red-500/10 text-red-600 border border-red-500/20' : '',
                        app.status === 'WITHDRAWN' ? 'bg-slate-400/10 text-slate-600 border border-slate-400/20' : '',
                      ]"
                    >
                      {{ app.status }}
                    </span>
                    <span class="text-slate-400 text-sm">{{ formatDate(app.applied_at || app.created_at) }}</span>
                  </div>
                  <h3 class="text-xl font-display font-bold text-midnight truncate">
                    {{ app.job_title || 'Job' }}
                  </h3>
                  <template v-if="authStore.isClient">
                    <p class="text-slate-600 text-sm truncate">
                      From {{ app.provider_name || app.provider_email }}
                      <span v-if="app.proposed_rate" class="text-slate-500"> · {{ formatRate(app.proposed_rate) }}</span>
                    </p>
                  </template>
                  <p
                    v-else-if="app.proposed_rate != null && expandedId !== app.id"
                    class="text-slate-500 text-sm mt-1"
                  >
                    {{ formatRate(app.proposed_rate) }}/hr
                  </p>
                  <p
                    v-if="app.cover_letter && expandedId !== app.id"
                    class="text-slate-600 text-sm mt-1.5 line-clamp-2"
                  >
                    {{ app.cover_letter }}
                  </p>

                  <div
                    v-if="expandedId === app.id"
                    class="mt-4 pt-4 border-t border-slate-100 space-y-4"
                    @click.stop
                  >
                    <div v-if="app.proposed_rate != null">
                      <p class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">Proposed rate</p>
                      <p class="text-midnight font-semibold">{{ formatRate(app.proposed_rate) }}/hr</p>
                    </div>
                    <div>
                      <p class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">Cover letter</p>
                      <p v-if="app.cover_letter" class="text-slate-700 text-sm whitespace-pre-wrap leading-relaxed">
                        {{ app.cover_letter }}
                      </p>
                      <p v-else class="text-slate-400 text-sm italic">No message provided.</p>
                    </div>
                    <div class="flex flex-wrap gap-2 pt-1">
                      <router-link
                        v-if="getAppJobId(app)"
                        :to="`/jobs/${getAppJobId(app)}`"
                        class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-midnight hover:border-slate-300 hover:bg-slate-50"
                      >
                        <span class="material-symbols-outlined text-base">visibility</span>
                        View job
                      </router-link>
                      <router-link
                        v-if="authStore.isClient && getAppProviderId(app)"
                        :to="`/providers/${getAppProviderId(app)}`"
                        class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-midnight hover:border-slate-300 hover:bg-slate-50"
                      >
                        <span class="material-symbols-outlined text-base">person</span>
                        View profile
                      </router-link>
                      <button
                        type="button"
                        class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-midnight hover:border-slate-300 hover:bg-slate-50 disabled:opacity-50"
                        :disabled="messageLoading === app.id"
                        @click="startConversation(app)"
                      >
                        <span v-if="messageLoading === app.id" class="material-symbols-outlined text-base animate-spin">refresh</span>
                        <span v-else class="material-symbols-outlined text-base">chat</span>
                        Message
                      </button>
                      <router-link
                        v-if="authStore.isClient && app.status === 'PENDING' && getAppJobId(app) && getAppProviderId(app)"
                        :to="{ path: '/contracts/create', query: { job: getAppJobId(app), application: app.id, provider: getAppProviderId(app) } }"
                        class="inline-flex items-center gap-1.5 rounded-lg bg-amber px-3 py-2 text-sm font-semibold text-midnight hover:bg-amber-dark"
                      >
                        <span class="material-symbols-outlined text-base">description</span>
                        Create contract
                      </router-link>
                    </div>
                  </div>
                </div>
                <div class="flex items-center gap-1 shrink-0" @click.stop>
                  <span
                    class="material-symbols-outlined text-slate-400 transition-transform"
                    :class="expandedId === app.id ? 'rotate-180' : ''"
                  >
                    expand_more
                  </span>
                  <div class="relative">
                    <button
                      type="button"
                      class="p-2 rounded-lg text-slate-500 hover:bg-slate-100 hover:text-midnight transition-colors"
                      :disabled="messageLoading === app.id"
                      aria-haspopup="true"
                      :aria-expanded="openDropdownId === app.id"
                      @click="openDropdownId = openDropdownId === app.id ? null : app.id"
                    >
                      <span class="material-symbols-outlined text-xl">more_vert</span>
                    </button>
                    <div
                      v-if="openDropdownId === app.id"
                      v-click-outside="() => (openDropdownId = null)"
                      class="absolute right-0 top-full mt-1 z-20 min-w-[180px] rounded-xl border border-slate-200 bg-white py-1 shadow-lg"
                    >
                      <router-link
                        v-if="authStore.isClient && app.provider"
                        :to="`/providers/${typeof app.provider === 'string' ? app.provider : (app.provider as { id: string }).id}`"
                        class="flex items-center gap-2 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50"
                        @click="openDropdownId = null"
                      >
                        <span class="material-symbols-outlined text-lg">person</span>
                        View Profile
                      </router-link>
                      <router-link
                        v-if="getAppJobId(app)"
                        :to="`/jobs/${getAppJobId(app)}`"
                        class="flex items-center gap-2 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50"
                        @click="openDropdownId = null"
                      >
                        <span class="material-symbols-outlined text-lg">visibility</span>
                        View Job
                      </router-link>
                      <button
                        type="button"
                        class="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-left text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                        :disabled="messageLoading === app.id"
                        @click="startConversation(app); openDropdownId = null"
                      >
                        <span v-if="messageLoading === app.id" class="material-symbols-outlined text-lg animate-spin">refresh</span>
                        <span v-else class="material-symbols-outlined text-lg">chat</span>
                        Message
                      </button>
                      <router-link
                        v-if="authStore.isClient && app.status === 'PENDING' && getAppJobId(app) && getAppProviderId(app)"
                        :to="{ path: '/contracts/create', query: { job: getAppJobId(app), application: app.id, provider: getAppProviderId(app) } }"
                        class="flex items-center gap-2 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50"
                        @click="openDropdownId = null"
                      >
                        <span class="material-symbols-outlined text-lg">description</span>
                        Create Contract
                      </router-link>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </template>

      <!-- Invitations -->
      <template v-else>
        <div v-if="invitesLoading" class="flex justify-center py-12">
          <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
        </div>
        <div v-else-if="validInvitations.length === 0" class="text-center py-12">
          <p class="text-slate-500">No invitations yet</p>
          <p class="text-slate-400 text-sm mt-1">
            {{
              authStore.isProvider
                ? 'Job invitations will appear here.'
                : 'Send invitations to providers from your job posts.'
            }}
          </p>
        </div>
        <div v-else class="space-y-4 max-w-3xl">
          <Card
            v-for="invitation in validInvitations"
            :key="invitation.id"
            class="bg-white rounded-xl p-5 shadow-sm border border-slate-200"
          >
            <CardContent class="p-0">
              <div class="flex flex-col md:flex-row md:items-start justify-between gap-4">
                <div class="flex-1 min-w-0 space-y-2">
                  <div class="flex items-center gap-2 flex-wrap">
                    <span
                      :class="[
                        'px-2.5 py-1 rounded-full text-xs font-black uppercase tracking-wider border',
                        invitation.status === 'PENDING' ? 'bg-amber/10 text-amber border-amber/20' : '',
                        invitation.status === 'ACCEPTED' ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20' : '',
                        invitation.status === 'DECLINED' ? 'bg-red-500/10 text-red-600 border-red-500/20' : '',
                      ]"
                    >
                      {{ invitation.status }}
                    </span>
                    <span class="text-slate-400 text-sm">
                      {{ formatDate(invitation.invited_at ?? invitation.created_at ?? '') }}
                    </span>
                  </div>
                  <h3 class="text-xl font-display font-bold text-midnight truncate">
                    {{ getJobTitle(invitation.job) }}
                  </h3>
                  <p v-if="invitation.message" class="text-slate-600 text-sm leading-relaxed">
                    {{ invitation.message }}
                  </p>
                </div>
                <div class="flex flex-wrap gap-2 shrink-0">
                  <Button
                    v-if="invitation.status === 'PENDING' && authStore.isProvider"
                    variant="default"
                    size="default"
                    class="bg-emerald-600 text-white hover:bg-emerald-700"
                    @click="handleAccept(invitation.id)"
                  >
                    Accept
                  </Button>
                  <Button
                    v-if="invitation.status === 'PENDING' && authStore.isProvider"
                    variant="outline"
                    size="default"
                    class="border-red-200 text-red-600 hover:bg-red-50"
                    @click="handleDecline(invitation.id)"
                  >
                    Decline
                  </Button>
                  <router-link
                    v-if="invitation.status === 'ACCEPTED' && authStore.isClient && getJobId(invitation.job) && getProviderId(invitation.provider)"
                    :to="`/contracts/create?job=${getJobId(invitation.job)}&provider=${getProviderId(invitation.provider)}`"
                  >
                    <Button variant="default" size="default" class="bg-amber text-midnight">
                      Create contract
                    </Button>
                  </router-link>
                  <router-link v-if="getJobId(invitation.job)" :to="`/jobs/${getJobId(invitation.job)}`">
                    <Button variant="outline" size="default">
                      View job
                    </Button>
                  </router-link>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </template>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useJobsStore } from '@/stores/jobs'
import { useMessagingStore } from '@/stores/messaging'
import type { JobApplication, JobInvitation } from '@/services/jobs'
import AppLayout from '@/components/AppLayout.vue'
import Card from '@/components/ui/Card.vue'
import CardContent from '@/components/ui/CardContent.vue'
import Button from '@/components/ui/Button.vue'
import { toast } from 'vue-sonner'

type Tab = 'applications' | 'invitations'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const jobsStore = useJobsStore()
const messagingStore = useMessagingStore()
const messageLoading = ref<string | null>(null)
const openDropdownId = ref<string | null>(null)
const expandedId = ref<string | null>(null)
const appsLoading = ref(false)
const invitesLoading = ref(false)
const invitesLoaded = ref(false)

const activeTab = computed<Tab>(() =>
  route.query.tab === 'invitations' ? 'invitations' : 'applications'
)

const vClickOutside = {
  mounted(el: HTMLElement, binding: { value: () => void }) {
    const handler = (e: MouseEvent) => {
      if (el && !el.contains(e.target as Node)) binding.value()
    }
    ;(el as any)._clickOutside = handler
    setTimeout(() => document.addEventListener('click', handler), 0)
  },
  unmounted(el: HTMLElement) {
    const fn = (el as any)._clickOutside
    if (fn) document.removeEventListener('click', fn)
  },
}

const validApplications = computed(() => {
  const list = Array.isArray(jobsStore.applications) ? jobsStore.applications : []
  return list.filter((app): app is NonNullable<typeof app> => app != null && app.id != null)
})

const validInvitations = computed(() => {
  const list = Array.isArray(jobsStore.invitations) ? jobsStore.invitations : []
  return list.filter((inv): inv is JobInvitation => inv != null && inv.id != null)
})

function setTab(tab: Tab) {
  router.replace({
    name: 'applications',
    query: tab === 'invitations' ? { tab: 'invitations' } : {},
  })
}

function toggleExpanded(id: string) {
  expandedId.value = expandedId.value === id ? null : id
  openDropdownId.value = null
}

async function startConversation(app: JobApplication) {
  if (!app.job) return
  const otherId = authStore.isClient ? app.provider : (app as { job_client?: string }).job_client
  if (!otherId) return
  messageLoading.value = app.id
  try {
    const conv = await messagingStore.createConversation({
      participant2_id: otherId,
      initial_message: '',
    })
    if (conv?.id && conv.id !== 'undefined') {
      router.push(`/messages/${conv.id}`)
    } else {
      toast.error('Conversation created but could not open it.')
    }
  } catch (err: any) {
    const msg = err.response?.data?.participant2_id?.[0] ?? err.response?.data?.detail ?? 'Failed to start conversation'
    toast.error(msg)
  } finally {
    messageLoading.value = null
  }
}

function getAppJobId(app: JobApplication): string | null {
  if (!app) return null
  const j = app.job
  if (typeof j === 'string') return j || null
  if (j && typeof j === 'object' && 'id' in j) return (j as { id: string }).id
  return null
}

function getAppProviderId(app: JobApplication): string | null {
  if (!app) return null
  const p = app.provider
  if (typeof p === 'string') return p || null
  if (p && typeof p === 'object' && 'id' in p) return (p as { id: string }).id
  return null
}

function formatDate(dateString: string) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatRate(rate: number | string) {
  const n = typeof rate === 'string' ? parseFloat(rate) : rate
  return Number.isNaN(n) ? '—' : 'Br ' + Number(n).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
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
    toast.success('Invitation accepted')
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

async function loadApplications() {
  appsLoading.value = true
  try {
    await jobsStore.fetchMyApplications()
  } finally {
    appsLoading.value = false
  }
}

async function loadInvitations() {
  invitesLoading.value = true
  try {
    await jobsStore.fetchInvitations()
    invitesLoaded.value = true
  } finally {
    invitesLoading.value = false
  }
}

onMounted(async () => {
  if (authStore.isClient && !authStore.isProvider) {
    await router.replace({ name: 'jobs' })
    return
  }
  await loadApplications()
  if (activeTab.value === 'invitations') {
    await loadInvitations()
  }
})

watch(activeTab, async (tab) => {
  if (tab === 'invitations' && !invitesLoaded.value) {
    await loadInvitations()
  }
})
</script>
