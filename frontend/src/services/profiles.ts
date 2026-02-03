import api from './api'
import { AxiosResponse } from 'axios'

export interface Profile {
  id: string
  user: string
  email?: string
  user_type?: string
  first_name?: string
  last_name?: string
  full_name?: string
  phone_number?: string
  avatar?: string
  bio?: string
  location?: string
  address?: string
  timezone?: string
  is_verified?: boolean
  created_at: string
  updated_at: string
}

export interface ServiceProviderProfile {
  id: string
  profile: Profile | string
  hourly_rate?: number
  availability_status?: string
  years_of_experience?: number
  service_radius?: number
  skills?: Tag[]
  certifications?: Tag[]
  languages?: Tag[]
  /** For API update: list of tag IDs to set as skills */
  skill_ids?: string[]
  portfolio_visibility?: boolean
  total_jobs_completed?: number
  average_rating?: number
  total_earnings?: number
  experiences?: Experience[]
  created_at: string
  updated_at: string
}

export interface Tag {
  id: string
  name: string
  category: 'SKILL' | 'CERTIFICATION' | 'LANGUAGE' | 'OTHER'
  description?: string
}

export interface Experience {
  id: string
  title: string
  company_name?: string
  description?: string
  location?: string
  start_date: string
  end_date?: string
  is_current: boolean
  created_at: string
  updated_at: string
}

export const profilesService = {
  getProfile(): Promise<AxiosResponse<Profile>> {
    return api.get('/profiles/me/')
  },
  updateProfile(data: Partial<Profile>): Promise<AxiosResponse<Profile>> {
    return api.patch('/profiles/me/', data)
  },
  uploadProfileAvatar(file: File): Promise<AxiosResponse<Profile>> {
    const formData = new FormData()
    formData.append('avatar', file)
    return api.patch('/profiles/me/', formData)
  },
  getProviderProfile(): Promise<AxiosResponse<ServiceProviderProfile>> {
    return api.get('/profiles/provider/')
  },
  updateProviderProfile(data: Partial<ServiceProviderProfile> & { skill_ids?: string[] }): Promise<AxiosResponse<ServiceProviderProfile>> {
    return api.patch('/profiles/provider/', data)
  },
  listTags(params?: { category?: string }): Promise<AxiosResponse<Tag[]>> {
    return api.get('/profiles/tags/', { params })
  },
  createTag(data: Partial<Tag>): Promise<AxiosResponse<Tag>> {
    return api.post('/profiles/tags/', data)
  },
  listExperiences(): Promise<AxiosResponse<Experience[]>> {
    return api.get('/profiles/experiences/')
  },
  createExperience(data: Partial<Experience>): Promise<AxiosResponse<Experience>> {
    return api.post('/profiles/experiences/', data)
  },
  getExperience(id: string): Promise<AxiosResponse<Experience>> {
    return api.get(`/profiles/experiences/${id}/`)
  },
  updateExperience(id: string, data: Partial<Experience>): Promise<AxiosResponse<Experience>> {
    return api.patch(`/profiles/experiences/${id}/`, data)
  },
  deleteExperience(id: string): Promise<AxiosResponse> {
    return api.delete(`/profiles/experiences/${id}/`)
  },
}
