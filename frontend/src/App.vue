<template>
  <Toaster position="top-right" richColors closeButton />
  <router-view />
</template>

<script setup lang="ts">
import { watch } from 'vue'
import { Toaster } from 'vue-sonner'
import { useAuthStore } from '@/stores/auth'
import { useMessagingStore } from '@/stores/messaging'

const authStore = useAuthStore()
const messagingStore = useMessagingStore()

watch(
  () => authStore.isAuthenticated,
  async (authed) => {
    if (authed) {
      await messagingStore.fetchUnreadCount()
      await messagingStore.connectInbox()
      return
    }
    messagingStore.disconnectInbox()
    messagingStore.disconnectChat()
  },
  { immediate: true }
)
</script>
