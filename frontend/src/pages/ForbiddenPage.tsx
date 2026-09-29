import { ShieldAlert } from 'lucide-react'
import { Link } from 'react-router-dom'

import { EmptyState } from '@/components/common/EmptyState'
import { Button } from '@/components/ui/button'

/** Shown when the route exists but the role can't use it (e.g. Staff -> Activity log). */
export function ForbiddenPage() {
  return (
    <div className="flex min-h-[60svh] items-center justify-center">
      <EmptyState
        icon={ShieldAlert}
        title="You don't have access to this page"
        description="Ask an administrator in your organization if you need access."
        action={
          <Button asChild variant="outline">
            <Link to="/">Back to dashboard</Link>
          </Button>
        }
      />
    </div>
  )
}
