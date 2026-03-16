.PHONY: check clean format init lint lint-fix test start db-playground email-playground generate-test-data regenerate-test-data

check: lint test

clean:
	uvx pyclean . --debris all --erase ".venv/**/*" ".venv/" --yes

format:
	uv run ruff format .

init:
	uv sync

lint:
	uv run ruff check .
	uv run ty check

lint-fix:
	uv run ruff check --fix .
	uv run ty check .

test:
	uv run pytest

up:
	uv run start

db-playground:
	uv run python -c "from scripts.db_playground import main; main()"

email-playground:
	uv run python -c "from scripts.email_playground import main; main()"

generate-test-data:
	uv run python -c "from test_data.generator import generate; generate()"

regenerate-test-data:
	uv run python -c "from test_data.generator import regenerate; regenerate()"
