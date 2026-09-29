# Enclave CRM

[![CI](https://github.com/cnkarunarathna/enclave-crm/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/cnkarunarathna/enclave-crm/actions/workflows/ci.yml)

A multi-tenant CRM built with Django REST Framework, React, PostgreSQL and AWS S3. Many
organizations share one deployment. Each one manages its own companies and contacts, with
role-based access (Admin, Manager, Staff) and a full audit log. No user can ever read or change
another organization's data.

![Dashboard](docs/screenshots/dashboard.png)

## Contents

- [Features](#features)
- [Quick start](#quick-start-everything-in-docker)
- [Demo accounts](#demo-accounts)
- [Architecture](#architecture)
- [Tenant isolation](#tenant-isolation)
- [Roles and permissions](#roles-and-permissions)
- [Soft delete and the activity log](#soft-delete-and-the-activity-log)
- [Logo storage on S3](#logo-storage-on-s3)
- [Configuration](#configuration)
- [API](#api)
- [Testing and quality](#testing-and-quality)
- [Trade-offs and future work](#trade-offs-and-future-work)

## Features

- **Organizations and users:** every user belongs to one organization and has one role. Login
  uses JWT access and refresh tokens, with rotation, logout (blacklisting) and rate limiting.
- **Companies:** create, edit and delete; logo upload to a private S3 bucket. Search, filters
  (industry, country, created date), sorting and pagination.
- **Contacts:** managed from their company's page. Email is validated and unique within its
  company; phone is optional (8–15 digits). Search, a job-title filter and pagination.
- **Soft delete** everywhere. Deleting a company also removes its contacts.
- **Activity log:** every create, update and delete, with the user and the old → new values.
  Admins and Managers can see it; it can't be edited.
- **Dashboard:** totals, companies by industry and recent activity.
- **API:** versioned (`/api/v1/`), with one response envelope, central error handling and
  OpenAPI/Swagger docs.
- **Frontend:** React + TypeScript, responsive on desktop and mobile. Routes are protected and
  role-aware. Every view has loading, empty and error states, and list filters live in the URL.
- **Delivery:** Docker for development and production, GitHub Actions CI, git hooks that run the
  same checks, and demo data for two organizations.

| Companies | Company detail with contacts |
|---|---|
| ![Companies](docs/screenshots/companies.png) | ![Company detail](docs/screenshots/company-detail.png) |

| Activity log | Mobile |
|---|---|
| ![Activity log](docs/screenshots/activity-log.png) | <img src="docs/screenshots/companies-mobile.png" alt="Companies on a phone" width="260"> |

## Prerequisites

- Docker (Docker Desktop or Docker Engine with Compose v2)
- For running natively and for the git hooks: [uv](https://docs.astral.sh/uv/) (installs
  Python 3.12 automatically) and Node.js 24 LTS + npm

## Quick start (everything in Docker)

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

docker compose up --build        # db + API on :8000 + frontend on :5173 (hot reload)
docker compose exec backend python manage.py seed_demo   # in a second terminal
```

Open http://localhost:5173 and sign in with a [demo account](#demo-accounts). The API docs are at
http://localhost:8000/api/v1/docs/.

Logos are stored in `backend/media/` until S3 is configured (see
[docs/AWS_S3_SETUP.md](docs/AWS_S3_SETUP.md)).

## Quick start (native, database in Docker)

Faster reloads, and this is what the git hooks use. After the three `cp` commands above:

```bash
make install          # uv sync (backend) + npm ci (frontend, also installs git hooks)
make up               # Postgres 16 only, on localhost:5433
make migrate
make seed

make backend-dev      # http://localhost:8000
make frontend-dev     # http://localhost:5173 (in a second terminal)
```

## Production-style stack

`docker-compose.prod.yml` runs what a deployment would:
- the API with prod settings under gunicorn (non-root user, `DEBUG=False`, JSON logs, API docs
  off)
- behind nginx, which serves the built frontend and proxies `/api/` to the backend, so the
  browser talks to a single origin

```bash
# in the root .env: set DJANGO_SECRET_KEY (the command is in .env.example)
make prod-up          # builds images, migrates, waits until healthy: http://localhost:8080
make prod-seed        # demo data (seed_demo --force, since DEBUG is off)
make prod-down
```

It reuses `backend/.env` for the S3 settings, has its own database volume (project `crm-prod`),
and turns off the HTTPS redirect because there is no TLS locally. Behind a real HTTPS load
balancer, leave `DJANGO_SECURE_SSL_REDIRECT` at its default (`True`).

## Demo accounts

`seed_demo` creates two organizations. Every account's password is `Passw0rd!123`.

| Organization | Plan | Admin | Manager | Staff |
|---|---|---|---|---|
| Acme Travel | Pro | `admin@acme.test` | `manager@acme.test` | `staff@acme.test` |
| Blue Sky Tours | Basic | `admin@bluesky.test` | `manager@bluesky.test` | `staff@bluesky.test` |

About the demo data:
- **Acme** has 13 companies (two pages) and 29 contacts. **Blue Sky** has 4 companies and 8
  contacts.
- Both organizations have a company called "Sunrise Hotels" and a contact with the same email,
  which shows that uniqueness and isolation are per tenant.
- At the end, the command prints the id of an Acme company to try as a Blue Sky user; the result
  is "not found".

The command is idempotent:
- `--reset` wipes the demo organizations first.
- It refuses to run with `DEBUG=False` unless you pass `--force`.

## Architecture

```
React SPA ──HTTPS + JWT──▶ Django REST Framework ──▶ PostgreSQL
 pages → hooks → api/      middleware → views → serializers
                           → services (write + audit log, one transaction)   ──▶ S3 (private)
```

| Layer | Responsibility |
|---|---|
| `apps/core` | Tenancy building blocks (base model, managers, middleware), permissions, base viewsets, response envelope, error handling, validators |
| `apps/organizations` | Organization, User, roles and permission matrix, auth endpoints, `seed_demo` |
| `apps/crm` | Company and Contact: models, serializers, filters, viewsets, **services** |
| `apps/activity` | The append-only activity log and its read-only API |
| `apps/dashboard` | Stats endpoint |
| `frontend/src` | `api/` (the only place that knows URLs), `hooks/` (TanStack Query), `components/`, `features/`, `pages/` |

Views are thin: validate with the serializer, call a service, return the result. The full
picture, with an ERD, a request sequence diagram and the deployment shape, is in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

Other documents:
- [docs/SRS.md](docs/SRS.md): requirements.
- [docs/DECISIONS.md](docs/DECISIONS.md): every design decision and its reasons.
- [docs/RECORDING_SCRIPT.md](docs/RECORDING_SCRIPT.md): the demo walkthrough.

**Tech stack**
- **Backend:**
  - Python 3.12, Django 5.2 LTS, Django REST Framework, simplejwt
  - django-filter, drf-spectacular, django-storages + boto3, Pillow
  - psycopg 3, gunicorn, WhiteNoise
  - uv, ruff, pytest
- **Frontend:**
  - Vite, React 19, TypeScript (strict), React Router
  - TanStack Query, axios, react-hook-form + zod
  - Tailwind CSS 4, shadcn/ui (Radix)
  - Vitest, ESLint, Prettier
- **Infrastructure:** PostgreSQL 16, Docker Compose, nginx, GitHub Actions, husky.

## Tenant isolation

Isolation is enforced in four layers, so a mistake in one doesn't expose data:

1. **Schema:** every tenant model (`Company`, `Contact`, `ActivityLog`) has a non-null
   `organization` foreign key. Contacts inherit their company's organization, and the model
   refuses a mismatch.
2. **Queries (the primary control):** every viewset starts from
   `Model.objects.for_org(request.user.organization_id)`. DRF's `get_object()` uses that
   queryset, so another organization's id returns **404**. It looks exactly like a missing
   record; a 403 would confirm that the id exists.
3. **Manager:** the default manager additionally filters by the organization of the current
   request, held in a `ContextVar`, and hides soft-deleted rows.
4. **Middleware:** `TenantContextMiddleware` sets that `ContextVar` from the signed JWT's
   `org_id` claim and always resets it. It has to decode the token itself, because DRF
   authenticates inside the view.

Layers 2 and 3 are combined with AND. If they ever disagreed (say, a token's `org_id` differs
from the user's organization), queries return nothing rather than the wrong tenant's data.

Three related rules close the remaining gaps:
- Serializer fields that point at tenant data only accept the user's own records; you can't add
  a contact to another organization's company.
- The audit writer refuses cross-organization entries.
- `tests/test_tenant_isolation.py` checks all of this over the real API.

## Roles and permissions

| Resource | Action | Admin | Manager | Staff |
|---|---|:-:|:-:|:-:|
| Company | view | ✓ | ✓ | ✓ |
| Company | create / edit | ✓ | ✓ | ✗ |
| Company | delete | ✓ | ✗ | ✗ |
| Contact | view / create | ✓ | ✓ | ✓ |
| Contact | edit | ✓ | ✓ | ✗ |
| Contact | delete | ✓ | ✗ | ✗ |
| Activity log | view | ✓ | ✓ | ✗ |
| Dashboard | view | ✓ | ✓ | ✓ (without recent activity) |

How it works:
- **One source of truth:** the matrix lives in `apps/organizations/roles.py`.
- **Server-side enforcement:** `RolePermission` enforces it on every request and denies
  anything not listed. It reads the role from the database, so a role change applies
  immediately.
- **UI:** the frontend receives the same matrix as `capabilities` from `/auth/me/` and hides what
  a role can't do. That's a convenience only; the API is the control.
- **Tests:** `tests/test_rbac.py` checks every cell of the table.

## Soft delete and the activity log

**Every write goes through the service layer.** All creates, updates and deletes of companies and
contacts go through `apps/crm/services.py`. Each service function runs in one database
transaction: it makes the change and writes the `ActivityLog` row. If the log write fails, the
change is rolled back, so nothing is ever changed without a record of it.

| Change | Log entries | Recorded values |
|---|---|---|
| Create | 1 `CREATE` | All fields set |
| Update | 1 `UPDATE` | Changed fields only, old → new |
| Delete a company | 1 `DELETE`, plus 1 `DELETE` per contact it removes | none |
| Delete a contact | 1 `DELETE` | none |

- **Services, not signals:** signals can't know which user acted.
- **Logos** are recorded by their storage key, never by a signed URL.
- **The log is append-only:** it has no update or delete endpoints, it's read-only in Django
  admin, and the model refuses updates.

**Soft delete:** deleting sets `is_deleted` and `deleted_at`; the row stays.
- The default manager hides deleted rows everywhere: lists, detail pages, counts and uniqueness
  checks.
- Contact email uniqueness uses a *partial* unique index (active rows only), so a deleted
  contact's email can be reused.

## Logo storage on S3

**The bucket is private (Block Public Access on).** The flow:
1. The API validates each upload: JPEG, PNG or WebP (no SVG, which can carry scripts), real image
   content, at most 2 MB.
2. It stores the file under `org-{id}/logos/{uuid}.{ext}` and saves only the key.
3. Every API response then includes a **presigned URL that expires after 5 minutes**. The
   browser loads it directly from S3 with a normal `<img>` tag.

Why presigned URLs rather than public ones:
- A public URL would let anyone who ever saw it fetch another tenant's logo, forever.
- Keys are namespaced per organization, and the app's IAM user can only touch `org-*/logos/*`.
- **Credentials** come only from environment variables. In production on AWS, leave the key
  variables empty and boto3 uses the instance's or task's IAM role.

What it costs:
- Signed URLs change on every response, so browsers cache logos less well.
- Uploads pass through the API. Presigned POST (browser → S3 directly) is the scalable
  alternative.

When a logo is replaced or removed, the old file is deleted after the transaction commits.
Soft-deleted companies keep their logo. With `USE_S3=False`, the same code stores files locally,
so development and tests never need AWS.

Setting up the bucket and IAM user, step by step: [docs/AWS_S3_SETUP.md](docs/AWS_S3_SETUP.md).

## Configuration

All configuration comes from environment variables; nothing secret is in the repository. Each
`.env.example` documents its variables. Copy it to `.env` (git-ignored).

**`backend/.env`**

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.dev` | `config.settings.dev` or `config.settings.prod` |
| `DJANGO_SECRET_KEY` | dev only | Signs sessions and JWTs; **required** in prod |
| `DJANGO_DEBUG` | `True` in dev | Always `False` in prod |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Required in prod |
| `DATABASE_URL` | `postgres://crm:crm@localhost:5433/crm` | Required in prod |
| `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` | `http://localhost:5173` in dev | Explicit list; never "allow all" |
| `JWT_ACCESS_MINUTES`, `JWT_REFRESH_DAYS` | `15`, `7` | Token lifetimes |
| `LOG_LEVEL`, `LOG_FORMAT` | `INFO`, `text` (`json` in prod) | Logging |
| `TRUSTED_PROXY_COUNT` | `0` | Reverse proxies in front of the API (for the client IP used by rate limiting) |
| `API_DOCS_ENABLED` | on in dev, off in prod | Serve `/api/v1/schema/` and `/api/v1/docs/` |
| `MAX_LOGO_SIZE_MB` | `2` | Logo upload limit |
| `USE_S3` | `False` | Store logos in S3 instead of `backend/media/` |
| `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME` | | Bucket and region |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | | Leave empty on AWS to use an IAM role |
| `AWS_QUERYSTRING_EXPIRE` | `300` | Presigned URL lifetime in seconds |
| `DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_SECURE_HSTS_SECONDS` | `True`, 30 days | Prod HTTPS settings |
| `CACHE_URL` | `dbcache://django_cache` | Prod cache shared by all workers (rate-limit counters) |

**Root `.env`:** `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` (the database container),
and `DJANGO_SECRET_KEY` for the production-style stack.

**`frontend/.env`:** `VITE_API_BASE_URL` (default `http://localhost:8000/api/v1`; the production
image uses `/api/v1`).

**Development vs production**

| Concern | Development (`dev.py`) | Production (`prod.py`) |
|---|---|---|
| Debug | On | Off, always |
| Secrets | Dev default allowed | Secret key, hosts and database URL required |
| Server | `runserver` | gunicorn behind nginx, non-root user |
| HTTPS | Off | SSL redirect, HSTS, secure cookies, proxy SSL header |
| Static files | Django | WhiteNoise, compressed and hashed |
| API docs / browsable API | On | Off (JSON only) |
| Logs | Readable text | JSON, one object per line |
| Cache | In memory | Shared database cache |

`python manage.py check --deploy` passes with the production settings, and CI checks it on every
PR.

## API

Base path: `/api/v1/`. The interactive docs are at `/api/v1/docs/` (Swagger UI) and the schema
at `/api/v1/schema/`; both are on in development. The schema describes the raw serializers; the
envelope below wraps every real response.

| Method | Path | Notes |
|---|---|---|
| `POST` | `/auth/login/` | `{email, password}` → `{access, refresh, user}`; 10/min per IP |
| `POST` | `/auth/refresh/` | `{refresh}` → new `{access, refresh}` (old one revoked) |
| `POST` | `/auth/logout/` | `{refresh}` → revokes it |
| `GET` | `/auth/me/` | User, organization, capabilities |
| `GET`, `POST` | `/companies/` | `?search=`, `?industry=`, `?country=`, `?created_after=`, `?created_before=`, `?ordering=name`, `?page=`, `?page_size=` (max 100). `POST` accepts JSON or multipart (logo) |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/companies/{id}/` | `PATCH` with a new `logo`, or `remove_logo=true` |
| `GET` | `/companies/facets/` | Distinct industries and countries (filter options) |
| `GET`, `POST` | `/contacts/` | `?company=`, `?role=`, `?search=`, `?ordering=` |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/contacts/{id}/` | `company` can't change |
| `GET` | `/activity-logs/`, `/activity-logs/{id}/` | `?model_name=`, `?action=`, `?user=`, `?object_id=`, `?timestamp_after=`, `?timestamp_before=`, `?search=` |
| `GET` | `/dashboard/stats/` | Totals, companies by industry, recent activity |
| `GET` | `/health/` | Checks the database; no auth |

Every response uses the same envelope:

```json
{"success": true, "message": "", "data": [ ... ], "meta": {"count": 13, "page": 1, "page_size": 10, "total_pages": 2}}
{"success": false, "message": "Validation failed.", "code": "validation_error",
 "errors": {"email": ["A contact with this email already exists for this company."]}}
```

| Status | `code` | When |
|---|---|---|
| 400 | `validation_error` | Invalid input (per-field `errors`) |
| 401 | `not_authenticated` | Missing, invalid or expired token |
| 403 | `permission_denied` | The role isn't allowed |
| 404 | `not_found` | Missing, deleted, **or another organization's** record |
| 409 | `conflict` | A unique constraint lost a race |
| 429 | `throttled` | Too many login attempts |
| 500 | `server_error` | Unexpected; a generic message only, details go to the server log |

Deletes return `200` with `data: null`, so every response has the same shape.

## Testing and quality

```bash
make test     # backend: pytest + coverage (fails under 90%); frontend: Vitest
make lint     # ruff (lint + format), ESLint, tsc, Prettier
make fmt      # auto-fix formatting
```

**Backend tests** (163 of them, about 97% coverage) are in `backend/tests/`, one file per
concern. They use real JWTs, so the middleware runs as it would in production.

| File | What it covers |
|---|---|
| `test_tenant_isolation.py` | Cross-tenant list, detail, update, delete, filters, logs, dashboard, stale token claims |
| `test_rbac.py` | Every role × resource × action |
| `test_activity_log.py` | Log rows per write, cascades, diffs, rollback on failure |
| `test_auth.py` | Login, refresh, logout, me, expired or missing tokens |
| `test_validation.py` | Email, phone, duplicates, logo type and size |
| `test_companies.py`, `test_contacts.py` | CRUD, pagination, search, filters, ordering, soft delete |
| `test_tenancy_middleware.py`, `test_envelope.py` | ContextVar reset, response shapes |
| `test_crm_models.py`, `test_dashboard.py`, `test_hardening.py`, `test_seed.py` | Constraints, stats, throttling, logging, seed idempotency |

**Frontend tests** (Vitest + Testing Library) cover:
- the token refresh being shared across parallel 401s
- error normalization
- `ProtectedRoute`
- `Pagination`
- mapping server field errors onto form fields

**CI** (GitHub Actions, on every PR into `master` and every push to `master`) runs three jobs:
- **Backend:** ruff, the migrations check, pytest with the coverage gate, and `check --deploy`.
- **Frontend:** lint, typecheck, format check, tests and build.
- **Docker:** builds both images, starts the production-style stack and smoke-tests it through
  nginx.

### Git hooks (husky)

The same checks as CI run locally, so problems are caught before a push:

| Hook | Runs |
|---|---|
| `pre-commit` (~2 s) | ruff lint + format check, ESLint, Prettier check, `tsc` |
| `pre-push` (~10 s) | migrations check, pytest (needs `make up`), Vitest, frontend build |

Hooks are installed by `npm ci` in `frontend/`. Fix formatting failures with `make fmt`.
Bypass in an emergency with `--no-verify`. If your editor's git can't find `uv` or `npm`,
add your PATH to `~/.config/husky/init.sh`.

Backend dependencies are managed with uv: add one with `cd backend && uv add <pkg>`
(or `uv add --dev <pkg>`), which updates `pyproject.toml` and `uv.lock`.

### Common commands

| Command | What it does |
|---|---|
| `make up` / `make stack` / `make down` | Database only / full dev stack in Docker / stop everything |
| `make migrate` / `make makemigrations` | Django migrations |
| `make seed` | Demo data (native) |
| `make shell` | Django shell |
| `make build` | Build the production images |
| `make prod-up` / `prod-seed` / `prod-logs` / `prod-down` | Production-style stack on :8080 |

## Trade-offs and future work

Choices made for this scope, and what would come next:

- **PostgreSQL Row-Level Security.** Isolation is enforced in the application today (four
  layers). RLS would also enforce it inside the database, so even a raw SQL mistake couldn't
  cross tenants.
- **Refresh token in an httpOnly cookie.** It's in `localStorage` today (access token in memory
  only), which script injection could read. Rotation, blacklisting and a strict CSP reduce the
  risk; a `SameSite` cookie removes it.
- **Presigned POST uploads.** Logos go through the API today; direct browser-to-S3 uploads
  would scale better. CloudFront with signed cookies would improve logo caching.
- **Redis** for the shared cache and rate limiting (the production cache is the database
  today), and throttles for more endpoints.
- **Asynchronous work (Celery):** only worth it if audit logging or uploads get heavy; logging
  inside the transaction is what guarantees that nothing goes unaudited.
- **Observability:** metrics, tracing and error tracking (for example Sentry) on top of the JSON
  logs.
- **Deployment:** infrastructure as code for AWS (ECS or Kubernetes, RDS, IAM roles instead of
  keys).
- **Not built, by design:**
  - user management UI, self-registration, password reset and email
  - enforcing billing plans (the plan is stored only)
  - restoring deleted records
  - real-time updates and internationalization
