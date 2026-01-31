<template>
  <div class="min-h-screen bg-[#020617]">
    <Header />
    <main class="flex-1 flex flex-col items-center">
      <div class="w-full max-w-[1280px] px-8 py-10 flex flex-col gap-10">
        <div v-if="loading" class="flex justify-center py-12">
          <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
        </div>
        <div v-else-if="contract" class="space-y-10">
          <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div class="flex flex-col gap-4">
              <div class="flex items-center gap-3">
                <span class="bg-amber/10 text-amber text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest border border-amber/20">Active Contract</span>
                <p class="text-slate-500 text-sm font-mono tracking-tighter">#SS-{{ contract.id.slice(0, 8).toUpperCase() }}</p>
              </div>
              <h1 class="text-white text-5xl font-extrabold tracking-tight leading-none">{{ contractTitle }}</h1>
            </div>
            <div class="flex gap-4 flex-wrap">
              <Button variant="outline" size="default" class="border-2 border-white/10 bg-white/5 text-white hover:bg-white/10">
                <span class="material-symbols-outlined mr-2 text-lg">description</span>
                View Agreement
              </Button>
              <Button
                variant="default"
                size="default"
                class="bg-amber text-midnight hover:bg-amber-dark shadow-lg shadow-amber/20"
                :disabled="contactLoading"
                @click="openConversation"
              >
                <span v-if="contactLoading" class="material-symbols-outlined mr-2 text-lg animate-spin">refresh</span>
                <span v-else class="material-symbols-outlined mr-2 text-lg">mail</span>
                {{ authStore.user?.id === contract.client ? 'Contact Provider' : 'Contact Client' }}
              </Button>
              <Button
                v-if="canSign"
                variant="default"
                size="default"
                class="bg-emerald-600 text-white hover:bg-emerald-700"
                :disabled="signLoading"
                @click="handleSign"
              >
                <span v-if="signLoading" class="material-symbols-outlined mr-2 text-lg animate-spin">refresh</span>
                <span v-else class="material-symbols-outlined mr-2 text-lg">draw</span>
                Sign Contract
              </Button>
            </div>
          </div>
          <div class="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
            <div class="lg:col-span-7 flex flex-col gap-10">
              <Card class="bg-midnight rounded-2xl border border-white/5 shadow-2xl overflow-hidden">
                <div class="px-8 py-6 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
                  <h2 class="text-white text-lg font-bold flex items-center gap-2">
                    <span class="material-symbols-outlined text-amber">account_tree</span>
                    Project Roadmap
                  </h2>
                  <div class="flex items-center gap-2">
                    <span class="size-2 rounded-full bg-amber animate-pulse"></span>
                    <span class="text-xs font-bold text-slate-400 uppercase tracking-widest">Phase {{ activePhase }} Active</span>
                  </div>
                </div>
                <CardContent class="p-8">
                  <div class="relative">
                    <div class="absolute left-[19px] top-6 bottom-6 w-[2px] bg-slate-800"></div>
                    <div
                      v-for="(milestone, index) in sortedMilestones"
                      :key="milestone.id"
                      class="relative flex gap-6"
                      :class="index < sortedMilestones.length - 1 ? 'pb-12' : ''"
                    >
                      <div
                        :class="[
                          'z-10 flex items-center justify-center size-10 rounded-full border-4 border-midnight',
                          milestone.status === 'COMPLETED' ? 'bg-slate-800 text-emerald-500' : '',
                          milestone.status === 'IN_PROGRESS' ? 'bg-gradient-to-b from-amber to-amber-dark text-midnight ring-8 ring-amber/10' : '',
                          milestone.status === 'PENDING' ? 'bg-slate-700 text-slate-500' : '',
                        ]"
                      >
                        <span v-if="milestone.status === 'COMPLETED'" class="material-symbols-outlined text-xl font-bold">check</span>
                        <span v-else-if="milestone.status === 'IN_PROGRESS'" class="material-symbols-outlined text-xl font-bold">construction</span>
                        <span v-else class="material-symbols-outlined text-xl">pending</span>
                      </div>
                      <div
                        :class="[
                          'flex-1',
                          milestone.status === 'IN_PROGRESS' ? 'bg-amber/[0.03] p-5 rounded-xl border border-amber/10 -mt-2' : '',
                        ]"
                      >
                        <div class="flex justify-between items-center mb-1">
                          <h3
                            :class="[
                              'text-lg font-bold',
                              milestone.status === 'COMPLETED' ? 'text-slate-400' : '',
                              milestone.status === 'IN_PROGRESS' ? 'text-amber' : '',
                              milestone.status === 'PENDING' ? 'text-slate-500' : '',
                            ]"
                          >
                            {{ milestone.title }}
                          </h3>
                          <span
                            :class="[
                              'text-[10px] font-black px-2 py-0.5 rounded uppercase border',
                              milestone.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' : '',
                              milestone.status === 'IN_PROGRESS' ? 'bg-amber/10 text-amber border-amber/20' : '',
                              milestone.status === 'PENDING' ? 'text-slate-600 border-slate-800' : '',
                            ]"
                          >
                            {{ milestone.status === 'COMPLETED' ? 'Paid' : milestone.status === 'IN_PROGRESS' ? 'Active' : 'Pending' }}
                          </span>
                        </div>
                        <p
                          :class="[
                            'text-sm leading-relaxed',
                            milestone.status === 'COMPLETED' ? 'text-slate-500' : '',
                            milestone.status === 'IN_PROGRESS' ? 'text-slate-300 mb-4' : '',
                            milestone.status === 'PENDING' ? 'text-slate-600' : '',
                          ]"
                        >
                          {{ milestone.description || 'No description provided' }}
                        </p>
                        <div v-if="milestone.status === 'IN_PROGRESS'" class="flex items-center gap-4">
                          <div class="flex items-center gap-1.5 text-slate-400 text-xs font-medium">
                            <span class="material-symbols-outlined text-base">calendar_month</span>
                            <span>Due {{ formatDate(milestone.completed_at || '') }}</span>
                          </div>
                          <div class="h-1 flex-1 bg-slate-800 rounded-full overflow-hidden">
                            <div class="h-full bg-amber w-[75%] rounded-full"></div>
                          </div>
                          <span class="text-xs font-bold text-amber">75%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card class="bg-midnight rounded-2xl border border-white/5 shadow-xl overflow-hidden">
                <div class="px-8 py-6 border-b border-white/5 bg-white/[0.01]">
                  <h2 class="text-white text-lg font-bold">Contract Terms & Details</h2>
                </div>
                <CardContent class="p-8">
                  <div class="grid grid-cols-2 md:grid-cols-3 gap-y-8 gap-x-12">
                    <div>
                      <p class="text-slate-500 text-[10px] font-black uppercase tracking-widest mb-1">Total Budget</p>
                      <p class="text-white text-lg font-extrabold">${{ contract.total_amount.toLocaleString() }}</p>
                    </div>
                    <div>
                      <p class="text-slate-500 text-[10px] font-black uppercase tracking-widest mb-1">Escrow Status</p>
                      <div class="flex items-center gap-2 text-emerald-400">
                        <span class="material-symbols-outlined text-lg">verified_user</span>
                        <p class="text-sm font-bold">Fully Funded</p>
                      </div>
                    </div>
                    <div>
                      <p class="text-slate-500 text-[10px] font-black uppercase tracking-widest mb-1">Warranty</p>
                      <p class="text-white text-sm font-bold">12-Month Labor</p>
                    </div>
                    <div>
                      <p class="text-slate-500 text-[10px] font-black uppercase tracking-widest mb-1">Status</p>
                      <p class="text-white text-sm font-bold">{{ contract.status }}</p>
                    </div>
                    <div>
                      <p class="text-slate-500 text-[10px] font-black uppercase tracking-widest mb-1">Commenced</p>
                      <p class="text-white text-sm font-bold">{{ formatDate(contract.start_date || contract.created_at) }}</p>
                    </div>
                    <div>
                      <p class="text-slate-500 text-[10px] font-black uppercase tracking-widest mb-1">Standard</p>
                      <p class="text-white text-sm font-bold">Premium Tier</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
            <div class="lg:col-span-5 flex flex-col gap-6 sticky top-28">
              <Card v-if="nextMilestone" class="bg-midnight rounded-3xl border border-white/10 shadow-[0_30px_60px_-12px_rgba(0,0,0,0.5)] overflow-hidden">
                <div class="bg-gradient-to-br from-midnight-light to-midnight px-8 py-8 border-b border-white/5">
                  <div class="flex justify-between items-start mb-4">
                    <div>
                      <p class="text-amber text-xs font-black uppercase tracking-widest mb-1">Next Disbursement</p>
                      <h3 class="text-white text-2xl font-black">Milestone {{ nextMilestone.order }} Payment</h3>
                    </div>
                    <div class="p-2 bg-amber/10 rounded-xl text-amber">
                      <span class="material-symbols-outlined text-2xl">account_balance_wallet</span>
                    </div>
                  </div>
                  <div class="flex items-center gap-2 text-slate-400 text-sm">
                    <span class="material-symbols-outlined text-base">layers</span>
                    {{ nextMilestone.title }}
                  </div>
                </div>
                <CardContent class="p-8 flex flex-col gap-8">
                  <div class="space-y-4">
                    <div class="flex justify-between text-sm">
                      <span class="text-slate-400">Labor & Service Fee</span>
                      <span class="text-white font-bold">${{ (nextMilestone.amount * 0.85).toFixed(2) }}</span>
                    </div>
                    <div class="flex justify-between text-sm">
                      <span class="text-slate-400">Material Costs</span>
                      <span class="text-white font-bold">${{ (nextMilestone.amount * 0.10).toFixed(2) }}</span>
                    </div>
                    <div class="flex justify-between text-sm">
                      <div class="flex items-center gap-1.5">
                        <span class="text-slate-400">Platform Service Fee</span>
                        <span class="material-symbols-outlined text-sm text-slate-500 cursor-help">info</span>
                      </div>
                      <span class="text-slate-400 font-bold">${{ (nextMilestone.amount * 0.05).toFixed(2) }}</span>
                    </div>
                    <div class="pt-4 mt-4 border-t border-white/5 flex justify-between items-end">
                      <div>
                        <p class="text-slate-500 text-[10px] font-black uppercase tracking-widest">Amount to Pay</p>
                        <p class="text-white text-3xl font-black tracking-tight">${{ nextMilestone.amount.toLocaleString() }}</p>
                      </div>
                      <div class="text-right">
                        <p class="text-emerald-500 text-[10px] font-black uppercase tracking-widest mb-1">Includes Tax</p>
                        <p class="text-slate-500 text-xs">USD</p>
                      </div>
                    </div>
                  </div>
                  <div class="bg-white/5 p-4 rounded-xl border border-white/5 flex gap-3">
                    <span class="material-symbols-outlined text-amber">shield_with_heart</span>
                    <p class="text-slate-400 text-[11px] leading-relaxed">
                      SkillSpot Escrow Protection active. Funds are held securely and only released when you approve the work for this milestone.
                    </p>
                  </div>
                  <div class="flex flex-col gap-4">
                    <router-link :to="`/payments/contract/${contract.id}/milestone/${nextMilestone.id}`">
                      <Button variant="default" size="lg" class="w-full h-14 bg-[#635bff] hover:bg-[#7a73ff] text-white font-bold shadow-xl">
                        <svg class="w-5 h-5 mr-2" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
                          <path d="M34.722 17.58c0-5.321-2.731-8.527-7.462-8.527-4.325 0-7.23 2.152-7.23 2.152l-1.043-1.637s-3.52-1.39-5.118-1.39C9.366 8.178 6 12.33 6 18.064c0 6.641 3.966 9.423 9.471 9.423 4.14 0 7.848-1.956 7.848-1.956s.904 1.34 1.151 1.696c2.091 0 4.398-.946 5.378-1.425.074.053 4.874-2.723 4.874-8.222zm-12.793 4.321s-2.316 1.096-4.996 1.096c-3.141 0-5.397-1.425-5.397-5.027 0-3.615 2.126-5.467 5.174-5.467 2.478 0 4.35 1.069 4.35 1.069l.869 8.329zm9.052-1.503c-.63 0-1.873.315-1.873.315l-.801-7.794s1.171-.462 2.373-.462c2.441 0 3.864 1.487 3.864 4.09 0 2.502-1.353 3.851-3.563 3.851z" fill="currentColor"></path>
                        </svg>
                        Pay with Stripe
                      </Button>
                    </router-link>
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
              <Card class="bg-midnight rounded-2xl border border-white/5 p-6 flex flex-col gap-4">
                <h3 class="text-white text-xs font-black uppercase tracking-widest opacity-50">Transaction History</h3>
                <div class="space-y-4">
                  <div
                    v-for="payment in payments"
                    :key="payment.id"
                    class="flex gap-4"
                  >
                    <div class="size-1.5 rounded-full bg-emerald-500 mt-1.5 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                    <div class="flex-1">
                      <p class="text-slate-200 text-xs font-bold leading-none mb-1">{{ payment.status === 'completed' ? 'Funds Released' : 'Payment Pending' }}</p>
                      <p class="text-slate-500 text-[10px]">{{ formatDate(payment.created_at) }}</p>
                    </div>
                    <span class="text-slate-400 text-xs font-bold">${{ payment.amount.toLocaleString() }}</span>
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
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useMessagingStore } from '@/stores/messaging'
import { contractsService, type Contract, type ContractMilestone } from '@/services/contracts'
import { paymentsService, type Payment } from '@/services/payments'
import Header from '@/components/Header.vue'
import Card from '@/components/ui/Card.vue'
import CardContent from '@/components/ui/CardContent.vue'
import Button from '@/components/ui/Button.vue'
import { toast } from 'vue-sonner'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const messagingStore = useMessagingStore()
const contract = ref<Contract | null>(null)
const milestones = ref<ContractMilestone[]>([])
const payments = ref<Payment[]>([])
const loading = ref(false)
const contactLoading = ref(false)
const signLoading = ref(false)

