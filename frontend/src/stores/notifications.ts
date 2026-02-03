import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  notificationsService,
  type NotificationItem,
  type PaginatedNotifications,
} from '@/services/notifications'

export const useNotificationsStore = defineStore('notifications', () => {
  const list = ref<NotificationItem[]>([])
  const totalCount = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const unreadCount = computed(() => list.value.filter((n) => !n.read).length)

  function setFromResponse(data: NotificationItem[] | PaginatedNotifications) {
    list.value = Array.isArray(data) ? data : (data?.results ?? [])
    if (!Array.isArray(data) && data && 'count' in data) {
      totalCount.value = data.count ?? 0
    } else {
      totalCount.value = list.value.length
    }
  }

  async function fetchNotifications(page = 1, pageSize = 10) {
    try {
      loading.value = true
      error.value = null
      const response = await notificationsService.list({ page, page_size: pageSize })
      const data = response.data
      setFromResponse(data as PaginatedNotifications)
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to load notifications'
      list.value = []
      totalCount.value = 0
      throw err
    } finally {
      loading.value = false
    }
  }

  async function markRead(id: string, read: boolean = true) {
    const item = await notificationsService.markRead(id, read)
    const idx = list.value.findIndex((n) => n.id === id)
    if (idx !== -1) list.value[idx] = item.data
    return item.data
  }

  async function markAllRead() {
    await notificationsService.markAllRead()
    list.value = list.value.map((n) => ({ ...n, read: true, read_at: new Date().toISOString() }))
  }

  return {
    list,
    totalCount,
    loading,
    error,
    unreadCount,
    fetchNotifications,
    markRead,
    markAllRead,
    setFromResponse,
  }
})



