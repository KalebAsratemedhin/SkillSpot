<template>
  <div class="min-h-screen bg-[#020617]">
    <Header />
    <main class="flex-1 flex flex-col items-center">
      <div class="w-full max-w-[1280px] px-8 py-10 flex flex-col gap-10">
        <div v-if="loading" class="flex justify-center py-12">
          <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
        </div>
        <div v-else-if="!contract" class="text-center py-16">
          <p class="text-slate-500 mb-4">Contract not found or you don't have access.</p>
          <Button variant="default" @click="router.push('/contracts')">Back to Contracts</Button>
        </div>
        <div v-else class="space-y-10">
          <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div class="flex flex-col gap-4">
              <div class="flex items-center gap-3">
                <span
                  :class="[
                    'text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest border',
                    contract.status === 'ACTIVE' ? 'bg-amber/10 text-amber border-amber/20' : '',
                    contract.status === 'TERMINATED' || contract.status === 'COMPLETED' ? 'bg-slate-600 text-slate-300 border-slate-500/30' : '',
                    contract.status === 'DRAFT' || contract.status === 'PENDING_SIGNATURES' ? 'bg-slate-600 text-slate-400 border-slate-500/30' : '',
                  ]"
                >
                  {{ contract.status === 'ACTIVE' ? 'Active Contract' : contract.status === 'TERMINATED' ? 'Ended' : contract.status === 'COMPLETED' ? 'Completed' : contract.status.replace(/_/g, ' ') }}
                </span>
                <p class="text-slate-500 text-sm font-mono tracking-tighter">#SS-{{ contract.id.slice(0, 8).toUpperCase() }}</p>
              </div>
              <h1 class="text-white text-5xl font-extrabold tracking-tight leading-none">{{ contractTitle }}</h1>
            </div>
            <div class="flex gap-4 flex-wrap">
              <router-link
                v-if="isClient && canPayContract && isFixedPrice && !fixedPricePaid"
                :to="`/payments/contract/${contract.id}`"
              >
                <Button variant="default" size="default" class="bg-[#635bff] hover:bg-[#7a73ff] text-white shadow-lg">
                  <span class="material-symbols-outlined mr-2 text-lg">payments</span>
                  Pay full amount
                </Button>
              </router-link>
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
              <Button
                v-if="canCloseContract"
                variant="default"
                size="default"
                class="bg-amber text-midnight hover:bg-amber-dark shadow-lg"
                :disabled="closeContractLoading"
                @click="showCloseContractConfirm = true"
              >
                <span v-if="closeContractLoading" class="material-symbols-outlined mr-2 text-lg animate-spin">refresh</span>
                <span v-else class="material-symbols-outlined mr-2 text-lg">check_circle</span>
                Close contract
              </Button>
              <Button
                v-if="canEndContract"
                variant="outline"
                size="default"
                class="border-amber/50 text-amber hover:bg-amber/10"
                :disabled="endContractLoading"
                @click="showEndContractConfirm = true"
              >
                <span v-if="endContractLoading" class="material-symbols-outlined mr-2 text-lg animate-spin">refresh</span>
                <span v-else class="material-symbols-outlined mr-2 text-lg">flag</span>
                End contract (terminate)
              </Button>
              <Button
                v-if="canDelete"
                variant="outline"
                size="default"
                class="border-red-500/50 text-red-400 hover:bg-red-500/10 hover:text-red-300"
                @click="showDeleteConfirm = true"
              >
                <span class="material-symbols-outlined mr-2 text-lg">delete</span>
                Delete Contract
              </Button>
            </div>
          </div>
          <Dialog v-model:open="showCloseContractConfirm">
            <DialogContent class="sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle>Close contract</DialogTitle>
                <DialogDescription>
                  Mark this contract as complete? You'll be asked to leave a review for the provider. This action cannot be undone.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <DialogClose as-child>
                  <Button type="button" variant="outline">Cancel</Button>
                </DialogClose>
                <Button
                  type="button"
                  variant="default"
                  class="bg-amber text-midnight hover:bg-amber/90"
                  :loading="closeContractLoading"
                  @click="confirmCloseContract"
                >
                  Close contract
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          <Dialog v-model:open="showEndContractConfirm">
            <DialogContent class="sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle>End contract</DialogTitle>
                <DialogDescription>
                  Terminate this contract? No further work will be required. This action cannot be undone.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <DialogClose as-child>
                  <Button type="button" variant="outline">Cancel</Button>
                </DialogClose>
                <Button
                  type="button"
                  variant="default"
                  class="bg-amber text-midnight hover:bg-amber/90"
                  :loading="endContractLoading"
                  @click="confirmEndContract"
                >
                  End contract
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          <!-- Review prompt when contract is completed -->
          <Card
            v-if="(showReviewForClient || showReviewForProvider) && !showReviewModal"
            class="bg-amber/10 border-amber/30"
          >
            <CardContent class="p-6">
              <h3 class="text-lg font-bold text-white mb-2">
                {{ showReviewForClient ? 'Rate the provider' : 'Rate the client' }}
              </h3>
              <p class="text-slate-400 text-sm mb-4">
                {{ showReviewForClient ? 'How was your experience working with the provider?' : 'How was your experience working with the client?' }}
              </p>
              <Button variant="default" class="bg-amber text-midnight" @click="openReviewModal">
                <span class="material-symbols-outlined mr-2">star</span>
                Leave a review
              </Button>
            </CardContent>
          </Card>
          <Dialog v-model:open="showReviewModal" @update:open="(v: boolean) => !v && resetReviewForm()">
            <DialogContent class="sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle>{{ reviewModalTitle }}</DialogTitle>
                <DialogDescription>{{ reviewModalDescription }}</DialogDescription>
              </DialogHeader>
              <form class="space-y-4" @submit.prevent="submitReview">
                <div>
                  <p class="text-slate-300 text-sm mb-2">Rating (1–5 stars)</p>
                  <div class="flex gap-1">
                    <button
                      v-for="i in 5"
                      :key="i"
                      type="button"
                      class="p-2 rounded-lg transition-colors"
                      :class="reviewForm.score >= i ? 'text-amber bg-amber/20' : 'text-slate-500 hover:text-slate-300'"
                      @click="reviewForm.score = i"
                    >
                      <span class="material-symbols-outlined filled text-2xl">star</span>
                    </button>
                  </div>
                </div>
                <div>
                  <label class="text-slate-300 text-sm block mb-2">Comment (optional)</label>
                  <textarea
                    v-model="reviewForm.comment"
                    class="w-full rounded-xl border border-white/10 bg-white/5 text-white p-3 min-h-[80px] text-sm focus:ring-2 focus:ring-amber/40"
                    placeholder="Share your experience..."
                  />
                </div>
                <DialogFooter>
                  <DialogClose as-child>
                    <Button type="button" variant="outline">Cancel</Button>
                  </DialogClose>
                  <Button type="submit" class="bg-amber text-midnight" :loading="reviewSubmitting">
                    Submit review
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
          <Dialog v-model:open="showDeleteConfirm">
            <DialogContent class="sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle>Delete contract</DialogTitle>
                <DialogDescription>
                  Are you sure you want to delete this contract? This action cannot be undone.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <DialogClose as-child>
                  <Button type="button" variant="outline">Cancel</Button>
                </DialogClose>
                <Button
                  type="button"
                  variant="default"
                  class="bg-red-600 hover:bg-red-700 text-white"
                  :loading="deleteLoading"
                  @click="confirmDelete"
                >
                  Delete
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          <Dialog v-model:open="showAddTimeEntry">
            <DialogContent class="sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle>Log hours</DialogTitle>
                <DialogDescription>
                  Enter the date and hours worked for this contract.
                </DialogDescription>
              </DialogHeader>
              <div class="grid gap-4 py-4">
                <div class="grid gap-2">
                  <label class="text-sm font-medium text-slate-200">Date</label>
                  <input
                    v-model="newTimeEntry.date"
                    type="date"
                    :min="timeEntryMinDate"
                    class="w-full px-3 py-2 rounded-lg bg-midnight border border-white/10 text-white [color-scheme:dark]"
                  />
                </div>
                <div class="grid gap-2">
                  <label class="text-sm font-medium text-slate-200">Hours</label>
                  <input
                    v-model.number="newTimeEntry.hours"
                    type="number"
                    step="0.25"
                    min="0.25"
                    class="w-full px-3 py-2 rounded-lg bg-midnight border border-white/10 text-white"
                  />
                </div>
                <div class="grid gap-2">
                  <label class="text-sm font-medium text-slate-200">Description (optional)</label>
                  <textarea
                    v-model="newTimeEntry.description"
                    rows="2"
                    class="w-full px-3 py-2 rounded-lg bg-midnight border border-white/10 text-white"
                    placeholder="What did you work on?"
                  />
                </div>
              </div>
              <DialogFooter>
                <DialogClose as-child>
                  <Button type="button" variant="outline">Cancel</Button>
                </DialogClose>
                <Button
                  type="button"
                  variant="default"
                  :loading="addTimeEntryLoading"
                  @click="submitTimeEntry"
                >
                  Log hours
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          <div class="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
            <div class="lg:col-span-7 flex flex-col gap-10">
              <Card class="bg-midnight rounded-2xl border border-white/5 shadow-2xl overflow-hidden">
                <div class="px-8 py-6 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
                  <h2 class="text-white text-lg font-bold flex items-center gap-2">
                    <span class="material-symbols-outlined text-amber">{{ isHourly ? 'schedule' : 'payments' }}</span>
                    {{ isHourly ? 'Time entries' : 'Fixed price' }}
                  </h2>
                </div>
                <CardContent class="p-8">
                  <template v-if="isHourly">
                    <div class="space-y-4">
                      <p v-if="timeEntries.length === 0" class="text-slate-500 text-sm">No time entries yet. Provider logs hours here.</p>
                      <div
                        v-for="entry in timeEntries"
                        :key="entry.id"
                        class="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl border border-white/5 bg-white/[0.02]"
                      >
                        <div>
                          <p class="text-white font-bold">{{ formatDate(entry.date) }} – {{ entry.hours }}h</p>
                          <p v-if="entry.description" class="text-slate-400 text-sm mt-1">{{ entry.description }}</p>
                          <span
                            :class="[
                              'inline-block mt-2 text-[10px] font-black px-2 py-0.5 rounded uppercase border',
                              entry.status === 'PAID' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' : '',
                              entry.status === 'APPROVED' ? 'bg-amber/10 text-amber border-amber/20' : '',
                              entry.status === 'PENDING_APPROVAL' ? 'bg-slate-600 border-slate-800 text-slate-400' : '',
                              entry.status === 'REJECTED' ? 'bg-red-500/10 text-red-400 border-red-500/20' : '',
                            ]"
                          >
                            {{ entry.status === 'PAID' ? 'Paid' : entry.status === 'APPROVED' ? 'Approved' : entry.status === 'PENDING_APPROVAL' ? 'Pending approval' : 'Rejected' }}
                          </span>
                        </div>
                        <div class="flex items-center gap-2">
                          <span v-if="entry.amount != null" class="text-white font-bold">Br {{ Number(entry.amount).toLocaleString() }}</span>
                          <template v-if="isClient && entry.status === 'PENDING_APPROVAL'">
                            <Button variant="outline" size="sm" class="border-emerald-500/50 text-emerald-400" @click="approveTimeEntry(entry.id)">Approve</Button>
                            <Button variant="outline" size="sm" class="border-red-500/50 text-red-400" @click="rejectTimeEntry(entry.id)">Reject</Button>
                          </template>
                        </div>
                      </div>
                      <div v-if="isClient && canPayContract && approvedUnpaidTimeEntries.length > 0" class="pt-4 border-t border-white/5 flex flex-wrap items-center justify-between gap-4">
                        <p class="text-slate-400 text-sm">
                          {{ approvedUnpaidTimeEntries.length }} approved entr{{ approvedUnpaidTimeEntries.length === 1 ? 'y' : 'ies' }} · Total Br {{ totalUnpaidAmount.toLocaleString() }}
                        </p>
                        <Button
                          variant="default"
                          size="default"
                          class="bg-[#635bff] hover:bg-[#7a73ff] text-white"
                          :loading="payTimeEntriesLoading"
                          @click="payAllTimeEntries"
                        >
                          <span class="material-symbols-outlined mr-2">payments</span>
                          Pay Br {{ totalUnpaidAmount.toLocaleString() }}
                        </Button>
                      </div>
                      <div v-if="isProvider && contract.payment_schedule === 'HOURLY'" class="pt-4 border-t border-white/5">
                        <Button variant="outline" size="default" class="border-amber/50 text-amber" @click="showAddTimeEntry = true">
                          <span class="material-symbols-outlined mr-2">add</span>
                          Log hours
                        </Button>
                      </div>
                    </div>
                  </template>
                  <template v-else>
                    <p class="text-slate-400 text-sm">Single payment of Br {{ contract.total_amount.toLocaleString() }} when work is complete.</p>
                    <p v-if="isClient && canPayContract && !fixedPricePaid" class="text-amber text-sm mt-2">Use the &quot;Pay full amount&quot; button above to pay.</p>
                  </template>
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
                      <p class="text-white text-lg font-extrabold">Br {{ contract.total_amount.toLocaleString() }}</p>
                    </div>
                    <div>
                      <p class="text-slate-500 text-[10px] font-black uppercase tracking-widest mb-1">Escrow Status</p>
                      <div class="flex items-center gap-2 text-emerald-400">
                        <span class="material-symbols-outlined text-lg">verified_user</span>
                        <p class="text-sm font-bold">Fully Funded</p>
                      </div>
                    </div>
                    <div>
                      <p class="text-slate-500 text-[10px] font-black uppercase tracking-widest mb-1">Status</p>
                      <p class="text-white text-sm font-bold">{{ contract.status }}</p>
                    </div>
                    <div>
                      <p class="text-slate-500 text-[10px] font-black uppercase tracking-widest mb-1">Commenced</p>
                      <p class="text-white text-sm font-bold">{{ formatDate(contract.start_date || contract.created_at) }}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
            <div class="lg:col-span-5 flex flex-col gap-6 sticky top-28">
              <Card v-if="isClient && canPayContract && isFixedPrice && !fixedPricePaid" class="bg-midnight rounded-3xl border border-white/10 shadow-[0_30px_60px_-12px_rgba(0,0,0,0.5)] overflow-hidden">
                <div class="bg-gradient-to-br from-midnight-light to-midnight px-8 py-8 border-b border-white/5">
                  <div class="flex justify-between items-start mb-4">
                    <div>
                      <p class="text-amber text-xs font-black uppercase tracking-widest mb-1">Payment</p>
                      <h3 class="text-white text-2xl font-black">Full amount</h3>
                    </div>
                    <div class="p-2 bg-amber/10 rounded-xl text-amber">
                      <span class="material-symbols-outlined text-2xl">account_balance_wallet</span>
                    </div>
                  </div>
                  <div class="flex items-center gap-2 text-slate-400 text-sm">
                    <span class="material-symbols-outlined text-base">payments</span>
                    Fixed price – pay once when work is complete
                  </div>
                </div>
                <CardContent class="p-8 flex flex-col gap-8">
                  <div class="pt-4 border-t border-white/5 flex justify-between items-end">
                    <div>
                      <p class="text-slate-500 text-[10px] font-black uppercase tracking-widest">Amount to Pay</p>
                      <p class="text-white text-3xl font-black tracking-tight">Br {{ contract.total_amount.toLocaleString() }}</p>
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
                    <router-link :to="`/payments/contract/${contract.id}`">
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
                      <p class="text-slate-200 text-xs font-bold leading-none mb-1">{{ (payment.status === 'COMPLETED' || payment.status === 'completed') ? 'Funds Released' : 'Payment Pending' }}</p>
                      <p class="text-slate-500 text-[10px]">{{ formatDate(payment.created_at) }}</p>
                    </div>
                    <span class="text-slate-400 text-xs font-bold">Br {{ payment.amount.toLocaleString() }}</span>
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
import { ref, computed, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useMessagingStore } from '@/stores/messaging'
import { contractsService, type Contract, type ContractMilestone, type TimeEntry } from '@/services/contracts'
import { paymentsService, type Payment } from '@/services/payments'
import { ratingsService, type Rating, type RatingType } from '@/services/ratings'
import Header from '@/components/Header.vue'
import Card from '@/components/ui/Card.vue'
import CardContent from '@/components/ui/CardContent.vue'
import Button from '@/components/ui/Button.vue'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogClose,
} from '@/components/ui/dialog'
import { toast } from 'vue-sonner'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const messagingStore = useMessagingStore()
const contract = ref<Contract | null>(null)
const milestones = ref<ContractMilestone[]>([])
const timeEntries = ref<TimeEntry[]>([])
const payments = ref<Payment[]>([])
const loading = ref(false)
const contactLoading = ref(false)
const signLoading = ref(false)
const deleteLoading = ref(false)
const endContractLoading = ref(false)
const closeContractLoading = ref(false)
const showCloseContractConfirm = ref(false)
const showDeleteConfirm = ref(false)
const showEndContractConfirm = ref(false)
const showAddTimeEntry = ref(false)
const contractRatings = ref<Rating[]>([])
const showReviewModal = ref(false)
const reviewForm = reactive({ score: 5, comment: '' })
const reviewSubmitting = ref(false)
const reviewTypeRef = ref<RatingType | null>(null)
const addTimeEntryLoading = ref(false)
const payTimeEntriesLoading = ref(false)
const newTimeEntry = reactive({ date: '', hours: 0, description: '' })

