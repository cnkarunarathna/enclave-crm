import { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { describe, expect, it } from 'vitest'

import { ApiError, toApiError } from './errors'

const config = { headers: {} } as InternalAxiosRequestConfig

describe('toApiError', () => {
  it('reads the error envelope, including field errors', () => {
    const response = {
      status: 400,
      statusText: '',
      headers: {},
      config,
      data: {
        success: false,
        message: 'Validation failed.',
        code: 'validation_error',
        errors: { email: ['A contact with this email already exists for this company.'] },
      },
    }

    const error = toApiError(new AxiosError('400', 'ERR_BAD_REQUEST', config, null, response))

    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(400)
    expect(error.code).toBe('validation_error')
    expect(error.fieldErrors.email[0]).toMatch(/already exists/)
  })

  it('explains network failures', () => {
    const error = toApiError(new AxiosError('Network Error', 'ERR_NETWORK', config))

    expect(error.status).toBe(0)
    expect(error.code).toBe('network_error')
  })
})
