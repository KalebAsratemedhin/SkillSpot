<template>
  <AppLayout>
    <div class="w-full max-w-7xl mx-auto px-4 md:px-6 lg:px-10 py-6 md:py-10">
      <h1 class="text-2xl md:text-3xl font-bold text-midnight mb-6 md:mb-8">
        {{ isEdit ? 'Edit Job' : 'Post a Job' }}
      </h1>

      <div v-if="pageLoading" class="flex justify-center py-16">
        <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
      </div>

      <div
        v-else
        class="flex flex-col lg:flex-row gap-6 lg:gap-8 items-stretch lg:items-start"
      >
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

          <FormField :error="errors.address">
            <Label class="text-sm font-semibold text-slate-700">Address</Label>
            <Input
              v-model="form.address"
              placeholder="Street, area, or neighborhood"
              :error="errors.address"
              class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20 focus:border-amber"
            />
          </FormField>

          <FormField>
            <Label class="text-sm font-semibold text-slate-700">Required skills</Label>
            <Input
              v-model="skillFilter"
              type="search"
              placeholder="Filter skills…"
              class="w-full mt-2 px-3 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20 focus:border-amber"
            />
            <div class="flex flex-wrap gap-2 mt-2 p-3 rounded-xl border border-slate-200 bg-white min-h-[48px] max-h-48 overflow-y-auto">
              <button
                v-for="tag in filteredSkillTags"
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
              <span v-else-if="!filteredSkillTags.length" class="text-slate-400 text-sm">No skills match “{{ skillFilter.trim() }}”.</span>
            </div>
            <p v-if="form.skill_ids.length" class="text-xs text-slate-500 mt-1.5">
              {{ form.skill_ids.length }} selected
            </p>
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

          <div class="pt-2 flex flex-col sm:flex-row gap-3">
            <Button
              v-if="isEdit"
              type="button"
              variant="outline"
              size="lg"
              class="w-full sm:w-auto"
              @click="router.push(`/jobs/${editJobId}`)"
            >
              Cancel
            </Button>
            <Button type="submit" :loading="jobsStore.loading" variant="default" size="lg" class="w-full sm:flex-1">
              {{ isEdit ? 'Save changes' : 'Post Job' }}
            </Button>
          </div>
        </form>

        <!-- One map instance: below form on mobile, sticky right (wider) on desktop -->
        <aside
          class="w-full order-2 lg:flex-1 lg:min-w-0 lg:sticky lg:top-24 lg:h-[min(42rem,calc(100dvh-12rem))] flex flex-col"
        >
          <FormField :error="errors.latitude" class="flex flex-col h-full min-h-0">
            <Label class="text-sm font-semibold text-slate-700 mb-2">
              Location on map <span class="font-normal text-slate-400">(optional)</span>
            </Label>

            <div class="relative mb-2">
              <Input
                v-model="placeQuery"
                type="search"
                autocomplete="off"
                placeholder="Search a place…"
                class="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20 focus:border-amber"
                @focus="showHits = placeHits.length > 0"
                @keydown.escape="showHits = false"
              />
              <p v-if="placeSearchError" class="text-xs text-red-500 mt-1">{{ placeSearchError }}</p>
              <ul
                v-if="showHits && placeHits.length"
                class="absolute z-20 left-0 right-0 mt-1 max-h-56 overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-lg"
                role="listbox"
              >
                <li
                  v-for="(hit, i) in placeHits"
                  :key="`${hit.lat}-${hit.lng}-${i}`"
                  role="option"
                  class="px-3 py-2.5 text-sm text-slate-800 cursor-pointer hover:bg-slate-50 border-b border-slate-100 last:border-0"
                  @mousedown.prevent="selectPlace(hit)"
                >
                  <span class="font-medium">{{ hit.label }}</span>
                  <span v-if="hit.kind" class="block text-xs text-slate-400 mt-0.5">{{ hit.kind }}</span>
                </li>
              </ul>
            </div>

            <div class="h-[330px] lg:flex-1 lg:min-h-[360px] lg:h-auto relative rounded-xl overflow-hidden border border-slate-200">
              <LocationMap
                :lat="form.latitude"
                :lng="form.longitude"
                :pinned="form.latitude != null && form.longitude != null"
                :interactive="true"
                :zoom="6"
                @pick="onMapPick"
              />
            </div>
            <p class="text-xs text-slate-500 mt-2 flex flex-wrap items-center gap-x-2 gap-y-1">
              <span>Optional — search or click the map to set coordinates.</span>
              <span v-if="form.latitude != null">Lat {{ form.latitude }}, Lng {{ form.longitude }}</span>
              <button
                v-if="form.latitude != null && form.longitude != null"
                type="button"
                class="text-amber font-medium underline-offset-2 hover:underline"
                @click="clearMapPin"
              >
                Clear pin
              </button>
            </p>
          </FormField>
        </aside>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useJobsStore } from '@/stores/jobs'
