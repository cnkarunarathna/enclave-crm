import { useQuery } from '@tanstack/react-query'

import { dashboardApi } from '@/api/dashboard.api'

import { queryKeys } from './queryKeys'

export function useDashboard() {
  return useQuery({ queryKey: queryKeys.dashboard(), queryFn: dashboardApi.stats })
}
