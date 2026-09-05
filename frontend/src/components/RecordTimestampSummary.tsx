import {theme, Tooltip} from 'antd'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import {formatDateTime} from '../utils/recordDisplay'
import {tabularNumbersStyle, typography} from '../utils/typography'

dayjs.extend(relativeTime)

interface RecordTimestampSummaryProps {
  record: Record<string, unknown>
}

const timestampFields = [
  { key: 'created_at', label: 'Created' },
  { key: 'updated_at', label: 'Updated' },
] as const

function timestampItem(record: Record<string, unknown>, key: string, label: string) {
  const rawValue = record[key]
  if (typeof rawValue !== 'string' || !rawValue) return null

  const timestamp = dayjs(rawValue)
  if (!timestamp.isValid()) return null

  return {
    key,
    label,
    relative: timestamp.fromNow(),
    absolute: formatDateTime(rawValue),
  }
}

export default function RecordTimestampSummary({ record }: RecordTimestampSummaryProps) {
  const { token } = theme.useToken()
  const items = timestampFields
    .map(({ key, label }) => timestampItem(record, key, label))
    .filter((item): item is NonNullable<typeof item> => item !== null)

  if (!items.length) return null

  return (
    <div style={{ ...typography.compact, ...tabularNumbersStyle, display: 'flex', alignItems: 'center', gap: 8, color: token.colorTextTertiary }}>
      {items.map((item, index) => (
        <span key={item.key} style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
          {index > 0 && <span aria-hidden="true">·</span>}
          <Tooltip title={item.absolute}>
            <span>{item.label} {item.relative}</span>
          </Tooltip>
        </span>
      ))}
    </div>
  )
}
