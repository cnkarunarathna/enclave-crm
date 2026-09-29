import type { QueryClient } from '@tanstack/react-query'

import type { ListParams } from '@/api/types'

/** Every TanStack Query key in one place, so invalidation can't drift from the queries. */
export const queryKeys = {
  companies: (params?: ListParams) => (params ? ['companies', params] : ['companies']),
  companyFacets: () => ['companies', 'facets'],
  company: (id?: number) => (id === undefined ? ['company'] : ['company', id]),
  contacts: (params?: ListParams) => (params ? ['contacts', params] : ['contacts']),
  activityLogs: (params?: ListParams) => (params ? ['activity-logs', params] : ['activity-logs']),
  dashboard: () => ['dashboard'],
}

/** Every write shows up in the audit log and the dashboard numbers. */
export function invalidateAfterWrite(queryClient: QueryClient) {
  queryClient.invalidateQueries({ queryKey: queryKeys.activityLogs() })
  queryClient.invalidateQueries({ queryKey: queryKeys.dashboard() })
}
