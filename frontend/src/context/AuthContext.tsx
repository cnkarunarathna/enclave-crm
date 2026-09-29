import { useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { toast } from 'sonner'

import { authApi } from '@/api/auth.api'
import { onSessionExpired } from '@/api/authEvents'
import { refreshAccessToken } from '@/api/client'
import { tokenStore } from '@/api/tokenStore'
import type { Resource, User, Verb } from '@/api/types'

import { AuthContext, type AuthStatus } from './auth-context'

/** On page load: a stored refresh token -> new access token -> current user. */
async function restoreSession(): Promise<User | null> {
  if (!tokenStore.getRefresh()) return null
  try {
    await refreshAccessToken()
    return await authApi.me()
  } catch {
    tokenStore.clear()
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [status, setStatus] = useState<AuthStatus>('loading')
  const [user, setUser] = useState<User | null>(null)

  const signOutLocally = useCallback(() => {
    tokenStore.clear()
    queryClient.clear() // never show the previous user's cached data
    setUser(null)
    setStatus('anonymous')
  }, [queryClient])

  useEffect(() => {
    let cancelled = false
    restoreSession().then((restored) => {
      if (cancelled) return
      setUser(restored)
      setStatus(restored ? 'authenticated' : 'anonymous')
    })
    return () => {
      cancelled = true
    }
  }, [])

  // The API client fires this when a refresh fails (expired or revoked session).
  useEffect(
    () =>
      onSessionExpired(() => {
        signOutLocally()
        toast.error('Your session has expired. Please sign in again.')
      }),
    [signOutLocally],
  )

  const login = useCallback(async (email: string, password: string) => {
    const { access, refresh, user: loggedIn } = await authApi.login(email, password)
    tokenStore.setTokens({ access, refresh })
    setUser(loggedIn)
    setStatus('authenticated')
  }, [])

  const logout = useCallback(async () => {
    const refresh = tokenStore.getRefresh()
    try {
      if (refresh) await authApi.logout(refresh) // revoke server-side
    } catch {
      // Already invalid or offline: signing out locally is still correct.
    } finally {
      signOutLocally()
    }
  }, [signOutLocally])

  const can = useCallback(
    (resource: Resource, verb: Verb) => user?.capabilities[resource]?.[verb] === true,
    [user],
  )

  const value = useMemo(
    () => ({ status, user, login, logout, can }),
    [status, user, login, logout, can],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
