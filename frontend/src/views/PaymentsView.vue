<template>
  <AppLayout>
    <div class="w-full max-w-[1280px] mx-auto px-4 md:px-6 lg:px-10 py-6 md:py-10 flex flex-col gap-8 md:gap-10">
      <div class="flex flex-col gap-2">
        <span class="w-fit bg-amber/10 text-amber text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest border border-amber/20">
          {{ authStore.isProvider ? 'Earnings' : 'Payments' }}
        </span>
        <h1 class="text-2xl md:text-3xl font-bold text-midnight tracking-tight">
          {{ authStore.isProvider ? 'Payment History' : 'Payment Management' }}
        </h1>
        <p class="text-slate-500 text-sm md:text-base">
          {{ authStore.isProvider ? 'Track your earnings and completed milestones' : 'Manage payments and transaction history' }}
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
        <Card class="bg-gradient-to-br from-emerald-600 to-emerald-700 rounded-2xl border-0 shadow-lg shadow-emerald-900/20 p-6">
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

        <Card class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <div class="flex items-start justify-between">
            <div>
              <p class="text-slate-500 text-xs font-black uppercase tracking-widest mb-2">Completed</p>
              <h3 class="text-midnight text-3xl font-black">{{ completedCount }}</h3>
            </div>
            <div class="p-3 bg-emerald-500/10 rounded-xl">
              <span class="material-symbols-outlined text-2xl text-emerald-600">check_circle</span>
            </div>
          </div>
        </Card>

        <Card class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <div class="flex items-start justify-between">
            <div>
              <p class="text-slate-500 text-xs font-black uppercase tracking-widest mb-2">Pending</p>
              <h3 class="text-midnight text-3xl font-black">{{ pendingCount }}</h3>
            </div>
            <div class="p-3 bg-amber/10 rounded-xl">
              <span class="material-symbols-outlined text-2xl text-amber">schedule</span>
            </div>
          </div>
        </Card>
      </div>

      <div class="flex flex-wrap gap-3">
        <Button
          v-for="filter in statusFilters"
          :key="filter.value"
          :variant="selectedStatus === filter.value ? 'default' : 'outline'"
          size="sm"
          :class="filterButtonClass(filter.value)"
          @click="selectedStatus = filter.value"
        >
          <span class="material-symbols-outlined mr-2 text-base">{{ filter.icon }}</span>
          {{ filter.label }}
        </Button>
      </div>

      <div v-if="loading" class="flex justify-center py-12">
        <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
      </div>

      <div v-else-if="payments.length === 0" class="text-center py-16">
        <div class="inline-flex items-center justify-center size-20 rounded-full bg-slate-100 mb-4">
          <span class="material-symbols-outlined text-4xl text-slate-400">receipt_long</span>
        </div>
        <p class="text-slate-500 mb-2">No payments found</p>
        <p class="text-slate-400 text-sm">{{ selectedStatus === 'all' ? 'Payments will appear here once transactions are made' : `No ${selectedStatus} payments` }}</p>
      </div>

      <div v-else class="space-y-4">
        <Card
          v-for="payment in payments"
          :key="payment.id"
          class="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-all p-6"
        >
          <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div class="flex-1 space-y-4">
              <div class="flex items-center gap-3 flex-wrap">
                <span
                  :class="[
                    'px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider border',
                    payment.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-700 border-emerald-500/20' : '',
                    payment.status === 'PENDING' ? 'bg-amber/10 text-amber border-amber/20' : '',
                    payment.status === 'PROCESSING' ? 'bg-blue-500/10 text-blue-600 border-blue-500/20' : '',
                    payment.status === 'FAILED' ? 'bg-red-500/10 text-red-600 border-red-500/20' : '',
                    payment.status === 'REFUNDED' ? 'bg-purple-500/10 text-purple-600 border-purple-500/20' : '',
                  ]"
                >
                  {{ payment.status }}
                </span>
                <span class="text-slate-500 text-sm font-mono">{{ formatDate(payment.created_at) }}</span>
                <span class="text-slate-400 text-xs">ID: #{{ payment.id.slice(0, 8) }}</span>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <p class="text-slate-500 text-xs font-bold uppercase tracking-wider mb-1">Contract</p>
                  <p class="text-midnight text-sm font-mono">#{{ typeof payment.contract === 'string' ? payment.contract.slice(0, 8) : payment.contract?.id?.slice(0, 8) || 'N/A' }}</p>
                </div>
                <div>
                  <p class="text-slate-500 text-xs font-bold uppercase tracking-wider mb-1">Payment Method</p>
                  <div class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-base text-slate-400">credit_card</span>
                    <p class="text-midnight text-sm">{{ formatPaymentMethod(payment.payment_method) }}</p>
                  </div>
                </div>
                <div>
                  <p class="text-slate-500 text-xs font-bold uppercase tracking-wider mb-1">{{ authStore.isProvider ? 'Platform Fee' : 'Transaction' }}</p>
                  <p class="text-slate-600 text-sm">{{ payment.platform_fee ? `Br ${Number(payment.platform_fee).toLocaleString()}` : 'N/A' }}</p>
                </div>
              </div>

              <div v-if="payment.description" class="text-slate-600 text-sm">
                {{ payment.description }}
              </div>
            </div>

            <div class="flex items-center gap-4">
              <div class="text-right">
                <p class="text-slate-500 text-xs font-bold uppercase tracking-wider mb-1">Amount</p>
                <p class="text-midnight text-2xl font-black">${{ payment.amount.toLocaleString() }}</p>
                <p v-if="authStore.isProvider && payment.provider_amount" class="text-emerald-600 text-xs font-bold mt-1">
                  You received: Br {{ payment.provider_amount != null ? Number(payment.provider_amount).toLocaleString() : '0' }}
                </p>
              </div>
              <router-link
                v-if="typeof payment.contract === 'string'"
                :to="`/contracts/${payment.contract}`"
              >
                <Button variant="outline" size="sm" class="border-slate-200 text-slate-600 hover:text-midnight hover:border-slate-300">
                  <span class="material-symbols-outlined mr-2 text-base">visibility</span>
                  View
                </Button>
              </router-link>
            </div>
          </div>
        </Card>
      </div>

      <PaginationBar
        v-if="!loading && totalCount > 0"
        :current-page="currentPage"
        :total-pages="totalPages"
        :total-count="totalCount"
        :page-size="pageSize"
        :loading="loading"
        @go-to-page="onGoToPage"
        @update-page-size="onPageSizeChange"
      />
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { paymentsService, type Payment } from '@/services/payments'
import AppLayout from '@/components/AppLayout.vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import PaginationBar from '@/components/PaginationBar.vue'