const sortedMilestones = computed(() => {
  return [...milestones.value].sort((a, b) => a.order - b.order)
})

const activePhase = computed(() => {
  const active = milestones.value.find(m => m.status === 'IN_PROGRESS')
  return active?.order || 1
})

const nextMilestone = computed(() => {
  return sortedMilestones.value.find(m => m.status === 'IN_PROGRESS' || m.status === 'PENDING')
})

const contractTitle = computed(() => {
  if (contract.value?.job && typeof contract.value.job === 'object') {
    return (contract.value.job as { title?: string }).title || 'Contract Details'
  }
  return 'Contract Details'
})

const canSign = computed(() => {
  const c = contract.value
  if (!c || !authStore.user) return false
  if (!['DRAFT', 'PENDING_SIGNATURES'].includes(c.status)) return false
  const mySignature = c.signatures?.find((s: { signer: string }) => s.signer === authStore.user?.id)
  return mySignature && !mySignature.is_signed
})

async function openConversation() {
  const c = contract.value
  if (!c || !authStore.user) return
  const otherId = authStore.user.id === c.client ? c.provider : c.client
  contactLoading.value = true
  try {
    const conv = await messagingStore.createConversation({
      participant2_id: otherId,
      job_id: typeof c.job === 'string' ? c.job : undefined,
      initial_message: '',
    })
    if (conv?.id && conv.id !== 'undefined') {
      router.push(`/messages/${conv.id}`)
    } else {
      console.log('Conversation created but could not open it.', conv)
      toast.error('Conversation created but could not open it.')
    }
  } catch (err: any) {
    const msg = err.response?.data?.detail ?? 'Failed to open conversation'
    toast.error(msg)
  } finally {
    contactLoading.value = false
  }
}

