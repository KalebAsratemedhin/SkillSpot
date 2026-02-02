<template>
  <AppLayout>
    <div class="flex-1 bg-midnight">
      <main class="flex-1">
      <section class="bg-midnight pt-8 md:pt-12 pb-12 md:pb-16">
        <div class="mx-auto max-w-[1400px] px-4 md:px-6 lg:px-10">
          <div v-if="profilesStore.loading" class="flex justify-center py-12">
            <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
          </div>
          <div v-else class="flex flex-col md:flex-row items-center gap-10">
            <div class="relative group">
              <div class="h-40 w-40 md:h-52 md:w-52 rounded-2xl ring-4 ring-amber/20 overflow-hidden shadow-2xl shadow-amber/5 relative">
                <div
                  class="h-full w-full bg-cover bg-center transition-transform duration-500 group-hover:scale-110"
                  :style="{
                    backgroundImage: profilePictureUrl
                      ? `url(${profilePictureUrl})`
                      : 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
                  }"
                >
                  <div v-if="!profilePictureUrl" class="h-full w-full flex items-center justify-center text-amber text-6xl font-black">
                    {{ initials }}
                  </div>
                </div>
                <input
                  ref="avatarInputRef"
                  type="file"
                  accept="image/*"
                  class="hidden"
                  @change="onAvatarFileChange"
                />
                <button
                  v-if="authStore.isAuthenticated && profilesStore.profile"
                  type="button"
                  class="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl cursor-pointer"
                  @click="triggerAvatarUpload"
                >
                  <span class="flex flex-col items-center gap-1 text-white text-sm font-semibold">
                    <span class="material-symbols-outlined text-3xl">photo_camera</span>
                    Change photo
                  </span>
                </button>
              </div>
              <div
                v-if="profilesStore.profile?.is_verified"
                class="absolute -bottom-3 -right-3 flex h-10 w-10 items-center justify-center rounded-xl bg-amber text-midnight shadow-lg"
              >
                <span class="material-symbols-outlined filled text-xl">verified</span>
              </div>
            </div>
            <div class="flex-1 text-center md:text-left">
              <div class="flex flex-col md:flex-row md:items-center gap-3 md:gap-4">
                <h1 class="text-3xl md:text-4xl lg:text-5xl font-extrabold tracking-tight text-white">
                  {{ fullName }}
                </h1>
                <div class="flex items-center justify-center md:justify-start gap-2 flex-wrap">
                  <span
                    v-if="profilesStore.profile?.is_verified"
                    class="inline-flex items-center rounded-lg bg-amber/10 px-3 py-1 text-sm font-bold text-amber border border-amber/20"
                  >
                    ELITE PRO
                  </span>
                  <span
                    v-if="primarySkill"
                    class="inline-flex items-center rounded-lg bg-white/5 px-3 py-1 text-sm font-bold text-slate-400"
                  >
                    {{ primarySkill }}
                  </span>
                </div>
              </div>
              <p v-if="profilesStore.profile?.bio" class="mt-3 md:mt-4 text-base md:text-lg lg:text-xl text-slate-400 max-w-2xl font-medium">
                {{ profilesStore.profile.bio }}
              </p>
              <div class="mt-4 md:mt-6 flex flex-wrap items-center justify-center md:justify-start gap-4 md:gap-6">
                <div v-if="ratingStats && (ratingStats.average_rating != null || ratingStats.total_ratings != null)" class="flex items-center gap-3">
                  <div class="flex text-amber">
                    <span
                      v-for="i in 5"
                      :key="i"
                      class="material-symbols-outlined filled text-2xl"
                      :class="i <= Math.round(ratingStats.average_rating ?? 0) ? 'text-amber' : 'text-slate-600'"
                    >
                      star
                    </span>
                  </div>
                  <div class="flex items-baseline gap-1">
                    <span class="text-2xl font-black text-white">{{ (ratingStats.average_rating ?? 0).toFixed(1) }}</span>
                    <span class="text-sm text-slate-400 font-semibold">({{ ratingStats.total_ratings ?? 0 }} Reviews)</span>
                  </div>
                </div>
                <div v-if="ratingStats && (ratingStats.average_rating != null || ratingStats.total_ratings != null)" class="h-6 w-px bg-white/10"></div>
                <div v-if="location" class="flex items-center gap-2 text-slate-400">
                  <span class="material-symbols-outlined text-amber">location_on</span>
                  <span class="font-semibold text-sm tracking-wide uppercase">{{ location }}</span>
                </div>
                <div v-if="profilesStore.providerProfile?.years_of_experience" class="h-6 w-px bg-white/10"></div>
                <div v-if="profilesStore.providerProfile?.years_of_experience" class="flex items-center gap-2 text-slate-400">
                  <span class="material-symbols-outlined text-amber">workspace_premium</span>
                  <span class="font-semibold text-sm tracking-wide">{{ profilesStore.providerProfile.years_of_experience }}+ YEARS EXP</span>
                </div>
              </div>
              <div v-if="authStore.isAuthenticated && profilesStore.profile" class="mt-8 flex flex-col sm:flex-row items-center gap-4">
                <Dialog v-model:open="showEditProfile" @update:open="(v: boolean) => v && initEditForm()">
                  <DialogTrigger as-child>
                    <Button variant="default" size="lg" class="w-full sm:w-auto px-10 py-4">
                      <span class="material-symbols-outlined filled mr-2">edit</span>
                      Edit Profile
                    </Button>
                  </DialogTrigger>
                  <DialogContent class="sm:max-w-[425px]">
                    <DialogHeader>
                      <DialogTitle>Edit profile</DialogTitle>
                      <DialogDescription>Update your profile details. Click save when you're done.</DialogDescription>
                    </DialogHeader>
                    <form id="edit-profile-form" @submit.prevent="saveProfile" class="space-y-4">
                      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <FormField :error="editErrors.first_name">
                          <Label class="text-slate-300">First Name</Label>
                          <Input v-model="editForm.first_name" class="bg-white/5 border-white/10 text-white" />
                        </FormField>
                        <FormField :error="editErrors.last_name">
                          <Label class="text-slate-300">Last Name</Label>
                          <Input v-model="editForm.last_name" class="bg-white/5 border-white/10 text-white" />
                        </FormField>
                      </div>
                      <FormField :error="editErrors.phone_number">
                        <Label class="text-slate-300">Phone</Label>
                        <Input v-model="editForm.phone_number" class="bg-white/5 border-white/10 text-white" />
                      </FormField>
                      <FormField :error="editErrors.location">
                        <Label class="text-slate-300">Location</Label>
                        <Input v-model="editForm.location" class="bg-white/5 border-white/10 text-white" />
                      </FormField>
                      <FormField :error="editErrors.bio">
                        <Label class="text-slate-300">Bio</Label>
                        <textarea
                          v-model="editForm.bio"
                          class="w-full rounded-xl border border-white/10 bg-white/5 text-white p-4 min-h-[100px] focus:ring-2 focus:ring-amber/40"
                          placeholder="Tell clients about yourself..."
                        ></textarea>
                      </FormField>
                    </form>
                    <DialogFooter>
                      <DialogClose as-child>
                        <Button type="button" variant="outline" class="border-white/20 text-white">Cancel</Button>
                      </DialogClose>
                      <Button type="submit" form="edit-profile-form" :loading="profilesStore.loading" variant="default" class="bg-amber text-midnight">
                        Save
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
            </div>
          </div>
        </div>
      </section>
      <div class="mx-auto max-w-[1400px] px-4 md:px-6 lg:px-10 py-8 md:py-12">
        <div class="flex flex-col lg:flex-row gap-8 md:gap-12">
          <div class="flex-1">
            <div class="mb-6 md:mb-10 border-b border-white/5">
              <nav class="flex gap-6 md:gap-10 overflow-x-auto">
                <template v-if="authStore.isProvider">
                  <button
                    v-for="tab in ['portfolio', 'services', 'jobs']"
                    :key="tab"
                    :class="[
                      'relative pb-3 md:pb-4 text-sm md:text-base font-semibold transition-colors whitespace-nowrap capitalize',
                      activeTab === tab ? 'text-amber' : 'text-slate-400 hover:text-white',
                    ]"
                    @click="onTabClick(tab)"
                  >
                    {{ tab }}
                    <span
                      v-if="activeTab === tab"
                      class="absolute bottom-0 left-0 h-1 w-full bg-amber rounded-t-full"
                    ></span>
                  </button>
                </template>
                <template v-else>
                  <button
                    :class="[
                      'relative pb-3 md:pb-4 text-sm md:text-base font-semibold transition-colors whitespace-nowrap',
                      activeTab === 'jobs' ? 'text-amber' : 'text-slate-400 hover:text-white',
                    ]"
                    @click="onTabClick('jobs')"
                  >
                    Jobs
                    <span
                      v-if="activeTab === 'jobs'"
                      class="absolute bottom-0 left-0 h-1 w-full bg-amber rounded-t-full"
                    ></span>
                  </button>
                </template>
              </nav>
            </div>
            <!-- Provider: Portfolio (experiences) -->
            <section v-if="authStore.isProvider && activeTab === 'portfolio'">
              <Card class="bg-midnight-light border-white/10">
                <CardContent class="p-8">
                  <div class="flex items-center justify-between mb-4">
                    <h3 class="text-xl font-bold text-white">Portfolio</h3>
                    <Dialog v-model:open="showAddExperience" @update:open="(v: boolean) => !v && resetExpForm()">
                      <DialogTrigger as-child>
                        <Button variant="outline" size="default" class="border-amber/30 text-amber">
                          <span class="material-symbols-outlined text-lg mr-1">add</span>
                          Add experience
                        </Button>
                      </DialogTrigger>
                      <DialogContent class="sm:max-w-[480px]">
                        <DialogHeader>
                          <DialogTitle>Add experience</DialogTitle>
                          <DialogDescription>Add a role or project. Dates help clients see your journey.</DialogDescription>
                        </DialogHeader>
                        <form id="add-experience-form" @submit.prevent="submitExperience" class="space-y-4">
                          <FormField :error="expErrors.title">
                            <Label class="text-slate-300">Title</Label>
                            <Input v-model="expForm.title" class="bg-white/5 border-white/10 text-white" placeholder="e.g. Senior Plumber" required />
                          </FormField>
                          <FormField :error="expErrors.company_name">
                            <Label class="text-slate-300">Company</Label>
                            <Input v-model="expForm.company_name" class="bg-white/5 border-white/10 text-white" placeholder="e.g. ABC Services" />
                          </FormField>
                          <FormField :error="expErrors.description">
                            <Label class="text-slate-300">Description</Label>
                            <textarea v-model="expForm.description" class="w-full rounded-xl border border-white/10 bg-white/5 text-white p-4 min-h-[80px] placeholder:text-slate-500" placeholder="What did you do there?" />
                          </FormField>
                          <div class="grid grid-cols-2 gap-4">
                            <FormField :error="expErrors.start_date">
                              <Label class="text-slate-300">Start date</Label>
                              <Input v-model="expForm.start_date" type="date" class="bg-white/5 border-white/10 text-white [color-scheme:dark]" required />
                            </FormField>
                            <FormField :error="expErrors.end_date">
                              <Label class="text-slate-300">End date</Label>
                              <Input v-model="expForm.end_date" type="date" class="bg-white/5 border-white/10 text-white [color-scheme:dark]" :disabled="expForm.is_current" />
                            </FormField>
                          </div>
                          <label class="flex items-center gap-2 cursor-pointer">
                            <input v-model="expForm.is_current" type="checkbox" class="rounded border-white/20 bg-white/5 text-amber focus:ring-amber" />
                            <span class="text-slate-300 text-sm">Currently working here</span>
                          </label>
                        </form>
                        <DialogFooter>
                          <DialogClose as-child>
                            <Button type="button" variant="outline" class="border-white/20 text-white">Cancel</Button>
                          </DialogClose>
                          <Button type="submit" form="add-experience-form" :loading="profilesStore.loading" variant="default" class="bg-amber text-midnight">
                            Add experience
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  </div>
                  <div v-if="(profilesStore.providerProfile?.experiences || profilesStore.experiences).length > 0" class="space-y-4">
                    <div
                      v-for="exp in (profilesStore.providerProfile?.experiences || profilesStore.experiences)"
                      :key="exp.id"
                      class="border-l-2 border-amber/30 pl-4 py-2 flex items-start justify-between gap-4"
                    >
                      <div>
                        <div class="flex items-baseline gap-2 mb-1">
                          <h5 class="font-bold text-white">{{ exp.title }}</h5>
                          <span v-if="exp.company_name" class="text-slate-400 text-sm">{{ exp.company_name }}</span>
                        </div>
                        <p v-if="exp.description" class="text-slate-400 text-sm">{{ exp.description }}</p>
                        <p class="text-slate-500 text-xs mt-1">
                          {{ formatDate(exp.start_date) }} - {{ exp.is_current ? 'Present' : formatDate(exp.end_date || '') }}
                        </p>
                      </div>
                      <Button
                        v-if="exp.id"
                        variant="ghost"
                        size="sm"
                        class="text-red-400/80 hover:text-red-400 hover:bg-red-500/10 flex-shrink-0"
                        @click="deleteExperience(exp.id)"
                      >
                        <span class="material-symbols-outlined text-sm">delete</span>
                      </Button>
                    </div>
                  </div>
                  <p v-else class="text-slate-400">No portfolio items yet. Add your experience above.</p>
                </CardContent>
              </Card>
            </section>
            <!-- Provider: Services (skills) -->
            <section v-if="authStore.isProvider && activeTab === 'services'">
              <Card class="bg-midnight-light border-white/10">
                <CardContent class="p-8">
                  <h3 class="text-xl font-bold text-white mb-4">Services</h3>
                  <div v-if="providerSkills.length > 0" class="flex flex-wrap gap-2.5 mb-4">
                    <span
                      v-for="tag in providerSkills"
                      :key="tag.id"
                      class="inline-flex items-center gap-1 rounded-xl bg-amber/10 border border-amber/20 px-4 py-2 text-sm font-bold text-amber"
                    >
                      {{ tag.name }}
                      <button
                        type="button"
                        class="ml-1 text-slate-400 hover:text-red-400"
                        aria-label="Remove skill"
                        @click="removeSkill(tag.id)"
                      >
                        <span class="material-symbols-outlined text-sm">close</span>
                      </button>
                    </span>
                  </div>
                  <div class="flex flex-wrap items-end gap-2 mb-4">
                    <div class="min-w-[200px]">
                      <Label class="text-slate-300 block mb-2">Add skill from list</Label>
                      <Select v-model="selectedSkillId">
                        <SelectTrigger class="w-full bg-white/5 border-white/10 text-white">
                          <SelectValue placeholder="Select a skill..." />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem
                            v-for="tag in availableSkillsToAdd"
                            :key="tag.id"
                            :value="tag.id"
                            class="rounded-lg focus:bg-slate-100 focus:text-slate-900"
                          >
                            {{ tag.name }}
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <Button type="button" variant="default" size="default" class="bg-amber text-midnight" :disabled="!selectedSkillId" @click="addSkill()">
                      Add
                    </Button>
                  </div>
                  <div class="flex flex-wrap items-end gap-2">
                    <div>
                      <Label class="text-slate-300 block mb-2">Or create new skill</Label>
                      <Input
                        v-model="newSkillName"
                        placeholder="e.g. Plumbing, Electrical"
                        class="bg-white/5 border-white/10 text-white min-w-[200px]"
                        @keydown.enter.prevent="addNewSkill()"
                      />
                    </div>
                    <Button type="button" variant="default" size="default" class="bg-amber text-midnight" :disabled="!newSkillName.trim()" :loading="addingNewSkill" @click="addNewSkill()">
                      Create &amp; Add
                    </Button>
                  </div>
                  <p v-if="providerSkills.length === 0" class="text-slate-400 mt-4">Add skills above to show your services.</p>
                </CardContent>
              </Card>
            </section>
            <!-- Jobs tab: contracts with job link + review if completed (provider and client) -->
            <section v-if="activeTab === 'jobs'">
              <div v-if="profileContractsLoading" class="flex justify-center py-12">
                <span class="material-symbols-outlined animate-spin text-4xl text-amber">refresh</span>
              </div>
              <div v-else-if="profileContractsList.length === 0" class="text-center py-12 rounded-2xl border border-white/10 bg-midnight-light">
                <p class="text-slate-400 mb-4">{{ authStore.isClient ? 'No jobs with contracts yet' : 'No hired jobs yet' }}</p>
                <router-link v-if="authStore.isClient" to="/jobs/create">
                  <Button variant="outline" class="border-amber/30 text-amber">Post a job</Button>
                </router-link>
              </div>
              <div v-else class="flex flex-col gap-4">
                <Card
                  v-for="c in profileContractsList"
                  :key="c.id"
                  class="bg-midnight-light border-white/10"
                >
                  <CardContent class="p-6">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div class="min-w-0">
                        <router-link :to="c.job ? `/jobs/${c.job}` : '#'" class="text-lg font-bold text-white hover:text-amber transition-colors line-clamp-1">
                          {{ c.job_title || 'Job' }}
                        </router-link>
                        <span
                          :class="[
                            'inline-block mt-2 text-[10px] font-bold px-2 py-0.5 rounded uppercase',
                            c.status === 'ACTIVE' ? 'bg-amber/20 text-amber' : c.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-500/20 text-slate-400',
                          ]"
                        >
                          {{ c.status === 'ACTIVE' ? 'Active' : c.status === 'COMPLETED' ? 'Completed' : c.status.replace(/_/g, ' ') }}
                        </span>
                      </div>
                      <router-link v-if="c.job" :to="`/contracts/${c.id}`">
                        <Button variant="outline" size="sm" class="border-white/20 text-slate-300 hover:text-white">
                          View contract
                        </Button>
                      </router-link>
                    </div>
                    <div v-if="c.status === 'COMPLETED' && contractReviewByContractId[c.id]" class="mt-4 pt-4 border-t border-white/10">
                      <div class="flex items-center gap-2 mb-2">
                        <div class="flex text-amber">
                          <span
                            v-for="i in 5"
                            :key="i"
                            class="material-symbols-outlined filled text-lg"
                            :class="i <= (contractReviewByContractId[c.id].score ?? 0) ? 'text-amber' : 'text-slate-600'"
                          >
                            star
                          </span>
                        </div>
                        <span class="text-slate-400 text-sm">{{ formatDate(contractReviewByContractId[c.id].created_at) }}</span>
                      </div>
                      <p v-if="contractReviewByContractId[c.id].comment" class="text-slate-300 text-sm">{{ contractReviewByContractId[c.id].comment }}</p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </section>
          </div>
          <aside class="w-full lg:w-[380px]">
            <div class="lg:sticky lg:top-28 space-y-6 md:space-y-8">
              <Card v-if="(profilesStore.providerProfile?.skills && profilesStore.providerProfile.skills.length > 0) || skillTags.length > 0" class="bg-midnight-light border-white/10">
                <CardContent class="p-8">
                  <h3 class="text-sm font-black uppercase tracking-widest text-slate-400 mb-6 flex items-center gap-2">
                    <span class="w-8 h-px bg-white/10"></span>
                    Core Expertise
                  </h3>
                  <div class="flex flex-wrap gap-2.5">
                    <span
                      v-for="tag in (profilesStore.providerProfile?.skills || skillTags).slice(0, 6)"
                      :key="tag.id"
                      class="rounded-xl bg-amber/10 border border-amber/20 px-4 py-2 text-sm font-bold text-amber"
                    >
                      {{ tag.name }}
                    </span>
                  </div>
                </CardContent>
              </Card>
              <Card
                v-if="profilesStore.providerProfile?.hourly_rate"
                class="bg-gradient-to-br from-amber to-amber-soft p-8 shadow-2xl shadow-amber/20 text-midnight"
              >
                <div class="flex items-baseline justify-between mb-6">
                  <span class="text-sm font-bold uppercase tracking-widest opacity-70">Premium Rate</span>
                  <div class="text-right">
                    <span class="text-4xl font-black">Br {{ Math.round(profilesStore.providerProfile.hourly_rate).toLocaleString() }}/hr</span>
                    <span class="text-sm font-bold opacity-70">/hr</span>
                  </div>
                </div>
                <ul class="space-y-4 mb-8">
                  <li class="flex items-center gap-3 font-bold text-sm">
                    <span class="material-symbols-outlined text-xl">verified</span>
                    Free Detailed Consultation
                  </li>
                  <li class="flex items-center gap-3 font-bold text-sm">
                    <span class="material-symbols-outlined text-xl">verified</span>
                    Priority Scheduling
                  </li>
                </ul>
                <Button variant="secondary" class="w-full bg-midnight text-white hover:bg-midnight-light">
                  Secure Booking
                </Button>
              </Card>
              <Card class="bg-midnight-light border-white/10">
                <CardContent class="p-8">
                  <h3 class="text-sm font-black uppercase tracking-widest text-slate-400 mb-6 flex items-center gap-2">
                    <span class="material-symbols-outlined text-amber text-lg">account_balance_wallet</span>
                    Payments &amp; Payouts
                  </h3>
                  <div v-if="authStore.isProvider || authStore.user?.user_type === 'BOTH'" class="space-y-4">
                    <div v-if="stripeConnectLoading" class="flex items-center gap-2 text-slate-400">
                      <span class="material-symbols-outlined animate-spin">refresh</span>
                      <span class="text-sm">Loading...</span>
                    </div>
                    <template v-else-if="stripeConnectStatus?.has_account">
                      <div class="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/10">
                        <span class="material-symbols-outlined text-emerald-500 text-2xl">check_circle</span>
                        <div>
                          <p class="font-bold text-white">Stripe connected</p>
                          <p class="text-xs text-slate-400">
                            {{ stripeConnectStatus.enabled ? 'Ready to receive payments' : 'Complete onboarding to receive payments' }}
                          </p>
                        </div>
                      </div>
                      <div class="flex flex-col gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          class="w-full border-white/20 text-slate-300 hover:text-white"
                          :disabled="stripeDashboardLoading"
                          @click="openStripeDashboard"
                        >
                          <span class="material-symbols-outlined mr-2 text-lg">open_in_new</span>
                          Open Stripe Express dashboard
                        </Button>
                      </div>
                    </template>
                    <template v-else>
                      <p class="text-slate-400 text-sm">Connect your Stripe account to receive payments from clients securely.</p>
                      <Button
                        variant="default"
                        size="default"
                        class="w-full bg-[#635bff] hover:bg-[#7a73ff] text-white"
                        :disabled="stripeConnectLoading || stripeOnboardLoading"
                        @click="connectStripe"
                      >
                        <span v-if="stripeOnboardLoading" class="material-symbols-outlined animate-spin mr-2">refresh</span>
                        <span v-else class="material-symbols-outlined mr-2">link</span>
                        Connect Stripe account
                      </Button>
                    </template>
                  </div>
                  <div v-else class="space-y-2">
                    <p class="text-slate-400 text-sm">Payment is collected securely at checkout when you pay for contract milestones.</p>
                    <router-link to="/payments">
                      <Button variant="outline" size="sm" class="w-full border-white/20 text-slate-300 hover:text-white">
                        <span class="material-symbols-outlined mr-2 text-lg">receipt_long</span>
                        View payment history
                      </Button>
                    </router-link>
                  </div>
                </CardContent>
              </Card>
              <Card class="bg-midnight-light border-white/10">
                <CardContent class="p-8">
                  <h3 class="text-sm font-black uppercase tracking-widest text-slate-400 mb-6">Verified Credentials</h3>
                  <div class="space-y-6">
                    <div v-if="profilesStore.providerProfile?.certifications && profilesStore.providerProfile.certifications.length > 0" class="flex gap-4">
                      <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white/5 text-amber">
                        <span class="material-symbols-outlined">badge</span>
                      </div>
                      <div>
                        <p class="font-bold text-white">{{ profilesStore.providerProfile.certifications.length }} Certification(s)</p>
                        <p class="text-xs text-slate-400 mt-0.5">Verified Professional</p>
                      </div>
                    </div>
                    <div v-if="profilesStore.profile?.is_verified" class="flex gap-4">
                      <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white/5 text-amber">
                        <span class="material-symbols-outlined">shield_moon</span>
                      </div>
                      <div>
                        <p class="font-bold text-white">Verified Profile</p>
                        <p class="text-xs text-slate-400 mt-0.5">Identity Verified</p>
                      </div>
                    </div>
                    <div v-if="!profilesStore.providerProfile?.certifications?.length && !profilesStore.profile?.is_verified" class="text-center py-4">
                      <p class="text-slate-400 text-sm">No verified credentials yet</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </aside>
        </div>
      </div>
      </main>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useProfilesStore } from '@/stores/profiles'
