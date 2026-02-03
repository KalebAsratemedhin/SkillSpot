<template>
  <footer class="bg-midnight text-white border-t border-white/10 pt-16 pb-8">
    <div class="mx-auto max-w-[1400px] px-6">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-12 mb-16">
        <div class="col-span-2 md:col-span-2">
          <div class="flex items-center gap-3 text-amber mb-6">
            <svg class="size-6" fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
              <path d="M44 11.2727C44 14.0109 39.8386 16.3957 33.69 17.6364C39.8386 18.877 44 21.2618 44 24C44 26.7382 39.8386 29.123 33.69 30.3636C39.8386 31.6043 44 33.9891 44 36.7273C44 40.7439 35.0457 44 24 44C12.9543 44 4 40.7439 4 36.7273C4 33.9891 8.16144 31.6043 14.31 30.3636C8.16144 29.123 4 26.7382 4 24C4 21.2618 8.16144 18.877 14.31 17.6364C8.16144 16.3957 4 14.0109 4 11.2727C4 7.25611 12.9543 4 24 4C35.0457 4 44 7.25611 44 11.2727Z" fill="currentColor"></path>
            </svg>
            <h2 class="text-xl font-extrabold tracking-tight uppercase italic">SkillSpot</h2>
          </div>
          <p class="text-slate-400 text-sm leading-relaxed max-w-[300px]">
            Connecting quality local professionals with homeowners. Reliable service at your fingertips.
          </p>
        </div>
        <div>
          <h5 class="font-bold text-sm mb-6 text-white">Platform</h5>
          <ul class="flex flex-col gap-4 text-sm text-slate-400">
            <li><router-link to="/categories" class="hover:text-amber transition-colors">Categories</router-link></li>
            <li><router-link to="/login" class="hover:text-amber transition-colors">Login</router-link></li>
            <li><router-link to="/register" class="hover:text-amber transition-colors">Register</router-link></li>
          </ul>
        </div>
        <div>
          <h5 class="font-bold text-sm mb-6 text-white">Company</h5>
          <ul class="flex flex-col gap-4 text-sm text-slate-400">
            <li><router-link to="/about" class="hover:text-amber transition-colors">About</router-link></li>
            <li><router-link to="/contact" class="hover:text-amber transition-colors">Contact</router-link></li>
          </ul>
        </div>
      </div>
      <div class="border-t border-white/10 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
        <p class="text-xs text-slate-400">© {{ new Date().getFullYear() }} SkillSpot. All rights reserved.</p>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
</script>
