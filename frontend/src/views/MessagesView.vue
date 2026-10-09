<template>
  <AppLayout>
    <div class="h-[calc(100vh-64px)] flex overflow-hidden bg-slate-50">
      <!-- Inbox -->
      <aside
        class="w-full md:w-72 lg:w-80 flex flex-col min-h-0 shrink-0 border-r border-slate-200/80 bg-white"
      >
        <div class="shrink-0 px-4 pt-4 pb-3 space-y-3 border-b border-slate-100">
          <div class="flex items-center justify-between gap-2">
            <div>
              <h1 class="text-lg font-display font-bold text-midnight tracking-tight">Messages</h1>
              <p class="text-[11px] text-slate-400 font-medium mt-0.5">Direct chats with people you work with</p>
            </div>
            <div class="relative" ref="composeMenuRef">
              <button
                type="button"
                class="size-9 rounded-xl bg-amber text-midnight flex items-center justify-center shadow-sm hover:brightness-105 transition"
                aria-label="New conversation"
                @click="composeMenuOpen = !composeMenuOpen"
              >
                <span class="material-symbols-outlined text-[20px]">edit_square</span>
              </button>
              <div
                v-if="composeMenuOpen"
                class="absolute right-0 top-11 z-30 w-48 rounded-xl border border-slate-200 bg-white py-1.5 shadow-lg"
              >
                <button
                  type="button"
                  class="w-full flex items-center gap-2.5 px-3 py-2.5 text-left text-sm font-medium text-midnight hover:bg-slate-50"
                  @click="openNewChat"
                >
                  <span class="material-symbols-outlined text-[18px] text-amber">chat</span>
                  New chat
                </button>
                <button
                  type="button"
                  class="w-full flex items-center gap-2.5 px-3 py-2.5 text-left text-sm font-medium text-midnight hover:bg-slate-50"
                  @click="openNewGroup"
                >
                  <span class="material-symbols-outlined text-[18px] text-amber">group_add</span>
                  New group
                </button>
              </div>
            </div>
          </div>
          <div class="relative">
            <span
              class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-[18px]"
            >search</span>
            <input
              v-model="searchQuery"
              class="w-full rounded-xl border border-slate-200 bg-slate-50/80 pl-9 pr-3 py-2 text-sm text-midnight placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-amber/25 focus:border-amber/60"
              placeholder="Search conversations..."
              type="search"
            />
          </div>
        </div>

        <div class="flex-1 min-h-0 overflow-y-auto">
          <div v-if="messagingStore.loading && validConversations.length === 0" class="flex justify-center py-10">
            <span class="material-symbols-outlined animate-spin text-2xl text-amber">refresh</span>
          </div>
          <div v-else-if="messagingStore.error" class="text-center py-8 px-4">
            <p class="text-red-500 text-sm">{{ messagingStore.error }}</p>
          </div>
          <div v-else-if="validConversations.length === 0" class="text-center py-10 px-6">
            <div class="mx-auto mb-3 size-12 rounded-2xl bg-amber/15 flex items-center justify-center">
              <span class="material-symbols-outlined text-amber text-[22px]">forum</span>
            </div>
            <p class="text-midnight text-sm font-semibold">No conversations yet</p>
            <p class="text-slate-400 text-xs mt-1.5 leading-relaxed">
              Start a chat from here, or message someone from a job.
            </p>
            <button
              type="button"
              class="mt-4 text-sm font-semibold text-amber hover:underline"
              @click="openNewChat"
            >
              New chat
            </button>
          </div>
          <button
            v-for="conv in validConversations"
            :key="conv.id"
            type="button"
            :class="[
              'w-full flex items-center gap-3 px-3.5 py-3 text-left transition-colors border-l-[3px]',
              selectedConversation === conv.id
                ? 'bg-amber/10 border-amber'
                : 'border-transparent hover:bg-slate-50',
            ]"
            @click="selectConversation(conv.id)"
          >
            <div class="relative shrink-0">
              <div
                class="size-11 rounded-full bg-gradient-to-br from-midnight to-slate-700 text-white flex items-center justify-center text-sm font-semibold"
              >
                {{ getConversationInitial(conv) }}
              </div>
              <span
                class="absolute bottom-0 right-0 size-2.5 rounded-full border-2 border-white"
                :class="conv.other_participant?.is_online ? 'bg-emerald-500' : 'bg-slate-300'"
                :title="conv.other_participant?.is_online ? 'Online' : 'Offline'"
              />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between gap-2 mb-0.5">
                <p class="text-sm font-semibold text-midnight truncate">
                  {{ getConversationDisplayName(conv) }}
                </p>
                <span
                  v-if="(conv.unread_count ?? 0) > 0"
                  class="shrink-0 min-w-[1.25rem] h-5 px-1.5 rounded-full bg-amber text-midnight text-[10px] font-bold flex items-center justify-center"
                >
                  {{ conv.unread_count }}
                </span>
              </div>
              <p class="text-xs text-slate-400 truncate">
                {{ conversationPreview(conv) }}
              </p>
            </div>
          </button>
        </div>
      </aside>

      <!-- Thread — fills remaining space between inbox and details -->
      <div
        class="flex flex-col min-h-0 min-w-0 flex-1 overflow-hidden bg-slate-100/70 xl:border-r border-slate-200/80"
      >
        <template v-if="selectedConversation && activeConversation">
          <header class="shrink-0 px-4 py-3 border-b border-slate-200/80 bg-white">
            <p class="text-sm font-semibold text-midnight truncate">
              {{ threadHeaderTitle }}
            </p>
            <p v-if="threadHeaderHint" class="text-[11px] text-slate-500 truncate mt-0.5">
              {{ threadHeaderHint }}
            </p>
          </header>

          <div
            ref="messagesScrollRef"
            class="flex-1 min-h-0 overflow-y-auto py-4 space-y-3"
          >
            <div
              v-for="message in messagingStore.messages"
              :key="message.id"
              :class="[
                'flex px-4',
                isMine(message) ? 'justify-end' : 'justify-start',
              ]"
            >
              <div
                :class="[
                  'max-w-[90%] rounded-2xl px-3.5 py-2.5 shadow-sm',
                  isMine(message)
                    ? 'bg-amber text-midnight rounded-br-md'
                    : 'bg-white border border-slate-200/80 text-midnight rounded-bl-md',
                ]"
              >
                <p
                  v-if="message.content"
                  class="text-sm leading-relaxed break-words whitespace-pre-wrap"
                >{{ message.content }}</p>
                <div
                  v-if="message.attachments?.length"
                  class="mt-2 space-y-1.5"
                  :class="{ 'mt-0': !message.content }"
                >
                  <a
                    v-for="att in message.attachments"
                    :key="att.id"
                    :href="att.file || undefined"
                    :target="att.file ? '_blank' : undefined"
                    :rel="att.file ? 'noopener noreferrer' : undefined"
                    :class="[
                      'flex items-center gap-2 rounded-xl px-2.5 py-2 text-xs font-medium',
                      isMine(message) ? 'bg-black/10' : 'bg-slate-50 border border-slate-100',
                      att.file ? 'hover:opacity-90 cursor-pointer' : 'cursor-default',
                    ]"
                  >
                    <span class="material-symbols-outlined text-[18px] shrink-0">
                      {{ attachmentIcon(att.file_type || att.file_name) }}
                    </span>
                    <span class="truncate min-w-0">{{ att.file_name || 'Attachment' }}</span>
                    <span v-if="att.file_size" class="shrink-0 opacity-60">
                      {{ formatFileSize(att.file_size) }}
                    </span>
                  </a>
                </div>
                <p
                  :class="[
                    'text-[10px] mt-1.5',
                    isMine(message) ? 'text-midnight/60' : 'text-slate-400',
                  ]"
                >
                  {{ formatTime(message.created_at) }}
                </p>
              </div>
            </div>
          </div>

          <div class="shrink-0 px-4 pb-3 pt-1">
            <div class="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
              <div
                v-if="pendingFiles.length"
                class="flex flex-wrap gap-2 mb-2.5"
              >
                <div
                  v-for="(file, idx) in pendingFiles"
                  :key="`${file.name}-${idx}`"
                  class="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 pl-2.5 pr-1 py-1 text-xs text-midnight max-w-[200px]"
                >
                  <span class="material-symbols-outlined text-[14px] text-amber shrink-0">attach_file</span>
                  <span class="truncate">{{ file.name }}</span>
                  <button
                    type="button"
                    class="size-6 rounded-md hover:bg-slate-200/80 flex items-center justify-center text-slate-500"
                    aria-label="Remove file"
                    @click="removePendingFile(idx)"
                  >
                    <span class="material-symbols-outlined text-[14px]">close</span>
                  </button>
                </div>
              </div>
              <form class="flex items-center gap-2" @submit.prevent="handleSendMessage">
                <input
                  ref="fileInputRef"
                  type="file"
                  class="hidden"
                  multiple
                  @change="onFilesPicked"
                />
                <button
                  type="button"
                  class="size-10 shrink-0 self-center rounded-xl border border-slate-200 text-slate-500 hover:text-midnight hover:bg-slate-50 flex items-center justify-center transition"
                  title="Share a file"
                  @click="fileInputRef?.click()"
                >
                  <span class="material-symbols-outlined text-[20px]">attach_file</span>
                </button>
                <div class="flex-1 min-w-0 flex items-center">
                  <textarea
                    v-model="messageForm.content"
                    rows="1"
                    class="w-full min-h-10 max-h-28 resize-none rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm leading-5 text-midnight placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-amber/25 focus:border-amber/60 focus:bg-white"
                    placeholder="Write a message…"
                    @keydown.enter.exact.prevent="handleSendMessage"
                  />
                </div>
                <Button
                  type="submit"
                  variant="default"
                  size="icon"
                  class="size-10 shrink-0 self-center rounded-xl p-0 shadow-none hover:scale-100"
                  :disabled="!canSend"
                  aria-label="Send"
                >
                  <span class="material-symbols-outlined text-[20px]">send</span>
                </Button>
              </form>
            </div>
          </div>
        </template>

        <div v-else class="flex-1 flex flex-col items-center justify-center px-4 text-center">
          <div class="size-16 rounded-2xl bg-amber/15 flex items-center justify-center mb-4">
            <span class="material-symbols-outlined text-amber text-[32px]">chat_bubble</span>
          </div>
          <p class="text-midnight font-display font-bold text-lg">Pick a conversation</p>
          <p class="text-slate-500 text-sm mt-1.5 max-w-xs">
            Or start a new chat or group from the compose menu.
          </p>
          <div class="flex gap-2 mt-5">
            <Button variant="default" @click="openNewChat">
              New chat
            </Button>
            <Button variant="outline" @click="openNewGroup">
              New group
            </Button>
          </div>
        </div>
      </div>

      <!-- Details aside -->
      <aside
        class="hidden xl:flex w-96 shrink-0 flex-col min-h-0 bg-white"
      >
        <template v-if="selectedConversation && activeConversation">
          <div class="px-6 py-6 border-b border-slate-100 text-center">
            <div
              class="mx-auto size-16 rounded-full bg-gradient-to-br from-midnight to-slate-700 text-white flex items-center justify-center text-xl font-semibold"
            >
              {{ getConversationInitial(activeConversation) }}
            </div>
            <p class="mt-3 text-base font-semibold text-midnight truncate">
              {{ getConversationDisplayName(activeConversation) }}
            </p>
            <p
              v-if="activeConversation.other_participant?.email && !isGroupChat"
              class="mt-0.5 text-xs text-slate-500 truncate"
            >
              {{ activeConversation.other_participant.email }}
            </p>
            <p
              class="mt-3 inline-flex items-center gap-1.5 text-[11px] font-medium"
              :class="peerIsOnline ? 'text-emerald-600' : 'text-slate-500'"
            >
              <span
                class="size-1.5 rounded-full"
                :class="peerIsOnline ? 'bg-emerald-500' : 'bg-slate-300'"
              />
              {{ peerPresenceLabel }}
            </p>
          </div>

          <div class="flex-1 min-h-0 overflow-y-auto px-5 py-5 space-y-6">
            <!-- 1:1 — contracts with this person -->
            <template v-if="!isGroupChat">
              <div>
                <p class="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">Contracts</p>
                <div v-if="peerContractsLoading" class="flex justify-center py-6">
                  <span class="material-symbols-outlined animate-spin text-amber">refresh</span>
                </div>
                <ul v-else-if="peerContractsPage.length" class="space-y-2">
                  <li v-for="c in peerContractsPage" :key="c.id">
                    <router-link
                      :to="`/contracts/${c.id}`"
                      class="block rounded-xl border border-slate-200 px-3 py-2.5 hover:border-amber/40 hover:bg-amber/5 transition"
                    >
                      <p class="text-sm font-semibold text-midnight truncate">
                        {{ c.title || c.job_title || 'Contract' }}
                      </p>
                      <div class="mt-1 flex items-center justify-between gap-2">
                        <span class="text-[10px] font-bold uppercase tracking-wide text-slate-500">
                          {{ c.status?.replace(/_/g, ' ') }}
                        </span>
                        <span class="text-xs font-medium text-slate-600">
                          Br {{ Number(c.total_amount || 0).toLocaleString() }}
                        </span>
                      </div>
                    </router-link>
                  </li>
                </ul>
                <p v-else class="text-xs text-slate-400 leading-relaxed">
                  No contracts with this person yet.
                </p>
                <div
                  v-if="peerContractsTotalPages > 1"
                  class="flex items-center justify-between mt-3"
                >
                  <button
                    type="button"
                    class="text-xs font-semibold text-slate-500 hover:text-midnight disabled:opacity-40"
                    :disabled="peerContractsPageNum <= 1"
                    @click="peerContractsPageNum -= 1"
                  >
                    Previous
                  </button>
                  <span class="text-[11px] text-slate-400">
                    {{ peerContractsPageNum }} / {{ peerContractsTotalPages }}
                  </span>
                  <button
                    type="button"
                    class="text-xs font-semibold text-slate-500 hover:text-midnight disabled:opacity-40"
                    :disabled="peerContractsPageNum >= peerContractsTotalPages"
                    @click="peerContractsPageNum += 1"
                  >
                    Next
                  </button>
                </div>
              </div>
            </template>

            <!-- Group — members + files -->
            <template v-else>
              <div>
                <p class="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">Members</p>
                <ul v-if="groupMembersPage.length" class="space-y-1.5">
                  <li
                    v-for="m in groupMembersPage"
                    :key="m.id"
                    class="flex items-center gap-2.5 rounded-xl border border-slate-200 px-2.5 py-2"
                  >
                    <div
                      class="size-8 rounded-full bg-midnight text-white flex items-center justify-center text-xs font-semibold shrink-0"
                    >
                      {{ (m.name || '?')[0].toUpperCase() }}
                    </div>
                    <p class="text-sm font-medium text-midnight truncate">{{ m.name }}</p>
                  </li>
                </ul>
                <p v-else class="text-xs text-slate-400">No members listed yet.</p>
                <div
                  v-if="groupMembersTotalPages > 1"
                  class="flex items-center justify-between mt-3"
                >
                  <button
                    type="button"
                    class="text-xs font-semibold text-slate-500 hover:text-midnight disabled:opacity-40"
                    :disabled="groupMembersPageNum <= 1"
                    @click="groupMembersPageNum -= 1"
                  >
                    Previous
                  </button>
                  <span class="text-[11px] text-slate-400">
                    {{ groupMembersPageNum }} / {{ groupMembersTotalPages }}
                  </span>
                  <button
                    type="button"
                    class="text-xs font-semibold text-slate-500 hover:text-midnight disabled:opacity-40"
                    :disabled="groupMembersPageNum >= groupMembersTotalPages"
                    @click="groupMembersPageNum += 1"
                  >
                    Next
                  </button>
                </div>
              </div>

              <div>
                <p class="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">Shared files</p>
                <ul v-if="filesPage.length" class="space-y-1.5">
                  <li v-for="att in filesPage" :key="att.id">
                    <a
                      :href="att.file || undefined"
                      :target="att.file ? '_blank' : undefined"
                      :rel="att.file ? 'noopener noreferrer' : undefined"
                      class="flex items-center gap-2 rounded-xl border border-slate-200 px-2.5 py-2 text-xs text-midnight hover:bg-slate-50"
                      :class="att.file ? 'cursor-pointer' : 'cursor-default opacity-70'"
                    >
                      <span class="material-symbols-outlined text-[16px] text-amber shrink-0">
                        {{ attachmentIcon(att.file_type || att.file_name) }}
                      </span>
                      <span class="truncate">{{ att.file_name || 'Attachment' }}</span>
                    </a>
                  </li>
                </ul>
                <p v-else class="text-xs text-slate-400 leading-relaxed">
                  Files shared in this chat will show up here.
                </p>
                <div
                  v-if="filesTotalPages > 1"
                  class="flex items-center justify-between mt-3"
                >
                  <button
                    type="button"
                    class="text-xs font-semibold text-slate-500 hover:text-midnight disabled:opacity-40"
                    :disabled="filesPageNum <= 1"
                    @click="filesPageNum -= 1"
                  >
                    Previous
                  </button>
                  <span class="text-[11px] text-slate-400">
                    {{ filesPageNum }} / {{ filesTotalPages }}
                  </span>
                  <button
                    type="button"
                    class="text-xs font-semibold text-slate-500 hover:text-midnight disabled:opacity-40"
                    :disabled="filesPageNum >= filesTotalPages"
                    @click="filesPageNum += 1"
                  >
                    Next
                  </button>
                </div>
              </div>
            </template>
          </div>
        </template>
        <div v-else class="flex-1 flex items-center justify-center px-6 text-center">
          <p class="text-xs text-slate-400 leading-relaxed">
            Select a conversation to see details.
          </p>
        </div>
      </aside>
    </div>

    <!-- New chat -->
    <Dialog v-model:open="showNewChat">
      <DialogContent class="sm:max-w-[440px]">
        <DialogHeader>
          <DialogTitle>New chat</DialogTitle>
          <DialogDescription>Search for someone to message.</DialogDescription>
        </DialogHeader>
        <div class="space-y-3 py-1">
          <div class="relative">
            <span
              class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-[18px]"
            >search</span>
            <input
              v-model="peopleQuery"
              class="w-full rounded-xl border border-slate-200 bg-white pl-9 pr-3 py-2.5 text-sm text-midnight placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-amber/25 focus:border-amber/60"
              placeholder="Name or skill…"
              type="search"
              @input="onPeopleSearch"
            />
          </div>
          <div class="max-h-64 overflow-y-auto rounded-xl border border-slate-200 bg-slate-50/50 divide-y divide-slate-200">
            <div v-if="peopleLoading" class="py-8 flex justify-center">
              <span class="material-symbols-outlined animate-spin text-amber">refresh</span>
            </div>
            <p v-else-if="!peopleResults.length" class="py-8 text-center text-sm text-slate-500">
              {{ peopleQuery.trim() ? 'No people found' : 'Type to search providers' }}
            </p>
            <button
              v-for="person in peopleResults"
              :key="person.user_id"
              type="button"
              class="w-full flex items-center gap-3 px-3 py-2.5 text-left bg-white hover:bg-amber/5 transition"
              :disabled="startingChat"
              @click="startChatWith(person.user_id)"
            >
              <div
                class="size-9 rounded-full bg-midnight text-white flex items-center justify-center text-xs font-semibold shrink-0"
              >
                {{ (person.full_name || '?')[0].toUpperCase() }}
              </div>
              <div class="min-w-0">
                <p class="text-sm font-semibold text-midnight truncate">{{ person.full_name }}</p>
                <p class="text-xs text-slate-500 truncate">{{ person.location || 'Provider' }}</p>
              </div>
            </button>
          </div>
        </div>
        <DialogFooter>
          <DialogClose as-child>
            <Button type="button" variant="outline">Cancel</Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- New group (UI ready; backend groups not yet available) -->
    <Dialog v-model:open="showNewGroup">
      <DialogContent class="sm:max-w-[440px]">
        <DialogHeader>
          <DialogTitle>New group</DialogTitle>
          <DialogDescription>
            Create a shared conversation with multiple people.
          </DialogDescription>
        </DialogHeader>
        <div class="space-y-3 py-1">
          <div>
            <label class="text-xs font-semibold text-slate-500 uppercase tracking-wide">Group name</label>
            <input
              v-model="groupName"
              class="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-midnight placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-amber/25 focus:border-amber/60"
              placeholder="e.g. Kitchen remodel crew"
              type="text"
            />
          </div>
          <div class="relative">
            <span
              class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-[18px]"
            >search</span>
            <input
              v-model="groupPeopleQuery"
              class="w-full rounded-xl border border-slate-200 bg-white pl-9 pr-3 py-2.5 text-sm text-midnight placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-amber/25 focus:border-amber/60"
              placeholder="Add people…"
              type="search"
              @input="onGroupPeopleSearch"
            />
          </div>
          <div
            v-if="groupSelected.length"
            class="flex flex-wrap gap-1.5"
          >
            <span
              v-for="p in groupSelected"
              :key="p.user_id"
              class="inline-flex items-center gap-1 rounded-full bg-amber/15 text-midnight text-xs font-medium pl-2.5 pr-1 py-1"
            >
              {{ p.full_name }}
              <button
                type="button"
                class="size-5 rounded-full hover:bg-amber/30 flex items-center justify-center text-midnight"
                @click="toggleGroupMember(p)"
              >
                <span class="material-symbols-outlined text-[12px]">close</span>
              </button>
            </span>
          </div>
          <div class="max-h-48 overflow-y-auto rounded-xl border border-slate-200 bg-slate-50/50 divide-y divide-slate-200">
            <div v-if="groupPeopleLoading" class="py-6 flex justify-center">
              <span class="material-symbols-outlined animate-spin text-amber">refresh</span>
            </div>
            <button
              v-for="person in groupPeopleResults"
              :key="person.user_id"
              type="button"
              class="w-full flex items-center gap-3 px-3 py-2.5 text-left bg-white hover:bg-amber/5 transition"
              @click="toggleGroupMember(person)"
            >
              <div
                class="size-8 rounded-full bg-midnight text-white flex items-center justify-center text-xs font-semibold shrink-0"
              >
                {{ (person.full_name || '?')[0].toUpperCase() }}
              </div>
              <p class="text-sm font-medium text-midnight truncate flex-1">{{ person.full_name }}</p>
              <span
                class="material-symbols-outlined text-[18px]"
                :class="isGroupSelected(person.user_id) ? 'text-amber' : 'text-slate-400'"
              >
                {{ isGroupSelected(person.user_id) ? 'check_circle' : 'circle' }}
              </span>
            </button>
          </div>
          <p class="text-xs text-slate-500 leading-relaxed">
            Group chats are almost ready — you can set this up now, and we’ll enable them as soon as the backend ships.
          </p>
        </div>
        <DialogFooter>
          <DialogClose as-child>
            <Button type="button" variant="outline">Cancel</Button>
          </DialogClose>
          <Button
            type="button"
            variant="default"
            :disabled="!groupName.trim() || groupSelected.length < 2"
            @click="createGroupStub"
          >
            Create group
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { onClickOutside } from '@vueuse/core'
import { toast } from 'vue-sonner'
import { useAuthStore } from '@/stores/auth'
import { useMessagingStore } from '@/stores/messaging'
import type { Conversation, Message, MessageAttachment } from '@/services/messaging'
import { contractsService, type Contract } from '@/services/contracts'
import { profilesService, type PublicProvider } from '@/services/profiles'
import AppLayout from '@/components/AppLayout.vue'
import Button from '@/components/ui/Button.vue'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogClose,
} from '@/components/ui/dialog'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const messagingStore = useMessagingStore()

