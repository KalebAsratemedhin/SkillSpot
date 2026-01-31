<template>
  <div :class="['flex flex-col bg-slate-50', isMessagesPage ? 'h-screen overflow-hidden' : 'min-h-screen']">
    <Header />
    <main class="flex-1 ">
      <slot />
    </main>
    <Footer v-if="!isMessagesPage" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Header from '@/components/Header.vue'
import Footer from '@/components/Footer.vue'

const route = useRoute()
const isMessagesPage = computed(() => route.path.startsWith('/messages'))
</script>
