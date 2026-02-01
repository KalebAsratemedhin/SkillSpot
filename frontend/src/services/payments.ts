import api from './api'
import { AxiosResponse } from 'axios'

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface Payment {
  id: string
  contract: string
  milestone?: string
  time_entry?: string
  time_entry_id?: string
  amount: number
  status: string
  payment_method: string
  stripe_payment_intent_id?: string
  created_at: string
}

export interface PaymentIntent {
  client_secret: string
  payment_intent_id: string
  payment_id?: string
}

export interface CreatePaymentPayload {
  contract: string
  milestone_id?: string
  time_entry_id?: string
  amount: number
  currency: string
  description?: string
  payment_method?: string
}

export interface StripeConnectStatus {
  has_account: boolean
  account_id?: string
  charges_enabled?: boolean
  payouts_enabled?: boolean
  details_submitted?: boolean
  enabled?: boolean
  message?: string
}

export const paymentsService = {
  list(params?: { contract?: string; milestone?: string; time_entry?: string; status?: string }): Promise<AxiosResponse<PaginatedResponse<Payment>>> {
    return api.get('/payments/', { params })
  },
  get(id: string): Promise<AxiosResponse<Payment>> {
    return api.get(`/payments/${id}/`)
  },
  create(data: CreatePaymentPayload): Promise<AxiosResponse<Payment>> {
    return api.post('/payments/', data)
  },
  createPaymentIntent(data: { payment_id: string; return_url?: string }): Promise<AxiosResponse<PaymentIntent>> {
    return api.post('/payments/create-intent/', data)
  },
  confirmPayment(paymentId: string, data: { payment_intent_id: string }): Promise<AxiosResponse<Payment>> {
    return api.post(`/payments/${paymentId}/confirm/`, data)
  },
  getHistory(): Promise<AxiosResponse<Payment[]>> {
    return api.get('/payments/history/')
  },
  getStripeConnectStatus(): Promise<AxiosResponse<StripeConnectStatus>> {
    return api.get('/payments/stripe-connect/status/')
  },
  onboardStripeConnect(): Promise<AxiosResponse<{ onboarding_url: string; account_id?: string; message?: string }>> {
    return api.post('/payments/stripe-connect/onboard/')
  },
  loginStripeConnect(): Promise<AxiosResponse<{ login_url: string; message?: string }>> {
    return api.get('/payments/stripe-connect/login/')
  },
}
