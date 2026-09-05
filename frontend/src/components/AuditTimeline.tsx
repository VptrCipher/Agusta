import {useCallback, useEffect, useMemo, useState} from 'react'
import type {GetProps} from 'antd'
import {Alert, Button, DatePicker, Empty, Select, Space, Spin, Tag, Timeline} from 'antd'
import {FilterOutlined, ReloadOutlined, RightOutlined} from '@ant-design/icons'
import client from '../api/client'
import {normalizeCursorPage} from '../api/cursor'
import {getResourceConfig} from '../config/resources'
import useCursorFeed from '../hooks/useCursorFeed'
import {comfortableTagProps} from '../utils/tagStyles'
import {tabularNumbersStyle, typography} from '../utils/typography'
import FeedLoadMore from './FeedLoadMore'

const { RangePicker } = DatePicker
const actionColor: Record<string, string> = { create: 'green', update: 'blue', delete: 'red', linked: 'cyan', unlinked: 'orange', deleted: 'red' }
const relationActions = new Set(['linked', 'unlinked', 'deleted'])
const actionOptions = Object.keys(actionColor).map((action) => ({ label: action, value: action }))
const resourceKeyByContentType: Record<string, string> = {
  case: 'cases',
  alert: 'alerts',
  artifact: 'artifacts',
  enrichment: 'enrichments',
  playbook: 'playbooks',
  knowledge: 'knowledge',
  user: 'users',
}
type RangePickerValue = GetProps<typeof RangePicker>['value']

interface FilterOption {
  label: string
  value: string
}

interface AuditLog {
  id: number
  action: string
  actor: string | null
  actor_id: string | number | null
  actor_name?: string
  changes?: Record<string, unknown>
  display_changes?: Record<string, unknown>
  metadata?: {
    relation?: string
    related_resource?: string
    related_id?: string
    related_label?: string
  }
  created_at: string
}

function formatValue(value: unknown) {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function valuePill(value: unknown, tone: 'from' | 'to', obsolete = false) {
  const color = tone === 'from' ? '#dd9a92' : '#a9c48d'
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        maxWidth: '100%',
        color,
        ...typography.compact,
        whiteSpace: 'pre-wrap',
        overflowWrap: 'anywhere',
        textDecoration: obsolete ? 'line-through' : undefined,
      }}
    >
      {formatValue(value)}
    </span>
  )
}

function formatChanges(changes?: Record<string, unknown>, action?: string, fieldLabel?: (field: string) => string) {
  if (!changes || !Object.keys(changes).length) return null
  const obsoleteOldValue = action === 'update'
  return (
    <div style={{ marginTop: 8, display: 'grid', gap: 10 }}>
      {Object.entries(changes).map(([field, raw]) => {
        const change = raw as { from?: unknown; to?: unknown; added?: unknown[]; removed?: unknown[]; cleared?: boolean }
        const label = fieldLabel?.(field) || field
        if ('from' in change || 'to' in change) {
          return (
            <div key={field} style={{ display: 'grid', gap: 6, minWidth: 0 }}>
              <div style={{ ...typography.fieldLabel, color: 'rgba(240, 238, 231, 0.9)' }}>{label}</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0, flexWrap: 'wrap' }}>
                {valuePill(change.from, 'from', obsoleteOldValue)}
                <RightOutlined style={{ color: 'rgba(240, 238, 231, 0.45)', fontSize: typography.compact.fontSize }} />
                {valuePill(change.to, 'to')}
              </div>
            </div>
          )
        }

        const added = change.added?.length ? `added ${change.added.map(formatValue).join(', ')}` : ''
        const removed = change.removed?.length ? `removed ${change.removed.map(formatValue).join(', ')}` : ''
        const text = change.cleared ? 'cleared' : [added, removed].filter(Boolean).join('; ')
        return (
          <div key={field} style={{ ...typography.compact, color: 'rgba(240, 238, 231, 0.68)' }}>
            <span style={{ color: 'rgba(240, 238, 231, 0.88)' }}>{label}</span>: {text}
          </div>
        )
      })}
    </div>
  )
}

