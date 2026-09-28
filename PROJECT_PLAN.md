# Multi-Tenant CRM: Project Plan & Build Instructions

> **Audience:** Claude Code (primary reader) and the repo owner (reviewer, who must explain every file on camera).
> **Purpose:** Single source of truth for building the "Associate Full Stack Developer Technical Examination" deliverable: a production-minded, multi-tenant CRM (Django REST Framework + React + PostgreSQL + AWS S3).
> **Rule of thumb:** When this file and your instincts disagree, follow this file. When this file is silent or ambiguous, pick the simplest option that satisfies the brief, and record the choice in `docs/DECISIONS.md`.

---

## 0. Working agreement for Claude Code (read first)

1. **Read this whole file before writing code.** Then work phase by phase (section 16). Tick the checkboxes in section 16 as tasks complete.
2. **Priorities, in order:** (1) tenant isolation, (2) role-based access control, (3) audit log, (4) clean structure/separation of concerns, (5) production readiness, (6) UI structure. Visual polish is explicitly last.
3. **Simple, readable code beats clever code.** The owner must explain every file in a screen recording. Prefer small files, explicit names, and short comments that explain *why* (especially in tenancy, permissions, services, and storage code).
4. **Commit small and often** using Conventional Commits (`feat(core): ...`, `fix(crm): ...`, `test(rbac): ...`, `docs: ...`, `chore: ...`, `ci: ...`). One logical change per commit. Never commit a broken build, and never commit secrets or `.env` files.
5. **Run tests and linters before each commit** (`make test`, `make lint`). Do not disable or skip failing tests to move on; fix them.
6. **Do not add dependencies outside section 4** without a one-line justification in `docs/DECISIONS.md`.
7. **Never accept `organization`, `is_deleted`, `deleted_at`, or timestamps from client input.** The server sets them.
8. **Backend is the authority for security.** The UI hiding a button is a courtesy, never a control.
9. **Human-only tasks are marked `HUMAN:`** (AWS account/bucket/IAM, screen recording, GitHub repo creation). Do the code side, leave clear instructions in `docs/AWS_S3_SETUP.md`, and do not block on them: the local `FileSystemStorage` fallback must always work.
10. **Pin exact dependency versions** in `requirements/*.txt` and `package-lock.json` after installing (use the latest stable versions that are compatible with each other).
11. **Keep `README.md` truthful.** If a command in the README does not work from a fresh clone, that is a bug.

---

## 1. Goal, scope, and non-goals

### 1.1 Goal
Build one application that many organizations (tenants) use simultaneously. Each organization manages its own **Companies** and **Contacts**. Users belong to exactly one organization and have a role (**Admin / Manager / Staff**). No user can ever read or modify another organization's data. Every create/update/delete on Companies and Contacts is recorded in an **Activity Log**.

### 1.2 In scope (must ship)
- Organization + custom User model with roles; JWT auth (login, refresh, logout, me).
- Tenant isolation at DB-model level, query level, manager level, and middleware level.
- RBAC enforced server-side through custom permission classes.
- Company CRUD (with logo upload to AWS S3) and Contact CRUD, both with pagination, search, filtering, ordering, and **soft delete** (`is_deleted`).
- Activity log for every CREATE/UPDATE/DELETE on Companies/Contacts, plus a read-only API.
- Versioned API (`/api/v1/`), consistent response envelope, centralized exception handling, OpenAPI docs.
- React frontend: Login, Dashboard, Companies, Company Detail (with nested contacts), Activity Log; protected routing, centralized API layer, structured state, loading and error states, pagination, reusable components.
- Production-readiness: `.env` usage, `.env.example`, dev/prod settings split, CORS, PostgreSQL, Docker, CI, docs.
- Demo data (`seed_demo`) with two organizations to demonstrate isolation.

### 1.3 Explicit non-goals (do NOT build)
User-management UI, self-registration, password reset/email sending, billing/plan enforcement (plan is a stored field only), Celery/queues, websockets, i18n, Kubernetes manifests, complex charts, file types other than logos, hard-delete/restore UI. Mention some of these as "future work" in the README instead.

---

## 2. Requirements traceability (brief → implementation)

| # | Requirement from the brief | Where implemented | Verified by |
|---|---|---|---|
| R1 | Organization model: name, plan (Basic/Pro), created timestamp | `organizations.Organization` (§6) | model test, seed |
| R2 | User belongs to organization, has role Admin/Manager/Staff | `organizations.User` (§6) | auth tests |
| R3 | DB modeling with organization FKs | `TenantModel` base (§6, §9.2) | migration review |
| R4 | Query-level filtering | `OrganizationScopedViewSet.get_queryset` (§9.4) | isolation tests |
| R5 | Middleware / manager-level isolation | `TenantContextMiddleware` + `TenantManager` (§9.2) | middleware tests |
| R6 | RBAC: Admin deletes; Manager edits, no delete; Staff limited write | `PERMISSION_MATRIX` + `RolePermission` (§7.2) | RBAC tests |
| R7 | JWT auth, all protected endpoints need tokens | simplejwt, default `IsAuthenticated` (§9.1) | auth tests |
| R8 | Company fields (name, industry, country, logo, org, created) | `crm.Company` (§6) | CRUD tests |
| R9 | Logo on AWS S3 (Free Tier, small files), env vars, no hardcoded creds, secure IAM, bucket access explanation | §10, `docs/AWS_S3_SETUP.md` | manual + README |
| R10 | Contact fields; email unique per company; phone optional 8–15 digits; valid email | `crm.Contact`, serializers (§6, §9.5) | validation tests |
| R11 | Full CRUD, pagination, search, filtering, soft delete | crm viewsets + filters (§8, §9.5) | CRUD tests |
| R12 | All queries auto-scoped to authenticated user's org | R4 + R5 | isolation tests |
| R13 | Activity log: user, action, model, object id, timestamp | `activity.ActivityLog` + service (§7.4) | audit tests |
| R14 | Separation: serializers, views, service layer, permissions, models | app layout (§5) | code review |
| R15 | Custom permission classes, consistent responses, exception handling, versioned routing | §7.6, §9.3 | envelope tests |
| R16 | Frontend: 5 pages, protected routes, central API service, state mgmt, loading/error, pagination, reusable components | §11 | manual + Vitest |
| R17 | `.env`, `.env.example`, dev vs prod config, CORS, PostgreSQL | §9.1, §13 | fresh-clone test |
| R18 | GitHub repo, clean structure, meaningful commits | §0, §5 | git log |
| R19 | 15–20 min screen recording | §15.5 (script) | HUMAN |

---

## 3. Locked decisions (defaults; change here before starting, never mid-build)

| Topic | Decision | Reason |
|---|---|---|
| Staff permissions | Read everything; **create Contacts only**; no edit, no delete | Brief says "limited write access"; this is the clearest interpretation |
| Manager permissions | Read, create, update; **no delete** | Brief |
| Admin permissions | Everything including delete | Brief |
| Activity log visibility | Admin and Manager can read; Staff cannot | Audit data is sensitive; easy to change in `PERMISSION_MATRIX` |
| Cross-tenant access | Returns **404** (not 403) | Do not reveal that an ID exists elsewhere |
| Contacts API shape | Flat `/contacts/` with `?company=<id>` filter | Fewer dependencies than nested routers; frontend nests it visually |
| Primary keys | Default integer `BigAutoField` | Simple for demo; isolation never relies on ID secrecy |
| Audit implementation | **Service layer**, inside `transaction.atomic` | Signals cannot know the acting user; explicit is testable |
| Soft delete cascade | Deleting a company soft-deletes its contacts (each gets its own DELETE log row) | Truthful audit trail |
| Contact `company` on update | Immutable after creation | Avoids re-validating uniqueness/tenancy on moves |
| Frontend language | TypeScript (`strict`) | Maintainability signal |
| Token storage | Access token in memory; refresh token in `localStorage` | Reasonable trade-off; note httpOnly-cookie refresh as production improvement |
| Delete responses | `200` with envelope (`data: null`), not `204` | Keeps response format uniform |
| Storage | Private S3 bucket + **presigned URLs** (5 min); local `FileSystemStorage` when `USE_S3=False` | Secure by default; no dev dependency on AWS |

