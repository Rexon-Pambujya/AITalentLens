.PHONY: up down build logs migrate test lint backend-shell db-shell clean

# Bring up the full stack (Postgres+pgvector, Redis, MinIO, backend API,
# Celery worker, frontend). First run: `cp .env.example .env` first.
up:
	docker compose -f infra/docker-compose.yml up --build

down:
	docker compose -f infra/docker-compose.yml down

build:
	docker compose -f infra/docker-compose.yml build

logs:
	docker compose -f infra/docker-compose.yml logs -f

# Run Alembic migrations manually (the backend container also runs this
# automatically on startup - see infra/docker-compose.yml).
migrate:
	docker compose -f infra/docker-compose.yml exec backend alembic upgrade head

migration:
	docker compose -f infra/docker-compose.yml exec backend alembic revision --autogenerate -m "$(msg)"

test:
	docker compose -f infra/docker-compose.yml exec backend pytest tests/ -v

lint:
	docker compose -f infra/docker-compose.yml exec backend ruff check app/
	docker compose -f infra/docker-compose.yml exec frontend npm run lint

backend-shell:
	docker compose -f infra/docker-compose.yml exec backend bash

db-shell:
	docker compose -f infra/docker-compose.yml exec postgres psql -U talentlens -d talentlens

clean:
	docker compose -f infra/docker-compose.yml down -v
