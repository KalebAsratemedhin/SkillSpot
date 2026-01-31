<template>
  <AppLayout>
    <div class="relative flex flex-1 flex-col w-full overflow-x-hidden">
      <main class="flex flex-1 flex flex-col">
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
                  <div class="size-12 rounded-full border-4 border-midnight bg-slate-400"></div>
                  <div class="size-12 rounded-full border-4 border-midnight bg-slate-500"></div>
                  <div class="size-12 rounded-full border-4 border-midnight bg-slate-600"></div>
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
              <div class="grid grid-cols-2 gap-4">
                <div class="space-y-4 pt-12">
                  <div class="aspect-[3/4] rounded-3xl overflow-hidden shadow-2xl transform rotate-[-2deg] bg-gradient-to-br from-amber/20 to-midnight-light"></div>
                  <div class="p-5 rounded-2xl bg-white/10 backdrop-blur-md border border-white/10 text-white">
                    <p class="text-sm font-bold">Electrical Excellence</p>
                    <p class="text-xs opacity-70">Certified Industrial Experts</p>
                  </div>
                </div>
                <div class="space-y-4">
                  <div class="aspect-[3/4] rounded-3xl overflow-hidden shadow-2xl transform rotate-[2deg] bg-gradient-to-br from-amber/20 to-midnight-light"></div>
                  <div class="p-5 rounded-2xl bg-amber text-midnight">
                    <p class="text-sm font-black">Elite Woodworking</p>
                    <p class="text-xs font-bold opacity-80">Master Craftsmen</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="py-24 bg-white">
        <div class="mx-auto max-w-[1400px] px-6">
          <div class="flex flex-col md:flex-row justify-between items-end gap-6 mb-16">
            <div class="flex flex-col gap-4">
              <h2 class="text-amber font-extrabold text-sm uppercase tracking-widest">Marketplace</h2>
              <h3 class="text-4xl font-black text-midnight md:text-5xl">Trending Categories</h3>
            </div>
            <a class="group flex items-center gap-2 font-bold text-midnight hover:text-amber transition-colors" href="#">
              Explore all categories <span class="material-symbols-outlined transition-transform group-hover:translate-x-2">east</span>
            </a>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            <Card v-for="category in categories" :key="category.name" class="group relative bg-slate-50 p-10 rounded-[2.5rem] border border-transparent hover:border-amber/30 hover:bg-white hover:shadow-2xl transition-all duration-300 overflow-hidden">
              <div class="absolute -top-10 -right-10 size-40 bg-amber/5 rounded-full group-hover:scale-150 transition-transform duration-500"></div>
              <div class="mb-8 inline-flex size-20 items-center justify-center rounded-3xl bg-white shadow-lg text-midnight group-hover:bg-amber group-hover:text-white transition-all">
                <span class="material-symbols-outlined text-4xl">{{ category.icon }}</span>
              </div>
              <h4 class="text-2xl font-black text-midnight mb-3">{{ category.name }}</h4>
              <p class="text-slate-500 mb-6 font-medium leading-relaxed">{{ category.description }}</p>
              <div class="flex items-center justify-between mt-auto pt-6 border-t border-slate-200">
                <span class="text-sm font-bold text-slate-400">{{ category.count }}+ Pros</span>
                <span class="material-symbols-outlined text-amber group-hover:translate-x-1 transition-transform">arrow_forward</span>
              </div>
            </Card>
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
  { name: 'Plumbing', icon: 'plumbing', description: 'Modern leak detection & rapid fixture installation by master plumbers.', count: 840 },
  { name: 'Electrical', icon: 'bolt', description: 'High-voltage industrial work & smart home integration specialists.', count: 520 },
  { name: 'Carpentry', icon: 'carpenter', description: 'Custom furniture, cabinetry & architectural woodworking masters.', count: 680 },
  { name: 'Healthcare', icon: 'medical_services', description: 'Licensed nurses, caregivers & specialized medical support.', count: 920 },
])
</script>
