<template>
  <AppLayout>
    <div class="w-full max-w-[1200px] mx-auto px-4 md:px-6 py-10 md:py-16">
      <div class="mb-12 md:mb-16">
        <h1 class="text-3xl md:text-4xl font-bold text-midnight mb-4">Job categories</h1>
        <p class="text-slate-600 text-lg max-w-2xl">
          Find skilled professionals by category. Each area includes vetted providers ready to help with your project.
        </p>
      </div>

      <div class="space-y-8">
        <article
          v-for="category in categories"
          :key="category.slug"
          :id="category.slug"
          class="scroll-mt-24 rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-sm hover:shadow-md transition-shadow"
        >
          <div class="flex flex-col md:flex-row">
            <div class="md:w-64 shrink-0 aspect-video md:aspect-square bg-slate-100 flex items-center justify-center overflow-hidden">
              <img
                :src="category.image"
                :alt="category.name"
                class="w-full h-full object-cover"
                loading="lazy"
                @error="(e) => (e.currentTarget!.src = category.fallbackImage)"
              />
            </div>
            <div class="p-6 md:p-8 flex-1 flex flex-col justify-center">
              <div class="flex items-center gap-3 mb-3">
                <span class="flex items-center justify-center size-12 rounded-xl bg-amber/10 text-amber">
                  <span class="material-symbols-outlined text-2xl">{{ category.icon }}</span>
                </span>
                <h2 class="text-2xl font-bold text-midnight">{{ category.name }}</h2>
              </div>
              <p class="text-slate-600 leading-relaxed mb-4">{{ category.description }}</p>
              <p class="text-sm text-slate-500">{{ category.detail }}</p>
              <router-link
                v-if="authStore.isAuthenticated"
                to="/dashboard"
                class="inline-flex items-center gap-2 mt-4 text-amber font-semibold hover:underline"
              >
                Browse {{ category.name }} jobs
                <span class="material-symbols-outlined text-lg">arrow_forward</span>
              </router-link>
              <router-link
                v-else
                to="/register"
                class="inline-flex items-center gap-2 mt-4 text-amber font-semibold hover:underline"
              >
                Get started
                <span class="material-symbols-outlined text-lg">arrow_forward</span>
              </router-link>
            </div>
          </div>
        </article>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// Fallback image (generic gardening) used when a category image fails to load
const FALLBACK_IMAGE = 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=600&q=80'

const categories = ref([
  {
    slug: 'electrical',
    name: 'Electrical',
    icon: 'bolt',
    image: 'https://images.unsplash.com/photo-1621905251189-08b45d6a269e?w=600&q=80',
    fallbackImage: FALLBACK_IMAGE,
    description: 'Licensed electricians for residential and commercial work.',
    detail: 'Wiring, panel upgrades, lighting, smart home installation, and electrical repairs. All providers are qualified to work safely with local codes.',
  },
  {
    slug: 'plumbing',
    name: 'Plumbing',
    icon: 'plumbing',
    image: 'https://images.unsplash.com/photo-1607472586893-edb57bdc0e39?w=600&q=80',
    fallbackImage: FALLBACK_IMAGE,
    description: 'Plumbers for leaks, installations, and full plumbing projects.',
    detail: 'Leak detection and repair, fixture installation, drain cleaning, water heater service, and new construction plumbing. Licensed and insured professionals.',
  },
  {
    slug: 'carpentry',
    name: 'Carpentry & Woodworking',
    icon: 'carpenter',
    image: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80',
    fallbackImage: FALLBACK_IMAGE,
    description: 'Carpenters and woodworkers for custom builds and repairs.',
    detail: 'Custom furniture, cabinetry, trim work, decking, and general carpentry. From small repairs to full renovations and bespoke pieces.',
  },
  {
    slug: 'mechanics',
    name: 'Mechanics & Auto',
    icon: 'build',
    image: 'https://images.unsplash.com/photo-1581092160562-40aa08e78837?w=600&q=80',
    fallbackImage: FALLBACK_IMAGE,
    description: 'Auto mechanics for repair, maintenance, and diagnostics.',
    detail: 'Engine repair, brakes, oil changes, diagnostics, and general vehicle maintenance. Certified technicians for cars and light trucks.',
  },
  {
    slug: 'gardening',
    name: 'Gardening & Landscaping',
    icon: 'grass',
    image: 'https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=600&q=80',
    fallbackImage: 'https://images.unsplash.com/photo-1592150621744-aca64f48394a?w=600&q=80',
    description: 'Gardeners and landscapers for outdoor spaces.',
    detail: 'Lawn care, planting, pruning, landscaping design, and seasonal maintenance. Keep your garden and outdoor areas in top shape.',
  },
  {
    slug: 'cleaning',
    name: 'Cleaning & Maintenance',
    icon: 'cleaning_services',
    image: 'https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=600&q=80',
    fallbackImage: FALLBACK_IMAGE,
    description: 'Cleaning and general maintenance services.',
    detail: 'Deep cleaning, regular housekeeping, move-in/move-out cleans, and light maintenance. Reliable and thorough professionals.',
  },
])
</script>

