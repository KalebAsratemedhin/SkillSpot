import api from './api'
import { AxiosResponse } from 'axios'

export interface Contract {
  id: string
  job?: string
  job_application?: string
  client: string
  provider: string
  terms: string
  total_amount: number
  status: string
  signed_by_client?: boolean
  signed_by_provider?: boolean
  signatures?: ContractSignature[]
  start_date?: string
  end_date?: string
  created_at: string
  milestones?: ContractMilestone[]
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

/** Payload for creating a contract (backend: provider_id, job?, job_application?, title, description, terms, total_amount, currency, start_date, end_date?, milestones?) */
export interface CreateContractPayload {
  provider_id: string
  job?: string
  job_application?: string
  title: string
  description: string
  terms: string
  total_amount: number
  currency?: string
  start_date: string
  end_date?: string
  milestones?: Partial<ContractMilestone>[]
}

export const contractsService = {
  list(): Promise<AxiosResponse<Contract[]>> {
    return api.get('/contracts/')
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
  getMilestones(contractId: string): Promise<AxiosResponse<ContractMilestone[]>> {
    return api.get(`/contracts/${contractId}/milestones/`)
  },
  createMilestone(contractId: string, data: Partial<ContractMilestone>): Promise<AxiosResponse<ContractMilestone>> {
    return api.post(`/contracts/${contractId}/milestones/`, data)
  },
  updateMilestone(id: string, data: Partial<ContractMilestone>): Promise<AxiosResponse<ContractMilestone>> {
    return api.patch(`/contracts/milestones/${id}/`, data)
  },
}
