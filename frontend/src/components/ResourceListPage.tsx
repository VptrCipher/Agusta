import {useCallback, useEffect, useState} from 'react'
import {Button, Tooltip} from 'antd'
import {PlusOutlined} from '@ant-design/icons'
import DataTable from './DataTable'
import RecordDetailModal from './RecordDetailModal'
import {fetchResourceMetadata} from '../api/metadata'
import {getResourceConfig} from '../config/resources'
import type {MetadataResponse, OpenResourceOptions, ResourceConfig} from '../types/records'

interface ResourceListPageProps {
  resourceKey: string
  actions?: React.ReactNode
}

export default function ResourceListPage({ resourceKey, actions }: ResourceListPageProps) {
  const config = getResourceConfig(resourceKey)
  const [metadata, setMetadata] = useState<MetadataResponse | null>(null)
  const [selectedRowId, setSelectedRowId] = useState<string | number | null>(null)
  const [selectedInitialTab, setSelectedInitialTab] = useState<string | undefined>()
  const [relatedDetail, setRelatedDetail] = useState<{
    config: ResourceConfig
    rowId: string | number
    onChanged: () => void
  } | null>(null)
  const [tableRefreshToken, setTableRefreshToken] = useState(0)

  useEffect(() => {
    fetchResourceMetadata().then(setMetadata).catch(() => setMetadata(null))
  }, [])

  const refreshTable = useCallback(() => {
    setTableRefreshToken((current) => current + 1)
  }, [])

  const openRelatedDetail = useCallback((targetResourceKey: string, targetRowId: string | number, options?: OpenResourceOptions) => {
    setRelatedDetail({
      config: getResourceConfig(targetResourceKey),
      rowId: targetRowId,
      onChanged: () => {
        options?.onChanged?.()
        refreshTable()
      },
    })
  }, [refreshTable])

  const closePrimaryDetail = useCallback(() => {
    setSelectedRowId(null)
    setSelectedInitialTab(undefined)
  }, [])

  const closeRelatedDetail = useCallback(() => {
    setRelatedDetail(null)
  }, [])

  return (
    <>
      <DataTable
        endpoint={config.endpoint}
        tableKey={config.key}
        rowKey={config.rowKey}
        columns={config.columns}
        filters={config.filters}
        advancedFilters={config.advancedFilters}
        metadata={metadata?.resources?.[config.key]}
        searchPlaceholder={config.searchPlaceholder}
        actions={actions}
        onRowClick={(record, options) => {
          setSelectedInitialTab(options?.tabKey)
          setSelectedRowId(record[config.rowKey] as string | number)
        }}
        onOpenResource={openRelatedDetail}
        refreshToken={tableRefreshToken}
        readOnly={config.readOnly}
        dense
        fillParent
      />
      <RecordDetailModal
        config={config}
        rowId={selectedRowId}
        open={selectedRowId !== null}
        initialTabKey={selectedInitialTab}
        onOpenResource={openRelatedDetail}
        onChanged={refreshTable}
        onClose={closePrimaryDetail}
      />
      {relatedDetail && (
        <RecordDetailModal
          config={relatedDetail.config}
          rowId={relatedDetail.rowId}
          open
          onOpenResource={openRelatedDetail}
          onChanged={relatedDetail.onChanged}
          onClose={closeRelatedDetail}
        />
      )}
    </>
  )
}

export function AddButton({ onClick, label }: { onClick: () => void; label: string }) {
  return (
    <Tooltip title={label}>
      <Button icon={<PlusOutlined />} onClick={onClick} />
    </Tooltip>
  )
}
