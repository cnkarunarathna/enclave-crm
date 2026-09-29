# System Requirements Specification

## 1. Purpose

A web-based CRM that many organizations (tenants) use at the same time from one deployment. Each
organization manages its own companies and contacts. The system guarantees that no user can read
or change another organization's data, restricts actions by role, and records every change in an
audit log.

## 2. Scope

**In scope:**
- Authentication (JWT).
- Organizations and users with roles.
- Company management, including logo upload.
- Contact management.
- The activity (audit) log.
- A dashboard.
- A REST API (`/api/v1/`) and a React single-page frontend.

**Out of scope:**
- User management UI and self-registration.
- Password reset and email.
- Billing or plan enforcement (the plan is stored only).
- Restoring deleted records.
- Real-time updates and internationalization.

## 3. Actors

| Actor | Description |
|---|---|
| Admin | Full control of their organization's data, including deletion |
| Manager | Reads, creates and edits; cannot delete |
| Staff | Reads companies and contacts; may add contacts only; cannot see the audit log |
| System administrator | Django superuser; manages organizations and users in Django admin (not a tenant user) |

## 4. Functional requirements

| ID | Requirement |
|---|---|
| FR-1 | A user signs in with email and password and receives an access token and a refresh token. A failed login shows one generic message. |
| FR-2 | Sessions renew transparently while the refresh token is valid; signing out revokes the refresh token. |
| FR-3 | Each user belongs to exactly one organization and has one role (Admin, Manager, Staff). Users without an organization cannot sign in. |
| FR-4 | An organization has a name, a subscription plan (Basic, Pro) and a creation time. |
| FR-5 | Users can list, search (name, industry, country), filter (industry, country, created date), sort and page through companies. |
| FR-6 | Admins and Managers can create and edit companies (name, industry, country, logo); only Admins can delete them. |
| FR-7 | A company logo is a JPEG, PNG or WebP image of at most 2 MB. It is stored in a private AWS S3 bucket and shown through a link that expires. |
| FR-8 | Deleting a company also deletes its contacts. |
| FR-9 | Users can list, search, filter by company and role, and page through contacts; a company's page shows its contacts. |
| FR-10 | All roles can add contacts; Admins and Managers can edit them; only Admins can delete them. |
| FR-11 | A contact has a full name (required), an email (required, valid, unique within its company), a phone (optional, 8–15 digits) and a job title (optional). |
| FR-12 | Deleted records disappear from every list, count and lookup but remain in the database (soft delete). A deleted contact's email can be reused. |
| FR-13 | Every create, update and delete of a company or contact records who acted, the action, the record type and id, the time and the changed values. |
| FR-14 | Admins and Managers can view, filter (record type, action, date range; the API also filters by user and record id) and search the activity log. The log cannot be edited or deleted through the application. |
| FR-15 | The dashboard shows the organization, company and contact totals, companies by industry, and (for Admins and Managers) the five most recent activities. |
| FR-16 | All API responses use one success/error format with a machine-readable error code and per-field validation messages. |

## 5. Non-functional requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-1 | Isolation | Every query is limited to the user's organization, enforced at the query, manager, middleware and schema levels. Requests for another organization's records return "not found". |
| NFR-2 | Security | Authorization is enforced by the server. The UI only hides actions. Anything not explicitly allowed is denied. |
| NFR-3 | Security | No secrets are in source control; all configuration comes from environment variables. Production requires HTTPS settings, `DEBUG` off and an explicit list of allowed hosts and origins. |
| NFR-4 | Security | Login is rate-limited (10 attempts per minute per client IP). Uploaded files are validated by type, content and size. Error responses never expose internals. |
| NFR-5 | Auditability | A change and its audit entry are saved in one transaction: neither is stored without the other. |
| NFR-6 | Performance | Lists are paginated (10 per page by default, at most 100). List endpoints avoid per-row queries. Indexes cover the organization-scoped lookups. |
| NFR-7 | Maintainability | There is a layered structure (views, serializers, services, permissions, models); one permission matrix; automated tests with at least 90% backend coverage; linting in CI and in git hooks. |
| NFR-8 | Portability | The system runs with Docker Compose (development and production-style). Local file storage replaces S3 when it isn't configured. |
| NFR-9 | Usability | Every data view has loading, empty and error states. The layout works on desktop and mobile. List filters are kept in the URL. |

## 6. Constraints and assumptions

**Constraints:**
- Django REST Framework, React, PostgreSQL and AWS S3 (Free Tier, small files).

**Assumptions:**
- Organizations and users are created by a system administrator (or the demo seed).
- One user belongs to one organization.
- HTTPS is terminated by a load balancer or proxy in production.

## 7. Use cases

| Use case | Actor | Main flow |
|---|---|---|
| UC-1 Sign in | Any | Enter email and password → dashboard. Wrong credentials → generic error. |
| UC-2 Manage companies | Admin, Manager | Search or filter the list → create or edit in a form (with logo) → Admin can delete after confirmation. |
| UC-3 Manage contacts | All (by role) | Open a company → add a contact → Admin or Manager edits → Admin deletes. Duplicate email or a bad phone number shows a field error. |
| UC-4 Review activity | Admin, Manager | Open the activity log → filter by type, action or date → expand an entry to see old and new values. |

## 8. Acceptance criteria

1. A user of organization B cannot list, open, edit or delete organization A's companies,
   contacts or activity entries, or attach a contact to A's company (FR-3, NFR-1).
2. The role matrix in FR-6, FR-10 and FR-14 holds for every role and action, via both the UI and
   the API (NFR-2).
3. Each create, update and delete produces exactly one audit entry, plus one per contact removed
   by a company delete (FR-8, FR-13, NFR-5).
4. Deleted records disappear everywhere, and a deleted contact's email can be reused (FR-12).
5. Invalid emails, duplicate emails within a company and phone numbers outside 8–15 digits are
   rejected with field messages (FR-11).
6. Logos upload to a private bucket, and the returned link expires (FR-7).
7. A fresh clone runs by following the README. Production settings pass Django's deployment
   check, and CI is green (NFR-3, NFR-8).

Each brief requirement is mapped to its implementation and verification in the traceability
table in [PROJECT_PLAN.md §2](../PROJECT_PLAN.md#2-requirements-traceability-brief--implementation).
The backend test suite (`backend/tests/`) verifies criteria 1–5 automatically.
