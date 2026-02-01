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
              <div class="h-40 w-40 md:h-52 md:w-52 rounded-2xl ring-4 ring-amber/20 overflow-hidden shadow-2xl shadow-amber/5">
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
                <button
                  :class="[
                    'relative pb-3 md:pb-4 text-sm md:text-base font-bold transition-colors whitespace-nowrap',
                    activeTab === 'portfolio' ? 'text-amber' : 'text-slate-400 hover:text-white',
                  ]"
                  @click="activeTab = 'portfolio'"
                >
                  Portfolio
                  <span
                    v-if="activeTab === 'portfolio'"
                    class="absolute bottom-0 left-0 h-1 w-full bg-amber rounded-t-full"
                  ></span>
                </button>
                <button
                  :class="[
                    'pb-3 md:pb-4 text-sm md:text-base font-semibold transition-colors whitespace-nowrap',
                    activeTab === 'about' ? 'text-amber' : 'text-slate-400 hover:text-white',
                  ]"
                  @click="activeTab = 'about'"
                >
                  About Expert
                </button>
                <button
                  :class="[
                    'pb-3 md:pb-4 text-sm md:text-base font-semibold transition-colors whitespace-nowrap',
                    activeTab === 'services' ? 'text-amber' : 'text-slate-400 hover:text-white',
                  ]"
                  @click="activeTab = 'services'"
                >
                  Services
                </button>
                <button
                  :class="[
                    'pb-3 md:pb-4 text-sm md:text-base font-semibold transition-colors whitespace-nowrap',
                    activeTab === 'reviews' ? 'text-amber' : 'text-slate-400 hover:text-white',
                  ]"
                  @click="activeTab = 'reviews'"
                >
                  Reviews
                </button>
              </nav>
            </div>
            <section v-if="activeTab === 'portfolio'">
              <div v-if="authStore.isProvider" class="mb-8">
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
                      <DialogDescription>Add a role or project to your portfolio. Dates help clients see your journey.</DialogDescription>
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
              <!-- Timeline-style portfolio -->
              <div class="relative">
                <div v-if="portfolioItems.length > 0" class="space-y-0">
                  <div
                    v-for="(experience, index) in portfolioItems"
                    :key="experience.id || index"
                    class="relative flex gap-6 md:gap-10 group"
                  >
                    <div class="flex flex-col items-center flex-shrink-0">
                      <div class="w-4 h-4 rounded-full bg-amber ring-4 ring-midnight-light group-hover:ring-amber/30 transition-all z-10" />
                      <div v-if="index < portfolioItems.length - 1" class="w-px flex-1 min-h-[60px] bg-gradient-to-b from-amber/60 to-white/10 mt-1" />
                    </div>
                    <article class="flex-1 pb-10 md:pb-12">
                      <div class="relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-midnight-light to-midnight/80 p-6 md:p-8 transition-all duration-300 group-hover:border-amber/30 group-hover:shadow-xl group-hover:shadow-amber/5">
                        <div class="absolute top-0 right-0 w-32 h-32 bg-amber/5 rounded-bl-full" />
                        <div class="relative">
                          <span class="inline-block text-6xl md:text-7xl font-black text-amber/30 leading-none mb-2 select-none" style="font-family: Georgia, serif;">{{ experience.title.charAt(0) }}</span>
                          <h3 class="text-xl md:text-2xl font-bold text-white mb-1 -mt-2">{{ experience.title }}</h3>
                          <p v-if="experience.company_name" class="text-amber text-sm font-semibold mb-3">{{ experience.company_name }}</p>
                          <p v-if="experience.description" class="text-slate-400 text-sm leading-relaxed mb-4">{{ experience.description }}</p>
                          <div class="flex flex-wrap items-center justify-between gap-3 mt-2">
                            <span class="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-500">
                              <span class="material-symbols-outlined text-amber text-sm">calendar_today</span>
                              {{ formatDate(experience.start_date) }} — {{ experience.is_current ? 'Present' : (experience.end_date ? formatDate(experience.end_date) : '—') }}
                            </span>
                            <Button
                              v-if="authStore.isProvider && experience.id"
                              variant="ghost"
                              size="sm"
                              class="text-red-400/80 hover:text-red-400 hover:bg-red-500/10"
                              @click="deleteExperience(experience.id)"
                            >
                              <span class="material-symbols-outlined text-sm">delete</span>
                              Remove
                            </Button>
                          </div>
                        </div>
                      </div>
                    </article>
                  </div>
                </div>
                <div v-else class="text-center py-16 px-6 rounded-2xl border border-dashed border-white/10 bg-white/[0.02]">
                  <span class="material-symbols-outlined text-5xl text-slate-600 mb-4 block">work</span>
                  <p class="text-slate-400 font-medium mb-2">No portfolio items yet</p>
                  <p class="text-slate-500 text-sm">Add your experience to show clients your track record.</p>
                  <Button v-if="authStore.isProvider" variant="outline" size="default" class="mt-6 border-amber/30 text-amber" @click="showAddExperience = true">
                    <span class="material-symbols-outlined text-lg mr-1">add</span>
                    Add experience
                  </Button>
                </div>
              </div>
            </section>
            <section v-if="activeTab === 'about'">
              <Card class="bg-midnight-light border-white/10">
                <CardContent class="p-8">
                  <h3 class="text-xl font-bold text-white mb-4">About</h3>
                  <p v-if="profilesStore.profile?.bio" class="text-slate-300 leading-relaxed mb-6">
                    {{ profilesStore.profile.bio }}
                  </p>
                  <div v-if="profilesStore.experiences.length > 0" class="space-y-4">
                    <h4 class="text-lg font-bold text-white mb-3">Experience</h4>
                    <div
                      v-for="exp in (profilesStore.providerProfile?.experiences || profilesStore.experiences)"
                      :key="exp.id"
                      class="border-l-2 border-amber/30 pl-4 py-2"
                    >
                      <div class="flex items-baseline gap-2 mb-1">
                        <h5 class="font-bold text-white">{{ exp.title }}</h5>
                        <span v-if="exp.company_name" class="text-slate-400 text-sm">{{ exp.company_name }}</span>
                      </div>
                      <p v-if="exp.description" class="text-slate-400 text-sm">{{ exp.description }}</p>
                      <p class="text-slate-500 text-xs mt-1">
                        {{ formatDate(exp.start_date) }} - {{ exp.is_current ? 'Present' : formatDate(exp.end_date || '') }}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </section>
            <section v-if="activeTab === 'services'">
              <Card class="bg-midnight-light border-white/10">
                <CardContent class="p-8">
                  <h3 class="text-xl font-bold text-white mb-4">Services Offered</h3>
                  <div v-if="providerSkills.length > 0" class="flex flex-wrap gap-2.5 mb-4">
                    <span
                      v-for="tag in providerSkills"
                      :key="tag.id"
                      class="inline-flex items-center gap-1 rounded-xl bg-amber/10 border border-amber/20 px-4 py-2 text-sm font-bold text-amber"
                    >
                      {{ tag.name }}
                      <button
                        v-if="authStore.isProvider"
                        type="button"
                        class="ml-1 text-slate-400 hover:text-red-400"
                        aria-label="Remove skill"
                        @click="removeSkill(tag.id)"
                      >
                        <span class="material-symbols-outlined text-sm">close</span>
                      </button>
                    </span>
                  </div>
                  <div v-if="authStore.isProvider" class="mt-4 space-y-4">
                    <div class="flex flex-wrap items-end gap-2">
                      <div class="min-w-[200px]">
                        <Label class="text-slate-300 block mb-2">Add skill from list</Label>
                        <Select v-model="selectedSkillId" class="w-full">
                          <SelectTrigger class="w-full">
                            <SelectValue placeholder="Select a skill..." />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem
                              v-for="tag in availableSkillsToAdd"
                              :key="tag.id"
                              :value="tag.id"
                            >
                              {{ tag.name }}
                            </SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <Button
                        type="button"
                        variant="default"
                        size="default"
                        class="bg-amber text-midnight"
                        :disabled="!selectedSkillId"
                        @click="addSkill()"
                      >
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
                      <Button
                        type="button"
                        variant="default"
                        size="default"
                        class="bg-amber text-midnight"
                        :disabled="!newSkillName.trim()"
                        :loading="addingNewSkill"
                        @click="addNewSkill()"
                      >
                        Create &amp; Add
                      </Button>
                    </div>
                  </div>
                  <p v-if="providerSkills.length === 0 && !authStore.isProvider" class="text-slate-400">No services listed yet</p>
                  <p v-else-if="providerSkills.length === 0" class="text-slate-400">Add skills above to show your services.</p>
                </CardContent>
              </Card>
            </section>
            <section v-if="activeTab === 'reviews'">
              <div v-if="reviews.length > 0" class="space-y-4">
                <Card
                  v-for="review in reviews"
                  :key="review.id"
                  class="bg-midnight-light border-white/10"
                >
                  <CardContent class="p-6">
                    <div class="flex items-center gap-3 mb-3">
                      <div class="flex text-amber">
                        <span
                          v-for="i in 5"
                          :key="i"
                          class="material-symbols-outlined filled text-lg"
                          :class="i <= review.rating ? 'text-amber' : 'text-slate-600'"
                        >
                          star
                        </span>
                      </div>
                      <span class="text-slate-400 text-sm">{{ formatDate(review.created_at) }}</span>
                    </div>
                    <p v-if="review.comment" class="text-slate-300">{{ review.comment }}</p>
                  </CardContent>
                </Card>
              </div>
              <div v-else class="text-center py-12">
                <p class="text-slate-400">No reviews yet</p>
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
                    <span class="text-4xl font-black">${{ Math.round(profilesStore.providerProfile.hourly_rate) }}</span>
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
                  <li class="flex items-center gap-3 font-bold text-sm">
                    <span class="material-symbols-outlined text-xl">verified</span>
                    5-Year Warranty on Labor
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
import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from '@/components/ui/select'
import { toast } from 'vue-sonner'
import { paymentsService, type StripeConnectStatus } from '@/services/payments'

