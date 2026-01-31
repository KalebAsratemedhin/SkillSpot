import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authService, type User, type LoginData, type RegisterData } from '@/services/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
  const isProvider = computed(() => user.value?.user_type === 'provider')
  const isClient = computed(() => user.value?.user_type === 'client')

  async function login(credentials: LoginData) {
    try {
      loading.value = true
      error.value = null
      const response = await authService.login(credentials)
      const { access, refresh } = response.data
      
      accessToken.value = access
      refreshToken.value = refresh
      localStorage.setItem('access_token', access)
      localStorage.setItem('refresh_token', refresh)
      
      await fetchUser()
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Login failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function register(data: RegisterData) {
    try {
      loading.value = true
      error.value = null
      await authService.register(data)
      await login({ email: data.email, password: data.password })
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Registration failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await authService.logout()
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      user.value = null
      accessToken.value = null
      refreshToken.value = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  }

  async function fetchUser() {
    try {
      const response = await authService.getCurrentUser()
      user.value = response.data
    } catch (err) {
      console.error('Failed to fetch user:', err)
      await logout()
    }
  }

  async function initialize() {
    if (accessToken.value) {
      await fetchUser()
    }
  }

  return {
    user,
    accessToken,
    refreshToken,
    loading,
    error,
    isAuthenticated,
    isProvider,
    isClient,
    login,
    register,
    logout,
    fetchUser,
    initialize,
  }
})
