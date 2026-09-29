import type { FieldValues, Path, UseFormSetError } from 'react-hook-form'

import { ApiError } from '@/api/errors'

/**
 * Put server validation errors next to the matching form fields.
 * Returns a message for anything that doesn't belong to a field (show it above the form).
 *
 *   catch (error) { setFormError(applyServerErrors(error, setError, ['name', 'email'])) }
 */
export function applyServerErrors<T extends FieldValues>(
  error: unknown,
  setError: UseFormSetError<T>,
  fields: readonly Path<T>[],
): string | null {
  if (!(error instanceof ApiError)) return 'Something went wrong. Please try again.'

  const unmatched: string[] = []
  for (const [field, messages] of Object.entries(error.fieldErrors)) {
    if ((fields as readonly string[]).includes(field)) {
      setError(field as Path<T>, { type: 'server', message: messages[0] })
    } else {
      unmatched.push(...messages)
    }
  }
  if (unmatched.length) return unmatched.join(' ')
  // Validation errors that all landed on fields need no banner.
  return Object.keys(error.fieldErrors).length ? null : error.message
}