function mergeOptions(previous: FilterOption[], options: FilterOption[]) {
  const optionMap = new Map(previous.map((option) => [option.value, option]))
  options.forEach((option) => {
    if (option.value) optionMap.set(option.value, option)
  })
  return Array.from(optionMap.values()).toSorted((left, right) => left.label.localeCompare(right.label))
}

function logFieldOptions(logs: AuditLog[], fieldLabel: (field: string) => string) {
  return logs.flatMap((log) => {
    const changeFields = Object.keys(log.display_changes || log.changes || {})
    const relation = log.metadata?.relation
    return [...changeFields, relation || '']
      .filter(Boolean)
      .map((field) => ({ label: fieldLabel(field), value: field }))
  })
}

function logActorOptions(logs: AuditLog[]) {
  return logs.map((log) => {
    if (!log.actor_id) return { label: 'system', value: 'system' }
    return {
      label: log.actor_name || log.actor || String(log.actor_id),
      value: String(log.actor_id),
    }
  })
}

interface AuditTimelineProps {
  contentType: string
  objectId: string
  onOpenResource?: (resourceKey: string, rowId: string | number) => void
}

function resourceName(resourceKey: string) {
  const names: Record<string, string> = {
    cases: 'case',
    alerts: 'alert',
    artifacts: 'artifact',
    enrichments: 'enrichment',
    playbooks: 'playbook',
    knowledge: 'knowledge',
    users: 'user',
  }
  return names[resourceKey] || resourceKey
}

function RelationEvent({ log, onOpenResource }: { log: AuditLog; onOpenResource?: (resourceKey: string, rowId: string | number) => void }) {
  const metadata = log.metadata || {}
  const canOpen = log.action !== 'deleted' && Boolean(metadata.related_resource && metadata.related_id && onOpenResource)
  const label = metadata.related_label || metadata.related_id || 'related record'
  return (
    <div style={{ ...typography.compact, marginTop: 6, color: 'rgba(240, 238, 231, 0.68)' }}>
      <span>{metadata.related_resource ? resourceName(metadata.related_resource) : metadata.relation || 'relationship'}: </span>
      {canOpen && metadata.related_resource && metadata.related_id ? (
        <Button
          type="link"
          size="small"
          style={{ ...typography.compact, padding: 0, height: 'auto' }}
          onClick={() => onOpenResource?.(metadata.related_resource || '', metadata.related_id || '')}
        >
          {label}
        </Button>
      ) : (
        <span style={{ color: 'rgba(240, 238, 231, 0.88)' }}>{label}</span>
      )}
    </div>
  )
}

