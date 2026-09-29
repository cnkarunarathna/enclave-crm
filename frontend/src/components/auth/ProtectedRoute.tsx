import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'

import { FullPageSpinner } from '@/components/common/FullPageSpinner'
import { useAuth } from '@/hooks/useAuth'

/** Signed-in users only. Others go to /login, which sends them back here afterwards. */
export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { status } = useAuth()
  const location = useLocation()

  if (status === 'loading') return <FullPageSpinner label="Restoring your session…" />
  if (status === 'anonymous') {
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  return <>{children}</>
}
