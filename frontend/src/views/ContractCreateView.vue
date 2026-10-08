<template>
  <AppLayout>
    <div class="max-w-2xl mx-auto px-6 lg:px-10 py-10">
      <h1 class="text-3xl font-bold text-midnight mb-8">Create Contract</h1>
      <p v-if="!authStore.isClient" class="text-slate-500 mb-6">Only clients can create contracts from accepted applications.</p>
      <form v-else @submit.prevent="handleSubmit" class="space-y-6">
        <div v-if="job" class="rounded-xl border border-slate-200 bg-slate-50 p-4 mb-2 space-y-1">
          <p class="text-xs font-bold uppercase tracking-wider text-slate-500">From job</p>
          <p class="text-midnight font-bold">{{ job.title }}</p>
          <p v-if="job.description" class="text-slate-600 text-sm line-clamp-2">{{ job.description }}</p>
          <p v-if="budgetCeiling != null" class="text-xs text-slate-500 pt-1">
            Client budget ceiling: Br {{ budgetCeiling.toLocaleString() }}{{ isHourlyJob ? '/hr' : '' }}
          </p>
        </div>
        <div
          v-if="applicationPrefill"
          class="rounded-xl border border-amber/20 bg-amber/5 p-4 text-sm text-slate-700"
        >
          Prefilling from provider proposal
          <span v-if="applicationPrefill.proposed_rate != null" class="font-semibold text-midnight">
            — Br {{ Number(applicationPrefill.proposed_rate).toLocaleString() }}{{ isHourlyJob ? '/hr' : '' }}
          </span>
        </div>
        <template v-if="!job">
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
              class="w-full rounded-xl border border-slate-200 bg-white text-slate-900 focus:ring-2 focus:ring-amber/20 p-4 min-h-[100px] placeholder:text-slate-400"
              placeholder="Scope of work..."
            />
          </FormField>
          <FormField :error="errors.terms">
            <Label class="text-sm font-semibold text-slate-700">Terms</Label>
            <textarea
              v-model="form.terms"
              class="w-full rounded-xl border border-slate-200 bg-white text-slate-900 focus:ring-2 focus:ring-amber/20 p-4 min-h-[80px] placeholder:text-slate-400"
              placeholder="Payment terms, timeline..."
            />
          </FormField>
        </template>
        <FormField :error="errors.payment_schedule">
          <Label class="text-sm font-semibold text-slate-700">Payment schedule</Label>
          <Select v-model="form.payment_schedule">
            <SelectTrigger
              class="h-11 w-full rounded-xl border border-slate-200 bg-white text-slate-900 placeholder:text-slate-500 focus:ring-2 focus:ring-amber/20 [&>span]:line-clamp-1"
              :disabled="!!job"
            >
              <SelectValue placeholder="Choose schedule" />
            </SelectTrigger>
            <SelectContent class="rounded-xl border border-slate-200 bg-white text-slate-900">
              <SelectItem value="FIXED" class="rounded-lg focus:bg-slate-100 focus:text-slate-900 data-[highlighted]:bg-slate-100 data-[highlighted]:text-slate-900">Fixed price (milestones)</SelectItem>
              <SelectItem value="HOURLY" class="rounded-lg focus:bg-slate-100 focus:text-slate-900 data-[highlighted]:bg-slate-100 data-[highlighted]:text-slate-900">Hourly (provider logs hours, you approve and pay)</SelectItem>
            </SelectContent>
          </Select>
          <p v-if="job" class="text-xs text-slate-500 mt-1">
            Matches the job ({{ isHourlyJob ? 'hourly' : 'fixed price' }}).
          </p>
        </FormField>
        <FormField v-if="form.payment_schedule === 'HOURLY'" :error="errors.hourly_rate">
          <Label class="text-sm font-semibold text-slate-700">Hourly rate (Br)</Label>
          <Input
            v-model="form.hourly_rate"
            type="number"
            step="0.01"
            min="0"
            :max="budgetCeiling ?? undefined"
            placeholder="0"
            :error="errors.hourly_rate"
            class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20"
          />
        </FormField>
        <FormField :error="errors.total_amount">
          <Label class="text-sm font-semibold text-slate-700">{{ form.payment_schedule === 'HOURLY' ? 'Total cap (Br)' : 'Total amount (Br)' }}</Label>
          <Input
            v-model="form.total_amount"
            type="number"
            step="0.01"
            min="0"
            :max="form.payment_schedule === 'FIXED' ? (budgetCeiling ?? undefined) : undefined"
            placeholder="0"
            :error="errors.total_amount"
            class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20"
          />
        </FormField>
        <FormField :error="errors.start_date">
          <Label class="text-sm font-semibold text-slate-700">Start date</Label>
          <Input
            v-model="form.start_date"
            type="date"
            :error="errors.start_date"
            class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20"
          />
        </FormField>
        <FormField :error="errors.end_date">
          <Label class="text-sm font-semibold text-slate-700">End date (optional)</Label>
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
import { jobsService, type JobApplication } from '@/services/jobs'
import { contractsService, type CreateContractPayload } from '@/services/contracts'
import AppLayout from '@/components/AppLayout.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Label from '@/components/ui/Label.vue'
import FormField from '@/components/ui/FormField.vue'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { toast } from 'vue-sonner'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const jobsStore = useJobsStore()
const loading = ref(false)
const applicationPrefill = ref<JobApplication | null>(null)

