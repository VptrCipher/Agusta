import type {Attachment} from './attachments'
import client from './client'
import {type CursorPage, normalizeCursorPage} from './cursor'
import type {MentionedUser} from './comments'

export type InboxMessageKind = 'system' | 'user'

export interface InboxMessage {
  id: number
  kind: InboxMessageKind
  sender: number | null
  sender_name: string
  sender_username: string
  sender_avatar_url: string
  parent: number | null
  parent_author_name: string
  parent_author_username: string
  parent_body: string
  recipients: number[]
  recipient_users: MentionedUser[]
  attachments: Attachment[]
  content_type: number | null
  object_id: string
  resource_key: string
  resource_label: string
  body: string
  metadata: Record<string, unknown>
  created_at: string
  read_at: string | null
  is_read: boolean
  can_delete: boolean
}

export async function fetchInboxMessages(options: { unread?: boolean; cursor?: string | null; pageSize?: number } = {}): Promise<CursorPage<InboxMessage>> {
  const { data } = await client.get('/inbox/messages/', {
    params: {
      unread: options.unread ? true : undefined,
      cursor: options.cursor || undefined,
      page_size: options.pageSize,
    },
  })
  return normalizeCursorPage<InboxMessage>(data)
}

export async function fetchInboxUnreadCount(): Promise<number> {
  const { data } = await client.get<{ count: number }>('/inbox/messages/unread-count/')
  return data.count
}

export async function fetchInboxMessage(id: number): Promise<InboxMessage> {
  const { data } = await client.get<InboxMessage>(`/inbox/messages/${id}/`)
  return data
}

export async function createInboxMessage(input: {
  body: string
  recipients: number[]
  attachments?: number[]
  content_type?: number | string
  object_id?: string
  resource_key?: string
  resource_label?: string
}): Promise<InboxMessage> {
  const { data } = await client.post<InboxMessage>('/inbox/messages/', input)
  return data
}

export async function replyInboxMessage(id: number, input: {
  body: string
  attachments?: number[]
}): Promise<InboxMessage> {
  const { data } = await client.post<InboxMessage>(`/inbox/messages/${id}/reply/`, input)
  return data
}

export async function markAllInboxMessagesRead(): Promise<{ updated: number }> {
  const { data } = await client.post<{ updated: number }>('/inbox/messages/mark-all-read/')
  return data
}

export async function deleteInboxMessage(id: number): Promise<void> {
  await client.delete(`/inbox/messages/${id}/`)
}
