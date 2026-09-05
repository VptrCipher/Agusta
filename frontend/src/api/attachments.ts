import client from './client'

export interface Attachment {
  id: number
  access_key: string
  file: string
  filename: string
  size: number
  uploaded_by: number | null
  uploaded_by_name: string
  uploaded_at: string
}

export async function uploadAttachment(file: File): Promise<Attachment> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await client.post<Attachment>('/attachments/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}
