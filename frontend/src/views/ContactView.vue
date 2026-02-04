<template>
  <AppLayout>
    <div class="w-full max-w-[600px] mx-auto px-4 md:px-6 py-12 md:py-20">
      <h1 class="text-3xl md:text-4xl font-bold text-midnight mb-2">Contact us</h1>
      <p class="text-slate-600 mb-10">Have a question or feedback? Get in touch.</p>
      <div class="rounded-2xl border border-slate-200 bg-slate-50/50 p-6 md:p-8 space-y-6">
        <div>
          <h3 class="text-sm font-bold text-slate-500 uppercase tracking-wider mb-1">Email</h3>
          <a href="mailto:support@skillspot.com" class="text-midnight font-semibold hover:text-amber transition-colors">support@skillspot.com</a>
        </div>
        <p class="text-slate-600 text-sm">
          We aim to respond within 24–48 hours. For account or payment issues, please include your registered email so we can assist you quickly.
        </p>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import AppLayout from '@/components/AppLayout.vue'
</script>




