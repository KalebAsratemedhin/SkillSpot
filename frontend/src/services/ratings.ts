import api from './api'
import { AxiosResponse } from 'axios'

export interface Rating {
  id: string
  contract: string
  rater: string
  ratee: string
  rating: number
  comment?: string
  created_at: string
}

export interface RatingStats {
  average_rating: number
  total_ratings: number
  rating_breakdown: {
    [key: number]: number
  }
}

export const ratingsService = {
  list(params?: { provider_id?: string, client_id?: string }): Promise<AxiosResponse<Rating[]>> {
    return api.get('/ratings/', { params })
  },
  get(id: string): Promise<AxiosResponse<Rating>> {
    return api.get(`/ratings/${id}/`)
  },
  create(data: Partial<Rating>): Promise<AxiosResponse<Rating>> {
    return api.post('/ratings/', data)
  },
  update(id: string, data: Partial<Rating>): Promise<AxiosResponse<Rating>> {
    return api.patch(`/ratings/${id}/`, data)
  },
  getStats(userId?: string): Promise<AxiosResponse<RatingStats>> {
    const url = userId ? `/ratings/stats/${userId}/` : '/ratings/stats/'
    return api.get(url)
  },
  getProviderRatings(providerId: string): Promise<AxiosResponse<Rating[]>> {
    return api.get(`/ratings/providers/${providerId}/`)
  },
  getClientRatings(clientId: string): Promise<AxiosResponse<Rating[]>> {
    return api.get(`/ratings/clients/${clientId}/`)
  },
}
