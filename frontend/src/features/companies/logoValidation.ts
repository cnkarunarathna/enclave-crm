// Mirrors the server's checks (core/validators.py) so users get instant feedback.
// The server still validates every upload; this is only a convenience.
export const MAX_LOGO_MB = 2
export const LOGO_ACCEPT = 'image/png,image/jpeg,image/webp'
const ALLOWED_TYPES = LOGO_ACCEPT.split(',')

/** Returns an error message, or null when the file looks acceptable. */
export function checkLogoFile(file: File): string | null {
  if (!ALLOWED_TYPES.includes(file.type)) return 'Logo must be a JPEG, PNG or WebP image.'
  if (file.size > MAX_LOGO_MB * 1024 * 1024) return `Logo must be ${MAX_LOGO_MB} MB or smaller.`
  return null
}