import { ratingsService, type Rating, type RatingStats } from '@/services/ratings'
import { contractsService, type Contract } from '@/services/contracts'
import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from '@/components/ui/select'
import AppLayout from '@/components/AppLayout.vue'
import Card from '@/components/ui/Card.vue'
import CardContent from '@/components/ui/CardContent.vue'
import Button from '@/components/ui/Button.vue'
import FormField from '@/components/ui/FormField.vue'
import Label from '@/components/ui/Label.vue'
import Input from '@/components/ui/Input.vue'
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from '@/components/ui/dialog'
import { toast } from 'vue-sonner'
import { paymentsService, type StripeConnectStatus } from '@/services/payments'

const authStore = useAuthStore()
const profilesStore = useProfilesStore()
const activeTab = ref<'portfolio' | 'services' | 'jobs'>(authStore.isProvider ? 'portfolio' : 'jobs')
const ratingStats = ref<RatingStats | null>(null)
const showEditProfile = ref(false)
const avatarInputRef = ref<HTMLInputElement | null>(null)

const editForm = ref({
  first_name: '',
  last_name: '',
  phone_number: '',
  location: '',
  bio: '',
})
const editErrors = ref<Record<string, string>>({})
const expForm = ref({
  title: '',
  company_name: '',
  description: '',
  start_date: '',
  end_date: '',
  is_current: false,
})
const expErrors = ref<Record<string, string>>({})
const showAddExperience = ref(false)
const selectedSkillId = ref('')
const newSkillName = ref('')
const addingNewSkill = ref(false)
const profileContracts = ref<Contract[]>([])
const profileContractsList = computed(() => Array.isArray(profileContracts.value) ? profileContracts.value : [])
const profileContractsLoading = ref(false)
const contractReviewByContractId = ref<Record<string, Rating>>({})
const providerSkills = computed(() => profilesStore.providerProfile?.skills || [])
const availableSkillsToAdd = computed(() => {
  const currentIds = new Set(providerSkills.value.map((s: { id: string }) => s.id))
  return skillTags.value.filter(tag => !currentIds.has(tag.id))
})

