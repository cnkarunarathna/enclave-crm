import { Building2, Plus, SearchX } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'

import { ApiError } from '@/api/errors'
import type { Company } from '@/api/types'
import { RoleGate } from '@/components/auth/RoleGate'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { EmptyState } from '@/components/common/EmptyState'
import { PageHeader } from '@/components/common/PageHeader'
import { DataTable, type Column } from '@/components/data/DataTable'
import { FilterSelect } from '@/components/data/FilterSelect'
import { Pagination } from '@/components/data/Pagination'
import { RowActions } from '@/components/data/RowActions'
import { SearchInput } from '@/components/data/SearchInput'
import { Button } from '@/components/ui/button'
import { CompanyFormDialog } from '@/features/companies/CompanyFormDialog'
import { CompanyLogo } from '@/features/companies/CompanyLogo'
import { useAuth } from '@/hooks/useAuth'
import { useCompanies, useCompanyFacets, useDeleteCompany } from '@/hooks/useCompanies'
import { useListParams } from '@/hooks/useListParams'
import { formatDate } from '@/lib/format'

const ORDERING_OPTIONS = [
  { value: '-created_at', label: 'Newest first' },
  { value: 'created_at', label: 'Oldest first' },
  { value: 'name', label: 'Name A–Z' },
  { value: '-name', label: 'Name Z–A' },
]

const toOptions = (values: string[] = []) => values.map((value) => ({ value, label: value }))

export function CompaniesPage() {
  const { can } = useAuth()
  const { values, page, setParam, setParams, setPage } = useListParams([
    'search',
    'industry',
    'country',
    'ordering',
  ] as const)
  const ordering = values.ordering || '-created_at'
  const companies = useCompanies({ ...values, ordering, page })
  const facets = useCompanyFacets()
  const deleteCompany = useDeleteCompany()

  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Company | undefined>()
  const [deleting, setDeleting] = useState<Company | null>(null)

  const hasFilters = Boolean(values.search || values.industry || values.country)
  const clearFilters = () => setParams({ search: '', industry: '', country: '' })

  const openForm = (company?: Company) => {
    setEditing(company)
    setFormOpen(true)
  }

  const confirmDelete = async () => {
    if (!deleting) return
    try {
      await deleteCompany.mutateAsync(deleting.id)
      toast.success(`${deleting.name} deleted.`)
      setDeleting(null)
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : 'Delete failed.')
    }
  }

  const columns: Column<Company>[] = [
    {
      header: 'Company',
      cell: (company) => (
        <div className="flex min-w-0 items-center gap-3">
          <CompanyLogo name={company.name} url={company.logo_url} />
          <div className="min-w-0">
            <Link
              to={`/companies/${company.id}`}
              className="block truncate font-medium hover:underline"
            >
              {company.name}
            </Link>
            {/* On phones the industry/country columns are hidden, so show them here. */}
            <p className="text-muted-foreground truncate text-xs md:hidden">
              {[company.industry, company.country].filter(Boolean).join(' · ') || '—'}
            </p>
          </div>
        </div>
      ),
    },
    {
      header: 'Industry',
      className: 'hidden md:table-cell',
      cell: (c) => c.industry || '—',
    },
    { header: 'Country', className: 'hidden md:table-cell', cell: (c) => c.country || '—' },
    {
      header: 'Contacts',
      className: 'hidden text-right sm:table-cell',
      cell: (c) => <span className="tabular-nums">{c.contacts_count}</span>,
    },
    {
      header: 'Created',
      className: 'hidden lg:table-cell',
      cell: (c) => formatDate(c.created_at),
    },
    {
      header: <span className="sr-only">Actions</span>,
      className: 'w-12 text-right',
      cell: (company) => (
        <RowActions
          label={company.name}
          onEdit={can('company', 'update') ? () => openForm(company) : undefined}
          onDelete={can('company', 'delete') ? () => setDeleting(company) : undefined}
        />
      ),
    },
  ]

  return (
    <>
      <PageHeader
        title="Companies"
        description="Companies your organization works with."
        actions={
          <RoleGate resource="company" verb="create">
            <Button onClick={() => openForm()}>
              <Plus />
              New company
            </Button>
          </RoleGate>
        }
      />

      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
        <SearchInput
          value={values.search}
          onChange={(value) => setParam('search', value)}
          placeholder="Search companies…"
          className="sm:w-64"
        />
        <FilterSelect
          label="Industry"
          allLabel="All industries"
          value={values.industry}
          onChange={(value) => setParam('industry', value)}
          options={toOptions(facets.data?.industries)}
        />
        <FilterSelect
          label="Country"
          allLabel="All countries"
          value={values.country}
          onChange={(value) => setParam('country', value)}
          options={toOptions(facets.data?.countries)}
        />
        <FilterSelect
          label="Sort by"
          value={ordering}
          onChange={(value) => setParam('ordering', value === '-created_at' ? '' : value)}
          options={ORDERING_OPTIONS}
          className="sm:ml-auto"
        />
      </div>

      <DataTable
        columns={columns}
        rows={companies.data?.data}
        rowKey={(company) => company.id}
        isLoading={companies.isPending}
        error={companies.error}
        onRetry={() => companies.refetch()}
        empty={
          hasFilters ? (
            <EmptyState
              icon={SearchX}
              title="No matching companies"
              description="Try a different search or clear the filters."
              action={
                <Button variant="outline" onClick={clearFilters}>
                  Clear filters
                </Button>
              }
            />
          ) : (
            <EmptyState
              icon={Building2}
              title="No companies yet"
              description="Companies you add will appear here."
              action={
                <RoleGate resource="company" verb="create">
                  <Button onClick={() => openForm()}>
                    <Plus />
                    New company
                  </Button>
                </RoleGate>
              }
            />
          )
        }
      />
      {companies.data && <Pagination meta={companies.data.meta} onPageChange={setPage} />}

      {formOpen && <CompanyFormDialog open onOpenChange={setFormOpen} company={editing} />}
      <ConfirmDialog
        open={deleting !== null}
        onOpenChange={(open) => !open && setDeleting(null)}
        title={`Delete ${deleting?.name}?`}
        description="The company and all of its contacts will be removed. This is recorded in the activity log."
        confirmLabel="Delete company"
        destructive
        pending={deleteCompany.isPending}
        onConfirm={confirmDelete}
      />
    </>
  )
}
