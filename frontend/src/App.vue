<template>
  <Toaster position="top-right" richColors closeButton />
  <router-view />
</template>

<script setup lang="ts">
import { Toaster } from 'vue-sonner'
</script>
