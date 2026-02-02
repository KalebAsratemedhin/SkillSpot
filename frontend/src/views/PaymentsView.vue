<template>
  <div class="min-h-screen bg-[#020617]">
    <Header />
    <main class="flex-1 flex flex-col items-center">
      <div class="w-full max-w-[1280px] px-8 py-10 flex flex-col gap-10">
        <!-- Header -->
        <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div class="flex flex-col gap-4">
            <div class="flex items-center gap-3">
              <span class="bg-amber/10 text-amber text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest border border-amber/20">
                {{ authStore.isProvider ? 'Earnings' : 'Payments' }}
              </span>
            </div>
            <h1 class="text-white text-5xl font-extrabold tracking-tight leading-none">
              {{ authStore.isProvider ? 'Payment History' : 'Payment Management' }}
            </h1>
            <p class="text-slate-400 text-lg">
              {{ authStore.isProvider ? 'Track your earnings and completed milestones' : 'Manage payments and transaction history' }}
            </p>
          </div>
        </div>

        <!-- Stats Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card class="bg-gradient-to-br from-emerald-600 to-emerald-700 rounded-2xl border-0 shadow-2xl shadow-emerald-900/50 p-6">
            <div class="flex items-start justify-between">
              <div>
                <p class="text-emerald-100 text-xs font-black uppercase tracking-widest mb-2">Total {{ authStore.isProvider ? 'Earned' : 'Paid' }}</p>
                <h3 class="text-white text-3xl font-black">Br {{ totalAmount.toLocaleString() }}</h3>
              </div>
              <div class="p-3 bg-white/20 rounded-xl">
                <span class="material-symbols-outlined text-2xl text-white">{{ authStore.isProvider ? 'account_balance_wallet' : 'payment' }}</span>
              </div>
            </div>
          </Card>
          
          <Card class="bg-midnight rounded-2xl border border-white/5 p-6">
            <div class="flex items-start justify-between">
              <div>
                <p class="text-slate-400 text-xs font-black uppercase tracking-widest mb-2">Completed</p>
                <h3 class="text-white text-3xl font-black">{{ completedCount }}</h3>
              </div>
              <div class="p-3 bg-emerald-500/10 rounded-xl">
                <span class="material-symbols-outlined text-2xl text-emerald-500">check_circle</span>
              </div>
            </div>
          </Card>
          
          <Card class="bg-midnight rounded-2xl border border-white/5 p-6">
            <div class="flex items-start justify-between">
              <div>
                <p class="text-slate-400 text-xs font-black uppercase tracking-widest mb-2">Pending</p>
                <h3 class="text-white text-3xl font-black">{{ pendingCount }}</h3>
              </div>
              <div class="p-3 bg-amber/10 rounded-xl">
                <span class="material-symbols-outlined text-2xl text-amber">schedule</span>
              </div>
            </div>
          </Card>
        </div>

        <!-- Filters -->
        <div class="flex flex-wrap gap-3">
          <Button
            v-for="filter in statusFilters"
            :key="filter.value"
            :variant="selectedStatus === filter.value ? 'default' : 'outline'"
            size="sm"
            @click="selectedStatus = filter.value"
            :class="[
              selectedStatus === filter.value 
                ? 'bg-amber text-midnight hover:bg-amber-dark' 
                : 'border-white/10 text-slate-400 hover:text-white hover:border-white/20'
            ]"
          >
            <span class="material-symbols-outlined mr-2 text-base">{{ filter.icon }}</span>
            {{ filter.label }}
          </Button>
        </div>

        <!-- Payments List -->
        <div v-if="loading" class="flex justify-center py-12">
          <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
        </div>
        
        <div v-else-if="filteredPayments.length === 0" class="text-center py-16">
          <div class="inline-flex items-center justify-center size-20 rounded-full bg-white/5 mb-4">
            <span class="material-symbols-outlined text-4xl text-slate-500">receipt_long</span>
          </div>
          <p class="text-slate-500 mb-2">No payments found</p>
          <p class="text-slate-600 text-sm">{{ selectedStatus === 'all' ? 'Payments will appear here once transactions are made' : `No ${selectedStatus} payments` }}</p>
        </div>

        <div v-else class="space-y-4">
          <Card
            v-for="payment in filteredPayments"
            :key="payment.id"
            class="bg-midnight rounded-2xl border border-white/5 hover:border-white/10 transition-all p-6"
          >
            <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
              <div class="flex-1 space-y-4">
                <div class="flex items-center gap-3">
                  <span
                    :class="[
                      'px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider border',
                      payment.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' : '',
                      payment.status === 'PENDING' ? 'bg-amber/10 text-amber border-amber/20' : '',
                      payment.status === 'PROCESSING' ? 'bg-blue-500/10 text-blue-500 border-blue-500/20' : '',
                      payment.status === 'FAILED' ? 'bg-red-500/10 text-red-500 border-red-500/20' : '',
                      payment.status === 'REFUNDED' ? 'bg-purple-500/10 text-purple-500 border-purple-500/20' : '',
                    ]"
                  >
                    {{ payment.status }}
                  </span>
                  <span class="text-slate-500 text-sm font-mono">{{ formatDate(payment.created_at) }}</span>
                  <span class="text-slate-600 text-xs">ID: #{{ payment.id.slice(0, 8) }}</span>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <p class="text-slate-500 text-xs font-bold uppercase tracking-wider mb-1">Contract</p>
                    <p class="text-white text-sm font-mono">#{{ typeof payment.contract === 'string' ? payment.contract.slice(0, 8) : payment.contract?.id?.slice(0, 8) || 'N/A' }}</p>
                  </div>
                  <div>
                    <p class="text-slate-500 text-xs font-bold uppercase tracking-wider mb-1">Payment Method</p>
                    <div class="flex items-center gap-2">
                      <span class="material-symbols-outlined text-base text-slate-400">credit_card</span>
                      <p class="text-white text-sm">{{ formatPaymentMethod(payment.payment_method) }}</p>
                    </div>
                  </div>
                  <div>
                    <p class="text-slate-500 text-xs font-bold uppercase tracking-wider mb-1">{{ authStore.isProvider ? 'Platform Fee' : 'Transaction' }}</p>
                    <p class="text-slate-400 text-sm">{{ payment.platform_fee ? `Br ${Number(payment.platform_fee).toLocaleString()}` : 'N/A' }}</p>
                  </div>
                </div>

                <div v-if="payment.description" class="text-slate-400 text-sm">
                  {{ payment.description }}
                </div>
              </div>

              <div class="flex items-center gap-4">
                <div class="text-right">
                  <p class="text-slate-500 text-xs font-bold uppercase tracking-wider mb-1">Amount</p>
                  <p class="text-white text-2xl font-black">${{ payment.amount.toLocaleString() }}</p>
                  <p v-if="authStore.isProvider && payment.provider_amount" class="text-emerald-500 text-xs font-bold mt-1">
                    You received: Br {{ payment.provider_amount != null ? Number(payment.provider_amount).toLocaleString() : '0' }}
                  </p>
                </div>
                <router-link
                  v-if="typeof payment.contract === 'string'"
                  :to="`/contracts/${payment.contract}`"
                >
                  <Button variant="outline" size="sm" class="border-white/10 text-slate-400 hover:text-white hover:border-white/20">
                    <span class="material-symbols-outlined mr-2 text-base">visibility</span>
                    View
                  </Button>
                </router-link>
              </div>
            </div>
          </Card>
        </div>

        <!-- Pagination -->
        <div v-if="!loading && totalPages > 1" class="flex justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            @click="currentPage--"
            :disabled="currentPage === 1"
            class="border-white/10 text-slate-400 hover:text-white disabled:opacity-50"
          >
            <span class="material-symbols-outlined text-base">chevron_left</span>
          </Button>
          <div class="flex items-center gap-2 px-4">
            <span class="text-slate-400 text-sm">Page {{ currentPage }} of {{ totalPages }}</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            @click="currentPage++"
            :disabled="currentPage === totalPages"
            class="border-white/10 text-slate-400 hover:text-white disabled:opacity-50"
          >
            <span class="material-symbols-outlined text-base">chevron_right</span>
          </Button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { paymentsService, type Payment } from '@/services/payments'
