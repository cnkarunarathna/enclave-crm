const dateFormatter = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' })
const dateTimeFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
  timeStyle: 'short',
})

/** API timestamps are UTC ISO strings; show them in the viewer's local time. */
export const formatDate = (iso: string) => dateFormatter.format(new Date(iso))
export const formatDateTime = (iso: string) => dateTimeFormatter.format(new Date(iso))

/** "Jane Doe" -> "JD", "acme" -> "AC". Used for avatar fallbacks. */
export function initials(name: string) {
  const words = name.trim().split(/\s+/).filter(Boolean)
  if (words.length === 0) return '?'
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase()
  return (words[0][0] + words[words.length - 1][0]).toUpperCase()
}

export const roleLabel = (role: string) => role.charAt(0) + role.slice(1).toLowerCase()
