import {create} from 'zustand'
import {persist} from 'zustand/middleware'

export interface AuthUser {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  mobile_phone: string
  auth_type: 'local' | 'ldap'
  is_active: boolean
  role: 'admin' | 'user' | 'viewer'
  notify_on_playbook_completion: boolean
  notify_on_case_assignment: boolean
  has_avatar: boolean
  avatar_url: string
}

interface AuthState {
  token: string | null
  user: AuthUser | null
  setAuth: (token: string, user: AuthState['user']) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: 'agusta-auth' },
  ),
)