const stripeConnectStatus = ref<StripeConnectStatus | null>(null)
const stripeConnectLoading = ref(false)
const stripeOnboardLoading = ref(false)
const stripeDashboardLoading = ref(false)

const fullName = computed(() => {
  if (profilesStore.profile?.first_name || profilesStore.profile?.last_name) {
    return `${profilesStore.profile.first_name || ''} ${profilesStore.profile.last_name || ''}`.trim()
  }
  return authStore.user?.email || 'User'
})

const initials = computed(() => {
  const name = fullName.value
  const parts = name.split(' ')
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  }
  return name.charAt(0).toUpperCase()
})

const profilePictureUrl = computed(() => {
  const raw = profilesStore.profile?.avatar || (authStore.user as { avatar?: string })?.avatar || null
  if (!raw) return null
  if (raw.startsWith('http')) return raw
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
  const origin = apiBase.replace(/\/api\/v1\/?$/, '')
  return origin + (raw.startsWith('/') ? raw : '/' + raw)
})

const location = computed(() => {
  return profilesStore.profile?.location?.toUpperCase() || null
})

const primarySkill = computed(() => {
  const skills = skillTags.value
  return skills.length > 0 ? skills[0].name : null
})

const skillTags = computed(() => {
  const tags = profilesStore.tags
  if (!Array.isArray(tags)) return []
  return tags.filter(tag => (tag.category || '').toUpperCase() === 'SKILL')
})

