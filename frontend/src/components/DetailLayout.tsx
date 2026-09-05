import {Button, Tag, theme} from 'antd'
import type {ReactNode} from 'react'
import {comfortableTagProps} from '../utils/tagStyles'
import {fontFamilyMono, typography} from '../utils/typography'

interface Field {
  label: string
  value: ReactNode
  color?: string
  mono?: boolean
}

interface Action {
  label: string
  icon?: ReactNode
  onClick: () => void
  danger?: boolean
}

interface DetailLayoutProps {
  title: string
  fields: Field[]
  description?: string
  actions?: Action[]
  tabs: ReactNode
}

export default function DetailLayout({ title, fields, description, actions, tabs }: DetailLayoutProps) {
  const { token } = theme.useToken()

  return (
    <div style={{ display: 'flex', gap: 16, height: 'calc(100vh - 112px)' }}>
      {/* Left Panel */}
      <div style={{
        width: 320,
        flexShrink: 0,
        background: token.colorBgContainer,
        borderRadius: 8,
        padding: 16,
        overflowY: 'auto',
        border: `1px solid ${token.colorBorderSecondary}`,
      }}>
        <h2 style={{ ...typography.detailTitle, margin: '0 0 16px', color: token.colorTextHeading }}>{title}</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {fields.map((f) => (
            <div key={f.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ ...typography.secondary, color: token.colorTextTertiary }}>{f.label}</span>
              {f.color
                ? <Tag {...comfortableTagProps} color={f.color}>{f.value}</Tag>
                : <span style={{ ...typography.body, color: token.colorText, fontFamily: f.mono ? fontFamilyMono : undefined, fontVariantNumeric: f.mono ? 'tabular-nums' : undefined }}>{f.value || '--'}</span>
              }
            </div>
          ))}
        </div>
        {description && (
          <div style={{ marginTop: 16, paddingTop: 16, borderTop: `1px solid ${token.colorBorderSecondary}` }}>
            <div style={{ ...typography.secondary, color: token.colorTextTertiary, marginBottom: 4 }}>Description</div>
            <div style={{ ...typography.body, color: token.colorText, whiteSpace: 'pre-wrap' }}>{description}</div>
          </div>
        )}
        {actions && actions.length > 0 && (
          <div style={{ marginTop: 16, paddingTop: 16, borderTop: `1px solid ${token.colorBorderSecondary}`, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {actions.map((a) => (
              <Button key={a.label} icon={a.icon} onClick={a.onClick} danger={a.danger} block>
                {a.label}
              </Button>
            ))}
          </div>
        )}
      </div>
      {/* Right Panel */}
      <div style={{
        flex: 1,
        background: token.colorBgContainer,
        borderRadius: 8,
        padding: 16,
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        border: `1px solid ${token.colorBorderSecondary}`,
      }}>
        {tabs}
      </div>
    </div>
  )
}
