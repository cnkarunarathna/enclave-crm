/**
 * The single axios instance. Only files in src/api/ import this.
 *
 * - Adds `Authorization: Bearer <access>` to every request.
 * - On a 401, refreshes the access token once and retries the request. Many
 *   parallel 401s share ONE refresh call (the refresh token rotates, so a second
 *   concurrent refresh would fail and log the user out).
 * - Converts every failure into an ApiError.
 */
import axios, { type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'

import { emitSessionExpired } from './authEvents'
import { ApiError, toApiError } from './errors'
import { tokenStore } from './tokenStore'
import type { Paginated, SuccessEnvelope, Tokens } from './types'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
})

api.interceptors.request.use((config) => {
  const access = tokenStore.getAccess()
  if (access) config.headers.Authorization = `Bearer ${access}`
  return config
})

// These endpoints are the auth flow itself; a 401 from them must not trigger a refresh.
const NO_REFRESH_URLS = ['/auth/login/', '/auth/refresh/']

let refreshPromise: Promise<string> | null = null

/** Get a new access token (single-flight). Rejects if there is no valid refresh token. */
export function refreshAccessToken(): Promise<string> {
  refreshPromise ??= (async () => {
    const refresh = tokenStore.getRefresh()
    if (!refresh) throw new ApiError('Not signed in.', 401, 'not_authenticated')
    const tokens = await getData<Tokens>(api.post('/auth/refresh/', { refresh }))
    tokenStore.setTokens(tokens) // the refresh token rotates: store the new one
    return tokens.access
  })().finally(() => {
    refreshPromise = null
  })
  return refreshPromise
}

type RetryableConfig = InternalAxiosRequestConfig & { _retry?: boolean }

api.interceptors.response.use(undefined, async (error) => {
  const original = error.config as RetryableConfig | undefined
  const canRefresh =
    error.response?.status === 401 &&
    original !== undefined &&
    !original._retry &&
    !NO_REFRESH_URLS.some((url) => original.url?.includes(url)) &&
    tokenStore.getRefresh() !== null

  if (canRefresh) {
    original._retry = true
    try {
      const access = await refreshAccessToken()
      original.headers.Authorization = `Bearer ${access}`
      return api(original)
    } catch {
      tokenStore.clear()
      emitSessionExpired() // AuthContext switches to anonymous -> /login
    }
  }
  return Promise.reject(toApiError(error))
})

// --- Envelope helpers: API modules return plain data, never axios responses ---

export async function getData<T>(request: Promise<AxiosResponse<SuccessEnvelope<T>>>) {
  return (await request).data.data
}

export async function getPage<T>(
  request: Promise<AxiosResponse<SuccessEnvelope<T[]>>>,
): Promise<Paginated<T>> {
  const body = (await request).data
  return { data: body.data, meta: body.meta! }
}

/** Drop empty filters so the URL stays clean (`?search=` is not sent). */
export function cleanParams(params: Record<string, string | number | undefined>) {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== ''),
  )
}
