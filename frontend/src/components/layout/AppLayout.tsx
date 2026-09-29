import { useState } from 'react'
import { Outlet } from 'react-router-dom'

import { Sheet, SheetContent, SheetDescription, SheetTitle } from '@/components/ui/sheet'

import { SidebarNav } from './SidebarNav'
import { Topbar } from './Topbar'

/**
 * Desktop (md and up): fixed sidebar + content.
 * Phones/tablets: the sidebar becomes a slide-out drawer opened from the top bar.
 */
export function AppLayout() {
  const [drawerOpen, setDrawerOpen] = useState(false)

  return (
    <div className="bg-muted/40 flex min-h-svh">
      <aside className="bg-background sticky top-0 hidden h-svh w-60 shrink-0 border-r md:block">
        <SidebarNav />
      </aside>

      <Sheet open={drawerOpen} onOpenChange={setDrawerOpen}>
        <SheetContent side="left" className="w-64 p-0">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          <SheetDescription className="sr-only">Main navigation links</SheetDescription>
          <SidebarNav onNavigate={() => setDrawerOpen(false)} />
        </SheetContent>
      </Sheet>

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar onMenuClick={() => setDrawerOpen(true)} />
        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <div className="mx-auto w-full max-w-6xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
