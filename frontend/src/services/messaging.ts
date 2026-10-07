import api from './api'
import { AxiosResponse } from 'axios'

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface MessageAttachment {
  id: string
  file: string | null
  file_name: string
  file_size: number
  file_type?: string
  created_at?: string
}

export interface Conversation {
  id: string
  participant1?: string
  participant1_name?: string
  participant2?: string
  participant2_name?: string
  other_participant?: {
    id: string
    email: string
    name: string
    is_online?: boolean
    last_seen_at?: string | null
  }
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

/** Payload for creating a conversation — one thread per user pair (no per-job rooms). */
export interface CreateConversationPayload {
  participant2_id: string
  /** @deprecated Ignored — rooms are per pair only. Kept optional for older callers. */
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
  sender_name?: string
  sender_email?: string
  attachments?: MessageAttachment[]
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
  getMessages(
    conversationId: string,
    params?: { mark_read?: boolean; page?: number; page_size?: number }
  ): Promise<AxiosResponse<PaginatedResponse<Message>>> {
    return api.get(`/messaging/conversations/${conversationId}/messages/`, { params })
  },
  sendMessage(conversationId: string, data: { content: string }): Promise<AxiosResponse<Message>> {
    return api.post(`/messaging/conversations/${conversationId}/messages/`, data)
  },
  sendMessageWithFiles(
    conversationId: string,
    data: { content?: string; files?: File[] }
  ): Promise<AxiosResponse<Message>> {
    const form = new FormData()
    const text = (data.content ?? '').trim()
    if (text) form.append('content', text)
    else form.append('content', '')
    for (const file of data.files ?? []) {
      form.append('files', file)
    }
    return api.post(`/messaging/conversations/${conversationId}/messages/`, form)
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
