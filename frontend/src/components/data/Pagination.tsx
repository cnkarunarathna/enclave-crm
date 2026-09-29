import { ChevronLeft, ChevronRight } from 'lucide-react'

import type { PageMeta } from '@/api/types'
import { Button } from '@/components/ui/button'

interface PaginationProps {
  meta: PageMeta
  onPageChange: (page: number) => void
}

/** "Showing 11–20 of 42" + Previous/Next. Hidden when everything fits on one page. */
export function Pagination({ meta, onPageChange }: PaginationProps) {
  const { count, page, page_size: pageSize, total_pages: totalPages } = meta
  if (totalPages <= 1) return null

  const first = (page - 1) * pageSize + 1
  const last = Math.min(page * pageSize, count)

  return (
    <nav
      aria-label="Pagination"
      className="flex flex-col items-center justify-between gap-3 pt-4 sm:flex-row"
    >
      <p className="text-muted-foreground text-sm">
        Showing <span className="text-foreground font-medium">{first}</span>–
        <span className="text-foreground font-medium">{last}</span> of{' '}
        <span className="text-foreground font-medium">{count}</span>
      </p>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
        >
          <ChevronLeft />
          Previous
        </Button>
        <span className="text-muted-foreground px-1 text-sm tabular-nums">
          {page} / {totalPages}
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
        >
          Next
          <ChevronRight />
        </Button>
      </div>
    </nav>
  )
}
