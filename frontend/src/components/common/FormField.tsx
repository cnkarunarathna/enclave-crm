import type { ReactNode } from 'react'

import { Field, FieldDescription, FieldError, FieldLabel } from '@/components/ui/field'

interface FormFieldProps {
  label: string
  /** Must match the input's id so clicking the label focuses it. */
  htmlFor: string
  /** Client (zod) or server (ApiError.fieldErrors) message. */
  error?: string
  description?: string
  required?: boolean
  children: ReactNode
}

/** Label + input + help text + error, with the right aria wiring. */
export function FormField({
  label,
  htmlFor,
  error,
  description,
  required,
  children,
}: FormFieldProps) {
  return (
    <Field data-invalid={error ? true : undefined}>
      <FieldLabel htmlFor={htmlFor}>
        {label}
        {required && <span className="text-destructive">*</span>}
      </FieldLabel>
      {children}
      {description && !error && <FieldDescription>{description}</FieldDescription>}
      {error && <FieldError id={`${htmlFor}-error`}>{error}</FieldError>}
    </Field>
  )
}
