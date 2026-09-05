import type {AuthUser} from '../stores/auth'

export type PermissionKey = 'admin'

export function hasPermission(user: AuthUser | null, permission: PermissionKey) {
  if (!user) return false
  if (permission === 'admin') {
    return user.role === 'admin'
  }
  return false
}
