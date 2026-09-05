import type {DescriptionsProps} from 'antd'
import {Button, Descriptions} from 'antd'
import type {ReactNode} from 'react'
import type {FieldEditingController} from '../types/records'
import {DescriptionValue, EditableDescriptionValue} from './DescriptionValue'
import {descriptionStyles} from './descriptionValueStyles'
import {InlineTextAreaEditor, InlineTextEditor} from './InlineFieldEditors'
import JsonViewer from './JsonViewer'
import {choiceTag, emptyValue} from '../utils/recordDisplay'
import {editableLabel} from './editableLabel'
import {monoTextStyle} from '../utils/typography'

type RecordRow = Record<string, unknown>

interface EnrichmentBasicViewProps {
  record: RecordRow
  onOpenResource?: (resourceKey: string, rowId: string | number) => void
  fieldController?: FieldEditingController
}

const value = (record: RecordRow, key: string) => record[key]
const stringValue = (record: RecordRow, key: string) => emptyValue(value(record, key))
const upperStringValue = (record: RecordRow, key: string) => {
  const displayValue = stringValue(record, key)
  return displayValue === '—' ? displayValue : displayValue.toUpperCase()
}

function linkedObjectResourceKey(record: RecordRow) {
  const model = String(value(record, 'content_type_model') || '')
  const resources: Record<string, string> = {
    case: 'cases',
    alert: 'alerts',
    artifact: 'artifacts',
  }
  return resources[model]
}

function item(key: string, label: string, children: ReactNode, span?: number) {
  return {
    key,
    label,
    span,
    children: <DescriptionValue>{children}</DescriptionValue>,
  }
}

export default function EnrichmentBasicView({ record, onOpenResource, fieldController }: EnrichmentBasicViewProps) {
  const linkedResourceKey = linkedObjectResourceKey(record)
  const linkedRowId = value(record, 'linked_object_id') as string | number | null | undefined
  const canOpenLinkedObject = Boolean(linkedResourceKey && linkedRowId !== null && linkedRowId !== undefined && onOpenResource)
  const controller = fieldController
  const uidState = controller?.getFieldState('uid')
  const valueState = controller?.getFieldState('value')
  const descState = controller?.getFieldState('desc')

  const linkedObject = (
    <span style={monoTextStyle}>
      {canOpenLinkedObject && linkedResourceKey && linkedRowId !== null && linkedRowId !== undefined ? (
        <Button
          type="link"
          size="small"
          style={{ padding: 0, height: 'auto', ...monoTextStyle }}
          onClick={() => onOpenResource?.(linkedResourceKey, linkedRowId)}
        >
          {upperStringValue(record, 'linked_object')}
        </Button>
      ) : upperStringValue(record, 'linked_object')}
    </span>
  )

  const items: DescriptionsProps['items'] = [
    { key: 'enrichment-id', label: 'Enrichment ID', children: <DescriptionValue mono>{upperStringValue(record, 'enrichment_id')}</DescriptionValue> },
    item('type', 'Type', choiceTag(String(value(record, 'type') || ''), 'magenta')),
    item('provider', 'Provider', choiceTag(String(value(record, 'provider') || ''), 'purple')),
    item('linked-object', 'Linked Object', linkedObject),
    {
      key: 'uid',
      label: uidState && controller ? editableLabel('UID') : 'UID',
      children: uidState && controller ? (
        <EditableDescriptionValue
          state={uidState}
          editor={(
            <InlineTextEditor
              value={String(uidState.value ?? '')}
              disabled={uidState.saving}
              autoFocus={false}
              onChange={(next) => controller.setFieldDraftValue('uid', next)}
              onComplete={() => controller.finishFieldEdit('uid')}
              onCancel={() => controller.cancelFieldDraft('uid')}
            />
          )}
        />
      ) : <DescriptionValue mono>{stringValue(record, 'uid')}</DescriptionValue>,
    },
    {
      key: 'value',
      label: valueState && controller ? editableLabel('Value') : 'Value',
      span: 3,
      children: valueState && controller ? (
        <EditableDescriptionValue
          state={valueState}
          editor={(
            <InlineTextEditor
              value={String(valueState.value ?? '')}
              disabled={valueState.saving}
              autoFocus={false}
              onChange={(next) => controller.setFieldDraftValue('value', next)}
              onComplete={() => controller.finishFieldEdit('value')}
              onCancel={() => controller.cancelFieldDraft('value')}
            />
          )}
        />
      ) : <DescriptionValue mono>{stringValue(record, 'value')}</DescriptionValue>,
    },
    {
      key: 'description',
      label: descState && controller ? editableLabel('Description') : 'Description',
      span: 4,
      children: descState && controller ? (
        <EditableDescriptionValue
          state={descState}
          minHeight={86}
          height={86}
          editor={(
            <InlineTextAreaEditor
              value={String(descState.value ?? '')}
              disabled={descState.saving}
              autoFocus={false}
              onChange={(next) => controller.setFieldDraftValue('desc', next)}
              onComplete={() => controller.finishFieldEdit('desc')}
              onCancel={() => controller.cancelFieldDraft('desc')}
            />
          )}
        />
      ) : <DescriptionValue minHeight={86} height={86} multiline>{stringValue(record, 'desc')}</DescriptionValue>,
    },
    { key: 'data', label: 'Data', span: 4, children: <JsonViewer value={record.data} /> },
  ]

  return (
    <div style={{ padding: '20px 20px 16px', overflow: 'auto', height: '100%', boxSizing: 'border-box' }}>
      <Descriptions
        size="small"
        layout="vertical"
        colon={false}
        column={4}
        style={{ paddingTop: 4 }}
        styles={descriptionStyles}
        items={items}
      />
    </div>
  )
}
