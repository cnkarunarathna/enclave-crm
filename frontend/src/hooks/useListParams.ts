import { useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'

/**
 * List state (page, search, filters, ordering) lives in the URL query string,
 * so reload, back/forward and shared links all keep the same view.
 *
 *   const { values, page, setParam, setPage } = useListParams(['search', 'industry'])
 */
export function useListParams<K extends string>(keys: readonly K[]) {
  const [searchParams, setSearchParams] = useSearchParams()

  const page = Math.max(1, Number(searchParams.get('page')) || 1)
  const values = Object.fromEntries(
    keys.map((key) => [key, searchParams.get(key) ?? '']),
  ) as Record<K, string>

  /** Changing any filter resets to page 1 (the old page may not exist any more). */
  const setParam = useCallback(
    (key: K, value: string) => {
      setSearchParams(
        (current) => {
          const next = new URLSearchParams(current)
          if (value) next.set(key, value)
          else next.delete(key)
          next.delete('page')
          return next
        },
        { replace: true },
      )
    },
    [setSearchParams],
  )

  const setPage = useCallback(
    (nextPage: number) => {
      setSearchParams((current) => {
        const next = new URLSearchParams(current)
        if (nextPage > 1) next.set('page', String(nextPage))
        else next.delete('page')
        return next
      })
    },
    [setSearchParams],
  )

  // TanStack Query compares query keys by value, so a fresh object each render is fine.
  return { values, page, params: { ...values, page }, setParam, setPage }
}
