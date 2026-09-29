import { LayoutDashboard } from 'lucide-react'

import { EmptyState } from '@/components/common/EmptyState'
import { PageHeader } from '@/components/common/PageHeader'
import { useAuth } from '@/hooks/useAuth'

// Placeholder: stat cards, industry bars and recent activity arrive in phase 7.
export function DashboardPage() {
  const { user } = useAuth()
  return (
    <>
      <PageHeader title="Dashboard" description={`Welcome back, ${user?.full_name}.`} />
      <EmptyState icon={LayoutDashboard} title="Dashboard coming soon" />
    </>
  )
}