const approvedUnpaidTimeEntries = computed(() => {
  return timeEntries.value.filter(
    (e: TimeEntry) => e.status === 'APPROVED' && !timeEntryPaid(e.id)
  )
})
const totalUnpaidAmount = computed(() => {
  return approvedUnpaidTimeEntries.value.reduce(
    (sum: number, e: TimeEntry) => sum + Number(e.amount ?? 0),
    0
  )
})

const timeEntryMinDate = computed(() => {
  const d = new Date()
  return d.toISOString().slice(0, 10)
})

const isFixedPrice = computed(() => (contract.value?.payment_schedule ?? 'FIXED') === 'FIXED')
const isHourly = computed(() => contract.value?.payment_schedule === 'HOURLY')

const fixedPricePaid = computed(() => {
  const c = contract.value
  if (!c || c.payment_schedule !== 'FIXED') return false
  return payments.value.some(
    (p: Payment) => (p.status === 'COMPLETED' || p.status === 'completed')
  )
})

const isProvider = computed(() => {
  const c = contract.value
  if (!c || !authStore.user) return false
  const providerId = typeof c.provider === 'object' && c.provider !== null && 'id' in c.provider ? (c.provider as { id: string }).id : c.provider
  return providerId === authStore.user?.id
})

function timeEntryPaid(entryId: string): boolean {
  return payments.value.some(
    (p: Payment) => (p.time_entry === entryId || p.time_entry_id === entryId) && (p.status === 'COMPLETED' || p.status === 'completed')
  )
}

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

