import { Building2 } from 'lucide-react'

import { EmptyState } from '@/components/common/EmptyState'
import { PageHeader } from '@/components/common/PageHeader'

// Placeholder: the companies table with search, filters and CRUD arrives in phase 7.
export function CompaniesPage() {
  return (
    <>
      <PageHeader title="Companies" />
      <EmptyState icon={Building2} title="Companies coming soon" />
    </>
  )
}
