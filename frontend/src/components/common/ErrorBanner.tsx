import { AlertCircle, RotateCw } from 'lucide-react'

import { ApiError } from '@/api/errors'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'

interface ErrorBannerProps {
  error: unknown
  title?: string
  onRetry?: () => void
}

export function ErrorBanner({ error, title = 'Something went wrong', onRetry }: ErrorBannerProps) {
  const message = error instanceof ApiError ? error.message : 'Unexpected error. Please try again.'
  return (
    <Alert variant="destructive">
      <AlertCircle />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription>
        <p>{message}</p>
        {onRetry && (
          <Button variant="outline" size="sm" className="mt-2" onClick={onRetry}>
            <RotateCw />
            Retry
          </Button>
        )}
      </AlertDescription>
    </Alert>
  )
}
