<template>
  <div class="min-h-screen bg-[#020617]">
    <Header />
    <main class="flex-1 flex flex-col items-center">
      <div class="w-full max-w-[1280px] px-8 py-10 flex flex-col gap-10">
        <div v-if="loading" class="flex justify-center py-12">
          <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
        </div>
        <div v-else-if="!contract" class="text-center py-16 text-slate-500">Contract not found.</div>
        <div v-else-if="paymentMode === 'fixed' || paymentMode === 'time-entry' || (paymentMode === 'milestone' && milestone)" class="space-y-10">
          <div class="flex flex-col gap-4">
            <div class="flex items-center gap-3">
              <span class="bg-amber/10 text-amber text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest border border-amber/20">Payment</span>
              <p class="text-slate-500 text-sm font-mono tracking-tighter">#SS-{{ contract.id.slice(0, 8).toUpperCase() }}</p>
            </div>
            <h1 class="text-white text-5xl font-extrabold tracking-tight leading-none">{{ paymentTitle }}</h1>
            <p class="text-slate-400">{{ paymentSubtitle }}</p>
          </div>
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-10">
            <div class="lg:col-span-2">
              <Card class="bg-midnight rounded-3xl border border-white/10 shadow-[0_30px_60px_-12px_rgba(0,0,0,0.5)] overflow-hidden">
                <div class="bg-gradient-to-br from-midnight-light to-midnight px-8 py-8 border-b border-white/5">
                  <div class="flex justify-between items-start mb-4">
                    <div>
                      <p class="text-amber text-xs font-black uppercase tracking-widest mb-1">Payment Amount</p>
                      <h3 class="text-white text-2xl font-black">Br {{ payAmount.toLocaleString() }}</h3>
                    </div>
                    <div class="p-2 bg-amber/10 rounded-xl text-amber">
                      <span class="material-symbols-outlined text-2xl">account_balance_wallet</span>
                    </div>
                  </div>
                </div>
                <CardContent class="p-8 flex flex-col gap-8">
                  <div class="pt-4 border-t border-white/5 flex justify-between items-end">
                    <div>
                      <p class="text-slate-500 text-[10px] font-black uppercase tracking-widest">Amount to Pay</p>
                      <p class="text-white text-3xl font-black tracking-tight">Br {{ payAmount.toLocaleString() }}</p>
                    </div>
                    <div class="text-right">
                      <p class="text-emerald-500 text-[10px] font-black uppercase tracking-widest mb-1">Includes Tax</p>
                      <p class="text-slate-500 text-xs">{{ contract.currency || 'ETB' }}</p>
                    </div>
                  </div>
                  <div class="bg-white/5 p-4 rounded-xl border border-white/5 flex gap-3">
                    <span class="material-symbols-outlined text-amber">shield_with_heart</span>
                    <p class="text-slate-400 text-[11px] leading-relaxed">
                      SkillSpot Escrow Protection active. Funds are held securely and released when you approve the work.
                    </p>
                  </div>
                  <div class="flex flex-col gap-4">
                    <Button
                      variant="default"
                      size="lg"
                      @click="handlePayment"
                      :loading="processing"
                      class="w-full h-14 bg-[#635bff] hover:bg-[#7a73ff] text-white font-bold shadow-xl"
                    >
                      <svg class="w-5 h-5 mr-2" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
                        <path d="M34.722 17.58c0-5.321-2.731-8.527-7.462-8.527-4.325 0-7.23 2.152-7.23 2.152l-1.043-1.637s-3.52-1.39-5.118-1.39C9.366 8.178 6 12.33 6 18.064c0 6.641 3.966 9.423 9.471 9.423 4.14 0 7.848-1.956 7.848-1.956s.904 1.34 1.151 1.696c2.091 0 4.398-.946 5.378-1.425.074.053 4.874-2.723 4.874-8.222zm-12.793 4.321s-2.316 1.096-4.996 1.096c-3.141 0-5.397-1.425-5.397-5.027 0-3.615 2.126-5.467 5.174-5.467 2.478 0 4.35 1.069 4.35 1.069l.869 8.329zm9.052-1.503c-.63 0-1.873.315-1.873.315l-.801-7.794s1.171-.462 2.373-.462c2.441 0 3.864 1.487 3.864 4.09 0 2.502-1.353 3.851-3.563 3.851z" fill="currentColor"></path>
                      </svg>
                      Pay with Stripe
                    </Button>
                    <div class="flex justify-center items-center gap-3 opacity-40">
                      <span class="h-px w-8 bg-slate-500"></span>
                      <div class="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-300">
                        <span class="material-symbols-outlined text-sm">lock</span>
                        SECURE ENCRYPTED PAYMENT
                      </div>
                      <span class="h-px w-8 bg-slate-500"></span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
            <div class="lg:col-span-1">
              <Card class="bg-midnight rounded-2xl border border-white/5 p-6">
                <h3 class="text-white text-xs font-black uppercase tracking-widest opacity-50 mb-4">Payment Summary</h3>
                <div class="space-y-3">
                  <div class="flex justify-between text-sm">
                    <span class="text-slate-400">Contract</span>
                    <span class="text-white font-bold">#{{ contract.id.slice(0, 8) }}</span>
                  </div>
                  <div v-if="paymentMode === 'milestone' && milestone" class="flex justify-between text-sm">
                    <span class="text-slate-400">Milestone</span>
                    <span class="text-white font-bold">{{ milestone.title }}</span>
                  </div>
                  <div v-if="paymentMode === 'time-entry' && timeEntry" class="flex justify-between text-sm">
                    <span class="text-slate-400">Time entry</span>
                    <span class="text-white font-bold">{{ formatDate(timeEntry.date) }} – {{ timeEntry.hours }}h</span>
                  </div>
                  <div class="flex justify-between text-sm">
                    <span class="text-slate-400">Amount</span>
                    <span class="text-amber font-bold">Br {{ payAmount.toLocaleString() }}</span>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { contractsService, type Contract, type ContractMilestone, type TimeEntry } from '@/services/contracts'
