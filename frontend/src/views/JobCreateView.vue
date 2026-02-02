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
            placeholder="City, area or address (optional: pick on map below)"
            :error="errors.location"
            class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20 focus:border-amber"
          />
        </FormField>
        <FormField v-if="showMap" :error="errors.latitude">
          <Label class="text-sm font-semibold text-slate-700">Pick location on map</Label>
          <div class="job-create-map-wrapper relative z-0 rounded-xl overflow-hidden border border-slate-200 h-[280px] bg-slate-100">
            <div ref="mapContainer" class="w-full h-full"></div>
          </div>
          <p class="text-xs text-slate-500 mt-1">Click on the map to set job location. Lat: {{ form.latitude ?? '–' }}, Lng: {{ form.longitude ?? '–' }}</p>
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
            <span v-if="!skillTags.length" class="text-slate-400 text-sm">Loading skills…</span>
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

        <!-- Fixed-height row so layout doesn't shift when switching hourly/fixed -->
        <div class="min-h-[76px] flex flex-col justify-end">
          <FormField v-if="form.budget_type === 'hourly'" :error="errors.budget_min">
            <Label class="text-sm font-semibold text-slate-700">Rate (Br/hr)</Label>
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
            <Label class="text-sm font-semibold text-slate-700">Fixed Price (Br)</Label>
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
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { useJobsStore } from '@/stores/jobs'
import { useProfilesStore } from '@/stores/profiles'
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
const profilesStore = useProfilesStore()

onMounted(async () => {
  await profilesStore.fetchTags({ category: 'SKILL' })
  skillTags.value = (profilesStore.tags || []).map((t: { id: string; name: string }) => ({ id: t.id, name: t.name }))
  showMap.value = true
  await import('vue').then(({ nextTick }) => nextTick())
  initMap()
})

const form = reactive({
  title: '',
  description: '',
  location: '',
  budget_type: 'hourly' as 'hourly' | 'fixed',
  budget_min: '',
  budget_max: '',
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
  latitude: '',
})

const skillTags = ref<{ id: string; name: string }[]>([])
const showMap = ref(false)
const mapContainer = ref<HTMLElement | null>(null)
let mapInstance: import('leaflet').Map | null = null
let marker: import('leaflet').Marker | null = null

function toggleSkill(id: string) {
  const i = form.skill_ids.indexOf(id)
  if (i >= 0) form.skill_ids.splice(i, 1)
  else form.skill_ids.push(id)
}

function initMap() {
  const el = mapContainer.value
  if (!el || mapInstance) return
  import('leaflet').then((L) => {
    mapInstance = L.map(el).setView([9.03, 38.74], 6)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap',
    }).addTo(mapInstance)
    mapInstance.on('click', (e: { latlng: { lat: number; lng: number } }) => {
      const { lat, lng } = e.latlng
      form.latitude = Math.round(lat * 1e6) / 1e6
      form.longitude = Math.round(lng * 1e6) / 1e6
      if (marker) marker.setLatLng(e.latlng)
      else {
        marker = L.marker(e.latlng).addTo(mapInstance!)
      }
    })
  })
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
  errors.title = ''
  errors.description = ''
  errors.location = ''
  errors.budget_min = ''
  errors.budget_max = ''
  errors.latitude = ''

  try {
    const budget = getBudgetPayload()
    const payload: Record<string, unknown> = {
      title: form.title.trim(),
      description: form.description.trim(),
      location: form.location.trim() || 'Location to be specified',
      payment_schedule: form.budget_type === 'hourly' ? 'HOURLY' : 'FIXED',
      ...budget,
    }
    if (form.skill_ids.length) payload.skill_ids = form.skill_ids
    const latNum = form.latitude != null ? Number(form.latitude) : undefined
    const lngNum = form.longitude != null ? Number(form.longitude) : undefined
    if (latNum != null && lngNum != null && !Number.isNaN(latNum) && !Number.isNaN(lngNum)) {
      payload.latitude = latNum
      payload.longitude = lngNum
    }

    console.log('[Job Create] Sending payload:', {
      ...payload,
      latitude: form.latitude,
      longitude: form.longitude,
      hasLatLng: form.latitude != null && form.longitude != null,
    })

    const job = await jobsStore.createJob(payload)

    console.log('[Job Create] Job created – response from API:', {
      id: job?.id,
      latitude: job?.latitude,
      longitude: job?.longitude,
      hasLatLng: job?.latitude != null && job?.longitude != null,
      fullJob: job,
    })
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

<style scoped>
.job-create-map-wrapper :deep(.leaflet-pane),
.job-create-map-wrapper :deep(.leaflet-control) {
  z-index: 1 !important;
}
</style>
