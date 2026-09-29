import { Plus, SearchX, Users } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { ApiError } from '@/api/errors'
import type { Contact } from '@/api/types'
import { RoleGate } from '@/components/auth/RoleGate'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { EmptyState } from '@/components/common/EmptyState'
import { DataTable, type Column } from '@/components/data/DataTable'
import { Pagination } from '@/components/data/Pagination'
import { RowActions } from '@/components/data/RowActions'
import { SearchInput } from '@/components/data/SearchInput'
import { Button } from '@/components/ui/button'
import { Card, CardAction, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/hooks/useAuth'
import { useContacts, useDeleteContact } from '@/hooks/useContacts'
import { useListParams } from '@/hooks/useListParams'

import { ContactFormDialog } from './ContactFormDialog'

/** Contacts of one company: search, role filter, pagination and CRUD. State lives in the URL. */
export function ContactsSection({ companyId }: { companyId: number }) {
  const { can } = useAuth()
  const { values, page, setParam, setParams, setPage } = useListParams(['search', 'role'] as const)
  const contacts = useContacts({ company: companyId, ...values, page })
  const deleteContact = useDeleteContact()

  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Contact | undefined>()
  const [deleting, setDeleting] = useState<Contact | null>(null)

  const openForm = (contact?: Contact) => {
    setEditing(contact)
    setFormOpen(true)
  }

  const confirmDelete = async () => {
    if (!deleting) return
    try {
      await deleteContact.mutateAsync(deleting.id)
      toast.success(`${deleting.full_name} deleted.`)
      setDeleting(null)
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : 'Delete failed.')
    }
  }

  const columns: Column<Contact>[] = [
    {
      header: 'Name',
      cell: (contact) => (
        <div className="min-w-0">
          <p className="truncate font-medium">{contact.full_name}</p>
          {/* Email/role columns are hidden on phones: show them under the name instead. */}
          <p className="text-muted-foreground truncate text-xs md:hidden">{contact.email}</p>
          {contact.role && (
            <p className="text-muted-foreground truncate text-xs lg:hidden">{contact.role}</p>
          )}
        </div>
      ),
    },
    {
      header: 'Email',
      className: 'hidden md:table-cell',
      cell: (c) => (
        <a href={`mailto:${c.email}`} className="hover:underline">
          {c.email}
        </a>
      ),
    },
    {
      header: 'Phone',
      className: 'hidden sm:table-cell',
      cell: (c) => <span className="tabular-nums">{c.phone || '—'}</span>,
    },
    { header: 'Job title', className: 'hidden lg:table-cell', cell: (c) => c.role || '—' },
    {
      header: <span className="sr-only">Actions</span>,
      className: 'w-12 text-right',
      cell: (contact) => (
        <RowActions
          label={contact.full_name}
          onEdit={can('contact', 'update') ? () => openForm(contact) : undefined}
          onDelete={can('contact', 'delete') ? () => setDeleting(contact) : undefined}
        />
      ),
    },
  ]

  const hasFilters = Boolean(values.search || values.role)

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Contacts
          {contacts.data && (
            <span className="text-muted-foreground ml-2 text-sm font-normal">
              {contacts.data.meta.count}
            </span>
          )}
        </CardTitle>
        <CardAction>
          <RoleGate resource="contact" verb="create">
            <Button size="sm" onClick={() => openForm()}>
              <Plus />
              <span className="hidden sm:inline">Add contact</span>
              <span className="sm:hidden">Add</span>
            </Button>
          </RoleGate>
        </CardAction>
      </CardHeader>
      <CardContent>
        <div className="mb-4 flex flex-col gap-2 sm:flex-row">
          <SearchInput
            value={values.search}
            onChange={(value) => setParam('search', value)}
            placeholder="Search name, email, phone…"
            className="sm:w-72"
          />
          <SearchInput
            value={values.role}
            onChange={(value) => setParam('role', value)}
            placeholder="Filter by job title…"
            className="sm:w-56"
          />
        </div>

        <DataTable
          columns={columns}
          rows={contacts.data?.data}
          rowKey={(contact) => contact.id}
          isLoading={contacts.isPending}
          error={contacts.error}
          onRetry={() => contacts.refetch()}
          empty={
            hasFilters ? (
              <EmptyState
                icon={SearchX}
                title="No matching contacts"
                action={
                  <Button variant="outline" onClick={() => setParams({ search: '', role: '' })}>
                    Clear filters
                  </Button>
                }
              />
            ) : (
              <EmptyState
                icon={Users}
                title="No contacts yet"
                description="People you add to this company will appear here."
              />
            )
          }
        />
        {contacts.data && <Pagination meta={contacts.data.meta} onPageChange={setPage} />}
      </CardContent>

      {formOpen && (
        <ContactFormDialog
          open
          onOpenChange={setFormOpen}
          companyId={companyId}
          contact={editing}
        />
      )}
      <ConfirmDialog
        open={deleting !== null}
        onOpenChange={(open) => !open && setDeleting(null)}
        title={`Delete ${deleting?.full_name}?`}
        description="The contact will be removed. This is recorded in the activity log."
        confirmLabel="Delete contact"
        destructive
        pending={deleteContact.isPending}
        onConfirm={confirmDelete}
      />
    </Card>
  )
}