const canDelete = computed(() => {
  const c = contract.value
  if (!c || !authStore.user) return false
  if (c.client !== authStore.user.id) return false
  return ['DRAFT', 'CANCELLED'].includes(c.status)
})

const canCloseContract = computed(() => {
  const c = contract.value
  if (!c || !authStore.user) return false
  return isClient.value && c.status === 'ACTIVE'
})

const canEndContract = computed(() => {
  const c = contract.value
  if (!c || !authStore.user) return false
  const clientId = typeof c.client === 'object' && c.client !== null && 'id' in c.client ? (c.client as { id: string }).id : c.client
  const providerId = typeof c.provider === 'object' && c.provider !== null && 'id' in c.provider ? (c.provider as { id: string }).id : c.provider
  const isParty = authStore.user.id === clientId || authStore.user.id === providerId
  return isParty && c.status === 'ACTIVE'
})

const contractRatingsList = computed(() =>
  Array.isArray(contractRatings.value) ? contractRatings.value : []
)
const hasClientRatedProvider = computed(() =>
  contractRatingsList.value.some((r: Rating) => r.rating_type === 'CLIENT_TO_PROVIDER')
)
const hasProviderRatedClient = computed(() =>
  contractRatingsList.value.some((r: Rating) => r.rating_type === 'PROVIDER_TO_CLIENT')
)
const showReviewForClient = computed(() => {
  const c = contract.value
  if (!c || c.status !== 'COMPLETED' || !isClient.value) return false
  return !hasClientRatedProvider.value
})
const showReviewForProvider = computed(() => {
  const c = contract.value
  if (!c || c.status !== 'COMPLETED' || !isProvider.value) return false
  return !hasProviderRatedClient.value
})
const reviewModalTitle = computed(() =>
  showReviewForClient.value ? 'Rate the provider' : 'Rate the client'
)
const reviewModalDescription = computed(() =>
  showReviewForClient.value
    ? 'How was your experience working with the provider?'
    : 'How was your experience working with the client?'
)