import Header from '@/components/Header.vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'

const authStore = useAuthStore()
const payments = ref<Payment[]>([])
const loading = ref(false)
const selectedStatus = ref<string>('all')
const currentPage = ref(1)
const itemsPerPage = 10

const statusFilters = [
  { value: 'all', label: 'All', icon: 'receipt_long' },
  { value: 'COMPLETED', label: 'Completed', icon: 'check_circle' },
  { value: 'PENDING', label: 'Pending', icon: 'schedule' },
  { value: 'PROCESSING', label: 'Processing', icon: 'sync' },
  { value: 'FAILED', label: 'Failed', icon: 'error' },
]

const filteredPayments = computed(() => {
  let filtered = payments.value
  if (selectedStatus.value !== 'all') {
    filtered = filtered.filter(p => p.status === selectedStatus.value)
  }
  // Paginate
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return filtered.slice(start, end)
})

const totalPages = computed(() => {
  let filtered = payments.value
  if (selectedStatus.value !== 'all') {
    filtered = filtered.filter(p => p.status === selectedStatus.value)
  }
  return Math.ceil(filtered.length / itemsPerPage)
})

const totalAmount = computed(() => {
  return payments.value
    .filter(p => p.status === 'COMPLETED')
    .reduce((sum, p) => {
      if (authStore.isProvider && p.provider_amount) {
        return sum + Number(p.provider_amount)
      }
      return sum + Number(p.amount)
    }, 0)
})

const completedCount = computed(() => {
  return payments.value.filter(p => p.status === 'COMPLETED').length
})

const pendingCount = computed(() => {
  return payments.value.filter(p => p.status === 'PENDING' || p.status === 'PROCESSING').length
})

function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatPaymentMethod(method: string) {
  const methods: Record<string, string> = {
    'STRIPE': 'Stripe',
    'BANK_TRANSFER': 'Bank Transfer',
    'OTHER': 'Other'
  }
  return methods[method] || method
}

async function fetchPayments() {
  loading.value = true
  try {
    const response = await paymentsService.list()
    payments.value = response.data.results || []
  } catch (err) {
    console.error('Failed to fetch payments:', err)
    payments.value = []
  } finally {
    loading.value = false
  }
}

watch(selectedStatus, () => {
  currentPage.value = 1
})

onMounted(async () => {
  await fetchPayments()
})
</script>
