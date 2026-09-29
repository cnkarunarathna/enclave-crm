# Common commands. The native targets (migrate, seed, test, ...) run the backend
# through uv against the Docker database from `make up` (or `make stack`).
BACKEND = cd backend &&
MANAGE  = $(BACKEND) uv run python manage.py
PROD    = docker compose -f docker-compose.prod.yml

.PHONY: install up stack down logs migrate makemigrations seed test lint fmt shell \
	backend-dev frontend-dev build prod-up prod-down prod-logs prod-seed

install: ## Install backend (uv) and frontend (npm) dependencies
	$(BACKEND) uv sync --all-groups
	cd frontend && npm ci

up: ## Start only Postgres (run backend/frontend natively: backend-dev, frontend-dev)
	docker compose up -d db

stack: ## Whole dev stack in Docker: db + backend (:8000) + frontend (:5173), hot reload
	docker compose up --build -d

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

build: ## Build the production images
	docker build -t crm-backend ./backend
	docker build -t crm-frontend ./frontend

prod-up: ## Production-style stack (gunicorn + nginx) on http://localhost:8080
	$(PROD) up --build -d --wait

prod-down:
	$(PROD) down

prod-logs:
	$(PROD) logs -f

prod-seed: ## Demo data in the prod-style stack (seed_demo needs --force when DEBUG=False)
	$(PROD) exec backend python manage.py seed_demo --force
