# Recording script (target 17 minutes)

A shot list for the 15–20 minute screen recording. Each section says what to show and the points
to make; the words are yours. Timings add up to 17 minutes, which leaves slack either way.

## Before recording

1. Start everything and reset the demo data:

   ```bash
   make up && make migrate
   cd backend && uv run python manage.py seed_demo --reset && cd ..
   make backend-dev            # terminal 1
   make frontend-dev           # terminal 2
   ```

2. Note the **cross-tenant hint** that `seed_demo` prints at the end: the id of Acme's "Sunrise
   Hotels" and the URL to try as Blue Sky. Ids change after `--reset`, so always use the printed
   one. It's written as `<ACME_ID>` below.
3. Make sure `USE_S3=True` in `backend/.env` and have the S3 console open on the bucket (empty
   `org-*/logos/` prefix).
4. Browser: one normal window (Acme admin) and one private window (the other users). Zoom to
   125% so text is legible. Close unrelated tabs and notifications.
5. Editor tabs ready: `docs/ARCHITECTURE.md` (preview), `apps/core/middleware.py`,
   `apps/core/managers.py`, `apps/core/viewsets.py`, `apps/organizations/roles.py`,
   `apps/core/permissions.py`, `apps/crm/services.py`, `apps/activity/services.py`,
   `frontend/src/api/client.ts`.
6. A third terminal for the API calls in section 4.
7. **Rate limit:** login is limited to 10 attempts per minute per IP. Rehearsing many logins in
   a row can trigger "Request was throttled"; wait a minute, or restart the backend (the dev
   cache is in memory).

## 1. System overview and architecture (3 min)

Show `docs/ARCHITECTURE.md` in Markdown preview.

- **What it is:** one deployment, many organizations; companies, contacts and an audit log;
  Django REST Framework, React, PostgreSQL, S3.
- **Component diagram:** React → API → service layer → PostgreSQL and S3. Views stay thin;
  every write goes through `services.py`.
- **The four isolation layers** (section 4 table):
  1. The org foreign key on every tenant model.
  2. `for_org()` in every viewset: the primary control.
  3. The `TenantManager` ambient filter.
  4. The middleware that sets it.
- **Open `middleware.py`:** DRF authenticates inside the view, so the middleware can't see
  `request.user`. It verifies the JWT and reads the `org_id` claim itself. It resets the
  ContextVar in `finally`, and it never rejects a request.
- **Open `managers.py`:** the ambient filter is fail-open in the shell and in migrations, which
  is why `viewsets.py` filters explicitly. The two layers are AND-ed, so if they disagree the
  result is empty, never another tenant's data.
- **Why 404 and not 403:** a 403 would confirm that the id exists in another organization.

## 2. Authentication flow (2 min)

- **Log in as `admin@acme.test` / `Passw0rd!123`.** In DevTools → Network, show the login
  response: `access`, `refresh` and `user`. Paste the access token into jwt.io (or just point
  at it) to show the `org_id`, `role` and `email` claims.
- **Reload the page:** you stay logged in. The access token lives only in memory; on load the
  app uses the refresh token (in `localStorage`) to get a new one, then calls `/auth/me/`.
- **Open `client.ts`:** on a 401, one shared refresh (single-flight) retries every waiting
  request. If the refresh fails, the user is sent to `/login`.
- **Protected routes:** log out, then open `/companies` directly → redirected to login, and
  returned to `/companies` after signing in.
- **No-token behavior,** in the terminal:

  ```bash
  curl -s localhost:8000/api/v1/companies/
  # {"success": false, "message": "Authentication credentials were not provided.", "code": "not_authenticated", ...}
  ```

## 3. Tenant isolation, live (3 min)

- **As the Acme admin,** open Companies. Point out 13 companies over 2 pages, including
  "Sunrise Hotels". Open it and show the id in the URL.
- **Private window:** log in as `admin@bluesky.test`. Its list has 4 companies, and it has its
  *own* "Sunrise Hotels" (same name, different id). One of its contacts shares an email with an
  Acme contact. Uniqueness is per company, isolation per tenant.
- **Still as Blue Sky,** paste `http://localhost:5173/companies/<ACME_ID>` → "Company not found".
- **Mention the test suite** (`tests/test_tenant_isolation.py`). It covers list, detail, update,
  delete, `?company=` filters, the activity log, the dashboard, attaching a contact to another
  org's company, and a stale `org_id` claim.

## 4. Role-based access control (2 min)

- **Open `roles.py`:** one permission matrix. `RolePermission` maps DRF actions to verbs and
  denies anything unknown. The role comes from the database, not the token.
