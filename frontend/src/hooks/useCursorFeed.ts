import {useCallback, useEffect, useRef, useState} from 'react'
import {type CursorPage, normalizeCursorPage} from '../api/cursor'

interface UseCursorFeedOptions<T> {
  enabled?: boolean
  errorMessage?: string
  fetchPage: (cursor?: string | null) => Promise<CursorPage<T> | T[]>
  getItemKey: (item: T) => string | number
}

function mergeByKey<T>(current: T[], incoming: T[], getItemKey: (item: T) => string | number) {
  const seen = new Set(current.map((item) => getItemKey(item)))
  const merged = [...current]
  incoming.forEach((item) => {
    const key = getItemKey(item)
    if (!seen.has(key)) {
      seen.add(key)
      merged.push(item)
    }
  })
  return merged
}

export default function useCursorFeed<T>({
  enabled = true,
  errorMessage = 'Failed to load data',
  fetchPage,
  getItemKey,
}: UseCursorFeedOptions<T>) {
  const [items, setItems] = useState<T[]>([])
  const [nextCursor, setNextCursor] = useState<string | null>(null)
  const [hasMore, setHasMore] = useState(false)
  const [loadingInitial, setLoadingInitial] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')
  const mountedRef = useRef(true)
  const requestIdRef = useRef(0)

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      requestIdRef.current += 1
    }
  }, [])

  const loadInitial = useCallback(async () => {
    const requestId = requestIdRef.current + 1
    requestIdRef.current = requestId
    setLoadingInitial(true)
    setLoadingMore(false)
    setError('')
    setItems([])

    try {
      const page = normalizeCursorPage(await fetchPage(null))
      if (!mountedRef.current || requestId !== requestIdRef.current) return
      setItems(page.results)
      setNextCursor(page.next_cursor)
      setHasMore(page.has_more)
    } catch {
      if (!mountedRef.current || requestId !== requestIdRef.current) return
      setItems([])
      setNextCursor(null)
      setHasMore(false)
      setError(errorMessage)
    } finally {
      if (mountedRef.current && requestId === requestIdRef.current) {
        setLoadingInitial(false)
      }
    }
  }, [errorMessage, fetchPage])

  const loadMore = useCallback(async () => {
    if (loadingInitial || loadingMore || !hasMore || !nextCursor) return
    const requestId = requestIdRef.current + 1
    requestIdRef.current = requestId
    setLoadingMore(true)
    setError('')

    try {
      const page = normalizeCursorPage(await fetchPage(nextCursor))
      if (!mountedRef.current || requestId !== requestIdRef.current) return
      setItems((current) => mergeByKey(current, page.results, getItemKey))
      setNextCursor(page.next_cursor)
      setHasMore(page.has_more)
    } catch {
      if (!mountedRef.current || requestId !== requestIdRef.current) return
      setError(errorMessage)
    } finally {
      if (mountedRef.current && requestId === requestIdRef.current) {
        setLoadingMore(false)
      }
    }
  }, [errorMessage, fetchPage, getItemKey, hasMore, loadingInitial, loadingMore, nextCursor])

  useEffect(() => {
    if (!enabled) return
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadInitial()
    return () => {
      requestIdRef.current += 1
    }
  }, [enabled, loadInitial])

  return {
    items,
    setItems,
    loadingInitial,
    loadingMore,
    hasMore,
    error,
    refresh: loadInitial,
    loadMore,
  }
}
