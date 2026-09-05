import type {CSSProperties} from 'react'
import {paper, palette} from '../palette'

const markdownBackground = 'transparent'
export const markdownBorderColor = palette.border
export const markdownPreviewBackground = 'transparent'

export const markdownEditorThemeStyle = {
  '--md-editor-background-color': markdownBackground,
  '--md-editor-box-shadow-color': markdownBorderColor,
  '--color-canvas-default': markdownBackground,
  '--color-canvas-subtle': 'transparent',
  '--color-canvas-inset': markdownBackground,
  '--color-border-default': markdownBorderColor,
  '--color-border-muted': palette.borderSoft,
  '--color-fg-default': palette.text,
  '--color-fg-muted': palette.textSecondary,
  '--color-fg-subtle': palette.textTertiary,
  '--color-accent-fg': palette.primary,
  '--color-accent-muted': palette.primaryBorder,
  '--color-neutral-muted': paper(0.08),
} as CSSProperties