export default function AuditTimeline({ contentType, objectId, onOpenResource }: AuditTimelineProps) {
  const [actionFilter, setActionFilter] = useState<string | null>(null)
  const [actorFilter, setActorFilter] = useState<string | null>(null)
  const [fieldFilter, setFieldFilter] = useState<string | null>(null)
  const [createdRange, setCreatedRange] = useState<RangePickerValue>(null)
  const [filtersExpanded, setFiltersExpanded] = useState(false)
  const [userOptions, setUserOptions] = useState<FilterOption[]>([])
  const hasActiveFilters = Boolean(actionFilter || actorFilter || fieldFilter || createdRange?.[0] || createdRange?.[1])

  const fieldLabelMap = useMemo(() => {
    const resourceKey = resourceKeyByContentType[contentType] || `${contentType}s`
    const config = getResourceConfig(resourceKey)
    const entries = [
      ...config.columns.map((column) => [column.dataIndex || column.key, column.title] as const),
      ...(config.advancedFilters || []).map((field) => [field.key, field.label] as const),
      ...config.tabs.map((tab) => [tab.key, tab.label] as const),
    ]
    return new Map(entries.filter(([key]) => Boolean(key)))
  }, [contentType])

  const fieldLabel = useMemo(() => (
    (field: string) => fieldLabelMap.get(field) || field
  ), [fieldLabelMap])

  useEffect(() => {
    let mounted = true
    client.get<FilterOption[]>('/auth/user-options/')
      .then(({ data }) => {
        if (mounted) setUserOptions(data)
      })
      .catch(() => {
        if (mounted) setUserOptions([])
      })
    return () => {
      mounted = false
    }
  }, [])

  const fetchAuditPage = useCallback(async (cursor?: string | null) => {
    const params: Record<string, string | number | undefined> = {
      content_type: contentType,
      object_id: objectId,
      cursor: cursor || undefined,
      page_size: 20,
    }
    if (actionFilter) params.action = actionFilter
    if (actorFilter) params.actor = actorFilter
    if (fieldFilter) params.field = fieldFilter
    if (createdRange?.[0]) params.created_after = createdRange[0].toISOString()
    if (createdRange?.[1]) params.created_before = createdRange[1].toISOString()

    const { data } = await client.get('/audit-logs/', { params })
    return normalizeCursorPage<AuditLog>(data)
  }, [actionFilter, actorFilter, contentType, createdRange, fieldFilter, objectId])

  const {
    items: logs,
    loadingInitial,
    loadingMore,
    hasMore,
    error: loadError,
    refresh: refreshLogs,
    loadMore,
  } = useCursorFeed({
    fetchPage: fetchAuditPage,
    getItemKey: (log) => log.id,
    errorMessage: 'Failed to load audit log',
  })

  const fieldOptions = useMemo(() => (
    mergeOptions([], logFieldOptions(logs, fieldLabel))
  ), [fieldLabel, logs])

  const actorOptions = useMemo(() => (
    mergeOptions([{ label: 'system', value: 'system' }, ...logActorOptions(logs)], userOptions)
  ), [logs, userOptions])

  const filterBar = (
    <div style={{ width: '100%', marginBottom: 12 }}>
      <Space style={{ marginBottom: filtersExpanded ? 8 : 0 }}>
        <Button
          type={hasActiveFilters ? 'primary' : 'default'}
          icon={<FilterOutlined />}
          onClick={() => setFiltersExpanded((previous) => !previous)}
        >
          Filters
        </Button>
        <Button icon={<ReloadOutlined />} loading={loadingInitial} onClick={refreshLogs} />
      </Space>
      {filtersExpanded && (
        <div style={{ display: 'grid', gap: 8 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)', gap: 8 }}>
            <Select
              showSearch={{ optionFilterProp: 'label' }}
              allowClear
              placeholder="Field"
              options={fieldOptions}
              value={fieldFilter}
              onChange={(next) => setFieldFilter(next ?? null)}
              style={{ width: '100%' }}
            />
            <Select
              showSearch={{ optionFilterProp: 'label' }}
              allowClear
              placeholder="Operator"
              options={actorOptions}
              value={actorFilter}
              onChange={(next) => setActorFilter(next ?? null)}
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '100px minmax(0, 1fr)', gap: 8 }}>
            <Select
              allowClear
              placeholder="Action"
              options={actionOptions}
              value={actionFilter}
              onChange={(next) => setActionFilter(next ?? null)}
              style={{ width: '100%' }}
            />
            <RangePicker
              showTime
              allowClear
              value={createdRange}
              onChange={(next) => setCreatedRange(next)}
              style={{ width: '100%' }}
            />
          </div>
        </div>
      )}
    </div>
  )

  let content = (
    <>
      {loadError && logs.length > 0 && <Alert type="error" title={loadError} showIcon style={{ marginBottom: 12 }} />}
      <Timeline items={logs.map((log) => ({
        color: actionColor[log.action] || 'gray',
        children: (
          <div>
            <Space size={8} wrap>
              <Tag {...comfortableTagProps} color={actionColor[log.action]} style={{ marginInlineEnd: 0 }}>{log.action}</Tag>
              <span>{log.actor_name || log.actor || 'system'}</span>
              <span style={{ ...typography.compact, ...tabularNumbersStyle, color: '#8c877d' }}>{new Date(log.created_at).toLocaleString()}</span>
            </Space>
            {relationActions.has(log.action) ? <RelationEvent log={log} onOpenResource={onOpenResource} /> : formatChanges(log.display_changes || log.changes, log.action, fieldLabel)}
          </div>
        ),
      }))} />
      {hasMore && <FeedLoadMore loading={loadingMore} onClick={loadMore} />}
    </>
  )

  if (loadingInitial) content = <Spin style={{ margin: 16 }} />
  else if (loadError && !logs.length) content = <Alert type="error" title={loadError} showIcon style={{ margin: '0 4px' }} />
  else if (!logs.length) content = <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No audit log" />

  return (
    <div>
      {filterBar}
      {content}
    </div>
  )
}
