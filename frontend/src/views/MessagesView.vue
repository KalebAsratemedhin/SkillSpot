<template>
  <AppLayout>
    <div class="h-[calc(100vh-64px)] flex overflow-hidden bg-slate-50">
      <aside class="w-full md:w-64 lg:w-80 bg-midnight text-slate-300 flex flex-col min-h-0 shrink-0 overflow-hidden">
        <div class="shrink-0 p-4 md:p-5 flex flex-col gap-3 md:gap-4 border-b border-slate-800">
          <div class="flex items-center justify-between text-white">
            <h1 class="text-base md:text-lg font-bold">Conversations</h1>
            <button class="p-1.5 rounded-lg hover:bg-slate-800 transition-colors">
              <span class="material-symbols-outlined text-[18px] md:text-[20px]">add_comment</span>
            </button>
          </div>
          <div class="relative">
            <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-[16px] md:text-[18px]">search</span>
            <input
              v-model="searchQuery"
              class="w-full bg-slate-900/50 border-none rounded-lg pl-9 py-1.5 md:py-2 text-xs md:text-sm text-white placeholder-slate-500 focus:ring-1 focus:ring-amber/50"
              placeholder="Search messages..."
              type="text"
            />
          </div>
        </div>
        <div class="flex-1 min-h-0 overflow-y-auto overflow-x-hidden">
          <div v-if="messagingStore.loading && validConversations.length === 0" class="flex justify-center py-8">
            <span class="material-symbols-outlined animate-spin text-2xl text-amber">refresh</span>
          </div>
          <div v-else-if="messagingStore.error" class="text-center py-8 px-4">
            <p class="text-red-400 text-sm">{{ messagingStore.error }}</p>
          </div>
          <div v-else-if="validConversations.length === 0" class="text-center py-8 px-4">
            <p class="text-slate-400 text-sm">No conversations yet</p>
            <p class="text-slate-500 text-xs mt-2">Start a conversation from a job or application</p>
          </div>
          <div
            v-for="conv in validConversations"
            :key="conv.id"
            :class="[
              'flex items-center gap-2 md:gap-3 px-3 md:px-5 py-3 md:py-5 cursor-pointer group transition-colors',
              selectedConversation === conv.id
                ? 'bg-slate-800/40 border-l-4 border-amber'
                : 'hover:bg-slate-800/20'
            ]"
            @click="selectConversation(conv.id)"
          >
            <div class="relative shrink-0">
              <div class="size-10 md:size-12 rounded-full bg-amber flex items-center justify-center font-semibold text-midnight text-sm md:text-base">
                {{ getConversationInitial(conv) }}
              </div>
              <div class="absolute bottom-0 right-0 size-2.5 md:size-3 bg-green-500 border-2 border-midnight rounded-full"></div>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between mb-0.5 md:mb-1">
                <p class="text-white font-semibold text-xs md:text-sm truncate">{{ getConversationDisplayName(conv) }}</p>
                <span v-if="(conv.unread_count ?? 0) > 0" class="bg-amber text-midnight text-[9px] md:text-[10px] font-black px-1.5 py-0.5 rounded-full">
                  {{ conv.unread_count }}
                </span>
              </div>
              <p v-if="conv.last_message" class="text-slate-400 text-[11px] md:text-xs truncate">{{ conv.last_message.content }}</p>
            </div>
          </div>
        </div>
      </aside>
      <div class="flex-1 flex flex-col min-h-0 overflow-hidden bg-white">
        <div v-if="selectedConversation" class="flex-1 flex flex-col min-h-0 overflow-hidden">
          <div class="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-4 md:p-6 space-y-3 md:space-y-4">
            <div
              v-for="message in messagingStore.messages"
              :key="message.id"
              :class="[
                'flex',
                message.sender === authStore.user?.id ? 'justify-end' : 'justify-start'
              ]"
            >
              <div
                :class="[
                  'max-w-[85%] md:max-w-[70%] rounded-xl p-3 md:p-4',
                  message.sender === authStore.user?.id
                    ? 'bg-amber text-midnight'
                    : 'bg-slate-100 text-midnight'
                ]"
              >
                <p class="text-xs md:text-sm break-words">{{ message.content }}</p>
                <p class="text-[10px] md:text-xs opacity-70 mt-1">{{ formatTime(message.created_at) }}</p>
              </div>
            </div>
          </div>
          <form @submit.prevent="handleSendMessage" class="p-3 md:p-6 border-t border-slate-200">
            <div class="flex gap-2">
              <input
                v-model="messageForm.content"
                class="flex-1 rounded-xl border border-slate-200 bg-white text-midnight focus:ring-2 focus:ring-amber/20 focus:border-amber px-3 md:px-4 py-2 md:py-3 text-sm"
                placeholder="Type a message..."
              />
              <Button type="submit" variant="default" size="default" class="px-4 md:px-6 text-sm">
                Send
              </Button>
            </div>
          </form>
        </div>
        <div v-else class="flex-1 flex items-center justify-center">
          <p class="text-slate-500">Select a conversation to start messaging</p>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useMessagingStore } from '@/stores/messaging'