import { paymentsService } from '@/services/payments'
import { toast } from 'vue-sonner'
import Header from '@/components/Header.vue'
import Card from '@/components/ui/Card.vue'
import CardContent from '@/components/ui/CardContent.vue'
import Button from '@/components/ui/Button.vue'

const route = useRoute()
const contract = ref<Contract | null>(null)
const milestone = ref<ContractMilestone | null>(null)
const timeEntry = ref<TimeEntry | null>(null)
const loading = ref(false)
const processing = ref(false)

const contractId = computed(() => route.params.contractId as string)
const milestoneId = computed(() => route.params.milestoneId as string | undefined)
const timeEntryId = computed(() => route.params.timeEntryId as string | undefined)

const paymentMode = computed(() => {
  if (timeEntryId.value) return 'time-entry'
  if (milestoneId.value) return 'milestone'
  return 'fixed'
})

const payAmount = computed(() => {
  if (paymentMode.value === 'time-entry' && timeEntry.value?.amount != null) return Number(timeEntry.value.amount)
  if (paymentMode.value === 'milestone' && milestone.value) return Number(milestone.value.amount)
  if (contract.value) return Number(contract.value.total_amount)
  return 0
})

const paymentTitle = computed(() => {
  if (paymentMode.value === 'fixed') return 'Full amount payment'
  if (paymentMode.value === 'time-entry') return 'Time entry payment'
  return 'Milestone Payment'
})

const paymentSubtitle = computed(() => {
  if (paymentMode.value === 'fixed') return 'Pay the full contract amount once work is complete.'
  if (paymentMode.value === 'time-entry' && timeEntry.value) return `${timeEntry.value.date} – ${timeEntry.value.hours}h`
  if (milestone.value) return milestone.value.title
  return ''
})

function formatDate(dateString: string) {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

async function handlePayment() {
  if (!contract.value) return
  if (paymentMode.value === 'milestone' && !milestone.value) return
  if (paymentMode.value === 'time-entry' && !timeEntry.value) return
  processing.value = true
  try {
    const payload: Parameters<typeof paymentsService.create>[0] = {
      contract: contract.value.id,
      amount: payAmount.value,
      currency: contract.value.currency || 'ETB',
      payment_method: 'STRIPE',
    }
    if (paymentMode.value === 'milestone' && milestone.value) {
      payload.milestone_id = milestone.value.id
      payload.description = `Payment for milestone: ${milestone.value.title}`
    } else if (paymentMode.value === 'time-entry' && timeEntry.value) {
      payload.time_entry_id = timeEntry.value.id
      payload.description = `Payment for time entry: ${timeEntry.value.date}`
    } else {
      payload.description = 'Full contract payment'
    }
    const paymentRes = await paymentsService.create(payload)
    const payment = paymentRes.data
    const sessionRes = await paymentsService.createCheckoutSession({
      payment_id: payment.id,
      success_url: `${window.location.origin}/contracts/${contract.value.id}?payment=success`,
      cancel_url: `${window.location.origin}/payments/contract/${contract.value.id}`,
    })
    const checkoutUrl = sessionRes.data?.url
    if (checkoutUrl) {
      toast.success('Redirecting to Stripe to complete payment.')
      window.location.href = checkoutUrl
    } else {
      toast.error('Could not start checkout.')
      processing.value = false
    }
  } catch (err: any) {
    const msg = err.response?.data?.error ?? err.response?.data?.detail ?? 'Failed to start payment.'
    console.error('Failed to create payment:', err)
    toast.error(msg)
  } finally {
    processing.value = false
  }
}

onMounted(async () => {
  const cId = contractId.value
  if (!cId) return
  loading.value = true
  try {
    contract.value = (await contractsService.get(cId)).data
    if (milestoneId.value) {
      const res = await contractsService.getMilestones(cId)
      const list = res.data.results ?? []
      milestone.value = list.find((m: { id: string }) => m.id === milestoneId.value) ?? null
    } else if (timeEntryId.value) {
      const res = await contractsService.getTimeEntries(cId)
      const list = res.data.results ?? []
      timeEntry.value = list.find((t: { id: string }) => t.id === timeEntryId.value) ?? null
    }
  } catch (err) {
    console.error('Failed to fetch payment data:', err)
  } finally {
    loading.value = false
  }
})
</script>