const selectedConversation = ref<string | null>(null)
const messageForm = ref({ content: '' })
const sendingMessage = ref(false)
const searchQuery = ref('')
const pendingFiles = ref<File[]>([])
const fileInputRef = ref<HTMLInputElement | null>(null)
const messagesScrollRef = ref<HTMLElement | null>(null)

const composeMenuOpen = ref(false)
const composeMenuRef = ref<HTMLElement | null>(null)
onClickOutside(composeMenuRef, () => {
  composeMenuOpen.value = false
})

const showNewChat = ref(false)
const peopleQuery = ref('')
const peopleResults = ref<PublicProvider[]>([])
const peopleLoading = ref(false)
const startingChat = ref(false)
let peopleSearchTimer: ReturnType<typeof setTimeout> | null = null

const showNewGroup = ref(false)
const groupName = ref('')
const groupPeopleQuery = ref('')
const groupPeopleResults = ref<PublicProvider[]>([])
const groupPeopleLoading = ref(false)
const groupSelected = ref<PublicProvider[]>([])
let groupSearchTimer: ReturnType<typeof setTimeout> | null = null

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

const activeConversation = computed(() => {
  if (!selectedConversation.value) return null
  return (
    messagingStore.conversations.find((c) => c.id === selectedConversation.value) ||
    messagingStore.currentConversation
  )
})

