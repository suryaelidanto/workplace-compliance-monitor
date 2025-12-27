.PHONY: setup dev test lint up down

# Install all dependencies including dev-groups
setup:
	uv sync

# Setup local development environment with pre-commit hooks
dev:
	uv sync
	uv run pre-commit install

# Run all tests (Integration & AI Evaluations)
test:
	uv run pytest

# Fix linting and format code using ruff
lint:
	uv run ruff check . --fix
	uv run ruff format .

# Build and start the containerized service
up:
	docker compose up --build

# Stop and remove containers
down:
	docker compose down