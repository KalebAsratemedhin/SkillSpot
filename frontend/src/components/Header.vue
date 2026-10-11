<template>
  <header class="sticky top-0 z-50 w-full border-b border-white/10 bg-midnight/95 backdrop-blur-md px-4 md:px-6 lg:px-20 py-3 md:py-4 text-white">
    <div class="mx-auto flex max-w-[1400px] items-center justify-between">
      <router-link to="/" class="flex items-center gap-2 md:gap-3 no-underline text-inherit">
        <div class="text-amber">
          <svg class="size-7 md:size-9" fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
            <path d="M44 11.2727C44 14.0109 39.8386 16.3957 33.69 17.6364C39.8386 18.877 44 21.2618 44 24C44 26.7382 39.8386 29.123 33.69 30.3636C39.8386 31.6043 44 33.9891 44 36.7273C44 40.7439 35.0457 44 24 44C12.9543 44 4 40.7439 4 36.7273C4 33.9891 8.16144 31.6043 14.31 30.3636C8.16144 29.123 4 26.7382 4 24C4 21.2618 8.16144 18.877 14.31 17.6364C8.16144 16.3957 4 14.0109 4 11.2727C4 7.25611 12.9543 4 24 4C35.0457 4 44 7.25611 44 11.2727Z" fill="currentColor"></path>
          </svg>
        </div>
        <h2 class="text-lg md:text-2xl font-extrabold leading-tight tracking-tight uppercase italic">SkillSpot</h2>
      </router-link>
      <nav v-if="authStore.isAuthenticated" class="hidden lg:flex flex-1 justify-center gap-6 xl:gap-10 items-center">
        <div class="relative group">
          <button type="button" class="text-sm font-semibold hover:text-amber transition-colors flex items-center gap-1">
            Jobs
            <span class="material-symbols-outlined text-base">expand_more</span>
          </button>
          <div class="absolute left-0 top-full pt-1 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
            <div class="rounded-lg border border-white/10 bg-midnight/95 backdrop-blur-md shadow-xl py-1 min-w-[160px]">
              <router-link to="/browse" class="block px-4 py-2 text-sm font-medium hover:bg-white/10 hover:text-amber transition-colors">Browse</router-link>
              <router-link
                v-if="authStore.isClient"
                to="/jobs"
                class="block px-4 py-2 text-sm font-medium hover:bg-white/10 hover:text-amber transition-colors"
              >
                My Jobs
              </router-link>
              <router-link
                v-if="authStore.isProvider"
                to="/applications"
                class="block px-4 py-2 text-sm font-medium hover:bg-white/10 hover:text-amber transition-colors"
              >
                Requests
              </router-link>
            </div>
          </div>
        </div>
        <router-link to="/messages" class="relative text-sm font-semibold hover:text-amber transition-colors">
          Messages
          <span
            v-if="messagingStore.unreadCount > 0"
            class="absolute -top-2 -right-4 min-w-[1.1rem] h-[1.1rem] px-1 rounded-full bg-amber text-midnight text-[9px] font-black flex items-center justify-center"
          >
            {{ messagingStore.unreadCount > 99 ? '99+' : messagingStore.unreadCount }}
          </span>
        </router-link>
        <div class="relative group">
          <button type="button" class="text-sm font-semibold hover:text-amber transition-colors flex items-center gap-1">
            Contracts & Payments
            <span class="material-symbols-outlined text-base">expand_more</span>
          </button>
          <div class="absolute left-0 top-full pt-1 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
            <div class="rounded-lg border border-white/10 bg-midnight/95 backdrop-blur-md shadow-xl py-1 min-w-[180px]">
              <router-link to="/contracts" class="block px-4 py-2 text-sm font-medium hover:bg-white/10 hover:text-amber transition-colors">Contracts</router-link>
              <router-link to="/payments" class="block px-4 py-2 text-sm font-medium hover:bg-white/10 hover:text-amber transition-colors">Payments</router-link>
            </div>
          </div>
        </div>
      </nav>
      <nav v-else class="hidden md:flex flex-1 justify-center gap-8 items-center">
        <router-link to="/browse" class="text-sm font-semibold hover:text-amber transition-colors">Browse</router-link>
      </nav>
      <div class="flex items-center gap-2 sm:gap-4 md:gap-6">
        <template v-if="authStore.isAuthenticated">
          <router-link v-if="authStore.isClient" to="/jobs/create" class="hidden sm:block">
            <Button variant="default" size="default" class="min-w-[100px] md:min-w-[120px] h-10 md:h-11 px-4 md:px-5 text-sm rounded-lg shadow-[0_4px_14px_0_rgba(245,158,11,0.39)] active:scale-95">
              Post a Job
            </Button>
          </router-link>
          <router-link
            to="/notifications"
            class="relative hidden sm:flex items-center justify-center rounded-lg h-10 w-10 md:h-11 md:w-11 bg-midnight-light text-slate-300 hover:text-white transition-colors"
            aria-label="Notifications"
          >
            <span class="material-symbols-outlined text-[20px] md:text-[22px]">notifications</span>
            <span
              v-if="notificationsStore.unreadCount > 0"
              class="absolute top-1.5 right-1.5 size-2 rounded-full bg-amber"
            />
          </router-link>
          <div ref="avatarMenuRef" class="relative">
            <button
              type="button"
              class="size-8 md:size-10 rounded-full border-2 border-midnight-light overflow-hidden focus:outline-none focus-visible:ring-2 focus-visible:ring-amber p-0"
              aria-haspopup="menu"
              :aria-expanded="avatarMenuOpen"
              @click="avatarMenuOpen = !avatarMenuOpen"
            >
              <UserAvatar
                :src="userAvatarUrl"
                :name="userDisplayName"
                size-class="size-full"
                rounded-class="rounded-full"
                fallback-class="bg-amber text-midnight"
                text-class="text-sm md:text-base"
              />
            </button>
            <div
              v-if="avatarMenuOpen"
              class="absolute right-0 top-full mt-2 z-50 min-w-[180px] rounded-lg border border-white/10 bg-midnight/95 backdrop-blur-md shadow-xl py-1"
              role="menu"
            >
              <router-link
                to="/profile"
                class="flex items-center gap-2 px-4 py-2.5 text-sm font-medium hover:bg-white/10 hover:text-amber transition-colors"
                role="menuitem"
                @click="avatarMenuOpen = false"
              >
                <span class="material-symbols-outlined text-base">person</span>
                Profile
              </router-link>
              <button
                type="button"
                class="flex w-full items-center gap-2 px-4 py-2.5 text-sm font-medium text-left hover:bg-white/10 hover:text-amber transition-colors"
                role="menuitem"
                :disabled="loggingOut"
                @click="handleLogout"
              >
                <span class="material-symbols-outlined text-base">logout</span>
                {{ loggingOut ? 'Logging out…' : 'Log out' }}
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
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { onClickOutside } from '@vueuse/core'
import { useAuthStore } from '@/stores/auth'
import { useMessagingStore } from '@/stores/messaging'
import { useNotificationsStore } from '@/stores/notifications'
import { useProfilesStore } from '@/stores/profiles'
import Button from './ui/Button.vue'
import UserAvatar from './UserAvatar.vue'