const peerIsOnline = computed(
  () => Boolean(activeConversation.value?.other_participant?.is_online)
)

const peerPresenceLabel = computed(() => {
  const peer = activeConversation.value?.other_participant
  if (!peer) return 'Offline'
  if (peer.is_online) return 'Online'
  if (peer.last_seen_at) return `Last seen ${formatLastSeen(peer.last_seen_at)}`
  return 'Offline'
})

/** Slim thread chrome — context only; profile/presence live in the aside. */
const threadHeaderTitle = computed(() => {
  const conv = activeConversation.value
  if (!conv) return ''
  if (conv.job_title) return conv.job_title
  return isGroupChat.value ? 'Group chat' : 'Direct message'
})

const threadHeaderHint = computed(() => {
  const conv = activeConversation.value
  if (!conv?.job_title) return ''
  return `With ${getConversationDisplayName(conv)}`
})

const canSend = computed(
  () =>
    Boolean(selectedConversation.value) &&
    !sendingMessage.value &&
    (Boolean(messageForm.value.content?.trim()) || pendingFiles.value.length > 0)
)

const ASIDE_PAGE_SIZE = 5

/** Group chats will expose participants/is_group; until then treat as 1:1. */
const isGroupChat = computed(() => {
  const c = activeConversation.value
  if (!c) return false
  if ((c as { is_group?: boolean }).is_group) return true
  return Array.isArray(c.participants) && c.participants.length > 2
})

