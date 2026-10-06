<template>
  <AppLayout>
    <div class="w-full max-w-7xl mx-auto px-4 md:px-6 lg:px-10 py-6 md:py-10">
      <h1 class="text-2xl md:text-3xl font-bold text-midnight mb-6 md:mb-8">Post a Job</h1>

      <div class="flex flex-col lg:flex-row gap-6 lg:gap-8 items-stretch lg:items-start">
        <form @submit.prevent="handleSubmit" class="w-full lg:w-[40%] lg:max-w-xl lg:shrink-0 space-y-6 min-w-0 order-1">
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
              class="w-full rounded-xl border border-slate-200 bg-white text-slate-900 focus:ring-2 focus:ring-amber/20 focus:border-amber p-4 min-h-[160px] placeholder:text-slate-400"
              :class="errors.description ? 'border-red-500' : ''"
              placeholder="Describe the job in detail..."
            />
          </FormField>

          <FormField :error="errors.location">
            <Label class="text-sm font-semibold text-slate-700">Location <span class="font-normal text-slate-400">(optional)</span></Label>
            <Input
              v-model="form.location"
              placeholder="City, area or address — or pick on the map"
              :error="errors.location"
              class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20 focus:border-amber"
            />
          </FormField>

          <FormField>
            <Label class="text-sm font-semibold text-slate-700">Required skills</Label>
            <div class="flex flex-wrap gap-2 mt-2 p-3 rounded-xl border border-slate-200 bg-white min-h-[48px]">
              <button
                v-for="tag in skillTags"
                :key="tag.id"
                type="button"
                :class="form.skill_ids.includes(tag.id)
                  ? 'px-3 py-1.5 rounded-lg text-sm font-semibold bg-amber text-midnight border border-amber'
                  : 'px-3 py-1.5 rounded-lg text-sm font-semibold bg-slate-100 text-slate-600 border border-transparent hover:bg-slate-200'"
                @click="toggleSkill(tag.id)"
              >
                {{ tag.name }}
              </button>
              <span v-if="skillsLoading" class="text-slate-400 text-sm">Loading skills…</span>
              <span v-else-if="skillsLoadError" class="text-red-600 text-sm">
                {{ skillsLoadError }}
                <button type="button" class="ml-2 underline font-medium" @click="loadSkills">Retry</button>
              </span>
              <span v-else-if="!skillTags.length" class="text-slate-400 text-sm">No skills available. Add skills in your profile or ask an admin to add tags.</span>
            </div>
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

          <div class="min-h-[76px] flex flex-col justify-end">
            <FormField v-if="form.budget_type === 'hourly'" :error="errors.rate_hourly || errors.budget_min">
              <Label class="text-sm font-semibold text-slate-700">Rate (Br/hr)</Label>
              <Input
                v-model="form.rate_hourly"
                type="number"
                step="0.01"
                min="0"
                placeholder="e.g. 45"
                :error="errors.rate_hourly || errors.budget_min"
                class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20 focus:border-amber"
              />
            </FormField>
            <FormField v-else :error="errors.price_fixed || errors.budget_max">
              <Label class="text-sm font-semibold text-slate-700">Fixed Price ($)</Label>
              <Input
                v-model="form.price_fixed"
                type="number"
                step="0.01"
                min="0"
                placeholder="e.g. 500"
                :error="errors.price_fixed || errors.budget_max"
                class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20 focus:border-amber"
              />
            </FormField>
          </div>

          <p v-if="formError" class="text-sm text-red-500">{{ formError }}</p>

          <div class="pt-2">
            <Button type="submit" :loading="jobsStore.loading" variant="default" size="lg" class="w-full">
              Post Job
            </Button>
          </div>
        </form>

        <!-- One map instance: below form on mobile, sticky right (wider) on desktop -->
        <aside
          class="w-full order-2 lg:flex-1 lg:min-w-0 lg:sticky lg:top-24 lg:h-[calc(100dvh-8rem)] flex flex-col"
        >
          <FormField :error="errors.latitude" class="flex flex-col h-full min-h-0">
            <Label class="text-sm font-semibold text-slate-700 mb-2">Pick location on map</Label>
            <div class="h-[280px] lg:flex-1 lg:min-h-[320px] lg:h-auto relative rounded-xl overflow-hidden border border-slate-200">
              <LocationMap
                :lat="form.latitude"
                :lng="form.longitude"
                :pinned="form.latitude != null && form.longitude != null"
                :interactive="true"
                :zoom="6"
                @pick="onMapPick"
              />
            </div>
            <p class="text-xs text-slate-500 mt-2">
              Optional — click the map to set coordinates.
              <span v-if="form.latitude != null">Lat {{ form.latitude }}, Lng {{ form.longitude }}</span>
            </p>
          </FormField>
        </aside>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useJobsStore } from '@/stores/jobs'
import { useProfilesStore } from '@/stores/profiles'
import { jobCreateSchema } from '@/lib/validations/job'
import AppLayout from '@/components/AppLayout.vue'
import LocationMap from '@/components/LocationMap.vue'
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
const profilesStore = useProfilesStore()

