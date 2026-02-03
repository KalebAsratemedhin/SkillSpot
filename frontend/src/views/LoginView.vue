<template>
  <div class="bg-white min-h-screen flex overflow-hidden">
    <section class="hidden lg:flex lg:w-1/2 relative bg-midnight text-white flex-col justify-between p-16">
      <div class="z-10 flex items-center gap-2">
        <div class="w-10 h-10 bg-amber rounded-xl flex items-center justify-center">
          <span class="material-symbols-outlined text-midnight font-bold">handyman</span>
        </div>
        <span class="text-2xl font-extrabold tracking-tight">SkillSpot</span>
      </div>
      <div class="z-10 max-w-lg">
        <div class="mb-8">
          <span class="inline-block px-3 py-1 bg-amber/20 text-amber text-xs font-bold uppercase tracking-widest rounded-full mb-6">Welcome back</span>
          <h2 class="text-4xl font-bold leading-tight mb-6 italic text-amber-100">"SkillSpot connects me with clients who need my expertise. My calendar is always full."</h2>
        </div>
        <div class="flex items-center gap-4">
          <div class="relative">
            <img
              src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=128&h=128&fit=crop&q=80"
              alt="Sarah Chen"
              class="w-16 h-16 rounded-full object-cover border-2 border-amber bg-slate-400"
            />
            <div class="absolute -bottom-1 -right-1 bg-green-500 w-5 h-5 rounded-full border-2 border-midnight flex items-center justify-center">
              <span class="material-symbols-outlined text-[10px] text-white">check</span>
            </div>
          </div>
          <div>
            <p class="font-bold text-lg">Sarah Chen</p>
            <p class="text-slate-400 text-sm">Licensed Electrician, 8 years exp.</p>
            <div class="flex text-amber mt-1">
              <span class="material-symbols-outlined text-sm fill-1">star</span>
              <span class="material-symbols-outlined text-sm fill-1">star</span>
              <span class="material-symbols-outlined text-sm fill-1">star</span>
              <span class="material-symbols-outlined text-sm fill-1">star</span>
              <span class="material-symbols-outlined text-sm fill-1">star</span>
            </div>
          </div>
        </div>
      </div>
      <div class="absolute inset-0 opacity-20 pointer-events-none">
        <svg class="absolute bottom-0 left-0 w-full h-auto" viewBox="0 0 1000 1000" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="grad1" x1="0%" x2="100%" y1="0%" y2="100%">
              <stop offset="0%" style="stop-color:var(--amber);stop-opacity:0.2"></stop>
              <stop offset="100%" style="stop-color:var(--midnight);stop-opacity:0"></stop>
            </linearGradient>
          </defs>
          <circle cx="0" cy="1000" fill="url(#grad1)" r="600"></circle>
        </svg>
      </div>
      <div class="z-10 text-slate-500 text-sm">
        © 2024 SkillSpot Marketplace. Empowering local talent globally.
      </div>
    </section>
    <section class="w-full lg:w-1/2 flex flex-col bg-slate-50 overflow-y-auto">
      <div class="max-w-xl mx-auto w-full px-8 py-12 lg:py-20">
        <div class="mb-10 text-center lg:text-left">
          <div class="lg:hidden flex justify-center items-center gap-2 mb-8">
            <div class="w-8 h-8 bg-amber rounded-lg flex items-center justify-center">
              <span class="material-symbols-outlined text-midnight text-lg font-bold">handyman</span>
            </div>
            <span class="text-xl font-bold text-midnight tracking-tight">SkillSpot</span>
          </div>
          <h1 class="text-3xl font-extrabold text-midnight mb-2">Sign In</h1>
          <p class="text-slate-600">Welcome back! Enter your details to continue.</p>
        </div>
        <form @submit.prevent="handleSubmit" class="space-y-6">
          <FormField :error="errors.email">
            <Label for="email" class="text-sm font-semibold text-slate-700">Email Address</Label>
            <Input
              id="email"
              v-model="form.email"
              type="email"
              placeholder="name@skillspot.com"
              :error="errors.email"
              class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20 focus:border-amber"
            />
          </FormField>
          <FormField :error="errors.password">
            <div class="flex justify-between items-center">
              <Label for="password" class="text-sm font-semibold text-slate-700">Password</Label>
              <a class="text-amber text-xs font-bold hover:text-amber-600 transition-colors" href="#">Forgot password?</a>
            </div>
            <Input
              id="password"
              v-model="form.password"
              type="password"
              placeholder="••••••••"
              :error="errors.password"
              class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20 focus:border-amber"
            />
          </FormField>
          <div class="pt-2">
            <Button type="submit" :loading="authStore.loading" class="w-full py-4 bg-midnight text-white font-bold rounded-xl shadow-lg hover:bg-slate-800 transition-all flex items-center justify-center gap-2">
              Sign In
              <span class="material-symbols-outlined group-hover:translate-x-1 transition-transform">arrow_forward</span>
            </Button>
          </div>
          <div class="text-center pt-6 border-t border-slate-200">
            <p class="text-slate-600">
              Don't have an account?
              <router-link to="/register" class="text-amber font-bold hover:underline ml-1">Sign up for free</router-link>
            </p>
          </div>
        </form>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { loginSchema, type LoginFormData } from '@/lib/validations/auth'
import Input from '@/components/ui/Input.vue'
import Button from '@/components/ui/Button.vue'
import Label from '@/components/ui/Label.vue'
import FormField from '@/components/ui/FormField.vue'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive<LoginFormData>({
  email: '',
  password: '',
})

const errors = reactive({
  email: '',
  password: '',
})

async function handleSubmit() {
  errors.email = ''
  errors.password = ''

  try {
    const validated = loginSchema.parse(form)
    await authStore.login(validated)
    const redirect = router.currentRoute.value.query.redirect as string
    await router.push(redirect || '/dashboard')
  } catch (err: any) {
    if (err.name === 'ZodError') {
      err.errors?.forEach((error: any) => {
        const field = error.path?.[0] as keyof typeof errors
        if (field in errors) {
          errors[field] = error.message
        }
      })
    } else if (err.response?.data) {
      const data = err.response.data
      if (data.email) errors.email = Array.isArray(data.email) ? data.email[0] : data.email
      if (data.password) errors.password = Array.isArray(data.password) ? data.password[0] : data.password
      if (data.detail) errors.email = data.detail
      if (data.error) errors.email = data.error
    }
  }
}
</script>
