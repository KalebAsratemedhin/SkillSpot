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
        <FormField :error="errors.payment_schedule">
          <Label class="text-sm font-semibold text-slate-700">Payment schedule</Label>
          <select
            v-model="form.payment_schedule"
            class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20"
          >
            <option value="FIXED">Fixed price (pay once)</option>
            <option value="HOURLY">Hourly (provider logs hours, you approve and pay)</option>
          </select>
        </FormField>
        <FormField v-if="form.payment_schedule === 'HOURLY'" :error="errors.hourly_rate">
          <Label class="text-sm font-semibold text-slate-700">Hourly rate</Label>
          <Input
            v-model="form.hourly_rate"
            type="number"
            step="0.01"
            min="0"
            placeholder="0.00"
            :error="errors.hourly_rate"
            class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20"
          />
        </FormField>
        <FormField :error="errors.total_amount">
          <Label class="text-sm font-semibold text-slate-700">{{ form.payment_schedule === 'HOURLY' ? 'Total cap (optional max)' : 'Total Amount' }}</Label>
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
  payment_schedule: 'FIXED' as 'FIXED' | 'HOURLY',
  hourly_rate: '',
  total_amount: '',
  start_date: '',
  end_date: '',
})

const errors = reactive({
  title: '',
  description: '',
  terms: '',
  payment_schedule: '',
  hourly_rate: '',
  total_amount: '',
  start_date: '',
  end_date: '',
})

function clearErrors() {
  errors.title = ''
  errors.description = ''
  errors.terms = ''
  errors.payment_schedule = ''
  errors.hourly_rate = ''
  errors.total_amount = ''
  errors.start_date = ''
  errors.end_date = ''
}

onMounted(async () => {
  if (jobId.value && authStore.isClient) {
    await jobsStore.fetchJob(jobId.value)
    const job = jobsStore.currentJob as { title?: string; budget_max?: number; budget_min?: number; payment_schedule?: 'FIXED' | 'HOURLY' } | null
    if (job) {
      if (!form.title) form.title = job.title ?? ''
      if (!form.total_amount && (job.budget_max ?? job.budget_min) != null) {
        form.total_amount = String(job.budget_max ?? job.budget_min)
      }
      if (job.payment_schedule) form.payment_schedule = job.payment_schedule
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
  const hourlyRate = form.hourly_rate ? parseFloat(String(form.hourly_rate).trim()) : NaN
  if (!form.title?.trim()) errors.title = 'Title is required.'
  if (!form.description?.trim()) errors.description = 'Description is required.'
  if (!form.terms?.trim()) errors.terms = 'Terms are required.'
  if (!form.start_date?.trim()) errors.start_date = 'Start date is required.'
  if (form.payment_schedule === 'HOURLY' && (Number.isNaN(hourlyRate) || hourlyRate <= 0)) {
    errors.hourly_rate = 'Enter a valid hourly rate.'
  }
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
      currency: 'ETB',
      payment_schedule: form.payment_schedule,
      start_date: form.start_date.trim(),
    }
    if (form.payment_schedule === 'HOURLY') payload.hourly_rate = hourlyRate
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
      ;['title', 'description', 'terms', 'payment_schedule', 'hourly_rate', 'total_amount', 'start_date', 'end_date'].forEach((key) => {
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
