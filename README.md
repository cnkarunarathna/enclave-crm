# Multi-Tenant CRM

A multi-tenant CRM (Django REST Framework + React + PostgreSQL + AWS S3). Many organizations
share one deployment; each manages its own Companies and Contacts, with role-based access
(Admin / Manager / Staff) and an audit log.

> Work in progress: see [`PROJECT_PLAN.md`](PROJECT_PLAN.md) for scope and build phases.
> The full README (architecture, tenancy, RBAC, S3 strategy) arrives in phase 9.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (installs Python 3.12 automatically)
- Node.js 24 LTS + npm
- Docker (for PostgreSQL)

## Quick start (development)

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

make install          # uv sync (backend) + npm ci (frontend, also installs git hooks)
make up               # Postgres 16 on localhost:5433

make backend-dev      # http://localhost:8000
make frontend-dev     # http://localhost:5173 (in a second terminal)
```

## Common commands

| Command | What it does |
|---|---|
| `make test` | Backend pytest (with coverage) + frontend Vitest |
| `make lint` | ruff check/format check, ESLint, `tsc`, Prettier check |
| `make fmt` | Auto-fix formatting (ruff, Prettier) |
| `make migrate` / `make makemigrations` | Django migrations |

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
