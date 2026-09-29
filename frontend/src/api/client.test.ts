import { AxiosError, type AxiosAdapter, type InternalAxiosRequestConfig } from 'axios'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { onSessionExpired } from './authEvents'
import { api } from './client'
import { ApiError } from './errors'
import { tokenStore } from './tokenStore'

/** Fake server: only accepts `Bearer fresh`, and counts refresh calls. */
function fakeServer({ refreshSucceeds = true } = {}) {
  const calls = { refresh: 0 }

  const reject = (config: InternalAxiosRequestConfig, status: number, body: object) => {
    const response = { status, statusText: '', headers: {}, config, data: body }
    throw new AxiosError(`HTTP ${status}`, 'ERR_BAD_REQUEST', config, null, response)
  }

  const adapter: AxiosAdapter = async (config) => {
    if (config.url === '/auth/refresh/') {
      calls.refresh += 1
      await new Promise((resolve) => setTimeout(resolve, 10)) // let parallel 401s pile up
      if (!refreshSucceeds) {
        reject(config, 401, {
          success: false,
          message: 'Token is blacklisted',
          code: 'not_authenticated',
          errors: null,
        })
      }
      const data = { success: true, message: '', data: { access: 'fresh', refresh: 'rotated' } }
      return { status: 200, statusText: 'OK', headers: {}, config, data }
    }
    if (config.headers.Authorization !== 'Bearer fresh') {
      reject(config, 401, {
        success: false,
        message: 'Token expired',
        code: 'not_authenticated',
        errors: null,
      })
    }
    const data = { success: true, message: '', data: { ok: true } }
    return { status: 200, statusText: 'OK', headers: {}, config, data }
  }

  return { adapter, calls }
}

describe('api client token refresh', () => {
  const originalAdapter = api.defaults.adapter

  beforeEach(() => {
    tokenStore.setTokens({ access: 'expired', refresh: 'original' })
  })

  afterEach(() => {
    api.defaults.adapter = originalAdapter
    tokenStore.clear()
  })

  it('refreshes once for many parallel 401s, then retries every request', async () => {
    const server = fakeServer()
    api.defaults.adapter = server.adapter

    const responses = await Promise.all([
      api.get('/companies/'),
      api.get('/contacts/'),
      api.get('/dashboard/stats/'),
    ])

    expect(responses.map((res) => res.data.data.ok)).toEqual([true, true, true])
    expect(server.calls.refresh).toBe(1)
    expect(tokenStore.getAccess()).toBe('fresh')
    expect(tokenStore.getRefresh()).toBe('rotated') // rotated token is stored
  })

  it('ends the session when the refresh token is rejected', async () => {
    api.defaults.adapter = fakeServer({ refreshSucceeds: false }).adapter
    const expired = vi.fn()
    const unsubscribe = onSessionExpired(expired)

    await expect(api.get('/companies/')).rejects.toBeInstanceOf(ApiError)

    expect(expired).toHaveBeenCalledOnce()
    expect(tokenStore.getAccess()).toBeNull()
    expect(tokenStore.getRefresh()).toBeNull()
    unsubscribe()
  })

  it('never refreshes for a failed login', async () => {
    const server = fakeServer()
    api.defaults.adapter = server.adapter

    await expect(api.post('/auth/login/', {})).rejects.toMatchObject({ status: 401 })
    expect(server.calls.refresh).toBe(0)
  })
})
