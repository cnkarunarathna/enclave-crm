# Decisions (ADR-lite)

Each entry: the decision, the alternatives considered, and why. Locked decisions from
`PROJECT_PLAN.md` §3 are recorded as they are implemented.

## D-001: uv manages the Python backend instead of `requirements/*.txt`

- **Decision:** Backend dependencies are declared in `backend/pyproject.toml` with exact `==`
  pins and locked (including transitive packages, with hashes) in `backend/uv.lock`. Groups:
  default (runtime), `dev` (pytest, ruff, factory-boy), `prod` (gunicorn).
- **Alternatives:** pip + `requirements/{base,dev,prod}.txt` as in plan §5; pip-tools.
- **Why:** Requested by the repo owner. uv gives one reproducible lock file, fast installs, and
  manages the Python 3.12 interpreter itself. Dependency groups map 1:1 to the planned
  base/dev/prod split. Docker and CI install with `uv sync --frozen`.

## D-002: ESLint instead of the Vite template's oxlint

- **Decision:** Removed `oxlint` (current `create-vite` default) and configured ESLint
  (`eslint.config.js`) with typescript-eslint, react-hooks, react-refresh and eslint-config-prettier.
- **Why:** Plan §4.2 specifies ESLint + Prettier; it is also the more widely recognized setup.

## D-003: react-router-dom v7

- **Decision:** Use the latest stable `react-router-dom` (v7). Plan §4.2 asks for "v6+".
- **Why:** v7 is backwards compatible with the v6 component/`createBrowserRouter` APIs we use.

## D-004: Custom login serializer instead of subclassing `TokenObtainPairSerializer`

- **Decision:** `LoginSerializer` checks the password itself, and `tokens.issue_tokens()` adds the
  `org_id`, `role` and `email` claims to the refresh token (simplejwt copies them into every
  access token, including after rotation).
- **Alternatives:** Subclass simplejwt's `TokenObtainPairSerializer` (plan §9.3).
- **Why:** simplejwt's serializer goes through `authenticate()`, which returns `None` for inactive
  users. That makes "inactive" look exactly like "wrong password", but the plan needs a generic
  401 for bad credentials and a 403 for inactive or org-less accounts. Tests reuse
  `issue_tokens()` too, so they get the same claims as real logins.

## D-005: Audit `changes` are computed from before/after values, not `diff_instance(instance, data)`

- **Decision:** `activity.services.field_values()` reads the fields before the update and again
  after `save()`; `diff_values()` compares the two. `snapshot()` builds the CREATE payload.
- **Alternatives:** `diff_instance(instance, validated_data)` before mutating (plan §7.4).
- **Why:** A new logo's storage key only exists after the file is saved, so diffing the incoming
  upload would record the original filename instead of the real key. Reading values after the save
  records exactly what is stored (keys, never signed URLs).

## D-006: Write methods on read-only endpoints return 403, not 405

- **Decision:** `POST/PATCH/DELETE /activity-logs/` answer 403.
- **Why:** DRF runs permission checks before method dispatch. These methods have no viewset action,
  so `RolePermission` denies them (deny by default). We keep that rather than special-casing
  unknown actions in the permission class. The log is immutable either way (model `save()` also
  refuses updates, and Django admin is view-only).

## D-007: husky git hooks run the CI checks locally

- **Decision:** Add `husky` (frontend dev dependency). `pre-commit` runs the fast static checks
  (ruff, ESLint, Prettier, tsc); `pre-push` runs migrations check, pytest, Vitest and the build.
  Hooks live in `frontend/.husky` because `package.json` is not at the git root
  (`"prepare": "cd .. && husky frontend/.husky"`).
- **Alternatives:** `lint-staged` to auto-fix only staged files (one more dependency, and it has to
  cover both the Python and TS halves of the repo); the Python `pre-commit` framework (a second
  hook manager for a mostly-JS team).
- **Why:** One small dependency, and the hooks run the exact commands CI runs, so a green local
  push means a green CI run. CI sets `HUSKY=0` so hooks are never installed on runners.

## D-008: IAM `s3:ListBucket` without the prefix condition

- **Decision:** The app's IAM policy grants `s3:ListBucket` on the bucket with no `s3:prefix`
  condition (object actions stay limited to `org-*/logos/*`).
- **Alternatives:** Plan §10's `ListBucket` with `StringLike s3:prefix = org-*/logos/*`; or
  `file_overwrite=True` so django-storages skips the existence check and needs no `ListBucket`.
- **Why:** django-storages checks whether a key exists (HeadObject) before saving. S3 answers 404 for
  a missing key only if the caller has `ListBucket`; the `s3:prefix` condition key exists only on
  list requests, so with the condition the check gets 403 and the upload fails. The bucket stores
  only logos, so listing it reveals nothing extra.

## D-009: Trust `X-Forwarded-For` only from a configured number of proxies

- **Decision:** `REST_FRAMEWORK["NUM_PROXIES"] = TRUSTED_PROXY_COUNT` (default 0 = use the socket
  address; set to 1 behind a single nginx or load balancer).
- **Why:** DRF's default (`None`) uses the client-supplied `X-Forwarded-For` header as the client
  identity for throttling, so an attacker could send a new fake IP on every request and get
  unlimited login attempts. `test_hardening.py` proves the limit holds even with spoofed headers.

## D-010: API docs are off in production by default

- **Decision:** `/api/v1/schema/` and `/api/v1/docs/` are only routed when `API_DOCS_ENABLED=True`
  (default on in dev, off in prod).
- **Why:** Plan §8.5 asks for docs to be restricted or disabled in prod. Not routing them at all is
  the simplest option; a deployment can turn them on explicitly.

## D-011: JSON logs in production

- **Decision:** `LOG_FORMAT` selects `text` (dev default) or `json` (prod default), implemented by a
  20-line `JsonFormatter` in `apps/core/log_formatters.py` instead of a logging library.
- **Why:** Log platforms can filter JSON by level, logger and status code without parsing free text;
  a small formatter avoids adding a dependency.

## D-012: shadcn/ui (Radix) for UI components

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

## D-013: `sonner` toasts instead of a hand-written ToastContext

- **Decision:** Plan §11.1 lists a `ToastContext`. We use shadcn's `sonner` `<Toaster />` once in
  `App.tsx` and call `toast.success()` / `toast.error()` anywhere.
- **Why:** sonner already keeps its own global toast queue, so a React context around it would
  add code without adding behavior.

## D-014: Only login and refresh skip the refresh-and-retry

- **Decision:** The axios interceptor retries a 401 after refreshing for every endpoint except
  `/auth/login/` and `/auth/refresh/`.
- **Alternatives:** Plan §11.2 skips all `/auth/*` URLs.
- **Why:** `/auth/me/` (session restore) and `/auth/logout/` are ordinary authenticated calls; an
  expired access token there should refresh transparently too. Login and refresh are the auth
  flow itself, and retrying them would loop.
