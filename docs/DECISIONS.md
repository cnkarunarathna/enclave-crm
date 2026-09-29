# Decisions (ADR-lite)

Each entry gives the decision, the alternatives considered, and why.

- **L-entries** are the decisions fixed before the build (`PROJECT_PLAN.md` §3 and §7.1).
- **D-entries** are the choices made during the build, including every deviation from the plan.

## Locked decisions

### L-01: Staff may read everything but only create contacts

- **Alternatives:** Staff may also edit contacts; Staff is read-only.
- **Why:** The brief says Staff has "limited write access". Adding contacts is the smallest
  useful write, and it's easy to explain. The rule lives in one place, `PERMISSION_MATRIX`.

### L-02: Managers read, create and update, but never delete

- **Why:** The brief's wording. Deletion is the most destructive action, so it stays with Admins.

### L-03: Admins can do everything, including delete

- **Why:** The brief's wording.

### L-04: Only Admins and Managers can read the activity log

- **Alternatives:** Everyone reads it; Admins only.
- **Why:** Audit data shows who changed what; it's sensitive. The dashboard's "recent activity"
  follows the same rule, and one line in `PERMISSION_MATRIX` changes it.

### L-05: Another tenant's record returns 404, not 403

- **Why:** A 403 would confirm that the id exists in some other organization. With 404, a
  foreign id is indistinguishable from a missing one. It also follows naturally from filtering
  the queryset by organization before the lookup.

### L-06: Flat `/contacts/` endpoint with a `?company=` filter

- **Alternatives:** Nested `/companies/{id}/contacts/` (for example with drf-nested-routers).
- **Why:** No extra dependency, and one set of list, search and filter behavior. The UI still
  shows contacts nested under their company.

### L-07: Integer primary keys

- **Alternatives:** UUIDs.
- **Why:** Simpler to read in a demo and in logs. Isolation never relies on ids being hard to
  guess: every lookup is filtered by organization.

### L-08: The audit log is written by the service layer, not by signals

- **Alternatives:** `post_save` / `post_delete` signals; a third-party audit package.
- **Why:**
  - Signals can't see the acting user.
  - Bulk updates (the delete cascade) don't fire them.
  - They hide the write path.

  Explicit service functions inside `transaction.atomic` are easy to read, to test, and
  guarantee that no change is saved without its log row.

### L-09: Deleting a company soft-deletes its contacts, each logged

- **Why:** Contacts of a deleted company would otherwise be orphaned but still visible. One log
  row per contact keeps the audit trail truthful about what disappeared.

### L-10: A contact's company can't change after creation

- **Why:** Moving a contact would mean re-checking tenancy and per-company email uniqueness, and
  it isn't in the brief. The service ignores `company` on update.

### L-11: TypeScript in strict mode for the frontend

- **Why:** The API types (`src/api/types.ts`) catch mismatches at build time, and it makes the
  code easier to maintain.

### L-12: Access token in memory, refresh token in `localStorage`

- **Alternatives:** Both in `localStorage`; the refresh token in an httpOnly cookie.
- **Why:**
  - The access token never touches storage, and the session survives a reload.
  - The trade-off: script injection (XSS) could read the refresh token. Refresh-token
    rotation, blacklisting and a strict CSP reduce that risk.
  - An httpOnly, `SameSite` cookie for the refresh token is the production improvement. It
    needs CSRF handling on the refresh endpoint.

### L-13: Delete returns 200 with the envelope, not 204

- **Why:** Every response then has the same shape (`{"success": true, "message": "Company
  deleted.", "data": null}`), and the client never special-cases an empty body.

### L-14: Private S3 bucket with presigned URLs; local storage when S3 is off

- **Alternatives:** A public-read bucket or prefix; CloudFront with signed cookies.
- **Why:**
  - Logos belong to a tenant, and a public URL would work for anyone forever.
  - Presigned GET URLs expire after 5 minutes and need no bucket CORS for `<img>` tags.
  - Costs: signed URLs change on every response, so browsers cache logos less well.
  - `USE_S3=False` falls back to `FileSystemStorage`, so development and tests never depend on
    AWS.

