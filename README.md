# Multi-Tenant CRM

A multi-tenant CRM (Django REST Framework + React + PostgreSQL + AWS S3). Many organizations
share one deployment; each manages its own Companies and Contacts, with role-based access
(Admin / Manager / Staff) and an audit log.

> Work in progress: see [`PROJECT_PLAN.md`](PROJECT_PLAN.md) for scope and build phases.
> The full README (architecture, tenancy, RBAC, S3 strategy) arrives in phase 9.

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

Open http://localhost:5173 and log in as `admin@acme.test` / `Passw0rd!123` (also `manager@`,
`staff@`, and the same three at `bluesky.test`). API docs: http://localhost:8000/api/v1/docs/.

Logos are stored in `backend/media/` until S3 is configured (`docs/AWS_S3_SETUP.md`).

## Quick start (native, database in Docker)

Faster reloads and what the git hooks use. After the three `cp` commands above:

```bash
make install          # uv sync (backend) + npm ci (frontend, also installs git hooks)
make up               # Postgres 16 only, on localhost:5433
make migrate
make seed

make backend-dev      # http://localhost:8000
make frontend-dev     # http://localhost:5173 (in a second terminal)
```

## Production-style stack

`docker-compose.prod.yml` runs what a deployment would: the API with prod settings under gunicorn
(non-root, `DEBUG=False`, JSON logs, docs off) behind nginx, which serves the built frontend and
proxies `/api/` to the backend, so the browser talks to a single origin.

```bash
# in the root .env: set DJANGO_SECRET_KEY (the command is in .env.example)
make prod-up          # builds images, migrates, waits until healthy: http://localhost:8080
make prod-seed        # demo data (seed_demo --force, since DEBUG is off)
make prod-down
```

It reuses `backend/.env` for the S3 settings, has its own database volume (project `crm-prod`),
and turns off the HTTPS redirect because there is no TLS locally. Behind a real HTTPS load
balancer, leave `DJANGO_SECURE_SSL_REDIRECT` at its default (`True`).

## Common commands

| Command | What it does |
|---|---|
| `make test` | Backend pytest (with coverage) + frontend Vitest |
| `make lint` | ruff check/format check, ESLint, `tsc`, Prettier check |
| `make fmt` | Auto-fix formatting (ruff, Prettier) |
| `make migrate` / `make makemigrations` | Django migrations |
| `make stack` / `make down` | Start the full dev stack in Docker (detached) / stop everything |
| `make build` | Build the production images |

## Git hooks (husky)

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