const authStore = useAuthStore()
const payments = ref<Payment[]>([])
const totalCount = ref(0)
const loading = ref(false)
const selectedStatus = ref<string>('all')
const currentPage = ref(1)
const pageSize = ref(10)

function filterButtonClass(value: string): string {
  return selectedStatus.value === value
    ? 'bg-amber text-midnight hover:bg-amber-dark'
    : 'border-slate-200 text-slate-600 hover:text-midnight hover:border-slate-300 bg-white'
}

const statusFilters = [
  { value: 'all', label: 'All', icon: 'receipt_long' },
  { value: 'COMPLETED', label: 'Completed', icon: 'check_circle' },
  { value: 'PENDING', label: 'Pending', icon: 'schedule' },
  { value: 'PROCESSING', label: 'Processing', icon: 'sync' },
  { value: 'FAILED', label: 'Failed', icon: 'error' },
]

const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize.value)))

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

const completedCount = computed(() => payments.value.filter(p => p.status === 'COMPLETED').length)
const pendingCount = computed(() => payments.value.filter(p => p.status === 'PENDING' || p.status === 'PROCESSING').length)

function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatPaymentMethod(method: string) {
  const methods: Record<string, string> = {
    STRIPE: 'Stripe',
    BANK_TRANSFER: 'Bank Transfer',
    OTHER: 'Other',
  }
  return methods[method] || method
}

async function fetchPayments() {
  loading.value = true
  try {
    const params: Record<string, string | number> = { page: currentPage.value, page_size: pageSize.value }
    if (selectedStatus.value !== 'all') params.status = selectedStatus.value
    const response = await paymentsService.list(params)
    payments.value = response.data.results || []
    totalCount.value = response.data.count ?? 0
  } catch (err) {
    console.error('Failed to fetch payments:', err)
    payments.value = []
    totalCount.value = 0
  } finally {
    loading.value = false
  }
}

watch(selectedStatus, () => {
  currentPage.value = 1
  fetchPayments()
})

watch(currentPage, () => {
  fetchPayments()
}, { immediate: false })

function onGoToPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
}

function onPageSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  fetchPayments()
}

onMounted(async () => {
  await fetchPayments()
})
</script>
