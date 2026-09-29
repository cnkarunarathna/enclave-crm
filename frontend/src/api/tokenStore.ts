import type { Tokens } from './types'

/**
 * Where the JWTs live.
 * - Access token: in memory only, so an XSS script can't read it from storage later.
 * - Refresh token: localStorage, so a page reload can restore the session.
 * Production improvement: move the refresh token to an httpOnly cookie.
 */
const REFRESH_KEY = 'crm.refreshToken'

let accessToken: string | null = null

export const tokenStore = {
  getAccess: () => accessToken,

  getRefresh: () => {
    try {
      return localStorage.getItem(REFRESH_KEY)
    } catch {
      return null // storage blocked (e.g. some private modes)
    }
  },

  setTokens({ access, refresh }: Tokens) {
    accessToken = access
    try {
      localStorage.setItem(REFRESH_KEY, refresh)
    } catch {
      // Session still works until reload.
    }
  },

  clear() {
    accessToken = null
    try {
      localStorage.removeItem(REFRESH_KEY)
    } catch {
      // nothing to clear
    }
  },
}
