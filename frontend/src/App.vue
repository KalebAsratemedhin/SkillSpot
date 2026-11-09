<template>
  <Toaster position="top-right" richColors closeButton />

  <router-view v-slot="{ Component }">
    <Suspense>
      <component :is="Component" />
      <template #fallback>
        <div class="min-h-screen bg-slate-50">
          <div class="h-16 bg-midnight" />
          <div class="mx-auto max-w-[1400px] px-4 md:px-6 lg:px-10 py-10 space-y-4 animate-pulse">
            <div class="h-8 w-48 bg-slate-200 rounded-lg" />
            <div class="h-4 w-72 bg-slate-200 rounded" />
            <div class="h-40 bg-slate-200 rounded-2xl" />
          </div>
        </div>
      </template>
    </Suspense>
  </router-view>
</template>

<script setup lang="ts">
import { watch } from 'vue'
import { Toaster } from 'vue-sonner'
import { useAuthStore } from '@/stores/auth'
import { useMessagingStore } from '@/stores/messaging'
import { useNotificationsStore } from '@/stores/notifications'

const authStore = useAuthStore()
const messagingStore = useMessagingStore()
const notificationsStore = useNotificationsStore()

watch(
  () => authStore.isAuthenticated,
  async (authed) => {
    if (authed) {
      await messagingStore.fetchUnreadCount()
      await messagingStore.connectInbox()
      notificationsStore.fetchNotifications(1, 20).catch(() => {})
      return
    }
    messagingStore.disconnectInbox()
    messagingStore.disconnectChat()
    notificationsStore.reset()
  },
  { immediate: true }
)
</script>
