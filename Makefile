# Common commands. Backend runs natively through uv (DB in Docker) until the
# backend/frontend compose services land in phase 8.
BACKEND = cd backend &&
MANAGE  = $(BACKEND) uv run python manage.py

.PHONY: install up down logs migrate makemigrations seed test lint fmt shell backend-dev frontend-dev build

install: ## Install backend (uv) and frontend (npm) dependencies
	$(BACKEND) uv sync --all-groups
	cd frontend && npm ci

up: ## Start the Postgres container
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	$(MANAGE) migrate

makemigrations:
	$(MANAGE) makemigrations

seed:
	$(MANAGE) seed_demo

test:
	$(BACKEND) uv run pytest --cov=apps --cov-report=term-missing
	cd frontend && npm test

lint:
	$(BACKEND) uv run ruff check . && uv run ruff format --check .
	cd frontend && npm run lint && npm run typecheck && npm run format:check

fmt:
	$(BACKEND) uv run ruff check --fix . && uv run ruff format .
	cd frontend && npm run format

shell:
	$(MANAGE) shell

backend-dev:
	$(MANAGE) runserver 0.0.0.0:8000

frontend-dev:
	cd frontend && npm run dev

build:
	docker compose build
	cd frontend && npm run build
