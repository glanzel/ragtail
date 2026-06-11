.PHONY: help install install-python install-node sync lock build watch dev demo test clean docker-build docker-run

UV     ?= uv
NPM    ?= npm
HOST   ?= 127.0.0.1
PORT   ?= 8000
DOCKER_IMAGE ?= oxytail-demo
DOCKER_VOLUME ?= oxytail-data

.DEFAULT_GOAL := help

help: ## Show available targets
	@echo "Oxytail development commands:"
	@echo ""
	@grep -E '^[a-zA-Z0-9_.-]+:.*##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: sync install-node build ## Install Python + npm deps and build frontend assets
	@echo "Installation complete."

install-python: sync ## Alias for uv sync (demo extra + dev group)

sync: ## Sync Python env from uv.lock (demo extra + dev group)
	$(UV) sync --locked --extra demo

lock: ## Refresh uv.lock after dependency changes
	$(UV) lock

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

dev: ## Run demo app with auto-reload (uvicorn)
	$(UV) run uvicorn examples.demo.main:app --reload --host $(HOST) --port $(PORT)

demo: ## Run demo app without reload
	$(UV) run python examples/demo/main.py

test: ## Run pytest suite
	$(UV) run pytest

clean: ## Remove build artifacts and caches
	rm -rf .pytest_cache .venv
	rm -rf node_modules
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.py[co]' -delete

docker-build: ## Build demo Docker image
	docker build -t $(DOCKER_IMAGE) .

docker-run: ## Run demo in Docker on port 8000
	docker run --rm -p $(PORT):8000 -v $(DOCKER_VOLUME):/data $(DOCKER_IMAGE)
