import api from './api'
import { AxiosResponse } from 'axios'

export interface RegisterData {
  email: string
  password: string
  password_confirm: string
  first_name: string
  last_name: string
  user_type: 'client' | 'provider'
}

export interface LoginData {
  email: string
  password: string
}

export interface LoginResponse {
  access: string
  refresh: string
}

export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  user_type: 'client' | 'provider' | 'BOTH'
  is_active: boolean
  date_joined: string
}

export interface PasswordResetData {
  email: string
}

export interface PasswordResetConfirmData {
  new_password: string
  new_password_confirm: string
}

export const authService = {
  register(data: RegisterData): Promise<AxiosResponse<User>> {
    const { password_confirm: _, ...payload } = data
    return api.post('/auth/register/', payload)
  },
  login(data: LoginData): Promise<AxiosResponse<LoginResponse>> {
    return api.post('/auth/login/', data)
  },
  logout(): Promise<AxiosResponse> {
    return api.post('/auth/logout/')
  },
  refreshToken(refresh: string): Promise<AxiosResponse<{ access: string }>> {
    return api.post('/auth/token/refresh/', { refresh })
  },
  resetPassword(data: PasswordResetData): Promise<AxiosResponse> {
    return api.post('/auth/reset-password/', data)
  },
  resetPasswordConfirm(uidb64: string, token: string, data: PasswordResetConfirmData): Promise<AxiosResponse> {
    return api.post(`/auth/reset-password-confirm/${uidb64}/${token}/`, data)
  },
  getCurrentUser(): Promise<AxiosResponse<User>> {
    return api.get('/auth/users/me/')
  },
}
