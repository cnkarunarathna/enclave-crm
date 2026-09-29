import { describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/errors'
import { checkLogoFile } from '@/features/companies/logoValidation'

import { applyServerErrors } from './forms'

describe('applyServerErrors', () => {
  it('puts field errors on their fields and needs no banner', () => {
    const setError = vi.fn()
    const error = new ApiError('Validation failed.', 400, 'validation_error', {
      email: ['A contact with this email already exists for this company.'],
    })

    const banner = applyServerErrors(error, setError, ['email', 'full_name'])

    expect(setError).toHaveBeenCalledWith('email', {
      type: 'server',
      message: 'A contact with this email already exists for this company.',
    })
    expect(banner).toBeNull()
  })

  it('returns errors for unknown fields as a banner message', () => {
    const setError = vi.fn()
    const error = new ApiError('Validation failed.', 400, 'validation_error', {
      remove_logo: ['Send a new logo or remove_logo, not both.'],
    })

    expect(applyServerErrors(error, setError, ['name'])).toBe(
      'Send a new logo or remove_logo, not both.',
    )
    expect(setError).not.toHaveBeenCalled()
  })

  it('uses the error message for non-validation errors', () => {
    const error = new ApiError('Not found.', 404, 'not_found')
    expect(applyServerErrors(error, vi.fn(), ['name'])).toBe('Not found.')
  })
})

describe('checkLogoFile', () => {
  const file = (type: string, bytes = 10) => new File([new Uint8Array(bytes)], 'logo', { type })

  it('accepts small JPEG, PNG and WebP images', () => {
    for (const type of ['image/jpeg', 'image/png', 'image/webp']) {
      expect(checkLogoFile(file(type))).toBeNull()
    }
  })

  it('rejects SVG and other types', () => {
    expect(checkLogoFile(file('image/svg+xml'))).toMatch(/JPEG, PNG or WebP/)
    expect(checkLogoFile(file('application/pdf'))).toMatch(/JPEG, PNG or WebP/)
  })

  it('rejects files over 2 MB', () => {
    expect(checkLogoFile(file('image/png', 2 * 1024 * 1024 + 1))).toMatch(/2 MB or smaller/)
  })
})
