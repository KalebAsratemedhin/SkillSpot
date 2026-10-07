import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  notificationsService,
  type NotificationItem,
  type PaginatedNotifications,
} from '@/services/notifications'

type NotificationCreatedFrame = {
  type: 'notification_created'
  notification: NotificationItem
  unread_count: number
}

type NotificationUpdatedFrame = {
  type: 'notification_updated'
  notification: NotificationItem
  unread_count: number
}

type NotificationsReadFrame = {
  type: 'notifications_read'
  marked?: number
  unread_count: number
}

export type NotificationInboxFrame =
  | NotificationCreatedFrame
  | NotificationUpdatedFrame
  | NotificationsReadFrame

export const useNotificationsStore = defineStore('notifications', () => {
  const list = ref<NotificationItem[]>([])
  const totalCount = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)
  /** Prefer server push count over counting a partial local page. */
  const serverUnreadCount = ref<number | null>(null)

  const unreadCount = computed(() => {
    if (serverUnreadCount.value != null) return serverUnreadCount.value
    return list.value.filter((n) => !n.read).length
  })

  function setUnreadFromServer(count: number) {
    if (typeof count === 'number' && Number.isFinite(count)) {
      serverUnreadCount.value = Math.max(0, count)
    }
  }

  function setFromResponse(data: NotificationItem[] | PaginatedNotifications) {
    list.value = Array.isArray(data) ? data : (data?.results ?? [])
    if (!Array.isArray(data) && data && 'count' in data) {
      totalCount.value = data.count ?? 0
    } else {
      totalCount.value = list.value.length
    }
    // Seed badge from loaded page until a live unread_count arrives.
    if (serverUnreadCount.value == null) {
      serverUnreadCount.value = list.value.filter((n) => !n.read).length
    }
  }

  function prependNotification(item: NotificationItem) {
    if (!item?.id) return
    if (list.value.some((n) => n.id === item.id)) {
      list.value = list.value.map((n) => (n.id === item.id ? item : n))
      return
    }
    list.value = [item, ...list.value]
    totalCount.value += 1
  }

  function patchNotification(item: NotificationItem) {
    if (!item?.id) return
    const idx = list.value.findIndex((n) => n.id === item.id)
    if (idx >= 0) {
      const next = list.value.slice()
      next[idx] = item
      list.value = next
    }
  }

  function markAllLocalRead() {
    const now = new Date().toISOString()
    list.value = list.value.map((n) =>
      n.read ? n : { ...n, read: true, read_at: n.read_at || now }
    )
  }

  /** Inbox WS frames: notification_created | notification_updated | notifications_read */
  function handleInboxFrame(frame: NotificationInboxFrame) {
    if (!frame?.type) return
    if (frame.type === 'notification_created') {
      prependNotification(frame.notification)
      setUnreadFromServer(frame.unread_count)
      return
    }
    if (frame.type === 'notification_updated') {
      patchNotification(frame.notification)
      setUnreadFromServer(frame.unread_count)
      return
    }
    if (frame.type === 'notifications_read') {
      markAllLocalRead()
      setUnreadFromServer(frame.unread_count)
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
    // Live frame will set authoritative unread_count; optimistic tweak if offline.
    if (serverUnreadCount.value != null) {
      serverUnreadCount.value = Math.max(
        0,
        serverUnreadCount.value + (read ? -1 : 1)
      )
    }
    return item.data
  }

  async function markAllRead() {
    await notificationsService.markAllRead()
    markAllLocalRead()
    serverUnreadCount.value = 0
  }

  function reset() {
    list.value = []
    totalCount.value = 0
    serverUnreadCount.value = null
    error.value = null
  }

  return {
    list,
    totalCount,
    loading,
    error,
    unreadCount,
    serverUnreadCount,
    fetchNotifications,
    markRead,
    markAllRead,
    setFromResponse,
    handleInboxFrame,
    reset,
  }
})
