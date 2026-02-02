<template>
  <AppLayout>
    <div class="px-4 md:px-6 lg:px-20 py-6 md:py-10">
      <div class="flex items-center justify-between mb-6 md:mb-8">
        <div>
          <h1 class="text-2xl md:text-3xl font-display font-bold text-midnight">My Applications</h1>
          <p class="text-slate-500 text-xs md:text-sm mt-1">
            {{ authStore.isProvider ? 'Applications you’ve submitted' : 'Applications to your jobs' }}
          </p>
        </div>
      </div>
      <div v-if="jobsStore.loading" class="flex justify-center py-12">
        <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
      </div>
      <div v-else-if="validApplications.length === 0" class="text-center py-12">
        <p class="text-slate-500">No applications yet</p>
        <p class="text-slate-400 text-sm mt-1">
          {{ authStore.isProvider ? 'Apply to jobs from Browse Jobs or My Jobs.' : 'Applications to your posted jobs will appear here.' }}
        </p>
      </div>
      <div v-else class="space-y-4 max-w-3xl">
        <Card
          v-for="app in validApplications"
          :key="app.id"
          class="bg-white rounded-xl p-5 shadow-sm border border-slate-200 hover:shadow-md transition-all"
        >
          <CardContent class="p-0">
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
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
                <p v-if="app.cover_letter" class="text-slate-600 text-sm mt-1.5 line-clamp-2">
                  {{ app.cover_letter }}
                </p>
              </div>
              <div class="relative flex items-center shrink-0 overflow-visible">
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
          </CardContent>
        </Card>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useJobsStore } from '@/stores/jobs'
import { useMessagingStore } from '@/stores/messaging'
import type { JobApplication } from '@/services/jobs'
import AppLayout from '@/components/AppLayout.vue'
import Card from '@/components/ui/Card.vue'
import CardContent from '@/components/ui/CardContent.vue'
import { toast } from 'vue-sonner'

const router = useRouter()
const authStore = useAuthStore()
const jobsStore = useJobsStore()
const messagingStore = useMessagingStore()
const messageLoading = ref<string | null>(null)
const openDropdownId = ref<string | null>(null)

const vClickOutside = {
  mounted(el: HTMLElement, binding: { value: () => void }) {
    const handler = (e: MouseEvent) => {
      if (el && !el.contains(e.target as Node)) binding.value()
    }
    ;(el as any)._clickOutside = handler
    // Defer so the click that opened the dropdown doesn't immediately trigger close
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

async function startConversation(app: JobApplication) {
  if (!app.job) return
  const otherId = authStore.isClient ? app.provider : (app as { job_client?: string }).job_client
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
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatRate(rate: number | string) {
  const n = typeof rate === 'string' ? parseFloat(rate) : rate
  return Number.isNaN(n) ? '—' : 'Br ' + Number(n).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

onMounted(async () => {
  await jobsStore.fetchMyApplications()
})
</script>
