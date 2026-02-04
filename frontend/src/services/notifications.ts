import api from './api'
import { AxiosResponse } from 'axios'

export interface NotificationItem {
  id: string
  recipient: string
  title: string
  message: string
  link: string
  actor: string | null
  actor_email?: string | null
  read: boolean
  read_at: string | null
  created_at: string
}

export interface PaginatedNotifications {
  count: number
  next: string | null
  previous: string | null
  results: NotificationItem[]
}

export const notificationsService = {
  list(params?: { page?: number; page_size?: number }): Promise<AxiosResponse<NotificationItem[] | PaginatedNotifications>> {
    return api.get('/notifications/', { params })
  },
  get(id: string): Promise<AxiosResponse<NotificationItem>> {
    return api.get(`/notifications/${id}/`)
  },
  markRead(id: string, read: boolean = true): Promise<AxiosResponse<NotificationItem>> {
    return api.patch(`/notifications/${id}/`, { read })
  },
  markAllRead(): Promise<AxiosResponse<{ marked: number }>> {
    return api.post('/notifications/mark-all-read/')
  },
}






