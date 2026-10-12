<template>
  <AppLayout>
    <div class="max-w-6xl mx-auto px-6 lg:px-20 py-10">
      <h1 class="text-3xl font-bold text-midnight mb-8">Contracts</h1>
      <div v-if="loading && contracts.length === 0" class="rounded-2xl border border-slate-200 bg-white px-6">
        <SectionLoader :lines="6" />
      </div>
      <div v-else-if="!loading && contracts.length === 0" class="text-center py-12">
        <p class="text-slate-500">No contracts found</p>
      </div>
      <div
        v-else
        class="space-y-4 transition-opacity duration-150"
        :class="loading ? 'opacity-60 pointer-events-none' : 'opacity-100'"
      >
        <Card
          v-for="contract in contracts"
          :key="contract.id"
          class="bg-white rounded-xl shadow-sm border border-slate-200 hover:shadow-md hover:border-amber/30 transition-all cursor-pointer"
          @click="$router.push(`/contracts/${contract.id}`)"
        >
          <CardContent class="p-5 md:p-6">
            <div class="flex flex-col md:flex-row md:items-start justify-between gap-4">
              <div class="flex-1 min-w-0 space-y-2">
                <div class="flex items-center gap-2 flex-wrap">
                  <span
                    class="px-2.5 py-1 rounded-full text-xs font-black uppercase tracking-wider border"
                    :class="statusClass(contract.status)"
                  >
                    {{ formatStatus(contract.status) }}
                  </span>
                  <span class="text-slate-400 text-sm">{{ formatDate(contract.created_at) }}</span>
                </div>
                <h3 class="text-xl font-display font-bold text-midnight truncate">
                  {{ contractTitle(contract) }}
                </h3>
                <div class="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-600">
                  <span v-if="contractRate(contract)" class="inline-flex items-center gap-1 font-semibold text-midnight">
                    <span class="material-symbols-outlined text-amber text-base">payments</span>
                    {{ contractRate(contract) }}
                  </span>
                  <span v-if="counterpartyLabel(contract)" class="inline-flex items-center gap-1 truncate">
                    <span class="material-symbols-outlined text-slate-400 text-base">person</span>
                    {{ counterpartyLabel(contract) }}
                  </span>
                  <span
                    v-if="contract.payment_schedule"
                    class="inline-flex items-center gap-1 text-slate-500"
                  >
                    <span class="material-symbols-outlined text-slate-400 text-base">schedule</span>
                    {{ contract.payment_schedule === 'HOURLY' ? 'Hourly' : 'Fixed' }}
                  </span>
                </div>
              </div>
              <div class="flex md:flex-col items-center md:items-end gap-2 shrink-0">
                <Button
                  variant="outline"
                  size="default"
                  class="border-slate-200"
                  @click.stop="$router.push(`/contracts/${contract.id}`)"
                >
                  View contract
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
        <PaginationBar
          v-if="totalCount > 0"
          :current-page="currentPage"
          :total-pages="totalPages"
          :total-count="totalCount"
          :page-size="pageSize"
          :loading="loading"
          @go-to-page="goToPage"
          @update-page-size="onPageSizeChange"
        />
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { contractsService, type Contract } from '@/services/contracts'
import AppLayout from '@/components/AppLayout.vue'
import SectionLoader from '@/components/SectionLoader.vue'
import Card from '@/components/ui/Card.vue'
import CardContent from '@/components/ui/CardContent.vue'
import Button from '@/components/ui/Button.vue'
import PaginationBar from '@/components/PaginationBar.vue'

const authStore = useAuthStore()
const contracts = ref<Contract[]>([])
const totalCount = ref(0)
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)

const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize.value)))

function formatDate(dateString: string) {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function formatStatus(status: string) {
  return status.replace(/_/g, ' ')
}

function statusClass(status: string) {
  if (status === 'ACTIVE') return 'bg-emerald-500/10 text-emerald-700 border-emerald-500/20'
  if (status === 'COMPLETED') return 'bg-slate-100 text-slate-700 border-slate-200'
  if (status === 'TERMINATED' || status === 'CANCELLED') return 'bg-red-500/10 text-red-600 border-red-500/20'
  if (status === 'PENDING_SIGNATURES' || status === 'DRAFT') return 'bg-amber/10 text-amber border-amber/20'
  return 'bg-slate-100 text-slate-700 border-slate-200'
}

function contractTitle(contract: Contract) {
  return (
    contract.title?.trim() ||
    contract.job_title?.trim() ||
    `Contract #${contract.id.slice(0, 8)}`
  )
}

function contractRate(contract: Contract) {
  const money = (n: number) =>
    '$' + n.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
  if (contract.payment_schedule === 'HOURLY' && contract.hourly_rate != null) {
    return `${money(Number(contract.hourly_rate))}/hr`
  }
  if (contract.total_amount != null) {
    const suffix = contract.payment_schedule === 'HOURLY' ? ' cap' : ''
    return `${money(Number(contract.total_amount))}${suffix}`
  }
  return ''
}

function counterpartyLabel(contract: Contract) {
  const userId = authStore.user?.id
  if (userId && String(contract.client) === String(userId)) {
    const name = contract.provider_name || contract.provider_email
    return name ? `Provider · ${name}` : ''
  }
  if (userId && String(contract.provider) === String(userId)) {
    const name = contract.client_name || contract.client_email
    return name ? `Client · ${name}` : ''
  }
  if (authStore.isClient) {
    const name = contract.provider_name || contract.provider_email
    return name ? `Provider · ${name}` : ''
  }
  const name = contract.client_name || contract.client_email
  return name ? `Client · ${name}` : ''
}

async function fetchContracts() {
  loading.value = true
  try {
    const response = await contractsService.list({
      page: currentPage.value,
      page_size: pageSize.value,
    })
    contracts.value = response.data.results || []
    totalCount.value = response.data.count ?? 0
  } catch (err) {
    console.error('Failed to fetch contracts:', err)
    contracts.value = []
    totalCount.value = 0
  } finally {
    loading.value = false
  }
}

function goToPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  fetchContracts()
}

function onPageSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  fetchContracts()
}

onMounted(() => {
  fetchContracts()
})
</script>