---

## 4. Tech stack

### 4.1 Backend
- Python 3.12, **Django 5.2 LTS** (use 6.x only if every dependency supports it; default to 5.2), Django REST Framework
- `djangorestframework-simplejwt` (+ `token_blacklist` app) for JWT
- `django-filter` (filtering), DRF `SearchFilter` and `OrderingFilter`
- `django-storages[s3]` + `boto3` for S3; `Pillow` for image validation
- `django-environ` for env vars; `django-cors-headers` for CORS
- `drf-spectacular` for OpenAPI/Swagger
- `psycopg[binary]` (PostgreSQL driver), `gunicorn`, `whitenoise`
- Dev/test: `pytest`, `pytest-django`, `pytest-cov`, `factory-boy` (optional), `ruff` (lint + format)

### 4.2 Frontend
- Vite + React (latest stable) + TypeScript (`strict`)
- `react-router-dom` v6+ (protected/role routes)
- `axios` (single configured instance + interceptors)
- `@tanstack/react-query` (server state: loading, error, pagination, caching)
- React Context for auth and toasts
- `react-hook-form` + `zod` + `@hookform/resolvers` (forms and validation)
- Tailwind CSS (utility styling only; no design time); `lucide-react` (icons, optional)
- Dev/test: `eslint`, `prettier`, `vitest` + `@testing-library/react` (2–3 tests only)

### 4.3 Infrastructure
- PostgreSQL 16 in Docker Compose (local), Dockerfiles for backend and frontend, GitHub Actions CI, `Makefile` for common commands.

---

## 5. Repository layout

```
crm/                                  # repo root
├── PROJECT_PLAN.md                   # this file
├── CLAUDE.md                         # one line: @PROJECT_PLAN.md
├── README.md
├── Makefile
├── docker-compose.yml                # dev: db + backend + frontend
├── docker-compose.prod.yml           # prod-like: gunicorn + nginx static frontend
├── .env.example                      # compose-level vars (POSTGRES_*)
├── .gitignore
├── .github/workflows/ci.yml
├── docs/
│   ├── ARCHITECTURE.md               # Mermaid diagrams: ERD, request flow, tenancy
│   ├── SRS.md                        # short System Requirements Specification
│   ├── DECISIONS.md                  # ADR-lite: decision, alternatives, why
│   ├── AWS_S3_SETUP.md               # bucket, IAM policy, env vars, access strategy
│   └── RECORDING_SCRIPT.md           # demo script with timings
├── backend/
│   ├── manage.py
│   ├── pyproject.toml                # ruff + pytest config
│   ├── requirements/{base,dev,prod}.txt
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── .env.example
│   ├── config/
│   │   ├── urls.py  wsgi.py  asgi.py
│   │   └── settings/{__init__,base,dev,prod}.py
│   ├── apps/
│   │   ├── core/                     # cross-cutting: tenancy, permissions, envelope, errors
│   │   │   ├── models.py             # TenantModel (abstract)
│   │   │   ├── managers.py           # OrgScopedManager, TenantManager
│   │   │   ├── tenancy.py            # contextvar helpers
│   │   │   ├── middleware.py         # TenantContextMiddleware
│   │   │   ├── permissions.py        # RolePermission, IsSameOrganization
│   │   │   ├── viewsets.py           # OrganizationScopedViewSet
│   │   │   ├── pagination.py  renderers.py  exceptions.py  validators.py
│   │   │   └── views.py              # health check
│   │   ├── organizations/            # Organization, User, roles, auth endpoints
│   │   │   ├── models.py  roles.py  serializers.py  views.py  urls.py  admin.py
│   │   │   └── management/commands/seed_demo.py
│   │   ├── crm/                      # Company, Contact
│   │   │   ├── models.py  serializers.py  views.py  urls.py  filters.py
│   │   │   ├── services.py           # ALL writes go through here (+ audit)
│   │   │   ├── storage.py            # upload_to path builder
│   │   │   └── admin.py
│   │   ├── activity/                 # ActivityLog
│   │   │   ├── models.py  services.py  serializers.py  views.py  filters.py  urls.py
│   │   └── dashboard/                # stats endpoint
│   │       └── views.py  urls.py
│   └── tests/
│       ├── conftest.py               # fixtures: orgs, users per role, auth_client
│       └── test_*.py
└── frontend/
    ├── package.json  vite.config.ts  tsconfig.json  eslint.config.js
    ├── Dockerfile  nginx.conf  .env.example
    └── src/
        ├── main.tsx  App.tsx  router.tsx
        ├── api/            # client.ts, tokenStore.ts, errors.ts, types.ts, *.api.ts per resource
        ├── context/        # AuthContext.tsx, ToastContext.tsx
        ├── hooks/          # useAuth, useCompanies, useContacts, useActivityLogs, useDashboard, useDebounce, useListParams
        ├── components/
        │   ├── ui/         # Button, Badge, Modal, ConfirmDialog, FormField, Spinner, ErrorBanner, EmptyState
        │   ├── data/       # DataTable, Pagination, SearchInput
        │   ├── layout/     # AppLayout, Sidebar, Topbar
        │   └── auth/       # ProtectedRoute, RoleGate
        ├── features/       # companies/ (CompanyForm...), contacts/ (ContactForm...), activity/
        ├── pages/          # Login, Dashboard, Companies, CompanyDetail, ActivityLog, NotFound, Forbidden
        └── lib/            # format.ts
```

---

## 6. Domain model

```mermaid
erDiagram
    ORGANIZATION ||--o{ USER : has
    ORGANIZATION ||--o{ COMPANY : owns
    ORGANIZATION ||--o{ CONTACT : owns
    ORGANIZATION ||--o{ ACTIVITY_LOG : owns
    COMPANY ||--o{ CONTACT : has
    USER ||--o{ ACTIVITY_LOG : performs
    ORGANIZATION {
        bigint id PK
        string name
        string subscription_plan
        datetime created_at
    }
    USER {
        bigint id PK
        string email UK
        string first_name
        string last_name
        string role
        bigint organization_id FK
    }
    COMPANY {
        bigint id PK
        bigint organization_id FK
        string name
        string industry
        string country
        string logo
        bool is_deleted
        datetime created_at
    }
    CONTACT {
        bigint id PK
        bigint organization_id FK
        bigint company_id FK
        string full_name
        string email
        string phone
        string role
        bool is_deleted
        datetime created_at
    }
    ACTIVITY_LOG {
        bigint id PK
        bigint organization_id FK
        bigint user_id FK
        string action
        string model_name
        bigint object_id
        datetime timestamp
    }
```

### 6.1 Organization
| Field | Type | Notes |
|---|---|---|
| `name` | CharField(150), unique | |
| `subscription_plan` | CharField, choices `BASIC`/`PRO`, default `BASIC` | Stored only; no enforcement |
| `created_at` | DateTimeField(auto_now_add) | |

### 6.2 User (`AUTH_USER_MODEL = "organizations.User"`)
- Extend `AbstractUser`; **remove `username`**; `USERNAME_FIELD = "email"`; email unique and lowercased; custom `UserManager` (`create_user`, `create_superuser`).
- `organization` FK → Organization (`PROTECT`, `null=True` **only** to allow a Django-admin superuser).
- `role`: choices `ADMIN` / `MANAGER` / `STAFF`, default `STAFF`.
- `full_name` property.
- **DB `CheckConstraint`:** `organization IS NOT NULL OR is_superuser = TRUE`.
- **API rule:** a user without an organization cannot obtain or use a token (login returns 403).

### 6.3 `TenantModel` (abstract; inherited by Company and Contact)
| Field | Notes |
|---|---|
| `organization` | FK → Organization, `PROTECT`, `related_name="+"`, indexed |
| `is_deleted` | BooleanField, default False, indexed |
| `deleted_at` | DateTimeField, null |
| `created_at` / `updated_at` | auto timestamps |

Managers: `objects = TenantManager()` (excludes soft-deleted + ambient org filter), `all_objects = models.Manager()` (unfiltered; use only in tests/admin/migrations/services when explicitly needed).

