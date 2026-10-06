<template>
  <AppLayout>
    <div class="max-w-[1280px] mx-auto w-full px-4 md:px-6 lg:px-10 py-6 md:py-10">
      <div v-if="jobsStore.loading" class="flex justify-center py-12">
        <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
      </div>
      <div v-else-if="!jobsStore.currentJob" class="text-center py-16">
        <p class="text-slate-500 mb-4">Job not found or you don't have access.</p>
        <Button variant="default" @click="router.push('/jobs')">Back to Jobs</Button>
      </div>
      <div v-else-if="jobsStore.currentJob" class="space-y-6 md:space-y-8">
        <div class="flex items-center gap-2 mb-4 md:mb-8 text-xs font-bold uppercase tracking-widest text-gray-400">
          <router-link to="/dashboard" class="hover:text-midnight">Home</router-link>
          <span class="material-symbols-outlined text-[10px]">chevron_right</span>
          <span class="hover:text-midnight">Job</span>
          <span class="material-symbols-outlined text-[10px]">chevron_right</span>
          <span class="text-midnight">Job Details</span>
        </div>
        <div class="flex flex-col lg:flex-row gap-6 lg:gap-10">
          <div class="flex-1 space-y-6 lg:space-y-8">
            <Card class="bg-white rounded-xl md:rounded-2xl p-6 md:p-8 lg:p-10 shadow-sm border border-gray-100">
              <CardContent class="p-0">
                <div class="flex flex-col gap-3 md:gap-4">
                  <div class="flex items-center gap-2 md:gap-3 flex-wrap">
                    <span class="px-2 md:px-3 py-1 bg-amber/10 text-amber text-[9px] md:text-[10px] font-black uppercase tracking-widest rounded-full">Urgent Hire</span>
                    <span class="text-gray-400 text-xs md:text-sm">Posted {{ formatDate(jobsStore.currentJob.created_at) }}</span>
                    <div v-if="isJobOwner" class="flex flex-col gap-1.5 ml-auto items-end">
                      <span class="text-xs font-bold uppercase tracking-wider text-slate-400 self-start sm:self-end">Status</span>
                      <Select v-model="jobStatusValue">
                        <SelectTrigger
                          class="!h-10 !w-auto min-w-[10rem] !border-slate-200 !bg-white !text-midnight !placeholder:text-slate-500 focus:!ring-amber/20"
                        >
                          <SelectValue placeholder="Choose status" />
                        </SelectTrigger>
                        <SelectContent class="rounded-xl border border-slate-200 bg-white text-slate-900">
                          <SelectItem value="DRAFT" class="focus:bg-slate-100 focus:text-slate-900 data-[highlighted]:bg-slate-100 data-[highlighted]:text-slate-900">Draft</SelectItem>
                          <SelectItem value="OPEN" class="focus:bg-slate-100 focus:text-slate-900 data-[highlighted]:bg-slate-100 data-[highlighted]:text-slate-900">Open</SelectItem>
                          <SelectItem value="IN_PROGRESS" class="focus:bg-slate-100 focus:text-slate-900 data-[highlighted]:bg-slate-100 data-[highlighted]:text-slate-900">In Progress</SelectItem>
                          <SelectItem value="COMPLETED" class="focus:bg-slate-100 focus:text-slate-900 data-[highlighted]:bg-slate-100 data-[highlighted]:text-slate-900">Completed</SelectItem>
                          <SelectItem value="CANCELLED" class="focus:bg-slate-100 focus:text-slate-900 data-[highlighted]:bg-slate-100 data-[highlighted]:text-slate-900">Cancelled</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div class="flex items-start gap-3">
                    <h1 class="text-midnight text-3xl sm:text-4xl font-extrabold leading-tight tracking-tight flex-1 min-w-0">
                      {{ jobsStore.currentJob.title }}
                    </h1>
                    <div
                      v-if="isJobOwner"
                      ref="ownerMenuRef"
                      class="relative shrink-0"
                    >
                      <button
                        type="button"
                        class="grid size-9 place-items-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-midnight transition-colors"
                        :class="ownerMenuOpen ? 'bg-slate-100 text-midnight' : ''"
                        :aria-expanded="ownerMenuOpen"
                        aria-haspopup="menu"
                        aria-label="Job actions"
                        @click="ownerMenuOpen = !ownerMenuOpen"
                      >
                        <span class="material-symbols-outlined text-xl">more_vert</span>
                      </button>

                      <div
                        v-if="ownerMenuOpen"
                        role="menu"
                        class="absolute right-0 top-full mt-1 z-30 min-w-[10rem] rounded-lg border border-slate-200 bg-white py-1 shadow-md"
                      >
                        <button
                          type="button"
                          role="menuitem"
                          class="flex w-full items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                          @click="goEditJob"
                        >
                          <span class="material-symbols-outlined text-lg">edit</span>
                          Edit
                        </button>
                        <button
                          type="button"
                          role="menuitem"
                          class="flex w-full items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50"
                          @click="openDeleteFromMenu"
                        >
                          <span class="material-symbols-outlined text-lg">delete</span>
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                  <div class="flex flex-wrap gap-6 pt-2">
                    <div v-if="jobAddressDisplay" class="flex items-center gap-2 text-gray-600">
                      <span class="material-symbols-outlined text-amber text-xl">location_on</span>
                      <span class="text-sm font-medium">{{ jobAddressDisplay }}</span>
                    </div>
                    <div class="flex items-center gap-2 text-gray-600">
                      <span class="material-symbols-outlined text-amber text-xl">payments</span>
                      <span class="text-sm font-medium">{{ jobBudgetLabel }}</span>
                    </div>
                  </div>
                  <div v-if="hasJobLocation" class="mt-6 relative h-[240px] w-full rounded-xl overflow-hidden border border-gray-200">
                    <LocationMap
                      :key="`job-map-${jobMapLat}-${jobMapLng}`"
                      :lat="jobMapLat"
                      :lng="jobMapLng"
                      :pinned="true"
                      :interactive="false"
                      :zoom="14"
                      :tooltip="jobMapTooltip"
                    />
                  </div>
                </div>
                <div class="mt-12 space-y-8">
                  <section>
                    <h3 class="text-lg font-bold text-midnight mb-4 flex items-center gap-2">
                      <span class="w-1 h-6 bg-amber rounded-full"></span>
                      Project Description
                    </h3>
                    <div class="text-gray-600 space-y-4 leading-relaxed text-lg">
                      <p>{{ jobsStore.currentJob.description }}</p>
                    </div>
                  </section>
                  <section v-if="jobTags.length" class="pt-8 border-t border-gray-100">
                    <h3 class="text-lg font-bold text-midnight mb-6">Required Skills & Expertise</h3>
                    <div class="flex flex-wrap gap-3">
                      <span
                        v-for="tag in jobTags"
                        :key="tag"
                        class="px-5 py-2.5 bg-gray-100 text-midnight text-sm font-bold rounded-xl hover:bg-midnight hover:text-white transition-all cursor-default"
                      >
                        {{ tag }}
                      </span>
                    </div>
                  </section>
                </div>
              </CardContent>
            </Card>

            <Card v-if="isJobOwner" class="bg-white rounded-2xl p-6 md:p-10 shadow-sm border border-gray-100">
              <div class="flex gap-6 border-b border-slate-200 mb-6">
                <button
                  type="button"
                  class="relative pb-3 text-sm font-bold transition-colors"
                  :class="ownerPanelTab === 'applications' ? 'text-amber' : 'text-slate-500 hover:text-midnight'"
                  @click="ownerPanelTab = 'applications'"
                >
                  Applications
                  <span
                    v-if="applicationsForThisJob.length"
                    class="ml-1.5 text-xs font-semibold text-slate-400"
                  >({{ applicationsForThisJob.length }})</span>
                  <span
                    v-if="ownerPanelTab === 'applications'"
                    class="absolute bottom-0 left-0 h-1 w-full bg-amber rounded-t-full"
                  />
                </button>
                <button
                  type="button"
                  class="relative pb-3 text-sm font-bold transition-colors"
                  :class="ownerPanelTab === 'invitations' ? 'text-amber' : 'text-slate-500 hover:text-midnight'"
                  @click="ownerPanelTab = 'invitations'"
                >
                  Invitations
                  <span
                    v-if="invitationsForThisJob.length"
                    class="ml-1.5 text-xs font-semibold text-slate-400"
                  >({{ invitationsForThisJob.length }})</span>
                  <span
                    v-if="ownerPanelTab === 'invitations'"
                    class="absolute bottom-0 left-0 h-1 w-full bg-amber rounded-t-full"
                  />
                </button>
              </div>

              <!-- Applications tab -->
              <div v-if="ownerPanelTab === 'applications'">
                <ul v-if="applicationsForThisJob.length" class="divide-y divide-gray-100">
                  <li v-for="app in applicationsForThisJob" :key="app.id" class="py-6 first:pt-0">
                    <div class="flex flex-col gap-3">
                      <div class="flex items-start justify-between flex-wrap gap-3">
                        <div class="flex items-center gap-3 min-w-0">
                          <div
                            v-if="app.provider_summary?.avatar"
                            class="size-11 rounded-xl bg-cover bg-center shrink-0 ring-2 ring-slate-100"
                            :style="{ backgroundImage: `url(${app.provider_summary.avatar})` }"
                          />
                          <div
                            v-else
                            class="size-11 rounded-xl bg-slate-100 text-amber font-black flex items-center justify-center shrink-0"
                          >
                            {{ providerInitials(app) }}
                          </div>
                          <div class="min-w-0">
                            <router-link
                              v-if="providerProfileId(app)"
                              :to="`/providers/${providerProfileId(app)}`"
                              class="font-semibold text-midnight hover:text-amber transition-colors"
                            >
                              {{ app.provider_summary?.full_name || app.provider_name || 'Provider' }}
                            </router-link>
                            <span v-else class="font-semibold text-midnight">{{ app.provider_name || 'Provider' }}</span>
                            <div class="flex flex-wrap items-center gap-2 mt-0.5 text-xs text-slate-500">
                              <span
                                v-if="app.provider_summary?.is_verified"
                                class="inline-flex items-center gap-0.5 text-amber font-bold"
                              >
                                <span class="material-symbols-outlined text-sm">verified</span>
                                Verified
                              </span>
                              <span v-if="app.provider_summary?.location">{{ app.provider_summary.location }}</span>
                              <span v-if="app.provider_summary?.rating?.count">
                                ★ {{ Number(app.provider_summary.rating.average).toFixed(1) }}
                                ({{ app.provider_summary.rating.count }})
                              </span>
                            </div>
                          </div>
                        </div>
                        <span
                          class="text-xs font-medium px-2 py-1 rounded-full"
                          :class="app.status === 'ACCEPTED' ? 'bg-green-100 text-green-800' : app.status === 'REJECTED' ? 'bg-red-100 text-red-800' : 'bg-slate-100 text-slate-700'"
                        >
                          {{ app.status }}
                        </span>
                      </div>

                      <div class="flex flex-wrap gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          class="border-slate-200 text-slate-700"
                          @click="toggleProposal(app.id)"
                        >
                          <span class="material-symbols-outlined text-sm">{{ expandedProposalId === app.id ? 'expand_less' : 'description' }}</span>
                          {{ expandedProposalId === app.id ? 'Hide proposal' : 'View proposal' }}
                        </Button>
                        <Button v-if="app.status === 'PENDING'" size="sm" @click="handleApplicationStatus(app.id, 'ACCEPTED')">Accept</Button>
                        <Button v-if="app.status === 'PENDING'" size="sm" variant="outline" @click="handleApplicationStatus(app.id, 'REJECTED')">Reject</Button>
                        <Button size="sm" variant="outline" :disabled="messageLoading === app.id" @click="startConversation(app)">
                          <span v-if="messageLoading === app.id" class="material-symbols-outlined animate-spin text-sm">refresh</span>
                          <span v-else class="material-symbols-outlined text-sm">chat</span>
                          Message
                        </Button>
                        <Button v-if="app.status === 'ACCEPTED'" size="sm" :disabled="contractLoading === app.id" @click="createContractFromApplication(app)">
                          <span v-if="contractLoading === app.id" class="material-symbols-outlined animate-spin text-sm">refresh</span>
                          <span v-else class="material-symbols-outlined text-sm">description</span>
                          Create Contract
                        </Button>
                      </div>

                      <div
                        v-if="expandedProposalId === app.id"
                        class="rounded-xl border border-slate-100 bg-slate-50 p-4 space-y-3"
                      >
                        <div v-if="app.proposed_rate != null">
                          <p class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">Proposed rate</p>
                          <p class="text-midnight font-semibold">Br {{ Number(app.proposed_rate).toLocaleString() }}/hr</p>
                        </div>
                        <div>
                          <p class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">Cover letter</p>
                          <p v-if="app.cover_letter" class="text-slate-700 text-sm whitespace-pre-wrap leading-relaxed">{{ app.cover_letter }}</p>
                          <p v-else class="text-slate-400 text-sm italic">No message provided.</p>
                        </div>
                        <p v-if="app.applied_at" class="text-xs text-slate-400">Submitted {{ formatAppliedAt(app.applied_at) }}</p>
                      </div>
                    </div>
                  </li>
                </ul>
                <p v-else class="text-gray-500 text-sm py-6">No applications yet.</p>
              </div>

              <!-- Invitations tab -->
              <div v-else class="space-y-5">
                <p class="text-gray-500 text-sm">
                  Browse providers below, optionally filter by this job’s skills, then invite.
                </p>
                <div class="flex flex-wrap gap-2">
                  <button
                    type="button"
                    class="px-3 py-1.5 rounded-lg text-xs font-bold border transition-colors"
                    :class="inviteSkillFilter === '__all__'
                      ? 'bg-amber/15 border-amber/40 text-amber'
                      : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'"
                    @click="setInviteSkillFilter('__all__')"
                  >
                    All providers
                  </button>
                  <button
                    v-if="jobSkillOptions.length"
                    type="button"
                    class="px-3 py-1.5 rounded-lg text-xs font-bold border transition-colors"
                    :class="inviteSkillFilter === '__job__'
                      ? 'bg-amber/15 border-amber/40 text-amber'
                      : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'"
                    @click="setInviteSkillFilter('__job__')"
                  >
                    Match job skills
                  </button>
                  <button
                    v-for="s in jobSkillOptions"
                    :key="s.id"
                    type="button"
                    class="px-3 py-1.5 rounded-lg text-xs font-bold border transition-colors"
                    :class="inviteSkillFilter === s.id
                      ? 'bg-amber/15 border-amber/40 text-amber'
                      : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'"
                    @click="setInviteSkillFilter(s.id)"
                  >
                    {{ s.name }}
                  </button>
                </div>

                <div class="flex flex-col lg:flex-row gap-3 lg:items-end">
                  <div class="flex-1 space-y-1.5">
                    <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Search</span>
                    <div class="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-50 border border-slate-200">
                      <span class="material-symbols-outlined text-amber text-xl">search</span>
                      <input
                        v-model="inviteQuery"
                        type="search"
                        class="w-full bg-transparent outline-none text-sm text-midnight placeholder:text-slate-400"
                        placeholder="Name, skill, or location…"
                        @keydown.enter.prevent="runInviteSearch"
                      />
                    </div>
                  </div>
                  <div class="sm:w-48 space-y-1.5">
                    <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Sort</span>
                    <Select :model-value="inviteOrdering" @update:model-value="onInviteOrderingChange">
                      <SelectTrigger class="!h-11 !w-full !rounded-xl !border-slate-200 !bg-white !text-slate-900 focus:!ring-amber/20">
                        <SelectValue placeholder="Top rated" />
                      </SelectTrigger>
                      <SelectContent class="rounded-xl border border-slate-200 bg-white text-slate-900">
                        <SelectItem value="-rating" class="focus:bg-slate-100 focus:text-slate-900 data-[highlighted]:bg-slate-100 data-[highlighted]:text-slate-900">Top rated</SelectItem>
                        <SelectItem value="hourly_rate" class="focus:bg-slate-100 focus:text-slate-900 data-[highlighted]:bg-slate-100 data-[highlighted]:text-slate-900">Low to high</SelectItem>
                        <SelectItem value="-hourly_rate" class="focus:bg-slate-100 focus:text-slate-900 data-[highlighted]:bg-slate-100 data-[highlighted]:text-slate-900">High to low</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button
                    type="button"
                    variant="secondary"
                    class="bg-midnight text-white hover:bg-slate-800 h-11 px-5"
                    :disabled="inviteProvidersLoading"
                    @click="runInviteSearch"
                  >
                    Search
                  </Button>
                </div>

                <FormField>
                  <Label>Message (optional)</Label>
                  <textarea
                    v-model="inviteMessage"
                    class="w-full rounded-xl border border-slate-200 bg-white text-midnight focus:ring-2 focus:ring-amber/20 focus:border-amber p-4 min-h-[72px] text-sm"
                    placeholder="Add a personal note to invitations…"
                    :disabled="!!inviteLoadingId"
                  />
                </FormField>
                <p v-if="inviteError" class="text-sm text-red-600">{{ inviteError }}</p>

                <div class="flex items-center justify-between gap-2">
                  <p class="text-sm text-slate-500">
                    <span v-if="inviteProvidersLoading">Loading providers…</span>
                    <span v-else>{{ inviteProvidersTotal }} provider{{ inviteProvidersTotal === 1 ? '' : 's' }}</span>
                  </p>
                </div>

                <div v-if="inviteProvidersLoading && !inviteProviders.length" class="flex justify-center py-10">
                  <span class="material-symbols-outlined animate-spin text-3xl text-amber">refresh</span>
                </div>
                <div
                  v-else-if="!inviteProviders.length"
                  class="text-center py-10 rounded-xl border border-dashed border-slate-200 bg-slate-50"
                >
                  <p class="text-slate-500 text-sm">No providers found. Try clearing search or skill filters.</p>
                </div>
                <ul v-else class="divide-y divide-slate-100 rounded-xl border border-slate-200 overflow-hidden" :class="inviteProvidersLoading ? 'opacity-60' : ''">
                  <li
                    v-for="p in inviteProviders"
                    :key="p.user_id"
                    class="flex flex-col sm:flex-row sm:items-center gap-3 p-4 bg-white hover:bg-slate-50/80"
                  >
                    <div class="flex items-center gap-3 min-w-0 flex-1">
                      <div
                        v-if="p.avatar"
                        class="size-11 rounded-xl bg-cover bg-center shrink-0 ring-2 ring-slate-100"
                        :style="{ backgroundImage: `url(${p.avatar})` }"
                      />
                      <div
                        v-else
                        class="size-11 rounded-xl bg-slate-100 text-amber font-black flex items-center justify-center shrink-0"
                      >
                        {{ inviteProviderInitials(p.full_name) }}
                      </div>
                      <div class="min-w-0">
                        <div class="flex items-center gap-1.5 flex-wrap">
                          <router-link
                            :to="`/providers/${p.user_id}`"
                            class="font-semibold text-midnight hover:text-amber truncate"
                          >
                            {{ p.full_name || 'Provider' }}
                          </router-link>
                          <span
                            v-if="p.is_verified"
                            class="material-symbols-outlined text-amber text-base"
                            title="Verified"
                          >verified</span>
                        </div>
                        <p v-if="p.location" class="text-xs text-slate-500 truncate">{{ p.location }}</p>
                        <div v-if="p.headline_skills?.length" class="flex flex-wrap gap-1 mt-1">
                          <span
                            v-for="s in p.headline_skills.slice(0, 3)"
                            :key="s.id"
                            class="px-1.5 py-0.5 text-[10px] font-semibold rounded bg-amber/10 text-amber"
                          >
                            {{ s.name }}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div class="flex items-center gap-3 shrink-0 sm:ml-auto">
                      <div class="text-right text-xs text-slate-500 hidden sm:block">
                        <p v-if="p.hourly_rate" class="font-bold text-midnight text-sm">
                          Br {{ Number(p.hourly_rate).toLocaleString() }}/hr
                        </p>
                        <p v-if="p.rating?.count > 0">
                          ★ {{ Number(p.rating.average).toFixed(1) }} ({{ p.rating.count }})
                        </p>
                      </div>
                      <span
                        v-if="isProviderInvited(p.user_id)"
                        class="text-xs font-bold px-2.5 py-1 rounded-full bg-slate-100 text-slate-600"
                      >
                        Invited
                      </span>
                      <span
                        v-else-if="isProviderApplied(p.user_id)"
                        class="text-xs font-bold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700"
                      >
                        Applied
                      </span>
                      <Button
                        v-else
                        size="sm"
                        class="bg-amber text-midnight hover:bg-amber-dark"
                        :loading="inviteLoadingId === p.user_id"
                        :disabled="!!inviteLoadingId"
                        @click="inviteProviderById(p.user_id)"
                      >
                        <span class="material-symbols-outlined text-sm">send</span>
                        Invite
                      </Button>
                    </div>
                  </li>
                </ul>

                <PaginationBar
                  :current-page="invitePage"
                  :total-pages="inviteTotalPages"
                  :total-count="inviteProvidersTotal"
                  :page-size="invitePageSize"
                  :loading="inviteProvidersLoading"
                  @go-to-page="goInvitePage"
                  @update-page-size="onInvitePageSizeChange"
                />

                <div v-if="invitationsForThisJob.length" class="pt-4 border-t border-gray-100">
                  <h4 class="text-sm font-bold text-midnight mb-3">Invitations sent</h4>
                  <ul class="space-y-2">
                    <li
                      v-for="inv in invitationsForThisJob"
                      :key="inv.id"
                      class="flex flex-wrap items-center justify-between gap-2 text-sm py-2 px-3 rounded-lg bg-gray-50"
                    >
                      <span class="text-gray-700">{{ getInvitationProviderDisplay(inv) }}</span>
                      <div class="flex items-center gap-2">
                        <span
                          class="text-xs font-medium px-2 py-0.5 rounded-full"
                          :class="inv.status === 'PENDING' ? 'bg-amber/10 text-amber' : inv.status === 'ACCEPTED' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
                        >
                          {{ inv.status }}
                        </span>
                        <Button
                          v-if="inv.status === 'ACCEPTED' && inv.provider"
                          size="sm"
                          :disabled="contractLoading === inv.id"
                          @click="createContractFromInvitation(inv)"
                        >
                          <span v-if="contractLoading === inv.id" class="material-symbols-outlined animate-spin text-sm">refresh</span>
                          <span v-else class="material-symbols-outlined text-sm">description</span>
                          Create Contract
                        </Button>
                      </div>
                    </li>
                  </ul>
                </div>
              </div>
            </Card>

            <Card v-if="authStore.isProvider && !isJobOwner && providerHasInvitationForThisJob" class="bg-white rounded-2xl p-10 shadow-sm border border-gray-100 border-amber/30 bg-amber/5">
              <CardHeader>
                <CardTitle class="text-lg font-bold text-midnight flex items-center gap-2">
                  <span class="material-symbols-outlined text-amber text-xl">mail</span>
                  You've been invited
                </CardTitle>
                <p class="text-gray-600 text-sm mt-1">The client has invited you to this job. Accept or decline from your invitations, then you can message them here.</p>
              </CardHeader>
              <CardContent class="flex flex-col gap-3">
                <router-link to="/invitations">
                  <Button variant="default" size="default" class="bg-amber text-midnight hover:bg-amber-dark">
                    <span class="material-symbols-outlined mr-2 text-lg">inbox</span>
                    View invitations
                  </Button>
                </router-link>
                <router-link to="/messages">
                  <Button variant="outline" size="default" class="border-slate-200">
                    <span class="material-symbols-outlined mr-2 text-lg">chat</span>
                    Open messages
                  </Button>
                </router-link>
              </CardContent>
            </Card>
            <Card
              v-else-if="authStore.isProvider && !isJobOwner && myApplication"
              class="bg-white rounded-2xl p-10 shadow-sm border border-gray-100"
            >
              <CardHeader>
                <CardTitle class="text-lg font-bold text-midnight flex items-center gap-2">
                  <span class="material-symbols-outlined text-amber text-xl">assignment_turned_in</span>
                  Your application
                </CardTitle>
              </CardHeader>
              <CardContent class="space-y-4">
                <div class="flex flex-wrap items-center gap-2">
                  <span class="text-sm text-slate-500">Status</span>
                  <span
                    class="text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide"
                    :class="applicationStatusClass(myApplication.status)"
                  >
                    {{ formatApplicationStatus(myApplication.status) }}
                  </span>
                </div>
                <p v-if="myApplication.cover_letter" class="text-slate-600 text-sm whitespace-pre-wrap">{{ myApplication.cover_letter }}</p>
                <p v-if="myApplication.proposed_rate != null && myApplication.proposed_rate !== ''" class="text-sm text-slate-500">
                  Proposed rate: Br {{ Number(myApplication.proposed_rate).toLocaleString() }}/hr
                </p>
                <p class="text-xs text-slate-400">Submitted {{ formatAppliedAt(myApplication.applied_at) }}</p>
              </CardContent>
            </Card>
            <Card
              v-else-if="providerCanApply"
              id="apply-form"
              class="bg-white rounded-2xl p-10 shadow-sm border border-gray-100"
            >
              <CardHeader>
                <CardTitle class="text-lg font-bold text-midnight mb-8">Apply for this Job</CardTitle>
              </CardHeader>
              <CardContent>
                <form @submit.prevent="handleApply" class="space-y-4">
                  <FormField :error="applicationErrors.message">
                    <Label>Message</Label>
                    <textarea
                      v-model="applicationForm.message"
                      class="w-full rounded-xl border border-slate-200 bg-white text-midnight focus:ring-2 focus:ring-amber/20 focus:border-amber p-4 min-h-[120px]"
                      :class="applicationErrors.message ? 'border-red-500' : ''"
                      placeholder="Tell the client why you're the right fit..."
                    ></textarea>
                  </FormField>
                  <FormField :error="applicationErrors.proposed_rate">
                    <Label>{{ isHourlyJob ? 'Proposed Rate (Br/hr)' : 'Proposed Price (Br)' }}</Label>
                    <Input
                      v-model="applicationForm.proposed_rate"
                      type="number"
                      step="0.01"
                      min="0"
                      :max="jobBudgetCeiling ?? undefined"
                      :placeholder="isHourlyJob ? 'Your hourly rate' : 'Your total price'"
                      :error="applicationErrors.proposed_rate"
                      @blur="validateProposedRateField"
                    />
                    <p v-if="jobBudgetCeiling != null" class="text-xs text-slate-500 mt-1">
                      Must be Br {{ jobBudgetCeiling.toLocaleString() }}{{ isHourlyJob ? '/hr' : '' }} or less
                    </p>
                  </FormField>
                  <Button type="submit" :loading="jobsStore.loading" variant="default" size="lg" class="w-full">
                    Submit Application
                  </Button>
                </form>
              </CardContent>
            </Card>
            <Card
              v-else-if="!authStore.isAuthenticated && !isJobOwner"
              class="bg-white rounded-2xl p-10 shadow-sm border border-gray-100"
            >
              <CardHeader>
                <CardTitle class="text-lg font-bold text-midnight">Want to apply?</CardTitle>
              </CardHeader>
              <CardContent class="space-y-4">
                <p class="text-slate-600 text-sm mb-4">Sign in as a service provider to submit a proposal for this job.</p>
                <router-link :to="{ name: 'login', query: { redirect: route.fullPath } }">
                  <Button variant="default" size="lg" class="w-full">Sign in to apply</Button>
                </router-link>
              </CardContent>
            </Card>
            <Card v-if="showClientProfileCard" class="bg-white rounded-2xl p-10 shadow-sm border border-gray-100">
              <CardHeader>
                <CardTitle class="text-lg font-bold text-midnight mb-8">Client Profile</CardTitle>
              </CardHeader>
              <CardContent class="p-0">
                <div class="flex flex-col md:flex-row items-start gap-8">
                  <div class="relative shrink-0">
                    <div
                      v-if="clientAvatarUrl"
                      class="bg-center bg-no-repeat aspect-square bg-cover rounded-2xl size-24 ring-4 ring-gray-50 shadow-inner"
                      :style="{ backgroundImage: `url(${clientAvatarUrl})` }"
                    />
                    <div
                      v-else
                      class="flex items-center justify-center aspect-square rounded-2xl size-24 ring-4 ring-gray-50 shadow-inner bg-slate-100 text-amber text-2xl font-black"
                    >
                      {{ clientInitials }}
                    </div>
                  </div>
                  <div class="flex-1 min-w-0">
                    <h4 class="text-xl font-extrabold text-midnight mb-1">{{ clientDisplayName }}</h4>
                    <p v-if="clientMemberSinceLabel" class="text-gray-500 font-medium mb-4">
                      Member since {{ clientMemberSinceLabel }}
                    </p>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
                      <div v-if="clientProfileLocation" class="space-y-1">
                        <p class="text-xs text-gray-400 font-bold uppercase tracking-wider">Location</p>
                        <p class="text-midnight font-bold">{{ clientProfileLocation }}</p>
                      </div>
                      <div class="space-y-1">
                        <p class="text-xs text-gray-400 font-bold uppercase tracking-wider">Rating</p>
                        <div v-if="clientRatingDisplay" class="flex items-center gap-1">
                          <span class="text-midnight font-bold">{{ clientRatingDisplay.average }}</span>
                          <span class="material-symbols-outlined text-amber text-sm fill-1">star</span>
                          <span class="text-slate-500 text-sm">({{ clientRatingDisplay.count }} reviews)</span>
                        </div>
                        <p v-else class="text-slate-500 text-sm">No reviews yet</p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
          <div class="lg:w-[380px] space-y-4 md:space-y-6">
            <Card class="bg-midnight rounded-2xl md:rounded-3xl p-6 md:p-8 shadow-2xl lg:sticky lg:top-28 overflow-hidden">
              <div class="absolute top-0 right-0 -mr-16 -mt-16 w-32 h-32 bg-amber/10 blur-3xl rounded-full"></div>
              <div class="relative z-10 space-y-8">
                <div>
                  <p class="text-amber text-xs font-black uppercase tracking-[0.2em] mb-2">{{ isHourlyJob ? 'Hourly rate (Br/hr)' : 'Investment' }}</p>
                  <div class="flex items-baseline gap-2">
                    <span class="text-white text-4xl font-black tracking-tight">Br {{ formatBudgetMax(jobsStore.currentJob.budget_max) }}</span>
                    <span class="text-gray-400 text-sm font-medium">{{ isHourlyJob ? 'Br/hr' : 'max budget' }}</span>
                  </div>
                </div>
                <div class="space-y-4">
                  <Button
                    v-if="providerCanApply"
                    variant="default"
                    size="lg"
                    type="button"
                    class="w-full h-16 bg-amber text-midnight text-lg font-black shadow-lg shadow-amber/30 hover:shadow-amber/40 hover:scale-[1.02] transition-all"
                    @click="scrollToApplyForm"
                  >
                    Apply Now
                  </Button>
                  <router-link
                    v-else-if="!authStore.isAuthenticated && !isJobOwner"
                    :to="{ name: 'login', query: { redirect: route.fullPath } }"
                    class="block"
                  >
                    <Button
                      variant="default"
                      size="lg"
                      type="button"
                      class="w-full h-16 bg-amber text-midnight text-lg font-black shadow-lg shadow-amber/30"
                    >
                      Sign in to apply
                    </Button>
                  </router-link>
                  <div
                    v-else-if="authStore.isProvider && !isJobOwner && myApplication"
                    class="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-4 text-center"
                  >
                    <p class="text-amber text-xs font-black uppercase tracking-widest mb-1">Already applied</p>
                    <p class="text-white font-bold">{{ formatApplicationStatus(myApplication.status) }}</p>
                  </div>
                  <Button variant="outline" size="lg" class="w-full h-14 border-2 border-midnight-light bg-midnight-light/50 text-white hover:bg-midnight-light">
                    <span class="material-symbols-outlined text-xl">bookmark</span>
                    Save Project
                  </Button>
                </div>
                <div v-if="jobsStore.currentJob" class="pt-8 border-t border-white/10">
                  <div class="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/10">
                    <div class="flex items-center gap-3">
                      <div class="p-2 rounded-lg bg-amber/10">
                        <span class="material-symbols-outlined text-amber">groups</span>
                      </div>
                      <span class="text-sm text-gray-300 font-medium">Proposals</span>
                    </div>
                    <span class="text-white font-bold">{{ applicationsCountForJob }}</span>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>

    <Dialog v-model:open="showDeleteConfirm">
      <DialogContent class="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Delete job post</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete this job? This cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <DialogClose as-child>
            <Button type="button" variant="outline">Cancel</Button>
          </DialogClose>
          <Button
            type="button"
            variant="default"
            class="bg-red-600 hover:bg-red-700 text-white"
            :loading="deleteLoading"
            @click="confirmDeleteJob"
          >
            Delete
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </AppLayout>
</template>
<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { onClickOutside } from '@vueuse/core'
import { useAuthStore } from '@/stores/auth'
import { useJobsStore } from '@/stores/jobs'
import { useMessagingStore } from '@/stores/messaging'
import AppLayout from '@/components/AppLayout.vue'
import LocationMap from '@/components/LocationMap.vue'
import Card from '@/components/ui/Card.vue'
import CardHeader from '@/components/ui/CardHeader.vue'
import CardTitle from '@/components/ui/CardTitle.vue'
import CardContent from '@/components/ui/CardContent.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Label from '@/components/ui/Label.vue'
import FormField from '@/components/ui/FormField.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogClose,
} from '@/components/ui/dialog'
import { toast } from 'vue-sonner'
import type { JobApplication } from '@/services/jobs'
import { jobAddressText, jobCoordinates } from '@/services/jobs'
import { profilesService, type PublicProvider } from '@/services/profiles'

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const jobsStore = useJobsStore()
const messagingStore = useMessagingStore()
const messageLoading = ref<string | null>(null)
const contractLoading = ref<string | null>(null)
const showDeleteConfirm = ref(false)
const deleteLoading = ref(false)
const ownerMenuOpen = ref(false)
const ownerMenuRef = ref<HTMLElement | null>(null)

