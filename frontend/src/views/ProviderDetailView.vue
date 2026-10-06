<template>
  <AppLayout>
    <div class="w-full max-w-[1100px] mx-auto px-4 md:px-6 lg:px-10 py-6 md:py-10">
      <div v-if="loading" class="flex justify-center py-16">
        <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
      </div>
      <div v-else-if="!provider" class="text-center py-16">
        <p class="text-slate-500 mb-4">Provider not found.</p>
        <router-link to="/browse">
          <Button variant="default">Browse</Button>
        </router-link>
      </div>
      <div v-else class="space-y-8">
        <div class="flex flex-col md:flex-row gap-8 items-start">
          <div
            v-if="provider.avatar"
            class="size-28 md:size-36 rounded-2xl bg-cover bg-center shrink-0 ring-4 ring-amber/20 shadow-lg"
            :style="{ backgroundImage: `url(${provider.avatar})` }"
          />
          <div
            v-else
            class="size-28 md:size-36 rounded-2xl bg-slate-100 text-amber font-black flex items-center justify-center shrink-0 text-4xl ring-4 ring-amber/20"
          >
            {{ initials }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex flex-wrap items-center gap-3">
              <h1 class="text-3xl md:text-4xl font-extrabold text-midnight tracking-tight">
                {{ provider.full_name || 'Service provider' }}
              </h1>
              <span
                v-if="provider.is_verified"
                class="inline-flex items-center gap-1 rounded-lg bg-amber/10 px-3 py-1 text-sm font-bold text-amber border border-amber/20"
              >
                <span class="material-symbols-outlined text-base">verified</span>
                Verified
              </span>
            </div>
            <p v-if="provider.location" class="mt-2 text-slate-500 flex items-center gap-1">
              <span class="material-symbols-outlined text-amber text-lg">location_on</span>
              {{ provider.location }}
            </p>
            <div class="mt-4 flex flex-wrap gap-4 text-sm">
              <div v-if="provider.hourly_rate" class="font-bold text-midnight text-lg">
                Br {{ Number(provider.hourly_rate).toLocaleString() }}<span class="text-slate-500 font-medium text-sm">/hr</span>
              </div>
              <div v-if="provider.rating.count > 0" class="flex items-center gap-1 text-slate-600">
                <span class="material-symbols-outlined text-amber fill-1">star</span>
                <span class="font-bold text-midnight">{{ Number(provider.rating.average).toFixed(1) }}</span>
                <span>({{ provider.rating.count }} reviews)</span>
              </div>
              <div v-else class="text-slate-400">No reviews yet</div>
              <div v-if="provider.years_of_experience" class="text-slate-600">
                {{ provider.years_of_experience }}+ years experience
              </div>
              <div v-if="provider.availability" class="text-slate-600 capitalize">
                {{ provider.availability.replace(/_/g, ' ').toLowerCase() }}
              </div>
            </div>
            <p v-if="provider.member_since" class="mt-2 text-xs text-slate-400">
              Member since {{ formatMemberSince(provider.member_since) }}
            </p>
          </div>
        </div>

        <section v-if="provider.bio" class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 md:p-8">
          <h2 class="text-lg font-bold text-midnight mb-3">About</h2>
          <p class="text-slate-600 leading-relaxed whitespace-pre-wrap">{{ provider.bio }}</p>
        </section>

        <section class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 md:p-8">
          <h2 class="text-lg font-bold text-midnight mb-4">Skills</h2>
          <div v-if="displaySkills.length" class="flex flex-wrap gap-2">
            <span
              v-for="s in displaySkills"
              :key="s.id"
              class="px-4 py-2 rounded-xl bg-amber/10 border border-amber/20 text-sm font-bold text-amber"
            >
              {{ s.name }}
            </span>
          </div>
          <p v-else class="text-slate-400 text-sm">No skills listed.</p>
        </section>

        <section
          v-if="provider.certifications?.length"
          class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 md:p-8"
        >
          <h2 class="text-lg font-bold text-midnight mb-4">Certifications</h2>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="c in provider.certifications"
              :key="c.id"
              class="px-4 py-2 rounded-xl bg-slate-100 text-sm font-semibold text-midnight"
            >
              {{ c.name }}
            </span>
          </div>
        </section>

        <section
          v-if="provider.experiences?.length"
          class="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 md:p-8"
        >
          <h2 class="text-lg font-bold text-midnight mb-4">Experience</h2>
          <ul class="space-y-4">
            <li
              v-for="exp in provider.experiences"
              :key="exp.id"
              class="border-l-2 border-amber/30 pl-4"
            >
              <h3 class="font-bold text-midnight">{{ exp.title }}</h3>
              <p v-if="exp.company_name" class="text-sm text-slate-500">{{ exp.company_name }}</p>
              <p v-if="exp.description" class="text-sm text-slate-600 mt-1">{{ exp.description }}</p>
              <p class="text-xs text-slate-400 mt-1">
                {{ formatExpDate(exp.start_date) }} –
                {{ exp.is_current ? 'Present' : formatExpDate(exp.end_date || '') }}
              </p>
            </li>
          </ul>
        </section>

        <div class="flex flex-wrap gap-3">
          <router-link to="/browse">
            <Button variant="outline" class="border-slate-200 text-slate-700">Back to browse</Button>
          </router-link>
          <router-link v-if="!authStore.isAuthenticated" :to="{ name: 'login', query: { redirect: route.fullPath } }">
            <Button variant="default">Sign in to hire</Button>
          </router-link>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { profilesService, type PublicProviderDetail } from '@/services/profiles'
import AppLayout from '@/components/AppLayout.vue'
import Button from '@/components/ui/Button.vue'

const route = useRoute()
const authStore = useAuthStore()
const loading = ref(true)
const provider = ref<PublicProviderDetail | null>(null)

const initials = computed(() => {
  const name = provider.value?.full_name || 'P'
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  return name.charAt(0).toUpperCase()
})

const displaySkills = computed(() => {
  if (!provider.value) return []
  if (provider.value.skills?.length) return provider.value.skills
  return provider.value.headline_skills || []
})

function formatMemberSince(raw: string) {
  return new Date(raw).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
}

function formatExpDate(raw: string) {
  if (!raw) return ''
  return new Date(raw).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
}

async function load() {
  const userId = route.params.userId as string
  if (!userId) return
  loading.value = true
  provider.value = null
  try {
    const res = await profilesService.getPublicProvider(userId)
    provider.value = res.data
  } catch {
    provider.value = null
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => route.params.userId, load)
</script>
