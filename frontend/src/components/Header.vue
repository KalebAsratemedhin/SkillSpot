<template>
  <header class="sticky top-0 z-[1000] w-full border-b border-white/10 bg-midnight/95 backdrop-blur-md px-4 md:px-6 lg:px-20 py-3 md:py-4 text-white">
    <div class="mx-auto flex max-w-[1400px] items-center justify-between">
      <div class="flex items-center gap-2 md:gap-3">
        <div class="text-amber">
          <svg class="size-7 md:size-9" fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
            <path d="M44 11.2727C44 14.0109 39.8386 16.3957 33.69 17.6364C39.8386 18.877 44 21.2618 44 24C44 26.7382 39.8386 29.123 33.69 30.3636C39.8386 31.6043 44 33.9891 44 36.7273C44 40.7439 35.0457 44 24 44C12.9543 44 4 40.7439 4 36.7273C4 33.9891 8.16144 31.6043 14.31 30.3636C8.16144 29.123 4 26.7382 4 24C4 21.2618 8.16144 18.877 14.31 17.6364C8.16144 16.3957 4 14.0109 4 11.2727C4 7.25611 12.9543 4 24 4C35.0457 4 44 7.25611 44 11.2727Z" fill="currentColor"></path>
          </svg>
        </div>
        <h2 class="text-lg md:text-2xl font-extrabold leading-tight tracking-tight uppercase italic">SkillSpot</h2>
      </div>
      <nav v-if="authStore.isAuthenticated" class="hidden lg:flex flex-1 justify-center gap-6 xl:gap-10">
        <router-link to="/dashboard" class="text-sm font-semibold hover:text-amber transition-colors">Browse Jobs</router-link>
        <router-link to="/jobs" class="text-sm font-semibold hover:text-amber transition-colors">My Jobs</router-link>
        <router-link to="/applications" class="text-sm font-semibold hover:text-amber transition-colors">Applications</router-link>
        <router-link to="/invitations" class="text-sm font-semibold hover:text-amber transition-colors">Invitations</router-link>
        <router-link to="/messages" class="text-sm font-semibold hover:text-amber transition-colors">Messages</router-link>
        <router-link to="/contracts" class="text-sm font-semibold hover:text-amber transition-colors">Contracts</router-link>
        <router-link to="/payments" class="text-sm font-semibold hover:text-amber transition-colors">Payments</router-link>
      </nav>
      <div class="flex items-center gap-2 sm:gap-4 md:gap-6">
        <template v-if="authStore.isAuthenticated">
          <router-link v-if="authStore.isClient" to="/jobs/create" class="hidden sm:block">
            <Button variant="default" size="default" class="min-w-[100px] md:min-w-[120px] h-10 md:h-11 px-4 md:px-5 text-sm rounded-lg shadow-[0_4px_14px_0_rgba(245,158,11,0.39)] active:scale-95">
              Post a Job
            </Button>
          </router-link>
          <button class="hidden sm:flex items-center justify-center rounded-lg h-10 w-10 md:h-11 md:w-11 bg-midnight-light text-slate-300 hover:text-white transition-colors">
            <span class="material-symbols-outlined text-[20px] md:text-[22px]">notifications</span>
          </button>
          <div class="relative" ref="profileDropdownRef">
            <button
              type="button"
              class="size-8 md:size-10 rounded-full border-2 border-midnight-light overflow-hidden flex items-center justify-center font-semibold text-midnight text-sm md:text-base hover:ring-2 hover:ring-amber/50 focus:outline-none focus:ring-2 focus:ring-amber/50 bg-cover bg-center"
              :class="profilePictureUrl ? '' : 'bg-amber'"
              :style="profilePictureUrl ? { backgroundImage: `url(${profilePictureUrl})` } : undefined"
              @click="profileDropdownOpen = !profileDropdownOpen"
              aria-haspopup="true"
              :aria-expanded="profileDropdownOpen"
            >
              <span v-if="!profilePictureUrl">{{ userInitials }}</span>
            </button>
            <div
              v-if="profileDropdownOpen"
              class="absolute right-0 mt-2 w-48 rounded-xl border border-white/10 bg-midnight-light shadow-xl py-1 z-[1001]"
            >
              <router-link
                to="/profile"
                class="flex items-center gap-2 px-4 py-2.5 text-sm text-slate-300 hover:bg-white/5 hover:text-white transition-colors"
                @click="profileDropdownOpen = false"
              >
                <span class="material-symbols-outlined text-lg">person</span>
                Profile
              </router-link>
              <button
                type="button"
                class="flex w-full items-center gap-2 px-4 py-2.5 text-sm text-slate-300 hover:bg-white/5 hover:text-red-400 transition-colors"
                @click="handleLogout"
              >
                <span class="material-symbols-outlined text-lg">logout</span>
                Logout
              </button>
            </div>
          </div>
        </template>
        <template v-else>
          <router-link to="/login" class="text-sm font-semibold hover:text-amber transition-colors hidden sm:block">Login</router-link>
          <router-link to="/register">
            <Button variant="default" size="default" class="rounded-full h-9 md:h-11 px-5 md:px-7 text-sm">
              Join Today
            </Button>
          </router-link>
        </template>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProfilesStore } from '@/stores/profiles'
import Button from './ui/Button.vue'

const authStore = useAuthStore()
const profilesStore = useProfilesStore()
const router = useRouter()
const profileDropdownOpen = ref(false)
const profileDropdownRef = ref<HTMLElement | null>(null)

const profilePictureUrl = computed(() => {
  const raw = profilesStore.profile?.avatar || (authStore.user as { avatar?: string })?.avatar || null
  if (!raw) return null
  if (raw.startsWith('http')) return raw
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
  const origin = apiBase.replace(/\/api\/v1\/?$/, '')
  return origin + (raw.startsWith('/') ? raw : '/' + raw)
})

const userInitials = computed(() => {
  if (!authStore.user) return 'U'
  const first = authStore.user.first_name?.[0] || ''
  const last = authStore.user.last_name?.[0] || ''
  return (first + last).toUpperCase() || 'U'
})

function handleLogout() {
  profileDropdownOpen.value = false
  authStore.logout()
  router.push('/login')
}

function onClickOutside(event: MouseEvent) {
  if (profileDropdownRef.value && !profileDropdownRef.value.contains(event.target as Node)) {
    profileDropdownOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', onClickOutside)
  if (authStore.isAuthenticated) {
    profilesStore.fetchProfile().catch(() => {})
  }
})
onUnmounted(() => {
  document.removeEventListener('click', onClickOutside)
})
</script>