function onTabClick(tab: 'portfolio' | 'services' | 'jobs') {
  activeTab.value = tab
  if (tab === 'jobs') loadProfileContracts()
}

async function loadProfileContracts() {
  profileContractsLoading.value = true
  try {
    const params = authStore.isClient ? { my_contracts: 'true' } : undefined
    const res = await contractsService.list(params)
    const list = res.data.results ?? []
    profileContracts.value = list
    const completedIds = list.filter((c: Contract) => c.status === 'COMPLETED').map((c: Contract) => c.id)
    if (completedIds.length > 0) {
      const ratingType = authStore.isClient ? 'PROVIDER_TO_CLIENT' : 'CLIENT_TO_PROVIDER'
      const map: Record<string, Rating> = {}
      await Promise.all(
        completedIds.map(async (id: string) => {
          try {
            const r = await ratingsService.list({ contract: id, rating_type: ratingType })
            const data = r.data as { results?: Rating[] } | Rating[]
            const arr = Array.isArray(data) ? data : (data?.results ?? [])
            if (arr.length > 0) map[id] = arr[0]
          } catch (_) {}
        })
      )
      contractReviewByContractId.value = map
    } else {
      contractReviewByContractId.value = {}
    }
  } catch (err) {
    console.error('Failed to load contracts:', err)
    profileContracts.value = []
  } finally {
    profileContractsLoading.value = false
  }
}

