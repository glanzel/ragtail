.PHONY: help install install-python install-node sync demo-sync lock build watch run-demo demo test clean docker-build docker-run init-db createsuperuser seeddb setup makemigrations migrate showmigrations

UV     ?= uv
NPM    ?= npm
HOST   ?= 127.0.0.1
PORT   ?= 8000
DEMO_DIR := examples/demo
DOCKER_IMAGE ?= ragtail-demo
DOCKER_VOLUME ?= ragtail-data
USERNAME ?=
EMAIL ?=
PASSWORD ?=
LANGUAGE_CODE ?=
DISPLAY_NAME ?=
NOINPUT ?=
UPDATE ?=
MIGRATION_NAME ?=

.DEFAULT_GOAL := help

help: ## Show available targets
	@echo "Oxytail development commands:"
	@echo ""
	@grep -E '^[a-zA-Z0-9_.-]+:.*##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: sync demo-sync install-node build ## Install library + demo deps and build frontend assets
	@echo "Installation complete."
	@echo "Next: make migrate && make createsuperuser && make run-demo"

setup: install seeddb ## First-time install, migrate DB, default locale, and admin user

install-python: sync demo-sync ## Sync Python envs (library tests + demo app)

sync: ## Sync library env from uv.lock (tests + dev tools)
	$(UV) sync --locked

demo-sync: ## Sync demo app env (local editable ragtail)
	cd $(DEMO_DIR) && $(UV) sync --locked

lock: ## Refresh root and demo uv.lock files
	$(UV) lock
	cd $(DEMO_DIR) && $(UV) lock

install-node: ## Install npm dependencies (prefers npm ci when lockfile exists)
	@if [ -f package-lock.json ]; then $(NPM) ci; else $(NPM) install; fi

build: install-node ## Build Tailwind CSS and richtext bundle
	$(NPM) run build:css

watch: install-node ## Watch CSS sources and rebuild on change
	@echo "Watching admin + site CSS (Ctrl+C to stop)..."
	@trap 'kill 0' EXIT INT TERM; \
	$(NPM) run watch:css & \
	npx tailwindcss -i ./styles/site.css -o ./examples/demo/static/site.css --watch & \
	wait

init-db: migrate ## Alias for migrate (apply schema migrations)

makemigrations: ## Generate Ragtail package migration files (MIGRATION_NAME=optional)
	$(UV) run ragtail-makemigrations \
		$(if $(MIGRATION_NAME),--name "$(MIGRATION_NAME)",)

migrate: ## Create database file (if needed) and apply migrations
	cd $(DEMO_DIR) && $(UV) run ragtail-initdb

showmigrations: ## Show Ragtail package migrations (applied state from demo DB)
	cd $(DEMO_DIR) && $(UV) run ragtail-showmigrations

createsuperuser: ## Create staff user only (run migrate first; USERNAME/EMAIL/PASSWORD/NOINPUT=1 for scripted)
	cd $(DEMO_DIR) && $(UV) run ragtail-createsuperuser \
		$(if $(USERNAME),--username "$(USERNAME)",) \
		$(if $(EMAIL),--email "$(EMAIL)",) \
		$(if $(PASSWORD),--password "$(PASSWORD)",) \
		$(if $(NOINPUT),--noinput,) \
		$(if $(UPDATE),--update,)

seeddb: ## Migrate DB, seed default locale, and create staff user
	cd $(DEMO_DIR) && $(UV) run ragtail-seeddb \
		$(if $(LANGUAGE_CODE),--language-code "$(LANGUAGE_CODE)",) \
		$(if $(DISPLAY_NAME),--display-name "$(DISPLAY_NAME)",) \
		$(if $(USERNAME),--username "$(USERNAME)",) \
		$(if $(EMAIL),--email "$(EMAIL)",) \
		$(if $(PASSWORD),--password "$(PASSWORD)",) \
		$(if $(NOINPUT),--noinput,) \
		$(if $(UPDATE),--update,)

run-demo: demo-sync ## Run demo app with auto-reload (from examples/demo)
	cd $(DEMO_DIR) && $(UV) run uvicorn main:app --reload --host $(HOST) --port $(PORT)

demo: demo-sync ## Run demo app without reload
	cd $(DEMO_DIR) && $(UV) run python main.py

test: ## Run pytest suite
	$(UV) run pytest

clean: ## Remove build artifacts and caches
	rm -rf .pytest_cache .venv $(DEMO_DIR)/.venv
	rm -rf node_modules
	rm -f *.db-shm *.db-wal freshtest.db migrations-test.db ragtail.db
	rm -f $(DEMO_DIR)/ragtail.db $(DEMO_DIR)/ragtail.db-shm $(DEMO_DIR)/ragtail.db-wal
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.py[co]' -delete

docker-build: ## Build demo Docker image
	docker build -t $(DOCKER_IMAGE) .

docker-run: ## Run demo in Docker on port 8000
	docker run --rm -p $(PORT):8000 -v $(DOCKER_VOLUME):/data $(DOCKER_IMAGE)
