<template>
  <AppLayout>
    <div class="min-h-[60vh] flex flex-col items-center justify-center px-4 py-12 bg-slate-50">
      <div v-if="isReturn" class="max-w-md w-full text-center space-y-6">
        <div v-if="loading" class="flex flex-col items-center gap-4">
          <span class="material-symbols-outlined animate-spin text-5xl text-amber">refresh</span>
          <p class="text-slate-600 font-medium">Checking your Stripe account…</p>
        </div>

        <!-- Fully ready -->
        <template v-else-if="outcome === 'ready'">
          <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-100 text-emerald-600 mb-2">
            <span class="material-symbols-outlined text-4xl">check_circle</span>
          </div>
          <h1 class="text-2xl font-bold text-midnight">Stripe account connected</h1>
          <p class="text-slate-600">
            Your account is set up. You can now receive payments from clients.
          </p>
          <div class="flex flex-col sm:flex-row gap-3 justify-center pt-2">
            <Button
              variant="default"
              size="lg"
              class="bg-amber text-midnight hover:bg-amber/90"
              @click="router.push('/profile')"
            >
              Continue to Profile
            </Button>
            <Button variant="outline" size="lg" @click="router.push('/payments')">
              View Payments
            </Button>
          </div>
          <p class="text-slate-400 text-sm">
            Redirecting to your profile in {{ countdown }}s…
          </p>
        </template>

        <!-- Account exists but onboarding / capabilities incomplete -->
        <template v-else-if="outcome === 'incomplete'">
          <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-amber/15 text-amber mb-2">
            <span class="material-symbols-outlined text-4xl">pending</span>
          </div>
          <h1 class="text-2xl font-bold text-midnight">Almost done</h1>
          <p class="text-slate-600">
            Your Stripe account was created, but setup isn’t finished yet. Complete any remaining
            requirements (or wait if Stripe is still verifying) before you can receive payments.
          </p>
          <div class="flex flex-col gap-3 justify-center pt-2">
            <Button
              variant="default"
              size="lg"
              class="bg-[#635bff] hover:bg-[#7a73ff] text-white"
              :loading="actionLoading === 'onboard'"
              @click="resumeOnboarding"
            >
              Finish Stripe setup
            </Button>
            <Button
              variant="outline"
              size="lg"
              :loading="actionLoading === 'dashboard'"
              @click="openDashboard"
            >
              Open Stripe dashboard
            </Button>
            <Button variant="outline" size="lg" @click="router.push('/profile')">
              Back to Profile
            </Button>
          </div>
        </template>

        <!-- No account or status failure -->
        <template v-else>
          <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 text-red-600 mb-2">
            <span class="material-symbols-outlined text-4xl">error</span>
          </div>
          <h1 class="text-2xl font-bold text-midnight">Couldn’t confirm Stripe setup</h1>
          <p class="text-slate-600">
            {{ errorMessage || 'We couldn’t verify your Stripe account status. Try again from your profile.' }}
          </p>
          <div class="flex flex-col sm:flex-row gap-3 justify-center pt-2">
            <Button
              variant="default"
              size="lg"
              class="bg-amber text-midnight hover:bg-amber/90"
              @click="router.push('/profile')"
            >
              Try again from Profile
            </Button>
            <Button
              variant="outline"
              size="lg"
              :loading="actionLoading === 'retry'"
              @click="refreshStatus"
            >
              Check again
            </Button>
          </div>
        </template>
      </div>

      <div v-else class="max-w-md w-full text-center space-y-6">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-amber/10 text-amber mb-2">
          <span class="material-symbols-outlined text-4xl">schedule</span>
        </div>
        <h1 class="text-2xl font-bold text-midnight">Session expired</h1>
        <p class="text-slate-600">
          Your Stripe onboarding session expired. You can start again from your profile.
        </p>
        <Button
          variant="default"
          size="lg"
          class="bg-amber text-midnight hover:bg-amber/90"
          @click="router.push('/profile')"
        >
          Go to Profile
        </Button>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import AppLayout from '@/components/AppLayout.vue'
import Button from '@/components/ui/Button.vue'
import { paymentsService, type StripeConnectStatus } from '@/services/payments'

type Outcome = 'ready' | 'incomplete' | 'error'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const countdown = ref(5)
const status = ref<StripeConnectStatus | null>(null)
const errorMessage = ref('')
const actionLoading = ref<'onboard' | 'dashboard' | 'retry' | null>(null)
let countdownTimer: ReturnType<typeof setInterval> | null = null

const isReturn = computed(() => route.path.endsWith('/return'))

const outcome = computed<Outcome>(() => {
  if (!status.value) return 'error'
  if (status.value.enabled) return 'ready'
  if (status.value.has_account) return 'incomplete'
  return 'error'
})

function clearCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

function startReadyCountdown() {
  clearCountdown()
  countdown.value = 5
  countdownTimer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) {
      clearCountdown()
      router.push('/profile')
    }
  }, 1000)
}

async function fetchStatusOnce(): Promise<StripeConnectStatus> {
  const res = await paymentsService.getStripeConnectStatus()
  return res.data
}

/** Stripe can lag right after redirect — poll a couple times before deciding. */
async function loadStatusWithPoll() {
  loading.value = true
  errorMessage.value = ''
  clearCountdown()
  try {
    let latest = await fetchStatusOnce()
    status.value = latest

    if (!latest.enabled && latest.has_account) {
      await new Promise((r) => setTimeout(r, 1500))
      latest = await fetchStatusOnce()
      status.value = latest
    }
    if (!latest.enabled && latest.has_account) {
      await new Promise((r) => setTimeout(r, 1500))
      latest = await fetchStatusOnce()
      status.value = latest
    }

    if (latest.enabled) startReadyCountdown()
  } catch (err: any) {
    status.value = null
    errorMessage.value =
      err.response?.data?.error ??
      err.response?.data?.detail ??
      'Failed to load Stripe account status.'
  } finally {
    loading.value = false
  }
}

async function refreshStatus() {
  actionLoading.value = 'retry'
  try {
    await loadStatusWithPoll()
  } finally {
    actionLoading.value = null
  }
}

async function resumeOnboarding() {
  actionLoading.value = 'onboard'
  try {
    const res = await paymentsService.onboardStripeConnect()
    const url = res.data.onboarding_url
    if (url) window.location.href = url
    else toast.error('Could not get Stripe onboarding link')
  } catch (err: any) {
    toast.error(err.response?.data?.error ?? 'Failed to restart Stripe setup')
  } finally {
    actionLoading.value = null
  }
}

async function openDashboard() {
  actionLoading.value = 'dashboard'
  try {
    const res = await paymentsService.loginStripeConnect()
    const url = res.data.login_url
    if (url) window.open(url, '_blank', 'noopener,noreferrer')
    else toast.error('Could not open Stripe dashboard')
  } catch (err: any) {
    toast.error(err.response?.data?.error ?? 'Failed to open Stripe dashboard')
  } finally {
    actionLoading.value = null
  }
}

onMounted(async () => {
  if (!isReturn.value) {
    loading.value = false
    return
  }
  await loadStatusWithPoll()
})

onUnmounted(() => {
  clearCountdown()
})
</script>
