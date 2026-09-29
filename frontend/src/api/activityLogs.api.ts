import { api, cleanParams, getPage } from './client'
import type { ActivityLog, ListParams } from './types'

export const activityLogsApi = {
  list: (params: ListParams) =>
    getPage<ActivityLog>(api.get('/activity-logs/', { params: cleanParams(params) })),
}