const peerContractsAll = ref<Contract[]>([])
const peerContractsLoading = ref(false)
const peerContractsPageNum = ref(1)

const peerContractsTotalPages = computed(() =>
  Math.max(1, Math.ceil(peerContractsAll.value.length / ASIDE_PAGE_SIZE))
)
const peerContractsPage = computed(() => {
  const start = (peerContractsPageNum.value - 1) * ASIDE_PAGE_SIZE
  return peerContractsAll.value.slice(start, start + ASIDE_PAGE_SIZE)
})

const threadAttachments = computed(() => {
  const out: MessageAttachment[] = []
  const seen = new Set<string>()
  for (const msg of messagingStore.messages) {
    for (const att of msg.attachments ?? []) {
      if (!att?.id || seen.has(att.id)) continue
      seen.add(att.id)
      out.push(att)
    }
  }
  return out.reverse()
})

const filesPageNum = ref(1)
const filesTotalPages = computed(() =>
  Math.max(1, Math.ceil(threadAttachments.value.length / ASIDE_PAGE_SIZE))
)
const filesPage = computed(() => {
  const start = (filesPageNum.value - 1) * ASIDE_PAGE_SIZE
  return threadAttachments.value.slice(start, start + ASIDE_PAGE_SIZE)
})

type AsideMember = { id: string; name: string }

