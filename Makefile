.PHONY: help build up down logs shell-backend shell-worker shell-frontend test lint clean

help:
	@echo "Available commands:"
	@echo "  make build          - Build all Docker images"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make logs           - View logs from all services"
	@echo "  make shell-backend  - Open shell in backend container"
	@echo "  make shell-worker   - Open shell in worker container"
	@echo "  make shell-frontend - Open shell in frontend container"
	@echo "  make test           - Run all tests"
	@echo "  make lint           - Run linters"
	@echo "  make clean          - Remove containers and volumes"

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

shell-backend:
	docker compose exec backend /bin/bash

shell-worker:
	docker compose exec celery-worker /bin/bash

shell-frontend:
	docker compose exec frontend /bin/sh

test:
	docker compose exec backend pytest
	docker compose exec frontend npm test

lint:
	docker compose exec backend ruff check .
	docker compose exec frontend npm run lint

clean:
	docker compose down -v --remove-orphans
