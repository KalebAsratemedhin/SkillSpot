import api from './api'
import { AxiosResponse } from 'axios'

export interface Job {
  id: string
  title: string
  description: string
  category?: string
  location: string
  budget_min?: number
  budget_max?: number
  budget_type?: 'hourly' | 'fixed' | 'range'
  status: string
  client: string
  client_name?: string
  client_email?: string
  created_at: string
  updated_at: string
  tags?: string[]
  required_skills?: { id: string; name: string; category?: string }[]
}

export interface JobApplication {
  id: string
  job: string
  job_title?: string
  job_client?: string
  provider: string
  provider_name?: string
  provider_email?: string
  message?: string
  cover_letter?: string
  proposed_rate?: number
  status: string
  created_at: string
  applied_at?: string
}

export interface JobInvitation {
  id: string
  job: string | { id?: string; title?: string }
  provider: string
  message: string
  status: string
  created_at?: string
  invited_at?: string
}

export interface JobListParams {
  category?: string
  location?: string
  status?: string
  search?: string
  page?: number
  /** When true (and user is client), returns only the current user's jobs including completed/cancelled */
  my_jobs?: boolean
}

export const jobsService = {
  list(params?: JobListParams): Promise<AxiosResponse<{ results: Job[], count: number, next?: string, previous?: string }>> {
    const { my_jobs, ...rest } = params ?? {}
    const requestParams = { ...rest } as Record<string, string | number | undefined>
    if (my_jobs === true) requestParams.my_jobs = 'true'
    return api.get('/jobs/', { params: requestParams })
  },
  get(id: string): Promise<AxiosResponse<Job>> {
    return api.get(`/jobs/${id}/`)
  },
  create(data: Partial<Job>): Promise<AxiosResponse<Job>> {
    return api.post('/jobs/', data)
  },
  update(id: string, data: Partial<Job>): Promise<AxiosResponse<Job>> {
    return api.patch(`/jobs/${id}/`, data)
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
