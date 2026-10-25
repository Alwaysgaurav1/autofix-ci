.PHONY: install test demo demo-node demo-docker api ui dev docker-build

VENV = .venv
PYTHON = $(VENV)/bin/python
PYTEST = $(VENV)/bin/pytest
BUN = ~/.bun/bin/bun

install:
	@echo "Installing AutoFix CI Python dependencies with uv..."
	uv venv $(VENV)
	uv pip install -e .
	@if [ -d "ui" ]; then \
		echo "Installing UI dependencies..."; \
		cd ui && $(BUN) install; \
	fi

test:
	@echo "Running AutoFix CI Test Suite..."
	PYTHONPATH=. $(PYTEST) tests/ -v

demo:
	@echo "Running AutoFix CI Demo Scenario 1 (Python / Pytest)..."
	PYTHONPATH=. $(PYTHON) cli/main.py demo 1

demo-node:
	@echo "Running AutoFix CI Demo Scenario 2 (Node.js / Jest)..."
	PYTHONPATH=. $(PYTHON) cli/main.py demo 2

demo-docker:
	@echo "Running AutoFix CI Demo Scenario 3 (Docker)..."
	PYTHONPATH=. $(PYTHON) cli/main.py demo 3

api:
	@echo "Starting AutoFix CI API server at http://localhost:8000..."
	PYTHONPATH=. $(PYTHON) -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

ui:
	@echo "Starting AutoFix CI Next.js Cockpit at http://localhost:3000..."
	cd ui && $(BUN) dev -p 3000

docker-build:
	docker-compose build