const authStore = useAuthStore()
const profilesStore = useProfilesStore()
const activeTab = ref<'portfolio' | 'about' | 'services' | 'reviews'>('portfolio')
const ratingStats = ref<RatingStats | null>(null)
const reviews = ref<Rating[]>([])
const showEditProfile = ref(false)
const showAddExperience = ref(false)

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
const selectedSkillId = ref('')
const newSkillName = ref('')
const addingNewSkill = ref(false)

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
  return profilesStore.profile?.avatar || authStore.user?.avatar || null
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

const providerSkills = computed(() => {
  return profilesStore.providerProfile?.skills || []
})

const availableSkillsToAdd = computed(() => {
  const currentIds = new Set(providerSkills.value.map((s: { id: string }) => s.id))
  return skillTags.value.filter(tag => !currentIds.has(tag.id))
})

const portfolioItems = computed(() => {
  if (profilesStore.providerProfile?.experiences?.length) {
    return profilesStore.providerProfile.experiences.map((exp: { id: string; title: string; description?: string; company_name?: string; start_date: string; end_date?: string; is_current?: boolean }) => ({
      id: exp.id,
      title: exp.title,
      description: exp.description,
      company_name: exp.company_name,
      start_date: exp.start_date,
      end_date: exp.end_date,
      is_current: exp.is_current,
      image: null,
    }))
  }
  const exps = profilesStore.experiences
  if (!Array.isArray(exps)) return []
  return exps.map((exp: { id: string; title: string; description?: string; company_name?: string; start_date: string; end_date?: string; is_current?: boolean }) => ({
    id: exp.id,
    title: exp.title,
    description: exp.description,
    company_name: exp.company_name,
    start_date: exp.start_date,
    end_date: exp.end_date,
    is_current: exp.is_current,
    image: null,
  }))
})

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
  const newIds = [...currentIds, selectedSkillId.value]
  profilesStore.updateProviderProfile({ skill_ids: newIds }).then(() => {
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
    if (currentIds.includes(tagId)) {
      toast.success('Skill already added')
    } else {
      await profilesStore.updateProviderProfile({ skill_ids: [...currentIds, tagId] })
      toast.success('Skill added')
      await profilesStore.fetchProviderProfile()
    }
    newSkillName.value = ''
    await profilesStore.fetchTags()
  } catch (err: any) {
    toast.error(err.response?.data?.name?.[0] || err.response?.data?.detail || 'Failed to add skill')
  } finally {
    addingNewSkill.value = false
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
    
    if (profilesStore.providerProfile?.id) {
      try {
        const userId = typeof profilesStore.profile?.user === 'string' ? profilesStore.profile.user : profilesStore.profile?.user
        const [statsResponse, reviewsResponse] = await Promise.all([
          ratingsService.getStats(userId),
          ratingsService.getProviderRatings(profilesStore.providerProfile.id),
        ])
        ratingStats.value = statsResponse.data
        reviews.value = reviewsResponse.data
      } catch (err) {
        console.error('Failed to fetch ratings:', err)
      }
    }
  }
})
</script>

<style scoped>
.portfolio-grid {
  column-count: 1;
  column-gap: 1.5rem;
}

@media (min-width: 768px) {
  .portfolio-grid {
    column-count: 2;
  }
}

@media (min-width: 1024px) {
  .portfolio-grid {
    column-count: 3;
  }
}

.portfolio-item {
  display: inline-block;
  width: 100%;
  margin-bottom: 1.5rem;
  break-inside: avoid;
}
</style>
