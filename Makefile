.PHONY: up down logs backend-test backend-lint

up:
	cd infra && cp -n .env.example .env || true
	cd infra && docker compose up --build

down:
	cd infra && docker compose down -v

logs:
	cd infra && docker compose logs -f --tail=200

backend-test:
	cd backend && pytest

backend-lint:
	cd backend && python -m compileall app tests