### 6.4 Company (`TenantModel`)
| Field | Type / rule |
|---|---|
| `name` | CharField(200), required |
| `industry` | CharField(100), blank allowed |
| `country` | CharField(100), blank allowed |
| `logo` | `ImageField(upload_to=company_logo_upload_to, null=True, blank=True, max_length=255)` → key `org-{org_id}/logos/{uuid}.{ext}` |

Indexes: `(organization, is_deleted, name)`.

### 6.5 Contact (`TenantModel`)
| Field | Type / rule |
|---|---|
| `company` | FK → Company, `PROTECT`, `related_name="contacts"`; **contact.organization must equal company.organization** (set server-side from the company) |
| `full_name` | CharField(200), required |
| `email` | EmailField, required, stored **lowercased and stripped** |
| `phone` | CharField(15), optional; after stripping spaces, must match `^\d{8,15}$` |
| `role` | CharField(100), optional (job title) |

Constraints/indexes:
- `UniqueConstraint(fields=["company","email"], condition=Q(is_deleted=False), name="uniq_contact_email_per_company_active")`. Soft-deleted rows do not block re-use of an email.
- Index `(organization, company, is_deleted)`.

### 6.6 ActivityLog (append-only; not soft-deletable)
| Field | Notes |
|---|---|
| `organization` | FK, `PROTECT`, indexed; manager applies ambient org filter |
| `user` | FK → User, `SET_NULL`, null (survives user removal) |
| `user_email` | snapshot string (readable even if user removed) |
| `action` | choices `CREATE` / `UPDATE` / `DELETE` |
| `model_name` | `"Company"` or `"Contact"` |
| `object_id` | PositiveBigIntegerField |
| `object_repr` | short human label (company name / contact full name), max 255 |
| `changes` | JSONField, default dict: `{field: {"old": ..., "new": ...}}` for UPDATE; `{field: {"new": ...}}` snapshot for CREATE; `{}` or snapshot for DELETE |
| `timestamp` | DateTimeField(auto_now_add, indexed) |

Indexes: `(organization, -timestamp)`, `(organization, model_name, object_id)`.
The log is immutable: expose **no** update/delete endpoints; register read-only in Django admin. Never store signed URLs in `changes`; for logos store the storage key (or `null`).

---

## 7. Architecture rules

### 7.1 Tenant isolation: four layers (defense in depth)

1. **Schema:** every tenant model has a non-null `organization` FK (§6.3).
2. **Query level (primary control):** `OrganizationScopedViewSet.get_queryset()` always starts from `Model.objects.for_org(request.user.organization_id)`. Because `get_object()` uses `get_queryset()`, another tenant's ID naturally returns **404**.
3. **Manager level (ambient):** `TenantManager` additionally filters by the *current org id* held in a `ContextVar`, and always excludes soft-deleted rows.
4. **Middleware level:** `TenantContextMiddleware` reads the `Authorization: Bearer` access token, validates it, and sets the ContextVar from the token's `org_id` claim (always reset in `finally`). It never rejects requests; DRF authentication still does that.

Notes to record in `docs/DECISIONS.md` and mention in the recording:
- DRF authenticates at *view* level, so a plain middleware cannot see `request.user`. That is why the middleware decodes the signed JWT claim itself.
- Layers 2 and 3 are AND-ed. If a token's `org_id` ever disagreed with the user's DB org, results would be empty (fail-safe).
- The ambient layer is fail-open when unset (shell, admin, migrations, management commands), which is why layer 2 is explicit and mandatory. Postgres Row-Level Security is the "next step" for production.
- **Related-object leaks:** any serializer field referencing a tenant object (e.g. `Contact.company`) must use a tenant-scoped queryset (§9.5), otherwise a user could attach a record to another org's company.
- **Permissions use the DB user** (`request.user.role`), not the token's role claim, so role changes take effect immediately.

```mermaid
sequenceDiagram
    participant C as Client
    participant MW as TenantContextMiddleware
    participant A as DRF JWT Auth
    participant P as RolePermission
    participant V as ViewSet
    participant S as Service layer
    participant DB as PostgreSQL
    C->>MW: Request + Bearer token
    MW->>MW: decode token, set current org (ContextVar)
    MW->>A: continue
    A->>A: verify token, load User
    A->>P: has_permission (role vs action matrix)
    P->>V: allowed
    V->>DB: Model.objects.for_org(user.org) (+ ambient filter)
    V->>S: create/update/delete(user, ...)
    S->>DB: atomic: write record + ActivityLog
    V-->>C: Envelope response
    MW->>MW: reset ContextVar (finally)
```

### 7.2 RBAC
Single source of truth in `organizations/roles.py`:

```python
class Role(models.TextChoices):
    ADMIN = "ADMIN"; MANAGER = "MANAGER"; STAFF = "STAFF"

ALL = {Role.ADMIN, Role.MANAGER, Role.STAFF}
PERMISSION_MATRIX = {
    "company":      {"read": ALL, "create": {Role.ADMIN, Role.MANAGER}, "update": {Role.ADMIN, Role.MANAGER}, "delete": {Role.ADMIN}},
    "contact":      {"read": ALL, "create": ALL,                        "update": {Role.ADMIN, Role.MANAGER}, "delete": {Role.ADMIN}},
    "activity_log": {"read": {Role.ADMIN, Role.MANAGER}},
}
ACTION_TO_VERB = {"list": "read", "retrieve": "read", "create": "create",
                  "update": "update", "partial_update": "update", "destroy": "delete"}

def capabilities_for(role) -> dict:
    """{'company': {'read': True, 'create': True, ...}, ...} for /auth/me, so the UI never duplicates the matrix."""
```

| Resource | Action | Admin | Manager | Staff |
|---|---|:-:|:-:|:-:|
| Company | list / retrieve | ✓ | ✓ | ✓ |
| Company | create | ✓ | ✓ | ✗ |
| Company | update | ✓ | ✓ | ✗ |
| Company | delete | ✓ | ✗ | ✗ |
| Contact | list / retrieve | ✓ | ✓ | ✓ |
| Contact | create | ✓ | ✓ | ✓ |
| Contact | update | ✓ | ✓ | ✗ |
| Contact | delete | ✓ | ✗ | ✗ |
| Activity log | list / retrieve | ✓ | ✓ | ✗ |
| Dashboard stats | read | ✓ | ✓ | ✓ (without recent activity) |

**Deny by default:** unknown action or resource → 403.

### 7.3 Soft delete
- `DELETE` never removes rows: set `is_deleted=True`, `deleted_at=now()` via the service.
- Company delete also soft-deletes its (non-deleted) contacts in the same transaction; each contact gets its own `DELETE` log entry (use `bulk_create`).
- Default managers hide deleted rows everywhere (lists, detail, uniqueness checks in serializers).
- Creating a contact for a soft-deleted company is rejected (validation error).
- `QuerySet.update()` bypasses `auto_now`; set `updated_at` explicitly in bulk updates.
- Logo files are **not** deleted from S3 on soft delete. When a logo is *replaced or removed* on an active company, delete the old object in `transaction.on_commit`.

### 7.4 Activity log (service layer)
- All writes to Company/Contact go through `crm/services.py`: `create_company`, `update_company`, `delete_company`, `create_contact`, `update_contact`, `delete_contact`.
- Each service is `@transaction.atomic`: perform the change, then call `activity.services.log_activity(user=..., action=..., obj=..., changes=...)`. If logging fails, the change rolls back.
- Views stay thin: validate with serializer → call service → serialize result.
- `changes` is computed by a helper `diff_instance(instance, validated_data)` *before* applying the update (normalize file fields to their storage name).
- A test must prove that **every** write endpoint produces exactly one log row (plus one per cascaded contact).

### 7.5 File storage (S3)
See §10. Summary: private bucket; presigned GET URLs via `ImageField.url` (`AWS_QUERYSTRING_AUTH=True`, expiry 300 s); keys namespaced per tenant; credentials only from env (default boto3 chain in prod so IAM roles work); local `FileSystemStorage` when `USE_S3=False`.

