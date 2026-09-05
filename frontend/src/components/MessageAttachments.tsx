import {useState} from 'react'
import {CloseOutlined, FileImageOutlined, FileOutlined, FileTextOutlined} from '@ant-design/icons'
import {Button, Image, Space, Tooltip, Typography} from 'antd'
import type {Attachment} from '../api/attachments'
import {typography} from '../utils/typography'

interface MessageAttachmentsProps {
  attachments: Attachment[]
  removable?: boolean
  compactCards?: boolean
  onRemove?: (id: number) => void
}

function isImageAttachment(attachment: Attachment) {
  return /\.(apng|avif|gif|jpe?g|png|webp|bmp|svg)$/i.test(attachment.filename)
}

function isTextAttachment(attachment: Attachment) {
  return /\.(csv|json|log|md|txt|xml|yaml|yml)$/i.test(attachment.filename)
}

function fileIcon(attachment: Attachment) {
  if (isImageAttachment(attachment)) return <FileImageOutlined style={{ color: '#e0a88f', fontSize: 20 }} />
  if (isTextAttachment(attachment)) return <FileTextOutlined style={{ color: '#a3bf88', fontSize: 20 }} />
  return <FileOutlined style={{ color: 'rgba(240, 238, 231, 0.65)', fontSize: 20 }} />
}

function formatSize(size: number) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

function AttachmentCard({
  attachment,
  removable,
  onRemove,
  onPreview,
}: {
  attachment: Attachment
  removable: boolean
  onRemove?: (id: number) => void
  onPreview?: (attachment: Attachment) => void
}) {
  const image = isImageAttachment(attachment)
  return (
    <div
      className="message-attachment-card"
      onClick={() => {
        if (image) onPreview?.(attachment)
      }}
      style={{
        position: 'relative',
        width: 156,
        minWidth: 0,
        padding: '8px 24px 8px 8px',
        border: '1px solid #35322e',
        borderRadius: 8,
        background: '#1b1a19',
        display: 'flex',
        gap: 8,
        alignItems: 'center',
        cursor: image ? 'pointer' : 'default',
      }}
    >
      <span style={{ flexShrink: 0 }}>{fileIcon(attachment)}</span>
      <div style={{ minWidth: 0, flex: 1, display: 'grid', gap: 2 }}>
        <Typography.Text ellipsis style={typography.compact}>{attachment.filename}</Typography.Text>
        <Typography.Text type="secondary" style={typography.compact}>{formatSize(attachment.size)}</Typography.Text>
      </div>
      {removable && (
        <Tooltip title="Remove">
          <Button
            className="message-attachment-card-remove"
            type="text"
            size="small"
            icon={<CloseOutlined />}
            style={{ position: 'absolute', top: 2, right: 2, width: 18, height: 18, minWidth: 18, padding: 0 }}
            onClick={(event) => {
              event.stopPropagation()
              onRemove?.(attachment.id)
            }}
          />
        </Tooltip>
      )}
    </div>
  )
}

export default function MessageAttachments({ attachments, removable = false, compactCards = false, onRemove }: MessageAttachmentsProps) {
  const [previewAttachment, setPreviewAttachment] = useState<Attachment | null>(null)
  if (!attachments.length) return null

  if (compactCards) {
    return (
      <>
        <div style={{ display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 2 }}>
          {attachments.map((attachment) => (
            <AttachmentCard
              key={attachment.id}
              attachment={attachment}
              removable={removable}
              onRemove={onRemove}
              onPreview={setPreviewAttachment}
            />
          ))}
        </div>
        {previewAttachment && (
          <Image
            src={previewAttachment.file}
            alt={previewAttachment.filename}
            style={{ display: 'none' }}
            preview={{
              visible: Boolean(previewAttachment),
              onVisibleChange: (visible) => {
                if (!visible) setPreviewAttachment(null)
              },
            }}
          />
        )}
      </>
    )
  }

  const images = attachments.filter(isImageAttachment)
  const files = attachments.filter((attachment) => !isImageAttachment(attachment))

  return (
    <div style={{ display: 'grid', gap: 8 }}>
      {images.length > 0 && (
        <Image.PreviewGroup>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {images.map((attachment) => (
              <div key={attachment.id} style={{ position: 'relative' }}>
                <Image
                  src={attachment.file}
                  width={72}
                  height={72}
                  style={{ objectFit: 'cover', borderRadius: 6, border: '1px solid #35322e' }}
                  alt={attachment.filename}
                />
                {removable && (
                  <Button
                    size="small"
                    danger
                    type="primary"
                    style={{ position: 'absolute', top: -8, right: -8, width: 20, height: 20, minWidth: 20, padding: 0 }}
                    onClick={() => onRemove?.(attachment.id)}
                  >
                    x
                  </Button>
                )}
              </div>
            ))}
          </div>
        </Image.PreviewGroup>
      )}
      {files.map((attachment) => (
        <Space key={attachment.id} size={6} wrap>
          <FileOutlined />
          <Typography.Link href={attachment.file} target="_blank" rel="noreferrer">
            {attachment.filename}
          </Typography.Link>
          <Typography.Text type="secondary">({formatSize(attachment.size)})</Typography.Text>
          {removable && (
            <Button type="link" size="small" danger onClick={() => onRemove?.(attachment.id)}>
              Remove
            </Button>
          )}
        </Space>
      ))}
    </div>
  )
}
