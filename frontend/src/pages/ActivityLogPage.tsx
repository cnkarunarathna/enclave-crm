import { History, SearchX } from 'lucide-react'

import type { ActivityLog } from '@/api/types'
import { EmptyState } from '@/components/common/EmptyState'
import { PageHeader } from '@/components/common/PageHeader'
import { DataTable, type Column } from '@/components/data/DataTable'
import { FilterSelect } from '@/components/data/FilterSelect'
import { Pagination } from '@/components/data/Pagination'
import { SearchInput } from '@/components/data/SearchInput'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ActionBadge } from '@/features/activity/ActionBadge'
import { ChangesSummary } from '@/features/activity/ChangesSummary'
import { useActivityLogs } from '@/hooks/useActivityLogs'
import { useListParams } from '@/hooks/useListParams'
import { formatDateTime } from '@/lib/format'

const MODEL_OPTIONS = [
  { value: 'Company', label: 'Companies' },
  { value: 'Contact', label: 'Contacts' },
]
const ACTION_OPTIONS = [
  { value: 'CREATE', label: 'Created' },
  { value: 'UPDATE', label: 'Updated' },
  { value: 'DELETE', label: 'Deleted' },
]
const FILTER_KEYS = [
  'search',
  'model_name',
  'action',
  'timestamp_after',
  'timestamp_before',
] as const

// Desktop: When | User | Action | Record | Changes.
// Phones: only "Record" is shown, and it carries everything else (a card-like row).
const columns: Column<ActivityLog>[] = [
  {
    header: 'When',
    className: 'hidden whitespace-nowrap sm:table-cell',
    cell: (log) => formatDateTime(log.timestamp),
  },
  {
    header: 'User',
    className: 'hidden md:table-cell',
    cell: (log) => (
      <div className="min-w-0">
        <p className="truncate">{log.user?.full_name ?? log.user_email}</p>
        {log.user && log.user.full_name !== log.user_email && (
          <p className="text-muted-foreground truncate text-xs">{log.user_email}</p>
        )}
      </div>
    ),
  },
  {
    header: 'Action',
    className: 'hidden sm:table-cell',
    cell: (log) => <ActionBadge action={log.action} />,
  },
  {
    header: 'Record',
    className: 'whitespace-normal',
    cell: (log) => (
      <div className="flex min-w-0 flex-col gap-0.5">
        <div className="flex items-center gap-2">
          <span className="sm:hidden">
            <ActionBadge action={log.action} />
          </span>
          <span className="font-medium wrap-break-word">{log.object_repr}</span>
        </div>
        <p className="text-muted-foreground text-xs">
          {log.model_name} #{log.object_id}
          <span className="sm:hidden"> · {formatDateTime(log.timestamp)}</span>
          <span className="md:hidden"> · {log.user?.full_name ?? log.user_email}</span>
        </p>
        <div className="mt-1 md:hidden">
          <ChangesSummary log={log} />
        </div>
      </div>
    ),
  },
  {
    header: 'Changes',
    className: 'hidden w-2/5 whitespace-normal md:table-cell',
    cell: (log) => <ChangesSummary log={log} />,
  },
]

export function ActivityLogPage() {
  const { values, page, setParam, setParams, setPage } = useListParams(FILTER_KEYS)
  const logs = useActivityLogs({ ...values, page })
  const hasFilters = FILTER_KEYS.some((key) => values[key])

  return (
    <>
      <PageHeader
        title="Activity log"
        description="Every create, update and delete of companies and contacts in your organization."
      />

      <div className="mb-4 flex flex-col gap-2 lg:flex-row lg:flex-wrap lg:items-end">
        <SearchInput
          value={values.search}
          onChange={(value) => setParam('search', value)}
          placeholder="Search record or user…"
          className="lg:w-64"
        />
        <div className="grid grid-cols-2 gap-2 sm:flex">
          <FilterSelect
            label="Record type"
            allLabel="All records"
            value={values.model_name}
            onChange={(value) => setParam('model_name', value)}
            options={MODEL_OPTIONS}
          />
          <FilterSelect
            label="Action"
            allLabel="All actions"
            value={values.action}
            onChange={(value) => setParam('action', value)}
            options={ACTION_OPTIONS}
          />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div className="grid gap-1">
            <Label htmlFor="log-from" className="text-muted-foreground text-xs">
              From
            </Label>
            <Input
              id="log-from"
              type="date"
              value={values.timestamp_after}
              max={values.timestamp_before || undefined}
              onChange={(event) => setParam('timestamp_after', event.target.value)}
            />
          </div>
          <div className="grid gap-1">
            <Label htmlFor="log-to" className="text-muted-foreground text-xs">
              To
            </Label>
            <Input
              id="log-to"
              type="date"
              value={values.timestamp_before}
              min={values.timestamp_after || undefined}
              onChange={(event) => setParam('timestamp_before', event.target.value)}
            />
          </div>
        </div>
        {hasFilters && (
          <Button
            variant="ghost"
            onClick={() => setParams(Object.fromEntries(FILTER_KEYS.map((key) => [key, ''])))}
          >
            Clear filters
          </Button>
        )}
      </div>

      <DataTable
        columns={columns}
        rows={logs.data?.data}
        rowKey={(log) => log.id}
        isLoading={logs.isPending}
        error={logs.error}
        onRetry={() => logs.refetch()}
        empty={
          hasFilters ? (
            <EmptyState icon={SearchX} title="No activity matches these filters" />
          ) : (
            <EmptyState
              icon={History}
              title="No activity yet"
              description="Changes to companies and contacts will be listed here."
            />
          )
        }
      />
      {logs.data && <Pagination meta={logs.data.meta} onPageChange={setPage} />}
    </>
  )
}