onClickOutside(ownerMenuRef, () => {
  ownerMenuOpen.value = false
})

function goEditJob() {
  ownerMenuOpen.value = false
  const id = jobsStore.currentJob?.id
  if (id) void router.push(`/jobs/${id}/edit`)
}

function openDeleteFromMenu() {
  ownerMenuOpen.value = false
  showDeleteConfirm.value = true
}

const jobStatusValue = computed({
  get: () => jobsStore.currentJob?.status ?? '',
  set: (value: string) => {
    if (value && jobsStore.currentJob) handleStatusChange(value)
  },
})

const applicationForm = ref({
  message: '',
  proposed_rate: '',
})

const applicationErrors = ref({
  message: '',
  proposed_rate: '',
})

watch(() => applicationForm.value.message, () => {
  applicationErrors.value.message = ''
})
watch(() => applicationForm.value.proposed_rate, () => {
  applicationErrors.value.proposed_rate = ''
})

const jobTags = computed(() => {
  const job = jobsStore.currentJob
  if (!job) return []
  if (job.tags?.length) return job.tags
  if (job.required_skills?.length) return job.required_skills.map((s: { name: string }) => s.name)
  return []
})

const jobAddressDisplay = computed(() => jobAddressText(jobsStore.currentJob))

const isHourlyJob = computed(() => {
  const job = jobsStore.currentJob
  return job?.payment_schedule === 'HOURLY' || job?.budget_type === 'hourly'
})

