.PHONY: setup dev test lint up down

setup:
	uv python install
	uv sync

dev:
	uv sync
	uv run pre-commit install

test:
	uv run pytest

lint:
	uv run ruff check . --fix
	uv run ruff format .

up:
	docker compose up --build

down:
	docker compose down