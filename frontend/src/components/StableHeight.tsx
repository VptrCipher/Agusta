import type {ReactNode} from 'react'

interface StableHeightProps {
  minHeight: number
  children: ReactNode
}

export default function StableHeight({ minHeight, children }: StableHeightProps) {
  return (
    <div style={{ minHeight, width: '100%', minWidth: 0 }}>
      {children}
    </div>
  )
}
