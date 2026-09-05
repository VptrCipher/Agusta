import type {Attachment} from './attachments'
import client from './client'
import {type CursorPage, normalizeCursorPage} from './cursor'

export interface MentionedUser {
  id: number
  username: string
  name: string
}

export interface MentionUser {
  id: number
  username: string
  displayName: string
}

export interface RecordComment {
  id: number
  content_type: number
  object_id: string
  author: number
  author_name: string
  author_username: string
  author_avatar_url: string
  parent: number | null
  parent_author_name: string
  parent_author_username: string
  parent_body: string
  mentions: number[]
  mentioned_users: MentionedUser[]
  attachments: Attachment[]
  body: string
  created_at: string
  updated_at: string
  can_delete: boolean
}

const commentRequests = new Map<string, Promise<CursorPage<RecordComment>>>()
let mentionUsersCache: MentionUser[] | null = null
let mentionUsersRequest: Promise<MentionUser[]> | null = null

function commentsRequestKey(contentType: string, objectId: string, cursor?: string | null, pageSize?: number) {
  return `${contentType}:${objectId}:${cursor || ''}:${pageSize || ''}`
}

export async function fetchComments(
  contentType: string,
  objectId: string,
  options: { force?: boolean; cursor?: string | null; pageSize?: number } = {},
): Promise<CursorPage<RecordComment>> {
  const key = commentsRequestKey(contentType, objectId, options.cursor, options.pageSize)
  if (!options.force) {
    const existingRequest = commentRequests.get(key)
    if (existingRequest) return existingRequest
  }

  const request = client.get('/comments/', {
    params: {
      content_type: contentType,
      object_id: objectId,
      cursor: options.cursor || undefined,
      page_size: options.pageSize,
    },
  })
    .then(({ data }) => normalizeCursorPage<RecordComment>(data))
    .finally(() => {
      if (commentRequests.get(key) === request) {
        commentRequests.delete(key)
      }
    })

  commentRequests.set(key, request)
  return request
}

export async function fetchMentionUsers(): Promise<MentionUser[]> {
  if (mentionUsersCache) return mentionUsersCache
  if (mentionUsersRequest) return mentionUsersRequest

  mentionUsersRequest = client.get('/auth/user-options/')
    .then(({ data }) => {
      const users = (data.results || data).map((user: { id?: number; value?: string; username?: string; label?: string; name?: string }) => ({
        id: user.id ?? Number(user.value),
        username: user.username || user.label || '',
        displayName: user.name || user.label || user.username || '',
      }))
      mentionUsersCache = users
      return users
    })
    .finally(() => {
      mentionUsersRequest = null
    })

  return mentionUsersRequest
}

export async function createComment(input: {
  content_type: number | string
  object_id: string
  body: string
  parent?: number
  mentions?: number[]
  attachment_ids?: number[]
}): Promise<RecordComment> {
  const { data } = await client.post('/comments/', input)
  return data
}

export async function deleteComment(id: number): Promise<void> {
  await client.delete(`/comments/${id}/`)
}
