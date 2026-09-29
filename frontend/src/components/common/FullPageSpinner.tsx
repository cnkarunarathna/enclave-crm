import { Spinner } from '@/components/ui/spinner'

/** Shown while the session is being restored on page load. */
export function FullPageSpinner({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex min-h-svh items-center justify-center">
      {/* Spinner already has role="status"; the label is what screen readers announce. */}
      <Spinner className="size-6" aria-label={label} />
    </div>
  )
}
