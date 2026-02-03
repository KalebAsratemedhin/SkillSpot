import { defineStore } from 'pinia'
import { ref } from 'vue'
import { messagingService, type Conversation, type Message, type CreateConversationPayload } from '@/services/messaging'

function getWsBaseUrl(): string {
  const api = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
  const u = api.replace(/\/api\/v1\/?$/, '').trim()
  return (u.startsWith('https') ? 'wss:' : 'ws:') + u.replace(/^https?:\/\//, '//')
}

export const useMessagingStore = defineStore('messaging', () => {
  const conversations = ref<Conversation[]>([])
  const currentConversation = ref<Conversation | null>(null)
  const messages = ref<Message[]>([])
  const unreadCount = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const chatWs = ref<WebSocket | null>(null)
  const wsConnected = ref(false)

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

  function connectChat(conversationId: string) {
    disconnectChat()
    const token = localStorage.getItem('access_token')
    if (!token) return
    const base = getWsBaseUrl()
    const url = `${base}/ws/chat/${conversationId}/?token=${encodeURIComponent(token)}`
    const ws = new WebSocket(url)
    chatWs.value = ws
    ws.onopen = () => { wsConnected.value = true }
    ws.onclose = () => {
      wsConnected.value = false
      chatWs.value = null
    }
    ws.onerror = () => { wsConnected.value = false }
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as Message
        if (data?.id && data?.content != null) {
          if (!messages.value.some((m) => m.id === data.id)) {
            messages.value = [...messages.value, data]
          }
        }
      } catch {
        // ignore parse errors
      }
    }
  }

  function disconnectChat() {
    if (chatWs.value) {
      chatWs.value.close()
      chatWs.value = null
    }
    wsConnected.value = false
  }

  function sendMessageViaWs(content: string): boolean {
    const ws = chatWs.value
    if (!ws || ws.readyState !== WebSocket.OPEN) return false
    ws.send(JSON.stringify({ type: 'send_message', content }))
    return true
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
    chatWs,
    wsConnected,
    fetchConversations,
    fetchConversation,
    createConversation,
    fetchMessages,
    sendMessage,
    sendMessageViaWs,
    connectChat,
    disconnectChat,
    markAsRead,
    fetchUnreadCount,
  }
})
