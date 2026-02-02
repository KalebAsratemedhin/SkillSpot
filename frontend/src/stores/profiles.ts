import { defineStore } from 'pinia'
import { ref } from 'vue'
import { profilesService, type Profile, type ServiceProviderProfile, type Tag, type Experience } from '@/services/profiles'

export const useProfilesStore = defineStore('profiles', () => {
  const profile = ref<Profile | null>(null)
  const providerProfile = ref<ServiceProviderProfile | null>(null)
  const tags = ref<Tag[]>([])
  const experiences = ref<Experience[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchProfile() {
    try {
      loading.value = true
      error.value = null
      const response = await profilesService.getProfile()
      profile.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch profile'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateProfile(data: Partial<Profile>) {
    try {
      loading.value = true
      error.value = null
      const response = await profilesService.updateProfile(data)
      profile.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to update profile'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function uploadAvatar(file: File) {
    try {
      loading.value = true
      error.value = null
      const response = await profilesService.uploadProfileAvatar(file)
      profile.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to upload photo'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchProviderProfile() {
    try {
      loading.value = true
      error.value = null
      const response = await profilesService.getProviderProfile()
      providerProfile.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch provider profile'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateProviderProfile(data: Partial<ServiceProviderProfile>) {
    try {
      loading.value = true
      error.value = null
      const response = await profilesService.updateProviderProfile(data)
      providerProfile.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to update provider profile'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchTags(params?: { category?: string }) {
    try {
      loading.value = true
      error.value = null
      const response = await profilesService.listTags(params)
      const data = response.data
      tags.value = Array.isArray(data) ? data : (data?.results ?? [])
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch tags'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createTag(data: Partial<Tag>) {
    try {
      loading.value = true
      error.value = null
      const response = await profilesService.createTag(data)
      tags.value.push(response.data)
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to create tag'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchExperiences() {
    try {
      loading.value = true
      error.value = null
      const response = await profilesService.listExperiences()
      const data = response.data
      experiences.value = Array.isArray(data) ? data : (data?.results ?? [])
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch experiences'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createExperience(data: Partial<Experience>) {
    try {
      loading.value = true
      error.value = null
      const response = await profilesService.createExperience(data)
      experiences.value.push(response.data)
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to create experience'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateExperience(id: string, data: Partial<Experience>) {
    try {
      loading.value = true
      error.value = null
      const response = await profilesService.updateExperience(id, data)
      const index = experiences.value.findIndex(e => e.id === id)
      if (index !== -1) {
        experiences.value[index] = response.data
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to update experience'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteExperience(id: string) {
    try {
      loading.value = true
      error.value = null
      await profilesService.deleteExperience(id)
      experiences.value = experiences.value.filter(e => e.id !== id)
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to delete experience'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    profile,
    providerProfile,
    tags,
    experiences,
    loading,
    error,
    fetchProfile,
    updateProfile,
    uploadAvatar,
    fetchProviderProfile,
    updateProviderProfile,
    fetchTags,
    createTag,
    fetchExperiences,
    createExperience,
    updateExperience,
    deleteExperience,
  }
})
