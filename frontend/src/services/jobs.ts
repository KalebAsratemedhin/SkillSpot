import api from './api'
import { AxiosResponse } from 'axios'

export interface JobClientProfile {
  id: string
  full_name: string
  email: string
  avatar: string | null
  location: string
  member_since: string
}

export interface JobClientRating {
  average: number | null
  count: number
}

/** Current user's application to this job (providers only; null if none). */
export interface JobMyApplication {
  id: string
  status: string
  cover_letter: string
  proposed_rate: string | number
  applied_at: string
}

/** Nested map pin from the jobs API (`null` when unset). */
export interface JobLocationCoords {
  latitude: number | string
  longitude: number | string
}

export interface Job {
  id: string
  title: string
  description: string
  category?: string
  /** Street / area text. */
  address?: string
  /**
   * Map coordinates `{ latitude, longitude }`, or `null`.
   * Legacy APIs may return a plain string here — treat as address text only.
   */
  location?: JobLocationCoords | string | null
  budget_min?: number
  budget_max?: number
  budget_type?: 'hourly' | 'fixed' | 'range'
  payment_schedule?: 'HOURLY' | 'FIXED'
  status: string
  client: string
  client_name?: string
  client_email?: string
  client_profile?: JobClientProfile | null
  client_rating?: JobClientRating | null
  my_application?: JobMyApplication | null
  created_at: string
  updated_at: string
  tags?: string[]
  required_skills?: { id: string; name: string; category?: string }[]
  applications_count?: number
  accepted_applications_count?: number
  /** @deprecated Prefer nested `location` — kept for older API responses. */
  latitude?: number | null
  longitude?: number | null
}

/** Textual address for display (never uses nested coordinate `location`). */
export function jobAddressText(job: {
  address?: string | null
  location?: JobLocationCoords | string | null
} | null | undefined): string {
  if (!job) return ''
  const a = job.address?.trim()
  if (a) return a
  if (typeof job.location === 'string') return job.location.trim()
  return ''
}

/** Map pin coords from nested `location` or legacy flat fields. */
export function jobCoordinates(job: {
  location?: JobLocationCoords | string | null
  latitude?: number | string | null
  longitude?: number | string | null
} | null | undefined): { lat: number; lng: number } | null {
  if (!job) return null
  const nested = job.location
  if (nested && typeof nested === 'object') {
    const lat = Number(nested.latitude)
    const lng = Number(nested.longitude)
    if (Number.isFinite(lat) && Number.isFinite(lng)) return { lat, lng }
  }
  if (job.latitude != null && job.longitude != null) {
    const lat = Number(job.latitude)
    const lng = Number(job.longitude)
    if (Number.isFinite(lat) && Number.isFinite(lng)) return { lat, lng }
  }
  return null
}

/** Backend DecimalField(decimal_places=6). */
export function roundJobCoord(n: number, places = 6): number {
  const f = 10 ** places
  return Math.round(n * f) / f
}

/** Normalize create/update API payloads that may omit or wrap `id`. */
export function coerceJob(data: unknown): Job | null {
  if (data == null) return null
  if (typeof data === 'string') {
    try {
      return coerceJob(JSON.parse(data) as unknown)
    } catch {
      return null
    }
  }
  if (typeof data !== 'object' || Array.isArray(data)) return null
  const obj = data as Record<string, unknown>
  if (obj.job && typeof obj.job === 'object') return coerceJob(obj.job)
  if (obj.data && typeof obj.data === 'object' && !Array.isArray(obj.data)) {
    const inner = obj.data as Record<string, unknown>
    if ('id' in inner || 'title' in inner) return coerceJob(inner)
  }
  const id = obj.id ?? obj.pk
  if (id == null || String(id).trim() === '') return null
  return { ...(obj as unknown as Job), id: String(id) }
}

export function jobIdFromLocationHeader(location: unknown): string | null {
  if (typeof location !== 'string' || !location.trim()) return null
  const match = location.match(/\/jobs\/([0-9a-fA-F-]{36})\/?/)
  return match?.[1] ?? null
}

