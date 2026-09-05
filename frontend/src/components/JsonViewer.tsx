import JsonView from '@uiw/react-json-view'
import {darkTheme} from '@uiw/react-json-view/dark'
import {typography} from '../utils/typography'
import {emptyValueNode} from '../utils/recordDisplay'

interface JsonViewerProps {
  value: unknown
  maxHeight?: number | 'none'
}

function parseJson(value: unknown) {
  if (typeof value !== 'string') return value
  try {
    return JSON.parse(value)
  } catch {
    return value
  }
}

export default function JsonViewer({ value, maxHeight = 360 }: JsonViewerProps) {
  const parsedValue = parseJson(value)

  if (!parsedValue) {
    return emptyValueNode()
  }

  return (
    <JsonView
      value={parsedValue}
      style={{ ...darkTheme, background: 'transparent', fontSize: typography.code.fontSize, maxHeight, overflow: 'auto' }}
      collapsed={2}
      displayDataTypes={false}
      enableClipboard={false}
    />
  )
}