const form = reactive({
  title: '',
  description: '',
  location: '',
  budget_type: 'hourly' as 'hourly' | 'fixed',
  rate_hourly: '',
  price_fixed: '',
  skill_ids: [] as string[],
  latitude: null as number | null,
  longitude: null as number | null,
})

const errors = reactive({
  title: '',
  description: '',
  location: '',
  budget_type: '',
  budget_min: '',
  budget_max: '',
  rate_hourly: '',
  price_fixed: '',
  latitude: '',
})

const formError = ref('')
const skillTags = ref<{ id: string; name: string }[]>([])
const skillsLoadError = ref<string | null>(null)
const skillsLoading = ref(true)

function clearFieldError(...keys: (keyof typeof errors)[]) {
  keys.forEach((key) => {
    errors[key] = ''
  })
  formError.value = ''
}

watch(() => form.title, () => clearFieldError('title'))
watch(() => form.description, () => clearFieldError('description'))
watch(() => form.location, () => clearFieldError('location'))
watch(() => form.budget_type, () => clearFieldError('budget_type'))
watch(() => form.rate_hourly, () => clearFieldError('rate_hourly', 'budget_min'))
watch(() => form.price_fixed, () => clearFieldError('price_fixed', 'budget_max'))

function clearErrors() {
  Object.keys(errors).forEach((key) => {
    errors[key as keyof typeof errors] = ''
  })
  formError.value = ''
}

function applyFieldErrors(source: Record<string, unknown>) {
  const fieldMap: Record<string, keyof typeof errors> = {
    title: 'title',
    description: 'description',
    location: 'location',
    budget_type: 'budget_type',
    budget_min: 'budget_min',
    budget_max: 'budget_max',
    rate_hourly: 'rate_hourly',
    price_fixed: 'price_fixed',
    latitude: 'latitude',
    longitude: 'latitude',
    payment_schedule: 'budget_type',
  }
  Object.entries(source).forEach(([key, val]) => {
    const target = fieldMap[key]
    if (!target) return
    errors[target] = Array.isArray(val) ? String(val[0] ?? '') : String(val ?? '')
  })
}

async function loadSkills() {
  skillsLoadError.value = null
  skillsLoading.value = true
  try {
    await profilesStore.fetchTags({ category: 'SKILL' })
    const data = profilesStore.tags ?? []
    skillTags.value = Array.isArray(data) ? data.map((t: { id: string; name: string }) => ({ id: t.id, name: t.name })) : []
  } catch (_err: any) {
    skillsLoadError.value = _err.response?.data?.detail || 'Could not load skills.'
    skillTags.value = []
  } finally {
    skillsLoading.value = false
  }
}

onMounted(() => {
  void loadSkills()
})

function toggleSkill(id: string) {
  const i = form.skill_ids.indexOf(id)
  if (i >= 0) form.skill_ids.splice(i, 1)
  else form.skill_ids.push(id)
}

function onMapPick(lat: number, lng: number) {
  form.latitude = lat
  form.longitude = lng
  clearFieldError('latitude')
}

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
  clearErrors()

  const parsed = jobCreateSchema.safeParse({
    title: form.title,
    description: form.description,
    location: form.location,
    budget_type: form.budget_type,
    rate_hourly: form.rate_hourly,
    price_fixed: form.price_fixed,
    skill_ids: form.skill_ids,
    latitude: form.latitude,
    longitude: form.longitude,
  })

  if (!parsed.success) {
    parsed.error.issues.forEach((issue) => {
      const field = issue.path[0] as keyof typeof errors | undefined
      if (field && field in errors && !errors[field]) {
        errors[field] = issue.message
      }
    })
    return
  }

  try {
    const budget = getBudgetPayload()
    const payload: Record<string, unknown> = {
      title: parsed.data.title,
      description: parsed.data.description,
      location: parsed.data.location.trim(),
      payment_schedule: parsed.data.budget_type === 'hourly' ? 'HOURLY' : 'FIXED',
      ...budget,
    }
    if (parsed.data.skill_ids.length) payload.skill_ids = parsed.data.skill_ids
    if (
      parsed.data.latitude != null &&
      parsed.data.longitude != null &&
      Number.isFinite(parsed.data.latitude) &&
      Number.isFinite(parsed.data.longitude)
    ) {
      payload.latitude = parsed.data.latitude
      payload.longitude = parsed.data.longitude
    }

    const job = await jobsStore.createJob(payload)
    if (job?.id) {
      await router.push(`/jobs/${job.id}`)
      return
    }
    formError.value = 'Job was created but we could not open it.'
  } catch (err: any) {
    const data = err.response?.data
    if (data && typeof data === 'object') {
      applyFieldErrors(data as Record<string, unknown>)
      const hasFieldError = Object.values(errors).some(Boolean)
      if (!hasFieldError) {
        formError.value =
          (data.error as string) ??
          (Array.isArray(data.non_field_errors) ? data.non_field_errors[0] : null) ??
          'Failed to create job.'
      }
    } else {
      formError.value = 'Failed to create job. Please try again.'
    }
  }
}
</script>