import { useProfilesStore } from '@/stores/profiles'
import { useAuthStore } from '@/stores/auth'
import { jobCreateSchema } from '@/lib/validations/job'
import { searchPlaces, reversePlace, type GeoHit } from '@/lib/geocode'
import { jobAddressText, jobCoordinates, jobsService, roundJobCoord, type Job } from '@/services/jobs'
import { toast } from 'vue-sonner'
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

const route = useRoute()
const router = useRouter()
const jobsStore = useJobsStore()
const profilesStore = useProfilesStore()
const authStore = useAuthStore()

const editJobId = computed(() => {
  if (route.name !== 'job-edit') return null
  const id = route.params.id
  return typeof id === 'string' ? id : Array.isArray(id) ? id[0] ?? null : null
})
const isEdit = computed(() => !!editJobId.value)
const pageLoading = ref(false)
/** When editing, if the user clears the pin we must send location: null. */
const pinCleared = ref(false)

const form = reactive({
  title: '',
  description: '',
  address: '',
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
  address: '',
  budget_type: '',
  budget_min: '',
  budget_max: '',
  rate_hourly: '',
  price_fixed: '',
  latitude: '',
})

const formError = ref('')
const skillTags = ref<{ id: string; name: string }[]>([])
const skillFilter = ref('')
const filteredSkillTags = computed(() => {
  const q = skillFilter.value.trim().toLowerCase()
  if (!q) return skillTags.value
  return skillTags.value.filter((t) => t.name.toLowerCase().includes(q))
})
const skillsLoadError = ref<string | null>(null)
const skillsLoading = ref(true)

const placeQuery = ref('')
const placeHits = ref<GeoHit[]>([])
const showHits = ref(false)
const placeSearchError = ref('')
let searchTimer: ReturnType<typeof setTimeout> | null = null
let searchAbort: AbortController | null = null
let reverseAbort: AbortController | null = null

function clearFieldError(...keys: (keyof typeof errors)[]) {
  keys.forEach((key) => {
    errors[key] = ''
  })
  formError.value = ''
}

watch(() => form.title, () => clearFieldError('title'))
watch(() => form.description, () => clearFieldError('description'))
watch(() => form.address, () => clearFieldError('address'))
watch(() => form.budget_type, () => clearFieldError('budget_type'))
watch(() => form.rate_hourly, () => clearFieldError('rate_hourly', 'budget_min'))
watch(() => form.price_fixed, () => clearFieldError('price_fixed', 'budget_max'))

watch(placeQuery, (q) => {
  placeSearchError.value = ''
  if (searchTimer) clearTimeout(searchTimer)
  const trimmed = q.trim()
  if (trimmed.length < 2) {
    placeHits.value = []
    showHits.value = false
    searchAbort?.abort()
    return
  }
  searchTimer = setTimeout(() => {
    void runPlaceSearch(trimmed)
  }, 320)
})

async function runPlaceSearch(q: string) {
  searchAbort?.abort()
  searchAbort = new AbortController()
  try {
    const bias =
      form.latitude != null && form.longitude != null
        ? { lat: form.latitude, lng: form.longitude }
        : undefined
    const hits = await searchPlaces(q, bias, searchAbort.signal)
    placeHits.value = hits
    showHits.value = hits.length > 0
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === 'AbortError') return
    placeHits.value = []
    showHits.value = false
    placeSearchError.value = 'Place search failed. Try again.'
  }
}

function selectPlace(hit: GeoHit) {
  form.latitude = roundJobCoord(hit.lat)
  form.longitude = roundJobCoord(hit.lng)
  form.address = hit.label
  placeQuery.value = hit.label
  placeHits.value = []
  showHits.value = false
  pinCleared.value = false
  clearFieldError('address', 'latitude')
}

function clearMapPin() {
  form.latitude = null
  form.longitude = null
  pinCleared.value = true
  clearFieldError('latitude')
}

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
    address: 'address',
    location: 'latitude',
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
    if (val && typeof val === 'object' && !Array.isArray(val)) {
      const nested = val as Record<string, unknown>
      const msg =
        nested.latitude ?? nested.longitude ?? nested.non_field_errors ?? nested[Object.keys(nested)[0] ?? '']
      errors[target] = Array.isArray(msg) ? String(msg[0] ?? '') : String(msg ?? '')
      return
    }
    errors[target] = Array.isArray(val) ? String(val[0] ?? '') : String(val ?? '')
  })
}

