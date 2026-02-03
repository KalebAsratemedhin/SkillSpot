<template>
  <AppLayout>
    <div class="relative flex flex-1 flex-col w-full overflow-x-hidden">
      <main class="flex flex-1 flex-col">
        <!-- Hero -->
        <section class="relative w-full overflow-hidden bg-midnight pt-20 pb-24 lg:pt-32 lg:pb-40">
          <div class="absolute top-0 right-0 w-1/3 h-full bg-gradient-to-l from-amber/5 to-transparent"></div>
          <div class="absolute -bottom-24 -left-24 size-96 rounded-full bg-amber/10 blur-3xl"></div>
          <div class="mx-auto max-w-[1400px] px-6 relative z-10">
            <div class="grid grid-cols-1 gap-16 lg:grid-cols-12 lg:items-center">
              <div class="lg:col-span-6 flex flex-col gap-10">
                <div class="flex flex-col gap-6">
                  <span class="inline-flex w-fit items-center gap-2 rounded-full border border-white/20 bg-white/5 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-amber">
                    <span class="size-2 rounded-full bg-amber animate-pulse"></span>
                    Top Rated Professionals On-Demand
                  </span>
                  <h1 class="text-5xl font-extrabold leading-[1.1] tracking-tight text-white md:text-6xl lg:text-7xl">
                    Precision Skill <br/> <span class="text-amber">Personalized</span> Care
                  </h1>
                  <p class="text-xl font-medium leading-relaxed text-slate-300 max-w-[540px]">
                    Connect with the most elite local professionals. From high-voltage electrical projects to master carpentry, SkillSpot delivers excellence to your doorstep.
                  </p>
                </div>
                <div class="flex flex-wrap gap-5">
                  <router-link to="/register">
                    <Button variant="default" size="lg" class="h-16 min-w-[200px] rounded-full px-8 text-lg">
                      Hire a Professional
                    </Button>
                  </router-link>
                  <router-link to="/register">
                    <Button variant="outline" size="lg" class="h-16 min-w-[200px] rounded-full px-8 text-lg border-2 border-white/20">
                      Become a Provider
                    </Button>
                  </router-link>
                </div>
                <div class="flex items-center gap-6">
                  <div class="flex -space-x-4">
                    <div class="size-12 rounded-full border-4 border-midnight bg-slate-400 overflow-hidden">
                      <img src="https://images.unsplash.com/photo-1560250097-0b93528c311a?w=96&h=96&fit=crop" alt="" class="w-full h-full object-cover" />
                    </div>
                    <div class="size-12 rounded-full border-4 border-midnight bg-slate-500 overflow-hidden">
                      <img src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=96&h=96&fit=crop" alt="" class="w-full h-full object-cover" />
                    </div>
                    <div class="size-12 rounded-full border-4 border-midnight bg-slate-600 overflow-hidden">
                      <img src="https://images.unsplash.com/photo-1580489944761-15a19d654956?w=96&h=96&fit=crop" alt="" class="w-full h-full object-cover" />
                    </div>
                  </div>
                  <div class="flex flex-col">
                    <p class="text-sm font-bold text-white">Join 25,000+ happy clients</p>
                    <div class="flex text-amber scale-75 -ml-4">
                      <span class="material-symbols-outlined fill-1">star</span>
                      <span class="material-symbols-outlined fill-1">star</span>
                      <span class="material-symbols-outlined fill-1">star</span>
                      <span class="material-symbols-outlined fill-1">star</span>
                      <span class="material-symbols-outlined fill-1">star</span>
                    </div>
                  </div>
                </div>
              </div>
              <div class="lg:col-span-6 relative">
                <div class="grid grid-cols-2 gap-3 sm:gap-4">
                  <div class="space-y-3 pt-8 sm:pt-12">
                    <div class="aspect-[3/4] rounded-2xl sm:rounded-3xl overflow-hidden shadow-2xl transform rotate-[-2deg] border-2 border-white/10">
                      <img src="https://images.unsplash.com/photo-1621905251189-08b45d6a269e?w=500&q=80" alt="Electrician at work" class="w-full h-full object-cover" />
                    </div>
                    <div class="p-4 sm:p-5 rounded-xl sm:rounded-2xl bg-white/10 backdrop-blur-md border border-white/10 text-white">
                      <p class="text-sm font-bold">Electrical Excellence</p>
                      <p class="text-xs opacity-70">Certified Industrial Experts</p>
                    </div>
                  </div>
                  <div class="space-y-3">
                    <div class="aspect-[3/4] rounded-2xl sm:rounded-3xl overflow-hidden shadow-2xl transform rotate-[2deg] border-2 border-white/10">
                      <img src="https://images.unsplash.com/photo-1607472586893-edb57bdc0e39?w=500&q=80" alt="Plumber at work" class="w-full h-full object-cover" />
                    </div>
                    <div class="p-4 sm:p-5 rounded-xl sm:rounded-2xl bg-amber text-midnight">
                      <p class="text-sm font-black">Expert Plumbing</p>
                      <p class="text-xs font-bold opacity-80">Licensed & Insured</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- How it works -->
        <section class="py-20 sm:py-24 bg-slate-50 border-y border-slate-200">
          <div class="mx-auto max-w-[1400px] px-6">
            <h2 class="text-amber font-extrabold text-sm uppercase tracking-widest mb-2">How it works</h2>
            <h3 class="text-3xl font-black text-midnight sm:text-4xl mb-12">Get started in three steps</h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-10">
              <div class="flex flex-col items-center text-center">
                <div class="size-16 rounded-2xl bg-amber text-midnight flex items-center justify-center text-2xl font-black mb-4">1</div>
                <h4 class="text-xl font-bold text-midnight mb-2">Post or browse</h4>
                <p class="text-slate-600">Clients post a job with skills and budget. Providers browse and apply, or get invited.</p>
              </div>
              <div class="flex flex-col items-center text-center">
                <div class="size-16 rounded-2xl bg-amber text-midnight flex items-center justify-center text-2xl font-black mb-4">2</div>
                <h4 class="text-xl font-bold text-midnight mb-2">Agree & sign</h4>
                <p class="text-slate-600">Create a contract, agree on terms, and both parties sign to start the job.</p>
              </div>
              <div class="flex flex-col items-center text-center">
                <div class="size-16 rounded-2xl bg-amber text-midnight flex items-center justify-center text-2xl font-black mb-4">3</div>
                <h4 class="text-xl font-bold text-midnight mb-2">Pay & review</h4>
                <p class="text-slate-600">Pay securely through the platform. Complete the job and leave reviews.</p>
              </div>
            </div>
          </div>
        </section>

        <!-- Why SkillSpot -->
        <section class="py-20 sm:py-24 bg-white">
          <div class="mx-auto max-w-[1400px] px-6">
            <h2 class="text-amber font-extrabold text-sm uppercase tracking-widest mb-2">Why SkillSpot</h2>
            <h3 class="text-3xl font-black text-midnight sm:text-4xl mb-12">Built for trust and quality</h3>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
              <div class="p-6 rounded-2xl border border-slate-200 bg-slate-50/50">
                <span class="material-symbols-outlined text-3xl text-amber mb-3">verified_user</span>
                <h4 class="text-lg font-bold text-midnight mb-2">Verified professionals</h4>
                <p class="text-slate-600 text-sm">Skills and profiles are vetted. Work with confidence.</p>
              </div>
              <div class="p-6 rounded-2xl border border-slate-200 bg-slate-50/50">
                <span class="material-symbols-outlined text-3xl text-amber mb-3">payments</span>
                <h4 class="text-lg font-bold text-midnight mb-2">Secure payments</h4>
                <p class="text-slate-600 text-sm">Escrow protection. Pay when you’re satisfied with the work.</p>
              </div>
              <div class="p-6 rounded-2xl border border-slate-200 bg-slate-50/50">
                <span class="material-symbols-outlined text-3xl text-amber mb-3">description</span>
                <h4 class="text-lg font-bold text-midnight mb-2">Clear contracts</h4>
                <p class="text-slate-600 text-sm">Agreed scope, timeline, and payment. Both parties sign.</p>
              </div>
              <div class="p-6 rounded-2xl border border-slate-200 bg-slate-50/50">
                <span class="material-symbols-outlined text-3xl text-amber mb-3">rate_review</span>
                <h4 class="text-lg font-bold text-midnight mb-2">Reviews that matter</h4>
                <p class="text-slate-600 text-sm">Real feedback from completed jobs. Choose the best fit.</p>
              </div>
            </div>
          </div>
        </section>

        <!-- Categories -->
        <section class="py-24 bg-slate-50">
          <div class="mx-auto max-w-[1400px] px-6">
            <div class="flex flex-col md:flex-row justify-between items-end gap-6 mb-16">
              <div class="flex flex-col gap-4">
                <h2 class="text-amber font-extrabold text-sm uppercase tracking-widest">Marketplace</h2>
                <h3 class="text-4xl font-black text-midnight md:text-5xl">Trending Categories</h3>
              </div>
              <router-link to="/categories" class="group flex items-center gap-2 font-bold text-midnight hover:text-amber transition-colors">
                Explore all categories <span class="material-symbols-outlined transition-transform group-hover:translate-x-2">east</span>
              </router-link>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
              <router-link v-for="category in categories" :key="category.name" :to="'/categories#' + category.slug" class="block">
                <Card class="group relative bg-white p-10 rounded-[2.5rem] border border-slate-200 hover:border-amber/30 hover:shadow-2xl transition-all duration-300 overflow-hidden h-full">
                  <div class="absolute -top-10 -right-10 size-40 bg-amber/5 rounded-full group-hover:scale-150 transition-transform duration-500"></div>
                  <div class="mb-8 inline-flex size-20 items-center justify-center rounded-3xl bg-slate-100 text-midnight group-hover:bg-amber group-hover:text-white transition-all">
                    <span class="material-symbols-outlined text-4xl">{{ category.icon }}</span>
                  </div>
                  <h4 class="text-2xl font-black text-midnight mb-3">{{ category.name }}</h4>
                  <p class="text-slate-500 mb-6 font-medium leading-relaxed">{{ category.description }}</p>
                  <div class="flex items-center justify-between mt-auto pt-6 border-t border-slate-200">
                    <span class="text-sm font-bold text-slate-400">{{ category.count }}+ Pros</span>
                    <span class="material-symbols-outlined text-amber group-hover:translate-x-1 transition-transform">arrow_forward</span>
                  </div>
                </Card>
              </router-link>
            </div>
          </div>
        </section>
      </main>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'

const categories = ref([
  { name: 'Plumbing', slug: 'plumbing', icon: 'plumbing', description: 'Leak detection, fixture installation, and repairs by licensed plumbers.', count: 840 },
  { name: 'Electrical', slug: 'electrical', icon: 'bolt', description: 'Wiring, smart home setup, and industrial electrical work.', count: 520 },
  { name: 'Carpentry', slug: 'carpentry', icon: 'carpenter', description: 'Custom furniture, cabinetry, and architectural woodworking.', count: 680 },
  { name: 'Mechanics', slug: 'mechanics', icon: 'build', description: 'Auto repair, maintenance, and diagnostics by certified mechanics.', count: 410 },
])
</script>
