export interface CursorPage<T> {
  results: T[]
  next_cursor: string | null
  has_more: boolean
}

export function normalizeCursorPage<T>(data: T[] | Partial<CursorPage<T>>): CursorPage<T> {
  if (Array.isArray(data)) {
    return { results: data, next_cursor: null, has_more: false }
  }
  return {
    results: data.results || [],
    next_cursor: data.next_cursor || null,
    has_more: Boolean(data.has_more),
  }
}
