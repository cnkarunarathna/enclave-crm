import { zodResolver } from '@hookform/resolvers/zod'
import { AlertCircle, ImageUp, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { z } from 'zod'

import type { Company } from '@/api/types'
import { FormField } from '@/components/common/FormField'
import { Modal } from '@/components/common/Modal'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Spinner } from '@/components/ui/spinner'
import { useCreateCompany, useUpdateCompany } from '@/hooks/useCompanies'
import { applyServerErrors } from '@/lib/forms'

import { CompanyLogo } from './CompanyLogo'
import { checkLogoFile, LOGO_ACCEPT, MAX_LOGO_MB } from './logoValidation'

const companySchema = z.object({
  name: z.string().trim().min(1, 'Name is required.').max(200, 'Max 200 characters.'),
  industry: z.string().trim().max(100, 'Max 100 characters.'),
  country: z.string().trim().max(100, 'Max 100 characters.'),
  // The file itself is kept in component state; this entry only carries logo errors.
  logo: z.unknown().optional(),
})
type CompanyValues = z.infer<typeof companySchema>

interface CompanyFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Edit this company; omit to create a new one. */
  company?: Company
  onSaved?: (company: Company) => void
}

/** Create/edit form. Render it only while open, so every opening starts fresh. */
export function CompanyFormDialog({
  open,
  onOpenChange,
  company,
  onSaved,
}: CompanyFormDialogProps) {
  const isEdit = company !== undefined
  const createCompany = useCreateCompany()
  const updateCompany = useUpdateCompany()

  const {
    register,
    handleSubmit,
    setError,
    clearErrors,
    formState: { errors, isSubmitting },
  } = useForm<CompanyValues>({
    resolver: zodResolver(companySchema),
    defaultValues: {
      name: company?.name ?? '',
      industry: company?.industry ?? '',
      country: company?.country ?? '',
    },
  })

  const [newLogo, setNewLogo] = useState<{ file: File; previewUrl: string } | null>(null)
  const [removeLogo, setRemoveLogo] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  // Free the preview's memory when it is replaced or the dialog closes.
  const previewUrlRef = useRef<string | null>(null)
  useEffect(() => () => revokePreview(previewUrlRef), [])

  const chooseLogo = (file: File | null) => {
    revokePreview(previewUrlRef)
    if (!file) return setNewLogo(null)
    previewUrlRef.current = URL.createObjectURL(file)
    setNewLogo({ file, previewUrl: previewUrlRef.current })
  }

  const shownLogo = newLogo?.previewUrl ?? (removeLogo ? null : (company?.logo_url ?? null))

  const onPickFile = (file: File | undefined) => {
    if (!file) return
    const problem = checkLogoFile(file)
    if (problem) return setError('logo', { type: 'client', message: problem })
    clearErrors('logo')
    chooseLogo(file)
    setRemoveLogo(false)
  }

  const onSubmit = async ({ name, industry, country }: CompanyValues) => {
    setFormError(null)
    const logo = newLogo?.file ?? null
    try {
      const saved = isEdit
        ? await updateCompany.mutateAsync({
            id: company.id,
            input: { name, industry, country, logo, remove_logo: removeLogo || undefined },
          })
        : await createCompany.mutateAsync({ name, industry, country, logo })
      toast.success(isEdit ? 'Company updated.' : 'Company created.')
      onSaved?.(saved)
      onOpenChange(false)
    } catch (error) {
      setFormError(applyServerErrors(error, setError, ['name', 'industry', 'country', 'logo']))
    }
  }

  return (
    <Modal
      open={open}
      onOpenChange={(next) => !isSubmitting && onOpenChange(next)}
      title={isEdit ? 'Edit company' : 'New company'}
      description={isEdit ? `Update ${company.name}.` : 'Add a company to your organization.'}
      footer={
        <>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button type="submit" form="company-form" disabled={isSubmitting}>
            {isSubmitting && <Spinner />}
            {isEdit ? 'Save changes' : 'Create company'}
          </Button>
        </>
      }
    >
      <form
        id="company-form"
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
        <FormField label="Name" htmlFor="company-name" error={errors.name?.message} required>
          <Input id="company-name" aria-invalid={!!errors.name} {...register('name')} />
        </FormField>
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField label="Industry" htmlFor="company-industry" error={errors.industry?.message}>
            <Input
              id="company-industry"
              placeholder="e.g. Hospitality"
              aria-invalid={!!errors.industry}
              {...register('industry')}
            />
          </FormField>
          <FormField label="Country" htmlFor="company-country" error={errors.country?.message}>
            <Input
              id="company-country"
              placeholder="e.g. Sri Lanka"
              aria-invalid={!!errors.country}
              {...register('country')}
            />
          </FormField>
        </div>

        <FormField
          label="Logo"
          htmlFor="company-logo"
          error={errors.logo?.message}
          description={`JPEG, PNG or WebP, up to ${MAX_LOGO_MB} MB.`}
        >
          <div className="flex items-center gap-3">
            <CompanyLogo
              name={company?.name || 'New company'}
              url={shownLogo}
              className="size-14"
            />
            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="outline" size="sm" asChild>
                <label htmlFor="company-logo" className="cursor-pointer">
                  <ImageUp />
                  {shownLogo ? 'Replace' : 'Upload'}
                </label>
              </Button>
              {shownLogo && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    chooseLogo(null)
                    setRemoveLogo(isEdit && company.logo_url !== null)
                  }}
                >
                  <X />
                  Remove
                </Button>
              )}
            </div>
            <input
              id="company-logo"
              type="file"
              accept={LOGO_ACCEPT}
              className="sr-only"
              aria-invalid={!!errors.logo}
              onChange={(event) => {
                onPickFile(event.target.files?.[0])
                event.target.value = '' // allow picking the same file again
              }}
            />
          </div>
        </FormField>
      </form>
    </Modal>
  )
}

function revokePreview(ref: { current: string | null }) {
  if (ref.current) URL.revokeObjectURL(ref.current)
  ref.current = null
}
