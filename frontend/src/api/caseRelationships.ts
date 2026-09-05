import client from './client'

export type CaseRelationshipType = 'Related' | 'Duplicate of' | 'Parent of'

export interface RelatedCaseSummary {
  id: string
  case_id: string
  title: string
  status: string
  severity: string
  verdict: string
  assignee_id: number | null
  assignee_name: string
}

export interface CaseRelationship {
  [key: string]: unknown
  id: string
  source_case: RelatedCaseSummary
  target_case: RelatedCaseSummary
  relationship_type: CaseRelationshipType
  note: string
  created_by: string
  created_at: string
  updated_at: string
}

export interface CaseRelationshipSuggestion {
  case: RelatedCaseSummary
  shared_artifact_count: number
  shared_artifacts: Array<{
    id: string
    type: string
    value: string
  }>
}

export interface CaseRelationshipInput {
  source_case_id: string
  target_case_id: string
  relationship_type: CaseRelationshipType
  note: string
}

export async function fetchCaseRelationshipSuggestions(caseId: string) {
  const {data} = await client.get<{results?: CaseRelationshipSuggestion[]}>(
    '/case-relationships/suggestions/',
    {params: {case: caseId}},
  )
  return data.results || []
}

export async function createCaseRelationship(input: CaseRelationshipInput) {
  const {data} = await client.post<CaseRelationship>('/case-relationships/', input)
  return data
}

export async function updateCaseRelationship(id: string, input: CaseRelationshipInput) {
  const {data} = await client.patch<CaseRelationship>(`/case-relationships/${id}/`, input)
  return data
}

export async function deleteCaseRelationship(id: string) {
  await client.delete(`/case-relationships/${id}/`)
}

export async function searchCases(search: string) {
  const {data} = await client.get<{results?: RelatedCaseSummary[]}>('/cases/', {
    params: {search, page_size: 20},
  })
  return data.results || []
}