const isClient = computed(() => {
  const c = contract.value
  if (!c || !authStore.user) return false
  const clientId = typeof c.client === 'object' && c.client !== null && 'id' in c.client ? (c.client as { id: string }).id : c.client
  return clientId === authStore.user?.id
})

/** Client can pay when contract is ACTIVE (backend only accepts payments for active contracts) */
const canPayContract = computed(() => {
  const c = contract.value
  if (!c || !isClient.value) return false
  return c.status === 'ACTIVE'
})

async function approveTimeEntry(entryId: string) {
  try {
    await contractsService.updateTimeEntry(entryId, { status: 'APPROVED' })
    toast.success('Time entry approved.')
    await loadContract()
  } catch (err: any) {
    toast.error(err.response?.data?.error ?? 'Failed to approve.')
  }
}

async function rejectTimeEntry(entryId: string) {
  try {
    await contractsService.updateTimeEntry(entryId, { status: 'REJECTED' })
    toast.success('Time entry rejected.')
    await loadContract()
  } catch (err: any) {
    toast.error(err.response?.data?.error ?? 'Failed to reject.')
  }
}

async function payAllTimeEntries() {
  const c = contract.value
  if (!c?.id || approvedUnpaidTimeEntries.value.length === 0) return
  if (totalUnpaidAmount.value < 25) {
    toast.error('Total payment must be at least 25 ETB. Please add more hours.')
    return
  }
  payTimeEntriesLoading.value = true
  try {
    const res = await paymentsService.createCheckoutSessionForTimeEntries({
      contract_id: c.id,
      success_url: `${window.location.origin}/contracts/${c.id}?payment=success`,
      cancel_url: `${window.location.origin}/contracts/${c.id}`,
    })
    const url = res.data?.url
    if (url) {
      toast.success('Redirecting to Stripe to complete payment.')
      window.location.href = url
    } else {
      toast.error('Could not start checkout.')
      payTimeEntriesLoading.value = false
    }
  } catch (err: any) {
    const msg = err.response?.data?.error ?? err.response?.data?.detail ?? 'Failed to start payment.'
    toast.error(msg)
  } finally {
    payTimeEntriesLoading.value = false
  }
}