/** Max amount/rate the client set — providers must not propose above this. */
const jobBudgetCeiling = computed(() => {
  const job = jobsStore.currentJob
  if (!job) return null
  const raw = job.budget_max ?? job.budget_min
  if (raw == null) return null
  const max = Number(raw)
  if (!Number.isFinite(max)) return null
  return max
})

function proposedRateError(raw: string): string {
  const trimmed = String(raw ?? '').trim()
  if (!trimmed) return 'Proposed rate is required'
  const proposedRate = Number(trimmed)
  if (!Number.isFinite(proposedRate) || proposedRate < 0) {
    return 'Enter a valid proposed rate'
  }
  const ceiling = jobBudgetCeiling.value
  if (ceiling != null && proposedRate > ceiling) {
    const unit = isHourlyJob.value ? '/hr' : ''
    return `Must be Br ${ceiling.toLocaleString()}${unit} or less`
  }
  return ''
}

function validateProposedRateField() {
  applicationErrors.value.proposed_rate = proposedRateError(applicationForm.value.proposed_rate)
}
const jobBudgetLabel = computed(() => {
  const job = jobsStore.currentJob
  if (!job) return ''
  const min = job.budget_min ?? 0
  const max = job.budget_max ?? min
  if (isHourlyJob.value) {
    return min === max ? `Br ${min.toLocaleString()} Br/hr` : `Br ${min.toLocaleString()} – ${max.toLocaleString()} Br/hr`
  }
  if (job.budget_type === 'fixed' || job.payment_schedule === 'FIXED') {
    return `Br ${(max || min).toLocaleString()} fixed`
  }
  return `Br ${min.toLocaleString()} – ${max.toLocaleString()}`
})