const jobId = computed(() => route.query.job as string | undefined)
const applicationId = computed(() => route.query.application as string | undefined)
const providerId = computed(() => route.query.provider as string | undefined)

const job = computed(() => {
  if (!jobId.value || !jobsStore.currentJob) return null
  return jobsStore.currentJob
})

const isHourlyJob = computed(() => {
  const j = job.value
  if (!j) return false
  return j.payment_schedule === 'HOURLY' || j.budget_type === 'hourly'
})

const budgetCeiling = computed(() => {
  const j = job.value
  if (!j) return null
  const max = j.budget_max ?? j.budget_min
  if (max == null || Number.isNaN(Number(max))) return null
  return Number(max)
})

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

function applyJobDefaults() {
  const j = jobsStore.currentJob
  if (!j) return
  form.title = j.title ?? ''
  form.description = (j.description ?? '').trim() || 'As per job description.'
  form.terms = 'Payment and terms as agreed. As per job agreement.'
  const ceiling = j.budget_max ?? j.budget_min
  if (ceiling != null) {
    form.total_amount = String(ceiling)
  }
  if (j.payment_schedule === 'HOURLY' || j.budget_type === 'hourly') {
    form.payment_schedule = 'HOURLY'
    form.hourly_rate = String(j.budget_min ?? j.budget_max ?? '')
  } else {
    form.payment_schedule = 'FIXED'
    form.hourly_rate = ''
  }
}

function applyApplicationDefaults(app: JobApplication) {
  applicationPrefill.value = app
  const rate = app.proposed_rate != null ? Number(app.proposed_rate) : NaN
  if (!Number.isFinite(rate) || rate < 0) return

  // proposed_rate is hourly rate on HOURLY jobs, total price on FIXED jobs — never force HOURLY.
  if (isHourlyJob.value) {
    form.payment_schedule = 'HOURLY'
    form.hourly_rate = String(rate)
    if (!form.total_amount && budgetCeiling.value != null) {
      form.total_amount = String(budgetCeiling.value)
    }
  } else {
    form.payment_schedule = 'FIXED'
    form.hourly_rate = ''
    form.total_amount = String(rate)
  }
}

onMounted(async () => {
  if (!authStore.isClient) return

  if (jobId.value) {
    await jobsStore.fetchJob(jobId.value)
    applyJobDefaults()
  }

  if (applicationId.value) {
    try {
      const res = await jobsService.getApplication(applicationId.value)
      applyApplicationDefaults(res.data)
    } catch {
      toast.error('Could not load the application proposal. Fill contract terms manually.')
    }
  }

  if (!providerId.value) {
    toast.error('Missing provider. Create a contract from an accepted application on the job page.')
  }
})

async function handleSubmit() {
  if (!authStore.isClient || !providerId.value) return
  clearErrors()
  // Job always wins — never save HOURLY for a fixed-price job (or vice versa).
  const schedule = job.value
    ? (isHourlyJob.value ? 'HOURLY' : 'FIXED')
    : form.payment_schedule
  form.payment_schedule = schedule

  const amount = form.total_amount ? parseFloat(String(form.total_amount).trim()) : NaN
  const hourlyRate = form.hourly_rate ? parseFloat(String(form.hourly_rate).trim()) : NaN
  if (!form.title?.trim()) errors.title = 'Title is required.'
  if (!form.description?.trim()) form.description = 'As per job description.'
  if (!form.terms?.trim()) form.terms = 'As per job agreement.'
  if (!form.start_date?.trim()) errors.start_date = 'Start date is required.'
  if (schedule === 'HOURLY') {
    if (Number.isNaN(hourlyRate) || hourlyRate <= 0) {
      errors.hourly_rate = 'Enter a valid hourly rate.'
    } else if (budgetCeiling.value != null && hourlyRate > budgetCeiling.value) {
      errors.hourly_rate = `Hourly rate cannot exceed the client budget of Br ${budgetCeiling.value.toLocaleString()}/hr.`
    }
  }
  if (Number.isNaN(amount) || amount < 0) {
    errors.total_amount = 'Enter a valid amount.'
  } else if (
    schedule === 'FIXED' &&
    budgetCeiling.value != null &&
    amount > budgetCeiling.value
  ) {
    errors.total_amount = `Amount cannot exceed the client budget of Br ${budgetCeiling.value.toLocaleString()}.`
  }
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
      payment_schedule: schedule,
      start_date: form.start_date.trim(),
    }
    if (schedule === 'HOURLY') payload.hourly_rate = hourlyRate
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
