import { LogOut, Menu } from 'lucide-react'
import { useState } from 'react'

import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuth } from '@/hooks/useAuth'
import { initials, roleLabel } from '@/lib/format'

export function Topbar({ onMenuClick }: { onMenuClick: () => void }) {
  const { user, logout } = useAuth()
  const [signingOut, setSigningOut] = useState(false)
  if (!user) return null

  const handleLogout = async () => {
    setSigningOut(true)
    await logout()
  }

  return (
    <header className="bg-background/95 supports-[backdrop-filter]:bg-background/80 sticky top-0 z-30 flex h-14 items-center gap-3 border-b px-4 backdrop-blur sm:px-6">
      <Button
        variant="ghost"
        size="icon"
        className="md:hidden"
        onClick={onMenuClick}
        aria-label="Open navigation"
      >
        <Menu />
      </Button>

      <div className="flex min-w-0 items-center gap-2">
        <span className="truncate font-medium">{user.organization.name}</span>
        <Badge variant={user.organization.subscription_plan === 'PRO' ? 'default' : 'secondary'}>
          {user.organization.subscription_plan}
        </Badge>
      </div>

      <div className="ml-auto">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-9 gap-2 px-2" aria-label="Account menu">
              <Avatar className="size-7">
                <AvatarFallback className="text-xs">{initials(user.full_name)}</AvatarFallback>
              </Avatar>
              <span className="hidden max-w-40 truncate text-sm sm:inline">{user.full_name}</span>
              <Badge variant="outline" className="hidden sm:inline-flex">
                {roleLabel(user.role)}
              </Badge>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="font-normal">
              <p className="truncate text-sm font-medium">{user.full_name}</p>
              <p className="text-muted-foreground truncate text-xs">{user.email}</p>
              <Badge variant="outline" className="mt-2 sm:hidden">
                {roleLabel(user.role)}
              </Badge>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem variant="destructive" disabled={signingOut} onSelect={handleLogout}>
              <LogOut />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
