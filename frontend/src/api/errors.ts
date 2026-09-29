import { isAxiosError } from 'axios'

import type { ErrorEnvelope } from './types'

/** The one error type the UI deals with, whatever went wrong. */
export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly fieldErrors: Record<string, string[]>

  constructor(
    message: string,
    status: number,
    code: string,
    fieldErrors: Record<string, string[]> = {},
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.fieldErrors = fieldErrors
  }
}

function isErrorEnvelope(body: unknown): body is ErrorEnvelope {
  return typeof body === 'object' && body !== null && (body as ErrorEnvelope).success === false
}

export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error

  if (isAxiosError(error)) {
    const status = error.response?.status ?? 0
    const body = error.response?.data
    if (isErrorEnvelope(body)) {
      return new ApiError(body.message, status, body.code, body.errors ?? {})
    }
    if (!error.response) {
      return new ApiError(
        "Can't reach the server. Check your connection and try again.",
        0,
        'network_error',
      )
    }
    return new ApiError('Something went wrong. Please try again.', status, 'unknown_error')
  }

  return new ApiError('Something went wrong. Please try again.', 0, 'unknown_error')
}
