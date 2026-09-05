import {useState} from 'react'
import KnowledgeCreateModal from '../components/KnowledgeCreateModal'
import ResourceListPage, {AddButton} from '../components/ResourceListPage'

export default function KnowledgeList() {
  const [createOpen, setCreateOpen] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)

  const handleCreated = () => {
    setCreateOpen(false)
    setRefreshKey((value) => value + 1)
  }

  return (
    <>
      <ResourceListPage
        key={refreshKey}
        resourceKey="knowledge"
        actions={<AddButton label="Add Knowledge" onClick={() => setCreateOpen(true)} />}
      />
      <KnowledgeCreateModal
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onCreated={handleCreated}
      />
    </>
  )
}
