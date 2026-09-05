/**
 * AGUSTA design tokens.
 *
 * A warm, editorial palette: terracotta accent on low-chroma charcoal surfaces.
 * Neutral overlays are warm (paper-toned) rather than pure white so nothing in
 * the UI reads as cold blue-grey.
 *
 * Keep this file the single source of truth. CSS mirrors it via the custom
 * properties declared on `:root` in `index.css`.
 */

/** Paper-toned white used for every translucent light overlay. */
const PAPER = '240, 238, 231'
/** Terracotta accent channel, for translucent accent washes. */
const ACCENT = '217, 119, 87'

/** `rgba()` over the warm paper white. Use instead of `rgba(255,255,255,a)`. */
export const paper = (alpha: number) => `rgba(${PAPER}, ${alpha})`
/** `rgba()` over the terracotta accent. */
export const accent = (alpha: number) => `rgba(${ACCENT}, ${alpha})`

export const palette = {
  /** App canvas, behind everything. */
  bgBase: '#1B1A19',
  /** Navigation rail and other structural chrome. */
  bgLayout: '#201F1D',
  /** Cards, headers, table surfaces. */
  bgContainer: '#262422',
  /** Dropdowns, popovers, modals — one step closer to the viewer. */
  bgElevated: '#2E2C29',
  /** Deepest recess: code wells, side panels, empty states. */
  bgWell: '#161514',
  /** Subtle raised fill for chips and inset rows. */
  bgSubtle: paper(0.04),
  /** Scrim behind modals. */
  bgMask: 'rgba(12, 11, 10, 0.72)',

  border: '#35322E',
  borderSoft: '#2B2825',
  borderStrong: '#433F3A',

  text: '#F0EEE7',
  textSecondary: '#B9B4AA',
  textTertiary: '#8C877D',
  textQuaternary: '#6B665E',

  primary: '#D97757',
  primaryHover: '#E28D70',
  primaryActive: '#C2603F',
  primaryBg: accent(0.12),
  primaryBgHover: accent(0.18),
  primaryBorder: accent(0.32),

  success: '#85A96F',
  warning: '#D9A344',
  error: '#C75B52',
  info: '#8FA8BF',

  /** Warm gold used sparingly for premium accents and dividers. */
  brass: '#C8A35C',
} as const

/** Severity scale, tuned to the warm palette while staying easy to tell apart. */
export const severityColors: Record<string, string> = {
  Critical: '#B5342B',
  High: '#D97757',
  Medium: '#D9A344',
  Low: '#85A96F',
  Info: '#8FA8BF',
  Informational: '#8FA8BF',
}

/** Ant Design preset tag colours matched to the severity scale above. */
export const severityTagColors: Record<string, string> = {
  Critical: 'red',
  High: 'volcano',
  Medium: 'gold',
  Low: 'green',
  Info: 'geekblue',
  Informational: 'geekblue',
}

export const radius = {
  sm: 6,
  md: 10,
  lg: 14,
  xl: 20,
} as const

export const elevation = {
  /** Resting card lift. */
  card: '0 1px 2px rgba(0, 0, 0, 0.24), 0 8px 24px rgba(0, 0, 0, 0.18)',
  /** Floating surfaces: dropdowns, popovers. */
  raised: '0 12px 32px rgba(0, 0, 0, 0.34)',
  /** Modals and drawers. */
  overlay: '0 24px 64px rgba(0, 0, 0, 0.48)',
  /** Focus ring in the accent colour. */
  focus: `0 0 0 3px ${accent(0.22)}`,
} as const