const myApplication = computed(() => jobsStore.currentJob?.my_application ?? null)

const providerCanApply = computed(() => {
  return (
    authStore.isAuthenticated &&
    authStore.isProvider &&
    !isJobOwner.value &&
    !providerHasInvitationForThisJob.value &&
    !myApplication.value
  )
})

const expandedProposalId = ref<string | null>(null)
const ownerPanelTab = ref<'applications' | 'invitations'>('applications')

function toggleProposal(id: string) {
  expandedProposalId.value = expandedProposalId.value === id ? null : id
}

function providerProfileId(app: JobApplication): string | null {
  return app.provider_summary?.user_id || (typeof app.provider === 'string' ? app.provider : null) || null
}

function providerInitials(app: JobApplication): string {
  const name = app.provider_summary?.full_name || app.provider_name || 'P'
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  return name.charAt(0).toUpperCase()
}

const clientProfile = computed(() => jobsStore.currentJob?.client_profile ?? null)

const clientDisplayName = computed(() => {
  const job = jobsStore.currentJob
  return (
    clientProfile.value?.full_name ||
    job?.client_name ||
    clientProfile.value?.email ||
    job?.client_email ||
    'Client'
  )
})

const clientAvatarUrl = computed(() => clientProfile.value?.avatar ?? null)

