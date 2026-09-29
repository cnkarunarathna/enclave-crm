import { createContext } from 'react'

import type { Resource, User, Verb } from '@/api/types'

export type AuthStatus = 'loading' | 'authenticated' | 'anonymous'

export interface AuthContextValue {
  status: AuthStatus
  user: User | null
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  /** UI convenience only: the backend enforces permissions regardless. */
  can: (resource: Resource, verb: Verb) => boolean
}

export const AuthContext = createContext<AuthContextValue | null>(null)
