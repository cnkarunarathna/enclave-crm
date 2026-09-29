import type { ReactNode } from 'react'
import { Navigate, useLocation, type Location } from 'react-router-dom'

import { FullPageSpinner } from '@/components/common/FullPageSpinner'
import { useAuth } from '@/hooks/useAuth'

/** The login page: already signed-in users are sent on to where they were going. */
export function PublicOnlyRoute({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const location = useLocation()
  const from = (location.state as { from?: Location } | null)?.from

  if (status === 'loading') return <FullPageSpinner />
  if (status === 'authenticated') {
    return <Navigate to={from ? `${from.pathname}${from.search}` : '/'} replace />
  }
  return <>{children}</>
}
