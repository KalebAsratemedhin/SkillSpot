<template>
  <AppLayout>
    <div class="w-full max-w-[800px] mx-auto px-4 md:px-6 py-8 md:py-10">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <h1 class="text-2xl md:text-3xl font-bold text-midnight">Notifications</h1>
        <Button
          v-if="notificationsStore.unreadCount > 0"
          variant="outline"
          size="default"
          class="shrink-0"
          :disabled="notificationsStore.loading"
          @click="handleMarkAllRead"
        >
          Mark all as read
        </Button>
      </div>

      <div v-if="notificationsStore.loading && notificationsStore.list.length === 0" class="flex justify-center py-12">
        <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
      </div>

      <div v-else-if="notificationsStore.error" class="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700 text-sm">
        {{ notificationsStore.error }}
      </div>

      <div v-else-if="notificationsStore.list.length === 0" class="text-center py-16 rounded-xl border border-slate-200 bg-slate-50">
        <span class="material-symbols-outlined text-5xl text-slate-400">notifications</span>
        <p class="text-slate-600 mt-4">No notifications yet</p>
        <p class="text-slate-500 text-sm mt-1">When you get notifications, they’ll show up here.</p>
      </div>

      <ul v-else class="space-y-2">
        <li
          v-for="n in notificationsStore.list"
          :key="n.id"
          :class="[
            'rounded-xl border p-4 transition-colors cursor-pointer',
            n.read
              ? 'bg-white border-slate-200 hover:border-slate-300'
              : 'bg-amber/5 border-amber/20 hover:border-amber/30'
          ]"
          @click="handleNotificationClick(n)"
        >
          <div class="flex items-start gap-3">
            <div
              :class="[
                'shrink-0 size-10 rounded-full flex items-center justify-center',
                n.read ? 'bg-slate-100 text-slate-500' : 'bg-amber/20 text-amber'
              ]"
            >
              <span class="material-symbols-outlined text-xl">notifications</span>
            </div>
            <div class="min-w-0 flex-1">
              <p class="font-semibold text-midnight">{{ n.title }}</p>
              <p v-if="n.message" class="text-slate-600 text-sm mt-0.5">{{ n.message }}</p>
              <p class="text-slate-500 text-xs mt-2">{{ formatDate(n.created_at) }}</p>
            </div>
            <span v-if="!n.read" class="shrink-0 size-2.5 rounded-full bg-amber"></span>
          </div>
        </li>
      </ul>

      <PaginationBar
        v-if="notificationsStore.totalCount > 0"
        :current-page="currentPage"
        :total-pages="totalPages"
        :total-count="notificationsStore.totalCount"
        :page-size="pageSize"
        :loading="notificationsStore.loading"
        @go-to-page="goToPage"
        @update-page-size="onPageSizeChange"
      />
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationsStore } from '@/stores/notifications'
import type { NotificationItem } from '@/services/notifications'
import AppLayout from '@/components/AppLayout.vue'
import PaginationBar from '@/components/PaginationBar.vue'

const router = useRouter()
const notificationsStore = useNotificationsStore()
const currentPage = ref(1)
const pageSize = ref(10)

const totalPages = computed(() => Math.max(1, Math.ceil(notificationsStore.totalCount / pageSize.value)))

async function goToPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  await notificationsStore.fetchNotifications(page, pageSize.value)
}

function onPageSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  notificationsStore.fetchNotifications(1, pageSize.value)
}

function formatDate(iso: string) {
  try {
    const d = new Date(iso)
    const now = new Date()
    const diffMs = now.getTime() - d.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return d.toLocaleDateString()
  } catch {
    return ''
  }
}

function handleNotificationClick(n: NotificationItem) {
  if (!n.read) {
    notificationsStore.markRead(n.id, true).catch(() => {})
  }
  if (n.link) {
    if (n.link.startsWith('http')) {
      window.location.href = n.link
    } else {
      router.push(n.link)
    }
  }
}

async function handleMarkAllRead() {
  await notificationsStore.markAllRead().catch(() => {})
}

onMounted(() => {
  currentPage.value = 1
  notificationsStore.fetchNotifications(1, pageSize.value).catch(() => {})
})
</script>