### 7.6 API conventions
- Base path `/api/v1/`. Resource names plural, trailing slashes.
- **Success envelope:** `{"success": true, "message": "", "data": <object|array|null>, "meta": {...optional}}`
- **Error envelope:** `{"success": false, "message": "Human readable", "code": "machine_code", "errors": {"field": ["msg"]} | null}`
- Status codes: `200` ok, `201` created, `400` validation, `401` unauthenticated/expired token, `403` role not allowed, `404` not found **or other tenant's object**, `409` unique conflict from DB race, `429` throttled, `500` unexpected (generic message, logged server-side, never leaks stack traces).
- Codes: `validation_error`, `not_authenticated`, `permission_denied`, `not_found`, `conflict`, `throttled`, `server_error`.
- Pagination `meta`: `{"count", "page", "page_size", "total_pages"}`; default `page_size=10`, `?page_size=` up to 100.
- Ordering via `?ordering=name` / `-created_at`; search via `?search=`.
- Times are UTC ISO-8601 (`USE_TZ=True`, `TIME_ZONE="UTC"`).

---

## 8. API specification (`/api/v1`)

### 8.1 Auth
| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/auth/login/` | none (throttled `10/min`) | Body `{email, password}` → `{access, refresh, user}` |
| POST | `/auth/refresh/` | none | Body `{refresh}` → `{access, refresh}` (rotation on) |
| POST | `/auth/logout/` | Bearer | Body `{refresh}` → blacklists the refresh token |
| GET | `/auth/me/` | Bearer | `{id, email, full_name, role, organization: {id, name, subscription_plan}, capabilities}` |

- Token claims: `user_id`, `org_id`, `role`, `email`. Access TTL 15 min, refresh 7 days (both env-configurable).
- Login failure: generic `"Invalid email or password."` (no user enumeration). Inactive user or user without org → `403`.

### 8.2 Companies (`permission_resource="company"`)
| Method | Path | Roles | Notes |
|---|---|---|---|
| GET | `/companies/` | A/M/S | Paginated. Filters: `industry` (iexact), `country` (iexact), `created_after`, `created_before`. Search: `name`, `industry`, `country`. Ordering: `name`, `industry`, `country`, `created_at` (default `-created_at`) |
| POST | `/companies/` | A/M | `multipart/form-data` or JSON. Fields: `name`, `industry`, `country`, `logo` (file, optional) |
| GET | `/companies/{id}/` | A/M/S | |
| PATCH/PUT | `/companies/{id}/` | A/M | Optional `logo` (replace) or `remove_logo=true` |
| DELETE | `/companies/{id}/` | A | Soft delete + cascade to contacts |

Company representation: `id, name, industry, country, logo_url (presigned or null), contacts_count, created_at, updated_at` (annotate `contacts_count = Count("contacts", filter=Q(contacts__is_deleted=False))`).

### 8.3 Contacts (`permission_resource="contact"`)
| Method | Path | Roles | Notes |
|---|---|---|---|
| GET | `/contacts/` | A/M/S | Filters: `company` (id), `role` (icontains). Search: `full_name`, `email`, `phone`, `role`. Ordering: `full_name`, `email`, `created_at` |
| POST | `/contacts/` | A/M/S | `company` (id) required |
| GET | `/contacts/{id}/` | A/M/S | |
| PATCH/PUT | `/contacts/{id}/` | A/M | `company` cannot change |
| DELETE | `/contacts/{id}/` | A | Soft delete |

Contact representation: `id, company, company_name, full_name, email, phone, role, created_at, updated_at`.

### 8.4 Activity log (`permission_resource="activity_log"`, read-only)
| Method | Path | Roles | Notes |
|---|---|---|---|
| GET | `/activity-logs/` | A/M | Filters: `model_name`, `action`, `user`, `object_id`, `timestamp_after`, `timestamp_before`. Search: `object_repr`, `user_email`. Ordering default `-timestamp` |
| GET | `/activity-logs/{id}/` | A/M | |

Representation: `id, user: {id, email, full_name} | null, user_email, action, model_name, object_id, object_repr, changes, timestamp`. Use `select_related("user")`.

### 8.5 Dashboard & utility
| Method | Path | Roles | Notes |
|---|---|---|---|
| GET | `/dashboard/stats/` | A/M/S | `{organization: {name, subscription_plan}, totals: {companies, contacts}, companies_by_industry: [{industry, count}], recent_activity: [...last 5, only for A/M else []]}` |
| GET | `/health/` | none | Checks DB with `SELECT 1`; `{status: "ok"}` |
| GET | `/schema/`, `/docs/` | none in dev; restricted or disabled in prod | OpenAPI + Swagger UI (drf-spectacular). Note in README that schema shows raw serializers, not the envelope |

### 8.6 Example payloads
```json
// GET /api/v1/companies/?page=1&search=sun
{
  "success": true, "message": "",
  "data": [{"id": 1, "name": "Sunrise Hotels", "industry": "Hospitality", "country": "Sri Lanka",
            "logo_url": "https://bucket.s3.amazonaws.com/org-1/logos/ab12.png?X-Amz-...", "contacts_count": 3,
            "created_at": "2026-09-28T09:00:00Z", "updated_at": "2026-09-28T09:00:00Z"}],
  "meta": {"count": 1, "page": 1, "page_size": 10, "total_pages": 1}
}

// POST /api/v1/contacts/ with a duplicate email
{
  "success": false, "message": "Validation failed.", "code": "validation_error",
  "errors": {"email": ["A contact with this email already exists for this company."]}
}

// GET /api/v1/companies/999/ belonging to another org
{ "success": false, "message": "Not found.", "code": "not_found", "errors": null }
```

---

## 9. Backend implementation guide

### 9.1 Settings & configuration
- `config/settings/base.py` (shared), `dev.py` (DEBUG, console email, browsable API, local storage default), `prod.py` (hardening). `DJANGO_SETTINGS_MODULE` selects one (default `config.settings.dev`; the Docker prod image sets `config.settings.prod`).
- All secrets/config come from env via `django-environ`. **`SECRET_KEY` has no default in prod** (raise `ImproperlyConfigured`).
- `INSTALLED_APPS` include: `rest_framework`, `rest_framework_simplejwt.token_blacklist`, `django_filters`, `corsheaders`, `drf_spectacular`, `storages`, and the four local apps. `AUTH_USER_MODEL = "organizations.User"`.
- `MIDDLEWARE` order: `SecurityMiddleware`, `WhiteNoiseMiddleware`, `CorsMiddleware` (before `CommonMiddleware`), `SessionMiddleware`, `CommonMiddleware`, `CsrfViewMiddleware`, `AuthenticationMiddleware`, `apps.core.middleware.TenantContextMiddleware`, `MessageMiddleware`, `XFrameOptionsMiddleware`.

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],  # secure by default
    "DEFAULT_RENDERER_CLASSES": ["apps.core.renderers.EnvelopeJSONRenderer"],
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_RATES": {"login": "10/min"},
}
```

**Environment variables** (`backend/.env.example`; every one documented with a comment):

```dotenv
DJANGO_SETTINGS_MODULE=config.settings.dev
DJANGO_SECRET_KEY=change-me-in-real-envs
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://crm:crm@localhost:5433/crm
CORS_ALLOWED_ORIGINS=http://localhost:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173
JWT_ACCESS_MINUTES=15
JWT_REFRESH_DAYS=7
LOG_LEVEL=INFO
MAX_LOGO_SIZE_MB=2
# --- Storage: set USE_S3=True and fill the rest to use S3; otherwise local media/ is used ---
USE_S3=False
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=
AWS_ACCESS_KEY_ID=           # leave EMPTY in prod on EC2/ECS: boto3 uses the instance/task IAM role
AWS_SECRET_ACCESS_KEY=       # leave EMPTY in prod on EC2/ECS
AWS_QUERYSTRING_EXPIRE=300
```
Root `.env.example`: `POSTGRES_DB=crm`, `POSTGRES_USER=crm`, `POSTGRES_PASSWORD=crm`. Frontend `.env.example`: `VITE_API_BASE_URL=http://localhost:8000/api/v1`.

**Dev vs prod differences**