const groupMembersAll = computed((): AsideMember[] => {
  const c = activeConversation.value
  if (!c) return []
  const members: AsideMember[] = []
  const seen = new Set<string>()
  const push = (id?: string, name?: string) => {
    if (!id || seen.has(id)) return
    seen.add(id)
    members.push({ id, name: name || 'Member' })
  }
  if (c.other_participant?.id) {
    push(c.other_participant.id, c.other_participant.name || c.other_participant.email)
  }
  if (authStore.user?.id) {
    const me = authStore.user
    push(me.id, [me.first_name, me.last_name].filter(Boolean).join(' ') || me.email)
  }
  for (const pid of c.participants ?? []) {
    push(pid, pid === authStore.user?.id ? 'You' : undefined)
  }
  return members
})

const groupMembersPageNum = ref(1)
const groupMembersTotalPages = computed(() =>
  Math.max(1, Math.ceil(groupMembersAll.value.length / ASIDE_PAGE_SIZE))
)
const groupMembersPage = computed(() => {
  const start = (groupMembersPageNum.value - 1) * ASIDE_PAGE_SIZE
  return groupMembersAll.value.slice(start, start + ASIDE_PAGE_SIZE)
})

async function loadPeerContracts(peerId: string) {
  peerContractsLoading.value = true
  peerContractsPageNum.value = 1
  try {
    const me = authStore.user?.id
    // Prefer API counterparty filters when role is clear; otherwise load my contracts and filter.
    let results: Contract[] = []
    if (authStore.isClient && !authStore.isProvider) {
      const res = await contractsService.list({ provider: peerId, page_size: 50 })
      results = res.data.results ?? []
    } else if (authStore.isProvider && !authStore.isClient) {
      const res = await contractsService.list({ client: peerId, page_size: 50 })
      results = res.data.results ?? []
    } else {
      const res = await contractsService.list({ page_size: 50 })
      results = (res.data.results ?? []).filter(
        (c) =>
          (c.client === peerId || c.provider === peerId) &&
          (c.client === me || c.provider === me)
      )
    }
    peerContractsAll.value = results
  } catch {
    peerContractsAll.value = []
  } finally {
    peerContractsLoading.value = false
  }
}

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

