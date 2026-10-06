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

export interface Tag {
  id: string
  name: string
  category: 'SKILL' | 'CERTIFICATION' | 'LANGUAGE' | 'OTHER'
  description?: string
}

export type TagPageSize = 5 | 10 | 15 | 20 | 50

export interface TagListParams {
  category?: string
  page?: number
  page_size?: TagPageSize
}

export interface PaginatedTags {
  count: number
  next: string | null
  previous: string | null
  results: Tag[]
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

export interface ProviderRating {
  average: number | null
  count: number
}

export interface ProviderSkillTag {
  id: string
  name: string
  category?: string
  description?: string
}

export interface PublicProvider {
  user_id: string
  full_name: string
  avatar: string | null
  location: string
  headline_skills: ProviderSkillTag[]
  hourly_rate: string | null
  availability: string
  is_verified: boolean
  rating: ProviderRating
  member_since: string
}

export interface PublicProviderDetail extends PublicProvider {
  bio?: string
  years_of_experience?: number
  total_jobs_completed?: number
  skills?: ProviderSkillTag[]
  certifications?: ProviderSkillTag[]
  languages?: ProviderSkillTag[]
  experiences?: Experience[]
}

export interface PublicProviderListParams {
  q?: string
  search?: string
  location?: string
  skill?: string
  /** Single id, comma-separated ids, or array of ids (serialized as comma-separated). */
  skills?: string | string[]
  hourly_rate_min?: number
  hourly_rate_max?: number
  availability?: string
  is_verified?: boolean | string
  ordering?: string
  page?: number
  page_size?: number
}

export interface ProviderApplicationSummary {
  user_id: string
  full_name: string
  avatar: string | null
  location: string
  hourly_rate: string | null
  is_verified: boolean
  rating: ProviderRating
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
  listTags(params?: TagListParams): Promise<AxiosResponse<PaginatedTags | Tag[]>> {
    return api.get('/profiles/tags/', { params })
  },

  /**
   * Load every tag page (page_size up to 50). Pickers should use this so newer
   * seeded skills are not stuck behind default page_size=10.
   */
  async listAllTags(params?: { category?: string; page_size?: TagPageSize }): Promise<Tag[]> {
    const page_size = params?.page_size ?? 50
    const all: Tag[] = []
    let page = 1

    for (;;) {
      const response = await profilesService.listTags({
        category: params?.category,
        page,
        page_size,
      })
      const data = response.data

      if (Array.isArray(data)) {
        return data
      }

      const pageRows = data.results ?? []
      all.push(...pageRows)

      if (!data.next || pageRows.length === 0) break
      page += 1
      if (page > 100) break
    }

    return all
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
  listPublicProviders(
    params?: PublicProviderListParams
  ): Promise<AxiosResponse<{ results: PublicProvider[]; count: number; next?: string; previous?: string } | PublicProvider[]>> {
    const { skills, is_verified, ...rest } = params ?? {}
    const query: Record<string, string | number | boolean | undefined> = { ...rest }
    if (typeof is_verified === 'boolean') {
      query.is_verified = is_verified ? 'true' : 'false'
    } else if (is_verified != null && is_verified !== '') {
      query.is_verified = is_verified
    }
    if (Array.isArray(skills)) {
      if (skills.length) query.skills = skills.join(',')
    } else if (skills) {
      query.skills = skills
    }
    return api.get('/profiles/providers/', { params: query })
  },
  getPublicProvider(userId: string): Promise<AxiosResponse<PublicProviderDetail>> {
    return api.get(`/profiles/providers/${userId}/`)
  },
}
