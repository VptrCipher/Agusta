import {useCallback, useState} from 'react'
import {useNavigate, useParams} from 'react-router-dom'
import {getResourceConfig} from '../config/resources'
import RecordDetailModal from './RecordDetailModal'
import type {ResourceConfig} from '../types/records'

const routeResourceKeys = new Set(['cases', 'alerts', 'artifacts', 'enrichments', 'playbooks', 'knowledge'])

export default function ResourceDetailRoute({ resourceKey }: { resourceKey: string }) {
  const { rowId } = useParams<{ rowId: string }>()
  const navigate = useNavigate()
  const config = getResourceConfig(resourceKey)
  const [relatedDetail, setRelatedDetail] = useState<{
    config: ResourceConfig
    rowId: string | number
  } | null>(null)
  const openRelatedDetail = useCallback((targetResourceKey: string, targetRowId: string | number) => {
    if (routeResourceKeys.has(targetResourceKey)) {
      setRelatedDetail(null)
      navigate(`/${targetResourceKey}/${encodeURIComponent(String(targetRowId))}`)
      return
    }
    setRelatedDetail({
      config: getResourceConfig(targetResourceKey),
      rowId: targetRowId,
    })
  }, [navigate])

  return (
    <>
      <RecordDetailModal
        config={config}
        rowId={rowId || null}
        open={Boolean(rowId)}
        onOpenResource={openRelatedDetail}
        onClose={() => navigate(`/${resourceKey}`)}
      />
      {relatedDetail && (
        <RecordDetailModal
          config={relatedDetail.config}
          rowId={relatedDetail.rowId}
          open
          onOpenResource={openRelatedDetail}
          onClose={() => setRelatedDetail(null)}
        />
      )}
    </>
  )
}
