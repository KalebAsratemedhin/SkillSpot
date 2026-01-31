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
          <span class="inline-block px-3 py-1 bg-amber/20 text-amber text-xs font-bold uppercase tracking-widest rounded-full mb-6">Top Rated Pro</span>
          <h2 class="text-4xl font-bold leading-tight mb-6 italic text-amber-100">"SkillSpot changed my business. I found 15 new regular clients in my first month alone."</h2>
        </div>
        <div class="flex items-center gap-4">
          <div class="relative">
            <div class="w-16 h-16 rounded-full object-cover border-2 border-amber bg-slate-400"></div>
            <div class="absolute -bottom-1 -right-1 bg-green-500 w-5 h-5 rounded-full border-2 border-midnight flex items-center justify-center">
              <span class="material-symbols-outlined text-[10px] text-white">check</span>
            </div>
          </div>
          <div>
            <p class="font-bold text-lg">Mark Henderson</p>
            <p class="text-slate-400 text-sm">Master Plumber, 12 years exp.</p>
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
          <h1 class="text-3xl font-extrabold text-midnight mb-2">Join SkillSpot</h1>
          <p class="text-slate-600">Start your journey today. Pick your role to begin.</p>
        </div>
        <form @submit.prevent="handleSubmit" class="space-y-8">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <label class="relative group cursor-pointer">
              <input v-model="form.user_type" value="client" class="peer sr-only" name="role" type="radio"/>
              <div class="flex flex-col p-6 bg-white border-2 border-slate-200 rounded-2xl transition-all peer-checked:border-amber peer-checked:bg-amber/5 hover:border-slate-300">
                <div class="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform peer-checked:bg-amber peer-checked:text-white">
                  <span class="material-symbols-outlined">person_search</span>
                </div>
                <span class="font-bold text-midnight text-lg">I want to hire</span>
                <span class="text-slate-500 text-sm mt-1">Find top experts for my projects</span>
              </div>
              <div class="absolute top-4 right-4 text-amber opacity-0 peer-checked:opacity-100">
                <span class="material-symbols-outlined">check_circle</span>
              </div>
            </label>
            <label class="relative group cursor-pointer">
              <input v-model="form.user_type" value="provider" class="peer sr-only" name="role" type="radio"/>
              <div class="flex flex-col p-6 bg-white border-2 border-slate-200 rounded-2xl transition-all peer-checked:border-amber peer-checked:bg-amber/5 hover:border-slate-300">
                <div class="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform peer-checked:bg-amber peer-checked:text-white">
                  <span class="material-symbols-outlined">construction</span>
                </div>
                <span class="font-bold text-midnight text-lg">I want to work</span>
                <span class="text-slate-500 text-sm mt-1">Offer my services & grow business</span>
              </div>
              <div class="absolute top-4 right-4 text-amber opacity-0 peer-checked:opacity-100">
                <span class="material-symbols-outlined">check_circle</span>
              </div>
            </label>
          </div>
          <div class="space-y-4">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField :error="errors.first_name">
                <Label for="first_name" class="text-sm font-semibold text-slate-700">First Name</Label>
                <Input
                  id="first_name"
                  v-model="form.first_name"
                  placeholder="Mark"
                  :error="errors.first_name"
                  class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20 focus:border-amber"
                />
              </FormField>
              <FormField :error="errors.last_name">
                <Label for="last_name" class="text-sm font-semibold text-slate-700">Last Name</Label>
                <Input
                  id="last_name"
                  v-model="form.last_name"
                  placeholder="Henderson"
                  :error="errors.last_name"
                  class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20 focus:border-amber"
                />
              </FormField>
            </div>
            <FormField :error="errors.email">
              <Label for="email" class="text-sm font-semibold text-slate-700">Email Address</Label>
              <Input
                id="email"
                v-model="form.email"
                type="email"
                placeholder="mark@company.com"
                :error="errors.email"
                class="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20 focus:border-amber"
              />
            </FormField>
            <FormField :error="errors.password">
              <Label for="password" class="text-sm font-semibold text-slate-700">Password</Label>
              <p class="text-xs text-slate-500 mb-1.5">At least 8 characters; avoid common passwords and all numbers.</p>
              <div class="relative">
                <Input
                  id="password"
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="••••••••"
                  :error="errors.password"
                  class="w-full px-4 py-3 pr-12 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20 focus:border-amber"
                />
                <button
                  type="button"
                  class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 z-10"
                  :aria-label="showPassword ? 'Hide password' : 'Show password'"
                  @click.stop="showPassword = !showPassword"
                >
                  <span class="material-symbols-outlined text-lg">{{ showPassword ? 'visibility_off' : 'visibility' }}</span>
                </button>
              </div>
            </FormField>
            <FormField :error="errors.password_confirm">
              <Label for="password_confirm" class="text-sm font-semibold text-slate-700">Confirm Password</Label>
              <div class="relative">
                <Input
                  id="password_confirm"
                  v-model="form.password_confirm"
                  :type="showPasswordConfirm ? 'text' : 'password'"
                  placeholder="••••••••"
                  :error="errors.password_confirm"
                  class="w-full px-4 py-3 pr-12 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber/20 focus:border-amber"
                />
                <button
                  type="button"
                  class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 z-10"
                  :aria-label="showPasswordConfirm ? 'Hide password' : 'Show password'"
                  @click.stop="showPasswordConfirm = !showPasswordConfirm"
                >
                  <span class="material-symbols-outlined text-lg">{{ showPasswordConfirm ? 'visibility_off' : 'visibility' }}</span>
                </button>
              </div>
            </FormField>
          </div>
          <div class="pt-2">
            <Button type="submit" :loading="authStore.loading" class="w-full py-4 bg-midnight text-white font-bold rounded-xl shadow-lg hover:bg-slate-800 transition-all flex items-center justify-center gap-2">
              Create Account
              <span class="material-symbols-outlined group-hover:translate-x-1 transition-transform">arrow_forward</span>
            </Button>
          </div>
          <p class="text-center text-slate-500 text-sm">
            By continuing, you agree to our
            <a class="text-midnight font-bold hover:text-amber transition-colors" href="#">Terms of Service</a> &
            <a class="text-midnight font-bold hover:text-amber transition-colors" href="#">Privacy Policy</a>.
          </p>
          <div class="text-center pt-6 border-t border-slate-200">
            <p class="text-slate-600">
              Already have an account?
              <router-link to="/login" class="text-amber font-bold hover:underline ml-1">Sign In</router-link>
            </p>
          </div>
        </form>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { useAuthStore } from '@/stores/auth'
