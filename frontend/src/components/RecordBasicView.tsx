import {Button, theme} from 'antd'
import type {ResourceConfig} from '../types/records'
import DetailSectionDivider from './DetailSectionDivider'
import {fontFamilyMono, typography} from '../utils/typography'

interface RecordBasicViewProps {
  config: ResourceConfig
  record: Record<string, unknown>
  onOpenResource?: (resourceKey: string, rowId: string | number) => void
}

export default function RecordBasicView({ config, record, onOpenResource }: RecordBasicViewProps) {
  const { token } = theme.useToken()

  return (
    <div style={{ padding: '20px 20px 16px', overflow: 'auto', height: '100%', boxSizing: 'border-box' }}>
      <div style={{ ...typography.secondary, color: token.colorTextTertiary, marginBottom: 8 }}>
        {config.label.slice(0, -1) || config.label}
      </div>
      <h1 style={{ ...typography.detailTitle, color: token.colorTextHeading, margin: '0 0 24px' }}>
        {String(record.title || record.name || record.username || record.value || record.id || '—')}
      </h1>
      {config.basicSections.map((section) => (
        <section key={section.key} style={{ marginTop: 16 }}>
          <DetailSectionDivider title={section.title} />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(220px, 1fr))', gap: '16px 28px' }}>
            {section.fields.map((field) => {
              const openResource = field.openResource
              const linkedResourceKey = typeof openResource?.resourceKey === 'function'
                ? openResource.resourceKey(record)
                : openResource?.resourceKey
              const linkedRowId = openResource?.rowId(record)
              const canOpenResource = Boolean(linkedResourceKey && onOpenResource && linkedRowId !== null && linkedRowId !== undefined)

              return (
                <div key={`${section.key}-${field.label}`}>
                  <div style={{ ...typography.fieldLabel, color: token.colorTextSecondary, marginBottom: 8 }}>
                    {field.label}
                  </div>
                  <div
                    style={{
                      ...typography.body,
                      color: token.colorText,
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      fontFamily: field.mono ? fontFamilyMono : undefined,
                      fontVariantNumeric: field.mono ? 'tabular-nums' : undefined,
                    }}
                  >
                    {canOpenResource && linkedResourceKey && linkedRowId !== null && linkedRowId !== undefined ? (
                      <Button
                        type="link"
                        size="small"
                        style={{ padding: 0, height: 'auto', fontFamily: field.mono ? fontFamilyMono : undefined }}
                        onClick={() => onOpenResource?.(linkedResourceKey, linkedRowId)}
                      >
                        {field.value(record)}
                      </Button>
                    ) : field.value(record)}
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      ))}
    </div>
  )
}