| Concern | Dev | Prod |
|---|---|---|
| `DEBUG` | True | False (enforced) |
| Static files | runserver | WhiteNoise + `collectstatic` |
| Server | `runserver` | `gunicorn` |
| HTTPS | off | `SECURE_SSL_REDIRECT`, `SECURE_PROXY_SSL_HEADER`, HSTS, secure cookies |
| CORS | `localhost:5173` | explicit env allow-list; **never** `CORS_ALLOW_ALL_ORIGINS` |
| Browsable API / Swagger | on | Swagger off or admin-only |
| Storage default | local unless `USE_S3` | S3 |
| Logging | console, readable | console, structured level from env |

Also set: `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS="DENY"`, default password validators, `SIMPLE_JWT` with `ROTATE_REFRESH_TOKENS=True`, `BLACKLIST_AFTER_ROTATION=True`, `UPDATE_LAST_LOGIN=True`, and a custom token serializer adding `org_id`, `role`, `email` claims.

### 9.2 `apps/core` building blocks

```python
# tenancy.py
from contextvars import ContextVar
_current_org_id: ContextVar[int | None] = ContextVar("current_org_id", default=None)
def get_current_org_id(): return _current_org_id.get()
def set_current_org_id(v): return _current_org_id.set(v)      # returns a token
def reset_current_org_id(token): _current_org_id.reset(token)

# managers.py
class TenantQuerySet(models.QuerySet):
    def for_org(self, org):                                     # accepts Organization or id
        return self.filter(organization_id=getattr(org, "pk", org))

class OrgScopedManager(models.Manager.from_queryset(TenantQuerySet)):
    def get_queryset(self):
        qs = super().get_queryset()
        org_id = get_current_org_id()
        return qs.filter(organization_id=org_id) if org_id is not None else qs

class TenantManager(OrgScopedManager):                          # + soft-delete filter
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

# middleware.py
class TenantContextMiddleware:
    def __init__(self, get_response): self.get_response = get_response
    def __call__(self, request):
        token = set_current_org_id(self._org_id_from(request))
        try:
            return self.get_response(request)
        finally:
            reset_current_org_id(token)                         # never leak between requests
    @staticmethod
    def _org_id_from(request):
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header.startswith("Bearer "):
            return None
        try:
            return AccessToken(header[7:]).get("org_id")        # verifies signature, expiry, type
        except TokenError:
            return None
```

`permissions.py`:
```python
class RolePermission(BasePermission):
    message = "You do not have permission to perform this action."
    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated and u.organization_id):
            return False
        verb = ACTION_TO_VERB.get(getattr(view, "action", None))
        allowed = PERMISSION_MATRIX.get(view.permission_resource, {}).get(verb, set())
        return u.role in allowed                                # deny by default

class IsSameOrganization(BasePermission):                       # belt and braces at object level
    def has_object_permission(self, request, view, obj):
        return obj.organization_id == request.user.organization_id
```

`viewsets.py`:
```python
class OrganizationScopedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, RolePermission, IsSameOrganization]
    permission_resource: str            # required on subclasses
    model = None                        # required on subclasses
    def get_queryset(self):
        return self.model.objects.for_org(self.request.user.organization_id)
```
Subclasses override `create`, `update`, and `destroy` (not `perform_*`) to call services and return the envelope response, and set `http_method_names` sensibly (`get, post, put, patch, delete, head, options`).

Also in `core`: `EnvelopeJSONRenderer` (wraps successful data unless the payload already has a `success` key; error payloads from the exception handler pass through), `StandardPagination` (returns `{"success": True, "data": [...], "meta": {...}}`), `api_exception_handler` (maps DRF exceptions, `Http404`, Django `PermissionDenied`, `ValidationError`, and `IntegrityError` → 409; logs and hides unexpected errors), `validators.py` (phone regex, logo validators), `views.py` (health).

### 9.3 Auth app (`organizations`)
- Custom `TokenObtainPairSerializer` adds claims and returns the `user` payload; login view uses `throttle_scope="login"`, `permission_classes=[AllowAny]`, `authentication_classes=[]`.
- `MeView` returns user + organization + `capabilities_for(user.role)`.
- `LogoutView` blacklists the provided refresh token (must belong to the requesting user).
- Django admin: register Organization and User (superuser only) for convenience; ActivityLog read-only.

### 9.4 Services skeleton (`crm/services.py`)
```python
@transaction.atomic
def create_company(*, user, data) -> Company:
    company = Company.objects.create(organization_id=user.organization_id, **data)  # org from server, never from client
    log_activity(user=user, action=Action.CREATE, obj=company, changes=snapshot(company, data))
    return company

@transaction.atomic
def update_company(*, user, company, data) -> Company:
    remove_logo = data.pop("remove_logo", False)
    changes = diff_instance(company, data, remove_logo=remove_logo)   # BEFORE mutating
    old_logo = company.logo.name if company.logo else None
    ...apply fields, save()...
    log_activity(user=user, action=Action.UPDATE, obj=company, changes=changes)
    if old_logo and old_logo != (company.logo.name if company.logo else None):
        transaction.on_commit(lambda: default_storage.delete(old_logo))
    return company

@transaction.atomic
def delete_company(*, user, company) -> None:
    contacts = list(Contact.objects.for_org(user.organization_id).filter(company=company))
    now = timezone.now()
    company.is_deleted, company.deleted_at = True, now; company.save(update_fields=[...,"updated_at"])
    Contact.all_objects.filter(pk__in=[c.pk for c in contacts]).update(is_deleted=True, deleted_at=now, updated_at=now)
    log_activity(user=user, action=Action.DELETE, obj=company)
    bulk_log_activity(user=user, action=Action.DELETE, objs=contacts)
```
`create_contact` sets `organization_id = company.organization_id`. `update_contact` never changes `company`. Handle `IntegrityError` for the unique constraint by raising a validation error (or let the exception handler map it to 409).

### 9.5 Serializers & validation
- `CompanySerializer`: read fields `id, logo_url, contacts_count, created_at, updated_at`; write fields `name, industry, country, logo, remove_logo`. `logo_url` = `obj.logo.url if obj.logo else None`. **Do not expose `organization`.**
- Logo validation: extension in `.jpg/.jpeg/.png/.webp`, content type in `image/jpeg|png|webp`, size ≤ `MAX_LOGO_SIZE_MB` (default 2), and Pillow verification through `ImageField`. **SVG is not allowed** (script injection risk).
- `ContactSerializer`:
  - `company` uses a **tenant-scoped related field** whose `get_queryset()` returns `Company.objects.for_org(request.user.organization_id)`; cross-tenant/deleted company → `400` "Company not found." Read-only after creation.
  - `validate_email`: strip + lowercase, then reject if an active contact with the same email exists in the same company (exclude self on update). The DB constraint is the race-condition backstop.
  - `validate_phone`: optional; strip spaces; must match `^\d{8,15}$`; message "Phone must be 8–15 digits."
- Filters in `filters.py` with `django_filters.FilterSet`: `CompanyFilter`, `ContactFilter`, `ActivityLogFilter` (fields per §8).

### 9.6 Dashboard
Single query set per metric, all org-scoped: totals via `count()`, industries via `values("industry").annotate(count=Count("id")).order_by("-count")[:8]` (blank industry shown as "Unspecified"), recent activity only for roles with `activity_log:read`.

---

## 10. AWS S3 setup and access strategy

**Strategy (explain this in README and on camera):** the bucket is **private** (Block Public Access ON). The API uploads the file (server-side validated), stores only the object *key*, and returns a **short-lived presigned GET URL** (5 min) in `logo_url`. The browser loads it via `<img src>` (no CORS needed for images). Keys are namespaced `org-{id}/logos/{uuid}.{ext}` so tenant data is logically separated and the IAM policy can be scoped to that prefix. Trade-off: signed URLs change on every fetch (so browser caching is weaker), and server-side upload passes the bytes through the API; the scalable alternative is presigned POST direct-to-S3.