const clientInitials = computed(() => {
  const name = clientDisplayName.value
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  }
  return name.charAt(0).toUpperCase() || 'C'
})

const clientProfileLocation = computed(() => {
  const loc = clientProfile.value?.location?.trim()
  return loc || null
})

const clientMemberSinceLabel = computed(() => {
  const raw = clientProfile.value?.member_since
  if (!raw) return null
  return new Date(raw).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
})

const clientRatingDisplay = computed(() => {
  const rating = jobsStore.currentJob?.client_rating
  if (!rating || rating.count <= 0 || rating.average == null) return null
  return {
    average: Number(rating.average).toFixed(1),
    count: rating.count,
  }
})

const showClientProfileCard = computed(() => {
  if (isJobOwner.value) return false
  const job = jobsStore.currentJob
  return !!(job?.client_profile || job?.client_name || job?.client_email)
})

const isJobOwner = computed(() => {
  const job = jobsStore.currentJob
  const user = authStore.user
  if (!job || !user) return false
  return job.client === user.id
})

const applicationsForThisJob = computed(() => {
  const jobId = jobsStore.currentJob?.id
  if (!jobId) return []
  const apps = jobsStore.applications
  if (!Array.isArray(apps)) return []
  return apps.filter((a: JobApplication) => a.job === jobId)
})