function conversationPreview(conv: Conversation): string {
  const content = conv.last_message?.content?.trim()
  if (content) return content
  return 'No messages yet'
}

function formatTime(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function formatLastSeen(dateString: string) {
  const date = new Date(dateString)
  if (Number.isNaN(date.getTime())) return 'recently'
  const now = Date.now()
  const diffMs = Math.max(0, now - date.getTime())
  const mins = Math.floor(diffMs / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
}

function formatFileSize(bytes: number) {
  if (!bytes || bytes < 1024) return `${bytes || 0} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function attachmentIcon(hint: string) {
  const h = (hint || '').toLowerCase()
  if (h.includes('image') || /\.(png|jpe?g|gif|webp|svg)$/.test(h)) return 'image'
  if (h.includes('pdf') || h.endsWith('.pdf')) return 'picture_as_pdf'
  if (h.includes('video')) return 'movie'
  return 'draft'
}

function isMine(message: Message) {
  return String(message.sender) === String(authStore.user?.id)
}

async function scrollToBottom() {
  await nextTick()
  const el = messagesScrollRef.value
  if (el) el.scrollTop = el.scrollHeight
}

async function openConversation(id: string) {
  selectedConversation.value = id
  peerContractsPageNum.value = 1
  filesPageNum.value = 1
  groupMembersPageNum.value = 1
  await messagingStore.fetchConversation(id)
  await messagingStore.markAsRead(id)
  await messagingStore.connectChat(id)
  const peerId = messagingStore.currentConversation?.other_participant?.id
  if (peerId && !isGroupChat.value) {
    await loadPeerContracts(peerId)
  } else {
    peerContractsAll.value = []
  }
  await scrollToBottom()
}

async function selectConversation(id: string) {
  if (id !== selectedConversation.value) {
    await router.push({ name: 'conversation', params: { id } })
  }
  await openConversation(id)
}

function onFilesPicked(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])
  if (!files.length) return
  const next = [...pendingFiles.value, ...files].slice(0, 5)
  pendingFiles.value = next
  input.value = ''
}

function removePendingFile(index: number) {
  pendingFiles.value = pendingFiles.value.filter((_, i) => i !== index)
}

async function handleSendMessage() {
  if (!selectedConversation.value || !canSend.value || sendingMessage.value) return
  const content = messageForm.value.content?.trim() || ''
  const files = [...pendingFiles.value]
  if (!content && !files.length) return
  messageForm.value.content = ''
  pendingFiles.value = []
  sendingMessage.value = true
  try {
    await messagingStore.sendChatMessage(selectedConversation.value, content, files)
    await scrollToBottom()
  } catch {
    messageForm.value.content = content
    pendingFiles.value = files
  } finally {
    sendingMessage.value = false
  }
}

function openNewChat() {
  composeMenuOpen.value = false
  showNewChat.value = true
  peopleQuery.value = ''
  peopleResults.value = []
}

function openNewGroup() {
  composeMenuOpen.value = false
  showNewGroup.value = true
  groupName.value = ''
  groupPeopleQuery.value = ''
  groupPeopleResults.value = []
  groupSelected.value = []
}

async function searchPeople(query: string, target: 'chat' | 'group') {
  const q = query.trim()
  if (target === 'chat') peopleLoading.value = true
  else groupPeopleLoading.value = true
  try {
    const res = await profilesService.listPublicProviders({
      q: q || undefined,
      page_size: 20,
    })
    const data = res.data
    const results = Array.isArray(data) ? data : data.results || []
    if (target === 'chat') peopleResults.value = results
    else groupPeopleResults.value = results
  } catch {
    if (target === 'chat') peopleResults.value = []
    else groupPeopleResults.value = []
  } finally {
    if (target === 'chat') peopleLoading.value = false
    else groupPeopleLoading.value = false
  }
}

function onPeopleSearch() {
  if (peopleSearchTimer) clearTimeout(peopleSearchTimer)
  peopleSearchTimer = setTimeout(() => searchPeople(peopleQuery.value, 'chat'), 280)
}

function onGroupPeopleSearch() {
  if (groupSearchTimer) clearTimeout(groupSearchTimer)
  groupSearchTimer = setTimeout(() => searchPeople(groupPeopleQuery.value, 'group'), 280)
}

function isGroupSelected(userId: string) {
  return groupSelected.value.some((p) => p.user_id === userId)
}

function toggleGroupMember(person: PublicProvider) {
  if (isGroupSelected(person.user_id)) {
    groupSelected.value = groupSelected.value.filter((p) => p.user_id !== person.user_id)
  } else {
    groupSelected.value = [...groupSelected.value, person]
  }
}

async function startChatWith(userId: string) {
  if (!userId || startingChat.value) return
  startingChat.value = true
  try {
    const conv = await messagingStore.createConversation({ participant2_id: userId })
    showNewChat.value = false
    if (conv?.id) {
      await selectConversation(conv.id)
      await messagingStore.fetchConversations()
    }
  } catch (err: any) {
    toast.error(err?.response?.data?.detail || 'Could not start chat')
  } finally {
    startingChat.value = false
  }
}

function createGroupStub() {
  toast.success('Group chats coming soon', {
    description: 'We’ll enable group rooms as soon as the backend is ready.',
  })
  showNewGroup.value = false
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
    await openConversation(id)
    return
  }
  const first = validConversations.value[0]
  if (first?.id) {
    await selectConversation(first.id)
  }
})

onUnmounted(() => {
  messagingStore.disconnectChat()
  if (peopleSearchTimer) clearTimeout(peopleSearchTimer)
  if (groupSearchTimer) clearTimeout(groupSearchTimer)
})

watch(
  () => getConversationIdFromRoute(),
  async (id, prev) => {
    if (id && id !== prev) {
      await openConversation(id)
      return
    }
    if (!id && prev) {
      selectedConversation.value = null
      messagingStore.disconnectChat()
    }
  }
)

watch(
  () => messagingStore.messages.length,
  () => {
    void scrollToBottom()
  }
)
</script>
