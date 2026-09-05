import {RollbackOutlined, SaveOutlined} from '@ant-design/icons'
import {Button} from 'antd'

interface DetailDraftActionBarProps {
  dirtyCount: number
  saving: boolean
  onCancel: () => void
  onSave: () => void
}

export default function DetailDraftActionBar({ dirtyCount, saving, onCancel, onSave }: DetailDraftActionBarProps) {
  return (
    <div
      style={{
        position: 'absolute',
        left: 16,
        right: 16,
        bottom: 16,
        zIndex: 5,
        display: 'flex',
        justifyContent: 'center',
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          padding: '10px 12px',
          border: '1px solid #35322e',
          borderRadius: 10,
          background: 'rgba(27, 26, 25, 0.96)',
          boxShadow: '0 12px 32px rgba(0,0,0,0.42)',
          pointerEvents: 'auto',
        }}
      >
        <span style={{ color: 'rgba(240, 238, 231, 0.72)' }}>
          {dirtyCount} field{dirtyCount === 1 ? '' : 's'} changed
        </span>
        <Button icon={<RollbackOutlined />} disabled={saving} onClick={onCancel}>
          Cancel
        </Button>
        <Button type="primary" icon={<SaveOutlined />} loading={saving} onClick={onSave}>
          Save
        </Button>
      </div>
    </div>
  )
}