function resetExpForm() {
  expForm.value = { title: '', company_name: '', description: '', start_date: '', end_date: '', is_current: false }
  expErrors.value = {}
}

async function submitExperience() {
  expErrors.value = {}
  if (!expForm.value.title || !expForm.value.start_date) {
    expErrors.value.title = 'Title and start date are required'
    return
  }
  try {
    await profilesStore.createExperience({
      title: expForm.value.title,
      company_name: expForm.value.company_name || undefined,
      description: expForm.value.description || undefined,
      start_date: expForm.value.start_date,
      end_date: expForm.value.end_date || undefined,
      is_current: expForm.value.is_current,
    })
    toast.success('Experience added')
    showAddExperience.value = false
    resetExpForm()
    await profilesStore.fetchProviderProfile()
    await profilesStore.fetchExperiences()
  } catch (err: any) {
    const data = err.response?.data
    if (data && typeof data === 'object') {
      Object.keys(data).forEach(key => {
        const val = data[key]
        expErrors.value[key] = Array.isArray(val) ? val[0] : val
      })
    } else {
      toast.error('Failed to add experience')
    }
  }
}

async function deleteExperience(id: string) {
  try {
    await profilesStore.deleteExperience(id)
    toast.success('Experience removed')
    await profilesStore.fetchProviderProfile()
    await profilesStore.fetchExperiences()
  } catch {
    toast.error('Failed to remove experience')
  }
}