export interface JobApplication {
  id: string
  job: string
  job_title?: string
  job_client?: string
  provider: string
  provider_name?: string
  provider_email?: string
  provider_summary?: {
    user_id: string
    full_name: string
    avatar: string | null
    location: string
    hourly_rate: string | null
    is_verified: boolean
    rating: { average: number | null; count: number }
  } | null
  message?: string
  cover_letter?: string
  proposed_rate?: number
  status: string
  created_at: string
  applied_at?: string
  reviewed_at?: string
}

export interface JobInvitation {
  id: string
  job: string | { id?: string; title?: string }
  provider: string
  provider_name?: string
  provider_email?: string
  message: string
  status: string
  created_at?: string
  invited_at?: string
}

export interface JobListParams {
  category?: string
  location?: string
  status?: string
  /** Preferred search param (backend also accepts `search`) */
  q?: string
  search?: string
  page?: number
  page_size?: number
  skill?: string
  skills?: string
  budget_min?: number
  budget_max?: number
  payment_schedule?: 'HOURLY' | 'FIXED' | string
  ordering?: string
  /** When true (and user is client), returns only the current user's jobs including completed/cancelled */
  my_jobs?: boolean
}

export const jobsService = {
  list(params?: JobListParams): Promise<AxiosResponse<{ results: Job[], count: number, next?: string, previous?: string }>> {
    const { my_jobs, q, search, ...rest } = params ?? {}
    const requestParams = { ...rest } as Record<string, string | number | undefined>
    if (my_jobs === true) requestParams.my_jobs = 'true'
    const query = (q || search || '').trim()
    if (query) requestParams.q = query
    return api.get('/jobs/', { params: requestParams })
  },
  get(id: string): Promise<AxiosResponse<Job>> {
    return api.get(`/jobs/${id}/`)
  },
  create(data: Partial<Job> | Record<string, unknown>): Promise<AxiosResponse<Job>> {
    return api.post('/jobs/', data)
  },
  update(id: string, data: Partial<Job> | Record<string, unknown>): Promise<AxiosResponse<Job>> {
    return api.patch(`/jobs/${id}/`, data)
  },
  delete(id: string): Promise<AxiosResponse<void>> {
    return api.delete(`/jobs/${id}/`)
  },
  close(id: string): Promise<AxiosResponse<Job>> {
    return api.post(`/jobs/${id}/close/`)
  },
  getApplications(jobId: string): Promise<AxiosResponse<JobApplication[]>> {
    return api.get(`/jobs/${jobId}/applications/`)
  },
  getMyApplications(): Promise<AxiosResponse<JobApplication[]>> {
    return api.get('/jobs/applications/')
  },
  createApplication(
    jobId: string,
    data: { cover_letter?: string; proposed_rate?: number }
  ): Promise<AxiosResponse<JobApplication>> {
    const body: { cover_letter: string; proposed_rate?: number } = {
      cover_letter: data.cover_letter ?? '',
    }
    if (data.proposed_rate != null && !Number.isNaN(data.proposed_rate) && data.proposed_rate >= 0) {
      body.proposed_rate = data.proposed_rate
    }
    return api.post(`/jobs/${jobId}/applications/`, body)
  },
  getApplication(id: string): Promise<AxiosResponse<JobApplication>> {
    return api.get(`/jobs/applications/${id}/`)
  },
  updateApplication(id: string, data: Partial<JobApplication>): Promise<AxiosResponse<JobApplication>> {
    return api.patch(`/jobs/applications/${id}/`, data)
  },
  listInvitations(): Promise<AxiosResponse<JobInvitation[]>> {
    return api.get('/jobs/invitations/')
  },
  getInvitation(id: string): Promise<AxiosResponse<JobInvitation>> {
    return api.get(`/jobs/invitations/${id}/`)
  },
  createInvitation(data: Partial<JobInvitation>): Promise<AxiosResponse<JobInvitation>> {
    return api.post('/jobs/invitations/', data)
  },
  updateInvitation(id: string, data: Partial<JobInvitation>): Promise<AxiosResponse<JobInvitation>> {
    return api.patch(`/jobs/invitations/${id}/`, data)
  },
}
