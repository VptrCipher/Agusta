import client from './client'
import type {AuthUser} from '../stores/auth'

export type AuthType = 'local' | 'ldap'

export interface LoginResponse {
  access: string
  refresh: string
  user: AuthUser
}

export interface CredentialPayload {
  username: string
  auth_type: AuthType
  password?: string
}

export interface UserMutationResponse {
  user: AuthUser
  credentials: CredentialPayload
}

export interface ApiKey {
  id: number
  name: string
  key: string
  expires_at: string | null
  last_used_at: string | null
  created_at: string
  updated_at: string
}

export function login(username: string, password: string, authType: AuthType) {
  return client.post<LoginResponse>('/auth/login/', { username, password, auth_type: authType })
}
export function getMe() { return client.get<AuthUser>('/auth/me/') }
export function updateProfile(values: Partial<Pick<AuthUser, 'email' | 'first_name' | 'last_name' | 'mobile_phone' | 'notify_on_playbook_completion' | 'notify_on_case_assignment'>>) {
  return client.patch<AuthUser>('/auth/profile/', values)
}
export function changePassword(oldPassword: string, newPassword: string) {
  return client.post('/auth/change_password/', { old_password: oldPassword, new_password: newPassword })
}
