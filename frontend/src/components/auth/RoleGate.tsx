import type { ReactNode } from 'react'

import type { Resource, Verb } from '@/api/types'
import { useAuth } from '@/hooks/useAuth'

interface RoleGateProps {
  resource: Resource
  verb: Verb
  children: ReactNode
  /** Rendered instead when not allowed (default: nothing). */
  fallback?: ReactNode
}

/**
 * <RoleGate resource="company" verb="delete"><DeleteButton /></RoleGate>
 *
 * Hides UI the role can't use. A courtesy only: the API enforces the same rules.
 */
export function RoleGate({ resource, verb, children, fallback = null }: RoleGateProps) {
  const { can } = useAuth()
  return <>{can(resource, verb) ? children : fallback}</>
}
