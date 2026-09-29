import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'

// Radix Select can't use "" as an item value, so "all" stands for "no filter".
const ALL = '__all__'

interface FilterSelectProps {
  label: string
  value: string
  onChange: (value: string) => void
  options: { value: string; label: string }[]
  /** Text for the "no filter" option, e.g. "All industries". Omit to require a choice. */
  allLabel?: string
  className?: string
}

export function FilterSelect({
  label,
  value,
  onChange,
  options,
  allLabel,
  className,
}: FilterSelectProps) {
  return (
    <Select
      value={value || (allLabel ? ALL : undefined)}
      onValueChange={(next) => onChange(next === ALL ? '' : next)}
    >
      <SelectTrigger aria-label={label} className={cn('w-full sm:w-44', className)}>
        <SelectValue placeholder={label} />
      </SelectTrigger>
      <SelectContent>
        {allLabel && <SelectItem value={ALL}>{allLabel}</SelectItem>}
        {options.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
