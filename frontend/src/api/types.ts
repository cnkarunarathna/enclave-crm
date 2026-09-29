// Shapes returned by the Django API (inside the envelope's `data`).

export type Role = 'ADMIN' | 'MANAGER' | 'STAFF'
export type Plan = 'BASIC' | 'PRO'
export type Resource = 'company' | 'contact' | 'activity_log'
export type Verb = 'read' | 'create' | 'update' | 'delete'

/** From /auth/me: what the current role may do. The UI never hard-codes the matrix. */
export type Capabilities = Partial<Record<Resource, Partial<Record<Verb, boolean>>>>

export interface Organization {
  id: number
  name: string
  subscription_plan: Plan
}

export interface User {
  id: number
  email: string
  full_name: string
  role: Role
  organization: Organization
  capabilities: Capabilities
}

export interface Tokens {
  access: string
  refresh: string
}

export interface LoginResponse extends Tokens {
  user: User
}

export interface Company {
  id: number
  name: string
  industry: string
  country: string
  logo_url: string | null
  contacts_count: number
  created_at: string
  updated_at: string
}

export interface CompanyInput {
  name: string
  industry?: string
  country?: string
  logo?: File | null
  remove_logo?: boolean
}

export interface CompanyFacets {
  industries: string[]
  countries: string[]
}

export interface Contact {
  id: number
  company: number
  company_name: string
  full_name: string
  email: string
  phone: string
  role: string
  created_at: string
  updated_at: string
}

export interface ContactInput {
  company?: number
  full_name: string
  email: string
  phone?: string
  role?: string
}

export type Action = 'CREATE' | 'UPDATE' | 'DELETE'

export interface ActivityLog {
  id: number
  user: { id: number; email: string; full_name: string } | null
  user_email: string
  action: Action
  model_name: 'Company' | 'Contact'
  object_id: number
  object_repr: string
  changes: Record<string, { old?: unknown; new?: unknown }>
  timestamp: string
}

export interface DashboardStats {
  organization: { name: string; subscription_plan: Plan }
  totals: { companies: number; contacts: number }
  companies_by_industry: { industry: string; count: number }[]
  recent_activity: ActivityLog[]
}

// --- Envelope & pagination ---------------------------------------------------

export interface PageMeta {
  count: number
  page: number
  page_size: number
  total_pages: number
}

export interface SuccessEnvelope<T> {
  success: true
  message: string
  data: T
  meta?: PageMeta
}

export interface ErrorEnvelope {
  success: false
  message: string
  code: string
  errors: Record<string, string[]> | null
}

export interface Paginated<T> {
  data: T[]
  meta: PageMeta
}

/** Query string for list endpoints: page, page_size, search, ordering and filters. */
export type ListParams = Record<string, string | number | undefined>
