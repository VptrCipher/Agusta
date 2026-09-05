import {Tag} from 'antd'
import {severityTagColors} from '../theme'
import {comfortableTagProps} from './tagStyles'

export function emptyValueNode() {
  return <span style={{ color: 'rgba(240, 238, 231, 0.35)' }}>—</span>
}

export function emptyValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return '—'
  return String(value)
}

export function formatDateTime(value: string | null | undefined) {
  if (!value) return emptyValueNode()
  return new Date(value).toLocaleString()
}

export function formatDurationSeconds(value: unknown) {
  if (value === null || value === undefined || value === '') return emptyValueNode()
  const seconds = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(seconds)) return emptyValueNode()

  const sign = seconds < 0 ? '-' : ''
  let remaining = Math.abs(Math.trunc(seconds))
  const days = Math.floor(remaining / 86400)
  remaining %= 86400
  const hours = Math.floor(remaining / 3600)
  remaining %= 3600
  const minutes = Math.floor(remaining / 60)
  const restSeconds = remaining % 60
  const parts = [
    days ? `${days}d` : '',
    hours ? `${hours}h` : '',
    minutes ? `${minutes}m` : '',
    restSeconds || (!days && !hours && !minutes) ? `${restSeconds}s` : '',
  ].filter(Boolean)

  return `${sign}${parts.slice(0, 2).join(' ')}`
}

export function choiceTag(value: string | null | undefined, color?: string) {
  const display = emptyValue(value)
  if (display === '—') return emptyValueNode()
  return <Tag {...comfortableTagProps} color={color}>{display}</Tag>
}

const alphaTagColors = [
  'magenta',
  'red',
  'volcano',
  'orange',
  'gold',
  'lime',
  'green',
  'cyan',
  'blue',
  'geekblue',
  'purple',
]

const caseCategoryOptions = [
  { value: 'DLP', label: 'DLP' },
  { value: 'Email', label: 'Email' },
  { value: 'OT', label: 'OT' },
  { value: 'Proxy', label: 'Proxy' },
  { value: 'UEBA', label: 'UEBA' },
  { value: 'ThreatIntelligence', label: 'TI' },
  { value: 'IAM', label: 'IAM' },
  { value: 'EDR', label: 'EDR' },
  { value: 'NDR', label: 'NDR' },
  { value: 'Cloud', label: 'Cloud' },
  { value: 'SIEM', label: 'SIEM' },
  { value: 'WAF', label: 'WAF' },
  { value: 'Other', label: 'Other' },
]

export function rotatingColorTag(value: string | null | undefined, options: { value: string; label?: string }[]) {
  const display = emptyValue(value)
  if (display === '—') return choiceTag(value)
  if (display === 'Unknown' || display === 'Other') return choiceTag(value, 'default')

  const index = options.findIndex((option) => option.value === display)
  if (index === -1) return choiceTag(value, 'default')

  const option = options[index]
  return choiceTag(option.label || option.value, alphaTagColors[index % alphaTagColors.length])
}

export function caseCategoryTag(value: string | null | undefined) {
  return rotatingColorTag(value, caseCategoryOptions)
}

export function severityTag(value: string | null | undefined) {
  return choiceTag(value, value ? severityTagColors[value] : undefined)
}

export function statusTag(value: string | null | undefined) {
  const colors: Record<string, string> = {
    New: 'cyan',
    'In Progress': 'processing',
    'On Hold': 'gold',
    Resolved: 'green',
    Closed: 'default',
  }
  return choiceTag(value, value ? colors[value] : undefined)
}

export function verdictTag(value: string | null | undefined) {
  const colors: Record<string, string> = {
    Unknown: 'default',
    'False Positive': 'green',
    'True Positive': 'red',
    Disregard: 'default',
    Suspicious: 'orange',
    Benign: 'green',
    Test: 'purple',
    'Insufficient Data': 'gold',
    'Security Risk': 'volcano',
    'Managed Externally': 'blue',
    Duplicate: 'cyan',
    Other: 'default',
  }
  return choiceTag(value, value ? colors[value] : undefined)
}

export function dispositionTag(value: string | null | undefined) {
  const colors: Record<string, string> = {
    Unknown: 'default',
    'False Positive': 'green',
    'True Positive': 'red',
    Disregard: 'default',
    Suspicious: 'orange',
    Benign: 'green',
    Test: 'purple',
    'Insufficient Data': 'gold',
    'Security Risk': 'volcano',
    'Managed Externally': 'blue',
    Duplicate: 'cyan',
    Other: 'default',
  }
  return choiceTag(value, value ? colors[value] : undefined)
}

