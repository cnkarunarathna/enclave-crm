import { createBrowserRouter } from 'react-router-dom'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { PublicOnlyRoute } from '@/components/auth/PublicOnlyRoute'
import { RoleGate } from '@/components/auth/RoleGate'
import { FullPageSpinner } from '@/components/common/FullPageSpinner'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoginPage } from '@/pages/LoginPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

// Pages behind login are loaded on first visit (code splitting), so the login
// screen doesn't download the tables, forms and charts of the whole app.
export const router = createBrowserRouter([
  {
    path: '/login',
    element: (
      <PublicOnlyRoute>
        <LoginPage />
      </PublicOnlyRoute>
    ),
  },
  {
    // Everything inside the app shell requires a signed-in user.
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    // Shown on first load while the page's code is being fetched.
    HydrateFallback: FullPageSpinner,
    children: [
      {
        index: true,
        lazy: async () => ({ Component: (await import('@/pages/DashboardPage')).DashboardPage }),
      },
      {
        path: 'companies',
        lazy: async () => ({ Component: (await import('@/pages/CompaniesPage')).CompaniesPage }),
      },
      {
        path: 'companies/:id',
        lazy: async () => ({
          Component: (await import('@/pages/CompanyDetailPage')).CompanyDetailPage,
        }),
      },
      {
        path: 'activity',
        lazy: async () => {
          const [{ ActivityLogPage }, { ForbiddenPage }] = await Promise.all([
            import('@/pages/ActivityLogPage'),
            import('@/pages/ForbiddenPage'),
          ])
          return {
            element: (
              <RoleGate resource="activity_log" verb="read" fallback={<ForbiddenPage />}>
                <ActivityLogPage />
              </RoleGate>
            ),
          }
        },
      },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
