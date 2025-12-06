.PHONY: help dev prod build-dev build-prod down-dev down-prod \
        logs-dev logs-prod api-logs-dev api-logs-prod \
        db-logs-dev db-logs-prod redis-logs-dev redis-logs-prod \
        migrate shell test clean-docker-dev status

# Variables
BACKEND_DIR := backend
COMPOSE_DEV := $(BACKEND_DIR)/docker/docker-compose.dev.yml
COMPOSE_PROD := $(BACKEND_DIR)/docker/docker-compose.yml
DC_DEV := docker compose -f $(COMPOSE_DEV)
DC_PROD := docker compose -f $(COMPOSE_PROD)

help:
	@echo "BookBytes - Development Commands"
	@echo "================================="
	@echo ""
	@echo "🚀 Environment:"
	@echo "  dev              - Start dev (hot reload)"
	@echo "  prod             - Start production"
	@echo "  build-dev        - Build dev containers"
	@echo "  build-prod       - Build prod containers"
	@echo "  down-dev         - Stop dev services"
	@echo "  down-prod        - Stop prod services"
	@echo ""
	@echo "Logs (composable env-component):"
	@echo "  logs-dev         - All dev logs"
	@echo "  logs-prod        - All prod logs"
	@echo "  api-logs-dev     - Dev API logs"
	@echo "  api-logs-prod    - Prod API logs"
	@echo "  db-logs-dev      - Dev DB logs"
	@echo "  db-logs-prod     - Prod DB logs"
	@echo "  redis-logs-dev   - Dev Redis logs"
	@echo "  redis-logs-prod  - Prod Redis logs"
	@echo ""
	@echo "Database (dev-container only):"
	@echo "  migrate          - Run migrations (dev)"
	@echo "  shell            - Python shell (dev)"
	@echo "  db-shell         - PostgreSQL shell (dev)"
	@echo ""
	@echo "🧪 Testing (dev-container only):"
	@echo "  test             - Run tests"
	@echo "  test-cov         - Tests with coverage"
	@echo ""
	@echo "🧹 Cleanup (dev-container only):"
	@echo "  clean-docker-dev - Remove dev containers/images/volumes"
	@echo "  status           - Show container status"

# Start
dev:
	$(DC_DEV) up -d

prod:
	$(DC_PROD) up -d

# Build
build-dev:
	$(DC_DEV) build

build-prod:
	$(DC_PROD) build

# Stop
down-dev:
	$(DC_DEV) down

down-prod:
	$(DC_PROD) down

# Logs (composable)
logs-dev:
	$(DC_DEV) logs -f

logs-prod:
	$(DC_PROD) logs -f

api-logs-dev:
	$(DC_DEV) logs -f api

api-logs-prod:
	$(DC_PROD) logs -f api

db-logs-dev:
	$(DC_DEV) logs -f postgres

db-logs-prod:
	$(DC_PROD) logs -f postgres

redis-logs-dev:
	$(DC_DEV) logs -f redis

redis-logs-prod:
	$(DC_PROD) logs -f redis

# Database
migrate:
	$(DC_DEV) exec api uv run alembic upgrade head

shell:
	$(DC_DEV) exec api uv run python

db-shell:
	$(DC_DEV) exec postgres psql -U bookbytes -d bookbytes

# Test
test:
	cd $(BACKEND_DIR) && uv sync --all-extras && uv run pytest

test-cov:
	cd $(BACKEND_DIR) && uv sync --all-extras && uv run pytest --cov=src/bookbytes --cov-report=html

# Status
status:
	@echo "Dev containers:"
	@$(DC_DEV) ps
	@echo ""
	@echo "Prod containers:"
	@$(DC_PROD) ps

# Cleanup (DEV ONLY - composable)
clean-dev-containers:
	@echo "🧹 Removing dev containers..."
	$(DC_DEV) rm -f

clean-dev-images:
	@echo "🧹 Removing dev images..."
	@docker images | grep bookbytes-.*-dev | awk '{print $$3}' | xargs -r docker rmi 2>/dev/null || echo "No dev images to remove"

clean-dev-volumes:
	@echo "⚠️  Removing dev volumes..."
	@read -p "Remove dev volumes? [y/N] " confirm && [ "$$confirm" = "y" ] && \
		docker volume ls | grep bookbytes_dev | awk '{print $$2}' | xargs -r docker volume rm 2>/dev/null || echo "Skipped volume removal"

clean-dev: down-dev clean-dev-containers clean-dev-images clean-dev-volumes
	@echo "✅ Dev cleanup complete"
