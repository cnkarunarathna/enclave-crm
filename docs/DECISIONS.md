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
