import { History } from 'lucide-react'

import { EmptyState } from '@/components/common/EmptyState'
import { PageHeader } from '@/components/common/PageHeader'

// Placeholder: the audit table with filters arrives in phase 7.
export function ActivityLogPage() {
  return (
    <>
      <PageHeader title="Activity log" />
      <EmptyState icon={History} title="Activity log coming soon" />
    </>
  )
}
