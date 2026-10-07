<template>
  <Toaster position="top-right" richColors closeButton />
  <router-view />
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