async function submitTimeEntry() {
  const c = contract.value
  if (!c?.id || !newTimeEntry.date || !newTimeEntry.hours || newTimeEntry.hours <= 0) {
    toast.error('Enter a valid date and hours.')
    return
  }
  addTimeEntryLoading.value = true
  try {
    await contractsService.createTimeEntry(c.id, {
      date: newTimeEntry.date,
      hours: newTimeEntry.hours,
      description: newTimeEntry.description || undefined,
    })
    toast.success('Time entry added.')
    showAddTimeEntry.value = false
    newTimeEntry.date = ''
    newTimeEntry.hours = 0
    newTimeEntry.description = ''
    await loadContract()
  } catch (err: any) {
    toast.error(err.response?.data?.error ?? err.response?.data?.detail ?? 'Failed to add time entry.')
  } finally {
    addTimeEntryLoading.value = false
  }
}

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

async function confirmDelete() {
  const c = contract.value
  if (!c?.id || !canDelete.value) return
  deleteLoading.value = true
  try {
    await contractsService.delete(c.id)
    showDeleteConfirm.value = false
    toast.success('Contract deleted.')
    router.push('/contracts')
  } catch (err: any) {
    const msg = err.response?.data?.error ?? err.response?.data?.detail ?? 'Failed to delete contract'
    toast.error(msg)
  } finally {
    deleteLoading.value = false
  }
}