export function alertDispositionTag(value: string | null | undefined) {
  const colors: Record<string, string> = {
    Unknown: 'default',
    Allowed: 'green',
    Blocked: 'red',
    Quarantined: 'orange',
    Isolated: 'volcano',
    Deleted: 'red',
    Dropped: 'orange',
    'Custom Action': 'purple',
    Approved: 'green',
    Restored: 'green',
    Exonerated: 'green',
    Corrected: 'green',
    'Partially Corrected': 'lime',
    Uncorrected: 'red',
    Delayed: 'gold',
    Detected: 'blue',
    'No Action': 'default',
    Logged: 'cyan',
    Tagged: 'geekblue',
    Alert: 'red',
    Count: 'blue',
    Reset: 'orange',
    Captcha: 'purple',
    Challenge: 'purple',
    'Access Revoked': 'red',
    Rejected: 'red',
    Unauthorized: 'volcano',
    Error: 'red',
    Other: 'default',
  }
  return choiceTag(value, value ? colors[value] : undefined)
}

export function alertActionTag(value: string | null | undefined) {
  const colors: Record<string, string> = {
    Unknown: 'default',
    Allowed: 'green',
    Denied: 'red',
    Observed: 'blue',
    Modified: 'orange',
    Other: 'default',
  }
  return choiceTag(value, value ? colors[value] : undefined)
}

export function alertAnalyticTypeTag(value: string | null | undefined) {
  const colors: Record<string, string> = {
    Unknown: 'default',
    Rule: 'blue',
    Behavioral: 'purple',
    Statistical: 'cyan',
    'Learning (ML/DL)': 'magenta',
    Fingerprinting: 'geekblue',
    Tagging: 'lime',
    'Keyword Match': 'gold',
    'Regular Expressions': 'volcano',
    'Exact Data Match': 'green',
    'Partial Data Match': 'orange',
    'Indexed Data Match': 'cyan',
    Other: 'default',
  }
  return choiceTag(value, value ? colors[value] : undefined)
}

export function productCategoryTag(value: string | null | undefined) {
  const colors: Record<string, string> = {
    DLP: 'magenta',
    Email: 'blue',
    OT: 'orange',
    Proxy: 'cyan',
    UEBA: 'purple',
    ThreatIntelligence: 'red',
    IAM: 'geekblue',
    EDR: 'volcano',
    NDR: 'lime',
    Cloud: 'blue',
    SIEM: 'gold',
    WAF: 'red',
    Other: 'default',
  }
  return choiceTag(value, value ? colors[value] : undefined)
}

export function knowledgeSourceTag(value: string | null | undefined) {
  const colors: Record<string, string> = {
    Manual: 'purple',
    Case: 'blue',
  }
  return choiceTag(value, value ? colors[value] : undefined)
}

export function artifactRoleTag(value: string | null | undefined) {
  const colors: Record<string, string> = {
    Unknown: 'default',
    Target: 'red',
    Actor: 'purple',
    Affected: 'orange',
    Related: 'blue',
    Other: 'default',
  }
  return choiceTag(value, value ? colors[value] : undefined)
}

export function enrichmentTypeTag(value: string | null | undefined) {
  const colors: Record<string, string> = {
    Unknown: 'default',
    Other: 'default',
    'Threat Intelligence': 'red',
    Reputation: 'orange',
    'Geo Location': 'cyan',
    WHOIS: 'geekblue',
    DNS: 'blue',
    'Passive DNS': 'cyan',
    Certificate: 'lime',
    Sandbox: 'purple',
    'Malware Analysis': 'magenta',
    Vulnerability: 'volcano',
    Exposure: 'orange',
    Asset: 'green',
    CMDB: 'green',
    Identity: 'purple',
    Authentication: 'geekblue',
    Authorization: 'blue',
    Behavior: 'gold',
    Detection: 'red',
    Correlation: 'cyan',
    History: 'default',
    Remediation: 'green',
    Observation: 'lime',
    'External Ticket': 'gold',
  }
  return choiceTag(value, value ? colors[value] : undefined)
}

export function jsonPreview(value: unknown): string {
  if (!value) return '—'
  return JSON.stringify(value, null, 2)
}
