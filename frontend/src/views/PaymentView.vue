<template>
  <div class="min-h-screen bg-[#020617]">
    <Header />
    <main class="flex-1 flex flex-col items-center">
      <div class="w-full max-w-[1280px] px-8 py-10 flex flex-col gap-10">
        <div v-if="loading" class="flex justify-center py-12">
          <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
        </div>
        <div v-else-if="contract && milestone" class="space-y-10">
          <div class="flex flex-col gap-4">
            <div class="flex items-center gap-3">
              <span class="bg-amber/10 text-amber text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest border border-amber/20">Payment</span>
              <p class="text-slate-500 text-sm font-mono tracking-tighter">#SS-{{ contract.id.slice(0, 8).toUpperCase() }}</p>
            </div>
            <h1 class="text-white text-5xl font-extrabold tracking-tight leading-none">Milestone Payment</h1>
            <p class="text-slate-400">{{ milestone.title }}</p>
          </div>
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-10">
            <div class="lg:col-span-2">
              <Card class="bg-midnight rounded-3xl border border-white/10 shadow-[0_30px_60px_-12px_rgba(0,0,0,0.5)] overflow-hidden">
                <div class="bg-gradient-to-br from-midnight-light to-midnight px-8 py-8 border-b border-white/5">
                  <div class="flex justify-between items-start mb-4">
                    <div>
                      <p class="text-amber text-xs font-black uppercase tracking-widest mb-1">Payment Amount</p>
                      <h3 class="text-white text-2xl font-black">${{ milestone.amount.toLocaleString() }}</h3>
                    </div>
                    <div class="p-2 bg-amber/10 rounded-xl text-amber">
                      <span class="material-symbols-outlined text-2xl">account_balance_wallet</span>
                    </div>
                  </div>
                </div>
                <CardContent class="p-8 flex flex-col gap-8">
                  <div class="space-y-4">
                    <div class="flex justify-between text-sm">
                      <span class="text-slate-400">Labor & Service Fee</span>
                      <span class="text-white font-bold">${{ (milestone.amount * 0.85).toFixed(2) }}</span>
                    </div>
                    <div class="flex justify-between text-sm">
                      <span class="text-slate-400">Material Costs</span>
                      <span class="text-white font-bold">${{ (milestone.amount * 0.10).toFixed(2) }}</span>
                    </div>
                    <div class="flex justify-between text-sm">
                      <div class="flex items-center gap-1.5">
                        <span class="text-slate-400">Platform Service Fee</span>
                        <span class="material-symbols-outlined text-sm text-slate-500 cursor-help">info</span>
                      </div>
                      <span class="text-slate-400 font-bold">${{ (milestone.amount * 0.05).toFixed(2) }}</span>
                    </div>
                    <div class="pt-4 mt-4 border-t border-white/5 flex justify-between items-end">
                      <div>
                        <p class="text-slate-500 text-[10px] font-black uppercase tracking-widest">Amount to Pay</p>
                        <p class="text-white text-3xl font-black tracking-tight">${{ milestone.amount.toLocaleString() }}</p>
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
                  <div class="flex justify-between text-sm">
                    <span class="text-slate-400">Milestone</span>
                    <span class="text-white font-bold">{{ milestone.title }}</span>
                  </div>
                  <div class="flex justify-between text-sm">
                    <span class="text-slate-400">Status</span>
                    <span class="text-amber font-bold">{{ milestone.status }}</span>
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
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { contractsService, type Contract, type ContractMilestone } from '@/services/contracts'
import { paymentsService } from '@/services/payments'
import Header from '@/components/Header.vue'
import Card from '@/components/ui/Card.vue'
import CardContent from '@/components/ui/CardContent.vue'
import Button from '@/components/ui/Button.vue'

const route = useRoute()
const router = useRouter()
const contract = ref<Contract | null>(null)
const milestone = ref<ContractMilestone | null>(null)
const loading = ref(false)
const processing = ref(false)

async function handlePayment() {
  if (!contract.value || !milestone.value) return
  processing.value = true
  try {
    const response = await paymentsService.createPaymentIntent({
      amount: milestone.value.amount,
      contract_id: contract.value.id,
      milestone_id: milestone.value.id,
    })
    router.push(`/contracts/${contract.value.id}`)
  } catch (err) {
    console.error('Failed to create payment intent:', err)
  } finally {
    processing.value = false
  }
}

onMounted(async () => {
  loading.value = true
  const contractId = route.params.contractId as string
  const milestoneId = route.params.milestoneId as string
  try {
    const [contractResponse, milestonesResponse] = await Promise.all([
      contractsService.get(contractId),
      contractsService.getMilestones(contractId),
    ])
    contract.value = contractResponse.data
    milestone.value = milestonesResponse.data.find(m => m.id === milestoneId) || null
  } catch (err) {
    console.error('Failed to fetch payment data:', err)
  } finally {
    loading.value = false
  }
})
</script>
