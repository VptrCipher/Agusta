import {useEffect, useMemo, useState} from 'react'
import {Alert, Table, Typography} from 'antd'
import type {ColumnsType} from 'antd/es/table'
import client from '../api/client'
import {choiceTag, emptyValueNode, formatDateTime, formatDurationSeconds} from '../utils/recordDisplay'

interface WorkerError {
  type: string
  message: string
}

interface WorkerHealth {
  worker_type: string
  display_name: string
  state: 'Starting' | 'Idle' | 'Running' | 'Degraded' | 'Down'
  reason: string
  started_at: string | null
  heartbeat_at: string | null
  iteration_started_at: string | null
  last_iteration_success_at: string | null
  last_processed_at: string | null
  last_failure_at: string | null
  last_duration_ms: number | null
  running_duration_seconds: number | null
  last_message: string
  last_error: WorkerError | null
  log_role: string
}

const STATE_COLORS: Record<WorkerHealth['state'], string> = {
  Starting: 'processing',
  Idle: 'green',
  Running: 'blue',
  Degraded: 'orange',
  Down: 'red',
}

function errorMessage(error: unknown) {
  const detail = (error as {response?: {data?: {detail?: unknown}}}).response?.data?.detail
  return typeof detail === 'string' ? detail : 'Failed to load worker health.'
}

function duration(worker: WorkerHealth) {
  if (worker.state === 'Running' && worker.running_duration_seconds !== null) {
    return formatDurationSeconds(worker.running_duration_seconds)
  }
  if (worker.last_duration_ms === null) return emptyValueNode()
  if (worker.last_duration_ms < 1000) return `${worker.last_duration_ms} ms`
  return formatDurationSeconds(worker.last_duration_ms / 1000)
}

export default function WorkersSettings() {
  const [workers, setWorkers] = useState<WorkerHealth[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    let timer: number | undefined

    const poll = async () => {
      try {
        const {data} = await client.get<{results: WorkerHealth[]}>('/settings/workers/')
        if (!active) return
        setWorkers(data.results)
        setError('')
      } catch (requestError: unknown) {
        if (!active) return
        setWorkers([])
        setError(errorMessage(requestError))
      } finally {
        if (active) {
          setLoading(false)
          timer = window.setTimeout(poll, 10_000)
        }
      }
    }

    poll()
    return () => {
      active = false
      if (timer !== undefined) window.clearTimeout(timer)
    }
  }, [])

  const columns = useMemo<ColumnsType<WorkerHealth>>(() => [
    {
      title: 'Worker',
      dataIndex: 'display_name',
      key: 'display_name',
      width: 220,
      fixed: 'left',
    },
    {
      title: 'State',
      dataIndex: 'state',
      key: 'state',
      width: 220,
      render: (state: WorkerHealth['state'], worker) => (
        <span style={{display: 'inline-flex', alignItems: 'center', gap: 8, flexWrap: 'wrap'}}>
          {choiceTag(state, STATE_COLORS[state])}
          {worker.reason ? <Typography.Text type="secondary">{worker.reason.replaceAll('_', ' ')}</Typography.Text> : null}
        </span>
      ),
    },
    {
      title: 'Current / Last Duration',
      key: 'duration',
      width: 180,
      render: (_, worker) => duration(worker),
    },
    {
      title: 'Current / Last Task',
      dataIndex: 'last_message',
      key: 'last_message',
      width: 360,
      render: (value: string, worker) => (
        worker.state === 'Running' ? 'Worker iteration is running.' : value || emptyValueNode()
      ),
    },
    {
      title: 'Last Heartbeat',
      dataIndex: 'heartbeat_at',
      key: 'heartbeat_at',
      width: 180,
      render: formatDateTime,
    },
    {
      title: 'Last Success',
      dataIndex: 'last_iteration_success_at',
      key: 'last_iteration_success_at',
      width: 180,
      render: formatDateTime,
    },
    {
      title: 'Last Processed',
      dataIndex: 'last_processed_at',
      key: 'last_processed_at',
      width: 180,
      render: formatDateTime,
    },
    {
      title: 'Last Failure',
      dataIndex: 'last_failure_at',
      key: 'last_failure_at',
      width: 180,
      render: formatDateTime,
    },
    {
      title: 'Last Error',
      dataIndex: 'last_error',
      key: 'last_error',
      width: 280,
      render: (value: WorkerError | null) => value ? `${value.type}: ${value.message}` : emptyValueNode(),
    },
  ], [])

  return (
    <div style={{height: '100%', minHeight: 0, display: 'flex', flexDirection: 'column', gap: 12}}>
      {error ? <Alert type="error" showIcon title={error} /> : null}
      <Table<WorkerHealth>
        rowKey="worker_type"
        size="small"
        loading={loading}
        columns={columns}
        dataSource={workers}
        pagination={false}
        scroll={{x: 1980, y: 'calc(100vh - 260px)'}}
      />
    </div>
  )
}
