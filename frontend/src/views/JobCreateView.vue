<template>
  <AppLayout>
    <div class="w-full max-w-2xl mx-auto px-4 md:px-6 lg:px-10 py-6 md:py-10">
      <h1 class="text-2xl md:text-3xl font-bold text-midnight mb-6 md:mb-8">Post a Job</h1>
      <form @submit.prevent="handleSubmit" class="space-y-6">
        <FormField :error="errors.title">
          <Label class="text-sm font-semibold text-slate-700">Job Title</Label>
          <Input
            v-model="form.title"
            placeholder="e.g. Master Electrician for Home Rewiring"
            :error="errors.title"
            class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20 focus:border-amber"
          />
        </FormField>

        <FormField :error="errors.description">
          <Label class="text-sm font-semibold text-slate-700">Description</Label>
          <textarea
            v-model="form.description"
            class="w-full rounded-xl border border-slate-200 bg-white text-slate-900 focus:ring-2 focus:ring-amber/20 focus:border-amber p-4 min-h-[200px] placeholder:text-slate-400"
            placeholder="Describe the job in detail..."
          />
        </FormField>

        <FormField :error="errors.location">
          <Label class="text-sm font-semibold text-slate-700">Location</Label>
          <Input
            v-model="form.location"
            placeholder="City, State or Zip Code"
            :error="errors.location"
            class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20 focus:border-amber"
          />
        </FormField>

        <FormField :error="errors.budget_type">
          <Label class="text-sm font-semibold text-slate-700">Payment Schedule</Label>
          <Select v-model="form.budget_type">
            <SelectTrigger
              class="h-11 w-full rounded-xl border border-slate-200 bg-white text-slate-900 placeholder:text-slate-500 focus:ring-2 focus:ring-amber/20 [&>span]:line-clamp-1"
            >
              <SelectValue placeholder="Select payment type" />
            </SelectTrigger>
            <SelectContent class="rounded-xl border border-slate-200 bg-white text-slate-900">
              <SelectItem value="hourly" class="data-[highlighted]:bg-slate-100 data-[highlighted]:text-slate-900 focus:bg-slate-100 focus:text-slate-900">Hourly</SelectItem>
              <SelectItem value="fixed" class="data-[highlighted]:bg-slate-100 data-[highlighted]:text-slate-900 focus:bg-slate-100 focus:text-slate-900">Fixed Price</SelectItem>
            </SelectContent>
          </Select>
        </FormField>

        <!-- Fixed-height row so layout doesn't shift when switching hourly/fixed -->
        <div class="min-h-[76px] flex flex-col justify-end">
          <FormField v-if="form.budget_type === 'hourly'" :error="errors.budget_min">
            <Label class="text-sm font-semibold text-slate-700">Rate ($/hr)</Label>
            <Input
              v-model="form.rate_hourly"
              type="number"
              step="0.01"
              min="0"
              placeholder="e.g. 45"
              :error="errors.budget_min"
              class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20 focus:border-amber"
            />
          </FormField>
          <FormField v-else :error="errors.budget_max">
            <Label class="text-sm font-semibold text-slate-700">Fixed Price ($)</Label>
            <Input
              v-model="form.price_fixed"
              type="number"
              step="0.01"
              min="0"
              placeholder="e.g. 500"
              :error="errors.budget_max"
              class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20 focus:border-amber"
            />
          </FormField>
        </div>

        <div class="pt-4">
          <Button type="submit" :loading="jobsStore.loading" variant="default" size="lg" class="w-full">
            Post Job
          </Button>
        </div>
      </form>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { useJobsStore } from '@/stores/jobs'
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

const router = useRouter()
const jobsStore = useJobsStore()

const form = reactive({
  title: '',
  description: '',
  location: '',
  budget_type: 'hourly' as 'hourly' | 'fixed',
  budget_min: '',
  budget_max: '',
  rate_hourly: '',
  price_fixed: '',
})

const errors = reactive({
  title: '',
  description: '',
  location: '',
  budget_type: '',
  budget_min: '',
  budget_max: '',
})

function getBudgetPayload(): { budget_min?: number; budget_max?: number } {
  if (form.budget_type === 'hourly') {
    const v = form.rate_hourly ? parseFloat(String(form.rate_hourly).trim()) : NaN
    if (!Number.isNaN(v) && v >= 0) return { budget_min: v, budget_max: v }
    return {}
  }
  const v = form.price_fixed ? parseFloat(String(form.price_fixed).trim()) : NaN
  if (!Number.isNaN(v) && v >= 0) return { budget_min: v, budget_max: v }
  return {}
}

async function handleSubmit() {
  errors.title = ''
  errors.description = ''
  errors.location = ''
  errors.budget_min = ''
  errors.budget_max = ''

  try {
    const budget = getBudgetPayload()
    const payload = {
      title: form.title.trim(),
      description: form.description.trim(),
      location: form.location.trim(),
      ...budget,
    }
    const job = await jobsStore.createJob(payload)
    if (job?.id) {
      router.push(`/jobs/${job.id}`)
    } else {
      toast.error('Job was created but we could not open it.')
    }
  } catch (err: any) {
    const data = err.response?.data
    if (data && typeof data === 'object') {
      const msg = data.error ?? (Array.isArray(data.non_field_errors) ? data.non_field_errors[0] : null) ?? 'Failed to create job.'
      toast.error(msg)
      ;['title', 'description', 'location', 'budget_min', 'budget_max'].forEach((key) => {
        const val = data[key]
        if (key in errors) {
          errors[key as keyof typeof errors] = Array.isArray(val) ? val[0] : (val ?? '')
        }
      })
    } else {
      toast.error('Failed to create job. Please try again.')
    }
  }
}
</script>
