import { Search, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

const DEBOUNCE_MS = 400

interface SearchInputProps {
  /** The committed value (usually from the URL). */
  value: string
  /** Called 400 ms after the user stops typing, not on every keystroke. */
  onChange: (value: string) => void
  placeholder?: string
  className?: string
}

export function SearchInput({
  value,
  onChange,
  placeholder = 'Search…',
  className,
}: SearchInputProps) {
  const [text, setText] = useState(value)
  const [lastValue, setLastValue] = useState(value)
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined)

  // The URL changed from outside (back button, "clear filters"): show the new value.
  // Adjusting state during render is React's recommended alternative to an effect here.
  if (value !== lastValue) {
    setLastValue(value)
    setText(value)
  }

  useEffect(() => () => clearTimeout(timer.current), [])

  const update = (next: string, delay = DEBOUNCE_MS) => {
    setText(next)
    clearTimeout(timer.current)
    timer.current = setTimeout(() => onChange(next), delay)
  }

  return (
    <div className={cn('relative', className)}>
      <Search className="text-muted-foreground pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2" />
      <Input
        type="search"
        value={text}
        onChange={(event) => update(event.target.value)}
        placeholder={placeholder}
        aria-label={placeholder}
        className="pr-8 pl-8"
      />
      {text && (
        <Button
          type="button"
          variant="ghost"
          size="icon-xs"
          className="absolute top-1/2 right-1 -translate-y-1/2"
          onClick={() => update('', 0)}
          aria-label="Clear search"
        >
          <X />
        </Button>
      )}
    </div>
  )
}
