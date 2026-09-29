import { FileQuestion } from 'lucide-react'
import { Link } from 'react-router-dom'

import { EmptyState } from '@/components/common/EmptyState'
import { Button } from '@/components/ui/button'

export function NotFoundPage() {
  return (
    <div className="flex min-h-[60svh] items-center justify-center px-4">
      <EmptyState
        icon={FileQuestion}
        title="Page not found"
        description="The page you're looking for doesn't exist or you don't have access to it."
        action={
          <Button asChild>
            <Link to="/">Go to dashboard</Link>
          </Button>
        }
      />
    </div>
  )
}
