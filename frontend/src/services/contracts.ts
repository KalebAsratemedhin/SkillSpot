import api from './api'
import { AxiosResponse } from 'axios'

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export type PaymentSchedule = 'FIXED' | 'HOURLY'

export interface Contract {
  id: string
  job?: string
  job_title?: string
  job_application?: string
  client: string
  provider: string
  terms: string
  total_amount: number
  currency?: string
  payment_schedule?: PaymentSchedule
  hourly_rate?: number | null
  status: string
  signed_by_client?: boolean
  signed_by_provider?: boolean
  signatures?: ContractSignature[]
  start_date?: string
  end_date?: string
  created_at: string
  milestones?: ContractMilestone[]
  time_entries?: TimeEntry[]
  completion_percentage?: number
}

export interface TimeEntry {
  id: string
  contract: string
  provider: string
  date: string
  hours: number
  description?: string
  status: 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'PAID'
  approved_by?: string | null
  approved_at?: string | null
  amount?: number | null
  created_at: string
  updated_at: string
}

export interface ContractMilestone {
  id: string
  contract: string
  title: string
  description?: string
  amount: number
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED'
  order: number
  completed_at?: string
  created_at: string
}

export interface ContractSignature {
  id: string
  contract: string
  signer: string
  signer_email?: string
  signer_name?: string
  is_signed: boolean
  signed_at?: string
}

/** Payload for creating a contract (backend: provider_id, job?, job_application?, title, description, terms, total_amount, currency, payment_schedule, hourly_rate?, start_date, end_date?) */
export interface CreateContractPayload {
  provider_id: string
  job?: string
  job_application?: string
  title: string
  description: string
  terms: string
  total_amount: number
  currency?: string
  payment_schedule?: PaymentSchedule
  hourly_rate?: number | null
  start_date: string
  end_date?: string
}

export const contractsService = {
  list(params?: { my_contracts?: string; status?: string; page?: number; page_size?: number }): Promise<AxiosResponse<PaginatedResponse<Contract>>> {
    return api.get('/contracts/', { params })
  },
  get(id: string): Promise<AxiosResponse<Contract>> {
    return api.get(`/contracts/${id}/`)
  },
  create(data: CreateContractPayload): Promise<AxiosResponse<Contract>> {
    return api.post('/contracts/', data)
  },
  update(id: string, data: Partial<Contract>): Promise<AxiosResponse<Contract>> {
    return api.patch(`/contracts/${id}/`, data)
  },
  sign(id: string, data: { signature_data: string; signature_type?: string }): Promise<AxiosResponse<ContractSignature>> {
    return api.post(`/contracts/${id}/sign/`, { signature_type: data.signature_type ?? 'DIGITAL', ...data })
  },
  delete(id: string): Promise<AxiosResponse<void>> {
    return api.delete(`/contracts/${id}/`)
  },
  getMilestones(contractId: string): Promise<AxiosResponse<PaginatedResponse<ContractMilestone>>> {
    return api.get(`/contracts/${contractId}/milestones/`)
  },
  createMilestone(contractId: string, data: Partial<ContractMilestone>): Promise<AxiosResponse<ContractMilestone>> {
    return api.post(`/contracts/${contractId}/milestones/`, data)
  },
  updateMilestone(id: string, data: Partial<ContractMilestone>): Promise<AxiosResponse<ContractMilestone>> {
    return api.patch(`/contracts/milestones/${id}/`, data)
  },
  getTimeEntries(contractId: string): Promise<AxiosResponse<PaginatedResponse<TimeEntry>>> {
    return api.get(`/contracts/${contractId}/time-entries/`)
  },
  createTimeEntry(contractId: string, data: { date: string; hours: number; description?: string }): Promise<AxiosResponse<TimeEntry>> {
    return api.post(`/contracts/${contractId}/time-entries/`, data)
  },
  updateTimeEntry(id: string, data: Partial<TimeEntry>): Promise<AxiosResponse<TimeEntry>> {
    return api.patch(`/contracts/time-entries/${id}/`, data)
  },
}