const authStore = useAuthStore()
const messagingStore = useMessagingStore()
const notificationsStore = useNotificationsStore()
const profilesStore = useProfilesStore()
const router = useRouter()
const avatarMenuOpen = ref(false)
const avatarMenuRef = ref<HTMLElement | null>(null)
const loggingOut = ref(false)

onClickOutside(avatarMenuRef, () => {
  avatarMenuOpen.value = false
})

const userDisplayName = computed(() => {
  const p = profilesStore.profile
  if (p?.first_name || p?.last_name) {
    return `${p.first_name || ''} ${p.last_name || ''}`.trim()
  }
  const u = authStore.user
  if (!u) return 'User'
  const name = `${u.first_name || ''} ${u.last_name || ''}`.trim()
  return name || u.email || 'User'
})

const userAvatarUrl = computed(() => {
  return profilesStore.profile?.avatar || (authStore.user as { avatar?: string } | null)?.avatar || null
})

watch(
  () => authStore.isAuthenticated,
  (authed) => {
    if (authed && !profilesStore.profile) {
      profilesStore.fetchProfile().catch(() => {})
    }
  },
  { immediate: true }
)

async function handleLogout() {
  if (loggingOut.value) return
  loggingOut.value = true
  try {
    await authStore.logout()
    avatarMenuOpen.value = false
    await router.push('/login')
  } finally {
    loggingOut.value = false
  }
}
</script>
