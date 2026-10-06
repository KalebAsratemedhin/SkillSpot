import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authService } from '@/services/auth'
import {
  messagingService,
  type Conversation,
  type Message,
  type CreateConversationPayload,
} from '@/services/messaging'
import { useAuthStore } from '@/stores/auth'

function getWsBaseUrl(): string {
  const api = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
  const u = api.replace(/\/api\/v1\/?$/, '').trim()
  return (u.startsWith('https') ? 'wss:' : 'ws:') + u.replace(/^https?:\/\//, '//')
}

function redactWsUrl(url: string): string {
  return url.replace(/([?&]token=)[^&]*/i, '$1***')
}

type EchoWaiter = {
  content: string
  resolve: (msg: Message | null) => void
  timer: ReturnType<typeof setTimeout>
}

type InboxConversationSlice = {
  id: string
  last_message?: Conversation['last_message'] | null
  last_message_at?: string | null
  unread_count: number
  updated_at?: string
}

type InboxUpdatePayload = {
  type: 'inbox_update'
  event?: 'conversation_updated' | 'conversation_read' | string
  conversation: InboxConversationSlice
  total_unread: number
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
  const inboxWsConnected = ref(false)

  let activeConversationId: string | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let reconnectAttempts = 0
  /** Bumped on every new connect/disconnect; stale socket handlers must no-op. */
  let connectGeneration = 0
  let connectInFlight: Promise<boolean> | null = null
  let connectInFlightId: string | null = null
  const echoWaiters: EchoWaiter[] = []

  // Inbox socket (singleton while logged in)
  let inboxWs: WebSocket | null = null
  let inboxGeneration = 0
  let inboxReconnectTimer: ReturnType<typeof setTimeout> | null = null
  let inboxReconnectAttempts = 0
  let inboxDesired = false
  let inboxConnectInFlight: Promise<boolean> | null = null
  let inboxFetchMissingInFlight = false

  function clearEchoWaiters() {
    while (echoWaiters.length) {
      const w = echoWaiters.shift()!
      clearTimeout(w.timer)
      w.resolve(null)
    }
  }

  function appendMessage(msg: Message) {
    if (!msg?.id) return

    const tempIdx = messages.value.findIndex(
      (m) =>
        String(m.id).startsWith('temp-') &&
        m.content === msg.content &&
        (!msg.sender || !m.sender || m.sender === msg.sender)
    )
    if (tempIdx >= 0) {
      const next = messages.value.slice()
      next[tempIdx] = msg
      messages.value = next
      return
    }

    if (messages.value.some((m) => m.id === msg.id)) return
    messages.value = [...messages.value, msg]
  }

  function removeMessageById(id: string) {
    messages.value = messages.value.filter((m) => m.id !== id)
  }

  function notifyEcho(msg: Message) {
    if (String(msg.id).startsWith('temp-')) return
    const i = echoWaiters.findIndex((w) => w.content === msg.content)
    if (i < 0) return
    const [w] = echoWaiters.splice(i, 1)
    clearTimeout(w.timer)
    w.resolve(msg)
  }

  function waitForEcho(content: string, ms: number): Promise<Message | null> {
    return new Promise((resolve) => {
      const timer = setTimeout(() => {
        const idx = echoWaiters.findIndex((w) => w.timer === timer)
        if (idx >= 0) echoWaiters.splice(idx, 1)
        resolve(null)
      }, ms)
      echoWaiters.push({ content, resolve, timer })
    })
  }

  async function refreshAccessToken(): Promise<string | null> {
    const refresh = localStorage.getItem('refresh_token')
    if (!refresh) return null
    try {
      const { data } = await authService.refreshToken(refresh)
      localStorage.setItem('access_token', data.access)
      try {
        const auth = useAuthStore()
        auth.accessToken = data.access
      } catch {
        // Pinia may be unavailable in edge cases
      }
      return data.access
    } catch {
      return null
    }
  }

  function clearReconnectTimer() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  function scheduleReconnect(conversationId: string, closeCode?: number, forGeneration?: number) {
    // Ignore closes from superseded sockets.
    if (forGeneration != null && forGeneration !== connectGeneration) return
    if (activeConversationId !== conversationId) return
    if (reconnectTimer) return
    if (reconnectAttempts > 8) {
      if (import.meta.env.DEV) {
        console.warn('[chat-ws] giving up reconnect after', reconnectAttempts, 'attempts')
      }
      return
    }

    const attempt = reconnectAttempts
    reconnectAttempts += 1
    const delay = Math.min(1000 * 2 ** attempt, 15000)

    reconnectTimer = setTimeout(async () => {
      reconnectTimer = null
      if (activeConversationId !== conversationId) return
      if (closeCode === 4401 || attempt > 0) {
        await refreshAccessToken()
      }
      await connectChat(conversationId)
    }, delay)
  }

  async function fetchConversations(options?: { silent?: boolean }) {
    const silent = options?.silent === true
    try {
      if (!silent) {
        loading.value = true
        error.value = null
      }
      const response = await messagingService.listConversations()
      conversations.value = response.data.results || []
    } catch (err: any) {
      if (!silent) {
        error.value = err.response?.data?.detail || 'Failed to fetch conversations'
        throw err
      }
      if (import.meta.env.DEV) {
        console.warn('[inbox-ws] silent conversation refresh failed', err)
      }
    } finally {
      if (!silent) loading.value = false
    }
  }

  function patchConversationFromInbox(slice: InboxConversationSlice) {
    const id = String(slice.id)
    const idx = conversations.value.findIndex((c) => c.id === id)
    if (idx < 0) return false

    const prev = conversations.value[idx]
    const next: Conversation = {
      ...prev,
      unread_count: slice.unread_count ?? prev.unread_count ?? 0,
      last_message:
        slice.last_message === undefined
          ? prev.last_message
          : slice.last_message || undefined,
      last_message_at:
        slice.last_message_at === undefined
          ? prev.last_message_at
          : slice.last_message_at || undefined,
      updated_at: slice.updated_at || prev.updated_at,
    }

    const list = conversations.value.slice()
    list.splice(idx, 1)
    list.unshift(next)
    conversations.value = list

    if (currentConversation.value?.id === id) {
      currentConversation.value = { ...currentConversation.value, ...next }
    }
    return true
  }

  async function applyInboxUpdate(payload: InboxUpdatePayload) {
    if (typeof payload.total_unread === 'number') {
      unreadCount.value = payload.total_unread
    }

    const slice = payload.conversation
    if (!slice?.id) return

    const patched = patchConversationFromInbox(slice)
    if (patched) return

    if (inboxFetchMissingInFlight) return
    inboxFetchMissingInFlight = true
    try {
      await fetchConversations({ silent: true })
    } finally {
      inboxFetchMissingInFlight = false
    }
  }

  function clearInboxReconnectTimer() {
    if (inboxReconnectTimer) {
      clearTimeout(inboxReconnectTimer)
      inboxReconnectTimer = null
    }
  }

  function scheduleInboxReconnect(closeCode?: number, forGeneration?: number) {
    if (forGeneration != null && forGeneration !== inboxGeneration) return
    if (!inboxDesired) return
    if (inboxReconnectTimer) return
    if (inboxReconnectAttempts > 8) {
      if (import.meta.env.DEV) {
        console.warn('[inbox-ws] giving up reconnect after', inboxReconnectAttempts, 'attempts')
      }
      return
    }

    const attempt = inboxReconnectAttempts
    inboxReconnectAttempts += 1
    const delay = Math.min(1000 * 2 ** attempt, 15000)

    inboxReconnectTimer = setTimeout(async () => {
      inboxReconnectTimer = null
      if (!inboxDesired) return
      if (closeCode === 4401 || attempt > 0) {
        await refreshAccessToken()
      }
      await connectInbox()
    }, delay)
  }

  /**
   * Connect once while logged in. Push-only — list + badge updates.
   * Keep the per-chat socket separately for the open thread.
   */
  async function connectInbox(): Promise<boolean> {
    inboxDesired = true

    if (inboxWs?.readyState === WebSocket.OPEN) {
      inboxWsConnected.value = true
      return true
    }
    if (inboxConnectInFlight) return inboxConnectInFlight

    const generation = ++inboxGeneration
    clearInboxReconnectTimer()

    const previous = inboxWs
    inboxWs = null
    inboxWsConnected.value = false
    if (previous) {
      try {
        previous.onclose = null
        previous.onerror = null
        previous.onmessage = null
        previous.onopen = null
        previous.close()
      } catch {
        // ignore
      }
    }

    let token = localStorage.getItem('access_token')
    if (!token) token = await refreshAccessToken()
    if (!token || generation !== inboxGeneration || !inboxDesired) return false

    const url = `${getWsBaseUrl()}/ws/inbox/?token=${encodeURIComponent(token)}`
    if (import.meta.env.DEV) {
      console.info('[inbox-ws] connecting', redactWsUrl(url))
    }

    inboxConnectInFlight = new Promise((resolve) => {
      let settled = false
      const finish = (ok: boolean) => {
        if (settled) return
        settled = true
        clearTimeout(openTimer)
        resolve(ok)
      }

      const openTimer = setTimeout(() => {
        if (generation !== inboxGeneration) {
          finish(false)
          return
        }
        if (import.meta.env.DEV) {
          console.warn('[inbox-ws] open timeout', redactWsUrl(url))
        }
        finish(false)
      }, 5000)

      try {
        const ws = new WebSocket(url)
        if (generation !== inboxGeneration) {
          try {
            ws.close()
          } catch {
            // ignore
          }
          finish(false)
          return
        }
        inboxWs = ws

        ws.onopen = () => {
          if (generation !== inboxGeneration) {
            try {
              ws.close()
            } catch {
              // ignore
            }
            finish(false)
            return
          }
          inboxWsConnected.value = true
          inboxReconnectAttempts = 0
          if (import.meta.env.DEV) {
            console.info('[inbox-ws] open')
          }
          finish(true)
        }

        ws.onclose = (ev) => {
          if (generation !== inboxGeneration) return
          if (inboxWs === ws) {
            inboxWs = null
            inboxWsConnected.value = false
          }
          if (!settled) {
            if (import.meta.env.DEV) {
              console.warn('[inbox-ws] closed before open', ev.code, redactWsUrl(url))
            }
            finish(false)
          }
          if (inboxDesired && inboxWs == null) {
            scheduleInboxReconnect(ev.code, generation)
          }
        }

        ws.onerror = () => {
          if (generation !== inboxGeneration) return
          if (import.meta.env.DEV) {
            console.warn('[inbox-ws] error', redactWsUrl(url))
          }
        }

        ws.onmessage = (event) => {
          if (generation !== inboxGeneration) return
          try {
            const data = JSON.parse(event.data) as InboxUpdatePayload
            if (data?.type === 'inbox_update' && data.conversation) {
              void applyInboxUpdate(data)
            }
          } catch {
            // ignore parse errors
          }
        }
      } catch (err) {
        if (import.meta.env.DEV) {
          console.warn('[inbox-ws] construct failed', err)
        }
        finish(false)
      }
    })

    try {
      return await inboxConnectInFlight
    } finally {
      inboxConnectInFlight = null
    }
  }

  function disconnectInbox() {
    inboxDesired = false
    clearInboxReconnectTimer()
    inboxReconnectAttempts = 0
    inboxGeneration += 1
    inboxConnectInFlight = null
    const ws = inboxWs
    inboxWs = null
    inboxWsConnected.value = false
    if (ws) {
      try {
        ws.onclose = null
        ws.onerror = null
        ws.onmessage = null
        ws.onopen = null
        ws.close()
      } catch {
        // ignore
      }
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
      // One room per pair — never scope by job.
      const { job_id: _ignored, ...rest } = data
      const response = await messagingService.createConversation({
        participant2_id: rest.participant2_id,
        initial_message: rest.initial_message,
      })
      const conv = response.data
      if (conv?.id && !conversations.value.some((c) => c.id === conv.id)) {
        conversations.value.unshift(conv)
      }
      return conv
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
      const response = await messagingService.getMessages(
        conversationId,
        markRead ? { mark_read: true } : undefined
      )
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
      appendMessage(response.data)
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to send message'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function sendMessageWithFiles(
    conversationId: string,
    content: string,
    files: File[]
  ) {
    try {
      loading.value = true
      error.value = null
      const response = await messagingService.sendMessageWithFiles(conversationId, {
        content,
        files,
      })
      appendMessage(response.data)
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to send message'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Open (or reuse) the WS for a conversation. Resolves true when OPEN.
   */
  async function connectChat(conversationId: string): Promise<boolean> {
    if (
      activeConversationId === conversationId &&
      chatWs.value?.readyState === WebSocket.OPEN
    ) {
      wsConnected.value = true
      return true
    }

    // Coalesce concurrent connects for the same room.
    if (
      connectInFlight &&
      connectInFlightId === conversationId &&
      (chatWs.value?.readyState === WebSocket.CONNECTING ||
        chatWs.value?.readyState === WebSocket.OPEN)
    ) {
      return connectInFlight
    }

    const generation = ++connectGeneration
    clearReconnectTimer()
    clearEchoWaiters()

    const previous = chatWs.value
    chatWs.value = null
    wsConnected.value = false
    activeConversationId = conversationId

    // Close previous socket after bumping generation so its onclose is ignored.
    if (previous) {
      try {
        previous.onclose = null
        previous.onerror = null
        previous.onmessage = null
        previous.onopen = null
        previous.close()
      } catch {
        // ignore
      }
    }

    let token = localStorage.getItem('access_token')
    if (!token) {
      token = await refreshAccessToken()
    }
    if (!token || generation !== connectGeneration) return false

    const base = getWsBaseUrl()
    const url = `${base}/ws/chat/${conversationId}/?token=${encodeURIComponent(token)}`
    if (import.meta.env.DEV) {
      console.info('[chat-ws] connecting', redactWsUrl(url))
    }

    connectInFlightId = conversationId
    connectInFlight = new Promise((resolve) => {
      let settled = false
      const finish = (ok: boolean) => {
        if (settled) return
        settled = true
        clearTimeout(openTimer)
        resolve(ok)
      }

      const openTimer = setTimeout(() => {
        if (generation !== connectGeneration) {
          finish(false)
          return
        }
        if (import.meta.env.DEV) {
          console.warn('[chat-ws] open timeout', redactWsUrl(url))
        }
        finish(false)
      }, 5000)

      try {
        const ws = new WebSocket(url)
        if (generation !== connectGeneration) {
          try {
            ws.close()
          } catch {
            // ignore
          }
          finish(false)
          return
        }
        chatWs.value = ws

        ws.onopen = () => {
          if (generation !== connectGeneration) {
            try {
              ws.close()
            } catch {
              // ignore
            }
            finish(false)
            return
          }
          wsConnected.value = true
          reconnectAttempts = 0
          if (import.meta.env.DEV) {
            console.info('[chat-ws] open', conversationId)
          }
          finish(true)
        }

        ws.onclose = (ev) => {
          // Superseded connection — do not touch shared state or reconnect.
          if (generation !== connectGeneration) return

          if (chatWs.value === ws) {
            chatWs.value = null
            wsConnected.value = false
          }
          if (!settled) {
            if (import.meta.env.DEV) {
              console.warn('[chat-ws] closed before open', ev.code, redactWsUrl(url))
            }
            finish(false)
          }
          // Unexpected drop of the active socket.
          if (activeConversationId === conversationId && chatWs.value == null) {
            scheduleReconnect(conversationId, ev.code, generation)
          }
        }

        ws.onerror = () => {
          if (generation !== connectGeneration) return
          if (import.meta.env.DEV) {
            console.warn('[chat-ws] error', redactWsUrl(url))
          }
        }

        ws.onmessage = (event) => {
          if (generation !== connectGeneration) return
          try {
            const data = JSON.parse(event.data) as Message
            if (data?.id != null && (data.content != null || data.attachments?.length)) {
              appendMessage(data)
              notifyEcho(data)
            }
          } catch {
            // ignore parse errors
          }
        }
      } catch (err) {
        if (import.meta.env.DEV) {
          console.warn('[chat-ws] construct failed', err)
        }
        finish(false)
      }
    })

    try {
      return await connectInFlight
    } finally {
      if (connectInFlightId === conversationId) {
        connectInFlight = null
        connectInFlightId = null
      }
    }
  }

  function disconnectChat() {
    clearReconnectTimer()
    clearEchoWaiters()
    activeConversationId = null
    reconnectAttempts = 0
    connectGeneration += 1
    connectInFlight = null
    connectInFlightId = null
    const ws = chatWs.value
    chatWs.value = null
    wsConnected.value = false
    if (ws) {
      try {
        ws.onclose = null
        ws.onerror = null
        ws.onmessage = null
        ws.onopen = null
        ws.close()
      } catch {
        // ignore
      }
    }
  }

  async function ensureChatConnected(conversationId: string): Promise<boolean> {
    if (
      activeConversationId === conversationId &&
      chatWs.value?.readyState === WebSocket.OPEN
    ) {
      return true
    }
    if (
      connectInFlight &&
      connectInFlightId === conversationId &&
      chatWs.value?.readyState === WebSocket.CONNECTING
    ) {
      return connectInFlight
    }
    return connectChat(conversationId)
  }

  /** @deprecated Prefer sendChatMessage — kept for callers that only check OPEN. */
  function sendMessageViaWs(content: string): boolean {
    const ws = chatWs.value
    if (!ws || ws.readyState !== WebSocket.OPEN) return false
    ws.send(JSON.stringify({ type: 'send_message', content }))
    return true
  }

  /**
   * Prefer WS (wait for open), optimistic UI, echo within 2s, else REST.
   * REST create also broadcasts on the backend channel layer.
   */
  async function sendChatMessage(
    conversationId: string,
    content: string,
    files: File[] = []
  ): Promise<Message | null> {
    const text = content.trim()
    if (!text && !files.length) return null

    const auth = useAuthStore()
    const senderId = auth.user?.id ? String(auth.user.id) : ''
    const tempId = `temp-${crypto.randomUUID()}`
    const optimistic: Message = {
      id: tempId,
      conversation: conversationId,
      sender: senderId,
      content: text || (files[0]?.name ?? ''),
      is_read: true,
      created_at: new Date().toISOString(),
      attachments: files.map((f, i) => ({
        id: `temp-att-${i}`,
        file: null,
        file_name: f.name,
        file_size: f.size,
        file_type: f.type,
      })),
    }
    appendMessage(optimistic)

    // Multipart uploads go through REST (WS is text-only).
    if (files.length) {
      try {
        loading.value = true
        error.value = null
        const response = await messagingService.sendMessageWithFiles(conversationId, {
          content: text,
          files,
        })
        removeMessageById(tempId)
        appendMessage(response.data)
        return response.data
      } catch (err: any) {
        removeMessageById(tempId)
        error.value = err.response?.data?.detail || 'Failed to send message'
        throw err
      } finally {
        loading.value = false
      }
    }

    const connected = await ensureChatConnected(conversationId)
    const ws = chatWs.value
    if (connected && ws && ws.readyState === WebSocket.OPEN) {
      try {
        ws.send(JSON.stringify({ type: 'send_message', content: text }))
        const echoed = await waitForEcho(text, 2000)
        if (echoed) {
          removeMessageById(tempId)
          appendMessage(echoed)
          return echoed
        }
      } catch {
        // fall through to REST
      }
    }

    removeMessageById(tempId)
    try {
      return await sendMessage(conversationId, text)
    } catch (err) {
      throw err
    }
  }

  async function markAsRead(conversationId: string) {
    try {
      const conv = conversations.value.find((c) => c.id === conversationId)
      if (conv) conv.unread_count = 0
      await messagingService.markRead(conversationId)
      // total_unread / list patch also arrive via inbox_update; refresh as fallback
      if (!inboxWsConnected.value) {
        await fetchUnreadCount()
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
    inboxWsConnected,
    fetchConversations,
    fetchConversation,
    createConversation,
    fetchMessages,
    sendMessage,
    sendMessageWithFiles,
    sendChatMessage,
    sendMessageViaWs,
    connectChat,
    ensureChatConnected,
    disconnectChat,
    connectInbox,
    disconnectInbox,
    markAsRead,
    fetchUnreadCount,
  }
})