async function handleSign() {
  const c = contract.value
  if (!c?.id || !authStore.user) return
  signLoading.value = true
  try {
    const name = authStore.user.email ?? 'User'
    await contractsService.sign(c.id, {
      signature_data: `Signed by ${name} at ${new Date().toISOString()}`,
      signature_type: 'TEXT',
    })
    toast.success('Contract signed.')
    const res = await contractsService.get(c.id)
    contract.value = res.data
  } catch (err: any) {
    const msg = err.response?.data?.detail ?? err.response?.data?.signature_data?.[0] ?? 'Failed to sign contract'
    toast.error(msg)
  } finally {
    signLoading.value = false
  }
}

function formatDate(dateString: string) {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

async function loadContract() {
  loading.value = true
  const contractId = route.params.id as string
  try {
    const [contractResponse, milestonesResponse, paymentsResponse] = await Promise.all([
      contractsService.get(contractId),
      contractsService.getMilestones(contractId),
      paymentsService.list(),
    ])
    contract.value = contractResponse.data
    milestones.value = milestonesResponse.data
    payments.value = paymentsResponse.data.filter((p: Payment) => p.contract === contractId)
  } catch (err) {
    console.error('Failed to fetch contract data:', err)
  } finally {
    loading.value = false
  }
}

onMounted(loadContract)
</script>

<style scoped>
.milestone-gradient-active {
  background: linear-gradient(180deg, #F59E0B 0%, #D97706 100%);
}
</style>
