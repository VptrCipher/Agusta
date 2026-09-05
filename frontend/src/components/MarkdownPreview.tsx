import type {CSSProperties} from 'react'
import MDEditor from '@uiw/react-md-editor'
import {markdownBorderColor, markdownEditorThemeStyle, markdownPreviewBackground} from './MarkdownEditorTheme'
import {disallowedMarkdownElements} from './markdownSecurity'

interface MarkdownPreviewProps {
  source: string
  height?: CSSProperties['height']
  minHeight?: CSSProperties['minHeight']
}

export default function MarkdownPreview({
  source,
  height,
  minHeight = 96,
}: MarkdownPreviewProps) {
  const containerStyle: CSSProperties = {
    width: '100%',
    minWidth: 0,
    overflow: 'auto',
    border: `1px solid ${markdownBorderColor}`,
    borderRadius: 6,
    boxSizing: 'border-box',
    background: markdownPreviewBackground,
  }

  if (height !== undefined) {
    containerStyle.height = height
  }

  return (
    <div className="agusta-markdown-preview" data-color-mode="dark" style={containerStyle}>
      <MDEditor.Markdown
        source={source}
        disallowedElements={disallowedMarkdownElements}
        style={{
          minHeight,
          padding: 12,
          boxSizing: 'border-box',
          background: markdownPreviewBackground,
          ...markdownEditorThemeStyle,
        }}
      />
    </div>
  )
}
