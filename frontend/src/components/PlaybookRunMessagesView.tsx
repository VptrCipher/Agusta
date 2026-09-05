import {useCallback, useEffect, useMemo, useRef, useState} from 'react'
import {Alert, Empty, Table} from 'antd'
import type {ColumnsType, TablePaginationConfig} from 'antd/es/table'
import client from '../api/client'
import {formatDateTime} from '../utils/recordDisplay'

interface PlaybookRunMessage {
  id: string
  sequence: number
  message: string
  created_at: string
}

interface PaginatedMessages {
  count: number
  results: PlaybookRunMessage[]
}

function errorMessage(error: unknown) {
  const detail = (error as {response?: {data?: {detail?: unknown}}}).response?.data?.detail
  return typeof detail === 'string' ? detail : 'Failed to load run messages'
}

export default function PlaybookRunMessagesView({
  playbookRunId,
  refreshToken,
}: {
  playbookRunId: string
  refreshToken?: unknown
}) {
  const [messages, setMessages] = useState<PlaybookRunMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [total, setTotal] = useState(0)
  const requestIdRef = useRef(0)

  const loadMessages = useCallback(async (nextPage: number, nextPageSize: number) => {
    void refreshToken
    if (!playbookRunId) return
    const requestId = requestIdRef.current + 1
    requestIdRef.current = requestId
    setLoading(true)
    setError('')
    try {
      const {data} = await client.get<PaginatedMessages>(
        `/playbooks/${encodeURIComponent(playbookRunId)}/messages/`,
        {params: {page: nextPage, page_size: nextPageSize}},
      )
      if (requestId !== requestIdRef.current) return
      setMessages(data.results)
      setTotal(data.count)
    } catch (loadError) {
      if (requestId !== requestIdRef.current) return
      setMessages([])
      setTotal(0)
      setError(errorMessage(loadError))
    } finally {
      if (requestId === requestIdRef.current) setLoading(false)
    }
  }, [playbookRunId, refreshToken])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadMessages(page, pageSize)
    return () => {
      requestIdRef.current += 1
    }
  }, [loadMessages, page, pageSize])

  const columns = useMemo<ColumnsType<PlaybookRunMessage>>(() => [
    {
      title: '#',
      dataIndex: 'sequence',
      width: 88,
    },
    {
      title: 'Time',
      dataIndex: 'created_at',
      width: 220,
      render: (value: string) => formatDateTime(value),
    },
    {
      title: 'Message',
      dataIndex: 'message',
      render: (value: string) => (
        <span style={{whiteSpace: 'pre-wrap', overflowWrap: 'anywhere'}}>{value}</span>
      ),
    },
  ], [])

  const handleTableChange = (pagination: TablePaginationConfig) => {
    setPage(pagination.current || 1)
    setPageSize(pagination.pageSize || 20)
  }

  return (
    <div style={{minWidth: 0}}>
      {error && <Alert type="error" showIcon title={error} style={{marginBottom: 12}}/>}
      <Table<PlaybookRunMessage>
        rowKey="id"
        size="small"
        columns={columns}
        dataSource={messages}
        loading={loading}
        onChange={handleTableChange}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: true,
          pageSizeOptions: [20, 50, 100],
          showTotal: (count) => `${count} message${count === 1 ? '' : 's'}`,
        }}
        locale={{emptyText: loading ? <span/> : <Empty description="No run messages"/>}}
        scroll={{y: 320}}
      />
    </div>
  )
}