### L-15: Tenancy notes (plan §7.1)

- **Why the middleware decodes the JWT:** DRF authenticates at view level, so a middleware
  can't see `request.user`. `TenantContextMiddleware` verifies the token and reads its `org_id`
  claim. It never rejects requests; that remains DRF's job.
- **Layers 2 and 3 are AND-ed:** if a token's `org_id` disagreed with the user's organization,
  queries would return nothing (fail-safe). `test_stale_org_claim_in_token_fails_safe` covers
  this.
- **Why layer 2 is mandatory:** the ambient manager filter is fail-open when no org is set
  (shell, admin, migrations, commands), so every view filters explicitly. PostgreSQL Row-Level
  Security would be the next step.
- **Related objects:** any serializer field that points at tenant data (`Contact.company`) uses a
  tenant-scoped queryset, so a record can't be attached to another organization's data.
- **Where roles come from:** permissions use the role from the database user, not the token
  claim, so role changes apply at once.

## Implementation decisions

### D-001: uv manages the Python backend instead of `requirements/*.txt`

- **Decision:** Backend dependencies are declared in `backend/pyproject.toml` with exact `==`
  pins and locked (including transitive packages, with hashes) in `backend/uv.lock`. Groups:
  default (runtime), `dev` (pytest, ruff, factory-boy), `prod` (gunicorn).
- **Alternatives:** pip + `requirements/{base,dev,prod}.txt` as in plan §5; pip-tools.
- **Why:** Requested by the repo owner. uv gives one reproducible lock file, fast installs, and
  manages the Python 3.12 interpreter itself. Dependency groups map 1:1 to the planned
  base/dev/prod split. Docker and CI install with `uv sync --frozen`.

### D-002: ESLint instead of the Vite template's oxlint

- **Decision:** Removed `oxlint` (current `create-vite` default) and configured ESLint
  (`eslint.config.js`) with typescript-eslint, react-hooks, react-refresh and eslint-config-prettier.
- **Why:** Plan §4.2 specifies ESLint + Prettier; it is also the more widely recognized setup.

### D-003: react-router-dom v7

- **Decision:** Use the latest stable `react-router-dom` (v7). Plan §4.2 asks for "v6+".
- **Why:** v7 is backwards compatible with the v6 component/`createBrowserRouter` APIs we use.

### D-004: Custom login serializer instead of subclassing `TokenObtainPairSerializer`

- **Decision:** `LoginSerializer` checks the password itself, and `tokens.issue_tokens()` adds the
  `org_id`, `role` and `email` claims to the refresh token (simplejwt copies them into every
  access token, including after rotation).
- **Alternatives:** Subclass simplejwt's `TokenObtainPairSerializer` (plan §9.3).
- **Why:** simplejwt's serializer goes through `authenticate()`, which returns `None` for inactive
  users. That makes "inactive" look exactly like "wrong password", but the plan needs a generic
  401 for bad credentials and a 403 for inactive or org-less accounts. Tests reuse
  `issue_tokens()` too, so they get the same claims as real logins.

### D-005: Audit `changes` are computed from before/after values, not `diff_instance(instance, data)`

- **Decision:** `activity.services.field_values()` reads the fields before the update and again
  after `save()`; `diff_values()` compares the two. `snapshot()` builds the CREATE payload.
- **Alternatives:** `diff_instance(instance, validated_data)` before mutating (plan §7.4).
- **Why:** A new logo's storage key only exists after the file is saved, so diffing the incoming
  upload would record the original filename instead of the real key. Reading values after the save
  records exactly what is stored (keys, never signed URLs).

### D-006: Write methods on read-only endpoints return 403, not 405

