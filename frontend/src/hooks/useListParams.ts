import { useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'

/**
 * List state (page, search, filters, ordering) lives in the URL query string,
 * so reload, back/forward and shared links all keep the same view.
 *
 *   const { values, page, setParam, setParams, setPage } = useListParams(['search', 'industry'])
 */
export function useListParams<K extends string>(keys: readonly K[]) {
  const [searchParams, setSearchParams] = useSearchParams()

  const page = Math.max(1, Number(searchParams.get('page')) || 1)
  const values = Object.fromEntries(
    keys.map((key) => [key, searchParams.get(key) ?? '']),
  ) as Record<K, string>

  /**
   * Update one or more filters at once. Changing a filter resets to page 1 (the old
   * page may not exist any more). Use this for several keys: React Router does not
   * queue successive setSearchParams calls, so only the last of them would apply.
   */
  const setParams = useCallback(
    (updates: Partial<Record<K, string>>) => {
      setSearchParams(
        (current) => {
          const next = new URLSearchParams(current)
          for (const [key, value] of Object.entries(updates) as [K, string | undefined][]) {
            if (value) next.set(key, value)
            else next.delete(key)
          }
          next.delete('page')
          return next
        },
        { replace: true },
      )
    },
    [setSearchParams],
  )

  const setParam = useCallback(
    (key: K, value: string) => setParams({ [key]: value } as Partial<Record<K, string>>),
    [setParams],
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
  return { values, page, params: { ...values, page }, setParam, setParams, setPage }
}
