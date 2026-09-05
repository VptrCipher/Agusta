import type {CSSProperties, ReactNode} from 'react'
import {ExclamationCircleOutlined} from '@ant-design/icons'
import {theme, Tooltip} from 'antd'
import type {EditableFieldState} from '../types/records'
import {DESCRIPTION_VALUE_HEIGHT} from './descriptionValueStyles'
import {fontFamilyMono, typography} from '../utils/typography'

interface DescriptionValueProps {
  children?: ReactNode
  height?: CSSProperties['height']
  minHeight?: CSSProperties['minHeight']
  mono?: boolean
  multiline?: boolean
}

interface EditableDescriptionValueProps extends DescriptionValueProps {
  state: EditableFieldState
  editor: ReactNode
}

export function DescriptionValue({
  children,
  height = DESCRIPTION_VALUE_HEIGHT,
  minHeight = DESCRIPTION_VALUE_HEIGHT,
  mono = false,
  multiline = false,
}: DescriptionValueProps) {
  const { token } = theme.useToken()

  return (
    <div
      style={{
        ...typography.body,
        minHeight,
        height,
        minWidth: 0,
        display: 'flex',
        alignItems: multiline ? 'flex-start' : 'center',
        color: token.colorText,
        fontFamily: mono ? fontFamilyMono : undefined,
        fontVariantNumeric: mono ? 'tabular-nums' : undefined,
        overflow: multiline ? 'visible' : 'hidden',
        overflowWrap: multiline ? 'anywhere' : undefined,
        whiteSpace: multiline ? 'pre-wrap' : 'nowrap',
        textOverflow: multiline ? undefined : 'ellipsis',
      }}
    >
      {children}
    </div>
  )
}

export function EditableDescriptionValue({
  state,
  editor,
  height = DESCRIPTION_VALUE_HEIGHT,
  minHeight = DESCRIPTION_VALUE_HEIGHT,
}: EditableDescriptionValueProps) {
  const { token } = theme.useToken()

  return (
    <div
      style={{
        position: 'relative',
        minHeight,
        height,
        width: '100%',
        minWidth: 0,
        boxSizing: 'border-box',
      }}
    >
      {editor}
      {state.dirty && !state.error && (
        <span
          style={{
            position: 'absolute',
            left: 0,
            top: 7,
            bottom: 7,
            width: 2,
            borderRadius: 1,
            background: token.colorPrimary,
            pointerEvents: 'none',
          }}
        />
      )}
      {state.error ? (
        <Tooltip title={state.error}>
          <ExclamationCircleOutlined
            style={{
              position: 'absolute',
              top: 8,
              right: 8,
              color: token.colorError,
              pointerEvents: 'auto',
            }}
          />
        </Tooltip>
      ) : null}
    </div>
  )
}
