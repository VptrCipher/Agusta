import {Avatar} from 'antd'

interface UserAvatarProps {
  username?: string
  avatarUrl?: string
  size?: number
}

function initialFor(username?: string) {
  return (username?.trim()?.[0] || 'U').toUpperCase()
}

export default function UserAvatar({ username, avatarUrl, size = 32 }: UserAvatarProps) {
  return (
    <Avatar size={size} src={avatarUrl || undefined} style={{ backgroundColor: '#d97757', flexShrink: 0 }}>
      {avatarUrl ? null : initialFor(username)}
    </Avatar>
  )
}