function addSkill() {
  if (!selectedSkillId.value) return
  const currentIds = (profilesStore.providerProfile?.skills || []).map((s: { id: string }) => s.id)
  if (currentIds.includes(selectedSkillId.value)) return
  profilesStore.updateProviderProfile({ skill_ids: [...currentIds, selectedSkillId.value] }).then(() => {
    toast.success('Skill added')
    selectedSkillId.value = ''
    profilesStore.fetchProviderProfile()
  }).catch(() => toast.error('Failed to add skill'))
}

function removeSkill(tagId: string) {
  const currentIds = (profilesStore.providerProfile?.skills || []).map((s: { id: string }) => s.id).filter((id: string) => id !== tagId)
  profilesStore.updateProviderProfile({ skill_ids: currentIds }).then(() => {
    toast.success('Skill removed')
    profilesStore.fetchProviderProfile()
  }).catch(() => toast.error('Failed to remove skill'))
}

async function addNewSkill() {
  const name = newSkillName.value.trim()
  if (!name) return
  addingNewSkill.value = true
  try {
    let tagId: string
    try {
      const created = await profilesStore.createTag({ name, category: 'SKILL' })
      tagId = created.id
    } catch (err: any) {
      if (err.response?.status === 400) {
        await profilesStore.fetchTags()
        const existing = (profilesStore.tags || []).find((t: { name: string }) => t.name.toLowerCase() === name.toLowerCase())
        if (existing) tagId = existing.id
        else throw err
      } else throw err
    }
    const currentIds = (profilesStore.providerProfile?.skills || []).map((s: { id: string }) => s.id)
    if (!currentIds.includes(tagId)) {
      await profilesStore.updateProviderProfile({ skill_ids: [...currentIds, tagId] })
      await profilesStore.fetchProviderProfile()
    }
    toast.success('Skill added')
    newSkillName.value = ''
    await profilesStore.fetchTags()
  } catch (err: any) {
    toast.error(err.response?.data?.name?.[0] || err.response?.data?.detail || 'Failed to add skill')
  } finally {
    addingNewSkill.value = false
  }
}