const applicationsCountForJob = computed(() => {
  const job = jobsStore.currentJob
  if (job?.applications_count != null) return job.applications_count
  return applicationsForThisJob.value.length
})

const jobCoords = computed(() => jobCoordinates(jobsStore.currentJob))

const hasJobLocation = computed(() => jobCoords.value != null)

const jobMapLat = computed(() => jobCoords.value?.lat ?? null)

const jobMapLng = computed(() => jobCoords.value?.lng ?? null)

const jobMapTooltip = computed(() => jobAddressText(jobsStore.currentJob) || 'Job location')

const invitationsForThisJob = computed(() => {
  const jobId = jobsStore.currentJob?.id
  if (!jobId) return []
  const list = Array.isArray(jobsStore.invitations) ? jobsStore.invitations : []
  return list.filter((inv: { job: string | { id?: string }; id?: string }) => {
    const invJobId = typeof inv.job === 'object' && inv.job != null ? inv.job.id : inv.job
    return invJobId === jobId
  })
})

/** True when current user (provider) has received an invitation for this job — they should not apply. */
const providerHasInvitationForThisJob = computed(() => invitationsForThisJob.value.length > 0)

const jobSkillOptions = computed(() => {
  const skills = jobsStore.currentJob?.required_skills || []
  return skills.filter((s): s is { id: string; name: string } => !!s?.id && !!s?.name)
})

