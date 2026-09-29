import type { Action } from '@/api/types'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

const STYLES: Record<Action, string> = {
  CREATE: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  UPDATE: 'border-sky-200 bg-sky-50 text-sky-700',
  DELETE: 'border-red-200 bg-red-50 text-red-700',
}
const LABELS: Record<Action, string> = { CREATE: 'Created', UPDATE: 'Updated', DELETE: 'Deleted' }

export function ActionBadge({ action }: { action: Action }) {
  return (
    <Badge variant="outline" className={cn('font-medium', STYLES[action])}>
      {LABELS[action]}
    </Badge>
  )
}
