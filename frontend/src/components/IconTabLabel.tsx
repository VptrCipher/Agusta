import type {LucideIcon} from 'lucide-react'

const tabIconProps = {size: '1.2em', strokeWidth: 2}

interface IconTabLabelProps {
  icon: LucideIcon
  children: string
}

export default function IconTabLabel({ icon: Icon, children }: IconTabLabelProps) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
      <Icon {...tabIconProps} />
      {children}
    </span>
  )
}
