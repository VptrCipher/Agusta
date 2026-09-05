import {EditOutlined} from '@ant-design/icons'
import type {ReactNode} from 'react'
import {typography} from '../utils/typography'

export function editableLabel(label: ReactNode) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
      {label}
      <EditOutlined style={{ color: 'rgba(240, 238, 231, 0.35)', fontSize: typography.compact.fontSize }} />
    </span>
  )
}
