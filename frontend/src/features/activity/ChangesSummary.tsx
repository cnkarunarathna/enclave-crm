import type { ActivityLog } from '@/api/types'

const FIELD_LABELS: Record<string, string> = {
  full_name: 'Full name',
  role: 'Job title',
  company: 'Company id',
}

const label = (field: string) =>
  FIELD_LABELS[field] ?? field.charAt(0).toUpperCase() + field.slice(1).replace(/_/g, ' ')

function display(field: string, value: unknown) {
  if (value === null || value === undefined) return '—'
  if (value === '') return '(empty)'
  // Logos are stored as storage keys (org-1/logos/ab12….png); the file name is enough.
  if (field === 'logo' && typeof value === 'string') return value.split('/').pop()
  return String(value)
}

/** Native <details> expander: "2 fields changed" → old → new per field. */
export function ChangesSummary({ log }: { log: ActivityLog }) {
  const entries = Object.entries(log.changes)
  if (entries.length === 0) {
    return (
      <span className="text-muted-foreground">{log.action === 'DELETE' ? '—' : 'No changes'}</span>
    )
  }

  const summary =
    log.action === 'CREATE'
      ? `${entries.length} field${entries.length === 1 ? '' : 's'} set`
      : `${entries.length} field${entries.length === 1 ? '' : 's'} changed`

  return (
    <details className="group text-sm">
      <summary className="text-primary cursor-pointer underline-offset-4 select-none hover:underline">
        {summary}
      </summary>
      <dl className="mt-2 grid gap-1.5">
        {entries.map(([field, change]) => (
          <div key={field} className="grid gap-0.5 sm:grid-cols-[8rem_1fr] sm:gap-2">
            <dt className="text-muted-foreground">{label(field)}</dt>
            <dd className="min-w-0 break-all">
              {log.action === 'UPDATE' && (
                <>
                  <span className="text-muted-foreground line-through">
                    {display(field, change.old)}
                  </span>
                  <span className="text-muted-foreground mx-1.5">→</span>
                </>
              )}
              <span>{display(field, change.new)}</span>
            </dd>
          </div>
        ))}
      </dl>
    </details>
  )
}
