import { defineStore } from 'pinia'
import { ref } from 'vue'
import { messagingService, type Conversation, type Message, type CreateConversationPayload } from '@/services/messaging'

export const useMessagingStore = defineStore('messaging', () => {
  const conversations = ref<Conversation[]>([])
  const currentConversation = ref<Conversation | null>(null)
  const messages = ref<Message[]>([])
  const unreadCount = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchConversations() {
    try {
      loading.value = true
      error.value = null
      const response = await messagingService.listConversations()
      conversations.value = response.data.results || []
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch conversations'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchConversation(id: string, markRead = true) {
    try {
      loading.value = true
      error.value = null
      const response = await messagingService.getConversation(id)
      currentConversation.value = response.data
      await fetchMessages(id, markRead)
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch conversation'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createConversation(data: CreateConversationPayload) {
    try {
      loading.value = true
      error.value = null
      const response = await messagingService.createConversation(data)
      conversations.value.push(response.data)
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to create conversation'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchMessages(conversationId: string, markRead = false) {
    try {
      loading.value = true
      error.value = null
      const response = await messagingService.getMessages(conversationId, markRead ? { mark_read: true } : undefined)
      messages.value = response.data.results || []
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch messages'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function sendMessage(conversationId: string, content: string) {
    try {
      loading.value = true
      error.value = null
      const response = await messagingService.sendMessage(conversationId, { content })
      messages.value.push(response.data)
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to send message'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function markAsRead(conversationId: string) {
    try {
      await messagingService.markRead(conversationId)
      await fetchUnreadCount()
      const conv = conversations.value.find(c => c.id === conversationId)
      if (conv) {
        conv.unread_count = 0
      }
    } catch (err) {
      console.error('Failed to mark as read:', err)
    }
  }

  async function fetchUnreadCount() {
    try {
      const response = await messagingService.getUnreadCount()
      unreadCount.value = response.data.total_unread ?? response.data.count ?? 0
    } catch (err) {
      console.error('Failed to fetch unread count:', err)
    }
  }

  return {
    conversations,
    currentConversation,
    messages,
    unreadCount,
    loading,
    error,
    fetchConversations,
    fetchConversation,
    createConversation,
    fetchMessages,
    sendMessage,
    markAsRead,
    fetchUnreadCount,
  }
})
