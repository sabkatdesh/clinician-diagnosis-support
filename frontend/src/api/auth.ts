import { api } from './client'

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  doctor_id: string
}

export interface DoctorProfile {
  id: string
  email: string
  full_name: string
  hospital: string
  created_at: string
}

export const authApi = {
  login: (email: string, password: string) =>
    api.post<LoginResponse>('/auth/login', { email, password }).then(r => r.data),

  signup: (email: string, password: string, full_name: string, hospital: string) =>
    api.post('/auth/signup', { email, password, full_name, hospital }).then(r => r.data),

  me: () =>
    api.get<DoctorProfile>('/auth/me').then(r => r.data),
}
