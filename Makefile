include .env
export

code-dir = app

up:
	docker compose -f docker-compose.yml up -d --build --timeout 60

down:
	docker compose -f docker-compose.yml down --timeout 60

.PHONY pull:
pull:
	git pull origin master
	git submodule update --init --recursive

.PHONY lint:
lint:
	@echo "Running ruff..."
	@ruff check --config pyproject.toml --diff $(code-dir)

.PHONY format:
format:
	@echo "Running ruff check with --fix..."
	@ruff check --config pyproject.toml --fix $(code-dir)

	@echo "Running ruff..."
	@ruff format --config pyproject.toml $(code-dir)

	@echo "Running isort..."
	@isort --settings-file pyproject.toml $(code-dir)

.PHONY poetry-show:
poetry-show:
	@cd $(code-dir) && @poetry show --top-level --latest

.PHONY poetry-show-outdated:
poetry-show-outdated:
	@cd $(code-dir) && @poetry show --top-level --outdated
