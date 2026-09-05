import client from './client'

export type DashboardWindow = '24h' | '7d' | '30d'

export interface DashboardLabelValue {
  label: string
  value: number
}

export interface DashboardKeyword {
  text: string
  value: number
}

export interface DashboardMitreSeverityCell {
  tactic: string
  severity: string
  value: number
}

export interface DashboardTrendPoint extends DashboardLabelValue {
  time: string
}

export interface DashboardMeanTime {
  seconds: number | null
  sample_count: number
}

export interface DashboardSummary {
  active_risk_index: number
  total_cases: number
  total_alerts: number
  total_artifacts: number
  total_enrichments: number
  total_knowledge: number
  open_cases: number
  open_critical_cases: number
  critical_high_alerts: number
  running_playbooks: number
  failed_playbooks: number
  automation_success_rate: number | null
}

export interface DashboardCoverage {
  enrichment_coverage: number | null
  playbook_coverage: number | null
  knowledge_records: number
  artifact_records: number
  enrichment_records: number
}

export interface DashboardRiskArtifact {
  id: string
  name: string
  type: string
  role: string
  value: string
  risk_score: number
  alert_count: number
}

export interface DashboardHighlight {
  id: string
  kind: 'case' | 'alert'
  readable_id: string
  title: string
  severity: string
  status: string
  timestamp: string
  subtitle: string
}

export interface DashboardCacheMetadata {
  generated_at: string
  refreshed_at: string
  refresh_interval_seconds: number
  age_seconds: number
  stale_warning: boolean
}

export interface DashboardOverview {
  window: DashboardWindow
  window_start: string
  generated_at: string
  cache: DashboardCacheMetadata
  summary: DashboardSummary
  mean_times: {
    mttd: DashboardMeanTime
    mtta: DashboardMeanTime
    mttr: DashboardMeanTime
  }
  alert_trend: DashboardTrendPoint[]
  severity_distribution: DashboardLabelValue[]
  case_status_mix: DashboardLabelValue[]
  product_category_distribution: DashboardLabelValue[]
  mitre_tactics: DashboardLabelValue[]
  mitre_severity_heatmap: DashboardMitreSeverityCell[]
  threat_keywords: DashboardKeyword[]
  automation: DashboardLabelValue[]
  coverage: DashboardCoverage
  top_risk_artifacts: DashboardRiskArtifact[]
  recent_highlights: DashboardHighlight[]
}

export async function fetchDashboardOverview(window: DashboardWindow) {
  const { data } = await client.get<DashboardOverview>('/dashboard/overview/', {
    params: { window },
  })
  return data
}