- **Private window, as `staff@acme.test`:**
  - no "New company" button
  - no edit or delete on rows
  - "Add contact" still works
  - no Activity log in the sidebar
  - `/activity` shows the Forbidden page
- **As `manager@acme.test`:** "Edit" is shown, "Delete" is not.
- **The UI only hides buttons.** Prove it with a direct call as Staff:

  ```bash
  TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/login/ \
    -H 'Content-Type: application/json' \
    -d '{"email":"staff@acme.test","password":"Passw0rd!123"}' \
    | python3 -c 'import sys, json; print(json.load(sys.stdin)["data"]["access"])')

  curl -s -X DELETE localhost:8000/api/v1/companies/<ACME_ID>/ -H "Authorization: Bearer $TOKEN"
  # {"success": false, "message": "You do not have permission to perform this action.", "code": "permission_denied", ...}

  curl -s localhost:8000/api/v1/activity-logs/ -H "Authorization: Bearer $TOKEN"   # also 403
  ```

  (Alternatively use Swagger at `http://localhost:8000/api/v1/docs/`: **Authorize** with the
  token and try the delete.)

## 5. CRUD (4 min)

As the Acme admin:

- **Search, filters and pagination:**
  - Type "sun": the search is debounced and appears in the URL.
  - Pick Industry "Hospitality"; the dropdown options come from the org's own data.
  - Sort A–Z and go to page 2.
  - Reload: the filters survive. Clear filters.
- **Create a company with a logo:** "New company", upload a PNG (preview shown) → the toast and
  the logo in the table.
- **Show the S3 side:**
  - In the S3 console, the object is at `org-<id>/logos/<uuid>.png`.
  - Right-click the logo → open image in a new tab. The URL has `X-Amz-Signature` and
    `X-Amz-Expires=300`.
  - Remove the query string and reload → **AccessDenied**: the bucket is private, and only
    signed links work, for 5 minutes.
- **Validation:** edit the company and try a text file renamed `.png` → the server rejects it
  under the Logo field.
- **Nested contacts:** open the company → "Add contact":
  - A phone number `1234` → "Phone must be 8–15 digits."
  - Save a valid contact, then add another with the same email in different case → "A contact
    with this email already exists for this company." (checked by the server).
- **Edit:** change a contact's job title; the contacts count on the header card updates.
- **Soft delete:**
  - Delete the company (confirmation dialog) → you're back on the list and it's gone.
  - Its contacts are gone too. The rows still exist with `is_deleted=true`.
  - A deleted contact's email can be reused.

## 6. Activity log (2 min)

- **Open Activity log.** Point out:
  - the entries just created: CREATE company, CREATE contact, UPDATE contact
  - the company DELETE, followed by one DELETE per contact it cascaded to
- **Filter** by Action = Updated and expand an entry: old → new values. Logos are recorded as
  storage keys, never signed URLs.
- **Open `crm/services.py`:**
  - each function is `@transaction.atomic` and writes the change, then the log row
  - if logging fails, the change rolls back
  - services, not signals, because signals can't know the acting user
- **Open `activity/services.py`:**
  - `log_activity` refuses to log for another organization's object
  - the log is append-only (read-only API and admin; `save()` refuses updates)

## 7. Production readiness and trade-offs (1 min)

Show the README's "Production-style stack" section and `docker-compose.prod.yml`. Points:

- **Configuration:** every setting comes from environment variables (`.env.example`
  documents each one), and the dev and prod settings are split.
- **Hardening:**
  - Prod requires a secret key, keeps `DEBUG` off, and sets HTTPS, HSTS and secure cookies.
  - Allowed hosts and CORS origins are explicit.
  - `check --deploy` is clean.
- **Deployment shape:**
  - gunicorn runs as a non-root user behind nginx.
  - nginx serves the SPA and the API from one origin.
  - Logs are JSON; API docs are off.
- **CI:** the GitHub Actions badge is green, covering lint, tests with a 90% coverage gate, the
  deploy check, and an image build plus smoke test. husky runs the same checks before each
  commit and push.
- **Next steps:**
  - PostgreSQL Row-Level Security
  - an httpOnly-cookie refresh token
  - presigned POST uploads straight to S3
  - Redis for the cache
  - Celery if the audit log should be written asynchronously
  - observability

## After recording

- Check the audio, and that code is readable at 1080p.
- Delete the demo company you created (if you didn't in section 5), or run
  `seed_demo --reset`. The S3 object stays after a soft delete; remove it in the console if you
  want the bucket empty.
