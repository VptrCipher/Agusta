import {Button} from 'antd'
import {DownOutlined} from '@ant-design/icons'
import {typography} from '../utils/typography'

interface FeedLoadMoreProps {
  label?: string
  loading?: boolean
  onClick: () => void
}

export default function FeedLoadMore({label = 'Load more', loading = false, onClick}: FeedLoadMoreProps) {
  return (
    <div style={{display: 'flex', alignItems: 'center', gap: 10, padding: '10px 0 2px'}}>
      <span style={{height: 1, flex: 1, background: 'rgba(240, 238, 231, 0.08)'}}/>
      <Button
        type="text"
        size="small"
        icon={<DownOutlined/>}
        loading={loading}
        onClick={onClick}
        style={{
          ...typography.compact,
          height: 28,
          borderRadius: 999,
          paddingInline: 12,
          color: 'rgba(240, 238, 231, 0.58)',
          background: 'rgba(240, 238, 231, 0.03)',
          border: '1px solid rgba(240, 238, 231, 0.08)',
        }}
      >
        {label}
      </Button>
      <span style={{height: 1, flex: 1, background: 'rgba(240, 238, 231, 0.08)'}}/>
    </div>
  )
}
