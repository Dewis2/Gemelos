.PHONY: install backend frontend test lint format migrate up down

install:
	python -m pip install -e "./backend[dev]"

backend:
	python -m uvicorn main:app --app-dir backend/src --reload

frontend:
	npm --prefix frontend run dev

test:
	python -m pytest backend/tests

lint:
	ruff check backend/src backend/tests ml/src ml/tests edge
	mypy backend/src

format:
	ruff check --fix backend/src backend/tests ml/src ml/tests edge
	black backend/src backend/tests ml/src ml/tests edge

migrate:
	cd backend && alembic upgrade head

up:
	docker compose up --build

down:
	docker compose down

