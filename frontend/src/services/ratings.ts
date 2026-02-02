import api from './api'
import { AxiosResponse } from 'axios'

export type RatingType = 'CLIENT_TO_PROVIDER' | 'PROVIDER_TO_CLIENT'

export interface Rating {
  id: string
  contract?: string
  job?: string
  rater: string
  rated_user: string
  rating_type: RatingType
  score: number
  comment?: string
  created_at: string
  updated_at?: string
}

export interface RatingStats {
  user_id?: string
  average_rating_as_provider?: number
  rating_count_as_provider?: number
  average_rating_as_client?: number
  rating_count_as_client?: number
  total_ratings?: number
  /** Combined average for display (computed from backend fields if needed) */
  average_rating?: number
}

export const ratingsService = {
  list(params?: { contract?: string; rater?: string; rating_type?: RatingType }): Promise<AxiosResponse<Rating[]>> {
    return api.get('/ratings/', { params })
  },
  get(id: string): Promise<AxiosResponse<Rating>> {
    return api.get(`/ratings/${id}/`)
  },
  create(data: { contract_id: string; rating_type: RatingType; score: number; comment?: string }): Promise<AxiosResponse<Rating>> {
    return api.post('/ratings/', data)
  },
  update(id: string, data: Partial<Rating>): Promise<AxiosResponse<Rating>> {
    return api.patch(`/ratings/${id}/`, data)
  },
  getStats(userId?: string): Promise<AxiosResponse<RatingStats>> {
    const url = userId ? `/ratings/stats/${userId}/` : '/ratings/stats/'
    return api.get(url)
  },
  getProviderRatings(userId: string): Promise<AxiosResponse<{ results?: Rating[] } | Rating[]>> {
    return api.get(`/ratings/providers/${userId}/`)
  },
  getClientRatings(userId: string): Promise<AxiosResponse<{ results?: Rating[] } | Rating[]>> {
    return api.get(`/ratings/clients/${userId}/`)
  },
}