function formatDate(dateString: string) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
}

function initEditForm() {
  const p = profilesStore.profile
  if (p) {
    editForm.value = {
      first_name: p.first_name || '',
      last_name: p.last_name || '',
      phone_number: p.phone_number || '',
      location: p.location || '',
      bio: p.bio || '',
    }
    editErrors.value = {}
  }
}

function triggerAvatarUpload() {
  avatarInputRef.value?.click()
}

async function onAvatarFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    toast.error('Please select an image file')
    input.value = ''
    return
  }
  try {
    await profilesStore.uploadAvatar(file)
    toast.success('Profile picture updated')
  } catch {
    toast.error('Failed to upload photo')
  }
  input.value = ''
}

async function saveProfile() {
  editErrors.value = {}
  try {
    await profilesStore.updateProfile(editForm.value)
    showEditProfile.value = false
    toast.success('Profile updated')
  } catch (err: any) {
    const data = err.response?.data
    if (data && typeof data === 'object') {
      Object.keys(data).forEach(key => {
        const val = data[key]
        editErrors.value[key] = Array.isArray(val) ? val[0] : val
      })
    } else {
      toast.error('Failed to update profile')
    }
  }
}

async function fetchStripeStatus() {
  if (!authStore.isProvider && authStore.user?.user_type !== 'BOTH') return
  stripeConnectLoading.value = true
  try {
    const res = await paymentsService.getStripeConnectStatus()
    stripeConnectStatus.value = res.data
  } catch {
    stripeConnectStatus.value = null
  } finally {
    stripeConnectLoading.value = false
  }
}

