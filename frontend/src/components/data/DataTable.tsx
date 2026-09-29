import type { ReactNode } from 'react'

import { ErrorBanner } from '@/components/common/ErrorBanner'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { cn } from '@/lib/utils'

export interface Column<T> {
  header: ReactNode
  cell: (row: T) => ReactNode
  /**
   * Responsive visibility, e.g. "hidden md:table-cell" hides the column on phones.
   * Applied to both the header and the cells.
   */
  className?: string
}

interface DataTableProps<T> {
  columns: Column<T>[]
  rows: T[] | undefined
  rowKey: (row: T) => string | number
  isLoading: boolean
  error: unknown
  onRetry?: () => void
  /** Rendered when the request succeeded but returned no rows. */
  empty: ReactNode
}

/** Table with built-in loading (skeleton), error (banner + retry) and empty states. */
export function DataTable<T>({
  columns,
  rows,
  rowKey,
  isLoading,
  error,
  onRetry,
  empty,
}: DataTableProps<T>) {
  if (error) return <ErrorBanner error={error} onRetry={onRetry} />
  if (!isLoading && rows?.length === 0) return <>{empty}</>

  return (
    // Wide tables scroll sideways inside their card on small screens.
    <div className="bg-background overflow-x-auto rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((column, index) => (
              <TableHead key={index} className={column.className}>
                {column.header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading || !rows
            ? Array.from({ length: 5 }, (_, rowIndex) => (
                <TableRow key={rowIndex}>
                  {columns.map((column, index) => (
                    <TableCell key={index} className={column.className}>
                      <Skeleton className="h-5 w-full max-w-40" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            : rows.map((row) => (
                <TableRow key={rowKey(row)}>
                  {columns.map((column, index) => (
                    <TableCell key={index} className={cn('align-middle', column.className)}>
                      {column.cell(row)}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
        </TableBody>
      </Table>
    </div>
  )
}
