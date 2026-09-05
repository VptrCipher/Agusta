import {useState} from 'react'
import {PlusOutlined} from '@ant-design/icons'
import {Button, Tooltip} from 'antd'
import type {AdvancedFilterFieldConfig, OpenResourceOptions, ResourceColumn, ResourceFilterConfig} from '../types/records'
import EnrichmentCreateModal, {type EnrichmentTargetType} from './EnrichmentCreateModal'
import RelatedRecordsTable from './RelatedRecordsTable'

type RecordRow = Record<string, unknown>

interface RelatedEnrichmentsTableProps {
  targetType: EnrichmentTargetType
  targetId: string
  columns: ResourceColumn<RecordRow>[]
  filters: ResourceFilterConfig[]
  advancedFilters?: AdvancedFilterFieldConfig[]
  onOpenResource?: (resourceKey: string, rowId: string | number, options?: OpenResourceOptions) => void
  onChanged?: () => void
}

export type {EnrichmentTargetType}

export default function RelatedEnrichmentsTable({
  targetType,
  targetId,
  columns,
  filters,
  advancedFilters,
  onOpenResource,
  onChanged,
}: RelatedEnrichmentsTableProps) {
  const [createOpen, setCreateOpen] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)

  const handleCreated = () => {
    setCreateOpen(false)
    setRefreshKey((current) => current + 1)
    onChanged?.()
  }

  return (
    <>
      <RelatedRecordsTable
        endpoint="/enrichments/"
        tableKey={`${targetType}-enrichments:${targetId}`}
        resourceKey="enrichments"
        columns={columns}
        filters={filters}
        advancedFilters={advancedFilters}
        baseParams={targetId ? {[targetType]: targetId} : {}}
        onOpenResource={onOpenResource}
        refreshToken={refreshKey}
        actions={(
          <Tooltip title="Add Enrichment">
            <Button
              icon={<PlusOutlined />}
              disabled={!targetId}
              onClick={() => setCreateOpen(true)}
            />
          </Tooltip>
        )}
      />
      <EnrichmentCreateModal
        open={createOpen}
        targetType={targetType}
        targetId={targetId}
        onCancel={() => setCreateOpen(false)}
        onCreated={handleCreated}
      />
    </>
  )
}
