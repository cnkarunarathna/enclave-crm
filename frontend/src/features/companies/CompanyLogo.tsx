import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { initials } from '@/lib/format'
import { cn } from '@/lib/utils'

interface CompanyLogoProps {
  name: string
  /** Presigned S3 URL (expires after a few minutes) or null. */
  url: string | null
  className?: string
}

/** Logo if there is one, otherwise the company's initials. */
export function CompanyLogo({ name, url, className }: CompanyLogoProps) {
  return (
    <Avatar className={cn('size-9 rounded-md', className)}>
      {url && <AvatarImage src={url} alt="" className="object-contain" />}
      <AvatarFallback className="rounded-md text-xs font-medium">{initials(name)}</AvatarFallback>
    </Avatar>
  )
}
