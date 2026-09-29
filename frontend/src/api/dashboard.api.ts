import { api, getData } from './client'
import type { DashboardStats } from './types'

export const dashboardApi = {
  stats: () => getData<DashboardStats>(api.get('/dashboard/stats/')),
}
