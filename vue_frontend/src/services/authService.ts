import api from '@/services/api'
import type { AxiosResponse } from 'axios'

interface LoginResponse {
  user: any
  token?: string
}

export class AuthService {
  public static async login(email: string, password: string): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/dj-rest-auth/login/', {
      email,
      password,
    })
    return response.data
  }

  public static async logout(): Promise<void> {
    await api.post('/dj-rest-auth/logout/')
  }

  public static async signup(email: string, password: string): Promise<void> {
    await api.post('/dj-rest-auth/registration/', {
      email,
      password1: password,
      password2: password,
    })
  }

  public static async verifyEmail(key: string): Promise<AxiosResponse> {
    const response = await api.post('/dj-rest-auth/registration/verify-email/', { key })
    return response
  }

  public static async passwordReset(email: string): Promise<AxiosResponse> {
    const response = await api.post('/dj-rest-auth/password/reset/', { email })
    return response
  }

  public static async passwordResetConfirm(uid: string, token: string, password: string): Promise<AxiosResponse> {
    const response = await api.post('/dj-rest-auth/password/reset/confirm/', { uid, token, new_password1: password, new_password2: password })
    return response
  }

  public static async fetchUser(): Promise<any> {
    const response = await api.get('/dj-rest-auth/user/')
    return response.data
  }

  public static async changePassword(oldPassword: string, newPassword: string): Promise<AxiosResponse> {
    const response = await api.post('/dj-rest-auth/password/change/', {
      old_password: oldPassword,
      new_password1: newPassword,
      new_password2: newPassword,
    })
    return response
  }
}
