<template>
  <AppLayout>
    <div class="min-h-[60vh] flex flex-col items-center justify-center px-4 py-12 bg-slate-50">
      <div v-if="isReturn" class="max-w-md w-full text-center space-y-6">
        <div v-if="loading" class="flex flex-col items-center gap-4">
          <span class="material-symbols-outlined animate-spin text-5xl text-amber">refresh</span>
          <p class="text-slate-600 font-medium">Updating your Stripe account...</p>
        </div>
        <template v-else>
          <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-100 text-emerald-600 mb-4">
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
            <Button
              variant="outline"
              size="lg"
              @click="router.push('/payments')"
            >
              View Payments
            </Button>
          </div>
          <p class="text-slate-400 text-sm">
            Redirecting to your profile in {{ countdown }}s...
          </p>
        </template>
      </div>
      <div v-else class="max-w-md w-full text-center space-y-6">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-amber/10 text-amber mb-4">
          <span class="material-symbols-outlined text-4xl">schedule</span>
        </div>
        <h1 class="text-2xl font-bold text-midnight">Session expired</h1>
        <p class="text-slate-600">
          Your Stripe onboarding session expired. You can start again or complete setup from your profile.
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
import AppLayout from '@/components/AppLayout.vue'
import Button from '@/components/ui/Button.vue'
import { paymentsService } from '@/services/payments'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const countdown = ref(5)
let countdownTimer: ReturnType<typeof setInterval> | null = null

const isReturn = computed(() => route.path.endsWith('/return'))

onMounted(async () => {
  if (!isReturn.value) {
    loading.value = false
    return
  }
  try {
    await paymentsService.getStripeConnectStatus()
  } catch {
    // Still show success; backend may sync later
  } finally {
    loading.value = false
  }
  countdownTimer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0 && countdownTimer) {
      clearInterval(countdownTimer)
      router.push('/profile')
    }
  }, 1000)
})

onUnmounted(() => {
  if (countdownTimer) clearInterval(countdownTimer)
})
</script>




