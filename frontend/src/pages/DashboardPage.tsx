import { ArrowRight, Building2, Crown, History, Users, type LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

import type { DashboardStats } from '@/api/types'
import { RoleGate } from '@/components/auth/RoleGate'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorBanner } from '@/components/common/ErrorBanner'
import { PageHeader } from '@/components/common/PageHeader'
import { Button } from '@/components/ui/button'
import { Card, CardAction, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { ActionBadge } from '@/features/activity/ActionBadge'
import { useAuth } from '@/hooks/useAuth'
import { useDashboard } from '@/hooks/useDashboard'
import { formatDateTime } from '@/lib/format'

export function DashboardPage() {
  const { user } = useAuth()
  const stats = useDashboard()

  return (
    <>
      <PageHeader
        title="Dashboard"
        description={`Welcome back, ${user?.full_name}. Here's ${user?.organization.name} at a glance.`}
      />

      {stats.error ? (
        <ErrorBanner error={stats.error} onRetry={() => stats.refetch()} />
      ) : (
        <div className="grid gap-4 lg:grid-cols-3">
          <StatCard icon={Building2} label="Companies" value={stats.data?.totals.companies} />
          <StatCard icon={Users} label="Contacts" value={stats.data?.totals.contacts} />
          <StatCard
            icon={Crown}
            label="Plan"
            value={stats.data?.organization.subscription_plan}
            className="sm:col-span-2 lg:col-span-1"
          />

          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle>Companies by industry</CardTitle>
            </CardHeader>
            <CardContent>
              <IndustryBars data={stats.data?.companies_by_industry} />
            </CardContent>
          </Card>

          <RoleGate resource="activity_log" verb="read">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Recent activity</CardTitle>
                <CardAction>
                  <Button variant="ghost" size="sm" asChild>
                    <Link to="/activity">
                      View all
                      <ArrowRight />
                    </Link>
                  </Button>
                </CardAction>
              </CardHeader>
              <CardContent>
                <RecentActivity logs={stats.data?.recent_activity} />
              </CardContent>
            </Card>
          </RoleGate>
        </div>
      )}
    </>
  )
}

function StatCard({
  icon: Icon,
  label,
  value,
  className,
}: {
  icon: LucideIcon
  label: string
  value?: ReactNode
  className?: string
}) {
  return (
    <Card className={className}>
      <CardContent className="flex items-center gap-4">
        <div className="bg-muted flex size-10 shrink-0 items-center justify-center rounded-md">
          <Icon className="size-5" />
        </div>
        <div>
          <p className="text-muted-foreground text-sm">{label}</p>
          {value === undefined ? (
            <Skeleton className="mt-1 h-7 w-16" />
          ) : (
            <p className="text-2xl font-semibold tabular-nums">{value}</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

/** Plain CSS bars: width relative to the biggest industry. */
function IndustryBars({ data }: { data?: DashboardStats['companies_by_industry'] }) {
  if (!data) {
    return (
      <div className="grid gap-3">
        {Array.from({ length: 4 }, (_, index) => (
          <Skeleton key={index} className="h-6 w-full" />
        ))}
      </div>
    )
  }
  if (data.length === 0) return <EmptyState icon={Building2} title="No companies yet" />

  const max = Math.max(...data.map((row) => row.count))
  return (
    <ul className="grid gap-3">
      {data.map((row) => (
        <li key={row.industry} className="grid gap-1">
          <div className="flex justify-between text-sm">
            <span className="truncate">{row.industry}</span>
            <span className="text-muted-foreground tabular-nums">{row.count}</span>
          </div>
          <div className="bg-muted h-2 rounded-full">
            <div
              className="bg-primary h-2 rounded-full"
              style={{ width: `${(row.count / max) * 100}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  )
}

function RecentActivity({ logs }: { logs?: DashboardStats['recent_activity'] }) {
  if (!logs) {
    return (
      <div className="grid gap-3">
        {Array.from({ length: 5 }, (_, index) => (
          <Skeleton key={index} className="h-10 w-full" />
        ))}
      </div>
    )
  }
  if (logs.length === 0) return <EmptyState icon={History} title="No activity yet" />

  return (
    <ul className="divide-y">
      {logs.map((log) => (
        <li key={log.id} className="flex items-start gap-3 py-3 first:pt-0 last:pb-0">
          <ActionBadge action={log.action} />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm">
              <span className="font-medium">{log.object_repr}</span>{' '}
              <span className="text-muted-foreground">({log.model_name.toLowerCase()})</span>
            </p>
            <p className="text-muted-foreground truncate text-xs">
              {log.user?.full_name ?? log.user_email} · {formatDateTime(log.timestamp)}
            </p>
          </div>
        </li>
      ))}
    </ul>
  )
}
