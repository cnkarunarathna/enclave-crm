import { zodResolver } from '@hookform/resolvers/zod'
import { AlertCircle } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { z } from 'zod'

import type { Contact } from '@/api/types'
import { FormField } from '@/components/common/FormField'
import { Modal } from '@/components/common/Modal'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Spinner } from '@/components/ui/spinner'
import { useCreateContact, useUpdateContact } from '@/hooks/useContacts'
import { applyServerErrors } from '@/lib/forms'

// Mirrors the API's rules. Uniqueness per company is checked by the server.
const contactSchema = z.object({
  full_name: z.string().trim().min(1, 'Full name is required.').max(200, 'Max 200 characters.'),
  email: z.email('Enter a valid email address.'),
  phone: z
    .string()
    .trim()
    .refine(
      (value) => value === '' || /^\d{8,15}$/.test(value.replace(/\s/g, '')),
      'Phone must be 8–15 digits.',
    ),
  role: z.string().trim().max(100, 'Max 100 characters.'),
})
type ContactValues = z.infer<typeof contactSchema>
const FIELDS = ['full_name', 'email', 'phone', 'role'] as const

interface ContactFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  companyId: number
  /** Edit this contact; omit to create one for `companyId`. */
  contact?: Contact
}

export function ContactFormDialog({
  open,
  onOpenChange,
  companyId,
  contact,
}: ContactFormDialogProps) {
  const isEdit = contact !== undefined
  const createContact = useCreateContact()
  const updateContact = useUpdateContact()
  const [formError, setFormError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<ContactValues>({
    resolver: zodResolver(contactSchema),
    defaultValues: {
      full_name: contact?.full_name ?? '',
      email: contact?.email ?? '',
      phone: contact?.phone ?? '',
      role: contact?.role ?? '',
    },
  })

  const onSubmit = async (values: ContactValues) => {
    setFormError(null)
    try {
      if (isEdit) {
        await updateContact.mutateAsync({ id: contact.id, input: values })
      } else {
        await createContact.mutateAsync({ ...values, company: companyId })
      }
      toast.success(isEdit ? 'Contact updated.' : 'Contact added.')
      onOpenChange(false)
    } catch (error) {
      // e.g. "A contact with this email already exists for this company." under Email.
      setFormError(applyServerErrors(error, setError, FIELDS))
    }
  }

  return (
    <Modal
      open={open}
      onOpenChange={(next) => !isSubmitting && onOpenChange(next)}
      title={isEdit ? 'Edit contact' : 'Add contact'}
      footer={
        <>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button type="submit" form="contact-form" disabled={isSubmitting}>
            {isSubmitting && <Spinner />}
            {isEdit ? 'Save changes' : 'Add contact'}
          </Button>
        </>
      }
    >
      <form
        id="contact-form"
        onSubmit={handleSubmit(onSubmit)}
        noValidate
        className="flex flex-col gap-4"
      >
        {formError && (
          <Alert variant="destructive">
            <AlertCircle />
            <AlertDescription>{formError}</AlertDescription>
          </Alert>
        )}
        <FormField
          label="Full name"
          htmlFor="contact-name"
          error={errors.full_name?.message}
          required
        >
          <Input id="contact-name" aria-invalid={!!errors.full_name} {...register('full_name')} />
        </FormField>
        <FormField label="Email" htmlFor="contact-email" error={errors.email?.message} required>
          <Input
            id="contact-email"
            type="email"
            aria-invalid={!!errors.email}
            {...register('email')}
          />
        </FormField>
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField
            label="Phone"
            htmlFor="contact-phone"
            error={errors.phone?.message}
            description="8–15 digits, spaces allowed."
          >
            <Input
              id="contact-phone"
              type="tel"
              inputMode="tel"
              aria-invalid={!!errors.phone}
              {...register('phone')}
            />
          </FormField>
          <FormField label="Job title" htmlFor="contact-role" error={errors.role?.message}>
            <Input
              id="contact-role"
              placeholder="e.g. Sales Manager"
              aria-invalid={!!errors.role}
              {...register('role')}
            />
          </FormField>
        </div>
      </form>
    </Modal>
  )
}
