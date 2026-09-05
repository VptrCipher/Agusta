import type {CSSProperties, ReactNode} from 'react'
import {Empty} from 'antd'
import {
    AimOutlined,
    BranchesOutlined,
    CheckCircleOutlined,
    ClockCircleOutlined,
    CloudServerOutlined,
    FileTextOutlined,
    PlayCircleOutlined,
    QuestionCircleOutlined,
    SearchOutlined,
    ToolOutlined,
} from '@ant-design/icons'
import {fontFamilyMono} from '../utils/typography'

type RecordMap = Record<string, unknown>

interface InvestigationReportViewProps {
  value: unknown
}

interface ParsedReport {
  raw: RecordMap
  report: RecordMap
}

const c = {
  bg: '#1b1a19',
  panel: '#262422',
  item: '#201f1d',
  chip: '#2b2825',
  well: '#161514',
  border: '#35322e',
  borderSoft: '#2b2825',
  text: '#d6d2c9',
  textStrong: '#e8e4db',
  textMuted: '#8c877d',
  gray: '#a8a29a',
  red: '#d97c72',
  orange: '#dfa05e',
  blue: '#93aec6',
  cyan: '#7fb8ae',
  indigo: '#a6a3d4',
  purple: '#c4a2d9',
  green: '#85a96f',
}

const reportRootStyle: CSSProperties = {
  width: '100%',
  height: '100%',
  overflowY: 'auto',
  background: c.bg,
  color: c.text,
  fontFamily: 'inherit',
  boxSizing: 'border-box',
  padding: 20,
}

const sectionStyle: CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: 16,
  flexShrink: 0,
}

function isObjectRecord(value: unknown): value is RecordMap {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function stringValue(record: RecordMap, key: string, fallback = '—') {
  const value = record[key]
  if (value === null || value === undefined || value === '') return fallback
  return String(value)
}

function recordArray(value: unknown): RecordMap[] {
  return Array.isArray(value) ? value.filter(isObjectRecord) : []
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => String(item)).filter(Boolean) : []
}

function parseReport(value: unknown): { status: 'empty' } | { status: 'report'; data: ParsedReport } | { status: 'fallback'; raw: unknown } {
  if (value === null || value === undefined || value === '') return { status: 'empty' }

  let raw = value
  if (typeof value === 'string') {
    if (!value.trim()) return { status: 'empty' }
    try {
      raw = JSON.parse(value)
    } catch {
      return { status: 'fallback', raw: value }
    }
  }

  if (!isObjectRecord(raw) || !isObjectRecord(raw.report)) return { status: 'fallback', raw }
  return { status: 'report', data: { raw, report: raw.report } }
}

function rawPreview(value: unknown) {
  if (typeof value === 'string') return value
  return JSON.stringify(value, null, 2)
}

function formatLocalTime(value: unknown) {
  if (!value) return 'N/A'
  const date = new Date(String(value))
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleString()
}

