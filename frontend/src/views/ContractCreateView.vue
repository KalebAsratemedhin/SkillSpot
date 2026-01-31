<template>
  <AppLayout>
    <div class="max-w-2xl mx-auto px-6 lg:px-10 py-10">
      <h1 class="text-3xl font-bold text-midnight mb-8">Create Contract</h1>
      <p v-if="!authStore.isClient" class="text-slate-500 mb-6">Only clients can create contracts from accepted applications.</p>
      <form v-else @submit.prevent="handleSubmit" class="space-y-6">
        <FormField :error="errors.title">
          <Label class="text-sm font-semibold text-slate-700">Contract Title</Label>
          <Input
            v-model="form.title"
            placeholder="e.g. Home Rewiring – Master Electrician"
            :error="errors.title"
            class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20"
          />
        </FormField>
        <FormField :error="errors.description">
          <Label class="text-sm font-semibold text-slate-700">Description</Label>
          <textarea
            v-model="form.description"
            class="w-full rounded-xl border border-slate-200 bg-white text-slate-900 focus:ring-2 focus:ring-amber/20 p-4 min-h-[120px] placeholder:text-slate-400"
            placeholder="Scope of work and deliverables..."
          />
        </FormField>
        <FormField :error="errors.terms">
          <Label class="text-sm font-semibold text-slate-700">Terms & Conditions</Label>
          <textarea
            v-model="form.terms"
            class="w-full rounded-xl border border-slate-200 bg-white text-slate-900 focus:ring-2 focus:ring-amber/20 p-4 min-h-[120px] placeholder:text-slate-400"
            placeholder="Payment terms, timeline, and other conditions..."
          />
        </FormField>
        <FormField :error="errors.total_amount">
          <Label class="text-sm font-semibold text-slate-700">Total Amount</Label>
          <Input
            v-model="form.total_amount"
            type="number"
            step="0.01"
            min="0"
            placeholder="0.00"
            :error="errors.total_amount"
            class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20"
          />
        </FormField>
        <FormField :error="errors.start_date">
          <Label class="text-sm font-semibold text-slate-700">Start Date</Label>
          <Input
            v-model="form.start_date"
            type="date"
            :error="errors.start_date"
            class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20"
          />
        </FormField>
        <FormField :error="errors.end_date">
          <Label class="text-sm font-semibold text-slate-700">End Date (optional)</Label>
          <Input
            v-model="form.end_date"
            type="date"
            :error="errors.end_date"
            class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20"
          />
        </FormField>
        <div class="pt-4 flex gap-3">
          <Button type="submit" :loading="loading" variant="default" size="lg" class="flex-1">
            Create Contract
          </Button>
          <Button type="button" variant="outline" size="lg" @click="router.push('/contracts')">
            Cancel
          </Button>
        </div>
      </form>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useJobsStore } from '@/stores/jobs'
import { contractsService, type CreateContractPayload } from '@/services/contracts'
import AppLayout from '@/components/AppLayout.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Label from '@/components/ui/Label.vue'
import FormField from '@/components/ui/FormField.vue'
import { toast } from 'vue-sonner'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const jobsStore = useJobsStore()
const loading = ref(false)

const jobId = computed(() => route.query.job as string | undefined)
const applicationId = computed(() => route.query.application as string | undefined)
const providerId = computed(() => route.query.provider as string | undefined)

const form = reactive({
  title: '',
  description: '',
  terms: '',
  total_amount: '',
  start_date: '',
  end_date: '',
})

const errors = reactive({
  title: '',
  description: '',
  terms: '',
  total_amount: '',
  start_date: '',
  end_date: '',
})

function clearErrors() {
  errors.title = ''
  errors.description = ''
  errors.terms = ''
  errors.total_amount = ''
  errors.start_date = ''
  errors.end_date = ''
}

onMounted(async () => {
  if (jobId.value && authStore.isClient) {
    await jobsStore.fetchJob(jobId.value)
    const job = jobsStore.currentJob
    if (job) {
      if (!form.title) form.title = job.title
      if (!form.total_amount && (job.budget_max ?? job.budget_min) != null) {
        form.total_amount = String(job.budget_max ?? job.budget_min)
      }
    }
  }
  if (!providerId.value && authStore.isClient) {
    toast.error('Missing provider. Create a contract from an accepted application on the job page.')
  }
})

async function handleSubmit() {
  if (!authStore.isClient || !providerId.value) return
  clearErrors()
  const amount = form.total_amount ? parseFloat(String(form.total_amount).trim()) : NaN
  if (!form.title?.trim()) errors.title = 'Title is required.'
  if (!form.description?.trim()) errors.description = 'Description is required.'
  if (!form.terms?.trim()) errors.terms = 'Terms are required.'
  if (!form.start_date?.trim()) errors.start_date = 'Start date is required.'
  if (Number.isNaN(amount) || amount < 0) errors.total_amount = 'Enter a valid amount.'
  if (Object.values(errors).some(Boolean)) return

  loading.value = true
  try {
    const payload: CreateContractPayload = {
      provider_id: providerId.value,
      title: form.title.trim(),
      description: form.description.trim(),
      terms: form.terms.trim(),
      total_amount: amount,
      currency: 'USD',
      start_date: form.start_date.trim(),
    }
    if (jobId.value) payload.job = jobId.value
    if (applicationId.value) payload.job_application = applicationId.value
    if (form.end_date?.trim()) payload.end_date = form.end_date.trim()

    const res = await contractsService.create(payload)
    const contract = res.data
    if (contract?.id) {
      toast.success('Contract created. Both parties can sign to start the job.')
      router.push(`/contracts/${contract.id}`)
    } else {
      toast.error('Contract was created but could not open it.')
    }
  } catch (err: any) {
    const data = err.response?.data
    if (data && typeof data === 'object') {
      const msg = data.error ?? (Array.isArray(data.non_field_errors) ? data.non_field_errors[0] : null) ?? 'Failed to create contract.'
      toast.error(msg)
      ;['title', 'description', 'terms', 'total_amount', 'start_date', 'end_date'].forEach((key) => {
        const val = data[key]
        if (key in errors) (errors as Record<string, string>)[key] = Array.isArray(val) ? val[0] : (val ?? '')
      })
    } else {
      toast.error('Failed to create contract. Please try again.')
    }
  } finally {
    loading.value = false
  }
}
</script>