const inviteQuery = ref('')
const inviteOrdering = ref('-rating')
/** __all__ = no skill filter; __job__ = any of job skills; else a skill id */
const inviteSkillFilter = ref<string>('__all__')
const inviteMessage = ref('')
const inviteError = ref('')
const inviteLoadingId = ref<string | null>(null)
const inviteProvidersLoading = ref(false)
const inviteProviders = ref<PublicProvider[]>([])
const inviteProvidersTotal = ref(0)
const invitePage = ref(1)
const invitePageSize = ref(10)

const inviteTotalPages = computed(() =>
  Math.max(1, Math.ceil(inviteProvidersTotal.value / invitePageSize.value))
)

const invitedProviderIds = computed(() => {
  const ids = new Set<string>()
  for (const inv of invitationsForThisJob.value) {
    const p = (inv as { provider?: string | { id?: string } }).provider
    if (typeof p === 'string' && p) ids.add(p)
    else if (p && typeof p === 'object' && p.id) ids.add(p.id)
  }
  return ids
})

const appliedProviderIds = computed(() => {
  const ids = new Set<string>()
  for (const app of applicationsForThisJob.value) {
    const id = providerProfileId(app)
    if (id) ids.add(id)
  }
  return ids
})

function isProviderInvited(userId: string) {
  return invitedProviderIds.value.has(userId)
}

function isProviderApplied(userId: string) {
  return appliedProviderIds.value.has(userId)
}

function inviteProviderInitials(name: string) {
  const parts = (name || '').trim().split(/\s+/).filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  return (name.charAt(0) || 'P').toUpperCase()
}

function inviteSkillsParam(): string[] | undefined {
  if (inviteSkillFilter.value === '__all__') return undefined
  if (inviteSkillFilter.value === '__job__') {
    const ids = jobSkillOptions.value.map((s) => s.id)
    return ids.length ? ids : undefined
  }
  return [inviteSkillFilter.value]
}

function setInviteSkillFilter(id: string) {
  if (inviteSkillFilter.value === id) return
  inviteSkillFilter.value = id
  invitePage.value = 1
  void fetchInviteProviders()
}

function runInviteSearch() {
  invitePage.value = 1
  void fetchInviteProviders()
}

function onInviteOrderingChange(value: string) {
  if (!value || value === inviteOrdering.value) return
  inviteOrdering.value = value
  invitePage.value = 1
  void fetchInviteProviders()
}

function goInvitePage(page: number) {
  invitePage.value = page
  void fetchInviteProviders()
}

function onInvitePageSizeChange(size: number) {
  invitePageSize.value = size
  invitePage.value = 1
  void fetchInviteProviders()
}

async function fetchInviteProviders() {
  if (!isJobOwner.value || !jobsStore.currentJob) {
    inviteProviders.value = []
    inviteProvidersTotal.value = 0
    return
  }
  inviteProvidersLoading.value = true
  inviteError.value = ''
  try {
    const q = inviteQuery.value.trim() || undefined
    const res = await profilesService.listPublicProviders({
      q,
      search: q,
      skills: inviteSkillsParam(),
      ordering: inviteOrdering.value,
      page: invitePage.value,
      page_size: invitePageSize.value,
    })
    const data = res.data
    if (Array.isArray(data)) {
      inviteProviders.value = data
      inviteProvidersTotal.value = data.length
    } else {
      inviteProviders.value = data.results || []
      inviteProvidersTotal.value = data.count ?? inviteProviders.value.length
    }
  } catch (err: any) {
    console.error('Invite provider search failed', err)
    inviteProviders.value = []
    inviteProvidersTotal.value = 0
    inviteError.value = err.response?.data?.detail || 'Failed to load providers.'
  } finally {
    inviteProvidersLoading.value = false
  }
}

function getInvitationProviderDisplay(inv: { provider_name?: string; provider_email?: string; provider?: string }) {
  if (inv.provider_name) return inv.provider_name
  if (inv.provider_email) return inv.provider_email
  return inv.provider || 'Provider'
}