import type { Conversation } from '@/services/messaging'
import AppLayout from '@/components/AppLayout.vue'
import Button from '@/components/ui/Button.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const messagingStore = useMessagingStore()

const selectedConversation = ref<string | null>(null)
const messageForm = ref({ content: '' })
const searchQuery = ref('')

const validConversations = computed(() => {
  const list = Array.isArray(messagingStore.conversations) ? messagingStore.conversations : []
  const filtered = list.filter((c): c is Conversation => c != null && c.id != null)
  if (!searchQuery.value.trim()) return filtered
  const q = searchQuery.value.toLowerCase()
  return filtered.filter(
    (c) =>
      getConversationDisplayName(c).toLowerCase().includes(q) ||
      (c.last_message?.content ?? '').toLowerCase().includes(q)
  )
})

function getConversationDisplayName(conv: Conversation): string {
  if (conv.other_participant?.name) return conv.other_participant.name
  if (conv.other_participant?.email) return conv.other_participant.email
  const names = [conv.participant1_name, conv.participant2_name].filter(Boolean)
  if (names.length) return names.join(', ')
  return 'Conversation'
}

function getConversationInitial(conv: Conversation): string {
  const name = conv.other_participant?.name || conv.other_participant?.email
  if (name) return name[0].toUpperCase()
  const n = conv.participant1_name || conv.participant2_name
  return n ? n[0].toUpperCase() : 'U'
}

function formatTime(dateString: string) {
  console.log('formatTime', dateString)
  const date = new Date(dateString)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

async function selectConversation(id: string) {
  selectedConversation.value = id
  router.push({ name: 'conversation', params: { id } })
  await messagingStore.fetchConversation(id)
  await messagingStore.markAsRead(id)
  if (typeof messagingStore.connectChat === 'function') {
    messagingStore.connectChat(id)
  }
}

async function handleSendMessage() {
  const content = messageForm.value.content?.trim()
  if (!selectedConversation.value || !content) return
  if (messagingStore.sendMessageViaWs(content)) {
    messageForm.value.content = ''
    return
  }
  await messagingStore.sendMessage(selectedConversation.value, content)
  messageForm.value.content = ''
}

function getConversationIdFromRoute(): string | undefined {
  const p = route.params.id
  const id = Array.isArray(p) ? p[0] : p
  return typeof id === 'string' ? id : undefined
}

onMounted(async () => {
  try {
    await messagingStore.fetchConversations()
  } catch (error) {
    console.error('Error fetching conversations:', error)
  }
  const id = getConversationIdFromRoute()
  if (id) {
    selectedConversation.value = id
    await messagingStore.fetchConversation(id)
    await messagingStore.markAsRead(id)
    if (typeof messagingStore.connectChat === 'function') {
      messagingStore.connectChat(id)
    }
  }
})

onUnmounted(() => {
  if (typeof messagingStore.disconnectChat === 'function') {
    messagingStore.disconnectChat()
  }
})

watch(
  () => getConversationIdFromRoute(),
  async (id) => {
    if (id && id !== selectedConversation.value) {
      selectedConversation.value = id
      await messagingStore.fetchConversation(id)
      await messagingStore.markAsRead(id)
      messagingStore.connectChat(id)
    }
    if (!id) {
      selectedConversation.value = null
      if (typeof messagingStore.disconnectChat === 'function') {
        messagingStore.disconnectChat()
      }
    }
  }
)
</script>