**HUMAN tasks (document them step by step in `docs/AWS_S3_SETUP.md`):**
1. Create (or use) an AWS account; enable MFA on root; create a **$1–5 AWS Budget alert**.
2. Create a bucket in one region (e.g. `ap-south-1`): **Block all public access = ON**, ACLs disabled (Bucket owner enforced), default encryption SSE-S3, versioning off.
3. Create a dedicated IAM user `crm-app-s3` (programmatic access only, no console) with this **least-privilege inline policy** (replace `BUCKET`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Sid": "LogoObjects", "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::BUCKET/org-*/logos/*" },
    { "Sid": "ListLogoPrefix", "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::BUCKET",
      "Condition": { "StringLike": { "s3:prefix": ["org-*/logos/*"] } } }
  ]
}
```
   (`ListBucket` is needed so `django-storages` `exists()` checks return 404 instead of 403 for missing keys.)
4. Put the access key in `backend/.env` only (git-ignored). **Never commit keys.** Note in README: on EC2/ECS/EKS use an **IAM role** and leave the key vars empty.
5. Upload only small test images (well inside Free Tier limits). Note that Free Tier terms depend on account age/plan; check what the account shows.

**Code side (Claude Code does this):**
```python
# settings (django-storages >= 1.14 style: STORAGES + OPTIONS; verify against the installed version's docs)
if env.bool("USE_S3", default=False):
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": env("AWS_STORAGE_BUCKET_NAME"),
            "region_name": env("AWS_S3_REGION_NAME"),
            "access_key": env("AWS_ACCESS_KEY_ID", default=None) or None,       # None → boto3 default chain (IAM role)
            "secret_key": env("AWS_SECRET_ACCESS_KEY", default=None) or None,
            "signature_version": "s3v4",
            "querystring_auth": True,                                            # presigned URLs
            "querystring_expire": env.int("AWS_QUERYSTRING_EXPIRE", default=300),
            "file_overwrite": False,
            "default_acl": None,
        },
    }
else:
    STORAGES["default"] = {"BACKEND": "django.core.files.storage.FileSystemStorage"}
    MEDIA_ROOT = BASE_DIR / "media"; MEDIA_URL = "/media/"   # serve via static() in dev only
```
- `upload_to` in `crm/storage.py`: `f"org-{instance.organization_id}/logos/{uuid4().hex}{ext.lower()}"` (organization must be set on the instance before saving the file).
- Tests use `FileSystemStorage` with a temp `MEDIA_ROOT`; never hit real S3 in tests/CI.

---

## 11. Frontend implementation guide

### 11.1 Architecture rules
- **Pages** compose **features/components**; **hooks** wrap TanStack Query; **api/** is the only place that knows URLs and axios; components never call axios directly.
- Server state lives in TanStack Query (`['companies', params]`, `['company', id]`, `['contacts', params]`, `['activity-logs', params]`, `['dashboard']`). Mutations invalidate related keys (contact mutations also invalidate `['companies']` for `contacts_count`, and all mutations invalidate `['activity-logs']` and `['dashboard']`).
- Global client state: `AuthContext` (user, status `loading|authenticated|anonymous`, `login`, `logout`, `can(resource, verb)`) and `ToastContext`.
- List state (page, search, filters, ordering) lives in the **URL query string** via `useListParams()` so reload/back/share work; changing any filter resets `page` to 1; search input is debounced (400 ms).

### 11.2 Centralized API layer (`src/api`)
- `client.ts`: one axios instance (`baseURL = import.meta.env.VITE_API_BASE_URL`).
  - **Request interceptor:** attach `Authorization: Bearer <access>` from `tokenStore`.
  - **Response interceptor:** on `401` (not from `/auth/*`, and not already retried): perform **one shared refresh** (single-flight promise), retry the original request; if refresh fails → clear tokens, set auth to anonymous, redirect to `/login`.
  - Unwrap the envelope: API functions return typed `{data, meta}` and never expose raw axios responses.
  - Normalize failures into `ApiError { status, code, message, fieldErrors }` (`errors.ts`).
- `tokenStore.ts`: access token in a module variable (memory); refresh token in `localStorage`.
- On app start `AuthContext` tries `refresh → /auth/me` to restore the session (show a full-page spinner while `loading`).

```ts
let refreshPromise: Promise<string> | null = null;
api.interceptors.response.use(undefined, async (error) => {
  const original = error.config;
  const isAuthCall = original?.url?.includes("/auth/");
  if (error.response?.status === 401 && !original._retry && !isAuthCall) {
    original._retry = true;
    refreshPromise ??= refreshAccessToken().finally(() => (refreshPromise = null));
    try {
      const token = await refreshPromise;
      original.headers.Authorization = `Bearer ${token}`;
      return api(original);
    } catch { authEvents.emit("logout"); }
  }
  return Promise.reject(toApiError(error));
});
```

### 11.3 Routing & guards
| Route | Component | Guard |
|---|---|---|
| `/login` | LoginPage | redirect to `/` if already authenticated |
| `/` | DashboardPage | ProtectedRoute |
| `/companies` | CompaniesPage | ProtectedRoute |
| `/companies/:id` | CompanyDetailPage | ProtectedRoute |
| `/activity` | ActivityLogPage | ProtectedRoute + `can("activity_log","read")` else Forbidden page |
| `*` | NotFoundPage | none |

`ProtectedRoute` waits on `loading`, then redirects anonymous users to `/login` (remember the intended path). `RoleGate` (`<RoleGate resource="company" verb="delete">…</RoleGate>`) hides UI by capability. Sidebar hides Activity Log for Staff.

### 11.4 Pages (functional spec)
1. **Login:** email + password (RHF + zod), submit spinner, inline server error (`Invalid email or password.`), shows demo credentials hint in dev only.
2. **Dashboard:** org name + plan badge; stat cards (Companies, Contacts); "Companies by industry" as simple CSS bars; "Recent activity" list (Admin/Manager only); loading skeleton and error banner with Retry.
3. **Companies:** search box, industry filter, country filter, ordering select; table (logo thumbnail or initials avatar, name → detail link, industry, country, contacts count, created date, actions); pagination; "New company" (A/M); edit (A/M); delete with `ConfirmDialog` (A). Company form modal: name, industry, country, logo file input with preview, client-side type/size check (mirrors the server), field errors mapped from `ApiError.fieldErrors`. Empty state and error/loading states.
4. **Company detail:** header card (logo, name, industry, country, created, contacts count) with Edit (A/M) and Delete (A; on success navigate to `/companies`); **Contacts section**: search, role filter, paginated table (name, email, phone, role, actions), "Add contact" (all roles), edit (A/M), delete (A); contact form modal (full name, email, phone, role) with server-side field errors (duplicate email, bad phone).
5. **Activity log:** table (time, user, action badge, model, object label + id, expandable "changes" diff), filters (model, action, date range), pagination, auto-refreshes via query invalidation after mutations.

### 11.5 Reusable components (build first, use everywhere)
`Button`, `Badge`, `Modal`, `ConfirmDialog`, `FormField` (label + input + error), `Spinner`, `ErrorBanner` (with retry), `EmptyState`, `DataTable<T>` (columns config, loading/empty/error slots), `Pagination` (uses `meta`), `SearchInput` (debounced), `AppLayout`/`Sidebar`/`Topbar` (org name, plan badge, user + role, logout), `ProtectedRoute`, `RoleGate`, toasts for success/error feedback.

### 11.6 Quality bar
Every data view has a loading state, an error state, and an empty state. Every mutation button shows a pending state and disables double-submit. No `any` without a comment. No business rules duplicated from the backend beyond convenience validation; capabilities come from `/auth/me`.

---

## 12. Testing plan (backend, `pytest-django`)

`conftest.py` provides: `org_a`, `org_b`; `admin_a`, `manager_a`, `staff_a`, `admin_b`; a helper `auth_client(user)` that issues a **real JWT** (with `org_id`/`role` claims) and sets the `Authorization` header, so the middleware is exercised; a temp `MEDIA_ROOT`; throttling disabled except in the throttle test.

**Must-have tests (target 30+ assertions across these files):**
- `test_auth.py`: login success/failure (generic message), refresh, logout blacklists, `me` includes capabilities, protected endpoint without/with expired token → `401`, user without org cannot log in.
- `test_tenant_isolation.py`: Org B user cannot list, retrieve, update, or delete Org A's company/contact/log (`404`); lists contain only own org; contact cannot be created for another org's company (`400`); cross-tenant `?company=` filter yields nothing; middleware resets the ContextVar between requests; manager `for_org` and ambient filter behave as documented.
- `test_rbac.py`: parametrized matrix (role × resource × verb) equals §7.2 exactly, including Staff creating contacts only, Manager cannot delete, Staff cannot read activity logs.
- `test_companies.py` / `test_contacts.py`: CRUD, pagination meta, search, filters, ordering, `contacts_count`, soft delete hides record, deleted company's contacts hidden, email reusable after soft delete.
- `test_validation.py`: invalid email; duplicate email in same company (`400`) but allowed in a different company; phone accepts 8–15 digits, rejects 7/16 digits/letters, optional; logo rejects wrong type/oversize/SVG.
- `test_activity_log.py`: exactly one log row per create/update/delete with correct user, action, model, object id; company delete logs company + each cascaded contact; update `changes` diff correct; log write failure rolls back the change; logs are org-scoped.
- `test_envelope.py`: success and error shapes; `500` hides internals; `404` shape.
- `test_dashboard.py`: totals correct and org-scoped; Staff gets empty `recent_activity`.
- `test_seed.py` (light): `seed_demo` is idempotent.

**Frontend (optional, only if time allows):** Vitest for `ProtectedRoute` redirect, `Pagination` behavior, and the axios refresh single-flight.

CI must run: `ruff check`, `ruff format --check`, `pytest --cov`, frontend `npm run lint`, `tsc --noEmit`, `npm run build`.

---

## 13. DevOps

### 13.1 Docker Compose (dev)
- `db`: `postgres:16-alpine`, env from root `.env`, **named volume**, healthcheck (`pg_isready`), host port `5433:5432`.
- `backend`: builds `backend/`, `depends_on: db (service_healthy)`, env file `backend/.env` with `DATABASE_URL` overridden to host `db:5432`, runs `migrate` then `runserver 0.0.0.0:8000`, bind-mount source for hot reload, port `8000`.
- `frontend`: Node image, `npm run dev -- --host`, bind mount, port `5173`.
- Also document the hybrid flow (DB in Docker; backend/frontend run natively).

### 13.2 Production-style build
- `backend/Dockerfile`: multi-stage, non-root user, `pip install -r requirements/prod.txt`, `collectstatic`, `entrypoint.sh` (wait/migrate optional via env), `gunicorn config.wsgi`.
- `frontend/Dockerfile`: build stage (`npm ci && npm run build`) → `nginx:alpine` serving `dist/` with SPA fallback (`try_files $uri /index.html`).
- `docker-compose.prod.yml`: db + backend (gunicorn, `config.settings.prod`) + frontend (nginx). Secrets via env, never baked into images. Add `.dockerignore` files.

### 13.3 Makefile targets
`up`, `down`, `logs`, `migrate`, `makemigrations`, `seed`, `test`, `lint`, `fmt`, `shell`, `frontend-dev`, `build`.

### 13.4 GitHub Actions (`.github/workflows/ci.yml`)
Two jobs: **backend** (Postgres service container, Python 3.12, cache pip, `ruff`, `pytest --cov`, `manage.py check --deploy` with prod settings and dummy env) and **frontend** (Node LTS, `npm ci`, lint, typecheck, build, optional vitest). Trigger on push and PR to `main`.

---

## 14. Seed data (`python manage.py seed_demo`)

Idempotent; refuses to run when `DEBUG=False` unless `--force`. Creates via the **service layer** so the activity log is populated realistically:

| Org | Plan | Users (password printed at the end: `Passw0rd!123`) |
|---|---|---|
| Acme Travel | PRO | `admin@acme.test`, `manager@acme.test`, `staff@acme.test` |
| Blue Sky Tours | BASIC | `admin@bluesky.test`, `manager@bluesky.test`, `staff@bluesky.test` |

Data: Acme gets ~13 companies (enough to paginate at page size 10, varied industries/countries incl. one named "Sunrise Hotels") and ~30 contacts; Blue Sky gets ~4 companies and ~8 contacts, **including a company with the same name and a contact with the same email as one in Acme** (proves uniqueness and isolation are per-tenant). At the end print a **"cross-tenant demo" hint**: the ID of an Acme company and the URL a Blue Sky user should try. A `--reset` flag wipes demo orgs first.

---

## 15. Documentation deliverables

### 15.1 `README.md`
Overview and feature list → architecture summary (link to `docs/ARCHITECTURE.md`) → tech stack → **quick start** (`cp .env.example .env`, `cp backend/.env.example backend/.env`, `docker compose up --build`, `make seed`, open `http://localhost:5173`) → demo credentials → env var table → **Tenant isolation explained** (4 layers) → **RBAC matrix** → **Soft delete & audit log** → **S3 bucket access strategy** (public vs signed URLs; why signed) → dev vs prod configuration → API overview + link to `/api/v1/docs/` → testing commands → trade-offs & future work (Postgres RLS, Celery for async audit, presigned POST, httpOnly-cookie refresh, rate limiting, Kubernetes, observability).

### 15.2 `docs/ARCHITECTURE.md`
Mermaid: component diagram (React → API → services → Postgres/S3), the ERD (§6), the request/tenancy sequence (§7.1), and the RBAC matrix.

### 15.3 `docs/SRS.md` (short; 1–2 pages)
Purpose, scope, actors/roles, functional requirements (numbered FR-1..), non-functional requirements (security, isolation, auditability, performance basics, maintainability), constraints, assumptions, use-case list (login, manage company, manage contact, view audit log), and acceptance criteria. Reference the traceability table (§2).

### 15.4 `docs/DECISIONS.md` and `docs/AWS_S3_SETUP.md`
ADR-lite entries for every row in §3 plus any deviation. AWS doc contains §10's human steps with screenshots optional.

### 15.5 `docs/RECORDING_SCRIPT.md` (HUMAN records; 15–20 min, target 17)
1. **System overview & architecture (3 min):** diagram, four isolation layers, service layer + audit, why 404 not 403, middleware/ContextVar caveat.
2. **Auth flow (2 min):** login, JWT claims, refresh, protected routes, expired/no token behavior.
3. **Tenant isolation live (3 min):** log in as Acme admin, copy a company URL/ID; log in as Blue Sky → paste it → "not found"; show lists differ.
4. **RBAC (2 min):** Admin vs Manager vs Staff in UI *and* a forbidden direct API call (Swagger or curl).
5. **CRUD (4 min):** company create with logo (show the presigned URL and that the bucket is private), edit, search/filter/pagination, nested contacts, validation errors (duplicate email, bad phone), soft delete.
6. **Activity log (2 min):** show entries for the actions just performed; quick tour of `services.py`.
7. **Production readiness & trade-offs (1 min):** env vars, CORS, Docker, CI, and what you would do next.

---

## 16. Phased build plan (tick boxes as you go)

> Hours are guidance for a ~20 h window; **gates matter more than the clock**. If behind, use the cut list in §17.2.

### Phase 0: Foundation (~0.75 h)
- [x] `git init`, `.gitignore` (python, node, `.env`, `media/`, `*.sqlite3`, `.DS_Store`), README stub, `CLAUDE.md` (`@PROJECT_PLAN.md`)
- [x] Root `docker-compose.yml` with `db` (healthcheck + volume); root `.env.example`
- [x] Django project skeleton, settings split, ~~`requirements/{base,dev,prod}.txt`~~ uv `pyproject.toml` + `uv.lock` (D-001), `pyproject.toml` (ruff, pytest), backend `.env.example`
- [x] Vite + React + TS + Tailwind + eslint/prettier scaffold, frontend `.env.example`
- [x] `Makefile`
- [ ] `HUMAN:` AWS budget + bucket + IAM user + keys (§10); create GitHub repo and push
- **Done when:** `docker compose up db` healthy; `python manage.py check` passes; `npm run dev` renders a page.
- Commit e.g.: `chore: scaffold backend, frontend and docker compose`

### Phase 1: Core, tenancy, users, auth (~2 h)
- [x] `core`: tenancy ContextVar, managers, `TenantModel`, `TenantContextMiddleware`, `RolePermission`, `IsSameOrganization`, `OrganizationScopedViewSet`, pagination, renderer, exception handler, health endpoint
- [x] `organizations`: `Organization`, `User` (+manager, check constraint), `roles.py` (matrix + `capabilities_for`), migrations, admin
- [x] Auth endpoints: login (custom claims, throttle), refresh, logout (blacklist), me
- [x] `conftest.py` + `test_auth.py`, `test_envelope.py`
- **Done when:** curl login returns tokens; `/auth/me` returns capabilities; no token → `401` in envelope; tests green.
- Commits: `feat(core): tenant base model, managers, middleware`, `feat(auth): JWT login/refresh/logout/me`

### Phase 2: Activity log + CRM models (~1.25 h)
- [x] `activity`: model, `log_activity`/`bulk_log_activity`, serializer, filterset, read-only viewset, migrations
- [x] `crm`: `Company`, `Contact` (constraints, indexes), `storage.py` upload path, admin, migrations
- **Done when:** migrations apply on a fresh DB; constraint tests for partial unique index pass.

### Phase 3: CRM API (~1.75 h)
- [ ] Serializers (tenant-scoped `company` field, validators, `logo_url`, `contacts_count`)
- [ ] `services.py` (create/update/delete for both models, audit, cascade)
- [ ] Viewsets, `filters.py`, URL routing under `/api/v1/`, dashboard stats endpoint
- [ ] Tests: companies, contacts, validation, soft delete, activity log, RBAC matrix, tenant isolation, dashboard
- **Done when:** all §12 backend tests for these areas pass; a cross-tenant ID returns `404`; each write yields the right log rows.
- Commits: `feat(crm): company and contact services with audit logging`, `feat(crm): viewsets, filters, pagination`, `test: tenant isolation and rbac matrix`

### Phase 4: S3 storage & logos (~1 h)
- [ ] Storage switch in settings (§10), logo validators, replace/remove logo behavior, `on_commit` cleanup
- [ ] Manual verification with real bucket (`HUMAN:` provides keys): upload → object appears under `org-{id}/logos/`; `logo_url` opens; bucket is not public; a URL after expiry fails
- [ ] `docs/AWS_S3_SETUP.md`
- **Done when:** logo upload works locally (FileSystemStorage) and on S3.

### Phase 5: Seed, API docs, hardening (~1.25 h)
- [ ] `seed_demo` command (§14), `test_seed.py`
- [ ] drf-spectacular schema + Swagger (`/api/v1/docs/`), tags and descriptions
- [ ] Throttle test, security settings review, structured logging, `ruff` clean, coverage report
- **Done when:** `make seed` then login works as all six users; Swagger renders; `make test` green.

### Phase 6: Frontend foundation (~1.5 h)
- [ ] `api/` layer (client, tokenStore, errors, types, per-resource modules), `AuthContext`, `ToastContext`
- [ ] Router + `ProtectedRoute` + `RoleGate` + `AppLayout`
- [ ] UI kit: Button, Badge, Modal, ConfirmDialog, FormField, Spinner, ErrorBanner, EmptyState, DataTable, Pagination, SearchInput
- [ ] Login page working end-to-end (login, refresh-on-401, logout, session restore)
- **Done when:** you can log in/out, reload and stay logged in, and an expired access token refreshes transparently.

### Phase 7: Frontend pages (~4 h)
- [ ] Companies page (search/filter/order/pagination in URL, create/edit/delete, logo upload)
- [ ] Company detail with nested contacts (search, pagination, CRUD, field errors)
- [ ] Activity log page (filters, pagination, changes expander)
- [ ] Dashboard (cards, industry bars, recent activity)
- [ ] Loading/error/empty states everywhere; role-based hiding; toasts
- [ ] Optional Vitest tests
- **Done when:** the full demo script in §15.5 can be performed without touching the API manually (except the forbidden-call demo).
- Commits per page: `feat(ui): companies page with filters and pagination`, etc.

### Phase 8: Production readiness & CI (~1.5 h)
- [ ] `backend/Dockerfile`, `frontend/Dockerfile` + `nginx.conf`, `docker-compose.prod.yml`, `.dockerignore`s
- [ ] `prod.py` hardening verified with `manage.py check --deploy`
- [ ] GitHub Actions CI green on `main`
- [ ] Fresh-clone test: clone into a new folder, follow README exactly, everything works
- **Done when:** CI badge green; `docker compose -f docker-compose.prod.yml up --build` serves the app.

### Phase 9: Documentation (~1.25 h)
- [ ] `README.md`, `docs/ARCHITECTURE.md`, `docs/SRS.md`, `docs/DECISIONS.md`, `docs/RECORDING_SCRIPT.md`
- [ ] Screenshots optional (login, companies, activity log)
- **Done when:** a stranger could run and understand the project from the README alone.

### Phase 10: Rehearse, record, submit (~2.5 h) `HUMAN`
- [ ] Reseed, rehearse once, record 15–20 min (§15.5), verify audio/screen legibility
- [ ] Final QA (§17.1), push, share repo + recording per the instructions given by the employer

---

## 17. Definition of done & cut list

### 17.1 Final QA checklist
- [ ] Fresh clone → README steps → app runs; seed users can log in
- [ ] Org B cannot see or touch Org A data by any endpoint (list, detail, update, delete, `?company=`, activity logs, dashboard)
- [ ] RBAC matrix verified in tests and manually (UI and API)
- [ ] Every create/update/delete on Company/Contact creates the expected log rows; cascade logs present
- [ ] Soft-deleted records disappear everywhere; email reusable after delete
- [ ] Logo uploads to a **private** bucket; `logo_url` is presigned and expires; no AWS keys anywhere in git (`git log -p | grep -i AKIA` returns nothing; `.env` ignored)
- [ ] Validation: email format, per-company uniqueness, phone 8–15 digits optional
- [ ] Consistent envelope for success and error; no stack traces in `500`
- [ ] CORS restricted to configured origins; prod settings pass `check --deploy`
- [ ] Frontend: protected routes, loading/error/empty states, pagination, no console errors
- [ ] CI green; `ruff`, `tsc`, tests pass; commit history is meaningful
- [ ] Recording complete, 15–20 min, covers overview, auth, CRUD, activity log, architecture decisions

### 17.2 Cut list (if time runs short, cut in this order, never cut the last four)
1. Vitest frontend tests → 2. Dashboard industry bars (keep counts) → 3. `docker-compose.prod.yml` and frontend Dockerfile (keep backend Dockerfile) → 4. Date-range filters on activity log → 5. `remove_logo`/on-commit S3 cleanup → 6. `seed_demo --reset`.
**Never cut:** tenant isolation, RBAC, audit log, README.

---

## 18. Pitfalls checklist (know these before you code)

1. **DRF auth is view-level:** middleware cannot read `request.user`; decode the JWT claim (§7.1) and still filter explicitly in views.
2. **Cross-tenant foreign keys:** any `PrimaryKeyRelatedField` must use a tenant-scoped queryset.
3. **Uniqueness + soft delete:** a plain `unique_together` blocks re-use of an email after deletion; use the **conditional** `UniqueConstraint`.
4. **Signals can't see the acting user;** use the service layer.
5. **`QuerySet.update()` skips `auto_now`** and skips signals; set `updated_at` yourself.
6. **`upload_to` needs `instance.organization_id` set** before the file is saved.
7. **`ListBucket` permission** is required for `django-storages` existence checks; without it S3 returns 403 instead of 404.
8. **Do not put signed URLs in the audit log** or database; store keys.
9. **401 vs 403 vs 404:** unauthenticated = 401; authenticated but role denied = 403; other tenant's object = 404.
10. **Refresh races:** multiple parallel 401s must share one refresh call.
11. **N+1 queries:** `select_related("user")` for logs, annotate `contacts_count`, avoid per-row queries in serializers.
12. **CORS preflight:** `CorsMiddleware` must sit above `CommonMiddleware`; allow only the configured frontend origin(s).
13. **ContextVar hygiene:** always reset in `finally`; tests must prove there is no leakage.
14. **Throttling in tests:** disable or use a locmem cache and clear it between tests.
15. **Envelope vs OpenAPI:** the generated schema shows raw serializers; state that in the README instead of spending time on schema post-processing.
16. **Secrets:** `.env` git-ignored from the first commit; if a key is ever committed, rotate it immediately (removing it from history is not enough).