- **Decision:** `POST/PATCH/DELETE /activity-logs/` answer 403.
- **Why:** DRF runs permission checks before method dispatch. These methods have no viewset action,
  so `RolePermission` denies them (deny by default). We keep that rather than special-casing
  unknown actions in the permission class. The log is immutable either way (model `save()` also
  refuses updates, and Django admin is view-only).

### D-007: husky git hooks run the CI checks locally

- **Decision:** Add `husky` (frontend dev dependency). `pre-commit` runs the fast static checks
  (ruff, ESLint, Prettier, tsc); `pre-push` runs migrations check, pytest, Vitest and the build.
  Hooks live in `frontend/.husky` because `package.json` is not at the git root
  (`"prepare": "cd .. && husky frontend/.husky"`).
- **Alternatives:** `lint-staged` to auto-fix only staged files (one more dependency, and it has to
  cover both the Python and TS halves of the repo); the Python `pre-commit` framework (a second
  hook manager for a mostly-JS team).
- **Why:** One small dependency, and the hooks run the exact commands CI runs, so a green local
  push means a green CI run. CI sets `HUSKY=0` so hooks are never installed on runners.

### D-008: IAM `s3:ListBucket` without the prefix condition

- **Decision:** The app's IAM policy grants `s3:ListBucket` on the bucket with no `s3:prefix`
  condition (object actions stay limited to `org-*/logos/*`).
- **Alternatives:** Plan §10's `ListBucket` with `StringLike s3:prefix = org-*/logos/*`; or
  `file_overwrite=True` so django-storages skips the existence check and needs no `ListBucket`.
- **Why:** django-storages checks whether a key exists (HeadObject) before saving. S3 answers 404 for
  a missing key only if the caller has `ListBucket`; the `s3:prefix` condition key exists only on
  list requests, so with the condition the check gets 403 and the upload fails. The bucket stores
  only logos, so listing it reveals nothing extra.

### D-009: Trust `X-Forwarded-For` only from a configured number of proxies

- **Decision:** `REST_FRAMEWORK["NUM_PROXIES"] = TRUSTED_PROXY_COUNT` (default 0 = use the socket
  address; set to 1 behind a single nginx or load balancer).
- **Why:** DRF's default (`None`) uses the client-supplied `X-Forwarded-For` header as the client
  identity for throttling, so an attacker could send a new fake IP on every request and get
  unlimited login attempts. `test_hardening.py` proves the limit holds even with spoofed headers.

### D-010: API docs are off in production by default

- **Decision:** `/api/v1/schema/` and `/api/v1/docs/` are only routed when `API_DOCS_ENABLED=True`
  (default on in dev, off in prod).
- **Why:** Plan §8.5 asks for docs to be restricted or disabled in prod. Not routing them at all is
  the simplest option; a deployment can turn them on explicitly.

### D-011: JSON logs in production

- **Decision:** `LOG_FORMAT` selects `text` (dev default) or `json` (prod default), implemented by a
  20-line `JsonFormatter` in `apps/core/log_formatters.py` instead of a logging library.
- **Why:** Log platforms can filter JSON by level, logger and status code without parsing free text;
  a small formatter avoids adding a dependency.

### D-012: shadcn/ui (Radix) for UI components

- **Decision:** UI primitives come from shadcn/ui (`radix` base, `nova` style, neutral colors),
  copied into `frontend/src/components/ui/` by the shadcn CLI. Our reusable components
  (`common/`, `data/`, `layout/`, `auth/`) are built from them.
