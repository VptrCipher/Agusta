import {type ReactNode, useEffect, useState} from 'react'
import type {DescriptionsProps} from 'antd'
import {Descriptions, Tag} from 'antd'
import type {ChoiceOption, FieldEditingController} from '../types/records'
import client from '../api/client'
import {DescriptionValue, EditableDescriptionValue} from './DescriptionValue'
import DetailSectionDivider from './DetailSectionDivider'
import {descriptionStyles} from './descriptionValueStyles'
import {InlineDateTimeEditor, InlineMarkdownEditor, InlineSelectEditor, InlineTagChoiceEditor, InlineUserEditor} from './InlineFieldEditors'
import MarkdownPreview from './MarkdownPreview'
import {caseCategoryTag, emptyValue, emptyValueNode, formatDateTime, formatDurationSeconds, severityTag, statusTag, verdictTag} from '../utils/recordDisplay'
import {comfortableTagProps} from '../utils/tagStyles'
import {editableLabel} from './editableLabel'

type RecordRow = Record<string, unknown>

interface CaseBasicViewProps {
  record: RecordRow
  fieldController?: FieldEditingController
}

const value = (record: RecordRow, key: string) => record[key]
const stringValue = (record: RecordRow, key: string) => emptyValue(value(record, key))
const upperStringValue = (record: RecordRow, key: string) => {
  const displayValue = stringValue(record, key)
  return displayValue === '—' ? displayValue : displayValue.toUpperCase()
}
const mono = (children: string) => <DescriptionValue mono>{children}</DescriptionValue>
const block = (children: string) => <DescriptionValue height="auto" multiline>{children}</DescriptionValue>
const riskTag = (raw: unknown) => severityTag(String(raw || ''))
const verdictColors: Record<string, string> = {
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
const tags = (items: unknown) => Array.isArray(items) && items.length
  ? <span style={{ display: 'inline-flex', flexWrap: 'wrap', gap: 4 }}>{items.map((item) => <Tag {...comfortableTagProps} key={String(item)} color="blue" style={{ marginInlineEnd: 0 }}>{String(item)}</Tag>)}</span>
  : emptyValueNode()
const verdictChoiceTag = (next: string, selected?: boolean) => next
  ? <Tag {...comfortableTagProps} variant={selected ? 'solid' : 'outlined'} color={verdictColors[next]} style={{ marginInlineEnd: 0 }}>{next}</Tag>
  : emptyValueNode()

function Section({ title, items, showTitle = true }: { title?: string; items: DescriptionsProps['items']; showTitle?: boolean }) {
  return (
    <div style={{ marginTop: showTitle ? 16 : 0 }}>
      {showTitle && title && <DetailSectionDivider title={title} />}
      <Descriptions
        size="small"
        layout="vertical"
        colon={false}
        column={4}
        items={items}
        styles={descriptionStyles}
      />
    </div>
  )
}

function textItem(key: string, label: string, children: ReactNode, span?: number) {
  return {
    key,
    label,
    span,
    children: <DescriptionValue>{children}</DescriptionValue>,
  }
}

function optionLabel(options: ChoiceOption[], optionValue: unknown, fallback?: string) {
  const rawValue = optionValue === null || optionValue === undefined ? '' : String(optionValue)
  if (!rawValue) return '—'
  return options.find((option) => String(option.value) === rawValue)?.label || fallback || rawValue
}

export default function CaseBasicView({ record, fieldController }: CaseBasicViewProps) {
  const controller = fieldController
  const statusState = controller?.getFieldState('status')
  const assigneeState = controller?.getFieldState('assignee')
  const acknowledgedTimeState = controller?.getFieldState('acknowledged_time')
  const closedTimeState = controller?.getFieldState('closed_time')
  const verdictState = controller?.getFieldState('verdict')
  const summaryState = controller?.getFieldState('summary')
  const editable = Boolean(controller)
  const [userOptions, setUserOptions] = useState<ChoiceOption[]>([])

  useEffect(() => {
    if (!editable) return
    let mounted = true
    client.get<ChoiceOption[]>('/auth/user-options/')
      .then(({ data }) => {
        if (mounted) setUserOptions(data)
      })
      .catch(() => {
        if (mounted) setUserOptions([])
      })
    return () => {
      mounted = false
    }
  }, [editable])

  const assigneeDisplayValue = assigneeState
    ? optionLabel(userOptions, assigneeState.value, stringValue(record, 'assignee_name'))
    : stringValue(record, 'assignee_name')


  const summaryItems: DescriptionsProps['items'] = [
    { key: 'case-id', label: 'Case ID', children: mono(upperStringValue(record, 'case_id')) },
    {
      key: 'status',
      label: statusState && controller ? editableLabel('Status') : 'Status',
      children: statusState && controller ? (
        <InlineSelectEditor
          value={statusState.value ? String(statusState.value) : null}
          disabled={statusState.saving}
          options={statusState.options}
          allowClear={false}
          onStart={() => controller.startFieldEdit('status')}
          onChange={(next) => controller.setFieldDraftValue('status', next)}
          onComplete={() => controller.finishFieldEdit('status')}
          onCancel={() => controller.cancelFieldDraft('status')}
        />
      ) : <DescriptionValue>{statusTag(String(value(record, 'status') || ''))}</DescriptionValue>,
    },
    {
      key: 'assignee',
      label: assigneeState && controller ? editableLabel('Assignee') : 'Assignee',
      children: assigneeState && controller ? (
        <InlineUserEditor
          value={assigneeState.value ? String(assigneeState.value) : null}
          disabled={assigneeState.saving}
          options={userOptions}
          fallbackLabel={assigneeDisplayValue}
          onStart={() => controller.startFieldEdit('assignee')}
          onChange={(next) => controller.setFieldDraftValue('assignee', next)}
          onComplete={() => controller.finishFieldEdit('assignee')}
          onCancel={() => controller.cancelFieldDraft('assignee')}
        />
      ) : <DescriptionValue>{stringValue(record, 'assignee_name')}</DescriptionValue>,
    },
    textItem('spacer', '', null),
    textItem('severity', 'Severity', riskTag(value(record, 'severity'))),
    textItem('confidence', 'Confidence', riskTag(value(record, 'confidence'))),
    textItem('impact', 'Impact', riskTag(value(record, 'impact'))),
    textItem('priority', 'Priority', riskTag(value(record, 'priority'))),
    textItem('severity-ai', 'Severity (AI)', riskTag(value(record, 'severity_ai'))),
    textItem('confidence-ai', 'Confidence (AI)', riskTag(value(record, 'confidence_ai'))),
    textItem('impact-ai', 'Impact (AI)', riskTag(value(record, 'impact_ai'))),
    textItem('priority-ai', 'Priority (AI)', riskTag(value(record, 'priority_ai'))),
    textItem('category', 'Category', caseCategoryTag(String(value(record, 'category') || ''))),
    { key: 'correlation-uid', label: 'Correlation UID', children: mono(stringValue(record, 'correlation_uid')) },
    textItem('tags', 'Tags', tags(value(record, 'tags')), 2),
    { key: 'description', label: 'Description', span: 4, children: block(stringValue(record, 'description')) },
    textItem('first-alert-seen-time', 'First Seen Alert', formatDateTime(String(value(record, 'first_alert_seen_time') || ''))),
    textItem('detection-time', 'Detection Time (TTD)', formatDurationSeconds(value(record, 'detection_time_seconds'))),
  ]

  const inProcessItems: DescriptionsProps['items'] = [
    {
      key: 'acknowledged-time',
      label: acknowledgedTimeState && controller ? editableLabel('Acknowledged Time') : 'Acknowledged Time',
      children: acknowledgedTimeState && controller ? (
        <EditableDescriptionValue
          state={acknowledgedTimeState}
          editor={(
            <InlineDateTimeEditor
              value={acknowledgedTimeState.value ? String(acknowledgedTimeState.value) : null}
              disabled={acknowledgedTimeState.saving}
              autoFocus={false}
              onChange={(next) => controller.setFieldDraftValue('acknowledged_time', next)}
              onComplete={() => controller.finishFieldEdit('acknowledged_time')}
              onCancel={() => controller.cancelFieldDraft('acknowledged_time')}
            />
          )}
        />
      ) : <DescriptionValue>{formatDateTime(String(value(record, 'acknowledged_time') || ''))}</DescriptionValue>,
    },
    textItem('acknowledgement-time', 'Time to Acknowledge (TTA)', formatDurationSeconds(value(record, 'acknowledgement_time_seconds'))),
  ]

  const resolvedItems: DescriptionsProps['items'] = [
    {
      key: 'closed-time',
      label: closedTimeState && controller ? editableLabel('Closed Time') : 'Closed Time',
      children: closedTimeState && controller ? (
        <EditableDescriptionValue
          state={closedTimeState}
          editor={(
            <InlineDateTimeEditor
              value={closedTimeState.value ? String(closedTimeState.value) : null}
              disabled={closedTimeState.saving}
              autoFocus={false}
              onChange={(next) => controller.setFieldDraftValue('closed_time', next)}
              onComplete={() => controller.finishFieldEdit('closed_time')}
              onCancel={() => controller.cancelFieldDraft('closed_time')}
            />
          )}
        />
      ) : <DescriptionValue>{formatDateTime(String(value(record, 'closed_time') || ''))}</DescriptionValue>,
    },
    textItem('response-time', 'Time to Respond (TTR)', formatDurationSeconds(value(record, 'response_time_seconds'))),
    {
      key: 'verdict',
      label: verdictState && controller ? editableLabel('Verdict') : 'Verdict',
      children: verdictState && controller ? (
        <InlineTagChoiceEditor
          value={String(verdictState.value ?? '')}
          disabled={verdictState.saving}
          options={verdictState.options}
          renderTag={verdictChoiceTag}
          clearLabel="Unset"
          onStart={() => controller.startFieldEdit('verdict')}
          onChange={(next) => controller.setFieldDraftValue('verdict', next)}
          onComplete={() => controller.finishFieldEdit('verdict')}
          onCancel={() => controller.cancelFieldDraft('verdict')}
        />
      ) : <DescriptionValue>{verdictTag(String(value(record, 'verdict') || ''))}</DescriptionValue>,
    },
    textItem('verdict-ai', 'Verdict (AI)', verdictTag(String(value(record, 'verdict_ai') || ''))),
    {
      key: 'summary',
      label: summaryState && controller ? editableLabel('Summary') : 'Summary',
      span: 4,
      children: summaryState && controller ? (
        <InlineMarkdownEditor
          value={String(summaryState.value ?? '')}
          disabled={summaryState.saving}
          height="480px"
          onChange={(next) => controller.setFieldDraftValue('summary', next)}
          onCancel={() => controller.cancelFieldDraft('summary')}
        />
      ) : <MarkdownPreview source={stringValue(record, 'summary')} height="480px" />,
    },
  ]

  return (
    <div style={{ padding: '20px 20px 16px', overflow: 'auto', height: '100%', boxSizing: 'border-box' }}>
      <Section showTitle={false} items={summaryItems} />
      <Section title="In Process & On Hold" items={inProcessItems} />
      <Section title="Resolved & Close" items={resolvedItems} />
    </div>
  )
}