import { registerSchema, type RegisterFormData } from '@/lib/validations/auth'
import Input from '@/components/ui/Input.vue'
import Button from '@/components/ui/Button.vue'
import Label from '@/components/ui/Label.vue'
import FormField from '@/components/ui/FormField.vue'

const router = useRouter()
const authStore = useAuthStore()
const showPassword = ref(false)
const showPasswordConfirm = ref(false)

const form = reactive<RegisterFormData>({
  first_name: '',
  last_name: '',
  email: '',
  user_type: 'client',
  password: '',
  password_confirm: '',
})

const errors = reactive({
  first_name: '',
  last_name: '',
  email: '',
  user_type: '',
  password: '',
  password_confirm: '',
})

function getFirstMessage(data: Record<string, unknown>): string {
  return data.error as string || 'Registration failed. Please check the form.'
}

async function handleSubmit() {
  Object.keys(errors).forEach(key => {
    errors[key as keyof typeof errors] = ''
  })

  try {
    const validated = registerSchema.parse(form)
    await authStore.register(validated)
    router.push('/dashboard')
  } catch (err: any) {
    if (err.name === 'ZodError') {
      const first = err.issues?.[0]
      const message = first ? (first.message as string) : 'Please fix the form errors.'
      toast.error(message)
      err.issues.forEach((issue: { path: (string | number)[]; message: string }) => {
        const field = issue.path[0] as keyof typeof errors
        if (field in errors) {
          errors[field] = issue.message
        }
      })
    } else if (err.response?.data) {
      const data = err.response.data as Record<string, unknown>
      const message = getFirstMessage(data)
      toast.error(message)
      Object.keys(data).forEach(key => {
        if (key in errors) {
          const val = data[key]
          errors[key as keyof typeof errors] = Array.isArray(val) ? (val[0] as string) : (val as string)
        }
      })
    } else {
      toast.error('Registration failed. Please try again.')
    }
  }
}
</script>
