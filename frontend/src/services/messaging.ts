import api from './api'
import { AxiosResponse } from 'axios'

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface Conversation {
  id: string
  participant1?: string
  participant1_name?: string
  participant2?: string
  participant2_name?: string
  other_participant?: { id: string; email: string; name: string }
  participants?: string[]
  job?: string
  job_title?: string
  contract?: string
  last_message?: { id: string; content: string; sender_email?: string; created_at: string }
  unread_count: number
  created_at: string
  updated_at: string
  last_message_at?: string
}

/** Payload for creating a conversation (backend: participant2_id, job_id?, initial_message?) */
export interface CreateConversationPayload {
  participant2_id: string
  job_id?: string
  initial_message?: string
}

export interface Message {
  id: string
  conversation: string
  sender: string
  content: string
  is_read: boolean
  created_at: string
}

export const messagingService = {
  listConversations(): Promise<AxiosResponse<PaginatedResponse<Conversation>>> {
    return api.get('/messaging/conversations/')
  },
  getConversation(id: string): Promise<AxiosResponse<Conversation>> {
    return api.get(`/messaging/conversations/${id}/`)
  },
  createConversation(data: CreateConversationPayload): Promise<AxiosResponse<Conversation>> {
    return api.post('/messaging/conversations/', data)
  },
  getMessages(conversationId: string, params?: { mark_read?: boolean }): Promise<AxiosResponse<PaginatedResponse<Message>>> {
    return api.get(`/messaging/conversations/${conversationId}/messages/`, { params })
  },
  sendMessage(conversationId: string, data: { content: string }): Promise<AxiosResponse<Message>> {
    return api.post(`/messaging/conversations/${conversationId}/messages/`, data)
  },
  getMessage(id: string): Promise<AxiosResponse<Message>> {
    return api.get(`/messaging/messages/${id}/`)
  },
  markRead(conversationId: string): Promise<AxiosResponse> {
    return api.post(`/messaging/conversations/${conversationId}/mark-read/`)
  },
  getUnreadCount(): Promise<AxiosResponse<{ total_unread?: number; count?: number }>> {
    return api.get('/messaging/conversations/unread-count/')
  },
}
