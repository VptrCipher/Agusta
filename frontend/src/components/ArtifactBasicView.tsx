import {Descriptions} from 'antd'
import {artifactRoleTag, choiceTag, emptyValue} from '../utils/recordDisplay'
import {monoTextStyle} from '../utils/typography'

type RecordRow = Record<string, unknown>

interface ArtifactBasicViewProps {
  record: RecordRow
}

const value = (record: RecordRow, key: string) => record[key]
const stringValue = (record: RecordRow, key: string) => emptyValue(value(record, key))
const upperStringValue = (record: RecordRow, key: string) => {
  const displayValue = stringValue(record, key)
  return displayValue === '—' ? displayValue : displayValue.toUpperCase()
}

export default function ArtifactBasicView({ record }: ArtifactBasicViewProps) {
  return (
    <div style={{ padding: '20px 20px 16px', overflow: 'auto', height: '100%', boxSizing: 'border-box' }}>
      <Descriptions
        size="small"
        layout="vertical"
        colon={false}
        column={4}
        style={{ paddingTop: 4 }}
      >
        <Descriptions.Item label="Artifact ID">
          <span style={monoTextStyle}>{upperStringValue(record, 'artifact_id')}</span>
        </Descriptions.Item>
        <Descriptions.Item label="Type">{choiceTag(String(value(record, 'type') || ''), 'geekblue')}</Descriptions.Item>
        <Descriptions.Item label="Role">{artifactRoleTag(String(value(record, 'role') || ''))}</Descriptions.Item>
        <Descriptions.Item label="Value" span={4}>
          <div
            style={{
              ...monoTextStyle,
              whiteSpace: 'pre-wrap',
              overflowWrap: 'anywhere',
            }}
          >
            {stringValue(record, 'value')}
          </div>
        </Descriptions.Item>
      </Descriptions>
    </div>
  )
}