- **Added dependencies** (requested by the repo owner; not in plan §4.2):
  `radix-ui` (accessible dialogs, menus, drawers), `class-variance-authority` (component
  variants), `cn` (shadcn's class-name merger, replaces clsx + tailwind-merge), `sonner`
  (toasts), `tw-animate-css` (animations), `@fontsource-variable/geist` (self-hosted font), and
  `shadcn` as a dev dependency (its Tailwind CSS preset, used at build time).
- **Removed:** `next-themes` (added by the sonner component to follow a theme switcher the app
  doesn't have); toasts use the light theme.
- **Why:** Accessible, keyboard-friendly components (focus traps, ARIA) without writing them by
  hand; the code lives in the repo, so it can be read and changed like our own.
- **Lint:** `react-refresh/only-export-components` is off for `src/components/ui/**` only, because
  shadcn files export style helpers (e.g. `buttonVariants`) next to components.

### D-013: `sonner` toasts instead of a hand-written ToastContext

- **Decision:** Plan §11.1 lists a `ToastContext`. We use shadcn's `sonner` `<Toaster />` once in
  `App.tsx` and call `toast.success()` / `toast.error()` anywhere.
- **Why:** sonner already keeps its own global toast queue, so a React context around it would
  add code without adding behavior.

### D-014: Only login and refresh skip the refresh-and-retry

- **Decision:** The axios interceptor retries a 401 after refreshing for every endpoint except
  `/auth/login/` and `/auth/refresh/`.
- **Alternatives:** Plan §11.2 skips all `/auth/*` URLs.
- **Why:** `/auth/me/` (session restore) and `/auth/logout/` are ordinary authenticated calls; an
  expired access token there should refresh transparently too. Login and refresh are the auth
  flow itself, and retrying them would loop.

### D-015: `GET /companies/facets/` for the industry and country filters

- **Decision:** A read-only viewset action returns the distinct, non-empty industries and countries
  of the user's organization (soft-deleted companies excluded). `ACTION_TO_VERB` maps `facets` to
  `read`, so every role that can list companies can use it.
- **Alternatives:** Free-text filter inputs (the API filters with `iexact`, so users would have to
  type exact values), or deriving options from the dashboard's top-8 industries (incomplete).
- **Why:** Dropdowns with real values are the usable form of an exact-match filter; the endpoint is
  a few lines and follows the same tenant scoping and RBAC as the rest of the API.

### D-016: Route-level code splitting

- **Decision:** Pages behind login are loaded with React Router `lazy` routes.
- **Why:** The single bundle had grown past Vite's 500 kB warning. With lazy routes the login screen
  loads ~150 kB gzipped and each page fetches its own small chunk on first visit.

### D-017: One origin in the production-style stack (nginx proxies the API)

- **Decision:** In `docker-compose.prod.yml` the frontend's nginx serves the built app and proxies
  `/api/`, `/admin/` and `/static/` to gunicorn. The app is built with `VITE_API_BASE_URL=/api/v1`,
  so the browser only talks to one origin. The backend has no published port, and
  `TRUSTED_PROXY_COUNT=1` makes rate limiting use the client IP that nginx saw.
- **Alternatives:** Publish the API on its own port or host and allow the frontend origin with CORS
  (the dev setup does this: `localhost:5173` calls `localhost:8000`).
- **Why:** No CORS preflights, one place for TLS and security headers (CSP, `X-Frame-Options`),
  and the API is not reachable except through the proxy. A split-origin deployment still works:
  build the frontend with a full `VITE_API_BASE_URL` and set `CORS_ALLOWED_ORIGINS` on the API.

### D-018: Shared database cache for rate limiting in prod

- **Decision:** `prod.py` sets `CACHES` from `CACHE_URL`, defaulting to Django's database cache
  (`dbcache://django_cache`); `entrypoint.sh` runs `createcachetable`. Dev and tests keep the
  in-memory cache.
- **Alternatives:** The default in-process cache, or Redis.
- **Why:** DRF throttles store their counters in the cache. With the in-process cache each gunicorn
  worker counted separately: a 40-request burst let 28 login attempts through instead of 10. The
  database cache is shared by all workers and containers and needs no new service or dependency;
  `CACHE_URL=redis://...` (plus the `redis` package) swaps it later without code changes. DRF's
  throttle is read-then-write, so parallel bursts can still overshoot slightly (12 of 40 in the
  same test); acceptable for a login limiter.