function formatDate(dateString: string) {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))
  if (hours < 1) return 'just now'
  if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`
  const days = Math.floor(hours / 24)
  return `${days} day${days > 1 ? 's' : ''} ago`
}

function formatApplicationStatus(status: string) {
  const normalized = status.replace(/_/g, ' ').toLowerCase()
  return normalized.charAt(0).toUpperCase() + normalized.slice(1)
}

function applicationStatusClass(status: string) {
  if (status === 'ACCEPTED') return 'bg-emerald-500/10 text-emerald-700'
  if (status === 'REJECTED') return 'bg-red-500/10 text-red-700'
  if (status === 'WITHDRAWN') return 'bg-slate-100 text-slate-600'
  return 'bg-amber/10 text-amber'
}

function formatAppliedAt(dateString: string) {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function scrollToApplyForm() {
  document.getElementById('apply-form')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function formatBudgetMax(max?: number) {
  if (!max) return '0'
  if (max >= 1000) {
    return `${(max / 1000).toFixed(1)}k`
  }
  return max.toString()
}

async function handleApply() {
  if (!jobsStore.currentJob) return

  applicationErrors.value.message = ''
  applicationErrors.value.proposed_rate = ''

  const message = (applicationForm.value.message ?? '').trim()
  const rawRate = String(applicationForm.value.proposed_rate ?? '').trim()
  let valid = true

  if (!message) {
    applicationErrors.value.message = 'Message is required'
    valid = false
  }

  if (!rawRate) {
    applicationErrors.value.proposed_rate = 'Proposed rate is required'
    valid = false
  } else {
    const rateErr = proposedRateError(rawRate)
    if (rateErr) {
      applicationErrors.value.proposed_rate = rateErr
      valid = false
    }
  }

  if (!valid) return

  const proposedRate = Number(rawRate)
  try {
    const jobId = jobsStore.currentJob.id
    await jobsStore.createApplication(jobId, {
      cover_letter: message,
      proposed_rate: proposedRate,
    })
    await jobsStore.fetchJob(jobId)
    toast.success('Application submitted.')
    applicationForm.value = { message: '', proposed_rate: '' }
  } catch (err: any) {
    const data = err.response?.data
    if (data && typeof data === 'object') {
      if (data.cover_letter || data.message) {
        const val = data.cover_letter ?? data.message
        applicationErrors.value.message = Array.isArray(val) ? val[0] : String(val)
      }
      if (data.proposed_rate) {
        const val = data.proposed_rate
        applicationErrors.value.proposed_rate = Array.isArray(val) ? val[0] : String(val)
      }
      if (!applicationErrors.value.message && !applicationErrors.value.proposed_rate) {
        toast.error(data.error || 'Failed to apply for this job. Please try again.')
      }
    } else {
      toast.error('Failed to apply for this job. Please try again.')
    }
  }
}

async function handleStatusChange(newStatus: string) {
  if (!jobsStore.currentJob) return
  try {
    await jobsStore.updateJob(jobsStore.currentJob.id, { status: newStatus })
    toast.success('Job status updated.')
  } catch (err: any) {
    const msg = err.response?.data?.error ?? 'Failed to update status.'
    toast.error(msg)
  }
}

async function confirmDeleteJob() {
  const job = jobsStore.currentJob
  if (!job?.id || !isJobOwner.value) return
  deleteLoading.value = true
  try {
    await jobsStore.deleteJob(job.id)
    showDeleteConfirm.value = false
    toast.success('Job deleted.')
    await router.push('/jobs')
  } catch (err: any) {
    const msg =
      err.response?.data?.error ??
      err.response?.data?.detail ??
      'Failed to delete job.'
    toast.error(msg)
  } finally {
    deleteLoading.value = false
  }
}

async function handleApplicationStatus(applicationId: string, newStatus: 'ACCEPTED' | 'REJECTED') {
  if (!jobsStore.currentJob) return
  try {
    await jobsStore.updateApplication(applicationId, { status: newStatus })
    await jobsStore.fetchApplications(jobsStore.currentJob.id)
    toast.success(newStatus === 'ACCEPTED' ? 'Application accepted.' : 'Application rejected.')
  } catch (err: any) {
    const msg = err.response?.data?.error ?? 'Failed to update application.'
    toast.error(msg)
  }
}

async function startConversation(app: JobApplication) {
  if (!app.job || !jobsStore.currentJob) return
  const otherId = isJobOwner.value ? app.provider : app.job_client
  if (!otherId) return
  messageLoading.value = app.id
  try {
    const conv = await messagingStore.createConversation({
      participant2_id: otherId,
      initial_message: '',
    })
    if (conv?.id && conv.id !== 'undefined') {
      router.push(`/messages/${conv.id}`)
    } else {
      console.log('Conversation created but could not open it.', conv)
      toast.error('Conversation created but could not open it.')
    }
  } catch (err: any) {
    const msg = err.response?.data?.participant2_id?.[0] ?? err.response?.data?.detail ?? 'Failed to start conversation'
    toast.error(msg)
  } finally {
    messageLoading.value = null
  }
}

function createContractFromApplication(app: JobApplication) {
  if (!app.job || !app.provider) return
  contractLoading.value = app.id
  router.push({
    path: '/contracts/create',
    query: { job: app.job, application: app.id, provider: app.provider },
  })
  contractLoading.value = null
}

function createContractFromInvitation(inv: { id?: string; provider?: string }) {
  if (!jobsStore.currentJob?.id || !inv.provider) return
  contractLoading.value = inv.id ?? inv.provider
  router.push({
    path: '/contracts/create',
    query: { job: jobsStore.currentJob.id, provider: inv.provider },
  })
  contractLoading.value = null
}

async function inviteProviderById(providerUserId: string) {
  if (!jobsStore.currentJob) return
  inviteError.value = ''
  inviteLoadingId.value = providerUserId
  try {
    await jobsStore.createInvitation({
      job: jobsStore.currentJob.id,
      provider: providerUserId,
      message: inviteMessage.value.trim() || undefined,
    })
    toast.success('Invitation sent successfully.')
    await jobsStore.fetchInvitations()
  } catch (err: any) {
    inviteError.value =
      jobsStore.error ||
      err.response?.data?.provider?.[0] ||
      err.response?.data?.provider_email?.[0] ||
      err.response?.data?.detail ||
      'Failed to send invitation.'
    toast.error(inviteError.value)
  } finally {
    inviteLoadingId.value = null
  }
}

async function loadJob() {
  const jobId = route.params.id as string
  if (!jobId) return
  jobsStore.currentJob = null
  inviteProviders.value = []
  inviteProvidersTotal.value = 0
  inviteSkillFilter.value = '__all__'
  inviteQuery.value = ''
  invitePage.value = 1
  ownerPanelTab.value = 'applications'
  await jobsStore.fetchJob(jobId)
  if (isJobOwner.value) {
    await jobsStore.fetchApplications(jobId)
    await jobsStore.fetchInvitations()
    await fetchInviteProviders()
  } else if (authStore.isProvider) {
    await jobsStore.fetchInvitations()
  }
}

onMounted(loadJob)

watch(() => route.params.id, () => {
  if (route.name === 'job-detail') loadJob()
})
</script>