function translucent(hex: string, alpha: number) {
  const value = hex.replace('#', '')
  const red = Number.parseInt(value.slice(0, 2), 16)
  const green = Number.parseInt(value.slice(2, 4), 16)
  const blue = Number.parseInt(value.slice(4, 6), 16)
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`
}

function severityColor(value: unknown) {
  const level = String(value || '')
  if (level === 'High' || level === 'Critical' || level === 'True Positive') return c.red
  if (level === 'Medium' || level === 'Suspicious') return c.orange
  if (level === 'Low' || level === 'False Positive' || level === 'Benign') return c.blue
  return c.gray
}

function verdictColor(value: unknown) {
  const verdict = String(value || '')
  if (verdict === 'True Positive') return c.red
  if (verdict === 'Suspicious') return c.orange
  if (verdict === 'False Positive') return c.green
  return c.gray
}

function badgeStyle(color: string): CSSProperties {
  return {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 46,
    padding: '6px 14px',
    borderRadius: 8,
    border: `1px solid ${translucent(color, 0.3)}`,
    background: translucent(color, 0.1),
  }
}

function smallTypeStyle(color = c.textMuted): CSSProperties {
  return {
    fontSize: 11,
    lineHeight: '16px',
    fontWeight: 700,
    color,
  }
}

function Icon({ children, color = c.gray, size = 18 }: { children: ReactNode; color?: string; size?: number }) {
  return <span style={{ display: 'inline-flex', color, fontSize: size, lineHeight: 1 }}>{children}</span>
}

function MetaLine({ raw }: { raw: RecordMap }) {
  const startedAt = raw.analysis_last_started_at || raw.generated_at
  const completedAt = raw.analysis_last_completed_at || raw.generated_at
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '8px 24px', color: c.textMuted, fontSize: 12, lineHeight: '18px', fontFamily: fontFamilyMono, flexShrink: 0 }}>
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
        <PlayCircleOutlined style={{ fontSize: 14 }} />
        Started: {formatLocalTime(startedAt)}
      </span>
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
        <CheckCircleOutlined style={{ fontSize: 14 }} />
        Completed: {formatLocalTime(completedAt)}
      </span>
      {raw.trigger ? <span>Trigger: {String(raw.trigger)}</span> : null}
      {raw.profile_version ? <span>Profile: {String(raw.profile_version)}</span> : null}
    </div>
  )
}

function RiskBadges({ report }: { report: RecordMap }) {
  const items = [
    { label: 'Verdict', value: stringValue(report, 'verdict'), color: verdictColor(report.verdict) },
    { label: 'Severity', value: stringValue(report, 'severity'), color: severityColor(report.severity) },
    { label: 'Impact', value: stringValue(report, 'impact'), color: severityColor(report.impact) },
    { label: 'Priority', value: stringValue(report, 'priority'), color: severityColor(report.priority) },
    { label: 'Confidence', value: stringValue(report, 'confidence'), color: severityColor(report.confidence) },
  ]

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12, flexShrink: 0 }}>
      {items.map((item) => (
        <div key={item.label} style={badgeStyle(item.color)}>
          <span style={{ fontSize: 10, lineHeight: '12px', textTransform: 'uppercase', letterSpacing: 0.8, color: translucent(item.color, 0.8), marginBottom: 1 }}>
            {item.label}
          </span>
          <span style={{ fontSize: 16, lineHeight: '20px', fontWeight: 600, color: item.color, textAlign: 'center' }}>
            {item.value}
          </span>
        </div>
      ))}
    </div>
  )
}

function SectionTitle({ icon, title, color }: { icon: ReactNode; title: string; color: string }) {
  return (
    <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, margin: 0, paddingBottom: 8, borderBottom: `1px solid ${c.border}`, color: c.textStrong, fontSize: 14, lineHeight: '22px', fontWeight: 700 }}>
      <Icon color={color}>{icon}</Icon>
      {title}
    </h3>
  )
}

function EmptySection() {
  return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={<span style={{ color: c.textMuted }}>No data</span>} />
}

function Chip({ children, color = c.gray, withBorder = false }: { children: ReactNode; color?: string; withBorder?: boolean }) {
  return (
    <span style={{ display: 'inline-flex', width: 'max-content', maxWidth: '100%', padding: withBorder ? '4px 8px' : '2px 8px', borderRadius: 4, border: withBorder ? `1px solid ${translucent(color, 0.25)}` : 0, background: withBorder ? c.chip : translucent(color, 0.1), color, fontSize: 11, lineHeight: '16px', fontWeight: 700, overflowWrap: 'anywhere' }}>
      {children}
    </span>
  )
}

function MonoEvidence({ children, emphasized = false }: { children: ReactNode; emphasized?: boolean }) {
  return (
    <span style={{ display: 'inline-block', maxWidth: '100%', padding: '2px 6px', borderRadius: 4,     border: `1px solid ${c.borderSoft}`, background: c.well, color: emphasized ? c.red : c.gray, fontFamily: fontFamilyMono, fontSize: emphasized ? 14 : 12, lineHeight: emphasized ? '20px' : '18px', fontWeight: emphasized ? 700 : 400, overflowWrap: 'anywhere' }}>
      {children}
    </span>
  )
}

function DigestSection({ report }: { report: RecordMap }) {
  return (
    <div style={{ background: c.panel, padding: 20, borderRadius: 8, border: `1px solid ${c.border}`, flexShrink: 0 }}>
      <SectionTitle icon={<FileTextOutlined />} title="Incident Digest" color={c.gray} />
      <p style={{ margin: '14px 0 0', color: c.text, fontSize: 15, lineHeight: '26px', textAlign: 'justify', whiteSpace: 'pre-wrap' }}>
        {stringValue(report, 'digest')}
      </p>
    </div>
  )
}

function AffectedAssetsSection({ report }: { report: RecordMap }) {
  const assets = recordArray(report.affected_assets)
  return (
    <div style={sectionStyle}>
      <SectionTitle icon={<CloudServerOutlined />} title="Affected Assets" color={c.blue} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {!assets.length ? <EmptySection /> : assets.map((asset, index) => (
          <div key={`${stringValue(asset, 'asset_type')}:${stringValue(asset, 'asset_value')}:${index}`} style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 8, padding: 12, background: c.item, borderRadius: 6, border: `1px solid ${c.border}` }}>
            <Chip color={c.gray} withBorder>{stringValue(asset, 'asset_type')}</Chip>
            <span style={{ color: c.text, fontFamily: fontFamilyMono, fontSize: 12, lineHeight: '18px', overflowWrap: 'anywhere', textAlign: 'right' }}>
              {stringValue(asset, 'asset_value')}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function IocSection({ report }: { report: RecordMap }) {
  const iocs = recordArray(report.ioc_indicators)
  return (
    <div style={sectionStyle}>
      <SectionTitle icon={<AimOutlined />} title="IOC Indicators" color={c.red} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {!iocs.length ? <EmptySection /> : iocs.map((ioc, index) => (
          <div key={`${stringValue(ioc, 'value')}:${index}`} style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: 12, background: 'rgba(199, 91, 82, 0.05)', borderRadius: 6, border: '1px solid rgba(199, 91, 82, 0.20)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <Chip color={c.red}>{stringValue(ioc, 'indicator_type')}</Chip>
              <MonoEvidence emphasized>{stringValue(ioc, 'value')}</MonoEvidence>
            </div>
            <span style={{ color: 'rgba(221, 154, 146, 0.72)', fontSize: 12, lineHeight: '18px' }}>
              {stringValue(ioc, 'context')}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function EvidenceFindingsSection({ report }: { report: RecordMap }) {
  const findings = recordArray(report.evidence_findings)
  return (
    <div style={{ ...sectionStyle, paddingTop: 8 }}>
      <SectionTitle icon={<SearchOutlined />} title="Evidence Findings" color={c.cyan} />
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr)', gap: 16 }}>
        {!findings.length ? <EmptySection /> : findings.map((finding, index) => (
          <div key={`${stringValue(finding, 'title')}:${index}`} style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: 16, background: c.item, borderRadius: 8, border: `1px solid ${c.border}` }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8, paddingBottom: 8, borderBottom: `1px solid ${c.border}` }}>
              <span style={{ color: c.textStrong, fontSize: 14, lineHeight: '20px', fontWeight: 700 }}>{stringValue(finding, 'title')}</span>
              <Chip color={c.cyan} withBorder>{stringValue(finding, 'finding_type')}</Chip>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 12, lineHeight: '18px' }}>
              <div style={{ display: 'flex', gap: 8 }}>
                <span style={{ ...smallTypeStyle(), flexShrink: 0, width: 82 }}>Subject:</span>
                <span style={{ color: c.text }}>{stringValue(finding, 'subject')}</span>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <span style={{ ...smallTypeStyle(), flexShrink: 0, width: 82 }}>Evidence:</span>
                <MonoEvidence>{stringValue(finding, 'evidence')}</MonoEvidence>
              </div>
              <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                <span style={{ ...smallTypeStyle(), flexShrink: 0, width: 82 }}>Conclusion:</span>
                <span style={{ color: c.text, fontWeight: 500, lineHeight: '20px' }}>{stringValue(finding, 'conclusion')}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function AttackChainSection({ report }: { report: RecordMap }) {
  const chain = recordArray(report.attack_chain)
  return (
    <div style={{ ...sectionStyle, paddingTop: 8 }}>
      <SectionTitle icon={<BranchesOutlined />} title="Attack Chain" color={c.indigo} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {!chain.length ? <EmptySection /> : chain.map((step, index) => (
          <div key={`${stringValue(step, 'attack_stage')}:${index}`} style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: 16, background: 'rgba(166, 163, 212, 0.05)', borderRadius: 8, border: '1px solid rgba(166, 163, 212, 0.20)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <Chip color={c.indigo}>Stage</Chip>
              <span style={{ color: '#bdb9e0', fontSize: 14, lineHeight: '20px', fontWeight: 700 }}>{stringValue(step, 'attack_stage')}</span>
            </div>
            <p style={{ margin: 0, color: c.gray, fontSize: 14, lineHeight: '22px', textAlign: 'justify' }}>{stringValue(step, 'description')}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

function TimelineSection({ report }: { report: RecordMap }) {
  const events = recordArray(report.attack_timeline)
  return (
    <div style={{ ...sectionStyle, paddingTop: 8 }}>
      <SectionTitle icon={<ClockCircleOutlined />} title="Timeline" color={c.purple} />
      {!events.length ? <EmptySection /> : (
        <div style={{ position: 'relative', marginLeft: 12, padding: '8px 0 8px 20px', borderLeft: '2px solid rgba(196, 162, 217, 0.30)', display: 'flex', flexDirection: 'column', gap: 32 }}>
          {events.map((event, index) => (
            <div key={`${stringValue(event, 'timestamp')}:${index}`} style={{ position: 'relative' }}>
              <span style={{ position: 'absolute', left: -27, top: 2, width: 12, height: 12, borderRadius: '50%', background: c.purple, boxShadow: `0 0 0 4px ${c.bg}` }} />
              <div style={{ color: c.purple, fontSize: 11, lineHeight: '16px', fontWeight: 700, fontFamily: fontFamilyMono, marginBottom: 4 }}>{formatLocalTime(event.timestamp)}</div>
              <div style={{ color: c.textStrong, fontSize: 14, lineHeight: '22px', fontWeight: 500, marginBottom: 8 }}>{stringValue(event, 'attack_behavior')}</div>
              <div style={{ color: c.gray, background: c.item, padding: 10, borderRadius: 6, border: `1px solid ${c.border}`, fontFamily: fontFamilyMono, fontSize: 11, lineHeight: '16px', overflowWrap: 'anywhere' }}>{stringValue(event, 'evidence_field')}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function UnknownsSection({ report }: { report: RecordMap }) {
  const unknowns = stringArray(report.unknowns)
  return (
    <div style={{ ...sectionStyle, paddingTop: 8 }}>
      <SectionTitle icon={<QuestionCircleOutlined />} title="Unknowns" color={c.orange} />
      {!unknowns.length ? <EmptySection /> : (
        <div style={{ background: 'rgba(217, 163, 68, 0.05)', padding: 16, borderRadius: 8, border: '1px solid rgba(217, 163, 68, 0.20)' }}>
          <ul style={{ margin: 0, paddingInlineStart: 18, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {unknowns.map((item, index) => (
              <li key={`${item}:${index}`} style={{ color: 'rgba(224, 186, 138, 0.90)', fontSize: 14, lineHeight: '22px' }}>{item}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function RemediationSection({ report }: { report: RecordMap }) {
  const remediations = recordArray(report.remediations)
  return (
    <div style={{ ...sectionStyle, paddingTop: 8 }}>
      <SectionTitle icon={<ToolOutlined />} title="Remediation Recommendations" color={c.green} />
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr)', gap: 12 }}>
        {!remediations.length ? <EmptySection /> : remediations.map((rec, index) => (
          <div key={`${stringValue(rec, 'action_type')}:${index}`} style={{ display: 'flex', gap: 16, padding: 16, background: 'rgba(133, 169, 111, 0.05)', borderRadius: 8, border: '1px solid rgba(133, 169, 111, 0.20)' }}>
            <Icon color={c.green} size={20}><CheckCircleOutlined /></Icon>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, width: '100%' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
                <span style={{ color: '#9cc287', fontSize: 14, lineHeight: '20px', fontWeight: 700 }}>{stringValue(rec, 'action_type')}</span>
                <span style={{ ...smallTypeStyle(severityColor(rec.priority)), padding: '2px 8px', borderRadius: 4, border: `1px solid ${translucent(severityColor(rec.priority), 0.35)}`, background: translucent(severityColor(rec.priority), 0.1), textTransform: 'uppercase', letterSpacing: 0.6 }}>
                  {stringValue(rec, 'priority')}
                </span>
              </div>
              <span style={{ color: 'rgba(169, 196, 141, 0.80)', fontSize: 12, lineHeight: '18px', textAlign: 'justify' }}>{stringValue(rec, 'description')}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function RawReportFallback({ raw }: { raw: unknown }) {
  return <pre style={{ margin: 0, padding: 16, whiteSpace: 'pre-wrap', overflow: 'auto', height: '100%' }}>{rawPreview(raw)}</pre>
}

export default function InvestigationReportView({ value }: InvestigationReportViewProps) {
  const parsed = parseReport(value)

  if (parsed.status === 'empty') return <div style={reportRootStyle}><div style={{ color: c.textMuted, textAlign: 'center', fontFamily: fontFamilyMono }}>No data</div></div>
  if (parsed.status === 'fallback') return <RawReportFallback raw={parsed.raw} />

  const { raw, report } = parsed.data
  return (
    <div style={reportRootStyle}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 24, width: '100%' }}>
        <MetaLine raw={raw} />
        <RiskBadges report={report} />
        <DigestSection report={report} />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 24 }}>
          <AffectedAssetsSection report={report} />
          <IocSection report={report} />
        </div>
        <EvidenceFindingsSection report={report} />
        <AttackChainSection report={report} />
        <TimelineSection report={report} />
        <UnknownsSection report={report} />
        <RemediationSection report={report} />
      </div>
    </div>
  )
}