async function connectStripe() {
  stripeOnboardLoading.value = true
  try {
    const res = await paymentsService.onboardStripeConnect()
    const url = res.data.onboarding_url
    if (url) window.location.href = url
    else toast.error('Could not get Stripe onboarding link')
  } catch (err: any) {
    const msg = err.response?.data?.error ?? 'Failed to start Stripe connection'
    toast.error(msg)
  } finally {
    stripeOnboardLoading.value = false
  }
}

async function openStripeDashboard() {
  stripeDashboardLoading.value = true
  try {
    const res = await paymentsService.loginStripeConnect()
    const url = res.data.login_url
    if (url) window.location.href = url
    else toast.error('Could not get Stripe dashboard link')
  } catch (err: any) {
    const msg = err.response?.data?.error ?? 'Failed to open Stripe dashboard'
    toast.error(msg)
  } finally {
    stripeDashboardLoading.value = false
  }
}

onMounted(async () => {
  await profilesStore.fetchProfile()
  if (authStore.isProvider || authStore.user?.user_type === 'BOTH') {
    await fetchStripeStatus()
  }
  if (authStore.isProvider) {
    await profilesStore.fetchProviderProfile()
    await profilesStore.fetchTags({ category: 'SKILL' })
    await profilesStore.fetchExperiences()
  }
  const userId = typeof profilesStore.profile?.user === 'string'
    ? profilesStore.profile.user
    : (profilesStore.profile?.user as { id?: string })?.id ?? authStore.user?.id
  if (userId) {
    try {
      const statsResponse = await ratingsService.getStats(userId)
      const stats = statsResponse.data as import('@/services/ratings').RatingStats
      const total = (stats.total_ratings ?? 0) || 0
      const countP = stats.rating_count_as_provider ?? 0
      const countC = stats.rating_count_as_client ?? 0
      const avgP = stats.average_rating_as_provider ?? 0
      const avgC = stats.average_rating_as_client ?? 0
      const combinedAvg = total > 0 ? (avgP * countP + avgC * countC) / total : 0
      ratingStats.value = {
        ...stats,
        average_rating: combinedAvg,
        total_ratings: total,
      }
    } catch (err) {
      console.error('Failed to fetch rating stats:', err)
    }
  }
  if (activeTab.value === 'jobs') loadProfileContracts()
})
</script>

