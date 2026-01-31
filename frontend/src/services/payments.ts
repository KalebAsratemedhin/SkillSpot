import api from './api'
import { AxiosResponse } from 'axios'

export interface Payment {
  id: string
  contract: string
  milestone?: string
  amount: number
  status: string
  payment_method: string
  stripe_payment_intent_id?: string
  created_at: string
}

export interface PaymentIntent {
  client_secret: string
  payment_intent_id: string
}

export interface StripeConnectStatus {
  connected: boolean
  account_id?: string
  onboarding_complete: boolean
}

export const paymentsService = {
  list(): Promise<AxiosResponse<Payment[]>> {
    return api.get('/payments/')
  },
  get(id: string): Promise<AxiosResponse<Payment>> {
    return api.get(`/payments/${id}/`)
  },
  createPaymentIntent(data: { amount: number, contract_id: string, milestone_id?: string }): Promise<AxiosResponse<PaymentIntent>> {
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
  onboardStripeConnect(): Promise<AxiosResponse<{ url: string }>> {
    return api.post('/payments/stripe-connect/onboard/')
  },
  loginStripeConnect(): Promise<AxiosResponse<{ url: string }>> {
    return api.post('/payments/stripe-connect/login/')
  },
}