async function confirmCloseContract() {
  const c = contract.value
  if (!c?.id || !canCloseContract.value) return
  closeContractLoading.value = true
  try {
    await contractsService.update(c.id, { status: 'COMPLETED' })
    showCloseContractConfirm.value = false
    toast.success('Contract closed. Please leave a review for the provider.')
    await loadContract()
    reviewTypeRef.value = 'CLIENT_TO_PROVIDER'
    showReviewModal.value = true
  } catch (err: any) {
    const msg = err.response?.data?.status?.[0] ?? err.response?.data?.error ?? err.response?.data?.detail ?? 'Failed to close contract'
    toast.error(msg)
  } finally {
    closeContractLoading.value = false
  }
}

async function confirmEndContract() {
  const c = contract.value
  if (!c?.id || !canEndContract.value) return
  endContractLoading.value = true
  try {
    await contractsService.update(c.id, { status: 'TERMINATED' })
    showEndContractConfirm.value = false
    toast.success('Contract ended.')
    await loadContract()
  } catch (err: any) {
    const msg = err.response?.data?.status?.[0] ?? err.response?.data?.error ?? err.response?.data?.detail ?? 'Failed to end contract'
    toast.error(msg)
  } finally {
    endContractLoading.value = false
  }
}

async function loadContractRatings() {
  const c = contract.value
  if (!c?.id || c.status !== 'COMPLETED') return
  try {
    const res = await ratingsService.list({ contract: c.id })
    const data = res.data as { results?: Rating[] } | Rating[]
    contractRatings.value = Array.isArray(data) ? data : (data.results ?? [])
  } catch {
    contractRatings.value = []
  }
}

