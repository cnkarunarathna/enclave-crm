import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { activityLogsApi } from '@/api/activityLogs.api'
import type { ListParams } from '@/api/types'

import { queryKeys } from './queryKeys'

export function useActivityLogs(params: ListParams) {
  return useQuery({
    queryKey: queryKeys.activityLogs(params),
    queryFn: () => activityLogsApi.list(params),
    placeholderData: keepPreviousData,
  })
}