function populateFromJob(job: Job) {
  form.title = job.title || ''
  form.description = job.description || ''
  form.address = jobAddressText(job)
  const hourly = job.payment_schedule === 'HOURLY' || job.budget_type === 'hourly'
  form.budget_type = hourly ? 'hourly' : 'fixed'
  const amount = job.budget_max ?? job.budget_min
  if (hourly) {
    form.rate_hourly = amount != null ? String(amount) : ''
    form.price_fixed = ''
  } else {
    form.price_fixed = amount != null ? String(amount) : ''
    form.rate_hourly = ''
  }
  form.skill_ids = (job.required_skills ?? []).map((s) => s.id)
  const coords = jobCoordinates(job)
  if (coords) {
    form.latitude = roundJobCoord(coords.lat)
    form.longitude = roundJobCoord(coords.lng)
  } else {
    form.latitude = null
    form.longitude = null
  }
  pinCleared.value = false
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

async function loadEditJob() {
  const id = editJobId.value
  if (!id) return
  pageLoading.value = true
  try {
    const { data: job } = await jobsService.get(id)
    const userId = authStore.user?.id
    if (!userId || job.client !== userId) {
      toast.error('You can only edit your own jobs.')
      await router.replace(`/jobs/${id}`)
      return
    }
    populateFromJob(job)
  } catch {
    toast.error('Could not load job for editing.')
    await router.replace('/jobs')
  } finally {
    pageLoading.value = false
  }
}

onMounted(() => {
  void loadSkills()
  if (isEdit.value) void loadEditJob()
})

onBeforeUnmount(() => {
  if (searchTimer) clearTimeout(searchTimer)
  searchAbort?.abort()
  reverseAbort?.abort()
})

function toggleSkill(id: string) {
  const i = form.skill_ids.indexOf(id)
  if (i >= 0) form.skill_ids.splice(i, 1)
  else form.skill_ids.push(id)
}

async function onMapPick(lat: number, lng: number) {
  form.latitude = roundJobCoord(lat)
  form.longitude = roundJobCoord(lng)
  pinCleared.value = false
  clearFieldError('latitude')

  if (form.address.trim()) return

  reverseAbort?.abort()
  reverseAbort = new AbortController()
  try {
    const label = await reversePlace(lat, lng, reverseAbort.signal)
    if (!form.address.trim()) {
      form.address = label
      clearFieldError('address')
    }
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === 'AbortError') return
  }
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

function buildPayload(parsed: {
  title: string
  description: string
  address: string
  budget_type: 'hourly' | 'fixed'
  skill_ids: string[]
  latitude?: number | null
  longitude?: number | null
}): Record<string, unknown> {
  const budget = getBudgetPayload()
  const payload: Record<string, unknown> = {
    title: parsed.title,
    description: parsed.description,
    address: parsed.address.trim(),
    payment_schedule: parsed.budget_type === 'hourly' ? 'HOURLY' : 'FIXED',
    skill_ids: parsed.skill_ids,
    ...budget,
  }
  if (
    parsed.latitude != null &&
    parsed.longitude != null &&
    Number.isFinite(parsed.latitude) &&
    Number.isFinite(parsed.longitude)
  ) {
    payload.location = {
      latitude: roundJobCoord(parsed.latitude),
      longitude: roundJobCoord(parsed.longitude),
    }
  } else if (isEdit.value && pinCleared.value) {
    payload.location = null
  }
  return payload
}

async function handleSubmit() {
  clearErrors()

  const parsed = jobCreateSchema.safeParse({
    title: form.title,
    description: form.description,
    address: form.address,
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
    const payload = buildPayload(parsed.data)
    if (isEdit.value && editJobId.value) {
      const job = await jobsStore.updateJob(editJobId.value, payload)
      toast.success('Job updated.')
      if (job?.id) {
        await router.push(`/jobs/${job.id}`)
        return
      }
      formError.value = 'Job was updated but we could not open it.'
      return
    }

    const job = await jobsStore.createJob(payload)
    if (job?.id) {
      await router.push(`/jobs/${job.id}`)
      return
    }
    // Create succeeded but body lacked id — still leave the form.
    toast.success('Job created.')
    await router.push('/jobs')
  } catch (err: any) {
    const data = err.response?.data
    if (data && typeof data === 'object') {
      applyFieldErrors(data as Record<string, unknown>)
      const hasFieldError = Object.values(errors).some(Boolean)
      if (!hasFieldError) {
        formError.value =
          (data.error as string) ??
          (Array.isArray(data.non_field_errors) ? data.non_field_errors[0] : null) ??
          (isEdit.value ? 'Failed to update job.' : 'Failed to create job.')
      }
    } else {
      formError.value = isEdit.value
        ? 'Failed to update job. Please try again.'
        : 'Failed to create job. Please try again.'
    }
  }
}
</script>