function openReviewModal() {
  reviewForm.score = 5
  reviewForm.comment = ''
  reviewTypeRef.value = showReviewForClient.value ? 'CLIENT_TO_PROVIDER' : 'PROVIDER_TO_CLIENT'
  showReviewModal.value = true
}

function resetReviewForm() {
  reviewForm.score = 5
  reviewForm.comment = ''
  reviewTypeRef.value = null
}

async function submitReview() {
  const c = contract.value
  const type = reviewTypeRef.value
  if (!c?.id || !type || reviewForm.score < 1 || reviewForm.score > 5) return
  reviewSubmitting.value = true
  try {
    await ratingsService.create({
      contract_id: c.id,
      rating_type: type,
      score: reviewForm.score,
      comment: reviewForm.comment.trim() || undefined,
    })
    toast.success('Review submitted.')
    showReviewModal.value = false
    resetReviewForm()
    await loadContractRatings()
  } catch (err: any) {
    const msg = err.response?.data?.detail ?? err.response?.data?.rating_type?.[0] ?? err.response?.data?.score?.[0] ?? 'Failed to submit review'
    toast.error(msg)
  } finally {
    reviewSubmitting.value = false
  }
}

function formatDate(dateString: string) {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function getContractIdFromRoute(): string | undefined {
  const p = route.params.id
  const id = Array.isArray(p) ? p[0] : p
  return typeof id === 'string' ? id : undefined
}

async function loadContract() {
  const contractId = getContractIdFromRoute()
  if (!contractId) return
  loading.value = true
  try {
    const [contractResponse, paymentsResponse] = await Promise.all([
      contractsService.get(contractId),
      paymentsService.list({ contract: contractId }),
    ])
    contract.value = contractResponse.data
    milestones.value = contractResponse.data.milestones ?? []
    timeEntries.value = contractResponse.data.time_entries ?? []
    const paymentsList = paymentsResponse.data.results || []
    payments.value = Array.isArray(paymentsList) ? paymentsList : []
    if (contractResponse.data.payment_schedule === 'HOURLY' && timeEntries.value.length === 0) {
      const teRes = await contractsService.getTimeEntries(contractId)
      timeEntries.value = teRes.data.results ?? []
    }
    if (contractResponse.data.status === 'COMPLETED') {
      await loadContractRatings()
    }
  } catch (err) {
    console.error('Failed to fetch contract data:', err)
  } finally {
    loading.value = false
  }
}

onMounted(loadContract)
watch(() => getContractIdFromRoute(), (id) => {
  if (id) loadContract()
})
</script>

<style scoped>
.milestone-gradient-active {
  background: linear-gradient(180deg, #F59E0B 0%, #D97706 100%);
}
</style>
