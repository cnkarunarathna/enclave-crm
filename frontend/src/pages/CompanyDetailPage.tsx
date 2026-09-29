import { ArrowLeft, Building2, CalendarDays, Globe, Pencil, Trash2, Users } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { ApiError } from '@/api/errors'
import { RoleGate } from '@/components/auth/RoleGate'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorBanner } from '@/components/common/ErrorBanner'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { CompanyFormDialog } from '@/features/companies/CompanyFormDialog'
import { CompanyLogo } from '@/features/companies/CompanyLogo'
import { ContactsSection } from '@/features/contacts/ContactsSection'
import { useCompany, useDeleteCompany } from '@/hooks/useCompanies'
import { formatDate } from '@/lib/format'

export function CompanyDetailPage() {
  const companyId = Number(useParams().id)
  const navigate = useNavigate()
  const company = useCompany(companyId)
  const deleteCompany = useDeleteCompany()
  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)

  const backLink = (
    <Button variant="ghost" size="sm" asChild className="-ml-2 mb-4">
      <Link to="/companies">
        <ArrowLeft />
        Companies
      </Link>
    </Button>
  )

  // Another organization's company answers 404 too: we can't tell (or show) the difference.
  if (company.error instanceof ApiError && company.error.status === 404) {
    return (
      <>
        {backLink}
        <EmptyState
          icon={Building2}
          title="Company not found"
          description="It may have been deleted, or it doesn't belong to your organization."
        />
      </>
    )
  }
  if (company.error) {
    return (
      <>
        {backLink}
        <ErrorBanner error={company.error} onRetry={() => company.refetch()} />
      </>
    )
  }

  const confirmDelete = async () => {
    try {
      await deleteCompany.mutateAsync(companyId)
      toast.success(`${company.data?.name} deleted.`)
      navigate('/companies', { replace: true })
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : 'Delete failed.')
    }
  }

  const data = company.data
  return (
    <>
      {backLink}
      <Card className="mb-6">
        <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-start">
          {data ? (
            <CompanyLogo name={data.name} url={data.logo_url} className="size-16" />
          ) : (
            <Skeleton className="size-16 rounded-md" />
          )}
          <div className="min-w-0 flex-1">
            {data ? (
              <h1 className="text-2xl font-semibold tracking-tight wrap-break-word">{data.name}</h1>
            ) : (
              <Skeleton className="h-8 w-56" />
            )}
            <dl className="text-muted-foreground mt-3 grid gap-2 text-sm sm:grid-cols-2 lg:grid-cols-4">
              <Detail icon={<Building2 />} label="Industry" value={data?.industry} />
              <Detail icon={<Globe />} label="Country" value={data?.country} />
              <Detail
                icon={<Users />}
                label="Contacts"
                value={data ? String(data.contacts_count) : undefined}
              />
              <Detail
                icon={<CalendarDays />}
                label="Created"
                value={data ? formatDate(data.created_at) : undefined}
              />
            </dl>
          </div>
          {data && (
            <div className="flex gap-2">
              <RoleGate resource="company" verb="update">
                <Button variant="outline" onClick={() => setEditOpen(true)}>
                  <Pencil />
                  Edit
                </Button>
              </RoleGate>
              <RoleGate resource="company" verb="delete">
                <Button variant="destructive" onClick={() => setDeleteOpen(true)}>
                  <Trash2 />
                  Delete
                </Button>
              </RoleGate>
            </div>
          )}
        </CardContent>
      </Card>

      {Number.isFinite(companyId) && <ContactsSection companyId={companyId} />}

      {editOpen && data && <CompanyFormDialog open onOpenChange={setEditOpen} company={data} />}
      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title={`Delete ${data?.name}?`}
        description={`The company and its ${data?.contacts_count ?? 0} contact(s) will be removed. This is recorded in the activity log.`}
        confirmLabel="Delete company"
        destructive
        pending={deleteCompany.isPending}
        onConfirm={confirmDelete}
      />
    </>
  )
}

function Detail({ icon, label, value }: { icon: ReactNode; label: string; value?: string }) {
  return (
    <div className="flex items-center gap-2 [&_svg]:size-4 [&_svg]:shrink-0">
      {icon}
      <dt className="sr-only">{label}</dt>
      <dd className="text-foreground truncate">
        {value === undefined ? <Skeleton className="h-4 w-20" /> : value || '—'}
      </dd>
    </div>
  )
}
