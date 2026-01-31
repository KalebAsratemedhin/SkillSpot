<template>
  <AppLayout>
    <div class="max-w-6xl mx-auto px-6 lg:px-20 py-10">
      <h1 class="text-3xl font-bold text-midnight mb-8">Contracts</h1>
      <div v-if="loading" class="flex justify-center py-12">
        <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
      </div>
      <div v-else-if="contracts.length === 0" class="text-center py-12">
        <p class="text-slate-500">No contracts found</p>
      </div>
      <div v-else class="space-y-4">
        <Card
          v-for="contract in contracts"
          :key="contract.id"
          class="bg-white rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow cursor-pointer"
          @click="$router.push(`/contracts/${contract.id}`)"
        >
          <CardContent class="p-6">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-lg font-bold text-midnight">Contract #{{ contract.id.slice(0, 8) }}</h3>
                <p class="text-sm text-slate-500 mt-1">Status: {{ contract.status }}</p>
              </div>
              <div class="text-right">
                <p class="text-lg font-bold text-midnight">${{ contract.total_amount }}</p>
                <p class="text-xs text-slate-500">{{ formatDate(contract.created_at) }}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { contractsService, type Contract } from '@/services/contracts'
import AppLayout from '@/components/AppLayout.vue'
import Card from '@/components/ui/Card.vue'
import CardContent from '@/components/ui/CardContent.vue'

const contracts = ref<Contract[]>([])
const loading = ref(false)

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString()
}

onMounted(async () => {
  loading.value = true
  try {
    const response = await contractsService.list()
    contracts.value = response.data
  } catch (err) {
    console.error('Failed to fetch contracts:', err)
  } finally {
    loading.value = false
  }
})
</script>
