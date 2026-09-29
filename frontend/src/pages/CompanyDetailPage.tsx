import { Building2 } from 'lucide-react'
import { useParams } from 'react-router-dom'

import { EmptyState } from '@/components/common/EmptyState'
import { PageHeader } from '@/components/common/PageHeader'

// Placeholder: company header card and nested contacts arrive in phase 7.
export function CompanyDetailPage() {
  const { id } = useParams()
  return (
    <>
      <PageHeader title={`Company #${id}`} />
      <EmptyState icon={Building2} title="Company details coming soon" />
    </>
  )
}
